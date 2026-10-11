#!/usr/bin/env python3
"""Build icon/contact.png — one sheet showing what every shipped icon actually looks like,
on the ground it will be seen on, at (or scaled from) its shipped size.

This exists because a list of filenames is not a review. It is also the sheet that catches
*this* class of mistake: an icon set that quietly stopped being one artwork. Every cell here is
the same mark — `../kwcapture-mark.svg` — resized, on a ground; there is no monogram cell, and
adding one would be the owner's decision, not a build step's.

Two things it settles by showing:
  * the circular crop GitHub applies, and that the avatar's 81 % artwork survives it with zero
    ink lost (the previous revision claimed a circular crop "amputates TURE" and answered that by
    shipping the monogram. Measured at full bleed it does lose 4 015 px / 45.6 px overshoot — and
    the fix was the scale, not a second drawing: `tiles.py` asserts zero clipped ink);
  * the grounds. Blue #0000ff is 2.20:1 against GitHub's #0d1117 — under the 3:1 WCAG figure
    for graphical objects — while the green is 6.32:1 there. On white it is the green that is
    borderline (3.00:1) and the blue that is strong (8.59:1). No ground wins both, so the
    tiled icons pick the *light* ground (both halves clear 3:1) and the transparent renders
    stay in the set for hosts that want them.

    python3 logo/icon/contact.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DARK = (13, 17, 23)
LIGHT = (255, 255, 255)
CELL, PAD, LAB = 168, 14, 44
COLS = 6

# (file, label, ground, display size, circular crop?)
CARDS = [
    ("kwcapture-mark-256.png", "mark 256 · light", LIGHT, 140, False),
    ("kwcapture-mark-128.png", "mark 128 · GitHub dark", DARK, 128, False),
    ("kwcapture-mark-64.png", "mark 64 · GitHub dark", DARK, 64, False),
    ("kwcapture-mark-32.png", "mark 32 · favicon size", DARK, 32, False),
    ("github-avatar-400.png", "avatar 400 · tiled, circle crop", DARK, 140, True),
    ("apple-touch-icon.png", "apple-touch 180 · tiled, 1:1", DARK, 180, False),
]


def fit(d, text, size, maxw, path=F):
    while size > 8 and d.textlength(text, font=ImageFont.truetype(path, size)) > maxw:
        size -= 1
    return ImageFont.truetype(path, size)


def circular(im):
    s = im.size[0]
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse([0, 0, s - 1, s - 1], fill=255)
    out = im.convert("RGBA").copy()
    out.putalpha(m)
    return out


rows = (len(CARDS) + COLS - 1) // COLS
W = COLS * (CELL + PAD) + PAD
H = rows * (CELL + LAB + PAD) + PAD
sheet = Image.new("RGB", (W, H), (247, 248, 250))
d = ImageDraw.Draw(sheet)

for i, (fname, label, ground, disp, crop) in enumerate(CARDS):
    r, c = divmod(i, COLS)
    x = PAD + c * (CELL + PAD)
    y = PAD + r * (CELL + LAB + PAD)
    d.rounded_rectangle([x, y, x + CELL, y + CELL + LAB], radius=10, fill=(255, 255, 255),
                        outline=(222, 226, 230))
    d.rectangle([x + 12, y + 12, x + CELL - 12, y + CELL - 12], fill=ground)
    im = Image.open(HERE / fname).convert("RGBA")
    if crop:
        im = circular(im)
    if im.size != (disp, disp):
        im = im.resize((disp, disp), Image.LANCZOS)
    base = Image.new("RGBA", (CELL - 24, CELL - 24), ground + (255,))
    base.alpha_composite(im, ((CELL - 24 - disp) // 2, (CELL - 24 - disp) // 2))
    sheet.paste(base.convert("RGB"), (x + 12, y + 12))
    kb = (HERE / fname).stat().st_size
    d.text((x + 12, y + CELL - 4), label, font=fit(d, f"{label}  {kb // 1024} KB", 15, CELL - 24),
           fill=(70, 78, 86))

sheet.save(HERE / "contact.png")
print(f"wrote {HERE/'contact.png'} {sheet.size}")
