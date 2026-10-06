"""`kwcapture` command line interface.

    kwcapture doctor               is everything in place?  (also: kwcapture setup)
    kwcapture setup                build the helper + authorise it with KWin
    kwcapture screens              list outputs
    kwcapture grab [options]       save a frame (png / jpg / raw bgra)
    kwcapture demo [options]       grab a few frames and print latency numbers
    kwcapture bench [options]      throughput measurement

Run `python -m kwcapture ...` if the console script is not on your PATH.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time
from typing import Optional

from . import (
    Capture,
    CaptureError,
    __version__,
    _desktop,
    _native,
    list_screens,
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

    try:
        with Capture(binary=str(exe), install_desktop=argv.fix) as cap:
            t0 = time.perf_counter()
            frame = cap.grab()
            ms = (time.perf_counter() - t0) * 1e3
            mean = float(frame.mean())
            if mean < 1.0:
                _bad("capture returned an all-black frame")
                problems += 1
            else:
                _ok(f"capture works: {frame.shape[1]}x{frame.shape[0]} in {ms:.1f} ms "
                    f"(grab {cap.stats()['grab_ms']:.1f} ms)")
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
def cmd_screens(argv: argparse.Namespace) -> int:
    for s in list_screens():
        print(f"{s['name']:<10} {s['width']}x{s['height']} @{s['refresh']:.2f}Hz "
              f"pos {s['x']},{s['y']} scale {s['scale']}")
    return 0


def _grab_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--screen", default=None, help="output name, e.g. DP-1")
    p.add_argument("--area", default=None, metavar="X,Y,W,H", help="capture a region")
    p.add_argument("--workspace", action="store_true", help="whole virtual desktop")
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
    return Capture(screen=ns.screen, area=area, workspace=ns.workspace, cursor=ns.cursor,
                   decoration=ns.decoration)


def cmd_grab(argv: argparse.Namespace) -> int:
    with _make_capture(argv) as cap:
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
    p.set_defaults(func=cmd_doctor)

    sub.add_parser("setup", help="build the helper and authorise it with KWin")

    p = sub.add_parser("install-desktop", help="authorise the helper with KWin")
    p.add_argument("--uninstall", action="store_true", help="remove our desktop entries")
    p.set_defaults(func=cmd_install_desktop)

    p = sub.add_parser("screens", help="list outputs")
    p.set_defaults(func=cmd_screens)

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
