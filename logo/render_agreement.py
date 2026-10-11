#!/usr/bin/env python3
"""render_agreement.py — do the installed SVG engines paint the SAME GEOMETRY?

    python3 logo/render_agreement.py [logo/*.svg ...]

`validate_logo.py`'s render check asks each engine whether BOTH brand colours appear, which
is what caught QtSvg ignoring `clip-path`. It cannot see WHERE an engine painted them. This
tool asks the sharper question: for every engine on this machine, what is the ink bounding
box per colour, and does it match the geometry the path data itself implies (computed here
from the same path data, with every `transform` applied by hand)?

An engine that disagrees has a `transform` bug, not a colour bug. Measured 2026-10-10:
Inkscape and QtSvg agree to 1 px on every artefact; ImageMagick's internal MSVG coder places
the *type* of both `kwcapture.svg` and `kwcapture-mark.svg` wrong — the mark's wordmark lands
with its top at y=127 instead of y=60 and runs off the right edge — while painting the green
monogram correctly, because the monogram sits under a plain translate+scale and the type sits
under a rotate/scale/rotate chain. Baking the transforms into the path data makes MSVG agree,
which is what proves the disagreement is about `transform` and not about the artwork.

Exit code: 0 if every engine agrees with the path data within --tol px, 1 otherwise. This is
deliberately NOT wired into validate_logo.py's gate yet: making it fatal would redden the
shipped files, and the fix (emit transform-free path data, or accept the disagreement) is the
owner's call — see AGENTS.md, *Which cut-out* and gotcha 27.
"""
import argparse
import atexit
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_logo as V                    # noqa: E402

NS = V.NS
TOL = 2.0                                     # px; antialiasing is worth about 1


def want(target, pal=None):
    """{colour: bbox} from the path data alone, every transform applied by hand.

    Which fill means which colour comes from `V.palette()`, i.e. from gen_logo's own GREEN and
    BLUE.  It used to be `fill.startswith("#00a")` / `startswith("#0000ff")` here, and on
    2026-10-11 the recolour to #008c46/#7f7fff made both tests false at once: `want()` returned
    {}, the loop below compared nothing, and the tool printed "all engines agree with the path
    data" and exited 0 on files it had not checked.  So: match the palette exactly, and if a
    file yields NO brand paint at all, `main()` says so and fails.  A check that silently
    checks nothing is the failure mode this folder keeps paying for (gotcha 30).
    """
    pal = pal or V.palette()
    shapes, vb, ds, overlays = V.ink(target)
    out = {}
    root = ET.parse(str(target)).getroot()
    top = root.find(f"{NS}g")
    m_top = V.tf_matrix(top.get("transform"))
    stack, painted = [(top, m_top)], {}
    while stack:
        el, m = stack.pop()
        for ch in el:
            if ch.tag == NS + "g":
                stack.append((ch, V.mul(m, V.tf_matrix(ch.get("transform")))))
            elif ch.tag == NS + "path":
                fill = (ch.get("fill") or "").lower()
                key = next((name for name, hexv in pal.items() if fill == hexv), None)
                if key is None:
                    continue
                mm = V.mul(m, V.tf_matrix(ch.get("transform")))
                pts = np.vstack([V.apply(mm, s) for s in V.parse_path(ch.get("d"))])
                painted.setdefault(key, []).append(pts)
    for key, arrs in painted.items():
        p = np.vstack(arrs)
        out[key] = (p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max())
    return out, (vb[2], vb[3])


def rasterise(target, engine, n=512):
    tmp = f"/tmp/kw-agree-{os.getpid()}.png"
    try:
        if engine == "inkscape":
            r = subprocess.run(["inkscape", str(target), "-o", tmp, "-b", "white",
                                "-w", str(n), "-h", str(n)], capture_output=True)
            if r.returncode:
                raise RuntimeError(r.stderr.decode()[-160:])
        elif engine == "msvg":
            r = subprocess.run(["magick", f"MSVG:{target}", "-background", "white",
                                "-resize", f"{n}x{n}", tmp], capture_output=True)
            if r.returncode:
                raise RuntimeError(r.stderr.decode()[-160:])
        elif engine == "qt":
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
            from PyQt6.QtCore import QByteArray
            from PyQt6.QtGui import QGuiApplication, QImage, QPainter
            from PyQt6.QtSvg import QSvgRenderer
            app = QGuiApplication.instance() or QGuiApplication([])
            rd = QSvgRenderer(QByteArray(Path(target).read_bytes()))
            if not rd.isValid():
                raise RuntimeError("QtSvg cannot parse the file")
            img = QImage(n, n, QImage.Format.Format_ARGB32)
            img.fill(0xFFFFFFFF)
            p = QPainter(img)
            rd.render(p)
            p.end()
            img.save(tmp)
        else:
            raise ValueError(engine)
        from PIL import Image
        return np.array(Image.open(tmp).convert("RGB")).astype(int)
    finally:
        Path(tmp).unlink(missing_ok=True)


def got(a):
    """{colour: bbox+count} as painted, classified by hue against the palette — the same
    `V.classify()` the validator uses, so the two tools can never disagree about which pixels
    are which colour (they used to carry two copies of a "channel wins by 25" rule)."""
    out = {}
    for key, mask in V.classify(a).items():
        ys, xs = np.nonzero(mask)
        out[key] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()),
                    int(mask.sum())) if mask.any() else None
    return out


def fmt(b):
    return "        --        " if b is None else (
        f"{b[0]:4.0f},{b[1]:4.0f}..{b[2]:4.0f},{b[3]:4.0f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", nargs="*", default=[],
                    help="default: the two shipped SVGs, plus the monogram rendered to a "
                         "temp dir from the sketch (it is not a file in logo/ any more)")
    ap.add_argument("--tol", type=float, default=TOL)
    a = ap.parse_args(argv[1:] if argv else None)
    pal = V.palette()
    bad = 0
    # `if targets is None` was the first attempt and it is wrong: with nargs="*" argparse
    # hands back [] for no arguments, so the loop body never ran, nothing was compared, and
    # the tool printed its cheerful "all engines agree" line at exit 0 -- the very failure
    # this block exists to prevent, reproduced one layer down in ten lines of code. Empty is
    # the signal, and the count of files actually compared is printed at the end.
    targets = list(a.targets)
    if not targets:
        targets = [HERE / "kwcapture.svg", HERE / "kwcapture-mark.svg"]
        # The bare monogram belongs in this comparison because it is the one artefact with no
        # rotate() -- the control that proves gotcha 27 is about transforms and not about the
        # artwork.  logo/kwcapture-mono.svg was deleted 2026-10-11 (unofficial, the owner's
        # ruling), so it is rendered from the sketch into a temp dir here, exactly as
        # preview/build.sh does for the ladder figure: a figure may hold a monogram, the
        # artwork directory may not (gotcha 38).
        tmp = Path(tempfile.mkdtemp(prefix="kw-agree-mono-"))
        atexit.register(__import__("shutil").rmtree, tmp, ignore_errors=True)
        mono = tmp / "kwcapture-mono.svg"
        try:
            subprocess.run([sys.executable, str(HERE / "gen_logo.py"), "--monogram",
                            "--out", str(mono)], check=True, capture_output=True)
            targets.append(mono)
        except Exception as e:
            print(f"NOTE the monogram control could not be rendered ({e}); "
                  f"gotcha 27's rotate-free control is MISSING from this run")
    for t in targets:
        t = Path(t)
        w, (W, H) = want(t, pal)
        print(f"# {t.name}   artboard {W:.0f}x{H:.0f}   (tolerance {a.tol:g} px)")
        if not w:
            print(f"    *** NO BRAND PAINT FOUND: nothing was compared. Palette is "
                  f"{pal or 'unknown -- gen_logo.py not importable'}; a file painted with "
                  f"anything else (a gradient, a variant) is outside this tool. ***")
            bad += 1
            continue
        for colour in ("green", "blue"):
            if colour not in w:
                continue
            print(f"  {colour:6} path data says {fmt(w[colour])}")
            for eng in ("inkscape", "qt", "msvg"):
                try:
                    g = got(rasterise(t, eng))
                except FileNotFoundError:
                    print(f"    {eng:10} not installed, SKIPPED")
                    continue
                except Exception as e:
                    print(f"    {eng:10} ERROR {e}")
                    bad += 1
                    continue
                b = g.get(colour)
                if b is None:
                    print(f"    {eng:10} {fmt(None)}  *** painted NO {colour} at all ***")
                    bad += 1
                    continue
                d = max(abs(b[0] - w[colour][0]), abs(b[1] - w[colour][1]),
                        abs(b[2] - w[colour][2]), abs(b[3] - w[colour][3]))
                off = (b[2] > W - 0.5 or b[0] < -0.5 or b[3] > H - 0.5 or b[1] < -0.5)
                tag = "ok" if d <= a.tol else f"OFF BY {d:.0f} px"
                if off:
                    tag += " and OUTSIDE the artboard"
                if d > a.tol:
                    bad += 1
                print(f"    {eng:10} {fmt(b)}  {tag}")
    if not targets:
        print("NO TARGETS: nothing was compared.")
        return 1
    print(f"\n{len(targets)} file(s) compared against the path data.  "
          + ("all engines agree" if not bad
             else f"{bad} engine/path disagreement(s) -- see the OFF lines above"))
    if bad:
        print("(the MSVG rotate() disagreements on the two lockups are gotcha 27, open, and "
              "this tool exits 1 until the owner decides it: a run that reports FEWER "
              "disagreements than that is a run that stopped looking.)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
