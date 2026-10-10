# The `kwcapture` logo — directory guide and tool manual

Everything here builds the identity of [`kwcapture`](https://github.com/tjandrasg/kwcapture),
the fast Wayland/KWin screen-capture library: **two hand-drawn Inkscape sketches in, three
512×512 SVGs out**, plus a validator that can see geometry, paint *and* what a real renderer
paints, and a diagnostic that compares renderers against each other.

| file | job |
|---|---|
| [`AGENTS.md`](AGENTS.md) | the working set: rules, knobs, expected numbers, open items. **Read it before editing anything here** |
| [`AGENTS.old.md`](AGENTS.old.md) | the archive: superseded numbers, the full gotchas, the session log |
| [`LICENSE.md`](LICENSE.md) | artwork **CC BY 4.0**, tooling **MIT**, Inter **OFL-1.1** |
| `README.md` | this file: the structure and the manual |

Everything on this page was run on 2026-10-11 and the output is pasted from those runs, not
from memory — which is the house style for a reason you will meet in
[gotcha 18](AGENTS.md).

---

## 1. The three artefacts

> **`kwcapture-mark.svg` is the official logo of the project** (decided 2026-10-11). The
> generated icon set GitHub and every host actually consumes — social preview, avatar,
> favicon, PWA, Apple touch — is in [`icon/`](icon), §8. The other two SVGs stay: the full
> lockup for large placements and the *original* monogram as a separate drawing.

| | |
|---|---|
| ![the full logo](preview/kwcapture-512.png) | **`kwcapture.svg`** — the logo. Original monogram + `APTURE` at −38°. `python3 gen_logo.py` |
| ![the mark](preview/kwcapture-mark-512.png) | **`kwcapture-mark.svg`** — the redrawn, geometric monogram + `APTURE` fitted into a helper box and stretched ×1.753 across the baseline. `python3 gen_logo.py --mark` |
| ![the monogram](preview/kwcapture-mono-512.png) | **`kwcapture-mono.svg`** — the bare monogram, two-tone, for favicons and ≤64 px. `python3 gen_logo.py --monogram` |

Palette: `#00ac4e` (the monogram half: the K's stem and the W) and `#0000ff` (the word half:
the C, the pointer-A, `PTURE`). Both flat, no gradient since 2026-10-10 — `--classic` brings
the old gradient back.

## 2. The one idea you need first

The mark spells **CAPTURE**, and only one third of it is type:

![how the mark is assembled](preview/anatomy.png)

```
  C     <-  the junction of the hand-drawn K and W   (#kw / #kw-c, the monogram)
  A     <-  the hand-drawn mouse pointer             (#a, laid out as a letter)
  PTURE <-  the only typeset letters                 (#wordmark)
```

So `WORD = "PTURE"`. **Setting `WORD="CAPTURE"` renders `CACAPTURE`.** The blue bracket in
the K↔W junction is not decoration — it is the first letter, and it is the reason the mark is
called what it is. The C is also a *colour*: the stem is green so the bracket is the only blue
thing inside the monogram. (The C's legibility is still an open question with the owner — see
`AGENTS.md` §*Still open*.)

## 3. Directory structure

```
logo/
├── kwcapture-sketch.svg        INPUT   the original drawing (Inkscape, A4 mm): monogram + pointer
├── kwcapture-mark-sketch.svg   INPUT   the redrawn monogram + the black helper box
│
├── kwcapture.svg               OUTPUT  the logo            <- gen_logo.py
├── kwcapture-mark.svg          OUTPUT  the mark            <- gen_logo.py --mark
├── kwcapture-mono.svg          OUTPUT  the monogram        <- gen_logo.py --monogram
│
├── gen_logo.py                 TOOL    sketch + knobs -> SVGs
├── validate_logo.py            TOOL    the gate: geometry, type, box, colour, render
├── render_agreement.py         TOOL    diagnostic: does each engine agree with the path data?
│
├── icon/                       SHIPPED  the official icon set (see icon/build.sh)
│   ├── kwcapture-mark-mono.svg         the glyph form of the mark (same drawing, no word)
│   ├── kwcapture-mark-{1024,512,256,128}.png     the logo, transparent
│   ├── glyph-{1024,512,400,192,180,128,64,48,32,24,16}.png   the glyph, transparent
│   ├── favicon.ico  apple-touch-icon.png  pwa-{192,512}.png  maskable-512.png
│   ├── github-avatar-400.png  github-social-preview.png (1280×640)  contact.png (the sheet §8 shows)
│   ├── build.sh                        rebuilds the whole set in one command
│   ├── tiles.py  card.py  contact.py   Pillow builders; each verifies its own output
│
├── preview/                    DERIVED the documentation PNGs and the scripts that build them
│   ├── build.sh                        one command rebuilds every image on this page
│   ├── anatomy.py                      the figure in §2
│   ├── kwcapture-512.png  kwcapture-mark-512.png  kwcapture-mono-512.png
│   ├── sketch-source-512.png  sketch-mark-source-512.png
│   ├── ladder-kwcapture.png  ladder-mono.png  ladder-icon.png
│   ├── variants-type.png  variants-paint.png
│   ├── on-dark.png                     msvg-rotate-bug.png
│
├── AGENTS.md      the rules          ├── README.md        this file
├── AGENTS.old.md  the archive        └── LICENSE.md       what you may do with it
│
├── *.jsonl                TRANSIENT  session transcripts — gitignored, personal data, never
│                                      commit, never read whole (§6 of LICENSE.md, and
│                                      *Reading the transcript* in AGENTS.md)
└── __pycache__/           IGNORED    validate_logo.py imports gen_logo to reuse its geometry
```

The dataflow is a straight line — inputs on the left, the gate on the right. The helper box is
*read and then dropped*, so it appears in no output:

```
kwcapture-sketch.svg ─┬─> gen_logo.py ──────> kwcapture.svg   ─┬─> validate_logo.py ──> OK / FAIL
                      └─> gen_logo.py --monogram -> …-mono.svg ┘            │
kwcapture-mark-sketch.svg ─> gen_logo.py --mark ─> …-mark.svg ──────────────┘
                    (the helper box is read, then dropped: it is not in any output)
```

### Inputs are sacred

`gen_logo.py` **never writes to a sketch**, and the SVGs are regenerated, not hand-edited:
every change belongs in a sketch or in a knob. If you "fix" a generated SVG by hand, the next
run erases it — and the validator will not notice, because it validates the file you replaced.

| what you want to change | where you change it |
|---|---|
| the monogram's shape, the pointer, the box | the relevant `*-sketch.svg`, in Inkscape |
| the letters, size, tilt, spacing, colours, stretch | a `gen_logo.py` flag (§4.4) |
| a rule about what is allowed | `validate_logo.py`, and then prove it fails (§5.4) |
| a number in the docs | run the tool and paste the real output |

## 4. `gen_logo.py` — the generator

`sketch + knobs → SVG`. It reads the drawing by **Inkscape path id**, extracts the glyph
outlines of `WORD` from a system font, lays the pointer out as a letter, and writes one file.

### 4.1 Requirements

| tool | needed by | without it |
|---|---|---|
| `python3` (3.9+; tested 3.14) | all three programs | — |
| `fontTools` | `gen_logo.py` | cannot extract glyph outlines (ImportError) |
| `numpy` | `validate_logo.py`, `render_agreement.py` | pairwise-distance and raster maths fail |
| `Pillow` | the render checks, `preview/anatomy.py` | render check skipped |
| `PyQt6.QtSvg` | `validate_logo.py` render check, `render_agreement.py` | engine reported missing, check skipped — **not silently passed** |
| ImageMagick (`magick`, internal MSVG coder) | same two | ditto |
| `inkscape` | `preview/build.sh`, `render_agreement.py` | previews cannot be rebuilt; engine skipped |
| `xmllint` | nothing (recommended) | you lose the cheapest syntax check there is |
| the font | `gen_logo.py` | `--font` any OTF/TTF; the shipped look is `Inter-ExtraBold.otf` |

Both the system `python3` and the repo's `.venv` have the Python pieces.

### 4.2 Modes

| command | writes | what it is |
|---|---|---|
| `python3 gen_logo.py` | `logo/kwcapture.svg` | original sketch, `PTURE` at −38°, cap 3.30 mm, padded to a 512² artboard |
| `python3 gen_logo.py --mark` | `logo/kwcapture-mark.svg` | mark sketch + `APTURE` **fitted into the helper box** drawn in that sketch (box read, then dropped), then stretched across the baseline |
| `python3 gen_logo.py --monogram` | `logo/kwcapture-mono.svg` | monogram only — no pointer, no type |
| anything `--out PATH` | `PATH` | an experiment; the repo is untouched |

Default output paths differ per mode *on purpose*, so one mode can never clobber another's
artefact.

### 4.3 What it prints, and why each line matters

```
$ python3 gen_logo.py
content bbox: (51.55, 99.83, 87.13, 129.96) (35.58 x 30.13 mm)   <- the drawing's own box, in mm
scale       : 11.918 px per mm                                   <- the mm->px map of the artboard
word        : 'PTURE'                                            <- THE RULE, printed back at you
'A' pointer : (69.87, 110.16, 72.84, 114.0)  ink 0.99 x cap wide <- the A is a real letter's width
'PTURE'     : (71.57, 99.83, 85.12, 111.43)
colour      : monogram #00ac4e, C + A + word #0000ff
written     : /home/tjandra/way_scr_cap/logo/kwcapture.svg
```

`--mark` prints the fit it solved for, and one report nobody can eyeball — **the box taper**:

```
$ python3 gen_logo.py --mark
box         : base 24.917 x 7.786 mm at -43.12 deg
fit         : cap 4.310 mm, ink 24.917 mm long = 100.0% of the length, 55.4% of the height
anchor      : (71.641, 118.073) mm [center across, center along], inset=0.0 mm
height fill : x1.753 across the baseline: type ink 4.365 mm -> 7.652 mm = 98.3% of the box height
              (as tall as the drawn box allows: the ink touches its top edge at u=24.6 mm)
clearance   : 0.810 mm from the monogram after the stretch (was 0.792 mm)
box taper   : the drawn box is NOT a rectangle: the headroom over its base falls 7.920 -> 7.651 mm
              along the length (its top edge is -0.62 deg off parallel). Filling the MEAN height
              (x1.784) would have hung 0.133 mm = 1.6 px outside the far end, so the answer is x1.753
box         : dropped from the output (it was only a guide)
colour      : monogram #00ac4e, C + A + word #0000ff
written     : /home/tjandra/way_scr_cap/logo/kwcapture-mark.svg
```

That `box taper` line exists because the obvious answer (fill the *mean* height, ×1.784) puts
type **1.6 px outside the hand-drawn box** at the end where the word is tallest and the box is
shortest — and a human cannot see 0.62° in a render. The generator prints its guide's
imperfection rather than leaving you to rediscover it.

```
$ python3 gen_logo.py --monogram
content bbox: (51.55, 99.83, 87.13, 129.96) (35.58 x 30.13 mm)
scale       : 11.918 px per mm
word        : (none)
colour      : monogram #00ac4e, C + A + word #0000ff
written     : /home/tjandra/way_scr_cap/logo/kwcapture-mono.svg
```

### 4.4 The write-guard: a variant needs `--out`

`--classic`, `--no-c-split`, `--c-paint` and friends change the **paint**, not the output path.
A variant run without `--out` used to overwrite the shipped logo and print a cheerful
`written:` line, while the file stayed valid XML, xmllint-clean and geometrically perfect.
That trap is now closed **by the tool**, which diffs every knob against argparse's own
defaults:

```
$ python3 gen_logo.py --classic
refusing to overwrite the shipped kwcapture.svg: this run deviates from the shipped look
by --classic.
  write it somewhere else:  --out /tmp/kwcapture-variant.svg
  or, if you really mean to replace the shipped file:  --force
$ echo $?
1
```

Verified 2026-10-11: exit 1 and `kwcapture.svg` byte-identical afterwards. `--force` means *I
intend to replace the shipped artefact*. The default paths of the three modes are still fine
for the shipped look — the guard only fires when a knob deviates from it.

### 4.5 Every flag

Typeset from `--help`, with the shipped value. **`--help` is not always right**: the
`--c-paint` description still says "`mask` (default) and solid render identically everywhere";
the default is `solid`, and MSVG paints **no C at all** through a mask. Trust §4.7 and
`AGENTS.md`, and fix the help text next time the file is edited (it is on the open list).

**Type & layout**

| flag | default | meaning |
|---|---|---|
| `--word` | `PTURE` | the typeset letters. **Never `CAPTURE`** (§2) |
| `--font` | `/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf` | ExtraBold matches a very heavy monogram; Bold looked thin next to it |
| `--cap` | `3.30` mm | cap height of the type (the drawn letters were ~3.4 mm) |
| `--track` | `0.10` em | letter-spacing; the sketch was widely set |
| `--angle` | `−38.0`° | baseline tilt (the drawing's baseline is ≈ −38.9°) |
| `--canvas` / `--pad` | `512` / `44` px | artboard and padding on the constrained axis |
| `--free-baseline` | off | stop levelling the word's cap-top with the top of the K |
| `--no-a` | off | monogram + `PTURE`, drop the pointer |

**The A** (the pointer, treated as a letter)

| flag | default | meaning |
|---|---|---|
| `--a-size` | `1.00` × cap | height, measured **perpendicular to the baseline**. >1 reads as "big C, medium A, small PTURE" |
| `--a-width` | `1.00` × a real capital A | stretches the pointer **along the baseline** to the face's own A width (3.282 mm at this cap). Uniform scaling gives a 0.71×-wide, decorative A |
| `--a-gap` | `0.70` mm | the A→P gap along the baseline; 0.90 mm read as a word break |
| `--a-upright` | off | snap the pointer exactly perpendicular. It then reads as an **arrow**, not a letter. Kept only so nobody rediscovers it |

**Helper box / `--mark` mode**

| flag | default | meaning |
|---|---|---|
| `--mark` | off | fit mode |
| `--box` | the unique parallelogram | id of the helper box (`fit-box` by convention) |
| `--inset` | `0.0` mm | keep away from the box edges. Costs type size **and** fill: `0.25`→×1.731, `0.5`→×1.708, `1.0`→×1.660 (measured) |
| `--align` / `--along` | `auto` | placement across / along the box; `auto` optimises both. `top` is now *rejected* when it buys clearance by spilling over the box edge |
| `--min-clear` | `0.50` mm | floor on ink clearance to the monogram. The word shrinks rather than touching it: `0.9` → cap 4.273 mm, `1.5` → 4.065 mm (measured) |
| `--no-height-fill` | off | keep the type uniform; ~45% of the box height stays empty. Byte-identical to the pre-Round-9 mark |
| `--max-stretch` | `2.00` × | ceiling on the fill. A taste guard: the box wants 1.753 and is not stopped |
| `--no-recenter` | off | keep the sketched position instead of centring on the artboard |

**Colour**

| flag | default | meaning |
|---|---|---|
| `--green` | `#00ac4e` | the monogram half (K's stem + W) |
| `--blue` | `#0000ff` | the word half (C + pointer-A + letters). Chosen against the green it touches (2.87:1), not the page |
| `--c-paint {solid,mask,clip}` | `solid` | how the blue C is cut — see §4.7. **The `--help` text about this is wrong** |
| `--no-c-split` | off | flat green monogram, no blue C: the *control* for "is it the colour that makes the C read?" |
| `--classic` | off | the pre-2026-10-10 look: gradient monogram, no split, black type |

**I/O**

| flag | default | meaning |
|---|---|---|
| `--sketch` | `kwcapture-sketch.svg` (or the mark sketch with `--mark`) | **literal path**: resolved from your cwd, not from the script. See the trap below |
| `--out` | per mode | where to write |
| `--force` | off | let a deviating variant overwrite a shipped artefact |

**Two path traps.** The *defaults* are resolved from the script's own directory, so the
documented commands work from any cwd. `--sketch` and `--out` are literal:

```
$ cd logo && python3 gen_logo.py --monogram --sketch logo/kwcapture-mark-sketch.svg --out /tmp/m.svg
FileNotFoundError: [Errno 2] No such file or directory: 'logo/kwcapture-mark-sketch.svg'
$ cd logo && python3 gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg --out /tmp/m.svg   # works
```

### 4.6 The knobs that change the design, as pictures

The type knob — how much the `APTURE` fills the box's height:

![the height fill and its escape hatches](preview/variants-type.png)

```bash
python3 gen_logo.py --mark                                  # shipped: x1.753
python3 gen_logo.py --mark --out /tmp/a.svg --no-height-fill # uniform, box height unused
python3 gen_logo.py --mark --out /tmp/b.svg --max-stretch 1.35
```

The paint knobs — and the control experiment for the C:

![shipped, classic, and no-c-split](preview/variants-paint.png)

```bash
python3 gen_logo.py                      # shipped: KW green, Capture blue
python3 gen_logo.py --out /tmp/c.svg --classic     # gradient monogram, black type
python3 gen_logo.py --out /tmp/d.svg --no-c-split  # all-green monogram: does the C still read?
```

`--no-c-split` is the answer to a question the docs cannot answer: if the mark stops reading as
CAPTURE, is it the green stem splitting the monogram into `| <` + `W`? Show both to someone who
has never seen the sketch.

### 4.7 Why `--c-paint solid`, in one table

Three ways to paint the same C; **renderers disagree about all three**. Ink as % blue (truth:
39.1–39.8%):

| renderer | `solid` | `mask` | `clip` |
|---|---|---|---|
| Inkscape / librsvg | 39.5% ✅ | 39.1% ✅ | 39.1% ✅ |
| **QtSvg** — Gwenview, Dolphin thumbnails, `QIcon` | 39.4% ✅ | 39.1% ✅ | **100% blue ❌** |
| **ImageMagick internal MSVG** | 39.8% ✅ | **0% blue ❌** | 39.6% ✅ |

`clip` shipped for a day and looked **100% blue in every Qt viewer** because QtSvg ignores
`clip-path`; `mask` fixes Qt but MSVG hides a mask it does not parse. `solid` asks nothing of a
renderer — the C is its own path — and is legal only because the ring lies 100.0% inside the
monogram's ink, which the validator asserts. Try them; the validator will tell you:

```bash
python3 gen_logo.py --out /tmp/p.svg  --c-paint clip && python3 validate_logo.py /tmp/p.svg
python3 gen_logo.py --out /tmp/p2.svg --c-paint mask && python3 validate_logo.py /tmp/p2.svg
```

Both are **proven to fail**, in opposite directions, which is exactly why `solid` is the default:

```
clip:  render QtSvg (Gwenview, Dolphin, QIcon): green  0 blue 37731 -> 100.0% blue [NO GREEN]
       FAIL: QtSvg renders 100% blue: the green monogram is covered -- a cut-out this
             renderer ignores is in use (--c-paint solid emits neither clip nor mask)
mask:  render MSVG  (ImageMagick internal):     green 35088 blue   514 ->   1.4% blue [NO BLUE]
       FAIL: MSVG renders no blue at all: the C overlay is hidden -- unsupported cut-out
```

### 4.8 Feeding it a different sketch

`gen_logo.py` binds paths **by Inkscape id**: `path1` **or** `kw` = the monogram, `path10`
**or** `cursor`/`a` = the pointer. Everything else in the sketch is ignored (the letters come
from the font). A sketch with neither id now tells you which ids it looked for and which it
found, instead of `KeyError: 'path1'`. If you redraw and the vertex count is no longer **19**,
the generator **refuses**: the letter rings (`K_RING`/`W_RING`/`C_RING`) are vertex indices,
and re-numbering them is the owner's call, not a guess.

```bash
python3 gen_logo.py --monogram --sketch logo/kwcapture-mark-sketch.svg --out /tmp/mono-mark.svg
content bbox: (49.03, 100.35, 86.25, 129.8) (37.22 x 29.45 mm)   # the mark's monogram, not the original's
```

The two monograms are genuinely different drawings, which is why "which one is the identity" is
still open in `AGENTS.md`.

## 5. `validate_logo.py` — the gate

```bash
python3 logo/validate_logo.py                          # checks logo/kwcapture.svg
python3 logo/validate_logo.py logo/kwcapture-mark.svg   # the mark must be named explicitly
```

It parses the **emitted SVG**, applies every `transform` itself, and measures ink — so it
disagrees with the generator whenever the generator is wrong, which is the entire point.

### 5.1 The seven checks

| check | what it proves | how it can fail |
|---|---|---|
| **ink bounds** | where each element's ink actually is, per element (`#kw`, `#a`, `#wordmark`) | — (informational; feeds the rest) |
| **clearances** | no two elements collide (< 1.5 px = FAIL, < 3.0 px = "tight") | a collision, e.g. the A landing on the W |
| **artboard + centring** | ink inside 512², and centred (L/R and T/B within 1 px) | ink clipped by the artboard, or off-centre |
| **type check** | the pointer **is** a letter: height ≈ cap (±2 px), width 0.85–1.15 × cap, shared cap line, shared baseline — all measured **unstretched**, off `#type` | a silently wrong `A_SIZE`/`A_WIDTH` (a projection bug once rendered 1.41× cap while the knob said 1.00) |
| **box check** | `#a` and `#wordmark` are inside the helper box, which is *not in the output*: re-read from `<name>-sketch.svg`, re-centring undone | > 1 px outside. **Skipped silently if there is no `-sketch.svg`** — read the line, not the exit code |
| **colour split** | the blue C is derived, not drawn: 5 assertions, incl. "≥95% of the ring lies on ink" and "0% of the stem's area is inside it" — the two that cannot agree with a wrong idea by construction | a ring that wanders into the counters, or an `#kw-c` whose `d` is not derived (a redraw in disguise) |
| **render** | rasterises the file with **QtSvg** and **ImageMagick MSVG** and requires both colours present in both — because every other check reads path data and therefore agrees with the generator | `--c-paint clip` → *QtSvg renders 100% blue*; `--c-paint mask` → *MSVG renders no blue at all* |

### 5.2 Real output — the mark (the fullest case)

```
$ python3 validate_logo.py logo/kwcapture-mark.svg
# kwcapture-mark.svg   artboard 512x512
  kw        ink  x    7.45 ..  451.08   y  100.97 ..  451.93   (1184 pts)
  a         ink  x  256.95 ..  327.62   y  234.36 ..  321.51   (60 pts)
  wordmark  ink  x  276.93 ..  504.55   y   60.06 ..  281.35   (561 pts)
  clearance kw        <-> a        :    9.68 px  [ok]
  clearance kw        <-> wordmark :   73.13 px  [ok]
  clearance a         <-> wordmark :   14.91 px  [ok]
  ink 7.5,60.1 -> 504.5,451.9   padding  L 7.5  R 7.5  T 60.1  B 60.1
  colour split (vs kwcapture-mark-sketch.svg): solid 10 pts == recomputed, 100.0% on ink,
                stem area 0.00% blue
                samples: stem 3/3 green, C 6/6 blue, W 3/3 green
  box check (vs kwcapture-mark-sketch.svg): closest ink -0.03 px from the box edge
                (positive = inside), tightest is #a
  type check, perpendicular to the -43 deg baseline:
    height fill x1.753 across the baseline (read off #type, along-baseline factor 1.0000);
    rules below measured unstretched
    A height  51.37 px   cap height  52.02 px   ratio 0.987
    A width   51.09 px   = 0.982 x cap  (a real capital A is ~0.95-1.00 x cap)
    cap line : A  346.70  word  346.68   (delta +0.01)
    baseline : A  436.75  word  437.88   (delta -0.64)
  render QtSvg   (Gwenview, Dolphin, QIcon): green  20319 blue  23506 ->  53.6% blue
  render MSVG    (ImageMagick internal): green  20602 blue  20870 ->  50.3% blue
  OK
```

The `box check` line is the one to watch: **−0.03 px** means the A's tip sits essentially *on*
the box's leaning edge — inside, and exactly where "as large as possible" leaves you.

### 5.3 The other two artefacts

```
$ python3 validate_logo.py                       # kwcapture.svg
  ... ink 44.0,76.5 -> 468.0,435.6  padding L 44.0 R 44.0 T 76.5 B 76.4
  colour split (vs kwcapture-sketch.svg): solid 10 pts == recomputed, 100.0% on ink,
                stem area 0.00% blue;  samples: stem 3/3 green, C 6/6 blue, W 3/3 green
  (no "box check" line: kwcapture-sketch.svg has no helper box, so the check returns nothing)
  render QtSvg 44.3% blue | MSVG 45.4% blue
  OK

$ python3 validate_logo.py logo/kwcapture-mono.svg
  kw        ink  x   44.00 ..  468.00   y   76.45 ..  435.56   (1164 pts)
  colour split ... stem area 0.00% blue; samples stem 3/3 green, C 6/6 blue, W 3/3 green
  render QtSvg 39.4% blue | MSVG 39.8% blue
  OK                          <- one element, so no clearances and no type check apply
```

~0% of one colour in some renderer does **not** mean the logo is wrong — it means that renderer
is ignoring a feature (that is how `clip` and `mask` were found).

### 5.4 Exit codes, and how to trust any check here

| exit | meaning |
|---|---|
| `0` | everything printed OK |
| `1` | at least one FAIL, **or a check that crashed** — `run_check()` prints `CRASH in <name>` + traceback, counts it as a failure (a check that died proved nothing) and ends with `NOT A CLEAN RUN` |

The last line is deliberately unmistakable, because a bare traceback through `| tail -1` once
left a session with `TypeError: …` and nothing else to go on. **Never diagnose from the tail of
a pipe.**

A check that agrees with you is not a check — so before believing one, **make it fail**. The
over-stretch sabotage, run and verified today:

```bash
cd logo
cp kwcapture-mark.svg /tmp/mark-backup.svg
sed -i 's/scale(1 1.753)/scale(1 1.86)/' kwcapture-mark.svg
test "$(grep -c 'scale(1 1.86)' kwcapture-mark.svg)" = 1 && echo "assert changed: OK"
python3 validate_logo.py kwcapture-mark.svg
python3 gen_logo.py --mark            # restore; cmp against the backup: byte-identical
```

```
  box check (vs kwcapture-mark-sketch.svg): closest ink -7.71 px from the box edge
                (positive = inside), tightest is #wordmark
  FAIL: ink is 7.7 px OUTSIDE the helper box - the fit is wrong
  FAIL: artwork not centred (L/R 7.5/9.0, T/B 54.4/60.1)
  2 problem(s)
```

The along-baseline sabotage (`s/scale(1 1.753)/scale(1.1 1.753)/`, same in-place procedure) fails
three ways instead:

```
  FAIL: the height stretch also scales ALONG the baseline (x1.1000): only across is allowed,
        or the tracking moves
  FAIL: ink is outside the artboard
  FAIL: artwork not centred (L/R 7.5/-14.0, T/B 40.0/60.1)
```

Two traps, both met for real while writing this file:

* **Assert the sabotage applied.** My first attempt used `scale\(1 1.753\)` in a BRE, matched
  nothing, changed nothing — and the validator cheerfully printed `OK` for a file I believed was
  sabotaged. That is gotcha 24's `assert changed` lesson, paid for a second time in a
  documentation round.
* **The box check finds its sketch by filename** (`<stem>-sketch.svg`, next to the *script*).
  Sabotage a copy at `/tmp/sab1.svg` and you get **no box-check line at all** — the file has no
  sketch, so containment is silently skipped and only the centring check catches the same bug.
  Sabotage **in place**, or accept that the sharpest check is the one you are not running.

### 5.5 The flake: re-run before you believe a crash

`box_check` → `gen_logo.find_box` → `convex_hull` crashes **intermittently** with errors its
source cannot produce — `TypeError: '<=' not supported between instances of 'float' and 'list'`
(where `tol` is a local float), or `IndexError: list index out of range`. Measured today:
**2/5, then 0/12, then 2/40** validator runs; also reproduced in a 70-line extract with **no
numpy and no fontTools**, and once as a hard
`Fatal Python error: _PyEval_EvalFrameDefault: Executing a cache.` — which no correct Python
program can cause. Bursty, not steady, which is why it survived three sessions as
"unreproducible".

Practical rules (full story, gotcha 29 in `AGENTS.md`):

* **Re-run.** One crash is not a finding, and one clean run is not either. `for i in {1..20}`.
* **Do not "fix" `convex_hull`** — the operands the message names cannot be built there. A
  retry wrapper would launder a machine fault into a passing build.
* Three message shapes were seen today, in three different checks — `TypeError: '<=' not
  supported between instances of 'float' and 'list'`, `IndexError: list index out of range`
  (both in `box_check`) and `TypeError: 'list' object cannot be interpreted as an integer` (in
  `colour_check`, 1/25 runs). Same fault, different costume: the message tells you about the
  *interpreter*, not about your code.
* Suspects, measured but unproven: a global `LD_PRELOAD=libgtk-nocsd.so.0`, and non-ECC RAM.
* Same family, quieter: one run printed `stem area 0.03% blue` where 310 other runs print
  `0.00%`. Identical input, different number, and it sits under the threshold — treat a marginal
  number as "re-run", not as evidence.

## 6. `render_agreement.py` — the diagnostic (it exits 1 on purpose)

```bash
python3 logo/render_agreement.py                     # the three artefacts
python3 logo/render_agreement.py --tol 4 logo/foo.svg # custom tolerance
```

`validate_logo.py`'s render check asks each engine *whether both colours appear*. It cannot see
**where** they were painted. This tool asks the sharper question: per engine, per colour, what
is the ink box, and does it match the box the **path data** implies (computed here from the
same path data, with every `transform` applied by hand)? An engine that disagrees has a
`transform` bug, not a colour bug.

```
$ python3 logo/render_agreement.py
# kwcapture.svg   artboard 512x512   (tolerance 2 px)
  green  path data says   44,  76.. 468, 436
    inkscape     44,  76.. 467, 435  ok
    qt           44,  76.. 467, 435  ok
    msvg         44,  76.. 468, 436  ok
  blue   path data says  111,  76.. 444, 427
    inkscape    111,  76.. 443, 426  ok
    qt          111,  76.. 443, 426  ok
    msvg        111, 102.. 468, 427  OFF BY 26 px
# kwcapture-mono.svg ... all ok   <- the only file with no rotate() in it
# kwcapture-mark.svg
  blue   path data says   64,  60.. 505, 450
    inkscape     64,  60.. 504, 449  ok
    qt           64,  60.. 504, 449  ok
    msvg         64, 127.. 511, 450  OFF BY 67 px
2 engine/path disagreement(s) -- see the OFF lines above
$ echo $?
1
```

**Exit 1 is the finding, not a failure of the build.** It stays non-fatal on purpose: making it
a gate would redden the shipped files over a third-party bug, and the fix is the owner's call
(`AGENTS.md` §*Still open*: emit a second, transform-free `kwcapture-flat.svg` for pipelines
using bare ImageMagick — compatibility without spending an invariant).

What it looks like, same files, two engines:

![QtSvg versus ImageMagick MSVG](preview/msvg-rotate-bug.png)

MSVG is wrong **exactly where a `rotate()` is involved** and exact on the mono, which has none.
Ruled out by measurement, not opinion: the argument separator, the transform *chain*, and
`rotate()` nested under a `scale()`. Baking the transforms into the path data *does* fix it —
which also proves the disagreement is about `transform`. Practical reach: ImageMagick **without**
a `librsvg` delegate (many servers and upload pipelines) renders the wordmark wrong; KDE,
Inkscape and browsers are fine, and `apt install librsvg2-bin` gives ImageMagick a delegate.

## 7. Making images: PNG, ICO, and the size ladder

One command rebuilds every image on this page (the exact commands are inside it):

```bash
bash logo/preview/build.sh
```

Individually:

```bash
inkscape logo/kwcapture.svg -o logo/preview/kwcapture-512.png -b white -w 512 -h 512
inkscape logo/kwcapture-mark.svg -o logo/preview/kwcapture-mark-512.png -b white -w 512 -h 512
inkscape logo/kwcapture-mono.svg -o logo/preview/kwcapture-mono-512.png -b white -w 512 -h 512
# the inputs, as Inkscape sees them: the helper box is visible here, and only here
inkscape logo/kwcapture-sketch.svg      -o logo/preview/sketch-source-512.png      -b white -w 512 -h 512
inkscape logo/kwcapture-mark-sketch.svg -o logo/preview/sketch-mark-source-512.png -b white -w 512 -h 512
```

![the two sketches, as drawn](preview/sketch-mark-source-512.png)

*`kwcapture-mark-sketch.svg`: the redrawn monogram and the black helper box. The box is read by
`--mark` and never emitted — this render is the only place you can see what the fitter was
given.*

### The ladder: where the word stops working

```bash
for n in 512 256 128 64 32; do
  inkscape logo/kwcapture.svg      -o /tmp/full-$n.png -b white -w $n -h $n
  inkscape logo/kwcapture-mono.svg -o /tmp/mono-$n.png -b white -w $n -h $n
done
```

![kwcapture.svg down the ladder](preview/ladder-kwcapture.png)

`APTURE` stops being readable around **128 px** and is gone by 64 — that is not a bug in the
render, it is the argument for the other two files:

![kwcapture-mono.svg down the ladder](preview/ladder-mono.png)

| size | use |
|---|---|
| ≥ 256 px | `kwcapture.svg` (docs header, README, og image) |
| 128–256 px | `kwcapture-mark.svg` — the box-fitted type survives here best |
| ≤ 64 px | a glyph and nothing else: `icon/kwcapture-mark-mono.svg` for the shipped set (§8), `kwcapture-mono.svg` if you want the *original* drawing's monogram. A favicon with `APTURE` is mush |

### Icons

The **shipped** icon set — every size, plus tiles, `.ico`, avatar and social card, with the
reasoning — is §8; `bash logo/icon/build.sh` makes all of it. These two one-liners are the
throwaway versions, for an icon you want in `/tmp` in ten seconds:

```bash
# favicon / app icon — ImageMagick does the sizes; -background none keeps it transparent
magick -background none logo/kwcapture-mono.svg \
       -define icon:auto-resize=16,32,48,64,128,256 /tmp/kwcapture.ico
# social card: 1200x630 exactly (note -extent: -resize alone would give you 630x630)
magick -background none logo/kwcapture.svg -resize 630x630 \
       -extent 1200x630 -gravity center /tmp/og.png
```

Verified: the `.ico` comes out with all six sizes; the card is 1200×630. **Do not ask Inkscape
for an `.ico`** — it exits 0 and writes no file at all. An icon that silently does not exist is
the same species of bug as a check that silently does not run: the exit code is not the result.

Build them from the **same** drawing the header uses: the shipped set settled that on 2026-10-11
by taking the glyph from the *mark* sketch (§8), so the favicon, the avatar and the README header
are one drawing. `kwcapture-mono.svg` — the original sketch's monogram — stays as the other
version of it, and `AGENTS.md` still carries the "two monograms" item.

## 8. The official icon set — `icon/`

On 2026-10-11 the owner chose **`kwcapture-mark.svg`** as the logo of the project. A logo is not
an icon, so `icon/` holds the formats the hosts actually ask for — GitHub's social preview and
avatar, a `.ico` favicon, Apple touch, PWA — and one command rebuilds every one of them:

```bash
cd logo && bash icon/build.sh      # inkscape + ImageMagick + Pillow; writes into icon/ only
```

![the shipped icon set](icon/contact.png)

| file | what it is for | built by |
|---|---|---|
| `../kwcapture-mark.svg` | **the logo** — the source of everything below | `gen_logo.py --mark` |
| `kwcapture-mark-mono.svg` | **the glyph form**: the same drawing with the word dropped | `gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg` |
| `kwcapture-mark-{1024,512,256,128}.png` | README headers, docs, og images — anywhere ≥ 128 px | `icon/build.sh` |
| `glyph-{1024,512,400,192,180,128,64,48,32,24,16}.png` | tab icons, list icons, any small or masked slot | `icon/build.sh` |
| `favicon.ico` (16/24/32/48/64) | browsers that still ask for `.ico` | `icon/build.sh` |
| `apple-touch-icon.png` (180, rounded) | iOS home screen (it masks again, which is fine) | `icon/tiles.py` |
| `pwa-192.png`, `pwa-512.png`, `maskable-512.png` | a PWA manifest; `maskable-512` keeps the 80 % safe zone | `icon/tiles.py` |
| `github-avatar-400.png` | **GitHub avatar** — org/profile image, cropped to a circle | `icon/tiles.py` |
| `github-social-preview.png` | **GitHub social preview**, 1280×640, 83 KB (the limit is 1 MB) | `icon/card.py` |
| `contact.png` | the review sheet above | `icon/contact.py` |

Nothing here is hand-made. `build.sh` refuses to run if a source SVG is missing, and each Python
builder checks its own output: `tiles.py` fails on a blank or greyscale tile, `card.py` measures
every string with `font.getlength()` and asserts nothing reached the right edge. That assert is
not decoration — the first `card.py` hard-coded font sizes and printed `wrote … 1280x640` over a
card whose tagline ran off the canvas. **A success message is not a check** (gotcha 24, met a
third time in this round).

### Why the set splits logo / glyph / tile

Two measurements decided it, not taste.

**The word dies at 64 px.** Rendered, not guessed (`bash preview/build.sh` makes this figure):

![mark and glyph down to favicon size](preview/ladder-icon.png)

`APTURE` is legible at 128 px, marginal at 64 — you can just resolve it — and mush at 48 and
below. So nothing below 64 px ships the word; it ships the glyph, and the glyph is the *same
drawing*, not a second design:

```bash
cd logo && python3 gen_logo.py --monogram \
           --sketch kwcapture-mark-sketch.svg --out icon/kwcapture-mark-mono.svg
```

The `--sketch`/`--out` literal-path trap (§4.5) applies, so cwd must be `logo/`. Verified
2026-10-11: that command reproduces `icon/kwcapture-mark-mono.svg` **byte-identically** (`cmp`),
and `validate_logo.py` prints **OK** on it (colour split 100 % on ink, render 42.3 % blue).

**No ground wins both colours.** WCAG relative luminance, computed from the two hex values:

| | against GitHub dark `#0d1117` | against white |
|---|---|---|
| blue `#0000ff` — the C, the A, `PTURE` | **2.20:1** | 8.59:1 |
| green `#00ac4e` — the KW | 6.32:1 | **3.00:1** |

The bold cells are the two that fall short of the 3:1 WCAG figure for graphical objects, one per
ground. The mark *is* visible on dark — the strokes are thick and `contact.png` shows it — which
is why the stronger claim this section first carried ("a transparent icon loses the blue
entirely") was struck from `build.sh` after the dark contact sheet disproved it. But a light tile
is the only ground where **both** halves clear 3:1, and a square is what iOS, PWA and avatar
slots want anyway. The transparent renders stay in the set for hosts that want them.

**Why the avatar is the glyph and not the logo:** GitHub crops avatars to a circle, and the
mark's word runs out to the right edge of the artboard — a circular crop amputates `TURE`. The
monogram keeps all its ink inside the circle. That comparison is exactly what `contact.png`
exists to show, and it settles by looking what a filename list cannot.

### Setting them on GitHub

The repository's picture is its **social preview**, and that image is a **web-UI setting** — the
APIs do not expose it, which was probed with an admin token on 2026-10-11 rather than assumed:
`POST /repos/tjandrasg/kwcapture/social_preview` → **404**, GraphQL's 262 mutations contain
**zero** matching `avatar|social|preview|image|upload`, and `github.com/settings/profile` with
that same token → **302 to `/login`** (the web app runs on a cookie session; a PAT is not one).
So no script in this repo can set it, and none pretends to (gotcha 34). Two uploads, both from
`logo/icon/`:

1. **Social preview** — <https://github.com/tjandrasg/kwcapture/settings> → *Social preview* →
   **Edit image** → upload `github-social-preview.png` (1280×640).
2. **Avatar** — a *repository* has no avatar of its own; only a user or org does. If the mark
   should be the profile image, upload `github-avatar-400.png` in the org/user avatar settings.

What *is* automatic is the README header: [`../README.md`](../README.md) opens with
`logo/icon/kwcapture-mark-256.png`, written as an absolute `raw.githubusercontent.com` URL on
purpose, because PyPI renders the same README and does not resolve repo-relative image paths.

### Re-running after a logo change

```bash
cd logo
python3 gen_logo.py --mark && python3 validate_logo.py kwcapture-mark.svg
python3 gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg \
        --out icon/kwcapture-mark-mono.svg
bash icon/build.sh          # every size, tile, .ico, card, and the contact sheet
```

Then open `icon/contact.png` and *look at it* before committing. The sheet is the review; the
exit codes only tell you the tools were awake.

## 9. Dark surfaces

![on GitHub dark](preview/on-dark.png)

The type is `#0000ff` on transparent; against GitHub dark `#0d1117` that is **2.20:1** — better
than the `#000000` it replaced (1.11:1, effectively invisible) and still short of usable. Both
colours are mid-tone, so a dark variant is two recolours, and the flags make it one line:

```bash
# what you see above: the shipped files composited on GitHub dark
inkscape logo/kwcapture.svg -o /tmp/dark-bg.png -b '#0d1117' -w 400 -h 400
# a real dark variant, if the owner decides to ship one
python3 gen_logo.py --out /tmp/dark.svg --blue '#4d8dff' --green '#3ddc84'
python3 validate_logo.py /tmp/dark.svg
```

Re-check the C against **its own** green when you do: today's blue-vs-green is 2.87:1 and
prettier light blues collapse toward 1.2, at which point the C dissolves into the W and the
first letter of the word is gone.

## 9. A clean build, end to end

This is the exact sequence behind the "verified" claim at the top of `AGENTS.md`. Generating to
`/tmp` and `cmp`-ing proves regeneration is byte-identical without touching the repo:

```bash
cd ~/way_scr_cap/logo
for f in kwcapture kwcapture-mark kwcapture-mono; do cp $f.svg /tmp/$f.orig.svg; done
python3 gen_logo.py               --out /tmp/t_full.svg
python3 gen_logo.py --mark        --out /tmp/t_mark.svg
python3 gen_logo.py --monogram    --out /tmp/t_mono.svg
cmp /tmp/t_full.svg /tmp/kwcapture.orig.svg        && echo full identical
cmp /tmp/t_mark.svg /tmp/kwcapture-mark.orig.svg   && echo mark identical
cmp /tmp/t_mono.svg /tmp/kwcapture-mono.orig.svg   && echo mono identical
xmllint --noout *.svg
python3 validate_logo.py kwcapture-mark.svg     # OK
python3 validate_logo.py kwcapture-mono.svg     # OK
python3 validate_logo.py kwcapture.svg          # OK when box_check survives it (see 5.5)
python3 render_agreement.py                     # exit 1: MSVG off by 26 and 67 px. Expected.
```

Measured 2026-10-11: 3/3 byte-identical, xmllint silent, both explicit validations OK,
`render_agreement.py` reporting the same two MSVG numbers the docs carry.

The icon set is a second, separate build (`bash icon/build.sh`, §8): it re-reads the same SVGs,
cannot write outside `icon/`, and each of its builders verifies its own pixels.

## 11. Where to go next

| you want to | read |
|---|---|
| change anything at all | [`AGENTS.md`](AGENTS.md) — the rules, the knobs and why, the expected numbers, the 29 gotchas |
| know why a rule exists, or what was tried and rejected | [`AGENTS.old.md`](AGENTS.old.md) — full gotchas, the falsified numbers, the session log |
| ship an icon, an avatar or a social card | `icon/` — §8: one command (`bash icon/build.sh`), and the measurements behind every size |
| use, copy or recolour the artwork | [`LICENSE.md`](LICENSE.md) — CC BY 4.0 (artwork), MIT (tooling), trademarks **not** granted |
| the software the mark belongs to | [`../README.md`](../README.md) — `kwcapture`: ~40 fps Wayland capture for KDE Plasma |
