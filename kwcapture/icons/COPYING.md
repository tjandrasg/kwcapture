# The icon set inside this package

**Generated — do not edit any file in this directory.** Regenerate with

```bash
python3 logo/sync_package_icons.py
```

Source of truth: `logo/` in the git repository (sketches → `gen_logo.py` →
`logo/icon/glyph-*.png`, reviewed on `logo/icon/contact.png`) — the sdist and the wheel ship
what it produced, not the generators. What is copied here is the **glyph** form of the
official mark: the same drawing with the word `APTURE` dropped, because a desktop icon is seen
at 16-48 px and that word is mush below ~64 px. The measurements are in `logo/README.md` §8.

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
| `hicolor/16x16/apps/kwcapture.png` | 504 B | `c9af45fa75eaef0a` |
| `hicolor/24x24/apps/kwcapture.png` | 741 B | `c6e52328aa97027b` |
| `hicolor/32x32/apps/kwcapture.png` | 936 B | `2ed510f6f534d705` |
| `hicolor/48x48/apps/kwcapture.png` | 1384 B | `55e3038dab3f1d62` |
| `hicolor/64x64/apps/kwcapture.png` | 1746 B | `edfc8aae88c0d784` |
| `hicolor/128x128/apps/kwcapture.png` | 3458 B | `7980a68dc1ff39ff` |
| `hicolor/256x256/apps/kwcapture.png` | 7343 B | `74f29cc277d995ea` |
| `hicolor/512x512/apps/kwcapture.png` | 16111 B | `46a9cddf7d54f458` |
| `hicolor/scalable/apps/kwcapture.svg` | 1432 B | `4eb2926d077078d9` |

`python3 logo/sync_package_icons.py --check` re-verifies all of it, and
`tests/test_icons.py` runs that check as part of the test suite.
