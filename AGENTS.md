# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

> **Archive:** `AGENTS.old.md` holds the superseded detail — the original three-key-findings
> investigation log, the v0.1/v0.2 file map and benchmark tables, old packaging/CI notes, the
> forensics write-up, and (moved 2026-10-08, see the *ARCHIVED* section below) the 2026-10-07
> session logs of the v0.4.0/v0.5.0 work, the original nested-`--virtual` discovery write-up, BUG-4's
> three-session hunt and the closed BUG-3. Consult it when something here is too terse or you want
> the reasoning behind a rule; it is history, **not to-do**.
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
> `probe/stale_window.py`) or their content goes into this file. See *Forensics* below for
> what can and cannot be recovered after the fact.

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

## FRESH STATUS — 2026-10-08 ~19:20 — **headless CI is GREEN, and honest about what it covers: KWin only owns `ScreenShot2` while it is OpenGL-compositing, and that needs a DRM device GitHub's runners do not have**

> Outcome: `build` + `headless KWin capture (Plasma 6, no GPU)` both pass on PR #1 (run 39). The
> job starts a real nested KWin 6.3 in a Debian trixie container, authorises the helper over the
> desktop-entry mechanism, lists the nested output and the client window, and reports the capture
> path as an `ENVIRONMENT LIMITATION` because that runner cannot give KWin a render node — with the
> whole reason below, so nobody has to rediscover it. On a machine that *can* composite (this
> desktop, any KDE self-hosted runner, a GPU runner) the same job runs strict and fails on anything.

> **MERGED 2026-10-08 ~19:50**: PR #1 → `main` as `a575828` (merge commit, all 7 commits kept),
> branch `ci/headless-kwin` deleted (the repo has `delete_branch_on_merge`, and the local branch is
> gone too). `README.md` now has a **How this is tested** section + a CI badge, so the DRM-node
> limitation is documented where users and distributors will look at it rather than only here.
> Runs on `main` now, on every push and PR.

> Last verified state of this tree: run **41** green (`build` + `headless KWin capture`), `PROBE OK` locally
> on Plasma 6.6, ring-reader suite green, functional suite **165/165** — **152 before the
> non-normal-window work below, +13 checks** — after one flake that is now FLAKE-1 below. The desk is
> **one output at x1** since today, not the 75 %/125 % pair the v0.5.0 notes describe, which is why
> the count is 165 and why the fractional-scaling tests are running in their degenerate branches.
> `probe/nested_kwin_test.sh` also says **PROBE OK** with the new code, and inside a nested KWin
> `--list-windows --require-full` exits 0 — the scripting route works in the CI harness too, not
> only on a real desk (a bare nested session has no panel/desktop, so full == filtered there).

The `headless-kwin` job gets a nested KWin up inside `debian:trixie-slim` (`nested KWin: pid 8033,
socket kwcapture-test, output 1024x640`, and `list_monitors()` even answers `Virtual-0 (1024,640)`
over Wayland) and then *every* capture dies with

```
kwcapture: The name org.kde.KWin.ScreenShot2 was not provided by any .service files
         ; kwcapture: initial grab failed: No route to host
```

That is **not** an authorisation bug and not a kwcapture bug. Read out of the upstream source
(kwin 6.3.6 = what trixie ships; identical in 6.4 / 6.5 / 6.6 and master):

* `src/plugins/screenshot/screenshot.cpp` → `bool ScreenShotEffect::supported() { return
effects->isOpenGLCompositing(); }`. That effect is the **only** owner of the bus name: its
constructor makes a `ScreenShotDBusInterface2`, which is what calls
`registerService("org.kde.KWin.ScreenShot2")` (`screenshotdbusinterface2.cpp`). No OpenGL
compositing ⇒ effect not loaded ⇒ **name never appears** ⇒ exactly the error above. The same
code also explains why an unauthorised call *raises* instead of returning black: different layer.
* `src/backends/virtual/virtual_backend.cpp` → `supportedCompositors()` adds `OpenGLCompositing`
**only if `findRenderDevice()`/`drmGetDevices2()` found a DRM node**; otherwise it offers
`QPainterCompositing` alone. A container has no `/dev/dri`, so `WaylandCompositor::createRenderer()`
logs `kwin_core: Configured compositor not supported by Platform. Falling back to defaults` —
which we now see in the CI log, and which is the *smoking gun* — and quietly composites with
QPainter. `kwin_wayland --x11` is no escape: `X11WindowedBackend` likewise only offers OpenGL when
DRI3 hands it a DRM fd (Xvfb has none).
* **Therefore the headless recipe needs a DRM render node, and no amount of Mesa env tinkering
can substitute for it** — the decision is taken on `drmGetDevices2()` before Mesa is asked
anything, so `LIBGL_ALWAYS_SOFTWARE=1` / `EGL_PLATFORM=surfaceless` / installing `libgl1-mesa-dri`
change nothing. (`--virtual`'s EGL backend in ≤ 6.6 is `EGL_PLATFORM_GBM_KHR` on that device,
see `virtual_egl_backend.cpp` — it genuinely cannot work without one.) Upstream even special-cases
**vgem** in `findRenderDevice()` ("prefer the primary node because gbm will attempt to allocate
dumb buffers"), i.e. KWin's own CI uses a *virtual* DRM node — that is the thing to get in CI.
Master (post-6.6) changed `supportedCompositors()` to `{OpenGLCompositing}` unconditionally with
the new `RenderDevice` abstraction, so a future KWin may do surfaceless llvmpipe with no DRM at
all; nothing released does today.
* **Measured on the runner itself (run 38, the first job that printed it):**
  `/dev/dri/card1` **exists** — driver **`hyperv_drm`**, `root:video`, and **no `renderD*` node**.
  A card node alone does not count for KWin (`nodeType = DRM_NODE_RENDER`, primary only for vgem),
  so even passing it in with `--device /dev/dri` does not buy the capture path. `vgem` and `vkms`
  are **not loadable** on the runner kernel (`6.17.0-1022-azure`): "Module … not found in directory
  /lib/modules/…" — they ship in `linux-modules-extra-<version>`, which the runner image does not
  install. The job now installs that package (if the archive still has the exact version) and
  retries `modprobe vgem`; KWin special-cases vgem precisely because dumb buffers need the primary
  node, so a vgem render/primary node is the thing that would make this work.
* **Run 39 answered that experiment too, and the answer is no:**
  `apt-get install linux-modules-extra-6.17.0-1022-azure` **works** (51 MB from
  azure.archive.ubuntu.com) and still `modprobe vgem → FATAL: Module vgem not found` — Ubuntu does
  not build `vgem`/`vkms` for the azure flavour at all. **Conclusion: a GitHub-hosted runner can
  never give KWin a render node**, so the ScreenShot2 frames are not testable there, period. What
  would work: a runner image/label with a real GPU, or a **self-hosted runner** on any KDE machine
  (that is the plan for the frames; the job needs nothing special — with a render node present it
  silently switches back to strict and tolerates nothing).
* **The CI proof, verbatim from the log** (`QT_LOGGING_RULES=kwin_core.debug=true`):
  `Configured compositor not supported by Platform. Falling back to defaults` → `Attempting to load
  the QPainter scene` → `QPainter compositing has been successfully initialized` → …
  `Effect is not supported:  "screenshot"`. Everything else in the job works with that compositor:
  the socket, `monitors: [('Virtual-0', (1024, 640))]`, `windows: 1 [('KCalc', (648, 513))]` — so
  window *listing* is not GL-dependent, only the frames are.
* **Upstream's own CI shortcut exists but is not usable for us:** since 6.5 (and in 6.6/6.7)
  `findRenderDevice()` starts with `if (qEnvironmentVariableIsSet("CI")) return
  RenderDevice::open("/dev/dri/card1");` — GitHub sets `CI=true`, so that would hand KWin the
  renderless hyperv node… but it is inside `#if !HAVE_LIBDRM_FAUX`, i.e. compiled out on any distro
  with libdrm ≥ the faux-bus release, and trixie's 6.3 does not have it at all. Do not build a plan
  on it.
* **So the CI job now states its own coverage honestly:** `probe/ci_headless_kwin.sh` asks "would
  KWin's `findRenderDevice()` find anything?" (render node, or a vgem primary via
  `/sys/class/drm/card*/device/driver`). Yes → strict, nothing tolerated. No →
  `KWCAPTURE_NESTED_ALLOW_NO_SCREENSHOT2=1`, which turns *only* the missing-ScreenShot2 failures
  into a printed `ENVIRONMENT LIMITATION` (socket, authorisation, output listing, window listing,
  client startup and every other `doctor` check still fail the job). A runner with a GPU — or a
  self-hosted KDE runner — automatically gets the strict job back.
* **Not the problem: PipeWire.** KWin logs `kwin_screencast: Failed to create PipeWire context`
in that container, and `screencast.so` is the *portal* screen-cast plugin. ScreenShot2 needs no
PipeWire: we hand KWin a **pipe** fd and `ScreenShotWriter2` writes the raw QImage into it from a
QThreadPool (that writer is also the origin of the benign `pipe is broken` line and of the
"KWin replies before the pixels arrive" fact). Do not add a `pipewire` package to the job chasing
that log line.
* **Second, independent bug in the same run:** the Qt **Wayland** QPA plugin is *not* in
`qt6-qpa-plugins`. Debian ships it as **`qt6-wayland`** (`.../qt6/plugins/platforms/
libqwayland-egl.so` + `libqwayland-generic.so`), so `QT_QPA_PLATFORM=wayland kcalc` aborted with
`Could not find the Qt platform plugin "wayland" ... Available platform plugins are: linuxfb,
vkkhrdisplay, eglfs, vnc, xcb, minimal, offscreen, minimalegl` — and note that `list_windows()`
returning `0 []` (not an error!) was the *correct* answer for a session whose only client died.
* Debugging lever for next time, cheap and decisive: `QT_LOGGING_RULES="kwin_core.debug=true"`
makes KWin say *why* (`Attempting to load the OpenGL scene` / `Driver does not recommend OpenGL
compositing` / `QPainter compositing has been successfully initialized`) instead of the one-line
warning. The probe now passes it when `KWCAPTURE_NESTED_KWIN_DEBUG=1`.
* Verified after reworking the probe: strict path still **PROBE OK** on this desktop (KCalc
  (640,508), 1024x640 screen frame, 640x480 window frame, doctor rc=0 ×3), and the tolerant path
  was exercised with `kwcapture` stubbed to raise exactly the CI error — exit 0 with
  `ENVIRONMENT LIMITATION` when allowed, exit 1 when not.

### How to run the headless job by hand (it is not GitHub-specific)

```
docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim bash /w/probe/ci_headless_kwin.sh
```

That is the whole CI job (KWin 6.3 + kcalc in trixie, kwcapture pip-installed, probe run with the
strict window requirement). On a Plasma box no container is needed at all:
`dbus-run-session -- bash probe/nested_kwin_test.sh`.


**Cost, measured (so nobody quotes "six seconds" without the rest of the sentence):** the probe's
own wall clock is **7.52 s** here, including its three `doctor` runs — but that is the *probe*, on a
machine that already has Plasma 6 and a render node. On a bare Debian trixie, Plasma 6 is
**248 MB of archives → 986 MB on disk → 437 packages** even with `--no-install-recommends`
(**36.1 s** of `apt` on a runner). No KDE *session*, no monitor and no GPU are needed — Plasma 6's
packages and any DRM render node are, and the six seconds starts after `apt` finishes.

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
* the helper is one C file (`kwcapture/native/kwcapture.c`, 1749 lines) + `kwcapture_shm.h` (103),
  a ~54 KB dynamically linked ELF; `ldd` = libc, glib/gio, libsystemd, libwayland-client;
* the only outbound connection in the source is `wl_display_connect(NULL)` — no sockets, no network
  code, no root, no portal; frames come from the shm ring KWin fills;
* KWin's authorisation is a plain `.desktop` file in `~/.local/share/applications` the user can read
  and delete (`_desktop.py`);
* the sdist carries the C source and `setup.py`/`_native.py` build it with `cc -O2 -std=gnu11` +
  pkg-config, so `pip install --no-binary=kwcapture kwcapture` needs no trust in us at all;
* the PyPI files for a release are the artefacts of that tag's public `release.yml` run.

## ARCHIVED into AGENTS.old.md (2026-10-08 — this file had grown to 81 KB)

Moved out **verbatim**, because they are session logs of *released* work whose conclusions are
already above, in `CHANGELOG.md` and in `README.md`. Nothing was deleted — the archive keeps the
reasoning and the dead ends — but this file is what a fresh session has to be able to hold in its
head, so read the two sections below (*SCALES*, *MONITORS & RESILIENCE*) instead of the nine that
used to be here:

* the nine `FRESH STATUS — 2026-10-07 …` sections (monitors, fractional scaling, resilience, and
  publishing 0.4.0 / 0.5.0). Durable conclusions distilled into **SCALES** and **MONITORS &
  RESILIENCE**; the publishing procedure itself is the *Release checklist*, which stayed.
* `NEW: kwcapture captures a KWin nobody is looking at (nested, headless, ~6 s)` — superseded by the
  headless-CI status at the top, which also carries the retraction of its "no DRM" claim (`0ce6feb`)
  and the measured costs.
* BUG-4's original three-session hunt. The conclusion, the fault rate, the decisive next experiment,
  the guardrails and BUG-4b **stay** in BUG-4; only the hunt moved.
* BUG-3 (two leaks on start/restart) — fixed and regression-tested in v0.3.x / v0.4.0. Its lesson is
  kept, as a Gotcha: *a fix with no test is a guess*.

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

## SESSION STATUS — 2026-10-08 ~23:50 — **DONE, PUSHED (`eb0bcae` on `main`) and CI GREEN: non-normal windows are visible and capturable (the Winamp case)**

> **Pushed 2026-10-09**: `e714acb..eb0bcae main -> main`; run 37866299569 — `build` and
> `headless KWin capture (Plasma 6, no GPU)` both **success**. **RELEASED as v0.6.0 on 2026-10-09**
> — see the FRESH STATUS at the top. The helper did change, so the wheel was rebuilt rather than
> reused, and both the GitHub assets and the PyPI files were re-verified after publishing.

> **Acceptance, on the user's own window:** `list_windows()` reports the 1041x662 Winamp dialog
> (`krunner_listed=False`, `window_type_name="dialog"`), `Capture(window=…)` streams it at ~7 ms a
> frame, the PNG is the window from the screenshot, and `active_window_id()` is unchanged before
> and after — nothing was raised, focused or moved. 165/165 functional + 37 ring-reader checks
> green, `PROBE OK` in the nested KWin, no script or file left behind in either session.
>
> Task: the last functional TODO below ("expose non-normal windows"). Repro on the desk right now:
> Winamp (wine, `winamp.exe`) has **two** X11 windows — `0x01e00001` 275x116
> `_NET_WM_WINDOW_TYPE_NORMAL` and `0x01e0000e` 1041x662 `_NET_WM_WINDOW_TYPE_DIALOG` (the big
> skinned one in the user's screenshot, `WM_TRANSIENT_FOR` set). `kwcapture --list-windows` shows
> only the NORMAL one.
>
> **Root cause, read out of the kwin v6.6.6 source** (fetched from
> `invent.kde.org/plasma/kwin/-/archive/v6.6.6/kwin-v6.6.6.tar.gz` — keep a copy under `/tmp`, it is
> the reference for every "does KWin expose X?" question):
> * `src/plugins/krunner-integration/windowsrunnerinterface.cpp` — every loop over
>   `Workspace::self()->windows()` skips `window->isUnmanaged()` **and** `!window->isNormalWindow()`.
> * `src/window.h:796` — `isNormalWindow()` is "NET::Normal or NET::Unknown non-transient". Dialog /
>   utility / dock / splash / desktop are all excluded, in every branch of `Match()`, so no query
>   string can reach them.
> * `src/plugins/screenshot/screenshotdbusinterface2.cpp:296` — `CaptureWindow` resolves its
>   argument with `workspace()->findWindow(QUuid(handle))`: **a uuid or nothing**, and `handle` is
>   `Window::internalId()`, which is `QUuid::createUuid()` (`src/window.cpp:62`) — random, so it
>   cannot be derived from the X11 window id.
> * `src/dbusinterface.cpp` — `getWindowInfo(uuid)` (uuid only; `getWindowInfo("0x…")`,
>   `getWindowInfo("winamp.exe")` and `getWindowInfo(caption)` all return an empty map — measured)
>   and `queryWindowInfo()`, which is the **interactive** "click a window" picker, not a query.
> * `supportInformation` again lists no windows (re-verified on 6.6.6), and there is no `/Tasks`,
>   no `windowIds` on `/VirtualDesktopManager`, nothing window-shaped on `org.kde.plasmashell`.
>   **Conclusion: the only API in Plasma 6 that reaches the full window list is the scripting one.**
>
> **The route (matches what the TODO guessed):** `org.kde.kwin.Scripting` at `/Scripting`
> (`src/scripting/scripting.{h,cpp}`) exposes `loadScript(filePath, pluginName) -> i`,
> `loadDeclarativeScript`, `isScriptLoaded`, `unloadScript` — **unauthenticated**, and `filePath` is
> a plain path, so nothing has to be installed under `~/.local/share`. The JS global `workspace` is
> `QtScriptWorkspaceWrapper`, and `windowList()` is literally `workspace()->windows()` — every
> window, unfiltered (`src/scripting/workspace_wrapper.cpp:477`). Plasma 6 has **no**
> `registerDBusAdaptor` anymore (grepped: zero hits), so a script cannot export a method — but
> `Script::callDBus(service, path, interface, method, args…, callback)` is **async** and can post
> the list back to us on *our own unique bus name* (`:1.NNN`, so nobody else can impersonate the
> reply). `Script::run()` early-returns while running, so re-triggering is load-once-per-query +
> `unloadScript`, not `run()` in a loop. `config()` is the script's own kwinrc group and JS only has
> `readConfig` — no accidental config writes.
>
> Probes: **`probe/kwin_script_enumerate.py`** (dbus_fast; owns a bus object, writes the JS to
> `$XDG_RUNTIME_DIR`, loads it, waits for the `callDBus` callback, unloads). **It works** — and
> so does the C port: `kwcapture --list-windows` now reports 9 windows instead of 6 (the Winamp
> dialog, the plasmashell desktop and the panel), and `kwcapture --window '{c5de347d-…}'
> --decoration` returns a 1041x662 frame of the Winamp window **while it is still behind
> Konsole** — checked by eye, not just by pixel statistics (98.5 % non-black).
>
> Implemented in `kwcapture/native/kwcapture.c` (the "full window enumeration" section):
> `collect_windows(bus, wins, max, all_types, why, whysz)` = the krunner pass plus
> `collect_windows_script()`, which writes a private 0600 script into `$XDG_RUNTIME_DIR`,
> listens on our own unique bus name (`sd_bus_add_object_vtable`, nonce-guarded),
> `loadScript(path, plugin)` → `run()` on `/Scripting/Script<id>` → waits ≤1500 ms →
> `unloadScript(plugin)` → `unlink()`. Measured: **load+run+reply ≈ 0.5 ms**, and any failure is
> a stderr note plus the old krunner list — never a failed call. New flags: `--normal-only`
> (skip the script route entirely) and `--require-full` (exit 3 when the full enumeration was
> unavailable — what `doctor` will use). `--window HANDLE` now also accepts a handle the runner
> list does not mention, validated with `getWindowInfo` (`window_handle_exists`): that alone
> fixes "cannot capture a window whose handle I already know". JSON gains `window_type_name`
> + `krunner_listed`; the table flags non-listed windows with `not-in-app-list,<type>`.
>
> **`probe/non_normal_windows.py`** is the user-facing reproducer for the original complaint: it
> lists the full and filtered lists side by side, captures **every** window KWin's own list hides,
> writes a PNG per capture, and asserts that focus never moved and nothing was left behind
> (`kwcapture-winlist-*.js` in `$XDG_RUNTIME_DIR`, or a `/Scripting/Script<N>` object still
> exported). On this desk: desktop + dock + the Winamp dialog, all captured, PROBE OK.
> **`probe/kwin_script_failure_path.py`** loads a deliberately broken script and checks the
> `Failed(nonce, reason)` channel reports the JS error instead of timing out.
>
> **Behaviour change to document:** with desktop/dock/dialog windows included, a *name* lookup
> can be ambiguous where it used to be unique (`--window winamp` matches both Winamp windows).
> That is the honest answer — the message lists the candidates and their handles, and
> `--normal-only` / `all_types=False` restores the old list.

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
  two-output desk (DP-1 75 % + HDMI-A-1 125 %) that the v0.5.0 notes describe — **165 now** that the
  desk has one output at 100 %, the +13 non-normal-window checks do not multiply with outputs, so
  172 there is arithmetic, not a measurement. `kwcapture monitors --measure-scale` before quoting a
  number; the
  per-output checks (`area_in="physical"` especially) are only meaningful with both a display scale
  and a scene scale that differ, and today's desk has neither (x1/x1 → the degenerate
  "one mapping only" branch).

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

The original three-session hunt — the symptom list, why every static search for it comes up empty,
the rejected fix attempts, and why we believed it was a race in our own zero-copy path — is archived
in `AGENTS.old.md` (*BUG-4: the original hunt*). It stays out of here deliberately: it is 6 KB of
reasoning about a fault now attributed to this box / numpy, and re-reading it misdirects anyone who
starts from the live conclusion above.

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
* **CI integration test against a real (headless) KWin — DONE in `.github/workflows/ci.yml`
  (`headless-kwin`, branch `ci/headless-kwin` + PR #1), with one hard limit: GitHub's runners have
  no DRM render node, so the job covers the nested session (KWin starts, Wayland socket, private
  D-Bus, desktop-entry authorisation, output listing, per-window listing, the Qt client) but not
  the frames themselves — see the FRESH STATUS at the top for why that is a hardware fact, not a
  bug.** Still open, and now cheap because the harness exists:
  * run the strict job somewhere with a render node: a **self-hosted runner** on this desktop, or a
    GPU-labelled runner. `docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim
    bash /w/probe/ci_headless_kwin.sh` already does it on any KDE machine without a runner.
  * test BUG-1 (minimised → stale frame) inside the nested session — minimise the KCalc from the
    probe and assert what comes back; nothing else in the repo can reach that state on demand.
  * test `scale=` handling: `kwin_wayland --scale` exists, so `KWCAPTURE_NESTED_SIZE` plus a scale
    knob in `probe/nested_kwin_test.sh` would re-verify the fractional-scaling conclusions on a
    compositor whose scale is known instead of whatever the desk happens to be set to.
* ~~Mark which listed window is *active*~~ **done in v0.3.0** — see finding #3
  (`Window.active`, `active_window_id()`, `--active-window-id`).
* `getWindowInfo` gives no pid — a `Window.pid` would need `/proc` matching by app id.
* ~~Expose non-normal windows — panels, desktop, overlays~~ **done, released in v0.6.0.** The
  guess in the old wording was right: a throwaway KWin script hands out the handles the
  krunner interface filters out (see the SESSION STATUS section and KEY FACTS → *Window
  enumeration*). `list_windows()` now returns them by default with `krunner_listed=False`
  and a `window_type_name`, `--normal-only`/`all_types=False` gives the old list, and
  `--window HANDLE` no longer insists that the handle came from krunner. What is *not*
  done, on purpose: no script is installed under `~/.local/share`, nothing is kept loaded
  in KWin between calls, and there is no event/streaming API for window changes — every
  query pays its ~0.5 ms and leaves nothing behind.
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
