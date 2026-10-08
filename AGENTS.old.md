# AGENTS.old.md — archived detail from AGENTS.md

> Archived 2026-10-06 when AGENTS.md was slimmed down. **History and reasoning only —
> nothing here is pending work.** Active guidance and open bugs live in `AGENTS.md`.

## FORENSICS — recovering a lost finding after a session died

Checked 2026-10-06 when a fatal bug from an earlier session had to be reconstructed:

* **Agent transcripts are NOT on disk here** — no `~/.claude`, `~/.codex`, or similar; a
  full-tree grep for "kwcapture" outside the repo found only pip wheel-cache metadata. So
  the previous session's tool calls and tracebacks are **unrecoverable**. Assume it.
* **`/var/crash/*.crash` (apport) DOES survive** and is gold: it recorded
  `Signal: 7 (SIGBUS)`, `ProcCmdline: .venv/bin/python tests/test_kwcapture.py quick` and
  the full `ProcMaps` showing the truncated `kwcapture-*.shm` mappings — hard evidence of
  the stale-ring crash at 18:30. Read it with
  `grep -aE "^(ProblemType|Signal|Date|ProcCmdline)" /var/crash/*python*.crash`.
* **`/tmp` scripts can survive** — `/tmp/repro.py` (daemon kill + restart) was still there
  and ran; it is what led to BUG-3. But `/tmp` is volatile: copy anything valuable into
  `probe/` immediately.
* **`__pycache__` is NOT useful** — it had already been regenerated, so no bytecode
  snapshot of the earlier source survived. Site-packages copies in old `/tmp/wt*` venvs
  were the same content as git (one was 0.1.0, useful only as a version snapshot).
* **Git history is the best source for code**, useless for anything never committed: `git
  log --all -S "<symbol>" -- <file>` showed the `sched_yield` block unchanged since the
  initial release, which is how we know that bug was never in the committed tree.

### Smaller things noticed while reading the code (unverified / judgement calls)

* `Window.maximized` is `maximizeHorizontal && maximizeVertical` (`kwcapture.c`, the
  `"maximized"` JSON field). KWin 6 **tiles** by maximising one axis only, so a
  left-tiled window reports `maximized: False` and the per-axis information is thrown away.
  Probably should be `maximized_h`/`maximized_v` on the dataclass (additive, non-breaking).
* `h->window` in the ring header is only ever written when `meta.window[0]` is non-empty
  and is **never cleared**, unlike `h->screen` which is cleared every frame (the
  `snprintf(h->screen…)` / `snprintf(h->window…)` pair in `advance()`). Benign today
  because a daemon's target never changes, but it means a failed frame keeps reporting the
  old handle — asymmetric and waiting to surprise someone.
* `Capture.screen` is the **requested** output from the constructor (None = active) while
  `Capture.screen_name` is what KWin actually answered. Two similar names, different
  meanings; `stats()['screen']` is the actual one. Easy to misread.
* Passing an **explicit** `shm=` that two `Capture` objects share still reproduces the old
  SIGBUS (the unique-path fix only applies when you do *not* pass `shm=`).

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
crop the result (KWin renders that window's item, not the screen region).

**But read *BUG-1* at the top of this file before you capture a minimised window:** it
"captures" only in the sense that bytes come back — they are a **stale frozen buffer**,
identical on every grab, with no error and no flag. The old wording here ("a minimised
window still captures — KWin keeps its buffer") was true-but-misleading and is exactly how
this stayed hidden. Likewise "occlusion does not crop" was verified for *geometry* only,
never for *liveness*.

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
  manylinux/musllinux. So the `linux_x86_64` wheel built here goes on the GitHub release
  only, and the PyPI wheel must come from cibuildwheel. **Since v0.3.0 the CI-built
  manylinux wheel is uploaded to PyPI too** (download it off the release with `curl -sL` and
  `twine upload -r pypi` it — that works and avoids needing PyPI credentials on the runner).
  auditwheel must be told `--exclude libsystemd.so.0 --exclude libwayland-client.so.0`
  (we intentionally do not vendor the compositor libs).
* Force-pushing a rewritten history needs `git push --force` — `--force-with-lease` said
  "stale info" because `git filter-branch --all` had rewritten `refs/remotes/origin/main`
  too. `git fetch` first, then force-push.
* A tag push runs the workflow **from the tag's commit**, so `release.yml` fired when I
  re-pointed `v0.1.0`; publishing is opt-in (`workflow_dispatch` + `publish: true`) so it
  cannot push anything to PyPI by accident.

---

## SESSION STATUS — 2026-10-06 21:50 (read this if you just woke up)

**v0.3.0 is FULLY SHIPPED: code, tag, GitHub release (3 assets + notes), PyPI sdist *and*
the first prebuilt manylinux wheel we have ever published.** Nothing is pending. The tree
is clean and `main` is pushed. Start from *Ideas not done yet* if you want new work.

**FIRST READ *OPEN BUGS* (right below SESSION STATUS).** BUG-1 (minimised windows return a
stale frame with no error) was known to two earlier sessions and never written down —
re-deriving it cost a whole investigation. If you add anything this session, add it there
the moment you see it.

**BUG-4 is the fatal one** (flaky `TypeError: 'int' object is not callable` + segfault in the
zero-copy read path). Recovered from the user's saved transcript (now at `private/chat_his.jsonl`, was
`chat_his.jsonl` in the repo root — see *Repository hygiene*); it is NOT
a typo and no static search will ever find it. Read that entry before debugging anything
that looks like a weird int/Slot_Array error in grab()/latest().

* **PyPI**: `0.3.0` = sdist + `py3-none-manylinux2014/2_17/2_28_x86_64` wheel (so
  `pip install kwcapture` needs no compiler now); `0.1.0`/`0.2.0` are sdist-only.
* **GitHub**: release `v0.3.0` (id 404767000) with the manylinux wheel + sdist (from CI)
  and `kwcapture-0.3.0-py3-none-linux_x86_64.whl` (built here, attached via the REST API),
  plus release notes. **`v0.2.0` has no GitHub release** — its run died on the broken
  workflow; the fix landed after the tag, so `v0.3.0` was re-pointed twice while iterating
  (`git tag -f` + `git push -f origin v0.3.0`). The v0.2.0 sdist on PyPI came from
  `61d06df`; the v0.3.0 GitHub sdist from the final tag commit `fbeff87`.
* **THE THREE REASONS `release.yml` HAD NEVER SHIPPED A WHEEL — all fixed, all verified
  green in run 37472650403:**
  1. `pypa/cibuildwheel@v2.21.3` pinned `quay.io/pypa/manylinux_2_28_x86_64:2024.10.07-1`,
     **a tag that no longer exists** → `Error response from daemon: No such image`.
     Fixed: `@v4.3.0` (cibuildwheel is at 4.3.0; quay's newest tags are 2026.x).
  2. `CIBW_REPAIR_WHEEL_COMMAND` used **`{dest}`**; cibuildwheel 4 only substitutes
     **`{dest_dir}`**, so auditwheel created a directory literally called `{dest}`, wrote
     the wheel into it, and the run failed with "the repair step completed successfully but
     did not produce a wheel". (auditwheel also reports our wheel is eligible for
     `manylinux_2_17`.)
  3. The wheel is **`py3-none-<platform>`** — the helper is a *standalone executable*, not a
     Python extension module — so all six `CIBW_BUILD` interpreters produced **identically
     named** wheels that overwrote each other, and the smoke test's
     `dist/*cp312*manylinux*.whl` glob matched nothing. Fixed: build once (`cp312`), glob
     `dist/*-py3-none-manylinux*.whl`. **Do not "fix" this by adding interpreters back.**
* **CI workflow**: `workflow_dispatch` on `main` is now safe for testing the wheel build
  (the GitHub-release step is gated on `startsWith(github.ref, 'refs/tags/v')`); its output
  is only the `dist` artifact. A single-build run takes **~4 min**; the six-interpreter one
  took ~18 min.
* **PyPI publishing is still manual** (`twine -r pypi`, credentials in `~/.pypirc`): the
  workflow's `publish` job needs `workflow_dispatch` + trusted publishing/`PYPI_API_TOKEN`,
  which is not configured. Setting that up would remove the last manual step.
* Verified `0.2.0`/`0.3.0` local wheels in throwaway venvs from `/tmp`: 159/179 ms startup,
  39.5 fps full-screen, per-window grab, `Window.active` correct, CLI works. 68/68 checks
  pass on the desktop.
* **v0.3.0 = focus tracking**, verified: full suite **68/68 PASS, 0 failures, 0 skips**
  (~35 s — the "~3 min" note below is stale). New: helper mode `--active-window-id`,
  `Window.active`, `active_window()`, `active_window_id()`, `list_windows(mark_active=…)`,
  `kwcapture windows -a/--no-active`.
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
* **DONE already**: cibuildwheel pin fixed; `ci.yml` green on `2c0118a`; v0.3.0 artefacts
  built locally and sanity-tested in a throwaway venv from `/tmp` (179 ms startup, 5 windows
  listed, `Window.active` correct, `active_window()`/`active_window_id()` correct, focused
  window grabbed 698x548); v0.3.0 sdist twined to PyPI; `v0.3.0` tagged and pushed.
* **How to poll a CI run** (learned the hard way): the *job* log is available as **plain
  text** at `.../actions/jobs/<job_id>/logs` but only **after the job finishes** — while it
  runs it returns `BlobNotFound` XML. So poll `.../actions/runs/<id>/jobs` for step
  statuses. `/actions/runs/<id>/logs` is a **zip**. `exec_shell_command` caps at 60 s, so
  `sleep 50` per poll.
* **Attaching a release asset**: `POST https://uploads.github.com/repos/tjandrasg/kwcapture/releases/<id>/assets?name=<file>`
  with `Content-Type: application/octet-stream` + `--data-binary @file` → 201; notes via
  `PATCH /repos/.../releases/<id>` with `{"body": …}`.
* Housekeeping: repo-root `bin/kwcapture` is **stale v0.1.0 debris** (gitignored, *not* on
  `_native`'s search path — the real helper is `kwcapture/bin/kwcapture`).

**Next useful features** (see *Ideas not done yet*): `Window.pid`, auto-restart of a dead
daemon inside `grab()`, and non-normal windows (panels/desktop) via a KWin script.

---

# ARCHIVE — moved out of AGENTS.md on 2026-10-08 (the working file had grown to 81 KB)

**History and reasoning only — nothing below is pending work.** The live conclusions are in
`AGENTS.md`; its *ARCHIVED into AGENTS.old.md* section is the map of what moved and where the
distilled facts ended up (SCALES, MONITORS & RESILIENCE, the Gotchas, the Release checklist).

## The nested `kwin_wayland --virtual` discovery, as originally written

Kept because the technique and the private-bus finding are the interesting part — but read the
correction at its top first: its "no DRM" claim is wrong and was retracted in `0ce6feb` (a DRM
render node is required, which is why the frames cannot be captured on a GPU-less CI runner).

### NEW: kwcapture captures a KWin nobody is looking at (nested, headless, ~6 s)

> **CORRECTED the same evening — two things written here (and in commit `2334a04`, which said
> "`--virtual` … no DRM, no X server, no GPU") were over-claimed, and CI is what proved it.**
> No X server, no monitor, no GPU *session*: still true. **"no DRM": false.** KWin's `--virtual`
> backend offers OpenGL compositing only if `drmGetDevices2()` finds a device, and ScreenShot2 is
> registered only while KWin is OpenGL-compositing — so **a DRM render node is mandatory for the
> frames** (see the FRESH STATUS at the top: `/dev/dri/renderD128` on a normal desktop, a vgem node,
> or nothing at all on a GitHub runner, where the whole capture path therefore does not exist).
> It looked true here because this machine has a render node, so the requirement was invisible.
> And "in about six seconds" is the **probe's own runtime** (re-measured: **7.52 s** wall, including
> its three `doctor` runs), not the cost of getting there: on a bare Debian trixie box, Plasma 6 is
> **248 MB of archives → 986 MB on disk → 437 packages** even with `--no-install-recommends`, i.e.
> another ~40 s of `apt` before the 6-second part starts. So the honest one-liner for a downstream
> tester (nagadomi and anyone else without Plasma) is: *no KDE session, no monitor and no GPU
> needed — but Plasma 6's packages and any DRM render node are.* See
> `probe/ci_headless_kwin.sh` / README "How this is tested".

`probe/nested_kwin_test.sh` + `probe/nested_kwin.py` (both verified today on Plasma 6.6 / KWin
6.6.6). This is the answer to "how do you test the KDE path without KDE hardware" — and therefore a
real CI path, see *Ideas* below.

```
dbus-run-session -- bash probe/nested_kwin_test.sh
  monitors: [('Virtual-0', (1024, 640))]
  windows: 1 [('KCalc', (640, 508))]
  screen grab: (640, 1024, 4) mean B/G/R = [22.0, 20.4, 19.0] max = 255
  window grab: (480, 640, 4) 5.7 ms  mean B/G/R = [43.4, 40.1, 37.3] max = 255
```

* Recipe: `kwin_wayland --virtual --socket <name> --width W --height H --no-lockscreen
  --no-global-shortcuts` renders to a **virtual framebuffer** (`QT_QPA_PLATFORM=offscreen` works, no
  X server, no GPU); a client started with `WAYLAND_DISPLAY=<name>` shows up in `list_windows()` and
  is capturable per window; the desktop-entry authorisation applies unchanged.
* **THE GOTCHA THAT MAKES OR BREAK IT: `dbus-run-session` is mandatory.** ScreenShot2 is reached
  over the session bus as part of `org.kde.KWin`, and the desktop KWin owns that name. Measured on
  the *desktop* bus with a nested KWin at 1024x640: `list_monitors()` → the nested `Virtual-0
  (1024,640)` (that follows `WAYLAND_DISPLAY`), but `list_windows()` → the **desktop's** 5 windows
  and `grab()` → **2560x1440**, the real screen. Silent split-brain: a test would assert against
  the developer's desktop. On a private bus the nested KWin owns the name and every answer is its
  own. `nested_kwin.py` asserts the frame size for exactly this reason.
* Interpreting a failure: **all-black frame of the right size** = the nested session is empty (start
  a client in it); **frame at the other size** = you captured the other compositor (no private bus).
* **FIXED same day — the `doctor` false alarm is gone.** It used to report
  `FAIL: capture returned an all-black frame` (exit 1) on an empty session, which is exactly what a
  *correct* capture of nothing looks like. Now: black + **0 capturable windows** → `warn`, exit 0;
  black **with windows** → still `FAIL` (locked/DPMS/not compositing — note that a missing
  authorisation *raises*, it does not return black, so this is never an auth symptom); and
  `--allow-black` accepts it unconditionally for CI. Verified on a nested session: empty → rc 0,
  empty + `--allow-black` → rc 0, with KCalc → rc 0; host session unchanged; suite still 159/159.
  `probe/nested_kwin_test.sh` runs doctor three times (empty, empty+flag, with client) so the
  heuristic cannot rot back, and prints `PROBE OK` + a single exit code.
* Benign noise, not bugs: KWin logs `kwin_screenshot: ... pipe is broken` when the helper exits with
  a request queued; `qt.qpa.services: Failed to register with host portal`, `kf.globalaccel…`,
  `fusermount3: failed to access mountpoint /run/user/1000/gvfs: Permission denied` and the
  `dbus-daemon` portal activation spam all appear under `dbus-run-session` and mean nothing.
* ⚠️ **`pkill -f "kwcapture/bin/kwcapture"` kills your own shell** (the pattern matches the `sh -c`
  command line that contains it) — the command dies with no output and the heredoc after it never
  runs. Resolve pids first and `kill` them, or split the pattern (`"kwcapture/bin/kw""capture"`).
  Same trap as `pgrep -c -f "kwin_wayland --virtual"`, which counts itself.


## Session logs — 2026-10-07 (v0.4.0 and v0.5.0 work)

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


## BUG-4: the original hunt (the conclusion itself stayed in AGENTS.md)

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


## Closed: BUG-3, two leaks on start/restart

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

