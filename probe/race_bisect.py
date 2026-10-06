"""BUG-4 bisect: mmap + ctypes.from_buffer + numpy.frombuffer, no daemon, no writer.

Rebuilds the previous session's /tmp/reproB.py from the transcript (see AGENTS.md BUG-4)
and adds the diagnostics it never got: which iteration, which variant, and a canary that
says WHAT was corrupted.

Nothing ever writes to the mapping after setup, so every field must read back exactly as
written on every single iteration. If a read returns anything else -- or an attribute
lookup returns an object of the wrong type -- the client's own memory has been corrupted.

    KWC_MODE=both|numpy|ctypes KWC_ITERS=3000000 .venv/bin/python -X dev probe/race_bisect.py

Observed on this box (Plasma 6.6, CPython 3.14.4, numpy 2.5.3):
    MODE=both    TypeError: 'int' object is not callable  at iteration 326,533
    MODE=numpy   Segmentation fault   (no ctypes at all -- numpy over the mmap is enough)
    MODE=ctypes  clean, 3.9M it/s

Exit 0 = survived and every read matched; 1 = corruption observed (printed with the
iteration count).  A hard crash (TypeError/ValueError/AttributeError with an impossible
type, or SIGSEGV) is the bug itself: the traceback line is where it *noticed*, not what
went wrong.
"""

from __future__ import annotations

import ctypes
import mmap
import os
import sys
import time

import numpy as np

MODE = os.environ.get("KWC_MODE", "both")
ITERS = int(os.environ.get("KWC_ITERS", "3000000"))

SLOTS = 4
HDR_SIZE = 4096
W, H, STRIDE, FMT = 640, 480, 2560, 6
SLOT_BYTES = STRIDE * H * 4


class Slot(ctypes.Structure):
    _fields_ = [
        ("a", ctypes.c_uint32),      # width
        ("b", ctypes.c_uint32),      # height
        ("c", ctypes.c_uint32),      # stride
        ("d", ctypes.c_uint32),      # format
        ("e", ctypes.c_double),
        ("f", ctypes.c_double),
        ("g", ctypes.c_double),
        ("hh", ctypes.c_uint64),
        ("i", ctypes.c_char * 64),
        ("j", ctypes.c_uint32),
        ("pad", ctypes.c_uint32 * 7),
    ]


class Hdr(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("hdr_size", ctypes.c_uint32),
        ("slot_bytes", ctypes.c_uint32),
        ("slots", ctypes.c_uint32),
        ("ready", ctypes.c_uint32),
        ("quit", ctypes.c_uint32),
        ("error", ctypes.c_uint32),
        ("pad2", ctypes.c_uint32 * 2),
        ("req_seq", ctypes.c_uint64),
        ("frame_seq", ctypes.c_uint64),
        ("published", ctypes.c_uint64),
        ("slot", Slot * SLOTS),
        ("reserved", ctypes.c_uint8 * 512),
    ]


def make_mmap() -> tuple[mmap.mmap, Hdr]:
    path = f"/tmp/kwcapture_race_bisect.{os.getuid()}.shm"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, HDR_SIZE + SLOT_BYTES * SLOTS)
    mm = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)
    os.close(fd)
    h = Hdr.from_buffer(mm)
    h.magic, h.version, h.hdr_size = 0x4B574350, 2, HDR_SIZE
    h.slot_bytes, h.slots, h.ready = SLOT_BYTES, SLOTS, 1
    for i in range(SLOTS):
        s = h.slot[i]
        s.a, s.b, s.c, s.d = W, H, STRIDE, FMT
    return mm, h


def main() -> int:
    mm, h = make_mmap()
    use_ctypes = MODE in ("both", "ctypes")
    use_numpy = MODE in ("both", "numpy", "mmap")

    def view(seq: int):
        if use_ctypes:
            slots = int(h.slots)
            sl = h.slot[(seq - 1) % slots]           # ctypes shadow object, per call
            w, hgt, stride = int(sl.a), int(sl.b), int(sl.c)
        else:
            slots, w, hgt, stride = SLOTS, W, H, STRIDE
        if use_numpy:
            off = HDR_SIZE + ((seq - 1) % slots) * SLOT_BYTES
            arr = np.frombuffer(mm, dtype=np.uint8, count=stride * hgt,
                                offset=off).reshape(hgt, stride // 4, 4)[:, :w, :]
            arr.setflags(write=False)
            return arr
        return None

    n = 0
    bad = 0
    ptrs: set[int] = set()
    t0 = time.perf_counter()
    while n < ITERS:
        try:
            arr = view(n + 1)
            if use_numpy and n % 977 == 0:            # cheap canary
                ptrs.add(arr.ctypes.data)
                if int(arr[0, 0, 0]) != 0:
                    raise AssertionError(f"pixel changed: {int(arr[0, 0, 0])}")
        except Exception as e:  # noqa: BLE001 -- the exception IS the finding
            print(f"CRASH MODE={MODE} at iteration {n} "
                  f"({n / max(1e-9, time.perf_counter() - t0):,.0f} it/s): "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            print(f"  canary: {len(ptrs)} distinct numpy pointers into the mapping; "
                  f"mm alive={not mm.closed}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
        n += 1
    dt = time.perf_counter() - t0
    print(f"OK  MODE={MODE}: {n:,} iters in {dt:.1f}s ({n / dt:,.0f} it/s), "
          f"{len(ptrs)} distinct numpy pointer(s), fields intact: "
          f"{[(int(h.slot[i].a), int(h.slot[i].b), int(h.slot[i].c)) for i in range(SLOTS)]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
