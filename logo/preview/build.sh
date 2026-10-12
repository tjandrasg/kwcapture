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
# inkscape is chatty about the accessibility bus, so its chatter is dropped — but the RESULT is
# checked, because "the thing that reports is the thing nobody checks" (gotcha 30, and this
# script's own gotcha 39). The old one-liner sent inkscape's exit code to the bit bucket along
# with its stderr: an unreadable input or a failed render left the PREVIOUS PNG in place, which
# during a recolour means a figure silently keeps the old palette while the build prints nothing.
# So: the input must exist, inkscape must exit 0, and the named output must exist and be
# non-empty afterwards. Three ways to fail, and each one says which.
ink() {
  local src="$1" out="" prev="" a
  shift
  [ -f "$src" ] || { echo "ink: no such input: $src" >&2; exit 1; }
  for a in "$@"; do
    if [ "$prev" = "-o" ]; then out="$a"; fi
    prev="$a"
  done
  [ -n "$out" ] || { echo "ink: no -o output argument for $src" >&2; exit 1; }
  inkscape "$src" "$@" >/dev/null 2>&1 \
    || { echo "ink: inkscape failed on $src (args: $*)" >&2; exit 1; }
  [ -s "$out" ] || { echo "ink: $src produced no non-empty output at $out" >&2; exit 1; }
}

# ---------------------------------------------------------------- the three artefacts
# The third is the bare MONOGRAM, and it is generated into $T, not read from logo/: there is no
# logo/kwcapture-mono.svg any more. The owner ruled it unofficial and historical on 2026-10-11,
# so it is deleted, `--monogram` survives as a mode, and a FIGURE may still show it — while the
# artwork directory must not, because an artefact next to the approved artwork eventually gets
# mistaken for it (gotcha 38, which is the lesson this line implements one folder up).
ink "$L/kwcapture.svg"      -o kwcapture-512.png      -b white -w 512 -h 512
ink "$L/kwcapture-mark.svg" -o kwcapture-mark-512.png -b white -w 512 -h 512
python3 "$L/gen_logo.py" --monogram --out "$T/mono-orig.svg" >/dev/null
ink "$T/mono-orig.svg"    -o kwcapture-mono-512.png   -b white -w 512 -h 512

# ------------------------------------------------------------- the two inputs (sketches)
ink "$L/kwcapture-sketch.svg"      -o sketch-source-512.png      -b white -w 512 -h 512
ink "$L/kwcapture-mark-sketch.svg" -o sketch-mark-source-512.png -b white -w 512 -h 512

# ------------------------------------------------------------------- the icon ladders
# Two DIFFERENT monograms appear in this script and the file names say which: mono-orig is the
# ORIGINAL drawing (`--monogram`, kwcapture-sketch.svg) used by the two size ladders, and
# mono-mark is the REDRAWN mark's monogram (`--monogram --sketch kwcapture-mark-sketch.svg`)
# used as the CONTROL row of the legibility figure. Naming them apart is not fussiness: the
# previous version read one SVG from logo/ for both, and they are different drawings.
for n in 512 256 128 64 32; do
  ink "$L/kwcapture.svg"   -o "$T/full-$n.png"      -b white -w "$n" -h "$n"
  ink "$T/mono-orig.svg"   -o "$T/mono-orig-$n.png" -b white -w "$n" -h "$n"
done
#
# EVERY title in this script is drawn by Pillow, never by `montage -title`, and the reason is
# gotcha 39: montage renders a title at a scale that is not the `-pointsize` you passed and
# CROPS whatever overflows, at exit 0. The first version of one of these figures shipped reading
# "…d mark (top) vs the monog…" — a caption amputated at both ends, into the README, because the
# tool said nothing. So: montage the body WITHOUT a title, then draw the title at a size solved
# from Pillow's own metrics and asserted to fit before a pixel of it is drawn, and print the
# measured ink extents so the figure can be re-checked without opening it.
draw_title() {
  # draw_title <body.png> <out.png> <bg> <fg> <line> [line2]
  python3 - "$FONT" "$@" <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont
font_path, body, out, bg, fg = sys.argv[1:6]
lines = sys.argv[6:]
body = Image.open(body).convert("RGB")
canvas = body.width
band = 20 + len(lines) * 32 + 24
font = ImageFont.truetype(font_path, 20)
ps = 20
for ln in lines:
    w = font.getlength(ln)
    if w > canvas - 48:
        ps = min(ps, int(20 * (canvas - 48) / w))
if ps < 12:
    sys.exit(f"title needs pointsize {ps} for a {canvas}px canvas: shorten it")
font = ImageFont.truetype(font_path, ps)
im = Image.new("RGB", (canvas, body.height + band), bg)
d = ImageDraw.Draw(im)
y = 20
for ln in lines:
    w = font.getlength(ln)
    if w > canvas:                        # cannot happen by construction; assert anyway
        sys.exit(f"title line still overflows ({w:.0f} px in {canvas}px): {ln!r}")
    d.text(((canvas - w) / 2, y), ln, font=font, fill=fg)
    y += ps + 12
im.paste(body, (0, band))
im.save(out)
widest = max(font.getlength(l) for l in lines)
print(f"  {out}: {canvas}x{im.height}, title at pointsize {ps}, widest line "
      f"{widest:.0f} px of {canvas} -> {canvas - widest:.0f} px of air")
PY
}
args=(); for n in 512 256 128 64 32; do args+=(-label "${n}" "$T/full-$n.png"); done
magick montage "${args[@]}" -tile 5x1 -geometry 170x170+10+10 -background white \
  -fill '#333' -pointsize 26 -font "$FONT" "$T/lk.png"
draw_title "$T/lk.png" ladder-kwcapture.png '#ffffff' '#333333' \
  'kwcapture.svg — the original drawing, plus APTURE at -38 degrees'

# ------------------------------- the legibility ladder, measured (README §8)
# (the monogram row of THIS figure is the mark's own monogram, hence a different --sketch than
#  the $T/mono-orig.svg the two ladders above use: that one is the original drawing)
# At which pixel size does the word stop paying for itself? Measured by rendering, not by
# guessing: legible at 128, marginal at 64, mush at 48 and below, while the bare monogram still
# reads at 32. That is a MEASUREMENT, not a shipping decision: the shipped icon is
# `kwcapture-mark.svg` at every size, including the sizes where the word is mush (owner's rule,
# 2026-10-11). The monogram row is rendered from the sketch on the fly, into $T, precisely so
# that no monogram file sits in icon/ looking like an approved icon.
args=(); for n in 512 256 128 64 32; do args+=(-label "${n}" "$T/mono-orig-$n.png"); done
magick montage "${args[@]}" -tile 5x1 -geometry 170x170+10+10 -background white \
  -fill '#333' -pointsize 26 -font "$FONT" "$T/lm.png"
draw_title "$T/lm.png" ladder-mono.png '#ffffff' '#333333' \
  'the monogram — gen_logo.py --monogram, a MODE: there is no shipped mono file'
# The mark's OWN monogram, rendered from the mark sketch into $T for the control row below.
python3 "$L/gen_logo.py" --monogram --sketch "$L/kwcapture-mark-sketch.svg" \
        --out "$T/mono-mark.svg" >/dev/null
for n in 128 64 48 32; do
  ink "$L/kwcapture-mark.svg" -o "$T/mark-$n.png"      -b white -w "$n" -h "$n"
  ink "$T/mono-mark.svg"      -o "$T/mono-mark-$n.png" -b white -w "$n" -h "$n"
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
for n in 128 64 48 32; do args+=(-label "monogram ${n}px" "$T/mono-mark-$n.png"); done
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
draw_title "$T/body.png" ladder-icon.png '#ffffff' '#333333' "$TITLE_A" "$TITLE_B"
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
# This figure used to exist to show a FAILURE: the type was #0000ff, 2.20:1 on GitHub dark
# #0d1117, under the 3:1 WCAG floor for graphical objects. Palette P2 (2026-10-11) fixed the
# failure, so the figure now shows the measurement instead — and the numbers in its title are
# computed here, off gen_logo.py's own constants, by contrast_report.py. They are not typed in:
# a caption that quotes a ratio nobody re-measured is the thing this folder keeps getting wrong.
# If a cell ever drops back under the floor the title says so and the build stops: a figure
# whose caption has gone stale is worse than no figure (gotcha 39, which was found IN this
# script's title, and gotcha 30: the thing that reports is the thing nobody checks).
DARK_MEASURE=$(python3 - "$L" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])          # logo/, where contrast_report.py lives
import contrast_report as C
g, b = C.palette_from_generator()
gd, bd = C.contrast(g, C.DARK), C.contrast(b, C.DARK)
gw, bw = C.contrast(g, C.WHITE), C.contrast(b, C.WHITE)
worst = min(gd, bd, gw, bw)
print(f"{gd:.2f} {bd:.2f} {gw:.2f} {bw:.2f} "
      + ("legal" if worst >= 3.0 else "ILLEGAL"))
PY
)
read -r G_DARK B_DARK G_WHITE B_WHITE DARK_VERDICT <<<"$DARK_MEASURE"
echo "on-dark: green $G_DARK / blue $B_DARK on #0d1117, $G_WHITE / $B_WHITE on white -> $DARK_VERDICT"
[ "$DARK_VERDICT" = legal ] || { echo "REFUSING to caption a dark figure as legal: the worst \
cell is under 3:1. Re-measure, then re-run."; exit 1; }

ink "$L/kwcapture.svg"    -o "$T/d1.png" -b '#0d1117' -w 400 -h 400
ink "$L/kwcapture-mark.svg" -o "$T/d2.png" -b '#0d1117' -w 400 -h 400
ink "$T/mono-orig.svg"    -o "$T/d3.png" -b '#0d1117' -w 400 -h 400
# body WITHOUT a title, then draw_title() (gotcha 39, above).
magick montage -label 'kwcapture\n(full)' "$T/d1.png" -label 'kwcapture\n-mark' "$T/d2.png" \
  -label 'the\nmonogram' "$T/d3.png" -tile 3x1 -geometry 260x260+14+14 \
  -background '#0d1117' -fill '#c9d1d9' -pointsize 22 -font "$FONT" "$T/dbody.png"
draw_title "$T/dbody.png" on-dark.png '#0d1117' '#c9d1d9' \
  'on GitHub dark #0d1117: both halves clear the 3:1 non-text floor' \
  "green ${G_DARK}:1   blue ${B_DARK}:1   (on white ${G_WHITE}:1 / ${B_WHITE}:1)"

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

# The anatomy figure is not just a picture: it re-derives the K and W boxes from gen_logo.py's
# vertex rings, cross-checks them against #kw-c's path data, against validate_logo.py's #kw ink
# box and against the RENDER (connected-component labelling of the ink mask), and asserts the
# figure's own ink is 8 px clear of every edge and every annotation colour clears 3:1 against
# both halves. So a wrong caption, a moved outline or a clipped row fails this build rather than
# shipping a confident lie. It reads the SVG and the render, and writes anatomy.png only.
python3 anatomy.py
for f in *.png; do magick "$f" -depth 8 -strip -define png:compression-level=9 "$f"; done
ls -la
