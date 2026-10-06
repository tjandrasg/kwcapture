# Changelog

## Unreleased

Captures now survive the things that break a long-running one: a monitor changing mode, a
window being resized or maximised, and the helper process dying.

- **`grab()` recovers by itself.** A daemon that was killed, crashed, or reaped for sitting
  idle is restarted and the frame retaken, so the caller does not have to notice. Turn it
  off with **`auto_restart=False`**, which restores the previous behaviour of raising
  `DaemonDead`. Recovery is bounded by **`restart_limit`** (default 5 *consecutive*
  restarts; the streak resets on the next good frame) so a daemon that cannot come back
  raises instead of respawning forever.
- **Resolution changes and window resizes are followed.** Frames simply come back at the new
  size — no need to re-create the `Capture`. **`Capture.resized`** is True on the frame where
  the size changed and **`Capture.last_geometry`** is the size of the frame just handed out;
  `geometry()` already tracked the live value.
- **`RingTooSmall`**, a new `CaptureError`, is what a frame bigger than the ring raises (a
  larger monitor mode, or a window grown past the ring's headroom). The ring cannot be
  grown in place — a client has it mapped at the old length, and writing a slot beyond that
  mapping would SIGBUS the reader — so the helper reports `ENOSPC` and exits, and a new
  daemon is started with a ring sized for the new geometry. With `auto_restart=True` that
  whole sequence happens inside one `grab()` call.
- **`slot_floor=(w, h)`** sets the resize headroom per ring slot (was a hardcoded 5120×2880
  constant in the helper, now `--slot-floor WxH`). Raise it for a 6K/8K display, lower it to
  shrink the footprint. The helper also reports the geometry it could not fit in its log.
- A window capture now **follows its app across a close-and-reopen**: if the captured handle
  disappears but the same name resolves again, the `Capture` moves to the new window instead
  of failing. A window that is gone for good still raises `WindowGone` — restarting cannot
  bring your window back — and a `TimeoutError` from a *live* daemon is never retried, so a
  wedged KWin stays visible rather than being masked by respawn churn.
- New observability on `Capture`: `auto_restarts` (cumulative), `last_restart_reason`,
  `slot_bytes`, `ring_bytes`.
- Tests: **156 checks** (was 116) — 119 functional (was 87) including a real resize test
  that launches an xterm, resizes it with `wmctrl`, and proves frames follow the window and
  that an overflowing ring heals, plus 37 ring-reader checks (was 29) covering the `ENOSPC`
  classification with no compositor.


## 0.4.0

Stale-frame detection for window capture, and two real leaks/crashes fixed.

- **`Capture(stale_check=True)`** — KWin does not render a minimised window, so a window
  capture silently repeats the last buffer forever with no error, no status and nothing in
  `stats()` to say so. With `stale_check=True`, `grab()` consults KWin (throttled to ~10/s)
  and sets **`Capture.stale_frame`**, warning once when a window goes stale.
  **`Capture.window_minimized`** answers the same question on demand for any window capture.
  Both default to off: the check is a D-Bus round trip and must not tax the fast path.
  `stale_frame is False` means *unknown*, not *fresh*, unless you enabled the check.
- Fix: **`restart()` leaked one file descriptor and one mapping per call.** `_start_once()`
  re-opened the ring fd/mmap without releasing the previous ones (measured 16 → 20 fds over
  4 restarts). A `_unmap()` helper now runs before re-opening and from `close()`.
- Fix: `sched_yield()` caught only `OSError`, but a missing libc symbol raises
  `AttributeError` — and it is called from `grab()`'s busy-wait, so it took down every
  capture on such a system. Now catches both, and the cached value is guarded with
  `callable()` so a non-callable can never be invoked.
- **The zero-copy read path is now read-only and self-validating (BUG-4).** A frame's
  metadata used to be read out of shared memory several times per `grab()`, through ctypes
  shadow objects, next to the numpy view of the same mapping — so two fields could belong
  to two different frames, and nothing checked that the advertised geometry fitted the
  ring. Now: one contiguous read of the frame descriptor; `slots`/`hdr_size`/`slot_bytes`
  validated once per daemon generation and every frame's `width`/`height`/`stride`
  bounds-checked before they become an offset or a shape; the ring is mapped
  **read-only**, so views are read-only for free and no client can write into the ring;
  `grab()` takes the newest published frame instead of the exact one it asked for; a
  `copy=True` read that the ring wrapped over is retaken once; and a read spanning a
  `restart()`/`close()` raises instead of returning a frame made of two daemons. A view
  keeps its bytes after `close()` (frozen at the last frame) instead of becoming invalid
  memory. **Honest caveat — these are correctness fixes, not a fix for the crash:** the
  flaky `TypeError: 'int' object is not callable` / SIGSEGV family that BUG-4 was about is
  *not* a kwcapture bug. It reproduces with plain numpy over an `mmap` and no kwcapture
  involved (`probe/race_bisect.py`, `probe/corruption_rate.py`), and it faults the old and
  the new read path at the **same rate** (`probe/fault_rate.py`,
  `probe/FAULT_RATE_RESULTS.txt`) — on this machine, which is running a 100 GB-RSS model
  server with no swap and whose kernel has oopsed once in page reclaim. See `AGENTS.md`
  BUG-4 for the whole story and the experiment that would settle it.
- New `tests/test_ring_reader.py`: the shared-memory reader tested against a synthetic ring
  (invalid descriptors, a concurrent writer, millions of reads) with **no compositor**
  needed, so it runs in CI.
- Tests: 87 functional checks (was 79), now also run under `-X dev`, plus 29 new
  ring-reader checks that need no compositor — 116 in total.


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
