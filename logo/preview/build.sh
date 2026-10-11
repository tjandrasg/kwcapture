#!/usr/bin/env bash
# Rebuild every PNG in this directory from the SVGs in ../. Nothing here is hand-made:
# each image is one command, and the commands below are the ones quoted in ../README.md.
#
#   cd logo && bash preview/build.sh          # needs inkscape, ImageMagick, PyQt6+PIL
#
# Previews are DERIVED artefacts, like the SVGs: regenerate rather than edit. The variant
# SVGs go to a temp dir, never into logo/, because a paint variant written to a default
# path would replace a shipped file (gen_logo.py now refuses that, but do not lean on it).
set -euo pipefail
cd "$(dirname "$0")"
L="$(pwd)/.."
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
# inkscape is chatty about the accessibility bus; its exit code is what we check
ink() { inkscape "$@" >/dev/null 2>&1; }

# ---------------------------------------------------------------- the three artefacts
ink "$L/kwcapture.svg"      -o kwcapture-512.png      -b white -w 512 -h 512
ink "$L/kwcapture-mark.svg" -o kwcapture-mark-512.png -b white -w 512 -h 512
ink "$L/kwcapture-mono.svg" -o kwcapture-mono-512.png -b white -w 512 -h 512

# ------------------------------------------------------------- the two inputs (sketches)
ink "$L/kwcapture-sketch.svg"      -o sketch-source-512.png      -b white -w 512 -h 512
ink "$L/kwcapture-mark-sketch.svg" -o sketch-mark-source-512.png -b white -w 512 -h 512

# ------------------------------------------------------------------- the icon ladders
for n in 512 256 128 64 32; do
  ink "$L/kwcapture.svg"      -o "$T/full-$n.png" -b white -w "$n" -h "$n"
  ink "$L/kwcapture-mono.svg" -o "$T/mono-$n.png" -b white -w "$n" -h "$n"
done
args=(); for n in 512 256 128 64 32; do args+=(-label "${n}" "$T/full-$n.png"); done
magick montage "${args[@]}" -tile 5x1 -geometry 170x170+10+10 -background white \
  -fill '#333' -pointsize 26 -font "$FONT" -title 'kwcapture.svg' ladder-kwcapture.png
args=(); for n in 512 256 128 64 32; do args+=(-label "${n}" "$T/mono-$n.png"); done
magick montage "${args[@]}" -tile 5x1 -geometry 170x170+10+10 -background white \
  -fill '#333' -pointsize 26 -font "$FONT" -title 'kwcapture-mono.svg' ladder-mono.png

# ------------------------------- the legibility ladder, measured (README §8)
# At which pixel size does the word stop paying for itself? Measured by rendering, not by
# guessing: legible at 128, marginal at 64, mush at 48 and below, while the bare monogram still
# reads at 32. That is a MEASUREMENT, not a shipping decision: the shipped icon is
# `kwcapture-mark.svg` at every size, including the sizes where the word is mush (owner's rule,
# 2026-10-11). The monogram row is rendered from the sketch on the fly, into $T, precisely so
# that no monogram file sits in icon/ looking like an approved icon.
python3 "$L/gen_logo.py" --monogram --sketch "$L/kwcapture-mark-sketch.svg" \
        --out "$T/mono-src.svg" >/dev/null
for n in 128 64 48 32; do
  ink "$L/kwcapture-mark.svg" -o "$T/mark-$n.png"  -b white -w "$n" -h "$n"
  ink "$T/mono-src.svg"       -o "$T/mono-$n.png" -b white -w "$n" -h "$n"
done
# Text geometry, MEASURED, because every way of getting it wrong here is silent. A `-label` wider
# than its tile (art + 2*border) runs under the neighbouring cell; and `montage -title` draws its
# title at a scale that is NOT the `-pointsize` you passed, cropping it at both ends when it
# overflows — measured: a title Pillow puts at 491 px in DejaVu 18 rendered wider than the 704 px
# canvas and lost characters at each end, exit 0. The first version of this figure was 512x360 and
# read "…d mark (top) vs the monog…": the caption that exists to say *NOT an icon* was itself cut
# off. Gotcha 30's family again — the thing that reports is the thing nobody checked. So: labels
# are sized from Pillow's metrics against the real tile width, the body is montaged WITHOUT a
# title, and the title is drawn by Pillow at a size solved from those metrics and asserted to fit
# before a pixel of it is drawn. Exits 1 rather than shipping a clipped figure.
TILE=176                      # 128 px art + 2 x 24 px border
CANVAS=$((TILE * 4))          # 4 columns — what the title has to fit inside
TITLE_A='legibility ladder: the shipped mark (top)'
TITLE_B='vs the monogram (bottom): the CONTROL, not an icon'
args=(); for n in 128 64 48 32; do args+=(-label "mark ${n}px" "$T/mark-$n.png"); done
for n in 128 64 48 32; do args+=(-label "monogram ${n}px" "$T/mono-$n.png"); done
# `montage -title` is not measurable: it renders the title at a scale that is not the `-pointsize`
# you passed (measured: a two-line title PIL puts at 491 px in DejaVu 18 came out wider than the
# 704 px canvas and was cropped at BOTH ends, silently, exit 0). So the body is montaged without a
# title and the title is drawn afterwards with Pillow, whose metrics are the ones we can assert on.
LABEL_PS=$(python3 - "$FONT" "$TILE" "mark 128px" "monogram 128px" <<'PY'
import sys
from PIL import ImageFont
font, tile, *labels = sys.argv[1:]
tile = int(tile) - 8
ps = 20
for ln in labels:
    w = ImageFont.truetype(font, ps).getlength(ln)
    if w > tile:
        ps = int(ps * tile / w)
if ps < 12:
    sys.exit(f"labels need pointsize {ps} to fit a {tile}px tile: shorten them")
print(ps)
PY
)
magick montage "${args[@]}" -tile 4x2 -geometry 128x128+24+24 -background white \
  -fill '#333' -pointsize "$LABEL_PS" -font "$FONT" "$T/body.png"

python3 - "$FONT" "$T/body.png" "$TITLE_A" "$TITLE_B" ladder-icon.png <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont
font_path, body, title_a, title_b, out = sys.argv[1:6]
body = Image.open(body).convert("RGB")
band = 96                                   # two title lines + margins
canvas = body.width
font = ImageFont.truetype(font_path, 20)
ps = 20
for ln in (title_a, title_b):
    w = font.getlength(ln)
    if w > canvas - 48:                     # 24 px of air each side
        ps = min(ps, int(20 * (canvas - 48) / w))
if ps < 12:
    sys.exit(f"title needs pointsize {ps} for a {canvas}px canvas: shorten it")
font = ImageFont.truetype(font_path, ps)
im = Image.new("RGB", (canvas, body.height + band), "white")
d = ImageDraw.Draw(im)
y = 16
for ln in (title_a, title_b):
    w = font.getlength(ln)
    if w > canvas:                          # cannot happen by construction; assert anyway
        sys.exit(f"title line still overflows ({w:.0f} px in {canvas}px): {ln!r}")
    d.text(((canvas - w) / 2, y), ln, font=font, fill=(51, 51, 51))
    y += ps + 12
im.paste(body, (0, band))
im.save(out)
print(f"  {out}: {canvas}x{im.height}, title drawn at pointsize {ps} "
      f"(widest line {max(font.getlength(l) for l in (title_a, title_b)):.0f} px of {canvas})")
PY
magick identify -format 'ladder-icon.png  %wx%h  %b\n' ladder-icon.png

# ------------------------------------------------- the knobs, as generated variants
python3 "$L/gen_logo.py" --mark --out "$T/nofill.svg"  --no-height-fill   >/dev/null
python3 "$L/gen_logo.py" --mark --out "$T/s135.svg"    --max-stretch 1.35 >/dev/null
python3 "$L/gen_logo.py"         --out "$T/classic.svg" --classic         >/dev/null
python3 "$L/gen_logo.py"         --out "$T/nosplit.svg" --no-c-split      >/dev/null
for v in nofill s135 classic nosplit; do ink "$T/$v.svg" -o "$T/$v.png" -b white -w 512 -h 512; done
magick montage \
  -label 'shipped\nx1.753'                kwcapture-mark-512.png \
  -label 'no-height-fill'                 "$T/nofill.png" \
  -label 'max-stretch\n1.35'              "$T/s135.png" \
  -tile 3x1 -geometry 260x260+14+14 -background white -fill '#333' -pointsize 22 \
  -font "$FONT" variants-type.png
magick montage \
  -label 'shipped\ntwo-tone'              kwcapture-512.png \
  -label 'classic\ngradient, black'       "$T/classic.png" \
  -label 'no-c-split\nall green'          "$T/nosplit.png" \
  -tile 3x1 -geometry 260x260+14+14 -background white -fill '#333' -pointsize 22 \
  -font "$FONT" variants-paint.png

# ------------------------------------------------------------------- dark surfaces
ink "$L/kwcapture.svg"      -o "$T/d1.png" -b '#0d1117' -w 400 -h 400
ink "$L/kwcapture-mark.svg" -o "$T/d2.png" -b '#0d1117' -w 400 -h 400
ink "$L/kwcapture-mono.svg" -o "$T/d3.png" -b '#0d1117' -w 400 -h 400
magick montage -label 'kwcapture\n(full)' "$T/d1.png" -label 'kwcapture\n-mark' "$T/d2.png" \
  -label 'kwcapture\n-mono' "$T/d3.png" -tile 3x1 -geometry 260x260+14+14 \
  -background '#0d1117' -fill '#c9d1d9' -pointsize 22 -font "$FONT" on-dark.png

# ------------------------------------------- the MSVG rotate() bug, painted not described
python3 - "$L" "$T" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import render_agreement as R
from PIL import Image
for f, tag in (("kwcapture.svg", "full"), ("kwcapture-mark.svg", "mark")):
    for eng in ("qt", "msvg"):
        Image.fromarray(R.rasterise(f"{sys.argv[1]}/{f}", eng, 512).astype("uint8")).save(
            f"{sys.argv[2]}/{tag}-{eng}.png")
PY
magick montage -label 'QtSvg\nGwenview, Dolphin, QIcon' "$T/full-qt.png" \
  -label 'MSVG\n26 px off' "$T/full-msvg.png" \
  -label 'QtSvg\ncorrect' "$T/mark-qt.png" \
  -label 'MSVG\n67 px off, clipped' "$T/mark-msvg.png" \
  -tile 2x2 -geometry 280x280+14+14 -background white -fill '#333' -pointsize 22 \
  -font "$FONT" msvg-rotate-bug.png

python3 anatomy.py
for f in *.png; do magick "$f" -depth 8 -strip -define png:compression-level=9 "$f"; done
ls -la
