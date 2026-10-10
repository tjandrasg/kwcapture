#!/usr/bin/env python3
"""Build the light-tile icons from the glyph PNGs: apple-touch-icon, PWA icons, maskable,
and the GitHub avatar.

Why a tile at all: the logo's type is #0000ff, which is **2.20:1 against GitHub's #0d1117**
(the number AGENTS.md keeps in its open list). A transparent icon in a dark browser tab, a
dark home screen or GitHub's dark chrome therefore loses the blue half of the mark — the C,
the A and the whole idea. A white tile fixes that without waiting for the dark-mode recolour
decision, and both Apple and GitHub apply their own masking to a square icon anyway, so the
square is the correct thing to ship.

Why the glyph and not the logo here: GitHub crops avatars to a circle, and the mark's word
runs out to the right edge — a circular crop amputates `TURE`. The monogram of the same
drawing does not. Small sizes are the glyph's job for the same reason the ladder says
`APTURE` is mush below ~64 px.

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


def tile(size, out, glyph_size=None, radius=0, src=None):
    """A white square of `size`, the glyph centred at `glyph_size` px.

    Always downscaled from glyph-1024.png rather than reading a raster of the target size:
    one source, one quality, and no dependency on which sizes build.sh happened to render.
    """
    glyph_size = glyph_size or size
    g = Image.open(src or HERE / "glyph-1024.png").convert("RGBA")
    if g.size != (glyph_size, glyph_size):
        g = g.resize((glyph_size, glyph_size), Image.LANCZOS)
    img = Image.new("RGBA", (size, size), WHITE)
    if radius:
        # supersample the mask 4x so the corner is smooth at 1x
        m = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1],
                                            radius * 4, fill=255)
        img.putalpha(m.resize((size, size), Image.LANCZOS))
    img.alpha_composite(g, ((size - glyph_size) // 2, (size - glyph_size) // 2))
    img.save(HERE / out)
    return out, img.size


BUILT = [
    tile(180, "apple-touch-icon.png", 137, radius=40),   # iOS masks it again; 76% inside
    tile(192, "pwa-192.png", 150),
    tile(512, "pwa-512.png", 400),
    tile(512, "maskable-512.png", 307),                  # maskable: keep the 80% safe zone
    tile(400, "github-avatar-400.png", 296),             # GitHub crops to a circle
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
