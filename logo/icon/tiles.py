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

Why a tile at all — and note that this reason is NOT contrast any more. Until palette P2
(2026-10-11) the type was #0000ff, **2.20:1 against GitHub's #0d1117**, and the white tile was
the answer to that failure. It is no longer: the type is now #7f7fff, 5.75:1 on the same dark
ground, and both halves of the mark clear the WCAG 3:1 non-text floor on *both* grounds
(`python3 logo/contrast_report.py`). What is left of the argument is the shape: a browser tab,
an iOS home screen, a PWA manifest slot and a GitHub avatar are all squares that get masked,
and a mark with transparent corners inside a square that a host will round or circle is the
same artwork with the host choosing its own background. The tile chooses it instead — white,
the ground every cell of `contact.png` is reviewed on — and the transparent renders stay in
the set for hosts that want them. If a future round wants the tile justified by arithmetic
again, re-run `contrast_report.py` first: on today's palette it does not say that.

The circular-crop arithmetic, measured rather than estimated (the mask GitHub applies is the
inscribed circle): the mark at **full bleed loses 4 015 ink pixels, worst 45.6 px beyond the
circle**, while at 79 % of the tile it loses **nothing** — the lockup's ink is wide but its
corners are empty, so it fits a circle better than its bounding box suggests. Shrinking the same
drawing is an allowed transform; inventing a second one is not.

(ImageMagick was tried first and `magick a.png b.png -gravity center -composite` returned a
blank grayscale canvas on this machine for every variation tried — white base, xc:none base,
`magick composite`, `-layers flatten`, `-type TrueColor`. Pillow is deterministic and is
already required by the render checks, so the compositing lives here.)

    python3 logo/icon/tiles.py           # build + verify
    python3 logo/icon/tiles.py --sweep   # and report FIT's measured headroom per masked tile
"""
import sys
import tempfile
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
#
# THE NUMBER IS TIED TO THE RASTER, NOT TO THE GEOMETRY — and palette P2 proved that the
# warning was not theoretical. The halo counted here is antialiasing, and antialiasing is a
# blend of the ink colour with the ground: swap #0000ff for #7f7fff and the same edge produces
# a different number of pixels over the alpha threshold, so a *recolour* can clip ink here
# without a single coordinate moving. If the mask check below ever reports clipped px > 0 and
# the sketch has not been touched, RE-MEASURE THIS CONSTANT (sweep the fraction, take the
# largest that clears every tile) — do not crop a tile and do not ship a second drawing, which
# is the decision that got `icon/` rebuilt in Round 13 (gotcha 38).
FIT = 0.79

# (size, name, artwork px, corner radius) — the shipped tile set, as DATA.
SPEC = [
    (180, "apple-touch-icon.png", int(180 * FIT), 40),    # iOS squircles it
    (192, "pwa-192.png", int(192 * FIT), 0),
    (512, "pwa-512.png", int(512 * FIT), 0),
    (512, "maskable-512.png", min(int(512 * FIT), int(512 * 0.80)), 0),  # safe zone caps it
    (400, "github-avatar-400.png", int(400 * FIT), 0),    # GitHub crops to a circle
]

# `--sweep` is a DIAGNOSTIC and it must not touch the artefacts it is measuring.
#
# It used to: `BUILT` was a module-level list of `tile(...)` CALLS, so importing this file for
# any reason — including `python3 tiles.py --sweep`, which only wants the FIT margin — re-saved
# all five shipped PNGs through Pillow's own encoder. `build.sh` ends by re-encoding every PNG
# in `icon/` (`magick -strip -define png:compression-level=9`), so a sweep run after a build
# left five files that no longer match what the build produces: **same pixels, different
# bytes**. That is exactly how Round 14 committed tile PNGs whose sizes disagreed with its own
# expected-numbers block, and it is the same trap as gotcha 30 in a new costume — the tool that
# measures is the tool that writes. Measured proof, before the fix: HEAD's `pwa-512.png` was
# 34 836 B / one IDAT (Pillow) against the build's 34 044 B / two IDATs (ImageMagick), with
# `ImageChops.difference().getbbox()` empty; and `build.sh` is itself byte-stable run to run,
# which is what made the sweep the only remaining suspect.
SWEEP_ONLY = "--sweep" in sys.argv
if SWEEP_ONLY:
    print("tiles: NOT written — `--sweep` measures and does not rebuild "
          "(`bash icon/build.sh` does)")
    BUILT = [(name, (size, size)) for size, name, _art, _r in SPEC]
else:
    BUILT = [tile(size, name, art, radius=rad) for size, name, art, rad in SPEC]

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
    print("if the sketch did not move and only the PAINT did, FIT is the number that went "
          "stale: re-measure it (`python3 tiles.py --sweep`), never crop the tile.")
    raise SystemExit(1)


if "--sweep" in sys.argv:
    # How much room is left between FIT and the first clipped pixel? Measured, because "0
    # clipped px" says nothing about the margin, and the margin is what a recolour eats. The
    # answer is a fraction per tile; FIT must clear the worst of them, and this prints the
    # worst so the next round can see how close it is running.
    print("\nFIT sweep (largest artwork fraction that still loses no ink):")
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="kw-fit-sweep-"))
    worst_fit = 1.0
    try:
        for size, name in ((400, "github-avatar-400.png"), (512, "maskable-512.png"),
                           (180, "apple-touch-icon.png")):
            probe = tmp / "probe.png"

            def clears(art):
                tile(size, probe, art, radius=40 if "apple" in name else 0,
                     src=HERE / "kwcapture-mark-1024.png")
                return ink_outside_circle(probe)[0] == 0

            # bisect: bigger artwork can only ever reach further out, so "clears" is monotone
            lo, hi = int(size * FIT), size
            if not clears(lo):
                print(f"  {name:26} FIT ALREADY CLIPS at {lo}px — re-measure before shipping")
                raise SystemExit(1)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                lo, hi = (mid, hi) if clears(mid) else (lo, mid)
            worst_fit = min(worst_fit, lo / size)
            print(f"  {name:26} largest artwork that loses no ink: {lo}px of {size} "
                  f"({lo / size:.3f}) — FIT {FIT:.3f} has {(lo - int(size * FIT))}px "
                  f"/ {100 * (lo / size - FIT):+.1f} % of headroom")
        print(f"  worst across the three: {worst_fit:.3f}; FIT = {FIT:.3f} "
              f"({100 * (worst_fit - FIT):+.1f} % of the side in hand)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
