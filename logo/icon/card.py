#!/usr/bin/env python3
"""Build icon/github-social-preview.png — the 1280x640 card GitHub shows when the repository
is shared (Settings -> Social preview; PNG/JPEG/GIF, recommended 1280x640, max 1 MB).

Composition, and why:
  * the official logo (kwcapture-mark) on the left, not the monogram: a 1280x640 card has
    room for the word, and the word is the idea;
  * a light ground: the type is #0000ff, 2.20:1 against GitHub's #0d1117, so a dark card
    would sink the blue half of the mark in the very theme most of this audience uses;
  * every string is measured with font.getlength() and shrunk until it fits its column,
    then the script asserts nothing reached the right edge. The first version of this file
    hard-coded font sizes and printed `wrote ... 1280x640` over a card whose tagline ran off
    the canvas — a success message is not a check.

Re-run after any change to the logo:  python3 logo/icon/card.py
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 1280, 640
INK = (15, 23, 32)
SUB = (88, 100, 112)
BLUE = (0, 0, 255)
BG = (255, 255, 255)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# --- the logo, rasterised from the SVG here so the card can never drift from the artwork
tmp = HERE / ".card-logo.png"
subprocess.run(["inkscape", str(HERE.parent / "kwcapture-mark.svg"), "-o", str(tmp),
                "-w", "900", "-h", "900"], check=True, capture_output=True)
logo = Image.open(tmp).convert("RGB")
bbox = ImageChops.difference(logo, Image.new("RGB", logo.size, BG)).getbbox()
logo = logo.crop(bbox)                                   # drop the square's white margins
tmp.unlink(missing_ok=True)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# --- left: the logo, centred in a fixed column
LOGO_X, LOGO_COL = 72, 430
lg_h = 400
lg_w = int(logo.width * lg_h / logo.height)
if lg_w > LOGO_COL:                                      # never let it eat the text column
    lg_w, lg_h = LOGO_COL, int(logo.height * LOGO_COL / logo.width)
img.paste(logo.resize((lg_w, lg_h), Image.LANCZOS), (LOGO_X, (H - lg_h) // 2))

# --- right: name, tagline, facts. Every size is chosen to fit the column.
X = LOGO_X + LOGO_COL + 72
MAXW = W - X - 64
right_edge = [0]


def put(y, text, path, size, fill, maxw=MAXW, x=None):
    """Draw in the largest size <= `size` that fits `maxw`, and track the right edge.
    `x` defaults to the text column; the bullet list passes X+30 so the dot never lands on
    the first letter (it did, in the version that produced the screenshot nobody looked at)."""
    x = X if x is None else x
    while size > 10:
        fnt = ImageFont.truetype(path, size)
        w = d.textlength(text, font=fnt)
        if w <= maxw:
            break
        size -= 2
    d.text((x, y), text, font=fnt, fill=fill)
    right_edge[0] = max(right_edge[0], x + w)
    return size


put(140, "kwcapture", FB, 96, INK)
put(272, "Fast screen and window capture on Wayland,", F, 33, SUB)
put(318, "for KDE Plasma — straight to KWin.", F, 33, SUB)
d.line([(X, 388), (X + 470, 388)], fill=(224, 229, 234), width=2)

y = 416
for fact in ("~40 fps at 2560x1440",
             "per-window and per-monitor by name or id",
             "26 ms to a JPEG, zero-copy Python API"):
    d.ellipse([X, y + 12, X + 13, y + 25], fill=BLUE)
    put(y, fact, F, 30, INK, maxw=MAXW - 30, x=X + 30)
    y += 56
put(y + 6, "org.kde.KWin.ScreenShot2 — Plasma only, and it says so", F, 22, SUB)

img.save(HERE / "github-social-preview.png", optimize=True)
print(f"wrote {HERE/'github-social-preview.png'} {img.size}")
# the assertion the first version of this file lacked
if right_edge[0] > W - 24:
    raise SystemExit(f"BROKEN LAYOUT: text reached x={right_edge[0]:.0f} of {W}")
print(f"layout ok: rightmost ink x={right_edge[0]:.0f} (canvas {W}, margin {W-right_edge[0]:.0f})")
