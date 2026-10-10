#!/usr/bin/env bash
# Build the shipped icon set from the two source SVGs in this directory and ../.
#
#   cd logo && bash icon/build.sh        # needs inkscape, ImageMagick, Pillow (for card.py)
#
# WHAT IS GENERATED, and why these sizes:
#
#   logo  (kwcapture-mark, transparent)  1024 512 256 128
#       README headers, docs, og images. The word `APTURE` is legible down to ~64 px and
#       mush below it (see the ladder in ../README.md) — so below 64 px nothing ships the
#       word.
#   glyph (kwcapture-mark-mono, transparent) 1024 512 400 192 180 128 64 48 32 24 16
#       The SAME drawing without the word: the monogram of the mark sketch, produced by
#       `gen_logo.py --monogram --sketch kwcapture-mark-sketch.svg`. Favicons, tab icons,
#       list icons, and anything GitHub crops to a circle (avatars) — the wide lockup loses
#       the end of its word under a circular crop, the monogram does not.
#   tile  (glyph on a white square; 180 is rounded) apple-touch-icon, pwa-192, pwa-512,
#         maskable-512, github-avatar-400
#       Apple touch icon, PWA icons, the GitHub avatar. The type is #0000ff, which is
#       2.20:1 against GitHub's #0d1117: a transparent icon in a dark browser tab or a dark
#       home screen loses the blue entirely. A light tile is the one-line fix that does not
#       require deciding the open dark-mode recolour question.
#   favicon.ico  16 24 32 48 64          browsers that still ask for .ico
#   github-social-preview.png 1280x640   Settings -> Social preview (card.py)
set -euo pipefail
cd "$(dirname "$0")"
L=".."
# NOTE: do NOT pass `-b none` for transparency. Inkscape 1.x accepts it, exits 0 and writes
# an OPAQUE WHITE background (verified: corner pixel alpha 255). Omitting -b entirely is what
# gives real alpha (corner alpha 0). A flag that silently produces the wrong artefact is the
# same family as a check that silently does not run.
# inkx = inkscape, with no -b: real transparency.
inkx() { inkscape "$@" >/dev/null 2>&1; }
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

# ---------------------------------------------------------------- source artefacts exist
for f in "$L/kwcapture-mark.svg" kwcapture-mark-mono.svg; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done

# -------------------------------------------------------------------------------- logo
for n in 1024 512 256 128; do
  inkx "$L/kwcapture-mark.svg" -o "kwcapture-mark-$n.png" -w "$n" -h "$n"
done

# ------------------------------------------------------------------------------- glyph
for n in 1024 512 400 192 180 128 64 48 32 24 16; do
  inkx "kwcapture-mark-mono.svg" -o "glyph-$n.png" -w "$n" -h "$n"
done

# --------------------------------------------------------------- tiles (dark-safe)
# white square + centred glyph, in Pillow, which verifies its own output and exits 1 if a
# tile comes out blank or grey. (ImageMagick was tried first: `magick a.png b.png -gravity
# center -composite` returned a blank grey canvas here in every variation — white base,
# xc:none base, `magick composite`, `-layers flatten`, `-type TrueColor` — while reporting
# success. See icon/tiles.py.)
python3 tiles.py

# --------------------------------------------------------------------------- favicon.ico
magick glyph-16.png glyph-24.png glyph-32.png glyph-48.png glyph-64.png \
  -define icon:auto-resize=16,24,32,48,64 favicon.ico

# ----------------------------------------------------------------------- social preview
python3 card.py

# ------------------------------------------------ the sheet every icon is reviewed on
python3 contact.py

# ------------------------------------------------------------------ housekeeping + report
for f in *.png; do magick "$f" -depth 8 -strip -define png:compression-level=9 "$f"; done
echo
echo "icon/ contents:"
ls -la | awk 'NR>1 {printf "  %-34s %8s\n", $NF, $5}'
echo
# Two measured things about this report line, both found by it being wrong here first:
#   * `-format` takes ONE dash. `identify --format FMT files…` treats FMT as a *filename*, dies
#     with "no decode delegate for this image format", and — because this block used to pipe
#     through 2>/dev/null — the report simply printed NOTHING while the build stayed green.
#     Gotcha 30, in a build script: a report that silently does not report. stderr is therefore
#     no longer suppressed here.
#   * width specifiers like `%-28f` are not supported by this ImageMagick (it prints `28f` and
#     warns `unknown image property "%-"`). Align with awk above, not with the format string.
magick identify -format '  %f  %wx%h  %[type]  %b\n' \
  favicon.ico github-social-preview.png github-avatar-400.png apple-touch-icon.png glyph-16.png
