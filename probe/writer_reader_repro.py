#!/usr/bin/env python3
"""Is the BUG-4 fault reproducible with NO kwcapture -- shm mapping + a concurrent writer?

    KWC_ITERS=20000000 .venv/bin/python -X dev probe/writer_reader_repro.py            # with writer
    KWC_WRITER=0       .venv/bin/python -X dev probe/writer_reader_repro.py            # control

Why this exists: after the RAM was taken off XMP and downclocked 5200 -> 4800 MT/s (2026-10-08),
`probe/fault_rate.py` (live kwcapture ring) still faulted 4 rounds in 6 at 5M reads each, while
`race_bisect.py` and `corruption_rate.py` -- numpy over an mmap with *no* writer -- were clean for
~144M iterations. So the fault now appears to need a *live, concurrently written* mapping. This
probe builds exactly that and nothing else: a /dev/shm file, a child process scribbling a
kwcapture-shaped header + payload into it, and a parent making numpy views over it.

Deliberately racy: there is no seqlock, so **torn values are EXPECTED** and are counted as
`torn=`. What we are looking for is the BUG-4 signature instead -- `TypeError: 'int' object is not
callable`, `AttributeError` on an object that has the attribute, `IndexError: only integers…`, a
segfault, i.e. a fault that torn data cannot explain.

  exit 0  + impossible=0            -> this construction is clean; the live path is implicated
  exit 3  + impossible>0 / crash    -> not kwcapture: it reproduces with a 60-line writer/reader
"""
from __future__ import annotations

import ctypes
import gc
import mmap
import os
import struct
import sys
import tempfile
import time

ITERS = int(os.environ.get("KWC_ITERS", "20000000"))
STEP = int(os.environ.get("KWC_STEP", "1000000"))
WRITER = os.environ.get("KWC_WRITER", "1") != "0"
WIDTH, HEIGHT = 640, 480
HDR = struct.Struct("<IIIIII")            # magic, seq, w, h, stride, format
SLOT = HDR.size + WIDTH * HEIGHT * 4

import numpy as np                         # noqa: E402  (after env, like the other probes)


def shm_map(tag: str):
    path = os.path.join(tempfile.gettempdir(), f"kwc_writer_reader_{tag}")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0o600)
    os.ftruncate(fd, SLOT * 2)
    mm = mmap.mmap(fd, SLOT * 2)
    os.close(fd)
    return path, mm


def writer(path: str) -> None:
    """Scribble a valid-looking header + payload, alternating slots. Never stops until killed.

    Both slots are filled with valid headers BEFORE the loop label matters: the reader must spend
    its time reading *valid* frames (like the real ring does), not zero-filled ones, or every read
    counts as torn and the test proves nothing.
    """
    _, mm = shm_map("writer")
    payload = bytes(range(256)) * ((WIDTH * HEIGHT * 4) // 256)
    seq = 0
    for slot in (0, 1):        # pre-fill: valid geometry from the first reader iteration on
        mm[slot * SLOT: slot * SLOT + HDR.size] = HDR.pack(
            0x4B574350, 0, WIDTH, HEIGHT, WIDTH * 4, 6)
        mm[slot * SLOT + HDR.size: (slot + 1) * SLOT] = payload
    while True:
        for slot in (0, 1):
            seq += 1
            mm[slot * SLOT: slot * SLOT + HDR.size] = HDR.pack(
                0x4B574350, seq, WIDTH, HEIGHT, WIDTH * 4, 6)
            mm[slot * SLOT + HDR.size: (slot + 1) * SLOT] = payload


def main() -> int:
    path, mm = shm_map("reader")
    child = 0
    if WRITER:
        child = os.fork()
        if child == 0:
            try:
                writer(path)
            finally:
                os._exit(0)
    print(f"writer={'on' if WRITER else 'off'} pid={child}; shm={path}; "
          f"target {ITERS:,} reads of {WIDTH}x{HEIGHT} views", flush=True)

    base = ctypes.addressof(ctypes.c_char.from_buffer(mm))
    torn = impossible = 0
    n = 0
    t0 = time.perf_counter()
    try:
        while n < ITERS:
            for i in range(STEP):
                off = ((n + i) % 2) * SLOT   # alternate slots per READ, not per step
                try:
                    magic, seq, w, h, stride, fmt = HDR.unpack_from(mm, off)
                    a = np.frombuffer(mm, dtype=np.uint8, count=stride * h,
                                      offset=off + HDR.size)
                    a = a.reshape(h, w, 4)          # torn header -> ValueError, expected
                    if a.shape[2] != 3 + 1 or a.dtype != np.uint8 or a.ndim != 3:
                        impossible += 1            # a wrong answer from a valid-looking read
                    if a.shape == (HEIGHT, WIDTH, 4) and int(a[7, 3, 0]) not in range(256):
                        impossible += 1            # touched memory, got a non-byte back
                    if fmt != 6 or (w, h) != (WIDTH, HEIGHT):
                        torn += 1
                except (struct.error, ValueError, IndexError):
                    torn += 1                      # geometry disagreement: torn, not a fault
                except Exception as e:             # noqa: BLE001 - THAT is the interesting case
                    impossible += 1
                    print(f"IMPOSSIBLE at {n:,}: {type(e).__name__}: {e}", flush=True)
                    if impossible >= 5:
                        return 3
            n += STEP
            print(f"  {n:,} reads  torn={torn:,}  impossible={impossible}  "
                  f"{n / (time.perf_counter() - t0):,.0f} it/s", flush=True)
    finally:
        if child:
            os.kill(child, 9)
            os.waitpid(child, 0)
        gc.collect()                      # drop the last view, or close() raises BufferError
        try:
            mm.close()
        except BufferError:               # a view is still alive; the unlink below is what matters
            pass
        os.unlink(path)
    print(f"clean: {n:,} reads, torn={torn:,}, impossible={impossible} in "
          f"{time.perf_counter() - t0:.0f}s", flush=True)
    return 0 if impossible == 0 else 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
