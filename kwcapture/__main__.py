"""`kwcapture` command line interface.

    kwcapture doctor               is everything in place?  (also: kwcapture setup)
                                   --allow-black for empty/locked/headless sessions where a
                                   black frame is the correct answer
    kwcapture setup                build the helper + authorise it with KWin
    kwcapture screens              list outputs
    kwcapture windows              list capturable windows (handle, name, app, size)
    kwcapture grab [options]       save a frame (png / jpg / raw bgra), whole screen or
                                   one window (--window HANDLE|NAME, --active-window)
    kwcapture demo [options]       grab a few frames and print latency numbers
    kwcapture bench [options]      throughput measurement

Run `python -m kwcapture ...` if the console script is not on your PATH.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from typing import Optional

from . import (
    Capture,
    CaptureError,
    Window,
    __version__,
    _desktop,
    _native,
    list_monitors,
    list_screens,
    list_windows,
)


def _ok(msg: str) -> None:
    print(f"  \033[32mok\033[0m   {msg}")


def _bad(msg: str) -> None:
    print(f"  \033[31mFAIL\033[0m {msg}")


def _warn(msg: str) -> None:
    print(f"  \033[33mwarn\033[0m {msg}")


# ------------------------------------------------------------------- doctor
def cmd_doctor(argv: argparse.Namespace) -> int:
    print(f"kwcapture {__version__} environment check")
    problems = 0

    wayland = os.environ.get("WAYLAND_DISPLAY")
    if wayland:
        _ok(f"WAYLAND_DISPLAY={wayland}")
    else:
        _bad("WAYLAND_DISPLAY is not set - this must run inside your graphical session")
        problems += 1

    if os.environ.get("XDG_CURRENT_DESKTOP", "").lower().find("kde") >= 0:
        _ok(f"XDG_CURRENT_DESKTOP={os.environ['XDG_CURRENT_DESKTOP']}")
    else:
        _warn(f"XDG_CURRENT_DESKTOP={os.environ.get('XDG_CURRENT_DESKTOP') or 'unset'} "
              f"- kwcapture needs KWin (KDE Plasma); other compositors should use "
              f"ext-image-copy-capture / wlr-screencopy instead")

    bus = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
    if bus:
        _ok("session D-Bus is reachable via DBUS_SESSION_BUS_ADDRESS")
    else:
        _warn("DBUS_SESSION_BUS_ADDRESS unset; will try the default socket path")

    try:
        exe = _native.ensure_binary(allow_build=argv.build, verbose=True)
        _ok(f"helper: {exe}")
    except _native.NativeBuildError as e:
        _bad(f"native helper unavailable: {e}")
        return 1

    if _desktop.is_installed(exe):
        _ok(f"KWin authorisation: {_desktop.desktop_path(exe)}")
    else:
        if argv.fix:
            path = _desktop.install_desktop_file(exe)
            _ok(f"wrote {path}")
        else:
            _warn(f"not authorised yet ({_desktop.desktop_path(exe)} missing) - "
                  f"run: kwcapture install-desktop   (or: kwcapture doctor --fix)")
            problems += 1

    stale = _desktop.prune()
    if stale:
        _warn("removed desktop entries for helper binaries that no longer exist: "
              + ", ".join(p.name for p in stale))

    try:
        screens = list_screens(str(exe))
        if screens:
            _ok("outputs: " + ", ".join(f"{s['name']} {s['width']}x{s['height']}"
                                        f"@{s['refresh']:.0f}Hz" for s in screens))
        else:
            _bad("compositor reported no outputs")
            problems += 1
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        _bad(f"could not list outputs: {e}")
        problems += 1

    window_count: Optional[int] = None
    try:
        windows = list_windows(str(exe))
        window_count = len(windows)
        _ok(f"{len(windows)} capturable window(s): "
            + ", ".join((w.name or w.app_id or "?")[:28] for w in windows[:6])
            + (" …" if len(windows) > 6 else ""))
    except (CaptureError, subprocess.SubprocessError, OSError) as e:
        _warn(f"could not list windows: {e}")

    try:
        with Capture(binary=str(exe), install_desktop=argv.fix) as cap:
            t0 = time.perf_counter()
            frame = cap.grab()
            ms = (time.perf_counter() - t0) * 1e3
            mean = float(frame.mean())
            size = f"{frame.shape[1]}x{frame.shape[0]}"
            timing = f"{size} in {ms:.1f} ms (grab {cap.stats()['grab_ms']:.1f} ms)"
            if mean >= 1.0:
                _ok(f"capture works: {timing}")
            elif argv.allow_black:
                _ok(f"capture works: {timing}, frame is black as expected (--allow-black)")
            elif window_count == 0:
                # Nothing is drawing in this session, so black is what a *correct* capture of
                # an empty desktop looks like: a nested/headless KWin (probe/nested_kwin_test.sh
                # starts one before any client is up), a session that just started, or a plain
                # black wallpaper with no windows open. Say it, do not fail it.
                _warn(f"capture works: {timing}, but the frame is all black and this session "
                      "has 0 capturable windows - nothing is drawing, so that is expected "
                      "(start an app, or pass --allow-black to stay quiet)")
            else:
                # A black frame with windows on screen is not nothing: KWin refused to composite
                # this output, the screen is locked/DPMS-blanked, or the frame is stale.
                _bad(f"capture returned an all-black frame while {window_count} window(s) are "
                     "capturable - is the screen locked or blanked? (not a missing-authorization "
                     "problem: that raises instead of returning black)")
                problems += 1
    except CaptureError as e:
        _bad(f"capture failed: {e}")
        problems += 1

    try:
        import numpy  # noqa: F401

        _ok("numpy installed")
    except ImportError:
        _bad("numpy is required: pip install numpy")
        problems += 1
    if importlib.util.find_spec("cv2") is None:
        _warn("opencv not installed - pip install 'kwcapture[fast]' for ~8x faster "
              "resize/encode")

    print()
    if problems:
        print(f"{problems} thing(s) need attention")
        return 1
    print("everything looks good")
    return 0


# -------------------------------------------------------------------- setup
def cmd_setup(argv: argparse.Namespace) -> int:
    try:
        exe = _native.build_binary(dest=None, verbose=True)
        _ok(f"built {exe}")
    except _native.NativeBuildError as e:
        _bad(str(e))
        return 1
    path = _desktop.install_desktop_file(exe, verbose=True)
    _ok(f"authorised via {path}")
    return 0


def cmd_install_desktop(argv: argparse.Namespace) -> int:
    exe = _native.ensure_binary()
    if argv.uninstall:
        removed = _desktop.uninstall()
        for p in removed:
            print(f"removed {p}")
        if not removed:
            print("nothing to remove")
        return 0
    path = _desktop.install_desktop_file(exe, verbose=True)
    print(f"KWin is now authorised to let {exe} take screenshots")
    print(f"wrote {path}")
    for stale in _desktop.prune(verbose=True):
        print(f"pruned {stale}")
    return 0


# ------------------------------------------------------------------ capture
def cmd_screens(argv: argparse.Namespace) -> int:  # kept: the old, terse output
    for s in list_screens():
        print(f"{s['name']:<10} {s['width']}x{s['height']} @{s['refresh']:.2f}Hz "
              f"pos {s['x']},{s['y']} scale {s['scale']}")
    return 0


def _window_flags(w: Window) -> str:
    return ",".join(n for n, on in (("active", w.active),
                                    ("minimized", w.minimized), ("fullscreen", w.fullscreen),
                                    ("maximized", w.maximized), ("above", w.keep_above),
                                    ("below", w.keep_below),
                                    ("skip-taskbar", w.skip_taskbar)) if on)


def cmd_windows(argv: argparse.Namespace) -> int:
    windows = list_windows(mark_active=not getattr(argv, "no_active", False))
    if getattr(argv, "active_only", False):
        windows = [w for w in windows if w.active]
    if argv.filter:
        needle = argv.filter.lower()
        windows = [w for w in windows
                   if needle in w.name.lower() or needle in w.app_id.lower()
                   or needle in w.desktop_file.lower()]
    if argv.json:
        from dataclasses import asdict

        print(json.dumps([asdict(w) for w in windows], ensure_ascii=False, indent=2))
        return 0
    print(f"{'WINDOW HANDLE (id)':<38}  {'NAME':<44}  {'APP_ID':<26}  "
          f"{'SIZE':>11}  {'POSITION':>12}  FLAGS")
    for w in windows:
        size = f"{w.width}x{w.height}"
        pos = f"{w.x:+d},{w.y:+d}"
        print(f"{w.id:<38}  {(w.name or '')[:44]:<44}  {(w.app_id or '')[:26]:<26}  "
              f"{size:>11}  {pos:>12}  {_window_flags(w)}")
    if not windows:
        print("(no capturable windows: KWin lists normal application windows only, "
              "not panels, overlays or the desktop)")
    return 0


def cmd_monitors(argv: argparse.Namespace) -> int:
    monitors = list_monitors(measure_scale=getattr(argv, "measure_scale", False))
    if argv.filter:
        needle = argv.filter.lower()
        monitors = [m for m in monitors
                    if needle in m.name.lower() or needle in m.make.lower()
                    or needle in m.model.lower()]
    if argv.json:
        from dataclasses import asdict

        print(json.dumps([asdict(m) for m in monitors], ensure_ascii=False, indent=2))
        return 0
    print(f"{'INDEX':<5}  {'ID':<6}  {'NAME':<12}  {'MAKE / MODEL':<24}  {'SIZE (px)':>11}  "
          f"{'SCALE':>6}  {'POSITION':>10}  REFRESH")
    for m in monitors:
        scale = m.effective_scale or m.scale or 1
        print(f"{m.index:<5}  {m.id:<6}  {m.name:<12}  {f'{m.make} {m.model}':<24.24}  "
              f"{f'{m.width}x{m.height}':>11}  {f'x{scale:g}':>6}  "
              f"{f'{m.x},{m.y}':>10}  {m.refresh_hz:.2f} Hz")
    if not monitors:
        print("(no enabled outputs: a connected but disabled monitor cannot be captured; "
              "see `kscreen-doctor -o`)")
    return 0


def _grab_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--monitor", default=None, metavar="NAME|ID",
                   help="capture one monitor by connector name (DP-1), by the "
                        "compositor's id, or by its `kwcapture monitors` index; with it, "
                        "--area is relative to that monitor")
    p.add_argument("--screen", default=None, help="output name, e.g. DP-1")
    p.add_argument("--area", default=None, metavar="X,Y,W,H", help="capture a region")
    p.add_argument("--workspace", action="store_true", help="whole virtual desktop")
    p.add_argument("--window", default=None, metavar="HANDLE|NAME",
                   help="capture one window: a handle from `kwcapture windows`, or a "
                        "window name / app id (must match exactly one window)")
    p.add_argument("--active-window", action="store_true",
                   help="capture the window that currently has focus")
    p.add_argument("--cursor", action="store_true", help="include the mouse cursor")
    p.add_argument("--decoration", action="store_true", help="include decorations/shadows")
    p.add_argument("--width", type=int, default=None, help="downscale to this width")
    p.add_argument("--resample", default="area",
                   choices=["area", "nearest", "bilinear", "bicubic", "lanczos"])


def _make_capture(ns: argparse.Namespace) -> Capture:
    area = None
    if ns.area:
        parts = [int(v) for v in ns.area.split(",")]
        if len(parts) != 4:
            raise SystemExit("--area wants X,Y,W,H")
        area = tuple(parts)
    return Capture(monitor=getattr(ns, "monitor", None), screen=ns.screen, area=area,
                   workspace=ns.workspace, window=ns.window,
                   active_window=ns.active_window, cursor=ns.cursor,
                   decoration=ns.decoration)


def cmd_grab(argv: argparse.Namespace) -> int:
    with _make_capture(argv) as cap:
        target = cap.target
        if target.startswith("window"):
            print(f"capturing window {cap.window_id} ({cap.window_name})")
        elif target == "active-window":
            print("capturing the focused window")
        if (argv.out or "shot").lower().endswith(".bgra") or argv.raw:
            st = cap.stats()
            frame = cap.grab(copy=True)
            data = frame.tobytes()
            target = argv.out or "frame.bgra"
            with open(target, "wb") as f:
                f.write(data)
            print(f"raw BGRA {st['width']}x{st['height']} stride {st['stride']} -> "
                  f"np.frombuffer(...).reshape({st['height']}, {st['stride'] // 4}, 4)")
        else:
            from . import jpeg_bytes, png_bytes

            img = cap.shot(width=argv.width, resample=argv.resample)
            target = argv.out or "shot.png"
            if target.lower().endswith((".jpg", ".jpeg")):
                blob = jpeg_bytes(img, quality=argv.quality)
            else:
                blob = png_bytes(img)
            with open(target, "wb") as f:
                f.write(blob)
            data = blob
        print(f"wrote {target} ({len(data) / 1024:.0f} KiB, "
              f"{cap.stats()['width']}x{cap.stats()['height']}, "
              f"grab {cap.stats()['grab_ms']:.1f} ms)")
    return 0


def cmd_demo(argv: argparse.Namespace) -> int:
    print("outputs:", list_screens())
    with _make_capture(argv) as cap:
        print("first frame:", cap.stats())
        img = cap.shot(width=argv.width)
        print("shot:", img.shape, img.dtype)
        if argv.save:
            with open(argv.save, "wb") as f:
                from . import png_bytes

                f.write(png_bytes(img))
            print("wrote", argv.save)
        r = cap.bench(frames=argv.frames)
        print("bench: {frames} frames, {fps:.1f} fps, median {median_ms:.2f} ms, "
              "p95 {p95_ms:.2f} ms".format(**r))
    return 0


def cmd_bench(argv: argparse.Namespace) -> int:
    with Capture() as cap:
        r = cap.bench(frames=argv.frames, rgb=True)
        print("kwcapture {frames} frames: {fps:.1f} fps | median {median_ms:.1f} ms | "
              "p95 {p95_ms:.1f} ms | min {min_ms:.1f} | max {max_ms:.1f}".format(**r))
    return 0


# --------------------------------------------------------------------- main
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kwcapture", description="Fast screen capture for KDE Plasma on Wayland")
    parser.add_argument("--version", action="version", version=f"kwcapture {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("doctor", help="check the environment")
    p.add_argument("--fix", action="store_true", help="write the authorisation file if needed")
    p.add_argument("--build", action="store_true", help="allow building the helper")
    p.add_argument("--allow-black", action="store_true",
                   help="an all-black frame is fine (empty, locked or headless/nested "
                        "sessions); without it a black frame is only accepted when no window "
                        "is capturable")
    p.set_defaults(func=cmd_doctor)

    sub.add_parser("setup", help="build the helper and authorise it with KWin")

    p = sub.add_parser("install-desktop", help="authorise the helper with KWin")
    p.add_argument("--uninstall", action="store_true", help="remove our desktop entries")
    p.set_defaults(func=cmd_install_desktop)

    p = sub.add_parser("screens", help="list outputs")
    p.set_defaults(func=cmd_screens)

    p = sub.add_parser("monitors", help="list outputs (index, id, name, position, scale)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("-f", "--filter", default=None,
                   help="only monitors whose name/make/model contains this text")
    p.add_argument("--measure-scale", action="store_true",
                   help="also probe each output's real scale (needed for 125%%/150%%; "
                        "costs ~25 ms per monitor)")
    p.set_defaults(func=cmd_monitors)

    p = sub.add_parser("windows", help="list capturable windows (handle + name)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("-f", "--filter", default=None,
                   help="only windows whose name/app id contains this text")
    p.add_argument("-a", "--active-only", action="store_true",
                   help="only the window that has focus")
    p.add_argument("--no-active", action="store_true",
                   help="do not query which window is focused (skips the ~8 ms query)")
    p.set_defaults(func=cmd_windows)

    p = sub.add_parser("grab", help="save one frame")
    p.add_argument("-o", "--out", default=None, help="shot.png / shot.jpg / frame.bgra")
    p.add_argument("--raw", action="store_true", help="write raw BGRA to frame.bgra")
    p.add_argument("--quality", type=int, default=85)
    _grab_options(p)
    p.set_defaults(func=cmd_grab)

    p = sub.add_parser("demo", help="grab a frame, print numbers")
    p.add_argument("--frames", type=int, default=60)
    p.add_argument("--save", default=None)
    _grab_options(p)
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("bench", help="throughput measurement")
    p.add_argument("--frames", type=int, default=120)
    p.set_defaults(func=cmd_bench)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except CaptureError as e:
        print(f"kwcapture: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
