<!--
Thanks for contributing!

Two facts about how this project is tested are printed here because CI cannot tell you
either of them, and getting them wrong is the usual way a PR goes sideways:

  1. CI cannot prove that capture works. GitHub's runners have no DRM render node, so KWin
     never becomes OpenGL-compositing there and therefore never owns
     org.kde.KWin.ScreenShot2. A green run means "it builds, imports, and the shared-memory
     reader is sound" — nothing about frames. See README -> "How this is tested".
  2. If you changed the C helper, the shipped wheel does not change with your commit.
     The wheel is built from the tag; helper + wheel drift is the one bug class that only
     ever shows up after a release.
-->

First time here? [CONTRIBUTING.md](../CONTRIBUTING.md) covers setup, what you can do without a KDE
machine, and the house rules. Everything below is the part CI cannot check for you.

## What this PR changes

<!-- One paragraph. User-visible behaviour, API, CLI, or the helper<->client protocol? -->

## Native helper

- [ ] I did **not** touch `kwcapture/native/`
- [ ] I touched the helper, and I understand the release wheel has to be rebuilt, and that an
      old daemon (already running) can be paired with a new client — so any change to
      `include/kwcapture_shm.h` needs the protocol version (`KWC_VERSION`) and a thought about
      what happens to a mismatched pair.

## Testing

The functional suite needs a **real KDE Plasma desktop** (KWin on Wayland). CI runs only the
ring-reader suite plus a build/import smoke test.

```
make && .venv/bin/python -X dev tests/test_kwcapture.py   # needs a Plasma desktop
.venv/bin/python -X dev tests/test_ring_reader.py         # no compositor needed
```

- [ ] Functional suite passes on a real desktop — Plasma/KWin version: ________, outputs and
      scales: ________
      (the check count follows the hardware: 165 on one output at 100 %, 172 on a 75 % + 125 %
      pair — say which you ran, not how many passed, if you are not sure)
- [ ] Ring-reader suite passes — this is the only automated coverage the zero-copy read path
      gets on machines without a compositor, so it is not optional
- [ ] Docs only, no code touched

## Compatibility

`kwcapture` is shipped as the **optional** KDE capture backend of
[nunif](https://github.com/nagadomi/nunif) (`iw3-desktop`), which must stay optional and
must not get heavier. So:

- [ ] `import kwcapture` is still cheap — no new hard dependency, no import-time work, no
      install-time step, nothing that requires a compositor or a compiler to be present
- [ ] The API surface that downstream calls still behaves:
      `Capture(monitor=…)` / `Capture(window=…)` with `cursor=` and `shm=`, `grab(copy=True)`,
      `geometry()`, `list_monitors(measure_scale=True)`, `list_windows()`, `find_window()` +
      `AmbiguousWindow`, `unique_shm_path()`, `effective_scale` / `area_scale`
- [ ] Any behaviour change is called out below **and** in `CHANGELOG.md` — a change to what a
      window *name*, a *handle*, or an `area=` rectangle resolves to is a breaking change for
      callers, even when it is an improvement

## Behaviour changes

<!--
Be loud here. Examples of the shape that matters: v0.6.0 made `list_windows()` return dialogs,
panels and the desktop, so a name that used to match exactly one window can now match its
dialog too and raise `AmbiguousWindow`. Callers need that spelled out, not buried in a diff.
-->

## Housekeeping

- [ ] `CHANGELOG.md` has an entry under *Unreleased* (version numbers are bumped at release
      time, not per PR)
- [ ] `README.md` updated if the API, CLI or install story changed
- [ ] No non-source files in the repo: logs, captures, screenshots, transcripts and dumps go in
      `private/` (gitignored); check `git add -A --dry-run` before you commit
- [ ] No secrets, tokens or machine paths that only exist on my desktop

## Notes for the maintainer

<!-- Anything you tried that did not work, suspected flakes (there is a known one in the
     area_in='physical' check when the screen is animating), or hardware you could not test. -->
