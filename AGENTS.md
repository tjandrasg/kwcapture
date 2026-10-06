# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

Working dir: `~/way_scr_cap`. **Read this first if you are a fresh session.**
Status: **done and working** — ~40 fps real Wayland capture, Python API + CLI + tests.
See `README.md` for user-facing docs; this file is the investigation log + gotchas.

## Goal
Make a **fast** full-screen capture program on Wayland. Original experiments
(`probe/bench_original.py`, `bench_result.md`): `PIL.ImageGrab` shells out to `spectacle`
(~2 fps); `mss` is 1100 fps but captures **XWayland** (black for native Wayland windows)
and dies when `$DISPLAY` is unset. Both unusable.

## What we ship (pip-installable package, v0.1.0)
`make setup` (or just `pip install .`) then `.venv/bin/python tests/test_kwcapture.py`.

| file | what |
|---|---|
| `kwcapture/native/kwcapture.c` | native helper: one-shot / `--bench` / `--list` / `serve` (daemon + shm ring), sd-bus + wayland-client |
| `kwcapture/native/include/kwcapture_shm.h` | shm ring protocol (`KWC_HDR_STRUCT_SIZE` = 1776, `_Static_assert`ed) |
| `kwcapture/__init__.py` | Python API: `Capture`, `grab/latest/shot/shot_jpeg/stats/bench`, ctypes mirror of the header, `to_rgb`/`resize`/`png_bytes`/`jpeg_bytes` |
| `kwcapture/_native.py` | helper discovery: `$KWCAPTURE_BIN` → `kwcapture/bin/kwcapture` (wheel) → `~/.cache/kwcapture/…` → compile from the shipped source; ELF-arch check |
| `kwcapture/_desktop.py` | writes/refreshes/prunes the KWin authorisation desktop entry |
| `kwcapture/__main__.py` | CLI: `doctor [--fix --build] / setup / install-desktop [--uninstall] / screens / grab / demo / bench` (console script `kwcapture`) |
| `pyproject.toml` + `setup.py` | packaging; `setup.py` compiles the helper during the wheel build (`build_py` → non-pure, `bdist_wheel.get_tag` → `linux_<arch>`), failure is non-fatal (runtime compile) |
| `tests/test_kwcapture.py` | 27 functional tests, also `pytest tests/` |
| `bench.py` | comparison table vs `mss` and `PIL.ImageGrab` |
| `Makefile` | `make` `install-desktop` `setup` `doctor` `test` `bench` `demo` `wheel` `sdist` `dev-install` `clean` |
| `probe/` | experiments: `globals.c` (dump compositor globals), Gio prototypes, scale/post micro-benchmarks |
| `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE` (MIT), `.github/workflows/ci.yml` | docs/CI |

Install story: **self-configuring** — first `Capture()` finds/builds the helper, writes the
desktop entry, retries while KDE's service cache notices it. Verified in a *fresh* venv
(`pip install dist/*.whl`, numpy only, no desktop entry present): ready in ~150 ms, 37.9 fps,
numpy-only fallback resize worked. **`kwcapture` is still an unclaimed name on PyPI (HTTP 404)**
— publish with `pip install twine && twine upload dist/*` (wheel + sdist) when ready.

## Results (2560x1440@164.69Hz, Plasma 6.6 / kwin 6.6.6, i9-13900K)
```
mss (XWayland)              1113.8 fps   0.9 ms   <-- BLACK/EMPTY, useless
PIL.ImageGrab (spectacle)      2.7 fps 357.1 ms
kwcapture raw BGRA view       38.4 fps  25.8 ms
kwcapture RGB full res        37.9 fps  26.0 ms
kwcapture RGB 1280 wide       38.0 fps  26.1 ms
kwcapture JPEG 1280           35.6 fps  28.0 ms   (grab + downscale + encode)
kwcapture latest()          551704   fps   0.0 ms   (view of already-published frame)
```
Breakdown at 1440p: KWin grab ≈ 18-25 ms (≈11 ms floor even for a 320x180 area), pipe drain
≈5 ms (14 MB). Throughput ceiling ≈47 fps (KWin serialises screenshot jobs); `depth=2`
reaches it, depth 3/4 only add latency (grab_ms 37/58/80 ms). Post-processing: cv2
`INTER_AREA` 2560→1280 = 0.1 ms, `cvtColor` BGRA2RGB of the small frame ≈3 ms, cv2 JPEG
1280 = 3.5 ms / 2560 = 4.5 ms, PNG 23 ms (avoid), PIL resize 17 ms (avoid → use cv2).
Colour fidelity verified vs an independent Spectacle capture: MAD **0.0** (9.7 if R/B swapped).

## THE TWO KEY FINDINGS

### 1. KWin's D-Bus API `org.kde.KWin.ScreenShot2`
service `org.kde.KWin.ScreenShot2`, path `/org/kde/KWin/ScreenShot2`, same interface, owned
by `kwin_wayland`. Methods (all `(…, options a{sv}, pipe h) -> results a{sv}`):
`CaptureScreen(name s)`, `CaptureActiveScreen`, `CaptureArea(x i,y i,width u,height u)`,
`CaptureWorkspace`, `CaptureWindow(handle s)`, `CaptureActiveWindow`, `CaptureInteractive(kind u)`.
* results: `type="raw"`, `format` (QImage::Format; **6 = ARGB32_Premultiplied = BGRA bytes**),
  `width`, `height`, `stride` (bytes/line), `scale` (double), `screen` (e.g. `DP-1`).
* options: `include-decoration` (def false), `include-shadow` (kwin default **true**),
  `include-cursor` (def false), `native-resolution`, `hide-caller-windows` (def **true** —
  hides the capture tool's own windows, which we want).
* **KWin replies BEFORE the pixels are written**: `ScreenShotSinkPipe2::flush()` sends the
  method return, then hands the fd to `ScreenShotWriter2` (QThreadPool) which sets
  O_NONBLOCK and `poll(POLLOUT, 60s)`. So EOF on our pipe = frame boundary; read the reply
  first for the geometry, then drain. (A memfd also works but you must poll for the size.)
* errors: `org.kde.KWin.ScreenShot2.Error.{NoAuthorized,Cancelled,InvalidWindow,
  NoActiveWindow,InvalidArea,InvalidScreen,FileDescriptor}`.
* Source for reference (branch Plasma/6.6): `src/plugins/screenshot/screenshotdbusinterface2.cpp`
  (`/tmp/sdbus2.cpp` held a copy), `src/utils/serviceutils.h`.

### 2. Authorisation (the thing that blocked us first)
`checkPermissions()` → `KWin::fetchRestrictedDBusInterfacesFromPid(pid)`:
caller pid (from `GetConnectionUnixProcessID`) → canonical `/proc/<pid>/exe` →
`KApplicationTrader` finds a **.desktop file whose `Exec=` first token canonicalises to that
exe** → allowed only if `X-KDE-DBUS-Restricted-Interfaces` contains
`org.kde.KWin.ScreenShot2`. Spectacle does exactly this.
⇒ **A Python script can never be authorised**; a native binary + desktop file can.
Installed by `make install-desktop`:
`~/.local/share/applications/io.github.kwcapture.desktop` with
`Exec=<abs path>/bin/kwcapture` + `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2`
(+ `kbuildsycoca6`). **Re-run it after moving/rebuilding the binary.**
Alternative (NOT used): start the session with `KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1` in
*kwin's* environment — disables the check for everyone in the session.

## Environment facts
Ubuntu, Plasma **6.6**, kwin 6.6.6 (`kwin_wayland` + `kwin_wayland_wrapper`), Wayland session,
single output `DP-1` 2560x1440@164.69Hz scale 1. `$XDG_RUNTIME_DIR=/run/user/1000` (tmpfs 13G).
`grim` absent; `xdg-desktop-portal` main daemon NOT running (portal/PipeWire route avoided).
KWin does **not** advertise `ext_image_copy_capture_manager_v1` (checked by dumping the
Wayland registry — `probe/globals.c`, compiled `probe/globals`); its XML on disk comes from
wlroots deps only. No `wlr-screencopy` (KWin is not wlroots). XWayland root window is black.
Toolchain: gcc, `pkg-config libsystemd` (sd-bus 259), `wayland-client`, `wayland-scanner`.
venv `~/way_scr_cap/.venv` (Python 3.14.4): numpy, pillow, mss, wxPython, dbus-fast, dasbus,
opencv-python-headless; plus `.pth` → `/usr/lib/python3/dist-packages` so `import gi`
(PyGObject 3.56 + Gst typelibs) also works inside the venv.

## Gotchas (each cost real time — respect them)
* **D-Bus fd passing**: `busctl`/`dbus-send` can't pass fds. Works with sd-bus
  (`sd_bus_message_append(m,"h",fd)`), `dbus-fast` (`Message(..., unix_fds=[fd])`), or Gio
  (`call_with_unix_fd_list`, **async-only**, arg order
  `bus_name, path, iface, method, params, reply_type, flags, timeout, fd_list, cancellable,
  callback`; `a{sv}` values must each be a `GLib.Variant`).
* sd-bus: pkg-config name is **libsystemd**, include `<systemd/sd-bus.h>`, and the public
  header has **no `_cleanup_`** macro — call `sd_bus_error_free()` manually.
* `__atomic_store_n()` does **not** accept `double`; plain-assign it and rely on the release
  store of the sequence counter to order it.
* **shm request flag needs a wake-up**: the first `serve` implementation polled with a
  250 ms timeout, so on-demand grabs took 273 ms. Fix = a FIFO `<shm>.req` opened O_RDWR by
  the daemon (never EOF, never blocks) and O_WRONLY|O_NONBLOCK by the client; write 1 byte
  per request.
* Pipes handed to KWin must be **O_NONBLOCK on our read end** in the daemon (else one
  in-flight drain stalls the whole loop and can deadlock at depth>1); handle EOF-before-size
  (set `hdr->error=EIO`, mark done) so the ring cannot wedge.
* Ring geometry: `KWC_HDR_STRUCT_SIZE` is asserted in **both** C (`_Static_assert`) and
  Python (`assert ctypes.sizeof(_Hdr)`). Bump both if you edit the struct.
* Keep the ring slot ≥ 5K frames (`5120*2880*4`) so a resolution change doesn't overflow;
  the file is sparse (226 MB apparent → 15 MB resident at 1440p).
* `np.frombuffer(mmap)` gives a read-only array; `setflags(write=copy)` in `_view()`.
  `mmap.close()` raises `BufferError` while ctypes/numpy hold views (caught in `close()`).
* Pillow: no `BGRA` mode — use `Image.frombuffer("RGBA", size, buf, "raw", "BGRA", 0, 1)`.
  `Image.fromarray(a, "BGRA")` does not work.
* `wl_output.geometry` width/height are **millimetres**; pixel size/refresh come from
  `wl_output.mode`. Connector name (`DP-1`) is the `wl_output.name` event → needs binding v4.
* `pkill -f kwcapture` from a shell command **matches that same shell command** and kills
  itself; use `pkill -f 'bin/kwcaptur[e] serv[e]'` or a unique `--shm` path to match.
* **The exec_shell tool caps out at 60 s** — `bench.py` (8 cases) and `tests.py` are close
  to that; run them with fewer seconds (`bench.py 1`) or background them.
* `PIL.ImageGrab` can leave a `spectacle` process holding your stdout pipe open (looks like
  a hang); `bench.py` reaps the ones it started.

## Packaging gotchas (v0.1.0)
* The wheel contains a compiled binary, so it must **not** be tagged `py3-none-any`:
  setting `root_is_pure = False` in `build_py.finalize_options` was NOT enough with the
  PEP 517 flow — override `bdist_wheel.get_tag()` (see `setup.py`) to get
  `py3-none-linux_x86_64`.
* `_native.binary_matches_arch()` reads the ELF `e_machine` field so a helper that came
  from a wheel built for another CPU is skipped (falls back to compiling here).
* Do **not** import the `kwcapture` package from `setup.py` (it imports numpy, which is not
  a build dependency) — the compile command is duplicated in `setup.py` on purpose.
* Use portable `-O2` in `setup.py`; `-march=native` only in the dev `make` build (or
  `KWCAPTURE_NATIVE=1`).
* KDE picks up a new desktop entry **asynchronously**: right after writing it, KWin can
  still answer `NoAuthorized` for a second or two → `Capture.start()` retries with backoff
  (0.1/0.3/0.6/1.0/1.5 s) and re-runs `kbuildsycoca6` every other attempt.
* One desktop entry per distinct helper path (`io.github.kwcapture-<sha1(path)[:10]>.desktop`)
  so several venvs coexist; `_desktop.prune()` drops entries whose binary is gone.

## Ideas not done yet
* Per-window capture (`CaptureWindow` + window enumeration; KWin has `org.kde.KWin`/Windows?).
* Multi-monitor: works via one `Capture` per screen name, but there is no combined-mode helper.
* Auto-restart the daemon inside `grab()` on `DaemonDead` (currently the caller must
  `restart()`; `kwcapture.grab()` singleton does re-create).
* Re-size the ring in place on resolution change instead of erroring out.
* Fractional scaling: `native-resolution` is set; behaviour with scale≠1 untested.
* If a non-KDE compositor is ever needed: `ext-image-copy-capture-v1`/`wlr-screencopy` with
  the XML in `/usr/share/wayland-protocols/` + `wayland-scanner` (KWin does not implement it yet).
