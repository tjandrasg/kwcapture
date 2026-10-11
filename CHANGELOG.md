# Changelog

## Unreleased

The desktop entry this package writes finally names an icon that **exists**, and the artwork
behind it ships inside the package instead of being re-drawn by whoever packages it. The artwork
is **`logo/kwcapture-mark.svg` and only that**: the icon is the official mark at every size, and
the permitted transformations are resize and re-render (see the second bullet — this round
started out shipping a different drawing and was corrected). No capture code changed, nothing
here runs at import time, and nothing here can make a screenshot slower.

- **New `kwcapture/_icons.py`; the icons now ship in the wheel.** The **official mark** —
  `logo/kwcapture-mark.svg` — at 16/24/32/48/64/128/256/512 plus that same SVG as the scalable
  entry, laid out as the freedesktop **hicolor** theme
  (`kwcapture/icons/hicolor/<size>/apps/kwcapture.png`), with a `COPYING.md`
  beside them: the pictures are CC BY 4.0, the code MIT, and an installed tree now says which is
  which where a reader will actually see it. Stdlib only — the PNG IHDR is read by hand — so no
  Pillow and no import-time work. **10 files in the wheel and 10 in the sdist**, measured by
  building both; `logo/` itself stays out — 1.5 MB on this checkout, 1.1 MB of it generated review
  PNGs (`du -sb logo --exclude='*.jsonl'`; the first draft of that number said "~700 KB" and the
  measurement corrected it).
- **`install-desktop` and `setup` install them**, into `$XDG_DATA_HOME/icons/hicolor` and never
  into a system directory: this runs as the user, into a tree that Wine and every other
  installer also writes to. `--no-icons` opts out. Sources are validated *before* anything is
  written (a PNG's IHDR against the size its directory promises, plus the presence of alpha),
  each write goes through a temp name + `os.replace`, and the bytes are re-read afterwards — so a
  corrupt package leaves the theme exactly as it was rather than half-branding it.
- **The bug: `Icon=accessories-screenshot`, carried since the first release, resolves in no theme
  on the desktop this project targets.** KDE ships `accessories-screenshot-tool`, HighContrast
  ships `applets-screenshooter`; the name from the naming spec is a suggestion, not a file.
  **A `;` fallback chain is not the fix** — measured on this machine: GLib's
  `DesktopAppInfo.get_icon()` puts the whole value into a `GThemedIcon` as **one** name
  (`Icon=kwcapture;x` → names `['kwcapture;x', …]`), and KService stores it verbatim
  (`m_strIcon = entryMap.take("Icon")`), so a chain resolves to *neither* name on *both*
  consumers, our own icon included. So the value is **resolved when the entry is written**
  (`pick_icon_name()`), against the themes actually installed here, and the entry gets exactly
  one name that exists on this machine — worst case the old spec name, i.e. never worse than
  before.
- **New `refresh_entries()`,** because entries are keyed per helper binary: three virtualenvs on
  one machine means three entries, and installing from one refreshes one. Two of the three
  entries on the developer's desktop were still pointing at the dangling name *after* the fix
  existed. `install-desktop` now rewrites every entry it owns while preserving each file's own
  `Exec=` (KWin's authorisation key is the sha1 of that path, so the auth survives — checked),
  and `--uninstall` removes the icons too, but only those whose sha256 still matches what we
  ship: a `kwcapture.png` somebody else drew is left where it is.
- **`kwcapture doctor` reports them**, in a line that reads *brand icons: 9 files in
  ~/.local/share/icons, entry uses `Icon=kwcapture`* — and `doctor --fix` installs them. A missing
  set is a note, **never** a problem count: branding must not make a working capture look broken.
  Verified on the target desktop: 9 files installed, all three entries `Icon=kwcapture`,
  `desktop-file-validate` silent.
- **The icon is the mark, at every size — the owner's decision, and it is now enforced.** An
  earlier revision of this work reasoned that a desktop icon is seen at 16-48 px, that `APTURE`
  is mush below ~64 px, and therefore shipped the **monogram** (`glyph-*.png`,
  `kwcapture-mark-mono.svg`). That was a build script making a branding decision that belongs to
  the owner. Reverted: `logo/icon/` renders the mark at nine sizes (16…1024) and nothing else,
  `sync_package_icons.py` copies those plus `logo/kwcapture-mark.svg`, and the monogram files are
  deleted. The consequence is documented instead of dodged — at 16 px the word is unreadable.
  Tiles changed with it: the mark sits at **79 %** of a masked tile, measured as the largest
  fraction that loses no ink under the host's mask (full bleed loses **4 015 px, worst 45.6 px
  past the inscribed circle**; at 79 %, zero), and `tiles.py` fails the build if that stops being
  true. `tests/test_icons.py` gained 9 checks: the scalable icon must be `kwcapture-mark.svg`
  byte for byte and every PNG must be that mark's render of its size — **98 checks now**.
- **`logo/sync_package_icons.py` is now the only sanctioned path from `logo/icon/` into the
  package**: a byte-for-byte copy that never resamples, with `--check` for drift, reading the
  size list out of `_icons.PNG_SIZES` so the two trees cannot disagree about which sizes exist.
  Every shipped size is a directory `/usr/share/icons/hicolor/index.theme` actually lists — so
  the mark is now rendered at 16/24/32/48/64 too, where it previously existed only from 128 up.
  The test suite runs `--check`, so "the desktop icon is last month's render" fails a build, in
  CI as well as on the machine that made the change.
- **Packaging:** `MANIFEST.in` and `[tool.setuptools.package-data]` carry `kwcapture/icons/` into
  sdist and wheel — **one glob per theme directory** (`icons/hicolor/*/apps/*`), because
  setuptools globs do not cross `/`, which a `icons/**`-style pattern quietly fails to do.
- **The mark was recoloured, and the recolour is provably *only* paint.** Palette **P2**, the
  owner's decision of 2026-10-11: green `#00ac4e → #008c46`, blue `#0000ff → #7f7fff`. Chosen
  because every half now clears the WCAG **3:1** floor for non-text content on *both* grounds a
  reader meets — green **4.34** on white / **4.36** on GitHub dark `#0d1117`, blue **3.29** /
  **5.75** — where the pair it replaces failed twice (blue **2.20:1** on dark, green 3.00:1 on
  white). The proof is a command, not an adjective: strip every 6-digit hex from both sides of
  `diff` against the previous commit and **nothing is left** — no path, no `transform`, no `#type`
  matrix — and `gen_logo.py --mark` still reproduces the shipped SVG **byte-identically** from the
  changed constants (a paint variant aimed at a shipped path is still refused, so the artwork stays
  reproducible from generator state rather than from a command line). Everything downstream was
  rebuilt and re-measured: 17 images in `logo/icon/`, every README figure, the packaged copies, the
  installed theme files (all byte-identical to the artwork), and every ratio, byte size and sha256
  in the logo docs. What it traded is stated in `logo/README.md` §8 rather than buried: the two
  halves are now **1.32:1** apart instead of 2.87, so the C reads on **hue** and would collapse in
  greyscale.
- **New `logo/contrast_report.py`, and a check that had quietly gone blind.** Every ratio this
  project quotes now comes from one file that reads the palette out of `gen_logo.py` and prints the
  2×2 against white and `#0d1117`, the half-vs-half split, the luminance window **[0.1164,
  0.3000]** that decides what "legal on both grounds" can even mean, and a dichromatic estimate;
  `--min` makes it a gate (exit 1) so a palette regression cannot ship by accident, and passing the
  old hexes reproduces the old numbers. It exists because `render_agreement.py` had been
  identifying the green half with `fill.startswith("#00a")` — true of `#00ac4e`, false of
  `#008c46`, so the recolour switched off the only check that can see *where* an engine paints,
  at exit 0, with a clean report. The palette is now **read, never repeated**, the pixel classifier
  matches by hue, and it refuses to guess when it cannot find the palette.
- **`logo/kwcapture-mono.svg` is deleted** (the owner ruled the monogram "unofficial variant and
  historical value only"), so the committed artwork is `kwcapture.svg`, `kwcapture-mark.svg` and the
  two sketches. `gen_logo.py --monogram` stays as a **mode** and now **requires `--out`**, because a
  mode whose default path re-creates a deleted artefact is how an icon set once shipped the wrong
  drawing; the figures that use a monogram render one into a temp directory, and doing that made it
  visible that the figures were drawing **two different monograms** (the original sketch's and the
  mark's) from one file name — they are separate now.
- **`logo/icon/tiles.py --sweep` no longer rewrites the icons it is measuring.** The five tiles were
  built by a module-level list of calls, so *importing* the module built them: `--sweep`, whose whole
  job is to print how much room `FIT` has left, also re-saved `apple-touch-icon.png`, `pwa-192.png`,
  `pwa-512.png`, `maskable-512.png` and `github-avatar-400.png` through Pillow — *after*
  `icon/build.sh` had re-encoded every PNG in `icon/` with ImageMagick. The result was a set whose
  committed bytes were not what the build produces: **identical pixels, different container**
  (34 836 B in one `IDAT` against the build's 34 044 B in two), so `git status` went dirty on a
  clean rebuild while nothing shipped was wrong. `--sweep` now measures and writes nothing. No
  artwork, no size and no `FIT` value changed; the guard that refuses a clipped tile was shown to
  still fire, on three sabotaged values of the constant.
- **A second in-suite failure, also reported rather than patched:** the
  *regression: BUG-4 zero-copy read path* block reports `[FAIL] BUG-4 regression ran` on some runs,
  so the suite measures **162 passed + 1 failed** rather than 165. It fails with three different
  errors in seven runs — two `AttributeError`s naming the wrong object as `self`, and a
  `CaptureError: unhandled pixel format 6` that cannot be true as printed, because 6 is in the
  allow-list it cites. It reproduces from a **pristine `HEAD` worktree** and **0 of 5** times when
  the same sequence is run standalone, so it is cross-test interference, not the read path — and the
  reason it cannot be pinned down is that the harness prints `type(e): e` and discards the
  traceback. See `AGENTS.md` → **FLAKE-3**.
- **A live-desktop flake, reported rather than patched:** `tests/test_kwcapture.py`'s
  `alpha is opaque` fails on ~96 % of grabs on this machine — **4 pixels at alpha 253/254**, in the
  bottom corners of a rounded-corner window KWin is compositing — and it reproduces from a pristine
  `HEAD` worktree with none of the above changes, so it is not the recolour. The assertion is left
  alone; see `AGENTS.md` → *OPEN BUGS* **FLAKE-2** for why loosening it would retire a real question
  about the alpha channel of a compositor grab.
- **`tests/test_icons.py`: 98 checks, no compositor needed**, now a CI step next to the
  ring-reader suite — and `probe/sabotage_icons.sh`, which breaks each guard in turn, restores it
  and compares the outcome with what it expected: **10/10 detected** here, clean tree green. It
  covers the awkward ones deliberately: a *stale* file counts as missing; uninstall cannot delete
  a foreign `kwcapture.png`; the verify-after-write fires when a write lies (`_write_atomic` is
  patched to flip a byte inside the IDAT, where nothing else in the module could notice — an
  earlier revision corrupted the header instead and passed for the wrong reason); and
  `theme_has_icon()` is graded against an independent `find`-based oracle, because its first
  version assumed hicolor's `16x16/apps/` layout and therefore reported Breeze's own screenshot
  icon — which lives in `apps/48/` — as missing **on a KDE desktop**.

**Not in this repo's hands, but done and verified:** the GitHub **social preview** is a stored
upload, not a render of the repository, so palette P2 had to be re-uploaded by hand — no API can do
it, which was probed rather than assumed. The owner did, and it now verifies off the pixels: the
live `openGraphImageUrl` is a **new object id** (`5425fcdb-…`, where the previous palette's upload
was `dc44cc05-…` — GitHub mints a fresh URL per upload) serving **1280×640 / 84 871 B** with **0 of
819 200 pixels** differing from the committed `logo/icon/github-social-preview.png`, against **6.73 %**
differing from the pre-P2 card. Between the upload and this verification there was a window in which
`usesCustomOpenGraphImage` read `true` while the pixels were the old palette — which is exactly why
the check is written in pixels and not in the flag: **after any change to that file, re-fetch the URL
and compare pixels with the committed artwork.** The optional user profile picture is unrelated
artwork, measured: `github.com/tjandrasg.png` differs from `icon/github-avatar-400.png` in 100 % of
pixels in both palettes, so that asset exists and is unused rather than stale.

**Behaviour change, for anyone scripting it:** `kwcapture install-desktop` now also writes files
under `$XDG_DATA_HOME/icons`, and `install-desktop --uninstall` removes them again (hash-checked,
ours only). Pass `--no-icons` to either for the old exactly-one-file behaviour. The automatic
first-`Capture()` path is unchanged and still writes one `.desktop` file and no icons — there is
a check asserting that promise. What an entry's `Icon=` value says remains machine-specific and
is not a stable interface.

## 0.6.0 — 2026-10-09

The windows a taskbar would not show are now findable, not just capturable: `list_windows()`
asks KWin's scripting interface in addition to its application-window list, so dialogs, tool
windows, the panel and the desktop itself come back with a handle you can capture — and a
handle you got somewhere else is always accepted. Nothing is installed, nothing stays loaded
in KWin, and no window is raised or focused along the way.

- **`list_windows()` now returns every window KWin can capture, not only the ones KWin
  calls *normal*.** KWin's krunner interface (`/WindowsRunner`) — the only unrestricted
  enumeration there is — filters on `Window::isNormalWindow()`, so dialogs, tool windows,
  docks/panels, the desktop, splash screens and override-redirect popups were invisible:
  capturable through `CaptureWindow(handle)`, impossible to *find*. (Real case: Winamp's
  big skinned window is `_NET_WM_WINDOW_TYPE_DIALOG`; only its tiny `NORMAL` sibling was
  ever listed.) The helper now also asks KWin's **scripting interface**
  (`org.kde.kwin.Scripting.loadScript` + `org.kde.kwin.Script run`) whose JS
  `workspace.windowList()` is KWin's unfiltered list. The script is generated per call into
  `$XDG_RUNTIME_DIR` (0600), answers on the helper's own unique bus name with a nonce, and
  is unloaded and deleted before the helper exits — ~0.5 ms, nothing installed, no config
  touched, and no focus change anywhere. Windows that came from there carry
  `krunner_listed=False`; every window now also carries `window_type_name` (`"normal"`,
  `"dialog"`, `"dock"`, `"desktop"`, …) and a `Window.normal` property.
- **`list_windows(all_types=…)`** — `False` restricts it to KWin's own list again (no
  scripting round trip). **`require_full=True`** turns an unavailable scripting interface
  into a `CaptureError` instead of the default quiet fallback to the filtered list; the CLI
  equivalent is `--normal-only` / `--require-full` (exit 3), and `kwcapture doctor` now
  reports which of the two it got.
- **`Capture(window=HANDLE)` / `--window HANDLE` accept a handle KWin's list does not
  mention** (validated with `getWindowInfo` instead of against the listing), so a handle
  obtained elsewhere — a KWin script, `--active-window-id`, a log — is always usable.
- **Behaviour change:** the wider list means a *name* can now match more than it used to —
  an app whose dialog shares its caption matches twice and raises `AmbiguousWindow`
  (`.candidates`) where it used to resolve. Resolve by handle, or pass
  `all_types=False` / `--normal-only`.
- Functional suite: 152 → **165 checks**. Three probes keep the mechanism reproducible on its
  own: `probe/non_normal_windows.py` (the user-facing reproducer — capture every window KWin's
  list hides, assert focus never moved and nothing was left behind),
  `probe/kwin_script_enumerate.py` (the raw scripting round trip) and
  `probe/kwin_script_failure_path.py` (a deliberately broken script must report a reason
  instead of timing out).
- `kwcapture doctor` now says which enumeration it got, and `kwcapture windows` gained
  `--normal-only` / `--require-full`.

## 0.5.0 — 2026-10-07

Monitors are now first-class (list them, capture one by name or id), fractional scaling is
measured rather than guessed, and captures survive the things that break a long-running
one: a monitor changing mode, a window being resized or maximised, and the helper process
dying.

- **`list_monitors()`** returns a `Monitor` per output — `index`, `id`, `name`, `make`,
  `model`, `position`, `geometry`, `refresh_hz`, `scale` — in a stable top-left-first order,
  mirroring `list_windows()`. **`Capture(monitor=...)`** captures one by connector name
  (`"DP-1"`, substrings ok), by the compositor's own numeric id, by its `list_monitors()`
  index, or by a `Monitor`. `find_monitor()` raises `MonitorNotFound` (listing what exists)
  or `AmbiguousMonitor` (with `.candidates`) instead of guessing, and resolution happens
  eagerly — a typo is an error now, not a compositor failure later. CLI: `kwcapture
  monitors [--json|--measure-scale]` and `grab --monitor NAME|ID`.
- **`area=` is relative to the monitor** when `monitor=` is given, so the same rectangle
  means the same corner on a mixed-DPI desk. Without `monitor=`, `area=` stays in global
  scene coordinates as before.
- **Fractional scaling, measured and verified on real 75 % / 125 % displays.** Whole-output
  frames are captured at device resolution (unchanged), but `wl_output` can only advertise
  an *integer* scale, so a 125 % display says `1` there. **`measure_output_scale()`** /
  **`Monitor.effective_scale`** measure the real scale from KWin (the same small area
  grabbed once in device pixels and once composited, ratio = scale), with
  `Monitor.fractional`, `Monitor.logical_geometry` and `Monitor.to_physical()` /
  `to_logical()` for conversion, plus `Capture.scale` (what KWin applied to this frame) and
  `Capture.pixel_scale` (measured, cached).
- **Two different scales, and they are not interchangeable.** The **display scale** (0.75 /
  1.25 measured) is what relates logical pixels to the pixels of a panel, and only a
  *whole-output* grab reports it. Region captures are answered at the **scene factor**
  (`Monitor.area_scale` / `Capture.area_scale`) — one number for the whole desktop, 1.25 on
  both outputs of the test desk, whose display scales were 0.75 and 1.25. So `area=(w, h)`
  returns a `w*area_scale` image, and where the two differ that image is a **resample** of
  the `w*pixel_scale` device pixels the region really covers (on a 75 % output a region
  grab is an upsample). `probe/fractional_scaling.py` measures
  all of it, and maps a region through every candidate factor to show which one KWin uses.
- **`Capture(area=..., area_in="physical")`** takes the rectangle in **device pixels of the
  `monitor=` given** — the region you name is the region you get, converted through the
  output's display scale. The image is still rendered at the scene factor, so it is
  `w * area_scale/pixel_scale` px wide (`Capture.geometry()` reports the size you actually
  got; `resize()` takes it back to the device size). Without `monitor=` it is an error, as
  device pixels have no meaning across outputs of different scales.
- **`active_monitor()`** reports which output a plain `Capture()` would grab, by way of the
  focused window's position.
- **Scope note: KDE Plasma only.** The name is the promise — `org.kde.KWin.ScreenShot2` is
  the only compositor interface this project targets. Non-KDE compositors
  (`wlr-screencopy`, `ext-image-copy-capture-v1`) are explicitly out of scope; on them
  kwcapture fails with a clear "cannot reach the compositor" error rather than pretending.

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
- Tests: **196 checks** (was 116) — 159 functional (was 87) including a monitor section
  that captures *every* output on the desktop by name and by id, region grabs checked
  **against a native frame** so a wrong scale mapping cannot pass, and a resize test that
  launches an xterm, resizes it with `wmctrl`, and proves frames follow the window and that
  an overflowing ring heals; plus 37 ring-reader checks (was 29) covering the `ENOSPC`
  classification with no compositor. The whole suite now runs on a mixed-DPI desk (one
  output at 75 %, one at 125 %) and is scale-aware: it passes at 1x and at fractional.


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
