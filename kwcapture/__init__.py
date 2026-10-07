"""kwcapture - fast Wayland screen capture for KDE Plasma, from Python.

    import kwcapture
    cap = kwcapture.Capture()                # starts the daemon, ~1 frame ready
    arr = cap.grab()                         # (H, W, 4) BGRA view of the newest frame
    rgb = cap.shot()                         # (H, W, 3) RGB, optionally downscaled
    cap.close()

    for w in kwcapture.list_windows():       # every capturable window: name + handle
        print(w.id, w.name, w.app_id)
    win = kwcapture.Capture(window="Kate")   # one window instead of a whole screen
    win2 = kwcapture.Capture(active_window=True)

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
import itertools
import json
import mmap
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import warnings
from ctypes import c_char, c_double, c_uint32, c_uint64, c_uint8
from dataclasses import dataclass, field
from typing import Optional, Union

import numpy as np

from . import _desktop, _native
from ._desktop import install_desktop_file
from ._native import NativeBuildError, ensure_binary, find_binary

__version__ = "0.4.0"

__all__ = [
    "Capture",
    "grab",
    "shot",
    "list_screens",
    "list_monitors",
    "find_monitor",
    "active_monitor",
    "measure_output_scale",
    "list_windows",
    "find_window",
    "active_window",
    "active_window_id",
    "Window",
    "Monitor",
    "to_rgb",
    "resize",
    "png_bytes",
    "jpeg_bytes",
    "cv2_module",
    "default_shm_path",
    "unique_shm_path",
    "is_window_handle",
    "find_binary",
    "ensure_binary",
    "install_desktop_file",
    "NativeBuildError",
    "CaptureError",
    "DaemonDead",
    "WindowNotFound",
    "AmbiguousWindow",
    "WindowGone",
    "NoActiveWindow",
    "MonitorNotFound",
    "AmbiguousMonitor",
    "RingTooSmall",
    "__version__",
]

KWC_MAGIC = 0x4B574350  # "KWCP"
KWC_MAGIC_GONE = 0x4B574347  # "KWCG"
KWC_VERSION = 2
KWC_MAX_SLOTS = 8
_KWC_STRUCT_SIZE = 1912  # must match sizeof(kwc_hdr_t)/KWC_HDR_STRUCT_SIZE

# what a daemon is capturing (kwcapture_shm.h KWC_TARGET_*)
KWC_TARGET_ACTIVE_SCREEN = 0
KWC_TARGET_SCREEN = 1
KWC_TARGET_AREA = 2
KWC_TARGET_WORKSPACE = 3
KWC_TARGET_WINDOW = 4
KWC_TARGET_ACTIVE_WINDOW = 5

# per-frame failures (>= 4096 are KWin screenshot errors, below that an errno)
KWC_OK = 0
KWC_ERR_INVALID_WINDOW = 4096
KWC_ERR_NO_ACTIVE_WINDOW = 4097
KWC_ERR_CANCELLED = 4098
KWC_ERR_NOT_AUTHORIZED = 4099
KWC_ERR_INVALID_SCREEN = 4100
KWC_ERR_INVALID_AREA = 4101
KWC_ERR_EMPTY_FRAME = 4102


_TARGET_NAMES = {
    KWC_TARGET_ACTIVE_SCREEN: "active-screen",
    KWC_TARGET_SCREEN: "screen",
    KWC_TARGET_AREA: "area",
    KWC_TARGET_WORKSPACE: "workspace",
    KWC_TARGET_WINDOW: "window",
    KWC_TARGET_ACTIVE_WINDOW: "active-window",
}

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


class WindowNotFound(CaptureError):
    """No window matched the requested handle or name."""


class AmbiguousWindow(WindowNotFound):
    """Several windows matched; the message lists them with their handles."""

    def __init__(self, message: str, candidates: Optional[list["Window"]] = None) -> None:
        super().__init__(message)
        self.candidates = list(candidates or [])


class MonitorNotFound(CaptureError):
    """No output matched the requested name, compositor id or index."""


class AmbiguousMonitor(MonitorNotFound):
    """Several outputs matched; the message lists them, and ``.candidates`` has them."""

    def __init__(self, message: str, candidates: Optional[list["Monitor"]] = None) -> None:
        super().__init__(message)
        self.candidates = list(candidates or [])


class WindowGone(CaptureError):
    """The captured window vanished (closed or unmapped) since the Capture started.

    The helper keeps running: list_windows() will no longer report the window, and a new
    Capture for another window (or the same app's new window) works normally.
    """


class NoActiveWindow(CaptureError):
    """active_window=True but KWin reports no focused window."""


class RingTooSmall(CaptureError):
    """A frame no longer fits the shared-memory ring: the target got bigger.

    This is what happens when the captured *window* is resized/maximised, or the monitor
    changes mode, past the room the ring was sized for.  The ring cannot be grown in
    place -- a client has it mapped at the old length, and writing a slot beyond that
    mapping would SIGBUS the reader -- so the helper reports ENOSPC and exits, and a new
    daemon is started with a ring sized for the new geometry.

    With the default ``auto_restart=True`` this is invisible: ``grab()`'s first frame at
    the new size comes back from the new ring (and ``Capture.resized`` says so).  Catch it
    yourself only if you set ``auto_restart=False``.
    """


# KWin screenshot errors reported on a frame -> (exception class, human reason)
_FRAME_ERRORS = {
    KWC_ERR_INVALID_WINDOW: (WindowGone, "the window no longer exists (closed?)"),
    KWC_ERR_NO_ACTIVE_WINDOW: (NoActiveWindow, "no window has focus"),
    KWC_ERR_CANCELLED: (CaptureError, "KWin cancelled the grab"),
    KWC_ERR_NOT_AUTHORIZED: (
        CaptureError,
        "KWin refused: the helper is not authorised (run `kwcapture install-desktop`)",
    ),
    KWC_ERR_INVALID_SCREEN: (CaptureError, "no such screen"),
    KWC_ERR_INVALID_AREA: (CaptureError, "invalid area"),
}


def _frame_error(status: int, target: int = -1) -> tuple[type, str]:
    """(exception class, human reason) for a per-frame status code from the daemon."""
    if not status:
        return CaptureError, "ok"
    if status == KWC_ERR_EMPTY_FRAME:
        # KWin replies OK with a 0x0 image when the target has no scene item to render;
        # for a window that means it was closed or is on its way out (minimised windows
        # do capture fine - KWin keeps their buffer).
        if target in (KWC_TARGET_WINDOW, KWC_TARGET_ACTIVE_WINDOW):
            return (WindowGone, "the window has nothing to capture "
                                "(closed or being unmapped)")
        return CaptureError, "the compositor returned an empty frame"
    if status in _FRAME_ERRORS:
        return _FRAME_ERRORS[status]
    if status == errno.ENOSPC:
        # the target outgrew the ring (resolution change / window resized): recoverable
        return RingTooSmall, os.strerror(errno.ENOSPC)
    if status < 4096:
        return CaptureError, os.strerror(int(status))
    return CaptureError, f"KWin screenshot error {status}"


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
        ("status", c_uint32),
        ("pad", c_uint32 * 7),
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
        ("target", c_uint32),
        ("pad4", c_uint32),
        ("window", c_char * 64),
        ("slot", _Slot * KWC_MAX_SLOTS),
        ("reserved", c_uint8 * 512),
    ]


assert ctypes.sizeof(_Hdr) == _KWC_STRUCT_SIZE, (
    f"kwcapture: header layout mismatch (python {ctypes.sizeof(_Hdr)} != "
    f"expected {_KWC_STRUCT_SIZE}); rebuild against include/kwcapture_shm.h"
)

# ---------------------------------------------------------------- shared-memory reads
# Everything in this block exists because of BUG-4 (AGENTS.md): the client reads memory
# the daemon owns and can rewrite at any time.  `_view()` used to read the same fields
# repeatedly through ctypes *shadow* objects (`h.slot[i]`), which could mix two frames'
# values into one geometry, and it did so inside the same expression as the numpy
# zero-copy view that turns out to corrupt memory by itself (probe/corruption_rate.py).
# The rules now:
#   * values that are fixed for one daemon generation (slots, hdr_size, slot_bytes) are
#     read once in `_start_once()` and cached on the instance;
#   * per-frame values come from ONE contiguous read of the slot descriptor into a
#     private bytes object, and nothing is derived from shared memory twice;
#   * every value is bounds-checked against the mapping before it becomes an offset;
#   * frames are read through a read-only mapping (so the numpy view is read-only for
#     free, no `setflags()`, and a caller can never write into the ring); the two control
#     words the client writes (`req_seq`, `quit`) go through a separate tiny writable one.
_LE = sys.byteorder
_HDR_OFF = {name: getattr(_Hdr, name).offset for name, _ in _Hdr._fields_}
_SLOT_OFF = {name: getattr(_Slot, name).offset for name, _ in _Slot._fields_}
_SLOT_SIZE = ctypes.sizeof(_Slot)
_U32 = struct.Struct("@I")
_U64 = struct.Struct("@Q")
# _Slot starts with four u32: width, height, stride, format
assert (_SLOT_OFF["width"], _SLOT_OFF["height"], _SLOT_OFF["stride"],
        _SLOT_OFF["format"]) == (0, 4, 8, 12), "unexpected _Slot layout"
assert _SLOT_SIZE == 144, f"unexpected _Slot size {_SLOT_SIZE}"
_GEOM = struct.Struct("@4I")


_SLOT_ARRAY_OFF = _HDR_OFF["slot"]     # start of the per-frame descriptors (v2: 248)


def _check_ring_geometry(slots: int, hdr_size: int, slot_bytes: int,
                         ring_len: int) -> None:
    """Refuse a ring the daemon advertises but the file cannot hold (BUG-4).

    Called once per daemon generation. Everything a frame view derives from shared memory
    (offsets, counts, shapes) is only safe if these numbers are sane, so nonsense is an
    error here rather than a bogus array -- or worse -- later.
    """
    if not 1 <= slots <= KWC_MAX_SLOTS:
        raise CaptureError(f"daemon reports {slots} ring slots "
                           f"(1..{KWC_MAX_SLOTS} are valid)")
    if not _KWC_STRUCT_SIZE <= hdr_size <= ring_len:
        raise CaptureError(f"daemon reports header size {hdr_size}, mapping is "
                           f"{ring_len} bytes: helper/kwcapture mismatch?")
    if slot_bytes < 1 or hdr_size + slot_bytes * slots > ring_len:
        raise CaptureError(
            f"ring does not fit its file: hdr {hdr_size} + {slots} x {slot_bytes} "
            f"> {ring_len} bytes")


def _u32(buf: bytes, off: int) -> int:
    return _U32.unpack_from(buf, off)[0]


def _u64(buf: bytes, off: int) -> int:
    return _U64.unpack_from(buf, off)[0]


def default_shm_path(tag: str = "") -> str:
    """The default ring-buffer path in tmpfs ($XDG_RUNTIME_DIR when set)."""
    base = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    suffix = f"-{tag}" if tag else ""
    return os.path.join(base, f"kwcapture-{os.getuid()}{suffix}.shm")


_shm_seq = itertools.count(1)


def unique_shm_path(tag: str = "") -> str:
    """default_shm_path() plus this pid and instance number.

    `Capture` uses this when you do not pass `shm=`: two Capture objects in one process
    must not share a ring file (the second daemon would ftruncate() the file the first
    one has mapped).
    """
    base = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    suffix = f"-{tag}" if tag else ""
    return os.path.join(base, f"kwcapture-{os.getuid()}{suffix}-{os.getpid()}-{next(_shm_seq)}.shm")


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


# ------------------------------------------------------------------- monitors
@dataclass
class Monitor:
    """One output the compositor can capture, as ``list_monitors()`` sees it.

    Three ways to name the same screen, all accepted by ``Capture(monitor=...)``:

    * ``name``  -- the connector, ``"DP-1"``.  What KWin addresses screens by.
    * ``id``    -- the compositor's own numeric id for the output (its ``wl_output``
      global name).  Stable for the session, unique, and what a raw Wayland client sees.
    * ``index`` -- position in ``list_monitors()`` order (top-left monitor first).
      Convenient, but it *does* shift if you plug a monitor in on the left.

    ``scale`` is the integer hint ``wl_output`` advertises, which cannot express 1.25 or
    1.5 -- use ``effective_scale`` (measured from KWin) for the real number.  ``width`` /
    ``height`` are device pixels; ``position`` is in logical scene coordinates, which is
    what ``Capture(area=...)`` also takes.
    """

    id: int
    name: str = ""
    index: int = 0
    make: str = ""
    model: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    refresh_hz: float = 0.0
    scale: int = 1
    effective_scale: Optional[float] = None   # filled in by list_monitors(measure_scale=True)
    extra: dict = field(default_factory=dict)

    @property
    def geometry(self) -> tuple[int, int]:
        """Size in device pixels (the current mode)."""
        return (self.width, self.height)

    @property
    def position(self) -> tuple[int, int]:
        """Position in logical scene coordinates (what ``area=`` uses)."""
        return (self.x, self.y)

    @property
    def fractional(self) -> bool:
        """True when the scale is not a whole number (1.25, 1.5, ...) -- if it was measured."""
        s = self.effective_scale
        return s is not None and abs(s - round(s)) > 0.01

    @property
    def logical_geometry(self) -> tuple[int, int]:
        """Size in logical pixels: device pixels divided by the measured scale."""
        s = self.effective_scale or self.scale or 1
        return (round(self.width / s), round(self.height / s))

    def to_logical(self, x: int, y: int) -> tuple[float, float]:
        """Device pixels -> logical scene coordinates (useful at 125%/150% scaling)."""
        s = self.effective_scale or self.scale or 1
        return (x / s, y / s)

    def to_physical(self, x: int, y: int) -> tuple[float, float]:
        """Logical scene coordinates -> device pixels."""
        s = self.effective_scale or self.scale or 1
        return (x * s, y * s)

    def __str__(self) -> str:
        scale = self.effective_scale or self.scale or 1
        frac = "" if abs(scale - round(scale)) <= 0.01 else f" (fractional)"
        return (f"{self.name} [{self.make} {self.model}]".rstrip()
                + f" {self.width}x{self.height}+{self.x}+{self.y}"
                + f" @ {self.refresh_hz:.2f} Hz x{scale:g}{frac}"
                + f" index={self.index} id={self.id}")

    @classmethod
    def from_dict(cls, d: dict) -> "Monitor":
        known = {f for f in cls.__dataclass_fields__ if f != "extra"}
        kw = {k: v for k, v in d.items() if k in known}
        rest = {k: v for k, v in d.items() if k not in known}
        return cls(extra=rest, **kw)


def list_monitors(binary: Optional[str] = None,
                  measure_scale: bool = False) -> list[Monitor]:
    """Every output the compositor offers for capture, top-left first.

    Returns :class:`Monitor` objects with ``name``, ``id``, ``index``, ``position``,
    ``geometry``, ``refresh_hz`` and ``scale``.  Like ``list_windows()`` this asks the
    compositor, so nothing has to be running beforehand.

    Only outputs that are *on* are listed: a connected-but-disabled monitor has no image
    to capture (``kscreen-doctor -o`` shows those, and turns them on).

    ``measure_scale=True`` also probes each output's real scale -- the number a fractional
    display is using, which ``wl_output`` cannot report.  Costs two small grabs per
    monitor (~25 ms), so it is opt-in.
    """
    binary = str(_native.resolve(binary))
    out = subprocess.run([binary, "--list-monitors", "--json"],
                         capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise CaptureError(out.stderr.strip() or "kwcapture --list-monitors failed")
    try:
        data = json.loads(out.stdout or "[]")
    except json.JSONDecodeError as e:
        raise CaptureError(f"could not parse the monitor list: {e}") from e
    monitors = [Monitor.from_dict(d) for d in data]
    if measure_scale:
        for m in monitors:
            try:
                m.effective_scale = measure_output_scale(m.name, binary=binary)
            except CaptureError:
                pass    # a monitor that refuses the probe keeps its integer scale
    return monitors


def measure_output_scale(name: str, binary: Optional[str] = None) -> float:
    """Device pixels per logical pixel on one output, measured from KWin.

    ``wl_output.scale`` is an integer hint, so a display set to 125% says 1 there (KWin
    tells fractional clients through a per-surface protocol we do not want to depend on).
    Instead the helper grabs one small area twice -- once in device pixels, once at the
    composited size -- and the ratio of the two is the scale actually in use.
    """
    binary = str(_native.resolve(binary))
    out = subprocess.run([binary, "--probe-scale", str(name)],
                         capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise CaptureError(out.stderr.strip() or f"kwcapture --probe-scale {name} failed")
    parts = out.stdout.split()
    if len(parts) < 6:
        raise CaptureError(f"unexpected scale probe output: {out.stdout.strip()!r}")
    scale = (float(parts[4]) + float(parts[5])) / 2.0
    if not 0.05 <= scale <= 16.0:
        raise CaptureError(f"implausible scale {scale} measured for {name}")
    return scale


def active_monitor(binary: Optional[str] = None) -> Monitor:
    """The output a plain ``Capture()`` would grab: the one holding the focused window.

    KWin has no "active screen" call, so this asks KWin which window has focus and takes
    the output whose logical rectangle contains that window's centre.  Falls back to the
    top-left output when nothing is focused (or no window is placed inside one).
    """
    monitors = list_monitors(binary)
    if not monitors:
        raise CaptureError("the compositor announces no enabled outputs")
    if len(monitors) == 1:
        return monitors[0]
    try:
        focus = active_window(binary=binary)
    except CaptureError:
        focus = None          # nothing focused, or focus is on a panel/desktop
    if focus is not None:
        cx, cy = focus.x + focus.width // 2, focus.y + focus.height // 2
        for m in monitors:
            # logical bounds: the mode size divided by the scale the output is drawn at
            s = m.effective_scale or m.scale or 1
            if (m.x <= cx < m.x + m.width / s and m.y <= cy < m.y + m.height / s):
                return m
    return monitors[0]


def find_monitor(
    spec: Union[str, int, Monitor, None],
    monitors: Optional[list[Monitor]] = None,
    binary: Optional[str] = None,
) -> Monitor:
    """Resolve a connector name, a compositor id, an enumeration index or a substring.

    ``"DP-1"`` (exact, then case-insensitive, then substring, as ``find_window`` does),
    ``65`` (the compositor id) or ``"65"``, and a plain integer that is not an id is taken
    as the ``list_monitors()`` index.  Raises MonitorNotFound / AmbiguousWindow.

    Numeric specs resolve **id first, then index** -- with two monitors `0` is an index,
    because no compositor id is 0; `65` is the id of DP-1 here.
    """
    if isinstance(spec, Monitor):
        return spec
    if spec is None or not str(spec).strip():
        raise MonitorNotFound("no monitor requested")
    text = str(spec).strip()
    if monitors is None:
        monitors = list_monitors(binary)
    if text.lstrip("+").isdigit():
        num = int(text)
        for m in monitors:                 # the compositor's own id wins
            if m.id == num:
                return m
        for m in monitors:                 # otherwise an enumeration index
            if m.index == num:
                return m
        raise MonitorNotFound(
            f"no monitor with id or index {num}; available: "
            + ", ".join(f"{m.name} (id {m.id}, index {m.index})" for m in monitors))
    low = text.lower()
    best, top = [], 0
    for m in monitors:
        if m.name == text:
            score = 3                       # exact connector name
        elif m.name.lower() == low:
            score = 2                       # case-insensitive connector name
        elif low in m.name.lower():
            score = 1                       # "hdmi" -> HDMI-A-1
        elif low in m.make.lower() or low in m.model.lower():
            score = 1                       # "lg" -> the monitor whose make/model matches
        else:
            score = 0
        if score > top:
            best, top = [m], score
        elif score == top and score:
            best.append(m)
    if not best:
        raise MonitorNotFound(
            f"no monitor matches {spec!r}; available: "
            + ", ".join(m.name for m in monitors))
    if len(best) > 1:
        raise AmbiguousMonitor(
            f"{spec!r} matches several monitors: " + ", ".join(m.name for m in best),
            candidates=best)
    return best[0]


# --------------------------------------------------------------------- windows
@dataclass
class Window:
    """One capturable window, as KWin sees it.

    `id` is the KWin window handle (a QUuid string like
    ``{2c14f294-93ea-48bf-bbea-f501d59f6fe5}``): pass it to ``Capture(window=...)``.
    It is only valid until the window is closed -- re-list when in doubt.
    """

    id: str
    name: str = ""            # window caption
    app_id: str = ""          # wayland app_id / X11 WM_CLASS
    resource_name: str = ""   # X11 WM_CLASS instance name
    desktop_file: str = ""    # .desktop file of the app, if it set one
    role: str = ""
    icon: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    minimized: bool = False
    fullscreen: bool = False
    keep_above: bool = False
    keep_below: bool = False
    no_border: bool = False
    skip_taskbar: bool = False
    skip_pager: bool = False
    skip_switcher: bool = False
    maximized: bool = False
    window_type: int = 0
    layer: int = 0
    desktops: tuple[str, ...] = ()
    active: bool = False        # has keyboard focus (list_windows() fills this in)
    extra: dict = field(default_factory=dict)

    # ``id`` is what CaptureWindow() wants; ``handle``/``uuid`` read better in code
    @property
    def handle(self) -> str:
        return self.id

    @property
    def uuid(self) -> str:
        return self.id.strip("{}")

    @property
    def geometry(self) -> tuple[int, int]:
        return (self.width, self.height)

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def visible(self) -> bool:
        return not self.minimized

    def __str__(self) -> str:
        flags = " ".join(
            n for n, on in (("minimized", self.minimized), ("fullscreen", self.fullscreen),
                            ("maximized", self.maximized)) if on
        )
        return (f"{self.name or '(untitled)'} [{self.app_id or '?'}] "
                f"{self.width}x{self.height}+{self.x}+{self.y} "
                f"{'(' + flags + ') ' if flags else ''}{self.id}")

    @classmethod
    def from_dict(cls, d: dict) -> "Window":
        known = {f for f in cls.__dataclass_fields__ if f != "extra"}
        return cls(
            **{k: (tuple(v) if k == "desktops" else v) for k, v in d.items() if k in known},
            extra={k: v for k, v in d.items() if k not in known},
        )


_HANDLE_RE = re.compile(r"^\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                        r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?$")


def is_window_handle(spec: str) -> bool:
    """Does this look like a KWin window handle (with or without the braces)?"""
    return bool(_HANDLE_RE.match(spec.strip()))


def active_window_id(binary: Optional[str] = None) -> Optional[str]:
    """KWin handle of the window that has keyboard focus, or None if nothing has it.

    KWin exposes no focus query over D-Bus (`supportInformation` does not list windows
    either). The helper asks for an active-window capture and reads `windowId` out of
    the reply, which KWin sends *before* it writes any pixels -- so the pixels are
    dropped and nothing is copied. About 8 ms, and it needs the same authorisation as
    a grab (unlike list_windows(), which works unauthorised).
    """
    binary = str(_native.resolve(binary))
    try:
        out = subprocess.run([binary, "--active-window-id"], capture_output=True,
                             text=True, timeout=30)
    except subprocess.SubprocessError as e:
        raise CaptureError(f"cannot query the focused window: {e}") from e
    if out.returncode == 2:  # nothing focused (e.g. the desktop has it)
        return None
    if out.returncode != 0:
        raise CaptureError(out.stderr.strip() or "kwcapture --active-window-id failed")
    return out.stdout.strip() or None


def active_window(
    binary: Optional[str] = None,
    windows: Optional[list[Window]] = None,
) -> Window:
    """The window that has keyboard focus.

    Raises WindowNotFound when nothing is focused or the focused window is not one
    KWin lists (a panel, overlay or the desktop).
    """
    handle = active_window_id(binary)
    if not handle:
        raise WindowNotFound("no window has focus")
    return find_window(handle, windows=windows, binary=binary)


def list_windows(
    binary: Optional[str] = None,
    mark_active: bool = True,
) -> list[Window]:
    """Every window KWin considers a normal application window.

    KWin's screenshot interface cannot enumerate windows, so the helper asks KWin's
    krunner interface (`/WindowsRunner`, an empty query matches all windows) for the
    handles and `/KWin getWindowInfo(handle)` for the details of each.  Panels, the
    desktop/wallpaper and other special windows are not in that list; if you do have a
    handle for one, `Capture(window=...)` still captures it.

    `mark_active` sets `Window.active` on the focused window (one extra ~8 ms query);
    pass False to skip it -- the focus query needs KWin's screenshot authorisation,
    enumeration does not.
    """
    binary = str(_native.resolve(binary))
    out = subprocess.run([binary, "--list-windows", "--json"], capture_output=True,
                         text=True, timeout=30)
    if out.returncode != 0:
        raise CaptureError(out.stderr.strip() or "kwcapture --list-windows failed")
    try:
        data = json.loads(out.stdout or "[]")
    except json.JSONDecodeError as e:  # pragma: no cover - would mean a broken helper
        raise CaptureError(f"cannot parse the window list: {e}") from e
    windows = [Window.from_dict(d) for d in data]
    if mark_active:
        try:
            focus = active_window_id(binary)
        except CaptureError:  # not authorised yet, or KWin refused: no active flag
            focus = None
        if focus:
            want = focus.strip("{}").lower()
            for w in windows:
                if w.uuid.lower() == want:
                    w.active = True
    return windows


def _match_score(w: Window, spec: str) -> int:
    """How well a window matches a name: 3 exact caption ... 1 substring."""
    low = spec.lower()
    if w.name == spec:
        return 3
    if w.name.lower() == low:
        return 2
    if low in (w.app_id.lower(), w.desktop_file.lower(), w.resource_name.lower(),
               w.role.lower()):
        return 2
    if low and low in w.name.lower():
        return 1
    if low and (low in w.app_id.lower() or low in w.desktop_file.lower()):
        return 1
    return 0


def find_window(
    spec: Union[str, Window, None],
    windows: Optional[list[Window]] = None,
    binary: Optional[str] = None,
) -> Window:
    """Resolve a handle, a caption, an app id or a substring to one :class:`Window`.

    Raises WindowNotFound if nothing matches and AmbiguousWindow (with .candidates) if
    several do.  Pass `windows` to search a pre-fetched list.
    """
    if isinstance(spec, Window):
        return spec
    if spec is None or not str(spec).strip():
        raise WindowNotFound("no window requested")
    spec = str(spec).strip()
    if windows is None:
        windows = list_windows(binary)
    if is_window_handle(spec):
        want = spec.strip("{}").lower()
        for w in windows:
            if w.uuid.lower() == want:
                return w
        raise WindowNotFound(
            f"no window with handle {spec}; current windows: "
            + ", ".join(f"{w.id} ({w.name})" for w in windows) or "none"
        )
    best, top = [], 0
    for w in windows:
        score = _match_score(w, spec)
        if score > top:
            best, top = [w], score
        elif score == top and score:
            best.append(w)
    if not best:
        raise WindowNotFound(
            f"no window matches {spec!r}; capturable windows: "
            + (", ".join(w.name or w.app_id for w in windows) or "none")
        )
    if len(best) > 1:
        raise AmbiguousWindow(
            f"{spec!r} matches {len(best)} windows, pick one by handle: "
            + ", ".join(f"{w.id} ({w.name})" for w in best),
            best,
        )
    return best[0]


class Capture:
    """Grab frames from KWin through a resident helper process.

    Parameters
    ----------
    screen : str, optional   output name (see list_screens()); default = active screen
    area : (x, y, w, h), optional   capture only this region (logical coords)
    workspace : bool         capture the entire virtual desktop
    window : str | Window    capture one window: a handle, caption or app id from
                             list_windows()/find_window() (e.g. window="Kate")
    active_window : bool     capture the window that has focus
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
    auto_restart : bool      recover inside grab() when the daemon dies, is reaped for
                             being idle, or when a frame outgrows the ring (resolution
                             change / window resized) -- see RingTooSmall.  Default True;
                             False restores the pre-0.5 behaviour of raising DaemonDead.
    restart_limit : int      give up (and raise) after this many *consecutive* automatic
                             restarts; the count resets on every successful frame.
    slot_floor : (w, h)      room to leave in every ring slot for a frame that grows
                             later.  Default (5120, 2880) -- any 5K-or-smaller mode or
                             window can be reached without a restart.  Raise it for a
                             6K/8K display, or lower it to shrink the footprint.
    """

    # Class-level defaults for the resilience state below, so a Capture built without
    # running __init__ (tests/test_ring_reader.py builds one from a synthetic ring) still
    # has them: the frame path must never be the thing that raises AttributeError.
    auto_restart = True
    restart_limit = 5
    auto_restarts = 0        # cumulative for this Capture; never reset
    last_restart_reason = ""
    _closed = False
    _resized = False
    _last_frame_geom: Optional[tuple[int, int]] = None
    monitor: Optional["Monitor"] = None
    area_in = "logical"
    _pixel_scale: Optional[float] = None

    def __init__(
        self,
        screen: Optional[str] = None,
        area: Optional[tuple[int, int, int, int]] = None,
        workspace: bool = False,
        window: Union[str, Window, None] = None,
        active_window: bool = False,
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
        stale_check: bool = False,
        autostart: bool = True,
        auto_restart: bool = True,
        restart_limit: int = 5,
        slot_floor: Optional[tuple[int, int]] = None,
        monitor: Union[str, int, "Monitor", None] = None,
        area_in: str = "logical",
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
        # monitor= accepts a connector name ("DP-1"), the compositor's id (65), an
        # enumeration index (0) or a Monitor from list_monitors(). Resolving it here means
        # a typo raises MonitorNotFound now, listing what exists, instead of the daemon
        # failing later with KWin's "no such screen".
        self.monitor: Optional[Monitor] = None
        if monitor is not None:
            if screen:
                raise CaptureError(
                    "pass either monitor= or screen=, not both -- monitor= takes a name "
                    "too, and also an id or an index")
            mon = find_monitor(monitor, binary=self.binary)
            self.monitor = mon
            screen = mon.name
        self.area_in = str(area_in)
        if self.area_in not in ("logical", "physical"):
            raise CaptureError("area_in must be 'logical' (default) or 'physical'")
        self._pixel_scale: Optional[float] = None
        if area is not None and self.area_in == "physical" and self.monitor is None:
            raise CaptureError(
                "area_in='physical' needs monitor=: device pixels only map to logical "
                "coordinates within one output, since scene coordinates are global")
        if area is not None and self.area_in == "physical":
            self._pixel_scale = measure_output_scale(self.monitor.name, binary=self.binary)
        if active_window and window is not None:
            raise CaptureError("window= and active_window=True are mutually exclusive")
        if (window is not None or active_window) and (screen or area or workspace):
            raise CaptureError(
                "a window capture cannot also be a screen/area/workspace capture"
            )
        self.screen = screen
        # area is relative to `monitor` when one was given (and converted from device
        # pixels first if area_in="physical"); in global scene coordinates when not.
        self.area = self._resolve_area(area)
        self.workspace = workspace
        self.window_spec: Union[str, Window, None] = window
        self.window_id = ""    # resolved KWin handle, empty until resolved/unresolved
        self.window_name = ""  # caption of the resolved window
        self.active_window = bool(active_window)
        if window is not None:
            win = find_window(window, binary=self.binary)
            self.window_id, self.window_name = win.id, win.name
        self.cursor = cursor
        self.shm_path = shm or unique_shm_path()
        self.req_path = self.shm_path + ".req"  # FIFO used to wake the daemon
        self._req_fd = -1
        self._proc: Optional[subprocess.Popen] = None
        self._mm: Optional[mmap.mmap] = None      # read-only: frame data (numpy views)
        self._ctl: Optional[mmap.mmap] = None     # writable: header control words only
        self._fd = -1
        self._hdr: Optional[_Hdr] = None
        # ring geometry of the *current* daemon generation, read once (see BUG-4) and
        # used to validate every per-frame value before it becomes an offset.
        self._gen = 0
        self._ring_slots = 0
        self._ring_hdr_size = 0
        self._ring_slot_bytes = 0
        self._ring_len = 0
        self._daemon_stderr = daemon_stderr
        self.idle_exit = idle_exit
        self._slots = slots
        self._depth = depth
        self._fps = fps
        self.hide_caller_windows = hide_caller_windows
        self.decoration = decoration
        self.start_timeout = start_timeout
        # BUG-1: KWin stops rendering a minimised window, so a window capture silently
        # repeats the last buffer forever -- no exception, no status, nothing in the ring.
        # The only source of truth is getWindowInfo, which is a D-Bus round trip, so it is
        # opt-in: stale_check=True makes grab() consult it (throttled) and flag the result.
        self.stale_check = bool(stale_check)
        self._stale = False
        self._stale_checked = 0.0
        # Resilience: recover inside grab() from a dead/reaped daemon and from a target
        # that outgrew the ring (see RingTooSmall), and notice when the frames change size.
        self.auto_restart = bool(auto_restart)
        self.restart_limit = int(restart_limit)
        self.auto_restarts = 0        # cumulative, for observability
        self._restart_streak = 0      # consecutive, for restart_limit
        self.last_restart_reason = ""
        self.slot_floor = tuple(slot_floor) if slot_floor else None
        if self.slot_floor is not None and len(self.slot_floor) != 2:
            raise CaptureError("slot_floor must be (width, height)")
        self._closed = False
        self._resized = False
        self._last_frame_geom = None
        if autostart:
            self.start()

    # -------------------------------------------------------------- lifecycle
    def _resolve_area(self, area) -> Optional[tuple[int, int, int, int]]:
        """Turn the caller's area into the scene-rectangle the helper wants."""
        if not area:
            return None
        vals = tuple(area)
        if len(vals) != 4:
            raise CaptureError("area must be (x, y, w, h)")
        x, y, w, h = (float(v) for v in vals)
        if self.area_in == "physical":
            s = self._pixel_scale or 1.0
            x, y, w, h = x / s, y / s, w / s, h / s
        if self.monitor is not None:
            x += self.monitor.x
            y += self.monitor.y
        out = (int(round(x)), int(round(y)), int(round(w)), int(round(h)))
        if out[2] < 1 or out[3] < 1:
            raise CaptureError(f"area is empty after scaling: {out}")
        return out

    def _argv(self) -> list[str]:
        argv = [self.binary, "serve", "--shm", self.shm_path,
                "--slots", str(self._slots), "--depth", str(self._depth),
                "--idle-exit", str(self.idle_exit)]
        if self.active_window:
            argv += ["--active-window"]
        elif self.window_id:
            argv += ["--window", self.window_id]
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
        if getattr(self, "slot_floor", None):
            argv += ["--slot-floor", f"{int(self.slot_floor[0])}x{int(self.slot_floor[1])}"]
        return argv

    # KService picks up a new desktop entry asynchronously, so after writing one we may
    # have to wait for KWin to agree with us.
    _AUTH_RETRY_DELAYS = (0.1, 0.3, 0.6, 1.0, 1.5)

    def start(self) -> None:
        """Spawn the daemon and map the ring.

        If KWin refuses us because the authorising desktop entry is missing - or has not
        been noticed by KDE's service cache yet - we (re)write it and retry with backoff.
        """
        self._closed = False   # an explicit start()/restart() revives a closed Capture
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
        # Drop a ring left behind by a previous daemon (e.g. after restart() when it was
        # killed): the file already looks complete, so without this we would map the stale
        # pages and then get SIGBUS'd when the new daemon truncates the file.  The
        # daemon_pid check below is the belt to these braces.
        # Drop the previous mapping before re-opening: _fd/_mm/_hdr are re-created below and
        # nothing else closes them, so a restart used to leak one fd each time (BUG-3).
        self._unmap()
        for stale in (self.shm_path, self.req_path):
            try:
                os.unlink(stale)
            except OSError:
                pass
        # Close the log file from the previous attempt first: _start_once() runs on every
        # retry and every restart(), so dropping the handle here leaked one fd per attempt
        # (found with /tmp/repro.py under -X dev, which raised ResourceWarning).
        if self._log_file is not None:
            try:
                self._log_file.close()
            except OSError:
                pass
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
        # Two mappings of the same ring, deliberately (BUG-4): the frame data is mapped
        # read-only, so numpy hands out read-only views without a `setflags()` call and no
        # caller can write into the ring; the only words the client writes (`req_seq`,
        # `quit`) go through a separate header-sized writable mapping.
        self._mm = mmap.mmap(self._fd, 0, access=mmap.ACCESS_READ)
        self._ctl = mmap.mmap(self._fd, _KWC_STRUCT_SIZE, access=mmap.ACCESS_WRITE)
        self._hdr = _Hdr.from_buffer(self._ctl)
        hdr = self._hdr
        deadline = time.monotonic() + self.start_timeout
        while (hdr.magic != KWC_MAGIC or not hdr.ready
               or int(hdr.daemon_pid) != proc.pid):
            if hdr.magic == KWC_MAGIC_GONE:
                raise DaemonDead("kwcapture daemon shut down during startup: "
                                 + (self._daemon_log_tail(3) or "no log output"))
            if proc.poll() is not None:
                raise CaptureError("kwcapture daemon died during startup")
            if time.monotonic() > deadline:
                raise CaptureError("timed out waiting for the first frame")
            time.sleep(0.002)
        if hdr.version != KWC_VERSION:
            raise CaptureError(f"unsupported kwcapture ABI {hdr.version}: rebuild the "
                               f"helper (`kwcapture setup`) or upgrade kwcapture")
        # Fixed for this daemon generation: read once here, then never re-read those
        # fields on the frame path (BUG-4: they used to be re-read per frame, through
        # ctypes shadow objects, next to the numpy view of the same memory).
        slots, hdr_size, slot_bytes = int(hdr.slots), int(hdr.hdr_size), int(hdr.slot_bytes)
        ring_len = len(self._mm)
        _check_ring_geometry(slots, hdr_size, slot_bytes, ring_len)
        self._ring_slots, self._ring_hdr_size = slots, hdr_size
        self._ring_slot_bytes, self._ring_len = slot_bytes, ring_len
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

    def _unmap(self) -> None:
        """Release the header, mappings and fd belonging to a previous daemon.

        restart() re-opens all three, so without this every restart leaked one fd and one
        mmap (measured: 16 -> 20 fds over 4 restarts). mmap.close() raises BufferError while
        numpy still exports a buffer from it, in which case we simply drop our reference --
        the mapping stays alive for those views, which is what we want: an outstanding
        frame view keeps its bytes readable (frozen at close time) instead of SIGSEGVing,
        and because the next daemon's file is created fresh (we unlink the path first)
        the old mapping's pages are never truncated underneath it.

        Bumps `_gen`: a read that started before this must not finish against the next
        generation's ring.
        """
        self._gen += 1
        self._ring_slots = self._ring_hdr_size = self._ring_slot_bytes = 0
        for attr in ("_hdr", "_ctl", "_mm"):
            obj = getattr(self, attr)
            if obj is None:
                continue
            setattr(self, attr, None)
            if attr == "_hdr":
                continue        # just released its export of _ctl
            try:
                obj.close()
            except (BufferError, ValueError):
                pass            # still exported by an outstanding view: leave it mapped
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = -1

    def restart(self) -> None:
        """Tear the daemon down and bring it back up (re-sizing the ring as needed).

        Called for you by ``grab()`` when ``auto_restart=True``; call it directly only if
        you disabled that. An explicit ``restart()``/``start()`` also revives a Capture
        that was ``close()``d.
        """
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
        self._closed = True   # grab() must not resurrect a Capture the user closed
        self.close_daemon()
        self._unmap()
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
        """Size the daemon is capturing right now (follows a resolution change)."""
        h = self._require()
        return int(h.width), int(h.height)

    @property
    def last_geometry(self) -> Optional[tuple[int, int]]:
        """Size of the last frame handed out by this Capture, or None before the first."""
        return self._last_frame_geom

    @property
    def resized(self) -> bool:
        """True if the frame just handed out differs in size from the one before it.

        Covers both ways the geometry can move: the monitor changing mode, and the
        captured window being resized or maximised. Cheap enough to poll per frame -- it
        compares two ints already read for the frame. False on the very first frame, and
        not sticky: it describes the grab that just happened.
        """
        return self._resized

    @property
    def scale(self) -> float:
        """Scale KWin reported for the frames it is sending (1.0 = device pixels)."""
        h = self._require()
        return float(h.scale)

    @property
    def pixel_scale(self) -> float:
        """Measured device-pixels-per-logical-pixel for this Capture's output.

        Measured once (two small grabs) and cached. KWin's reported `scale` above is what
        it applied to this frame; this is the output's actual scale, including 1.25/1.5.
        """
        if self._pixel_scale is None:
            name = self.screen or (self.monitor.name if self.monitor else "")
            if not name:
                name = active_monitor().name
            self._pixel_scale = measure_output_scale(name, binary=self.binary)
        return self._pixel_scale

    @property
    def slot_bytes(self) -> int:
        """Bytes per ring slot for the current daemon generation (0 if not started)."""
        return self._ring_slot_bytes

    @property
    def ring_bytes(self) -> int:
        """Size of the shared-memory ring this Capture has mapped."""
        return self._ring_len

    @property
    def screen_name(self) -> str:
        h = self._require()
        return h.screen.decode() if isinstance(h.screen, bytes) else str(h.screen)

    @property
    def target(self) -> str:
        """'screen', 'area', 'window', ... - what this Capture is pointed at."""
        h = self._require()
        return _TARGET_NAMES.get(int(h.target), str(int(h.target)))

    @property
    def window_minimized(self) -> bool:
        """Whether this Capture's target window is minimised right now.

        Ask KWin once per call (a D-Bus round trip), so do not call it per frame.
        A window that has disappeared entirely counts as minimised: either way there is
        nothing live to capture, so the frame you get is a stale snapshot (see BUG-1).
        Only meaningful for ``window=`` / ``active_window=True`` captures.
        """
        handle = self.window_id or (self.stats().get("window") or "")
        if not handle:
            raise CaptureError(
                "window_minimized needs a window= or active_window=True capture"
            )
        try:
            return find_window(handle, binary=self.binary).minimized
        except WindowNotFound:
            return True

    @property
    def stale_frame(self) -> bool:
        """True if the newest frame is known to be a stale snapshot (see BUG-1).

        Only ever becomes True when the Capture was created with ``stale_check=True``;
        without it nothing consults KWin and this stays False, which means "unknown".
        """
        return self._stale

    def _update_staleness(self) -> None:
        """Consult KWin (at most ~10x/s) and flag/warn when a window goes stale."""
        now = time.monotonic()
        if now - self._stale_checked < 0.1:
            return
        self._stale_checked = now
        try:
            minimized = self.window_minimized
        except CaptureError:
            return
        if minimized and not self._stale:
            warnings.warn(
                f"kwcapture: the captured window {self.window_id or self.window_name or ''} "
                "is minimised, so frames are a STALE snapshot - KWin does not render "
                "minimised windows and every grab repeats the same buffer (see BUG-1 in "
                "AGENTS.md). Map/activate the window, or stop polling it.",
                RuntimeWarning, stacklevel=3)
        self._stale = minimized

    def stats(self) -> dict:
        """Timings of the most recently published frame."""
        h = self._require()
        seq = self._frame_seq()
        # private copy of the descriptor: one read, then every field is ours (BUG-4)
        sl = _Slot.from_buffer_copy(self._descriptor(seq))
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
            window=(h.window.decode() if isinstance(h.window, bytes) else str(h.window))
            or None,
            target=_TARGET_NAMES.get(int(h.target), int(h.target)),
            status=_frame_error(int(sl.status), int(h.target))[1],
            pid=int(h.daemon_pid),
        )

    def _require(self) -> _Hdr:
        if self._hdr is None or self._mm is None or not self._ring_slots:
            raise CaptureError("capture not started")
        return self._hdr

    def _check_error(self) -> None:
        h = self._hdr
        assert h is not None
        # Read the shared field ONCE. Reading it twice (once to decide, once to format)
        # lets the daemon change it in between and produced the self-contradictory
        # "daemon error: Success" -- see BUG-4b in AGENTS.md.
        err = int(h.error)
        if err:
            if err == errno.ENOSPC:
                # The target outgrew the ring: the monitor changed mode, or the captured
                # window was resized/maximised past the room we left it. The daemon cannot
                # grow a mapping a client already holds, so it exits and we re-open bigger.
                raise RingTooSmall(
                    f"the captured target outgrew the ring "
                    f"({self._ring_slot_bytes or '?'} bytes per slot): "
                    + ("restarting the daemon with a ring sized for the new geometry"
                       if self.auto_restart else
                       "call restart() to re-open the ring at the new size, or "
                       "create the Capture with auto_restart=True"))
            raise CaptureError(f"daemon error: {os.strerror(err)}")
        if h.magic == KWC_MAGIC_GONE or (self._proc and self._proc.poll() is not None):
            raise DaemonDead("kwcapture daemon is no longer running")

    # ------------------------------------------------------- daemon recovery
    def _recoverable(self, exc: BaseException) -> bool:
        """Would starting a fresh daemon fix this?  This is what `grab()` retries on."""
        if isinstance(exc, RingTooSmall):
            return True     # a ring sized for the new geometry is exactly the fix
        if isinstance(exc, DaemonDead):
            return True     # killed, crashed, or reaped for being idle
        if isinstance(exc, TimeoutError):
            # No frame *and* the process is gone: the request died with the daemon. A live
            # daemon that merely did not answer in time is a different problem, and
            # silently restarting it would hide a KWin that is wedged.
            return not self.alive
        return False

    def _reresolve_window(self, exc: BaseException) -> None:
        """Follow the app across a close+reopen: our handle is gone, its name may not be."""
        try:
            find_window(self.window_id or self.window_spec, binary=self.binary)
            return                     # the handle is still alive: keep capturing it
        except CaptureError:
            pass
        try:
            win = find_window(self.window_spec, binary=self.binary)
        except CaptureError as e:
            raise WindowGone(
                f"the captured window {self.window_id or self.window_name!r} is gone, so "
                f"there is nothing to restart the daemon for ({e})") from exc
        if self.verbose:
            print(f"kwcapture: {self.window_id} is gone; following "
                  f"{win.name!r} at its new handle {win.id}", file=sys.stderr)
        self.window_id, self.window_name = win.id, win.name

    def _recover(self, exc: BaseException) -> None:
        """Bring the daemon back; the caller retries the grab once."""
        self.auto_restarts += 1        # cumulative: "has this Capture ever recovered?"
        self._restart_streak += 1      # consecutive: what restart_limit guards
        self.last_restart_reason = f"{type(exc).__name__}: {exc}"
        if self.verbose:
            print(f"kwcapture: {self.last_restart_reason}\n           restarting the "
                  f"daemon ({self._restart_streak}/{self.restart_limit} consecutive "
                  f"restarts, {self.auto_restarts} total)", file=sys.stderr)
        if self.window_spec is not None and not self.active_window:
            self._reresolve_window(exc)
        elif self.monitor is not None:
            # a monitor that has been unplugged cannot be captured again; say so plainly
            # rather than letting the daemon fail on a stale name
            wanted = self.monitor.name
            try:
                self.monitor = find_monitor(wanted, binary=self.binary)
                self.screen = self.monitor.name
            except MonitorNotFound as e:
                raise CaptureError(
                    f"monitor {wanted} is no longer available, so the capture cannot be "
                    f"restarted: {e}") from exc
        self.restart()

    # ------------------------------------------------------- shared-memory reads
    def _frame_seq(self) -> int:
        """Newest published frame number: one 8-byte read of the ring."""
        mm = self._mm
        if mm is None or not self._ring_slots:
            raise CaptureError("capture not started")
        off = _HDR_OFF["frame_seq"]
        return _u64(mm[off:off + 8], 0)

    def _descriptor(self, seq: int) -> bytes:
        """ONE contiguous read of the slot descriptor belonging to `seq`.

        Every per-frame value used to build a view comes out of this single read, so two
        fields can never belong to two different frames -- the daemon rewrites a
        descriptor when the ring wraps onto that slot -- and no ctypes shadow object is
        created on the frame path. See BUG-4 in AGENTS.md.
        """
        mm = self._mm
        if mm is None or not self._ring_slots:
            raise CaptureError("capture not started")
        so = _SLOT_ARRAY_OFF + ((seq - 1) % self._ring_slots) * _SLOT_SIZE
        d = mm[so:so + _SLOT_SIZE]
        if len(d) != _SLOT_SIZE:
            raise DaemonDead("ring is smaller than its own header: the daemon is gone?")
        return d

    # ------------------------------------------------------------------ frames
    def _view(self, seq: int, rgb: bool, copy: bool) -> np.ndarray:
        mm = self._mm
        if mm is None or not self._ring_slots:
            raise CaptureError("capture not started")
        d = self._descriptor(seq)
        status = _u32(d, _SLOT_OFF["status"])
        if status:
            # the compositor refused this frame: the slot holds nothing usable (a window
            # that got closed is the usual reason, see WindowGone)
            h = self._require()
            code = int(h.target)
            exc, reason = _frame_error(status, code)
            target = _TARGET_NAMES.get(code, "capture")
            what = ""
            if code == KWC_TARGET_WINDOW:
                handle = h.window.decode() if isinstance(h.window, bytes) else str(h.window)
                what = f" {handle}"
            raise exc(f"frame {seq} failed: {reason} (target={target}{what})")
        w, hgt, stride, fmt = _GEOM.unpack_from(d, 0)
        if w == 0 or hgt == 0:
            raise CaptureError("frame has no geometry")
        # Validate before use: nothing read out of shared memory becomes an offset, a
        # count or a shape for numpy unless it fits the mapping we actually hold. An
        # invalid descriptor must raise, not hand out header bytes as pixels and not read
        # past the end of the ring (BUG-4).
        if stride % 4 or w > stride // 4:
            raise DaemonDead(f"frame {seq} reports an invalid geometry: "
                             f"{w}x{hgt} stride {stride}")
        idx = (seq - 1) % self._ring_slots
        count = stride * hgt
        off = self._ring_hdr_size + idx * self._ring_slot_bytes
        if count > self._ring_slot_bytes or off + count > self._ring_len:
            raise DaemonDead(
                f"frame {seq} claims {count} bytes at offset {off}, outside the "
                f"{self._ring_len}-byte ring")
        if rgb and fmt not in (4, 5, 6, 11, 12, 13):
            raise CaptureError(f"unhandled pixel format {fmt}")
        arr = np.frombuffer(mm, dtype=np.uint8, count=count, offset=off)
        arr = arr.reshape(hgt, stride // 4, 4)
        if w != stride // 4:          # full-width frames need no slice at all
            arr = arr[:, :w, :]
        if rgb:
            arr = arr[..., 2::-1]     # BGRA -> RGB, zero copy (negative strides)
        if copy:
            arr = arr.copy()          # writable; the ring itself is mapped read-only
        # Geometry of what we actually built, from values already validated above: no
        # second read of shared memory. This is what Capture.resized compares.
        self._last_frame_geom = (w, hgt)
        return arr
        # (Reusing one array per slot instead of building a view per frame was tried to
        # dodge the upstream fault and measured: it changed nothing -- see
        # probe/FAULT_RATE_RESULTS.txt. So the read path stays simple.)

    def grab(
        self,
        timeout: float = 2.0,
        rgb: bool = False,
        copy: bool = False,
        fresh: bool = True,
    ) -> np.ndarray:
        """Return a frame as an (H, W, 4) BGRA or (H, W, 3) RGB uint8 array.

        With copy=False (default) the array is a read-only *view* of the shared ring: it
        is overwritten once `slots` more frames arrive, so use `copy=True` (or `.copy()`)
        if you need to keep it.  A view stays readable after `close()` -- frozen at the
        frame that was current when the Capture closed -- but belongs to no daemon after
        that.  With fresh=False the newest already-captured frame is returned immediately
        (no compositor round-trip).

        Recovery: with `auto_restart=True` (the default) a daemon that died, was reaped
        for sitting idle, or ran out of ring because the screen changed mode or the
        captured window was resized, is restarted here and the frame is retaken -- you get
        a frame and `Capture.resized` / `auto_restarts` tell you what happened. One retry
        per call, so a daemon that cannot come back raises rather than looping.
        """
        for attempt in (0, 1):
            try:
                return self._grab_once(timeout=timeout, rgb=rgb, copy=copy, fresh=fresh)
            except (CaptureError, TimeoutError) as exc:
                if (attempt or self._closed or not self.auto_restart
                        or not self._recoverable(exc)):
                    raise
                if self._restart_streak >= self.restart_limit:
                    raise CaptureError(
                        f"{exc} -- and the daemon has already restarted "
                        f"{self._restart_streak} times in a row without delivering a "
                        f"frame, so I am giving up (auto_restart=False disables recovery; "
                        f"restart_limit=N allows more)") from exc
                self._recover(exc)
        raise AssertionError("unreachable: the loop returns or raises")

    def _grab_once(
        self,
        timeout: float = 2.0,
        rgb: bool = False,
        copy: bool = False,
        fresh: bool = True,
    ) -> np.ndarray:
        """One grab against the current daemon; grab() wraps this with recovery."""
        h = self._require()
        prev_geom = self._last_frame_geom
        gen = self._gen
        self._check_error()
        seq = self._frame_seq()
        if fresh:
            want = seq + 1
            h.req_seq = want
            self._poke()
            deadline = time.monotonic() + timeout
            spins = 0
            while self._frame_seq() < want:
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
            # Take the NEWEST published frame rather than exactly `want`: if the daemon ran
            # ahead (fps mode, or a request still queued from earlier), `want` can be
            # `slots` frames behind by now -- a slot the daemon is free to rewrite while
            # we read it.
            seq = self._frame_seq()
        arr = self._view(seq, rgb, copy)
        if self._gen != gen:
            raise DaemonDead("the ring was replaced by restart()/close() while this frame "
                             "was being read: the result would mix two daemons")
        if copy and self._ring_slots:
            # A copy that the ring wrapped over while it was being made is torn: re-read
            # the newest frame once. A zero-copy view cannot be protected this way --
            # that is what copy=True is for.
            newest = self._frame_seq()
            if newest - seq >= self._ring_slots:
                arr = self._view(newest, rgb, copy)
        # A size change, not "I got a frame": the first frame has nothing to compare to.
        self._resized = prev_geom is not None and self._last_frame_geom != prev_geom
        self._restart_streak = 0   # a frame arrived: the daemon is healthy again
        if self.stale_check:
            self._update_staleness()
        return arr

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


def _sleep0() -> None:
    time.sleep(0)


def sched_yield() -> None:
    """Give up the timeslice while `grab()` waits for the next frame.

    Uses libc's sched_yield, falling back to sleep(0). Two things used to be wrong here
    (see BUG-2 in AGENTS.md): a missing symbol raises AttributeError, not OSError, and this
    is on the hot path of every grab, so it took the whole capture down; and the cache was
    tested with `is None`, so anything non-callable that ever landed in `_sched_yield` (for
    instance the *result* of a call -- `libc.sched_yield()` returns the int 0) would be
    invoked on every subsequent grab. `callable()` makes that impossible.
    """
    global _sched_yield
    if not callable(_sched_yield):
        try:
            _sched_yield = ctypes.CDLL("libc.so.6", use_errno=True).sched_yield
        except (OSError, AttributeError):  # no libc.so.6 (musl), or no such symbol
            _sched_yield = _sleep0
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
# Capture() constructor keys that describe *what* to capture: the module-level one-
# liners keep one daemon alive per distinct target instead of respawning one per grab.
_TARGET_KEYS = ("screen", "area", "workspace", "window", "active_window", "cursor",
                "decoration")
_singletons: dict[tuple, "Capture"] = {}


def _singleton(kw: dict) -> "Capture":
    """The cached Capture for the target described by the target keys in `kw`."""
    opts = {k: kw.pop(k) for k in _TARGET_KEYS if k in kw}
    key = tuple(sorted((k, str(v)) for k, v in opts.items()))
    cap = _singletons.get(key)
    if cap is None or not cap.alive:
        if cap is not None:
            try:
                cap.close()
            except Exception:
                pass
        cap = _singletons[key] = Capture(**opts)
    return cap


def grab(rgb: bool = False, copy: bool = False, **kw) -> np.ndarray:
    """One-liner on a lazily started, shared Capture instance.

    `grab()`, `grab(screen="DP-1")`, `grab(window="Kate")` and
    `grab(active_window=True)` each get (and reuse) their own helper process.
    """
    return _singleton(kw).grab(rgb=rgb, copy=copy, **kw)


def shot(width: Optional[int] = None, **kw) -> np.ndarray:
    """RGB one-liner; see grab() for the target keys (window=…, screen=…)."""
    return _singleton(kw).shot(width=width, **kw)
