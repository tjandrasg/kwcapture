"""BUG-4 root cause: a *rate* measurement of the corruption, per formulation.

The historic BUG-4 symptoms -- `TypeError: 'int' object is not callable`, locals that are
suddenly a `Capture`, a constant tuple that is `None`, `ValueError: cannot reshape array
of size 1`, SIGSEGV -- are all reproducible with **no kwcapture, no daemon and nothing
writing to the shared memory**: a tight loop that builds a numpy view over an `mmap`
(see probe/race_bisect.py for the ctypes variant, and this file for the numpy variants).

So the question this tool answers is not "is there a race" (there is no second writer
here) but "which formulation of the zero-copy read triggers the interpreter/numpy bug,
and how often".  Every variant does the *same* work and self-checks: the mapping is
written once with a known pattern, so any view that does not read back exactly that
pattern is corruption -- even when nothing crashes.

    KWC_MODE=A B C D E           # see MODES below
    KWC_ROUNDS=3 KWC_ITERS=20000000
    .venv/bin/python -X dev probe/corruption_rate.py

Exit 0 = every round clean; 1 = at least one round crashed or read back wrong.
"""

from __future__ import annotations

import mmap
import os
import sys
import time

import numpy as np

SLOTS = 4
HDR = 4096
W, H, STRIDE = 640, 480, 2560
SLOT_BYTES = STRIDE * H * 4
TOTAL = HDR + SLOT_BYTES * SLOTS
ROUNDS = int(os.environ.get("KWC_ROUNDS", "3"))
ITERS = int(os.environ.get("KWC_ITERS", "20000000"))

PATH = f"/tmp/kwcapture_corruption_rate.{os.getuid()}.shm"
_PATTERN = bytes(range(256)) * (TOTAL // 256 + 1)
PRIVATE = _PATTERN[:TOTAL]          # same bytes, ordinary heap, nobody maps it
EXPECT = PRIVATE[:64]


def make(writable: bool) -> mmap.mmap:
    """Fill the file with a checkable pattern, then map it as the variant wants it."""
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, TOTAL)
    seed = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)
    seed[:] = (bytes(range(256)) * (TOTAL // 256 + 1))[:TOTAL]   # byte i == i % 256
    seed.flush()
    seed.close()
    return mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE if writable else mmap.ACCESS_READ)


def check(arr: np.ndarray, off: int) -> None:
    """The view must describe the bytes we wrote -- a shape/stride/value surprise is
    corruption even if no exception was raised."""
    if arr.shape != (H, W, 4) or arr.dtype != np.uint8:
        raise AssertionError(f"shape/dtype {arr.shape} {arr.dtype}")
    expect = (off & 0xFF)
    if int(arr[0, 0, 0]) != expect:
        raise AssertionError(f"first byte {int(arr[0, 0, 0])} != {expect}")
    if int(arr[0, 0, 1]) != (expect + 1) & 0xFF:
        raise AssertionError("second byte wrong")


def run(mode: str) -> tuple[bool, str]:
    writable = mode not in ("C",)
    mm = make(writable)
    mv = memoryview(mm)
    try:
        for n in range(ITERS):
            off = HDR + (n % SLOTS) * SLOT_BYTES
            try:
                if mode == "A":       # what kwcapture 0.4.0 does today
                    a = np.frombuffer(mm, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)[:, :W, :]
                    a.setflags(write=False)
                elif mode == "B":     # same, without setflags()
                    a = np.frombuffer(mm, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)[:, :W, :]
                elif mode == "C":     # read-only mapping: already read-only, setflags gone
                    a = np.frombuffer(mm, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)[:, :W, :]
                elif mode == "D":     # our own memoryview as the buffer object
                    a = np.frombuffer(mv, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)[:, :W, :]
                    a.setflags(write=False)
                elif mode == "E":     # no per-frame width slice
                    a = np.frombuffer(mm, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)
                elif mode == "G":     # CONTROL: private bytes, same numpy view ops
                    a = np.frombuffer(PRIVATE, dtype=np.uint8, count=STRIDE * H,
                                      offset=off).reshape(H, STRIDE // 4, 4)[:, :W, :]
                    a.setflags(write=False)
                elif mode == "H":     # CONTROL: no numpy at all, same walk over the mmap
                    a = mm[off:off + 64]
                    if a != EXPECT:
                        raise AssertionError("mmap bytes changed")
                else:
                    raise SystemExit(f"unknown KWC_MODE={mode}")
                if n % 4093 == 0 and mode != "H":
                    check(a, off)
            except Exception as e:  # noqa: BLE001 - the exception is the measurement
                return False, f"{type(e).__name__}: {e} at iteration {n}"
        return True, "clean"
    finally:
        try:
            mv.release()
        except (BufferError, ValueError):
            pass
        try:
            mm.close()
        except BufferError:      # a numpy view from the last iteration is still alive
            pass


def main() -> int:
    modes = (os.environ.get("KWC_MODE") or "A B C D E").split()
    bad = 0
    for mode in modes:
        for r in range(ROUNDS):
            t0 = time.perf_counter()
            ok, detail = run(mode)
            dt = time.perf_counter() - t0
            rate = ITERS / dt if ok else 0
            print(f"[{'OK  ' if ok else 'BAD '}] MODE={mode} round {r + 1}/{ROUNDS}: "
                  f"{ITERS:,} iters in {dt:.1f}s ({rate:,.0f} it/s) {detail}", flush=True)
            bad += 0 if ok else 1
    print(f"\n{bad} of {len(modes) * ROUNDS} rounds were not clean.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
