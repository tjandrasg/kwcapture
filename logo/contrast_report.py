#!/usr/bin/env python3
"""contrast_report.py — the instrument behind every contrast ratio this folder quotes.

    python3 logo/contrast_report.py                 # the palette in gen_logo.py
    python3 logo/contrast_report.py '#00ac4e' '#0000ff'   # any two colours

`logo/AGENTS.md` and `logo/README.md` §8 quote WCAG ratios, and for two rounds the numbers
were typed in from a session that had computed them by hand. A ratio you cannot re-run is a
claim, so this file is the re-run: it prints the 2x2 table (each half of the palette against
each ground), the half-vs-half separation, the luminance window that the two-grounds problem
lives in, and a dichromatic check on the split. Every number it prints comes from the WCAG
relative-luminance formula and the hex values, both below, and from nothing else.

What the tool is for, concretely:

  * the two GROUNDS are the two a user actually meets — GitHub light `#ffffff` and GitHub
    dark `#0d1117` — and the floor is WCAG 2.x's 3:1 for NON-TEXT content (graphical objects,
    1.4.11), not the 4.5:1 for body text. The mark has no text at 12 px in it.
  * `--min` fails the run when any cell drops below the floor, so a recolour cannot ship a
    regression by accident: exit 1 is the answer to "is this palette legal on both grounds?".
  * the WINDOW lines explain why "both halves legal on both grounds" and "a loud two-tone
    split" fight each other. A colour clears 3:1 on white only if L <= 1.05/3 - 0.05 and on
    `#0d1117` only if L >= 3*(L_dark + 0.05) - 0.05; the two bounds are one narrow band, so
    two colours inside it cannot be far apart. That is arithmetic, not taste, and it is the
    reason the 2026-10-11 palette decision traded split strength for legality.
  * the dichromatic block exists because the split carries the C: if green and blue collapse
    for a deuteranope, the first letter of the word is gone whatever the ratios say. It is a
    Brettel/Viénot-style simulation in LMS space, which is an ESTIMATE, not a measurement of
    any person's vision — treat it as a smoke test, and see logo/AGENTS.md on the stranger
    test this folder still owes.

Exit code: 0 if every colour clears `--min` on every ground (default 3.0), 1 otherwise.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

WHITE = "#ffffff"
DARK = "#0d1117"          # GitHub's dark canvas, the ground preview/on-dark.png is about


# ------------------------------------------------------------- the WCAG 2.x formulae
def srgb_to_linear(c):
    """One 0..255 channel to its linear-light value (WCAG 2.x definition)."""
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(h):
    h = h.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise SystemExit(f"not a 6-digit hex colour: {h!r} (say e.g. '#008c46')")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(h):
    r, g, b = (srgb_to_linear(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------- the luminance window for "legal on both"
def window(floor, ground_light=WHITE, ground_dark=DARK):
    """(L_min, L_max): the relative-luminance band a colour must sit in to clear `floor`
    on BOTH grounds. Derived from the formula above, so it moves with --min."""
    hi = (luminance(ground_light) + 0.05) / floor - 0.05
    lo = floor * (luminance(ground_dark) + 0.05) - 0.05
    return lo, hi


# ------------------------------------------------ dichromatic simulation (an estimate)
# Viénot, Brettel & Mollon (1999) style: linear sRGB -> Hunt-Pointer-Estevez LMS -> collapse
# the missing cone's channel to what the other two predict -> back. Widely used, and a rough
# approximation of a rough topic; the point is only "does the split survive".
_LMS = ((0.4002, 0.7076, -0.0808),
        (-0.2263, 1.16532, 0.0457),
        (0.0, 0.0, 0.9182))


def _inv3(m):
    """Inverse of a 3x3, solved here rather than hard-coded: a magic inverse matrix cannot be
    checked by the reader, and `simulate()` is only as honest as this one multiply."""
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
           - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
           + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    if abs(det) < 1e-12:
        raise SystemExit("the LMS matrix is singular; the simulation cannot be inverted")
    co = [[(m[(j + 1) % 3][(k + 1) % 3] * m[(j + 2) % 3][(k + 2) % 3]
            - m[(j + 1) % 3][(k + 2) % 3] * m[(j + 2) % 3][(k + 1) % 3]) / det
           for j in range(3)] for k in range(3)]
    return co


_LMS_INV = _inv3(_LMS)
_SIM = {                    # matrices in LMS space, from Viénot & Brettel 1999 (as tabulated)
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048119, 1.052001)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047414),
                     (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779),
                   (-0.078411, 0.930809, 0.147602),
                   (0.004733, 0.691367, 0.303900)),
}


def _mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def simulate(h, kind):
    """The hex a person with `kind` of colour vision is estimated to see, as a hex."""
    lin = [srgb_to_linear(c) for c in rgb(h)]
    lms = _mul(_LMS, lin)
    sim = _mul(_SIM[kind], lms)
    back = _mul(_LMS_INV, sim)
    out = []
    for v in back:
        v = min(1.0, max(0.0, v))                       # clip: simulation is not colour-managed
        out.append(round(255 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4)
                                - 0.055)))
    return "#{:02x}{:02x}{:02x}".format(*out)


def delta_e76(h1, h2):
    """CIE76 distance in Lab (D65) — crude, but monotone enough to ask 'far apart or not'."""
    def lab(h):
        r, g, b = (srgb_to_linear(c) for c in rgb(h))
        x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
        f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
        fx, fy, fz = f(x), f(y), f(z)
        return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
    a, c = lab(h1), lab(h2)
    return sum((p - q) ** 2 for p, q in zip(a, c)) ** 0.5


def palette_from_generator():
    """GREEN and BLUE exactly as gen_logo.py defines them — so the report cannot drift
    from the artwork. Parsed, not imported: gen_logo needs fontTools, this must not."""
    txt = (HERE / "gen_logo.py").read_text()
    out = []
    for name in ("GREEN", "BLUE"):
        m = re.search(rf'^{name}\s*=\s*"([^"]+)"', txt, re.M)
        if not m:
            raise SystemExit(f"cannot find {name} in gen_logo.py — the report and the "
                             f"artwork must be checked against the same source")
        out.append(m.group(1))
    return tuple(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("colours", nargs="*", metavar="HEX",
                    help="two colours; default gen_logo.py's GREEN and BLUE")
    ap.add_argument("--min", type=float, default=3.0, dest="floor",
                    help="floor to enforce on every cell (default 3.0, WCAG non-text)")
    a = ap.parse_args(argv[1:] if argv else None)
    cols = a.colours or list(palette_from_generator())
    if len(cols) != 2:
        raise SystemExit("give exactly two colours, or none for the palette")
    green, blue = cols
    lo, hi = window(a.floor)

    print(f"grounds: light {WHITE} (L {luminance(WHITE):.4f}),  dark {DARK} "
          f"(L {luminance(DARK):.4f});  floor {a.floor:g}:1 (WCAG non-text, 1.4.11)")
    print(f"{'colour':9} {'lum':>7} {'vs white':>9} {'vs dark':>9}   verdict")
    fail = []
    for name, h in (("green", green), ("blue", blue)):
        cw, cd = contrast(h, WHITE), contrast(h, DARK)
        bad = [g for g, c in ((WHITE, cw), (DARK, cd)) if c < a.floor]
        if bad:
            fail.append(f"{name} {h} is {min(contrast(h, b) for b in bad):.2f}:1 on "
                        + ", ".join(bad))
        print(f"{h}{'':>2} {luminance(h):7.4f} {cw:9.2f} {cd:9.2f}   "
              f"{'clears both' if not bad else 'FAILS on ' + ', '.join(bad)}")
    split = contrast(green, blue)
    print(f"\nsplit green-vs-blue: {split:.2f}:1   (this is what makes the C read; "
          f"hue separation only, not lightness)")

    print(f"\nwindow: to clear {a.floor:g}:1 on BOTH grounds a colour's relative luminance "
          f"must be in [{lo:.4f}, {hi:.4f}]")
    print(f"  two colours inside that window can separate by at most "
          f"{(hi + 0.05) / (lo + 0.05):.2f}:1 — both-halves-legal and a loud split are in "
          f"tension by arithmetic")
    for name, h in (("green", green), ("blue", blue)):
        inside = lo <= luminance(h) <= hi
        print(f"  {name:5} {h}: L {luminance(h):.4f} {'inside' if inside else 'OUTSIDE'} "
              f"the window")

    print("\ndichromatic estimate (Viénot/Brettel LMS; an estimate, not a person):")
    print(f"  {'type':13} {'green as':9} {'blue as':9} {'ΔE76':>7} {'ratio':>7}  vs the "
          f"{contrast(green, blue):.2f} normal-vision split")
    for kind in ("protanopia", "deuteranopia", "tritanopia"):
        g, b = simulate(green, kind), simulate(blue, kind)
        print(f"  {kind:13} {g} {b} {delta_e76(g, b):7.1f} {contrast(g, b):7.2f}")

    if fail:
        print("\nFAIL: " + "; ".join(fail))
        return 1
    print(f"\nOK: both halves clear {a.floor:g}:1 on both grounds.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
