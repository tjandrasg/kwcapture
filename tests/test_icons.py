#!/usr/bin/env python3
"""Tests for the brand icons and the desktop entry's `Icon=` key — no compositor needed.

    python3 tests/test_icons.py
    pytest tests/test_icons.py

Everything writes into a scratch `$XDG_DATA_HOME` (this process' environment, restored on
exit), never into the real `~/.local/share`, and `refresh=False` everywhere so no test pokes
a live KDE service cache.

What is actually being defended here:

  1. **the shipped set is the reviewed artwork** — byte-identical to `logo/icon/`, via
     `logo/sync_package_icons.py --check`, so the desktop icon cannot silently become an old
     render of the mark;
  2. **a PNG's IHDR agrees with the hicolor directory it sits in** — the directory name is
     the promise the theme makes to consumers;
  3. **install/uninstall is honest and safe** — idempotent, detects a *stale* file (not just a
     missing one), and refuses to delete an icon that is not ours. That directory is shared
     with Wine, PlayOnLinux and anything else that writes there;
  4. **the `Icon=` name we emit resolves on the machine we emit it on.** This is the
     regression test for a real bug: the entry shipped `Icon=accessories-screenshot` for six
     releases and that name exists in no theme on the KDE desktop this project targets
     (KDE's name is `accessories-screenshot-tool`). A `;` chain is not a fix either — GLib
     and KService both treat the whole value as one name — so the value is *resolved* at
     write time and these tests assert it resolves.

Like `tests/test_ring_reader.py`, this needs no Wayland session and runs in CI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = Path(__file__).resolve().parent.parent

import kwcapture as K                     # noqa: E402
from kwcapture import _desktop, _icons    # noqa: E402

FAILED: list = []
SKIP: list = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)
    return bool(cond)


def skip(name, why):
    print(f"  [SKIP] {name}  {why}")
    SKIP.append(name)


def png_size(path):
    return _icons.png_size(path)


# --------------------------------------------------------------------- the shipped data
def shipped_section():
    print("== the set that ships inside the package")
    files = _icons.icon_files()
    want = {"%s/%dx%d/apps/kwcapture.png" % (_icons.THEME, n, n) for n in _icons.PNG_SIZES}
    want.add("%s/scalable/apps/kwcapture.svg" % _icons.THEME)
    check("all sizes present", set(files) == want,
          "%d files" % len(files) if set(files) == want else "missing %s" %
          sorted(want - set(files)))
    check("size list is the hicolor set",
          tuple(_icons.PNG_SIZES) == (16, 24, 32, 48, 64, 128, 256, 512),
          str(tuple(_icons.PNG_SIZES)))
    for rel, path in sorted(files.items()):
        declared = rel.split("/")[1]   # <theme>/<size>/apps/<file>
        if declared == "scalable":
            check("svg is non-empty XML", path.stat().st_size > 200 and
                  b"<svg" in path.read_bytes(), "%s" % rel)
            continue
        w, h = png_size(path)
        exp = int(declared.split("x")[0])
        check("%s matches its directory" % rel, (w, h) == (exp, exp), "%dx%d" % (w, h))
        check("%s can be transparent" % rel, _has_alpha(path))
    check("png_size rejects a non-PNG",
          _raises(png_size, str(files["%s/scalable/apps/kwcapture.svg" % _icons.THEME])))


def _has_alpha(path):
    data = path.read_bytes()
    ctype = data[25]
    return ctype == 6 or (ctype == 3 and b"tRNS" in data)


def _raises(fn, *a):
    try:
        fn(*a)
    except Exception:
        return True
    return False


def sync_section():
    print("== the package copy equals the artwork upstream (sync --check)")
    script = REPO / "logo" / "sync_package_icons.py"
    if not script.is_file():
        return skip("sync --check", "logo/ not present (an installed wheel, not the repo)")
    r = subprocess.run([sys.executable, str(script), "--check"],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    check("sync_package_icons.py --check is clean", r.returncode == 0,
          "" if r.returncode == 0 else (out[-1] if out else "no output"))


# -------------------------------------------------------------------------------- install
def _rel(n: int) -> str:
    """theme-relative, exactly as `_icons.icon_files()` spells it — theme component first."""
    return "%s/%dx%d/apps/kwcapture.png" % (_icons.THEME, n, n)


def _at(root: Path, n: int) -> Path:
    return root / _icons.THEME / ("%dx%d" % (n, n)) / "apps" / "kwcapture.png"


def install_section(sandbox: Path):
    print("== install into a scratch XDG_DATA_HOME")
    files = _icons.icon_files()
    n = len(files)
    wrote = _icons.install_icons(icons_root=sandbox, verbose=False, refresh=False)
    check("installs every file", len(wrote) == n, "%d written" % len(wrote))
    check("nothing missing afterwards", _icons.missing_icons(icons_root=sandbox) == [])
    check("icons_installed() agrees", _icons.icons_installed(icons_root=sandbox))
    again = _icons.install_icons(icons_root=sandbox, verbose=False, refresh=False)
    check("second install writes nothing (idempotent)", again == [], "%d written" % len(again))

    # a file that exists but is NOT ours is 'stale', and stale must be repaired
    small_n, big_n = _icons.PNG_SIZES[0], _icons.PNG_SIZES[1]
    one = _at(sandbox, small_n)
    original = one.read_bytes()
    one.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage" * 40)
    miss = _icons.missing_icons(icons_root=sandbox)
    check("a stale file counts as missing", miss == [_rel(small_n)], str(miss))
    _icons.install_icons(icons_root=sandbox, refresh=False)
    check("stale file is repaired to the real artwork", one.read_bytes() == original)

    # wrong-size guard: a 32x32 PNG parked in the 16x16 directory must not survive install
    one.write_bytes(files[_rel(big_n)].read_bytes())
    _icons.install_icons(icons_root=sandbox, refresh=False)
    check("install fixes a wrong-size file in place", png_size(one) == (small_n, small_n),
          str(png_size(one)))


def uninstall_section(sandbox: Path):
    print("== uninstall only ever removes OUR files")
    _icons.install_icons(icons_root=sandbox, refresh=False)
    mine = _at(sandbox, _icons.PNG_SIZES[0])
    theirs = _at(sandbox, _icons.PNG_SIZES[-1])
    source = _icons.icon_files()[_rel(_icons.PNG_SIZES[-1])].read_bytes()
    theirs.write_bytes(b"\x89PNG\r\n\x1a\n" + b"someone else's icon" * 30)
    removed = _icons.uninstall_icons(icons_root=sandbox, verbose=False)
    check("our files removed", len(removed) == len(_icons.icon_files()) - 1,
          "%d removed" % len(removed))
    check("a foreign kwcapture.png survives uninstall", theirs.is_file(),
          "the one thing that must never happen: deleting another tool's icon")
    check("removal left ours gone", not mine.is_file())
    _icons.install_icons(icons_root=sandbox, refresh=False)
    check("re-install repairs the tree", _icons.icons_installed(icons_root=sandbox))
    removed = _icons.uninstall_icons(icons_root=sandbox, ours_only=False)
    check("ours_only=False is the escape hatch", not theirs.is_file(),
          "%d removed" % len(removed))
    _icons.install_icons(icons_root=sandbox, refresh=False)
    assert theirs.read_bytes() == source


# --------------------------------------------------------------------- the desktop entry
def _helper(tmp: Path) -> Path:
    exe = tmp / "kwcapture-helper"
    exe.write_bytes(b"#!/bin/sh\nexit 0\n")
    exe.chmod(0o755)
    return exe


def entry_section(sandbox: Path):
    print("== the desktop entry: authorisation intact, Icon resolves")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-desk-"))
    exe = _helper(tmp)
    try:
        path = _desktop.install_desktop_file(exe, refresh=False, with_icons=True)
        body = path.read_text()
        check("entry written", path.is_file(), path.name)
        check("authorisation keys intact: Exec=", f"Exec={exe.resolve()}" in body)
        check("authorisation keys intact: interface",
              _desktop.INTERFACE in body and "X-KDE-DBUS-Restricted-Interfaces" in body)
        check("entry is hidden from the app menu", "NoDisplay=true" in body)
        check("is_installed() accepts what we wrote", _desktop.is_installed(exe))
        icon = [ln.split("=", 1)[1] for ln in body.splitlines()
                if ln.startswith("Icon=")][0]
        check("Icon= carries ONE name", ";" not in icon and "," not in icon, icon)
        check("Icon= is our icon once installed", icon == _icons.ICON_NAME, icon)
        check("and that name resolves in a theme", _icons.theme_has_icon(icon))
        check("the entry's own icon file is the shipped one",
              _icons.icons_installed(icons_root=sandbox / "icons"))
        tag = _desktop.tag_for(exe)
        check("the auth key is still the exe path hash (KWin depends on it)",
              tag == _desktop.tag_for(str(exe.resolve())) and len(tag) == 10, tag)

        # The automatic first-Capture path, in a HOME OF ITS OWN with no icons anywhere: one
        # file, no icon installed, and still an Icon= name this machine can resolve. The fresh
        # XDG_DATA_HOME is the point — reusing the sandbox above would let `kwcapture` resolve
        # from the previous install and the check would pass for the wrong reason.
        tmp2 = Path(tempfile.mkdtemp(prefix="kwc-desk2-"))
        saved = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = str(tmp2)
        try:
            (tmp2 / "bin").mkdir(parents=True, exist_ok=True)
            exe2 = _helper(tmp2 / "bin")
            _desktop.install_desktop_file(exe2, refresh=False)      # with_icons defaults False
            body2 = _desktop.desktop_path(exe2).read_text()
            check("auto path still authorises", _desktop.is_installed(exe2))
            check("auto path installs no icons (the 'one file' promise)",
                  not _at(tmp2 / "icons", _icons.PNG_SIZES[0]).exists())
            icon2 = [ln.split("=", 1)[1] for ln in body2.splitlines()
                     if ln.startswith("Icon=")][0]
            any_resolves = any(_icons.theme_has_icon(c) for c in _icons.FALLBACK_CANDIDATES)
            if any_resolves:
                check("auto path picks a name that resolves here", _icons.theme_has_icon(icon2),
                      icon2)
                check("auto path does not claim our icon when nothing installed it",
                      icon2 != _icons.ICON_NAME, icon2)
                check("and prefers a name that exists over the dangling spec name",
                      icon2 != "accessories-screenshot"
                      or not _icons.theme_has_icon("accessories-screenshot-tool"), icon2)
            else:
                skip("auto path picks a resolvable name",
                     "no theme on this machine provides any candidate (CI container?)")
        finally:
            if saved is None:
                os.environ.pop("XDG_DATA_HOME", None)
            else:
                os.environ["XDG_DATA_HOME"] = saved
        # the old bug, stated positively: the spec name alone was never checked to exist
        check("the spec name is last, not first, in the candidate list",
              _icons.FALLBACK_CANDIDATES[-1] == "accessories-screenshot")
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
        shutil.rmtree(str(tmp2), ignore_errors=True)


def refresh_section():
    """`refresh_entries()` fixes the entries this machine already has — and only ours.

    A machine that ran kwcapture from three environments has three entries keyed by three
    helper binaries; installing from one fixes one. That is how two of the three entries on the
    developer's desktop were left pointing at the dangling icon after the fix shipped.
    """
    print("== refreshing the entries that already exist")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-refresh-"))
    apps = Path(os.environ["XDG_DATA_HOME"]) / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    try:
        exes = []
        for i in range(2):
            e = tmp / ("helper-%d" % i)
            e.write_bytes(b"#!/bin/sh\n")
            e.chmod(0o755)
            exes.append(e)
            p = _desktop.desktop_path(e)
            p.write_text("[Desktop Entry]\nType=Application\nName=KWin Capture\n"
                         "Exec=%s\nIcon=accessories-screenshot\nTerminal=false\n"
                         "NoDisplay=true\nX-KDE-DBUS-Restricted-Interfaces=%s\n"
                         % (e, _desktop.INTERFACE))
        names_before = sorted(p.name for p in apps.glob("%s*.desktop" % _desktop.PREFIX))
        # somebody else's file that must not be touched
        foreign = apps / "com.example.other.desktop"
        foreign.write_text("[Desktop Entry]\nType=Application\nName=Other\n"
                           "Exec=/bin/true\nIcon=accessories-screenshot\n")

        changed = _desktop.refresh_entries()
        check("both of our stale entries were rewritten", len(changed) == 2,
              "%d changed" % len(changed))
        for e in exes:
            p = _desktop.desktop_path(e)
            body = p.read_text()
            icon = [ln.split("=", 1)[1] for ln in body.splitlines()
                    if ln.startswith("Icon=")][0]
            check("entry for %s: Icon resolved" % e.name,
                  _icons.theme_has_icon(icon) and icon != "accessories-screenshot", icon)
            check("entry for %s: Exec preserved (the KWin auth key)" % e.name,
                  f"Exec={e.resolve()}" in body)
            check("entry for %s: still authorises" % e.name, _desktop.is_installed(e))
        names_after = sorted(p.name for p in apps.glob("%s*.desktop" % _desktop.PREFIX))
        check("no entry was renamed (auth keys stable)", names_before == names_after,
              str(names_after))
        check("a foreign .desktop is untouched",
              foreign.is_file() and "Icon=accessories-screenshot" in foreign.read_text())
        check("and a second run changes nothing (converged)", _desktop.refresh_entries() == [])
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
        shutil.rmtree(str(apps), ignore_errors=True)


def validate_section():
    print("== desktop-file-validate, if installed")
    tool = shutil.which("desktop-file-validate")
    if not tool:
        return skip("desktop-file-validate", "tool not installed")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-desk3-"))
    exe = _helper(tmp)
    try:
        path = _desktop.install_desktop_file(exe, refresh=False, with_icons=True)
        r = subprocess.run([tool, str(path)], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        check("validator is silent", r.returncode == 0, out.splitlines()[0] if out else "")
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


# ------------------------------------------------------------------------- house rules
def make_png(w: int, h: int, colour_type: int = 6) -> bytes:
    """A valid PNG with no alpha when colour_type == 2, with alpha when 6. Stdlib only, so
    the test suite still does not need Pillow (which is an *optional* dependency here)."""
    import struct
    import zlib
    ch = 3 if colour_type == 2 else 4
    raw = b"".join(b"\x00" + bytes([0, 172, 78, 255][:ch]) * w for _ in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, colour_type, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def sources_section():
    """A bad *package* must be refused, and refused without touching the theme.

    `logo/sync_package_icons.py --check` guards the repo; it runs nowhere on an installed
    machine. So `install_icons()` validates its own sources — the only thing standing between
    a corrupted or hand-edited wheel and an opaque white square on the user's panel.
    """
    print("== a corrupted package is refused before anything is written")
    check("shipped PNGs have alpha", all(_icons.png_has_alpha(p)
                                         for r, p in _icons.icon_files().items()
                                         if r.endswith(".png")))
    tmp = Path(tempfile.mkdtemp(prefix="kwc-png-"))
    rgb = tmp / "rgb.png"
    rgb.write_bytes(make_png(16, 16, colour_type=2))          # 8-bit RGB, no alpha at all
    check("a crafted no-alpha PNG is detected", not _icons.png_has_alpha(rgb))
    try:
        small = _icons.PNG_SIZES[0]
        for label, mutate in (("no alpha", make_png(small, small, 2)),
                              ("wrong size", make_png(64, 64, 6))):
            pkg = tmp / ("pkg-" + label.replace(" ", "-"))
            for rel, src in _icons.icon_files().items():       # copy the real set…
                dst = pkg / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            (pkg / _rel(small)).write_bytes(mutate)            # …then corrupt one file
            target = tmp / ("theme-" + label.replace(" ", "-"))
            raised = ""
            try:
                _icons.install_icons(root=pkg, icons_root=target, refresh=False)
            except (IOError, OSError) as e:
                raised = str(e)
            check("install refuses a source with %s" % label, bool(raised),
                  raised.split("\n")[0][:78])
            check("…and wrote nothing to the theme (%s)" % label,
                  not target.exists() or not any(target.rglob("*")),
                  "%d files" % (0 if not target.exists() else len(list(target.rglob("*")))))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def generator_section():
    """`logo/sync_package_icons.py` must refuse bad artwork — and refuse *without* writing.

    Run against a scratch `--src`/`--dest` (the flags exist for exactly this), so the real
    trees are never touched. The interesting part is not the exit code but the state of the
    destination afterwards: a generator that validates per-file leaves a half-synced package
    behind, which is the worst of both worlds — a build that fails and an icons/ tree that no
    longer matches any artwork.
    """
    print("== the generator refuses bad artwork and leaves the tree alone")
    script = REPO / "logo" / "sync_package_icons.py"
    artwork = REPO / "logo" / "icon"
    if not (script.is_file() and artwork.is_dir()):
        return skip("generator validation", "logo/ not present (installed wheel)")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-gen-"))
    src, dest = tmp / "src", tmp / "dest"
    src.mkdir()
    try:
        for n in _icons.PNG_SIZES:
            shutil.copyfile(str(artwork / ("glyph-%d.png" % n)), str(src / ("glyph-%d.png" % n)))
        shutil.copyfile(str(artwork / "kwcapture-mark-mono.svg"),
                        str(src / "kwcapture-mark-mono.svg"))

        def run():
            return subprocess.run([sys.executable, str(script), "--src", str(src),
                                   "--dest", str(dest)], capture_output=True, text=True)

        r = run()
        check("a clean set syncs into a scratch dest", r.returncode == 0,
              r.stdout.strip().splitlines()[0] if r.stdout else "")
        good = (dest / _icons.THEME / "16x16" / "apps" / "kwcapture.png")
        check("the SVG is copied too",
              (dest / _icons.THEME / "scalable" / "apps" / "kwcapture.svg").is_file())
        check("COPYING.md was generated next to them", (dest / "COPYING.md").is_file())
        before = good.read_bytes() if good.is_file() else b""

        (src / ("glyph-%d.png" % _icons.PNG_SIZES[0])).write_bytes(
            make_png(_icons.PNG_SIZES[0], _icons.PNG_SIZES[0], colour_type=2))
        r = run()
        out = r.stdout + r.stderr
        check("a no-alpha render is refused", r.returncode == 1 and "alpha" in out,
              out.strip().splitlines()[-1][:74] if out.strip() else "")
        check("…and the destination is untouched", good.read_bytes() == before)

        (src / ("glyph-%d.png" % _icons.PNG_SIZES[0])).write_bytes(
            (artwork / ("glyph-%d.png" % _icons.PNG_SIZES[0])).read_bytes())
        big = _icons.PNG_SIZES[-1]
        (src / ("glyph-%d.png" % big)).write_bytes(make_png(32, 32, 6))   # wrong size
        r = run()
        out = r.stdout + r.stderr
        check("a wrongly-sized render is refused", r.returncode == 1 and "expected" in out,
              out.strip().splitlines()[-1][:74] if out.strip() else "")
        check("…again with nothing written", good.read_bytes() == before)

        r = subprocess.run([sys.executable, str(script), "--check", "--src", str(artwork),
                            "--dest", str(REPO / "kwcapture" / "icons")],
                           capture_output=True, text=True)
        check("--check on the real trees is clean", r.returncode == 0,
              r.stdout.strip().splitlines()[0] if r.stdout else "")
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def unwritable_section():
    """When the theme directory cannot be written, the install must be loud and leave nothing.

    The read-back comparison in `install_icons()` (`dst.read_bytes() != want`) guards against
    a filesystem that reports success and delivers something else — a condition you cannot
    arrange without fault injection, so this test covers the adjacent, reachable one: the write
    itself failing. What it insists on is that the failure *propagates* (branding must never
    half-happen) and that the temp-name dance leaves no `kwcapture.png.new` debris in a
    directory shared with other tools' icons.
    """
    print("== an unwritable theme directory fails loudly, and leaves no debris")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-ro-"))
    target = tmp / "icons"
    # Root ignores the mode bits, so an unwritable directory cannot be arranged in a container
    # running as uid 0. Saying so is the honest option; "passing" by writing successfully would
    # report a covered rule that nothing just tested (logo/AGENTS.md gotcha 30).
    as_root = hasattr(os, "geteuid") and os.geteuid() == 0
    try:
        (target / _icons.THEME / "16x16" / "apps").mkdir(parents=True)
        if as_root:
            skip("unwritable theme directory",
                 "running as root: chmod 0500 does not refuse a write, so there is nothing to "
                 "propagate")
        else:
            os.chmod(str(target / _icons.THEME / "16x16" / "apps"), 0o500)   # r-x: no writes
            raised = ""
            try:
                _icons.install_icons(icons_root=target, refresh=False)
            except (IOError, OSError) as e:
                raised = "%s" % type(e).__name__
            check("install propagates a write failure", bool(raised), raised)
            debris = list((target / _icons.THEME / "16x16" / "apps").glob("*.new"))
            check("no half-written *.new files left behind", debris == [], str(debris))
    finally:
        for d in (target / _icons.THEME / "16x16" / "apps",):
            try:
                os.chmod(str(d), 0o755)
            except OSError:
                pass
        shutil.rmtree(str(tmp), ignore_errors=True)


def verify_after_write_section():
    """The verify-after-write in `install_icons()` must fire when a write lies.

    `install_icons()` re-reads every file it wrote and compares bytes. That is unfalsifiable
    against an honest filesystem, so the seam `_write_atomic()` is patched to deliver something
    else — the way to prove the comparison is a check and not a comment.
    """
    print("== install re-reads what it wrote")
    tmp = Path(tempfile.mkdtemp(prefix="kwc-lie-"))
    target = tmp / "icons"
    real = _icons._write_atomic
    try:
        def lying_write(dst, data):
            # Flip a byte *inside the IDAT*: the signature, IHDR and colour type stay valid,
            # so nothing else in install_icons() can notice — only the read-back comparison.
            # (Corrupting the header instead would let the IHDR check pass this test for the
            # wrong reason, which is exactly what an earlier revision of this test did.)
            bad = bytearray(data)
            bad[len(bad) // 2] ^= 0xFF
            real(dst, bytes(bad))
        _icons._write_atomic = lying_write
        raised = ""
        try:
            _icons.install_icons(icons_root=target, refresh=False)
        except (IOError, OSError) as e:
            raised = str(e)
        check("install notices a write that did not deliver the bytes",
              "does not match" in raised, raised[:70])
        check("the corrupted file is not reported as installed",
              not _icons.icons_installed(icons_root=target))
    finally:
        _icons._write_atomic = real
        shutil.rmtree(str(tmp), ignore_errors=True)
    # and with the real writer restored, the same target installs cleanly
    tmp2 = Path(tempfile.mkdtemp(prefix="kwc-honest-"))
    try:
        _icons.install_icons(icons_root=tmp2 / "icons", refresh=False)
        check("restored writer: the same install succeeds",
              _icons.icons_installed(icons_root=tmp2 / "icons"))
    finally:
        shutil.rmtree(str(tmp2), ignore_errors=True)


def resolution_section():
    """`theme_has_icon()` against an independent oracle: `find`, not our own globbing.

    This exists because the first version of `theme_has_icon()` globbed `*/apps/NAME.ext`,
    which is the hicolor layout — and Breeze stores icons as `apps/<size>/NAME.svg`. So it
    reported KDE's own screenshot icon as missing on a KDE desktop. An oracle that does not
    share the assumption is the only way to catch that class of bug.
    """
    print("== icon-name resolution vs an independent oracle (`find`)")
    roots = [str(r) for r in _icons.theme_roots() if r.is_dir()]
    if not roots:
        return skip("resolution oracle", "no icon roots on this machine")

    def oracle(name):
        """True if any theme provides `name` as an app icon, decided by find(1)."""
        for r in roots:
            r2 = subprocess.run(["find", r, "-name", name + ".svg", "-o",
                                 "-name", name + ".png"],
                                capture_output=True, text=True)
            for line in r2.stdout.split("\n"):
                if line and "/apps/" in line:
                    return True
        return False

    # (the sandbox's XDG_DATA_HOME has our icons installed at this point in the run)
    ours = _icons.theme_has_icon(_icons.ICON_NAME)
    check("oracle agrees our own icon resolves once installed", ours == oracle(_icons.ICON_NAME),
          "ours=%s find=%s" % (ours, oracle(_icons.ICON_NAME)))
    for name in _icons.FALLBACK_CANDIDATES:
        mine, theirs = _icons.theme_has_icon(name), oracle(name)
        check("theme_has_icon(%s) agrees with find" % name, mine == theirs,
              "ours=%s find=%s" % (mine, theirs))
    check("a name nobody has is reported absent",
          not _icons.theme_has_icon("kwcapture-definitely-not-an-icon")
          and not oracle("kwcapture-definitely-not-an-icon"))
    # and the pick must be the first candidate that really exists, not a hard-coded guess
    first_real = next((c for c in _icons.FALLBACK_CANDIDATES if oracle(c)), None)
    saved = os.environ.get("XDG_DATA_HOME")
    empty = Path(tempfile.mkdtemp(prefix="kwc-empty-"))
    os.environ["XDG_DATA_HOME"] = str(empty)              # pretend our icons are not installed
    try:
        pick = _icons.pick_icon_name()
        if first_real is None:
            skip("pick_icon_name() equals the first real candidate",
                 "no candidate resolves on this machine")
        else:
            check("pick_icon_name() picks the first candidate that exists", pick == first_real,
                  "picked %s, find says first real is %s" % (pick, first_real))
        check("the spec name is only ever the last resort",
              pick != "accessories-screenshot" or first_real == "accessories-screenshot",
              "this is the six-release bug: the spec name was the only name")
    finally:
        if saved is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = saved
        shutil.rmtree(str(empty), ignore_errors=True)


def deps_section():
    print("== house rules: no new dependency, nothing at import time")
    src = (REPO / "kwcapture" / "_icons.py").read_text()
    mods = set()
    for line in src.splitlines():
        s = line.strip()
        if s.startswith("import "):
            mods.update(p.strip().split(" ")[0] for p in s[len("import "):].split(","))
        elif s.startswith("from ") and " import " in s and not s.startswith("from ."):
            mods.add(s.split(" ")[1].split(".")[0])
    stdlib = {"hashlib", "os", "shutil", "struct", "subprocess", "pathlib",
              "__future__"}                                        # from __future__ import annotations
    check("_icons.py imports stdlib only", mods <= stdlib,
          "extra: %s" % sorted(mods - stdlib))
    check("no PIL/OpenCV/numpy reference in the icon path",
          not any(m in mods for m in ("PIL", "numpy", "cv2")))
    check("icons_available() works without touching the user's home",
          isinstance(_icons.icons_available(), bool))


def main() -> int:
    print("kwcapture %s brand icons / desktop entry (no compositor needed)" % K.__version__)
    saved_xdg = os.environ.get("XDG_DATA_HOME")
    sandbox = Path(tempfile.mkdtemp(prefix="kwc-icons-"))
    os.environ["XDG_DATA_HOME"] = str(sandbox)
    # install_icons(icons_root=...) takes the *icons* dir itself, which is what
    # user_icon_root() derives from XDG_DATA_HOME — pass the same shape the runtime would use
    icons_root = sandbox / "icons"
    try:
        shipped_section()
        sync_section()
        install_section(icons_root)
        uninstall_section(icons_root)
        entry_section(sandbox)
        refresh_section()
        validate_section()
        sources_section()
        unwritable_section()
        verify_after_write_section()
        generator_section()
        resolution_section()
        deps_section()
    finally:
        if saved_xdg is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = saved_xdg
        shutil.rmtree(str(sandbox), ignore_errors=True)
    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print(f"RESULT: all icon tests passed ({len(SKIP)} skipped)")
    return 0


def test_icons():
    """pytest entry point."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
