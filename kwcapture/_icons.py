"""Brand icons for the desktop entry this package installs.

The artwork is **generated**, never hand-placed: `logo/` upstream is the source of truth and
`logo/sync_package_icons.py` copies the glyph of the official mark into the package under
`kwcapture/icons/hicolor/<size>/apps/kwcapture.png` (plus the scalable SVG), byte for byte.
Nothing here rasterises or resamples anything, so an installed icon is bit-identical to the
artwork that was reviewed in `logo/icon/contact.png`.

Three decisions worth knowing before you change this file:

* **Why the glyph and not the full mark:** a desktop icon is seen at 16-48 px and often
  masked to a circle or a squircle. `APTURE` is mush below ~64 px (measured,
  `logo/README.md` §8), so small sizes ship the glyph — the *same* drawing with the word
  dropped, not a second logo.
* **Why the name in `Icon=` is resolved when the entry is written, and never hard-coded:**
  installing icons is done by `kwcapture install-desktop` / `setup`, not by the automatic
  first-capture path, so the entry must still look right on a machine where nothing was ever
  installed. A `;` fallback list is *not* the answer — measured: GLib's `get_icon()` and
  KService's `KDesktopFile` both take the whole value as **one** name, so `Icon=kwcapture;x`
  resolves to neither, our own icon included. `pick_icon_name()` therefore asks the themes on
  this machine and writes the single name that exists here (ours, else the first candidate
  that resolves, else the old spec name).
* **Why only `$XDG_DATA_HOME` and never a system dir, and why uninstall is hash-checked:**
  this runs as the user, into a directory other tools own too (Wine's installers put hundreds
  of icons in there). Deleting `.../apps/kwcapture.png` that we did not install would be
  somebody else's icon. So a file is only removed when its sha256 equals ours.

Nothing happens at import time (house rule: `import kwcapture` stays cheap), and a wheel that
somehow lacks the data reports the icons as missing instead of failing.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import struct
import subprocess
from pathlib import Path

ICON_NAME = "kwcapture"
#: the theme we install into: the freedesktop fallback theme, whose index.theme declares
#: every size directory in PNG_SIZES
THEME = "hicolor"

#: Names tried, in order, when our own icon is not installed. **A `;` chain is not a thing**
#: — measured, do not "restore" it: GLib's `DesktopAppInfo.get_icon()` puts the whole value
#: into a GThemedIcon as ONE name (`Icon=kwcapture;x` → names `['kwcapture;x', ...]`), and
#: upstream KService does the same (`m_strIcon = entryMap.take("Icon")`, no parsing). A chain
#: would therefore resolve to nothing on both consumers, including our own icon. So the name
#: is *resolved at install time* by `pick_icon_name()` instead, and the entry always gets one
#: single name that exists on this machine.
FALLBACK_CANDIDATES = (
    "accessories-screenshot-tool",   # Breeze / Breeze-dark (KDE) — the real name
    "applets-screenshooter",         # HighContrast / GTK naming
    "accessories-screenshot",        # the freedesktop *spec* name; absent on real systems,
)                                    # which is what this entry shipped for six releases

#: hicolor directories we ship into — all of these are listed by the system
#: `/usr/share/icons/hicolor/index.theme`, which is what makes a user-dir install findable
PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)

PACKAGE_ICON_ROOT = Path(__file__).resolve().parent / "icons"


# --------------------------------------------------------------------------- shipped data
def _theme_rel(size, kind) -> str:
    """`16x16/apps` (int size) or `scalable/apps` (kind='svg')."""
    return ("scalable" if kind == "svg" else "%dx%d" % (size, size)) + "/apps"


def icon_files(root=None) -> dict:
    """{theme-relative path: Path} of the icon files that ship with the package.

    Paths are relative to an **icons root** (the directory that contains themes, i.e.
    `$XDG_DATA_HOME/icons`), so they carry the theme component: `hicolor/16x16/apps/
    kwcapture.png`. That component is not decoration — a theme directory is addressed by
    name, and `<icons root>/16x16/apps/…` is a directory no icon lookup will ever open. (An
    earlier revision of this module did exactly that, and the only reason it was caught is
    that `theme_has_icon()` looked for the file and could not find it after installing it.)

    `root` overrides the package directory (tests install into a scratch tree). Missing
    files are simply absent from the result — the caller decides whether that is an error.
    """
    base = Path(root) if root is not None else PACKAGE_ICON_ROOT
    want = ["%s/%s/kwcapture.png" % (THEME, _theme_rel(s, "png")) for s in PNG_SIZES]
    want.append("%s/%s/kwcapture.svg" % (THEME, _theme_rel(0, "svg")))
    return {rel: base / rel for rel in want if (base / rel).is_file()}


def icons_available(root=None) -> bool:
    """Is there anything to install at all (a wheel built without package data has nothing)?"""
    return bool(icon_files(root))


def png_has_alpha(path) -> bool:
    """Can this PNG be transparent? Colour type 6 (RGBA), or a palette plus a tRNS chunk.

    Worth checking before installing: a PNG with no alpha in an icon theme paints an opaque
    square behind the mark, which on a dark panel is exactly the white-box mistake that
    `logo/icon/build.sh` documents for Inkscape's `-b none` (logo gotcha 31).
    """
    data = Path(str(path)).read_bytes()
    if len(data) < 26 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    ctype = data[25]
    return ctype == 6 or (ctype == 3 and b"tRNS" in data)


def png_size(path) -> tuple:
    """(width, height) from a PNG's IHDR, stdlib only — no Pillow, no new dependency."""
    with open(str(path), "rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("not a PNG: %s" % path)
    w, h = struct.unpack(">II", head[16:24])
    return int(w), int(h)


# --------------------------------------------------------------------------- where they go
def user_icon_root() -> Path:
    """`$XDG_DATA_HOME/icons` — the only place this module ever writes."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "icons"


def _sha256(path) -> str:
    return hashlib.sha256(Path(str(path)).read_bytes()).hexdigest()


def _write_atomic(dst: Path, data: bytes) -> None:
    """Write via a temp name + rename, so a failure mid-write cannot leave a truncated icon
    where the theme will read it. A seam on purpose: it is what the tests corrupt to show the
    verify-after-write in `install_icons()` actually fires.
    """
    tmp = dst.with_name(dst.name + ".new")
    tmp.write_bytes(data)
    os.replace(str(tmp), str(dst))


def missing_icons(icons_root=None) -> list:
    """Shipped files that are absent *or differ* in the user's icon directory.

    "Differs" counts as missing on purpose: it is what a half-finished install, a manual
    edit or a different kwcapture version looks like, and all three want the same fix
    (`kwcapture install-desktop`).
    """
    root = Path(icons_root) if icons_root is not None else user_icon_root()
    out = []
    for rel, src in sorted(icon_files().items()):
        dst = root / rel
        try:
            if not dst.is_file() or _sha256(dst) != _sha256(src):
                out.append(rel)
        except OSError:
            out.append(rel)
    return out


def icons_installed(icons_root=None) -> bool:
    return bool(icon_files()) and not missing_icons(icons_root)


def status(icons_root=None) -> tuple:
    """(ok, text) for `kwcapture doctor`. `ok` is False when nothing is installed, but this
    is branding: the caller must not count it as a broken capture setup."""
    files = icon_files()
    if not files:
        return False, "brand icons: none shipped with this build (nothing to install)"
    miss = missing_icons(icons_root)
    root = Path(icons_root) if icons_root is not None else user_icon_root()
    if not miss:
        return True, "brand icons: %d files in %s, entry uses `Icon=%s`" % (
            len(files), root, pick_icon_name())
    return False, ("brand icons: %d of %d missing or stale in %s (entry would fall back to "
                   "`Icon=%s`) - run: kwcapture install-desktop") % (
        len(miss), len(files), root, pick_icon_name())


def status_line(icons_root=None) -> str:
    return status(icons_root)[1]


# --------------------------------------------------------------------- resolving an icon name
def theme_roots() -> list:
    """Icon search paths, in the order a theme lookup should try them.

    `$XDG_DATA_HOME/icons` first (ours lives there), then every `$XDG_DATA_DIRS/*/icons`.
    """
    out = [user_icon_root()]
    for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":"):
        if d:
            p = Path(d) / "icons"
            if p.is_dir() and p not in out:
                out.append(p)
    return out


def _kde_theme_name() -> str:
    """The icon theme Plasma/GTK was told to use, or "" when nothing declares one."""
    for cfg in (Path(os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config"))
                / "kdeglobals", Path(os.environ.get("XDG_CONFIG_HOME")
                                     or str(Path.home() / ".config")) / "gtk-3.0" / "settings.ini"):
        try:
            inside = False
            for line in cfg.read_text().splitlines():
                s = line.strip()
                if s.startswith("["):
                    inside = s.lower() in ("[icons]", "[icon theme]")
                elif inside and s.lower().startswith(("theme=", "iconthemename=")):
                    return s.split("=", 1)[1].strip()
        except OSError:
            continue
    return ""


_DIR_CACHE: dict = {}


def _theme_dirs(theme_dir: Path) -> list:
    """The directories a theme declares, from its own `index.theme` (`Directories=`).

    Reading the declaration is not pedantry: **themes do not agree on layout.** hicolor uses
    `<size>/apps/` (so `16x16/apps/`), while Breeze uses `apps/<size>/` (so `apps/48/`) — a
    `*/apps/NAME` glob finds the first and misses the second, which is exactly how
    `accessories-screenshot-tool` looked "missing" on a KDE desktop on the first attempt at
    this code. When there is no index.theme, fall back to both shapes.
    """
    key = str(theme_dir)
    if key in _DIR_CACHE:
        return _DIR_CACHE[key]
    out = []
    try:
        inside = False
        for line in (theme_dir / "index.theme").read_text().splitlines():
            s = line.strip()
            if s.startswith("["):
                inside = s == "[Icon Theme]"
            elif inside and s.lower().startswith("directories="):
                out = [d.strip() for d in s.split("=", 1)[1].split(",") if d.strip()]
                break
    except OSError:
        pass
    if not out:
        out = ["*/apps", "apps/*"]
    _DIR_CACHE[key] = out
    return out


def theme_has_icon(name: str, roots=None) -> bool:
    """Does *some* installed theme provide `name` as an app icon (svg or png)?

    This is the only honest way to answer "will `Icon=` show something": the naming spec
    suggests names, and a suggested name is not an installed file. Measured on this desktop,
    `accessories-screenshot` — what this project's desktop entry carried for six releases —
    resolves in **no** theme, while `accessories-screenshot-tool` (Breeze, `apps/48/`) and
    `applets-screenshooter` (HighContrast, `24x24/apps/`) both do.
    """
    declared = _kde_theme_name()
    for root in (roots or theme_roots()):
        try:
            entries = sorted(p.name for p in root.iterdir() if p.is_dir())
        except OSError:
            continue
        wanted = [declared, THEME, "breeze", "breeze-dark", "Adwaita"]
        ordered = [t for t in wanted if t and t in entries] + [t for t in entries
                                                              if t not in wanted]
        for theme in ordered:
            tdir = root / theme
            for d in _theme_dirs(tdir):
                if "/" not in d or "apps" not in d.split("/"):
                    continue                    # only app icons can match an app name
                for ext in ("svg", "png"):
                    if "*" in d:
                        if list(tdir.glob("%s/%s.%s" % (d, name, ext))):
                            return True
                    elif (tdir / d / ("%s.%s" % (name, ext))).is_file():
                        return True
    return False


def pick_icon_name() -> str:
    """The single name to put in `Icon=`, resolved against the themes on this machine.

    Ours if it resolves, otherwise the first candidate that resolves, otherwise the spec name
    — which is what the entry carried before, so the worst case is exactly the old behaviour
    and never worse.
    """
    if theme_has_icon(ICON_NAME):
        return ICON_NAME
    for cand in FALLBACK_CANDIDATES:
        if theme_has_icon(cand):
            return cand
    return FALLBACK_CANDIDATES[-1]


# --------------------------------------------------------------------------------- install
def refresh_icon_caches(icons_root=None, verbose: bool = False) -> bool:
    """Nudge the icon caches. Optional by design: the themes are read from disk anyway."""
    root = Path(icons_root) if icons_root is not None else user_icon_root()
    theme = root / THEME
    tool = shutil.which("gtk-update-icon-cache") or shutil.which("update-icon-caches")
    if not tool or not theme.is_dir():
        if verbose:
            print("no icon-cache tool found (or no theme dir); KDE reads icons from disk")
        return False
    try:
        subprocess.run([tool, "-q", "-f", str(theme)], capture_output=True, timeout=60)
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def install_icons(root=None, icons_root=None, verbose: bool = False,
                  refresh: bool = True) -> list:
    """Copy the shipped icons into `$XDG_DATA_HOME/icons/hicolor/...`.

    Returns the destination paths it wrote (empty when the build ships no icons, or when
    everything is already in place and identical — the second call is a no-op).

    Two passes, deliberately:

    * **pass 1 validates the sources** — a PNG's IHDR against the size its directory promises,
      and the presence of an alpha channel. The repo has `sync_package_icons.py --check` for
      this and it runs *nowhere* on an installed machine, so a corrupted or hand-edited wheel
      must fail here, and fail before any file is written: a bad package leaves the theme
      exactly as it was rather than half-branded.
    * **pass 2 writes**, through a temp name + `os.replace` (no half-written icon), then
      re-reads what landed and checks bytes and size again. A copy that lands wrong is a bug,
      not a detail — in hicolor the directory name *is* the promise made to every consumer.

    Raises `IOError`/`OSError` on a bad source; callers (`_desktop.install_desktop_file`)
    catch it, because branding must never break capture.
    """
    files = icon_files(root)
    if not files:
        if verbose:
            print("no icons shipped with this build; nothing to install")
        return []
    base = Path(icons_root) if icons_root is not None else user_icon_root()
    # ---- PASS 1: verify every source before writing anything. `logo/sync_package_icons.py
    # --check` proves the repo's copies are right, and it runs nowhere on an installed
    # machine: a wheel with a foreign, wrongly-sized or alpha-less PNG in it must fail here
    # instead of painting an opaque square on somebody's panel. Verifying up front (rather
    # than per file) also means a bad package leaves the theme exactly as it was — no partial
    # install to explain.
    for rel, src in sorted(files.items()):
        declared = rel.split("/")[1]                      # hicolor/<size>/apps/<file>
        if not rel.endswith(".png"):
            continue
        w, h = png_size(src)
        exp = int(declared.split("x")[0])
        if (w, h) != (exp, exp):
            raise IOError("shipped icon %s is %dx%d but %s requires %dx%d"
                          % (rel, w, h, declared, exp, exp))
        if not png_has_alpha(src):
            raise IOError("shipped icon %s has no alpha channel: it would paint an opaque "
                          "square in the theme" % rel)

    # ---- PASS 2: write
    wrote: list = []
    for rel, src in sorted(files.items()):
        dst = base / rel
        want = src.read_bytes()
        if dst.is_file():
            try:
                if _sha256(dst) == hashlib.sha256(want).hexdigest():
                    continue                     # already exactly right: leave mtime alone
                if verbose:
                    print("replacing a different file: %s" % dst)
            except OSError:
                pass
        dst.parent.mkdir(parents=True, exist_ok=True)
        _write_atomic(dst, want)
        # ---- verify what actually landed. Cheap, and the only way to notice a filesystem
        # that reported success and delivered something else. `tests/test_icons.py` patches
        # `_write_atomic` to prove this line is not decoration.
        if dst.read_bytes() != want:
            raise IOError("icon copy does not match the source: %s" % dst)
        if rel.endswith(".png"):
            w, h = png_size(dst)
            declared = dst.parent.parent.name          # hicolor/<size>/apps/<file>
            if declared != "scalable":
                exp = int(declared.split("x")[0])
                if (w, h) != (exp, exp):
                    raise IOError("icon %s is %dx%d but its directory promises %s"
                                  % (dst, w, h, declared))
        wrote.append(dst)
        if verbose:
            print("installed %s" % dst)
    if wrote and refresh:
        refresh_icon_caches(icons_root=base, verbose=verbose)
    return wrote


def uninstall_icons(icons_root=None, ours_only: bool = True, verbose: bool = False) -> list:
    """Remove the icons we installed.

    With `ours_only` (the default) a file is deleted **only if its sha256 matches the file we
    ship** — a `kwcapture.png` that someone else drew, or that a newer/older build left
    behind, stays exactly where it is. Returns what it removed.
    """
    base = Path(icons_root) if icons_root is not None else user_icon_root()
    removed: list = []
    for rel, src in sorted(icon_files().items()):
        dst = base / rel
        if not dst.is_file():
            continue
        if ours_only:
            try:
                if _sha256(dst) != _sha256(src):
                    if verbose:
                        print("kept %s (not our file)" % dst)
                    continue
            except OSError:
                continue
        try:
            dst.unlink()
            removed.append(dst)
            if verbose:
                print("removed %s" % dst)
        except OSError:
            pass
    if removed:
        refresh_icon_caches(icons_root=base, verbose=verbose)
    return removed
