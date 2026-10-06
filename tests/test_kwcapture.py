#!/usr/bin/env python3
"""Functional tests for the kwcapture Python API.

    python tests/test_kwcapture.py           # everything
    python tests/test_kwcapture.py quick   # skip the slow colour-reference check
    pytest tests/                          # same tests, via pytest
"""
import os
import signal
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)
    return bool(cond)


def main():
    quick = "quick" in sys.argv
    print("== discovery ==")
    screens = K.list_screens()
    check("list_screens returns outputs", len(screens) >= 1, str(screens))
    if not screens:
        print("no screens, aborting")
        return 1
    s0 = screens[0]

    print("\n== basic capture ==")
    with K.Capture() as cap:
        w, h = cap.geometry()
        check("geometry matches first output", (w, h) == (s0["width"], s0["height"]), f"{w}x{h}")
        arr = cap.grab()
        check("grab shape", arr.shape == (h, w, 4), str(arr.shape))
        check("grab dtype", arr.dtype == np.uint8)
        check("frame is not black", float(arr.mean()) > 1.0, f"mean={arr.mean():.1f}")
        check("alpha is opaque", int(arr[..., 3].min()) == 255)
        check("views are read-only", not arr.flags.writeable)
        dup = cap.grab(copy=True)
        check("copy=True is writable", dup.flags.writeable)

        seq_before = cap.stats()["seq"]
        latest = cap.latest()
        check("latest() does not advance the sequence", cap.stats()["seq"] == seq_before,
              f"seq={seq_before}")
        check("latest returns same shape", latest.shape == arr.shape)

        st = cap.stats()
        check("stats has plausible timings", 0 < st["grab_ms"] < 1000,
              f"grab={st['grab_ms']:.1f}ms total={st['total_ms']:.1f}ms fmt={st['format']}")

        small = cap.shot(width=640)
        check("shot(width=640) size", small.shape[1] == 640 and small.shape[2] == 3,
              str(small.shape))
        check("shot is contiguous", small.flags["C_CONTIGUOUS"])
        expect_h = round(h * 640 / w)
        check("shot keeps aspect ratio", abs(small.shape[0] - expect_h) <= 1,
              f"{small.shape[0]} vs {expect_h}")

        blob = cap.shot_jpeg(width=640, quality=80)
        check("jpeg magic bytes", blob[:2] == b"\xff\xd8" and blob[-2:] == b"\xff\xd9",
              f"{len(blob)/1024:.0f} KiB")
        png = cap.shot_png(width=640)
        check("png magic bytes", png[:8] == b"\x89PNG\r\n\x1a\n", f"{len(png)/1024:.0f} KiB")

        import io
        from PIL import Image

        img = Image.open(io.BytesIO(blob))
        check("jpeg decodes at requested width", img.size == (640, expect_h), str(img.size))

        print("\n== colour correctness vs an independent capture ==")
        if not quick:
            # Reference is Spectacle via Pillow (~350 ms a pop) and it fails every now and
            # then, so retry a few times and skip rather than fail if it stays broken.
            from PIL import ImageGrab

            done = False
            for attempt in range(4):
                try:
                    ref_img = ImageGrab.grab()
                    if ref_img.mode != "RGB":
                        ref_img = ref_img.convert("RGB")
                    ref = np.asarray(ref_img, dtype=np.int16)
                    ours = np.asarray(cap.shot(), dtype=np.int16)
                    if ref.shape != ours.shape:
                        h2 = min(ref.shape[0], ours.shape[0])
                        w2 = min(ref.shape[1], ours.shape[1])
                        ref, ours = ref[:h2, :w2], ours[:h2, :w2]
                    if float(ref.mean()) < 1.0:  # reference came back black, try again
                        raise ValueError("reference capture is black")
                    mad = float(np.abs(ref - ours).mean())
                    swapped = float(np.abs(ref - ours[:, :, ::-1]).mean())
                    check("RGB channel order correct (not BGR)", mad < max(12.0, swapped),
                          f"MAD={mad:.1f}, MAD if R/B swapped={swapped:.1f}")
                    done = True
                    break
                except Exception as e:
                    if attempt == 3:
                        print(f"  [skip] colour reference unavailable "
                              f"({type(e).__name__}: {e})")
                    time.sleep(0.5)
        else:
            print("  [skip] quick mode")

    print("\n== region / workspace capture ==")
    with K.Capture(area=(0, 0, 640, 360)) as cap:
        check("area capture geometry", cap.geometry() == (640, 360), str(cap.geometry()))
        check("area frame usable", cap.grab().shape == (360, 640, 4))
    with K.Capture(workspace=True) as cap:
        g = cap.geometry()
        check("workspace capture produced a frame", g[0] >= s0["width"] and g[1] >= s0["height"],
              f"{g[0]}x{g[1]}")

    print("\n== two independent instances ==")
    a = K.Capture(shm=K.default_shm_path("t1"))
    b = K.Capture(shm=K.default_shm_path("t2"))
    try:
        check("instance A grabs", a.grab().shape[0] > 0)
        check("instance B grabs", b.grab().shape[0] > 0)
        check("instances have distinct daemons",
              a.stats()["pid"] != b.stats()["pid"],
              f"{a.stats()['pid']} vs {b.stats()['pid']}")
    finally:
        a.close()
        b.close()

    print("\n== failure handling ==")
    cap = K.Capture()
    pid = cap.stats()["pid"]
    os.kill(pid, signal.SIGKILL)
    deadline = time.time() + 5
    while time.time() < deadline and cap.alive:
        time.sleep(0.05)
    check("daemon death is detected", not cap.alive)
    try:
        cap.grab(timeout=1.0)
        check("grab after daemon death raises", False, "no exception raised")
    except K.CaptureError:
        check("grab after daemon death raises CaptureError", True)
    try:
        cap.restart()
        check("restart() recovers", cap.grab().shape[0] > 0, str(cap.geometry()))
    except Exception as e:
        check("restart() recovers", False, f"{type(e).__name__}: {e}")
    cap.close()

    cap = K.Capture(idle_exit=1.0, shm=K.default_shm_path("idle"))
    pid = cap.stats()["pid"]
    time.sleep(2.6)
    gone = not cap.alive
    check("idle_exit reaps an unused daemon", gone, f"pid {pid} alive={cap.alive}")
    cap.close()

    print("\n== throughput sanity ==")
    with K.Capture() as cap:
        r = cap.bench(frames=40)
        check("on-demand fps > 15 at full resolution", r["fps"] > 15,
              f"{r['fps']:.1f} fps, median {r['median_ms']:.1f} ms")
        r720 = cap.bench(frames=40, rgb=True)
        check("rgb path keeps up", r720["fps"] > 15, f"{r720['fps']:.1f} fps")

    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print("RESULT: all tests passed")
    return 0


def test_kwcapture():
    """pytest entry point."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
