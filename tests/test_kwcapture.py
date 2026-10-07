#!/usr/bin/env python3
"""Functional tests for the kwcapture Python API.

    python tests/test_kwcapture.py           # everything
    python tests/test_kwcapture.py quick     # skip the slow colour-reference check
    python tests/test_kwcapture.py windows   # only the per-window capture section
    pytest tests/                            # same tests, via pytest

The window tests launch (and close) their own `kcalc` windows so they can also test
what happens when a captured window disappears; they skip if kcalc is not installed.
"""
import gc
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
            # KWin lists windows in *logical* px and the frame is device px, so the two
            # agree only after the output's scale (verified live: a window listed
            # 472x466 on a 75% output is grabbed as 354x329).
            ps = cap.pixel_scale
            check("window size matches what KWin reported (client vs frame geometry)",
                  abs(arr.shape[1] - w.width * ps) <= 96
                  and abs(arr.shape[0] - w.height * ps) <= 96,
                  f"grabbed {arr.shape[1]}x{arr.shape[0]}, listed {w.width}x{w.height} "
                  f"x{ps:g}")
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

        # BUG-1: KWin does not render a minimised window, so its frames go stale and the
        # ring gives no sign of it. Capture(stale_check=True) must ask getWindowInfo and
        # flag the result; without it nothing extra is queried and the flag stays False
        # (meaning "unknown", not "fresh").
        if shutil.which("busctl"):
            import warnings as _warn
            try:
                with K.Capture(window=w.id, shm=K.default_shm_path("winstale"),
                               stale_check=True) as cap:
                    cap.grab()
                    check("stale_frame is False while the window is mapped",
                          cap.stale_frame is False and cap.window_minimized is False)
                    if not _krunner(2, w.id):
                        print("  [skip] could not minimise; stale checks skipped")
                    else:
                        time.sleep(1.0)
                        with _warn.catch_warnings(record=True) as caught:
                            _warn.simplefilter("always")
                            s1 = cap.grab(copy=True)
                            time.sleep(0.4)
                            s2 = cap.grab(copy=True)
                        check("stale_check flags a minimised window",
                              cap.stale_frame is True and cap.window_minimized is True)
                        check("going stale warns once",
                              any("STALE" in str(x.message) for x in caught),
                              ", ".join(str(x.message)[:40] for x in caught))
                        check("minimised frames really are byte-identical (why we flag)",
                              bool((s1 == s2).all()))
                        _krunner(0, w.id)
                        time.sleep(1.0)
                        cap.grab()
                        check("stale_frame clears when the window is restored",
                              cap.stale_frame is False)
            except Exception as e:  # noqa: BLE001
                check("stale_check works", False, f"{type(e).__name__}: {e}")
            with K.Capture(window=w.id, shm=K.default_shm_path("winstale2")) as cap2:
                cap2.grab()
                check("stale_check defaults to off",
                      cap2.stale_check is False and cap2.stale_frame is False)

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


def bug_regression_section():
    """Regressions for BUG-2 (sched_yield crash), BUG-3 (fd leak on restart) and BUG-4
    (the zero-copy read path).  The deterministic part of BUG-4 lives in
    tests/test_ring_reader.py, which needs no compositor and runs in CI."""
    import ctypes
    import os as _os

    print("\n== regression: BUG-2 sched_yield ===")
    saved = K._sched_yield
    try:
        K.sched_yield()
        check("sched_yield() uses libc's function when present",
              callable(K._sched_yield) and K._sched_yield is not K._sleep0,
              type(K._sched_yield).__name__)

        class NoSym:  # CDLL succeeds, the symbol lookup does not -> AttributeError
            def __init__(self, *a, **k):
                pass

            def __getattr__(self, name):
                raise AttributeError(name)

        real = ctypes.CDLL
        ctypes.CDLL = NoSym
        try:
            K._sched_yield = None
            K.sched_yield()          # used to propagate AttributeError out of grab()
            check("missing libc symbol falls back instead of crashing",
                  K._sched_yield is K._sleep0)
        finally:
            ctypes.CDLL = real

        K._sched_yield = 0           # the cached-int state that produced the TypeError
        K.sched_yield()
        check("a non-callable cache re-initialises (no 'int' object is not callable)",
              callable(K._sched_yield))
    finally:
        K._sched_yield = saved

    print("\n== regression: BUG-3 fd leak on restart ==")
    def open_fds():
        try:
            return len(_os.listdir("/proc/self/fd"))
        except OSError:
            return -1

    try:
        with K.Capture(shm=K.default_shm_path("fdleak")) as cap:
            cap.grab()
            try:
                cap.window_minimized
                check("window_minimized needs a window target", False, "no exception raised")
            except K.CaptureError:
                check("window_minimized needs a window target", True)
            base = open_fds()
            for _ in range(4):
                cap.restart()
                cap.grab()
            after = open_fds()
            check("restart() does not leak file descriptors",
                  after - base <= 1, f"{base} -> {after} fds over 4 restarts")
    except Exception as e:  # noqa: BLE001
        check("BUG-3 restart regression ran", False, f"{type(e).__name__}: {e}")

    print("\n== regression: BUG-4 zero-copy read path ==")
    try:
        cap = K.Capture(shm=K.default_shm_path("bug4"))
    except Exception as e:  # noqa: BLE001
        check("BUG-4 regression ran", False, f"{type(e).__name__}: {e}")
        return
    try:
        first = cap.grab()
        check("a frame view is read-only without setflags() (RO mapping)",
              not first.flags.writeable)
        old = cap.latest()                       # view we keep across a restart
        old_first = int(old[0, 0, 0])
        cap.restart()
        fresh = cap.grab()
        check("grab works after restart with an outstanding view",
              fresh.shape[0] > 0, str(fresh.shape))
        check("the view from before the restart is still readable",
              old.shape[0] > 0 and int(old[0, 0, 0]) == old_first)
        check("it was not unmapped out from under us",
              old.base is not None)

        # hammer the exact path BUG-4 was reported on (latest + grab, GC pressure) and
        # self-check every frame: wrong shape / wrong dtype / unwritable copy is a failure
        bad = 0
        kept = []
        deadline = time.time() + 3.0
        n = 0
        while time.time() < deadline:
            a = cap.latest(rgb=True)
            if a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8:
                bad += 1
            kept.append(a)
            b = cap.grab(copy=True)
            if b.ndim != 3 or b.shape[2] != 4 or not b.flags.writeable:
                bad += 1
            n += 1
            if n % 20 == 0:
                del kept[:20]
            if n % 200 == 0:
                gc.collect()
        check("latest()/grab() survived a self-checking hammer",
              bad == 0, f"{n:,} iterations, {bad} bad frames, "
                        f"{n / 3.0:,.0f} it/s")

        # the historic trigger is `latest()` at hundreds of thousands of calls/s, which is
        # what BUG-4 was first seen on (probe/corruption_rate.py reproduces it with no
        # kwcapture in sight); a short burst keeps the pattern visible in the suite
        burst = 300_000
        t0 = time.time()
        for i in range(burst):
            v = cap.latest(rgb=True)
            if i % 2000 == 0 and (v.shape[2] != 3 or v.dtype != np.uint8):
                bad += 1
        check("latest(rgb=True) burst clean", bad == 0,
              f"{burst:,} calls in {time.time() - t0:.2f}s "
              f"({burst / max(1e-9, time.time() - t0):,.0f} it/s)")
        st = cap.stats()
        check("stats() and the frame agree on geometry",
              st["width"] == fresh.shape[1] and st["height"] == fresh.shape[0],
              f"{st['width']}x{st['height']}")
        # close() must not pull the mapping out from under a live view
        held = cap.latest()
        held_px = int(held[0, 0, 0])
        cap.close()
        check("a view stays readable after close() (frozen, not unmapped)",
              held.shape[0] > 0 and int(held[0, 0, 0]) == held_px)
        del held
    except Exception as e:  # noqa: BLE001
        check("BUG-4 regression ran", False, f"{type(e).__name__}: {e}")
    finally:
        try:
            cap.close()
        except Exception:
            pass


def _summary() -> int:
    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print("RESULT: all tests passed")
    return 0


def monitor_section():
    """v0.5: monitor enumeration + capture by name or id, on every output that exists."""
    print("\n== monitors: enumeration ==")
    try:
        monitors = K.list_monitors()
    except K.CaptureError as e:
        print(f"  [skip] no monitors reported ({e})")
        return
    check("list_monitors() returns the outputs", len(monitors) >= 1,
          ", ".join(m.name for m in monitors))
    check("every monitor has a name, an int id and a size",
          all(m.name and isinstance(m.id, int) and m.width > 0 and m.height > 0
              for m in monitors),
          str([(m.index, m.id, m.name, m.geometry) for m in monitors]))
    check("index is the position in the returned order",
          [m.index for m in monitors] == list(range(len(monitors))))
    check("enumeration is stable and top-left first (sorted by y, then x)",
          [(m.y, m.x) for m in monitors] == sorted((m.y, m.x) for m in monitors))
    check("position/geometry are tuples",
          all(isinstance(m.position, tuple) and isinstance(m.geometry, tuple)
              for m in monitors),
          str([(m.position, m.geometry) for m in monitors]))
    check("ids are unique", len({m.id for m in monitors}) == len(monitors))

    print("\n== monitors: finding ==")
    m0 = monitors[0]
    check("find by name", K.find_monitor(m0.name, monitors=monitors) is m0, m0.name)
    check("find by compositor id",
          K.find_monitor(m0.id, monitors=monitors).name == m0.name, f"id={m0.id}")
    check("find by enumeration index",
          K.find_monitor(m0.index, monitors=monitors).name == m0.name,
          f"index={m0.index}")
    check("find a Monitor object through unchanged",
          K.find_monitor(m0, monitors=monitors) is m0)
    if len(m0.name) > 2:
        frag = m0.name[:2]
        try:
            got = K.find_monitor(frag, monitors=monitors)
            check("find by substring", got.name == m0.name, f"{frag!r} -> {got.name}")
        except K.AmbiguousMonitor as e:
            # the fragment matches more than one output: refusing to guess is correct
            check("find by substring", len(e.candidates) > 1,
                  f"{frag!r} is ambiguous ({len(e.candidates)} outputs)")
        except K.MonitorNotFound as e:
            check("find by substring", False, str(e)[:70])
    try:
        K.find_monitor("definitely-not-an-output-99", monitors=monitors)
        check("unknown monitor raises MonitorNotFound", False, "no exception")
    except K.MonitorNotFound as e:
        check("unknown monitor raises MonitorNotFound", "available" in str(e), str(e)[:70])
    try:
        K.find_monitor(10 ** 9, monitors=monitors)
        check("unknown id/index raises MonitorNotFound", False, "no exception")
    except K.MonitorNotFound as e:
        check("unknown id/index raises MonitorNotFound", True, str(e)[:70])
    if len(monitors) > 1:
        # "-1" is a substring of DP-1 and HDMI-A-1 alike: must not pick one silently
        shared = next((s for s in ("-1", "-")
                       if sum(1 for m in monitors if s in m.name) > 1), None)
        if shared:
            try:
                K.find_monitor(shared, monitors=monitors)
                check(f"a substring matching several monitors is ambiguous ({shared!r})",
                      False, "picked one silently")
            except K.AmbiguousMonitor as e:
                check(f"a substring matching several monitors is ambiguous ({shared!r})",
                      len(e.candidates) > 1, f"{len(e.candidates)} candidates")

    print("\n== monitors: capture by name and by id, on every output ==")
    for m in monitors:
        for spec in dict(name=m.name, id=m.id).values():
            try:
                with K.Capture(monitor=spec,
                               shm=K.default_shm_path(f"m{m.index}")) as cap:
                    f = cap.grab(copy=True, timeout=10)
                    check(f"Capture(monitor={spec!r}) captures {m.name}",
                          f.shape[:2] == (m.height, m.width),
                          f"{f.shape[1]}x{f.shape[0]} vs {m.width}x{m.height}")
                    check(f"  {m.name}: reports its scale and Monitor", cap.scale > 0
                          and cap.monitor is not None and cap.monitor.name == m.name,
                          f"scale={cap.scale}")
            except Exception as e:  # noqa: BLE001
                check(f"Capture(monitor={spec!r}) captures {m.name}", False,
                      f"{type(e).__name__}: {e}")

    print("\n== monitors: area is relative to the monitor ==")
    m = monitors[-1]
    try:
        with K.Capture(monitor=m, area=(0, 0, 320, 200),
                       shm=K.default_shm_path("marea")) as cap:
            f = cap.grab(copy=True, timeout=10)
            # `area` is logical; the image comes back in device pixels, so under fractional
            # scaling the frame is area * area_scale, not area.
            a = cap.area_scale
            ew, eh = round(320 * a), round(200 * a)
            check("monitor-relative area captures that region", f.shape == (eh, ew, 4),
                  f"{f.shape[1]}x{f.shape[0]} expected {ew}x{eh} (area x{a:g})")
            check("and reports the region's geometry, not the monitor's",
                  cap.geometry() == (ew, eh), f"{cap.geometry()} vs ({ew},{eh})")
    except Exception as e:  # noqa: BLE001
        check("monitor-relative area gives that size", False, f"{type(e).__name__}: {e}")

    print("\n== monitors: scaling ==")
    try:
        s = K.measure_output_scale(m.name)
        check("measure_output_scale gives a sane scale", 0.05 <= s <= 16.0, f"x{s:g}")
        # wl_output carries only an integer hint (ceil), so it can be compared to only when
        # the real scale is a whole number
        check("it agrees with wl_output when the scale is a whole number",
              abs(s - round(s)) > 0.01 or abs(s - (m.scale or 1)) < 0.01,
              f"measured x{s:g} vs wl_output x{m.scale}")
        with K.Capture(monitor=m.name, shm=K.default_shm_path("mscale")) as cap:
            cap.grab(copy=True, timeout=10)
            check(f"{m.name}: measured scale == the scale KWin applies to frames",
                  abs(s - cap.scale) < 0.01, f"measured x{s:g} vs frame x{cap.scale:g}")
    except Exception as e:  # noqa: BLE001
        check("measure_output_scale gives a sane scale", False, f"{type(e).__name__}: {e}")
    measured = K.list_monitors(measure_scale=True)
    check("list_monitors(measure_scale=True) fills effective_scale",
          all(x.effective_scale for x in measured),
          str([x.effective_scale for x in measured]))
    check("logical_geometry == geometry / scale for every output",
          all(x.logical_geometry[0] >= 1 and abs(x.logical_geometry[0] * x.effective_scale
                                                  - x.width) <= 2 for x in measured),
          str([(x.name, x.geometry, x.logical_geometry) for x in measured]))
    if len(measured) > 1:
        # The layout itself proves the scale: positions are logical and neighbours abut
        # exactly, so the next monitor's x == the left one's logical right edge.
        left, right = measured[0], measured[1]
        want = left.x + left.width / left.effective_scale
        check("neighbour's logical x == left monitor's logical right edge (proves scale)",
              abs(right.x - want) <= 2,
              f"{right.name}.x={right.x} vs {left.name} logical edge {want:.1f}")
    one = measured[0]
    back = one.to_logical(*one.to_physical(100, 60))
    check("to_physical / to_logical round-trip", abs(back[0] - 100) < 1.5
          and abs(back[1] - 60) < 1.5, str(back))
    try:
        am = K.active_monitor()
        check("active_monitor() names one of the outputs",
              any(am.name == x.name for x in monitors), am.name)
    except Exception as e:  # noqa: BLE001
        check("active_monitor() names one of the outputs", False, f"{type(e).__name__}: {e}")

    print("\n== monitors: bad arguments are caught before the daemon is started ==")
    for name, kwargs, exc in (
        ("unknown monitor", dict(monitor="VGA-77"), K.MonitorNotFound),
        ("monitor= with screen=", dict(monitor=monitors[0].name, screen=monitors[0].name),
         K.CaptureError),
        ("bad area_in", dict(monitor=monitors[0].name, area=(0, 0, 8, 8), area_in="world"),
         K.CaptureError),
        ("physical area without a monitor", dict(area=(0, 0, 8, 8), area_in="physical"),
         K.CaptureError),
        ("area that is not 4 numbers", dict(area=(0, 0, 8)), K.CaptureError),
    ):
        try:
            cap = K.Capture(shm=K.default_shm_path("mbad"), **kwargs)
            cap.close()
            check(name + " raises", False, "no exception")
        except exc:
            check(name + " raises", True)
        except Exception as e:  # noqa: BLE001
            check(name + " raises", False, f"{type(e).__name__}: {e}")
    # area_in='physical' names the rectangle in **device pixels of this output** (that is
    # the whole point of it), so the region covers 256x144 real pixels. The image itself is
    # still rendered at the scene factor, hence 256*(area_scale/pixel_scale) px wide.
    # Checked on every output: on one running at the scene scale both mappings coincide and
    # only the size assertion bites, so the mixed-DPI case is the one that needs a sibling.
    for mm in monitors:
        try:
            with K.Capture(monitor=mm, shm=K.default_shm_path("mphysnat")) as cap:
                whole = cap.grab(copy=True, timeout=10)
            # pick a 256x144 device rectangle that actually has detail in it: a flat patch
            # of wallpaper matches every mapping and proves nothing
            best = None
            for yy in range(0, max(1, whole.shape[0] - 148), 90):
                for xx in range(0, max(1, whole.shape[1] - 260), 90):
                    c = whole[yy:yy + 144, xx:xx + 256, :3].astype(np.int16)
                    score = float(np.abs(c - np.roll(c, 2, axis=1)).mean())
                    if best is None or score > best[0]:
                        best = (score, xx, yy)
            detail, dx, dy = best
            with K.Capture(monitor=mm, area=(dx, dy, 256, 144), area_in="physical",
                           shm=K.default_shm_path("mphys")) as cap:
                f = cap.grab(copy=True, timeout=10)
                ps, a = cap.pixel_scale, cap.area_scale
            ew, eh = round(256 * a / ps), round(144 * a / ps)
            check(f"{mm.name}: area_in='physical' converts through the display scale",
                  abs(f.shape[1] - ew) <= 3 and abs(f.shape[0] - eh) <= 3,
                  f"{f.shape[1]}x{f.shape[0]} expected {ew}x{eh} "
                  f"(display x{ps:g}, scene x{a:g})")
            # the content check: the frame, back at device size, must be the device
            # rectangle it names -- and clearly not the region the scene factor gives
            got = K.resize(np.ascontiguousarray(f[..., :3]), width=256)[:144, :256].astype(int)
            ref = whole[dy:dy + 144, dx:dx + 256, :3].astype(int)
            mad = float(np.abs(got - ref).mean())
            k = ps / a
            if abs(k - 1.0) < 0.02:
                check(f"{mm.name}: area_in='physical' grabs the device region it names",
                      mad < 20.0, f"MAD={mad:.1f} (display == scene: one mapping only; "
                                  f"detail {detail:.1f})")
            else:
                ox, oy = int(dx * k), int(dy * k)
                alt = whole[oy:oy + max(8, int(144 * k)), ox:ox + max(8, int(256 * k)), :3]
                alt = K.resize(np.ascontiguousarray(alt), width=256)[:144, :256].astype(int)
                mad_alt = float(np.abs(got - alt).mean())
                check(f"{mm.name}: area_in='physical' grabs the device region it names",
                      mad < 20.0 and mad < mad_alt,
                      f"MAD={mad:.1f} vs {mad_alt:.1f} for the scene-factor region "
                      f"({detail:.1f} detail at device {dx},{dy})")
        except Exception as e:  # noqa: BLE001
            check(f"{mm.name}: area_in='physical' converts through the display scale",
                  False, f"{type(e).__name__}: {e}")


def _open_fds():
    try:
        return len(os.listdir("/proc/self/fd"))
    except OSError:
        return -1


def resilience_section():
    """v0.5: grab() recovers from a dead or reaped daemon, and from a target that outgrew
    the ring.  The whole point is that the caller does not have to notice."""
    print("\n== resilience: auto-restart after the daemon dies ==")
    with K.Capture(shm=K.default_shm_path("auto1")) as cap:
        pid1 = cap.stats()["pid"]
        f1 = cap.grab(copy=True)
        check("baseline frame", f1.shape[2] == 4, str(f1.shape))
        check("no restarts yet", cap.auto_restarts == 0, str(cap.auto_restarts))
        check("the first frame is not reported as a resize", not cap.resized)

        old_view = cap.grab(copy=False)          # zero-copy view of the current ring
        os.kill(pid1, signal.SIGKILL)
        deadline = time.time() + 5
        while time.time() < deadline and cap.alive:
            time.sleep(0.05)
        check("the daemon really is gone", not cap.alive)
        try:
            f2 = cap.grab(timeout=8)
            pid2 = cap.stats()["pid"]
            check("grab() recovers from SIGKILL without the caller noticing",
                  f2.shape == f1.shape and pid2 != pid1, f"pid {pid1} -> {pid2} {f2.shape}")
            check("the recovery is counted", cap.auto_restarts == 1, str(cap.auto_restarts))
            check("the reason is recorded", "DaemonDead" in cap.last_restart_reason,
                  cap.last_restart_reason[:70])
            check("the consecutive-restart streak resets when frames flow again",
                  cap._restart_streak == 0)
            check("a same-size frame is not reported as a resize", not cap.resized)
            check("frames keep flowing after the recovery",
                  cap.grab(copy=True).shape == f1.shape)
            check("a view from before the restart is still readable (frozen, not unmapped)",
                  old_view.shape == f2.shape and int(old_view[0, 0, 0]) >= 0)
        except Exception as e:  # noqa: BLE001
            check("grab() recovers from SIGKILL without the caller noticing", False,
                  f"{type(e).__name__}: {e}")

    print("\n== resilience: auto-restart does not leak (BUG-3 through the auto path) ==")
    with K.Capture(shm=K.default_shm_path("auto2")) as cap:
        cap.grab()
        base = _open_fds()
        try:
            for _ in range(3):
                os.kill(cap.stats()["pid"], signal.SIGKILL)
                time.sleep(0.2)
                cap.grab(timeout=8)
            after = _open_fds()
            check("3 auto-restarts do not leak file descriptors",
                  after - base <= 2, f"{base} -> {after} fds over 3 auto-restarts")
            check("every auto-restart is counted (cumulative)",
                  cap.auto_restarts == 3, str(cap.auto_restarts))
        except Exception as e:  # noqa: BLE001
            check("3 auto-restarts do not leak file descriptors", False,
                  f"{type(e).__name__}: {e}")

    print("\n== resilience: a daemon reaped for being idle comes back ==")
    with K.Capture(idle_exit=1.0, shm=K.default_shm_path("autoidle")) as cap:
        pid = cap.stats()["pid"]
        time.sleep(2.6)
        check("idle_exit reaped it", not cap.alive, f"pid {pid}")
        try:
            f = cap.grab(timeout=8)
            check("grab() revives a daemon that was reaped for being idle",
                  f.shape[0] > 0 and cap.stats()["pid"] != pid,
                  cap.last_restart_reason[:70])
        except Exception as e:  # noqa: BLE001
            check("grab() revives a daemon that was reaped for being idle", False,
                  f"{type(e).__name__}: {e}")

    print("\n== resilience: what is recoverable, and what is not ==")
    with K.Capture(shm=K.default_shm_path("auto4")) as cap:
        check("a dead daemon is recoverable", cap._recoverable(K.DaemonDead("x")))
        check("a ring the target outgrew is recoverable", cap._recoverable(K.RingTooSmall("x")))
        check("a closed window is NOT recoverable", not cap._recoverable(K.WindowGone("x")))
        check("a timeout with a live daemon is NOT recoverable (do not mask a wedged KWin)",
              not cap._recoverable(TimeoutError("x")))
        # Exhaust the streak, then kill: it must give up rather than respawn forever.
        cap._restart_streak = cap.restart_limit
        os.kill(cap.stats()["pid"], signal.SIGKILL)
        time.sleep(0.2)
        try:
            cap.grab(timeout=3)
            check("restart_limit stops a restart storm", False, "it kept restarting")
        except K.CaptureError as e:
            check("restart_limit stops a restart storm", "giving up" in str(e), str(e)[:95])

    print("\n== resilience: auto_restart=False keeps the old behaviour ==")
    with K.Capture(auto_restart=False, shm=K.default_shm_path("autooff")) as cap:
        os.kill(cap.stats()["pid"], signal.SIGKILL)
        time.sleep(0.3)
        try:
            cap.grab(timeout=1.5)
            check("auto_restart=False raises DaemonDead", False, "no exception raised")
        except K.DaemonDead:
            check("auto_restart=False raises DaemonDead", True)
        except Exception as e:  # noqa: BLE001
            check("auto_restart=False raises DaemonDead", False,
                  f"{type(e).__name__}: {e}")
        check("nothing was restarted behind your back", cap.auto_restarts == 0)
        cap.restart()
        check("restart() still revives it explicitly", cap.grab(timeout=8).shape[0] > 0)


def _x11_windows():
    """{x11 id: "x y w h"} for X11/XWayland windows, via wmctrl (empty if unavailable)."""
    if not shutil.which("wmctrl"):
        return {}
    try:
        out = subprocess.run(["wmctrl", "-lG"], capture_output=True, text=True,
                             timeout=10).stdout
    except Exception:  # noqa: BLE001
        return {}
    rows = {}
    for line in out.splitlines():
        parts = line.split(None, 7)   # id desktop x y w h host title (KWin's column order)
        if len(parts) >= 6:
            rows[parts[0]] = parts[2:6]
    return rows


def _wmctrl_geom(xid):
    """(w, h) of an X11 window as the X server sees it, or None. `wmctrl -lG` columns:
    id desktop x y w h host title."""
    out = subprocess.run(["wmctrl", "-l", "-G"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        cols = line.split()
        if len(cols) >= 6 and cols[0] == xid:
            return int(cols[4]), int(cols[5])
    return None


def _set_base(xid, w, h, tries=12):
    """Resize the xterm and wait for the resize to land before the Capture is created.

    Checked against wmctrl's own numbers, not KWin's: `Window.geometry` is *logical*, so
    on a scaled desk a 320 px X11 window is not 320 anything there (256 at scene 1.25).
    """
    subprocess.run(["wmctrl", "-i", "-r", xid, "-e", f"0,60,60,{w},{h}"], timeout=10)
    for _ in range(tries):
        time.sleep(0.4)
        g = _wmctrl_geom(xid)
        if g and abs(g[0] - w) <= 8 and abs(g[1] - h) <= 8:
            return True
    return False


def _resize_then_wait(cap, xid, w, h, tries=10, kx=1.0, ky=1.0):
    """Resize, then poll until the capture agrees on the new size.

    A window manager takes a moment, and the first frame after a resize can still carry
    the old geometry, so retry rather than declaring a miss too early. Returns
    (frame, matched, error).

    `kx`/`ky` are the frame px per X11 px measured at the base size: the client's size,
    KWin's logical size and the captured device size all differ under fractional scaling
    (320 X11 px -> 256 logical -> 192 device at scene 1.25 / display 0.75), so the test
    calibrates instead of assuming a 1:1 desk.
    """
    subprocess.run(["wmctrl", "-i", "-r", xid, "-e", f"0,60,60,{w},{h}"], timeout=10)
    err = None
    for _ in range(tries):
        time.sleep(0.5)
        try:
            f = cap.grab(copy=True, timeout=8)
        except Exception as e:  # noqa: BLE001
            err = e
            continue
        err = None
        # decorations/shadows: a little slack, but it must have moved to the new size
        if abs(f.shape[1] - w * kx) <= 60 and abs(f.shape[0] - h * ky) <= 90:
            return f, True, None
    return None, False, err


def window_resize_section():
    """v0.5: a window being resized must not wedge, mis-shape or stale-out the capture.

    Uses an xterm because it is an X11 window, so wmctrl can resize it on command; the
    ring's own resize headroom is what is under test, and `slot_floor` lets the test dial
    that headroom down until a resize overflows the ring and has to be recovered from.
    """
    print("\n== resilience: a resized window ==")
    if not (shutil.which("xterm") and shutil.which("wmctrl")):
        print("  [skip] needs xterm + wmctrl")
        return
    subprocess.run(["pkill", "-f", "xterm -name kwcttest"], timeout=10)
    time.sleep(0.6)
    before = set(_x11_windows())
    proc = subprocess.Popen(["xterm", "-name", "kwcttest", "-title", "KWCTTEST",
                             "-geometry", "50x12"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    xid, win = None, None
    deadline = time.time() + 15
    try:
        while time.time() < deadline and not (xid and win):
            new = set(_x11_windows()) - before
            xid = sorted(new)[0] if new else None
            cands = [w for w in K.list_windows() if (w.app_id or "") == "XTerm"]
            win = cands[0] if len(cands) == 1 else None
            if not (xid and win):
                time.sleep(0.3)
        if not check("launched an xterm we can resize", bool(xid and win),
                     f"x11={xid} kwin={getattr(win, 'id', None)}"):
            return
        # Both sub-tests must start from the SAME known size: the ring is sized from the
        # first frame, so inheriting whatever size the previous sub-test left behind makes
        # the "grew" steps below shrink instead (and the overflow never happens).
        base = (320, 200)
        steps = ((512, 384), (256, 192), (900, 620))
        for tiny in (False, True):
            if not check(f"window set to {base[0]}x{base[1]} "
                         f"({'tiny' if tiny else 'default'} ring)",
                         _set_base(xid, base[0], base[1])):
                continue
            cap = K.Capture(window=win.id, shm=K.default_shm_path("rz" + ("t" if tiny else "n")),
                            slot_floor=(96, 64) if tiny else None)
            try:
                f0 = cap.grab(copy=True, timeout=8)
                check(f"window capture works ({'tiny' if tiny else 'default'} ring)",
                      f0.shape[0] > 0, f"{f0.shape[1]}x{f0.shape[0]} "
                                       f"slot={cap.slot_bytes / 2**20:.2f}MiB")
                # frame px per X11 px on this desk (1.0 unscaled, 0.6 at scene 1.25 + 75%)
                kx, ky = f0.shape[1] / base[0], f0.shape[0] / base[1]
                followed = True
                for (ww, hh) in steps:
                    f, ok, err = _resize_then_wait(cap, xid, ww, hh, kx=kx, ky=ky)
                    if not ok:
                        followed = False
                        check(f"resize to {ww}x{hh} is followed "
                              f"({'tiny' if tiny else 'default'} ring)", False,
                              f"{type(err).__name__ if err else 'wrong size'}: "
                              f"{err or (f.shape[1], f.shape[0])}")
                        break
                if followed:
                    check(f"every resize is followed by a frame of the new size "
                          f"({'tiny' if tiny else 'default'} ring)", True)
                if tiny:
                    check("a resize that outgrew the ring healed itself",
                          cap.auto_restarts > 0
                          and cap.last_restart_reason.startswith("RingTooSmall"),
                          f"restarts={cap.auto_restarts} slot now="
                          f"{cap.slot_bytes / 2**20:.2f}MiB {cap.last_restart_reason[:50]}")
                else:
                    check("the default ring absorbed the resizes with no restart at all",
                          cap.auto_restarts == 0, str(cap.auto_restarts))
            finally:
                cap.close()
    finally:
        subprocess.run(["pkill", "-f", "xterm -name kwcttest"], timeout=10)
        if proc.poll() is None:
            proc.kill()


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
        # NOT "the first output": a plain Capture() follows the compositor's active
        # screen, and on a desk with two outputs that is whichever one holds the focus.
        # What must always hold is that the geometry agrees with the output it reports.
        reported = next((s for s in screens if s["name"] == cap.screen_name), None)
        check("geometry matches the output this Capture reports",
              reported is not None and (w, h) == (reported["width"], reported["height"]),
              f"{cap.screen_name} {w}x{h}; outputs: "
              + ", ".join(f"{s['name']} {s['width']}x{s['height']}" for s in screens))
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
                    # Compare like with like. Pillow grabs the X11 root; `cap` follows
                    # KWin's active output. With two monitors up those can be different
                    # screens, and cropping one onto the other produced a MAD that looked
                    # the same whether the channels were right or swapped -- i.e. proof of
                    # nothing. So: take whichever output actually matches the reference.
                    ours = None
                    targets = ([dict(screen=mon) for mon in
                                [cap.screen_name] + [s["name"] for s in screens
                                                     if s["name"] != cap.screen_name]]
                               + [dict(workspace=True)])   # the whole virtual desktop:
                                                           # what an X root grab covers
                    for kwargs in targets:
                        try:
                            with K.Capture(shm=K.default_shm_path("colour"),
                                           **kwargs) as ref_cap:
                                cand = np.asarray(ref_cap.shot(), dtype=np.int16)
                        except K.CaptureError:
                            continue
                        if cand.shape == ref.shape:
                            ours = cand
                            break
                    if ours is None:
                        raise ValueError(
                            f"the reference covers {ref.shape[1]}x{ref.shape[0]}, which is "
                            f"none of the outputs here "
                            + str([(s["name"], s["width"], s["height"]) for s in screens]))
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
        # `area` is logical and the image is rendered at the scene factor, so on a scaled
        # desk the frame is 640*area_scale wide, not 640 (1:1 when nothing is scaled).
        a = cap.area_scale
        ew, eh = round(640 * a), round(360 * a)
        check("area capture geometry", cap.geometry() == (ew, eh),
              f"{cap.geometry()} expected ({ew},{eh}) at area_scale x{a:g}")
        check("area frame usable", cap.grab().shape == (eh, ew, 4),
              str(cap.grab().shape))
    with K.Capture(workspace=True) as cap:
        g = cap.geometry()
        check("workspace capture produced a frame", g[0] >= s0["width"] and g[1] >= s0["height"],
              f"{g[0]}x{g[1]}")

    monitor_section()
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

    print("\n== failure handling (auto_restart=False: report it, do not recover) ==")
    cap = K.Capture(auto_restart=False, shm=K.default_shm_path("failh"))
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

    bug_regression_section()
    resilience_section()
    if not quick:
        window_resize_section()
    else:
        print("\n== resilience: a resized window ==\n  [skip] quick mode")

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
