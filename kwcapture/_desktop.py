"""KWin authorisation for the capture helper.

`org.kde.KWin.ScreenShot2` answers `Error.NoAuthorized` unless the calling process'
`/proc/<pid>/exe` matches the `Exec=` of a `.desktop` file that lists the interface in
`X-KDE-DBUS-Restricted-Interfaces` (this is how Spectacle is allowed in).  So we drop a
desktop file for our helper into `~/.local/share/applications/` and refresh KService.

KWin matches on the *canonical* executable path, and it keys the desktop file by that
path, so one file per distinct helper binary is written (different virtualenvs each get
their own entry and can coexist).

The entry also carries an icon, and the name in it is **resolved when the file is written**,
not hard-coded — see `_icons.pick_icon_name()`. Why, in three measurements:

* the name this file shipped for six releases, `accessories-screenshot`, resolves in **no
  theme on the desktop it targets** (KDE's real name is `accessories-screenshot-tool`). A
  name from the naming spec is not a name that exists;
* a `;` fallback chain is **not a thing**: GLib puts the whole `Icon=` value into a
  `GThemedIcon` as one name, and upstream KService stores it verbatim
  (`m_strIcon = entryMap.take("Icon")`), so `Icon=a;b` resolves to neither on either;
* so the entry gets exactly one name, chosen by looking at the themes on this machine: ours
  when it is installed (or was just installed by this call), else the first candidate that
  actually resolves, else the old spec name — worst case identical to the old behaviour.

Changing `Icon=` cannot affect authorisation: `is_installed()` matches on `Exec=` and the
interface name, and KWin keys the entry on the resolved executable path — never on its icon.
`tests/test_icons.py` asserts both keys survive, and that the name we emit resolves.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from . import _icons

INTERFACE = "org.kde.KWin.ScreenShot2"
PREFIX = "io.github.kwcapture"

TEMPLATE = """[Desktop Entry]
Type=Application
Name=KWin Capture
GenericName=Screen capture
Comment=Helper process kwcapture uses to capture the screen on KDE Plasma
Exec={exe}
Icon={icon}
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
                         verbose: bool = False, with_icons: bool = False) -> Path:
    """Write (or rewrite) the authorising desktop file for `exe`.

    `with_icons` also installs the brand icons into `$XDG_DATA_HOME/icons/hicolor` (what
    `kwcapture setup` and `kwcapture install-desktop` do). It defaults to **False** so the
    automatic path — the first `Capture()` writing the one file KWin needs — stays exactly
    that: one file. Nothing here fails if the icons cannot be written: the entry then names
    whatever screenshot icon this machine already has (`_icons.pick_icon_name()`).
    """
    exe = Path(exe).resolve()
    path = desktop_path(exe)
    if with_icons:
        # before the "already authorised" early return, or a machine that was authorised
        # by an earlier version would never get the icons
        try:
            _icons.install_icons(verbose=verbose, refresh=refresh)
        except OSError as e:                      # branding must never break capture
            if verbose:
                print("icons not installed: %s" % e)
    # choose the name AFTER the install attempt: if the icons landed, this is `kwcapture`;
    # if not, it is the best name this machine can actually resolve.
    body = TEMPLATE.format(exe=str(exe), interface=INTERFACE, icon=_icons.pick_icon_name())
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


def uninstall(desktop: Path | str | None = None, with_icons: bool = False,
              verbose: bool = False) -> list[Path]:
    """Remove our desktop file(s) — all of them when called without an argument.

    `with_icons` additionally removes the brand icons, and only those whose bytes still match
    what we ship (`_icons.uninstall_icons` refuses to delete somebody else's `kwcapture.png`).
    Default False: a caller who wants the authorisation gone should not silently lose files
    in a directory shared with Wine, PlayOnLinux and whoever else writes there.
    """
    if with_icons:
        _icons.uninstall_icons(verbose=verbose)
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


def refresh_entries(verbose: bool = False) -> list:
    """Rewrite **every** desktop entry we own with the current template.

    Why: entries are keyed by helper binary, and a machine that ran kwcapture from three
    environments has three entries — installing from one of them fixes one of them, and the
    other two keep whatever they were written with (an old `Icon=`, an old interface list).
    Each file's own `Exec=` is preserved, so the KWin auth key (the sha1 of that path) does not
    change; only the cosmetic and interface lines are refreshed. This is the difference between
    "my entry looks right" and "no kwcapture on this machine points at a dangling icon" — on
    this desktop two of three entries were stale until this function existed.
    """
    out: list = []
    icon = _icons.pick_icon_name()
    for path in sorted(applications_dir().glob(f"{PREFIX}*.desktop")):
        try:
            text = path.read_text()
        except OSError:
            continue
        exe = None
        for line in text.splitlines():
            if line.startswith("Exec="):
                exe = line.split("=", 1)[1].split()[0]
                break
        if not exe:
            continue                                  # not ours in full, leave it alone
        body = TEMPLATE.format(exe=str(Path(exe).resolve()), interface=INTERFACE, icon=icon)
        if body != text:
            try:
                path.write_text(body)
                out.append(path)
                if verbose:
                    print("refreshed %s" % path)
            except OSError:
                pass
    return out


def icon_status() -> tuple:
    """`(ok, text)` about the brand icons, for `kwcapture doctor`. Cosmetic: a False `ok`
    never means capture is broken."""
    return _icons.status()


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
