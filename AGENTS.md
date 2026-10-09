# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

> **Archive:** `AGENTS.old.md` holds the superseded detail — the original three-key-findings
> investigation log, the v0.1/v0.2 file map and benchmark tables, old packaging/CI notes, the
> forensics write-up, the 2026-10-07 session logs of the v0.4.0/v0.5.0 work, the original
> nested-`--virtual` discovery, and (moved 2026-10-09) the 2026-10-08 headless-CI and
> non-normal-window day-logs plus the long BUG-1 / BUG-2 / BUG-4 forensics. See *ARCHIVED* below for
> the map. Consult it when something here is too terse or you want the reasoning behind a rule; it is
> history, **not to-do**.
>
> **Size discipline:** this file is the working set, so finished work gets distilled into a few
> bullets here and its long form goes to the archive. If you catch yourself writing a third
> "FRESH STATUS" day-log into a file this size, distil the older ones instead.

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
> `probe/stale_window.py`) or their content goes into this file. See *Forensics* in `AGENTS.old.md`
> (*FORENSICS — recovering a lost finding after a session died*) for what can and cannot be recovered
> after the fact.

Repo: **https://github.com/tjandrasg/kwcapture** (branch `main`; releases `v0.1.0` … **`v0.6.0`**,
every one from `v0.3.0` on carrying a CI-built `manylinux` wheel plus a prebuilt
`linux_x86_64` wheel attached) and on PyPI as
**`kwcapture`** (https://pypi.org/project/kwcapture/) — publish new versions with
`.venv/bin/python -m twine upload -r pypi dist/<sdist and manylinux wheels>` (credentials
in `~/.pypirc`; never commit or print them). Author: Tjandra Satria Gunawan
<tjandra.satria@sci.ui.ac.id>. `origin` is SSH (`git@github.com:tjandrasg/kwcapture.git`).
There is no `gh` CLI here, so repo/release admin (creating releases, uploading assets,
topics) is done with the GitHub REST API via `curl` using whatever credential is
configured for github.com (it is in `~/.git-credentials`) — never commit or print a token.

Working dir: `~/way_scr_cap`. **Read this first if you are a fresh session.**
Status: **done and working** — ~40 fps full-screen / ~185 fps per-window Wayland capture,
Python API + CLI + 165 functional + 37 ring-reader checks. See `README.md` for user-facing
docs; this file is the investigation log + gotchas.

## FRESH STATUS — 2026-10-09 ~08:20 — **v0.6.0 RELEASED to GitHub + PyPI: the hidden-window enumeration is out**

> **What shipped**: tag `v0.6.0` → `cdb0458` on `main` = the non-normal-window work of the session
> below (dialogs/docks/desktop via the KWin scripting route) plus the headless-CI work already on
> `main`. `ci.yml` `build` and `release.yml` both **success** (runs 37868257712 / 37868258136).
> GitHub release 407395393 carries the CI sdist, the CI `manylinux_2_28` wheel and the locally built
> `linux_x86_64` wheel — same three assets as v0.3.0–v0.5.0. PyPI 0.6.0 carries **two** files: the
> sdist and the manylinux wheel, taken **off the GitHub release** first, so PyPI's sha256
> (`b2683129743983c3…` whl / `610205d2bc3ef1c0…` tar.gz) are byte-identical to the release assets.
> The `linux_x86_64` wheel is a GitHub asset only — PyPI rejects that tag, as the checklist says.

> **Verified, in the order done**: 165/165 functional + 37/37 ring-reader under `-X dev` on this
> desk (one output at 100 %, so the fractional-scaling checks sit in their degenerate branches —
> see FLAKE-1 for why 165 here vs 172 on the two-output desk); the locally built wheel installed in
> a throwaway venv **from `/tmp`** really captures (2560x1440, 99.7 % non-black) and lists
> desktop + dock + the Winamp dialog; the sdist carries no `private/`, no `*.jsonl`, no credential
> — **a loose `ghp_`/`pypi-AgEIcHlwaS` grep hits this very file's checklist text**, so re-grep for a
> long token-shaped run (`ghp_[A-Za-z0-9]{20,}`) before believing a hit; `pip install --no-cache-dir
> kwcapture` in a clean venv outside the checkout gives 0.6.0 and `kwcapture doctor` answers *"full
> window enumeration works via KWin scripting: 3 window(s) outside KWin's own app-window list
> (desktop, dialog, dock)"*. Release notes were PATCHed into the body (CI leaves only the
> `**Full Changelog**` stub — a body with just that stub means the run is unfinished).

> **Worth watching, unverified**: the wider default list is a behaviour change for downstream —
> `iw3-desktop` (nagadomi/nunif, see DOWNSTREAM above) calls `list_windows()` without `all_types=`,
> so it now sees panels and the desktop as well, and a name that used to resolve uniquely can raise
> `AmbiguousWindow`. Nothing in this tree shows that breaking anything, but it is the first thing to
> ask about if a downstream report arrives.

> **Post-release housekeeping, same day (`main` = `d57c837`, CI `build` green).** No library code
> changed — this was repo/docs work: the README badge row (PyPI version + status + license + CI, and
> two static badges *KDE Plasma: 6.x tested* / *Wayland: ScreenShot2*; **no download badge**, measured
> reason below), the community files (`SECURITY.md`, the two issue forms + `config.yml`,
> `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`), Dependabot's first PR merged (`2ec83eb`) **with the
> release workflow rehearsed against it** (run 37881396351 — recipe in the community-files section),
> then `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`. GitHub's community checklist: 7/7.
> **Packaging gotcha found while doing it:** `MANIFEST.in` lists docs **by explicit name**, so
> `SECURITY.md`, `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` were absent from the sdist until added
> there — a new root `.md` never ships automatically. Fixed and verified by rebuilding the sdist;
> the published 0.6.0 files are immutable, so this lands at the next release. Worth doing because
> the people who run `pip install --no-binary` are exactly the ones who read `SECURITY.md`.
> **Size note — trimmed the same day, 77 KB → 53 KB.** It had grown ~11 KB during this session, so the
> superseded detail went to `AGENTS.old.md` **verbatim** (nothing deleted; every move listed under
> *ARCHIVED* below): both 2026-10-08 day-logs, BUG-1's original analysis, BUG-2's full analysis,
> BUG-4's bisect record, the completed `~~done~~` ideas, and a shorter community-files section — each
> replaced by the distilled bullets that stay here. **What made this safe: the archive was written
> first, and the script asserted every moved line was present in it before a summary replaced it.**
> If you add a third FRESH STATUS, distil one out the same way rather than growing the file again.

## HEADLESS / NESTED KWin — what is settled (full day-log archived 2026-10-09)

> Long form: the `FRESH STATUS — 2026-10-08 ~19:20` day-log in `AGENTS.old.md` (under
> *ARCHIVED 2026-10-09*). The durable part, and it is now also in README → *How this is tested* and in
> the comments of `probe/ci_headless_kwin.sh`:

* **`org.kde.KWin.ScreenShot2` exists only while KWin is OpenGL-compositing** — its sole owner is
  the screenshot effect, and `ScreenShotEffect::supported()` is `effects->isOpenGLCompositing()`.
  No GL compositing ⇒ the bus name never appears ⇒ `was not provided by any .service files`.
* **OpenGL compositing needs a DRM render node.** The virtual backend offers it only if
  `findRenderDevice()`/`drmGetDevices2()` found one; otherwise KWin silently falls back to QPainter.
  So no Mesa env tinkering helps — `LIBGL_ALWAYS_SOFTWARE`, `EGL_PLATFORM=surfaceless`, installing
  `libgl1-mesa-dri` change nothing, because the decision is made before Mesa is asked.
* **A GitHub-hosted runner can never provide one** (measured on the runner: `/dev/dri/card1` exists
  as `hyperv_drm` with **no `renderD*` node**, and `vgem`/`vkms` are not built for the azure kernel
  even after installing `linux-modules-extra-*`). Window *listing* works there; frames cannot.
  What would work: a GPU runner, or a self-hosted KDE runner — with a render node present the job
  silently switches back to strict and tolerates nothing.
* **The tolerant path is deliberate, not a hidden failure:** `KWCAPTURE_NESTED_ALLOW_NO_SCREENSHOT2=1`
  converts *only* missing-ScreenShot2 failures into a printed `ENVIRONMENT LIMITATION`; socket,
  authorisation, output/window listing and every other `doctor` check still fail the job.
* **Run the harness by hand** (no GitHub involved, ~6 s on a Plasma box):
  `dbus-run-session -- bash probe/nested_kwin_test.sh`, or
  `docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim bash /w/probe/ci_headless_kwin.sh`.
* Two unrelated traps from that session, still true: the Qt **Wayland** QPA plugin is the Debian
  package **`qt6-wayland`**, not `qt6-qpa-plugins`; and `QT_LOGGING_RULES="kwin_core.debug=true"`
  makes KWin say *why* it is not compositing instead of one vague warning.
* Not the problem, then or now: **PipeWire**. `ScreenShot2` needs none — we hand KWin a pipe fd and
  `ScreenShotWriter2` writes the QImage into it. Don't add a `pipewire` package chasing that log line.


## DOWNSTREAM — nagadomi/nunif#746 is MERGED (this is the compatibility list for future releases)

`iw3-desktop` (part of [nunif](https://github.com/nagadomi/nunif)) ships kwcapture as its **optional
Wayland (KDE Plasma) screenshot backend**; nagadomi merged it 2026-10-08 into `nagadomi/nunif:dev`.
`README.md` now has a **Used by** section (commit `d429ea2`) naming it and the API it calls, which is
the compatibility list for future releases: `Capture(monitor=…)` / `Capture(window=…)` with
`cursor=` and a private `shm=`, `grab(copy=True)`, `geometry()`, `list_monitors(measure_scale=True)`,
`list_windows()`, `find_window()` + `AmbiguousWindow`, `unique_shm_path()`, `effective_scale` /
`area_scale`. It never requires kwcapture at import time and installs nothing automatically — the
maintainer's condition for merging — so **do not make importing `kwcapture` heavier or add a hard
install-time step**, or the optional-dependency story upstream breaks.

His stated reason for accepting, worth keeping in mind for any future discussion with a distributor:
he had not tested KDE capture but it "won't affect other environments", and on the shipped binary —
the GitHub Actions build "provides some evidence that the project is being handled responsibly",
though "ultimately it comes down to whether the binary is trusted". The facts that answer that
(verified in this tree, do not restate them without re-checking):
* the helper is one C file (`kwcapture/native/kwcapture.c`, 2141 lines) + `kwcapture_shm.h` (103),
  and its **direct** dependencies are exactly three — `libc`, `libsystemd` (sd-bus),
  `libwayland-client` — with no RPATH (`readelf -d`, not `ldd`: ldd also lists whatever the
  desktop session put in `LD_PRELOAD`, which on this desk adds a GTK CSD shim that the binary
  does not need). The sdist carries **no compiled artefact at all**: 5 `.py` files + the `.c` +
  the header. All of this is spelled out, with runnable checks, in `SECURITY.md`;
* the only outbound connection in the source is `wl_display_connect(NULL)` — no sockets, no network
  code, no root, no portal; frames come from the shm ring KWin fills;
* KWin's authorisation is a plain `.desktop` file in `~/.local/share/applications` the user can read
  and delete (`_desktop.py`);
* the sdist carries the C source and `setup.py`/`_native.py` build it with `cc -O2 -std=gnu11` +
  pkg-config, so `pip install --no-binary=kwcapture kwcapture` needs no trust in us at all;
* the PyPI files for a release are the artefacts of that tag's public `release.yml` run.

## ARCHIVED into AGENTS.old.md (2026-10-08, and again 2026-10-09)

Moved out **verbatim** — session logs of *released* work whose conclusions already live in
`CHANGELOG.md`, `README.md`, `SECURITY.md` or the CI job's own comments. Nothing is ever deleted; the
archive keeps the reasoning and the dead ends, and this file is what a fresh session can hold in its
head. If you are about to add a third `FRESH STATUS`, distil one out instead.

**2026-10-09** (file had grown back to 77 KB): the 2026-10-08 headless-CI day-log → distilled into
**HEADLESS / NESTED KWin**; the 2026-10-08 non-normal-window day-log → distilled into the
**SESSION STATUS → released as v0.6.0** section; BUG-1's original analysis, BUG-2's full analysis and
BUG-4's bisect record → each bug keeps its conclusion, rate, next experiment and guardrails; the
completed `~~done~~` bullets from *Ideas not done yet*; and a shorter *Community files* section.
**2026-10-08** (from 81 KB): the nine `FRESH STATUS — 2026-10-07 …` day-logs → **SCALES** and
**MONITORS & RESILIENCE**; the original nested-`--virtual` discovery write-up; BUG-4's three-session
hunt; BUG-3 (fixed, lesson kept as a Gotcha); the v0.1/v0.2 file map, benchmark tables, packaging/CI
notes and the forensics write-up.


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

## SESSION STATUS — 2026-10-08 ~23:50 → **released as v0.6.0** (log archived)

> Full session log: the `SESSION STATUS — 2026-10-08 ~23:50` day-log in `AGENTS.old.md` (under
> *ARCHIVED 2026-10-09*). Feature list in
> `CHANGELOG.md` 0.6.0, user docs in README → *Per-window capture*, security treatment in
> `SECURITY.md`. What a future session must not have to re-derive:

* **Why krunner was not enough:** `windowsrunnerinterface.cpp` skips `!window->isNormalWindow()` in
  every branch of `Match()`, and `CaptureWindow` resolves only `QUuid` handles that come from
  `Window::internalId()` = `QUuid::createUuid()` — random, so not derivable from an X11 window id.
  `getWindowInfo` takes a uuid only; `queryWindowInfo` is the interactive picker. **Conclusion: the
  scripting interface is the only API in Plasma 6 that reaches the full window list.**
  KWin source reference: `invent.kde.org/plasma/kwin/-/archive/v6.6.6/...` (fetch it before
  answering any "does KWin expose X?" question).
* **The mechanism:** `org.kde.kwin.Scripting.loadScript(path, plugin)` is unauthenticated and takes
  a plain path — nothing has to be installed under `~/.local/share`. JS `workspace.windowList()` is
  `workspace()->windows()`, unfiltered. Plasma 6 has no `registerDBusAdaptor`, so the reply comes
  back through `Script::callDBus` **to our own unique bus name**, nonce-guarded. `Script::run()`
  early-returns while running ⇒ load once per query + `unloadScript`, never `run()` in a loop.
  Measured load+run+reply ≈ **0.5 ms**.
* **Implemented in** `kwcapture/native/kwcapture.c` ("full window enumeration"): `collect_windows()`
  = krunner pass + `collect_windows_script()`; failures are a stderr note plus the old list, never a
  failed call. Flags `--normal-only`, `--require-full` (exit 3); JSON gains `window_type_name` +
  `krunner_listed`. Probes: `non_normal_windows.py`, `kwin_script_enumerate.py`,
  `kwin_script_failure_path.py`.
* **Behaviour change that will generate reports:** a *name* can now match its own dialog too, so a
  lookup that used to resolve can raise `AmbiguousWindow`. That is the honest answer; `--normal-only`
  / `all_types=False` restores the old list.


## OPEN BUGS — found, not yet fixed

> **RULE FOR FRESH SESSIONS: anything that looks wrong goes in this section the moment you
> see it, before you chase it.** Do not investigate first and write it up later — two
> sessions have now lost findings that way. A half-paragraph with the symptom is worth more
> than a perfect post-mortem that never gets typed. Mark unverified guesses `(unverified)`.

### FLAKE-1 (test suite, not the library): `area_in='physical' grabs the device region it names` fails when the screen is animating

* **Seen 2026-10-08 ~19:10**, once, on the desktop: `[FAIL] DP-1: area_in='physical' grabs the
  device region it names  MAD=70.0 (display == scene: one mapping only; detail 12.3)`. Rerunning
  the whole suite immediately after: **152/152 green**, twice. Nothing in the library was touched
  (that branch changes `probe/`, the workflow and the docs only).
* **Why the test can do that** (`tests/test_kwcapture.py`, the `mphysnat`/`mphys` pair): it grabs
  the whole output, picks the *most detailed* 256x144 device rectangle it can find, then grabs that
  rectangle again in a **second, separate** ScreenShot2 request and compares contents. Detail is
  exactly what animation looks like to that scan, so a video / terminal / anything repainting in
  the chosen rectangle makes MAD explode (70 is far past a cursor sprite: ~12 at most). The
  comparison is between two frames, not two mappings.
* **Fix, when someone touches that test**: grab the whole output twice and mask out every rectangle
  that differs between them, then choose the detailed-and-stable patch. Do not just loosen the
  20.0 threshold — a threshold that has to cover a moving picture protects nothing.
* **Also note**: the suite's check **count depends on how many outputs the desk has** — 172 on the
  two-output desk (DP-1 75 % + HDMI-A-1 125 %) that the v0.5.0 notes describe; **165 measured on
  2026-10-09 ~08:20**, when the desk had a single output at 100 %. The +13 non-normal-window checks do
  not multiply with outputs, so 172 there is arithmetic, not a measurement.
  **The desk changed again later the same day**: HDMI-A-1 (3840×2160) is back at 100 % beside DP-1
  (2560×1440 at 100 %), so the number in README/CHANGELOG (165) is the *single-output* figure and the
  current two-output count has **not** been measured. Re-run and count the `[PASS]` lines before
  quoting anything, and `kwcapture monitors --measure-scale` first: the per-output checks
  (`area_in="physical"` especially) only mean something when a display scale and the scene scale
  differ, and this desk has neither right now (x1/x1 → the degenerate "one mapping only" branch).

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
> The original 2026-10-06 analysis is archived; what it concluded is above.


The original analysis — how it was reproduced with a self-repainting `konsole`, the three fix options
considered before the one that shipped, and the fact that the repro script lived in `/tmp` (so it is
gone; `probe/stale_window.py` is the durable version) — is in `AGENTS.old.md` (*BUG-1: the original
analysis*). Two things from it are still worth knowing: **the stale buffer is not the last frame before minimising** (it is whatever KWin
rendered last, possibly mid-animation), and the fix deliberately avoided a per-frame D-Bus round
trip — a `KWC_ERR_STALE` frame status would need `KWC_VERSION` bumped to 3.


* **Also unverified, same family — test these next** (same silent-staleness shape):
  window on **another desktop** (switch with `/KWin setCurrentDesktop`), window on another
  **activity**, and a window that is fully **occluded** — README → *Per-window capture* claims
  "no cropping by whatever is on top of it", and that was verified for **geometry** only, never for
  **liveness** (an occluded window's buffer could in principle be as stale as a minimised one).

### BUG-2 (`sched_yield()` in the grab hot path) — fixed in v0.4.0; kept here for the hunt, not because it is open

A lazy ctypes init inside `grab()`'s busy-wait caught only `OSError`, but a missing libc symbol
raises **`AttributeError`** — so on musl or odd SONAMEs every capture died, not one code path.
Fixed in v0.4.0: catch both, keep the fallback a real named function, and guard the cache with
`callable()` rather than `is None`, with a regression test (`regression: BUG-2 sched_yield`).

The author's remembered `TypeError: 'int' object is not callable` was **never reproduced and is not
in the tree or its history**; `libc.sched_yield()` returns int 0, so a stray paren
(`= libc.sched_yield()`) caches 0 and produces exactly that message from far away — a hypothesis,
not a finding, and the same family is covered by BUG-4 (environmental). If it reappears:
`grep -rn "sched_yield" kwcapture/`, rerun under `python -X dev -X faulthandler` for a full
traceback, and remember the *frame above* is where an int came from. Full analysis, the AST scan
that came up empty, and the three verified branches: `AGENTS.old.md` (*BUG-2: sched_yield*).


### BUG-4 (ROOT-CAUSED 2026-10-07 — NOT OURS): corruption while reading shared memory zero-copy

> **Not a kwcapture bug, and probably not a software bug.** Never write "BUG-4 fixed" — write
> **"not ours, guardrails added, fault rate unchanged."**

* **Reproduces with no kwcapture at all:** `probe/race_bisect.py` / `probe/corruption_rate.py` hit
  the historic symptoms — `TypeError: 'int' object is not callable`, `IndexError: only integers…`,
  SIGSEGV, `double free or corruption (out)` in numpy's array dealloc — in a tight loop of numpy
  views over an `mmap`, no daemon, no writer, no thread.
* **Rewriting the read path changed nothing:** `probe/fault_rate.py` faulted 4/4 rounds on the old
  path and 4/4 on the hardened one (table in `probe/FAULT_RATE_RESULTS.txt`), and a
  cache-views-per-slot variant faulted 3/3 — so not the view-churn either. **Rate ≈ 1 event per
  10⁵–10⁷ view constructions**, non-deterministic; at ~40 fps that is days between events.
* **Likeliest cause was the box**: `llama-server` at ~103 GB RSS (72 GB shared), `MemFree` ≈ 1 GB of
  131 GB, `SwapTotal = 0`, direct reclaim live, **non-ECC** RAM, a kernel oops in page reclaim the
  same day, and a `.crash` record showing **SIGBUS** for the test suite — a ring page that could not
  be materialised looks exactly like "flaky, impossible values". RAM was later taken off XMP
  (5200 → 4800 MT/s); `probe/fault_rate.py` still faulted on the live ring afterwards, while the
  no-writer probes stayed clean for ~144M iterations — which is what `probe/writer_reader_repro.py`
  was built to test (raw shm + one concurrent writer, no kwcapture).
* **Decisive experiment, still the right one:** run it on another machine, or with `llama-server`
  stopped — `KWC_ITERS=40000000 .venv/bin/python -X dev probe/fault_rate.py`. Clean there ⇒
  environmental, closes. Faults there too on the same numpy/CPython ⇒ report upstream with
  `probe/corruption_rate.py`'s ~20-line core and the dealloc trace.
* **v0.4.0's read-path work stands on its own** (see `CHANGELOG.md` 0.4.0): single contiguous
  descriptor read, geometry validated once per generation, bounds-checking before any value becomes
  an offset/count/shape, **read-only** client mapping, newest-published-frame semantics, one retry
  of a torn `copy=True` read, and a generation counter that refuses a frame spanning
  `restart()`/`close()`. Correctness fixes — **not** a mitigation of this fault.
* Guardrails that run in CI without a compositor: `tests/test_ring_reader.py`.
  Full bisect record, the mis-executed-bytecode observations, the memory forensics and the
  head-to-head table: `AGENTS.old.md` (*BUG-4: the bisect record, 2026-10-09 archive*).


#### BUG-4b: `CaptureError: daemon error: Success` — double read of `hdr.error`

`_check_error()` reads the shared `error` field more than once (once to decide, once to
format), so a concurrent write can produce the self-contradictory message *"daemon error:
Success"*. Read it into a local **once** and raise from that. Same class of torn read as
BUG-4; fix together.

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
* **Window enumeration** (KWin has none on ScreenShot2) needs **two** sources. (1)
  `/WindowsRunner` `org.kde.krunner1` `Match("")` — empty query matches every window,
  locale-independent (do NOT use the translated `"window"` keyword); ids are
  `"<action>_<uuid>"`, dedupe (one entry per desktop); `Run("0_<uuid>","")` activate / `1`
  close / `2` minimise. **It filters: every loop skips `isUnmanaged()` and
  `!isNormalWindow()`** ("NET::Normal or NET::Unknown non-transient"), so dialogs, docks,
  the desktop, splash, tooltips and override-redirect windows are unreachable there — no
  query string changes that. (2) `org.kde.kwin.Scripting` `/Scripting`
  `loadScript(filePath, pluginName) -> i` + `org.kde.kwin.Script` `/Scripting/Script<id>`
  `run()` + `unloadScript(pluginName)` gives the whole list, because the JS global
  `workspace`'s `windowList()` is literally `Workspace::windows()`; the script answers by
  calling *us* (`callDBus(our_unique_name, …)`, async, so the compositor never blocks) —
  Plasma 6 has no `registerDBusAdaptor` anymore, so it cannot export a method. Four traps,
  each measured: `loadScript` **does not run** the script; `run()` sets `setDelayedReply`
  and only ever replies on its error path, so send it with a short timeout and ignore that
  one; `loadScript` is overloaded `(s)`/`(ss)` and a name-keyed binding picks `(s)` and
  silently loses the plugin name (then `unloadScript` cannot find it — ask for `ss`
  explicitly); `Script::run()` early-returns while running, so re-triggering means
  load-once-per-query + `unloadScript`, not `run()` in a loop. `String(w.internalId)` in JS
  is the uuid with braces, same spelling as krunner's.
  Details from `/KWin getWindowInfo(uuid)` → a{sv}: caption, resourceClass/Name,
  desktopFile, role, icon, x/y/width/height as **doubles**, minimized/fullscreen/
  keepAbove/keepBelow/noBorder/skipTaskbar/skipPager/skipSwitcher,
  maximizeHorizontal/Vertical (**ints**), type, layer, desktops/activities (`as`), uuid —
  **no pid, no focus flag**. It answers for *any* window (dialogs and panels included, and
  an unknown handle gives an empty map, which is what makes it usable as a handle check).
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

## SCALES — there are THREE; conflating them was a real bug (settled in v0.5.0)

* **`wl_output.scale`** — an integer hint (`1`, `2`). Useless for fractional scaling; never use it.
* **Display scale** — `Monitor.effective_scale`, and the `scale` field of a **whole-output** frame
  (measured 0.75 / 1.25 on a real 75 % + 125 % desk). `device px = logical × this`; whole-output
  frames are device px, 1:1, never resampled.
* **Scene / area factor** — `Monitor.area_scale` / `Capture.area_scale`, and the `scale` field of an
  **area** reply: one number for the whole desktop (1.25 on both outputs). It is also what XWayland
  surfaces are scaled by (a 320 px X11 window is 256 logical there) and what the workspace frame is
  rendered at (8108 px = 6486 logical × 1.25).
* **`area=` maps through the DISPLAY scale — measured, not guessed.** Take a high-detail device
  rectangle out of a native whole-output frame, then grab that region with the logical coordinates
  computed three ways (`/0.75`, `/1.25`, `/1.0`): MAD against the native crop
  **4.1 / 46.7 / 48.8**. So `_resolve_area()` divides by the **display** scale. Dividing by the scene
  factor was the v0.5.0 bug: it returned the pixel *count* you asked for but `pixel_scale /
  area_scale` (**0.6×**) of the region you named — a zoom, not a crop. The frame still comes back at
  the scene factor (`w × area_scale / pixel_scale` px); `geometry()` says what you got and
  `resize()` takes it back to device size.
* Consequence nobody guessed: **a region grab on a 75 % output is an upsample** — 250 image px for
  150 px of panel — while on an output sitting at the scene scale it is 1:1 native. No KWin option
  changes this (`native-resolution` on = scene factor, off = 1× logical; both measured).
* **`Window.geometry` is logical, frames are device** (measured with xterm: 320 X11 px → 256 logical
  → 192 device at scene 1.25 / display 0.75), so any assertion comparing a frame to `Window.width`
  must multiply by `Capture.pixel_scale`.
* Both mappings are only *distinguished* when the two factors differ. One output at 100 % runs these
  checks in a degenerate branch (see FLAKE-1), and the check count follows the hardware: **165** on
  a single output at 100 % (172 on the 75 % + 125 % desk, by arithmetic: the 13 checks added for
  non-normal windows are per-session, not per-output).

## MONITORS & RESILIENCE — facts the design rests on (from the v0.4.0 / v0.5.0 work)

* `Monitor.id` is the **`wl_output` global name** (65, 79 here) — ScreenShot2 has no per-output
  handle. `find_monitor()` resolves a number **id first, then index**; `index` is the
  top-left-first `list_monitors()` order; ambiguous names are refused rather than guessed.
* **`Capture()` with no `monitor=` follows KWin's *active screen*, which follows focus.** Never
  assert "geometry of the first output" — assert against `Capture.screen_name`, the invariant that
  actually holds. (The old test failed while an xterm had focus on the other screen and passed again
  minutes later with nothing changed.)
* **`kscreen-doctor` and KWin can disagree**: kscreen reported an output `disabled` while KWin
  advertised it on the registry *and* happily served 3840×2160 from it. `list_monitors()` is the
  truth about what is capturable — never kscreen's enabled flag.
* **`Capture(workspace=True)` is ScreenShot2 `CaptureWorkspace` = the bounding box of the scene**, not
  "the primary screen". Measured on the 2026-10-09 two-output desk (DP-1 2560×1440 @ 0,0 + HDMI-A-1
  3840×2160 @ 2560,0): geometry **6400×2160**; the band under the shorter output reads **exactly 0**
  (pure black, not garbage); and each output slices back out with the `position`/`geometry` that
  `list_monitors()` reports — `frame[y:y+h, x:x+w]` is shape-identical to a per-monitor capture,
  verified for both. Median cost on that desk: **76.5 ms** workspace vs 26.0 ms (1440p) and 50.5 ms
  (4K) for one output, and the ring it allocates is **442 MB** of tmpfs at the default 4 slots
  (221 MB at `slots=2`) — a workspace `Capture` is a RAM decision, not a free one. **Untested: whether
  it also spans KWin's virtual desktops**, since this desk runs a single one; "workspace" is verified
  here only as "union of the enabled outputs".
* `PIL.ImageGrab.grab()` returns the **whole X11 root** (both outputs, 6400×2160), not the primary
  output. A colour reference must compare against a `Capture(workspace=True)` frame: cropping a
  per-output frame onto it made the MAD nearly identical for correct and swapped channels, i.e. a
  check that silently tested nothing. Against the workspace frame it is exact (MAD 0.0, and 15.0 if
  the channels are swapped).
* **Fractional scale is measured, not read**: `--probe-scale NAME` grabs the same 128×128 logical
  area twice, with `native-resolution` on and off, and the ratio is the real scale
  (`mode_probe_scale`) — works whatever mechanism KDE uses internally.
* **The ring cannot be grown in place.** A client maps it at its length when the daemon starts, so
  `ftruncate`-ing it larger SIGBUSes anyone reading past the old end. Hence `ENOSPC` →
  `RingTooSmall` → the *client* restarts the helper and the ring is rebuilt, sized from its first
  frame (`--slot-floor WxH` sets the headroom). A daemon that re-execed itself would leave clients
  holding a stale mapping — which is why the client drives the restart.
* `auto_restart=True` (default) retries `DaemonDead` / `RingTooSmall` / a timeout with no daemon
  alive, bounded by `restart_limit=5` *consecutive* restarts (reset by a good frame;
  `auto_restarts` is cumulative). **Deliberately never recovered**: `WindowGone` (a new daemon cannot
  resurrect your window) and `TimeoutError` while the daemon is *alive* (that is KWin being slow or
  wedged; respawning would mask it). Both asserted in `resilience_section()`.
* Test-harness rules that came out of this work, all of them paid for:
  `tests/test_ring_reader.py` builds a `Capture` via `__new__` (no `__init__`), so **every**
  attribute the frame path touches needs a class-level default on `Capture`; `wmctrl` sees only
  **XWayland** windows and wants the X11 id, not kwcapture's QUuid handle; `Window.geometry`
  includes decoration/shadow margins (match by `app_id`, and give frame-size assertions ~60/90 px of
  slack); set a window's size **before** creating the `Capture`, because the ring is sized from the
  first frame (inheriting a large window turned a "grow" test into shrinks that passed for the wrong
  reason); the shell rewrites `xterm`'s title, so find a test xterm by pid, not by title; and
  `setsid` with redirected stdio for anything GUI started from a tool call, or the tool kills it.

## Gotchas (each cost real time — respect them)
* **A fix with no test is a guess.** BUG-3's first "fixed" note was disproved by the fd-counting
  regression test written for it — 16 → 20 fds over 4 `restart()` calls, i.e. one fd leaked per
  restart in the path just "fixed". Mark anything unverified until a test fails without it.
* **Never test a built wheel from the repo root**: `./kwcapture` shadows site-packages and you end up
  exercising the source tree (in CI that produced a bogus "helper not found"). `cd /tmp`, and assert
  `'site-packages' in kwcapture.__file__`.
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

## Community files — what is in `.github/` and why it is incomplete

`SECURITY.md` · `ISSUE_TEMPLATE/{bug_report,feature_request}.yml` + `config.yml` ·
`PULL_REQUEST_TEMPLATE.md` · `dependabot.yml` · `CODE_OF_CONDUCT.md` · `CONTRIBUTING.md`.
Written for this repo, not from stock templates; the useful content is the part a generator cannot
know.

* **Bug form** leads with the three things that decide most reports here — `kwcapture doctor` output,
  Plasma/KWin version, session type — and says up front that CI cannot test capture, so nobody treats
  a green pipeline as evidence. Blank issues stay enabled on purpose.
* **PR template** carries the two traps CI structurally cannot catch: **green CI ≠ capture works**
  (no DRM node on hosted runners) and **helper changed ⇒ the release wheel must be rebuilt**; plus the
  nunif API-compat list and the `private/` rule.
* **Dependabot covers `github-actions` only.** Versions rot there, not in the package: a stale
  cibuildwheel pin broke the v0.1.0 *and* v0.2.0 release runs when its dated manylinux image left
  quay.io. No `pip` section — `numpy` and the extras are deliberately unpinned, so bot PRs against
  open ranges are pure noise for one maintainer. An explicit `ignore` holds **cibuildwheel below 5**
  so a bot cannot step over a breaking major without a human reading `release.yml`'s comments.
* **First cycle (2026-10-09):** PR #2 grouped checkout v4→v7, setup-python v5→v7,
  upload-artifact v4→v6, download-artifact v4→v7, cibuildwheel untouched ✓. Squash-merged
  (`2ec83eb`), CI green — but **a PR runs `ci.yml`, which never touches the artefact actions**, so
  `release.yml` was rehearsed with `workflow_dispatch` at `publish: false` (run 37881396351): sdist +
  manylinux wheel built, ring-reader tests ran, `upload-artifact@v6` produced `dist`, smoke test said
  `wheel ok 0.6.0`, and the release-attach + publish steps were *skipped* as designed. **That
  dispatch is the way to verify release tooling without a release** — no `gh` needed:
  `curl -X POST -H "Authorization: Bearer $TOK" -d '{"ref":"main","inputs":{"publish":false}}'
  …/actions/workflows/release.yml/dispatches`. **Still untested by anything: `download-artifact@v7`**
  — it lives only in the `publish` job, which this process does not use (PyPI upload is local `twine`
  against the release assets). Dormant, not proven: if trusted publishing is ever turned on, verify
  it against TestPyPI first, never mid-release.
* **`CODE_OF_CONDUCT.md` = Contributor Covenant 2.1**, fetched from contributor-covenant.org rather
  than typed, assembled by a script that *asserted* the body is byte-identical apart from the one
  contact substitution — **do not hand-edit the covenant section, regenerate it**. Its preamble says
  the quiet parts out loud: one maintainer is contact **and** decision-maker, there is no committee,
  enforcement reaches this project's spaces only, nothing is retroactive, and **a report about the
  maintainer himself goes to GitHub Support**. "Acknowledge within 5 working days" deliberately
  matches `SECURITY.md` — change one, change the other. Added because distributors read this checklist
  as trust evidence (the nunif precedent), not for the badge; the objection that survived — a CoC
  needs a real contact — is answered by the maintainer's published email.
* **Deliberately absent:** Discussions, wiki, FUNDING, coverage/lint badges, `ACCESSIBILITY.md`.
  No coverage/lint badge because no such step exists, and the functional suite needs real hardware —
  a documented limitation, not a gap to paper over. No accessibility statement because there is no UI,
  docs site or interactive surface beyond Python and stdout: the only honest content would be
  "captured content inherits the source app's accessibility", which is a sentence, not a policy.
* **Validating issue forms:** `yaml.safe_load` is not enough — every body item needs
  `type` ∈ {markdown, textarea, input, dropdown, checkboxes}, markdown items `attributes.value` and
  the rest `attributes.label`, dropdowns ≥ 2 options, and `validations.required` never on checkboxes.


## README badges — chosen deliberately (do **not** add a download badge)

Top row: PyPI version, PyPI status (`beta`), license (`MIT`), CI `build`, and two **static**
shields.io badges — `KDE Plasma: 6.x tested` and `Wayland: ScreenShot2`. Static ones carry no
upstream data that can go stale, and the Plasma badge says *tested*, not *required*: Plasma 5
has never been tried here, so a version **requirement** would be a claim this tree cannot back
up. Deliberately absent: **downloads** (`pypi/dm`), stars/forks (vanity), coverage and lint
(there is no coverage or lint step — a badge for a thing that does not run is worse than no
badge), and a per-job CI badge for `headless KWin capture` (it passes *tolerantly* on runners
with no DRM node, so a green badge there overstates what was proven — the **How this is tested**
section carries that nuance instead).
**Measured, not assumed** (2026-10-09, three identical calls to `pypistats`): kwcapture
reported `last_day 8 / last_week 398 / last_month 0` — the monthly rollup is broken upstream, so
the standard download badge renders **red "0/month"** on a package that is being installed and
ships as nunif's optional KDE backend. Check before believing any badge:
`curl -s https://img.shields.io/pypi/dm/kwcapture.json` (and the same `.json` trick works for
every candidate badge — it returns the message shields would render).

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

**Open:**
* **Run the strict headless job somewhere with a render node** — a self-hosted KDE runner or a
  GPU-labelled runner; with a render node present `probe/ci_headless_kwin.sh` switches back to
  strict and tolerates nothing. Still open and now cheap, because the harness exists.
* **Test BUG-1 (minimised → stale frame) inside the nested session** — minimise the KCalc from the
  probe and assert what comes back; nothing else in the repo can reach that state on demand.
* **Test `scale=` handling** — `kwin_wayland --scale` exists, so `KWCAPTURE_NESTED_SIZE` plus a scale
  knob in `probe/nested_kwin_test.sh` would re-verify the fractional-scaling conclusions on a
  compositor whose scale is *known* instead of whatever the desk happens to be set to.
* `getWindowInfo` gives no pid — a `Window.pid` would need `/proc` matching by app id.
* Fractional scaling: `native-resolution` is set; behaviour with a scaled *window* (not output) is
  untested.
* **Non-KDE compositors stay out of scope, deliberately** — the `kw` in the name is the promise.
  `probe/globals.c` dumps what any compositor advertises if the question ever needs re-answering;
  the honest failure mode is a clear "cannot reach the compositor" error, never black frames.

**Done — recorded in `CHANGELOG.md`, not re-explained here:** window `active` flag (v0.3.0) ·
non-normal windows (v0.6.0) · following a resized window (`Capture.resized`, `last_geometry`) ·
auto-restart on `DaemonDead` with `restart_limit` · multi-monitor (`list_monitors()`,
`Capture(monitor=…)`, monitor-relative `area=`) · fractional scaling (`effective_scale`,
`measure_output_scale()`, `area_in="physical"`).
One design fact worth keeping from the ring-resize work: the ring is **never grown in place** — a
client has it mapped at the old length, so growing it under a reader would SIGBUS whoever read past
the old end. Instead `ENOSPC` → `RingTooSmall` → the daemon restarts and the ring is *rebuilt* at
the new size: same outcome for the caller, no window where a mapping and a file disagree.
