# Changelog

## 0.3.0

Which window has focus, and prebuilt wheels for PyPI.

- **`Window.active`** — `list_windows()` now marks the window that has keyboard focus
  (pass `mark_active=False` to skip the extra query). **`active_window()`** returns it as
  a `Window`, **`active_window_id()`** as a KWin handle (`None` when nothing is focused).
  CLI: `kwcapture windows` shows an `active` flag, `kwcapture windows -a` lists only the
  focused window. KWin has no focus query over D-Bus, so the helper asks for an
  active-window capture and reads `windowId` out of the reply — KWin sends that **before**
  writing any pixels, so the pixels are dropped: ~8 ms, no copy, no KWin script needed.
- **Prebuilt wheels.** The release workflow had never actually produced any: it pinned a
  cibuildwheel whose dated manylinux image has since been removed from quay.io, and used a
  `{dest}` placeholder that cibuildwheel 4 no longer substitutes. Releases now carry a
  `py3-none-manylinux_2_28_x86_64` wheel — the helper is a standalone executable rather
  than a Python extension module, so one wheel serves every CPython >= 3.9 on x86-64 Linux
  and no compiler is needed to install it.

## 0.2.0

Per-window capture and window enumeration.

- **`Capture(window=...)`** captures a single window; **`Capture(active_window=True)`**
  captures the focused one. `window=` takes a KWin handle (`{2c14f294-…}`) or a name:
  caption, app id, desktop file, or a unique substring. Uses `ScreenShot2
  CaptureWindow(handle)` / `CaptureActiveWindow` under the hood.
- **`list_windows()`** returns every capturable window as a `Window` (id/handle, name,
  app_id, geometry, minimised/fullscreen/maximised, desktops, …); **`find_window(spec)`**
  resolves a name or handle, raising `WindowNotFound` / `AmbiguousWindow`. CLI:
  `kwcapture windows [-f NAME] [--json]`, `kwcapture grab --window NAME|HANDLE`,
  `kwcapture grab --active-window`. KWin cannot list windows on its screenshot interface,
  so the helper reads the handles from `/WindowsRunner` (krunner, empty query matches
  everything — locale independent) and the details from `getWindowInfo(handle)`.
- **`WindowGone`** is raised when a captured window is closed. The helper now publishes
  failed frames (with a status code) instead of stopping the ring, so a vanished window,
  a refused request or a missing reply can no longer wedge a daemon; the other captures
  in the process are unaffected.
- Shared-memory protocol v2: per-frame `status`, `target` kind and the window handle.
  Rebuild old helpers (`kwcapture setup`); a v1 helper is rejected with a clear message.
- Fix: two `Capture` objects in one process used to share the default ring file (the
  second daemon truncated the file the first one had mapped). Each instance now gets a
  unique path, and `restart()` no longer maps (or SIGBUSes on) a dead daemon's stale ring.
- Fix: the helper now lists all windows, and `--window` accepts handles with or without
  braces.
- Tests: 60 functional checks (was 27), including launching real windows, minimising
  them, closing them underneath a running capture, and name resolution.

## 0.1.0

First public release.

- `bin/kwcapture` native helper (sd-bus, single file C): one-shot, `--bench`, `--list`,
  and a `serve` daemon that keeps a D-Bus connection open and publishes frames into a
  shared-memory ring.
- Python API: `Capture` (`grab` / `shot` / `shot_jpeg` / `latest` / `stats` / `bench`),
  `list_screens()`, zero-copy BGRA views, optional OpenCV-accelerated downscale+encode.
- Automatic setup on first use: compiles the helper if the wheel did not ship one, and
  writes the `~/.local/share/applications` desktop entry KWin requires to authorise
  `org.kde.KWin.ScreenShot2`.
- CLI: `kwcapture doctor|setup|install-desktop|screens|grab|demo|bench`.
- Tested against KDE Plasma 6.6 / kwin 6.6.6 on X86-64; ~40 fps at 2560x1440.
