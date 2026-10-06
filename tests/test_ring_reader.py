#!/usr/bin/env python3
"""Unit tests for the shared-memory reader -- no Wayland, no KWin, no daemon.

    python tests/test_ring_reader.py
    pytest tests/test_ring_reader.py

This is the deterministic half of the BUG-4 work (see AGENTS.md): a synthetic ring lets us
put values into the shared header that a live helper would never write, and assert that the
client *refuses* them instead of turning them into an array.  It also asserts the two
guarantees the reader is built on now:

  * one frame's metadata comes from ONE contiguous read of its slot descriptor, and every
    value is bounds-checked against the real mapping before it becomes an offset/count;
  * a frame view keeps its bytes after the Capture is closed/unmapped (frozen, readable),
    and the client never writes into the ring -- the data mapping is read-only.

Everything here runs in CI (no compositor needed), which is the point: BUG-4 was invisible
for three sessions because the only tests that touched this path needed a Plasma session.
"""
from __future__ import annotations

import gc
import mmap
import os
import struct
import sys
import tempfile
import threading
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K  # noqa: E402

FAILED: list[str] = []

SLOTS = 4
HDR = 4096
SLOT_BYTES = 1 << 20
W, H, STRIDE = 64, 8, 256          # stride/4 == W: the full-width case


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)
    return bool(cond)


class FakeRing:
    """A ring file with a 'daemon' (RW) mapping and a Capture reading it (RO)."""

    def __init__(self, path: str):
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
        os.ftruncate(self.fd, HDR + SLOT_BYTES * SLOTS)
        self.daemon = mmap.mmap(self.fd, 0, access=mmap.ACCESS_WRITE)
        self.h = K._Hdr.from_buffer(self.daemon)
        self.h.magic = K.KWC_MAGIC
        self.h.version = K.KWC_VERSION
        self.h.hdr_size = HDR
        self.h.slot_bytes = SLOT_BYTES
        self.h.slots = SLOTS
        self.h.daemon_pid = os.getpid()
        self.h.target = K.KWC_TARGET_SCREEN
        self.h.frame_seq = 0
        self.h.published = 0
        self.h.ready = 1
        # the client, built without ever starting a daemon: its own fd, a read-only data
        # mapping and a header-sized writable control mapping, exactly like _start_once()
        self.client_fd = os.open(path, os.O_RDWR)
        self.ctl = mmap.mmap(self.client_fd, K._KWC_STRUCT_SIZE, access=mmap.ACCESS_WRITE)
        self.cap = K.Capture.__new__(K.Capture)
        self.cap._mm = mmap.mmap(self.client_fd, 0, access=mmap.ACCESS_READ)
        self.cap._ctl = self.ctl
        self.cap._hdr = K._Hdr.from_buffer(self.ctl)
        self.cap._proc = None
        self.cap._fd = self.client_fd
        self.cap._req_fd = -1
        self.cap._gen = 0
        self.cap.stale_check = False
        self.cap.binary = None
        self.cap.window_id = ""
        self.cap.window_name = ""
        self.cap._ring_slots, self.cap._ring_hdr_size = SLOTS, HDR
        self.cap._ring_slot_bytes, self.cap._ring_len = SLOT_BYTES, len(self.cap._mm)

    def publish(self, seq: int, *, w=W, h=H, stride=STRIDE, fmt=6, status=0,
                fill=None) -> None:
        """Write one frame the way the helper does: pixels, descriptor, then frame_seq."""
        idx = (seq - 1) % SLOTS
        count = stride * h if not status else 0
        if count:
            off = HDR + idx * SLOT_BYTES
            pat = (bytes(fill) * (count // len(fill) + 1))[:count] if fill else \
                  (bytes(((seq * 7 + i) & 0xFF for i in range(min(count, 4096))))
                   * (count // 4096 + 1))[:count]
            self.daemon[off:off + count] = pat
        sl = self.h.slot[idx]
        sl.status = status
        sl.width = 0 if status else w
        sl.height = 0 if status else h
        sl.stride = 0 if status else stride
        sl.format = fmt
        sl.ts_ns = time.time_ns()
        self.daemon.flush()
        self.h.published = seq
        self.h.frame_seq = seq

    def close(self) -> None:
        for obj in (self.cap._mm, self.daemon, self.ctl):
            try:
                if obj is not None:
                    obj.close()
            except (BufferError, ValueError):
                pass
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.unlink(self.path)
        except OSError:
            pass


def _raises(fn, *kinds):
    """(did_it_raise, exception_or_None) -- kinds are exception classes."""
    try:
        fn()
    except kinds as e:            # type: ignore[misc]
        return True, e
    except Exception as e:        # noqa: BLE001 - anything else is a test failure
        return False, e
    return False, None


def geometry_section():
    print("\n== valid frames through the real reader ==")
    with tempfile.TemporaryDirectory() as td:
        ring = FakeRing(os.path.join(td, "ok.shm"))
        try:
            ring.publish(1, fill=b"\xde\xad\xbe\xef")
            arr = ring.cap._view(1, rgb=False, copy=False)
            check("_view returns the bytes the daemon wrote",
                  arr.shape == (H, W, 4) and arr[0, 0].tolist() == [0xDE, 0xAD, 0xBE, 0xEF],
                  f"{arr.shape} {arr[0, 0].tolist()}")
            check("frame views are read-only (data mapping is ACCESS_READ)",
                  not arr.flags.writeable)
            check("zero-copy: two views of a frame are the same memory, not a copy",
                  arr.ctypes.data == ring.cap._view(1, rgb=False,
                                                   copy=False).ctypes.data)
            rgb = ring.cap._view(1, rgb=True, copy=False)
            check("rgb=True takes bytes 2,1,0 (BGRA -> RGB) without copying",
                  rgb.shape == (H, W, 3) and rgb[0, 0].tolist() == [0xBE, 0xAD, 0xDE],
                  f"{rgb.shape} {rgb[0, 0].tolist()}")
            check("the rgb view is the ring's memory, not a copy",
                  rgb.ctypes.data == arr.ctypes.data + 2)
            cp = ring.cap._view(1, rgb=False, copy=True)
            check("copy=True is writable and independent",
                  cp.flags.writeable and cp[0, 0].tolist() == [0xDE, 0xAD, 0xBE, 0xEF])
            cp[0, 0] = 0
            check("writing the copy does not touch the ring",
                  ring.cap._view(1, rgb=False, copy=False)[0, 0].tolist()
                  == [0xDE, 0xAD, 0xBE, 0xEF])
            check("_frame_seq reads the counter", ring.cap._frame_seq() == 1)
            d1 = ring.cap._descriptor(1)
            check("_descriptor is one _SLOT_SIZE read of the slot's own descriptor",
                  len(d1) == K._SLOT_SIZE
                  and (K._u32(d1, 0), K._u32(d1, 4), K._u32(d1, 8),
                       K._u32(d1, K._SLOT_OFF["format"])) == (W, H, STRIDE, 6),
                  f"{len(d1)} bytes")
            check("a different sequence reads a different slot",
                  ring.cap._descriptor(SLOTS + 1) == d1
                  and ring.cap._descriptor(2) != d1)
        finally:
            ring.close()


def validation_section():
    """The BUG-4 guardrails: a bad descriptor must raise, never become an array."""
    print("\n== invalid ring metadata is refused, not read ==")
    with tempfile.TemporaryDirectory() as td:
        ring = FakeRing(os.path.join(td, "bad.shm"))
        try:
            # geometry that does not fit its own stride
            ring.publish(1)
            idx = 0
            so = K._SLOT_ARRAY_OFF + idx * K._SLOT_SIZE
            rw = mmap.mmap(ring.fd, 0, access=mmap.ACCESS_WRITE)

            def poke(off_from_slot: int, value: int) -> None:
                struct.pack_into("@I", rw, so + off_from_slot, value)

            # w > stride/4  (torn width vs stride)
            poke(K._SLOT_OFF["width"], W + 8)
            ok, e = _raises(lambda: ring.cap._view(1, rgb=False, copy=False),
                            K.CaptureError)
            check("width larger than the stride raises instead of clipping",
                  ok, f"{type(e).__name__}: {e}")
            poke(K._SLOT_OFF["width"], W)

            # stride not a multiple of 4
            poke(K._SLOT_OFF["stride"], STRIDE - 1)
            ok, e = _raises(lambda: ring.cap._view(1, rgb=False, copy=False),
                            K.CaptureError)
            check("a stride that is not a multiple of 4 raises", ok,
                  f"{type(e).__name__}: {e}")
            poke(K._SLOT_OFF["stride"], STRIDE)

            # geometry bigger than the slot / the mapping
            poke(K._SLOT_OFF["height"], SLOT_BYTES // 4)
            ok, e = _raises(lambda: ring.cap._view(1, rgb=False, copy=False),
                            K.CaptureError)
            check("a frame bigger than the slot raises instead of reading past it",
                  ok, f"{type(e).__name__}: {e}")
            poke(K._SLOT_OFF["height"], H)

            # zero geometry with status 0
            poke(K._SLOT_OFF["width"], 0)
            ok, e = _raises(lambda: ring.cap._view(1, rgb=False, copy=False),
                            K.CaptureError)
            check("zero geometry with status 0 raises 'no geometry'", ok,
                  f"{type(e).__name__}: {e}")
            poke(K._SLOT_OFF["width"], W)

            # a failed frame maps to the right exception class
            ring.publish(2, status=K.KWC_ERR_INVALID_WINDOW)
            ok, e = _raises(lambda: ring.cap._view(2, rgb=False, copy=False),
                            K.WindowGone)
            check("KWC_ERR_INVALID_WINDOW surfaces as WindowGone", ok,
                  f"{type(e).__name__}: {e}")
            check("the helper's message survives the rewrite",
                  "no longer exists" in str(e), str(e))
            check("a good frame still reads after four bad ones",
                  ring.cap._view(1, rgb=False, copy=False).shape == (H, W, 4))
            rw.close()
        finally:
            ring.close()

    print("\n== ring geometry is validated at attach time ==")
    good = (SLOTS, HDR, SLOT_BYTES, HDR + SLOT_BYTES * SLOTS)
    ok, e = _raises(lambda: K._check_ring_geometry(*good), K.CaptureError)
    check("a sane ring is accepted", not ok, f"{type(e).__name__ if e else ''}")
    for bad, why in (
        ((0, HDR, SLOT_BYTES, 1 << 24), "zero slots"),
        ((K.KWC_MAX_SLOTS + 1, HDR, SLOT_BYTES, 1 << 24), "more slots than the ABI allows"),
        ((SLOTS, 8, SLOT_BYTES, 1 << 24), "header smaller than the struct"),
        ((SLOTS, HDR, 0, 1 << 24), "zero-sized slot"),
        ((SLOTS, HDR, 1 << 22, HDR + (1 << 20)), "slots beyond the end of the file"),
    ):
        ok, e = _raises(lambda b=bad: K._check_ring_geometry(*b), K.CaptureError)
        check(f"refuses {why}", ok, f"{type(e).__name__ if e else ''}")


def lifetime_section():
    """BUG-4's lifetime half: what happens to a view when the ring goes away."""
    print("\n== a view outlives the Capture that made it ==")
    with tempfile.TemporaryDirectory() as td:
        ring = FakeRing(os.path.join(td, "life.shm"))
        try:
            ring.publish(3, fill=b"\x11\x22\x33\x44")
            view = ring.cap._view(3, rgb=False, copy=False)
            before = view[0, 0].tolist()
            gen = ring.cap._gen
            ring.cap._unmap()                     # what close() does to the mappings
            check("_unmap bumps the generation", ring.cap._gen == gen + 1)
            check("the outstanding view is still readable",
                  view[0, 0].tolist() == before, f"{view[0, 0].tolist()}")
            check("reading it does not resurrect the Capture",
                  ring.cap._mm is None and ring.cap._ring_slots == 0)
            ok, e = _raises(lambda: ring.cap._view(4, rgb=False, copy=False),
                            K.CaptureError)
            check("a new read after unmap raises 'capture not started'", ok,
                  f"{type(e).__name__}: {e}")
            gc.collect()
            check("still readable after a gc pass", view[0, 0].tolist() == before)
            del view
        finally:
            ring.close()


def race_section(seconds: float = 4.0):
    """A writer mutating the ring while the reader reads it: no crash, no impossible frame.

    This is the CI-runnable stand-in for BUG-4: it cannot fix the interpreter/numpy bug
    (see probe/corruption_rate.py) but it does exercise the exact read path with a live
    writer, including descriptors that are only ever briefly valid.
    """
    print("\n== concurrent writer stress ==")
    with tempfile.TemporaryDirectory() as td:
        ring = FakeRing(os.path.join(td, "race.shm"))
        stop = threading.Event()
        seq = [0]

        def writer() -> None:
            n = 0
            while not stop.is_set():
                n += 1
                # a mix of valid frames and frames a racing helper could leave behind
                ring.publish(1 + n % 1000, w=W, h=H, stride=STRIDE)
                if n % 7 == 0:
                    ring.publish(1 + n % 1000, status=K.KWC_ERR_EMPTY_FRAME)

        seen = {"frames": 0, "refused": 0, "bad": 0}
        th = threading.Thread(target=writer, daemon=True)
        th.start()
        t_end = time.monotonic() + seconds
        try:
            while time.monotonic() < t_end:
                s = ring.cap._frame_seq()
                try:
                    arr = ring.cap._view(s, rgb=False, copy=False)
                except K.CaptureError:
                    seen["refused"] += 1
                    continue
                except Exception as e:  # noqa: BLE001
                    seen["bad"] += 1
                    if seen["bad"] == 1:
                        print(f"       unexpected {type(e).__name__}: {e}")
                    continue
                if arr.ndim != 3 or arr.shape[2] != 4:
                    seen["bad"] += 1
                    if seen["bad"] == 1:
                        print(f"       impossible frame: shape={arr.shape} dtype={arr.dtype} "
                              f"(the reader can only build (h, w, 4))")
                else:
                    seen["frames"] += 1
                _ = int(arr[0, 0, 0])
        finally:
            stop.set()
            th.join(timeout=5)
            ring.close()
        check("survived a concurrent writer", seen["bad"] == 0,
              f"{seen['frames']} frames, {seen['refused']} cleanly refused, "
              f"{seen['bad']} invalid")


def main() -> int:
    print("== kwcapture ring reader (no compositor needed) ==")
    print(f"  python {sys.version.split()[0]}, numpy {np.__version__}, "
          f"kwcapture {K.__version__}")
    geometry_section()
    validation_section()
    lifetime_section()
    race_section(3.0 if "quick" in sys.argv else 6.0)
    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print("RESULT: all ring-reader tests passed")
    return 0


def test_ring_reader():
    """pytest entry point."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
