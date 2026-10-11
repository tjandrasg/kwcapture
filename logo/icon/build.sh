#!/usr/bin/env bash
# Build the shipped icon set from the two source SVGs in this directory and ../.
#
#   cd logo && bash icon/build.sh        # needs inkscape, ImageMagick, Pillow (for card.py)
#
# THE RULE (owner's decision, 2026-10-11): the icon of kwcapture is `../kwcapture-mark.svg`.
# Nothing else. No monogram, no "glyph form", no crop invented here, no second drawing — the
# only permitted transformations are RESIZE and RE-RENDER. An earlier revision of this script
# shipped the monogram (`glyph-*.png`, `kwcapture-mark-mono.svg`) as the icon set because the
# word is mush below ~64 px; that was a design decision made by the build script instead of by
# the owner, and it is reverted here. `icon/` now contains ONE artwork at many sizes.
#
# WHAT IS GENERATED, and why these sizes:
#
#   mark (kwcapture-mark, transparent)  1024 512 256 128 64 48 32 24 16
#       README headers, docs, og images — AND the icons: 16/24/32/48/64/128/256/512 are the
#       directories the system /usr/share/icons/hicolor/index.theme declares, and
#       logo/sync_package_icons.py copies these exact files into the Python package from here.
#       Measured, and accepted by the owner rather than worked around: `APTURE` is legible at
#       128 px, marginal at 64 and mush at 48 and below (../preview/ladder-icon.png). The mark
#       is still the mark at 16 px.
#   tile  (the mark on a white square; 180 is rounded) apple-touch-icon, pwa-192, pwa-512,
#         maskable-512, github-avatar-400
#       The tile is a GROUND, not a different drawing: the type is #0000ff, which is 2.20:1
#       against GitHub's #0d1117 and 8.59:1 on white, while the green is 6.32:1 / 3.00:1 — a
#       light ground is the only one where both halves clear 3:1. maskable keeps the 80% safe
#       zone; the avatar is the mark resized into 400x400 with no crop: GitHub's circular mask
#       clips 9.1% of its ink (measured, worst 45.6 px beyond the inscribed circle of 200) and
#       that is the host's masking, not a licence to ship another artwork.
#   favicon.ico  16 24 32 48 64          browsers that still ask for .ico, built from the mark
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
for f in "$L/kwcapture-mark.svg"; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done

# ---------------------------------------------------------------------------------- mark
# ONE artwork, many sizes. 16/24/32/48/64/128/256/512 == the hicolor directories declared by
# /usr/share/icons/hicolor/index.theme; 1024 is the docs/header master the tiles downscale from.
for n in 1024 512 256 128 64 48 32 24 16; do
  inkx "$L/kwcapture-mark.svg" -o "kwcapture-mark-$n.png" -w "$n" -h "$n"
done

# Nothing here renders a monogram. If a future round wants one, it is a conversation with the
# owner first (THE RULE in ../AGENTS.md), not a line in this script.

# --------------------------------------------------------------- tiles (dark-safe)
# white square + centred mark, in Pillow, which verifies its own output and exits 1 if a
# tile comes out blank or grey. (ImageMagick was tried first: `magick a.png b.png -gravity
# center -composite` returned a blank grey canvas here in every variation — white base,
# xc:none base, `magick composite`, `-layers flatten`, `-type TrueColor` — while reporting
# success. See icon/tiles.py.)
python3 tiles.py

# --------------------------------------------------------------------------- favicon.ico
magick kwcapture-mark-16.png kwcapture-mark-24.png kwcapture-mark-32.png \
  kwcapture-mark-48.png kwcapture-mark-64.png \
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
  favicon.ico github-social-preview.png github-avatar-400.png apple-touch-icon.png \
  kwcapture-mark-16.png kwcapture-mark-512.png
# …and the guard that the set is ONE artwork: every mark PNG must be a render of the same SVG,
# checked PIXEL-wise against a fresh render (not byte-wise: the `-strip` re-encode above changes
# the bytes while keeping the pixels). A hand-swapped or monogram file fails the build here.
python3 - <<'PY'
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
here = Path(".").resolve()
src = here.parent / "kwcapture-mark.svg"
bad = []
for n in (1024, 512, 256, 128, 64, 48, 32, 24, 16):
    f = here / ("kwcapture-mark-%d.png" % n)
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.png"
        subprocess.run(["inkscape", str(src), "-o", str(ref), "-w", str(n), "-h", str(n)],
                       check=True, capture_output=True)
        a, b = Image.open(f).convert("RGBA"), Image.open(ref).convert("RGBA")
        if a.size != b.size or a.tobytes() != b.tobytes():
            bad.append(f.name)
print("  %s" % ("all nine mark PNGs are pixel-identical to a fresh render of kwcapture-mark.svg"
                if not bad else "NOT renders of kwcapture-mark.svg: %s" % ", ".join(bad)))
sys.exit(1 if bad else 0)
PY
