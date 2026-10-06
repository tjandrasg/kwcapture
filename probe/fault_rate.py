"""How many zero-copy reads until the interpreter/numpy fault, for a given kwcapture?

    PYTHONPATH=/path/to/kwcapture KWC_ITERS=60000000 .venv/bin/python -X dev probe/fault_rate.py

Hammers `Capture.latest(rgb=True)` -- the call BUG-4 was originally reported on -- and
prints a progress line every KWC_STEP reads so a SIGSEGV still leaves a count behind.
Compare two checkouts (e.g. the pre-0.4.0 `_view()` and the new one) by pointing
PYTHONPATH at each; run the same number of rounds and look at iterations-to-fault.

Exit 0 = survived the whole run (the count is printed); the process dying is the fault.
Nothing here is a kwcapture bug: see probe/race_bisect.py / probe/corruption_rate.py and
AGENTS.md BUG-4 -- the fault reproduces with numpy over an mmap and no kwcapture at all.
"""
from __future__ import annotations

import gc
import os
import sys
import time

import numpy as np

import kwcapture as K

ITERS = int(os.environ.get("KWC_ITERS", "60000000"))
STEP = int(os.environ.get("KWC_STEP", "5000000"))


def main() -> int:
    print(f"kwcapture {K.__version__} from {os.path.dirname(K.__file__)}; "
          f"numpy {np.__version__}; python {sys.version.split()[0]}; "
          f"target {ITERS:,} reads", flush=True)
    cap = K.Capture(shm=K.default_shm_path("fault_rate"))
    geom = cap.geometry()
    n = 0
    t0 = time.perf_counter()
    try:
        while n < ITERS:
            for _ in range(STEP):
                a = cap.latest(rgb=True)
                # cheap structural self-check: a wrong shape/dtype is also a fault
                if a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8:
                    print(f"BAD FRAME at {n}: shape={a.shape} dtype={a.dtype}", flush=True)
                    return 1
            n += STEP
            print(f"  {n:,} reads, {n / (time.perf_counter() - t0):,.0f} it/s, "
                  f"ok", flush=True)
            gc.collect()
    finally:
        try:
            cap.close()
        except Exception:
            pass
    print(f"SURVIVED {n:,} zero-copy reads in "
          f"{time.perf_counter() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
