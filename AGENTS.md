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
Python API + CLI + 60 functional checks. See `README.md` for user-facing docs; this file
is the investigation log + gotchas.

## FRESH STATUS — 2026-10-06 ~23:05 (this is the current truth)

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

### BUG-4 (THE FATAL ONE, unfixed, flaky): memory-safety race in the zero-copy read path

**This is the bug earlier sessions kept hitting and never writing down. It is NOT a typo and
it is NOT statically findable — `'int' object is not callable' is a memory-corruption
symptom here, not a name error.** Reconstructed 2026-10-06 from the previous session's saved
transcript (`chat_his.jsonl`, lines ~349–381); that session died mid-bisect without a root
cause. If you are staring at a mysterious `int`/`Slot_Array_4`/segfault in `grab()`/`latest()`,
**read this whole entry first.**

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
* **Fix directions** (none applied yet):
  1. **APPLIED**: `_view()` now snapshots `slots`/`hdr_size`/`slot_bytes` once up front and
     `_check_error()` reads `h.error` once (kills BUG-4b's `daemon error: Success`). Still
     open: `sl.*` fields are read more than once in places, and `status`/`format` should be
     snapshotted the same way. Verified: windows suite green, `latest(rgb=True)` at 460k it/s
     for 8 s with `-X dev`, no warning — but **this does not prove BUG-4 is gone**, it is
     flaky by nature; do not close this entry on a clean run.
  2. **TRIED AND REJECTED — do not repeat this exact attempt**: `arr._kwc_shm = (mm, hdr)`
     silently does nothing because these are numpy **views**, which reject new attributes;
     wrapped in `except AttributeError` it looked like a fix while `hasattr(arr,'_kwc_shm')`
     was False. numpy already keeps the buffer via `arr.base`. A real keepalive needs an
     `ndarray` subclass or an explicit registry. **General lesson: a fix wrapped in a broad
     `except` that never asserts anything is a placebo — verify the effect, not the intent.**
  3. Never mutate `self._mm`/`self._hdr` while views may be outstanding — or make `close()`
     explicitly invalidate them and document that outstanding views become invalid.
  4. Run the suite under `-X dev` + `PYTHONFAULTHANDLER=1` in CI with a stress target so
     this stops being invisible.

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
