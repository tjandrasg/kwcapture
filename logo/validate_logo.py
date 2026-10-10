#!/usr/bin/env python3
"""Geometry check for the generated logo: ink bounds, centring, clearances.

    python3 logo/validate_logo.py                  # checks logo/kwcapture.svg
    python3 logo/validate_logo.py logo/kwcapture-mark.svg

Reports, in final canvas px:
  * the ink bounding box of each element (#kw, #a, #wordmark)
  * the clearance between each pair  (a collision is what ruins this logo)
  * the artboard padding, and whether the artwork is centred
  * the A-vs-type check: the pointer's height and width against the face's own cap, plus
    the shared cap line and baseline.  This is what catches a silently wrong A_SIZE/A_WIDTH
    -- a projection bug once rendered the A at 1.41x cap while the knob said 1.00.
  * the box check, for artefacts whose "<name>-sketch.svg" carries a helper box.  The box
    is deliberately absent from the output, so containment is verified against the sketch
    (re-read, with the re-centring shift undone) rather than assumed.
  * the colour split.  The C is painted by a second copy of the monogram clipped to a
    polygon, so no geometry check can see it at all: this checks the overlay is a copy of the
    base path data, that the clip equals C_RING recomputed from the sketch vertices, that
    sample points in the stem / the C's three strokes / the W's other strokes land on the
    intended side, and -- independent of anyone's idea of the letter -- that >=95% of the
    clip's area lies on the ink and none of the stem's area lies inside the clip.

Exit code is non-zero if any two elements collide (< 1.5 px apart), if the ink falls outside
the artboard or is off-centre, if the A fails the type check, or if the word's ink sits more
than 1 px outside the helper box.  numpy is used for the pairwise distance; it is a
dependency of the project anyway.
"""
import math
import os
import re
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / "kwcapture.svg"
sys.path.insert(0, str(HERE))
try:                                  # reuse the generator's box reading rather than
    import gen_logo as G              # duplicating the parallelogram geometry
except Exception:                     # pragma: no cover
    G = None
NS = "{http://www.w3.org/2000/svg}"


def parse_path(d):
    """Subpaths of densely sampled outline points (local user units)."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    subs, cur, i, cmd = [], [], 0, None
    cx = cy = sx = sy = 0.0
    while i < len(toks):
        t = toks[i]
        if t[0].isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                cur.append((cx, cy))
                if len(cur) > 1:
                    cur.append((sx, sy))
                subs.append(cur)
                cur = []
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
            if len(cur) > 1:
                subs.append(cur)
            cx, cy = ox + a[0], oy + a[1]
            sx, sy = cx, cy
            cur = [(cx, cy)]
            cmd = "l" if rel else "L"
        elif C == "L":
            px, py = cx, cy
            cx, cy = ox + a[0], oy + a[1]
            steps = max(1, int(math.hypot(cx - px, cy - py) / 0.15))
            for k in range(1, steps + 1):
                cur.append((px + (cx - px) * k / steps, py + (cy - py) * k / steps))
        elif C == "H":
            cx = ox + a[0]
            cur.append((cx, cy))
        elif C == "V":
            cy = oy + a[0]
            cur.append((cx, cy))
        elif C == "C":
            p0, p3 = (cx, cy), (ox + a[4], oy + a[5])
            p1, p2 = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            for k in range(1, 41):
                t, m = k / 40, 1 - k / 40
                cur.append((m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0],
                            m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]))
            cx, cy = p3
        elif C == "Q":
            p0, p3 = (cx, cy), (ox + a[2], oy + a[3])
            p1 = (ox + a[0], oy + a[1])
            for k in range(1, 41):
                t, m = k / 40, 1 - k / 40
                cur.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p3[0],
                            m * m * p0[1] + 2 * m * t * p1[1] + t * t * p3[1]))
            cx, cy = p3
    if len(cur) > 1:
        subs.append(cur)
    return subs


def tf_matrix(transform):
    """'translate(a b) scale(c)' etc -> affine (a,b,c,d,e,f)."""
    m = (1, 0, 0, 1, 0, 0)

    def mul(m1, m2):      # m1 outer, m2 inner
        a1, b1, c1, d1, e1, f1 = m1
        a2, b2, c2, d2, e2, f2 = m2
        return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2,
                b1 * c2 + d1 * d2, a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)

    for fn, args in re.findall(r"(\w+)\(([^)]*)\)", transform or ""):
        v = [float(x) for x in re.split(r"[ ,]+", args.strip())]
        if fn == "translate":
            m = mul(m, (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0))
        elif fn == "scale":
            m = mul(m, (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0))
        elif fn == "matrix":
            m = mul(m, tuple(v[:6]))
        elif fn == "rotate":
            ang = math.radians(v[0])
            ca, sa = math.cos(ang), math.sin(ang)
            if len(v) == 3:
                m = mul(m, (1, 0, 0, 1, v[1], v[2]))
                m = mul(m, (ca, sa, -sa, ca, 0, 0))
                m = mul(m, (1, 0, 0, 1, -v[1], -v[2]))
            else:
                m = mul(m, (ca, sa, -sa, ca, 0, 0))
    return m


def mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2,
            b1 * c2 + d1 * d2, a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def apply(m, pts):
    a, b, c, d, e, f = m
    return np.array([[a * x + c * y + e, b * x + d * y + f] for x, y in pts])


def ink(path):
    """({name: Nx2 outline points in canvas coords}, viewBox, {name: path data}, overlays.

    A path whose id is "<base>-c" is a COLOUR overlay: the same shape repainted through a
    clipPath, not new artwork. Its ink is the base shape's ink, so it is not counted twice
    (that would be a certain "collision" with itself); it is handed back instead, because
    "the overlay is a copy of the base path data" is precisely the promise worth checking.
    """
    root = ET.parse(str(path)).getroot()
    vb = (root.get("viewBox") or "0 0 512 512").split()
    if len(vb) != 4:
        # main() reads vb[2], vb[3] unguarded; a short viewBox must say so here rather than
        # surfacing later as a bare `IndexError: list index out of range` (a real flake of
        # exactly that shape showed up on 2026-10-10 and this is the one place in the file
        # that can produce it from file content).
        raise SystemExit(f"{path}: viewBox must be 4 numbers, got {vb!r}")
    vb = [float(v) for v in vb]
    top = root.find(f"{NS}g")
    m_top = tf_matrix(top.get("transform"))
    out, ds, overlays = {}, {}, {}
    stack = [(top, m_top)]
    while stack:
        el, m = stack.pop()
        for child in el:
            if child.tag == NS + "g":
                stack.append((child, mul(m, tf_matrix(child.get("transform")))))
            elif child.tag == NS + "path":
                name = child.get("id") or "wordmark"
                d = child.get("d")
                if name.endswith("-c") and name[:-2] in ds:
                    overlays[name[:-2]] = dict(fill=child.get("fill"),
                                               clip=child.get("clip-path"),
                                               mask=child.get("mask"), d=d)
                    continue
                pm = mul(m, tf_matrix(child.get("transform")))
                arr = np.vstack([apply(pm, s) for s in parse_path(d)])
                out[name] = arr if name not in out else np.vstack([out[name], arr])
                ds[name] = d
    return out, vb, ds, overlays


def clear(A, B):
    """Min distance between two point clouds (both densely sampled)."""
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    return float(d.min())


def pip(poly, p):
    """Even-odd point-in-polygon."""
    x, y = p
    inside, n = False, len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def colour_check(target, ds, overlays):
    """The C is a COLOUR split, so the geometry checks above cannot see it at all: the
    monogram is drawn twice with identical path data and only the paint differs. This
    proves the paint is where the design says it is, in the sketch's mm space:

      * the overlay must be a byte-for-byte copy of the monogram path data (the split is
        paint, never a redrawn #kw -- the wobble is the design);
      * the emitted clip polygon must equal the one the generator derives from the sketch
        vertices (so a hand-edit of the output is caught);
      * sample points inside the stem, the C's three strokes and the W's other strokes must
        land on the side the design intends: stem GREEN, C BLUE, W GREEN;
      * AREA tests that depend on the drawing rather than on anyone's idea of the letter:
        at least 95% of the clip's area must lie on the monogram's ink, and none of the
        stem's area may fall inside the clip.  These are what reject a plausible-but-wrong
        ring -- see AGENTS.md gotcha 22.
    """
    if "kw" not in ds:
        return []
    if "kw" not in overlays:
        print("  colour: one-tone monogram (no C split): classic or --no-c-split output")
        return []
    ov, bad = overlays["kw"], []
    # Three ways to cut the C out (--c-paint), and the file says which one it is.
    # `solid` has no cut-out at all: #kw-c carries the ring's own path data. It is still
    # not "a second drawing" -- that data is derived from the same sketch vertices by index
    # and is checked against them below, exactly like the other two forms.
    src = Path(target).read_text()
    root = ET.parse(str(target)).getroot()
    if ov.get("clip"):
        mode = "clip"
        if ov["d"] != ds["kw"]:
            bad.append("the #kw-c overlay is not a copy of #kw's path data: with "
                       "--c-paint clip the C must be a clipPath over the same outline, "
                       "never a re-drawn monogram")
        m = re.search(r'url\(#([^)]+)\)', ov["clip"])
        if not m:
            return bad + [f'#kw-c has no usable clip-path (got {ov["clip"]!r})']
        el = root.find(f".//{NS}clipPath[@id='{m.group(1)}']/{NS}polygon")
        if el is None:
            return bad + [f"clipPath #{m.group(1)} with a <polygon> not found"]
        poly = [tuple(float(c) for c in p.split(",")) for p in el.get("points").split()]
    elif ov.get("mask"):
        mode = "mask"
        if ov["d"] != ds["kw"]:
            bad.append("the #kw-c overlay is not a copy of #kw's path data: with "
                       "--c-paint mask the C must be a mask over the same outline")
        m = re.search(r'url\(#([^)]+)\)', ov["mask"])
        if not m:
            return bad + [f'#kw-c has no usable mask (got {ov["mask"]!r})']
        el = root.find(f".//{NS}mask[@id='{m.group(1)}']/{NS}polygon"
                       f"[@fill='#ffffff']")
        if el is None:
            return bad + [f"mask #{m.group(1)} with a white <polygon> not found"]
        poly = [tuple(float(c) for c in p.split(",")) for p in el.get("points").split()]
    else:
        mode = "solid"
        poly = [(float(a), float(b))
                for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", ov["d"])]

    if G is None:
        print(f"  colour: {mode} polygon read but NOT verified "
              "(gen_logo.py not importable)")
        return bad
    # Which sketch is the parent? The filename is only a hint: kwcapture-mono.svg comes
    # from kwcapture-sketch.svg normally, and from kwcapture-mark-sketch.svg when --sketch
    # says so. So match on CONTENT -- the sketch that actually contains the emitted #kw
    # path data -- and keep the name convention only to choose when several could do.
    sk, src_paths = None, {}
    named = HERE / (Path(target).stem + "-sketch.svg")
    cands = [named] if named.exists() else []
    cands += [p for p in sorted(HERE.glob("*-sketch.svg")) if p != named]
    for cand in cands:
        p = G.read_source(cand)
        if any(d == ds["kw"] for d in p.values()):
            sk, src_paths = cand, p
            break
    if sk is None:
        print("  colour: NOT VERIFIED -- no logo/*-sketch.svg contains the emitted #kw path "
              "data, so the clip cannot be checked against a drawing (keep the sketch next "
              "to the output as <name>-sketch.svg, or the checks stay silent)")
        return bad
    key = next(k for k, d in src_paths.items() if d == ds["kw"])
    v = G.poly_vertices(src_paths[key])
    want = G.c_clip_polygon(v)
    same = len(want) == len(poly) and all(
        abs(a[0] - b[0]) < 1e-3 and abs(a[1] - b[1]) < 1e-3
        for a, b in zip(want, poly))
    if not same:
        bad.append(f"the emitted C polygon ({mode}) is not the one derived from the "
                   f"sketch vertices ({len(poly)} pts emitted, {len(want)} expected)")

    # Sample points, one region per letter, verified against BOTH sketches on 2026-10-10.
    # The C is three strokes (top arm, the zero-width spine along the stem's edge, bottom
    # arm = leg + shared V + the first W rise up to the peak tip at 12) -- see C_RING.
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    lerp = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    stem = [(mid(v[0], v[18])[0], lerp(v[0], v[1], t)[1]) for t in (0.25, 0.5, 0.75)]
    c_pts = ([lerp(mid(v[17], v[14]), mid(v[16], v[15]), t) for t in (0.35, 0.7)]  # top arm
             + [mid(mid(v[3], v[4]), mid(v[13], v[14]))                # the leg
                , mid(mid(v[4], v[5]), mid(v[6], v[12]))               # the rise
                , lerp(mid(v[4], v[5]), mid(v[6], v[12]), 0.8)         # near the tip
                , mid(mid(v[3], v[17]), v[14])])                       # the junction
    w = [lerp(v[12], mid(v[7], v[8]), t) for t in (0.15, 0.4)]         # descending stroke
    w += [mid(mid(v[7], v[8]), mid(v[9], v[10]))]                      # final stroke

    # every sample must be inside the monogram at all, or the anatomy assumption broke
    for tag, pts in (("stem", stem), ("C", c_pts), ("W", w)):
        for p in pts:
            if not pip(v, p):
                return bad + [f"sample point for {tag} ({p[0]:.2f},{p[1]:.2f}) is not on "
                              f"the monogram: the 19-vertex anatomy has changed, update "
                              f"the sample sets in colour_check() before trusting them"]
    for tag, pts, want_in in (("stem", stem, False), ("C", c_pts, True), ("W", w, False)):
        for p in [p for p in pts if pip(poly, p) != want_in]:
            bad.append(f"{tag} at ({p[0]:.2f},{p[1]:.2f}) is not "
                       + ("blue: the C does not cover its own strokes" if want_in else
                          "green: the colour split bleeds onto a stroke that must stay green"))

    # Area tests -- the ones that catch a *wrong idea* rather than drift. A ring that is
    # mostly empty space (my first attempt overshoot into the counters) or a clip that eats
    # the stem both pass a point-sampling-only check by luck; these do not.
    def frac_in(a, b, step=0.15):
        """fraction of b's area that is also inside a, sampled on a grid"""
        x0, y0 = min(p[0] for p in b), min(p[1] for p in b)
        x1, y1 = max(p[0] for p in b), max(p[1] for p in b)
        tot = hit = 0
        y = y0 + step / 2
        while y < y1:
            x = x0 + step / 2
            while x < x1:
                if pip(b, (x, y)):
                    tot += 1
                    hit += pip(a, (x, y))
                x += step
            y += step
        return hit / tot if tot else 0.0
    on_ink = frac_in(v, poly)                 # the C ring should sit ON the drawing
    stem_blue = frac_in(poly, G.stem_polygon(v))   # the stem should be untouched
    if on_ink < 0.95:
        bad.append(f"only {100 * on_ink:.0f}% of the C clip polygon lies on the monogram: "
                   "the ring must follow the drawing's own edges and the two chords "
                   "(6->12 across the peak, 17->3 across the stem), not invented lines "
                   "through empty space")
    if stem_blue > 0.005:
        bad.append(f"{100 * stem_blue:.1f}% of the stem's area is inside the C clip: the "
                   "stem is what the C must NOT cover -- it is the stroke that competes "
                   "with it")
    print(f"  colour split (vs {sk.name}): {mode} {len(poly)} pts "
          f"{'==' if same else '!='} recomputed, {100 * on_ink:.1f}% on ink, "
          f"stem area {100 * stem_blue:.2f}% blue")
    print(f"                samples: stem {len(stem) - len([p for p in stem if pip(poly, p)])}"
          f"/{len(stem)} green, C {len(c_pts) - len([p for p in c_pts if not pip(poly, p)])}"
          f"/{len(c_pts)} blue, W {len(w) - len([p for p in w if pip(poly, p)])}/{len(w)} green")
    return bad


def box_check(target, shapes):
    """The mark is generated to fit a helper box drawn in <name>-sketch.svg, and the box
    is deliberately NOT in the output -- so nothing in the output proves the word is
    inside it. This closes that loop: read the box from the sketch, undo the re-centring
    shift, and require the A and the word to be inside it."""
    sk = HERE / (Path(target).stem + "-sketch.svg")
    if G is None or not sk.exists():
        return []                      # not a boxed artefact
    if "a" not in shapes or "wordmark" not in shapes:
        return []
    r_out = ET.parse(str(target)).getroot()
    r_sk = ET.parse(str(sk)).getroot()
    m_out = G.parse_transform(r_out.find(f"{NS}g").get("transform"))
    m_sk = G.parse_transform(r_sk.find(f"{NS}g").get("transform"))
    try:
        hull = G.find_box(r_sk)
    except SystemExit:
        return []                      # no helper box in that sketch
    box = [(x + m_out[4] - m_sk[4], y + m_out[5] - m_sk[5]) for x, y in hull]
    s = 1.0 if sum(box[i][0] * box[(i + 1) % 4][1] - box[(i + 1) % 4][0] * box[i][1]
                   for i in range(4)) > 0 else -1.0

    def depth(p):                      # >0 inside, <0 outside, in px
        w = 1e9
        for i in range(4):
            a, b = box[i], box[(i + 1) % 4]
            ex, ey = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ey) or 1.0
            w = min(w, s * (ex * (p[1] - a[1]) - ey * (p[0] - a[0])) / L)
        return w

    # the point CLOSEST to getting out, not the cosiest one inside (tracking the max
    # depth instead reported +46 px "inside" while the A was 20 px outside)
    shallow, who = 1e9, ""
    for name in ("a", "wordmark"):
        for p in shapes[name]:
            d = depth(p)
            if d < shallow:
                shallow, who = d, name
    pen = max(0.0, -shallow)
    print(f"  box check (vs {sk.name}): closest ink {shallow:+.2f} px from the box edge "
          f"(positive = inside), tightest is #{who}")
    if pen > 1.0:
        return [f"ink is {pen:.1f} px OUTSIDE the helper box - the fit is wrong"]
    return []


def type_stretch(target, ang):
    """(across-baseline stretch factor, ids the #type group covers, along-baseline factor).

    `--mark` fills the box's HEIGHT by stretching the type perpendicular to the baseline --
    so the emitted artwork has a ruler that is not the ruler the letters were drawn with.
    Every type rule below has to be measured with the DRAWN ruler: a cap that has been
    stretched x1.75 is not a bigger letter, and a capital A that is a correct 0.97 x cap
    reports as 0.55 x cap if the stretch is left in. Read the factor off the transform the
    file actually carries, not off a knob: the whole point of this file is that the artwork,
    not the generator, decides what is true. (1.0, [], 1.0) when there is no #type group.
    """
    root = ET.parse(str(target)).getroot()
    grp = root.find(f".//{NS}g[@id='type']")
    if grp is None:
        return 1.0, [], 1.0
    M = tf_matrix(grp.get("transform"))
    a = math.radians(ang)
    dv = np.array([math.cos(a), math.sin(a)])
    pv = np.array([-math.sin(a), math.cos(a)])
    lin = lambda v: np.array([M[0] * v[0] + M[2] * v[1], M[1] * v[0] + M[3] * v[1]])
    ids = [el.get("id") for el in grp.iter() if el.get("id")]
    return float(np.linalg.norm(lin(pv))), ids, float(np.linalg.norm(lin(dv)))


def band_check(target, shapes):
    """The A (pointer) and the word must share a baseline and a cap line.
    The word is all caps, so its extent perpendicular to the baseline IS the cap
    height -- that is the ruler the A has to match.  (A projection bug once made
    the A 1.41x cap while the knob said 1.00; this is what catches that now.)
    Measured unstretched: see type_stretch()."""
    if "a" not in shapes or "wordmark" not in shapes:
        return []
    txt = Path(target).read_text()
    m = re.search(r'id="wordmark"[^>]*rotate\((-?[\d.]+)\)', txt)
    if not m:
        return ["could not find the wordmark baseline angle"]
    ang = float(m.group(1))
    a = math.radians(ang)
    dirv = np.array([math.cos(a), math.sin(a)])
    perpv = np.array([-math.sin(a), math.cos(a)])   # positive = below the baseline
    sy, tids, salong = type_stretch(target, ang)

    def band(pts):
        w = pts @ perpv
        return w.min(), w.max()           # cap line, baseline

    out = []
    at, abl = band(shapes["a"])
    wt, wbl = band(shapes["wordmark"])
    # the drawn sizes: the stretch is uniform across the whole group, so undoing it is one
    # division -- and it is the only honest way to ask "is that A as wide as an A?"
    ha, hw = (abl - at) / sy, (wbl - wt) / sy
    ua = shapes["a"] @ dirv
    aw = ua.max() - ua.min()                       # A ink width along the baseline
    print(f"  type check, perpendicular to the {ang:+.0f} deg baseline:")
    if sy > 1.0005:
        print(f"    height fill x{sy:.3f} across the baseline (read off #type, along-baseline "
              f"factor {salong:.4f}); rules below measured unstretched")
    print(f"    A height {ha:6.2f} px   cap height {hw:6.2f} px   ratio {ha/hw:.3f}")
    print(f"    A width  {aw:6.2f} px   = {aw / hw:.3f} x cap  "
          f"(a real capital A is ~0.95-1.00 x cap)")
    print(f"    cap line : A {at:7.2f}  word {wt:7.2f}   (delta {(at - wt) / sy:+.2f})")
    print(f"    baseline : A {abl:7.2f}  word {wbl:7.2f}   (delta {(abl - wbl) / sy:+.2f})")
    if sy > 1.0005:
        # the stretch is only legal if it is a stretch: across, never along, and over the
        # whole word. A group that misses one of the two makes APTURE two different sizes
        # of type, and one that reaches #kw redraws the hand-drawn monogram
        if not {"a", "wordmark"} <= set(tids):
            out.append(f"the height stretch covers {sorted(tids)} but not both #a and "
                       f"#wordmark: the pointer and the letters must be one word")
        if "kw" in tids:
            out.append("the height stretch covers #kw: the monogram is hand-drawn and must "
                       "not be stretched (colour it, do not resize it)")
        if abs(salong - 1.0) > 1e-3:
            out.append(f"the height stretch also scales ALONG the baseline "
                       f"(x{salong:.4f}): only across is allowed, or the tracking moves")
    if abs(ha - hw) > 2.0:
        out.append(f"A height {ha:.1f}px != cap height {hw:.1f}px "
                   f"(ratio {ha/hw:.2f}); the A must match the letters")
    if abs(abl - wbl) / sy > 2.0:
        out.append(f"A does not stand on the word baseline (off by {(abl - wbl) / sy:+.1f}px)")
    if (wt - at) / sy > 2.0:
        out.append(f"A overshoots the cap line by {(wt - at) / sy:.1f}px")
    # A condensed A reads as a decoration; a wildly wide one reads as a blob. The exact
    # target is the face's own capital A (gen_logo prints that match); this is the
    # independent sanity net that does not need the font.
    if not 0.85 <= aw / hw <= 1.15:
        out.append(f"A width is {aw / hw:.2f} x cap: a capital A is ~1.0 x cap wide, "
                   f"fix A_WIDTH (uniform scaling gives ~0.73 and reads as a skinny A)")
    return out


def _qt_render(path, n=400):
    """(green, blue) pixel counts from QtSvg -- the engine behind Gwenview, Dolphin's
    thumbnails and QIcon. None if Qt is not available here."""
    try:
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QColor
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtCore import QByteArray
    except Exception:
        return None
    app = QGuiApplication.instance() or QGuiApplication([])
    r = QSvgRenderer(QByteArray(Path(path).read_bytes()))
    if not r.isValid():
        raise RuntimeError("QtSvg cannot parse the file")
    img = QImage(n, n, QImage.Format.Format_ARGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    r.render(p)
    p.end()
    a = np.empty((n, n, 3), np.uint8)
    for y in range(n):
        for x in range(n):
            c = img.pixelColor(x, y)
            a[y, x] = (c.red(), c.green(), c.blue())
    return _count(a)


def _msvg_render(path, n=400):
    """(green, blue) from ImageMagick's OWN MSVG coder (no Inkscape/librsvg delegate).
    None if ImageMagick is not installed. It is a weak renderer on purpose: it treats a
    mask it does not understand as 'hide everything'."""
    if subprocess.run(["bash", "-lc", "command -v magick"], capture_output=True).returncode:
        return None
    # mkstemp, not /tmp/<name>-<pid>.png: a pid-keyed path is only unique among *live*
    # processes, so a stale raster left behind by a killed run can be read back by a later
    # process that reuses the pid. Ask for a fresh file instead.
    fd, out = tempfile.mkstemp(prefix="kwcapture-msvg-", suffix=".png")
    os.close(fd)
    try:
        r = subprocess.run(["magick", f"MSVG:{path}", "-background", "white",
                            "-resize", f"{n}x{n}", out], capture_output=True)
        if r.returncode:
            raise RuntimeError("magick MSVG failed: " + r.stderr.decode()[:120])
        try:
            from PIL import Image
            with Image.open(out) as im:
                a = np.array(im.convert("RGB"))
        except Exception as e:
            # name the renderer and the file size: "what came back was not a raster" is the
            # finding, and a bare IndexError/PIL error does not say which renderer did it.
            raise RuntimeError(f"magick wrote a raster PIL cannot read "
                               f"({type(e).__name__}: {e}, {os.path.getsize(out)} bytes)")
    finally:
        Path(out).unlink(missing_ok=True)
    return _count(a)


def _count(a):
    a = np.asarray(a).astype(int)
    if a.ndim != 3 or a.shape[2] < 3:
        # never let this surface as a bare IndexError: it means a renderer produced
        # something that is not an RGB raster, and the message should say which
        raise RuntimeError(f"expected an RGB raster, got shape {a.shape}")
    R, Gc, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (int(((Gc > R + 25) & (Gc > B + 25)).sum()),
            int(((B > R + 25) & (B > Gc + 25)).sum()))


RENDERERS = (("QtSvg   (Gwenview, Dolphin, QIcon)", _qt_render),
             ("MSVG    (ImageMagick internal)", _msvg_render))


def render_check(target, overlays):
    """Render the file with every independent renderer this machine has, and fail if the
    green/blue split is not actually on screen in one of them.

    Scoped to the two-tone output: with no C split there is no split to protect. That also
    keeps --classic out of here, which is good -- MSVG cannot render our userSpaceOnUse
    gradient at all (measured: it paints nothing in either brand colour), and a switch that
    reproduces a retired look is not what this gate exists to defend.

    Everything else here reads path data and does its own geometry, so it agrees with the
    generator by construction (gotcha 22). This check cannot: it asks what a viewer paints.
    It exists because `clip-path` shipped for a day while QtSvg silently ignores that
    attribute -- the monogram rendered 100% blue in Gwenview and in Dolphin's thumbnails,
    with the file valid, the generator happy and every other check green.

    And a mask is not the fix either: ImageMagick's MSVG coder hides the whole overlay
    behind a mask it does not understand (0% blue). The two weak renderers fail in opposite
    directions, and only `--c-paint solid` -- no cut-out feature at all -- survives both,
    which is why solid is the default. Measured 2026-10-10, in the table in AGENTS.md.
    """
    if "kw" not in overlays:
        return []                       # one-tone output: nothing two-tone to verify
    out, seen = [], 0
    for name, fn in RENDERERS:
        try:
            res = fn(target)
        except Exception as e:
            print(f"  render {name}: ERROR {e}")
            out.append(f"{name.split()[0]} could not render the file: {e}")
            continue
        if res is None:
            print(f"  render {name}: not installed here, SKIPPED")
            continue
        seen += 1
        g, b = res
        tot = g + b
        frac = 100.0 * b / tot if tot else 0.0
        note = ""
        if not tot:
            out.append(f"{name.split()[0]} painted nothing in the brand colours")
            note = "NOTHING"
        elif g < 0.05 * tot:
            out.append(f"{name.split()[0]} renders {frac:.0f}% blue: the green "
                       "monogram is covered -- a cut-out this renderer ignores is in use "
                       "(--c-paint solid emits neither clip nor mask)")
            note = "NO GREEN"
        elif b < 0.05 * tot:
            out.append(f"{name.split()[0]} renders no blue at all: the C overlay is hidden "
                       "-- unsupported cut-out (--c-paint solid emits neither)")
            note = "NO BLUE"
        print(f"  render {name}: green {g:6d} blue {b:6d} -> {frac:5.1f}% blue"
              + (f"  [{note}]" if note else ""))
    if not seen:
        print("  render: NO RENDERER AVAILABLE -- this is the check that catches "
              "renderer-only breakage; run it where Qt or ImageMagick exists")
    return out


def run_check(name, fn, *args):
    """Run one check, which owes us a list of failure strings, and make any unexpected
    exception NAME ITSELF.

    A check that raises instead of returning was, until now, indistinguishable from a crash
    of the file: the traceback scrolls, `| tail -1` keeps one line, and what survives is a
    bare `IndexError: list index out of range` or `TypeError: '<=' not supported between
    instances of 'float' and 'list'` with no check, no line, no way to chase it. Two such
    messages appeared in the 2026-10-10 session and neither could be reproduced afterwards
    (~570 clean runs over the three artefacts and every mode, alone and 16-deep parallel),
    so the only honest repair is to make the next one identify the check that raised it.

    A crash is a FAIL, never a pass: the check did not run, so nothing was proven.
    """
    try:
        out = fn(*args)
    except Exception as e:                     # a crash IS the finding; report and continue
        sys.stdout.flush()                     # keep the traceback after the line that names it
        print(f"  CRASH in {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return [f"CRASH in {name}(): {type(e).__name__}: {e} -- see traceback; this check "
                f"did NOT run"]
    if not isinstance(out, list):
        print(f"  CRASH in {name}: returned {type(out).__name__}, expected a list")
        return [f"CRASH in {name}(): returned {type(out).__name__} instead of a list of "
                f"failures"]
    return out


def main(argv):
    target = Path(argv[1]) if len(argv) > 1 else DEFAULT
    shapes, vb, ds, overlays = ink(target)
    W, H = vb[2], vb[3]
    bad = []
    print(f"# {target.name}   artboard {W:.0f}x{H:.0f}")
    for k, v in shapes.items():
        print(f"  {k:9} ink  x {v[:,0].min():7.2f} .. {v[:,0].max():7.2f}"
              f"   y {v[:,1].min():7.2f} .. {v[:,1].max():7.2f}   ({len(v)} pts)")
    names = list(shapes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            d = clear(shapes[names[i]], shapes[names[j]])
            tag = "COLLISION" if d < 1.5 else ("tight" if d < 3.0 else "ok")
            if d < 1.5:
                bad.append(f"{names[i]}/{names[j]} collide ({d:.2f}px)")
            print(f"  clearance {names[i]:9} <-> {names[j]:9}: {d:7.2f} px  [{tag}]")
    allp = np.vstack(list(shapes.values()))
    l, r = allp[:, 0].min(), W - allp[:, 0].max()
    t, b = allp[:, 1].min(), H - allp[:, 1].max()
    print(f"  ink {l:.1f},{t:.1f} -> {allp[:,0].max():.1f},{allp[:,1].max():.1f}"
          f"   padding  L {l:.1f}  R {r:.1f}  T {t:.1f}  B {b:.1f}")
    bad += run_check("colour_check", colour_check, target, ds, overlays)
    bad += run_check("box_check", box_check, target, shapes)
    bad += run_check("band_check", band_check, target, shapes)
    bad += run_check("render_check", render_check, target, overlays)
    if min(l, r, t, b) < 0:
        bad.append("ink is outside the artboard")
    if abs(l - r) > 1.0 or abs(t - b) > 1.0:
        bad.append(f"artwork not centred (L/R {l:.1f}/{r:.1f}, T/B {t:.1f}/{b:.1f})")
    for w in bad:
        print("  FAIL:", w)
    # The last line is the one that survives `| tail -1`, and a crash must not be able to
    # look like an ordinary problem count from the end of a pipe.
    crashed = [w for w in bad if w.startswith("CRASH in")]
    if not bad:
        print("  OK")
    elif crashed:
        print(f"  {len(bad)} problem(s), {len(crashed)} of them CRASHES "
              f"({', '.join(w.split()[2] for w in crashed)}) -- NOT A CLEAN RUN")
    else:
        print(f"  {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
