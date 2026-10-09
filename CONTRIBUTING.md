# Contributing to kwcapture

Thank you for considering it. This file is the onboarding version of "what I wish I had known":
how to get a working tree, what you can do without a KDE machine, where the code lives, and the
handful of rules that are not obvious from the code. User-facing documentation is in
[README.md](README.md); this file does not repeat it.

## Ten-minute setup

You need **KDE Plasma with KWin on Wayland** to run the interesting parts. Building needs a C
compiler plus `pkg-config`, `libsystemd-dev` and `libwayland-dev` (`sudo apt install build-essential
libsystemd-dev libwayland-dev` on Debian/Ubuntu).

```bash
git clone https://github.com/tjandrasg/kwcapture && cd kwcapture
python3 -m venv .venv
.venv/bin/pip install numpy pillow opencv-python-headless
                        # numpy is the only hard dependency. Pillow / OpenCV unlock the JPEG and
                        # fast-resize paths, so install them or those tests take slow fallbacks.
make setup            # build the helper into kwcapture/bin/ AND write the KWin authorisation entry
make doctor           # session, helper, authorisation, a real capture, optional extras
make dev-install      # pip install -e . so `import kwcapture` is this checkout
```

`make setup` creates `~/.local/share/applications/io.github.kwcapture-<hash>.desktop`. That is the
*whole* of KWin's authorisation for the restricted screenshot interface — a plain text file you
own. Remove all of them with:

```bash
.venv/bin/python -m kwcapture install-desktop --uninstall
```

`make` uses `./.venv/bin/python` by default; override with `PY=python3 make test` if you keep your
interpreter elsewhere.

## Running the tests

```bash
make test                                                     # functional suite (real desktop needed, ~35 s)
.venv/bin/python -X dev tests/test_kwcapture.py quick         # skip the slow colour-reference check
.venv/bin/python -X dev tests/test_kwcapture.py windows       # the per-window capture section only
.venv/bin/python -X dev tests/test_ring_reader.py             # shared-memory protocol, NO compositor
.venv/bin/python -X dev tests/test_ring_reader.py quick       # shorter concurrency race
.venv/bin/python -m pytest tests/                             # both suites collect fine too
```

Use `-X dev`: it turns on the warnings that have caught real problems here (undeclared ctypes use,
resource warnings). Two things about the numbers:

* **The check count depends on your hardware.** The per-output checks multiply: 165 on a single
  output at 100 %, 172 on a 75 % + 125 % two-monitor desk. When you report a result, say what you
  have (`kwcapture monitors --measure-scale`), not just the number.
* **The functional suite launches and closes its own windows** (`kcalc`) and grabs your real
  screen. Close anything you would not want in a screenshot before running it.

## No KDE machine? You can still contribute

This is the question most often asked and the answer is better than it looks — because **CI cannot
verify frames either** (see below), so your laptop is not uniquely disqualified.

* **No compositor needed at all:** `tests/test_ring_reader.py` — 37 checks of the shared-memory
  protocol against a synthetic ring: invalid descriptors, torn frames, a concurrent writer,
  bounds-checking of frame geometry before it becomes an offset. This is real coverage of the
  zero-copy read path and it runs anywhere.
* **Nested compositor, no monitor / GPU / login session:**
  `dbus-run-session -- bash probe/nested_kwin_test.sh` starts `kwin_wayland --virtual` inside a
  private D-Bus session, puts a client window in it and drives a full capture against it (~6 s on
  Plasma 6.6). Or, on any Linux box with Docker:
  `docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim bash /w/probe/ci_headless_kwin.sh`.
* **No hardware needed at all:** docs, CLI wording, packaging, and Python-side refactors covered by
  the ring-reader suite.

**The honest caveat, so you don't chase it:** on a machine with no DRM render node, KWin does not
become OpenGL-compositing, and while it is not, it does not own `org.kde.KWin.ScreenShot2` at all —
so the harness starts, sockets, authorises and lists windows, but frames are unavailable. That is
why the CI job prints `ENVIRONMENT LIMITATION` instead of failing, and why **a green CI run is not
evidence about capture**. Details in README → *How this is tested*.

## Where things are

| path | role |
|---|---|
| `kwcapture/native/kwcapture.c` | the native helper: D-Bus, KWin, the ring writer. **One C file on purpose** — see house rules |
| `kwcapture/native/include/kwcapture_shm.h` | the shared-memory protocol: `KWC_MAGIC`, `KWC_VERSION` (currently 2) |
| `kwcapture/__init__.py` | public API, `Capture`, the zero-copy ring reader, frame validation |
| `kwcapture/_native.py` | finds the shipped helper or builds it from source |
| `kwcapture/_desktop.py` | the KWin authorisation entry: install / uninstall / prune stale ones |
| `kwcapture/__main__.py` | the `kwcapture` CLI |
| `tests/` | the two suites described above |
| `probe/` | standalone reproducers and measurement tools. **A bug repro belongs here, not in `/tmp`** |
| `AGENTS.md` | the working log: investigation notes, gotchas, the release checklist, and an *OPEN BUGS* section. Not written as onboarding — read the gotchas before touching the shared-memory protocol |

## House rules

These are the ones that have actually caused rework, not a style guide:

* **`import kwcapture` must stay cheap.** No new hard dependency, no work at import time, no
  install-time step, nothing that needs a compositor or a compiler merely to import. `kwcapture` is
  shipped as the *optional* KDE capture backend of
  [nunif](https://github.com/nagadomi/nunif) (`iw3-desktop`); that arrangement is conditional on it.
* **The helper stays one C file.** Every library it links has to exist on every machine that
  installs it — that is why it depends on nothing beyond `libc`, `libsystemd` and
  `libwayland-client`.
* **Change the protocol header, bump `KWC_VERSION`** — and reason about the mismatched pair,
  because a daemon that is *already running* gets paired with your new reader.
* **A fix without a test is a guess.** Several bugs here were "fixed" once and came back; the ones
  that stayed fixed have a check in `tests/`.
* **Non-source files go in `private/`** (gitignored): logs, captures, PNGs, transcripts, scratch
  notes. Run `git add -A --dry-run` and read it before committing.
* **`CHANGELOG.md` gets an entry under *Unreleased***. Version numbers are bumped at release time,
  not per PR.
* **Python ≥ 3.9** (`requires-python`), so no `match` statements or 3.10+-only syntax.
* **Participation in this project's spaces is covered by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).**
  Contributor Covenant 2.1, with a note at the top saying how it is actually applied here: the
  maintainer is both the contact and the decision-maker, reports go to the address in that file, and
  enforcement reaches this project's spaces only.
* Please don't reformat or rename unrelated code — it buries the change that is the point.

Contributing implies licensing your contribution under the project's MIT license; say so if that
is a problem before you start work.

## Before opening something big

If it adds a feature rather than fixes one, **open an issue first** — especially if it might need
something other than `org.kde.KWin.ScreenShot2`. Compositors outside KDE are out of scope by
design, and it is much cheaper to find that out in an issue than after you have written the code.

When you do open a pull request, the template asks two questions CI cannot answer for you. Both
are cheap to answer honestly and both have been the cause of a bad release somewhere before.
