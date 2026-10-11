# Licence — the `kwcapture` mark, and the code that generates it

This file governs **`logo/` only**. The `kwcapture` package itself is MIT-licensed under
[`../LICENSE`](../LICENSE), and nothing here changes that.

The reason this directory needs its own licence file is that it holds two different kinds
of thing, and one licence does not fit both:

* **artwork** — the hand-drawn sketches and the SVGs generated from them;
* **code** — `gen_logo.py`, `validate_logo.py`, `render_agreement.py`.

Shipping the artwork under MIT alone invites the question *"does the MIT notice cover the
pictures?"*; shipping the code under a Creative Commons licence would make the tooling
incompatible with the MIT package it belongs to. So the split below is not bureaucracy —
it is the smallest set of terms that lets the software stay MIT **and** lets the picture
be used, attributed and defended.

## TL;DR

| what | files | licence | SPDX |
|---|---|---|---|
| the mark / artwork | `kwcapture.svg`, `kwcapture-mark.svg`, `kwcapture-mono.svg`, `kwcapture-sketch.svg`, `kwcapture-mark-sketch.svg`, `preview/*.png`, and the shipped set `icon/*.svg`, `icon/*.png`, `icon/*.ico` | **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** | `CC-BY-4.0` |
| the tooling | `gen_logo.py`, `validate_logo.py`, `render_agreement.py`, `preview/build.sh`, `preview/anatomy.py`, `icon/build.sh`, `icon/tiles.py`, `icon/card.py`, `icon/contact.py` | **[MIT](../LICENSE)** (same terms as the package) | `MIT` |
| the typeface used to draw them | *(not included — no font file ships here)* | SIL Open Font License 1.1, © Rasmus Andersson | `OFL-1.1`, reference only |
| session transcripts | `*.jsonl` (present on this machine, **gitignored**) | **not licensed — do not copy, commit or distribute** | none |

Copyright (c) 2026 **Tjandra Satria Gunawan**, <https://github.com/tjandrasg/kwcapture>.

---

## 1. The artwork — CC BY 4.0

> **This licence allows you to:** copy and redistribute the mark, and adapt it (recolour,
> crop, extend, embed in a UI, print a sticker, draw fan art of it), **including
> commercially** — on one condition: **attribution**.

You may do all of that **provided you**:

1. **give appropriate credit** (the form in §3),
2. **link to the licence**, and
3. **indicate if you changed anything** — and you may do so in any reasonable manner,
   *but not in a way that suggests the licensor endorses you or your use*.

Full legal code: <https://creativecommons.org/licenses/by/4.0/legalcode>.
Human-readable summary: <https://creativecommons.org/licenses/by/4.0/>.

**Every file in `icon/` is this same artwork**, not a new work: the PNGs, the `.ico`, the tiles
and the renders are mechanical outputs of `icon/build.sh` from `kwcapture-mark.svg` (§2 covers
the builders, not what they emit). Since 2026-10-11 the owner's rule is that the mark is the only
artwork that may represent the project, so nothing else is generated into `icon/` at all —
resizing and re-rendering are the permitted transformations, and a second drawing is not.
Cropping, recolouring or tiling the mark is an **adaptation** under CC BY 4.0, so the attribution
of §3 travels with an avatar, a favicon or a social card just as it does with the SVG.

**Why CC BY 4.0 and not something else** — the alternatives, and what each would have cost:

* **CC0 / public domain** — zero friction for downstream, and tempting for a project this
  small. Rejected: this file is the *identity* of the project, not a chunk of content. A
  CC0 mark can be forked into a competing product with no trace back, and the author gives
  up the cleanest thing he has in a dispute — an unbroken, attributed chain of authorship.
* **CC BY-SA 4.0** (share-alike) — the usual "open but reciprocal" answer for artwork.
  Rejected for a *brand* asset: share-alike is designed for content you want to keep open,
  and on a logo it reaches into things nobody wants to litigate — a screenshot in a blog
  post, a wallpaper, a distro's icon theme, a slide deck. What a logo actually needs to
  survive is attribution and a trademark policy, not a viral clause.
* **All rights reserved** — the strongest control and the worst fit. The logo has to be
  copyable: it belongs in the README, in PyPI's long description, in distribution packages
  and in other people's documentation. ARR would make every one of those an infringement
  request, in a project whose own licence is MIT.
* **MIT, matching the package** — the code's licence is not the artwork's licence, and the
  mismatch is exactly what this file exists to remove.

## 2. The tooling — MIT

The Python and shell in this directory are under the same MIT terms as the rest of the
project, so the licence of the tooling never disagrees with the licence of the software it
builds, and `logo/` can be vendored, patched or copied into a fork without a licence
conflict. The text is [`../LICENSE`](../LICENSE); reproduced here so this directory is
self-describing:

```
MIT License

Copyright (c) 2026 Tjandra Satria Gunawan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**The licence on the code does not license the picture it emits.** `gen_logo.py` is MIT;
`kwcapture.svg` it writes is artwork under §1. That distinction is deliberate — MIT covers
the program, not the pixels a program produces.

## 3. Attribution, in the form to use

> **"kwcapture" logo** © 2026 Tjandra Satria Gunawan,
> from [kwcapture](https://github.com/tjandrasg/kwcapture) · licensed
> [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
> *(modified: recoloured for the dark theme)* ← replace with what you actually did

For an icon in a UI, a credit in the About box or a footer link satisfies this. For a
README header image, a link on the image to the logo's source is enough. Attribution is
not a popularity contest: what the clause protects is the ability to tell an official mark
from a stranger's variant.

## 4. What no licence here grants

* **Trademarks.** CC BY 4.0 conveys **copyright** permissions only. The name `kwcapture`,
  the mark itself, and anything that looks like it are not licensed as a brand: you may not
  release software under this mark, or use it in a way that implies this project ships,
  endorses or approved your product. (Creative Commons says the same about trademarks in
  its own [FAQ](https://creativecommons.org/faq/#does-my-use-of-licensed-material-infringe-a-trademark).)
* **KDE, KWin, Plasma.** Neither this mark nor this project is affiliated with or endorsed
  by KDE. The `kw` in the name is a reference to the compositor the tool talks to
  (`org.kde.KWin.ScreenShot2`), nothing more, and the mark deliberately contains no KDE
  branding. Do not add any.
* **Patents.** Nothing here grants a patent licence.

## 5. Third-party material

* **Inter ExtraBold** (SIL OFL 1.1, © Rasmus Andersson) was used to draw the letters
  `PTURE`. The SVGs carry **glyph outlines**, not a font file, and **no font is included
  in this directory**. The OFL governs the *font software*; it does not claim the artwork
  produced with it — but if you redistribute Inter itself (e.g. bundling the `.otf` so the
  generator runs elsewhere), the OFL travels with it and requires its licence text to
  travel too. `gen_logo.py` reads the font from your system
  (`/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf` by default, `--font` to override).
* **The two sketches are original** hand drawings made for this project in Inkscape, and
  are part of the artwork in §1.
* Everything else in this directory was generated from those inputs by the MIT tooling
  above.

## 6. Explicitly *not* licensed, and not to be distributed

`logo/*.jsonl` (on this machine: `prev_logo.jsonl`, ~2 MB) are **exports of the design
sessions**, and most of their bytes are base64 screenshots of the author's desktop. They
are **not** part of the work, are not offered under any licence, and must never be
committed or packaged: `.gitignore` has `logo/*.jsonl` for exactly that reason, and the
rule is name-agnostic because the export lands under a new name every session. Older
exports live in [`../private/`](../private), which self-ignores.

If you are reading a clone of this repository, the transcripts are not in it. If you are
reading a working copy and you find one, treat it as somebody's personal data.

## 7. Contributing

Contributing artwork or code to `logo/` means you offer it under the matching licence above
(inbound = outbound), and you confirm you have the right to do so. For an obviously
derivative mark — a recolour of someone else's logo, a traced icon — say so in the pull
request; this project's own inputs are original for a reason (§5).

## 8. Machine-readable summary

For a tool that wants one expression per file:

```
kwcapture*.svg, kwcapture-*-sketch.svg                  CC-BY-4.0
preview/*.png, icon/*.svg, icon/*.png, icon/*.ico       CC-BY-4.0   (derived artwork)
*.py, preview/build.sh, icon/build.sh                   MIT
*.jsonl                                                 NO-EVIL / not licensed (see §6)
```

The repository as a whole stays `MIT` (see [`../LICENSE`](../LICENSE) and the
`license = "MIT"` field in `../pyproject.toml`); this file refines that for `logo/` only.
If you package `logo/` alongside the software (a tarball, a distro icon package), ship
**both** this file and `../LICENSE`, and keep the attribution of §3 visible.
