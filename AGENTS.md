# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

Repo: **https://github.com/tjandrasg/kwcapture** (branch `main`; releases `v0.1.0`,
`v0.2.0` each with a prebuilt `linux_x86_64` wheel attached) and on PyPI as
**`kwcapture`** (https://pypi.org/project/kwcapture/) — publish new versions with
`.venv/bin/python -m twine upload -r pypi dist/<sdist and manylinux wheels>` (credentials
in `~/.pypirc`; never commit or print them). Author: Tjandra Satria Gunawan
<tjandra.satria@sci.ui.ac.id>. `origin` is SSH (`git@github.com:tjandrasg/kwcapture.git`).
There is no `gh` CLI here, so repo/release admin (creating releases, uploading assets,
topics) is done with the GitHub REST API via `curl` using whatever credential is
configured for github.com (it is in `~/.git-credentials`) — never commit or print a token.

Working dir: `~/way_scr_cap`. **Read this first if you are a fresh session.**
Status: **done and working** — ~40 fps full-screen / ~185 fps per-window Wayland capture,
Python API + CLI + 60 functional checks. See `README.md` for user-facing docs; this file
is the investigation log + gotchas.

## SESSION STATUS — 2026-10-06 20:20 (read this if you just woke up)

**v0.2.0 is RELEASED. v0.3.0 (focus tracking) is done locally and pushed; the remaining
step is to tag it and finish publishing (see the todo list below).**

* **Released**: commit `61d06df` tagged `v0.2.0`, pushed; **sdist 0.2.0 is on PyPI**
  (https://pypi.org/project/kwcapture/0.2.0/). The GitHub release for v0.2.0 does NOT
  exist yet — its workflow run failed (see the cibuildwheel finding below), and the local
  `linux_x86_64` wheel for it is in `dist/` (rebuild it for 0.3.0 instead).
* **v0.3.0 = focus tracking**, verified: full suite **68/68 PASS, 0 failures, 0 skips**
  (~35 s — the "~3 min" note below is stale). New: helper mode `--active-window-id`,
  `Window.active`, `active_window()`, `active_window_id()`, `list_windows(mark_active=…)`,
  `kwcapture windows -a/--no-active`. Version already 0.3.0 in `pyproject.toml` +
  `__init__.py`; CHANGELOG + README updated (README's wheel URL now points at v0.3.0).
* **CI discovery that explains why no release ever had wheels**: `release.yml` pinned
  `pypa/cibuildwheel@v2.21.3`, which pulls
  `quay.io/pypa/manylinux_2_28_x86_64:2024.10.07-1` — **that tag is gone from quay.io**
  (`Error response from daemon: No such image`), so *both* the v0.1.0 and v0.2.0 release
  runs failed at "Build manylinux wheels". Fixed to `@v4.3.0` (+ cp314 builds) — verify
  by dispatching `release.yml` on `main` (now harmless: the release-attach step is gated
  on `startsWith(github.ref, 'refs/tags/v')`). cibuildwheel is at 4.3.0; newest quay
  manylinux tags are dated 2026.x. **Read the CI job log with**
  `curl -sL -H "Authorization: Bearer $TOK" https://api.github.com/repos/tjandrasg/kwcapture/actions/jobs/<id>/logs`
  — it is **plain text**, not a zip (the `/actions/runs/<id>/logs` endpoint *is* a zip).
* **TODO for v0.3.0**: (1) `git tag v0.3.0 && git push origin main --follow-tags`; (2)
  confirm the release run goes green this time (it makes the GitHub release + manylinux
  wheels); (3) `rm -rf build dist && .venv/bin/python -m build`, sanity-test the wheel in a
  throwaway venv from `/tmp` (worked for 0.2.0: 159 ms startup, 39.5 fps, per-window grab),
  twine the **sdist** to PyPI; (4) once CI is green, **also upload the CI-built manylinux
  wheels to PyPI** — unlike `linux_x86_64` they are accepted, and then `pip install
  kwcapture` needs no compiler; (5) attach the local `linux_x86_64` wheel + notes to the
  release (REST API, *Release checklist* below).
* Housekeeping: repo-root `bin/kwcapture` is **stale v0.1.0 debris** (gitignored, *not* on
  `_native`'s search path — the real helper is `kwcapture/bin/kwcapture`).

**Next useful features** (see *Ideas not done yet*): `Window.pid`, auto-restart of a dead
daemon inside `grab()`, and non-normal windows (panels/desktop) via a KWin script.

## Goal
Make a **fast** full-screen capture program on Wayland. Original experiments
(`probe/bench_original.py`, `bench_result.md`): `PIL.ImageGrab` shells out to `spectacle`
(~2 fps); `mss` is 1100 fps but captures **XWayland** (black for native Wayland windows)
and dies when `$DISPLAY` is unset. Both unusable.

## What we ship (pip-installable package, v0.2.0)
`make setup` (or just `pip install .`) then `.venv/bin/python tests/test_kwcapture.py`.

| file | what |
|---|---|
| `kwcapture/native/kwcapture.c` | native helper: one-shot / `--bench` / `--list` / `--list-windows` / `serve` (daemon + shm ring); screen, area, workspace, `--window HANDLE`, `--active-window`; sd-bus + wayland-client |
| `kwcapture/native/include/kwcapture_shm.h` | shm ring protocol, **v2** (`KWC_HDR_STRUCT_SIZE` = 1912, `_Static_assert`ed) |
| `kwcapture/__init__.py` | Python API: `Capture`, `grab/latest/shot/shot_jpeg/stats/bench`, `Window`/`list_windows()`/`find_window()`, ctypes mirror of the header, `to_rgb`/`resize`/`png_bytes`/`jpeg_bytes` |
| `kwcapture/_native.py` | helper discovery: `$KWCAPTURE_BIN` → `kwcapture/bin/kwcapture` (wheel) → `~/.cache/kwcapture/…` → compile from the shipped source; ELF-arch check |
| `kwcapture/_desktop.py` | writes/refreshes/prunes the KWin authorisation desktop entry |
| `kwcapture/__main__.py` | CLI: `doctor [--fix --build] / setup / install-desktop [--uninstall] / screens / windows [--json -f] / grab [--window --active-window] / demo / bench` (console script `kwcapture`) |
| `pyproject.toml` + `setup.py` | packaging; `setup.py` compiles the helper during the wheel build (`build_py` → non-pure, `bdist_wheel.get_tag` → `linux_<arch>`), failure is non-fatal (runtime compile) |
| `tests/test_kwcapture.py` | 60 functional checks (screen/area/workspace/window/daemon/failure), also `pytest tests/`; `... windows` runs only the window section |
| `bench.py` | comparison table vs `mss` and `PIL.ImageGrab` |
| `Makefile` | `make` `install-desktop` `setup` `doctor` `test` `bench` `demo` `wheel` `sdist` `dev-install` `clean` |
| `probe/` | experiments: `globals.c` (dump compositor globals), Gio prototypes, scale/post micro-benchmarks |
| `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE` (MIT), `.github/workflows/ci.yml` | docs/CI |

Install story: **self-configuring** — first `Capture()` finds/builds the helper, writes the
desktop entry, retries while KDE's service cache notices it. Verified in a *fresh* venv
(`pip install dist/*.whl`, numpy only, no desktop entry present): ready in ~150 ms, 37.9 fps,
numpy-only fallback resize worked. Also verified installing straight from GitHub and from
the release wheel URL. Published on PyPI: `pip install kwcapture`.

## Results (2560x1440@164.69Hz, Plasma 6.6 / kwin 6.6.6, i9-13900K)
```
mss (XWayland)              1113.8 fps   0.9 ms   <-- BLACK/EMPTY, useless
PIL.ImageGrab (spectacle)      2.7 fps 357.1 ms
kwcapture raw BGRA view       38.4 fps  25.8 ms
kwcapture RGB full res        37.9 fps  26.0 ms
kwcapture RGB 1280 wide       38.0 fps  26.1 ms
kwcapture JPEG 1280           35.6 fps  28.0 ms   (grab + downscale + encode)
kwcapture latest()          551704   fps   0.0 ms   (view of already-published frame)
kwcapture one window 692x440   185.4 fps  4.7 ms  (v0.2.0, Capture(window=...))
```
Breakdown at 1440p: KWin grab ≈ 18-25 ms (≈11 ms floor even for a 320x180 area), pipe drain
≈5 ms (14 MB). Throughput ceiling ≈47 fps (KWin serialises screenshot jobs); `depth=2`
reaches it, depth 3/4 only add latency (grab_ms 37/58/80 ms). Post-processing: cv2
`INTER_AREA` 2560→1280 = 0.1 ms, `cvtColor` BGRA2RGB of the small frame ≈3 ms, cv2 JPEG
1280 = 3.5 ms / 2560 = 4.5 ms, PNG 23 ms (avoid), PIL resize 17 ms (avoid → use cv2).
Colour fidelity verified vs an independent Spectacle capture: MAD **0.0** (9.7 if R/B swapped).

## THE THREE KEY FINDINGS

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

### 3. Per-window capture and window enumeration (v0.2.0)
`CaptureWindow(handle s)` / `CaptureActiveWindow` on the same ScreenShot2 interface;
`handle` is **`QUuid` text** — `workspace()->findWindow(QUuid(handle))`, i.e. KWin's
`Window::internalId()`. Braced (`{2c14…}`) or bare both parse. The reply carries
`windowId` instead of `screen`. Which pixels you get (from
`src/plugins/screenshot/screenshot.cpp::takeScreenShot(Window*)`):

| options | geometry |
|---|---|
| neither `include-decoration` nor shadow | `clientGeometry()` (what we default to) |
| decoration without shadow | `frameGeometry()` |
| decoration + shadow | `visibleGeometry()` = window item's scene rect (incl. shadow); the shadow is transparent (alpha 0) |

Measured on a 692x467 KCalc: client 692x440, `--decoration` 822x598. Occlusion does not
crop the result (KWin renders that window's item, not the screen region), and a
**minimised window still captures** — KWin keeps its buffer.

**KWin has no window-list D-Bus call.** What works, and needs no authorisation (only the
pixel grab does):

* `org.kde.KWin` `/WindowsRunner` `org.kde.krunner1` **`Match("")`** → `a(sssida{sv})`.
  An **empty query matches every window** (`name.startsWith("")` in
  `windowsrunnerinterface.cpp`), each match id being `"<action>_<uuid>"`.
  Do *not* use the `"window"` keyword: it is translated, so it breaks on non-English
  locales. Empty query also returns each window twice (once per desktop) → dedupe.
  `Run("<action>_<uuid>", "")` acts on a window (0=activate, 1=close, 2=minimise) — handy
  in tests; `busctl call … Run ss "2_{uuid}" ""` (busctl wants the whole signature as one
  token: passing `s … s …` gives "Too many parameters for signature").
* `org.kde.KWin` `/KWin` `getWindowInfo(uuid s)` → `a{sv}`: caption, `resourceClass`,
  `resourceName`, `desktopFile`, role, icon, x/y/width/height (**doubles**, not ints!),
  minimized/fullscreen/keepAbove/keepBelow/noBorder/skipTaskbar/skipPager/skipSwitcher,
  maximizeHorizontal/Vertical, `type`, `layer`, `desktops` (`as`; `activities` is also an
  `as` — only collect the one you asked for), uuid.
  `queryWindowInfo()` is *not* a list: it makes KWin ask the **user to pick a window**.

Only **normal** windows show up (krunner filters `!isNormalWindow()`: no panels/docks,
desktop, splash, override-redirect, unmanaged). `CaptureWindow` still accepts their
handles if you obtain them elsewhere.

**The focused window IS observable, cheaply, and needs no KWin script** (v0.3.0;
this replaces the "no active-window getter over D-Bus" note in *Ideas*):
* `supportInformation` was checked first and **in Plasma 6.6 it lists no windows at
  all** — version/drivers/effects/plugins only. That route is dead, don't retry it.
* KWin replies to `CaptureActiveWindow` **before** writing any pixels, and that reply
  carries `windowId`. So: make the call with a pipe, parse the reply, `close()` the read
  end without draining → KWin's writer thread gets POLLERR/EPIPE and abandons the frame.
  **No errors appear in the kwin journal** (checked with
  `journalctl --user --since "-3 min" | grep -i kwin`) and it costs **≈8 ms per call
  including process spawn** (measured: 10 sequential helper invocations in 87 ms) because
  the compositor's render happens in the writer thread, off the reply path.
  Implemented as helper mode `--active-window-id` (stdout = handle; **exit 2 = nothing has
  focus**, exit 1 = error) → `active_window_id()` / `active_window()` / `Window.active`,
  `list_windows(mark_active=True)` (default; the query needs screenshot authorisation,
  plain enumeration does not, so failures there are swallowed and leave no flag set).
* Verified by activating each window with krunner `Run "0_<uuid>"` and asserting the
  reported handle (4/4 windows matched).
* `busctl` calls with **no input args** must be written without a type: `activeOutputName`
  → `busctl --user call org.kde.KWin /KWin org.kde.KWin activeOutputName` → `s "DP-1"`.
  (Passing `s ""` to it makes the call fail silently — that is what the empty probe output
  was.) `/KWin` also has `currentDesktop`, `GetAll`, `getWindowInfo`, `queryWindowInfo`,
  `showDesktop`, `killWindow`. Other KWin objects: `/Scripting`, `/Session`,
  `/VirtualDesktopManager`, `/Layouts`, `/Effects`, `/ColorPicker`, `/Compositor`,
  `/ScreenSaver`, `/component/<app>` (per-app entries).
* `getWindowInfo()` replies **no pid and no focus flag** (confirmed by dumping the whole
  `a{sv}`): keys are activities, caption, clientMachine, desktopFile, desktops, fullscreen,
  height, keepAbove/keepBelow, layer, localhost, maximizeHorizontal/Vertical (**ints**, not
  bools), minimized, noBorder, resourceClass, resourceName, role, skipPager/Switcher/
  Taskbar, type, uuid, width, x, y.

**A closed window does not produce a D-Bus error**: KWin replies *successfully* with a
0x0/stride-0 image (the scene item is gone → empty `visibleGeometry`). Treat
`width==0 || stride*height==0` as a failure, otherwise you wait forever for pixels that
never come and the ring wedges. All failures now publish the frame with a `status`
(`KWC_ERR_*`, `KWC_ERR_EMPTY_FRAME`, `ETIMEDOUT`) so `frame_seq` keeps moving; the Python
side turns them into `WindowGone` / `NoActiveWindow` / `CaptureError`. Same for a request
that never gets a reply (20 s safety valve in the serve loop).

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
* **sd-bus: you cannot leave a struct early.** `sd_bus_message_exit_container()` on a
  partially read `(sssida{sv})` entry fails, which silently ends the loop after one
  element. Read every field (`sd_bus_message_read(m, "sssid", …)`), then
  `sd_bus_message_skip(m, "a{sv}")` for the property dict (it can carry an icon pixmap),
  then exit. And when you read a signature off `busctl` output, count the letters:
  `(sssida{sv})` = s,s,s,i,d,a{sv} — there is no `u` in there.
* **A stale ring file SIGBUSes the client.** `serve` opens the shm with `O_TRUNC`, so if a
  client maps the previous daemon's file (same path, `restart()`, or two `Capture`s on one
  default path) the mapping goes past EOF the moment the new daemon truncates it. Fixes:
  `unique_shm_path()` per Capture instance, `_start_once()` unlinks the old shm+FIFO first,
  and the startup wait also requires `hdr.daemon_pid == proc.pid`.
* Pipes handed to KWin must be **O_NONBLOCK on our read end** in the daemon (else one
  in-flight drain stalls the whole loop and can deadlock at depth>1); handle EOF-before-size
  (set `hdr->error=EIO`, mark done) so the ring cannot wedge.
* Ring geometry: `KWC_HDR_STRUCT_SIZE` is asserted in **both** C (`_Static_assert`) and
  Python (`assert ctypes.sizeof(_Hdr)`). Bump both if you edit the struct (v1=1776,
  v2=1912: +`slot[].status`, +`target`, +`window[64]`), and bump `KWC_VERSION` when the
  *meaning* changes so a mismatched helper is refused instead of misread. Check C offsets
  against ctypes with `offsetof` vs `ctypes.<field>.offset` (v2: slot=248, window=184,
  slot.status=112).
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
* **The exec_shell tool's default timeout is 10 s** (it accepts longer values — pass
  `timeout=` explicitly). The full `tests/test_kwcapture.py` run is ~3 min; use
  `... quick` (~2 min) or `... windows` (~30 s), or background it and read the log.
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

## CI notes (learned the hard way — first 5 runs all failed)
* **Test the installed package from OUTSIDE the checkout.** Running `python -c "import
  kwcapture"` in the repo root imports the source tree (cwd shadows site-packages), so the
  "wheel contains the helper" assertion failed even though the wheel was correct.
* cibuildwheel's default image was `manylinux2014` (CentOS 7) → **`dnf` does not exist**
  there, only `yum`. Pin `CIBW_MANYLINUX_X86_64_IMAGE: manylinux_2_28` and write
  `CIBW_BEFORE_ALL_LINUX` as `dnf … || yum …`; EL8's pkg-config package is
  `pkgconf-pkg-config`, EL7's is `pkgconfig`.
* **PyPI rejects `linux_x86_64` wheels** (`400 … unsupported platform tag`) — only
  manylinux/musllinux. Hence PyPI currently carries the sdist; the `linux_x86_64` wheel is
  only on the GitHub release, and manylinux wheels must come from cibuildwheel.
  auditwheel must be told `--exclude libsystemd.so.0 --exclude libwayland-client.so.0`
  (we intentionally do not vendor the compositor libs).
* Force-pushing a rewritten history needs `git push --force` — `--force-with-lease` said
  "stale info" because `git filter-branch --all` had rewritten `refs/remotes/origin/main`
  too. `git fetch` first, then force-push.
* A tag push runs the workflow **from the tag's commit**, so `release.yml` fired when I
  re-pointed `v0.1.0`; publishing is opt-in (`workflow_dispatch` + `publish: true`) so it
  cannot push anything to PyPI by accident.

## Release checklist (do this in order; v0.2.0 was published this way)

1. Bump the version in **both** `pyproject.toml` and `kwcapture/__init__.py`, update
   `CHANGELOG.md` + `README.md` (including the release-wheel URL at the top of README).
2. `make && .venv/bin/python tests/test_kwcapture.py` — everything must pass on the real
   desktop (CI only checks that it *builds and imports*).
3. `git commit` the lot, then `git tag vX.Y.Z && git push origin main --follow-tags`.
4. Build the artefacts here: `.venv/bin/python -m build` → `dist/*.tar.gz` +
   `dist/*-py3-none-linux_x86_64.whl`. Sanity check the wheel in a throwaway venv **from
   outside the checkout** (`/tmp`), including a real `Capture()` + `list_windows()`.
5. PyPI (sdist only — PyPI rejects `linux_x86_64`): `rm -f dist/*linux_x86_64.whl.copy`
   and `.venv/bin/python -m twine upload -r pypi dist/kwcapture-X.Y.Z.tar.gz`.
   Verify with `curl -s https://pypi.org/pypi/kwcapture/json`.
6. The tag push runs `release.yml`, which builds the sdist + manylinux wheels and creates
   the GitHub release (via `gh` on the runner, `github.token`). Then upload the local
   `linux_x86_64` wheel as an extra release asset with the REST API:
   `curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/octet-stream" \
    --data-binary @dist/<wheel> https://uploads.github.com/repos/tjandrasg/kwcapture/releases/<id>/assets?name=<wheel>`
   (token from `~/.git-credentials`, release id from `/repos/.../releases/tags/vX.Y.Z`).
7. Add the release notes to the GitHub release body (`PATCH …/releases/<id>`), and confirm
   `pip install kwcapture` in a clean venv reports the new version.

## Ideas not done yet
* ~~Mark which listed window is *active*~~ **done in v0.3.0** — see finding #3
  (`Window.active`, `active_window_id()`, `--active-window-id`).
* `getWindowInfo` gives no pid — a `Window.pid` would need `/proc` matching by app id.
* Expose non-normal windows (panels, desktop, overlays): krunner filters them out. A KWin
  script or the qml console could hand out those handles; `Capture(window=…)` accepts them.
* Window resize handling: the ring slot floor is 5K-sized, so a window growing is fine,
  but a *maximised* window on a >5K display would still hit `ENOSPC` → helper exits.
* Multi-monitor: works via one `Capture` per screen name, but there is no combined-mode helper.
* Auto-restart the daemon inside `grab()` on `DaemonDead` (currently the caller must
  `restart()`; `kwcapture.grab()` singleton does re-create).
* Re-size the ring in place on resolution change instead of erroring out.
* Fractional scaling: `native-resolution` is set; behaviour with scale≠1 untested.
* If a non-KDE compositor is ever needed: `ext-image-copy-capture-v1`/`wlr-screencopy` with
  the XML in `/usr/share/wayland-protocols/` + `wayland-scanner` (KWin does not implement it yet).
