# logo/AGENTS.md — the kwcapture mark

Work on `logo/` only after reading this. Everything here was paid for once already.

Three files, three jobs. **This one is the working set**: the rules, the knobs, the numbers
and the open items. [`README.md`](README.md) is the user manual for the three programs and
the directory, with renders. [`AGENTS.old.md`](AGENTS.old.md) is the archive: the session
log, the falsified claims, the war story behind every gotcha.
[`LICENSE.md`](LICENSE.md) says what you may do with any of it.

> **Size discipline** (the root `AGENTS.md` says the same). This file is **108 525** bytes
> — measured with `wc -c logo/AGENTS.md`, not remembered. **Round 14** (the palette round) opened at
> **96 404** and closes at the number above. It paid for itself once, by moving Round 13's
> session-log narrative out **verbatim** — 7 327 bytes, presence in
> [`AGENTS.old.md` Part J](AGENTS.old.md) asserted by string search *before* the pointer replaced it,
> the way Parts G/H/I were done — and still grew, because a recolour round spends its budget on
> *proof*: a verified block, the corrected two-grounds arithmetic, the trade the palette made, a new
> gotcha (**40**: a check keyed on a colour *literal* goes blind quietly), and re-measured numbers
> throughout. That is what the round sells, so that is what it costs. The debt passes on, with one
> new candidate: the P2 decision history under *Still open* is now a **closed** decision and belongs
> in the archive the next time this file is trimmed. It was **86 077** before Round 10's
> archive-verbatim pass, which moved 45 KB of narrative to `AGENTS.old.md` and lost nothing
> (every substantive line of the old file is present in one of the two files — checked, not
> asserted; the archive's header carries the sha256 it was cut from); **59 077** when Round 11
> opened, and **69 298** at its close. The icon round spent ~10 KB on `icon/` — two Files rows, the
> regenerate commands, five gotchas, a block of expected numbers — and paid part of it straight
> back by moving Round 10's session-log narrative (2 029 bytes, verbatim) to
> [`AGENTS.old.md` Part G](AGENTS.old.md). **Round 12** (the desktop-icon round) opened at
> **69 298** and closes at **76 584**: ~5 KB went on `sync_package_icons.py` (a Files row, the
> regenerate commands, gotchas 36–37, the package-set expected numbers) and its log entry, and the
> payment was moving Round 11's narrative (3 019 bytes, verbatim) to
> [`AGENTS.old.md` Part H](AGENTS.old.md) — asserted present in the archive *before* the summary
> replaced it, the same way Round 10's pass was done. **A round that adds narrative also moves one
> out.** **Round 13** (the one-artwork round) opened at **76 584** and closes at **96 404**, and it
> did *not* pay for itself: it moved Round 12's narrative out (4 070 bytes, verbatim — the moved
> block's sha256 starts `cddb1ce7cb55b311`, and its presence in
> [`AGENTS.old.md` Part I](AGENTS.old.md) was asserted by string search *before* the pointer
> replaced it) and still grew by 19 820 bytes, because a round about *why a build script was not
> allowed to pick the artwork* spends its budget on reasoning: a verified block, gotchas 38 and 39,
> the Files/Still-open corrections and its own log entry. The debt is the next round's, and the two
> fattest candidates are the `icon/` expected-numbers block and Round 10's verification prose —
> which is exactly what this note has always said to do, and has always been slow to do.
> The failure mode is
> real: a note here once claimed 62 KB while the file was already 72, and the number in
> *this very note* was the stale one until it was recomputed. When a round finishes:
> **move its narrative to `AGENTS.old.md` verbatim and leave a pointer here**; distil the
> substance into the knob table / gotcha index / expected numbers; do not append forever, and
> do not correct history here. Precedents: Round 6's pass upstream (root `AGENTS.old.md`,
> 77→54 KB), Round 10's split of this file, and Round 11's Part G.

> **Verified 2026-10-11 (Round 10), on this machine, by running it — not by reading the
> last person's note:**
> `gen_logo.py`, `--mark` and `--monogram` regenerate all three SVGs **byte-identically**
> (`cmp` against the files on disk, 3/3); `xmllint --noout` is clean on all five SVGs;
> `validate_logo.py` prints **OK** for `kwcapture-mark.svg` and `kwcapture-mono.svg`, and
> for `kwcapture.svg` **whenever `box_check` does not crash** (it crashes intermittently —
> gotcha 29, and it is not fixed); `render_agreement.py` **exits 1 on purpose**, with MSVG
> off by 26 px on `kwcapture.svg` and 67 px on the mark, correct everywhere else — gotcha 27
> is still true. The mark is two-colour, **KW green / Capture blue** (*The colour split*),
> and its type is **stretched ×1.753 across the baseline** to fill the helper box (*The
> height fill*; *The box is four mouse clicks* explains why that is not 1.784).
> `gen_logo.py` now **refuses** a paint variant pointed at a shipped path (verified: exit 1,
> file untouched), so the old "the habit is the guard" line is obsolete.
> The two caveats above are the honest part: a doc that says "everything prints OK" about a
> tool that intermittently crashes is how Round 9b died.
> *Round 14 annotation, same policy as Round 13's: `kwcapture-mono.svg` no longer exists, so that
> command list is now two shipped SVGs plus a monogram rendered to `/tmp`. Everything else in this
> block — byte-identical regeneration, `xmllint` clean, `render_agreement.py` exiting 1 on purpose
> — was re-run on palette P2 on 2026-10-11 and reads as written.*

> **Verified 2026-10-11 (Round 11 — the icon round), by running it.** The owner chose
> **`kwcapture-mark.svg` as the official logo of the project**, and `icon/` is the shipped icon
> set built from it. `gen_logo.py --mark` reproduces `kwcapture-mark.svg` byte-identically, and
> `gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg --out icon/kwcapture-mark-mono.svg`
> reproduces the glyph form byte-identically (`cmp`, both); `validate_logo.py` prints **OK** on
> that glyph (colour split 100 % on ink, render 42.3 % blue); `bash icon/build.sh` rebuilds all
> **23 images** in `icon/` and `bash preview/build.sh` every README image, the new
> `preview/ladder-icon.png` included. Every number quoted by `README.md` §8 was measured on this
> machine for that round, not copied: blue `#0000ff` **2.20:1** on `#0d1117` / **8.59:1** on
> white, green `#00ac4e` **6.32:1** / **3.00:1**, blue-vs-green 2.87:1, and `APTURE` legible at
> 128 px / marginal at 64 / mush at 48 and below. Nothing in the Round 10 block above changed —
> including both caveats, and including `render_agreement.py` still exiting 1.
> *Round 13 annotation, not a rewrite: the `--monogram … --out icon/kwcapture-mark-mono.svg`
> command and the "glyph form" in this block no longer describe `icon/`. That file is deleted, and
> nothing in `icon/` is a monogram any more (gotcha 38). The byte-identical regeneration of
> `kwcapture-mark.svg` itself still holds — re-checked 2026-10-11 (`--out /tmp`, `cmp`: identical).*
> *Round 14 annotation, same policy: the four contrast ratios in this block are the **old**
> palette's and are now superseded — they were true of `#00ac4e`/`#0000ff` and are kept because
> that is what Round 11 measured. Palette P2's numbers are in the Round 14 block below and in
> *Expected numbers*; re-run `python3 logo/contrast_report.py` rather than copying either.*

> **Verified 2026-10-11 (Round 12 — the desktop-icon round), by running it.** `bash icon/build.sh`
> rebuilds **24 images** now: `glyph-256.png` was added because the desktop entry ships into
> hicolor's `256x256/apps` directory (gotcha 37) — that is the only change to the set itself.
> `python3 logo/sync_package_icons.py` writes 9 icon files + `COPYING.md` into
> `../kwcapture/icons/`, `--check` on the real trees is clean (*checked 9 icon files (0 written
> now)*, exit 0), and a `python -m build` here puts those **10 files in the wheel and 10 in the
> sdist**, with `logo/` in neither. `tests/test_icons.py`: **89 checks, 0 skipped** on this
> desktop; on its first CI run, **88 passed + 1 skipped** — the skip is `desktop-file-validate`,
> which the runner does not have and which announces itself instead of passing quietly. That suite
> is a CI step, as is the artefact assertion (*wheel: 10 icon files*, *sdist: … 10 icon files*). `probe/sabotage_icons.sh`: **10/10 sabotages detected**,
> tree restored. On this desktop: 9 files installed, all three `.desktop` entries `Icon=kwcapture`,
> `desktop-file-validate` silent, `kwcapture doctor` green. **This round touched no SVG, no sketch
> and no knob**, so the Round 10 and Round 11 blocks above stand unchanged — both caveats included
> (the flake, and `render_agreement.py` exiting 1 on purpose).
> *Round 13 annotation, not a rewrite: the **artwork** this block describes is dead. The set is the
> mark at nine sizes (**17 images**, not 24) and the suite is **98 checks**, not 89 — see the block
> below. Everything else in this block is the wiring, and the wiring survived: the sync rule, the
> hicolor size list, 10 files per artefact and 10/10 on the probe were all re-run in Round 13 and
> still read as written here.*

> **Verified 2026-10-11 (Round 13 — the one-artwork round), by running it.** The owner's rule, and
> it is now the build's rule too: **the icon of kwcapture is `kwcapture-mark.svg`**, and the only
> permitted transformations are **resize and re-render** — no monogram, no invented crop, no
> "better at 16 px" second drawing. What that meant in numbers, measured on this machine:
> `bash icon/build.sh` rebuilds **17 images** (nine mark PNGs 16…1024, five tiles, `favicon.ico`,
> the social card, `contact.png`) and it is **reproducible**: every file in `icon/` matched its
> pre-build sha256 after a full rebuild (`sha256sum -c`, 21/21 files OK including the four builders).
> Its new guard re-renders the mark at all nine sizes and compares **pixels** — *"all nine mark PNGs
> are pixel-identical to a fresh render of kwcapture-mark.svg"*, exit 1 otherwise — and `tiles.py`
> refuses a tile whose artwork the host would clip (**clipped px 0** on apple-touch, maskable and
> the avatar; full bleed would lose 4 015 px of the mark with 45.6 px past the inscribed circle).
> `git rm` took out `icon/glyph-*.png` (12 files) and `icon/kwcapture-mark-mono.svg`; the mark
> gained renders at 16/24/32/48/64, which it never had (it existed only from 128 up — gotcha 37 is
> how that came back to bite). `python3 logo/sync_package_icons.py --check` → *checked 9 icon files
> (0 written now)*, exit 0. `tests/test_icons.py`: **98 checks, 0 skipped** — 89 plus nine new ones
> that assert the shipped scalable SVG **is** `logo/kwcapture-mark.svg` byte for byte and every
> shipped PNG is that mark's render of the size its directory promises. `probe/sabotage_icons.sh`:
> **10/10 detected**, tree restored. `python -m build`: **10 icon files in the wheel and 10 in the
> sdist**, `logo/` in neither. On this desktop after `install-desktop`: 9 installed files
> byte-identical to the mark renders at 16/24/32/48/64/128/256/512 and the scalable byte-identical
> to `logo/kwcapture-mark.svg`, `desktop-file-validate` silent, `doctor` green. `bash
> preview/build.sh` rewrites every README image and only one of them changes — `ladder-icon.png`,
> whose title this round had to draw itself because `montage -title` had been cropping it at both
> ends while exiting 0 (gotcha 39; the title ink is now x 80..622 of a 704 px canvas). **No SVG, no
> sketch and no knob moved** — `gen_logo.py --mark` still reproduces the mark byte-identically and
> `validate_logo.py logo/kwcapture-mark.svg` still prints **OK** (render QtSvg 53.6 % blue, MSVG
> 50.3 %), so the Round 10 block stands; Round 11's and Round 12's icon-set claims do not, and are
> annotated above rather than deleted.
> *Round 14 annotation: those two render percentages are the **old palette**'s and are superseded —
> P2 measures **53.3 % / 49.8 %** on the same file with the same instrument. Every other number in
> this block is geometry or wiring, and all of it was re-run on P2 without moving; that is the
> difference between a claim and a check.*

> **Verified 2026-10-11 (Round 14 — the palette round), by running it.** Palette **P2** is applied:
> green `#00ac4e → #008c46`, blue `#0000ff → #7f7fff`, the owner's decision of 2026-10-11. It is
> paint and nothing else, and the proof is mechanical, not a claim: with every 6-digit hex string
> stripped out of both shipped SVGs, `diff` against `HEAD` is **empty** — no path, no transform, no
> `#type` line moved. `gen_logo.py --mark` and plain `gen_logo.py` reproduce `kwcapture-mark.svg`
> and `kwcapture.svg` **byte-identically** from the new constants (`cmp`, 2/2), and the paint
> variant guard still refuses to write one to a shipped path (`--mark --green '#00ff00'` → exit 1,
> file untouched). Why the palette changed, measured by `python3 logo/contrast_report.py`, the new
> instrument that reads `GREEN`/`BLUE` out of `gen_logo.py` so a doc can never quote a ratio the
> artwork disagrees with: every cell clears the WCAG 3:1 non-text floor on **both** grounds — green
> **4.34** white / **4.36** dark, blue **3.29** white / **5.75** dark — closing the finding this
> folder has carried since Round 10 (blue on `#0d1117` was **2.20:1**). What it costs: the halves
> are now **1.32:1** apart in lightness, not 2.87; the C reads on **hue** (240° vs 150°) and would
> collapse in greyscale. Everything downstream was rebuilt and re-measured, not trusted: `bash
> icon/build.sh` (17 images; *all nine mark PNGs pixel-identical to a fresh render*; tiles clipped
> **0 px**; `FIT 0.790` survives with **+0.4 %** headroom, worst tile 0.794, swept on both
> palettes), `bash preview/build.sh`, `sync_package_icons.py --check` clean, `tests/test_icons.py`
> **98 checks 0 skipped**, `probe/sabotage_icons.sh` **10/10**, `python -m build` → **10 icon files
> in the wheel and 10 in the sdist**, `logo/` in neither, and every wheel icon byte-identical to
> `logo/icon/`. Installed here after `install-desktop`: 9 files byte-identical to the mark renders,
> `scalable` byte-identical to `logo/kwcapture-mark.svg`, `desktop-file-validate` silent, `doctor`
> green, `tests/test_ring_reader.py` **37/37**. The validator's render numbers moved as a recolour
> must move them — mark **53.3 %** QtSvg / **49.8 %** MSVG blue (was 53.6 / 50.3), lockup **44.0 /
> 44.8**, mono **39.3 / 39.5** — and every *geometry* number in the Expected-numbers block is
> unchanged, which is the check that says "paint-only" instead of asserting it. Two real changes
> came out of doing it rather than describing it: `render_agreement.py` had been identifying the
> green half with `fill.startswith("#00a")` — true of the old green, false of the new one, so on
> the recoloured files it was **comparing nothing and exiting 0** — and `validate_logo.py`'s
> classifier is now hue-based against `palette()`, read from the generator. `kwcapture-mono.svg`
> was deleted in this round as scheduled (see *Still open*): `--monogram` is a mode that now
> **requires `--out`**, and every figure that shows a monogram renders one into a temp directory.
> `render_agreement.py` **still exits 1 on purpose** (gotcha 27, 26 px and 67 px, re-confirmed on
> the new paint), and the validator still prints no `box check` line for the lockup — both caveats
> from Round 10 stand. `tests/test_kwcapture.py` has a **new, unrelated** flake, reported rather
> than patched: see the last bullet of *Still open*.

---

## THE RULE: the wordmark is `PTURE`, not `CAPTURE`

The mark spells **CAPTURE** out of three parts, and only the third one is type:

```
  C     <-  the junction of the hand-drawn K and W   (part of #kw, the monogram)
  A     <-  the hand-drawn mouse pointer             (#a, laid out as a letter)
  PTURE <-  the only typeset letters                 (#wordmark)
```

So `WORD = "PTURE"` in `gen_logo.py`. Setting `WORD = "CAPTURE"` produces
**“CACAPTURE”** — which is exactly what happened in the session that first typeset this
logo, because from 2 metres the pointer reads as a blob and the C-in-the-junction is
invisible to anyone who has not been told to look for it. It is not invisible: it is the
whole idea. **Do not "complete" the word.**

![what the mark is made of](preview/anatomy.png)

If a future change makes the C or the A stop reading (different monogram, smaller pointer,
tighter spacing), the fix is to repair that part — **not to add letters**.

Since 2026-10-10 the C is also a **colour**: the K's stem is green so the bracket the
junction forms is the only blue thing inside the monogram. Colour changed the *paint* and
nothing else — the geometry, the fit and this rule are untouched.

---

## Files

| file | what it is |
|---|---|
| `kwcapture.svg` | the logo. 512×512, generated. **Edit the sketch or the knobs, never this file** |
| `kwcapture-mark.svg` | generated **from the mark sketch**: the redrawn monogram + `APTURE` fitted into the helper box, stretched ×1.753 across the baseline. The one that reads at small sizes |
| ~~`kwcapture-mono.svg`~~ | **deleted 2026-10-11 (Round 14)**, on the owner's ruling that the monogram is "unofficial variant and historical value only". The committed SVGs are now `kwcapture.svg`, `kwcapture-mark.svg` and the two sketches. `--monogram` survives as a **mode** and now requires `--out`; the figures that need a monogram render one into a temp directory. `gen_logo.py --monogram --out /tmp/mono.svg` reproduces the file byte for byte and `git log --diff-filter=D -- logo/kwcapture-mono.svg` recovers it. Gotcha 38's lesson one folder up: an artefact beside the approved artwork eventually *is* the approved artwork |
| `kwcapture-sketch.svg` | the **original** hand-drawn source (Inkscape, A4): the first monogram + the mouse pointer. **Input. Never written to by any tool.** Keep it forever — the pointer (the A) still comes from here |
| `kwcapture-mark-sketch.svg` | the **second, redrawn monogram** (cleaner, geometric) plus the black helper box, drawn in Inkscape. **Input. Never written to.** Its `#kw` is *not* the same path as the original sketch's |
| `gen_logo.py` | the generator: sketch + knobs → the SVGs. Manual: `README.md` §gen_logo.py |
| `contrast_report.py` | **every WCAG number this folder quotes**, from the two hex values and nothing else: the 2×2 of palette against white / GitHub dark `#0d1117`, the half-vs-half split, the luminance window that makes "legal on both grounds" and "a loud two-tone split" fight each other, and a dichromatic estimate. Reads `GREEN`/`BLUE` out of `gen_logo.py` (parsed, not imported — it must run without fontTools), so the report and the artwork cannot drift. `--min` makes it a gate: exit 1 when a cell falls under the floor. Added in Round 14 because two rounds of docs had been quoting ratios nobody could re-run | the gate: ink bounds, clearances, centring, the A-vs-cap **type check**, the **box check**, the **colour split check** (the only check that can see paint) and the **render check** (it rasterises with QtSvg and MSVG, so a *viewer* decides). One path argument, default `kwcapture.svg` |
| `render_agreement.py` | **diagnostic, not a gate**: per engine, the ink box it paints vs the box the path data implies, per colour. Found the MSVG `rotate()` bug. Exits 1 today **on purpose** (gotcha 27) |
| `sync_package_icons.py` | **the only sanctioned path from `icon/` into the package**: copies the nine mark renders and `../kwcapture-mark.svg` itself into `../kwcapture/icons/` (hicolor theme layout, one directory per declared size), generates `kwcapture/icons/COPYING.md` with the licence + provenance sha256s, and `--check` fails on any drift. Copies only — it never rasterises or resamples — and it reads the size list from `kwcapture/_icons.py`, so generator and installer cannot disagree (gotcha 36) |
| `preview/` | generated PNGs for `README.md`, plus `build.sh` (one command rebuilds all of them) and `anatomy.py`. Derived artefacts: regenerate, never hand-edit |
| `icon/` | **the shipped icon set, and it is ONE artwork**: `kwcapture-mark.svg` rendered at 16/24/32/48/64/128/256/512/1024, plus the tiles that ground is built on (`apple-touch-icon`, `pwa-192`, `pwa-512`, `maskable-512`, `github-avatar-400`), `favicon.ico`, `github-social-preview.png` and the `contact.png` review sheet — 17 images, built by `build.sh` + `tiles.py` + `card.py` + `contact.py`. The nine PNG renders at 16…512 (plus the SVG itself) are what `sync_package_icons.py` copies into the package. All derived: regenerate, never hand-edit. Manual: `README.md` §8 |
| ~~`icon/kwcapture-mark-mono.svg`~~, ~~`icon/glyph-*.png`~~ | **deleted 2026-10-11 (Round 13).** They were the monogram of the mark sketch, shipped as the icon set on the theory that `APTURE` is mush below 64 px. The owner's rule is that the icon is `kwcapture-mark.svg` and the permitted transforms are resize/re-render — so the monogram is not an icon and does not live in `icon/`. `gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg` reproduces the drawing to `/tmp` for figures (that is what `preview/build.sh` does for the ladder); `git log --diff-filter=D -- logo/icon/` recovers the files. |
| `README.md` | the manual: directory structure, every `*.py` program, the commands that make each image |
| `LICENSE.md` | artwork **CC BY 4.0**, tooling **MIT** (the package's own [`../LICENSE`](../LICENSE)), Inter **OFL-1.1** referenced. `*.jsonl` is licensed by nobody — §6 there |
| `AGENTS.old.md` | the archive: superseded numbers, the full gotchas, the 2026-10-10 session log. History, not instruction |
| `*.jsonl` | the design-session transcripts (here, as of 2026-10-11 evening: `unfinished_job.jsonl`, **1 110 676 B** — `wc -c`, measured because this row said `prev_logo.jsonl`, 2.0 MB, and both the name and the size had gone stale). **A different name every session**; **never committed** (`logo/*.jsonl` is gitignored — re-checked this round with `git check-ignore -v` and `git add -A --dry-run`); **never read whole** — see *Reading the transcript* |
| `__pycache__/` | appears because `validate_logo.py` imports `gen_logo` to reuse the box geometry. Gitignored |

## Regenerating

```bash
python3 logo/gen_logo.py                       # -> logo/kwcapture.svg
python3 logo/gen_logo.py --mark                # -> logo/kwcapture-mark.svg   (helper box mode)
python3 logo/gen_logo.py --monogram --out /tmp/mono.svg  # the MODE; there is no shipped mono file
python3 logo/contrast_report.py                # the palette's WCAG table; exit 1 under --min
python3 logo/gen_logo.py --out /tmp/x.svg --classic       # the old look: gradient mono, black type
python3 logo/gen_logo.py --out /tmp/x.svg --no-c-split    # CONTROL: "is colour what makes the C read?"
python3 logo/gen_logo.py --out /tmp/x.svg --a-size 1.15   # experiment; repo untouched
python3 logo/gen_logo.py --mark --out /tmp/x.svg --no-height-fill   # the pre-Round-9 word
python3 logo/gen_logo.py --mark --out /tmp/x.svg --max-stretch 1.35 # the mild fill
python3 logo/validate_logo.py                            # checks kwcapture.svg
python3 logo/validate_logo.py logo/kwcapture-mark.svg    # type check + BOX check
# (a recolour: change GREEN/BLUE in gen_logo.py and re-run these -- NEVER pass --green/--blue
#  into a shipped path. The guard refuses, and it is right: the artwork must be reproducible
#  from the constants, and it is `cmp`-identical to them, which is the check.)
python3 logo/render_agreement.py                         # exits 1; that is the finding, not a bug
xmllint --noout logo/*.svg                               # must be silent
bash logo/preview/build.sh                               # rebuild every README image

# the shipped icon set (README.md §8): ONE artwork at many sizes, then the tiles on it
bash logo/icon/build.sh                                  # 17 images, .ico, avatar, card, sheet
                                                       # ends by re-rendering the mark and
                                                       # comparing pixels: fails if a file in
                                                       # icon/ is not kwcapture-mark.svg

# and into the Python package (run from the repo root; stdlib only, no inkscape needed):
python3 logo/sync_package_icons.py         # icon/ -> kwcapture/icons/ + COPYING.md
python3 logo/sync_package_icons.py --check # drift only; exit 1. tests/test_icons.py runs this
```

**`--check` is the part that keeps the promise.** A copied artefact is a second artefact: re-render
the mark next month and the package is quietly shipping the old one (gotcha 36). The check runs
inside `tests/test_icons.py`, which is a CI step, so the drift has to be fixed in the same change
that introduces it.

**`icon/build.sh` reads one SVG: `../kwcapture-mark.svg`.** It refuses to run if that file is
missing, generates no SVG itself (SVGs are `gen_logo.py`'s job; the icon set's job is pixels),
and finishes by rendering the mark again at all nine sizes and comparing **pixels** with what it
wrote — so the day someone puts a monogram or a hand-edited raster into `icon/`, the build fails
instead of shipping it. `--sketch` and `--out` are literal paths (the trap above), which is why
the commands that use them are written from the repo root.

**A variant needs `--out`, and now the tool says so.** `--classic`, `--no-c-split`,
`--c-paint` and friends change the *paint* but not the default output path, so the old
documented commands overwrote the shipped logo with the old look while staying valid XML,
xmllint-clean and geometry-perfect — recovery was `gen_logo.py` with no flags. `gen_logo.py`
now compares every knob against **argparse's own defaults** and refuses:

```
$ python3 gen_logo.py --classic
refusing to overwrite the shipped kwcapture.svg: this run deviates from the shipped look
by --classic.
  write it somewhere else:  --out /tmp/kwcapture-variant.svg
  or, if you really mean to replace the shipped file:  --force
```

Verified 2026-10-11: exit 1, `kwcapture.svg` byte-identical afterwards. `--force` is the
escape hatch and means *I intend to replace the shipped file*.

**Two path traps.** Only the **default** paths are resolved from the script's own directory,
so the commands above work from any cwd. `--sketch` and `--out` are literal paths: the
documented `--sketch logo/kwcapture-mark-sketch.svg` raises a bare `FileNotFoundError` from
`xml.etree` if your cwd is `logo/`. Either run from the repo root as written, or drop the
`logo/`.

Needs **fontTools** (outline extraction) and **numpy** (validator) — present in the system
`python3` and in `.venv`. The render check additionally uses **PyQt6.QtSvg**, ImageMagick's
internal **MSVG** coder and **Pillow**; `render_agreement.py` adds **Inkscape**. Missing
tools are reported and skipped, not silently passed.

## The knobs, and what they cost

| knob | value | why this value |
|---|---|---|
| `WORD` | `PTURE` | see THE RULE |
| `FONT` | `Inter-ExtraBold.otf` | the drawn monogram is very heavy (stem/height ≈ 5.8/30.1 ≈ 0.19); Inter **Bold** looked thin next to it. Lato Bold and Noto Sans Bold were tried and are less neutral than the mark |
| `ANGLE` | `−38°` | measured off the sketch (drawn baseline ≈ −38.9°). The word deliberately rises shallower than the K's arm (~52°), which is what lets it tuck under the arm |
| `CAP` | `3.30 mm` | the drawn letters were ~3.4 mm cap |
| `TRACK` | `0.10 em` | the sketch was widely set; tighter looks cramped against the monogram |
| `A_SIZE` | `1.00 × cap` | **the A must be exactly as tall as the P.** One big letter in this mark — the C in the K+W junction — and `APTURE` must read as one evenly-set word. 1.30× made it "big C, medium A, small PTURE". Height is measured **perpendicular to the baseline**; the only sense in which rotated text has a height |
| `A_WIDTH` | `1.00 ×` a real capital A | **and as WIDE as an A.** In Inter ExtraBold at this cap the A is 3.282 mm of ink (0.995 × cap); the pointer scaled uniformly was 2.42 mm — a skinny A next to fat letters. So `#a` is stretched **along the baseline only**, ×1.36, to 3.282 mm. Height untouched. The sketch's arrow already had the right *width* and too much *height* — which is why uniform scaling felt wrong |
| `A_GAP` | `0.70 mm` | the A→P gap along the baseline — a *type* gap. 0.90 mm read as a word break once the A was shrunk to cap height |
| `ANCHOR` | `(73.4, 112.6)` mm | baseline start of `PTURE`, in the sketch's mm space, where the drawn P started |
| `ALIGN_TOP` | `True` | levels the cap-top of the word with the top of the K: one flat top edge |
| `CANVAS`/`PAD` | `512` / `44 px` | square artboard, icon-safe. The art is wider than tall (35.58 × 30.13 mm), so vertical padding ends up larger (76 px) — correct, not a bug |
| `C_PAINT` | `solid` | how the blue C is cut: `solid` \| `mask` \| `clip`. Chosen by the **renderer matrix**, not taste; `validate_logo.py` re-runs the matrix on every build. See *Which cut-out* |
| `MAX_STRETCH` | `2.00 ×` cap | ceiling on the height fill — a **taste guard, not geometry**: the shipped box wants 1.753 and is not stopped by it. It exists because the box is the owner's drawing and next week it may be twice as tall, and Inter at ×3 is a cage of vertical strokes. 0 = `--no-height-fill` |
| `GREEN` | `#008c46` | the K's stem and the W. Palette **P2**, the owner's decision of 2026-10-11 (was `#00ac4e`, the old gradient's end stop). The balanced one of the four greens measured: **4.34** on white / **4.36** on `#0d1117`, i.e. it clears 3:1 on both grounds, which `#00ac4e` did not (3.00 on white) |
| `BLUE` | `#7f7fff` | the C, the pointer-A and `PTURE`. Was `#0000ff`: 8.59 on white but **2.20** on GitHub dark, the oldest accessibility finding in this folder. `#7f7fff` is 3.29 white / **5.75** dark — the only single value measured that clears both. What it gives up: **1.32:1** against the green instead of 2.87, so the C separates by **hue** (240° vs 150°), not lightness; `#3b82f6` is 5.15 on dark but 1.18 from this green and the C dissolves into the W. Every number in these two rows is printed by `contrast_report.py` |

## The helper box — `--mark` mode

Draw a **four-corner box** (a parallelogram; give it id `fit-box` to be explicit) over where
`APTURE` should go in `kwcapture-mark-sketch.svg`, then run `--mark`. The box says three
things and is then **thrown away**:

| read off the box | used for |
|---|---|
| its **lower long edge, left→right** | the baseline slope — the shipped one is **−43.12°** |
| its **length** | how much type fits along the baseline |
| its **height** | the ceiling on cap height |

"Fit" is an **optimisation**: all nine placements (`center|base|top` across ×
`center|start|end` along) are tried, and for each the cap height is **bisected** to the
largest value that stays inside the box **and** keeps `--min-clear` (default **0.50 mm**) of
ink from the monogram. Biggest winner wins: today **centred across, centred along, cap
4.310 mm = 100% of the box's length** — and that is a **tie**, broken by list order (which
is also the nicest result). All three across-placements reach 4.310 mm because the word fills
the box's length exactly; clearances at that cap are `top` 17.36 px, `center` 9.45 px
(shipped), `base` 9.70 px. So at 0.50 mm **the box limits the type, not the monogram**, and
`--along` is a no-op while the word is exactly 100% of the box length — it starts to mean
something with `--cap`, a longer word or `--inset`.

Raising `--min-clear` now costs **type size**, never containment (`--no-height-fill`,
measured): 0.5 → cap 4.310 mm; 0.9 → 4.273; 1.2 → 4.169; 1.5 → 4.065, centred throughout.
Before Round 9 the answer to a higher floor was `top` — and `top` bought it by putting the
word 1.59 px **outside** the box, because `fits()` tested the monogram and only the *nominal*
box. Both halves of "inside **and** clear" are now tested against the quad; a placement that
spills is not a placement. The falsified table and the Round 4 claim it replaced ("centred
72%, top 100%, the geometry forces the top edge" — the anchor bug talking) are in
`AGENTS.old.md` **A.3**.

**Anchor semantics — read before touching `layout()`:** `place_A()` parks the pointer
*behind* the anchor it is given (trailing edge at `-gap`), so the anchor is **not** the left
edge of the word. The whole-word left edge is `anchor − (a_w + gap)`, and the pointer and
PTURE must be handed the *same* shifted anchor. Get it wrong one way and the A hangs outside
the box while PTURE falls short; get it wrong the other way and the word splits in half.

**Why the monogram has a veto at all:** the box's lower-left corner is drawn *inside* the W's
stroke, so filling the box blindly puts the A on top of the W — that file was emitted once,
`validate_logo.py` called it a `COLLISION`, and the fitter refuses to do it again. Note the
tense: the veto **is not being used** at today's numbers (0.810 mm clear, floor 0.50). It is
what makes it safe to move the box, lengthen the word or raise `--min-clear`.

After fitting, the whole lockup is **re-centred on the artboard** (same scale, new translate):
the box was drawn wherever the mouse happened to be and its right end runs off the canvas.
`--no-recenter` keeps the sketched position.

**"Inside the box" is verified, not assumed.** The box is not in the output, so nothing in the
output could prove the word was inside it. `validate_logo.py` re-reads the box from
`<name>-sketch.svg`, undoes the re-centring shift and fails if any ink of `#a` or `#wordmark`
is more than 1 px outside.

**The check is keyed by filename, and its two skips are silent (gotcha 30).** It looks for
`<stem>-sketch.svg` **next to the script**, and returns `[]` without printing anything when
that file is missing *or* when the sketch contains no box — so `logo/kwcapture.svg` prints no
box-check line (correct: its sketch has no box), and a sabotaged copy at `/tmp/sab1.svg` prints
no box-check line either (not correct-looking at all: the sharpest check on the mark quietly
stopped running, and only the centring test caught the same bug). **Absence of the line is the
only signal there is.** The older wording here — "it prints a line either way" — was false; it
was disproved by running it, and is corrected rather than argued about.

## The height fill — filling the box's *height* (`#type`)

Fitting by length leaves the box's height barely used: cap 4.310 mm in a 7.786 mm box is
**55.4%**. The owner asked for type "as tall as possible but still inside the black box", and
the only way to fill a box whose length is already full is to stretch it. The rules:

* **Across the baseline only, never along it.** Widths, the A's width, tracking and every
  along-baseline distance stay as fitted; only height grows. A stretch with an along
  component moves tracking and is refused by the validator.
* **One `<g id="type">` over the pointer-A *and* PTURE.** Two transforms would let them drift
  into two sizes of type. `#kw` is never inside it — `#kw` is the hand drawing, and `#kw`
  inside `#type` is a validator failure ("colour it, do not resize it").
* **Seat, then stretch:** `t ↦ a + s·t` in the box's frame — the ink's lowest point on the
  box's base line (`+--inset`), then scale by `s` across it. Emitted as
  `translate rotate scale(1 s) rotate translate`, measured independently by the validator off
  that transform.
* **One blend, `lam ∈ [0,1]`, on the *displacement*:** `lam = 0` is the identity —
  `--no-height-fill` is byte-identical to the pre-fill mark — and `lam = 1` is the full fill.
  The monogram's veto bisects on `lam`, so a half-stretch is also a half-seating. (An earlier
  version seated unconditionally and `--no-height-fill` came out 0.79 mm off-centre.)

**Shipped: `s = 1.753`.** Ink band 4.365 mm → 7.652 mm = **98.3%** of the box height; monogram
clearance 0.810 mm after the seating (0.792 mm before). The honest cost — the type is
**condensed**, the rendered A is 0.55 × as wide as it is tall, and the pointer reads more like
a cursor than like the letter A — is in `AGENTS.old.md` **A.4**, together with the escape
hatches (`--max-stretch 1.35` = 75.7% of the height and nearly undistorted; `1.5`;
`--no-height-fill`). A word that is *both* undistorted and this tall cannot fit this box: the
length is already 100% full, so the alternatives are a shorter word, a shorter box or a second
line — all sketch decisions, and the taste call is the owner's, not mine.

### The box is four mouse clicks, not a rectangle — why 1.753 and not 1.784

The obvious number is *fill the box's height*: `7.786 / 4.365 = 1.784`. It is wrong by
**1.6 px**, and the box check was reporting exactly that failure. `#path4` in the sketch is
four clicks:

| its edge | measured |
|---|---|
| top vs base | **0.62° off parallel** — headroom over the base falls **7.920 → 7.651 mm** along the length |
| left edge | leans inward 0.18° (clips the A's tip by 0.06 px: the shipped −0.03/−0.08 px margin) |
| right edge | leans inward 1.65° |

`box_frame()`'s `(length, height)` is the box's **average**, and type fitted to the average of
a non-rectangle hangs outside it — at the far end, where the word is tallest and the box
shortest. So both fits go through `halfplanes()`, the four inward half-planes of the drawn
quad: `fits()` refuses any layout whose **ink** pokes past `FIT_TOL` = **0.25 px**, and
`tallest_stretch()` solves the same half-planes for `s` directly (the map is linear in `s`, so
the tight edge is arithmetic: `s·(n_t·T) ≥ c − n_u·u − n_t·inset`). `FIT_TOL`, not the
validator's 1 px: the box's own lean makes ~0.06 px of spill unavoidable (0 would reject every
placement) while 1 px of spill is a *choice* the optimiser must not be allowed to make — with
1 px, `--min-clear 0.9` shipped `base/end` 0.66 px outside; with 0.25 px it is centred and
inside.

## The colour split — KW green, Capture blue

The K's **stem is the stroke that competes with the C**: the C is the bracket the junction
forms (arm + leg), and a stem running through it is what made it read as part of a K. So the
stem is green, that bracket is blue, and `APTURE` shares the blue.

* **It is paint, not geometry.** `#kw` is the monogram in `GREEN`; `#kw-c` is the blue C and
  `--c-paint` decides how the blue is cut to it. Nothing moves: every bound in *Expected
  numbers* is identical to the single-colour mark's. If a bound changes after a colour edit,
  the edit was not a colour edit.
* **The rings are the owner's numbering of the outline, not my reading of it.** Both monograms
  are 19-vertex closed outlines with the **same topology, index for index**, and the three
  letters are three rings over those indices (`K_RING`, `W_RING`, `C_RING`):

  ```
    K = 0  1  2  3  4           13 14 15 16 17 18
    W =    3  4  5  6  7  8  9 10 11 12 13 14
    C =    3  4  5  6           12 13 14 15 16 17      <- the blue one
  ```

  They **overlap**, which is what a ligature is: 3–4 is the K's leg and the W's first stroke at
  once, and the C borrows from both. The C is **three strokes, like `[`** — not two like `<`:

  | stroke | vertices | what it is |
  |---|---|---|
  | top arm | 14→15→16→17 | the K's arm |
  | spine | 17→3 | the stem's right edge — the C's back, zero width; the stem stays green |
  | bottom arm | 3→4→5→6 and 12→13 | the leg, the shared V, **and the first W rise all the way to the peak tip at 12** |

  So the ring is the drawing's **own edges plus exactly two chords** — `6→12` across the peak,
  `17→3` across the stem — no padding and no invented lines, which is why the cut is exact and
  why `frac_in` reports **100.0% of the clip polygon lying on ink**. My first attempt covered
  52–53%; the missing half was empty space I had invented (gotcha 22).
* `len(verts) != 19` makes the generator **refuse** rather than guess: re-sketching means
  re-checking the indices — same policy as the `path1`/`path10` id binding in *Re-sketching*.
* **The C polygon is in the sketch's mm space whichever `--c-paint` you use**, so it resolves
  inside the `#logo` transform exactly like the gradient coordinates do. In canvas px it would
  be right at one scale and wrong at every other.
* The blue covers **42.0%** of the mark's monogram ink and **39.1%** of the original's (0.15 mm
  grid) — near-balanced, not one garnish on a big shape. What colour *cannot* do is curve a
  stroke: the C is straight lines and square corners, so a curved C is a sketch job.

### Which cut-out: `--c-paint solid|mask|clip` — measured, not opinion

Three ways to paint the same C, and **renderers disagree about all of them**. Measured on this
machine on palette P2 (2026-10-11) with `validate_logo.py`'s own hue classifier, monogram ink as
% blue (the truth is 38.4–39.5%): the pre-recolour table read 39.1–39.8% for the same geometry,
which is the point of re-measuring a table like this per palette rather than trusting it to carry
over:

| renderer | `solid` | `mask` | `clip` |
|---|---|---|---|
| Inkscape / librsvg | 39.3% ✅ | 38.4% ✅ | 38.4% ✅ |
| **QtSvg** — Gwenview, Dolphin thumbnails, `QIcon`, KDE's image plugin | 39.3% ✅ | 38.5% ✅ | **100% blue ❌** |
| **ImageMagick internal MSVG** | 39.5% ✅ | **0% blue ❌** | 39.3% ✅ |

The two failure modes are renderer bugs and they came through a recolour untouched: Qt still
drops `clip-path` and paints the whole monogram blue, MSVG still hides a mask it cannot parse.

* **`clip` shipped for a day and is wrong in Qt.** QtSvg **ignores `clip-path`** — not a quirk
  of our file: Qt 6.10.2 drops even a canonical `<circle>` clip. The blue copy of the *whole*
  monogram painted over the green one and the mark looked **100% blue in Gwenview and every
  Dolphin thumbnail** while Inkscape, browsers and the validator all said it was fine. The
  owner found it by looking at a folder.
* **`mask` is not the safe answer either.** It fixes Qt and keeps the byte-identical `d`, but
  MSVG treats a mask it does not parse as *hide everything* and the C vanishes.
* **`solid` (default): `#kw-c` carries the C ring's own path data.** No `defs`, no cut-out
  feature, nothing for a renderer to ignore — legal **only** because the ring lies **100.0%
  inside the monogram's ink**, which the validator asserts for a different reason, so
  `monogram ∩ ring == ring` and the clip was always a set-theoretic no-op that only ever did
  edge antialiasing. Inkscape diff `clip` vs `solid`: 1160 px of 262 144, **4 px at 15% fuzz**.
  It is still **derived by vertex index**, never hand-drawn, so "never a second drawing"
  survives in the place that mattered: the polygon must equal `C_RING` recomputed from the
  sketch or the build fails.
* ⚠️ **`--help` lies about this.** `gen_logo.py --help` still prints "`mask` (default) and
  solid render identically everywhere". The default is **`solid`**, and mask and solid are *not*
  identical anywhere MSVG runs. Trust this table and the `C_PAINT` comment, and fix the help
  text the next time the file is edited (listed in *Still open*).

`validate_logo.py` **renders the file** in every engine the machine has and fails if the
two-tone split is not actually on screen; the two weak renderers fail in opposite directions,
so a file has to satisfy both. Gotcha 25.

## Rules for the emitted SVG

* **Outlines, never `<text>`.** A `<text>` element makes the logo depend on a font being
  installed; it renders as garbage on a random machine reading the README.
* **Keep the `#kw` path data verbatim from the sketch.** Its wobble *is* the design — the
  hand-drawn K/W junction is what doubles as the C. Straightening it can kill the C.
* **The C is never a second *drawing*.** With `--c-paint solid` (default) `#kw-c` carries the C
  ring's own path data, which must equal `C_RING` **recomputed from the sketch's vertices** —
  the validator fails the build otherwise. `clip|mask` restore the byte-identical-`d` form the
  old wording stated literally; both are wrong in at least one renderer. If the C needs a new
  **shape**, that happens in the sketch or in the ring's derivation, never by editing an
  outline in the output.
* **No `clip-path`, and no reliance on `mask`, in shipped artwork.** Renderers ignore them
  silently and in opposite directions. A logo is what viewers paint, not what the DOM says —
  the render check exists to enforce that. Generalises to `filter`, CSS and `<text>`.
* **The A is type, not ornament.** It must sit on the word baseline, tip on the cap line, as
  wide as a capital A — all four asserted. The build fails if the A's height is >2 px off cap,
  if it floats off the baseline, if it pokes past the cap line, or if its width leaves
  0.85–1.15× cap. (Inter's `U` overshoots ~0.5 px, which is why the height tolerance is 2 px
  and not 0.) A pointer that is merely scaled is a cursor; a pointer with the right height
  *and* width reads as the first letter of the word.
* **`#a` is one `matrix(...)` and it is deliberately anisotropic**: uniform scale to cap height
  plus a stretch *along the baseline* to the width of a real capital A (`world→baseline frame`,
  stretch, `frame→world`). Never stretch perpendicular to the baseline and never shear it: the
  tip axis is already within ~6° of perpendicular, which is *why* it reads as an upright A.
  `--a-upright` snaps it exactly perpendicular and it then reads as an arrow. Measured; don't
  re-try.
* **`#type` is the height fill and it is deliberately anisotropic**: `scale(1, 1.753)` inside a
  `rotate` pair, over `#a` + `#wordmark` only. Four assertions: the along-baseline factor is
  1.0000, it covers both letters, it does not cover `#kw`, and every rule of the type check is
  measured **unstretched** — a stretched cap is not a bigger letter, and a correct 0.98 × cap A
  reports as 0.55 × cap if the stretch is left in the ruler.
* `#kw-grad` (emitted only by `--classic`; the default mark is flat two-tone) is
  `gradientUnits="userSpaceOnUse"` with coordinates in the sketch's mm space — correct, because
  userSpaceOnUse resolves inside the ancestor `#logo` transform, so the gradient scales with
  the art. "The numbers look wrong for a 512 canvas" is not a bug; do not rescale them. The C
  polygon obeys the same rule.
* Transparent background. No `sodipodi:`/`inkscape:` editor junk in the output.
* **`--` is illegal inside an XML comment.** Bit the generator twice (a comment naming a flag).
  Structurally impossible now: everything goes through `write_svg()`, which refuses a comment
  containing `--`. Same family: an f-string with a misplaced `"` closed `transform="…"` before
  `rotate(…)`; xmllint caught it, a browser would have quietly dropped the rotation.
* Units: the sketch is in **millimetres** (`width="210mm"` + `viewBox="0 0 210 297"` → 1 user
  unit = 1 mm, *not* 1 px). `gen_logo.py` emits px on a 512 artboard and keeps the mm
  coordinates inside the single `#logo` transform.

## Gotchas already paid for — one line each

The rule, without the story. **Full narratives: [`AGENTS.old.md` Part B](AGENTS.old.md).**
Gotcha 29 is Round 10's and is told in full below, because it is still open. **31–35 are
Round 11's** (the icon round), and all five arrived while building something, not while reading.
**36–37 are Round 12's** (the desktop-icon round): their narrative is the Round 12 session-log
entry at the bottom of this file until the next round moves it to the archive.

1. The sketch shipped as an A4 page with ~36 mm of art off-centre: that is the "canvas size" bug. The fix is artboard→512² **and centring**, not scaling the drawing.
2. Two sketch paths rendered **nothing**: a bare line with `fill` and no `stroke` has no area. Never assume a drawn path is visible — render it.
3. **CACAPTURE** — see THE RULE.
4. fontTools: glyphs are y-up, SVG y-down → `(k,0,0,-k)`; size caps from `OS/2.sCapHeight`, not `hhea.ascent`; a TrueType `qCurveTo` can carry a *run* of off-curve points — split at the midpoints or bounding boxes lie.
5. A rotated text bbox ≠ anchor + cap height (a 22 mm word at −38° reaches ~13 mm above its anchor); `align_top` must use the measured union of wordmark **and** pointer or it shoves the word into the pointer.
6. The validator once squared a group matrix for paths with no `transform` of their own (10.9 became 118): if the reported ink bbox is wildly off, **suspect the checker before the artwork**.
7. **A projection bug made `A_SIZE=1.00` render the A at 1.41× cap** — the height fit mixed `dirv`/`perpv` and measured perpendicular to **+38°** instead of **−38°**. On rotated text, verify height against the baseline, end-to-end from the emitted SVG. The type check now does.
8. **Right height is not enough — the width was wrong too.** Uniform scale made the A 0.71× a real A's width. Fix is the anisotropic baseline stretch (`A_WIDTH`); and the first fix divided by the *unscaled* width and reported 0.74×. Anisotropic maths in a rotated frame is not something to eyeball.
9. **"As large as possible" needs an optimiser, not a formula**: enumerate placements, bisect cap per placement. (Its numbers — top 100%, centred 72% — were falsified by the anchor bug; the *method* lesson stands, see 18.)
10. A naive shrink loop (`cap *= gap/required`) **ran away to 0.14 mm**. The predicate is monotone in cap: bisect it.
11. **Convex-hull tolerance must scale with the shape.** Dedup at 1e-6 with a collinearity cut of 1e-9 makes a 300-unit box return 24 "corners". Use an area tolerance ≈1e-9·span².
12. Walking a closed polygon, **opposite edges are anti-parallel** (~180°, not ~0°); comparing them as parallel rejects every real box.
13. **`--` inside an XML comment, again** — a comment naming the `--mark` flag. Now impossible: `write_svg()` refuses.
14. **The width target must be measured at the fitted cap height** (4.310 mm in mark mode, not the module's 3.30 mm) — the skinny-A bug re-imported through a different door.
15. **The anchor is not the left edge of the word.** The A parks behind it. Hand the pointer and PTURE the same shifted anchor; the first fix over-corrected and split the word in half. The owner saw it before any test did.
16. **Containment wants `min(depth)`, not `max(depth)`** — the box check first tracked the cosiest point and printed "+46 px inside" while the A was 20 px outside.
17. **Load each font once** (`load_font()`): opening the same OTF ~200× while bisecting killed fontTools' lazy cmap subtable.
18. **Fix the bug, then grep for the sentences the bug wrote.** The anchor bug left four of its own claims circulating — a code comment, a *Still open* bullet, a log sentence and **a number inside gotcha 9** — all true measurements *of the broken layout*, so they read as constraints. After any layout fix: re-measure and search the prose for conclusions only ever true of the broken version — `cd logo && grep -n "72%\|top edge\|28%" *.md *.py` (`*.md *.py`, never `logo/*`: the transcript will answer with screenshots).
19. **A boolean parameter named `grad` lost an argument fight to a local variable** of the same name, and `--classic` leaked into the default build. Python's only complaint was an "element truth value" DeprecationWarning — the sound a name collision makes. Grep the body before adding a parameter; treat that warning as a collision report.
20. **`f("{x:.4f}")` is not an f-string** — it is this module's one-letter formatter `f()` on a literal. Write `f"{f(x)}"`. A helper named `f` makes every f-string in the file a two-way bet.
21. **A repaint is not a new mark.** The validator saw `#kw-c` as artwork and screamed `COLLISION` at distance 0.00 px — and worse, *everything else passed while the C could have been painted anywhere*: geometry checks are blind to paint by construction. Fixed by teaching the checker about identity (`<base>-c` = overlay, ink counted once, `d`/polygon/sample points asserted), not by loosening a threshold. A screenshot you looked at is not a test.
22. **A test that agrees with you is not a test.** I invented the C's anatomy, and the check validated the output against **the same wrong reading** and printed OK. Two rules: a letter partition is **intent and belongs to the owner** (ask for the vertex numbers), and every such check needs ≥1 assertion the generator **cannot agree with by construction** — here "≥95% of the clip on ink" and "0% of the stem inside it", both of which failed my ring on the first run.
23. **The helper box is four mouse clicks, not a rectangle.** `(length, height)` is an average of a non-rectangle, and anything fitted to it hangs outside. Treat a hand-drawn guide as a **polygon of half-planes**, and measure the **ink**, never the nominal band, when the thing being contained overshoots its own metrics.
24. **Gotcha 22 came back within one session, in the check written to fix it** — the new `fits()` sampled the word at `anc` instead of `wanc` and reported a spill as inside. What caught it was sweeping the knobs against the validator, not reading the code. So: **a new check must be shown to fail before it is believed** (four sabotages of the emitted mark, each must exit 1; and `assert changed` on the sabotage itself, because one of them was a silent no-op), and **print a hand-drawn guide's imperfection** — nobody sees 0.62° in a render, and "why 1.753?" otherwise gets re-asked every month.
25. **A valid file can be wrong in half the viewers on your desktop while every check says OK.** `clip-path` shipped for a day; QtSvg ignores it, so Gwenview and every Dolphin thumbnail showed a 100% blue monogram. "Then use a mask" is not the fix (MSVG hides it) — the two weak renderers fail in **opposite directions**, so prefer plain geometry that asks nothing of the viewer, and make the gate **render** with a renderer the generator did not assume. Side effect: MSVG cannot render our `userSpaceOnUse` gradient at all, so `--classic` is not MSVG-safe and the render check is scoped to two-tone output on purpose.
26. **An exception that escapes a check is a bug in the checker; a bare traceback is a bug in the report.** `run_check()` now prints `CRASH in <name>` + traceback, counts it as a FAIL (a check that died checked nothing) and ends with `NOT A CLEAN RUN` so even `| tail -1` cannot mistake it for a problem count. `ink()` rejects a non-4-number viewBox; `_msvg_render()` uses `mkstemp`, not a pid-keyed path. Generalises: **never diagnose from the tail of a pipe.**
27. **MSVG mis-renders `rotate()`** — the type lands 26 px (`kwcapture.svg`) / 67 px (the mark, clipped) out of place, and MSVG is exact on the mono, the one file with no `rotate()`. Ruled out by measurement: the argument separator, the transform *chain*, and `rotate()` nested under `scale()`. **Baking transforms into the path data does fix it** — and costs the mm-space C polygon, the `#type` transform `band_check` measures and the same-path-data invariant, so it is not done to the shipped files. A colour counter cannot see a position error: that is what `render_agreement.py` is for. Practical reach: ImageMagick **without** a `librsvg` delegate renders the wordmark wrong; KDE, Inkscape and browsers are fine.
28. **A shared fontTools glyphset corrupts state, and the impossibility of the messages *is* the diagnosis.** Four unrelated TypeErrors (`'str' object is not callable`, `'T2OutlineExtractor' object is not subscriptable`, `float * Wordmark`, `compile() arg 1 must be a string`) at ~1–3% of `--mark` builds: 2/60 shared glyphset, 0/60 one glyphset per `Wordmark`, 0/120 after. Fix keeps the `TTFont` cached (a second `TTFont()` on the same file really does die in the lazy cmap) and stops caching the *glyphset*. Byte-identical output: the corruption never reached the artwork, it only killed the process. **A cache is only safe if what it hands out is immutable**, and when a message describes operands the source cannot produce, stop reading your own code and ask what you share. Hide rate ~2% and no message repeats, so reproduce with 40+ builds in a loop.
29. **The flake is alive, and it is not in our code.** See below — Round 10.
30. **A check can stop running and say nothing.** The box check resolves its sketch as
    `<stem>-sketch.svg` beside the script and returns `[]` silently when that file is absent or
    has no box. It prints **no line at all** — the sentence in this file claiming "it prints a
    line either way" was wrong, and it made a skipped check look like a passing one. Sabotaging
    a copy in `/tmp` therefore validates the file with the containment rule switched off. Two
    rules: **a check that skips must print that it skipped**, and when you sabotage something to
    prove a check works, **assert the sabotage landed** (`test "$(grep -c …)" = 1`) — a `sed` with
    BRE-escaped parens matched nothing on the day this file was written and the validator printed
    `OK` at a file I believed was broken. Gotcha 24's lesson, paid for twice in one day.
31. **Inkscape's `-b none` is not transparency.** It is accepted, exits 0 and writes an
   **opaque white** background (measured: corner alpha 255); omitting `-b` entirely is what gives
   real alpha (corner alpha 0). Every icon build that wanted a transparent PNG and passed
   `-b none` got a white tile and a green exit code. `icon/build.sh` has a comment on this and a
   helper that never passes it. Same family as gotcha 25: a flag that silently produces the wrong
   artefact, and only the pixels know.
32. **ImageMagick compositing on this box returns a blank canvas and reports success.** Glyph on
   a white tile was first written with `magick a.png b.png -gravity center -composite`; it gave a
   blank *greyscale* canvas in every variation tried — white base, `xc:none`, `magick composite`,
   `-layers flatten`, `-type TrueColor` — while exiting 0. The tiles therefore live in Pillow
   (`tiles.py`, `card.py`, `contact.py`), which is already a dependency and is deterministic.
   Rule: on this machine, **verify the pixels of a composite, never its exit code** — and the
   grayscale `identify` type is what caught it.
33. **A card can be written off its own canvas and `wrote …` printed anyway.** The first
   `card.py` hard-coded font sizes; the tagline ran past the right edge of the 1280×640 card and
   the script cheerfully reported `wrote /home/…/github-social-preview.png (1280, 640)`. Now
   every string is measured with `font.getlength()`, shrunk until it fits its column, and the
   script asserts nothing reached the edge. Gotcha 24's "a new check must be shown to fail" —
   met a third time, in a *builder* rather than a checker.
34. **The GitHub API cannot set a repository's picture, and a repository has no avatar.**
   `PATCH /repos/{owner}/{repo}` takes description, homepage, wiki, discussions… and no image
   field; the social-preview image is a web-UI upload only. So `README.md` §8 carries two manual
   uploads instead of a script that pretends. `Repository` exposes `openGraphImageUrl` and
   `usesCustomOpenGraphImage` — **read-only**, so they are the way to *verify* the upload without
   a browser, never the way to do it. Check the API before promising an automation, and check
   *which* object owns the asset: avatars belong to a user or an org, never to a repo.
35. **A build script's report can print nothing and still leave the build green.** `icon/build.sh`
   used to end with `magick identify --format … 2>/dev/null | head -8`: `identify` wants `-format`
   with **one** dash, so with two it reads the format string as a *filename*, dies with "no decode
   delegate for this image format", and the suppressed stderr made the whole report vanish — the
   build printed its `ls` and exited 0. Fixed: one dash, stderr no longer suppressed. Measured on
   the same line: width specifiers (`%-28f`) are not supported by this ImageMagick — it prints
   `28f` and warns `unknown image property "%-"`. **Gotcha 30 one layer down**: the thing that
   reports on the artefacts can itself fail silently, so treat a report as a check — un-suppress
   its stderr and make sure its silence would mean something.

36. **A copied artefact is a second artefact, and second artefacts rot.** `../kwcapture/icons/` is
   a *copy* of `icon/`, so the day the mark is re-rendered the package ships the old drawing while
   every check in this directory keeps printing OK — they only ever look at `logo/`. The answer is
   one writer (`sync_package_icons.py`, byte-for-byte, never a resample), **one** source for the
   size list (`kwcapture/_icons.PNG_SIZES`, read by the generator itself), and `--check` inside
   `tests/test_icons.py`. The part that cost the most thinking: **a guard that runs only on the
   machine that made the artefact guards nothing**, so that suite is now a CI step and CI also
   asserts both built artefacts carry the 10 files.
37. **An icon size is a theme's declaration, not a taste list.** The package ships 16/24/32/48/64/
   128/256/512 because those are the directories `/usr/share/icons/hicolor/index.theme` declares,
   and the mark now has renders at every one of them (it used to exist only from 128 up, which is
   how the small sizes ended up being filled by a different drawing). A size that is invented — or
   one the theme declares that you skipped — is an icon that exists on disk and still never
   appears. Same animal as gotcha 30: a lookup driven by an `index.theme` nobody had read.
38. **A build script has no authority to make a branding decision.** Round 12 shipped the
   mark's *monogram* as the icon set — `glyph-*.png`, `kwcapture-mark-mono.svg` — on the strength
   of a real measurement (`APTURE` is mush below ~64 px, and a circular crop clips the lockup).
   The measurement was right; the conclusion was not this project's to draw. Owner's rule,
   2026-10-11: the icon is `kwcapture-mark.svg`, and the only permitted transforms are resize and
   re-render — so the cost is written down as a consequence and the artwork stays. Two guards so
   it cannot quietly happen again: `icon/build.sh` re-renders the mark at all nine sizes and
   compares **pixels**, and `tests/test_icons.py` asserts the shipped scalable SVG is
   `logo/kwcapture-mark.svg` byte for byte and every shipped PNG is that mark's render of its
   size. Generalises: **when a measurement appears to contradict the owner, document the
   measurement and ask; never route around the decision in a Makefile.**
39. **`montage -title` does not draw at the `-pointsize` you passed, and it crops what overflows in
   silence.** Rewriting the ladder figure (README §8) for Round 13 produced a title whose ink spanned
   `x 0 → 703` of a 704 px canvas — characters amputated at **both** ends, exit 0 — for a title
   Pillow measures at 491 px in DejaVu Sans 18. The old figure had shipped that way: 512 px wide and
   reading "…d mark (top) vs the monog…", i.e. the caption whose whole job is to say *NOT an icon*
   was itself cut off, and it went into the README unchallenged because `montage` said nothing.
   Related: a `-label` wider than art + 2·border runs **under** the neighbouring cell (the first fix
   here overlapped "monogram 128px" onto its neighbour). Fix in `preview/build.sh`: size labels from
   Pillow's metrics against the real tile width, montage the body **without** `-title`, then draw the
   title with Pillow at a size solved from the same metrics and asserted to fit before it is drawn.
   Found by looking at the image and then by measuring ink extents per row band with PIL — not by an
   exit code, which is the point: gotcha 24 and gotcha 30 again, in the one tool this folder uses for
   *presentation*. **A figure is an artefact: check its pixels like any other.**
40. **A check keyed on a colour *literal* goes blind on a recolour, and it goes blind quietly.**
   `render_agreement.py` decided which path was "the green half" with `fill.startswith("#00a")`.
   That is true of `#00ac4e` and false of `#008c46` — so the first thing the P2 recolour did was
   switch off the only check that can see *where* an engine paints, and it did so at exit 0, with a
   clean report, on the files that were supposed to be the reason for running it. `validate_logo.py`
   had the same class of assumption in its pixel classifier. Repaired structurally, not by updating
   the literal (which would go blind again at the next palette): `palette()` reads `GREEN`/`BLUE` out
   of `gen_logo.py`, the classifier matches **hue** rather than a prefix, and it refuses to guess
   when the palette cannot be found. Corollary for anyone adding a colour assertion anywhere in this
   folder: **the palette may be read, never repeated** — and the reason a recolour is cheap to prove
   is that the geometry checks do not mention colour at all.

### 29 — impossible errors: re-run before you believe (Round 10)

The two messages that killed two sessions and could not be reproduced in ~570 runs
(`IndexError: list index out of range`, `TypeError: '<=' not supported between instances of
'float' and 'list'`) **were reproduced on 2026-10-11**, both, in
`validate_logo.py` → `box_check` → `gen_logo.find_box` → `convex_hull`, at `cr(...) <= tol` —
a path that **never touches fonts**, so gotcha 28's glyphset is not the cause of *these*, and
independently:

* in a **70-line extract** of `parse_points` + `convex_hull` with **no numpy and no fontTools
  imported**, where `tol` is a local float computed from local floats and provably cannot be a
  list;
* once not as a Python error at all but as **`Fatal Python error:
  _PyEval_EvalFrameDefault: Executing a cache.`** — CPython reporting that it tried to execute
  an inline-cache slot as an instruction, which no correct Python program can cause.

Rates measured here, in three samples: **2/5, 0/12, 2/40** validator runs on
`kwcapture.svg`; 2/7 and 1/8 for the extract. **Bursty, not steady** — which is exactly why
every session that met it once concluded "unreproducible" and moved on.

So the honest summary of the two dead sessions' bug: an *impossible* error in this folder is
evidence **about the machine** until a re-run says otherwise. Suspects on this desktop,
measured and **not** proven: `LD_PRELOAD=libgtk-nocsd.so.0` in every process, and non-ECC RAM
(`EDAC ie31200: No ECC support`). What is *not* in doubt is what to do about it:

* **Re-run before you believe a crash, and before you believe a clean run either.** One run of
  `validate_logo.py` is not evidence about a flake; N runs are.
* **The crash-naming in gotcha 26 is what made this findable at all** — the check told us its
  name and left the frame. That guard paid for itself the day after it was written.
* **Do not "fix" `convex_hull` for this.** There is nothing to fix there: the operands the
  message describes cannot be built from that source. A defensive `try`/retry around
  `box_check` would hide a machine fault inside the artwork's toolchain, which is the same
  mistake as trusting a check that agrees with you (gotcha 22).
* A **third** message arrived later the same day, in a different check: on a `--c-paint clip`
  file, `CRASH in colour_check: TypeError: 'list' object cannot be interpreted as an integer`,
  1/25 runs. Three shapes, three checks, one fault.
* Related, and more troubling than the crashes: in one run the colour split printed
  `stem area 0.03% blue` where every other run — 240 in-process and 70 fresh-process repeats —
  prints `0.00%`. A **silent numeric wobble** on identical input is worse than a crash, and it
  is under the 0.5% threshold, so nothing failed. Treat a marginal number here as "re-run",
  not as "evidence".

## Expected numbers (so drift is obvious)

Re-measure with `python3 logo/validate_logo.py [file]`; these are what a good run prints.

```
kwcapture.svg   (gen_logo.py, from kwcapture-sketch.svg)
content bbox : 51.55,99.83 -> 87.13,129.96   (35.58 x 30.13 mm)  = the monogram's own box
scale        : 11.918 px/mm
ink          : 44.0,76.5 -> 468.0,435.6  on 512x512   padding L 44.0 R 44.0 T 76.5 B 76.4
   #kw  44.00..468.00 x 76.45..435.56   #a  262.31..297.74 x 199.56..245.37
   #wordmark 282.61..444.09 x 76.46..214.71
clearances   : kw<->a 57.09 px | kw<->wordmark 68.65 px | a<->wordmark 11.43 px
type check   : A height 39.33 px vs cap 39.83 px (ratio 0.987)
               A width  39.12 px = 0.982 x cap  (= the face's own capital A, 3.282 mm)
               cap line delta -0.01 px | baseline delta -0.51 px   (A == the letters)
colour split : solid 10 pts == C_RING from kwcapture-sketch.svg, 100.0% on ink,
               stem area 0.00% blue (one run said 0.03%: gotcha 29), samples stem 3/3 green |
               C 6/6 blue | W 3/3 green
render       : QtSvg 44.0% blue | MSVG 44.8% blue  (both colours present in both)
   fills     : #kw #008c46, #kw-c + #a + #wordmark #7f7fff   (palette P2, 2026-10-11;
               was #00ac4e / #0000ff -- geometry identical, these two lines are the only
               ones in this block that moved)
box check    : NO LINE AT ALL, and that is correct here - kwcapture-sketch.svg has no helper
               box, so box_check returns [] without printing (gotcha 30). A missing line is
               also what a mis-named or absent sketch produces, which is why absence is not
               proof of containment.

kwcapture-mark.svg   (--mark, from kwcapture-mark-sketch.svg)
helper box   : base 24.9175 x 7.7857 mm, slope -43.1249 deg, lower-left corner inside the W
               NOT a rectangle: top edge 0.62 deg off parallel, so the headroom over the
               base falls 7.920 -> 7.651 mm along the length (see *The height fill*)
fit          : cap 4.310 mm = 100% of the box length, 55.4% of its nominal height;
               placement centred across / centred along; ink 24.631 of the 24.918 mm length
height fill  : x1.753 across the baseline (the mean height wants x1.784 and spills 1.6 px),
               ink band 4.365 -> 7.652 mm = 98.3% of the box height, seated on the base line
               monogram clearance 0.792 mm before the fill, 0.810 mm after (floor is 0.50)
ink          : 7.5,60.1 -> 504.5,451.9   padding L 7.5 R 7.5 T 60.1 B 60.1
               #kw 7.45..451.08 x 100.97..451.93 | #a 256.95..327.62 x 234.36..321.51
               #wordmark 276.93..504.55 x 60.06..281.35
clearances   : kw<->a 9.68 | kw<->wordmark 73.13 | a<->wordmark 14.91 px
box check    : closest ink -0.03 px from the box edge (the A's tip against a leaning edge)
type check   : height fill x1.753 off #type, along-baseline factor 1.0000; then, UNSTRETCHED:
               A height 51.37 vs cap 52.02 px (0.987), A width 51.09 = 0.982 x cap,
               cap line +0.01, baseline -0.64
colour split : solid 10 pts == C_RING from kwcapture-mark-sketch.svg, 100.0% on ink,
               stem area 0.00% blue, samples stem 3/3 green | C 6/6 blue | W 3/3 green
render       : palette line first -- green #008c46 / blue #7f7fff, read off gen_logo.py
               QtSvg green 20460 blue 23315 -> 53.3% blue
               MSVG  green 20796 blue 20625 -> 49.8% blue
               (mono, from `--monogram --out /tmp/…`: 39.3% / 39.5%; ~0% of either colour in
                some renderer = that renderer is ignoring a feature, gotcha 25, not that the
                logo is wrong. Round 13 measured 53.6 / 50.3 on the old palette: the geometry
                lines above are byte-identical to that round's, which is what a "paint-only"
                change looks like in this table)
sweeps       : --inset 0.25 / 0.5 / 1.0 -> x1.731 / x1.708 / x1.660 (all inside)
               --max-stretch 1.35 -> 75.7% of the height; --min-clear >= 0.9 -> smaller cap,
               still centred, still inside (AGENTS.old.md A.3 has the table)
               --no-height-fill -> byte-identical to the pre-fill mark (lam = 0 is identity)

icon/ - the shipped set, ONE artwork (Round 14: bash logo/icon/build.sh, then magick identify.
       Every byte size below is palette-dependent and every one was re-measured on P2; the Round
       13 numbers were 5 836 / 12 342 / 27 201 / 59 849 for 128/256/512/1024)
kwcapture-mark-{16,24,32,48,64,128,256,512,1024}.png
                         719 / 1 133 / 1 553 / 2 197 / 3 056 / 6 610 / 14 010 / 30 485 / 66 631 B
                         16 is PaletteAlpha, above that TrueColorAlpha; corner alpha 0 ==
                           real transparency (gotcha 31: -b none would have made it 255 + white)
favicon.ico              16 / 24 / 32 / 48 / 64 px, 34 494 B (unchanged: an indexed 16 px frame
                           and a container -- a recolour that does not add a colour to the 16 px
                           palette does not change its size), PaletteAlpha at 16 and
                         TrueColorAlpha above (five sub-images is the point of an .ico;
                           frame[0] is pixel-identical to kwcapture-mark-16.png - verified with
                           `magick compare -metric AE`, 0 differing pixels)
apple-touch-icon.png     180x180 TrueColorAlpha 11 446 B   (mark at 142 = 79%, corner alpha 0;
                           ink 6 971 px, of which 5 857 chromatic)
pwa-192.png              192x192 10 775 B (mark at 151; ink 7 790 / 6 634 chromatic)
pwa-512.png              512x512 34 044 B (mark at 404; ink 48 623 / 45 113 chromatic)
maskable-512.png         512x512 TrueColorAlpha 34 044 B   (mark at 404: inside the 80% safe
                           zone, which caps at 410 - byte-identical to pwa-512 by construction)
github-avatar-400.png    400x400 TrueColorAlpha 25 293 B   (mark at 316; clipped ink under
                           GitHub's inscribed circle: 0 px, on P2 as on the old palette.
                           ink 30 607 / 27 840 chromatic. Full bleed: 4 015 px, 45.6 overshoot)
github-social-preview    1280x640 TrueColor 84 871 B      (GitHub's limit is 1 MB)
contact.png              1106x240 TrueColor 49 728 B      (6 cells x 1 row)
build.sh's own guard:    "all nine mark PNGs are pixel-identical to a fresh render of
                           kwcapture-mark.svg" (exit 1 otherwise - gotcha 38)
tiles.py's mask guard:   clipped px 0 on avatar / maskable / apple-touch, else exit 1
FIT sweep (`python3 logo/icon/tiles.py --sweep`, run on both palettes with the same instrument):
  largest artwork that loses no ink: 322/400 (0.805), 413/512 (0.807), 143/180 (0.794) -> the
  worst of the three is 0.794, so FIT 0.790 has 1 px / +0.4 % of the side in hand. THE ANSWER DID
  NOT MOVE with the recolour -- but it was re-measured, not assumed: antialiasing is a blend of
  ink with ground, so a different green is a different halo, and this is the constant that a
  paint-only change could have quietly broken (the warning is in tiles.py above the constant).
contrast -- re-measured on P2 by `python3 logo/contrast_report.py`, which reads the constants out
  of gen_logo.py and exits 1 if any cell drops under --min (default 3.0). Run the old pair
  through the same tool to reproduce Round 11's numbers: `contrast_report.py '#00ac4e' '#0000ff'`.
  #008c46 vs #ffffff 4.34:1 | vs #0d1117 4.36:1 | L 0.1920
  #7f7fff vs #ffffff 3.29:1 | vs #0d1117 5.75:1 | L 0.2691
  #008c46 vs #7f7fff 1.32:1   (the split; hue carries it, not lightness)
  both halves inside the legal-on-both window [0.1164, 0.3000], whose ceiling is 2.10:1 of split
legibility of the word, rendered (`preview/ladder-icon.png`; the monogram row is the CONTROL in
that figure, not a shippable icon):
  128 px legible | 64 px marginal | 48 px and below mush -- and the mark ships there anyway.
  That cost is the owner's to accept; substituting a drawing is not the build's to choose.
that figure's own pixels (gotcha 39): 704x512, title ink x 80..622 of 704 -- 80 px of air each
                           side, measured per row band with PIL, because `montage -title` had
                           been cropping it at BOTH ends at exit 0. Labels 128px-art tiles at
                           pointsize 18 (Pillow-measured); the title is drawn by Pillow at 20,
                           widest line 546 px of 704. (Re-measured on P2: the ink extents are the
                           Round 13 numbers exactly; the canvas grew 12 px because every title in
                           the script now goes through the same `draw_title()` band, which is
                           2 lines here and was 1 line in the figure Round 13 shipped.)
the other figures, same guard, same session: ladder-kwcapture 950x302 (title 671 px of 950),
                           ladder-mono 950x302 (830 px of 950 -- the honest caption is long),
                           on-dark 864x458 (657 px of 864), and all three print their measured
                           extents at build time. on-dark's title is generated from
                           contrast_report.py: `green 4.36:1 blue 5.75:1 (on white 4.34 / 3.29)`,
                           and build.sh REFUSES to draw it if any cell is under 3:1 -- a caption
                           that can go stale is a caption that will, so the number in the picture
                           is computed by the tool that draws the picture.

the copy that ships inside the Python package (Round 13: python3 logo/sync_package_icons.py;
sha256 first 16 of the SOURCE, also written into kwcapture/icons/COPYING.md)
(the Round 13 hashes are in this file's history and in kwcapture/icons/COPYING.md's previous
revision; these are P2's, from `python3 logo/sync_package_icons.py` on 2026-10-11)
hicolor/16x16/apps/kwcapture.png       719 B   bfa24ffcff355d2b   (== icon/kwcapture-mark-16.png)
hicolor/24x24/apps/kwcapture.png      1 133 B  971edc2459731859
hicolor/32x32/apps/kwcapture.png      1 553 B  8a10ce882a45b21e
hicolor/48x48/apps/kwcapture.png      2 197 B  bec1f331e2a35f43
hicolor/64x64/apps/kwcapture.png      3 056 B  48610cbfeabb9bc7
hicolor/128x128/apps/kwcapture.png    6 610 B  52ff201781b802ac
hicolor/256x256/apps/kwcapture.png   14 010 B  71a9c08c81063a79
hicolor/512x512/apps/kwcapture.png   30 485 B  eebdc9b3057bd6df
hicolor/scalable/apps/kwcapture.svg   3 797 B  3c6ee5d0d964ba09   (== logo/kwcapture-mark.svg,
                           the logo itself, copied verbatim -- asserted by tests/test_icons.py.
                           Same byte count as the old palette, different bytes: the SVG's only
                           content that changed is two `fill=` attributes and a comment)
sync_package_icons.py --check          "checked 9 icon files (0 written now)", exit 0
tests/test_icons.py                     98 checks, 0 skipped here (89 + the 9 one-artwork
                                       assertions). CI, measured off the log of the push that
                                       changed the suite (34432a8, run 38122958295): **97 passed +
                                       1 skipped** - `RESULT: all icon tests passed (1 skipped)`,
                                       the skip being `[SKIP] desktop-file-validate  tool not
                                       installed`, printed rather than passed quietly. The
                                       89-check version measured 88 + 1 on the same runner.
probe/sabotage_icons.sh                10 sabotages, 10 detected, tree restored
built wheel + sdist                    10 icon files each (8 png + 1 svg + COPYING.md) and CI
                                       says so too (`wheel: 10 icon files`, `sdist:
                                       kwcapture-0.6.0.tar.gz 10 icon files`); `logo/` in neither,
                                       verified locally with unzip -l / tar tzf as well, and on
                                       P2 also byte-compared: every PNG in the wheel `cmp`s to its
                                       `logo/icon/kwcapture-mark-<N>.png` and the wheel's scalable
                                       entry `cmp`s to `logo/kwcapture-mark.svg`
```

`validate_logo.py` exits non-zero on: a collision (< 1.5 px), ink outside the artboard,
off-centre artwork, the A failing the type check, ink > 1 px outside the helper box, a colour
split that fails any of its five assertions, a render where a viewer would not show both
colours, or **a check that crashed** (gotcha 26). Also run `xmllint --noout`, and render the
ladder 512/256/128/64/32 (`preview/ladder-*.png`): the wordmark stops being readable around
128 px. That is a measurement, not a licence — the shipped icon is the mark at those sizes anyway
(owner's rule, gotcha 38), and the mono row in `preview/ladder-icon.png` is the CONTROL in that
figure, never a deliverable.

## Re-sketching

If you replace `kwcapture-sketch.svg`, `gen_logo.py` reads it **by Inkscape path id**:
`path1` (or `kw`, the id the redrawn mark sketch uses) = the K+W monogram, `path10` (or
`cursor`/`a`) = the pointer. Keep those ids or extend `pick()` in `build()`; a sketch with
neither now says which ids it looked for and which it found, instead of throwing `KeyError:
'path1'` from three frames deep. Everything else in the sketch is ignored on purpose — the
letters come from the font. `--monogram` needs no pointer, so
`--monogram --sketch logo/kwcapture-mark-sketch.svg` gives you the **mark's** monogram as a
favicon (verified working, 2026-10-11 — from the repo root; see the `--sketch` path trap in
*Regenerating*). The two sketches' monograms differ, and which one is *the* identity is an
open item below, not a crash.

If you change the drawing's **vertex count**, `len(verts) != 19` refuses to build: the letter
rings are vertex indices and must be re-checked by the owner, not guessed by you (gotcha 22).

## Reading the transcript — `logo/*.jsonl`

Raw exports of the sessions that built this mark: one JSON object per node, and **most of the
bytes are base64 PNG screenshots pasted into messages**, so `cat`/`read_file` on it fills a
context window and teaches you nothing. **Never hard-code the name** — it is re-exported under
a new one every session (`logo_talk.jsonl`, `logo_chat.jsonl`, now `prev_logo.jsonl`), and it
is the newest file in the folder. Take the biggest:

```bash
cd logo
T=$(ls -S logo/*.jsonl | head -1)          # the biggest transcript IS the current one
# every message the owner sent, in order (the brief, in their words)
python3 - "$T" <<'EOF'
import json, re, sys
for line in open(sys.argv[1]):
    m = json.loads(line).get("message", {})
    if m.get("role") == "user":
        print("----", re.sub(r'data:image[^"]*', "[IMG]", str(m.get("content")))[:800])
EOF
# what a dead session was *about to* write: its unapplied tool-call arguments
tail -n 4 "$T" | python3 -c '
import json, sys
for l in sys.stdin:
    for tc in (json.loads(l).get("message", {}).get("toolCalls") or []):
        fn = tc["function"]; print("===", fn["name"], "|", fn["arguments"][:1500])'
```

Fields: `message.role` (`user`/`assistant`/`tool`), `.content`, `.timestamp`, and the two that
rescue a dead session — **`.reasoningContent`** (what it was trying to do) and
**`.toolCalls[].function.arguments`** (arguments survive a truncated call, so an unapplied
edit can be read straight back out). To find a word without reading a range:
`grep -o '"content":"[^"]\{0,240\}anchor[^"]\{0,240\}' "$T"`. Traps: the first object is a
session header with no `message` key and `wc -l` under-reports by one (no trailing newline) —
that is the file, not a bug; a regex containing `"` cannot go inside a `python3 -c '…'`
one-liner, because the first `"` closes the Python string.

**Resuming a session that died out of tokens** (happened twice, Rounds 6 and 9): find the last
real user brief — `role == "user"` and **not** `isSynthetic` (the "Set working directory to…"
lines are synthetic); then read the tail's `reasoningContent`, which is usually further ahead
than any file it managed to touch; then **re-run everything it claimed**. A dead session's
*question* is usually right and its *measurements* are stale. **The transcript is history, not
evidence**: it contains measurements made against broken code. Anything lifted out of it gets
re-run against `gen_logo.py`/`validate_logo.py` before it lands here — that is how Round 6
caught the four stale claims of gotcha 18. Full version, including the field-by-field walk:
[`AGENTS.old.md` Part D](AGENTS.old.md).

## Still open

* **MSVG paints the type 26–67 px out of place (gotcha 27) — fix it or accept it? Owner's
  call.** (a) Accept: KDE, Inkscape, browsers and delegated ImageMagick are correct; only IM's
  internal MSVG coder is wrong, and `librsvg2-bin` fixes IM. (b) Emit a second,
  **transform-free** artefact (say `kwcapture-flat.svg`) for pipelines using bare ImageMagick,
  leaving the transform-carrying files as the source of truth. (c) Bake transforms into every
  file — makes MSVG agree, spends the mm-space C polygon, the `#type` transform `band_check`
  measures from, and the same-path-data invariant. **(b) is the recommendation**: it buys the
  compatibility without spending an invariant, exactly as `--c-paint solid` did.
  `python3 logo/render_agreement.py` is the instrument and **exits 1 until this is decided**, so
  the finding cannot be quietly forgotten. Re-confirmed 2026-10-11: 26 px and 67 px, and re-confirmed
  again the same day **on palette P2** — a recolour cannot touch this bug, because a renderer that
  mis-applies `rotate()` does not care what colour it is rotating. What a recolour *can* touch is
  the instrument: `render_agreement.py` identified the green half with `fill.startswith("#00a")`,
  which the new green defeats, so it had been comparing nothing while exiting 0. It reads the
  palette out of `gen_logo.py` now, so the next palette cannot disarm it either (gotcha 30).
* **The flake (gotcha 29): cause still not established — but it is no longer "unreproducible".**
  Both historic messages came back on 2026-10-11 in a code path that never touches fonts, and
  in a pure-Python extract with no third-party imports, plus one CPython-level
  `Executing a cache` abort. Next steps, in order and cheap: (1) run the validator ~200× under
  `env -u LD_PRELOAD python3 …` and on a second machine; (2) once under
  `PYTHONMALLOC=malloc_debug`; (3) look at the machine, not the code (this desktop: a global
  `LD_PRELOAD` shim, non-ECC RAM). Keep the `CRASH in <name>` guard: it is the reason this is
  now diagnosable at all. **Do not wrap `box_check` in a retry** — that launders a machine
  fault into a passing build.
* **Does the mark actually read as CAPTURE? Still no stranger test.** The whole word depends on
  the junction, and the redrawn one is geometric where the original's soft corner did the work.
  Round 8's read was "it reads as a C at 512 px", Round 7's opposite read was struck as the
  product of a wrong ring, and my read today, looking at `preview/kwcapture-mark-512.png` on
  white with the same warning label attached (**unverified: one model's read, and being told to
  look for a C biases you**), is "**KW** + a cursor + **APTURE**": the blue bracket reads as a
  C only once you are told. Ask someone who has never seen the sketch *what does it say* and
  write the answer here. If it is not CAPTURE, in order: `--no-c-split` (is the green stem
  splitting the KW into `| <` + `W`?), then a **sketch** change — colour cannot curve a stroke,
  and THE RULE still says repair the junction rather than add letters.
* **Is `×1.753` the right amount of stretch?** A taste call currently made on a number, not an
  eye: the type is visibly condensed (the rendered A 0.55 × as wide as tall) and the pointer
  reads more like a cursor than like the letter A — the one thing the A rules exist to prevent.
  Three positions on the same box: `--max-stretch 1.35` (75.7% of the height, letters barely
  notice), `1.5`, and the shipped full fill — see `preview/variants-type.png`. Fold into the
  stranger test above: ask what the mark says **and** whether the third glyph is a letter or a
  mouse.
* **The two monograms: ruled and now executed (Round 14, 2026-10-11) —
  `logo/kwcapture-mono.svg` is deleted.** The owner's words: *"Unofficial variant and historical
  value only, safe to delete if you prefer."* So the committed SVGs are `kwcapture.svg`,
  `kwcapture-mark.svg` and the two sketches, and nothing else: the monogram is a **mode**
  (`--monogram`) and a **control** in the legibility figures, not a deliverable. `--monogram` now
  **requires `--out`** and says why in its refusal, because a mode whose default path re-creates a
  deleted artefact is gotcha 38 waiting to happen again. `preview/build.sh` and
  `render_agreement.py` render it into a temp directory, and doing that exposed a thing the single
  file name had been hiding: the figures were using **two different monograms** — the original
  drawing (`kwcapture-sketch.svg`) in the size ladders, the redrawn mark's monogram
  (`kwcapture-mark-sketch.svg`) as the ladder-icon control row. They are `mono-orig` and `mono-mark`
  now, each with its own `--sketch`, because two names that are one file is how a figure ends up
  measuring something other than what it says. History is intact:
  `gen_logo.py --monogram --out /tmp/mono.svg` reproduces the drawing byte for byte, and
  `git log --diff-filter=D -- logo/kwcapture-mono.svg` recovers the file.
* **Small sizes: ruled, and closed (2026-10-11).** Asked whether the unreadable `APTURE` at 16 px
  was worth anything, the owner's answer was *"Why bother? There's no way it would be readable at
  that low resolution."* So: the mark ships at 16 px with the word mush, permanently, by decision.
  The ladder stays as the measurement of what that means and nothing in the pipeline may "fix" it —
  see gotcha 38. If a legible 16 px asset is ever wanted it is a **new mark from the owner**, not a
  crop, not a monogram, not a build-script default.
* **PALETTE P2 — APPLIED (Round 14, 2026-10-11), and the dark-mode finding it closed is
  closed.** Green `#00ac4e → #008c46`, blue `#0000ff → #7f7fff`; the owner picked the pair from
  six rendered on white and on `#0d1117`, this round applied it and re-measured everything paint
  can move. The numbers, from `python3 logo/contrast_report.py` (which reads the constants out of
  `gen_logo.py`, exits 1 if a cell falls under `--min`, and reproduces the old pair if you hand it
  the old hexes): green **4.34** white / **4.36** dark, blue **3.29** / **5.75**, split **1.32**;
  every cell clears the WCAG 3:1 non-text floor on both grounds, where the pair it replaced had
  two failures (blue **2.20** on dark, green 3.00 on white). Paint only, and proved as paint only:
  the hex-stripped diff against the previous commit is empty.
  **What P2 bought and what it paid, because the trade is the thing to remember:** it bought a mark
  that is legal on every ground a host uses, and it paid split strength, **2.87 → 1.32**. The C
  now separates from the green by **hue** (240° against 150°) and not by lightness — so in
  greyscale, or through any pipeline that flattens saturation, the two halves become near-identical
  and the first letter of CAPTURE goes with the distinction. `contrast_report.py` prints a
  dichromatic estimate (Viénot/Brettel LMS — a smoke test, not a person): ΔE76 117 / 116 /
  33 and ratios 1.15 / 1.27 / 1.08 for protan / deuteran / tritan, i.e. the split survives the
  simulation by hue while the lightness separation does not. If a future round ever needs the loud
  two-tone back, it is an owner decision about *which ground to fail on*, not a recolour to be
  slipped in — and this is why.
  **The arithmetic that was mistaken for a law, now corrected in `README.md` §8.** That section
  said *"no ground wins both colours"*, which was true of the pair it measured and read as if no
  pair could. A colour clears 3:1 on white at L ≤ **0.3000** and on `#0d1117` at L ≥ **0.1164**;
  the window **[0.1164, 0.3000]** is not empty — both P2 halves are inside it (0.1920, 0.2691).
  What the window really forbids is *loudness*: two colours inside it can separate by at most
  **2.10:1**. "Both halves legal on both grounds" and "a strong two-tone split" are in tension by
  arithmetic; the old split was strong precisely because its blue sat **outside** the window, too
  dark for dark grounds.
  The greens measured before the owner chose, all keeping `#7f7fff`, kept because the reasoning is
  the useful part and because someone will propose a fifth green: `#00ac4e` 3.00/6.32, split 1.10
  (fails white); `#008c46` 4.34/4.36, split 1.32 — **chosen**, the balanced one; `#007a3d`
  5.45/3.47, split 1.66 (starts to read as forest rather than brand); `#007038` 6.22/3.04, split
  1.89, the last green that still clears dark. And the proposal that started it, `#00ff00`: not the
  *darkening* the owner asked for but the brightest green a byte holds (L 0.715 vs the old 0.301),
  **1.37:1** on white — and white is the ground of every tile in `icon/`, of the social card, of
  GitHub-light and of PyPI. Measured: pixels under 1.5:1 against white went 1.6 % → 47.9 % at
  512 px and 20.5 % → 57.5 % at 16 px. It was measured rather than obeyed and sent back with the
  awkward half included (gotcha 38 working as intended); the owner then chose from six pairs, which
  is the correct order of operations.
  **Still owed by this palette, and not by this round:** the GitHub social preview is a stored
  **upload**, so the live one is still the *old* palette until the owner re-uploads
  `icon/github-social-preview.png` — see the item below, and the root `AGENTS.md`.
* **`--c-paint`'s `--help` text is wrong** (says `mask (default)`, claims mask ≡ solid). The
  default is `solid` and the matrix above is the truth. One-line fix in `gen_logo.py`; left
  alone in a documentation round so the code stays byte-stable while its docs are re-checked.
* **Make the box check announce its skips (gotcha 30).** `box_check` should print
  `box check: SKIPPED (no <name>-sketch.svg)` / `(no parallelogram in that sketch)` instead of
  returning `[]` silently, so a mis-named sketch, a renamed artefact and a copy in `/tmp` cannot
  look like a passing containment test. Better still: for a file that was built by `--mark`, no
  sketch should be an error, not a shrug. Not changed in code this round — the fix is trivial and
  the *documentation* of the current behaviour is what was wrong ("it prints a line either way").
* **`--sketch`/`--out` are literal paths** while the defaults are script-relative, so the
  documented `--sketch logo/…` needs cwd = repo root. Either resolve them against `HERE` when
  they do not exist, or keep the README's warning. Documented in `README.md`, not changed in
  code.
* **`kwcapture.svg`'s `stem area` printed 0.03% once, 0.00% every other time** (240 in-process,
  70 fresh-process runs). Under the 0.5% threshold, so it never fails, but "identical input,
  different number" deserves its own hunt alongside the crash above.
* **The mark's word touches the near end of the box** — the A sits on the box's edge, which is
  what "as large as possible" bought. Want breathing room inside the band instead? That is
  `--inset 0.5` (mm), and it costs type size *by definition*: `--inset 0.5` also takes the
  height fill from ×1.753 down to ×1.708. `--align` is not free and never was safely: `top`
  buys clearance by spilling over the box's top edge, so it is now rejected (gotcha 24), and
  raising `--min-clear` costs cap height instead of containment.
* **The logo is referenced from outside this folder as of Round 11, and `logo/` is committed.**
  The root [`../README.md`](../README.md) opens with `logo/icon/kwcapture-mark-256.png` as an
  absolute `raw.githubusercontent.com` URL — absolute on purpose, because PyPI renders the same
  README and does not resolve repo-relative image paths, so the header 404s on any branch that
  has not been pushed to `main`. Derived PNGs are committed in **two** places, `preview/` (docs)
  and `icon/` (shipped); both are generated, so regenerate rather than hand-edit, and a stray
  `inkscape x.svg -o x.png` in some other directory is still wrong. `logo/*.jsonl` remains
  gitignored (verified again 2026-10-11 with `git check-ignore -v` and `git add -A --dry-run`,
  which staged 28 files in `icon/` and no transcript). **The rule is name-agnostic on purpose**:
  a transcript lands here every session under a *different* name, and the root rule
  `chat_his*.jsonl` matched exactly one of them — see the 2026-10-06 incident in the root
  `AGENTS.md`, which is why this line exists.
* **`tests/test_kwcapture.py`'s `alpha is opaque` is failing on this desktop, and it is not a
  logo bug (found 2026-10-11, Round 14, reported rather than patched).** The check is
  `check("alpha is opaque", int(arr[..., 3].min()) == 255)` on a live full-screen grab, and KWin is
  returning **alpha 253/254** at exactly four pixels — (284,1144), (2275,1144), (289,1149),
  (2270,1149) — which are the bottom corners of the System Monitor window
  (`1992x907+284+243`, so its bottom edge is y=1149 and its corners are x=284 and x=2275): the
  rounded-corner composite bleeds sub-opaque alpha into the screenshot. It is there in **24 of 25**
  grabs while that window is up; the suite therefore fails ~2 runs in 3 and passes when the desktop
  happens not to have such a window. Proven unrelated to this round: the same check fails 7 of 8
  times from a **pristine `git worktree` of `HEAD`** with none of the recolour's changes, and
  nothing under `kwcapture/` or `tests/` is modified by P2 (only `kwcapture/icons/`, which is data).
  **Not touched, on purpose**: tightening an assertion to make a red suite green is how a real
  bug — is the alpha channel of a compositor grab *allowed* to be non-opaque at a window corner,
  and does anything downstream assume 255? — gets archived as a passing test. Owner's call, in
  order: (a) leave the check and treat the failure as environmental, which costs a red suite every
  time a rounded window is on screen; (b) assert what the code actually guarantees on a controlled
  surface (a solid capture, or `min()` over a grab of a known-opaque region) and add a separate,
  explicitly-labelled check for the live-desktop case; (c) investigate whether KWin's BGRA grab
  alpha at rounded corners is expected, and write the answer down. (b) is the recommendation, and
  whichever way it goes belongs in a round that owns `tests/`, not in a recolour.
* **GitHub social preview: the mechanism is DONE, the image is STALE — owner, re-upload it.**
  Round 13 verified the whole loop end to end: *Settings → Social preview* was clicked,
  `usesCustomOpenGraphImage` is `true`, `openGraphImageUrl` is a
  `repository-images.githubusercontent.com/…` URL, and the bytes that URL served were 1280×640
  and **0 of 51 681 sampled pixels differed** from `icon/github-social-preview.png`. That closed the
  item gotcha 34 said no script could close — and palette P2 has just reopened it, because what
  GitHub stores is the **upload**, not a render of the repo. The file in this folder is the P2 card
  (**84 871 B**); the live card is still `#0000ff`-and-`#00ac4e`. **Action:** re-upload
  `logo/icon/github-social-preview.png`, then re-run the query in `README.md` §8 *and* the pixel
  comparison — the flag only proves *an* image is set, the pixels prove it is *this* one, and
  right now a `true` flag would mislead exactly as a stale caption does (gotcha 39). Same story for
  the optional user profile picture (`icon/github-avatar-400.png`, P2: 25 293 B): an account
  setting, no check can reach it, and no script pretends to (gotcha 34).
* **The package wiring is done (Rounds 12–13); PyPI's display of it is not measured.** The mark
  set — nine renders plus the SVG itself — now ships inside the package (`../kwcapture/icons/`) and
  `kwcapture install-desktop` puts it in the user's hicolor theme, so the artwork has a consumer
  that is not a README. Whether PyPI renders a *project icon* from any of that is **untested** — do
  not write that it does. The docs header remains the only displayed consumer verified end to end.
* **Icons go through ImageMagick or Pillow, never Inkscape for `.ico`**: `inkscape x.svg -o x.ico`
  exits 0 and writes no file (verified) — the shipped way is `bash logo/icon/build.sh`, which
  makes `favicon.ico` at 16/24/32/48/64 from the mark PNGs (frame[0] is pixel-identical to
  `kwcapture-mark-16.png`); the ad-hoc way is
  `magick -background none logo/kwcapture-mark.svg -define icon:auto-resize=16,32,48,64,128,256 out.ico`.
  Same species as a check that silently does not run: the exit code is not the result. And for
  transparency, do **not** pass Inkscape `-b none` (gotcha 31). (It says `kwcapture-mark.svg` here
  since Round 13; the mono it used to point at is deleted and is not an icon — gotcha 38.)
* Consider a **horizontal lockup** (monogram left, `APTURE` on a horizontal baseline) for nav
  bars — the diagonal *is* the mark's identity, so this is a separate asset, not a variant.

## Session log

Only this round's entry lives here. Rounds 1–9c (two recovered dead sessions, the anchor bug,
the falsified fit table, the renderer matrix, the MSVG `rotate()` find) are
[`AGENTS.old.md` Part C](AGENTS.old.md); Round 10's narrative is
[`AGENTS.old.md` Part G](AGENTS.old.md) and its own summary of what moved is
[Part F](AGENTS.old.md); **Round 11's** (the icon round) is
[`AGENTS.old.md` Part H](AGENTS.old.md); **Round 12's** (the desktop-icon round) is
[`AGENTS.old.md` Part I](AGENTS.old.md) — moved verbatim by Round 13, which left its **wiring**
standing and deleted its **artwork**, so read Part I for how the icon reaches a desktop and this
round's entry for what the artwork is. **Round 13's** (the one-artwork round) is
[`AGENTS.old.md` Part J](AGENTS.old.md), moved verbatim by Round 14 under the same rule; Round 14's
did not change the artwork, so Round 13's *conclusions* all still stand and are not amended there.
Read them before arguing with any number above.

**Round 13 — 2026-10-11, the one-artwork round.** Moved verbatim to
[`AGENTS.old.md` Part J](AGENTS.old.md), with its authority intact: the owner's rule that the icon
of kwcapture is `kwcapture-mark.svg` and the only permitted transforms are resize and re-render is
still *the* rule; gotcha 38 (*a build script has no authority to make a branding decision*) is the
one this folder still runs on; gotcha 39 (*never trust `montage -title`*) is still why every title
in `preview/build.sh` is drawn by Pillow. Read Part J for the story of the deleted glyphs, and the
entry below for what the round after it measured.

**Round 14 — 2026-10-11, the palette round: P2 applied.** One decision handed over written down
— green `#00ac4e → #008c46`, blue `#0000ff → #7f7fff`, the owner's pick from six rendered
pairs — with the instruction *"do not re-litigate the colour: it is chosen; your job is to apply
it completely and prove nothing broke"*. Applying a palette is the easiest round to fake: search,
replace, re-render, done. So this round is mostly the proving.

* **"Paint only" is a diff, not an adjective.** Strip every 6-digit hex from both sides
  (`sed -E "s/#[0-9a-fA-F]{6}//g"`) and `diff` against `HEAD` is **empty** — no coordinate, no
  `transform`, no `#type` matrix, not one comment re-wrapped. Two constants moved and the artwork
  moved with them: `gen_logo.py --mark` and plain `gen_logo.py` reproduce `kwcapture-mark.svg` and
  `kwcapture.svg` byte-identically, and the variant guard still refuses `--mark --green '#00ff00'`
  on a shipped path. That guard is exactly why a recolour goes through the **constants**: an SVG
  written by `--green` on a command line is an artwork no generator state reproduces.
* **The check that had gone blind was found by reading the checker, not the picture.**
  `render_agreement.py` identified the green half with `fill.startswith("#00a")` — a property of
  `#00ac4e`, not of green. On the recoloured files it matched nothing, so the tool that exists to
  catch an engine painting in the wrong place was comparing NOTHING and would have printed "all
  engines agree" at exit 0: gotcha 30, live, on the first change it would have missed. Repaired by
  deleting the hard-coded colour — the palette is read out of `gen_logo.py`, and
  `validate_logo.py` classifies rendered pixels **by hue** against it and refuses to guess when it
  cannot find it. Same reason, new file: `contrast_report.py`, because two rounds of docs had been
  quoting ratios no file could re-compute. It prints the 2x2 against white and `#0d1117`, the
  split, the window and a dichromatic estimate, and it exits 1 under `--min` so a palette
  regression cannot ship by accident.
* **Every number that could move, moved — so it was re-measured; the ones that could not, did
  not.** Render split: mark 53.6/50.3 → **53.3/49.8** % blue (QtSvg/MSVG), lockup 44.3/45.4
  → **44.0/44.8**, mono → **39.3/39.5**; every byte size in `icon/`; every sha256 in the
  package block; the `--c-paint` matrix re-run, where the two renderer bugs came through untouched
  (Qt still paints `clip` **100 % blue**, MSVG still swallows a `mask`). Geometry — ink bounds,
  clearances, the type check, the box check, the fit, the taper — is identical to Round 13's
  line for line. That half of the proof is the half a colour diff cannot give you.
* **`FIT = 0.79` was the trap, and it was measured rather than trusted.** Tiles count antialiasing
  as ink; antialiasing is a blend of ink with ground; the ground of every tile is white. So a
  recolour can clip ink while no coordinate moves. `tiles.py --sweep` on both palettes with the
  same instrument: worst tile 0.794 against FIT 0.790 — **+0.4 %** of the side in hand, clipped
  px 0 everywhere. It survived. Had it not, the answer was to re-measure the constant, never to
  crop a tile or ship a second drawing (gotcha 38 is the round that learned that).
* **What the palette was *for*, measured:** green **4.34** white / **4.36** dark, blue **3.29** /
  **5.75** — every cell over the 3:1 non-text floor, closing the oldest open finding in this
  folder (blue **2.20:1** on `#0d1117`, since Round 10). The sentence `README.md` §8 had been
  carrying — *"no ground wins both colours"* — was arithmetic about one pair of hex values,
  mistaken for a law: the window **[0.1164, 0.3000]** is not empty, both P2 halves sit in it. What
  the arithmetic really says is that two colours inside it cannot separate by more than **2.10:1**,
  so P2 buys legality by spending split strength (**2.87 → 1.32**) and the C now reads on
  **hue** (240° against 150°) rather than value. In greyscale it collapses, and that
  dependency is written down now instead of discovered in a year.
* **The monogram deletion folded in, as scheduled.** `git rm logo/kwcapture-mono.svg`;
  `--monogram` now **requires `--out`** instead of defaulting at a path that would resurrect a
  deleted artefact; `preview/build.sh` and `render_agreement.py` render the monogram into a temp
  directory the way the ladder already did. Doing it surfaced a real ambiguity: the script had
  been using *two different drawings* — the original monogram and the mark's monogram — from
  one file name, so they are `mono-orig` and `mono-mark` now, each with its own `--sketch`.
* **Reported, not routed around.** `tests/test_kwcapture.py`'s `alpha is opaque` fails on this
  desktop: 4 px at alpha 253/254 in the bottom corners of a window KWin composites there, ~96 % of
  grabs, and it reproduces on a **pristine `git worktree` of `HEAD`** carrying none of this round's
  changes. Nothing under `kwcapture/` or `tests/` was touched by P2, so the test stays as it is and
  the finding goes to the owner (*Still open*). A green suite you had to edit is worth less than a
  red one you understand.
