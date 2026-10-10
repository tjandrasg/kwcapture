#!/usr/bin/env python3
"""Build preview/anatomy.png — the one figure that explains the mark.

Three rows, each the shipped mark with one part boxed, because the whole design is
that one part of the picture is a monogram stroke, one part is a mouse pointer and one
part is type. The boxes are not eyeballed: they are the ink boxes validate_logo.py
reports for #a and #wordmark and the one computed from #kw-c's own path data, i.e. the
same boxes the validator measures on the emitted SVG.

    python3 logo/preview/anatomy.py     # after re-rendering kwcapture-mark-512.png
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ink boxes at 512 px, measured off the shipped kwcapture-mark.svg
ROWS = [
    ("C", (64.4, 126.8, 263.3, 449.9), (208, 2, 27),
     "the junction of the hand-drawn K and W",
     "part of #kw / #kw-c — the monogram, never type"),
    ("A", (256.9, 234.4, 327.6, 321.5), (126, 87, 194),
     "the hand-drawn mouse pointer, laid out as a letter",
     "#a inside #type — the cap height and width of a real A"),
    ("PTURE", (276.9, 60.1, 504.6, 281.4), (2, 119, 189),
     "the only typeset letters in the whole mark",
     "#wordmark — glyph outlines from Inter ExtraBold"),
]

TILE, ROWH, PAD = 230, 250, 16
W, H = 980, ROWH * 3 + 74
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
big, txt, small, foot = (ImageFont.truetype(FB, 30), ImageFont.truetype(F, 19),
                         ImageFont.truetype(F, 16), ImageFont.truetype(FB, 17))
base = Image.open(HERE / "kwcapture-mark-512.png").convert("RGB")

for i, (name, (x0, y0, x1, y1), col, what, how) in enumerate(ROWS):
    y = i * ROWH + PAD
    tile = base.resize((TILE, TILE), Image.LANCZOS)
    img.paste(tile, (PAD, y))
    s = TILE / 512.0
    bx = (PAD + x0 * s, y + y0 * s, PAD + x1 * s, y + y1 * s)
    d.rectangle(bx, outline=col, width=3)
    tx = PAD + TILE + 46
    d.line([(bx[2] if bx[2] < tx else (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2),
            (tx - 10, y + 30)], fill=col, width=2)
    d.text((tx, y + 10), name, font=big, fill=col)
    d.text((tx, y + 62), what, font=txt, fill="#222")
    d.text((tx, y + 90), how, font=small, fill="#666")

d.line([(PAD, H - 52), (W - PAD, H - 52)], fill="#ccc")
d.text((PAD, H - 40), "CAPTURE  =  C (drawn into the monogram)  +  A (the pointer)  "
                      "+  PTURE (type)", font=foot, fill="#111")
d.text((PAD + 620, H - 40),
       "WORD in gen_logo.py is \"PTURE\". Setting WORD=\"CAPTURE\" renders CACAPTURE.",
       font=small, fill="#777")
img.save(HERE / "anatomy.png")
print("wrote", HERE / "anatomy.png", img.size)
