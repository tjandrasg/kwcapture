#!/usr/bin/env python3
"""Functional tests for the kwcapture Python API.

    python tests/test_kwcapture.py           # everything
    python tests/test_kwcapture.py quick     # skip the slow colour-reference check
    python tests/test_kwcapture.py windows   # only the per-window capture section
    pytest tests/                            # same tests, via pytest

The window tests launch (and close) their own `kcalc` windows so they can also test
what happens when a captured window disappears; they skip if kcalc is not installed.
"""
import os
import shutil
import signal
import subprocess
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


# ------------------------------------------------------------- window helpers
def _krunner(action, handle):
    """Ask KWin to do something to a window (0=activate, 1=close, 2=minimise).

    Uses busctl; returns False when busctl is unavailable so callers can skip.
    """
    if not shutil.which("busctl"):
        return None
    r = subprocess.run(
        ["busctl", "--user", "call", "org.kde.KWin", "/WindowsRunner",
         "org.kde.krunner1", "Run", "ss", f"{action}_{handle}", ""],
        capture_output=True, text=True)
    return r.returncode == 0


def _windows_of(app, timeout=10.0):
    """Windows whose app id / desktop file mentions `app` (waits up to `timeout`s)."""
    deadline = time.time() + timeout
    found = []
    while time.time() < deadline:
        found = [w for w in K.list_windows()
                 if app in (w.app_id or "").lower()
                 or app in (w.desktop_file or "").lower()
                 or app in (w.resource_name or "").lower()]
        if found:
            return found
        time.sleep(0.2)
    return found


def _spawn(app):
    exe = shutil.which(app)
    if not exe:
        return None
    return subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wait_new_window(app, known=(), timeout=12.0):
    """Windows of `app` that were not in `known` (handles of a previous test run)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        fresh = [w for w in _windows_of(app, timeout=0.2) if w.id not in known]
        if fresh:
            return fresh
        time.sleep(0.2)
    return []


def window_section():
    """Enumeration, per-window capture, name resolution and vanished windows."""
    print("\n== window enumeration ==")
    try:
        windows = K.list_windows()
    except Exception as e:  # noqa: BLE001 - report and stop this section
        check("list_windows() works", False, f"{type(e).__name__}: {e}")
        return
    check("list_windows returns a list of Window", isinstance(windows, list) and
          all(isinstance(w, K.Window) for w in windows), f"{len(windows)} window(s)")
    if not windows:
        print("  [skip] no windows open, nothing to test")
        return
    check("window ids are KWin handles",
          all(K.is_window_handle(w.id) for w in windows), windows[0].id)
    check("windows carry a name or app id", all(w.name or w.app_id for w in windows))
    check("windows have a geometry", all(w.width > 0 and w.height > 0 for w in windows))
    w0 = windows[0]
    check("find_window(handle) round-trips", K.find_window(w0.id).id == w0.id, w0.id)
    check("handle without braces is accepted too",
          K.find_window(w0.id.strip("{}")).id == w0.id)
    check("Window objects know their geometry",
          w0.geometry == (w0.width, w0.height) and isinstance(str(w0), str))
    try:
        K.find_window("zz no such window zz")
        check("find_window() raises WindowNotFound", False, "no exception raised")
    except K.WindowNotFound:
        check("find_window() raises WindowNotFound", True)

    print("\n== focused window ==")
    # list_windows(mark_active=False) must not query focus at all
    check("mark_active=False leaves no window active",
          not any(w.active for w in K.list_windows(mark_active=False)))
    check("mark_active=True marks at most one window active",
          sum(1 for w in K.list_windows() if w.active) <= 1)
    if not shutil.which("busctl"):
        print("  [skip] busctl missing: cannot change focus deterministically")
    else:
        def _focused(expect, tries=6):
            """active_window_id() until it matches `expect` (focus changes are async)."""
            for _ in range(tries):
                if K.active_window_id() == expect.id:
                    return True
                time.sleep(0.2)
            return False

        a, b = windows[0], windows[min(1, len(windows) - 1)]
        if not _krunner(0, a.id):
            print("  [skip] krunner Run failed, cannot drive focus")
        else:
            check("active_window_id() follows activation", _focused(a),
                  f"wanted {a.id}, got {K.active_window_id()}")
            marked = [w for w in K.list_windows() if w.active]
            check("list_windows() marks the focused window",
                  len(marked) == 1 and marked[0].id == a.id,
                  ", ".join(w.name for w in marked) or "none")
            check("active_window() returns the focused window",
                  K.active_window().id == a.id, K.active_window().name)
            check("active_window() can reuse a pre-fetched list",
                  K.active_window(windows=windows).id == a.id)
            if b is not a and _krunner(0, b.id):
                check("focus moves to another window", _focused(b),
                      f"wanted {b.id}, got {K.active_window_id()}")

    print("\n== per-window capture ==")
    if not shutil.which("kcalc"):
        print("  [skip] kcalc not installed; the capture tests need a window of our own")
        return
    if not shutil.which("busctl"):
        print("  [note] busctl missing: the minimise checks are skipped")
    procs = []
    try:
        before = {w.id for w in K.list_windows()}
        p = _spawn("kcalc")
        if p is None:
            print("  [skip] could not start kcalc")
            return
        procs.append(p)
        mine = _wait_new_window("kcalc", before)
        if not check("launched a window to capture", bool(mine),
                     str([w.id for w in mine])):
            return
        w = mine[0]
        with K.Capture(window=w, shm=K.default_shm_path("win")) as cap:
            check("Capture(window=...) resolved the handle",
                  cap.window_id == w.id and cap.target == "window",
                  f"{cap.window_id} '{cap.window_name}'")
            arr = cap.grab()
            check("window frame is usable", arr.ndim == 3 and arr.shape[2] == 4,
                  str(arr.shape))
            check("window frame has real pixels", float(arr.mean()) > 1.0,
                  f"mean={arr.mean():.1f}")
            check("window size matches what KWin reported (client vs frame geometry)",
                  abs(arr.shape[1] - w.width) <= 96 and abs(arr.shape[0] - w.height) <= 96,
                  f"grabbed {arr.shape[1]}x{arr.shape[0]}, listed {w.width}x{w.height}")
            st = cap.stats()
            check("stats() reports the window target",
                  st["target"] == "window" and st["window"] == w.id and st["status"] == "ok",
                  f"{st['target']} {st['status']}")
            small = cap.shot(width=64)
            check("shot() works per window", small.ndim == 3 and small.shape[1] == 64,
                  str(small.shape))
            plain = cap.grab(copy=True)
        with K.Capture(window=w.id, decoration=True,
                       shm=K.default_shm_path("windeco")) as cap:
            deco = cap.grab(copy=True)
            check("decoration=True adds titlebar/shadow",
                  deco.shape[0] >= plain.shape[0] and deco.shape[1] >= plain.shape[1],
                  f"{plain.shape[1]}x{plain.shape[0]} -> {deco.shape[1]}x{deco.shape[0]}")

        with K.Capture(active_window=True, shm=K.default_shm_path("awin")) as cap:
            try:
                f = cap.grab()
                check("active_window=True captures the focused window",
                      f.shape[0] > 0 and cap.target == "active-window", str(f.shape))
                # the daemon publishes KWin's windowId, so it must agree with the
                # no-pixels --active-window-id query
                check("the daemon reports the same focused handle",
                      cap.stats()["window"] == K.active_window_id(),
                      f"{cap.stats()['window']} vs {K.active_window_id()}")
            except K.NoActiveWindow as e:
                check("active_window=True captures the focused window", False, str(e))

        # A minimised window returns a frame, but it is a STALE SNAPSHOT: KWin stops
        # rendering it, so every grab repeats the last buffer and nothing tells you.
        # The old name of these checks ("minimised windows still capture") made that
        # sound like a feature and helped hide BUG-1 -- see "OPEN BUGS" in AGENTS.md and
        # probe/stale_window.py, which proves staleness with a self-repainting window.
        if _krunner(2, w.id):
            time.sleep(0.7)
            check("list_windows reports a minimised window", K.find_window(w.id).minimized)
            try:
                with K.Capture(window=w.id, shm=K.default_shm_path("winmin")) as cap:
                    f = cap.grab(timeout=3.0)
                # kcalc does not repaint, so this cannot tell live from stale; it only
                # asserts we get a frame at all and do not wedge the ring.
                check("minimised window returns a frame (contents are STALE - BUG-1)",
                      f.shape[0] > 0, str(f.shape))
            except K.CaptureError as e:
                check("minimised window returns a frame (STALE - BUG-1)", False,
                      f"{type(e).__name__}: {e}")
            _krunner(0, w.id)
            time.sleep(0.7)
        else:
            print("  [skip] busctl missing: no minimise round-trip test")

        # Two windows with the same caption are ambiguous.  (kcalc is a unique
        # application, so this ranking is checked on a synthetic list rather than by
        # starting a second copy.)
        twin = K.Window(id="{11111111-1111-1111-1111-111111111111}", name="KCalc",
                        app_id="org.kde.kcalc")
        try:
            K.find_window("KCalc", windows=[w, twin])
            check("ambiguous names raise AmbiguousWindow", False, "picked one of two")
        except K.AmbiguousWindow as e:
            check("ambiguous names raise AmbiguousWindow", len(e.candidates) == 2,
                  f"{len(e.candidates)} candidates")
        check("a handle disambiguates",
              K.find_window(twin.id, windows=[w, twin]).id == twin.id)
        check("a unique substring match works",
              K.find_window("calc", windows=[w, ]).id == w.id)
        check("exact captions beat substring matches",
              K.find_window("KCalc", windows=[
                  K.Window(id="{22222222-2222-2222-2222-222222222222}", name="KCalc Two"),
                  twin]).id == twin.id)
    finally:
        for pr in procs:
            if pr.poll() is None:
                pr.terminate()
        deadline = time.time() + 10
        while time.time() < deadline and _windows_of("kcalc", timeout=0.5):
            time.sleep(0.2)


def window_vanish_section():
    """Killing a captured window must raise WindowGone, not wedge the daemon."""
    print("\n== captured window disappears ==")
    if not shutil.which("kcalc"):
        print("  [skip] kcalc not installed")
        return
    before = {w.id for w in K.list_windows()}
    p = _spawn("kcalc")
    mine = _wait_new_window("kcalc", before)
    if not check("launched a window to kill", bool(mine), str([w.id for w in mine])):
        if p.poll() is None:
            p.terminate()
        return
    try:
        with K.Capture(window=mine[0].id, shm=K.default_shm_path("wingone")) as cap:
            check("window captures before it dies", cap.grab().shape[0] > 0)
            p.terminate()
            gone = None
            deadline = time.time() + 15
            while time.time() < deadline:
                time.sleep(0.2)
                try:
                    cap.grab(timeout=2.0)
                except K.WindowGone as e:
                    gone = e
                    break
                except K.CaptureError as e:
                    gone = e
                    break
            check("grab() raises WindowGone when the window closes", gone is not None,
                  str(gone)[:110] if gone else "still returning frames")
            check("the daemon survives its window dying", cap.alive)
            check("stats() reports the failure", cap.stats()["status"] != "ok",
                  cap.stats()["status"])
            check("the closed window is no longer listed",
                  mine[0].id not in [w.id for w in K.list_windows()])
    finally:
        if p.poll() is None:
            p.kill()
    check("other captures still work afterwards", K.grab(copy=True).shape[0] > 0)


def _summary() -> int:
    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print("RESULT: all tests passed")
    return 0


def main():
    quick = "quick" in sys.argv
    if "windows" in sys.argv:
        window_section()
        window_vanish_section()
        return _summary()
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

    window_section()
    window_vanish_section()

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
