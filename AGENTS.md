# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

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
assets / PyPI sdists never contained it — **but GitHub kept serving the old commit objects**
(`raw@5391a52` returned HTTP 200 with the full file after the purge), so it was only gone
after GitHub Support removed it. **Force-pushing is NOT deletion on GitHub** — at the time of writing
`https://raw.githubusercontent.com/.../5391a52/chat_his.jsonl` still returns the full file,
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

### BUG-1 (confirmed, silent wrong output): a **minimised window captures a STALE frame**

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
* **Fix** (small, safe, and it kills the AttributeError crash regardless of the int story):
  catch `(OSError, AttributeError)`, keep the fallback a real named function, and guard the
  cache with `if not callable(_sched_yield)` instead of `is None` so a cached non-callable
  can never be invoked. **APPLIED** (commit after this one): all three branches verified —
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

### BUG-3 (fixed): fd + log-file leak on every start attempt / restart

`_start_once()` reset `self._log_file = None` and then opened a fresh `<shm>.log`, dropping
the handle from the previous attempt without closing it. `_start_once()` runs on **every**
authorisation retry (the backoff loop can fire 5 times) and on every `restart()`, so a
long-lived process leaked fds. Found by running the *previous session's* leftover
`/tmp/repro.py` (daemon `SIGKILL` + `restart()`) under `python -X dev`, which reported
`ResourceWarning: unclosed file <_io.TextIOWrapper ... shm.log>` at the reset line. Fixed by
closing the old handle first; the ResourceWarning is gone.
**`-X dev` is worth running on the suite** — it surfaces resource bugs that are otherwise
silent. (It also surfaced BUG-2's neighbourhood.)

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

## Goal
Make a **fast** full-screen capture program on Wayland. Original experiments
(`probe/bench_original.py`, `bench_result.md`): `PIL.ImageGrab` shells out to `spectacle`
(~2 fps); `mss` is 1100 fps but captures **XWayland** (black for native Wayland windows)
and dies when `$DISPLAY` is unset. Both unusable.

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
