"""Repro harness for BUG-4: memory-safety race in the client's zero-copy read path.

    .venv/bin/python probe/zero_copy_stress.py hot      [seconds]
    .venv/bin/python probe/zero_copy_stress.py views     [seconds]
    .venv/bin/python probe/zero_copy_stress.py restart   [seconds]
    .venv/bin/python probe/zero_copy_stress.py close     [seconds]
    .venv/bin/python probe/zero_copy_stress.py all       [seconds]   (each mode, ~1/4)

Modes (all of them run the client's zero-copy path -- copy=False -- because that is
where BUG-4 lives):

  hot     hammer grab()/latest(rgb=True) as fast as possible, with GC pressure.
  views   hold every frame view we ever got alive in a list, keep grabbing, then read
          all of them back. Stresses "a view outlives the ring generation that made it".
  restart grab continuously while another thread restart()s the daemon; the client's
          _mm/_hdr are replaced under the reader.
  close   grab continuously, then close() the Capture while views are still referenced
          and read them back (mmap lifetime vs. numpy's buffer export).

Run under `PYTHONFAULTHANDLER=1 .venv/bin/python -X dev` and repeat: BUG-4 is flaky, a
single clean pass proves nothing. Exit 0 = nothing anomalous in this run; exit 1 = a
wrong-shaped/corrupt frame or an unexpected exception was seen (the process dying of
SIGSEGV/SIGBUS is its own answer -- see the log).
"""

from __future__ import annotations

import faulthandler
import gc
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import kwcapture as K

faulthandler.enable()

ANOMALIES: list[str] = []


def note(msg: str) -> None:
    ANOMALIES.append(msg)
    print(f"  !! ANOMALY: {msg}", flush=True)


def sane(arr: np.ndarray, tag: str, geom: tuple[int, int]) -> bool:
    """Cheap structural check: the frame must match the advertised geometry and dtype."""
    w, h = geom
    if arr.dtype != np.uint8:
        note(f"{tag}: dtype {arr.dtype}")
        return False
    if arr.ndim != 3 or arr.shape[0] != h or arr.shape[1] != w:
        note(f"{tag}: shape {arr.shape} != expected ({h}, {w}, *)")
        return False
    if arr.shape[2] not in (3, 4):
        note(f"{tag}: channel count {arr.shape[2]}")
        return False
    return True


def mode_hot(seconds: float) -> None:
    """One fresh grab per `KWC_BURST` reads of the newest frame (default 200).

    The historic BUG-4 report is `latest()` at ~22k/s sustained, i.e. many more reads than
    grabs, so the burst is what reproduces the exposure; the grab in between keeps the
    ring moving and exercises the wait loop too.
    """
    burst = int(os.environ.get("KWC_BURST", "200"))
    cap = K.Capture(shm=K.default_shm_path("zcopy_hot"))
    try:
        geom = cap.geometry()
        n = 0
        t_end = time.monotonic() + seconds
        t0 = time.monotonic()
        last_grab = 0.0
        while time.monotonic() < t_end:
            # hammer the newest-frame path (that is where the millions-of-views-per-second
            # exposure is); force a real compositor round trip about every 2 s so the
            # ring actually moves and the wait/sched_yield path runs too
            for _ in range(burst):
                a = cap.latest(rgb=True)          # zero-copy, negative strides
                sane(a, "latest(rgb=True)", geom)
            n += burst
            if time.monotonic() - last_grab > 2.0:
                b = cap.grab(rgb=False)           # forces a fresh frame from KWin
                sane(b, "grab()", geom)
                if burst == 1:
                    c = cap.shot(width=320)       # resize + colour convert off the view
                    if c.ndim != 3 or c.shape[1] != 320:
                        note(f"shot(width=320): {c.shape}")
                last_grab = time.monotonic()
            if n % 200000 < burst:
                gc.collect()                      # BUG-4 is described as GC-dependent
        dt = time.monotonic() - t0
        print(f"  hot: {n:,} zero-copy reads in {dt:.0f}s ({n / dt:,.0f} reads/s), "
              f"seq={cap.stats()['seq']}")
    finally:
        cap.close()


def mode_views(seconds: float) -> None:
    """Keep every view alive; read them all back after the ring has wrapped many times."""
    cap = K.Capture(shm=K.default_shm_path("zcopy_views"))
    kept: list[np.ndarray] = []
    try:
        geom = cap.geometry()
        t_end = time.monotonic() + seconds
        n = 0
        while time.monotonic() < t_end:
            kept.append(cap.latest())
            cap.grab()
            n += 1
            if n % 500 == 0:
                gc.collect()
        bad = 0
        for arr in kept:
            if arr.dtype != np.uint8 or arr.shape[2] not in (3, 4):
                bad += 1
            else:
                _ = int(arr[0, 0, 0]) + int(arr[-1, -1, -1])
        print(f"  views: {len(kept)} views held and read back, {bad} structurally bad")
        if bad:
            note(f"{bad} views unreadable after the ring wrapped")
    finally:
        cap.close()
        # views still referenced here on purpose: they now outlive a closed Capture
        for arr in kept[:50]:
            _ = int(arr[0, 0, 0])
        print(f"  read {min(50, len(kept))} views after close(), still alive: "
              f"{kept[0].shape if kept else 'none'}")
        del kept
        gc.collect()


def mode_restart(seconds: float) -> None:
    """Replace _mm/_hdr under a reader that is reading views at full speed."""
    cap = K.Capture(shm=K.default_shm_path("zcopy_restart"))
    stop = threading.Event()
    errors: list[str] = []
    views: list[np.ndarray] = []

    def churn() -> None:
        while not stop.is_set():
            try:
                cap.restart()
            except Exception as e:  # noqa: BLE001 - a restart race is exactly the point
                errors.append(f"restart: {type(e).__name__}: {e}")
            time.sleep(0.05)

    th = threading.Thread(target=churn, daemon=True)
    th.start()
    try:
        n = 0
        t_end = time.monotonic() + seconds
        while time.monotonic() < t_end:
            try:
                arr = cap.latest(rgb=True)
                views.append(arr)
                if len(views) > 400:
                    del views[:200]
            except (K.CaptureError, TimeoutError) as e:
                errors.append(f"latest: {type(e).__name__}: {e}")
            n += 1
        gc.collect()
        for arr in views:                      # read views made before/during restarts
            _ = int(arr[0, 0, 0])
    finally:
        stop.set()
        th.join(timeout=5)
        cap.close()
    hard = [e for e in errors if not isinstance(e, str) or
            "daemon" not in e.lower() and "not started" not in e.lower()]
    print(f"  restart: {n} grabs, {len(errors)} exceptions "
          f"({len(set(hard))} distinct unexpected)")
    for e in sorted(set(errors))[:8]:
        print(f"     - {e}")


def mode_close(seconds: float) -> None:
    """close() with outstanding zero-copy views, then read them."""
    for i in range(max(1, int(seconds // 0.4))):
        cap = K.Capture(shm=K.default_shm_path("zcopy_close"))
        cap.grab()
        a = cap.latest(rgb=True)
        b = cap.latest()
        cap.close()
        gc.collect()
        try:
            _ = int(a[0, 0, 0]) + int(b[-1, -1, -1])
            _ = int(a.mean())
        except Exception as e:  # noqa: BLE001
            note(f"iteration {i}: reading a view after close(): "
                 f"{type(e).__name__}: {e}")
    print(f"  close: cycled Capture close/open with views held, survived")


MODES = {"hot": mode_hot, "views": mode_views, "restart": mode_restart,
         "close": mode_close}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "hot"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    print(f"BUG-4 zero-copy stress: mode={mode} seconds={seconds} "
          f"pid={os.getpid()} python={sys.version.split()[0]} "
          f"kwcapture={K.__version__}")
    if mode == "all":
        for name in ("hot", "views", "restart", "close"):
            MODES[name](max(2.0, seconds / 4))
    else:
        MODES[mode](seconds)
    print(f"RESULT: {len(ANOMALIES)} anomalies")
    return 1 if ANOMALIES else 0


if __name__ == "__main__":
    sys.exit(main())
