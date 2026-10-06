"""kwcapture - fast Wayland screen capture for KDE Plasma, from Python.

    import kwcapture
    cap = kwcapture.Capture()                # starts the daemon, ~1 frame ready
    arr = cap.grab()                         # (H, W, 4) BGRA view of the newest frame
    rgb = cap.shot()                         # (H, W, 3) RGB, optionally downscaled
    cap.close()

How it works
------------
KWin (the KDE compositor) exposes `org.kde.KWin.ScreenShot2` on D-Bus; it writes raw
ARGB32-premultiplied pixels (== BGRA on little endian) into a file descriptor we give it.
KWin only authorises callers whose `/proc/<pid>/exe` matches a `.desktop` file that
declares `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2`, so the capture is
done by a small native helper (`bin/kwcapture`, see AGENTS.md) rather than by Python.

`Capture` spawns `bin/kwcapture serve`, which keeps a D-Bus connection open and writes
each frame into a shared-memory ring.  A grab is therefore one request byte, a spin on a
sequence counter and a zero-copy numpy view - no subprocess per frame, no serialisation.

Measured on a 2560x1440@165Hz Plasma 6.6 session: ~18ms in the compositor + ~5ms to move
14MB => ~45 fps full resolution (PIL/spectacle on the same box: ~2 fps).
"""

from __future__ import annotations

import ctypes
import errno
import mmap
import os
import subprocess
import sys
import tempfile
import time
from ctypes import c_char, c_double, c_uint32, c_uint64, c_uint8
from typing import Optional

import numpy as np

from . import _desktop, _native
from ._desktop import install_desktop_file
from ._native import NativeBuildError, ensure_binary, find_binary

__version__ = "0.1.0"

__all__ = [
    "Capture",
    "grab",
    "shot",
    "list_screens",
    "to_rgb",
    "resize",
    "png_bytes",
    "jpeg_bytes",
    "cv2_module",
    "find_binary",
    "ensure_binary",
    "install_desktop_file",
    "NativeBuildError",
    "CaptureError",
    "DaemonDead",
    "__version__",
]

KWC_MAGIC = 0x4B574350  # "KWCP"
KWC_MAGIC_GONE = 0x4B574347  # "KWCG"
KWC_VERSION = 1
KWC_MAX_SLOTS = 8
_KWC_STRUCT_SIZE = 1776  # must match sizeof(kwc_hdr_t)/KWC_HDR_STRUCT_SIZE

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BINARY = None  # resolved by find_binary()/ensure_binary(); kept for compatibility

_FORMAT_NAMES = {
    4: "RGB32",
    5: "ARGB32",
    6: "ARGB32_Premultiplied",  # BGRA bytes on little endian - what we get
    11: "RGBX8888",
    12: "RGBA8888_Premultiplied",
    13: "RGBA8888",
}


class CaptureError(RuntimeError):
    pass


class DaemonDead(CaptureError):
    pass


class _Slot(ctypes.Structure):
    _fields_ = [
        ("width", c_uint32),
        ("height", c_uint32),
        ("stride", c_uint32),
        ("format", c_uint32),
        ("scale", c_double),
        ("grab_ms", c_double),
        ("total_ms", c_double),
        ("ts_ns", c_uint64),
        ("screen", c_char * 64),
        ("pad", c_uint32 * 6),
    ]


class _Hdr(ctypes.Structure):
    _fields_ = [
        ("magic", c_uint32),
        ("version", c_uint32),
        ("hdr_size", c_uint32),
        ("slot_bytes", c_uint32),
        ("slots", c_uint32),
        ("ready", c_uint32),
        ("quit", c_uint32),
        ("error", c_uint32),
        ("daemon_pid", c_uint32),
        ("capture_pid", c_uint32),
        ("pad2", c_uint32 * 2),
        ("req_seq", c_uint64),
        ("frame_seq", c_uint64),
        ("published", c_uint64),
        ("width", c_uint32),
        ("height", c_uint32),
        ("stride", c_uint32),
        ("format", c_uint32),
        ("scale", c_double),
        ("screen", c_char * 64),
        ("depth", c_uint32),
        ("pad3", c_uint32),
        ("fps", c_double),
        ("slot", _Slot * KWC_MAX_SLOTS),
        ("reserved", c_uint8 * 512),
    ]


assert ctypes.sizeof(_Hdr) == _KWC_STRUCT_SIZE, (
    f"kwcapture: header layout mismatch (python {ctypes.sizeof(_Hdr)} != "
    f"expected {_KWC_STRUCT_SIZE}); rebuild against include/kwcapture_shm.h"
)


def default_shm_path(tag: str = "") -> str:
    """A private tmpfs path for the ring buffer."""
    base = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    suffix = f"-{tag}" if tag else ""
    return os.path.join(base, f"kwcapture-{os.getuid()}{suffix}.shm")


def list_screens(binary: Optional[str] = None) -> list[dict]:
    """Outputs known to the compositor: [{'name','width','height','refresh','x','y','scale'}]."""
    binary = str(_native.resolve(binary))
    out = subprocess.run([binary, "--list"], capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise CaptureError(out.stderr.strip() or "kwcapture --list failed")
    screens = []
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        w, h = parts[1].split("x")
        screens.append(
            dict(name=parts[0], width=int(w), height=int(h), refresh=float(parts[2]),
                 x=int(parts[3]), y=int(parts[4]), scale=int(parts[5]))
        )
    return screens


class Capture:
    """Grab frames from KWin through a resident helper process.

    Parameters
    ----------
    screen : str, optional   output name (see list_screens()); default = active screen
    area : (x, y, w, h), optional   capture only this region (logical coords)
    workspace : bool         capture the entire virtual desktop
    cursor : bool            include the hardware cursor
    decoration : bool        include window decorations and shadows
    hide_caller_windows : bool   KWin hides our own windows by default (True keeps that)
    slots : int              ring depth (frames kept before reuse)
    depth : int              concurrent requests in flight to KWin (throughput)
    fps : float, optional    if set, the daemon captures continuously at this rate
    shm : str, optional      shared memory path (default: private path in $XDG_RUNTIME_DIR)
    binary : str, optional   path to the helper (default: find or build it)
    allow_build : bool       compile the helper on first use if it is not shipped
    install_desktop : bool   write the KDE desktop entry that authorises the helper
    verbose : bool           report build / authorisation steps on stderr
    """

    def __init__(
        self,
        screen: Optional[str] = None,
        area: Optional[tuple[int, int, int, int]] = None,
        workspace: bool = False,
        cursor: bool = False,
        decoration: bool = False,
        hide_caller_windows: bool = True,
        slots: int = 4,
        depth: int = 2,
        fps: Optional[float] = None,
        shm: Optional[str] = None,
        binary: Optional[str] = None,
        allow_build: bool = True,
        install_desktop: bool = True,
        verbose: bool = False,
        idle_exit: float = 300.0,
        start_timeout: float = 20.0,
        daemon_stderr=None,
        autostart: bool = True,
    ) -> None:
        self.verbose = verbose
        try:
            self.binary = str(_native.resolve(binary, allow_build=allow_build))
        except NativeBuildError as e:
            raise CaptureError(str(e)) from e
        self.install_desktop = install_desktop
        self._log_file = None
        if install_desktop and not _desktop.is_installed(self.binary):
            try:
                _desktop.install_desktop_file(self.binary, verbose=verbose)
            except OSError as e:  # read-only $HOME etc: capture may still work
                print(f"kwcapture: could not write the KDE authorisation file: {e}",
                      file=sys.stderr)
        self.screen = screen
        self.area = tuple(area) if area else None
        self.workspace = workspace
        self.cursor = cursor
        self.shm_path = shm or default_shm_path()
        self.req_path = self.shm_path + ".req"  # FIFO used to wake the daemon
        self._req_fd = -1
        self._proc: Optional[subprocess.Popen] = None
        self._mm: Optional[mmap.mmap] = None
        self._fd = -1
        self._hdr: Optional[_Hdr] = None
        self._daemon_stderr = daemon_stderr
        self.idle_exit = idle_exit
        self._slots = slots
        self._depth = depth
        self._fps = fps
        self.hide_caller_windows = hide_caller_windows
        self.decoration = decoration
        self.start_timeout = start_timeout
        if autostart:
            self.start()

    # -------------------------------------------------------------- lifecycle
    def _argv(self) -> list[str]:
        argv = [self.binary, "serve", "--shm", self.shm_path,
                "--slots", str(self._slots), "--depth", str(self._depth),
                "--idle-exit", str(self.idle_exit)]
        if self.area:
            argv += ["--area", ",".join(str(int(v)) for v in self.area)]
        elif self.screen:
            argv += ["--screen", self.screen]
        if self.workspace:
            argv += ["--workspace"]
        if self.cursor:
            argv += ["--cursor"]
        if self.decoration:
            argv += ["--decoration"]
        if not self.hide_caller_windows:
            argv += ["--no-hide-caller"]
        if self._fps:
            argv += ["--fps", str(self._fps)]
        return argv

    # KService picks up a new desktop entry asynchronously, so after writing one we may
    # have to wait for KWin to agree with us.
    _AUTH_RETRY_DELAYS = (0.1, 0.3, 0.6, 1.0, 1.5)

    def start(self) -> None:
        """Spawn the daemon and map the ring.

        If KWin refuses us because the authorising desktop entry is missing - or has not
        been noticed by KDE's service cache yet - we (re)write it and retry with backoff.
        """
        attempts = len(self._AUTH_RETRY_DELAYS) + 1 if self.install_desktop else 1
        for attempt in range(attempts):
            try:
                self._start_once()
                return
            except CaptureError as e:
                if attempt + 1 >= attempts or "authoriz" not in str(e).lower():
                    raise
                delay = self._AUTH_RETRY_DELAYS[min(attempt, len(self._AUTH_RETRY_DELAYS) - 1)]
                if self.verbose:
                    print(f"kwcapture: KWin refused the request; refreshing the desktop "
                          f"entry and retrying in {delay:.1f}s", file=sys.stderr)
                _desktop.install_desktop_file(self.binary, refresh=(attempt % 2 == 0),
                                              verbose=self.verbose)
                time.sleep(delay)

    def _daemon_log_tail(self, lines: int = 6) -> str:
        try:
            with open(self.shm_path + ".log", "r", errors="replace") as f:
                return " ; ".join(f.read().splitlines()[-lines:])
        except OSError:
            return ""

    def _start_once(self) -> None:
        """One daemon launch attempt; the helper's stderr goes to <shm>.log."""
        self.close_daemon()
        self._log_file = None
        stderr_target = self._daemon_stderr
        if stderr_target is None:
            try:
                self._log_file = open(self.shm_path + ".log", "w")
                stderr_target = self._log_file
            except OSError:
                stderr_target = subprocess.DEVNULL
        proc = subprocess.Popen(self._argv(), stdout=subprocess.DEVNULL,
                                stderr=stderr_target)
        self._proc = proc
        deadline = time.monotonic() + self.start_timeout
        while True:
            if proc.poll() is not None:
                detail = self._daemon_log_tail()
                raise CaptureError(
                    f"kwcapture daemon exited with code {proc.returncode} while starting"
                    + (f":\n  {detail}" if detail
                       else "\n  (authorisation? run `kwcapture install-desktop`)")
                )
            try:
                size = os.path.getsize(self.shm_path)
            except OSError:
                size = 0
            if size >= ctypes.sizeof(_Hdr):
                break
            if time.monotonic() > deadline:
                raise CaptureError("timed out waiting for the kwcapture daemon")
            time.sleep(0.002)

        self._fd = os.open(self.shm_path, os.O_RDWR)
        self._mm = mmap.mmap(self._fd, 0, access=mmap.ACCESS_WRITE)
        self._hdr = _Hdr.from_buffer(self._mm)
        hdr = self._hdr
        deadline = time.monotonic() + self.start_timeout
        while hdr.magic != KWC_MAGIC or not hdr.ready:
            if hdr.magic == KWC_MAGIC_GONE:
                break
            if proc.poll() is not None:
                raise CaptureError("kwcapture daemon died during startup")
            if time.monotonic() > deadline:
                raise CaptureError("timed out waiting for the first frame")
            time.sleep(0.002)
        if hdr.version != KWC_VERSION:
            raise CaptureError(f"unsupported kwcapture ABI {hdr.version}")
        self._open_req_channel()

    def _open_req_channel(self) -> None:
        """Open the daemon's request FIFO for writing (needs the reader to exist)."""
        deadline = time.monotonic() + self.start_timeout
        while True:
            try:
                self._req_fd = os.open(self.req_path, os.O_WRONLY | os.O_NONBLOCK)
                return
            except OSError:
                if time.monotonic() > deadline or (self._proc and self._proc.poll() is not None):
                    raise CaptureError(f"cannot open request channel {self.req_path}")
                time.sleep(0.002)

    def _poke(self) -> None:
        """Nudge the daemon out of poll(); the request itself is in shared memory."""
        if self._req_fd < 0:
            self._open_req_channel()
            return
        try:
            os.write(self._req_fd, b"1")
        except BlockingIOError:
            pass  # fifo full: the daemon will pick the request up on its next wake
        except OSError:
            self._req_fd = -1
            self._open_req_channel()

    def restart(self) -> None:
        self.start()

    def close_daemon(self) -> None:
        """Stop the daemon (leaves the mapping alone)."""
        if self._req_fd >= 0:
            try:
                os.close(self._req_fd)
            except OSError:
                pass
            self._req_fd = -1
        if self._hdr is not None and self._hdr.magic == KWC_MAGIC:
            self._hdr.quit = 1
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self._proc = None

    def close(self) -> None:
        self.close_daemon()
        for attr, closer in (("_hdr", None), ("_mm", "close")):
            obj = getattr(self, attr)
            if obj is not None:
                if closer:
                    try:
                        obj.close()
                    except (BufferError, ValueError):
                        pass
                setattr(self, attr, None)
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = -1
        if self._log_file is not None:
            try:
                self._log_file.close()
            except OSError:
                pass
            self._log_file = None
        for path in (self.shm_path, self.req_path, self.shm_path + ".log"):
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except OSError:
                pass

    def __enter__(self) -> "Capture":
        return self

    def __exit__(self, *exc) -> bool:
        self.close()
        return False

    def __del__(self) -> None:  # pragma: no cover
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ state
    @property
    def alive(self) -> bool:
        return (
            self._proc is not None
            and self._proc.poll() is None
            and self._hdr is not None
            and self._hdr.magic == KWC_MAGIC
        )

    def geometry(self) -> tuple[int, int]:
        h = self._require()
        return int(h.width), int(h.height)

    @property
    def screen_name(self) -> str:
        h = self._require()
        return h.screen.decode() if isinstance(h.screen, bytes) else str(h.screen)

    def stats(self) -> dict:
        """Timings of the most recently published frame."""
        h = self._require()
        seq = int(h.frame_seq)
        sl = h.slot[(seq - 1) % int(h.slots)]
        return dict(
            seq=seq,
            published=int(h.published),
            width=int(sl.width),
            height=int(sl.height),
            stride=int(sl.stride),
            format=_FORMAT_NAMES.get(int(sl.format), int(sl.format)),
            scale=float(sl.scale),
            grab_ms=float(sl.grab_ms),
            total_ms=float(sl.total_ms),
            age_ms=(time.monotonic_ns() - int(sl.ts_ns)) / 1e6,
            screen=sl.screen.decode() if isinstance(sl.screen, bytes) else sl.screen,
            pid=int(h.daemon_pid),
        )

    def _require(self) -> _Hdr:
        if self._hdr is None:
            raise CaptureError("capture not started")
        return self._hdr

    def _check_error(self) -> None:
        h = self._hdr
        assert h is not None
        if h.error:
            raise CaptureError(f"daemon error: {os.strerror(int(h.error))}")
        if h.magic == KWC_MAGIC_GONE or (self._proc and self._proc.poll() is not None):
            raise DaemonDead("kwcapture daemon is no longer running")

    # ------------------------------------------------------------------ frames
    def _view(self, seq: int, rgb: bool, copy: bool) -> np.ndarray:
        h = self._hdr
        assert h is not None
        slots = int(h.slots)
        sl = h.slot[(seq - 1) % slots]
        w, hgt, stride = int(sl.width), int(sl.height), int(sl.stride)
        if w == 0 or hgt == 0:
            raise CaptureError("frame has no geometry")
        off = int(h.hdr_size) + ((seq - 1) % slots) * int(h.slot_bytes)
        arr = np.frombuffer(
            self._mm, dtype=np.uint8, count=stride * hgt, offset=off
        ).reshape(hgt, stride // 4, 4)[:, :w, :]
        if rgb:
            if int(sl.format) not in (4, 5, 6, 11, 12, 13):
                raise CaptureError(f"unhandled pixel format {sl.format}")
            arr = arr[..., 2::-1]  # BGRA -> RGB, zero copy (negative strides)
        arr = arr.copy() if copy else arr
        arr.setflags(write=copy)
        return arr

    def grab(
        self,
        timeout: float = 2.0,
        rgb: bool = False,
        copy: bool = False,
        fresh: bool = True,
    ) -> np.ndarray:
        """Return a frame as an (H, W, 4) BGRA or (H, W, 3) RGB uint8 array.

        With copy=False (default) the array is a *view* of the shared ring: it is
        overwritten once `slots` more frames arrive, so `copy=True` (or `.copy()`)
        if you need to keep it.  With fresh=False the newest already-captured frame
        is returned immediately (no compositor round-trip).
        """
        h = self._require()
        self._check_error()
        seq = int(h.frame_seq)
        if fresh:
            want = seq + 1
            h.req_seq = want
            self._poke()
            deadline = time.monotonic() + timeout
            spins = 0
            while int(h.frame_seq) < want:
                self._check_error()
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"no frame within {timeout}s (daemon alive={self.alive})"
                    )
                spins += 1
                if spins > 200:
                    time.sleep(0.0002)
                else:
                    sched_yield()
            seq = want
        return self._view(seq, rgb, copy)

    def latest(self, rgb: bool = False, copy: bool = False) -> np.ndarray:
        """Newest published frame without asking the compositor for a new one."""
        return self.grab(rgb=rgb, copy=copy, fresh=False)

    def shot(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        resample: str = "area",
        timeout: float = 2.0,
    ) -> np.ndarray:
        """Grab and return a contiguous RGB array, optionally downscaled (for vision models).

        ~26 ms end to end for 1280 px wide on a 2560x1440 Plasma 6.6 desktop (with OpenCV).
        """
        arr = self.grab(timeout=timeout)
        return to_rgb(arr, width=width, height=height, resample=resample)

    def shot_png(self, width: Optional[int] = None, **kw) -> bytes:
        return png_bytes(self.shot(width=width, **kw))

    def shot_jpeg(self, width: Optional[int] = None, quality: int = 85, **kw) -> bytes:
        return jpeg_bytes(self.shot(width=width, **kw), quality=quality)

    # -------------------------------------------------------------- throughput
    def bench(self, frames: int = 60, rgb: bool = False, warmup: int = 3) -> dict:
        for _ in range(warmup):
            self.grab(rgb=rgb)
        lat = []
        t0 = time.perf_counter()
        for _ in range(frames):
            s = time.perf_counter()
            self.grab(rgb=rgb)
            lat.append((time.perf_counter() - s) * 1e3)
        wall = time.perf_counter() - t0
        lat.sort()
        return dict(
            frames=frames,
            fps=frames / wall,
            mean_ms=sum(lat) / len(lat),
            median_ms=lat[len(lat) // 2],
            p95_ms=lat[int(len(lat) * 0.95)],
            min_ms=lat[0],
            max_ms=lat[-1],
        )


# --------------------------------------------------------------------- helpers
_cv2: object | bool | None = None


def cv2_module():
    """OpenCV if importable (much faster resize/encode than Pillow), else None."""
    global _cv2
    if _cv2 is None:
        try:
            import cv2  # type: ignore

            _cv2 = cv2
        except Exception:
            _cv2 = False
    return _cv2 or None


def _target_size(h: int, w: int, width: Optional[int], height: Optional[int]):
    if width and not height:
        height = max(1, round(h * width / w))
    elif height and not width:
        width = max(1, round(w * height / h))
    if not width and not height:
        return w, h
    return int(width or w), int(height or h)


_INTERP = {
    "area": "INTER_AREA",
    "box": "INTER_AREA",
    "nearest": "INTER_NEAREST",
    "bilinear": "INTER_LINEAR",
    "bicubic": "INTER_CUBIC",
    "lanczos": "INTER_LANCZOS4",
}


_warned_no_resizer = False


def _resize_numpy(arr: np.ndarray, tw: int, th: int) -> np.ndarray:
    """Dependency-free downscale: box-average on exact integer factors, else nearest."""
    global _warned_no_resizer
    if not _warned_no_resizer:
        _warned_no_resizer = True
        import warnings

        warnings.warn(
            "install 'kwcapture[fast]' (OpenCV) or Pillow for much better/faster "
            "downscaling; falling back to numpy",
            RuntimeWarning,
            stacklevel=3,
        )
    h, w = arr.shape[:2]
    if tw <= 0 or th <= 0:
        raise ValueError("bad target size")
    if h % th == 0 and w % tw == 0:
        fy, fx = h // th, w // tw
        blocks = arr.reshape(th, fy, tw, fx, arr.shape[2])
        return (blocks.sum(axis=(1, 3), dtype=np.uint32) // (fy * fx)).astype(np.uint8)
    yi = (np.arange(th) * h // th).astype(np.intp)
    xi = (np.arange(tw) * w // tw).astype(np.intp)
    return arr[yi][:, xi]


def to_rgb(
    bgra: np.ndarray,
    width: Optional[int] = None,
    height: Optional[int] = None,
    resample: str = "area",
) -> np.ndarray:
    """BGRA (H,W,4) view -> contiguous RGB (H,W,3), optionally downscaled.

    Uses OpenCV when available: INTER_AREA on the raw 4-channel buffer plus a vectorised
    BGRA->RGB conversion is roughly 8x faster than doing it with Pillow/numpy.
    """
    if bgra.ndim != 3 or bgra.shape[2] not in (3, 4):
        raise ValueError(f"expected (H,W,4) BGRA or (H,W,3), got {bgra.shape}")
    h, w = bgra.shape[:2]
    tw, th = _target_size(h, w, width, height)
    cv2 = cv2_module()
    if cv2 is not None and bgra.flags["C_CONTIGUOUS"]:
        if (tw, th) != (w, h):
            small = cv2.resize(bgra, (tw, th), interpolation=getattr(cv2, _INTERP[resample]))
        else:
            small = bgra
        if small.shape[2] == 4:
            return cv2.cvtColor(small, cv2.COLOR_BGRA2RGB)
        return cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    # no OpenCV: Pillow if present, otherwise a pure-numpy resize
    rgb = bgra[..., 2::-1] if bgra.shape[2] == 4 else bgra
    if (tw, th) == (w, h):
        return np.ascontiguousarray(rgb)
    try:
        import PIL  # noqa: F401
    except ImportError:
        return np.ascontiguousarray(_resize_numpy(rgb, tw, th))
    return resize(np.ascontiguousarray(rgb), width=tw, height=th, resample=resample)


_sched_yield = None


def sched_yield() -> None:
    global _sched_yield
    if _sched_yield is None:
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            _sched_yield = libc.sched_yield
        except OSError:  # pragma: no cover
            _sched_yield = lambda: time.sleep(0)  # noqa: E731
    _sched_yield()


def resize(arr: np.ndarray, width: Optional[int] = None, height: Optional[int] = None,
           resample: str = "area") -> np.ndarray:
    """Downscale (H,W,3) RGB array; returns a contiguous array."""
    from PIL import Image

    h, w = arr.shape[:2]
    if width and not height:
        height = max(1, round(h * width / w))
    elif height and not width:
        width = max(1, round(w * height / h))
    if (width, height) == (w, h):
        return np.ascontiguousarray(arr)
    mode = {"area": Image.Resampling.BOX, "nearest": Image.Resampling.NEAREST,
            "lanczos": Image.Resampling.LANCZOS, "bilinear": Image.Resampling.BILINEAR}[
        resample
    ]
    img = Image.fromarray(np.ascontiguousarray(arr), "RGB").resize(
        (int(width), int(height)), mode
    )
    return np.asarray(img, dtype=np.uint8)


def _pil(arr: np.ndarray):
    try:
        from PIL import Image
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "image encoding needs Pillow or OpenCV:  pip install 'kwcapture[pil]' "
            "or 'kwcapture[fast]'"
        ) from e

    if arr.ndim == 3 and arr.shape[2] == 3:
        return Image.fromarray(arr, "RGB")
    if arr.ndim == 3 and arr.shape[2] == 4:  # BGRA view
        return Image.fromarray(np.ascontiguousarray(arr[..., 2::-1]), "RGB")
    return Image.fromarray(arr, "L")


def png_bytes(arr: np.ndarray) -> bytes:
    cv2 = cv2_module()
    if cv2 is not None:
        ok, buf = cv2.imencode(".png", arr, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        if ok:
            return buf.tobytes()
    import io

    bio = io.BytesIO()
    _pil(arr).save(bio, "PNG", compress_level=1)
    return bio.getvalue()


def jpeg_bytes(arr: np.ndarray, quality: int = 85) -> bytes:
    """Encode RGB (or BGR!) array to JPEG.  ~1.5-4 ms for 1280-2560 px wide."""
    cv2 = cv2_module()
    if cv2 is not None:
        ok, buf = cv2.imencode(".jpg", np.ascontiguousarray(arr), [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok:
            return buf.tobytes()
    import io

    bio = io.BytesIO()
    _pil(arr).save(bio, "JPEG", quality=quality, optimize=False)
    return bio.getvalue()


# ------------------------------------------------------------------- singleton
_default: Optional[Capture] = None


def grab(rgb: bool = False, copy: bool = False, **kw) -> np.ndarray:
    """One-liner using a lazily started shared Capture instance."""
    global _default
    if _default is None or not _default.alive:
        _default = Capture(**{k: kw.pop(k) for k in ("screen", "area", "cursor") if k in kw})
    return _default.grab(rgb=rgb, copy=copy, **kw)


def shot(width: Optional[int] = None, **kw) -> np.ndarray:
    global _default
    if _default is None or not _default.alive:
        _default = Capture()
    return _default.shot(width=width, **kw)
