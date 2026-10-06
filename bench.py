"""Benchmark screen capture options on this Wayland (KDE Plasma) session.

    .venv/bin/python bench.py [seconds_per_case]

Prints fps / latency for each method, plus a frame checksum so you can see that a
"fast" method is actually capturing pixels (mss is fast but returns XWayland, i.e. black).
"""
import os
import sys
import time

import numpy as np

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0


def _pids_named(name: str) -> set:
    out = set()
    for pid in os.listdir("/proc"):
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() == name:
                    out.add(int(pid))
        except OSError:
            continue
    return out


def measure(name, fn, note=""):
    """Time `fn()` for SECONDS, reporting fps and latency.  fn returns an ndarray or bytes."""
    try:
        first = fn()
    except Exception as e:  # mss raises when $DISPLAY is unset, etc.
        print(f"{name:<28} FAILED: {type(e).__name__}: {e}")
        return None
    lat, n = [], 0
    t_start = time.perf_counter()
    while time.perf_counter() - t_start < SECONDS:
        s = time.perf_counter()
        fn()
        lat.append((time.perf_counter() - s) * 1e3)
        n += 1
    wall = time.perf_counter() - t_start
    lat.sort()
    fps = n / wall
    black = isinstance(first, np.ndarray) and first.size and float(first.mean()) < 1.0
    flag = "  <-- BLACK/EMPTY!" if black else ""
    print(
        f"{name:<28} {fps:7.1f} fps   med {lat[len(lat)//2]:6.1f} ms   "
        f"p95 {lat[int(len(lat)*0.95)]:6.1f} ms   frames {n:5d}{flag}"
        + (f"   ({note})" if note else "")
    )
    return fps


def main():
    print(f"Wayland capture benchmark, {SECONDS:.1f}s per method\n")

    # ---------------------------------------------------------------- baselines
    try:
        import mss

        sct = mss.MSS(with_cursor=False)
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        measure("mss (XWayland)", lambda: np.asarray(sct.grab(mon)),
                f"{mon['width']}x{mon['height']}, via $DISPLAY")
    except Exception as e:
        print(f"{'mss (XWayland)':<28} FAILED: {type(e).__name__}: {e}")

    try:
        from PIL import ImageGrab

        def pil_shot():
            img = ImageGrab.grab(include_layered_windows=True)
            return np.asarray(img if img.mode == "RGB" else img.convert("RGB"))

        before = _pids_named("spectacle")
        measure("PIL.ImageGrab (spectacle)", pil_shot)
        # Pillow shells out to spectacle, which can outlive the call and keep our
        # stdout pipe open; reap the ones we started.
        for pid in _pids_named("spectacle") - before:
            try:
                os.kill(pid, 15)
            except OSError:
                pass
    except Exception as e:
        print(f"{'PIL.ImageGrab':<28} FAILED: {type(e).__name__}: {e}")

    # ---------------------------------------------------------------- kwcapture
    import kwcapture as K

    with K.Capture() as cap:
        print(f"kwcapture: KWin {cap.screen_name} {cap.geometry()[0]}x{cap.geometry()[1]}, "
              f"daemon pid {cap.stats()['pid']}\n")
        measure("kwcapture raw BGRA (view)", lambda: cap.grab())
        measure("kwcapture RGB full res", lambda: cap.shot())
        measure("kwcapture RGB 1280 wide", lambda: cap.shot(width=1280))
        measure("kwcapture RGB 1024 wide", lambda: cap.shot(width=1024))
        measure("kwcapture JPEG 1280", lambda: cap.shot_jpeg(width=1280))
        measure("kwcapture latest (no grab)", lambda: cap.latest(rgb=True),
                "newest published frame")

    # ---------------------------------------------------------- per-window mode
    windows = K.list_windows()
    if not windows:
        print("\n(no windows open, skipping the per-window cases)")
    else:
        biggest = max(windows, key=lambda w: w.width * w.height)
        smallest = min(windows, key=lambda w: w.width * w.height)
        print(f"\n{len(windows)} windows; biggest: {biggest.name!r} [{biggest.app_id}] "
              f"{biggest.width}x{biggest.height}")
        with K.Capture(window=biggest) as wcap:
            measure("kwcapture window raw BGRA", lambda: wcap.grab(),
                    f"{wcap.geometry()[0]}x{wcap.geometry()[1]}")
            measure("kwcapture window RGB", lambda: wcap.shot())
            measure("kwcapture window JPEG", lambda: wcap.shot_jpeg(quality=85))
        if smallest is not biggest:
            print(f"smallest: {smallest.name!r} [{smallest.app_id}] "
                  f"{smallest.width}x{smallest.height}")
            with K.Capture(window=smallest) as wcap:
                measure("kwcapture window raw BGRA", lambda: wcap.grab(),
                        f"{wcap.geometry()[0]}x{wcap.geometry()[1]}")
                measure("kwcapture window JPEG", lambda: wcap.shot_jpeg(quality=85))

    if K.cv2_module() is None:
        print("\nnote: install opencv-python-headless for the fastest resize/encode path")


if __name__ == "__main__":
    main()
