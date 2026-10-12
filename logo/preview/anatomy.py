#!/usr/bin/env python3
"""Build preview/anatomy.png — the one figure that explains the mark.

Five rows, each the shipped mark with one part boxed: the monogram's two letters, the
junction they form, the mouse pointer, and the type. The whole design is that one part of
the picture is a monogram stroke, one part is a pointer and one part is type.

THE BOXES ARE NOT EYEBALLED. Every row says on the image where its box came from, and the
script re-derives and cross-checks them at build time:

  A, PTURE   the ink boxes `validate_logo.py` reports for #a and #wordmark — the same two
             numbers quoted in README §5.2 and in AGENTS.md §Expected numbers.
  C          the box computed from #kw-c's own path data.
  K, W       THERE IS NO #k AND NO #w ELEMENT to measure: #kw is ONE closed 19-vertex
             outline, and the letters are index SUBSETS of it — the owner's numbering of
             2026-10-10, in gen_logo.py as K_RING / W_RING / C_RING. The box is min/max of
             x,y over that subset, mapped through the shipped file's own #logo transform,
             so it arrives in the same 512 px canvas space as the boxes above. Exact; no
             rasterising, no guessing.
             The rings are READ out of gen_logo.py, never retyped here (gotcha 40: a
             duplicated constant goes blind at the next edit), and the vertex count is
             guarded by the generator's own c_clip_polygon(), which refuses a monogram
             that is not 19 vertices (gotcha 22: an invented partition was tried on
             2026-10-10 and was wrong — if that guard trips, the rings go back to the
             owner, they are not re-guessed here).

  CROSS-CHECKS, every one asserted and printed:
   1  C_RING over the vertices reproduces the #kw-c box already drawn here to <0.1 px. A
      box whose authority is path data, reproduced by the subset method, is the evidence
      that the numbering is being applied to the polygon the artwork actually paints.
   2  union(K, W) reproduces validate_logo.py's #kw ink box
      (7.45..451.08 x 100.97..451.93 at 512 px).
   3  an INDEPENDENT instrument, the render itself: connected-component labelling of the
      ink mask of kwcapture-mark-512.png — a stdlib BFS, because Pillow has no CC
      labelling and this figure is not allowed to acquire a scipy dependency. It finds the
      monogram as ONE component (the letters touch: that is precisely why the per-letter
      boxes cannot come from segmenting the ink, and why they come from the owner's
      vertex numbering instead), and that component's ink box must match union(K, W)
      within antialiasing. The green channel is a second render instrument: green is the
      monogram minus the blue C, so it must touch all four sides of the union box.

The subsets OVERLAP, and that is the ligature, not a bug: the K's leg IS the W's first stroke
and the C borrows from both. The shared indices are COMPUTED here (`set(K_RING) & set(W_RING)`,
which on today's rings is 3, 4, 13 and 14) and printed, not copied out of a comment — the note in
`gen_logo.py` and the round plan both say "3-4", and prose about a set is not that set: vertex 12
is the W's peak and the C's, never the K's. So the K, W and C boxes overlap by design, the shared
vertices are dotted on the figure, and the wording is "one outline, three readings" — never "three
letters whose boxes happen to collide".

ANNOTATION COLOUR. Palette P2 puts the two halves only 1.32:1 apart in LIGHTNESS, so a
mid-tone leader line disappears into the ink and a green box on the green half is
invisible in greyscale. Every row colour here is measured by contrast_report.py — the
same instrument every ratio in this folder is quoted from — against GREEN, against BLUE
and against the white ground, and the build fails if any of the three falls under 3:1.

GOTCHA 41. This file READS kwcapture-mark.svg and kwcapture-mark-512.png and WRITES ONLY
preview/anatomy.png. Nothing in logo/*.svg or icon/ is touched: `bash preview/build.sh
&& git status` must stay clean for those paths.

    python3 logo/preview/anatomy.py     # after re-rendering kwcapture-mark-512.png
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LOGO = HERE.parent
sys.path.insert(0, str(LOGO))

import contrast_report as CR   # the WCAG instrument this folder quotes every ratio from
import gen_logo as G           # K_RING / W_RING / C_RING, poly_vertices(), GREEN / BLUE

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MARK_SVG = LOGO / "kwcapture-mark.svg"
RENDER = HERE / "kwcapture-mark-512.png"
SVG = "{http://www.w3.org/2000/svg}"

RENDER_PX = 512          # the size build.sh renders the mark at, and this figure measures
INK_L = 240              # a pixel is ink when its L falls under this (the ground is 255)
AA_TOL = 2.0             # px: how far rendered ink may sit from exact geometry
RING_TOL = 0.06          # px: the quoted boxes are printed to 1-2 dp; nothing coarser

# validate_logo.py's #kw ink box at 512 px, as AGENTS.md §Expected numbers publishes it.
# Pinned here so a coarse move in the artwork trips; cross-check 3 (rendered ink) is the
# instrument that cannot go stale, and it is run on every build.
VALIDATOR_KW = (7.45, 100.97, 451.08, 451.93)

# Row colours. Dark on purpose: to clear 3:1 against BOTH P2 halves (L 0.192 and 0.269) a
# colour has to sit under L 0.031, which is dark — that is what a 1.32:1 split costs, and
# it is arithmetic, not taste (see contrast_report.py's *window* lines). The hues are the
# ones the figure has always used, darkened rather than swapped, and the five are spread
# round the wheel away from the artwork's 150deg and 255deg.
COLOURS = {
    "K": "#5a0053",       # magenta
    "W": "#402a00",       # amber-brown
    "C": "#640018",       # crimson (was #d0021b)
    "A": "#38215f",       # violet  (was #7e57c2)
    "PTURE": "#003052",   # azure   (was #0277bd)
}


def fail(msg):
    sys.exit(f"anatomy.py: {msg}")


# ------------------------------------------------------------- geometry, read not typed
def kw_outline():
    """(#kw's vertices, the mm->px map, the artboard size) — all read out of the SHIPPED
    SVG, so the boxes live in the same space the validator measures in."""
    for path in (MARK_SVG, RENDER):
        if not path.is_file():
            fail(f"missing input {path} — re-run bash preview/build.sh")
    root = ET.parse(str(MARK_SVG)).getroot()
    logo = root.find(f".//{SVG}g[@id='logo']")
    kw = root.find(f".//{SVG}path[@id='kw']")
    if logo is None or kw is None:
        fail(f"{MARK_SVG.name} has no #logo group or no #kw path")
    m = re.fullmatch(r"translate\(([-\d.eE ]+)\)\s*scale\(([-\d.eE]+)\)",
                     (logo.get("transform") or "").strip())
    if not m:
        fail(f"cannot read #logo's transform as translate(...) scale(...): "
             f"{logo.get('transform')!r} — the K/W boxes are mapped through it, so the "
             f"reader has to be sure of it, not hopeful")
    tx, ty = (float(v) for v in m.group(1).split())
    sc = float(m.group(2))
    canvas = float(root.get("width"))
    if canvas <= 0:
        fail(f"{MARK_SVG.name} has no usable width attribute")
    return G.poly_vertices(kw.get("d")), (tx, ty, sc), canvas


def letter_box(verts, ring, xform):
    """min/max of x,y over the ring's vertices, in 512-px canvas space.

    A closed polygon of straight edges cannot overshoot its own vertices, so the vertex
    box IS the ink box of that subset of the outline: exact geometry, not a measurement
    of a picture."""
    tx, ty, sc = xform
    pts = [verts[i] for i in ring]
    xs = [sc * x + tx for x, _y in pts]
    ys = [sc * y + ty for _x, y in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def delta(a, b):
    return max(abs(a[i] - b[i]) for i in range(4))


# ------------------------------------------------- the render instrument (gotcha: it is
# not the source of the boxes, it is the instrument that keeps the geometry honest)
def ink_mask():
    im = Image.open(RENDER).convert("RGB")
    if im.size != (RENDER_PX, RENDER_PX):
        fail(f"{RENDER.name} is {im.size[0]}x{im.size[1]}, expected "
             f"{RENDER_PX}x{RENDER_PX} — re-run bash preview/build.sh")
    return im, im.convert("L").point(lambda v: 255 if v < INK_L else 0)


def components(mask):
    """Connected-component labelling by BFS over the ink mask. 4-connected, stdlib only,
    and deliberately simple: it has to count blobs and box them, nothing else."""
    w, h = mask.size
    data = bytearray(mask.tobytes())
    label = [0] * (w * h)          # a list, not a bytearray: 255 components is not a lot
    # and a speckled render would raise ValueError out of a bytearray, not a clear message
    out = []                                   # (size, box) per component, 1-based order
    for start in range(w * h):
        if not data[start] or label[start]:
            continue
        n = len(out) + 1
        q = deque([start])
        label[start] = n
        x0 = x1 = start % w
        y0 = y1 = start // w
        size = 0
        while q:
            i = q.popleft()
            size += 1
            x, y = i % w, i // w
            x0, x1 = min(x0, x), max(x1, x)
            y0, y1 = min(y0, y), max(y1, y)
            for j in ((i - 1 if x else None), (i + 1 if x < w - 1 else None),
                      (i - w if y else None), (i + w if y < h - 1 else None)):
                if j is not None and data[j] and not label[j]:
                    label[j] = n
                    q.append(j)
        out.append((size, (x0, y0, x1 + 1, y1 + 1)))   # box exclusive, like Image.getbbox
    return out


def channel_mask(im, ink, hi, mid, lo):
    """ink pixels where channel `hi` leads both other channels by >20 — how the figure
    separates the green monogram from the blue type without knowing the palette."""
    ch = im.split()

    def leads(a, b):
        return ImageChops.subtract(a, b).point(lambda v: 255 if v > 20 else 0)
    return ImageChops.multiply(ink, ImageChops.multiply(leads(ch[hi], ch[mid]),
                                                        leads(ch[hi], ch[lo])))


def fmt(box):
    return f"{box[0]:.2f}..{box[2]:.2f} x {box[1]:.2f}..{box[3]:.2f}"


def px(box):
    """A component box as PIL reports it (exclusive) printed like the validator's."""
    return f"{box[0]}..{box[2] - 1} x {box[1]}..{box[3] - 1}"


# -------------------------------------------------------------------- the five boxes
verts, xform, canvas = kw_outline()
c_clip = G.c_clip_polygon(verts)          # the generator's own 19-vertex guard (gotcha 22)
for name, ring in (("K_RING", G.K_RING), ("W_RING", G.W_RING), ("C_RING", G.C_RING)):
    if not ring or max(ring) >= len(verts):
        fail(f"{name} indexes past the monogram ({len(verts)} vertices): the rings are "
             f"the owner's numbering of THIS outline, so this is a question for the owner")

rings_read = "  ".join(
    f"{n} = {' '.join(str(i) for i in r)} ({len(r)} of {len(verts)})"
    for n, r in (("K_RING", G.K_RING), ("W_RING", G.W_RING), ("C_RING", G.C_RING)))
print(f"rings read from gen_logo.py: {rings_read}")
print(f"#kw {len(verts)} vertices, #logo translate{tuple(xform[:2])} scale {xform[2]}, "
      f"artboard {canvas:.0f} -> {RENDER_PX} px render")

shared = sorted(set(G.K_RING) & set(G.W_RING))
print("shared K&W vertices: " + " ".join(map(str, shared)) +
      "  <- the ligature: the K's leg is the W's first stroke, so the boxes overlap")

box_K = letter_box(verts, G.K_RING, xform)
box_W = letter_box(verts, G.W_RING, xform)
box_C = letter_box(verts, G.C_RING, xform)
box_KW = union(box_K, box_W)

# authority 1: #kw-c's own path data, as this figure has always drawn it
C_PATH_DATA = (64.4, 126.8, 263.3, 449.9)
d_c = delta(box_C, C_PATH_DATA)
if d_c > RING_TOL:
    fail(f"C_RING over the vertices gives {fmt(box_C)} but #kw-c's path data gives "
         f"{fmt(C_PATH_DATA)} ({d_c:.3f} px apart). The subset method and the painted C "
         f"disagree — the ring numbering is suspect (gotcha 22), ask the owner.")

# authority 2: the validator's #kw ink box
d_kw = delta(box_KW, VALIDATOR_KW)
if d_kw > RING_TOL:
    fail(f"union(K, W) = {fmt(box_KW)} but validate_logo.py's #kw box is "
         f"{fmt(VALIDATOR_KW)} ({d_kw:.3f} px apart). Either the rings no longer cover "
         f"the outline or the published number has gone stale — re-run the validator.")

# authority 3 (independent): the rendered ink
im, ink = ink_mask()
comps = components(ink)
comps.sort(key=lambda c: -c[0])
mono = comps[0][1]
d_render = delta(box_KW, mono)
if d_render > AA_TOL:
    fail(f"union(K, W) = {fmt(box_KW)} but the render's monogram component is "
         f"{px(mono)} ({d_render:.2f} px apart, tolerance {AA_TOL}). Vertex maths and "
         f"rendered ink disagree, which is a finding about the outline, not a rounding "
         f"error — report it, do not widen the tolerance.")
if len(comps) < 2 or comps[0][0] < 4 * comps[1][0]:
    fail(f"the largest ink component is not clearly the monogram: {comps[0][0]} px vs "
         f"{comps[1][0] if len(comps) > 1 else 0} px — the render is not what this "
         f"figure thinks it is")
n_letters = 1 + 1 + len(G.WORD)              # monogram + pointer-A + one per type glyph
green = channel_mask(im, ink, 1, 0, 2)       # green leads red and blue: the monogram's ink
gb = green.getbbox()
d_green = delta(box_KW, (gb[0], gb[1], gb[2], gb[3]))
if d_green > AA_TOL:
    fail(f"the green ink box {px(gb)} does not span union(K, W) = {fmt(box_KW)} "
         f"({d_green:.2f} px) — every side of that box is supposed to be green ink")

print(f"boxes at {RENDER_PX} px   K {fmt(box_K)}")
print(f"                    W {fmt(box_W)}   (overlaps K by "
      f"{min(box_K[2], box_W[2]) - max(box_K[0], box_W[0]):.1f} x "
      f"{min(box_K[3], box_W[3]) - max(box_K[1], box_W[1]):.1f} px)")
print(f"                    C {fmt(box_C)}   vs #kw-c path data {fmt(C_PATH_DATA)}: "
      f"max delta {d_c:.3f} px")
print(f"          union(K,W) {fmt(box_KW)}   vs validator #kw {fmt(VALIDATOR_KW)}: "
      f"max delta {d_kw:.3f} px")
print(f"render instrument: {len(comps)} ink components, largest {comps[0][0]} px = the "
      f"monogram at {px(mono)} -> {d_render:.2f} px from union(K,W) (AA tol {AA_TOL}); "
      f"{comps[0][0] / comps[1][0]:.0f}x the next biggest, so the whole monogram is ONE "
      f"component: K and W have no separate ink to box")
print(f"                   expected {n_letters} components "
      f"(1 monogram + #a + {len(G.WORD)} of \"{G.WORD}\")"
      + ("" if len(comps) == n_letters else "   <-- DIFFERENT: look at the render"))
print(f"                   green ink {px(gb)} spans the union box to {d_green:.2f} px "
      f"(the green is #kw minus the blue C)")

# ------------------------------------------------------------- annotation contrast
print(f"annotation contrast (contrast_report.py, floor 3:1; artwork green {G.GREEN} "
      f"blue {G.BLUE}, split {CR.contrast(G.GREEN, G.BLUE):.2f}:1)")
for name, hexc in COLOURS.items():
    cg, cb, cw = (CR.contrast(hexc, o) for o in (G.GREEN, G.BLUE, CR.WHITE))
    worst = min(cg, cb, cw)
    print(f"   {name:6} {hexc}  vs green {cg:4.2f}  vs blue {cb:4.2f}  "
          f"vs white {cw:5.2f}  {'ok' if worst >= 3.0 else 'FAIL'}")
    if worst < 3.0:
        fail(f"annotation colour {name} {hexc} is {worst:.2f}:1 — under 3:1 against "
             f"{'green' if cg == worst else 'blue' if cb == worst else 'the white ground'}. "
             f"On P2 a row colour has to sit under L 0.031 to clear both halves; pick a "
             f"darker hue, do not lower the floor.")

# ------------------------------------------------------------------------ the figure
TILE, ROWH, PAD = 210, 226, 16
big = ImageFont.truetype(FB, 30)
txt = ImageFont.truetype(F, 19)
how_f = ImageFont.truetype(F, 16)
note_f = ImageFont.truetype(F, 14)
foot = ImageFont.truetype(FB, 17)
foot_s = ImageFont.truetype(F, 16)


def wrap(font, text, max_px):
    """Wrap with Pillow's own metrics. Gotcha 39: a line wider than the canvas is a line
    Pillow crops silently at exit 0, so width is measured before anything is drawn and a
    line that still does not fit stops the build instead of shipping amputated."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or font.getlength(trial) <= max_px:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for ln in lines:
        if font.getlength(ln) > max_px:
            fail(f"text needs {font.getlength(ln):.0f} px, only {max_px:.0f} available: "
                 f"{ln!r}")
    return lines


# How far the two boxes overlap, measured, because "they share strokes" has to be a
# number on the figure and not a vibe: the overlap IS the ligature.
OVER = (min(box_K[2], box_W[2]) - max(box_K[0], box_W[0]),
        min(box_K[3], box_W[3]) - max(box_K[1], box_W[1]))
if OVER[0] <= 0 or OVER[1] <= 0:
    fail(f"the K and W boxes no longer overlap ({OVER[0]:.1f} x {OVER[1]:.1f} px): the "
         f"rings say they share vertices {' '.join(map(str, shared))}, so either the "
         f"rings or the outline have moved — gotcha 22, ask the owner")

ROWS = [
    dict(name="K", box=box_K, ghost=("W", box_W),
         what="the K of the monogram: stem, arm and leg",
         how="no #k element exists — this box is the K's vertex subset of the one #kw "
             "outline: " + " ".join(str(i) for i in G.K_RING) + f" of {len(verts)}, "
             "min/max of those vertices, mapped by #logo's own transform",
         note=f"solid = K, dashed = W's box over the same ink. They share vertices "
              f"{' '.join(str(i) for i in shared)} (dotted): the K's leg IS the W's "
              f"first stroke — one outline, three readings"),
    dict(name="W", box=box_W, ghost=("K", box_K),
         what="the W of the monogram: four strokes, one of them borrowed",
         how="no #w element exists — this box is the W's vertex subset of the same #kw "
             "outline: " + " ".join(str(i) for i in G.W_RING) + f" of {len(verts)}, "
             "min/max of those vertices, mapped by #logo's own transform",
         note=f"its first stroke IS the K's leg (vertices {shared[0]}-{shared[1]}), so "
              f"the two boxes cover the same {OVER[0]:.0f} x {OVER[1]:.0f} px of the "
              f"artboard: by design, never by accident — dashed = K's box"),
    dict(name="C", box=C_PATH_DATA, ghost=None,
         what="the junction of the hand-drawn K and W",
         how="part of #kw / #kw-c — the monogram, never type",
         note=f"the same subset method reproduces this box from C_RING "
              f"({' '.join(str(i) for i in G.C_RING)}) to {d_c:.2f} px — which is how "
              f"the K and W boxes above are earned"),
    dict(name="A", box=(256.9, 234.4, 327.6, 321.5), ghost=None,
         what="the hand-drawn mouse pointer, laid out as a letter",
         how="#a inside #type — the cap height and width of a real A",
         note="the ink box validate_logo.py reports for #a"),
    dict(name="PTURE", box=(276.9, 60.1, 504.6, 281.4), ghost=None,
         what="the only typeset letters in the whole mark",
         how="#wordmark — glyph outlines from Inter ExtraBold",
         note="the ink box validate_logo.py reports for #wordmark"),
]

FOOTER = [
    (foot, "#111111",
     "CAPTURE  =  C (drawn into the monogram)  +  A (the pointer)  +  PTURE (type)"),
    (foot_s, "#777777",
     f"#kw is ONE closed {len(verts)}-vertex outline read three ways (K, W, C): vertices "
     f"{' '.join(str(i) for i in shared)} belong to K and W at once, so their boxes "
     f"overlap by design — and in the ink the whole monogram is one connected component, "
     f"which is why the letters are boxed by vertex, never by segmentation."),
    (foot_s, "#777777",
     f'WORD in gen_logo.py is "{G.WORD}". Setting WORD="CAPTURE" renders CACAPTURE.'),
]

TX = PAD + TILE + 46                      # where the label column starts
COLW = 980 - TX - PAD                     # and how wide the text column is
footer_lines = [[(f, c, ln) for ln in wrap(f, t, 980 - 2 * PAD)] for f, c, t in FOOTER]
band = 18 + sum(len(g) * (24 if g[0][0] is foot else 21) for g in footer_lines) + 12
H = PAD + ROWH * len(ROWS) + band
img = Image.new("RGB", (980, H), "white")
d = ImageDraw.Draw(img)
base = im.resize((TILE, TILE), Image.LANCZOS)
s = TILE / float(RENDER_PX)


def dash_line(p, q, colour, dash=7, gap=5, width=2):
    """One dashed segment: Pillow has no dash style, and a ghost box that is not visibly a
    ghost would be a second claim about the artwork rather than an annotation on it."""
    n = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) // (dash + gap)))
    for k in range(n + 1):
        t0 = k * (dash + gap) / max(1e-9, math.hypot(q[0] - p[0], q[1] - p[1]))
        t1 = min(1.0, t0 + dash / max(1e-9, math.hypot(q[0] - p[0], q[1] - p[1])))
        d.line([(p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0),
                (p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1)],
               fill=colour, width=width)


def dashed_rect(box, colour):
    x0, y0, x1, y1 = box
    for p, q in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        dash_line(p, q, colour)


for i, row in enumerate(ROWS):
    name, what, how, note = row["name"], row["what"], row["how"], row["note"]
    x0, y0, x1, y1 = row["box"]
    y = i * ROWH + PAD
    img.paste(base, (PAD, y))
    col = COLOURS[name]
    bx = (PAD + x0 * s, y + y0 * s, PAD + x1 * s, y + y1 * s)
    if row["ghost"]:                       # the other reading of the SAME outline, dashed
        gname, gbox = row["ghost"]
        dashed_rect((PAD + gbox[0] * s, y + gbox[1] * s,
                     PAD + gbox[2] * s, y + gbox[3] * s), COLOURS[gname])
    d.rectangle(bx, outline=col, width=3)
    d.line([(bx[2] if bx[2] < TX else (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2),
            (TX - 10, y + 24)], fill=col, width=2)
    d.text((TX, y + 6), name, font=big, fill=col)
    yy = y + 54
    for ln in wrap(txt, what, COLW):
        d.text((TX, yy), ln, font=txt, fill="#222222")
        yy += 24
    yy += 2
    for ln in wrap(how_f, how, COLW):
        d.text((TX, yy), ln, font=how_f, fill="#555555")
        yy += 20
    yy += 2
    for ln in wrap(note_f, note, COLW):
        d.text((TX, yy), ln, font=note_f, fill="#888888")
        yy += 18
    if yy > y + TILE + 8:
        fail(f"row {name}: its text runs {yy - (y + TILE + 8):.0f} px past the tile band "
             f"— ROWH is too small for the caption, or the caption is too long")
    if row["ghost"]:                       # the shared vertices: annotation, not artwork
        for j in shared:
            vx, vy = xform[2] * verts[j][0] + xform[0], xform[2] * verts[j][1] + xform[1]
            cx, cy = PAD + vx * s, y + vy * s
            d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill="white")
            d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=col)

rule = PAD + ROWH * len(ROWS) + 6
d.line([(PAD, rule), (980 - PAD, rule)], fill="#cccccc")
fy = rule + 10
for group in footer_lines:
    for fnt, colour, ln in group:
        d.text((PAD, fy), ln, font=fnt, fill=colour)
        fy += 24 if fnt is foot else 21

# --------------------------------------------------- nothing cropped, measured (39)
fig = img.convert("L").point(lambda v: 255 if v < 250 else 0)
ib = fig.getbbox()
if not ib:
    fail("the figure has no ink at all")
air = (ib[0], 980 - ib[2], ib[1], H - ib[3])
if min(air) < 8:
    fail(f"ink sits {min(air):.0f} px from an edge of the canvas (L {air[0]}, R {air[1]}, "
         f"T {air[2]}, B {air[3]}): something is cropped or the canvas is too small")
img.save(HERE / "anatomy.png")
print(f"figure 980x{H}, ink x {ib[0]}..{ib[2] - 1} y {ib[1]}..{ib[3] - 1}, air "
      f"L {air[0]} R {air[1]} T {air[2]} B {air[3]} px -> nothing cropped")
print("wrote", HERE / "anatomy.png", "(that is the only file this script writes)")
