# logo/AGENTS.old.md — the archive of `logo/AGENTS.md`

**Nothing in this file is a current instruction.** It is what `logo/AGENTS.md` used to carry
and no longer does: superseded numbers, falsified claims, the war stories behind the
gotchas, the session log, and the long form of recipes that are now distilled. Read it when
you want to know *why* a rule exists, or when a rule in `AGENTS.md` looks arbitrary and you
are reaching for the "simplify" key. `AGENTS.md` is what to do today; this is why.

* **Split:** 2026-10-11 (Round 10) — an archive-verbatim pass in the style of the root
  repo's `8377f0e` ("77 KB → 54 KB by archiving superseded detail verbatim, nothing
  deleted").
* **Pre-split `logo/AGENTS.md`:** 86 077 bytes, sha256
  `48f0491b616ae075b9571652227488f2b81c8759958b48c4eb489977e93fbb78`. Every quotation below
  is extracted from that file by line range, so a later diff can prove nothing was edited,
  and that a reader can recover the original byte-for-byte from git.
* **The rule of this file:** text is *moved*, never corrected in place. A paragraph that is
  wrong today is kept here wrong, because the wrongness is the finding (gotcha 18).
  Corrections live in `AGENTS.md`, which points here.
* Only prose marked **Round 10** is new. Everything else is the pre-split file's words.

| part | was | now in `AGENTS.md` as |
|---|---|---|
| [A — superseded numbers and replaced prose](#a--superseded-numbers-and-replaced-prose) | inline in the size note, the verification claim, the helper box, the height fill, the colour split, the expected numbers and *Still open* | current numbers, or a one-line pointer |
| [B — the gotchas, in full](#b--the-gotchas-in-full) | `## Gotchas already paid for`, entries 1–28 | one line per gotcha: the rule, no story |
| [C — the session log, 2026-10-10](#c--the-session-log-2026-10-10-rounds-19c) | `## Session log — 2026-10-10`, Rounds 1 → 9c | nothing; only Round 10's short entry is kept, pointing here |
| [D — reading the transcript, long form](#d--reading-the-transcript-long-form) | `## Reading the transcript — logo/*.jsonl` | the same recipes, trimmed |
| [E — the long form of the technical sections](#e--the-long-form-of-the-sections-round-10-distilled) | the helper box, the height fill, the colour split, the emitted-SVG rules, the expected numbers | the same rules, distilled — the reasoning stays here |
| [F — what Round 10 added](#f--what-round-10-added-and-where-it-went) | *(new)* | gotcha 29, the three doc-vs-code mismatches, the new files |

> **For whoever distils next:** move narrative *here* and leave a pointer. The rules, the
> knob table and the expected numbers are the parts that must stay exact; prose about how a
> bug was found is what decays.


---

## A — superseded numbers and replaced prose

Each item is quoted exactly as it stood, with the lines it occupied. Several of these sentences were believed for days; that is the point of keeping them.


### A.1 — the size-discipline note, as of Round 9c
*superseded by the size note at the top of `AGENTS.md`.*

*(`AGENTS.md` pre-split, lines 5–15.)*

> > **Size discipline** (the root `AGENTS.md` says the same): this file is the working set, and
> > it is **86.1 KB measured after Round 9c** (48 KB before Round 9). That number is computed,
> > not remembered — the note here claimed 62 KB while the file was already 72, which is exactly
> > how size discipline dies. Round 9c added ~12 KB in two rounds' worth of findings and has
> > **not** been distilled yet; see *Still open*.
> > When a round finishes, distil it into the knob table / gotchas / expected numbers and let its
> > narrative shrink; do not append forever. The
> > session log is the first place to compress — a round's substance belongs in the sections
> > above it, and its log entry should be a paragraph pointing at them, which is what Round 9
> > did. Round 6's archive-verbatim pass (`AGENTS.old.md` upstream, 77 KB → 54 KB) is the
> > precedent if this needs it again.

### A.2 — the Round 9c verification claim
*superseded; re-verified 2026-10-11, result in `AGENTS.md`.*

*(`AGENTS.md` pre-split, lines 17–30.)*

> > **Verified 2026-10-10 22:55 (Round 9c)**: `gen_logo.py`, `--mark` and `--monogram`
> > regenerate all three SVGs **byte-identically across runs**; `validate_logo.py` prints OK for
> > each (type check + box check + **the colour split check** + **the render check**, which
> > rasterises the file with QtSvg and ImageMagick MSVG so a *viewer* — not the generator —
> > decides whether the two-tone split is really on screen), and **a check that raises now names
> > itself instead of dying as a bare traceback** (gotcha 26); `xmllint --noout` clean.
> > `logo/*.jsonl` is gitignored (verified with `git check-ignore -v`), so the transcript can
> > not be swept into a commit of the logo. The C is `--c-paint solid`: the blue is its own
> > path, because `clip-path` renders 100%-blue in Qt and `mask` renders no-blue in MSVG. The mark is two-colour — **KW green,
> > Capture blue** — see *The colour split*, and its type is **stretched ×1.753 across the
> > baseline** to fill the helper box — see *The height fill*, and *The box is four mouse
> > clicks* for why that number is not 1.784. Every number below was re-measured, not copied
> > from the transcript: Round 6 exists because copying is exactly how a dead session's bugs
> > survive into the docs, and Round 9 was itself recovered from a dead session.

**Round 10 note.** "`validate_logo.py` prints OK for each" was true of a *run*, not of the file. On 2026-10-11 `validate_logo.py logo/kwcapture.svg` does **not** reliably print OK: it crashes intermittently in `box_check` with the two messages the dead sessions left behind (gotcha 29 — reproduced 2/5, 0/12, 2/40 in three samples, and in a 70-line pure-Python extract with no numpy and no fontTools). And `kwcapture.svg` reports `stem area 0.03% blue` where this file recorded 0.00%. Neither is a change to the artwork; both are reasons not to trust a single green run.

### A.3 — the helper box: the falsified fit, and the Round 9 correction block
*the clearance table is superseded; the current one is in `AGENTS.md`.*

*(`AGENTS.md` pre-split, lines 157–177.)*

> > **Corrected in Round 9.** This section used to say "raise the floor and clearance
> discriminates again: `--min-clear 1.0` makes `top` the winner". It did — and `top` then put
> the word **1.59 px outside the box**, because `fits()` tested the monogram and only the
> *nominal* box, so buying clearance above the cap line meant spending it through the top
> edge. Both halves of "inside the box **and** clear of the monogram" are now tested, against
> the quad (see *The box is four mouse clicks*), and a placement that spills is simply not a
> placement. Measured after the fix, `--no-height-fill`:
> >
> > | `--min-clear` | chosen | cap | closest ink |
> > |---|---|---|---|
> > | 0.5 (default) | centred / centred | 4.310 mm | −0.08 px (the A's tip on a leaning edge) |
> > | 0.9 | centred / centred | 4.273 mm | +1.20 px (inside) |
> > | 1.2 | centred / centred | 4.169 mm | +4.76 px |
> > | 1.5 | centred / centred | 4.065 mm | +8.41 px |
> >
> > Raising the floor now costs **type size**, not containment — which is what a guard rail is
> > for. If you re-measure the old table: `top` is not rejected by the monogram at all, it is
> > rejected by the box.
>
> Round 4 recorded the opposite of all of the above (centred 72%, top 100%, "the geometry
> forces the top edge"). That was the anchor bug talking — see gotcha 18 for the rule.

### A.4 — the height fill: what it cost, honestly
*the taste argument. Shipped numbers and escape hatches are in `AGENTS.md`.*

*(`AGENTS.md` pre-split, lines 258–270.)*

> ### What it cost, honestly
>
> `x1.753` is a real distortion. Inter ExtraBold at that stretch is **condensed**: the rendered
> A is 51.1 px wide against 92.2 px tall, i.e. **0.55 × as wide as it is tall** — the drawn
> capital-A ratio (0.982) is preserved *unstretched*, which is what the type check asserts, but
> nobody sees it unstretched. Read at 512 px: the word is much more present and the dead space
> in the upper right is gone, the counters in `P R A` are squeezed but open, and the pointer-A
> reads **more like a cursor, less like an A** than it did. Escape hatches, in order:
> `--max-stretch 1.35` (75.7% of the height, letters nearly normal — the best-looking of the
> three by a stranger's standard, but not what was asked), `--max-stretch 1.5`, and
> `--no-height-fill`. A word that is *both* undistorted and this tall cannot fit this box: the
> length is already 100% full, so the alternatives are a shorter word, a shorter box, or a
> second line — all sketch decisions.

### A.5 — the colour split: what it bought, honestly
*an eyeball, and this file has been wrong about this shape twice.*

*(`AGENTS.md` pre-split, lines 360–367.)*

> * **What it bought, honestly** (rendered at 512, both sketches): with the correct ring the
>   blue is a bracket with a long, upturned bottom arm — it reads as a **C**, and the pointer-A
>   sits inside its mouth, so `C · A · PTURE` finally lines up across the mark. `APTURE` reads
>   as one word now that the pointer and the letters share a colour. What colour still cannot
>   do is *curve* anything: the C is made of straight strokes and square corners, so if the
>   owner wants a curved C that is a sketch job. And the stem being green means the monogram
>   can be read `| <` + `W` before it is read `KW` — `--no-c-split` is the control for that
>   trade, and a stranger test beats any opinion here, including mine.

### A.6 — the pre-fill reference numbers, and the paint-only argument
*pre-Round-9 geometry; do not compare a current file against these.*

*(`AGENTS.md` pre-split, lines 718–728.)*

> Pre-fill (2026-10-10, before Round 9), for reference: `ink 14.1,67.0 -> 497.9,445.0`,
> `kw<->a 9.45`, `kw<->wordmark 75.48`, box check `-0.08 px`. The fill moved the word down
> (seating) and up (stretch), so the padding closed in from 14.1 to 7.5 px L/R: the word is
> now the widest thing on the artboard, which is the point.
>
> The colour split is **paint only**: these bounds are identical to the ones the single-colour
> mark produced, to the last decimal, which is the proof that adding the clipped `#kw-c` did
> not move a point of the artwork. If a bound ever changes after a colour edit, the edit was
> not a colour edit. (The *ink* the blue covers is not a bound and is worth knowing: the C ring
> captures **42.0%** of the mark monogram's ink and **39.1%** of the original's — measured on a
> 0.15 mm grid, so the two colours are near-balanced rather than one garnish on a big shape.)

---

## B — the gotchas, in full

Entries 1–28, verbatim (`AGENTS.md` pre-split, lines 418–667). `AGENTS.md` keeps one line each. **Gotcha 29 is new in Round 10 and is told in `AGENTS.md`**, not here, because it is still open — and it is the one this archive's own rules were written to catch: a crash that names itself is what made this find analysable at all.

## Gotchas already paid for

1. The sketch shipped as an **A4 portrait page** (210×297 mm) with ~36 mm of artwork
   sitting off-centre. That is the "canvas size" bug; the fix is artboard→512² and
   centring, not scaling the drawing.
2. Two paths in the sketch (`path2`, `path16`) **rendered nothing at all**: a bare line
   with `fill` and no `stroke` has no area. Don't assume a drawn path is visible — render
   it. (Those two were stray strokes; they're gone in the output.)
3. **CACAPTURE** — see THE RULE.
4. `fontTools`: glyphs are y-up, SVG is y-down, so the matrix is `(k,0,0,-k,...)`; use
   `OS/2.sCapHeight` (not `hhea.ascent`) to size caps, or the word sits too high/tall.
   TrueType `qCurveTo` can carry a *run* of off-curve points — split at the midpoints, or
   bounding boxes come out wrong.
5. Rotated text bbox ≠ anchor + cap height: a 22 mm word at −38° reaches ~13 mm above
   its anchor. `align_top` must use the *measured* union of wordmark **and** pointer, or
   it shoves the word into the pointer.
6. The validator squared the group matrix for paths that had no `transform` of their own
   (scale 10.9 became 118) — if the reported ink bbox is wildly off, suspect the checker
   before the artwork.
7. **A projection bug made `A_SIZE=1.00` render the A at 1.41× cap.** The height fit in
   `place_A()` mixed `dirv` and `perpv` components, so it measured the extent perpendicular
   to **+38°** instead of **−38°** — a line tilted the other way. The knob read 1.00 and the
   artwork said otherwise. Lesson: on rotated text, verify height against the *baseline*,
   end-to-end from the emitted SVG, not from the constructor. `validate_logo.py`'s type
   check now does exactly that, so this cannot come back quietly.
8. **Right height is not enough — the width was wrong too.** Scaling the pointer uniformly
   to cap height made the A 0.71× the width of a real capital A: a condensed A next to
   ExtraBold letters, which reads as a decoration rather than as the first letter of the
   word. Fix is the anisotropic baseline stretch (`A_WIDTH`). And note: the first version of
   that fix divided the target width by the pointer's *unscaled* width instead of its
   scaled one, which cancelled most of the stretch and reported 0.74× — the width check
   caught it on the next run. Anisotropic maths in a rotated frame is not something to
   eyeball; trust `validate_logo.py`.
9. **"As large as possible" needs an optimiser, not a formula.** The box gives a size
   ceiling, the monogram can veto it, and *where* the word sits in the box can change what
   either allows — so enumerate the placements and bisect the cap height for each, instead
   of solving one placement and assuming it generalises. (The measurements this entry was
   written from — top 100%, centred 72%, base unusable — were falsified by the anchor bug;
   post-fix all three tie at 100%. The **method** lesson stands, the numbers did not: see
   gotcha 18.)
10. A naive shrink loop (`cap *= gap/required`) **ran away to 0.14 mm cap**. The predicate
    is monotone in cap, so bisect it.
11. **Convex-hull tolerance must scale with the shape.** Rounding coordinates to 1e-6 for
    dedup while rejecting collinearity at a cross product of 1e-9 makes a 300-unit box
    return 24 "corners", so the box is never recognised. Use an area tolerance ≈1e-9·span².
12. Walking a closed polygon, **opposite edges are anti-parallel** (~180° apart, not ~0°);
    comparing them as parallel rejects every real box.
13. **`--` inside an XML comment, again** — a comment naming the `--mark` flag. Now
    structurally impossible: everything goes through `write_svg()`, which refuses to write
    a comment containing `--`. Same family: an f-string with a misplaced `"` closed
    `transform="…"` before `rotate(…)`; xmllint caught it, a browser would have just
    quietly dropped the rotation.
14. **The width target must be measured at the fitted cap height.** In mark mode cap is
    4.310 mm; taking the reference capital A at the module's `CAP` (3.30 mm) made the A
    0.75× wide again — the skinny-A bug re-imported through a different door.
15. **The anchor is not the left edge of the word.** Because the A is placed behind its
    anchor, `layout()` fitted `A + PTURE` to the box but handed the box's near corner to
    PTURE, so the A hung ~5 mm **outside the box** (62 px by the checker's ruler) and the
    word stopped short of the far corner. The owner spotted it by eye before any test did.
    The first fix over-corrected and split the word in half (gap of `a_w + 2·gap` between
    the A and the P). Both are impossible now that the box check exists.
16. **The first version of the box check reported the *cosiest* point, not the riskiest.**
    It tracked `max(depth)` and cheerfully printed "+46 px inside" while the A was 20 px
    outside. Containment questions always want `min(depth)`.
17. **Load each font once.** `mark` mode opens the same OTF ~200× while bisecting; doing
    `TTFont()` + `getBestCmap()` repeatedly made fontTools' lazy cmap subtable sharing die
    with `'int' object is not iterable`. Use `load_font()`.
18. **Fix the bug, then grep for the sentences the bug wrote.** The anchor bug (gotcha 15)
    left four of its own claims circulating after it was dead: the in-code comment in the
    placement optimiser ("*for this box that is 'hung from the top edge' … centred would have
    been 72%*"), a *Still open* bullet ("*want it centred? it costs 28%*"), a Round-4 sentence
    in the session log, and **a number inside gotcha 9 itself** — found only by running the
    grep this entry prescribes. All four were true measurements **of the buggy layout**, so
    they read as evidence rather than as damage, and a fresh session would have taken them
    for constraints and re-broken the centring. After any layout fix: re-run the optimiser,
    re-measure, and search the prose and the comments for conclusions that were only ever
    true of the broken version —
    `cd logo && grep -n "72%\|top edge\|28%" *.md *.py` (`*.md *.py`, never `logo/*`: the
    transcript in here is 3.4 MB of base64 and will answer your grep with screenshots).
19. **A boolean parameter named `grad` lost an argument fight to a local variable.**
    `build_mark()` already had `grad = root.find("...linearGradient")`, so the new
    `grad=False` parameter was overwritten on every call and `--classic` behaviour leaked into
    the default build (gradient monogram, no split). Python's only complaint was a
    DeprecationWarning about *"testing an element's truth value"* — which is the sound a name
    collision makes. Grep the function body for the parameter name before adding it; call the
    flag `gradient`, and treat "element truth value" warnings as a collision report.
20. **`f("{x:.4f}")` is not an f-string** — it is a call to this module's one-letter
    formatter `f()` with a literal string, which raised `ValueError: unknown format code 'f'
    for object of type 'str'` at the first run. Loud this time; the quiet version of the same
    mistake is a literal brace reaching the SVG. Write `f"{f(x)}"`, and remember that a helper
    named `f` makes every f-string in the file a two-way bet.
21. **A repaint is not a new mark.** The validator saw `#kw-c` as artwork and reported a
    certain `COLLISION` with `#kw` (distance 0.00 px) — and the deeper problem is that
    *everything else passed while the C could have been painted anywhere*: geometry checks
    are blind to paint by construction. Fixed by teaching the checker about identity, not by
    loosening a threshold: an id `<base>-c` is a colour overlay, its ink is not counted twice,
    and in exchange it must be a byte-identical copy of the base `d`, its clip polygon must
    equal the recomputed one, and named sample points in the stem/arm/leg/W must land on the
    intended side. Any future colour work needs that same shape of check — a screenshot you
    looked at is not a test.
22. **A test that agrees with you is not a test.** The first C clip was my own invented
    anatomy: I looked at the shape, decided the C was "the K minus its stem" — a two-stroke
    chevron — and built the clip from that reading. The validator then checked the output
    against **the same wrong derivation** and printed OK; its sample points came from the
    same wrong idea, so they agreed too. Self-consistent, green, and wrong: the ring covered
    only 52–53% ink (the rest sat in the counters), and it left out the very stroke that
    makes the C a C — the W's first rise, up to the peak tip at 12. The owner then numbered
    the letters and the fix was ten indices. Two rules out of that:

    * **A letter partition is intent, and intent belongs to the owner.** Ask for the vertex
      numbers, or take them from the sketch's own structure — never reverse-engineer them
      from a render and then trust your reading.
    * Every such check needs at least one assertion the generator **cannot agree with by
      construction**: here "≥95% of the clip's area must lie on the drawing's ink" and "0%
      of the stem's area may be inside the clip". Both fail my ring on the first run, and
      neither depends on my idea of what the C is.
23. **The helper box is four mouse clicks, not a rectangle.** `box_frame()` hands back
    `(length, height)`, and both are *averages* of a quadrilateral whose edges are not
    parallel and whose corners are not right angles: on the shipped box the top edge is
    0.62° off the base, so the room over the baseline is 7.920 mm at one end and 7.651 mm at
    the other. Anything fitted to the average hangs outside the real shape — the height fill
    came out 1.6 px over the top edge at the far end of the word, which is where the word is
    tallest and where the box is shortest, and only the box check saw it. Two rules:

    * Treat a hand-drawn guide as a **polygon of half-planes** (`halfplanes()`), never as a
      bounding box, whenever the promise is "inside".
    * Measure the **ink**, never the nominal band, when the thing being contained overshoots
      its own metrics (Inter's caps and baseline overshoot ~0.5 px, and a ×1.75 stretch
      multiplies that overshoot too: ink band 4.365 mm, nominal cap 4.310 mm).
24. **Gotcha 22 came back within one session, in a check I wrote to fix it.** The new
    `fits()` containment test sampled the word at `anc` — the whole-word left edge — instead
    of `wanc`, the anchor the word is actually drawn from, so it tested ink sitting ~5 mm
    *short of* the word, in the tall end of the box, and reported `top` placement as inside.
    Green, self-consistent, wrong: `--min-clear 0.9` still shipped 1.59 px outside. What
    caught it was not reading the code, it was **running the sweep and reading the validator**
    (`--min-clear 0.5…2.0`, printing the chosen placement and the closest ink). So:

    * A new check must be **shown to fail** before it is believed. Four sabotages of the
      emitted mark, each of which must exit 1: stretch ×1.06 too far → *box check*; change
      `scale(1 s)` to `scale(1.1 s)` → *stretches along the baseline*; lift `#a` out of
      `#type` → *stretch does not cover both letters*; push `#kw` into `#type` → *the
      monogram must not be stretched*. All four fail correctly, and one of them (the
      no-op-looking `#a` move) only worked once the sabotage itself was checked with
      `assert changed` — an assertion on the *test*, not the code.
    * When a guide is drawn by hand, print its imperfection (`box taper :` in the `--mark`
      report). The owner cannot see 0.62° in a render, and "why is the answer 1.753 and not
      1.784?" is a question that otherwise gets re-asked every month.

25. **A valid file can be wrong in half the viewers on your desktop while every check says
    OK.** The C was painted through `clip-path` for a full day. The XML was well-formed,
    Inkscape and browsers showed the intended 42%-blue C, and `validate_logo.py` was green —
    because it reads path data and does its own geometry, so it agrees with the generator by
    construction. **QtSvg ignores `clip-path`** (measured: Qt 6.10.2 drops a canonical
    `<circle>` clip too), so Gwenview and every Dolphin thumbnail showed a **100% blue**
    monogram. The owner found it by eye, in a file manager.

    * "Then use a mask" is not the fix: ImageMagick's MSVG treats an unparsed mask as *hide
      everything* and the C vanishes. The two weak renderers fail in **opposite directions**,
      which is why the shipped form asks for nothing at all — `--c-paint solid` draws the C
      as its own path.
    * The rule generalises past colour: **any feature a viewer may silently ignore is a bug
      waiting for the viewer that ignores it.** Prefer plain geometry over `clip-path`,
      `mask`, `filter`, CSS — and over `<text>`, already banned for exactly this reason.
    * The check that catches this has to **render**, with a renderer that is not the one the
      generator assumed. `validate_logo.py` now does, over QtSvg and MSVG. Proven to fail:
      `--c-paint clip` → *QtSvg renders 100% blue*; `--c-paint mask` → *MSVG renders no blue
      at all*. Same lesson as gotcha 22, one level up.
    * Side effect worth knowing: **MSVG cannot render our `userSpaceOnUse` gradient at all**,
      so `--classic` is not MSVG-safe. The render check is scoped to two-tone output for
      that reason rather than pretending the old look is supported everywhere.

26. **An exception that escapes a check is a bug in the checker; a bare traceback is a bug in
    the report.** Round 9b's final verification printed `IndexError: list index out of range`
    (one build) and `TypeError: '<=' not supported between instances of 'float' and 'list'`
    (the mark), each as a single `| tail -1` line — no frame, no check name, nothing to chase.
    ~570 later runs did not reproduce either, and no reachable `float <= list` exists in the
    file, so **it is not fixed**; what got repaired is the reporting that made it un-analysable:
    * `run_check()` wraps every check: a raise prints `CRASH in <name>` + the traceback, counts
      as a FAIL (a check that died checked nothing), and the last line reads `NOT A CLEAN RUN`
      so even `| tail -1` cannot mistake it for an ordinary problem count. Proven by injecting
      that exact `TypeError`, and a check returning `None`.
    * `ink()` rejects a viewBox that is not 4 numbers — the one place where *file content* can
      raise that nameless `IndexError` through `main()`'s `vb[3]`.
    * `_msvg_render()` uses `mkstemp`, not `/tmp/…-<pid>.png`: a pid-keyed path is unique only
      among *live* processes, so a raster left by a killed run can be read back by whoever
      inherits the pid. An unreadable raster now reports the renderer's name and the byte count.
    * Generalises: **never diagnose from the tail of a pipe.** The context was destroyed by the
      reporting choice, and a session went into a bug report that could not be re-read.

27. **MSVG mis-renders `rotate()` — the type lands in the wrong place, and no colour check
    can see it.** `render_agreement.py` measures, per engine, the ink box of each colour and
    compares it with the box the path data implies (every `transform` applied by hand):

    | file | path data | Inkscape | QtSvg | MSVG |
    |---|---|---|---|---|
    | `kwcapture.svg` blue | y 76 .. 444 | ✅ | ✅ | **y 102, x to 468** (26 px off) |
    | `kwcapture-mono.svg` blue | y 102 .. 295 | ✅ | ✅ | ✅ (no `rotate()` in this file) |
    | `kwcapture-mark.svg` blue | y 60 .. 505 | ✅ | ✅ | **y 127, x to 511** (67 px off, clipped) |
    | every file, green monogram | — | ✅ | ✅ | ✅ |

    The pattern *is* the diagnosis: MSVG is wrong exactly where a `rotate()` is involved and
    right where there is none. Ruled out by measurement, not opinion: it is not the argument
    separator (comma form, byte-identical output), not the transform *chain* (folding each
    chain into one `matrix()` changes nothing), and not `rotate()` being nested under a
    `scale()` (folding the outer scale into the root `viewBox` changes nothing). **Baking the
    transforms into the path data does fix it** — measured, MSVG then agrees — which is the
    same argument that chose `--c-paint solid`, one level up: ask the renderer nothing.
    * It is NOT fixed in the shipped files, deliberately: baking means applying the matrix to
      every `M`/`L`/`C` control point, and that (a) throws away the mm-space geometry the C
      polygon and the sketch are defined in, (b) removes the `#type` transform that
      `band_check` reads to measure the height fill honestly, and (c) breaks "the overlay is
      derived from the same path data" — three invariants this file pays real money for.
      The owner decides; the options and their costs are in *Still open*.
    * The render gate in `validate_logo.py` cannot see this **by construction**: it counts
      green and blue pixels, and a rotated-out-of-place wordmark is still blue. Position has
      to be measured separately — that is what `render_agreement.py` is for.
    * Practical reach: ImageMagick without the `librsvg` delegate (many servers, some upload
      pipelines) renders the wordmark wrong. KDE, Inkscape and browsers are fine. Installing
      `librsvg2-bin` gives ImageMagick a delegate and sidesteps MSVG entirely.

28. **A shared fontTools glyphset corrupts state, and the crash messages are impossible —
    that impossibility is the diagnosis.** `--mark` bisects cap height, building a `Wordmark`
    dozens of times per run, and each one used to draw through the **same cached glyphset**
    from `_FONTS`. That intermittently wrecks state inside fontTools' CFF extractor. Four
    messages were caught, in four unrelated places, ~1–3% of builds:

    | message | where it surfaced |
    |---|---|
    | `'str' object is not callable` | `svgPathPen.pointToString` calling `self._ntos` |
    | `'T2OutlineExtractor' object is not subscriptable` | fontTools' charstring interpreter |
    | `unsupported operand type(s) for *: 'float' and 'Wordmark'` | our arithmetic, on an object that cannot be there |
    | `compile() arg 1 must be a string, bytes or AST object` | the interpreter, not our code |

    A type error describing operands that the source code cannot produce is not a logic bug —
    it is **reading garbage**. Measured 2026-10-10: **2/60** builds failed with the shared
    glyphset, **0/60** with one glyphset per `Wordmark`, then **0/120**. The fix keeps the
    `TTFont` cached (that half of the original bug was real: a second `TTFont()` on the same
    file dies in fontTools' lazy cmap subtable) and stops caching the *glyphset* —
    `load_font()` stores `glyphset=None` and `Wordmark.__init__` calls `font.getGlyphSet()`.
    Output is **byte-identical** before and after: the corruption never reached the artwork,
    it only ever killed the process.
    * This is very likely what the Round 9b session saw and could not explain — see the open
      item. Same shape: a `TypeError` about types the code cannot be holding, during `--mark`
      work, unreproducible afterwards.
    * **Generalises:** a cache is only safe if what it hands out is immutable. A fontTools
      glyphset is a stateful extractor factory wearing a dict's clothes. When the message
      describes an impossibility, stop reading your own code and start asking what you share.
    * Debugging note: it hid for weeks because the failure rate is ~2% and the messages never
      repeat, so no two people chase the same symptom. Reproduce with 40+ builds in a loop,
      not by re-running once and shrugging.

### 31 — Inkscape's `-b none` is an opaque white background (Round 11)

Every transparent icon render in `icon/build.sh` originally passed `-b none`, because that is
what the flag looks like it does. It is accepted, `inkscape` exits **0**, and the PNG that comes
out has `alpha = 255` in the corner: white. The set looked built and measured fine — file sizes
differed from the white-backed `-b white` renders only slightly, and nothing complained. The
corner-pixel check is two lines:

```bash
python3 -c "from PIL import Image; print(Image.open('glyph-64.png').getpixel((0,0))[3:])"
```

Omit `-b` **entirely** and the same render has alpha 0 in the corner. `build.sh` now has an
`inkx()` helper that never passes `-b`, plus a comment saying why, so the flag cannot creep
back in through a copy-paste.

* **Generalises:** a flag that is *accepted* is not a flag that *did what you meant*. Same family
  as gotcha 25 (`clip-path` shipped, QtSvg ignored it) and gotcha 30 (a check that skips and
  prints nothing): the toolchain's happy path is not a specification of the artefact. For any
  derived image, assert a **pixel**, not an exit code — here, one corner sample would have caught
  it on the first build.

### 32 — ImageMagick compositing returns a blank canvas and exits 0 on this box (Round 11)

The tiles (glyph centred on a white square) were first written as one `magick` line:

```
magick -size 1024x1024 xc:white glyph-1024.png -gravity center -composite tile.png
```

What came back, every time, was a **blank greyscale canvas** at the right size with exit status 0.
Variations tried, all failing the same way while reporting success: `-size … xc:white` vs
`xc:none` as the base, `magick composite` (the legacy binary form), `-layers flatten` instead of
`-composite`, and `-type TrueColor` to force the colour space. `magick identify` was what gave it
away — it reported `Type: Grayscale` for a composition of a green-and-blue mark, which is the
kind of impossibility gotcha 28 says to stop and read rather than work around.

The tiles, the social card and the contact sheet are therefore **Pillow** (`tiles.py`,
`card.py`, `contact.py`), and each one verifies its own output before writing — a blank or
grayscale tile exits 1, `tiles.py` fails loudly rather than shipping white squares.

* Whether this is this machine (the `LD_PRELOAD` shim and non-ECC RAM of gotcha 29 live here
  too) or this ImageMagick build is **not established**, and it is deliberately not chased: the
  workaround is cheaper than the diagnosis and Pillow is already a dependency of the validator's
  render check. Note what *is* established: the failure is silent, and the exit code is a liar.
* **Generalises:** when a compositing step's output has a *type* or a *statistic* that its inputs
  cannot explain (grayscale from coloured inputs, all-zero variance, uniform colour), treat that
  as a hard failure inside the build script, not as something to notice later in a viewer.

### 33 — a card that writes off its own canvas, and prints its own dimensions approvingly (Round 11)

The first `card.py` picked font sizes by hand and ended with

```
wrote /home/tjandra/way_scr_cap/logo/icon/github-social-preview.png (1280, 640)
```

which was perfectly true of the *canvas* and false about its content: the tagline ran past the
right edge. The success line printed the size of the image, not the extent of the ink in it, so
it read as a check and was not one. Only looking at the rendered card found it.

`card.py` now measures every string with `font.getlength()`, shrinks it until it fits its column,
and then **asserts that nothing reached the right edge** — a failure mode the generator cannot
agree with by construction (gotcha 22's requirement for a real assertion), because a layout that
overflows is exactly what the assert is for.

* This is gotcha 24 ("a test that agrees with you is not a test") arriving in a *builder* rather
  than a checker, which is the interesting part: build scripts get the same treatment as tests —
  show the builder failing on a deliberate overflow before believing it when it passes.
* **Generalises:** "wrote <path> (<size>)" is a statement about a file, not about its content.
  For anything drawn, the useful assertions are ink-based: bounding box of non-background pixels,
  contrast ratio, colour presence — the same move that turned `validate_logo.py` from a geometry
  checker into something that can see paint.

### 34 — the GitHub API has no repository image, and a repository has no avatar (Round 11)

"Set the project icon on GitHub" sounds like one API call. It is not:

* `PATCH /repos/{owner}/{repo}` — the documented way to change repository settings — takes
  `name`, `description`, `homepage`, `has_wiki`, `has_issues`, `has_discussions`,
  `default_branch` and so on, and **no image field**.
* Measured 2026-10-11 with an **admin** token on this repo, rather than trusted from the docs:
  `GET`/`POST /repos/tjandrasg/kwcapture/social_preview` and
  `GET /repos/tjandrasg/kwcapture/image` → **404 Not Found**; GraphQL introspection returns 262
  `Mutation` fields and **zero** of them match `avatar|social|preview|image|upload`; and
  `GET https://github.com/settings/profile` **with that same token** → **302 to `/login`**,
  because the web app authenticates on a cookie session and a PAT is not one. A token cannot
  click the button, so the upload cannot be scripted and is not claimed anywhere in this folder.
  (An admin *can* delete the repository through this API and cannot set its picture. Worth
  remembering when a tool promises "set your project icon via the API".)
* Six more candidate paths, all **404**, in case a future session is tempted to guess again:
  `POST /repos/tjandrasg/kwcapture/{social-preview-image, socialPreview, social_preview,
  preview-image, image, avatar}`.
* **The read side does exist, and it is the useful half.** `Repository` carries
  `openGraphImageUrl` and `usesCustomOpenGraphImage`, so the *upload* is unverifiable-by-luck only
  if you forget to ask. Baseline measured on 2026-10-11, after the icon set was pushed:
  `usesCustomOpenGraphImage: false`, `openGraphImageUrl` still the generated
  `https://opengraph.githubassets.com/<hash>/tjandrasg/kwcapture` placeholder. After the click in
  the web UI, `true` plus a `github-production-…` asset URL is the evidence it worked — the same
  discipline as `curl -o /dev/null -w '%{http_code}'` on the README header: **the claim is the
  check, not the upload attempt**.
* **Avatars belong to a user or an org, never to a repository.** A repo's "icon" *is* its social
  preview; `github-avatar-400.png` is therefore for a profile, not for the repo, and shipping it
  next to the card without saying so would have invited the next person to hunt for a repo avatar
  setting that does not exist.

So `README.md` §8 documents the two uploads as manual steps, and the repo carries the artefacts.
Check the API's actual field list **before** promising an automation, and check which object owns
the asset you were asked to set — the two mistakes here (assume an endpoint exists; assume a repo
has an avatar) both come from reasoning about the feature instead of the schema.

### 35 — a build script's report vanishing behind `2>/dev/null` (Round 11)

`icon/build.sh` ended with a summary of what it had just made:

```bash
magick identify --format '…' favicon.ico … 2>/dev/null | head -8
```

`identify` spells that flag `-format`. With `--format` ImageMagick takes the format **string as a
filename**, errors out (`no decode delegate for this image format '--format'`), and the
`2>/dev/null` ate the complaint. Net effect: the report printed **nothing at all**, the script
continued, exited 0, and the build looked like a build that had reported. It was spotted only
because the earlier version of that line (without `--format`) had printed something, and the
absence of the usual lines was noticed in the log.

Fix, and two measurements that came with it:

```bash
magick identify -format '  %f  %wx%h  %[type]  %b\n' favicon.ico …   # one dash
```

* stderr on the report line is **no longer suppressed**: a report is allowed to complain.
* `%-28f`-style width specifiers are **not** supported by this ImageMagick build — it emits
  `28f` and warns `unknown image property "%-"`. Pad with `awk` (as the `ls` report above the
  identify line already does), not with the format string.

* **This is gotcha 30 one layer down.** The rule "a check that skips must say so" applies to the
  tooling that *inspects* the checks: a build script's summary is a check whose failure mode is
  silence, and it is the part a human reads instead of re-running. Ask of every report line:
  *if this stopped printing, would anything change?* Here the answer was no, and it stayed
  broken across two runs.
* Related and deliberate in the same file: the builders verify **pixels** (a tile that comes out
  blank or greyscale exits 1, `card.py` asserts no string reaches the canvas edge), because
  gotchas 31–33 together say that on this machine an exit code is the weakest evidence there is.

---

## C — the session log, 2026-10-10, Rounds 1–9c

Verbatim (`AGENTS.md` pre-split, lines 938–1171). Nine rounds of narrative, two recovered dead sessions, three wrong verdicts struck out. `AGENTS.md` keeps only the current round's entry (Round 11 as of 2026-10-11; Round 10's narrative is Part G below), because a log is the first thing to compress and the last thing anyone re-reads.

## Session log — 2026-10-10

**Round 1.** Took the hand-drawn sketch, fixed the artboard (A4 → 512², centred), typeset
the letters as outlines, made the pointer behave as a letter instead of an ornament. One
wrong turn (typesetting `CAPTURE` → CACAPTURE) and one rejected experiment
(`--a-upright`) recorded above so they don't get re-walked. Files created: `gen_logo.py`,
`validate_logo.py`, `kwcapture-mark.svg`, this file.

**Round 2 — the A was still too big.** Owner's read of the state: *"big C, medium A, small
PTURE"*; what they want is *"big C, and APTURE with the A the same height as the P"*. Two
things fell out of that:

1. `A_SIZE` 1.30 → **1.00**, `A_GAP` 0.90 → **0.70** (once the A shrank, 0.90 read as a
   word break). The mark is now one big letter (the C in the junction) plus one evenly-set
   word.
2. Checking that change end-to-end exposed **the projection bug** (gotcha 7): `A_SIZE=1.00`
   had *never* meant cap height — it rendered 1.41× cap, because the height fit measured
   perpendicular to +38° instead of −38°. So every earlier judgement about "how big the A
   looks" was made against a number that was lying.

`validate_logo.py` grew a **type check** that measures the A and the word straight out of
the emitted SVG (A height vs cap height, shared cap line, shared baseline) and fails on
>2 px drift. Run it after *any* change to `A_SIZE`, `A_GAP`, `ANGLE`, `CAP` or `ANCHOR`.
Current numbers in *Expected numbers* above.

**Round 3 — "are you sure the width is correct too? 😏"** No. Height was right, but the
pointer scaled uniformly was 0.71× the width of a real capital A: a skinny A next to fat
letters. `#a` now carries a single `matrix()` that stretches it along the baseline to the
face's own capital-A ink width (3.282 mm = 0.982× cap as emitted), height unchanged, and
the type check gained a width assertion (0.85–1.15× cap, font-free). Gotcha 8 records both
the real bug and the slip in the first fix. **Lesson for whoever picks this up: a check you
have to ask me for is a check the tool should have run by itself — if a dimension looks
wrong, measure it, don't argue with it.**

**Round 4 — the helper box.** Owner edited `kwcapture-mark.svg` in Inkscape: a redrawn
(a cleaner, more geometric) monogram plus a black four-corner box, and asked for the box to
become `A` + `PTURE`, on the box's base slope, as large as possible, box removed from the
render. Their edit was copied to `kwcapture-mark-sketch.svg` **before** anything was
generated, because `--mark` writes to `kwcapture-mark.svg`. `gen_logo.py` grew `--mark`:
read the box (parallelogram detection, `fit-box` by convention) → base angle / length /
height → optimise placement and bisect cap height subject to box ∧ clearance → re-centre →
emit with no box. Result: **−43.12°, cap 4.310 mm, 100% of the box, 0.91 mm clear of the
W** — that clearance figure belonged to the buggy top-edge placement; the shipped centred
fit is 9.45 px = 0.79 mm clear (see the helper-box table). Bugs found on the way and
recorded above as
gotchas 9–14 (antiparallel test, hull tolerance, runaway shrink loop, `--` in a comment now
guarded by `write_svg()`, width reference measured at the wrong cap). Two things worth
remembering: *their box overlaps the W, so the monogram can veto the box* — it does not
veto it at today's numbers, but `--min-clear` is the reason the fitter can refuse — and
***"it fits" is a claim that needs a test, not a calculation***.

**Round 5 — "the mark version is better ✅ but why is the A outside the box?"** Because
`place_A()` parks the pointer *behind* the anchor it is given, and `layout()` treated that
anchor as the left edge of the whole word. The fitted length was right but the composition
sat `a_w + gap` too far along the baseline: the A hung outside the box's near end (62 px by
the checker's ruler) and `PTURE` stopped short of the far corner. **The owner saw it;
nothing in the toolchain did** — the box is deliberately absent from the output, so no
existing check could see it. Fixed by handing the pointer and `PTURE` the same shifted
anchor (`layout()` now returns both `anc`, the whole-word left edge, and `word_anc`); the
first attempt over-corrected and split the word in half, so gotcha 15 records both
failures. Added the **box check** to `validate_logo.py`: it re-reads the box from
`-sketch.svg`, undoes the re-centring shift, and fails on ink more than 1 px outside. It
caught the broken file immediately (62 px outside) and now reports **−0.08 px**, i.e. on the
edge and inside. Two more of my own bugs fell out of writing it: the check first tracked
`max(depth)` instead of `min` and printed *"+46 px inside"* while the A was 20 px out
(gotcha 16), and re-opening the font ~200× during the bisection crashed fontTools
(gotcha 17, `load_font()`). And the bug's most durable lie was retracted: with the anchor
fixed, **centred reaches 100% of the box too**, so Round 4's "the geometry forces the top
edge" was the bug talking. Cleared out of the code comment, the *Still open* list, Round 4
and gotcha 9 — gotcha 18.

**Round 6 — recovering a session that died mid-sentence.** The Round-5 session ran out of
tokens *while writing this log entry*: its last tool call came back
`Error: Expected ',' or '}' after property value in JSON at position 2298` (a truncated
`edit_file`), and its last successful edit had landed the gotchas but not the log. The
intended text was still recoverable — the dead call's arguments survive in
`logo_talk.jsonl` under `message.toolCalls[].function.arguments`, and so does the reasoning
that produced them — but everything in it was 20 minutes and one refactor old, so it was
**re-measured before being believed**. That is what caught the four stale claims of gotcha
18 — the fourth was hiding inside a gotcha, i.e. inside the very file this rule tells you to
trust — plus `kwcapture-mono.svg` being advertised in *Files* while absent from disk, and a
`ege` typo in the anchor paragraph.
The rule from the root `AGENTS.md`, paid for again: **log after every milestone, in small
pieces** — a 700-token tool call is how findings die. And when a predecessor dies, its
transcript is a real archive: see *Reading the transcript*.

**Round 7 — "make the C more visible: K's stem green, pointer and PTURE blue, so we have KW
(green) and Capture (blue)".** The owner's idea, and the diagnosis in it is right: the stem
is the one stroke *competing* with the C, so separating them by colour is cheaper than a
redraw. Shipped as **paint only** — `#kw` flat green, `#kw-c` the identical `d` clipped by
`<clipPath id="c-clip">` in blue, `#a` and `#wordmark` the same blue. Details worth keeping:

1. The clip polygon is **derived from the drawing's vertices by index**, because both
   monograms turned out to share one 19-vertex topology (see *The colour split* for the
   index table). The K and the W touch only in the shared foot at the V between vertices 4
   and 5, so the whole C/W cut is one short segment; everything else runs through empty
   space. `len(verts) != 19` refuses to build.
2. `#0000ff` was chosen against **the green it touches**, not the white page: 2.87:1 from
   `#00ac4e`, where a nicer-looking `#3b82f6` is only 1.23:1 and the C would dissolve into
   the W. Measured, in the knob table.
3. **Every ink bound in *Expected numbers* is unchanged**, to the decimal, before and after:
   that is the proof a colour edit didn't disturb the fit.
4. Honest read of the renders (512 px, both sketches): the bracket is the most prominent
   element and `APTURE` reads as one word now that the pointer-A and the letters share a
   colour. I also wrote: "it is still a **chevron**, and the monogram reads `| < W` — three
   objects". **That verdict was about my wrong ring, not about the design — Round 8 struck
   it.** Curving anything remains a sketch job. `--no-c-split` is the control for the
   stranger test; `--classic` is the old look.
5. `validate_logo.py` grew the **colour split check** (nothing else there can see paint) and
   it was **proven to fail**, not just to pass: shifting the clip 4 mm onto the stem →
   `stem 0/3 green`, 8 problems, exit 1; editing `#kw-c`'s `d` (a redraw in disguise) →
   `the #kw-c overlay is not a copy of #kw's path data`, exit 1. It also finds its parent
   sketch by *content*, so a `--monogram` built from the other drawing is still checked.
6. Three of my own bugs, recorded as gotchas 19–21: a `grad` parameter losing to a local
   variable of the same name, `f("…")` not being an f-string, and the validator screaming
   `COLLISION` at a repaint.
7. Side fix while testing the mono: `build()` now binds the monogram as `path1` **or** `kw`
   and the pointer as `path10`/`cursor`/`a`, with a message naming what it looked for and
   what the sketch has. That made `--monogram --sketch logo/kwcapture-mark-sketch.svg` work,
   so the two monograms are now a genuine choice rather than a `KeyError`.

**Round 8 — "the vertex split is wrong, you're hallucinating 😭 the C is not `<`, it is `[`
(three strokes!)".** Correct, and the numbering was the owner's, not mine to infer:

```
  K = 0  1  2  3  4           13 14 15 16 17 18
  W =    3  4  5  6  7  8  9 10 11 12 13 14
  C =    3  4  5  6           12 13 14 15 16 17     <- blue
```

Overlapping rings, because the letters share strokes — 3–4 is the K's leg and the W's first
stroke at once. What changed: `C_RING` replaced my invented polygon; the bottom arm now runs
3→4→5→6 and back 12→13, i.e. it takes the **first W rise all the way to the peak tip**, and
the spine is the zero-width edge 17→3 along the stem. The ring is the outline's own edges
plus exactly two chords (`6→12` across the peak, `17→3` across the stem), which is why it is
exact: **100.0% of its area lies on ink**, where mine managed 52.1% (mark) / 53.3%
(original) with half of it sitting in empty counters.

Also: the validator's W samples had to move — the first rise is the C's bottom arm now, not
the W's — and the check gained the two assertions that do not depend on my idea of the
letter (≥95% of the clip on ink; 0.00% of the stem's area inside it). **Both fail my old
ring**, which is the lesson in gotcha 22: my Round 7 check had been agreeing with me, and I
declared a verdict ("still a chevron, `KW` reads as three objects") on a split that was
never the design. That verdict is struck from *Still open*; Round 7's entry stays as the
record of a wrong turn, with this one pointing at it.

Verified after the fix: both sketches give `clip 10 pts == C_RING, 100.0% on ink, stem area
0.00% blue, stem 3/3 green | C 6/6 blue | W 3/3 green`; the C captures 42.0% / 39.1% of the
monogram's ink; all three artefacts regenerate; `xmllint` clean; and the render — finally —
reads as a **C** with the pointer-A sitting inside its mouth.

**Round 9 — "stretch the height of A + CAPTURE as tall as possible but still fit inside the
black box".** Shipped as `#type`: **×1.753 across the baseline, never along it, over `#a` +
`#wordmark` together**, ink seated on the box's base line, one blend so `--no-height-fill`
remains the identity. Full story in *The height fill*.

The round's real product is the two gotchas. **23**: the obvious answer (`fill the mean
height`, ×1.784) is wrong by 1.6 px because **the helper box is four mouse clicks, not a
rectangle** — top edge 0.62° off parallel, headroom 7.920 → 7.651 mm along its own length —
and `box_frame()`'s `(length, height)` is that shape's average. "Inside" now means
`halfplanes()` everywhere, in the height fit and in `fits()`; the optimiser had the same hole
and had been buying `--min-clear ≥ 0.9` by pushing the word 1.59 px outside the box, which
this file had been *recommending*. **24**: the containment test written to close that hole
sampled the wrong anchor, agreed with me, and shipped the same 1.59 px — caught by sweeping
the knobs against the validator, not by reading the code, so all four new assertions were
**shown to fail** first (and one sabotage edit turned out to be a silent no-op, hence
`assert changed` on the test too). The type check now measures **unstretched**, off `#type`
itself: the A is 0.982 × cap as drawn and 0.55 × cap as rendered, and both numbers are kept
because the second is the design cost.

Verified: mark OK (`box check -0.03 px`); `kwcapture.svg`, `kwcapture-mono.svg` and
`--no-height-fill` all regenerate **byte-identical**; `xmllint` clean; sweeps clean
(`--inset`, `--max-stretch 1.35/1.5/0`, `--min-clear 0.5…2.0`); rendered 512/256/128 — the
word is far more present and legible down the ladder, and condensed. The taste call on how
much stretch is now the owner's, in *Still open*.

**Round 9b — "it's all blue… Gwenview and Dolphin show 100% blue".** The owner was looking at
the folder; I was looking at Inkscape. **QtSvg ignores `clip-path`**, so the blue copy of the
whole monogram — which is what `#kw-c` always was, cut to the C by that clip — painted over
the green one in every Qt viewer. Full diagnosis, the three-way renderer matrix and why
`mask` is not the fix: gotcha 25 and *Which cut-out*.

What changed: `--c-paint solid|mask|clip`, **`solid` the default** — the C ring as its own
path, no cut-out feature anywhere in the file. `validate_logo.py` grew a **render check** that
rasterises the output with QtSvg *and* ImageMagick MSVG and fails if either would not show
both colours, because every check that existed read path data and therefore agreed with the
generator. Both new failures are **proven** (`--c-paint clip` and `mask` each exit 1 with a
named renderer). `#kw-c` is still not a second *drawing*: its path data must equal `C_RING`
recomputed from the sketch, which is the guarantee the old byte-identical-`d` wording was
protecting — said out loud at last, instead of implied by a mechanism.

Two things I got wrong in this round and the owner's question is what caught them: I had
recommended `mask`, and the matrix shows MSVG eats it — **measured after recommending, not
before**; and I had written a first version of the colour counter that matched RGB values
exactly, which reported "0% green" for a trivially-working test file and nearly sent me chasing
Qt's colour management instead of its parser. Both are the same lesson as gotcha 22 in a new
costume: a check that agrees with you, or that you have not seen fail, is not a check.

**Round 9c — recovered from a second dead session; a flake that would not be caught.** The
previous session died one message after its own final verification, which had printed
`TypeError: '<=' not supported between instances of 'float' and 'list'` for the mark where `OK`
belonged (an `IndexError` sibling had appeared one message earlier) — both through `| tail -1`,
so both arrived without the frame that would have explained them. ~570 later runs (every
artefact and mode, in parallel, over 40 `PYTHONHASHSEED` values, replaying both command shapes)
**did not reproduce either one**, an AST sweep found **no reachable `float <= list`** in the
file, and the artefacts themselves are clean and byte-stable. Nothing was "fixed" for it; what
was repaired is the reporting that made it un-diagnosable — `run_check()` now names a crashing
check, prints its traceback and ends with `NOT A CLEAN RUN`, `ink()` rejects a non-4-number
viewBox, and `_msvg_render()` uses `mkstemp` — all three proven to fail by injection. Gotcha 26
is the rule; *Still open* keeps the flake. Side fix: `.gitignore` gained `logo/*.jsonl`
(verified), because `git add -A --dry-run` was about to commit this session's 2 MB transcript.

**And the round's real find, from refusing to stop at "all green":** while re-rendering the
three files per engine to eyeball them, `kwcapture-mark.svg`'s wordmark was visibly clipped in
the ImageMagick panel. It is not a colour problem, so the render gate could never see it —
`render_agreement.py` now measures it, and **it exits 1 on the shipped files on purpose**.

**Then the flake bit again, in front of me.** While re-running the generator after the guard
work, `--mark` died with `TypeError: 'str' object is not callable` inside fontTools'
`svgPathPen`, and a second build with `'T2OutlineExtractor' object is not subscriptable`, and
over a batch of runs two more: `float * Wordmark` and `compile() arg 1 must be a string`. Four
messages, four places, none of them able to happen — the signature of reading garbage, not of
a logic bug. Cause: every `Wordmark` drew through **one cached fontTools glyphset** (`_FONTS`),
and `--mark` builds dozens per run. Measured: **2/60** builds failed shared, **0/60** with a
glyphset per `Wordmark`, then **0/120**. Fixed in `load_font()`/`Wordmark.__init__`, output
**byte-identical** — the corruption never reached the artwork, it only killed the process.
This is very probably the `float <= list` / `IndexError` pair that cost the last two sessions:
same shape, same `--mark` context, same unreproducibility. Gotcha 28; the open item keeps the
residual doubt, because reproducing *those two* messages was never managed.
MSVG places the type 26 px (`kwcapture.svg`) and 67 px (the mark, running off the artboard)
away from where the path data says it must be, and is exact on the mono, which is the one file
with no `rotate()`. Separator, transform-chain and scale-nesting all ruled out by measurement;
baking the transforms fixes it. Whether that cost is worth paying is the owner's call —
gotcha 27 and *Still open*.

---

## D — reading the transcript, long form

Verbatim (`AGENTS.md` pre-split, lines 751–841). `AGENTS.md` keeps the recipes that get used and the two traps; the field-by-field walk-through and the session-resumption checklist are here.

## Reading the transcript — `logo/*.jsonl`

The transcript is the raw export of the sessions that built this mark: one JSON object per
node, and most of the bytes are base64 PNG screenshots pasted into messages, so
`read_file`/`cat` on it will fill a whole context window and teach you nothing.
**The file gets re-exported and renamed between rounds, and it is the newest file in the
folder**: Round 6 found `logo_talk.jsonl` (413 objects / 3.4 MB), Round 9 found
`logo_chat.jsonl` (404 / 403 lines / 1.6 MB), and this round found `prev_logo.jsonl`
(421 objects / 420 lines / 2.0 MB). Older exports now live in `../private/`. **Never hard-code
the name** — every recipe below takes `$(ls -S logo/*.jsonl | head -1)`, the biggest transcript
in the folder, which *is* the current one. `wc -l` under-reports by one (no trailing newline)
and the first object is a session header with no `message` key, so `sum(1 for _)` and
`json.loads(...)["message"]` disagree — that is the file, not a bug.

Two passes that cost about 2 KB each instead:

```bash
cd logo
T=$(ls -S logo/*.jsonl | head -1)      # the newest/biggest transcript is the current one
# every message the owner sent, in order (the brief, in their words)
python3 - "$T" <<'EOF'
import json, re, sys
for line in open(sys.argv[1]):
    m = json.loads(line).get("message", {})
    if m.get("role") == "user":
        c = m.get("content")
        print("----", re.sub(r'data:image[^"]*', "[IMG]", str(c))[:800])
EOF

# the tail of the story: last ~12 nodes, whatever their type
tail -n 12 "$T" | python3 -c '
import json, sys
for l in sys.stdin:
    m = json.loads(l).get("message", {})
    print("===", m.get("role"), str(m.get("content"))[:200])'

# what a dead session was *about to* write: its unapplied tool-call arguments
tail -n 4 "$T" | python3 -c '
import json, sys
for l in sys.stdin:
    m = json.loads(l).get("message", {})
    for tc in m.get("toolCalls") or []:
        f = tc["function"]
        print("===", f["name"], "|", f["arguments"][:1500])'
```

### Resuming a session that died out of tokens (Round 9, and Round 6 before it)

Both times the work was recoverable, and the shape of the recovery is worth keeping because
the tail alone is misleading: the last node is usually an assistant message *thinking*, not a
record of what was asked.

1. **Find the brief**: the last *real* user message — `role == "user"` and *not*
   `isSynthetic` (the "Set working directory to…" lines are synthetic and are not the brief).
2. **Then read the tail's `reasoningContent`**, not just its `content`: that is where a dead
   session writes its diagnosis and its planned fix, and it is often further ahead than any
   file it managed to touch.
3. **Re-run everything it claimed.** Round 9's predecessor had ended with two failing checks
   and a half-written theory; one number in that theory (that the box was a rectangle whose
   height was 7.786 mm) was the thing to distrust, and distrusting it is what found gotcha
   23. A dead session's *question* is usually right and its *measurements* are usually stale.

```bash
# the briefs, newest last, with the node ids so you can walk forward from one
T=$(ls -S logo/*.jsonl | head -1)
python3 - "$T" <<'EOF'
import json, sys
for i, line in enumerate(open(sys.argv[1])):
    m = json.loads(line).get("message", {})
    if m.get("role") == "user" and not m.get("isSynthetic"):
        print(i, m.get("id"), "|", str(m.get("content"))[:120].replace(chr(10), " "))
EOF
```

Two traps in there, both hit while writing this file: the base64 lives in `extra[].base64Url`
on *user* messages (so `content` alone is cheap — truncating it to ~200 chars is enough), and
a regex containing `"` cannot go inside a `python3 -c` one-liner wrapped in `'…'`, because the
first `"` closes the Python string — the syntax error is in the doc, not in your data.

Fields worth knowing: `message.role` (`user` / `assistant` / `tool`), `message.content`
(reply text, or a tool result), `message.timestamp` (ms epoch). And the two that can rescue a
dead session: **`message.reasoningContent`** (what it was trying to do) and
**`message.toolCalls[].function.arguments`** — the arguments survive even when the call was
truncated and rejected, so an unapplied edit can be read straight back out. To find
something without reading a range:
`grep -o '"content":"[^"]\{0,240\}anchor[^"]\{0,240\}' "$T"`.

The transcript is **history, not evidence**: it contains measurements made against broken
code, and the numbers in it go stale within a refactor. Anything you lift out of it gets
re-run against `gen_logo.py`/`validate_logo.py` before it lands here — that is how Round 6
caught the four stale claims in gotcha 18.

---

## E — the long form of the sections Round 10 distilled

These were **not wrong** — they were long, with exactly one exception, flagged in F.4. `AGENTS.md` now carries the same rules in fewer words, so the paragraphs below are superseded in the only sense this archive cares about: get the rule from `AGENTS.md`, come here for the reasoning, the measurements in context and the wording that was argued over. Nothing was deleted from these sections; some of it was cut down, and one sentence that running the tool disproved is marked as such.


### F.1 — THE RULE, the Files table and the regenerate list, as they stood

*(`AGENTS.md` pre-split, lines 32–91; replaced by the same sections of `AGENTS.md`, re-worded but not weakened.)*

> ## THE RULE: the wordmark is `PTURE`, not `CAPTURE`
>
> The mark spells **CAPTURE** out of three parts, and only the third one is type:
>
> ```
>   C     <-  the junction of the hand-drawn K and W   (part of #kw, the monogram)
>   A     <-  the hand-drawn mouse pointer             (#a, laid out as a letter)
>   PTURE <-  the only typeset letters                 (#wordmark)
> ```
>
> So `WORD = "PTURE"` in `gen_logo.py`. Setting `WORD = "CAPTURE"` produces
> **“CACAPTURE”** — which is exactly what happened in the 2026-10-10 session that
> first typeset this logo, because from 2 metres the pointer reads as a blob and
> the C-in-the-junction is invisible to anyone who has not been told to look for it.
> It is not invisible: it is the whole idea. **Do not "complete" the word.**
>
> If a future change makes the C or the A stop reading (different monogram, smaller
> pointer, tighter spacing), the fix is to repair that part — not to add letters.
>
> Since 2026-10-10 the C is also a **colour**: the K's stem is green so that the bracket the
> junction forms is the only blue thing inside the monogram. Colour changed the *paint*
> and nothing else — the geometry, the fit and this rule are untouched.

---

## Files

| file | what it is |
|---|---|
| `kwcapture.svg` | the logo. 512×512, generated. **Edit the sketch or the knobs, never this file** |
| `kwcapture-sketch.svg` | the **original** hand-drawn source (Inkscape, A4): the first monogram + the mouse pointer. **Input. Never written to by any tool.** Keep it forever — the pointer (the A) still comes from here |
| `kwcapture-mark-sketch.svg` | a **second, redrawn monogram** (cleaner, geometric) plus a black helper box, drawn in Inkscape. **Input. Never written to.** Its `#kw` is *not* the same path as the original sketch's |
| `kwcapture-mark.svg` | generated **from the mark sketch**: the redrawn monogram + `APTURE` fitted into the box. **Not a bare monogram any more** |
| `kwcapture-mono.svg` | bare monogram only (still two-tone: green KW + the blue C), for favicons / ≤64 px where `APTURE` is mush. `--monogram`. **It has no `-mono-sketch.svg`**: it comes from `kwcapture-sketch.svg`, and the validator's fallback knows that |
| `gen_logo.py` | the generator: sketch + knobs → the SVGs (see the helper-box section and *The colour split*) |
| `validate_logo.py` | geometry check: ink bounds, centring, element clearances, **the A-vs-cap type check**, the **box check** (mark only), the **colour split check** (the only check that can see paint) and the **render check** — it rasterises the file with QtSvg and ImageMagick MSVG and fails if a real viewer would not show both colours. Takes one path, default `kwcapture.svg` — the mark must be named explicitly |
| `prev_logo.jsonl` | the transcript of these design sessions (2.0 MB). **It arrives under a different name every session** — `logo_talk.jsonl` in Round 6, `logo_chat.jsonl` in Round 9, `prev_logo.jsonl` now; older exports have been moved to `../private/`, which self-ignores. `ls logo/*.jsonl` before quoting a name. **Never read it whole** — see *Reading the transcript* |
| `render_agreement.py` | **diagnostic, not a gate**: per installed engine, compares the ink box it paints against the box the path data implies, per colour. Found the MSVG `rotate()` bug; exits 1 today on purpose — gotcha 27 |
| `__pycache__/` | appears because `validate_logo.py` imports `gen_logo` to reuse the box geometry. Gitignored; ignore it |

## Regenerating

```bash
python3 logo/gen_logo.py                    # -> logo/kwcapture.svg
python3 logo/gen_logo.py --mark             # -> logo/kwcapture-mark.svg   (helper box mode)
python3 logo/gen_logo.py --monogram         # -> logo/kwcapture-mono.svg
python3 logo/gen_logo.py --out /tmp/x.svg --no-c-split   # all-green CONTROL: "is the colour
                                            # what makes the C read?"  USE --out, see below
python3 logo/gen_logo.py --out /tmp/x.svg --classic    # the old look: gradient mono, black type
python3 logo/gen_logo.py --c-paint clip     # the historic clipped C: WRONG in Qt/Gwenview;
                                            # solid (default) and mask are the portable forms
python3 logo/gen_logo.py --out /tmp/x.svg --a-size 1.15   # experiment without touching the repo
python3 logo/gen_logo.py --mark --no-height-fill  # the pre-Round-9 word: uniform, ~half the
python3 logo/gen_logo.py --mark --max-stretch 1.35  # box height left empty; 1.35 is the mild
                                                   # fill, 0 the same as --no-height-fill
python3 logo/validate_logo.py                       # must print OK  (checks kwcapture.svg)
python3 logo/validate_logo.py logo/kwcapture-mark.svg  # must print OK (type + BOX check)
inkscape logo/kwcapture.svg -o /tmp/p.png -b white -w 512 # preview
```

### F.2 — the obsolete guard note: "nothing now enforces this; the habit is the guard"

*(`AGENTS.md` pre-split, lines 92–98; replaced by `AGENTS.md` §Regenerating: `gen_logo.py` now refuses.)*

**Every variant needs `--out`.** `--classic`, `--no-c-split` and `--c-paint` change the
*paint* but not the output path, so `gen_logo.py --classic` with no `--out` **overwrites the
shipped `kwcapture.svg` with the old look** and prints a happy `written:` line. This session
did exactly that while following the commands printed above, and only the render numbers in
this file caught it — the file stayed valid XML, `xmllint`-clean, and geometry-perfect, because
the variant differs from the shipped logo in paint alone. Recovery is `gen_logo.py` with no
flags. Nothing now enforces this; the habit is the guard.

**Round 10 note.** This is now **false**, and the file still said it: `gen_logo.py` compares every knob against argparse's own defaults and refuses to write a deviating paint variant onto a shipped path (verified 2026-10-11: exit 1, `kwcapture.svg` byte-identical). `--force` overrides. The habit is no longer the guard.

### F.3 — dependencies and the knob table, as they stood

*(`AGENTS.md` pre-split, lines 99–122; replaced by the knob table of `AGENTS.md`.)*

Needs `fontTools` (outline extraction) and `numpy` (validator only) — both present in
the system `python3` **and** in `.venv`. Paths are resolved from the script's own
directory, so it works from any cwd.

## The knobs, and what they cost

| knob | value | why this value |
|---|---|---|
| `WORD` | `PTURE` | see THE RULE |
| `FONT` | `Inter-ExtraBold.otf` | the drawn monogram is very heavy (stem/height ≈ 5.8/30.1 ≈ 0.19). Inter **Bold** looked thin next to it; Lato Bold and Noto Sans Bold were tried and are less neutral than the mark |
| `ANGLE` | `-38°` | measured off the sketch (drawn baseline ≈ -38.9°). The word deliberately rises shallower than the K's arm (~52°), which is what lets it tuck under the arm |
| `CAP` | `3.30 mm` | the drawn letters were ~3.4 mm cap |
| `TRACK` | `0.10 em` | the sketch was widely set; tighter looks cramped against the monogram |
| `A_SIZE` | `1.00 × cap` | **the A must be exactly as tall as the P.** There is exactly one big letter in this mark — the C in the K+W junction — and `APTURE` must read as one evenly-set word. 1.30× (echoing the sketch, where the arrow dwarfed the letters) made it read "big C, medium A, small PTURE". Height is measured **perpendicular to the −38° baseline**; that is the only sense in which rotated text has a height |
| `A_WIDTH` | `1.00 ×` a real capital A | **the A must also be as WIDE as an A.** In Inter ExtraBold at this cap height a capital A is 3.282 mm of ink (0.995 × cap); the mouse pointer scaled uniformly to cap height was 2.42 mm (0.71 of that) — a skinny, condensed A next to fat letters. So `#a` is stretched **along the baseline only**, by 1.36×, to hit 3.282 mm. Height is untouched. Your sketch's arrow already had the right *width* (3.22 mm) and too much *height* — that is why uniform scaling felt wrong |
| `A_GAP` | `0.70 mm` | the A→P gap, along the baseline — a *type* gap, not a decorative one. 0.90 mm read as a word break once the A was shrunk to cap height |
| `ANCHOR` | `(73.4, 112.6)` mm | baseline start of `PTURE`, in the sketch's mm space, where the drawn P started |
| `ALIGN_TOP` | `True` | levels the cap-top of the word with the top of the K, so the lockup has one flat top edge |
| `CANVAS`/`PAD` | `512` / `44 px` | square artboard, icon-safe. The artwork is wider than tall (35.6 × 30.1 mm), so vertical padding ends up larger (76 px) — that is correct, not a bug |
| `C_PAINT` | `solid` | how the blue C is cut out: `solid` \| `mask` \| `clip`. Chosen by the **renderer matrix**, not by taste: `clip` (shipped until 2026-10-10) renders **100% blue in Qt** — Gwenview, Dolphin thumbnails, `QIcon` — because QtSvg ignores `clip-path`; `mask` fixes Qt but MSVG hides the C behind a mask it doesn't parse; `solid` asks nothing of the renderer and is correct everywhere. `validate_logo.py` re-runs the matrix on every build. See *Which cut-out* |
| `MAX_STRETCH` | `2.00 ×` cap | ceiling on the height fill. A **taste guard, not geometry**: the shipped box wants 1.753 and is not stopped by it. It exists because the box is the owner's drawing and next week it may be twice as tall, and Inter at ×3 is a cage of vertical strokes, not a word. 0 = `--no-height-fill`. See *The height fill* |
| `GREEN` | `#00ac4e` | the K's stem and the W. It is the old gradient's end stop, so the palette did not change, only its job: colour now carries meaning (monogram vs word) |
| `BLUE` | `#0000ff` | the C, the pointer-A and `PTURE`. Chosen against its **neighbour**, not the page: contrast vs `#00ac4e` is 2.87 (a lighter `#3b82f6` is only 1.23 — the C would dissolve into the W). vs white 8.59; vs GitHub dark `#0d1117` 2.20 (black was 1.11, so dark mode got less bad, still open) |

### F.4 — the helper box, in full

*(`AGENTS.md` pre-split, lines 124–203; replaced by the helper-box section of `AGENTS.md`.)*

## The helper box — `--mark` mode

Draw a **four-corner box** (a parallelogram; give it id `fit-box` to be explicit) over the
area where `APTURE` should go in `kwcapture-mark-sketch.svg`, then run
`python3 logo/gen_logo.py --mark`. The box says three things and is then **thrown away**:

| read off the box | used for |
|---|---|
| its **lower long edge, read left→right** | the baseline slope — yours is **−43.12°** |
| its **length** | how much type fits along the baseline |
| its **height** | the ceiling on cap height |

The fit is an **optimisation**, because "as large as possible but still fit" is one: all
nine placements (across `center|base|top` × along `center|start|end`) are tried, and for
each the cap height is **bisected** up to the largest value that both stays inside the box
and keeps `--min-clear` (default **0.50 mm**) of ink between the word and the monogram.
The biggest winner wins: today that is **centred across, centred along, cap 4.310 mm =
100% of the box's length** — and that is a **tie**, not a ranking. With the anchor fixed
(gotcha 15) all three across-placements reach the same 4.310 mm, because the word fills
the box's length exactly; the tie breaks on list order (`places` starts at
`("center","center")`), which is also the nicest result. Measured, all at cap 4.310 mm:

| `--align` | kw↔A clearance | note |
|---|---|---|
| `top` | 17.36 px = 1.46 mm | what the buggy optimiser *believed* was the only 100% option |
| `center` | 9.45 px = 0.79 mm | **shipped** |
| `base` | 9.70 px = 0.81 mm | |

So at the shipped `--min-clear 0.50`, **the box limits the type, not the monogram**. And
`--along` is a no-op while the word is exactly 100% of the box length — `start`, `center`
and `end` resolve to the same anchor; it only starts to mean something once the word is
smaller than the box (`--cap`, a longer word, or `--inset`).

> **Corrected in Round 9.** This section used to say "raise the floor and clearance
discriminates again: `--min-clear 1.0` makes `top` the winner". It did — and `top` then put
the word **1.59 px outside the box**, because `fits()` tested the monogram and only the
*nominal* box, so buying clearance above the cap line meant spending it through the top
edge. Both halves of "inside the box **and** clear of the monogram" are now tested, against
the quad (see *The box is four mouse clicks*), and a placement that spills is simply not a
placement. Measured after the fix, `--no-height-fill`:
>
> | `--min-clear` | chosen | cap | closest ink |
> |---|---|---|---|
> | 0.5 (default) | centred / centred | 4.310 mm | −0.08 px (the A's tip on a leaning edge) |
> | 0.9 | centred / centred | 4.273 mm | +1.20 px (inside) |
> | 1.2 | centred / centred | 4.169 mm | +4.76 px |
> | 1.5 | centred / centred | 4.065 mm | +8.41 px |
>
> Raising the floor now costs **type size**, not containment — which is what a guard rail is
> for. If you re-measure the old table: `top` is not rejected by the monogram at all, it is
> rejected by the box.

Round 4 recorded the opposite of all of the above (centred 72%, top 100%, "the geometry
forces the top edge"). That was the anchor bug talking — see gotcha 18 for the rule.

**Anchor semantics — read this before touching `layout()`:** `place_A()` parks the pointer
*behind* the anchor it is given (trailing edge at `-gap`). So the anchor is **not** the left
edge of the word; the A's ink starts `a_w + gap` before it. The whole-word left edge is
`anchor - (a_w + gap)`, and both the pointer and PTURE must be handed the *same* shifted
anchor. Get it wrong one way and the A hangs outside the box while PTURE falls short; get
it wrong the other way and the word splits in half.

**Why the monogram has a veto at all:** the box's lower-left corner is drawn *inside* the
W's stroke. Filling the box blindly puts the A on top of the W — that file was emitted once,
`validate_logo.py` called it a `COLLISION`, and the fitter refuses to do it again. Note the
tense: with the anchor fixed the veto **is not being used** (the shipped fit keeps 0.79 mm,
above the 0.50 mm floor, and the box is what caps the type). The veto is what makes it safe
to move the box, lengthen the word or raise `--min-clear` — it is a guard rail, not today's
limiting factor.

After fitting, the whole lockup is **re-centred on the artboard** (same scale, new
translate): the box was drawn wherever the mouse happened to be and its right end runs off
the canvas. `--no-recenter` keeps the sketched position.

**"Inside the box" is verified, not assumed.** The box is not in the output, so nothing in
the output could prove the word was inside it — and when it wasn't, nothing said so.
`validate_logo.py` now has a **box check**: it re-reads the box from
`<name>-sketch.svg`, undoes the re-centring shift, and fails if any ink of `#a` or
`#wordmark` is more than 1 px outside it. If you rename a sketch, keep the
`-sketch.svg` suffix or the check silently skips (it prints a line either way).

**One claim in this range is false, not merely long** (lines 202–203): *"if you rename a sketch, keep the `-sketch.svg` suffix or the check silently skips (it prints a line either way)"*. It prints **nothing** when the sketch is absent or has no box — verified 2026-10-11 by validating a copy in `/tmp`, which produced no box-check line at all. A *skipped* check wearing the costume of a *passing* one: it cost the round a false conclusion about a sabotage. Gotcha 30.

### F.5 — the height fill, in full

*(`AGENTS.md` pre-split, lines 205–257; replaced by the height-fill section of `AGENTS.md`.)*

## The height fill — filling the box's *height* (`#type`)

Fitting by length leaves the box's height barely used: cap 4.310 mm in a 7.786 mm box is
**55.4%**. The owner asked (2026-10-10) for the type "as tall as possible but still fit
inside the black box", and the only way to fill a box whose length is already full is to
stretch it. So:

* **Across the baseline only, never along it.** Letter widths, the A's width, tracking and
  every along-baseline distance stay exactly as fitted; only the height grows. A stretch
  with an along component moves the tracking and is refused by the validator.
* **One `<g id="type">` over the pointer-A *and* PTURE.** Two transforms would let them drift
  into two sizes of type. The monogram is never inside it: `#kw` is the hand drawing, and
  `#kw` inside `#type` is a validator failure ("colour it, do not resize it").
* **The map seats then stretches:** `t ↦ a + s·t` in the box's frame — the ink's lowest point
  on the box's base line (`+--inset`), then scale by `s` across it. Emitted as
  `translate rotate scale(1 s) rotate translate`, which is the same map, and measured
  independently by the validator off that transform.
* **It is one blend, `lam ∈ [0,1]`, on the *displacement***: `lam = 0` is the identity —
  `--no-height-fill` ships the fitted type exactly where the centring put it (verified
  byte-identical to the pre-fill mark) — and `lam = 1` is the full fill. The monogram's veto
  bisects on `lam`, so a half-stretch is also a half-seating. An earlier version applied the
  seating unconditionally, and `--no-height-fill` came out 0.79 mm off-centre.

**Shipped: `s = 1.753`.** Ink band 4.365 mm → 7.652 mm = **98.3%** of the box height, ink
clear of the monogram by 0.810 mm (it was 0.792 mm — the seating moves the word *down*, away
from the W).

### The box is four mouse clicks, not a rectangle — why 1.753 and not 1.784

The obvious number is *fill the box's height*: `7.786 / 4.365 = 1.784`. It is wrong, by
**1.6 px**, and `validate_logo.py`'s box check was reporting exactly that failure. The
reason is in the sketch: `#path4` is four clicks, and

| its edge | measured |
|---|---|
| top vs base | **0.62° off parallel** — the headroom over the base falls **7.920 → 7.651 mm** along the length |
| left edge | leans inward 0.18° (it clips the A's tip by 0.06 px: the shipped −0.08 px margin) |
| right edge | leans inward 1.65° |

`box_frame()`'s `(length, height)` is the box's **average**, and a type fitted to the average
of a non-rectangle hangs outside it — at the far end, where the word happens to be tallest.
So both fits go through `halfplanes()`, the four inward half-planes of the drawn quad:

* `fits()` (the cap/placement optimiser) refuses any layout whose **ink** pokes out past
  `FIT_TOL` = 0.25 px;
* `tallest_stretch()` solves the same half-planes for `s` directly — the map is linear in
  `s`, so the tight edge is arithmetic, not a search: `s·(n_t·T) ≥ c − n_u·u − n_t·inset`.

`FIT_TOL`, not the validator's 1 px: the box's own lean makes ~0.06 px of spill unavoidable
(so 0 would reject every placement), while 1 px of spill is a *choice* the optimiser must not
be allowed to make. With 1 px the `--min-clear 0.9` winner was `base across, end along` 0.66
px outside; with 0.25 px it is centred and inside.

### F.6 — the colour split, in full

*(`AGENTS.md` pre-split, lines 272–359; replaced by the colour-split section of `AGENTS.md`.)*

## The colour split — KW green, Capture blue

The K's **stem is the stroke that competes with the C**: the C is the bracket the junction
forms (arm + leg), and a stem running through it is what made it read as part of a K. So the
stem is green, that bracket is blue, and `APTURE` shares the blue — `KW` green, `Capture`
blue.

* **It is paint, not geometry.** `#kw` is the monogram in `GREEN`; `#kw-c` is the blue C,
  `--c-paint` deciding how the blue is cut to it (see *Which cut-out* below). Nothing moved:
  every number in *Expected numbers* is identical to the single-colour mark's.

### Which cut-out: `--c-paint solid|mask|clip` — measured, not opinion

Three ways to paint the same C, and **renderers disagree about all of them**. Measured on
this machine 2026-10-10, monogram ink as % blue (the truth is 39.1–39.8%):

| renderer | `solid` | `mask` | `clip` |
|---|---|---|---|
| Inkscape / librsvg | 39.5% ✅ | 39.1% ✅ | 39.1% ✅ |
| **QtSvg** — Gwenview, Dolphin's thumbnails, `QIcon`, KDE's image plugin | 39.4% ✅ | 39.1% ✅ | **100% blue ❌** |
| **ImageMagick internal MSVG** | 39.8% ✅ | **0% blue ❌** | 39.6% ✅ |

* **`clip` was shipped for a day and is wrong in Qt.** QtSvg **ignores `clip-path`** — not a
  quirk of our file: Qt 6.10.2 drops even a canonical `<circle>` clip. So the blue copy of
  the *whole* monogram painted straight over the green one, and the mark looked **100% blue
  in Gwenview and in every Dolphin thumbnail** while Inkscape, browsers and the validator all
  said it was fine. The owner found it by looking at a folder.
* **`mask` is not the safe answer either.** It fixes Qt, and `#kw-c` keeps the
  byte-identical `d` which is nice for the invariant — but MSVG treats a mask it does not
  understand as *hide everything* and the C vanished.
* **`solid` (the default): `#kw-c` carries the C ring's own path data.** No `defs`, no
  cut-out feature, nothing for a renderer to ignore. It is legal **only** because the ring
  lies **100.0% inside the monogram's ink** — an assertion the validator already made for a
  different reason — so `monogram ∩ ring == ring` and the clip was always a set-theoretic
  no-op that only ever did edge antialiasing. Inkscape diff between `clip` and `solid`:
  1160 px of 262144, **4 px at 15% fuzz**. And it is still *derived by vertex index*, never
  hand-drawn, so the "never a second drawing" rule survives in the place that mattered:
  the polygon must equal `C_RING` recomputed from the sketch, or the build fails.

`validate_logo.py` now **renders the file** in every engine the machine has and fails if the
two-tone split is not actually on screen — the two weak renderers fail in opposite
directions, so a file has to satisfy both to pass. See gotcha 25.
* **The letter rings are the owner's numbering of the outline, not my reading of it.** Both
  monograms — the original and the redrawn mark — are 19-vertex closed outlines with the
  **same topology, index for index**, and the three letters are three rings over those
  indices (`K_RING`, `W_RING`, `C_RING` in `gen_logo.py`):

  ```
    K = 0  1  2  3  4           13 14 15 16 17 18
    W =    3  4  5  6  7  8  9 10 11 12 13 14
    C =    3  4  5  6           12 13 14 15 16 17      <- the blue one
  ```

  They **overlap**, which is what a ligature is: 3–4 is the K's leg and the W's first stroke
  at once, and the C borrows from both. The C is **three strokes, like `[`** — not two like
  `<`:

  | stroke | vertices | what it is |
  |---|---|---|
  | top arm | 14→15→16→17 | the K's arm |
  | spine | 17→3 | the stem's right edge — the C's back, zero width; the stem stays green |
  | bottom arm | 3→4→5→6 and 12→13 | the leg, the shared V, **and the first W rise all the way to the peak tip at 12** |

  So the ring is the drawing's **own edges plus exactly two chords**: `6→12` (across the
  peak — the C keeps the tip, the descending stroke stays green) and `17→3` (across the
  stem). No padding, no invented lines, which is why the cut is exact — and why `frac_in`
  reports **100.0% of the clip polygon lying on ink**. My first attempt covered 52–53%; the
  missing half was empty space I had invented (gotcha 22).
* `len(verts) != 19` makes the generator refuse rather than guess: re-sketching means
  re-checking the indices, the same policy as the `path1`/`path10` id binding in
  *Re-sketching*.
* **The C polygon is in the sketch's mm space, whichever `--c-paint` you use**, so it
  resolves inside the `#logo` transform exactly like the gradient coordinates do. In canvas
  px it would be correct at one scale and wrong at every other.
* **`validate_logo.py` proves it**, because no geometry check can see paint. Five
  assertions, and the last two are the ones that catch a wrong *idea* rather than drift:
  with `clip`/`mask` the overlay's `d` must equal the base's (the split is never a redraw);
  the emitted C polygon must equal `C_RING` recomputed from the sketch; **≥95% of its area
  must lie on the monogram's ink** (a ring that wanders through the counters is not a
  letter); and **the stem's area must be 0.00% inside it**. Plus per-letter sample points,
  plus the render check above. Output:

  ```
  colour split (vs kwcapture-mark-sketch.svg): solid 10 pts == recomputed, 100.0% on ink,
                                             stem area 0.00% blue
                samples: stem 3/3 green, C 6/6 blue, W 3/3 green
  ```

### F.7 — rules for the emitted SVG, in full

*(`AGENTS.md` pre-split, lines 369–416; replaced by the same section of `AGENTS.md`.)*

## Rules for the emitted SVG

* **Outlines, never `<text>`.** A `<text>` element means the logo depends on a font
  being installed; it renders as garbage on a random machine reading the README.
* **Keep the `#kw` path data verbatim from the sketch.** Its wobble *is* the design —
  the hand-drawn K/W junction is what doubles as the C. Straightening it can kill the C.
* **The C is never a second *drawing*.** Default `--c-paint solid`: `#kw-c` carries the C
  ring's own path data, which must equal `C_RING` **recomputed from the sketch's vertices** —
  the validator fails the build otherwise, and that is the guarantee the old wording was
  really protecting. (`--c-paint clip|mask` restore the byte-identical-`d` form, which that
  rule used to state literally; both are wrong in at least one renderer — see *Which
  cut-out*.) If the C needs to change **shape**, that happens in the sketch or in the ring's
  derivation, never by editing an outline in the output.
* **No `clip-path`, and no reliance on `mask`, in shipped artwork.** Renderers ignore them
  silently and in opposite directions (QtSvg drops `clip-path`; ImageMagick's MSVG hides
  masks). A logo is what viewers paint, not what the DOM says — `validate_logo.py` renders
  the file to enforce this.
* **The A is type, not ornament.** It must sit on the word baseline with its tip on the cap
  line and be as wide as a capital A — all four are asserted. `validate_logo.py` fails the
  build if the A's height is >2 px off cap, if it floats off the baseline, if it pokes past
  the cap line, or if its width leaves 0.85–1.15× cap. (Inter's `U` overshoots by ~0.5 px,
  which is why the height tolerance is 2 px and not 0.) A pointer that is merely scaled is
  a cursor; a pointer with the right height *and* width reads as the first letter of the word.
* **`#a` is one `matrix(...)`, and it is deliberately anisotropic**: uniform scale to cap
  height, plus a stretch *along the baseline* to the width of a real capital A
  (`world→baseline frame`, stretch, `frame→world`). Never stretch perpendicular to the
  baseline and never shear it — the tip axis is already within ~6° of perpendicular, which
  is *why* it reads as an upright A. `--a-upright` snaps it exactly perpendicular; it then
  reads as an arrow, not a letter. Measured; don't re-try.
* **`#type` is the height fill and it is deliberately anisotropic**: `scale(1, 1.753)` inside
  a `rotate` pair, so it stretches across the baseline and nothing else, over `#a` +
  `#wordmark` only. Four things are asserted about it (see *The height fill*): the
  along-baseline factor is 1.0000, it covers both letters, it does not cover `#kw`, and every
  rule of the type check is measured **unstretched** — a stretched cap is not a bigger letter,
  and a correct 0.98 × cap A reports as 0.55 × cap if the stretch is left in the ruler.
* `#kw-grad` (emitted only by `--classic`; the default mark is flat two-tone) is
  `gradientUnits="userSpaceOnUse"` with coordinates in the sketch's mm space. That is
  correct: userSpaceOnUse resolves inside the ancestor `#logo` transform, so the gradient
  scales with the art. The numbers looking "wrong for a 512 canvas" is not a bug — do not
  rescale them. **The C polygon obeys the same rule**: whether it rides in a `<mask>`
  (`--c-paint mask`) or is `#kw-c`'s own `d` (`solid`, the default), its coordinates are mm,
  on purpose, for the same reason.
* Transparent background. No `sodipodi:`/`inkscape:` editor junk in the output.
* **`--` is illegal inside an XML comment.** This bit the generator once
  (`xmllint`: *"not well-formed (invalid token)"* pointing at a comment line).
* Units: the sketch is in **millimetres** (`width="210mm"` + `viewBox="0 0 210 297"`
  means 1 user unit = 1 mm, *not* 1 px). `gen_logo.py` emits px on a 512 artboard and
  keeps the mm coordinates inside the single `#logo` transform.

### F.8 — expected numbers, as recorded before the split

*(`AGENTS.md` pre-split, lines 669–717; replaced by the expected-numbers section of `AGENTS.md`.)*

## Expected numbers (so drift is obvious)

```
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
               stem area 0.00% blue, samples stem 3/3 green | C 6/6 blue | W 3/3 green
render       : QtSvg 44.3% blue | MSVG 45.4% blue  (both colours present in both)
   fills     : #kw #00ac4e, #kw-c + #a + #wordmark #0000ff
```

Mark (`kwcapture-mark.svg`, from `--mark`):

```
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
                ignoring a feature, see gotcha 25, not that the logo is wrong)
sweeps       : --inset 0.25 / 0.5 / 1.0 -> x1.731 / x1.708 / x1.660 (all inside)
               --max-stretch 1.35 -> 75.7% of the height; --min-clear >= 0.9 -> smaller cap,
               still centred, still inside (see the table in the helper-box section)
               --no-height-fill -> byte-identical to the pre-fill mark (lam = 0 is identity)
```

### F.9 — the face reference, the exit conditions and re-sketching

*(`AGENTS.md` pre-split, lines 729–749; replaced by `AGENTS.md`.)*

Face reference, ink width at cap height 3.3 mm, for argument: **A 3.282**, T 2.78,
U 2.78, R 2.67, P 2.55, E 2.29 mm. The A is the widest letter in the word — shrinking the
pointer to fit was never going to look right.

`validate_logo.py` prints these and exits non-zero on: a collision (<1.5 px), ink outside
the artboard, off-centre artwork, or the A failing the type check. Also run `xmllint --noout`, and render the ladder
512/256/128/64/32: the wordmark stops being readable around 128 px, which is what
`kwcapture-mark.svg` is for.

## Re-sketching

If you replace `kwcapture-sketch.svg`, `gen_logo.py` reads it **by Inkscape path id**:
`path1` (or `kw`, the id the redrawn mark sketch uses) = the K+W monogram, `path10` (or
`cursor`/`a`) = the pointer. Keep those ids or extend `pick()` in `build()`; a sketch that
has neither now says which ids it looked for and which it found, instead of throwing
`KeyError: 'path1'` from three frames deep. Everything else in the sketch is ignored on
purpose — the letters come from the font. Note that `--monogram` needs no pointer, so
`--monogram --sketch logo/kwcapture-mark-sketch.svg` is how you get the **mark's** monogram
as a favicon (the two sketches' monograms differ; that is a design choice still open below,
not a crash any more).

### F.10 — the whole *Still open* list as it stood before Round 10

*(`AGENTS.md` pre-split, lines 843–936; replaced by *Still open* in `AGENTS.md`, updated item by item.)*

## Still open

* **Housekeeping: distil Round 9b+9c and archive, before the next round starts.** This file is
  80.8 KB, ~+14,154 bytes against the 71,855 it was when this round started, and grew ~13 KB across the last two rounds; both rounds' *narrative* is already in
  the knob table, gotchas 25–27, *Which cut-out* and *The height fill*, so the session-log
  entries for them are now the compressible part. The precedent is Round 6's archive-verbatim
  pass (root `AGENTS.old.md`, 77 KB → 54 KB, nothing deleted). Do it as its own change so a
  later diff can prove nothing was lost.


* **MSVG paints the type 26–67 px out of place (gotcha 27) — fix it or accept it? Owner's
  call.** (a) Accept: KDE, Inkscape, browsers and any delegated ImageMagick are correct; only
  IM's internal MSVG coder is wrong, and `librsvg2-bin` fixes IM. (b) Emit a *second*,
  transform-free artefact (say `kwcapture-flat.svg`) for pipelines that use bare ImageMagick,
  leaving the transform-carrying files as the source of truth. (c) Bake transforms into every
  file — makes MSVG agree, spends the mm-space definition of the C polygon, the `#type`
  transform `band_check` measures from, and the same-path-data invariant. **(b) is the
  recommendation**: it buys the compatibility without spending an invariant, exactly as
  `--c-paint solid` did. `python3 logo/render_agreement.py` is the instrument; it exits 1
  until this is decided, so the finding cannot be quietly forgotten.

* **The mystery flake: cause found (gotcha 28), fix measured, but NOT confirmed to be the
  same bug.** Two sessions of `TypeError: '<=' not supported between instances of 'float' and
  'list'` (on the mark) and `IndexError: list index out of range` (on `--mark
  --no-height-fill`) were never reproduced — ~570 validator runs, every artefact and mode,
  serial, 16-deep parallel, 40 `PYTHONHASHSEED` values, both command shapes replayed — and no
  reachable `float <= list` exists in `validate_logo.py`. Later **the same session** caught
  the generator crashing ~2% of `--mark` builds with four *different* impossible TypeErrors
  from the shared fontTools glyphset, and fixed it (0/120 builds). That is almost certainly
  the same defect: same shape (operands the code cannot hold), same context, same
  unreproducibility. What is **not** proven is that it produced the two messages seen in the
  validator, which never touches fonts — the residual doubt is why this item stays open.
  Settled the moment a `CRASH in <check>` line appears (gotcha 26's guard names it) or once
  ~500 more validator runs pass clean. Meanwhile: never pipe the validator through `tail -1`
  while chasing a crash; it destroys the only evidence.

* **Does the redrawn mark monogram still read as the C?** The whole word depends on that
  junction, and the redrawn one is geometric where the original's soft corner was doing the
  work. My eyeball read at 512 px (white background, both files rendered this session):
  `kwcapture.svg` gives a soft notch at the K↔W junction that can be read as a C **if you
  are looking for it**; the redrawn `#kw` in `kwcapture-mark.svg` is a hard symmetric
  crossing with no bowl at all, and what I read there is "**KW**" + a cursor + "**APTURE**"
  — no C. `(unverified: one model's read, and being told to look for a C biases you)` So the
  mark's "CAPTURE" may really be "K + W + APTURE".
  **Status after Round 8:** with the owner's rings the blue is a three-stroke bracket and it
  does read as a C at 512 px — but "it reads to me" is the weakest evidence in this file, and
  twice in one day my own read of this shape has been wrong (the vertex split, then the
  verdict on it). So the open item is the **stranger test**: render at 512, show someone who
  has never seen the sketch, ask *what does it say*, and write the answer here. If the answer
  is not CAPTURE, two follow-ups, in order: `--no-c-split` (is the green stem splitting the
  KW into `| <` + `W`?), then a **sketch** change — colour cannot curve a stroke, so a curved
  C means redrawing the junction, and THE RULE still says repair the junction rather than add
  letters.
* The mark's word **touches the near end of the box** — the A sits on the box's edge, which
  is what "as large as possible" bought. Want breathing room inside the band instead? That
  is `--inset 0.5` (mm), and it costs type size by definition (`--inset 0.5` also takes the
  height fill down from ×1.753 to ×1.708). `--align` is no longer free, and never was
  safely: `top` buys clearance by spilling over the box's top edge, so it is now rejected
  (gotcha 24) and raising `--min-clear` costs cap height instead. See the table in the
  helper-box section.
* **Is `×1.753` the right amount of stretch?** The owner asked for "as tall as possible", and
  that is what shipped — but it is a taste call made on a number, not an eye. At ×1.753 the
  type is visibly condensed (the rendered A is 0.55 as wide as it is tall) and the pointer
  reads **more like a cursor than like the letter A**, which is the one thing the A rules
  exist to prevent. Three positions on the same box: `--max-stretch 1.35` (75.7% of the
  height, the letters barely notice it), `1.5`, and the shipped full fill. The owner should
  pick from the renders, not from these words. Fold into the **stranger test** above: ask
  what the mark says *and* whether the third glyph is a letter or a mouse.
* `--monogram` builds from the **original** sketch, so `kwcapture-mono.svg` (on disk now,
  and two-tone) and `kwcapture-mark.svg` use *different* monograms — the difference is more
  visible now that both are green+blue. Pick one: `--monogram --sketch
  logo/kwcapture-mark-sketch.svg` gives the geometric one (verified working; it needs no
  pointer, which the mark sketch does not have). Whatever is picked, the favicon and the
  README header should come from the *same* monogram, or the identity says two things.

* The type is `#0000ff` on transparent: on a GitHub-dark `#0d1117` background that is
  **2.20:1**, which fails — better than the `#000000` it replaced (1.11:1, invisible), worse
  than usable. A dark-mode variant is now two recolours, not one (the blue and the green are
  both mid-tone), and `--blue`/`--green` make it a one-line job: e.g. `--blue '#4d8dff'
  --green '#3ddc84'` for dark surfaces — but check the C against its own green again if you
  do (that pair is 2.87:1 today, and lighter blues collapse toward 1.2).
* Nothing references the logo yet: README has no header image, no favicon, no
  `pyproject`/docs icon, and `logo/` is still untracked in git.
  **Resolved 2026-10-10 (Round 9c):** the transcript hazard is closed — `.gitignore` now has
  `logo/*.jsonl`, verified with `git check-ignore -v logo/prev_logo.jsonl` and with
  `git add -A --dry-run`, which now stages only the three SVGs, the two sketches, the two
  scripts and this file. (The rule is name-agnostic on purpose: a transcript lands here every
  session under a *different* name, and the root rule `chat_his*.jsonl` matched exactly one of
  them — see the 2026-10-06 incident in the root `AGENTS.md`.) Committing `logo/` is still the
  owner's call, and `kwcapture-mono.svg` should be regenerated if favicons are to reference it.
* No PNG/ICO exports are committed; `inkscape logo/kwcapture.svg -o k.png -w N` (or the
  `--monogram` file for ≤64 px) is the way to make them.
* Consider a horizontal lockup (monogram left, `APTURE` baseline rather than diagonal)
  for nav bars — the current diagonal is the mark's identity, so this is a separate asset.

**Round 10 notes on that list.** The first bullet (lines 845–850, *"Housekeeping: distil Round 9b+9c and archive, before the next round starts"*) is **closed by this file**. The MSVG item, the stranger test, the stretch taste call, the two-monograms item and the dark-mode item all stay open in `AGENTS.md`, with today's re-measurements. The *"mystery flake"* bullet is no longer about an unreproducible bug: both of its messages came back on 2026-10-11 in a path that never touches fonts (gotcha 29 in `AGENTS.md`), so the fontTools theory is demoted from *cause* to *a real bug of the same shape*.

---

## F — what Round 10 added, and where it went

Not an archive of anything — the record of the day of the split, kept here so `AGENTS.md`
stays a working set rather than a diary.

* **Re-verified end to end.** `gen_logo.py`, `--mark`, `--monogram` regenerate the three SVGs
  byte-identically against the files on disk (`cmp`, 3/3); `xmllint --noout` clean on all five
  SVGs; `validate_logo.py` OK on the mark and the mono; `render_agreement.py` exits 1 exactly
  as documented — MSVG off by 26 px on `kwcapture.svg`, 67 px on the mark, correct on the mono.
  Gotcha 27 survives contact with reality.
* **Gotcha 29, new: the flake is alive, and it is not fontTools.** The historic
  `IndexError: list index out of range` and `TypeError: '<=' not supported between instances
  of 'float' and 'list'` were both reproduced on 2026-10-11, in `validate_logo.py`'s
  `box_check` → `gen_logo.find_box` → `convex_hull` — a path that never touches fonts — and
  in a 70-line pure-Python extract of those two functions with **no numpy and no fontTools
  imported**, where the right-hand operand of `<=` is a locally computed float and cannot be
  a list. One such run did not raise a Python error at all but a CPython one:
  `Fatal Python error: _PyEval_EvalFrameDefault: Executing a cache.` — the interpreter
  reporting that it tried to execute an inline-cache slot as an instruction, which no amount
  of correct Python can cause. Rates measured here: 2/5, then 0/12, then 2/40 validator runs;
  2/7 and 1/8 for the extract; bursty, not steady. This is the strongest evidence yet that
  the `float <= list` / `IndexError` pair cost the Round 9b and Round 9c sessions was
  **not** in the logo code at all, and gotcha 28's glyphset fix — real, measured, 0/120 —
  was a different bug of the same shape. Machine-level suspicion, unproven: this desktop has
  `LD_PRELOAD=libgtk-nocsd.so.0` in every process and non-ECC RAM (`EDAC ie31200: No ECC
  support`); neither is demonstrated to be the cause, and the finding that matters is the
  practical one in `AGENTS.md`: **an impossible error in this folder is evidence about the
  machine until a re-run says otherwise, so re-run before you believe, and never believe a
  single run of the validator either way.**
* **Three doc-vs-code mismatches found by running the documented commands** (all recorded in
  `AGENTS.md`, none fixed in code, because this round is the documentation):
  1. *"Nothing now enforces this; the habit is the guard"* — false. `gen_logo.py` refuses a
     paint variant on a default output path and says what to do instead (verified: exit 1,
     `kwcapture.svg` untouched).
  2. `--c-paint`'s own `--help` text still says `mask (default)` and claims mask and solid
     "render identically everywhere". The default is `solid`, and MSVG paints no C at all
     through a mask. The help text contradicts gotcha 25 in the file it documents.
  3. The documented `--sketch logo/kwcapture-mark-sketch.svg` is repo-root-relative and
     raises a bare `FileNotFoundError` from `xml.etree` when run from inside `logo/`. Only
     the *default* paths are script-relative; `--sketch`/`--out` are literal paths.
* **New files:** `LICENSE.md` (artwork CC BY 4.0, tooling MIT), `README.md` (the directory
  and the three programs, with renders), `AGENTS.old.md` (this file), `preview/` (generated
  PNGs plus `build.sh`/`anatomy.py`, the commands that make them).

---

## G — Round 10's session-log narrative, verbatim

Moved here 2026-10-11 (Round 11) by the size rule in : one round's narrative per
file, the archive keeps the rest. Nothing edited — this is the text as it stood at the bottom of
the working set, including its own claims, which Round 11 re-verified rather than trusted.

**Round 10 — 2026-10-11, the documentation round.** Split this file (86 → 34 KB, narrative
verbatim to `AGENTS.old.md`), wrote `README.md` (manual for the three programs, with renders)
and `LICENSE.md` (artwork CC BY 4.0, tooling MIT, Inter OFL-1.1 referenced, transcripts
licensed by nobody), and added `preview/` with a `build.sh` that regenerates every image.
Everything claimed above was re-run first: the three artefacts regenerate byte-identically,
`xmllint` is clean, `render_agreement.py` still exits 1 with the same two numbers, the knob
sweeps (`--inset`, `--min-clear`, `--max-stretch`) reproduce their recorded numbers exactly, and
the `--out`/`--force` guard refuses a variant as documented. **Four** doc-vs-code mismatches came
out of running the documented commands — the obsolete "nothing enforces this" note, the lying
`--c-paint` help text, the cwd-sensitive `--sketch` path, and the box check "printing a line
either way" when in fact it prints nothing at all — and all four are recorded above rather than
quietly patched, because this round's job was the truth of the docs, not the code.

Two findings, one of them uncomfortable. **Gotcha 29**: the flake that cost Rounds 9b and 9c
their last messages reproduced here — in a code path that never touches fonts, in a 70-line
pure-Python extract with no third-party imports, in three different message shapes across two
checks, and once as a CPython `Executing a cache` abort. Suspicion moves off our code and onto
the machine, and the working rule is that in this folder **an impossible error is a re-run, not a
finding**. **Gotcha 30**: while proving that a sabotage is caught, my first sabotage was a
silent no-op (`sed` BRE escaping) and the validator printed `OK` at a file I believed broken —
the exact failure gotcha 24 documents, met a second time one day later — and the check I thought
was failing turned out to be **skipping silently**, keyed by filename. `assert changed` is not
pedantry; it is the only reason the first attempt was noticed at all.

---

## H — Round 11's session-log narrative, verbatim

Moved here 2026-10-11 (Round 12) by the size rule in `logo/AGENTS.md`: one round's narrative
per file, the archive keeps the rest. Nothing edited — this is the text as it stood at the
bottom of the working set, including its own claims. Round 12 (the desktop-icon round) did
re-verify two of them by running them: `bash icon/build.sh` still rebuilds the set (now **24**
images — `glyph-256.png` was added for the hicolor `256x256/apps` directory), and the README
header URL still answers 200. What Round 11 left undone in code — the wiring of the artwork
into the Python package — is what Round 12 did, so read this before reading Round 12's entry.

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
* **Checked after the push, because a pushed link is a claim:** the README header URL
  (`raw.githubusercontent.com/tjandrasg/kwcapture/main/logo/icon/kwcapture-mark-256.png`)
  answers **200 / 12 342 B**, byte-for-byte the file in `icon/`, and `logo/README.md` itself
  serves 200. The social preview is **not** live: `usesCustomOpenGraphImage` is `false` and
  `openGraphImageUrl` is still GitHub's generated placeholder — the honest status of the one item
  this round could not finish, and the query to re-ask it is in `README.md` §8.

---

## I — Round 12's session-log narrative, verbatim

Moved here 2026-10-11 (Round 13) by the size rule in `logo/AGENTS.md`: one round's narrative per
file, the archive keeps the rest. Nothing edited — this is the text as it stood at the bottom of
the working set, 4 070 bytes, including its own claims. **One of those claims is now wrong on
purpose and kept that way:** the artwork Round 12 shipped was the mark's *monogram*
(`icon/glyph-*.png`, `icon/kwcapture-mark-mono.svg`), chosen because `APTURE` is mush below 64 px.
The owner's rule of 2026-10-11 is that the icon is `logo/kwcapture-mark.svg` and the permitted
transforms are resize and re-render, so Round 13 deleted those files. Read Part I for the **wiring**
— the sync rule, the CI gate, the theme-declared sizes, the licence travelling with the bytes, the
sabotage probe — all of which survived, and read Round 13's entry in `logo/AGENTS.md` for what the
files in `icon/` and `kwcapture/icons/` actually are today. Recover a deleted drawing with
`git log --diff-filter=D -- logo/icon/`; the paragraph-level wrongness is the finding (gotcha 18),
and the generalised lesson is gotcha 38: a build script has no authority to make this decision.

**Round 12 — 2026-10-11, the desktop-icon round.** The mark left this directory and went into
the Python package: `kwcapture install-desktop` now installs it as an actual desktop icon. What
that turned out to be, in the order it bit:

* **A shipped copy is a second artefact, so it wants a rule and a check, not care.**
  `logo/sync_package_icons.py` is now the only thing allowed to write `kwcapture/icons/`: a
  byte-for-byte copy — it never resamples — with `--check` for drift, reading `PNG_SIZES` out of
  `kwcapture/_icons.py` rather than repeating it, so the generator and the installer cannot
  disagree about which sizes exist. `tests/test_icons.py` runs `--check`, so drift fails a build
  instead of quietly shipping last month's logo (gotcha 36).
* **A `--check` that runs only on the machine that made the copy is a note, not a gate.** That
  suite is a CI step now (no compositor, no KDE, no hardware — it writes into a scratch
  `$XDG_DATA_HOME` and restores the environment on the way out), and CI additionally asserts the
  wheel and the sdist each carry the 10 files. Verified here before claiming it: `python -m build`
  → 10 in each artefact and no `logo/` in the sdist; install the wheel in a throwaway venv, run it
  **from `/tmp`** with a scratch `XDG_DATA_HOME` → 9 files installed, and the status line reads
  *brand icons: 9 files in …, entry uses `Icon=kwcapture`*; uninstall → 9 gone and the same status
  line says the entry would fall back to `accessories-screenshot-tool` — the first name this
  desktop actually has installed.
* **Sizes belong to the theme, not to taste.** `glyph-256.png` joined the set because hicolor
  declares a `256x256/apps` directory and the desktop entry ships into it; every size in the
  package is one that `/usr/share/icons/hicolor/index.theme` actually lists (gotcha 37).
* **The `Icon=` findings belong to the root [`../AGENTS.md`](../AGENTS.md) gotchas** — the
  six-release spec name that resolves in no theme, `;` being parsed by nobody (GLib and KService
  both take the whole value as one name), and entries keyed per helper binary, which left two of
  this desktop's three entries stale until `_desktop.refresh_entries()`. From this directory's
  side only one thing matters, and it is a design statement: **the artwork ships as the glyph** —
  the same drawing as `kwcapture-mark.svg` with the word dropped, not a second logo. THE RULE is
  untouched by any of this: no letter was added, moved or repainted this round.
* **The licence now travels with the bytes.** `kwcapture/icons/COPYING.md` is generated: CC BY 4.0
  for the pictures against MIT for the code (the split this directory's
  [`LICENSE.md`](LICENSE.md) makes), the attribution line the licence asks for, and the source
  sha256 of every file — so an installed tree can be traced back to the sketch it came from.
  `logo/` stays out of the sdist deliberately — **1.5 MB** on this checkout, 1.1 MB of it generated
  review PNGs (`du -sb logo --exclude='*.jsonl'`, measured because the first draft of this line said
  "~700 KB" and was wrong); the `--check` inside the test suite is the bridge back to it.
* **A probe that proves the checks can fail:** `../probe/sabotage_icons.sh` breaks ten rules in
  turn and requires the suite to notice — **10/10 detected** here, clean tree green — restoring
  every file from a `trap`, because it edits tracked source and sessions here die mid-run. One
  sabotage needed the *test* rewritten rather than the code: the test corrupted a PNG **header**,
  so the module's IHDR check caught it and the guard under test (re-read after write) passed for
  the wrong reason. Flipping a byte inside the IDAT is the version that only that guard can see.
  Gotchas 22 and 24 in the wild, in a test written the same day.
* **Not done:** the two GitHub uploads are still web-UI clicks (gotcha 34), and whether PyPI
  renders a project icon out of the now-shipped artwork is **untested** — do not claim it. The
  docs header stays the only displayed consumer that is verified.


---

# Part J — Round 13's session log, moved verbatim (2026-10-11, by Round 14)

**Nothing here is a current instruction.** Moved out of `AGENTS.md` §*Session log* under this
folder's size rule — *a round that adds narrative also moves one out*. Source: `logo/AGENTS.md`
at commit `e5d1663`, sha256 starting `d1aef7c04a9fff65`, lines 1043–1121, 7379 bytes, extracted by
line range and not edited. `AGENTS.md`'s Round 14 entry points here and carries the current state
of the artwork, which is the same artwork: Round 14 changed paint, not drawing.

**Round 13 — 2026-10-11, the one-artwork round.** The owner's brief was one sentence long and
about a mistake: the previous session picked the **wrong drawing** — the monogram — for the shipped
icons, "the chosen official icon and logo for kwcapture is only `kwcapture-mark.svg`; no other
variant allowed except resizing or re-rendering". Fixing it cost 13 deleted files, 5 new ones, a
sweep through nine documents, and it produced the most transferable gotcha in this file:

* **A build script has no authority to make a branding decision (gotcha 38).** Round 12's glyph was
  not carelessness, it was a *measurement*: `APTURE` is legible at 128 px, marginal at 64, mush at
  48 and below, and a full-bleed mark loses 4 015 px under GitHub's circular crop. That measurement
  went into `icon/build.sh` as a **selection rule** — ship the drawing without the word at small
  sizes — which is an owner's decision expressed in a place with no authority to make it. The fix
  is not "the measurement was wrong"; the measurement is still true, still on the page, and is now
  written as a **consequence the owner accepted** (`README.md` §8) instead of a reason to substitute
  artwork. Generalises to anything with an owner: **when a number appears to contradict a decision,
  document the number and ask — never route around the decision in a Makefile.**
* **What the change actually is.** `icon/build.sh` renders the mark at nine sizes (16/24/32/48/64
  are new; the mark had never existed below 128 — gotcha 37 is exactly this gap, seen from the other
  side), `tiles.py` grounds those renders on white at **79 %** of the tile, `favicon.ico` is built
  from the mark PNGs (`frame[0]` is pixel-identical to `kwcapture-mark-16.png`), and
  `sync_package_icons.py` copies `logo/kwcapture-mark.svg` **verbatim** as the package's scalable
  entry. Out went `icon/glyph-*.png` (12 files) and `icon/kwcapture-mark-mono.svg`. `icon/` is
  **17 images of one artwork**, and `bash logo/icon/build.sh` is reproducible: all 21 files matched
  their pre-build sha256 after a full rebuild.
* **Two guards, because the reason it happened is that nothing stopped it.** `build.sh` now ends by
  re-rendering the mark at all nine sizes and comparing **pixels** — a byte comparison would fail on
  the `-strip` re-encode and a name check would pass a hand-swapped file, so it compares the thing
  that matters — and `tests/test_icons.py` gained nine checks: the packaged SVG **is**
  `logo/kwcapture-mark.svg` byte for byte, every packaged PNG is that mark's render of the size its
  directory promises, and a tile that comes out grey or blank fails. 89 → **98 checks**, 0 skipped
  here, and `probe/sabotage_icons.sh` still reports **10/10 detected**, which is the difference
  between a suite that asserts and a suite that is decorated.
* **The legibility ladder stays, demoted to what it always was: a control** — and rebuilding it
  caught a new gotcha (39). `preview/build.sh` now renders the monogram row into `$T` on the fly
  instead of reading a file in `icon/`, deliberately: a monogram sitting in the shipped-icon
  directory reads like an approved icon, which is how the last round got its artwork wrong. The
  figure's title has to say *NOT an icon*, which meant writing a title — and `montage -title` drew
  it wider than the canvas and cropped characters off **both** ends at exit 0, in the version that
  had been in the README all along ("…d mark (top) vs the monog…"). A tool this folder uses for
  presentation turned out to be the one tool nobody measured: the title is now drawn with Pillow at
  a size solved from its own metrics and asserted to fit, labels are sized against the tile, and the
  build prints the ink extents. Verified by measurement, not by looking: title ink spans x 80..622
  of 704, so 80 px of air each side.
* **The install path is byte-exact again.** After `install-desktop` on this desktop: nine installed
  files whose sha256 equals the mark render for that size, `scalable` equal to
  `logo/kwcapture-mark.svg`, `desktop-file-validate` silent, `doctor` green, and wheel + sdist still
  carrying 10 icon files each with `logo/` in neither. Nothing in `kwcapture/` changed except
  `_icons.py`'s docstring, which had been advertising the abandoned design.
* **Docs were swept, not patched.** Root `AGENTS.md`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `logo/README.md` §8, `logo/LICENSE.md`, `logo/AGENTS.md`, `logo/icon/build.sh`, `logo/preview/build.sh`
  and `logo/sync_package_icons.py` all said, in so many words, that the small-size artwork *is* the
  glyph; every one of those sentences now says the mark, and the reason keeps its place as a cost
  rather than being deleted with the mistake. Round 11's and Round 12's **verified blocks were
  annotated, not rewritten** — they are dated claims, and that this project believed the other story
  for two rounds is part of the record (the archive's rule: move, never correct in place).
* **Checked after the push, because "the tests pass" on the machine that wrote them is half a
  claim.** Run 38122958295 on `34432a8`: `build` and `headless KWin capture (Plasma 6, no GPU)`
  both **success**, and read off the log rather than inferred from the green tick — the icon suite
  printed **97 passed + 1 skipped** (`[SKIP] desktop-file-validate  tool not installed`, announced,
  not silently passed), and the artefact step printed **`wheel: 10 icon files`** and
  **`sdist: kwcapture-0.6.0.tar.gz 10 icon files`**. One method note, because it cost a detour: the
  `/actions/runs/<id>/jobs` endpoint gives conclusions but no output, `…/actions/jobs/<id>/logs`
  answers **401 to urllib** where `curl -sL` gets 200 — the log lives behind a redirected signed URL
  that urllib's redirect handling does not carry the credential across — and the per-suite count is
  `grep -c '[PASS]'` inside the *step's own slice* of the log: the whole log had 134 PASS lines,
  because the ring-reader suite ran first, and reporting that would have been a number that happens
  to be wrong.
* **Asked, answered, closed the same day — which is what this round's lesson is for.** Round 13
  ended by *asking* three things instead of deciding them in code, and the owner answered all three
  within one exchange: the social preview is **uploaded and verified live** (`true`, a
  `repository-images…` URL, 0 of 51 681 sampled pixels differing from `icon/github-social-preview.png`);
  `kwcapture-mono.svg` is **unofficial and historical, safe to delete** — so it leaves the tree and
  `--monogram` becomes a figure/`/tmp` tool, nothing more; and the unreadable word at 16 px is
  **accepted with a shrug** — *"Why bother? There's no way it would be readable at that low
  resolution"* — so the small sizes are settled and no future round may "rescue" them with other
  artwork. The fourth answer (a palette of `#00ff00` + `#7f7fff`) is the one this round had to push
  back on rather than apply, because measuring it showed the green is a *brightening* that fails on
  white — the ground every tile in `icon/` is built on. It is written up under *Still open* with the
  numbers, unapplied. That is the difference between gotcha 38 obeyed and gotcha 38 memorised: the
  measurement goes **back** to the owner, with the awkward half included, before anything ships.


---

# Part K — the ANATOMY ROUND plan, moved verbatim (2026-10-12)

**Nothing here is a current instruction — and, unlike every other part of this file, none of
it was ever committed.** Moved out of `logo/AGENTS.md` §*Still open* once the round it plans
had been executed, under this folder's size rule (*a round that adds narrative also moves one
out*). Source: `logo/AGENTS.md` in the working tree on top of `af20054`, where the bullet was
drafted and deliberately left uncommitted because it held the plan — so this archive is its
only survivor. Lines 1045-1153, 8957 bytes, sha256 starting
`b132d2d2c2ee7c96`, extracted by line range and not edited.
The executed result is `AGENTS.md` §*Still open*, bullet *ANATOMY ROUND — executed 2026-10-12*,
and it corrects one index in the plan's prose; the plan stays wrong here, because that is this
file's rule: *text is moved, never corrected in place*.

* **ANATOMY ROUND (drafted 2026-10-12, NOT started — this bullet is the whole plan, written
  because the session that drafted it had no tokens left to execute it).**
  `preview/anatomy.png` labels three parts of the mark — **C**, **A**, **PTURE** — and says nothing
  about **K** and **W**, which are the other two letters and the only ones that carry the
  monogram's green. The figure therefore explains the parts that are *not* type and the part that
  *is*, while leaving the actual monogram unlabelled. Add both letters, located the same way the
  existing three are located.
  **Where everything lives** (verified 2026-10-12, line numbers as of `af20054`):
  - `logo/preview/anatomy.py`, 63 lines. A `BOXES`-style list of
    `(label, ink_box, rgb_colour, caption)` tuples — currently three entries, C / A / PTURE — plus
    a Pillow-drawn footer line and a caption strip. `preview/build.sh:246` runs it, then re-encodes
    every PNG in place with `magick -strip -compression-level=9`.
  - Existing boxes at 512 px: `C (64.4,126.8,263.3,449.9)`, `A (256.9,234.4,327.6,321.5)`,
    `PTURE (276.9,60.1,504.6,281.4)`. Their authority is stated in the file header: **they are the
    ink boxes `validate_logo.py` reports** for `#a` and `#wordmark`, and the box computed from
    `#kw-c`'s path data — *not eyeballed*, and that property is the thing to preserve.
  - Docs that describe the figure: `logo/README.md` §8 area (it lists the README images) and the
    root `README.md` if it embeds `anatomy.png` — check both with
    `grep -rn "anatomy" README.md logo/README.md logo/AGENTS.md` before writing.
  **The hard part, and the reason this is a round rather than an afternoon:** there is **no `#k` or
  `#w` element to measure.** `#kw` is a *single* path holding the whole monogram — the validator
  prints one box for it, `#kw 7.45..451.08 x 100.97..451.93` at 512 px — so K and W have no
  individually-addressable geometry in the emitted SVG.

> **CORRECTION, same day — the owner supplied the answer, and it supersedes the fallback below.
> The per-letter geometry IS known: it is the vertex partition in `gen_logo.py`, commented at
> ~lines 1015-1016.** The monogram is **one closed 19-vertex outline**, and the letters are
> **index subsets of it**:
>
>     K = 0  1  2  3  4        13 14 15 16 17 18
>     W =    3  4  5  6  7  8  9 10 11 12 13 14
>     C =    3  4  5  6        12 13 14 15 16 17     <- the blue one
>
> **Route 1 is therefore: take the vertex list `gen_logo.py` already builds, subset it by letter,
> and take min/max of those vertices' x,y.** Exact, no rasterising, no guessing — and it lands in
> the same mm units the existing C/A/PTURE boxes use, so scale by the script's existing 512 px
> factor to stay comparable with the validator.
> **Three consequences that must be respected:**
> - **The subsets overlap — vertices 3-4, and 12-14 — and that is the ligature, not a bug.** K's leg
>   *is* the W's first stroke, and C borrows from both. So the K and W boxes **will overlap on the
>   image**: draw them as overlapping/transparent outlines or offset leader lines, never as two
>   disjoint regions, and say in the caption that they share strokes. "K and W are separate letters
>   whose boxes happen to overlap" is the false version; **one outline, three readings** is the true
>   one. This also refines the owner-facing question before any push: not "two letters or one
>   monogram", but *how much of the sharing to show*.
> - **Gotcha 22 lives right here**: an invented partition was tried on 2026-10-10 and was wrong. Use
>   the owner's numbering **as written in `gen_logo.py`**; if the vertex-count guard
>   (`len(verts) != 19`) trips, the letter rings are re-checked by the owner, never guessed here.
> - **Read the indices from the generator; do not retype them into `anatomy.py` as literals.** Same
>   law as the palette (gotcha 40): a duplicated constant goes blind at the next edit. Import or
>   parse them, and print what was read.
> **The old routes below are demoted to instrumentation, which is still worth doing:** keep a
> connected-component or ink-profile check as an **independent instrument**, not as the source of the
> boxes — assert that the union of the vertex-derived K and W boxes matches the validator's `#kw` ink
> box (`7.45..451.08 x 100.97..451.93` at 512 px) within antialiasing tolerance. Vertex maths and
> rendered ink disagreeing would be a real finding about the outline, and gets reported.

The three routes as first drafted (route 1 is now the vertex subset above):
  1. **Segment the render.** Rasterise `logo/kwcapture-mark.svg` at 512 (or 1024 for precision),
     threshold on alpha, run **connected-component labelling** (Pillow has no CC label; use
     `scipy.ndimage.label` if it's importable in `.venv`, else a small BFS/union-find — stdlib only,
     and keep it in `anatomy.py` so the figure stays self-contained). Each letter's ink box falls
     out of the components. This is a *measurement*, which is what the file's header promises.
     **Expect the letters to touch or overlap** — it is a monogram, they are designed to interlock —
     and then components merge and there is no per-letter box to report. When that happens, do NOT
     invent one.
  2. **Split on the ink profile.** Column-wise ink histogram between the two letter masses; the
     local minimum is the seam. Report the box as "K, left of the seam at x≈N" and **say in the
     caption that the box is a measured split of one path, not a separate element** — an annotation
     that implies structure the SVG does not have is a false claim wearing a leader line, which is
     this folder's oldest sin.
  3. **Ask the generator.** `gen_logo.py` places the glyphs, so it may know each letter's origin and
     advance. Reading geometry out of the generator is legitimate — it is how `contrast_report.py`
     reads the palette — but only if it is *read*, not re-derived by hand, and the two sources must
     be cross-checked (1 or 2 as the independent instrument), because a box lifted from the
     generator and never checked against the render is exactly the stale-number failure gotcha 40
     and 41 are about.
  **Rules this round must not break**
  - **Gotcha 38 / THE RULE: no new artwork.** Annotation is presentation. K and W get leader lines
    and boxes *drawn into the figure*, never a re-cut path, and `kwcapture-mark.svg` must stay
    byte-identical — prove it with `git diff` on the SVG, and with `gen_logo.py --mark` still
    reproducing it, before and after.
  - **Gotcha 39: titles and labels are drawn by Pillow in this script.** Three rows become five, so
    the canvas grows; measure the resulting ink extents and print them at build time like the other
    figures do, and show the labels are not cropped at either edge.
  - **Gotcha 41: the diagnostic must not be the writer.** `anatomy.py` reads the render and writes
    the figure; it must not rewrite anything in `icon/`, and after the round
    `bash preview/build.sh && git status` should show only the figures it is allowed to change.
  - **The colour split is load-bearing.** Green marks the monogram, blue the rest, and P2's split is
    only **1.32:1** in lightness (hue carries it). If K and W are boxed in green on a green half,
    the box will be invisible in greyscale — pick annotation colours that clear a visible contrast
    against *both* halves, and state the ratios you measured.
  **Definition of done**
  - `anatomy.py` has five labelled rows; every box is derived by a named, reproducible measurement
    with the method stated in the file header and, for anything that is a split rather than an
    element, in the **caption on the image itself**.
  - `bash preview/build.sh` exits 0, prints the measured extents, and the figure is legible at the
    width `README.md` renders it (check the PNG at README width, not just at full size).
  - `kwcapture-mark.svg`, `kwcapture.svg` and everything in `icon/` are unchanged: `git status`
    clean for those paths; `tests/test_icons.py` still 98 / 0.
  - Docs updated: `logo/README.md` §8 caption for the figure, the root `README.md` if it embeds it,
    and `logo/AGENTS.md` *Expected numbers* gains the new `anatomy.png` byte size and canvas
    dimensions. **Re-measure both `wc -c` size notes in this file at commit time — they are stale
    right now by design** (this bullet was added without a commit, so the file is deliberately
    dirty; the digits must be rewritten last, so they describe the file they end up in).
  - Commit locally, do **not** push, until the owner has looked at the rendered figure: it is a
    public-facing explanation of the mark, and whether K and W are described as "two letters" or as
    "one interlocked monogram" is a branding statement, not a rendering detail — owner's call, and
    the caption wording is theirs to approve before it goes out.

# Part L — Round 14's log, the two closed decision histories and the ANATOMY ROUND outcome, moved verbatim (2026-10-12)

> Trim pass after v0.7.0 shipped: `logo/AGENTS.md` **130129** B before it, **~107680** B after. What moved: the ANATOMY ROUND's outcome narrative (the round is done, approved and released), gotcha 29's pre-ruling investigation (closed 2026-10-12 by the owner as this desktop's environment), PALETTE P2's decision history (a closed decision — the bullet itself asked to be moved here), the two `test_kwcapture.py` failure write-ups (same ruling), the GitHub social-preview verification detail (nothing owed), Round 14's session log, and the size-discipline note as it read before this pass. **Nothing in this part is a current instruction**; the rules those rounds produced are still in `AGENTS.md` — the vertex-ring rule, the measured-annotation-contrast floor, gotchas 40 and 41, and the re-run-before-you-believe rule.


## The size-discipline note, before the 2026-10-12 trim

*moved verbatim from `logo/AGENTS.md` lines 23-76 on 2026-10-12; the summary that replaces it is in the working file.*

> **Size discipline** (the root `AGENTS.md` says the same). This file is **130 129** bytes
> — `wc -c logo/AGENTS.md`, not remembered. It was the **working copy's** number for a day, which
> was a first for this note: the *ANATOMY ROUND* at the top of *Still open* was finished and held
> uncommitted until the owner had seen the figure, so `af20054` still carried Round 14's **119 211**
> while this text existed only on disk. The owner has seen it and told me to push it, so this file is
> committed and the number is both again — and it still has to be rewritten **last** in any round
> that edits this file, because a count written inside the thing it counts is wrong by its own length
> until it is. These digits were measured, patched and re-measured until the two agreed. What the
> round cost here is small because it paid as it went: the ANATOMY ROUND **plan** moved
> **verbatim** to [`AGENTS.old.md` Part K](AGENTS.old.md) — 8 957 bytes, string-searched into the
> archive *before* the pointer replaced it — and that archive is now the plan's only copy, because
> the bullet that held it was never committed. `AGENTS.old.md` grew 128 492 → 138 364, the first
> time this rule has cost the archive anything rather than the file. **Round 14** (the palette
> round) opened at **96 404** and closes at **119 211**, the last committed state. It paid for
> itself once, by
> moving Round 13's session-log narrative out **verbatim** — 7 327 bytes, presence in
> [`AGENTS.old.md` Part J](AGENTS.old.md) asserted by string search *before* the pointer replaced it,
> the way Parts G/H/I were done — and still grew, because a recolour round spends its budget on
> *proof*: a verified block, the corrected two-grounds arithmetic, the trade the palette made, two
> new gotchas (**40**: a check keyed on a colour *literal* goes blind quietly; **41**: a diagnostic
> that writes the artefacts it measures makes a build lie about being reproducible), and re-measured
> numbers throughout. That is what the round sells, so that is what it costs — including a resumption
> that found gotcha 41 by re-running a build nobody had re-run, which is what the re-run rule is
> for. The debt passes on, with one
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


## ANATOMY ROUND — the full outcome narrative

*moved verbatim from `logo/AGENTS.md` lines 1082-1156 on 2026-10-12; the summary that replaces it is in the working file.*

* **ANATOMY ROUND — executed, approved and shipped 2026-10-12.** The owner looked at the rendered
  figure, said log it in `CHANGELOG.md` and push it, which settles the two framing questions the
  round left open: the wording the project ships is **one outline, three readings**, and the
  darkened annotation colours go with it (see the colour bullet below). The plan this ran to —
  drafted by the session that had no tokens left to run it — is archived verbatim at
  [AGENTS.old.md Part K](AGENTS.old.md); what is kept here is the outcome, the numbers, and the
  one thing the plan got wrong. `preview/anatomy.png` is **five rows: K, W, C, A, PTURE**.
  * **The boxes are geometry, not eyeballs, and the two new ones are *not* elements.** There is
    no `#k` and no `#w` to measure: `#kw` is one closed 19-vertex outline, so each letter's box
    is min/max of x,y over **its** vertices, mapped by the shipped file's own `#logo` transform
    (`translate(-576.8719 -1095.0049) scale(11.918)`, artboard 512 → 1 px per unit). The rings
    are **read out of `gen_logo.py`** (`K_RING`, `W_RING`, `C_RING`) and the vertex count is
    guarded by the generator's own `c_clip_polygon()` — nothing is retyped here (gotcha 40), and
    nothing is inferred from the shape (gotcha 22). Measured at 512 px:
    `K 7.45..200.67 x 100.97..451.93`, `W 65.27..451.08 x 281.92..451.10`, overlapping
    **135 x 169 px**, sharing vertices **3 4 13 14**.
  * **Three cross-checks, asserted in `preview/anatomy.py` and printed at build time:**
    `C_RING` over the vertices reproduces the box computed from `#kw-c`'s path data to
    **0.047 px**; `union(K, W)` reproduces `validate_logo.py`'s `#kw` ink box to **0.004 px**;
    and an independent instrument — connected-component labelling of the *render*, a stdlib BFS
    over the ink mask, because Pillow has no CC labelling and a figure must not acquire a scipy
    dependency — puts the monogram's ink at `7..450 x 101..451`, **0.45 px** from `union(K, W)`,
    with the green channel (the monogram minus the blue C) spanning all four sides to the same
    0.45 px. Any of the three failing stops the build, with a message that says which.
  * **What the instrument settled:** the render labels the monogram as **ONE component** —
    57 953 px, 21x the next blob, 7 components in all (`1 + #a + PTURE`). The letters touch.
    No segmentation of the ink can ever yield a per-letter box, which retires the archived
    plan's routes 1 and 2 as sources and keeps them as instruments, exactly as its correction
    said. The letters can be boxed **only** by vertex, i.e. only by the owner's numbering.
  * **The plan's prose was wrong by one index, and reading it instead of copying it is what
    caught it.** The plan said the subsets share "3-4, and 12-14". The intersection of the two
    rings *as written in* `gen_logo.py` is **3, 4, 13, 14** — vertex 12 is the W's peak tip and
    the C's, never the K's. The figure prints the computed intersection and the caption is
    generated from it. Gotcha 22 and gotcha 40 caught in one go, and the catch is the argument
    for both: a number re-typed into a caption cannot disagree with the prose about it.
  * **Annotation colour is now measured, not picked — and three existing colours moved
    because of it.** P2's halves are 1.32:1 apart in lightness, so a colour clears 3:1 against
    BOTH only under L 0.031: all five rows were darkened to hues that do (vs green
    **3.10-3.13**, vs blue **4.09-4.13**, vs white **13.46-13.60**; per-row numbers printed by
    the script, computed by `contrast_report.py`, build exits 1 under 3:1). The three colours
    the figure shipped before were chosen to read against *white* and measure **1.11-1.72:1**
    against the artwork (`#d0021b` 1.31 green / 1.72 blue, `#7e57c2` 1.20 / 1.58, `#0277bd`
    1.11 / 1.46) — a greyscale-invisible box on ink, which is the failure this rule exists to
    prevent. Hues were kept and darkened, not swapped, and the two sets of numbers were put in front
    of the owner with the figure: **the approval of 2026-10-12 covers the recolour as well**, rather
    than sending the three old hexes back.
  * **Nothing else moved.** No SVG, no sketch, no icon, no knob: `gen_logo.py --mark` still
    reproduces `kwcapture-mark.svg` byte-identically (`cmp`), `validate_logo.py
    kwcapture-mark.svg` still prints **OK**, `tests/test_icons.py` is **98 checks / 0 failed**,
    and after `bash preview/build.sh` the tree shows `preview/anatomy.py`, `preview/anatomy.png`
    and nothing else in `logo/` except the docs (plus one comment added to `preview/build.sh`,
    which is where the figure's guard is now described). Gotcha 41 respected: the diagnostic
    reads the render and the SVG, writes one PNG, and says so in its own last line. Canvas grew from
    980x824 to **980x1284** (three rows to five) and the script prints the figure's own ink box and
    the air to every edge, asserting
    8 px of it — gotcha 39, since every title and label in this figure is Pillow's.
  * **The wording, and who decided it.** "Two letters" or "one interlocked monogram" is a branding
    statement, not a rendering detail, so the round stopped for the owner rather than deciding it
    here. The figure as shipped says **one outline, three readings**: the K and W rows draw each
    other's box *dashed*, so the overlap is visible instead of implied, and dot the four shared
    vertices. **Owner's approval 2026-10-12**, given on the rendered figure with the instruction to
    put it in `CHANGELOG.md` §*Unreleased* and push; the three annotation colours that moved were
    part of what was approved. This round is also the reason root `AGENTS.md` gained a *LOGO*
    paragraph: the per-letter boxes are now a claim the repo makes, and it is asserted per build.
  * **Shipped: `1811ebc` (this round) + `ca1bf74` (root `AGENTS.md` + `CHANGELOG.md`), pushed
    2026-10-12, CI run 38192200374** — both jobs `success`: `build` (15 steps, among them the
    ring-reader suite, the brand-icon suite, *both artefacts carry the brand icons*, the wheel
    install and the sdist built from scratch) and `headless KWin capture (Plasma 6, no GPU)`.
    **What is claimed here is step conclusions, nothing more**: `GET
    /repos/tjandrasg/kwcapture/actions/runs/38192200374/jobs` with the credential in
    `~/.git-credentials` answers `log_url: null`, so the log bodies — including the pass/skip
    line the icon suite prints on a runner that has no themes — were never read, and the
    **97 passed + 1 skipped** this folder used to quote from CI is *that* run's number, not
    this one's. Locally, on this desktop, `tests/test_icons.py` prints **98 / 0 / 0 skipped**.



## The flake (gotcha 29) — the pre-ruling investigation

*moved verbatim from `logo/AGENTS.md` lines 1172-1187 on 2026-10-12; the summary that replaces it is in the working file.*

* **The flake (gotcha 29): cause still not established — but it is no longer "unreproducible".**
  Both historic messages came back on 2026-10-11 in a code path that never touches fonts, and
  in a pure-Python extract with no third-party imports, plus one CPython-level
  `Executing a cache` abort. **A fourth shape, 2026-10-12, and in a new program:** one run of
  `gen_logo.py --mark` died inside fontTools — `TypeError: 'str' object is not callable` in
  `pens/svgPathPen.py:pointToString`, mid-wordmark — where `ntos` is a bound method or `None`,
  never a `str`, so the interpreter had lost a reference it should not have. The same command
  on the same tree came back **byte-identically clean 5/5** straight afterwards (`cmp` against
  the shipped `kwcapture-mark.svg`), which is the whole point of gotcha 29: the crash is not
  evidence about the code, the re-run is, and the guard that says *which one died* is what
  makes the difference between the two. Next steps, in order and cheap: (1) run the validator ~200× under
  `env -u LD_PRELOAD python3 …` and on a second machine; (2) once under
  `PYTHONMALLOC=malloc_debug`; (3) look at the machine, not the code (this desktop: a global
  `LD_PRELOAD` shim, non-ECC RAM). Keep the `CRASH in <name>` guard: it is the reason this is
  now diagnosable at all. **Do not wrap `box_check` in a retry** — that launders a machine
  fault into a passing build.


## PALETTE P2 — the decision history and the dark-mode finding

*moved verbatim from `logo/AGENTS.md` lines 1226-1269 on 2026-10-12; the summary that replaces it is in the working file.*

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
  **Owed by this palette, and now paid:** the GitHub social preview is a stored **upload**, so it
  had to be re-uploaded for P2. The owner did, and it was verified off the pixels rather than off
  the flag: the live URL — a **new object id**, `5425fcdb-…` where Round 13 recorded `dc44cc05-…`,
  which is how you can tell an upload happened — serves 1280×640 / **84 871 B** with **0 of
  819 200 pixels** differing from the committed P2 card and **6.73 %** differing from the old one.
  See the item below and the root `AGENTS.md`.


## the two test failures on this desktop, as first written up

*moved verbatim from `logo/AGENTS.md` lines 1304-1337 on 2026-10-12; the summary that replaces it is in the working file.*

* **`tests/test_kwcapture.py` carries TWO failures on this desktop, neither of them a logo bug
  (both found 2026-10-11, Round 14, both reported rather than patched).** Measured together:
  **162 passed + 1 failed**, not 165 — the failing check is the BUG-4 block's catch-all
  (`[FAIL] BUG-4 regression ran`), which *replaces* two checks with one, or `alpha is opaque` on
  its own runs. Full write-ups are **FLAKE-2** and **FLAKE-3** in the root `AGENTS.md`; the parts
  that belong to this folder's rules are the method and the restraint. Method: each was proven
  pre-existing from a **pristine `git worktree add … HEAD`** carrying none of the round's changes,
  and FLAKE-3 additionally fails **0 of 5** standalone, which localises it to cross-test
  interference rather than to the zero-copy read path. Restraint: FLAKE-3's third error,
  `CaptureError: unhandled pixel format 6`, is *impossible as printed* — 6 is in the allow-list at
  `kwcapture/__init__.py:1716` — which says the value in the message is not the value that was
  checked, and the honest response to an error message that cannot be true is to make the harness
  print the traceback (one line, in a round that owns `tests/`), not to pick a number that makes
  the suite green.
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


## GitHub social preview + profile picture — the verification detail

*moved verbatim from `logo/AGENTS.md` lines 1338-1358 on 2026-10-12; the summary that replaces it is in the working file.*

* **GitHub social preview: DONE, and now verified live in palette P2 — nothing owed.**
  Re-measured 2026-10-12 after the owner's re-upload, off the URL rather than off the flag:
  `usesCustomOpenGraphImage` is `true` and `openGraphImageUrl` is
  `repository-images.githubusercontent.com/1406948211/**5425fcdb**-bcfa-4d50-b99e-30d4087c1849`.
  That URL is a **different object id** from the one Round 13 recorded (`dc44cc05-…`), which is
  itself the tell that a new upload happened — GitHub mints a new URL per upload. What it serves is
  1280×640, **84 871 B**, and against the committed P2 card **0 of 819 200 pixels differ** by more
  than 8/255; against the pre-P2 card (**84 565 B**) **55 119 px, 6.73 %**, differ. Same bytes as
  this folder, right down to the file size. The loop gotcha 34 said no script could close has now
  been closed twice from a shell: the click is outside the repo, the *proof* never was.
  **Keep the method, not the conclusion:** the flag only proves *an* image is set. The check that
  matters is pixels-against-`HEAD`, because a recolour silently reopens this — a `true` flag with
  the old upload is exactly as misleading as a stale caption (gotcha 39), and between the two
  uploads that is precisely what the repo's own docs had to say.
* **The optional user profile picture is NOT the mark, measured — so nothing is owed there either.**
  `https://github.com/tjandrasg.png` serves 460×460 / 48 875 B and differs from
  `icon/github-avatar-400.png` in **100 %** of pixels — in *both* palettes — so the account picture
  is unrelated artwork that the project never uploaded, not a stale copy of ours. Which means
  `icon/github-avatar-400.png` (P2: 25 293 B) is an asset that exists and is unused: if the owner
  ever wants it as the profile picture that is an account setting no script can reach (gotcha 34);
  until then, no doc may describe it as live.


## Session log — Round 14 day-log

*moved verbatim from `logo/AGENTS.md` lines 1376-1473 on 2026-10-12; the summary that replaces it is in the working file.*


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
* **The build was convicted by running it, not by reading it (gotcha 41).** Re-running
  `bash icon/build.sh` after the commit dirtied five tile PNGs. Two back-to-back builds hashed
  *identical* — so the build is reproducible and something else had written those files: `tiles.py`
  built its tiles at import time, so the `--sweep` diagnostic had re-saved them with Pillow after
  the build's ImageMagick pass. Identical pixels, different container, and git was holding bytes
  that this file's own byte table did not describe. Fixed by making `--sweep` read-only, and the
  mask guard was shown still to refuse on three sabotaged `FIT` values before the change was
  believed. The line worth keeping: **"the build is reproducible" is a claim about `git`, not about
  the build** — rebuilding twice proves only that the build is self-consistent.
* **Two sessions of this round died out of tokens, and the second died *inside* a tool call.** Its
  `edit_file` arguments are truncated mid-string (`Unterminated string in JSON at position 1049`),
  so the *new* text was unrecoverable and only the `old_text` anchor survived — which is still
  enough to know what it was recording: the CI count for the P2 push. Re-derived from the run log
  rather than reconstructed from the fragment (see *Reading the transcript*). The recovery rule held:
  re-run everything the dead session claimed before writing any of it down. Every claim in the
  verified block above was measured again in this resumption; one of them turned out to be false,
  which is the entire argument for the rule.

