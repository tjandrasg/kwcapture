# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

> **Archive:** `AGENTS.old.md` holds the superseded detail — the original three-key-findings
> investigation log, the v0.1/v0.2 file map and benchmark tables, old packaging/CI notes, and the
> forensics write-up. Consult it when something here is too terse; it is history, not to-do.

> ## UPDATE THIS FILE AS YOU WORK — NOT AT THE END
> Sessions here die from running out of context, **without warning**, and everything that is
> only in your head is lost. Three sessions have now lost findings this way, and one of them
> lost a fatal bug that then took a fresh investigation to rediscover.
> **The rule: write first, investigate second.** The moment you see something odd, add a
> line to *OPEN BUGS* (symptom + how to reproduce is enough; mark it `(unverified)`). Add to
> *SESSION STATUS* after each milestone — commit, release, broken thing — not when you feel
> done. Short and ugly is fine; you can improve it later, and a `git commit` of the docs is
> cheap. If you have learned something in the last ~10 tool calls and this file does not
> mention it, stop and fix that before continuing.
>
> **Also: never let `/tmp` hold the only copy.** Reproducers belong in `probe/` (see
> `probe/stale_window.py`) or their content goes into this file. See *Forensics* below for
> what can and cannot be recovered after the fact.

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
Python API + CLI + 159 functional + 37 ring-reader checks. See `README.md` for user-facing
docs; this file is the investigation log + gotchas.

## FRESH STATUS — 2026-10-07 ~12:45 — **v0.5.0 IS OUT** (PyPI + GitHub release, verified)

* **PyPI `kwcapture 0.5.0` is live**: sdist + the CI `manylinux_2_28` wheel, taken from the
  GitHub release so the bytes match. Verified with the per-version endpoint
  (`/pypi/kwcapture/0.5.0/json`) and with a real `pip install --no-cache-dir kwcapture` in a
  throwaway venv in `/tmp` — it captures: 2560x1440x4 grab, `scale 0.75`, 2 monitors, 6
  windows, `import` from site-packages.
* **GitHub release `v0.5.0`** (id 405416187): CI assets + this machine's
  `py3-none-linux_x86_64` wheel attached via the REST API, and the release **body written**
  (three-scale table, the `area_in="physical"` fix, resilience list) — not the CI stub.
* Test counts shipped: **159 functional + 37 ring-reader = 196**, all green on a desk with
  one output at 75 % and one at 125 % (README, CHANGELOG and this file now say 159/37 — the
  previous session had guessed 155/192).
* Release sequence used, for next time: bump → `make` + full suite → commit → `git tag
  vX.Y.Z && git push origin main --tags` → `python -m build` locally → **wait for
  `release.yml`** → download the two CI artefacts → `twine check` → `twine upload -r pypi` →
  attach the local wheel + PATCH the body → verify PyPI + clean-venv install → docs.
  One note: `pip install` of the local wheel inside a 55 s `exec_shell_command` can die
  mid-download with nothing but `ModuleNotFoundError` at the end — install first, then test
  in a second call.
* **Where the docs live from here on:** `AGENTS.md` in this repo is **kwcapture only**. The
  nunif project (and the kwcapture integration into its `iw3` desktop GUI) is documented in
  `private/AGENTS.md` — it is a different codebase, and `private/` is ignored, so nothing of
  it can leak into this repo's history.

## FRESH STATUS — 2026-10-07 ~10:40 — THREE scales, and `area_in="physical"` was wrong by 0.6x

The desk is still DP-1 at 75 % and HDMI-A-1 at 125 %. Everything below was measured on it
with `probe/fractional_scaling.py` (new; sections 1-5, run it with `--xwayland`).

* **There are THREE scales.** (1) `wl_output.scale`: **1 and 2** — an integer hint, useless.
  (2) the **display scale** — `Monitor.effective_scale`, and the `scale` field of a
  *whole-output* frame: **0.75 / 1.25**. `device px = logical x this`. Whole-output frames
  are device px, 1:1, never resampled. (3) the **scene factor** — `Monitor.area_scale` /
  `Capture.area_scale`, and the `scale` field of an *area* reply: **1.25 on both outputs**,
  one number for the whole desktop. It is also what XWayland surfaces are scaled by (a
  320 px X11 window is 256 logical here) and what the workspace frame is rendered at
  (8108 px = 6486 logical x 1.25).
* **Which factor does `area=` use? The display scale — measured, not guessed.** Take a
  high-detail 400x250 *device* rectangle out of a native whole-output frame of DP-1, then
  grab that region with the logical coordinates computed three ways: /0.75, /1.25, /1.0.
  MAD against the native crop: **4.1 / 46.7 / 48.8**. So the rectangle maps through the
  display scale. Consequence nobody guessed: **a region grab on a 75 % output is an
  upsample** — 250 image px for 150 px of panel — while on an output sitting at the scene
  scale it is 1:1 native. There is no KWin option to change this (`native-resolution` on =
  scene factor, off = 1x logical; both measured).
* **BUG FIXED: `area_in="physical"` divided by the scene factor.** It returned the pixel
  *count* you asked for but only `pixel_scale/area_scale` (**0.6x**) of the region you
  named — a zoom, not a crop. `_resolve_area()` now divides by the **display** scale, so the
  rectangle really is the device region it names; the frame is still rendered at the scene
  factor so it comes back `w x area_scale/pixel_scale` px (`geometry()` says what you got,
  `resize()` takes it back to the device size). The test now checks the size **and** the
  content against a native frame, on every output — one output at the scene scale only
  exercises half the logic, so this needs both.
* **Window sizes are logical; frames are device** (measured with xterm): 320 X11 px -> **256
  logical** (`Window.geometry`) -> **192 device** (the frame) at scene 1.25 / display 0.75.
  Any assertion comparing a frame to `Window.width` must multiply by `Capture.pixel_scale`,
  or calibrate the ratio from a first frame (`_resize_then_wait(..., kx, ky)` now does).
* **Test-harness gotchas found doing this:** the shell rewrites `xterm`'s title, so never
  find a test xterm by title — match on pid (`wmctrl -lp`) or on "the X11 window that was
  not there before"; and a GUI started from `exec_shell_command` must be `setsid`'d with
  stdio redirected, or the tool kills it when the command ends (it took a false FAIL to
  learn this).

## FRESH STATUS — 2026-10-07 ~09:20 — FRACTIONAL SCALING VERIFIED LIVE (real 75% + 125%)

The user enabled 75% on DP-1 and 125% on HDMI-A-1, and the experiment found three things.

* **It works, and the compositor proves it independently.** `list_monitors(measure_scale=True)`
  now reports `effective_scale` **0.75 / 1.25** — exactly what was set — and the strongest
  check is one that does not trust us at all: output positions are logical and neighbours
  abut, so `HDMI-A-1.x == 3414` must equal DP-1's logical right edge `2560/0.75 == 3413.3`.
  `Capture.scale` (per-frame metadata) agrees. `wl_output.scale` gave **1 and 2** (it is a
  ceil hint — useless for fractional, exactly as suspected).
* **There are TWO scales, and conflating them was my bug.** The **display scale** (0.75 /
  1.25) is only reported by a *whole-output* grab. The **area/scene factor** is what KWin
  multiplies `CaptureArea` by — measured **1.25 on BOTH outputs**, and the area reply's own
  `scale` field carries *that*, not the display scale. So `--probe-scale` now does three
  grabs (two 128px areas for the factor, one whole-output for the scale) and exposes both:
  `Monitor.effective_scale` vs `Monitor.area_scale` / `Capture.area_scale`. Consequence for
  users: `area=(w,h)` returns **w*area_scale** pixels, so `area_in="physical"` must divide
  by the *area* factor — never by the display scale (0.75 would have been wrong by ~1.67x).
* **Real double-free I introduced and fixed**: `grab_sync()` grows `*buf` and frees the old
  one, so `free(buf)` followed by another `grab_sync(&buf,...)` is a double free
  (`free(): double free detected in tcache 2`). After freeing a `grab_sync` buffer always
  set `buf = NULL; cap = 0;`.
* Also: the monitor tests had baked in "an area frame is the size I asked for", true only
  at scale 1. They are now scale-aware via `Capture.area_scale`.

## FRESH STATUS — 2026-10-07 ~08:30 — monitors + fractional scaling, NOT yet released

`list_monitors()` / `Capture(monitor=name|id|index)` / measured fractional scale, on top of
the resilience work below. Still **v0.4.0 in `pyproject.toml`** — `CHANGELOG.md` says
`Unreleased`; the next release is 0.5.0.

* **Monitor ids.** KWin's screenshot interface has no per-output handle, so `Monitor.id` is
  the **`wl_output` global name** (65 here for DP-1, 79 for HDMI-A-1) — the id the
  compositor itself uses. Plus `name` (connector) and `index` (position in
  `list_monitors()` order, top-left first via `out_cmp()` in the helper). `find_monitor()`
  resolves numeric specs **id first, then index**, and refuses ambiguous names.
* **Fractional scale is measured, not read.** `wl_output.scale` is an integer hint, so a
  125% display reports 1 there; the per-surface `wp_fractional_scale_manager_v1` would need
  a surface. Instead `--probe-scale NAME` grabs the same 128x128 logical area twice —
  `native-resolution` on and off — and the ratio is the real scale (`mode_probe_scale`).
  Works whatever mechanism KDE uses; verified 1.0 here (this box has no fractional mode).
* **Gotchas found building this:**
  - **`kscreen-doctor` and KWin can disagree**: kscreen reported HDMI-A-1 `disabled` while
    KWin announced it on the registry *and* happily captured 3840x2160 from it. Never use
    kscreen's enabled flag as a proxy for "capturable"; `list_monitors()` reports what the
    compositor will actually serve.
  - **`Capture()` with no arguments follows KWin's *active screen*, which follows focus.**
    The old test `geometry matches first output` was therefore wrong the moment a second
    output appeared — it failed while my xterm probe had focus on the TV, and passed again
    minutes later with nothing changed. It now asserts geometry agrees with
    `Capture.screen_name`, which is the invariant that actually holds.
  - **`PIL.ImageGrab.grab()` returns the whole X11 root** (6400x2160 = both outputs), not
    the primary output. The colour-reference check must compare against a
    `Capture(workspace=True)` frame on a multi-monitor desk — cropping a per-output frame
    onto it made the MAD nearly identical whether the channels were right or swapped,
    i.e. it silently stopped testing anything. With the workspace comparison it is exact
    again: MAD=0.0, MAD-if-swapped=15.0.
  - A test that moves a window onto another output **changes global compositor state**
    (which screen is active). Move it back, or write the test so it does not depend on it.
  - `area=` is scene coordinates, so with `monitor=` set we offset it by the monitor's
    logical position; `area_in="physical"` divides by the *measured* scale first and
    therefore requires `monitor=` (a device point has no meaning across outputs with
    different scales).

## FRESH STATUS — 2026-10-07 ~07:10 (superseded by the section above; resilience still
 accurate)

`grab()` now survives a dead daemon, a monitor mode change and a window resize. Committed
on `main` against **v0.4.0 — not released yet** (`CHANGELOG.md` calls it `Unreleased`; the
next release is 0.5.0). Version numbers in `pyproject.toml`/`__init__.py` are still 0.4.0.

* **`auto_restart=True` (default)**: `DaemonDead`, `RingTooSmall`, or a `TimeoutError` with
  no daemon alive → restart + one retry per `grab()`. `restart_limit=5` counts *consecutive*
  restarts (`_restart_streak`, reset by a good frame); `auto_restarts` is cumulative.
  `auto_restart=False` keeps the pre-0.5 behaviour — the old `== failure handling ==` test
  now runs that way, which is why it passes with `auto_restart=False` in it.
* **Why `ENOSPC` cannot be fixed in place**: a client maps the ring at its length when the
  daemon starts; `ftruncate` it bigger and a slot beyond the old end SIGBUSes the reader.
  So the helper reports `ENOSPC` and exits, and the ring is rebuilt by a new daemon sized
  from its first frame. The client must be the one to restart (it unmaps *before* the new
  daemon truncates the path) — a daemon that re-execed itself would leave clients holding a
  stale mapping. `--slot-floor WxH` (was a hardcoded 5120×2880) sets the headroom.
* **Deliberately not recovered**: `WindowGone` (a restart cannot resurrect your window) and
  `TimeoutError` while the daemon is *alive* (that is KWin being slow/wedged; respawning
  would mask it). Both are asserted in `resilience_section()`.
* **Gotchas found building this:**
  - `tests/test_ring_reader.py` builds a `Capture` via `__new__` (no `__init__`), so any
    attribute the frame path touches must have a **class-level default** on `Capture`, or
    the synthetic tests die with `AttributeError`. That is why `auto_restart`,
    `_last_frame_geom`, `_closed` etc. are declared on the class as well as set in `__init__`.
  - `wmctrl` only sees **XWayland** windows (KWin has no X11 client list for Wayland
    windows) — that is why the resize test launches an `xterm`. Its `-lG` column order here
    is `id desktop x y w h host title`, and `-r` wants the **X11 id**, not kwcapture's
    QUuid handle (passing a QUuid gives "Cannot convert argument to number").
  - kwcapture's `Window.geometry` includes decoration/shadow margins (a 304×160 xterm
    reports 304×188) — never match a window by comparing geometry to a requested size;
    match on `app_id`, and give frame-size assertions ~60/90 px of slack.
  - A test that resizes a window must **set the size before creating the `Capture`**: the
    ring is sized from the first frame, so inheriting a window the previous sub-test left
    large turns the "grow" steps into shrinks and the overflow never happens (this is
    exactly how the first version of `window_resize_section` passed for the wrong reason).
  - `resized` must be False on the first frame (`prev is None` is not a change), and
    `auto_restarts` must be cumulative or it reads 0 by the time anyone can look at it.

## FRESH STATUS — 2026-10-07 ~05:30 (superseded by the section above; v0.4.0 is indeed
 released — the BUG-4 findings below still stand)

The previous session committed and tagged v0.4.0 but ran out of context **before publishing
it**: PyPI was still serving 0.3.0 and the GitHub release had an empty body. Both are now
finished and verified.

* **PyPI: `kwcapture 0.4.0` is live** (`pip install kwcapture` → 0.4.0, verified from a
  clean venv with `--no-cache-dir`, and it captures for real: 1440x2560x4 grab +
  `list_windows()`). Published **sdist + the CI `manylinux_2_28` wheel**, so no compiler is
  needed. The uploaded files are **byte-identical to the GitHub release assets** — I
  downloaded them back off the release and compared sha256 (`2b69d155…` wheel,
  `1575298b…` sdist) rather than publishing my local build, so "what GitHub serves" ==
  "what `pip` installs". The local sdist differs only in mtimes: same 35 files.
* **GitHub release `v0.4.0`**: 3 assets (manylinux wheel, sdist, and the local
  `linux_x86_64` wheel, same set as v0.3.0) + a 4 kB release-notes body.
* **Test counts verified, not assumed**: 87 `[PASS]` functional + 29 `[PASS]` ring-reader
  = **116**, exactly what `CHANGELOG.md` claims.
* **Gotchas learned while releasing (save yourself the time):**
  - Redirecting the test output to a file **loses every `[PASS]` line when the process dies
    hard** (block buffering, no flush on SIGSEGV) — it looks like the suite never ran.
    Use `python -u` whenever a fault is possible.
  - A wheel smoke test run with the repo as CWD silently imports `./kwcapture/`, **not the
    wheel**. Always `cd /tmp` and assert `'site-packages' in kwcapture.__file__`.
  - PyPI's aggregate `/pypi/<pkg>/json` is Fastly-cached and lags a minute or two after an
    upload; `/pypi/<pkg>/<version>/json` and `/simple/<pkg>/` show it immediately. Do not
    conclude the upload failed from the aggregate endpoint.
  - `twine upload -r pypi` (token in `~/.pypirc`) accepts the manylinux wheel fine — the CI
    `publish` job / trusted publishing is **not** required. PyPI still rejects plain
    `linux_x86_64` wheels, so that one goes to the GitHub release only.
  - No `gh` CLI on this box; the REST API with the `github.com` token from
    `~/.git-credentials` does assets (`uploads.github.com/releases/<id>/assets`) and notes
    (`PATCH /repos/…/releases/<id>`).

## FRESH STATUS — 2026-10-07 ~02:30 (superseded by the section above; the BUG-4 findings
 below still stand — the next section adds two fresh data points from the release run)

* **BUG-4 is not a kwcapture bug, and quite possibly not a software bug at all.** It is
  arbitrary memory faults on **this machine**, and kwcapture's zero-copy loop is simply the
  thing that notices first. Full evidence and measurements in `AGENTS.md` BUG-4 and
  `probe/FAULT_RATE_RESULTS.txt`. In one hour of measuring:
  - the historic symptoms reproduce with **no kwcapture, no daemon, no thread** — plain
    `np.frombuffer(mmap, …)` (`probe/race_bisect.py`, `probe/corruption_rate.py`);
  - the hardened v0.4.0 read path and the old HEAD read path fault at **the same rate**
    (40M-read rounds, 4 each, see FAULT_RATE_RESULTS.txt); caching the numpy view instead
    of building one per frame changed nothing either (3/3 still faulted);
  - nonsense now appears anywhere: `_view()` returning an array of **shape (1, 3, 2560, 4)**
    (ndim 4 is unconstructable there), a module-level **int** resolving as
    `module 'numpy' has no attribute 'HDR'`, `'int' object is not callable`,
    `'int' + 'Capture'` inside `tests/test_ring_reader.py` — a test that never creates a
    `Capture` at all — and `double free or corruption (out)` in numpy's array dealloc.
* **The machine right now:** `MemFree` ≈ 1 GB of 131 GB, `SwapTotal` = 0, `Shmem` = 79 GB;
  `llama-server` (the model serving these agent sessions) holds **103 GB RSS** including a
  72 GB shared mapping; `pgscan_direct` 331k / `allocstall_movable` 318 (direct reclaim is
  live); non-ECC RAM (`EDAC ie31200: No ECC support`); the box already **oopsed in the
  kernel's page-reclaim path** today (`BUG: kernel NULL pointer dereference` in
  `free_pages_and_swap_cache`, PID `nvidia-smi`, tainted kernel 7.0.0-2018-nvidia-bos +
  NVIDIA 610.57.04), and `/var/crash` holds a **SIGBUS** (signal 7) for
  `tests/test_kwcapture.py quick` — i.e. a page of the ring that could not be
  materialised, which is the mechanism that fits "flaky, GC/timing-dependent, nonsense
  values" far better than any race in our code.
  **Next diagnostic (do this before ever re-opening BUG-4):** run
  `KWC_ITERS=40000000 .venv/bin/python -X dev probe/fault_rate.py` on a machine that is not
  holding a 100 GB model, or with `llama-server` stopped. If it is clean there, BUG-4 closes
  as environment and nothing in this repo needs changing.
* **Two more data points during the v0.4.0 release run (~05:15), both consistent with the
  above.** (1) `tests/test_ring_reader.py` died once with `Fatal Python error: Segmentation
  fault` inside `_view()` while the concurrent-writer section was running — and the
  **unbuffered re-run passed in full** (2,064,186 frames accepted, 325,764 cleanly refused,
  **0 invalid**). The guardrail is subject to the same fault; it is not a deterministic
  failure, and CI on the tag was green. (2) `KWC_MODE=both probe/race_bisect.py` — which
  imports only `ctypes`, `mmap` and `numpy`, **never kwcapture** — died with `Fatal Python
  error: Bus error` at `probe/race_bisect.py:100`, i.e. a page of a private file mapping
  that could not be materialised (SIGBUS, the mechanism named above), while `KWC_MODE=numpy`
  completed **4,000,000 clean iterations** in the same minute. `free` right now: 95 GB used
  of 125 GB, `Swap: 0`, `llama-server` 104 GB RSS. New symptom string for the family:
  *Bus error*.
* **What v0.4.0 still fixes** (real bugs found while chasing it, all covered by tests — see
  `tests/test_ring_reader.py`): torn per-frame metadata (two fields from two frames could
  make one shape), unchecked offsets/counts handed to numpy, a *writable* ring mapping in
  the client, reading a slot the daemon had already recycled, and a frame read spanning a
  `restart()`/`close()`. None of these is "the crash"; all of them are wrong behaviour.

## FRESH STATUS — 2026-10-07 ~00:40 (superseded by the section above; kept for the
 repro observations — its "mitigation cuts exposure" claim was wrong, see the fault-rate
 table in `probe/FAULT_RATE_RESULTS.txt`)

* **BUG-4 is not ours.** The whole symptom family reproduces **without kwcapture, without
  the daemon and without a second writer**: a tight loop of
  `np.frombuffer(mmap, count=…, offset=…)` (+ reshape / width slice / `setflags`) corrupts
  memory and eventually kills the interpreter — `probe/race_bisect.py` (historic
  `TypeError: 'int' object is not callable` at iteration 326,533; **the same script with
  ctypes removed outright SIGSEGVs**), `probe/corruption_rate.py` (`IndexError: only
  integers, slices … are valid indices`, `arr.ctypes` evaluating to a **`str`**,
  `AttributeError: module 'numpy' has no attribute 'HDR'` for a **module-level int**,
  `double free or corruption (out)` in numpy's array dealloc).
  Rate ~1 per 10^5–10^7 view constructions, non-deterministic (one 240M-iteration matrix
  run was completely clean) — which is exactly why three sessions could not pin it and why
  "it passed once" was never evidence. At a real ~40 fps capture rate the expected wait is
  days.
* Repro environment: `/usr/bin/python3.14` 3.14.4 (GCC 15.2, GIL build); venv numpy 2.5.3
  **and** system numpy 2.3.5 both fault. ctypes-only loops and pure-Python checksum stress
  stay clean; `np.frombuffer` alone and `+reshape` were clean at 4M — it needs the view-op
  chain *and*, as it turns out, this machine (see the section above).

## FRESH STATUS — 2026-10-06 ~23:05 (superseded by the section above)

* **v0.3.0 is released** (code, tag, GitHub release with 3 assets, PyPI sdist **+ the first
  prebuilt manylinux wheel** → `pip install kwcapture` needs no compiler). CI is green.
* **Nothing is pending in the release pipeline.** New work = the *Ideas* section or the bugs.
* **OPEN BUGS below is the most valuable section in this file** — BUG-4 in particular is a
  fatal flaky race in the client's zero-copy path that three sessions lost. It is unfixed.
* BUG-1 (minimised windows return STALE frames, silently) is unfixed. BUG-3 fixed.
  BUG-4b + the header snapshot in `_view()` are fixed; the race itself is not.
* The 21:50 release-run narrative (CI root causes, polling technique, artefact bookkeeping) was
  moved to `AGENTS.old.md` — it is done work, kept only for the reasoning.

## REPOSITORY HYGIENE — `private/` is the only place for non-source files

`private/` exists for this: **anything that is not source — chat transcripts, captures,
dumps, logs, credentials, scratch notes — goes in `private/`**, which is ignored by both
`private/.gitignore` (`*` + `!.gitignore`) and the root `.gitignore` (`private/*` +
`!private/.gitignore`). Only the ignore file itself is tracked, so the folder appears in
every fresh clone and the rule travels with the repo.

**Why this exists:** on 2026-10-06 a `git add -A` swept the user's 1.1 MB private chat
transcript (`chat_his.jsonl`, dropped in the repo root) into a commit and pushed it to the
**public** repo. It was removed from the branch and the history was rewritten
(`filter-branch` + reflog expiry + `gc --prune=now` + force-push), tags / GitHub release
assets / PyPI sdists never contained it — **but GitHub keeps serving the old dangling commit
objects**, both over HTTPS (`raw.githubusercontent.com/<repo>/<old-sha>/chat_his.jsonl`
→ 200 with the full file) and over the **git protocol**
(`git fetch --depth=1 origin <old-sha>` then `git cat-file`). Verified 2026-10-06.
**Do not write the old short/full SHAs into this file or into any commit message**: GitHub
resolves abbreviated SHAs, so publishing one hands every visitor a working download link.
They are deliberately omitted here. **Force-pushing is NOT deletion on GitHub** — at the time of writing
`raw.githubusercontent.com/<repo>/<old-sha>/chat_his.jsonl` still returns the full file,
and it will until GitHub Support purges the dangling objects (the user has been told to open
that request). Assume a force-push does not un-publish anything.

**Rules that follow from it:**
* Non-source files go in `private/`, never in the repo root (the old `*.bgra` scratch dumps
  in `/tmp` are the same hazard — they are gitignored, but `private/` is the habit).
* `git add -A` is acceptable **only** because `private/` is ignored now — and only if you
  check the `git status --porcelain` output the command implies. Before a push that will be
  public, run `git add -A --dry-run` and read it (it lists exactly what would be staged).
* Verify an ignore rule rather than trusting it: `git check-ignore -v <path>` shows which
  rule matched. A `.gitignore` entry that silently matches nothing looks identical to one
  that works.
* Never `git add -f`/`git add private/...` — `-f` overrides the ignore rules that protect
  this folder.

## OPEN BUGS — found, not yet fixed

> **RULE FOR FRESH SESSIONS: anything that looks wrong goes in this section the moment you
> see it, before you chase it.** Do not investigate first and write it up later — two
> sessions have now lost findings that way. A half-paragraph with the symptom is worth more
> than a perfect post-mortem that never gets typed. Mark unverified guesses `(unverified)`.

### BUG-1 (surfaced in v0.4.0; KWin's behaviour itself is unfixable): a **minimised window captures a STALE frame**

> **STATUS — fixed as far as it can be fixed (v0.4.0).** KWin simply does not render a
> minimised window, so the stale pixels are not something we can change; what we can do is
> **stop letting it be silent**, and that is implemented:
> * **`Capture(stale_check=True)`** → `grab()` consults `getWindowInfo` (throttled to ~10/s)
>   and sets **`Capture.stale_frame`**, emitting a one-shot `RuntimeWarning` on the transition
>   into staleness. Default **off** — the check is a D-Bus round trip and must not tax the
>   185 fps window path. `stale_frame is False` therefore means *unknown*, not *fresh*.
> * **`Capture.window_minimized`** — the same answer on demand (raises `CaptureError` for
>   non-window captures); a window that has vanished entirely counts as minimised.
> * Regression tests: 6 checks in the window section (flag set/cleared, warning issued,
>   frames really byte-identical, default off). `probe/stale_window.py` now also asserts the
>   **surfacing** works and exits 0 when it does — the underlying KWin staleness is expected
>   to remain forever, so that is no longer a failure condition.
>
> Everything below is the original analysis, kept because the reasoning is the useful part.


`AGENTS.md` has long said "a minimised window still captures — KWin keeps its buffer".
That is true only in the sense that you get **pixels back**: they are an **old snapshot**.
KWin stops rendering a minimised window's scene item, so the buffer holds whatever it last
held and **every grab returns identical bytes forever** — no exception, no `status`, no
flag, nothing in `stats()` to tell you the frame is dead. A caller polling a background
window gets a frozen image and believes it is live. This is the worst kind of bug: it is
silent, and "it returned a frame" looks like success.

* Reproduced 2026-10-06 with a self-repainting window (`konsole --hold -e sh -c
  'while :; do date; sleep 0.3; done'`) and `Capture(window=…)`, grabbing 1.8 s apart:
  `1 VISIBLE live repaint differs : True` / `2 MINIMISED two grabs identical : True` /
  `3 RESTORED live repaint differs : True`. Script was `/tmp/probe_stale.py`; rerun it with
  `PYTHONPATH=$PWD .venv/bin/python /tmp/probe_stale.py` (needs `busctl` to minimise).
* Note the stale buffer is **not** the last frame seen before minimising either
  (`changed vs pre-minimise: True`) — it is whatever KWin rendered last, possibly an
  animation frame. So it is not even a reliable thumbnail.
* **Fix direction** (nothing implemented yet): `getWindowInfo` reports `minimized`, so we
  *can* know. Cheapest honest options:
  1. a property `Capture.window_minimized` that does one `getWindowInfo` call on demand
     (do **not** do it per frame — that would add a D-Bus round trip to every grab);
  2. surface it as a frame status, e.g. a new `KWC_ERR_STALE`/`KWC_FLAG_STALE`, only when
     the daemon is told to check (`--check-minimised`), so the default fast path is
     untouched — this needs `KWC_VERSION` bumped to 3 (see the ring-geometry gotcha);
  3. at minimum, document it in the README's per-window section, which currently implies
     minimised capture gives you the window's current contents.
* **Also unverified, same family — test these next** (same silent-staleness shape):
  window on **another desktop** (switch with `/KWin setCurrentDesktop`), window on another
  **activity**, and a window that is fully **occluded** (the "occlusion does not crop"
  claim below was verified only for *geometry*, never for *liveness*).

### BUG-2 (latent fatal crash in the grab hot path, only partly explained): `sched_yield()`

`kwcapture/__init__.py` (~line 1103) has a lazy ctypes init, and it is called from
**`Capture.grab()`'s busy-wait loop** (the `sched_yield()` call inside `grab`, during the
first 200 spins — i.e. on essentially every fresh grab). So anything that breaks here is
fatal for *all* capture, not for one code path.

```python
_sched_yield = None

def sched_yield() -> None:
    global _sched_yield
    if _sched_yield is None:
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            _sched_yield = libc.sched_yield
        except OSError:            # <-- TOO NARROW
            _sched_yield = lambda: time.sleep(0)
    _sched_yield()
```

* **Verified defect**: if `CDLL("libc.so.6")` succeeds but the `dlsym` for `sched_yield`
fails, ctypes raises **`AttributeError`, not `OSError`**, which escapes the `except` and
propagates out of `grab()`. Proven by monkeypatching: `CRASH: AttributeError: sched_yield`.
Relevant on non-glibc/musl or odd SONAMEs. Unchanged since the initial release
(`git log -S sched_yield` shows exactly one commit).
* **The `'int' object is not callable' symptom the author remembers was NOT reproduced and
  is NOT in the tree or its history.** What is known for certain, and it is what makes this
  hard to pin down:
  - **`libc.sched_yield()` RETURNS AN INT (0). Verified.** So this is the one place in the
    package where the callable and an int sit side by side: a single stray paren —
    `_sched_yield = libc.sched_yield()` — caches **0**, and from then on every `grab()` dies
    with exactly `TypeError: 'int' object is not callable`, deep inside the wait loop, far
    from the line that caused it. That matches the remembered symptom, the fatality, and
    the difficulty; it is a **hypothesis, not a finding**.
  - An exhaustive AST scan (all 47 ctypes int fields of `_Hdr`/`_Slot` + every int/bool
    `Window` field, looking for `field(...)` call sites) found **no** such call in the
    committed tree. `h.ready()`, `h.frame_seq()`, `w.width()` etc. would all give the same
    error, so if the earlier session hit one of those it happened **in a scratch script in
    `/tmp`, which is gone** — the most likely reason it cannot be found again.
* **How to find it again** (do this, in order):
  1. `grep -rn "sched_yield" kwcapture/` and check the cache is assigned the function, never
     the call result (`= libc.sched_yield`, NOT `= libc.sched_yield()`).
  2. Reproduce any crash with `python -X dev -X faulthandler` and a **full traceback**; the
     `int` in the message is a ctypes field or a call result, so the *frame above* is where
     the int came from, not the frame that raised.
  3. Run the AST scan (kept below in this section's git history / re-create: parse each file,
     collect int-ish attribute names, look for `ast.Call` whose `func` is an `Attribute` with
     one of those names). It takes seconds and finds the whole family statically.
* **Fix — APPLIED and now covered by tests** (see `regression: BUG-2 sched_yield` in the suite):
  catch `(OSError, AttributeError)`, keep the fallback a real named function (`_sleep0`), and
  guard the cache with `if not callable(_sched_yield)` instead of `is None`. **APPLIED** (commit after this one): all three branches verified —
  normal `_FuncPtr`, `AttributeError` → `_sleep0`, and forcibly setting `_sched_yield = 0`
  now *re-initialises* instead of raising, with a real `grab()` still working. The
  `'int' object is not callable` origin story above is still unconfirmed; the guard only
  makes that whole family uninvokable. **If the crash ever reappears, read this section.**

### BUG-4 (ROOT-CAUSED 2026-10-07, NOT OURS): corruption while reading shared memory zero-copy

> **STATUS — 2026-10-07 ~02:30: not a kwcapture bug, and most likely not a software bug at
> all — see the "memory faults on this box" block below this quote. What follows is the
> bisect record; the conclusion in it ("numpy/CPython bug") was written before the machine
> itself was checked and is too strong.** It is **not a race in kwcapture** and never was. `probe/race_bisect.py` and `probe/corruption_rate.py` in
> this repo reproduce the exact historic symptoms with **no kwcapture, no daemon, no
> second writer, no thread** — a tight loop that builds numpy views over an `mmap`:
>
> ```
> probe/race_bisect.py  MODE=both   TypeError: 'int' object is not callable  @ iter 326,533
>                     MODE=numpy    Segmentation fault   <-- no ctypes involved at all
>                     MODE=ctypes   clean (3.9M it/s)
> probe/corruption_rate.py  MODE=A  IndexError: only integers, slices … @ iter 2,492,225
>                           MODE=C  double free or corruption (out) → abort in numpy's
>                                   array dealloc (_Py_Dealloc → _multiarray_umath → free)
> ```
> Other things observed on the same box while hunting it: `arr.ctypes` evaluated to a
> **`str`**; a module-level **int** `HDR` raised `AttributeError: module 'numpy' has no
> attribute 'HDR'` (i.e. the interpreter resolved a global against the wrong object); a
> `ValueError: cannot reshape array of size 1` when the geometry was a fixed 640×480×2560.
> Those are mis-executed bytecode / a corrupted heap inside **CPython 3.14.4
> (`/usr/bin/python3.14`, GCC 15.2) + numpy (venv 2.5.3 *and* system 2.3.5 both crashed)**,
> not a logic error in this package.
>
> **Rate: ~1 event per 10^5–10^7 view constructions**, and it is not deterministic: a
> 240M-iteration matrix run came back completely clean, and the same script crashes on one
> run and not the next. That is the whole reason three sessions could not pin it — and why
> "I ran it once and it was fine" was never evidence. At a real ~40 fps capture rate the
> expected time to one event is **days**, which is why nobody hits this in normal use.
>
> **HEAD-TO-HEAD, 2026-10-07 ~02:00 — rewriting the read path does not change anything.**
> `probe/fault_rate.py` (40M `latest(rgb=True)` reads per round, ~480k reads/s, `-X dev`),
> old = `git worktree` of HEAD, new = the hardened path. Full table in
> `probe/FAULT_RATE_RESULTS.txt`:
>
> ```
> old: faulted in 4/4 rounds   (~13M, ~1M, 0 reads, early)   '_Hdr' has no attribute '_hdr',
>                                                                      shape=(1, 3, 2560, 4)
> new: faulted in 4/4 rounds   (<1M, <1M, ~24M, ~?)            'Capture' - int,
>                                                        'int' % 'mmap.mmap', SIGSEGV
> ```
>
> Caching one numpy array per slot instead of building a view per frame (removing ~6 orders
> of magnitude of buffer-export churn) **also faulted 3/3** — so it is not the export churn
> either. That variant was reverted; the read path stays simple.
>
> **MEMORY FAULTS ON THIS BOX — the likeliest explanation.** While measuring, the fault
> rate rose until even `tests/test_ring_reader.py` — synthetic ring, no daemon, no
> threads — faulted, with `'int' + 'Capture'` in code that never creates a `Capture`. The
> machine's state at the time: `MemFree` ≈ 1 GB of 131 GB, **`SwapTotal` = 0**,
> `Shmem` = 79 GB, `pgscan_direct` 331k / `allocstall_movable` 318 (direct reclaim live),
> `pgmajfault` 57k — because **`llama-server` (the model these agent sessions run on)
> holds 103 GB RSS, including a 72 GB shared mapping**. Non-ECC RAM
> (`EDAC ie31200: No ECC support`). The kernel has already oopsed here once today:
> `BUG: kernel NULL pointer dereference … Oops: [#1] SMP NOPTI` in
> `free_pages_and_swap_cache+0x50` (page reclaim), PID `nvidia-smi`, tainted
> (`[P]ROPRIETARY [O]OT [E]UNSIGNED`) kernel `7.0.0-2018-nvidia-bos` + NVIDIA 610.57.04,
> ASRock Z790 Steel Legend. And `/var/crash/_usr_bin_python3.14.1000.crash` records
> **`Signal: 7` / `SIGBUS`** for `.venv/bin/python tests/test_kwcapture.py quick` — a page
> of the ring that could not be materialised, which is exactly the failure mode that looks
> like "flaky, GC/timing-dependent, impossible values".
>
> **Decisive next experiment (run it before touching this code again):**
> `KWC_ITERS=40000000 .venv/bin/python -X dev probe/fault_rate.py` on another machine, or
> with `llama-server` stopped. Clean there ⇒ BUG-4 is environmental, closes, and nothing
> here needs changing. Faults there too on the same numpy/CPython ⇒ then and only then it
> is worth reporting upstream, with `probe/corruption_rate.py`'s ~20-line core and the
> `double free or corruption (out)` dealloc trace.
>
> **What v0.4.0 changed** — real correctness fixes in the read path, *not* a mitigation of
> the fault (measured unchanged, above). See the `_view()`/`_descriptor()` comments:
> one contiguous read of the slot descriptor instead of a ctypes shadow object plus
> repeated field reads (two fields could previously come from two different frames); ring
> geometry validated once per generation; every value bounds-checked before it becomes an
> offset/count/shape (nonsense used to be able to hand numpy the header bytes as pixels);
> the client's data mapping is now **read-only**, so views are read-only for free and no
> client can write into the ring; `grab()` takes the newest published frame instead of the
> exact one it asked for (a slot the daemon had already recycled is no longer read);
> a torn `copy=True` read is retaken once; and a generation counter refuses to return a
> frame that spans a `restart()`/`close()`.
> **Never write "BUG-4 fixed" — write "not ours, guardrails added, fault rate unchanged".**
> Repros and measurement: `probe/race_bisect.py`, `probe/corruption_rate.py`,
> `probe/fault_rate.py`, `probe/FAULT_RATE_RESULTS.txt`. Deterministic guardrail tests:
> `tests/test_ring_reader.py` (no compositor needed, so they run in CI).

The rest of this entry is the original hunt, kept because the reasoning is why we believed
it was a race for three sessions. **This is the bug earlier sessions kept hitting and never
writing down. It is NOT a typo and it is NOT statically findable — `'int' object is not
callable' is a memory-corruption symptom, not a name error.** Reconstructed 2026-10-06 from
the previous session's saved transcript (`private/chat_his.jsonl`, lines ~349–381); that
session died mid-bisect without a root cause.

* **Symptoms, all three from the same stress run family:**
  1. `TypeError: "'int' object is not callable"` — hit inside `Capture.latest(rgb=True)`
     after **~22,400 iterations/second** sustained, with a **healthy ring header**
     (`magic 0x4b574350 version 2 error 0 quit 0 ready 1 frame_seq 159 published 159
     2560x1440 stride 10240 format 6 target 0`) — i.e. the daemon was fine, the *client*
     blew up.
  2. `CaptureError: daemon error: Success` raised from `_check_error()` — impossible unless
     the header was read **twice** (non-zero in the `if`, then 0 when formatting the
     message): a TOCTOU on shared memory. See BUG-4b.
  3. **`Segmentation fault`** — outright, in more than one configuration.
* **Flaky and GC/timing-dependent, so it does NOT reproduce in a short rerun** (one clean
  4 s run passed; the bisect harness showed `MODE=numpy_only` and `MODE=nosetflags` OK in
  one pass while `ctypes_numpy` crashed in another). The previous session's own conclusion:
  *"a genuine memory-safety bug that is timing/GC-dependent"*.
* **Where it lives: the client's zero-copy path**, not the daemon — `_view()` builds numpy
  arrays over the same `mmap` that `_Hdr.from_buffer(self._mm)` maps and that the daemon is
  writing concurrently, and `close()`/`restart()` can replace `self._mm` while a returned
  zero-copy view or the `_hdr` object still refers to the old buffer.
* **Why every static search for it fails** (do not repeat these):
  - an AST/regex scan for int-shaped fields called with `()` finds nothing — no such call
    exists; the `int` is *garbage that a name resolved to*, or a ctypes object whose
    backing buffer was released under it;
  - `git log -S` finds nothing (never committed as a typo);
  - apport never records a plain `TypeError`, and the SIGSEGV entries in `/var/crash` are
    the *stale-ring* SIGBUS class, not this one.
* **Reproduce** (budget time — it is flaky by nature): loop `cap.latest(rgb=True)` and
  `cap.grab()` for tens of seconds at full speed against a live daemon, under
  `PYTHONFAULTHANDLER=1 .venv/bin/python -X dev`, and **repeat the run many times** — a
  single clean pass proves nothing. Also try with `gc` pressure (allocate in the loop) and
  with concurrent `restart()`/`close()`.
* **Fix directions, 2026-10-07 status:**
  1. **APPLIED (v0.3.x)**: `_view()` snapshotted `slots`/`hdr_size`/`slot_bytes` once and
     `_check_error()` reads `h.error` once (killed BUG-4b's `daemon error: Success`).
  2. **TRIED AND REJECTED — do not repeat this exact attempt**: `arr._kwc_shm = (mm, hdr)`
     silently does nothing because these are numpy **views**, which reject new attributes;
     wrapped in `except AttributeError` it looked like a fix while `hasattr(arr,'_kwc_shm')`
     was False. numpy already keeps the buffer via `arr.base`. **General lesson: a fix
     wrapped in a broad `except` that never asserts anything is a placebo — verify the
     effect, not the intent.** (Re-confirmed in 0.4.0: an outstanding view really does keep
     the mapping alive — `tests/test_ring_reader.py::lifetime_section` asserts it, and
     `mmap.close()` refuses with `BufferError` while a view exists.)
  3. **APPLIED (v0.4.0)**: the frame path no longer re-reads shared memory. `_descriptor()`
     takes ONE contiguous `_SLOT_SIZE` read per frame, `_start_once()` caches the
     generation's `slots`/`hdr_size`/`slot_bytes`/`len(mm)` via `_check_ring_geometry()`,
     and `_view()` validates geometry + bounds before touching numpy. `close()`/`restart()`
     bump `_gen`, and a read that spans one raises `DaemonDead` instead of mixing rings; an
     outstanding view keeps its mapping and stays readable (documented in `grab()`).
  4. **APPLIED (v0.4.0)**: `tests/test_ring_reader.py` runs the reader against a synthetic
     ring — invalid descriptors, a concurrent writer, ~4.5M reads in 6 s — under `-X dev`
     **in CI** (`.github/workflows/ci.yml`), so this path is no longer untested off a
     Plasma desktop.
  5. **STILL OPEN / NOT OURS**: the numpy+CPython fault itself. If you are asked to "finish
     BUG-4", the useful next steps are upstream, not here: reduce `probe/corruption_rate.py`
     further (it is already a ~20-line core), report it against numpy with the
     `double free or corruption (out)` dealloc trace, and re-test on a different kernel /
     machine to separate numpy from this box. A `PYTHONMALLOC=debug` run is the next
     diagnostic — it was not tried yet.

#### BUG-4b: `CaptureError: daemon error: Success` — double read of `hdr.error`

`_check_error()` reads the shared `error` field more than once (once to decide, once to
format), so a concurrent write can produce the self-contradictory message *"daemon error:
Success"*. Read it into a local **once** and raise from that. Same class of torn read as
BUG-4; fix together.

### BUG-3 (fixed in v0.3.x + v0.4.0): two leaks on start/restart

> **Part two, found by the regression test written for part one.** My first fix closed only
> the leaked `<shm>.log` handle. The new fd-counting test then measured **16 → 20 fds over 4
> `restart()` calls — exactly one fd per restart** — because `_start_once()` re-opens
> `_fd`/`_mm`/`_hdr` and nothing released the previous ones. Fixed with a `_unmap()` helper
> called from `_start_once()` (before re-opening) and from `close()`; the test now asserts
> `<= 1` fd of drift over 4 restarts and passes.
> Note `mmap.close()` raises `BufferError` while numpy still exports a buffer, in which case
> we drop our reference and the mapping stays alive for those views — that is the safe
> direction, and it is BUG-4's neighbourhood, so touch it carefully.
>
> **Lesson: my "fixed" note on BUG-3 was premature — the test is what disproved it.** If a
> fix has no test, mark it *unverified*.


`_start_once()` reset `self._log_file = None` and then opened a fresh `<shm>.log`, dropping
the handle from the previous attempt without closing it. `_start_once()` runs on **every**
authorisation retry (the backoff loop can fire 5 times) and on every `restart()`, so a
long-lived process leaked fds. Found by running the *previous session's* leftover
`/tmp/repro.py` (daemon `SIGKILL` + `restart()`) under `python -X dev`, which reported
`ResourceWarning: unclosed file <_io.TextIOWrapper ... shm.log>` at the reset line. Fixed by
closing the old handle first; the ResourceWarning is gone.
**`-X dev` is worth running on the suite** — it surfaces resource bugs that are otherwise
silent. (It also surfaced BUG-2's neighbourhood.)

## Goal
Make a **fast** full-screen capture program on Wayland. Original experiments
(`probe/bench_original.py`, `bench_result.md`): `PIL.ImageGrab` shells out to `spectacle`
(~2 fps); `mss` is 1100 fps but captures **XWayland** (black for native Wayland windows)
and dies when `$DISPLAY` is unset. Both unusable.

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

## KEY FACTS — the essentials (full investigation log in AGENTS.old.md)

* **Capture API**: D-Bus service `org.kde.KWin.ScreenShot2`, path `/org/kde/KWin/ScreenShot2`,
  methods `CaptureScreen(s)`, `CaptureActiveScreen`, `CaptureArea(x,y,w,h)`,
  `CaptureWorkspace`, `CaptureWindow(handle)`, `CaptureActiveWindow`, `CaptureInteractive(u)`,
  each `(…, options a{sv}, pipe h) -> a{sv}`. Reply keys: `type="raw"`, `format`
  (**6 = ARGB32_Premultiplied = BGRA bytes**), `width`, `height`, `stride` (bytes/row),
  `scale`, `screen`, or **`windowId` for window captures**.
* **KWin replies BEFORE writing pixels** (`ScreenShotSinkPipe2::flush()` returns, then a
  QThreadPool writer does the copy) → EOF on our pipe is the frame boundary, and this is what
  makes the no-pixels `--active-window-id` query (~8 ms) possible.
* **Authorisation**: pid → canonical `/proc/<pid>/exe` → a `.desktop` file whose `Exec=`
  first token canonicalises to that exe and whose `X-KDE-DBUS-Restricted-Interfaces` contains
  `org.kde.KWin.ScreenShot2`. **A Python script can never be authorised** → native helper +
  desktop entry (`_desktop.py`, `kbuildsycoca6`, async propagation → retry with backoff).
* **Window enumeration** (KWin has none on ScreenShot2): `/WindowsRunner` `org.kde.krunner1`
  `Match("")` — empty query matches every window, locale-independent (do NOT use the
  translated `"window"` keyword); ids are `"<action>_<uuid>"`, dedupe (one entry per desktop);
  `Run("0_<uuid>","")` activate / `1` close / `2` minimise. Details from
  `/KWin getWindowInfo(uuid)` → a{sv}: caption, resourceClass/Name, desktopFile, role, icon,
  x/y/width/height as **doubles**, minimized/fullscreen/keepAbove/keepBelow/noBorder/
  skipTaskbar/skipPager/skipSwitcher, maximizeHorizontal/Vertical (**ints**), type, layer,
  desktops/activities (`as`), uuid — **no pid, no focus flag**.
* `activeOutputName()` → the focused output (`busctl call` with **no** input args).
  `supportInformation` lists **no windows** in Plasma 6.6.
* **A closed window is not a D-Bus error**: KWin returns a 0x0 / stride-0 image. Treat
  `width==0 || stride*height==0` as failure or the ring wedges; all failures publish a frame
  with a `KWC_ERR_*` status so `frame_seq` keeps moving.
* shm protocol **v2** (`KWC_HDR_STRUCT_SIZE` 1912, `KWC_VERSION` 2): per-frame `status`,
  `target`, `window[64]`. Asserted in C (`_Static_assert`) **and** Python (`ctypes.sizeof`);
  bump both, and bump `KWC_VERSION` when meaning changes. Pixel area starts at `hdr_size` 4096.
* Release/build essentials: the wheel contains a compiled helper so it must not be
  `py3-none-any` — override `bdist_wheel.get_tag()`; **the helper is a standalone executable,
  not an extension module, so the wheel is `py3-none-<platform>`** and one build covers every
  CPython ≥ 3.9; `auditwheel repair -w {dest_dir} {wheel}` (not `{dest}`),
  `--exclude libsystemd.so.0 --exclude libwayland-client.so.0`; PyPI rejects `linux_x86_64`
  (manylinux only); never import `kwcapture` from `setup.py` (numpy is not a build dep).

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
* **The exec_shell tool's default timeout is 10 s and the hard maximum is 60 s** — passing
  `timeout: 120`/`180` still gets killed at 60 s (`exit due to timed out`), so `sleep 120`
  never works: sleep ≤50 s per call and poll. The full `tests/test_kwcapture.py` run is
  actually **~35 s** (the earlier "~3 min" estimate was stale); `... quick` and `... windows`
  (~30 s) still exist, or background it with `nohup … > /tmp/x.log 2>&1 &` and read the log.
* `PIL.ImageGrab` can leave a `spectacle` process holding your stdout pipe open (looks like
  a hang); `bench.py` reaps the ones it started.

## Release checklist (do this in order; v0.2.0 was published this way)

1. Bump the version in **both** `pyproject.toml` and `kwcapture/__init__.py`, update
   `CHANGELOG.md` + `README.md` (including the release-wheel URL at the top of README).
2. `make && .venv/bin/python -X dev tests/test_kwcapture.py` — everything must pass on the
   real desktop (CI only checks that it *builds and imports*, plus
   `tests/test_ring_reader.py`, which needs no compositor). Check the count of `[PASS]`
   lines against the number claimed in CHANGELOG.md, and run
   `.venv/bin/python -X dev tests/test_ring_reader.py` too — it is the BUG-4 guardrail.
3. `git commit` the lot, then `git tag vX.Y.Z && git push origin main --follow-tags`.
4. Build the artefacts here: `.venv/bin/python -m build` → `dist/*.tar.gz` +
   `dist/*-py3-none-linux_x86_64.whl`. Sanity check the wheel in a throwaway venv **from
   outside the checkout** (`/tmp`), including a real `Capture()` + `list_windows()`.
5. PyPI — publish **the sdist + the CI manylinux wheel**, not the sdist alone: the manylinux
   wheel is what makes `pip install kwcapture` need no compiler. Take both **from the GitHub
   release of that tag** (so PyPI serves bytes identical to GitHub) rather than the local
   build, `twine check` them, then
   `.venv/bin/python -m twine upload -r pypi /tmp/publish/*` (token: `~/.pypirc`).
   Do **not** upload the local `linux_x86_64` wheel — PyPI rejects it.
   Before uploading, confirm the sdist carries no local-only files:
   `find <unpacked> -iname '*private*' -o -iname '*.jsonl'` and grep the tree for
   `ghp_`/`pypi-AgEIcHlwaS`. Verify with `curl -s
   https://pypi.org/pypi/kwcapture/<X.Y.Z>/json` (**not** the aggregate endpoint — it is
   Fastly-cached and lags ~1-2 min after a successful upload) and finally with a real
   `pip install --no-cache-dir kwcapture` in a throwaway venv **outside the checkout**.
6. The tag push runs `release.yml`, which builds the sdist + manylinux wheels and creates
   the GitHub release (via `gh` on the runner, `github.token`). Then upload the local
   `linux_x86_64` wheel as an extra release asset with the REST API:
   `curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/octet-stream" \
    --data-binary @dist/<wheel> https://uploads.github.com/repos/tjandrasg/kwcapture/releases/<id>/assets?name=<wheel>`
   (token from `~/.git-credentials`, release id from `/repos/.../releases/tags/vX.Y.Z`).
7. Add the release notes to the GitHub release body (`PATCH …/releases/<id>`) — CI only
   writes the `**Full Changelog**` stub, so a release with an empty body is a missed step,
   not a finished one. Then update this AGENTS.md with a `FRESH STATUS` section recording
   what shipped and what was verified, and commit + push that too.

## Ideas not done yet
* ~~Mark which listed window is *active*~~ **done in v0.3.0** — see finding #3
  (`Window.active`, `active_window_id()`, `--active-window-id`).
* `getWindowInfo` gives no pid — a `Window.pid` would need `/proc` matching by app id.
* **TODO (kept deliberately, low priority):** expose non-normal windows — panels, desktop,
  overlays. krunner filters them out, so `list_windows()` cannot see them; a KWin script or
  the qml console could hand out those handles, and `Capture(window=…)` already accepts
  them. Not important; revisit if anyone ever needs it.
* ~~Window resize handling~~ **done** — frames follow the resized window automatically (the
  per-frame geometry in the slot descriptor was already correct; what was missing was the
  recovery when it outgrows the ring). See `Capture.resized`, `last_geometry`.
* ~~Auto-restart the daemon inside `grab()` on `DaemonDead`~~ **done** — `auto_restart=True`
  is now the default; `restart_limit` bounds the streak. See the resilience notes below.
* ~~Re-size the ring in place on resolution change instead of erroring out~~ **done,
  deliberately NOT in place** — the client has the ring mapped at the old length, so growing
  the file under it would SIGBUS whoever read past the old end. Instead `ENOSPC` →
  `RingTooSmall` → the daemon is restarted and the ring is *rebuilt* at the new size. Same
  outcome for the caller, no window where a mapping and a file disagree.
* ~~Multi-monitor~~ **done** — `list_monitors()` + `Capture(monitor=name|id|index)`,
  monitor-relative `area=`, `active_monitor()`, CLI `monitors` / `grab --monitor`. A
  combined helper for *all* outputs at once is still not there: `workspace=True` gives the
  whole virtual desktop in one frame.
* ~~Fractional scaling~~ **done** — `Monitor.effective_scale` / `measure_output_scale()`
  measure it from KWin (integer `wl_output.scale` cannot express 1.25/1.5), with
  `to_physical`/`to_logical`, `Capture.pixel_scale` and `area_in="physical"`. Frames are
  device-resolution as before. **Not exercised on a real fractional display** — this box
  runs 1x; verified via the ratio mechanism, 1.0 exactly, and the math is unit-tested.
* Fractional scaling: `native-resolution` is set; behaviour with scale≠1 untested.
* ~~If a non-KDE compositor is ever needed~~ **out of scope, deliberately.** The name is
  the promise: this project targets KDE Plasma, and `org.kde.KWin.ScreenShot2` is the only
  capture interface it will speak. `ext-image-copy-capture-v1`/`wlr-screencopy` are not on
  the roadmap — on a non-KDE compositor kwcapture should fail loudly, not grow a second
  backend.
