# The icon set inside this package

**Generated — do not edit any file in this directory.** Regenerate with

```bash
python3 logo/sync_package_icons.py
```

Source of truth: `logo/kwcapture-mark.svg` in the git repository (sketches →
`gen_logo.py` → the mark → `logo/icon/kwcapture-mark-*.png`, reviewed on
`logo/icon/contact.png`) — the sdist and the wheel ship what it produced, not the generators.

**One artwork.** Every file here is that mark resized or re-rendered: eight PNG sizes plus one
scalable SVG. The owner's rule (2026-10-11) allows no other variant — no monogram, no invented
crop. It is known and accepted that `APTURE` is mush below about 64 px (`logo/README.md` §8 has
the ladder): the mark is still the mark at 16 px, and shipping a different drawing at small
sizes is not this package's decision to make.

The directory layout is the freedesktop **hicolor** theme layout, and `kwcapture/_icons.py`
installs it into `$XDG_DATA_HOME/icons/hicolor/...` when you run `kwcapture install-desktop`
or `kwcapture setup`. Every size here is a directory the system
`/usr/share/icons/hicolor/index.theme` declares; nothing invented.

## Licence

* These images are **artwork**, licensed **CC BY 4.0** — the full terms are in
  `logo/LICENSE.md` in the repository (root [`LICENSE`](../LICENSE) is MIT and covers the
  **code**, not the pictures). That distinction is the reason this file sits next to them:
  a reader of an installed tree sees which licence applies to which file.
* Attribution, in the form the licence asks for:

  > "kwcapture" logo © 2026 Tjandra Satria Gunawan, from [kwcapture](https://github.com/tjandrasg/kwcapture) · licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

* CC BY grants copyright, **not** trademarks: you may not ship software under this mark or
  imply this project endorsed yours.

## Provenance

`python3 logo/sync_package_icons.py` wrote these bytes from these sources (sha256, first 16):

| file | size | source sha256 |
|---|---|---|
| `hicolor/16x16/apps/kwcapture.png` | 719 B | `b65e21b3654a0e51` |
| `hicolor/24x24/apps/kwcapture.png` | 1133 B | `6f8a0f32cad06495` |
| `hicolor/32x32/apps/kwcapture.png` | 1549 B | `b77329e6690708e7` |
| `hicolor/48x48/apps/kwcapture.png` | 1943 B | `3c3401d501667c2b` |
| `hicolor/64x64/apps/kwcapture.png` | 2658 B | `341145818e9d89da` |
| `hicolor/128x128/apps/kwcapture.png` | 5836 B | `ac05cb4d09e1e447` |
| `hicolor/256x256/apps/kwcapture.png` | 12342 B | `553d545c4ad7dd05` |
| `hicolor/512x512/apps/kwcapture.png` | 27201 B | `afe3da1c7e2dbb01` |
| `hicolor/scalable/apps/kwcapture.svg` | 3797 B | `9663cec799efbbe7` |

`python3 logo/sync_package_icons.py --check` re-verifies all of it, and
`tests/test_icons.py` runs that check as part of the test suite.
