#!/usr/bin/env python3
"""Regenerate logo/kwcapture.svg from the hand-drawn sketch.

    python3 logo/gen_logo.py                       # writes logo/kwcapture.svg
    python3 logo/gen_logo.py --out /tmp/x.svg --a-size 1.15 --word PTURE
    python3 logo/gen_logo.py --help

THE ONE THING TO UNDERSTAND BEFORE TOUCHING THIS FILE
-----------------------------------------------------
The wordmark is *not* "CAPTURE".  The mark spells CAPTURE out of three parts:

    C  <-  the junction of the hand-drawn K and W  (#kw, part of the monogram)
    A  <-  the hand-drawn mouse pointer            (#a, laid out as a letter)
    PTURE  <-  the only typeset letters            (#wordmark)

So WORD is "PTURE".  Setting WORD="CAPTURE" produces "CACAPTURE".  See
logo/AGENTS.md for the full story.

Design decisions worth keeping (all are CLI knobs, so they can be argued with):
  * the wordmark is emitted as glyph OUTLINES, never a <text> element, so the
    logo renders the same on machines that do not have the font installed;
  * the pointer keeps the angle it was drawn at: its tip axis is within ~6 deg
    of perpendicular to the slanted baseline, which is what makes it read as an
    upright A. --a-upright snaps it exactly perpendicular and it then reads as
    an arrow, not a letter -- don't;
  * the pointer is sized 1.30x cap height and stands ON the baseline, because
    in the sketch the arrow was bigger and heavier than the drawn letters.
"""
import argparse
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = Path(__file__).resolve().parent
SKETCH = HERE / "kwcapture-sketch.svg"      # the hand-drawn source, never written to
DEFAULT_OUT = HERE / "kwcapture.svg"

NS = "{http://www.w3.org/2000/svg}"

# --------------------------------------------------------------- design knobs
CANVAS = 512.0        # square artboard, px
PAD = 44.0            # padding on the constrained axis, px
ANGLE = -38.0         # wordmark baseline tilt, deg; negative rises to the right
CAP = 3.30            # wordmark cap height, mm (the drawn letters were ~3.4mm)
TRACK = 0.10          # letter-spacing, em
WORD = "PTURE"        # ONLY the letters that are not already drawn in the mark!
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"   # ExtraBold matches the
                      # very heavy monogram; Inter Bold looked thin next to it
# Colour: two families, and they carry meaning.  GREEN = the monogram half (the K's stem
# and the W).  BLUE = the word half: the C that the junction forms, the pointer-A, and
# PTURE.  Before 2026-10-10 the monogram was a blue-to-green gradient and the type was
# black; --classic reproduces that exactly.
DARK = "#000000"        # --classic type colour only
# PALETTE P2, the owner's decision of 2026-10-11, applied 2026-10-11 (was #00ac4e/#0000ff).
# Every number in these two comments is WCAG relative luminance against the two grounds a
# reader actually meets -- white and GitHub dark #0d1117 -- and every one of them is printed
# by `python3 logo/contrast_report.py`, which reads the constants below.  Do not hand-edit a
# ratio here: re-run that and copy what it says.
GREEN = "#008c46"       # the W's green, and the K's stem.  4.34 on white, 4.36 on #0d1117:
                        # the balanced green of the four measured (4.34/4.36; #00ac4e was
                        # 3.00/6.32 and failed white by a hair, #007a3d 5.45/3.47 reads as
                        # forest, #007038 6.22/3.04 is the last green that clears dark).
                        # It is no longer "the old gradient's end stop": P2 is a palette,
                        # not a gradient, and the old stops live in --classic.
BLUE = "#7f7fff"        # the C, the A, the letters.  3.29 on white, 5.75 on #0d1117 -- the
                        # only single value measured that clears the 3:1 non-text floor on
                        # BOTH grounds, which is why the palette changed: the #0000ff it
                        # replaced was 8.59 on white but 2.20 on dark, and dark is where
                        # GitHub and every terminal theme live.
                        # What P2 costs, stated so nobody rediscovers it: the two halves are
                        # now only 1.32:1 apart in LIGHTNESS (the old pair was 2.87).  The
                        # C still separates from the W because it differs in HUE -- 240 deg
                        # against the green's 150 -- not in value.  Two halves that are both
                        # legal on both grounds must both sit in the luminance window
                        # [0.1164, 0.3000], and inside that window 2.10:1 is the loudest
                        # separation arithmetic allows; #3b82f6, the friendlier blue, is
                        # 5.15 on dark but 1.18 from this green, and the C would dissolve
                        # into the W.  Same instrument, `contrast_report.py`.
C_PAINT = "solid"     # how the blue C is cut out: solid | mask | clip. Chosen by the
                      # RENDERER MATRIX, not by taste (validate_logo.py re-runs it):
                      #   clip  -- what shipped until 2026-10-10. QtSvg IGNORES clip-path
                      #          (Qt 6.10.2 drops even a <circle> clip), so Gwenview and
                      #          Dolphin's thumbnails painted the monogram 100% blue.
                      #   mask  -- fixes Qt, but ImageMagick's internal MSVG treats an
                      #          unsupported mask as "hide everything": the C vanished
                      #          (0% blue). So a mask is not the safe choice either.
                      #   solid -- the C ring as its own path: uses no cut-out feature at
                      #          all, so there is nothing left for a renderer to ignore.
                      #          Correct in Inkscape, QtSvg and MSVG. See kw_paint().
MASK_PAD = 1.0        # mm of margin on the mask region, so no antialiased edge of the
                      # monogram falls outside it and gets eaten
A_SIZE = 1.00         # pointer-as-"A" height, x cap height. 1.00 = exactly the P's
                      # height (measured perpendicular to the slanted baseline, which is
                      # the only way height means anything on rotated text). It was 1.30
                      # to echo the sketch, where the arrow dwarfed the letters, but that
                      # made the mark read "big C, medium A, small PTURE"; the design
                      # wants ONE big letter (the C in the KW junction) and one
                      # evenly-set word, APTURE. Do not make the A big again.
A_GAP = 0.70          # space between the "A" pointer and the P, mm. 0.90 read as a word
                      # break once the A shrank; 0.70 keeps APTURE reading as one word
A_WIDTH = 1.00          # A width as a multiple of the ink width of a real capital "A"
                      # in the same face at the same cap height (Inter ExtraBold:
                      # 0.995 x cap). The pointer is stretched ALONG THE BASELINE to
                      # hit it: height stays exactly cap. 1.0 -> 3.28mm wide.
                      # Uniform scaling had made the A 0.71 of a real A: a skinny,
                      # condensed A next to fat ExtraBold letters
ANCHOR = (73.4, 112.6)   # baseline start of WORD, in the sketch's mm space
ALIGN_TOP = True      # level the cap-top of the word with the top of the K
MAX_STRETCH = 2.0     # --mark: ceiling on the height fill, x the fitted cap height. A
                      # taste guard, not geometry: the shipped box wants 1.753 and is not
                      # stopped. It exists because the box is the owner's drawing, so next
                      # week it may be twice as tall, and Inter at x3 is a cage of vertical
                      # strokes rather than a word. Lower it to taste; 0 = no height fill.


# -------------------------------------------------------------- path helpers
def read_source(sketch=SKETCH):
    tree = ET.parse(str(sketch))
    return {p.get("id"): p.get("d") for p in tree.iter(NS + "path")}


def poly_vertices(d):
    """The corner points of a path in order, WITHOUT densification (M/L/Z only).
    The C split needs the drawing's real vertices by index, not samples along them; a
    path with curves will not line up, and c_clip_polygon says so rather than guessing."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:e-?-?\d+)?", d)
    pts, cmd, i, cx, cy, start = [], None, 0, 0.0, 0.0, None
    while i < len(toks):
        t = toks[i]
        if t[0].isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                cx, cy = start
            continue
        n = {"M": 2, "m": 2, "L": 2, "l": 2, "H": 1, "h": 1, "V": 1, "v": 1,
             "C": 6, "c": 6, "Q": 4, "q": 4}[cmd]
        a = [float(x) for x in toks[i:i + n]]
        i += n
        ox, oy = (cx, cy) if cmd.islower() else (0.0, 0.0)
        if cmd.upper() in ("M", "L"):
            cx, cy = ox + a[0], oy + a[1]
            if cmd.upper() == "M":
                start = (cx, cy)
            pts.append((cx, cy))
    return pts


def parse_points(d):
    """Sample a path 'd' into on-curve points, densifying straight runs."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pts, i, cmd = [], 0, None
    cx = cy = sx = sy = 0.0
    while i < len(toks):
        t = toks[i]
        if t[0].isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                pts.append((cx, cy))
                cx, cy = sx, sy
            continue
        n = {"M": 2, "m": 2, "L": 2, "l": 2, "H": 1, "h": 1, "V": 1, "v": 1,
             "C": 6, "c": 6, "Q": 4, "q": 4}[cmd]
        a = [float(x) for x in toks[i:i + n]]
        i += n
        rel = cmd.islower()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        C = cmd.upper()
        if C == "M":
            cx, cy = ox + a[0], oy + a[1]
            sx, sy = cx, cy
            pts.append((cx, cy))
            cmd = "l" if rel else "L"
        elif C == "L":
            px, py = cx, cy
            cx, cy = ox + a[0], oy + a[1]
            steps = max(1, int(math.hypot(cx - px, cy - py) / 0.12))
            for k in range(1, steps + 1):
                pts.append((px + (cx - px) * k / steps, py + (cy - py) * k / steps))
        elif C == "H":
            cx = ox + a[0]
            pts.append((cx, cy))
        elif C == "V":
            cy = oy + a[0]
            pts.append((cx, cy))
        elif C == "C":
            p0, p3 = (cx, cy), (ox + a[4], oy + a[5])
            p1, p2 = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            for k in range(1, 41):
                t, m = k / 40, 1 - k / 40
                pts.append((m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0],
                            m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]))
            cx, cy = p3
        elif C == "Q":
            p0, p3 = (cx, cy), (ox + a[2], oy + a[3])
            p1 = (ox + a[0], oy + a[1])
            for k in range(1, 41):
                t, m = k / 40, 1 - k / 40
                pts.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p3[0],
                            m * m * p0[1] + 2 * m * t * p1[1] + t * t * p3[1]))
            cx, cy = p3
    return pts


def bbox(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def round_d(d, nd=3):
    return re.sub(r"-?\d+\.\d+",
                  lambda m: f"{float(m.group(0)):.{nd}f}".rstrip("0").rstrip("."), d)


def f(n):
    s = f"{n:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def write_svg(path, svg):
    """Refuse to emit a comment containing '--', which is illegal in XML. This has
    bitten the generator twice (a comment mentioning a flag name); it should never
    reach xmllint, let alone a browser."""
    for m in re.finditer(r"<!--(.*?)-->", svg, re.S):
        if "--" in m.group(1):
            bad = [ln.strip() for ln in m.group(1).splitlines() if "--" in ln]
            raise SystemExit(f"illegal '--' inside XML comment: {bad}")
    Path(path).write_text(svg)


def rot(deg):
    a = math.radians(deg)
    return math.cos(a), math.sin(a)


# ------------------------------------------------------------------- wordmark
_FONTS = {}


def load_font(path):
    """Open each font file ONCE and share it.

    mark mode opens the same OTF a hundred-plus times while bisecting cap height, and
    re-running TTFont()+getBestCmap() on the same file made fontTools' lazy cmap subtable
    sharing die with "'int' object is not iterable". Load once, share forever."""
    key = str(path)
    if key not in _FONTS:
        font = TTFont(key)
        cap_u = getattr(font["OS/2"], "sCapHeight", 0) or int(font["hhea"].ascent * 0.7)
        # The TTFont is cached (that part of the old bug was real: a second TTFont() on the
        # same file died in fontTools' lazy cmap subtable), but the GLYPHSET deliberately is
        # NOT. Sharing one glyphset across every Wordmark corrupts state inside fontTools'
        # CFF extractor, and it shows up as random, impossible TypeErrors ~1-3% of --mark
        # builds: 'str' object is not callable (svgPathPen._ntos), 'T2OutlineExtractor'
        # object is not subscriptable, unsupported operand * float and Wordmark, compile()
        # arg 1 must be a string. Measured 2026-10-10: 2/60 builds with a shared glyphset,
        # 0/60 with one per Wordmark. Each Wordmark now asks for its own; the font stays
        # open, so the cost is a dict of glyph proxies, not a file read.
        _FONTS[key] = dict(font=font, glyphset=None,
                           cmap=font.getBestCmap(), cap_u=cap_u)
    return _FONTS[key]


class Wordmark:
    """Glyph outlines laid out on a horizontal baseline, in mm, y down, origin =
    baseline start. Rotation/position are applied by the emitted <g>."""

    def __init__(self, font_path, word, cap, track):
        self.path, self.cap = font_path, cap
        f = load_font(font_path)
        self.glyphset = f["font"].getGlyphSet()   # NOT shared: see load_font()
        cmap = f["cmap"]
        # sCapHeight, not ascent: we want caps to sit on the cap band
        self.k = cap / f["cap_u"]
        self.track = track * cap / f["cap_u"]
        self.chars = [cmap.get(ord(c)) for c in word]
        if any(g is None for g in self.chars):
            raise SystemExit(f"font is missing a glyph for {word!r}")
        self._build()

    def _build(self):
        pen_x, d, pts = 0.0, [], []
        for g in self.chars:
            svg = SVGPathPen(self.glyphset)
            # (k,0,0,-k,...) also flips y: font units are y-up, SVG is y-down
            self.glyphset[g].draw(TransformPen(svg, (self.k, 0, 0, -self.k, pen_x, 0)))
            d.append(svg.getCommands())
            rec = RecordingPen()
            self.glyphset[g].draw(rec)
            pts += self._sample(rec, pen_x)
            pen_x += self.glyphset[g].width * self.k + self.track
        self.d = round_d(" ".join(x for x in d if x))
        self.width = pen_x - self.track
        self.local_pts = pts

    def _sample(self, rec, ox):
        """Outline points in mm (for bounding boxes / clearance maths)."""
        k = self.k
        out, cx, cy = [], 0.0, 0.0
        for op, args in rec.value:
            if op in ("moveTo", "lineTo"):
                cx, cy = args[0]
                out.append((cx * k + ox, -cy * k))
            elif op == "qCurveTo":
                p0, ctrl = (cx, cy), list(args)
                end = ctrl[-1]
                segs = []
                if len(ctrl) == 2:
                    segs.append((p0, ctrl[0], end))
                else:                      # TrueType run of off-curve points
                    prev = p0
                    for j in range(len(ctrl) - 1):
                        c, nxt = ctrl[j], ctrl[j + 1]
                        if j == len(ctrl) - 2:
                            segs.append((prev, c, nxt))
                        else:
                            mid = ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
                            segs.append((prev, c, mid))
                            prev = mid
                for a, b, c in segs:
                    for s in range(1, 41):
                        t, m = s / 40, 1 - s / 40
                        out.append(((m * m * a[0] + 2 * m * t * b[0] + t * t * c[0]) * k + ox,
                                    -(m * m * a[1] + 2 * m * t * b[1] + t * t * c[1]) * k))
                cx, cy = end
            elif op == "curveTo":
                p0, p1, p2, p3 = (cx, cy), args[0], args[1], args[2]
                for s in range(1, 41):
                    t, m = s / 40, 1 - s / 40
                    out.append(((m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0]) * k + ox,
                                -(m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]) * k))
                cx, cy = p3
        return out

    def placed_points(self, px, py, angle_deg):
        ca, sa = rot(angle_deg)
        return [(x * ca - y * sa + px, x * sa + y * ca + py) for x, y in self.local_pts]

    def ink_width(self, ch):
        """Ink width of one cap, in mm, at this wordmark's cap height. That is what
        'a capital A is this wide' means for the face in use."""
        one = Wordmark(self.path, ch, self.cap, 0.0)
        xs = [x for x, _ in one.local_pts]
        return max(xs) - min(xs)


# ------------------------------------------------- the pointer, as the letter A
def mm2(A, B):
    """2x2 multiply."""
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2))
                 for i in range(2))


def place_A(cursor_d, anchor, angle, cap, gap, size_mult, upright,
            ref_width=None, a_width=1.0):
    """Fit the drawn pointer into the 'A' slot: cap-band height, standing on the
    baseline, `gap` before the first typeset letter. Returns (transform, points).

    The pointer's own tip axis is already ~6 deg off perpendicular to the
    baseline, so by default it is NOT rotated -- only scaled and shifted."""
    pts = parse_points(cursor_d)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    ca, sa = rot(angle)
    dirv = (ca, sa)                       # along the baseline, reading way
    perpv = (-sa, ca)                     # 90 deg CCW on screen = below baseline
    tip = pts[0]

    extra_rot = 0.0
    if upright:
        ax = math.degrees(math.atan2(tip[1] - cy, tip[0] - cx))   # tail -> tip axis
        up = math.degrees(math.atan2(-perpv[1], -perpv[0]))       # "up" in the word frame
        extra_rot = up - ax

    def frame(p):                         # (u along baseline, v below baseline)
        dx, dy = p[0] - anchor[0], p[1] - anchor[1]
        return dx * dirv[0] + dy * dirv[1], dx * perpv[0] + dy * perpv[1]

    # HEIGHT is measured PERPENDICULAR TO THE BASELINE (perpv) and WIDTH ALONG IT
    # (dirv) -- the only senses in which rotated text has either. An earlier version
    # mixed dirv/perpv components and measured perpendicular to +38 deg instead of
    # -38 deg, so A_SIZE=1.00 rendered the A at 1.41x cap. validate_logo.py now
    # measures height AND width out of the emitted SVG.
    def in_frame(p):                      # coords relative to the pointer centroid
        dx, dy = p[0] - cx, p[1] - cy
        if extra_rot:
            cr, sr = rot(extra_rot)
            dx, dy = dx * cr - dy * sr, dx * sr + dy * cr
        return (dx * dirv[0] + dy * dirv[1],        # u: along the baseline
                dx * perpv[0] + dy * perpv[1])      # v: below the baseline

    fr = [in_frame(p) for p in pts]
    cs = (size_mult * cap) / (max(v for _, v in fr) - min(v for _, v in fr))
    # A capital A is about as WIDE as it is tall (Inter ExtraBold ink: 0.995 x cap).
    # Scaling the arrow uniformly to cap height gave 0.73 x cap: a skinny condensed A
    # next to fat ExtraBold letters. The sketch's arrow had the right WIDTH and too
    # much height, so stretch ALONG THE BASELINE ONLY -- height stays exactly cap.
    wu = max(u for u, _ in fr) - min(u for u, _ in fr)
    # u_final = su*cs*u_orig, so the target width has to be divided by cs as well
    # (dividing only by wu silently cancelled most of the stretch -- the width check
    # in validate_logo.py is what caught that).
    su = (ref_width * a_width / (cs * wu)) if ref_width else 1.0

    # world -> frame (F), stretch (D), frame -> world (Finv = F transposed); F is
    # orthonormal, so this is a clean anisotropic scale in the baseline's own axes.
    F = ((dirv[0], dirv[1]), (perpv[0], perpv[1]))
    Finv = ((dirv[0], perpv[0]), (dirv[1], perpv[1]))
    D = ((su * cs, 0.0), (0.0, cs))
    R2 = ((1.0, 0.0), (0.0, 1.0))
    if extra_rot:
        cr, sr = rot(extra_rot)
        R2 = ((cr, -sr), (sr, cr))
    M = mm2(Finv, mm2(D, mm2(F, R2)))

    sp = [(cx + M[0][0] * (p[0] - cx) + M[0][1] * (p[1] - cy),
           cy + M[1][0] * (p[0] - cx) + M[1][1] * (p[1] - cy)) for p in pts]
    us = [frame(p)[0] for p in sp]
    vs = [frame(p)[1] for p in sp]
    du = -gap - max(us)                   # trailing edge `gap` before the word
    dv = 0.0 - max(vs)                    # bottom of the pointer on the baseline
    dx = du * dirv[0] + dv * perpv[0]
    dy = du * dirv[1] + dv * perpv[1]
    placed = [(p[0] + dx, p[1] + dy) for p in sp]
    # p' = M.p + (cc - M.cc + delta), emitted as one SVG matrix(a b c d e f)
    me = cx - (M[0][0] * cx + M[0][1] * cy) + dx
    mf = cy - (M[1][0] * cx + M[1][1] * cy) + dy
    tf = (f"matrix({f(M[0][0])} {f(M[1][0])} {f(M[0][1])} {f(M[1][1])}"
          f" {f(me)} {f(mf)})")
    return tf, placed


# --------------------------------------------------------- the helper box mode
# kwcapture-mark-sketch.svg is drawn in Inkscape: a monogram plus a black
# four-corner box. The box says "put APTURE here, along this edge, this big". It is a
# GUIDE, never part of the render: gen_logo.py reads its base angle, its length and its
# height, sizes the word to fill it, and drops the box.

MARK_SKETCH = HERE / "kwcapture-mark-sketch.svg"
A_GAP_RATIO = A_GAP / CAP        # the A->P gap travels with the type size


def parse_transform(s):
    """'translate(a b) scale(c) ...' -> affine (a,b,c,d,e,f), SVG convention."""
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for fn, args in re.findall(r"(\w+)\(([^)]*)\)", s or ""):
        v = [float(x) for x in re.split(r"[ ,]+", args.strip())]
        if fn == "translate":
            n = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
        elif fn == "scale":
            n = (v[0], 0.0, 0.0, v[1] if len(v) > 1 else v[0], 0.0, 0.0)
        elif fn == "matrix":
            n = tuple(v[:6])
        elif fn == "rotate":
            ca, sa = rot(v[0])
            if len(v) == 3:
                n = (ca, sa, -sa, ca,
                     v[1] - (ca * v[1] - sa * v[2]), v[2] - (sa * v[1] + ca * v[2]))
            else:
                n = (ca, sa, -sa, ca, 0.0, 0.0)
        else:
            raise SystemExit(f"parse_transform: unsupported {fn}()")
        a1, b1, c1, d1, e1, f1 = m
        a2, b2, c2, d2, e2, f2 = n
        m = (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2,
             b1 * c2 + d1 * d2, a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)
    return m


def apply_m(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def inv_m(m):
    a, b, c, d, e, f = m
    det = a * d - b * c
    if not det:
        raise SystemExit("inv_m: singular transform")
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def walk_paths(root):
    """(element, absolute matrix) for every <path>, honouring ancestor transforms."""
    out = []

    def rec(el, m):
        for ch in el:
            cm = parse_transform(ch.get("transform")) if ch.get("transform") else m
            if ch.tag == NS + "path":
                out.append((ch, cm))
            elif ch.tag == NS + "g":
                rec(ch, cm)
    rec(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return out


def convex_hull(points, tol=None):
    """Monotone-chain hull. `tol` is an AREA tolerance (not a distance), and it must
    scale with the shape: path sampling jitters by ~1e-13 but rounding the input for
    dedup jitters by ~1e-6, and against a 300-unit lever arm that is a 1e-4 cross
    product -- a fixed 1e-9 epsilon kept 24 of them and the box never read as a
    quadrilateral. Corners of a real shape are orders of magnitude above this."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    if tol is None:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
        tol = 1e-9 * span * span

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= tol:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= tol:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def is_parallelogram(h, ang_tol=3.0, len_tol=0.08):
    if len(h) != 4:
        return False
    e = [(h[(i + 1) % 4][0] - h[i][0], h[(i + 1) % 4][1] - h[i][1]) for i in range(4)]
    L = [math.hypot(*v) for v in e]
    if min(L) < 1e-6:
        return False
    for i in range(2):
        j = i + 2
        if abs(L[i] - L[j]) / max(L[i], L[j]) > len_tol:
            return False
        a1 = math.degrees(math.atan2(e[i][1], e[i][0]))
        a2 = math.degrees(math.atan2(e[j][1], e[j][0]))
        delta = (a1 - a2 + 180) % 360 - 180
        # walking a closed polygon, opposite edges run ANTIparallel, so the angle
        # between them must be ~180 deg (a first version compared them as ~0 and
        # rejected every real box)
        if abs(180.0 - abs(delta)) > ang_tol:
            return False
    return True


def find_box(root, box_id=None):
    """The helper box: the path whose outline is a parallelogram. In Inkscape, name its
    id 'fit-box' to be explicit; otherwise the unique parallelogram wins."""
    cands = []
    for el, m in walk_paths(root):
        hull = convex_hull([apply_m(m, p) for p in parse_points(el.get("d"))])
        if is_parallelogram(hull):
            cands.append((el.get("id"), hull))
    if not cands:
        raise SystemExit("no helper box found: draw a 4-corner parallelogram "
                         "(id 'fit-box' recommended)")
    if box_id:
        for i, h in cands:
            if i == box_id:
                return h
        raise SystemExit(f"--box {box_id!r} not among {[i for i, _ in cands]}")
    if len(cands) > 1:
        raise SystemExit(f"ambiguous helper box: {[i for i, _ in cands]} "
                         f"- name the one you mean with --box ID")
    return cands[0][1]


def halfplanes(poly):
    """Inward unit normals of a convex polygon: a point is inside iff n . p >= c for every
    (n, c) returned. Unit length, so c is a real distance and a clearance can be subtracted
    from it. Used instead of (length, height) because the helper box is NOT a rectangle --
    see the height-fill comment in build_mark()."""
    q = np.asarray(poly, float)
    cen = q.mean(axis=0)
    out = []
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        n = np.array((b[1] - a[1], a[0] - b[0]))          # perpendicular to the edge
        if n @ (cen - a) < 0:
            n = -n                                        # point inward
        n = n / np.hypot(n[0], n[1])
        out.append((n, float(n @ a)))
    return out


def box_frame(hull):
    """Base = the LOWER long edge, read left to right. Returns origin (base start),
    unit dir, unit up, angle deg, length, height -- in whatever units the hull is in."""
    edges = [(hull[i], hull[(i + 1) % 4]) for i in range(4)]
    edges.sort(key=lambda ab: math.hypot(ab[1][0] - ab[0][0], ab[1][1] - ab[0][1]),
               reverse=True)
    longs = edges[:2]
    orients = []
    for a, b in longs:
        if b[0] - a[0] < 0:
            a, b = b, a
        orients.append((a, b))
    base = max(orients, key=lambda ab: (ab[0][1] + ab[1][1]) / 2)   # lower on screen
    (ox, oy), (bx, by) = base
    L = math.hypot(bx - ox, by - oy)
    dirv = ((bx - ox) / L, (by - oy) / L)
    upv = (dirv[1], -dirv[0])                       # 90 deg CW on screen = up
    other = [ab for ab in orients if ab != base][0]
    mid_o = ((other[0][0] + other[1][0]) / 2, (other[0][1] + other[1][1]) / 2)
    H = (mid_o[0] - (ox + bx) / 2) * upv[0] + (mid_o[1] - (oy + by) / 2) * upv[1]
    return dict(origin=base[0], dir=dirv, up=upv, angle=math.degrees(
        math.atan2(dirv[1], dirv[0])), length=L, height=abs(H))


def build_mark(sketch=MARK_SKETCH, font=FONT, word=WORD, track=TRACK, canvas=CANVAS,
               a_size=A_SIZE, a_width=A_WIDTH, a_gap_ratio=A_GAP_RATIO, inset=0.0,
               align="auto", along="auto", box_id=None, min_clear=0.50,
               recenter=True, out=None,
               green=GREEN, blue=BLUE, gradient=False, split_c=True,
               height_fill=True, max_stretch=MAX_STRETCH, c_paint=C_PAINT):
    """Monogram + A + PTURE, the word fitted inside the helper box, box removed."""
    root = ET.parse(str(sketch)).getroot()
    grp = root.find(f"{NS}g")
    if grp is None:
        raise SystemExit(f"{sketch}: expected the monogram inside <g id='logo'>")
    logo_tf = grp.get("transform") or ""
    m_logo = parse_transform(logo_tf)
    kw_el = grp.find(f"{NS}path")
    kw_d, kw_id = kw_el.get("d"), kw_el.get("id") or "kw"
    grad = root.find(f"{NS}defs/{NS}linearGradient")
    gx1, gy1 = grad.get("x1"), grad.get("y1")
    gx2, gy2 = grad.get("x2"), grad.get("y2")
    stops = [(s.get("offset"), s.get("stop-color"))
             for s in grad.iter(NS + "stop")]

    box_mm = [apply_m(inv_m(m_logo), p) for p in find_box(root, box_id)]
    fr = box_frame(box_mm)

    # u runs ALONG the box's base, t ACROSS it -- the box's own frame. Everything about the
    # type is measured in it, so nothing has to un-rotate anything later. The box goes in as
    # four HALF-PLANES rather than as (length, height), because the box is four mouse
    # clicks: on the shipped one the long edges are 0.63 deg off parallel (the headroom over
    # the base falls 7.920 -> 7.651 mm along the length) and the left edge leans inward by
    # 0.18 deg. (length, height) is the box's AVERAGE, and a type fitted to the average of a
    # non-rectangle hangs outside it -- see the height fill below and gotcha 23.
    ang = fr["angle"]
    ox, oy = fr["origin"]
    dv, uv = fr["dir"], fr["up"]
    O, U, D = np.array((ox, oy)), np.array(uv), np.array(dv)
    px = m_logo[0]                        # px per mm: for talking to the validator's px
    quad = np.array([[(np.asarray(p) - O) @ D, (np.asarray(p) - O) @ U] for p in box_mm])
    HP = halfplanes(quad)                 # inside == n . (u, t) >= c, every edge, |n| = 1
    BOX_TOL = 1.0 / px                    # the validator's 1 px, in mm
    FIT_TOL = 0.25 / px                   # what a PLACEMENT is held to (see fits())

    def ink_violation(pts):
        """How far (mm) this ink pokes OUT of the drawn box; 0.0 when it is inside.
        'Inside' has to mean the quad, not (length, height), and it has to be measured on
        the INK: Inter overshoots its own cap line, so a word placed with `top` alignment
        spills 1.6 px over a top edge that the nominal cap height says it is clear of."""
        q = np.asarray(pts, float)
        u, t = (q - O) @ D, (q - O) @ U
        return max([float((c - (u * n[0] + t * n[1])).max()) for n, c in HP] + [0.0])

    # how far from a rectangle is the box the owner drew? Reported, because it decides the
    # answer and it is invisible in a render.
    top = sorted((v for v in quad if v[1] > 0.5 * fr["height"]), key=lambda v: float(v[0]))
    if len(top) > 1:
        t_top_near, t_top_far = float(top[0][1]), float(top[-1][1])
        top_skew = math.degrees(math.atan2(t_top_far - t_top_near,
                                           float(top[-1][0] - top[0][0])))
    else:                                        # degenerate box: no top edge to lean
        t_top_near = t_top_far = float(top[0][1])
        top_skew = 0.0

    # how wide is "A + PTURE" per unit of cap height? (it all scales linearly)
    wm_ref = Wordmark(font, word, CAP, track)
    per_cap = (wm_ref.ink_width("A") + a_gap_ratio * CAP + wm_ref.width) / CAP
    cap_box = min((fr["length"] - 2 * inset) / per_cap, fr["height"] - 2 * inset)

    cursor_d = read_source()["path10"]      # the A always comes from the original sketch
    kw_pts = np.array(parse_points(kw_d))

    def layout(c, place=("center", "center")):
        """place A + word for cap height c at a (across, along) position in the box"""
        across, along = place
        total = c * per_cap
        u_along = {"center": (fr["length"] - total) / 2,
                   "start": inset,
                   "end": fr["length"] - total - inset}[along]
        u_across = {"center": (fr["height"] - c) / 2,
                    "base": inset,
                    "top": fr["height"] - c - inset}[across]
        ox, oy = fr["origin"]
        dv, uv = fr["dir"], fr["up"]
        # `anc` is the LEFT EDGE OF THE WHOLE WORD. place_A() parks the A *behind* its
        # anchor (trailing edge at -gap), so the anchor handed to it -- and to PTURE --
        # must be a_w + gap further along the baseline. Get this wrong and the A hangs
        # outside the box's near end while PTURE falls short of the far one (that was
        # the shipped bug), or the word splits in half (the first attempted fix).
        anc = (ox + dv[0] * u_along + uv[0] * u_across,
               oy + dv[1] * u_along + uv[1] * u_across)
        a_w = Wordmark(font, "A", c, 0.0).ink_width("A") * a_width
        g0 = c * a_gap_ratio
        word_anc = (anc[0] + dv[0] * (a_w + g0), anc[1] + dv[1] * (a_w + g0))
        # the target width for the A must be measured AT THIS cap height, not at CAP
        tf, ap = place_A(cursor_d, word_anc, fr["angle"], c, g0, a_size, False,
                         ref_width=Wordmark(font, "A", c, 0.0).ink_width("A"),
                         a_width=a_width)
        return tf, ap, Wordmark(font, word, c, track), anc, word_anc

    def gap_of(ap, wmk, anc):
        """closest ink distance from the word (incl. the A) to the monogram, in mm."""
        pts = np.array(ap + wmk.placed_points(anc[0], anc[1], fr["angle"]))
        d2 = ((kw_pts[:, None, 0] - pts[None, :, 0]) ** 2 +
              (kw_pts[:, None, 1] - pts[None, :, 1]) ** 2)
        return float(np.sqrt(d2.min()))

    # "as large as possible" = fill the box, but never at the price of touching the
    # monogram. The sketched box grazes the W's middle peak, so bisect on cap height:
    # smaller type sits further from the monogram (it is centred in the box), so
    # "clears by min_clear" is monotone in cap and a plain bisection is exact enough.
    # (A naive cap *= g/min_clear update was tried first: it ran away to 0.14 mm.)
    # Both halves of the contract are tested here: inside the box AND clear of the
    # monogram. Before the box went in as half-planes, only the clearance was tested and
    # `--min-clear 0.9` onward bought its clearance by moving the word to the top edge,
    # 1.6 px outside the box -- a COLLISION-free way to leave the box. The box check in
    # validate_logo.py was reporting exactly that.
    # FIT_TOL, not BOX_TOL: the fit is held to a quarter of the px the validator forgives,
    # because the box's own lean makes some spill unavoidable (0.06 px at the A's tip, where
    # its near end meets a leaning edge) while 1 px of spill is a PLACEMENT CHOICE, and the
    # optimiser should not be allowed to choose it. Measured at --min-clear 0.9: with 1 px
    # the winner was `base across, end along` 0.66 px outside; with 0.25 px the placements
    # that spill are rejected, and the word gets smaller but stays in.
    def fits(c, place):
        tf, ap, wmk, anc, wanc = layout(c, place)
        # wanc, not anc: `anc` is the whole-word left edge and the word itself starts
        # a_w + gap further along. Sampling at anc tests ink that is not where the word is
        # -- and reports it inside, because the box is taller at its near end. (measured)
        return (gap_of(ap, wmk, wanc) >= min_clear and
                ink_violation(ap + wmk.placed_points(wanc[0], wanc[1], fr["angle"])) <= FIT_TOL)

    def best_cap(place):
        """largest cap that fits the box AND clears the monogram, for one placement"""
        if fits(cap_box, place):
            return cap_box
        lo, hi = 0.05, cap_box
        if not fits(lo, place):
            return 0.0
        while hi - lo > 1e-4:
            mid = (lo + hi) / 2
            if fits(mid, place):
                lo = mid
            else:
                hi = mid
        return lo

    # "as large as possible but still fit in the black box" is an optimisation, not a
    # coin toss: try every placement in the box and take the one that allows the biggest
    # type. Measured on the shipped box, all three across-placements reach the same cap
    # (4.310 mm): the word fills the box's length, so the BOX binds and the monogram does
    # not -- kw<->A clearance is top 17.36 px, centred 9.45 px, base 9.70 px, all above
    # --min-clear 0.50 mm (0.79 mm = 9.45 px). Ties fall to list order, i.e. centred, which
    # is also the nicest; raise --min-clear to 1.0 and 'top' wins, which is the only case
    # where the monogram gets a vote. An earlier version of this comment claimed centred
    # could only reach 72% and that the geometry demanded the top edge: that was the anchor
    # bug (logo/AGENTS.md gotcha 15) measuring itself. Re-measure before believing it.
    places = [(ac, al) for ac in ("center", "base", "top")
              for al in ("center", "start", "end")]
    if align != "auto" or along != "auto":
        places = [("center" if align == "auto" else align,
                   "center" if along == "auto" else along)]
    scored = sorted(((best_cap(p), -places.index(p), p) for p in places), reverse=True)
    cap, _, place = scored[0]
    across, along = place
    if cap <= 0:
        raise SystemExit(
            f"no placement of {word!r} inside that box clears the monogram by "
            f"{min_clear} mm - move the box, or lower --min-clear")
    a_tf, a_pts, wm, anchor, word_anchor = layout(cap, place)
    g = gap_of(a_pts, wm, word_anchor)

    # ---------------------------------------------------------------- height fill
    # The box's LENGTH fixes the cap height (the word spans it exactly), which leaves its
    # HEIGHT barely used -- 55.4% on the shipped box. Filling it means stretching the type
    # PERPENDICULAR TO THE BASELINE and never along it: letter widths, the A's width,
    # tracking and every along-baseline distance stay exactly as fitted, only the height
    # grows. One transform over the whole type group (pointer-A AND PTURE together), so the
    # two cannot drift into two different sizes of type.
    # The monogram keeps its veto: the box's lower-left corner is drawn inside the W, so
    # the stretch factor is bisected exactly like the cap height was.
    #
    # (frame, half-planes and BOX_TOL were set up next to box_frame() above: the fit needs
    # them too, because "inside the box" is one definition used in two places)
    ink0 = np.array(a_pts + wm.placed_points(word_anchor[0], word_anchor[1], ang), float)
    t0 = (ink0 - O) @ U
    u0 = (ink0 - O) @ D
    # Measure the band the type's INK occupies, not the nominal cap band: Inter's letters
    # overshoot the cap line and the baseline, and a stretch multiplies the overshoot too.
    # Fitting the nominal band (4.310 mm) instead of the ink band (4.365 mm) put the ink
    # 1.6 px outside the box; the box check caught it.
    t_lo, t_hi = float(t0.min()), float(t0.max())
    band = t_hi - t_lo
    T = t0 - t_lo                          # every ink point sits at t = t_lo + T, T >= 0

    # ---- the tallest stretch that stays inside the box THAT WAS ACTUALLY DRAWN ---------
    # "Fill the box's height" is not one number when the box is four mouse clicks. On the
    # shipped box the two long edges are 0.63 deg off parallel, so the headroom above the
    # baseline falls from 7.920 mm at the near end to 7.651 mm at the far one, and the left
    # edge leans inward by 0.18 deg. Fitting the ink band to the frame's MEAN height (7.786
    # mm, i.e. x1.784) is the obvious move and it is wrong: it leaves the far end of the
    # word 1.6 px outside the top edge, which is exactly what the box check reported. So the
    # limit comes from the quad itself. Every edge is a half-plane and the map is linear in
    # s, so the tight edge is arithmetic rather than a search:
    #     n . (u, inset + s*T) >= c   ->   s * (n_t * T) >= c - n_u*u - n_t*inset
    # One exception, and it is what makes the answer honest rather than impossible: a point
    # the fit ALREADY left outside must not veto the stretch. The A's tip sits on the box's
    # near end, which the leaning left edge clips by 0.06 px -- the shipped margin, the
    # documented price of "as large as possible". Such a point is only forbidden from getting
    # WORSE by more than the validator's 1 px; every point that starts inside must stay in.
    def tallest_stretch(tol):
        """largest s with the filled type (t -> inset + s*(t - t_lo): seated on the box's
        base, stretched by s across it) still inside the drawn quad. (inf, None) if free."""
        best, at = np.inf, None
        for n, c in HP:
            m0 = u0 * n[0] + t0 * n[1] - c              # margin where the fit put the point
            floor = np.where(m0 >= 0.0, 0.0, m0 - tol)  # in: stays in. out: no worse.
            rhs = floor + c - u0 * n[0] - inset * n[1]
            coef = n[1] * T                             # d(margin)/ds, per point
            up = coef < -1e-12                          # s bounded above by this point
            if not up.any():
                continue
            lim = rhs[up] / coef[up]
            k = int(np.argmin(lim))
            if float(lim[k]) < best:
                best = float(lim[k])
                at = (float(u0[up][k]), float(inset + T[up][k]))
        return best, at

    sy_fill = (fr["height"] - 2 * inset) / band      # the mean-height fill: too tall
    sy_box, sy_at = tallest_stretch(BOX_TOL)         # what the drawn box really allows
    box_allows = f"x{sy_box:.3f}" if math.isfinite(sy_box) else "unbounded"
    taper_over = max(0.0, (sy_fill - sy_box) * band) if math.isfinite(sy_box) else 0.0
    sy_t = min(sy_box, max_stretch) if height_fill else 1.0
    a_t = inset - sy_t * t_lo            # the full fill seats the ink's lowest point on t=0

    # ---- the fill as ONE blend: lam = 0 nothing, lam = 1 the full fill ----------------
    # Blending the DISPLACEMENT, not the factor, keeps the family continuous and keeps
    # lam = 0 the identity: --no-height-fill then ships the fitted type exactly where the
    # centring put it, not slid down by the seating (an earlier version applied the seating
    # unconditionally and --no-height-fill came out 0.79 mm off-centre).
    #     t  ->  lam*a_t + (1 + lam*(sy_t - 1)) * t
    # which is still one affine stretch of t, so one SVG transform says it.
    def mapped(pts, lam):
        """the #type displacement field at blend lam, applied to points (mm)"""
        p = np.asarray(pts, float)
        return p + U * (lam * (a_t + (sy_t - 1.0) * ((p - O) @ U)))[:, None]

    def gap_at(lam):
        p, q = mapped(ink0, lam), kw_pts
        return float(np.sqrt(((q[:, None, 0] - p[None, :, 0]) ** 2 +
                              (q[:, None, 1] - p[None, :, 1]) ** 2).min()))

    lam = 1.0 if sy_t > 1.0005 else 0.0
    if lam == 0.0:
        sy_why = ("height fill off" if not height_fill else
                  "kept unstretched: the box as drawn leaves no room to grow")
    elif gap_at(lam) < min_clear:
        # the monogram's veto, bisected on the blend: taller type reaches further across
        # the baseline, so the gap falls as lam rises and a plain bisection is exact enough
        lo, hi = 0.0, 1.0
        if gap_at(lo) < min_clear:            # cannot even keep what we already have
            lam, sy_why = 0.0, "kept unstretched: the fit already sits under --min-clear"
        else:
            while hi - lo > 1e-4:
                mid = (lo + hi) / 2
                if gap_at(mid) >= min_clear:
                    lo = mid
                else:
                    hi = mid
            lam = lo
            sy_why = (f"held to {min_clear:.2f} mm clear of the monogram; the box alone "
                      f"would have allowed {box_allows}")
    elif height_fill and sy_box <= max_stretch:
        sy_why = (f"as tall as the drawn box allows: the ink touches its "
                  f"{'top edge' if sy_at and sy_at[1] > fr['height'] / 2 else 'edge'} "
                  f"at u={sy_at[0]:.1f} mm" if sy_at else "fills the drawn box")
    else:
        sy_why = f"capped by --max-stretch {max_stretch:.2f} (the box would take {box_allows})"
    # what the file carries, as opposed to what the box or the veto allowed
    sy = 1.0 + lam * (sy_t - 1.0)                    # across-baseline stretch emitted
    a0 = lam * a_t                                   # across-baseline seating emitted
    g2 = gap_at(lam)
    # t -> a0 + sy*t  ==  stretch by sy about the box's BASE line (t = 0), slid along the
    # across direction by a0.  local y of rotate(ang) IS the across axis, so one SVG
    # transform says exactly that -- and it is the same map `mapped()` measured with.
    type_tf = (
        f'translate({f(ox + a0 * uv[0])} {f(oy + a0 * uv[1])}) rotate({f(ang)})'
        f' scale(1 {f(sy)}) rotate({f(-ang)})'
        f' translate({f(-ox)} {f(-oy)})') if sy > 1.0005 else ""

    why = ("fills the box" if cap >= cap_box - 1e-3 else
           f"trimmed from {cap_box:.3f} to {cap:.3f} mm cap to keep {min_clear:.2f} mm "
           f"clear of the monogram")
    if align == "auto" and along == "auto":
        why += f"; placement chosen: {across} across, {along} along"
    total = cap * per_cap

    # NOTE: the type bboxes are taken AFTER the stretch -- centring on the unstretched ink
    # pushed the tall word 0.02 px off the right edge of the artboard.
    mb = bbox(parse_points(kw_d))
    ab = bbox(mapped(a_pts, lam))
    wmb = bbox(mapped(wm.placed_points(word_anchor[0], word_anchor[1], ang), lam))

    # The box was drawn by hand, so the lockup lands wherever the mouse happened to be.
    # Keep every relative position, but put the whole thing in the middle of the
    # artboard: same scale, new translate.
    sc, tx0 = m_logo[0], m_logo[4]
    ux0 = min(mb[0], ab[0], wmb[0])
    uy0 = min(mb[1], ab[1], wmb[1])
    ux1 = max(mb[2], ab[2], wmb[2])
    uy1 = max(mb[3], ab[3], wmb[3])
    if recenter:
        tx1 = (canvas - sc * (ux1 - ux0)) / 2 - sc * ux0
        ty1 = (canvas - sc * (uy1 - uy0)) / 2 - sc * uy0
    else:
        tx1, ty1 = m_logo[4], m_logo[5]
    logo_out = f"translate({f(tx1)} {f(ty1)}) scale({f(sc)})"

    # --classic: the gradient the sketch carries, verbatim, on a single-colour monogram
    classic_grad = (f'    <linearGradient id="kw-grad" x1="{gx1}" y1="{gy1}"'
                    f' x2="{gx2}" y2="{gy2}" gradientUnits="userSpaceOnUse">\n'
                    + ''.join(f'      <stop offset="{o}" stop-color="{c}"/>\n'
                              for o, c in stops)
                    + '    </linearGradient>\n')
    kw_defs, kw_els = kw_paint(kw_d, c_clip_polygon(poly_vertices(kw_d)),
                               green=green, blue=blue,
                               grad_defs=(classic_grad if gradient else None),
                               split=split_c, kw_id=kw_id, paint=c_paint)
    # The type group carries the height fill: ONE transform over the pointer-A and PTURE
    # together, so the word cannot split into two sizes of type, and never over #kw, whose
    # wobble is the drawing. Read it as: seat the ink's lowest point on the box's base line,
    # then stretch across the baseline -- never along it, or the tracking moves.
    type_body = (f'    <path id="a" fill="{blue}" transform="{a_tf}" d="{cursor_d}"/>\n'
                 f'    <g id="wordmark" transform="translate({f(word_anchor[0])}'
                 f' {f(word_anchor[1])}) rotate({f(fr["angle"])})">\n'
                 f'      <path fill="{blue}" d="{wm.d}"/>\n    </g>\n')
    if type_tf:
        type_body = ''.join('  ' + ln if ln.strip() else ln
                            for ln in type_body.splitlines(True))
        type_body = (f'    <g id="type" transform="{type_tf}">\n'
                     f'      <!-- the pointer-A and {word} together: stretched {sy:.3f}x '
                     f'across\n           the baseline (never along it) to fill the box '
                     f'height, and\n           seated on the box base line. The monogram is '
                     f'NOT in here -->\n'
                     + type_body + '    </g>\n')
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- kwcapture mark: the monogram from kwcapture-mark-sketch.svg plus APTURE fitted
     inside the helper box that was drawn there.
     The box is a GUIDE and is NOT in this file. Its base set the baseline slope
     ({fr['angle']:.2f} deg, read off the corner points) and its length/height set the type
     size: cap height {cap:.3f} mm fills {100 * total / fr['length']:.1f}% of the box's length
     and {100 * cap / fr['height']:.1f}% of its height, centred in the box.
     Re-run with the mark flag (see gen_logo.py); edit the box in the sketch, not here
     #kw       monogram, path data verbatim from the sketch
     #kw-c     the same path data again, clipped to the C the junction forms
     #a        the mouse pointer as the letter "A": cap height, capital-A width
     #wordmark "{word}" as vector outlines
     Colour: the monogram is {green} and the C, the A and the letters are {blue}, so the
     mark reads KW (green) and Capture (blue). The C is a colour split, not a redraw: the
     geometry and the type fit are untouched by it
     Relative positions are exactly as sketched; the lockup is re-centred on the artboard
     (same scale, new translate). Sizing: {why}.
     Reading: K+W junction = C, pointer = A, then {word}  ->  CAPTURE.
-->
<svg xmlns="http://www.w3.org/2000/svg" width="{canvas:.0f}" height="{canvas:.0f}"
     viewBox="0 0 {canvas:.0f} {canvas:.0f}" role="img" aria-label="kwcapture">
  <title>kwcapture</title>
  <desc>A green K+W monogram whose junction is a blue letter C, a blue mouse pointer
 standing in for the letter A, then the blue letters {word}: CAPTURE.</desc>
  <defs>
{kw_defs}  </defs>
  <g id="logo" transform="{logo_out}">
{kw_els}{type_body}  </g>
</svg>
'''
    if out:
        write_svg(out, svg)
    return svg, dict(box=fr, cap=cap, total=total, anchor=anchor, mono=mb, a=ab,
                     wordmark=wmb, per_cap=per_cap, gap=g, why=why, cap_box=cap_box,
                     place=place, logo_out=logo_out, union=(ux0, uy0, ux1, uy1),
                     sy=sy, sy_why=sy_why, gap_stretched=g2,
                     ink_filled=sy * band, ink_band=band,
                     px=px, sy_fill=sy_fill, sy_box=sy_box, sy_at=sy_at, lam=lam,
                     taper_over=taper_over,
                     top_edge=(t_top_near, t_top_far), top_skew=top_skew,
                     box_edge_tol=1.0 / px)


# ------------------------------------------------------- the C split (two colours)
# The monogram is ONE closed outline with 19 vertices, and BOTH sketches -- the original
# and the redrawn mark -- use the same topology index for index (verified 2026-10-10).
# The letter partition is the OWNER's numbering of it (2026-10-10; my first attempt
# invented a different one and was wrong -- AGENTS.md gotcha 22):
#
#     K = 0  1  2  3  4           13 14 15 16 17 18
#     W =    3  4  5  6  7  8  9 10 11 12 13 14
#     C =    3  4  5  6           12 13 14 15 16 17      <- this is the blue one
#
# They OVERLAP, which is the point of a ligature: 3-4 is the K's leg and the W's first
# stroke at the same time, and the C borrows from both.  The C is THREE strokes, like "[",
# not two like "<":
#
#   top arm     14 -> 15 -> 16 -> 17      the K's arm
#   spine       17 -> 3                   the stem's right edge: the C's back, of zero
#                                         width -- the stem itself stays green
#   bottom arm  3 -> 4 -> 5 -> 6  +  12 -> 13
#               the leg, the shared V, and the first W rise, all the way up to the peak
#               tip at 12 -- this is the stroke I was leaving green, and it is what made
#               my "C" read as a chevron instead of a letter
#
# The ring is therefore the drawing's OWN edges plus exactly two chords: 6->12 (slice the
# peak: the C keeps the tip, the descending stroke stays green) and 17->3 (slice the stem
# off). No padding, no invented geometry -- which is why the cut is exact.
C_RING = (3, 4, 5, 6, 12, 13, 14, 15, 16, 17)
K_RING = (0, 1, 2, 3, 4, 13, 14, 15, 16, 17, 18)
W_RING = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)


def c_clip_polygon(poly):
    """The C, as the owner numbered it: the ring through vertices 3,4,5,6,12,13,14,15,16,17
    of the sketch's mm space.  Everything of the monogram inside it is painted blue; the
    rest (the stem, the W's descending and final strokes) stays green."""
    if len(poly) != 19:
        raise SystemExit(
            f"the monogram has {len(poly)} vertices, not 19: the C split is cut by vertex "
            f"index (C_RING = {C_RING}), so re-sketching means re-checking the numbering "
            "with the owner -- do not infer it from the shape (gotcha 22).")
    return [poly[i] for i in C_RING]


def stem_polygon(poly):
    """The K's stem -- 0,1,2,3,17,18 -- the part that must stay green."""
    v = poly
    return [v[0], v[1], v[2], v[3], v[17], v[18]]


def ring_path(poly):
    """The C ring as its own path data (the sketch's mm space) -- --c-paint solid."""
    return "M " + " L ".join(f"{f(x)},{f(y)}" for x, y in poly) + " Z"


def kw_paint(kw_d, poly, green=GREEN, blue=BLUE, grad_defs=None, split=True,
             kw_id="kw", paint=C_PAINT):
    """Return (defs, elements) for the two-colour monogram: GREEN body, BLUE C.

    The C polygon is in the sketch's mm space and resolves inside the #logo transform
    exactly the way the gradient's mm coordinates do; emitting it in canvas px would put
    the C in the wrong place at every scale but one.

    `paint` is how the blue gets cut to the C, and it exists because renderers disagree:

      solid  (default) -- #kw-c is the C ring's OWN path data, no defs at all. The only
             form every renderer gets right, because it asks nothing of them: no clip
             support, no mask support. Legal only because the ring lies 100% inside the
             monogram's ink (asserted by validate_logo.py), so it is the same pixels --
             and it is still derived by vertex index, never hand-drawn.
      mask   -- #kw-c is the WHOLE monogram again, painted blue, cut by a <mask> (black
             backing rect + a white C polygon). Keeps the "a repaint, never a second
             drawing" property and works in Qt and Inkscape, but ImageMagick's internal
             MSVG hides the whole overlay: measured 0% blue. Not the default for that
             reason, which is worth remembering: a mask is not automatically safe.
      clip   -- the historic form: clip-path. **QtSvg ignores clip-path entirely**
             (measured: Qt 6.10.2 drops even a <circle> clip), which painted the whole
             monogram blue in Gwenview and in Dolphin's thumbnails. Kept only so the
             three forms can be diffed against each other.

    grad_defs: pass a <linearGradient> block to paint the base monogram with a gradient
    instead of flat green (that is all --classic changes, together with blue=DARK and
    split=False).
    """
    defs, els = "", ""
    if grad_defs:
        defs += grad_defs
        els += f'    <path id="{kw_id}" fill="url(#kw-grad)" d="{kw_d}"/>\n'
    else:
        els += f'    <path id="{kw_id}" fill="{green}" d="{kw_d}"/>\n'
    if split:
        pts = " ".join(f"{f(x)},{f(y)}" for x, y in poly)   # f() = the module's mm format
        if paint == "solid":
            els += (f'    <path id="{kw_id}-c" fill="{blue}" d="{ring_path(poly)}"/>\n')
        elif paint == "mask":
            x0, y0, x1, y1 = bbox(parse_points(kw_d))
            p = MASK_PAD
            x0, y0, x1, y1 = x0 - p, y0 - p, x1 + p, y1 + p
            w, h = x1 - x0, y1 - y0
            defs += (f'    <mask id="c-clip" maskUnits="userSpaceOnUse"'
                     f' x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}">\n'
                     f'      <rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" '
                     f'height="{f(h)}" fill="#000000"/>\n'
                     f'      <polygon points="{pts}" fill="#ffffff"/>\n'
                     f'    </mask>\n')
            els += (f'    <path id="{kw_id}-c" fill="{blue}" mask="url(#c-clip)" '
                    f'd="{kw_d}"/>\n')
        elif paint == "clip":
            defs += ('    <clipPath id="c-clip">\n'
                     '      <polygon points="' + pts + '"/>\n'
                     '    </clipPath>\n')
            els += (f'    <path id="{kw_id}-c" fill="{blue}" clip-path="url(#c-clip)" '
                    f'd="{kw_d}"/>\n')
        else:
            raise SystemExit(f"--c-paint {paint!r}: use mask, solid or clip")
    return defs, els


# ---------------------------------------------------------------------- build
# NOT the palette: these are the two stops the sketch carries, kept verbatim so --classic
# reproduces the retired 2026-10-10 look exactly.  Palette P2 changed GREEN and BLUE; it did
# not touch this, and a diff of GRAD_SKETCH against the sketch is the check that --classic is
# still honest.  (build_mark() reads the stops out of the sketch file for the same reason.)
GRAD_SKETCH = ('    <linearGradient id="kw-grad" x1="51.549733" y1="114.89782"\n'
               '                    x2="87.126312" y2="114.89782"'
               ' gradientUnits="userSpaceOnUse">\n'
               '      <stop offset="0" stop-color="#0000ff"/>\n'
               '      <stop offset="1" stop-color="#00ac4e"/>\n'
               '    </linearGradient>\n')


def build(font=FONT, word=WORD, cap=CAP, track=TRACK, angle=ANGLE, canvas=CANVAS,
          pad=PAD, a_size=A_SIZE, a_gap=A_GAP, a_width=A_WIDTH,
          a_upright=False, with_a=True,
          align_top=ALIGN_TOP, sketch=SKETCH, out=None,
          green=GREEN, blue=BLUE, gradient=False, split_c=True, c_paint=C_PAINT):
    paths = read_source(sketch)

    def pick(*names, what):
        """Find a path by Inkscape id. The ids ARE the interface (see AGENTS.md
        'Re-sketching'), so say which ones were looked for and what the sketch actually
        has -- a bare KeyError 'path1' tells the next person nothing."""
        for n in names:
            if paths.get(n):
                return paths[n]
        raise SystemExit(
            f"{sketch}: cannot find {what}. Looked for id {' or '.join(names)}; this sketch "
            f"has {sorted(k for k, d in paths.items() if d)}. Keep the ids, or add the new "
            f"one to pick() in build().")

    # as drawn, never rewritten: the sketch's own ids bind the parts
    mono_d = pick("path1", "kw", what="the K+W monogram")
    cursor_d = (pick("path10", "cursor", "a", what="the mouse pointer (the letter A)")
                if with_a else None)
    mono = bbox(parse_points(mono_d))

    wm = Wordmark(font, word, cap, track) if word else None
    # the width a capital A has in this face, at this cap height: the A's ruler
    ref_a = wm.ink_width("A") if wm else None

    def word_top(pt):
        return bbox(wm.placed_points(pt[0], pt[1], angle))[1] if wm else 1e9

    anchor = ANCHOR
    # --monogram has no pointer at all (and the mark sketch has none to offer), so the A
    # is placed only when there is something to place
    place = (lambda pt: place_A(cursor_d, pt, angle, cap, a_gap, a_size, a_upright,
                                ref_width=ref_a, a_width=a_width)) if cursor_d else \
            (lambda pt: ("", None))
    a_tf, a_pts = place(anchor)
    if align_top:
        top_now = min(bbox(a_pts)[1] if a_pts is not None else 1e9, word_top(anchor))
        anchor = (anchor[0], anchor[1] + (mono[1] - top_now))
        a_tf, a_pts = place(anchor)

    ab = bbox(a_pts) if with_a else (1e9, 1e9, -1e9, -1e9)
    wmb = (bbox(wm.placed_points(anchor[0], anchor[1], angle)) if wm
           else (1e9, 1e9, -1e9, -1e9))
    x0 = min(mono[0], ab[0], wmb[0])
    y0 = min(mono[1], ab[1], wmb[1])
    x1 = max(mono[2], ab[2], wmb[2])
    y1 = max(mono[3], ab[3], wmb[3])
    w, h = x1 - x0, y1 - y0
    s = min((canvas - 2 * pad) / w, (canvas - 2 * pad) / h)
    tx = (canvas - s * w) / 2 - s * x0
    ty = (canvas - s * h) / 2 - s * y0

    kw_defs, kw_els = kw_paint(mono_d, c_clip_polygon(poly_vertices(mono_d)),
                               green=green, blue=blue,
                               grad_defs=(GRAD_SKETCH if gradient else None),
                               split=split_c, paint=c_paint)
    two_tone = split_c
    if wm and with_a:
        reads = (f'     How it reads: the K+W junction is the "C", the mouse pointer is the "A",\n'
                 f'     the typeset letters are "{word}":   C + A + {word} = CAPTURE.\n'
                 + ('     Colour: KW green, Capture blue. #kw is the monogram in ' + green + ',\n'
                    + '     #kw-c a second copy of the same path data, clipped to the C the\n'
                    + '     junction forms, in ' + blue + '; #a and #wordmark share that blue.\n'
                    if two_tone else
                    '     Colour: the monogram is a blue to green gradient, the type is dark.\n')
                 + f'     #kw hand-drawn K+W monogram, kept exactly as drawn\n'
                 f'     #a  the hand-drawn pointer, laid out as the letter "A" (cap band, baseline)\n'
                 f'     #wordmark "{word}" as vector outlines on the {abs(angle):.0f} deg baseline the\n'
                 f'           sketch drew; outlines not a text element, so no font is needed\n')
        desc = ('  <desc>A K+W monogram whose junction is the letter C, in green with the C\n'
                f' in blue, a blue mouse pointer standing in for the letter A, then the blue\n'
                f' letters {word}: CAPTURE.</desc>\n') if two_tone else (
                '  <desc>A K+W monogram in a blue-to-green gradient whose junction is the\n'
                f' letter C, a mouse pointer standing in for the letter A, then the letters\n'
                f' {word}: CAPTURE.</desc>\n')
    else:
        reads = ('     Monogram only: no pointer, no wordmark. For favicons and tiny sizes where\n'
                 '     the C + A + PTURE reading cannot survive; kwcapture.svg is the real logo.\n')
        desc = ('  <desc>kwcapture monogram: a K and a W sharing a stroke, green, with the\n'
                ' C they form between them in blue.</desc>\n') if two_tone else \
               '  <desc>kwcapture monogram: a K and a W sharing a stroke, blue to green.</desc>\n'

    # NOTE: no "--" sequence inside this comment, it is illegal in XML.
    head = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- kwcapture logo.
     Artboard {canvas:.0f}x{canvas:.0f} px, artwork centred, {pad:.0f}px padding on the
     constrained axis.
{reads}     All coordinates below #logo are the sketch's own mm space, scaled to fit.
     Generated by gen_logo.py; edit the sketch or the knobs, not this file.
-->
<svg xmlns="http://www.w3.org/2000/svg" width="{canvas:.0f}" height="{canvas:.0f}"
     viewBox="0 0 {canvas:.0f} {canvas:.0f}" role="img" aria-label="kwcapture">
  <title>kwcapture</title>
{desc}{'  <defs>\n' + kw_defs + '  </defs>\n' if kw_defs else ''}  <g id="logo" transform="translate({f(tx)} {f(ty)}) scale({f(s)})">
{kw_els}'''
    body = ""
    if with_a:
        body += f'    <path id="a" fill="{blue}" transform="{a_tf}" d="{cursor_d}"/>\n'
    if wm:
        body += (f'    <g id="wordmark" transform="translate({f(anchor[0])} {f(anchor[1])})'
                 f' rotate({f(angle)})">\n'
                 f'      <path fill="{blue}" d="{wm.d}"/>\n'
                 f'    </g>\n')
    svg = head + body + "  </g>\n</svg>\n"
    if out:
        write_svg(out, svg)
    # the A's ink width along the baseline, in cap heights, for reporting
    ang = math.radians(angle)
    uu = [p_[0] * math.cos(ang) + p_[1] * math.sin(ang) for p_ in a_pts] if with_a else [0.0]
    return svg, dict(mono=mono, mono_d=mono_d, a=ab, wordmark=wmb, anchor=anchor,
                     scale=s, content=(x0, y0, x1, y1), a_ink_w=max(uu) - min(uu),
                     word_width=wm.width if wm else 0.0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--font", default=FONT)
    ap.add_argument("--word", default=WORD, help='default "PTURE" - do NOT use CAPTURE')
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--track", type=float, default=TRACK)
    ap.add_argument("--angle", type=float, default=ANGLE)
    ap.add_argument("--pad", type=float, default=PAD)
    ap.add_argument("--canvas", type=float, default=CANVAS)
    ap.add_argument("--a-size", type=float, default=A_SIZE)
    ap.add_argument("--a-gap", type=float, default=A_GAP)
    ap.add_argument("--a-width", type=float, default=A_WIDTH,
                    help="A width as a multiple of the ink width of a real capital A in "
                         "the same face at the same cap height (default 1.00)")
    ap.add_argument("--a-upright", action="store_true",
                    help="rotate the pointer to exactly perpendicular (reads as an "
                         "arrow, not an A; kept only because it is cheaper to document "
                         "than to rediscover)")
    ap.add_argument("--no-a", action="store_true", help="monogram + PTURE, no pointer")
    ap.add_argument("--monogram", action="store_true",
                    help="bare monogram only, no pointer and no wordmark; needs an "
                         "explicit --out, because there is no shipped kwcapture-mono.svg "
                         "any more (deleted 2026-10-11: unofficial and historical, the "
                         "owner's ruling -- see logo/AGENTS.md gotcha 38)")
    ap.add_argument("--mark", action="store_true",
                    help="build logo/kwcapture-mark.svg from kwcapture-mark-sketch.svg: "
                         "monogram + APTURE fitted inside the helper box drawn there, "
                         "box itself dropped")
    ap.add_argument("--box", default=None, help="id of the helper box path (default: the "
                    "only parallelogram in the sketch; 'fit-box' by convention)")
    ap.add_argument("--inset", type=float, default=0.0,
                    help="keep this much clearance from the box edges, mm (default 0)")
    ap.add_argument("--align", choices=["auto", "center", "base", "top"], default="auto",
                    help="across the box. auto (default) tries every placement and keeps "
                         "the one that allows the biggest type")
    ap.add_argument("--along", choices=["auto", "center", "start", "end"], default="auto",
                    help="along the box's base; auto (default) is optimised together with "
                         "--align")
    ap.add_argument("--no-height-fill", dest="height_fill", action="store_false",
                    help="mark mode: keep the type uniform (fitted by length only, about "
                         "half the box's height unused) instead of stretching it across the "
                         "baseline to fill the box's height")
    ap.add_argument("--max-stretch", type=float, default=MAX_STRETCH,
                    help="mark mode: ceiling on the height fill, x the fitted cap height "
                         "(default 2.00 -- a taste guard; the shipped box wants 1.753 and "
                         "is not stopped by it). 0 is the same as --no-height-fill")
    ap.add_argument("--min-clear", type=float, default=0.50,
                    help="mark mode: minimum ink clearance from the monogram, mm "
                         "(the word shrinks rather than touching it; default 0.50)")
    ap.add_argument("--no-recenter", dest="recenter", action="store_false",
                    help="mark mode: keep the sketched position instead of centring the "
                         "lockup on the artboard")
    ap.add_argument("--green", default=GREEN,
                    help="monogram colour: the K's stem and the W (default %(default)s)")
    ap.add_argument("--blue", default=BLUE,
                    help="the C, the pointer-A and the letters (default %(default)s)")
    ap.add_argument("--c-paint", choices=["mask", "solid", "clip"], default=C_PAINT,
                    help="how the blue C is cut out of the monogram. mask (default) and "
                         "solid render identically everywhere; clip is the historic form "
                         "and Qt (Gwenview, Dolphin thumbnails, QIcon) IGNORES clip-path, "
                         "which made the monogram render 100%% blue there")
    ap.add_argument("--no-c-split", dest="split_c", action="store_false",
                    help="flat green monogram with no blue C: the control for asking "
                         "whether it is the colour split that makes the C read")
    ap.add_argument("--classic", action="store_true",
                    help="the pre-2026-10-10 look: blue-to-green gradient monogram, no C "
                         "split, black type")
    ap.add_argument("--free-baseline", dest="align_top", action="store_false")
    ap.add_argument("--sketch", default=str(SKETCH),
                    help="source drawing (with --mark this defaults to "
                         "logo/kwcapture-mark-sketch.svg)")
    ap.add_argument("--out", default=None,
                    help="default logo/kwcapture.svg, or logo/kwcapture-mark.svg with "
                         "--monogram, so the real logo is never clobbered by accident")
    ap.add_argument("--force", action="store_true",
                    help="allow a paint variant to overwrite a shipped artefact (default: "
                         "refuse, because the result is a still-valid file with the wrong look)")
    a = ap.parse_args()
    # A variant with no --out silently overwrites a SHIPPED file, and the shipped file stays
    # perfectly valid while doing it: --classic / --no-c-split / --c-paint differ only in
    # PAINT, so xmllint, the geometry checks and even the colour fractions can all still look
    # sane. This happened by following this folder's own documented commands, which is proof
    # enough that a note in a README is not a guard. Default output paths are still fine for
    # the default look; only a deliberate deviation needs --out (or --force).
    # The shipped artefacts. kwcapture-mono.svg was here until 2026-10-11: the owner ruled the
    # monogram unofficial and historical, so it is deleted, and a default output path that
    # re-creates a deleted artefact is exactly the trap that made Round 12 ship the wrong
    # drawing (gotcha 38). --monogram therefore REQUIRES --out, below.
    shipped = {str(HERE / "kwcapture.svg"), str(HERE / "kwcapture-mark.svg")}
    # Which knobs deviate from the shipped look? Compared against argparse's OWN defaults,
    # so a knob added later cannot silently escape the list, and a change of default cannot
    # make the guard disagree with the help text.
    off = []
    for dest, flag in (("classic", "--classic"), ("split_c", "--no-c-split"),
                       ("height_fill", "--no-height-fill"), ("a_upright", "--a-upright"),
                       ("no_a", "--no-a"), ("recenter", "--no-recenter"),
                       ("align_top", "--free-baseline")):
        got = getattr(a, dest)
        want = ap.get_default(dest)
        if got != want:
            off.append(flag if want in (True, False) else f"{flag} {got}")
    for dest, flag in (("c_paint", "--c-paint"), ("align", "--align"), ("along", "--along"),
                       ("green", "--green"), ("blue", "--blue"), ("word", "--word")):
        got = getattr(a, dest)
        if got != ap.get_default(dest):
            off.append(f"{flag} {got}")
    for dest, flag in (("cap", "--cap"), ("track", "--track"), ("angle", "--angle"),
                       ("pad", "--pad"), ("canvas", "--canvas"), ("inset", "--inset"),
                       ("min_clear", "--min-clear"), ("max_stretch", "--max-stretch"),
                       ("a_size", "--a-size"), ("a_width", "--a-width"),
                       ("a_gap", "--a-gap")):
        got, want = getattr(a, dest), ap.get_default(dest)
        if isinstance(got, float) and abs(got - want) > 1e-9:
            off.append(f"{flag} {got:g}")
    if a.sketch != str(SKETCH) and not a.mark:
        off.append(f"--sketch {a.sketch}")
    guess = str(HERE / ("kwcapture-mark.svg" if a.mark else "kwcapture.svg"))
    if a.monogram and a.out is None:
        raise SystemExit(
            "--monogram needs an explicit --out: there is no shipped kwcapture-mono.svg to "
            "write.\n"
            "  a figure:  --monogram --out /tmp/mono.svg\n"
            "  the mode is still here; the ARTEFACT is not. It was deleted 2026-10-11 (the "
            "owner ruled\n  it unofficial and historical), and a monogram sitting next to the "
            "approved artwork eventually\n  gets mistaken for it -- which is how Round 12's "
            "icon set went wrong (gotcha 38).\n"
            "  the file itself: git log --diff-filter=D -- logo/kwcapture-mono.svg")
    if a.out is None and off and not a.force and guess in shipped and Path(guess).exists():
        raise SystemExit(
            f"refusing to overwrite the shipped {Path(guess).name}: this run deviates from "
            f"the shipped look by {' '.join(off)}.\n"
            f"  write it somewhere else:  --out /tmp/{Path(guess).stem}-variant.svg\n"
            f"  or, if you really mean to replace the shipped file:  --force")
    # colour: default KW green / Capture blue; --classic is the pre-2026-10-10 look
    green, blue, grad, split_c = a.green, a.blue, False, a.split_c
    if a.classic:
        blue, grad, split_c = DARK, True, False
    if a.mark:
        out = a.out or str(HERE / "kwcapture-mark.svg")
        svg, info = build_mark(sketch=a.sketch if a.sketch != str(SKETCH) else MARK_SKETCH,
                               font=a.font, word=a.word, track=a.track, canvas=a.canvas,
                               a_size=a.a_size, a_width=a.a_width, inset=a.inset,
                               align=a.align, along=a.along, box_id=a.box,
                               min_clear=a.min_clear,
                               recenter=a.recenter, out=out,
                               green=green, blue=blue, gradient=grad, split_c=split_c,
                               height_fill=a.height_fill, max_stretch=a.max_stretch,
                               c_paint=a.c_paint)
        fr = info["box"]
        print(f"box         : base {fr['length']:.3f} x {fr['height']:.3f} mm "
              f"at {fr['angle']:.2f} deg")
        print(f"fit         : cap {info['cap']:.3f} mm, ink {info['total']:.3f} mm long "
              f"= {100*info['total']/fr['length']:.1f}% of the length, "
              f"{100*info['cap']/fr['height']:.1f}% of the height")
        print(f"anchor      : ({info['anchor'][0]:.3f}, {info['anchor'][1]:.3f}) mm "
              f"[{info['place'][0]} across, {info['place'][1]} along], inset={a.inset} mm")
        if info["cap"] < info["cap_box"] - 1e-4:
            print(f"clearance   : {info['gap']:.3f} mm from the monogram - {info['why']} "
                  f"(the box alone would have allowed cap {info['cap_box']:.3f} mm)")
        box_h = info["box"]["height"]
        if info["sy"] > 1.0005:
            pct = 100 * info["ink_filled"] / box_h
            print(f"height fill : x{info['sy']:.3f} across the baseline: type ink "
                  f"{info['ink_band']:.3f} mm -> {info['ink_filled']:.3f} mm = "
                  f"{pct:.1f}% of the box height ({info['sy_why']})")
            print(f"clearance   : {info['gap_stretched']:.3f} mm from the monogram after "
                  f"the stretch (was {info['gap']:.3f} mm)")
            tn, tf_ = info["top_edge"]
            print(f"box taper   : the drawn box is NOT a rectangle: the headroom over its "
                  f"base falls {tn:.3f} -> {tf_:.3f} mm along the length (its top edge is "
                  f"{info['top_skew']:+.2f} deg off parallel). Filling the MEAN height "
                  f"(x{info['sy_fill']:.3f}) would have hung {info['taper_over']:.3f} mm = "
                  f"{info['taper_over'] * info['px']:.1f} px outside the far end, so the "
                  f"answer is x{info['sy']:.3f}")
        else:
            print(f"height fill : off ({info['sy_why']})")
        print("box         : dropped from the output (it was only a guide)")
        print(f"colour      : monogram {'blue-to-green gradient' if grad else green},"
              f" C + A + word {blue}" + ("  [no C split]" if not split_c else ""))
        print("written     :", out)
        raise SystemExit(0)

    out = a.out or str(HERE / "kwcapture.svg")          # --monogram already required --out

    word = "" if a.monogram else a.word
    svg, info = build(font=a.font, word=word, cap=a.cap, track=a.track,
                      angle=a.angle, canvas=a.canvas, pad=a.pad, a_size=a.a_size,
                      a_gap=a.a_gap, a_width=a.a_width, a_upright=a.a_upright,
                      with_a=not (a.no_a or a.monogram), align_top=a.align_top,
                      sketch=a.sketch, out=out,
                      green=green, blue=blue, gradient=grad, split_c=split_c,
                      c_paint=a.c_paint)

    print("content bbox:", tuple(round(v, 2) for v in info["content"]),
          f"({info['content'][2]-info['content'][0]:.2f} x "
          f"{info['content'][3]-info['content'][1]:.2f} mm)")
    print("scale       :", round(info["scale"], 4), "px per mm")
    print("word        :", repr(word) if word else "(none)")
    if not (a.no_a or a.monogram):
        print("'A' pointer :", tuple(round(v, 2) for v in info["a"]),
              "  ink %.2f x cap wide" % (info["a_ink_w"] / a.cap))
    if info["wordmark"][0] < 1e8:
        print("'PTURE'     :", tuple(round(v, 2) for v in info["wordmark"]))
    print(f"colour      : monogram {'blue-to-green gradient' if grad else green},"
          f" C + A + word {blue}" + ("  [no C split]" if not split_c else ""))
    print("written     :", out)
