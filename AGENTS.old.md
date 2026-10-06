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
