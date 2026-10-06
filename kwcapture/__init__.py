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
import subprocess
import sys
import tempfile
import time
from ctypes import c_char, c_double, c_uint32, c_uint64, c_uint8
from dataclasses import dataclass, field
from typing import Optional, Union

import numpy as np

from . import _desktop, _native
from ._desktop import install_desktop_file
from ._native import NativeBuildError, ensure_binary, find_binary

__version__ = "0.2.0"

__all__ = [
    "Capture",
    "grab",
    "shot",
    "list_screens",
    "list_windows",
    "find_window",
    "Window",
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


class WindowGone(CaptureError):
    """The captured window vanished (closed or unmapped) since the Capture started.

    The helper keeps running: list_windows() will no longer report the window, and a new
    Capture for another window (or the same app's new window) works normally.
    """


class NoActiveWindow(CaptureError):
    """active_window=True but KWin reports no focused window."""


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


def list_windows(binary: Optional[str] = None) -> list[Window]:
    """Every window KWin considers a normal application window.

    KWin's screenshot interface cannot enumerate windows, so the helper asks KWin's
    krunner interface (`/WindowsRunner`, an empty query matches all windows) for the
    handles and `/KWin getWindowInfo(handle)` for the details of each.  Panels, the
    desktop/wallpaper and other special windows are not in that list; if you do have a
    handle for one, `Capture(window=...)` still captures it.
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
    return [Window.from_dict(d) for d in data]


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
    """

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
        if active_window and window is not None:
            raise CaptureError("window= and active_window=True are mutually exclusive")
        if (window is not None or active_window) and (screen or area or workspace):
            raise CaptureError(
                "a window capture cannot also be a screen/area/workspace capture"
            )
        self.screen = screen
        self.area = tuple(area) if area else None
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
        # Drop a ring left behind by a previous daemon (e.g. after restart() when it was
        # killed): the file already looks complete, so without this we would map the stale
        # pages and then get SIGBUS'd when the new daemon truncates the file.  The
        # daemon_pid check below is the belt to these braces.
        for stale in (self.shm_path, self.req_path):
            try:
                os.unlink(stale)
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
        self._mm = mmap.mmap(self._fd, 0, access=mmap.ACCESS_WRITE)
        self._hdr = _Hdr.from_buffer(self._mm)
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

    @property
    def target(self) -> str:
        """'screen', 'area', 'window', ... - what this Capture is pointed at."""
        h = self._require()
        return _TARGET_NAMES.get(int(h.target), str(int(h.target)))

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
            window=(h.window.decode() if isinstance(h.window, bytes) else str(h.window))
            or None,
            target=_TARGET_NAMES.get(int(h.target), int(h.target)),
            status=_frame_error(int(sl.status), int(h.target))[1],
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
        status = int(sl.status)
        if status:
            # the compositor refused this frame: the slot holds nothing usable (a window
            # that got closed or minimised is the usual reason, see WindowGone)
            exc, reason = _frame_error(status, int(h.target))
            target = _TARGET_NAMES.get(int(h.target), "capture")
            what = ""
            if int(h.target) == KWC_TARGET_WINDOW:
                handle = h.window.decode() if isinstance(h.window, bytes) else str(h.window)
                what = f" {handle}"
            raise exc(f"frame {seq} failed: {reason} (target={target}{what})")
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
