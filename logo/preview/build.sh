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

# ------------------------------- the official mark vs the glyph, down to icon size (README §8)
# Same question as the two ladders above, but on the *shipped* pair: at which pixel size does
# the word stop paying for itself? Measured by rendering, not by guessing: the word is legible
# at 128, marginal at 64 and mush at 48 and below, while the glyph still reads at 32.
for n in 128 64 48 32; do
  ink "$L/kwcapture-mark.svg"           -o "$T/mark-$n.png"  -b white -w "$n" -h "$n"
  ink "$L/icon/kwcapture-mark-mono.svg" -o "$T/glyph-$n.png" -b white -w "$n" -h "$n"
done
args=(); for n in 128 64 48 32; do args+=(-label "mark  ${n}px" "$T/mark-$n.png"); done
for n in 128 64 48 32; do args+=(-label "glyph  ${n}px" "$T/glyph-$n.png"); done
magick montage "${args[@]}" -tile 4x2 -geometry 128x128 -background white \
  -fill '#333' -pointsize 20 -font "$FONT" ladder-icon.png

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
