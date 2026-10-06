"""KWin authorisation for the capture helper.

`org.kde.KWin.ScreenShot2` answers `Error.NoAuthorized` unless the calling process'
`/proc/<pid>/exe` matches the `Exec=` of a `.desktop` file that lists the interface in
`X-KDE-DBUS-Restricted-Interfaces` (this is how Spectacle is allowed in).  So we drop a
desktop file for our helper into `~/.local/share/applications/` and refresh KService.

KWin matches on the *canonical* executable path, and it keys the desktop file by that
path, so one file per distinct helper binary is written (different virtualenvs each get
their own entry and can coexist).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

INTERFACE = "org.kde.KWin.ScreenShot2"
PREFIX = "io.github.kwcapture"

TEMPLATE = """[Desktop Entry]
Type=Application
Name=KWin Capture
GenericName=Screen capture
Comment=Helper process kwcapture uses to capture the screen on KDE Plasma
Exec={exe}
Icon=accessories-screenshot
Terminal=false
NoDisplay=true
X-KDE-DBUS-Restricted-Interfaces={interface}
"""


def applications_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "applications"


def tag_for(exe: Path | str) -> str:
    return hashlib.sha1(str(Path(exe).resolve()).encode()).hexdigest()[:10]


def desktop_path(exe: Path | str) -> Path:
    return applications_dir() / f"{PREFIX}-{tag_for(exe)}.desktop"


def is_installed(exe: Path | str) -> bool:
    path = desktop_path(exe)
    if not path.is_file():
        return False
    try:
        text = path.read_text()
    except OSError:
        return False
    return f"Exec={Path(exe).resolve()}" in text and INTERFACE in text


def refresh_kde_service_cache(verbose: bool = False) -> bool:
    """Ask KDE to rescan desktop files (kwin reads them through KService)."""
    tool = shutil.which("kbuildsycoca6") or shutil.which("kbuildsycoca5")
    if not tool:
        if verbose:
            print("kbuildsycoca not found; KDE should still notice the new desktop file")
        return False
    try:
        subprocess.run([tool], capture_output=True, timeout=60)
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def install_desktop_file(exe: Path | str, refresh: bool = True,
                         verbose: bool = False) -> Path:
    """Write (or rewrite) the authorising desktop file for `exe`."""
    exe = Path(exe).resolve()
    path = desktop_path(exe)
    body = TEMPLATE.format(exe=str(exe), interface=INTERFACE)
    if path.is_file():
        try:
            if path.read_text() == body:
                if verbose:
                    print(f"already authorised: {path}")
                return path
        except OSError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    if verbose:
        print(f"wrote {path}")
    if refresh:
        refresh_kde_service_cache(verbose=verbose)
    return path


def uninstall(desktop: Path | str | None = None) -> list[Path]:
    """Remove our desktop file(s) — all of them when called without an argument."""
    removed: list[Path] = []
    if desktop is not None:
        path = Path(desktop)
        if path.is_file():
            path.unlink()
            removed.append(path)
        return removed
    for path in applications_dir().glob(f"{PREFIX}*.desktop"):
        try:
            path.unlink()
            removed.append(path)
        except OSError:
            pass
    return removed


def prune(verbose: bool = False) -> list[Path]:
    """Delete desktop files whose helper binary no longer exists (stale venvs)."""
    removed = []
    for path in applications_dir().glob(f"{PREFIX}*.desktop"):
        exe = None
        try:
            for line in path.read_text().splitlines():
                if line.startswith("Exec="):
                    exe = line.split("=", 1)[1].split()[0]
                    break
        except OSError:
            continue
        if exe and not Path(exe).exists():
            try:
                path.unlink()
                removed.append(path)
                if verbose:
                    print(f"removed stale {path} (missing {exe})")
            except OSError:
                pass
    return removed
