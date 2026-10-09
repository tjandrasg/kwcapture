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

---

# ARCHIVED 2026-10-09 — the file had grown back to 77 KB

Moved **verbatim** out of `AGENTS.md`; the distilled summaries stayed there. Nothing deleted.
Both describe *released* work: the headless-CI job is on `main` and documented in README,
and the non-normal-window enumeration shipped in v0.6.0.

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

## BUG-1: the original analysis (moved 2026-10-09)

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

## BUG-2: sched_yield — full analysis (moved 2026-10-09)

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

## BUG-4: the bisect record, 2026-10-09 archive

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

## Completed "Ideas not done yet" bullets (moved 2026-10-09)

* ~~Mark which listed window is *active*~~ **done in v0.3.0** — see finding #3
  (`Window.active`, `active_window_id()`, `--active-window-id`).

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

* ~~If a non-KDE compositor is ever needed~~ **out of scope, deliberately.** The name is
  the promise: this project targets KDE Plasma, and `org.kde.KWin.ScreenShot2` is the only
  capture interface it will speak. `ext-image-copy-capture-v1`/`wlr-screencopy` are not on
  the roadmap — on a non-KDE compositor kwcapture should fail loudly, not grow a second
  backend.


## Community-files section, long form (moved 2026-10-09)

## COMMUNITY FILES — what is in `.github/` and why (deliberately incomplete)

`SECURITY.md`, `ISSUE_TEMPLATE/{bug_report,feature_request}.yml`, `ISSUE_TEMPLATE/config.yml`,
`PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`. All of it written for *this* repo rather than from
stock templates, because the useful content is project-specific: the bug form leads with
`kwcapture doctor` + Plasma/KWin version + session type (the domain's three real failure layers),
and the PR template states the two traps CI structurally cannot catch — **green CI ≠ capture
works** (no DRM node on hosted runners) and **helper changed ⇒ the release wheel must be
rebuilt** — plus the nunif constraint (import must stay cheap, no new hard dep) and the `private/`
rule.
* **Dependabot covers `github-actions` only, by design.** The release workflow is the reason:
  a stale cibuildwheel pin broke the v0.1.0 *and* v0.2.0 release runs (dated manylinux images get
  deleted from quay.io). No `pip` section — `numpy`/extras are deliberately unpinned, so bot PRs
  against open ranges are pure noise for a solo maintainer. There is an explicit `ignore` keeping
  cibuildwheel below 5 so a bot cannot "help" past a breaking major without a human reading
  `release.yml`'s comments first.
>
> **First cycle, banked (2026-10-09).** Dependabot opened PR #2 — checkout v4→v7,
> setup-python v5→v7, upload-artifact v4→v6, download-artifact v4→**v7**, one grouped PR, and
> **cibuildwheel correctly left alone** by the `ignore` rule. Squash-merged as `2ec83eb`, CI green
> on `main`. Then the part that matters: **a PR cannot run `release.yml`, so its own bumps were
> unverified by that green check** — rehearsed instead with `workflow_dispatch` at
> `publish: false` (run 37881396351): sdist + manylinux wheel built, ring-reader tests ran,
> `upload-artifact@v6` produced the `dist` artefact, the wheel smoke test printed `wheel ok 0.6.0`
> and `kwcapture 0.6.0`, while "Attach to the GitHub release" and the whole `publish` job were
> *skipped* — they are gated on `refs/tags/v*` and on the `publish` input, which is exactly why
> this dry run is safe to fire at any time. Keep the recipe, it needs no `gh`:
> `curl -X POST -H "Authorization: Bearer $TOK" -d '{"ref":"main","inputs":{"publish":false}}'`
> `…/actions/workflows/release.yml/dispatches`.
> **Still the one line with no coverage: `download-artifact@v7`**, which exists only in the
> `publish` job — the job this release process does not use (PyPI upload is local `twine` against
> the release assets, checklist step 5). Dormant, not proven: if trusted publishing is ever turned
> on, verify that step against TestPyPI first, never mid-release.
* **`CODE_OF_CONDUCT.md` was added on 2026-10-09, and the reason is not "the GitHub checklist".**
  What moved it is the same argument that made `SECURITY.md` worth writing: distributors read this
  checklist as evidence about how a project is run — nunif's maintainer said outright that the CI
  build counted as responsibility evidence and that shipping came down to trust (see DOWNSTREAM
  above). The objection that *survived* is that a code of conduct needs a real enforcement contact,
  because an unfilled `user@example.com` advertises a promise nobody keeps; that is satisfied by the
  maintainer's main email, published with his explicit consent, and it is the same address
  `SECURITY.md` carries.
  The file is **Contributor Covenant 2.1 fetched from contributor-covenant.org** and assembled by a
  script that *asserted* the body is byte-identical to the published text apart from the single
  contact substitution — so **do not hand-edit the covenant section**; regenerate it if upstream ever
  revises. It is preceded by a project-specific note that says the quiet parts out loud rather than
  hiding them: one maintainer is both contact and decision-maker, there is no committee and the file
  does not pretend there is one, and **a report about the maintainer himself goes to GitHub Support**,
  since he cannot adjudicate a complaint against himself. Enforcement is scoped to this project's
  spaces; nothing is retroactive. Consistency note: its "acknowledge within 5 working days" matches
  `SECURITY.md` — change one, change the other.
* **Still deliberately absent: Discussions, wiki, FUNDING, coverage/lint badges, and
  `ACCESSIBILITY.md`.** The first three are premature with no contributor traffic; a coverage or lint
  badge would point at a step that does not exist (the functional suite needs real hardware — a
  documented limitation, not a gap to paper over); and `ACCESSIBILITY.md`, which GitHub lists as an
  *optional* extra, would be theatre: no UI, no docs site, no interactive surface beyond Python and
  stdout, so the only honest content is "captured screen content inherits whatever accessibility the
  source application has" — a sentence, not a policy. Leaving that box unchecked is the accurate
  state.
* **Private vulnerability reporting is ENABLED** (2026-10-09, by hand: Settings → Code security and
  privacy → *Privately report a security vulnerability*), confirmed by a logged-out account seeing
  the "Report a vulnerability" button. Do not try to switch it on over the API — the
  `PATCH …/repos` call *accepts* a `private_vulnerability_reporting` key and silently does nothing
  with it, and `GET` never returns that key either, so the API cannot confirm or deny it here. The
  only reliable checks are the Security tab as an outsider, or filing a report. `SECURITY.md` links
  the form and also gives the maintainer's email as a fallback contact (his decision, 2026-10-09).
* **Validate the forms before pushing**: `yaml.safe_load` is not enough — every body item needs
  `type` ∈ {markdown,textarea,input,dropdown,checkboxes}, markdown items need `attributes.value`,
  the rest `attributes.label`, dropdowns ≥2 options, and `validations.required` must never appear
  on `checkboxes`.
