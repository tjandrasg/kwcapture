# logo/AGENTS.md — the kwcapture mark

Work on `logo/` only after reading this. Everything here was paid for once already.

Three files, three jobs. **This one is the working set**: the rules, the knobs, the numbers
and the open items. [`README.md`](README.md) is the user manual for the three programs and
the directory, with renders. [`AGENTS.old.md`](AGENTS.old.md) is the archive: the session
log, the falsified claims, the war story behind every gotcha.
[`LICENSE.md`](LICENSE.md) says what you may do with any of it.

> **Size discipline** (the root `AGENTS.md` says the same). This file is **68 572 bytes**
> — measured with `wc -c logo/AGENTS.md`, not remembered. It was **86 077** before Round 10's
> archive-verbatim pass, which moved 45 KB of narrative to `AGENTS.old.md` and lost nothing
> (every substantive line of the old file is present in one of the two files — checked, not
> asserted; the archive's header carries the sha256 it was cut from); **59 077** when Round 11
> opened, and **68 572** at its close. The icon round spent ~9 KB on `icon/` — two Files rows, the
> regenerate commands, five gotchas, a block of expected numbers — and paid part of it straight
> back by moving Round 10's session-log narrative (2 029 bytes, verbatim) to
> [`AGENTS.old.md` Part G](AGENTS.old.md). **A round that adds narrative also moves one out.**
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
| `kwcapture-mono.svg` | bare monogram only (still two-tone), for favicons / ≤64 px where `APTURE` is mush. Built by `--monogram`. **There is no `-mono-sketch.svg`**: it comes from `kwcapture-sketch.svg`, and the validator's fallback knows that |
| `kwcapture-sketch.svg` | the **original** hand-drawn source (Inkscape, A4): the first monogram + the mouse pointer. **Input. Never written to by any tool.** Keep it forever — the pointer (the A) still comes from here |
| `kwcapture-mark-sketch.svg` | the **second, redrawn monogram** (cleaner, geometric) plus the black helper box, drawn in Inkscape. **Input. Never written to.** Its `#kw` is *not* the same path as the original sketch's |
| `gen_logo.py` | the generator: sketch + knobs → the SVGs. Manual: `README.md` §gen_logo.py |
| `validate_logo.py` | the gate: ink bounds, clearances, centring, the A-vs-cap **type check**, the **box check**, the **colour split check** (the only check that can see paint) and the **render check** (it rasterises with QtSvg and MSVG, so a *viewer* decides). One path argument, default `kwcapture.svg` |
| `render_agreement.py` | **diagnostic, not a gate**: per engine, the ink box it paints vs the box the path data implies, per colour. Found the MSVG `rotate()` bug. Exits 1 today **on purpose** (gotcha 27) |
| `preview/` | generated PNGs for `README.md`, plus `build.sh` (one command rebuilds all of them) and `anatomy.py`. Derived artefacts: regenerate, never hand-edit |
| `icon/` | **the shipped icon set**: 23 images (logo renders, glyph renders, `favicon.ico`, Apple touch, PWA, `github-avatar-400.png`, `github-social-preview.png`, the `contact.png` review sheet) built by `build.sh` + `tiles.py` + `card.py` + `contact.py`. All derived: regenerate, never hand-edit. Manual: `README.md` §8 |
| `icon/kwcapture-mark-mono.svg` | **the glyph form of the mark** — `--monogram` fed with the *mark* sketch, i.e. the same drawing as `kwcapture-mark.svg` with the word dropped. The source of every shipped small icon, favicon and avatar. **Not** the same drawing as `kwcapture-mono.svg` (the *original* sketch's monogram) — see *Still open* |
| `README.md` | the manual: directory structure, every `*.py` program, the commands that make each image |
| `LICENSE.md` | artwork **CC BY 4.0**, tooling **MIT** (the package's own [`../LICENSE`](../LICENSE)), Inter **OFL-1.1** referenced. `*.jsonl` is licensed by nobody — §6 there |
| `AGENTS.old.md` | the archive: superseded numbers, the full gotchas, the 2026-10-10 session log. History, not instruction |
| `*.jsonl` | the design-session transcripts (here: `prev_logo.jsonl`, 2.0 MB). **A different name every session**; **never committed** (`logo/*.jsonl` is gitignored); **never read whole** — see *Reading the transcript* |
| `__pycache__/` | appears because `validate_logo.py` imports `gen_logo` to reuse the box geometry. Gitignored |

## Regenerating

```bash
python3 logo/gen_logo.py                       # -> logo/kwcapture.svg
python3 logo/gen_logo.py --mark                # -> logo/kwcapture-mark.svg   (helper box mode)
python3 logo/gen_logo.py --monogram            # -> logo/kwcapture-mono.svg
python3 logo/gen_logo.py --out /tmp/x.svg --classic       # the old look: gradient mono, black type
python3 logo/gen_logo.py --out /tmp/x.svg --no-c-split    # CONTROL: "is colour what makes the C read?"
python3 logo/gen_logo.py --out /tmp/x.svg --a-size 1.15   # experiment; repo untouched
python3 logo/gen_logo.py --mark --out /tmp/x.svg --no-height-fill   # the pre-Round-9 word
python3 logo/gen_logo.py --mark --out /tmp/x.svg --max-stretch 1.35 # the mild fill
python3 logo/validate_logo.py                            # checks kwcapture.svg
python3 logo/validate_logo.py logo/kwcapture-mark.svg    # type check + BOX check
python3 logo/render_agreement.py                         # exits 1; that is the finding, not a bug
xmllint --noout logo/*.svg                               # must be silent
bash logo/preview/build.sh                               # rebuild every README image

# the shipped icon set (README.md §8): the glyph form first, then every size off it
python3 logo/gen_logo.py --monogram --sketch logo/kwcapture-mark-sketch.svg \
        --out logo/icon/kwcapture-mark-mono.svg
python3 logo/validate_logo.py logo/icon/kwcapture-mark-mono.svg    # OK
bash logo/icon/build.sh                                  # 23 images, .ico, avatar, card, sheet
```

**Order matters in that last block**: `icon/build.sh` reads `icon/kwcapture-mark-mono.svg` and
`../kwcapture-mark.svg` and *refuses to run* if either is missing — it does not generate them,
because the SVGs are `gen_logo.py`'s job and the icon set's job is pixels only. `--sketch` and
`--out` are literal paths (the trap above), which is why the two commands are written from the
repo root.

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
| `GREEN` | `#00ac4e` | the K's stem and the W: the old gradient's end stop, so the palette did not change, only its job — colour now carries meaning (monogram vs word) |
| `BLUE` | `#0000ff` | the C, the pointer-A and `PTURE`. Chosen against its **neighbour**, not the page: 2.87:1 vs `#00ac4e` (a prettier `#3b82f6` is only 1.23 — the C dissolves into the W); 8.59 vs white; **2.20 vs GitHub dark `#0d1117`**, which still fails (black was 1.11) |

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
machine, monogram ink as % blue (the truth is 39.1–39.8%):

| renderer | `solid` | `mask` | `clip` |
|---|---|---|---|
| Inkscape / librsvg | 39.5% ✅ | 39.1% ✅ | 39.1% ✅ |
| **QtSvg** — Gwenview, Dolphin thumbnails, `QIcon`, KDE's image plugin | 39.4% ✅ | 39.1% ✅ | **100% blue ❌** |
| **ImageMagick internal MSVG** | 39.8% ✅ | **0% blue ❌** | 39.6% ✅ |

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
   uploads instead of a script that pretends. Check the API before promising an automation, and
   check *which* object owns the asset: avatars belong to a user or an org, never to a repo.
35. **A build script's report can print nothing and still leave the build green.** `icon/build.sh`
   used to end with `magick identify --format … 2>/dev/null | head -8`: `identify` wants `-format`
   with **one** dash, so with two it reads the format string as a *filename*, dies with "no decode
   delegate for this image format", and the suppressed stderr made the whole report vanish — the
   build printed its `ls` and exited 0. Fixed: one dash, stderr no longer suppressed. Measured on
   the same line: width specifiers (`%-28f`) are not supported by this ImageMagick — it prints
   `28f` and warns `unknown image property "%-"`. **Gotcha 30 one layer down**: the thing that
   reports on the artefacts can itself fail silently, so treat a report as a check — un-suppress
   its stderr and make sure its silence would mean something.

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
render       : QtSvg 44.3% blue | MSVG 45.4% blue  (both colours present in both)
   fills     : #kw #00ac4e, #kw-c + #a + #wordmark #0000ff
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
render       : QtSvg green 20319 blue 23506 -> 53.6% blue
               MSVG  green 20602 blue 20870 -> 50.3% blue
               (mono 39.4% / 39.8%; ~0% of either colour in some renderer = that renderer is
                ignoring a feature, gotcha 25, not that the logo is wrong)
sweeps       : --inset 0.25 / 0.5 / 1.0 -> x1.731 / x1.708 / x1.660 (all inside)
               --max-stretch 1.35 -> 75.7% of the height; --min-clear >= 0.9 -> smaller cap,
               still centred, still inside (AGENTS.old.md A.3 has the table)
               --no-height-fill -> byte-identical to the pre-fill mark (lam = 0 is identity)

icon/ - the shipped set (Round 11: bash logo/icon/build.sh, then magick identify)
favicon.ico              16 / 24 / 32 / 48 / 64 px, 34 494 B, PaletteAlpha at 16 and
                         TrueColorAlpha above (an .ico with five sub-images is the point of it)
github-social-preview    1280x640 TrueColor 84 565 B      (GitHub's limit is 1 MB)
github-avatar-400.png    400x400 TrueColorAlpha 14 217 B   (a circle crop keeps all its ink)
apple-touch-icon.png     180x180 TrueColorAlpha 7 538 B    (corner alpha 0: the rounding)
glyph-16.png             16x16 PaletteAlpha 504 B          (corner alpha 0: real transparency;
                           gotcha 31: -b none would have made this 255 and white)
kwcapture-mark-1024.png  1024x1024 59 849 B; contact.png 1106x240 (6 cells x 1 row)
validate_logo.py icon/kwcapture-mark-mono.svg:
  ink 44.0,88.3 -> 468.0,423.7  padding L 44.0 R 44.0 T 88.3 B 88.3
  colour split (vs kwcapture-mark-sketch.svg) solid 10 pts == recomputed, 100.0% on ink,
               stem area 0.00% blue, samples stem 3/3 green | C 6/6 blue | W 3/3 green
    render QtSvg green 18 598 blue 13 611 -> 42.3% blue | MSVG 18 867 / 13 942 -> 42.5%
  (no rotate() in this file, so MSVG agrees - gotcha 27's control)
contrast, computed from the hex values with the WCAG relative-luminance formula:
  #0000ff vs #0d1117 2.20:1 | vs #ffffff 8.59:1
  #00ac4e vs #0d1117 6.32:1 | vs #ffffff 3.00:1 | #0000ff vs #00ac4e 2.87:1
legibility of the mark's word, rendered (`preview/ladder-icon.png`):
  128 px legible | 64 px marginal | 48 px and below mush. The glyph still reads at 32 px.
```

`validate_logo.py` exits non-zero on: a collision (< 1.5 px), ink outside the artboard,
off-centre artwork, the A failing the type check, ink > 1 px outside the helper box, a colour
split that fails any of its five assertions, a render where a viewer would not show both
colours, or **a check that crashed** (gotcha 26). Also run `xmllint --noout`, and render the
ladder 512/256/128/64/32 (`preview/ladder-*.png`): the wordmark stops being readable around
128 px, which is what `kwcapture-mark.svg` and the mono are for.

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
  the finding cannot be quietly forgotten. Re-confirmed 2026-10-11: 26 px and 67 px.
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
* **The two monograms are still two different drawings — but the shipped identity now picks
  one.** Round 11 resolved it *for the assets*: `icon/kwcapture-mark-mono.svg` is
  `--monogram --sketch kwcapture-mark-sketch.svg`, i.e. the **mark's** monogram, so the favicon,
  the tiles, the avatar and the README header are one drawing (`README.md` §8).
  `kwcapture-mono.svg` — the **original** sketch's monogram — is still shipped as an artefact and
  is still what a bare `--monogram` produces, so a fresh `--monogram` and a fresh
  `icon/kwcapture-mark-mono.svg` disagree. Unresolved part of the question: whether
  `kwcapture-mono.svg` should be regenerated from the mark sketch (one drawing, two files) or
  stay as the original's second voice (two drawings, and a user to explain them to). Whatever is
  decided, the invariant that matters is kept by `icon/build.sh`: the shipped small-icon chain
  reads only the mark sketch.
* **Dark mode still fails.** `#0000ff` on transparent against GitHub-dark `#0d1117` is **2.20:1**
  (better than the `#000000` it replaced, 1.11, still not usable) — see `preview/on-dark.png`.
  It is now two recolours, since both colours are mid-tone, and `--blue`/`--green` make it a
  one-line job (e.g. `--blue '#4d8dff' --green '#3ddc84'`), but re-check the C against *its own*
  green if you do: today's pair is 2.87:1 and lighter blues collapse toward 1.2.
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
* **Still open, and it is a human job:** GitHub's social-preview image is a web-UI upload — the
  REST and GraphQL APIs do not expose it (gotcha 34) — so `icon/github-social-preview.png` and
  `icon/github-avatar-400.png` sit in the repo **until someone clicks**. Steps in
  `README.md` §8. There is also still no `pyproject` icon field / package favicon wired to
  `icon/`; the docs header is the only automatic consumer.
* **Icons go through ImageMagick or Pillow, never Inkscape for `.ico`**: `inkscape x.svg -o x.ico`
  exits 0 and writes no file (verified) — the shipped way is `bash logo/icon/build.sh`, which
  makes `favicon.ico` at 16/24/32/48/64 from the glyph PNGs; the ad-hoc way is
  `magick -background none logo/kwcapture-mono.svg -define icon:auto-resize=16,32,48,64,128,256 out.ico`.
  Same species as a check that silently does not run: the exit code is not the result. And for
  transparency, do **not** pass Inkscape `-b none` (gotcha 31).
* Consider a **horizontal lockup** (monogram left, `APTURE` on a horizontal baseline) for nav
  bars — the diagonal *is* the mark's identity, so this is a separate asset, not a variant.

## Session log

Only this round's entry lives here. Rounds 1–9c (two recovered dead sessions, the anchor bug,
the falsified fit table, the renderer matrix, the MSVG `rotate()` find) are
[`AGENTS.old.md` Part C](AGENTS.old.md); Round 10's narrative is
[`AGENTS.old.md` Part G](AGENTS.old.md) and its own summary of what moved is
[Part F](AGENTS.old.md). Read them before arguing with any number above.

**Round 11 — 2026-10-11, the icon round.** The owner chose **`kwcapture-mark.svg` as the
official logo** and asked for the formats GitHub consumes, pushed. What that turned out to need,
in order of how much it taught:

* **A logo is not an icon.** `icon/` now holds 23 generated images plus the glyph SVG they all
  come from: the mark at 1024/512/256/128, the glyph at eleven sizes down to 16, a `favicon.ico`,
  Apple touch, PWA + maskable, a 400 px avatar, a 1280×640 social preview and a `contact.png`
  review sheet. One command (`bash icon/build.sh`) and three Pillow builders that each verify
  their own output.
* **The split logo/glyph/tile was decided by two measurements, not by taste.** The word dies
  (`preview/ladder-icon.png`: legible 128, marginal 64, mush 48 and below), and no single ground
  clears 3:1 for both colours (blue 2.20 on dark, green 3.00 on white) — so small sizes ship the
  glyph of the *same* drawing, and tiles are light. The avatar is the glyph because GitHub crops
  to a circle and a circular crop amputates `TURE`.
* **One of my own claims was too strong, and the contact sheet disproved it.** I had written in
  `build.sh` that a transparent icon on dark "loses the blue entirely"; the dark cells of the
  sheet show the strokes surviving fine at 2.20:1. The number stayed, the drama did not. That is
  gotcha 22's lesson again — **draw the thing and look before you keep the sentence**.
* **Gotchas 31–35** — Inkscape's `-b none` painting opaque white, ImageMagick compositing a blank
  canvas while exiting 0, a card writing off its own canvas and printing its size approvingly,
  the GitHub API having no image field at all, and `identify --format` (two dashes) making
  `icon/build.sh`'s own report vanish behind a `2>/dev/null` — are one-liners above, full versions
  in [`AGENTS.old.md` Part B](AGENTS.old.md). Four of the five are the same animal: **a tool that
  succeeds at the wrong thing**. The fifth is the meta case, and the one to remember: the report
  line that checked the artefacts was itself unchecked, so `build.sh` shipped a build whose
  summary printed nothing. It is fixed (one dash, stderr un-suppressed) and `%-28f` turned out to
  be unsupported by this ImageMagick in the process.
* **Not done, by nature rather than by failure:** the two GitHub uploads are clicks in a web UI
  (gotcha 34), and the `pyproject`/package icon wiring is untouched — this round touched assets
  and docs, no code in `kwcapture/`.
