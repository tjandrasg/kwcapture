#!/usr/bin/env python3
"""Build the light-tile icons from the mark (`kwcapture-mark-1024.png`): apple-touch-icon,
PWA icons, maskable-512 and the GitHub avatar.

**One artwork only.** The owner's rule (2026-10-11) is that kwcapture's icon is
`../kwcapture-mark.svg`, and the permitted transforms are resize and re-render. A tile is a
*ground*, not a second drawing: the mark is composited on white at a fraction of the tile, never
cropped, never replaced by a monogram. Where a host masks the icon (GitHub's circle, iOS's
squircle, maskable's safe zone) the artwork is scaled until **no ink falls under the mask** —
measured per tile below and asserted at the end of this script, because "it will probably survive
the crop" is how the last revision ended up shipping a different logo.

Why a tile at all: the logo's type is #0000ff, which is **2.20:1 against GitHub's #0d1117**
(the number AGENTS.md keeps in its open list). A transparent icon in a dark browser tab, a
dark home screen or GitHub's dark chrome therefore loses the blue half of the mark — the C,
the A and the whole idea. A white tile fixes that without waiting for the dark-mode recolour
decision, and both Apple and GitHub apply their own masking to a square icon anyway, so the
square is the correct thing to ship.

The circular-crop arithmetic, measured rather than estimated (the mask GitHub applies is the
inscribed circle): the mark at **full bleed loses 4 015 ink pixels, worst 45.6 px beyond the
circle**, while at 79 % of the tile it loses **nothing** — the lockup's ink is wide but its
corners are empty, so it fits a circle better than its bounding box suggests. Shrinking the same
drawing is an allowed transform; inventing a second one is not.

(ImageMagick was tried first and `magick a.png b.png -gravity center -composite` returned a
blank grayscale canvas on this machine for every variation tried — white base, xc:none base,
`magick composite`, `-layers flatten`, `-type TrueColor`. Pillow is deterministic and is
already required by the render checks, so the compositing lives here.)

    python3 logo/icon/tiles.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
WHITE = (255, 255, 255, 255)


def tile(size, out, art_size=None, radius=0, src=None):
    """A white square of `size`, the mark centred at `art_size` px (a resize, never a crop).

    Always downscaled from kwcapture-mark-1024.png rather than reading a raster of the target
    size: one source, one quality, and no dependency on which sizes build.sh happened to render.
    """
    art_size = art_size or size
    g = Image.open(src or HERE / "kwcapture-mark-1024.png").convert("RGBA")
    if g.size != (art_size, art_size):
        g = g.resize((art_size, art_size), Image.LANCZOS)
    img = Image.new("RGBA", (size, size), WHITE)
    if radius:
        # supersample the mask 4x so the corner is smooth at 1x
        m = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1],
                                            radius * 4, fill=255)
        img.putalpha(m.resize((size, size), Image.LANCZOS))
    img.alpha_composite(g, ((size - art_size) // 2, (size - art_size) // 2))
    img.save(HERE / out)
    return out, img.size


# How big the mark may be on a masked tile: 79 % of the tile side, MEASURED. The largest size
# that loses no ink under the inscribed circle is 322/400 (80.5 %), 143/180 (79.4 %) and
# 413/512 (80.7 %) — the search counts the LANCZOS halo too, because a 1 px fringe is ink to a
# rasteriser. 79 % is the largest single fraction that clears all three, and the mask check at
# the end of this script fails the build if the artwork, the resampler or the mark ever changes
# enough to break it. maskable additionally caps at its 80 % safe zone.
FIT = 0.79
BUILT = [
    tile(180, "apple-touch-icon.png", int(180 * FIT), radius=40),   # iOS squircles it
    tile(192, "pwa-192.png", int(192 * FIT)),
    tile(512, "pwa-512.png", int(512 * FIT)),
    tile(512, "maskable-512.png", min(int(512 * FIT), int(512 * 0.80))),  # safe zone caps it
    tile(400, "github-avatar-400.png", int(400 * FIT)),             # GitHub crops to a circle
]

# Verify what we just wrote, rather than trusting that a compositor composited: count ink
# pixels and *chromatic* pixels straight off the file. A blank or grey tile is the failure
# mode this script exists to avoid, so it is the failure mode it checks for.
print("tiles:")
for name, size in BUILT:
    im = Image.open(HERE / name).convert("RGB")
    colours = im.getcolors(maxcolors=1 << 20) or []
    ink = sum(c for c, col in colours if col != (255, 255, 255))
    chroma = sum(c for c, (r, g, b) in colours if abs(r - b) > 12 or abs(r - g) > 12)
    ok = chroma > 200 and im.size == size
    print(f"  {name:26} {im.size[0]}x{im.size[1]}  ink px {ink:6}  coloured px {chroma:6}"
          f"  {'OK' if ok else 'BLANK OR GREY - BROKEN'}")
    if not ok:
        raise SystemExit(1)


# ---- the mask guard: which tiles lose ink when the host masks them, measured not assumed.
# A circular mask is the inscribed circle (GitHub avatars, and the worst case for maskable);
# the apple-touch squircle is approximated by the same circle, which is stricter than iOS.
import math


def ink_outside_circle(path, threshold=32):
    im = Image.open(HERE / path).convert("RGBA")
    w, h = im.size
    cx, cy, r = (w - 1) / 2.0, (h - 1) / 2.0, min(w, h) / 2.0
    px = im.load()
    n = 0
    worst = 0.0
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > threshold and px[x, y][:3] != (255, 255, 255):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    n += 1
                    worst = max(worst, d - r)
    return n, worst


print("mask check (ink the host would clip):")
failing = []
for name in ("github-avatar-400.png", "maskable-512.png", "apple-touch-icon.png"):
    n, worst = ink_outside_circle(name)
    print(f"  {name:26} clipped px {n:5}  worst overshoot {worst:5.1f} px"
          f"  {'OK' if n == 0 else 'INK UNDER THE MASK'}")
    if n:
        failing.append(name)
if failing:
    print("refusing to ship tiles whose artwork the host would cut:", ", ".join(failing))
    raise SystemExit(1)
