#!/usr/bin/env python3
"""Copy the official mark into the Python package, and prove it did not drift.

    python3 logo/sync_package_icons.py            # write kwcapture/icons/ from logo/icon/
    python3 logo/sync_package_icons.py --check    # verify only; exit 1 on any drift

This is the only sanctioned path from the artwork (`logo/`) to the shipped package
(`kwcapture/icons/`). It exists because a copied icon is a *second* artefact of the same
drawing, and second artefacts rot: hand-copy a PNG once, re-render the mark next month, and
the desktop entry is quietly showing last month's logo. So the rule is that nothing in
`kwcapture/icons/` is written by hand, and `--check` (which `tests/test_icons.py` runs) fails
the moment the two trees disagree.

What it copies, and from where:

    logo/icon/kwcapture-mark-<N>.png   ->  kwcapture/icons/hicolor/NxN/apps/kwcapture.png
    logo/kwcapture-mark.svg            ->  kwcapture/icons/hicolor/scalable/apps/kwcapture.svg
    (generated)                        kwcapture/icons/COPYING.md   provenance + licence
    (the `hicolor/` component is what makes them findable; it is read from `_icons.THEME`)

The artwork is **`kwcapture-mark.svg` and only that** — the owner's decision of 2026-10-11, and
the permitted transforms are resize and re-render. An earlier revision of this file copied the
monogram (`glyph-*.png`) because the word is mush below ~64 px; that measurement is now a
*documented consequence* (README.md §8), not a licence to substitute a different drawing. If you
find yourself pointing `plan()` at a monogram again: the owner chose the mark, and `--check`
inside `tests/test_icons.py` is what makes such a change loud instead of silent.

It writes inside `kwcapture/icons/` and nowhere else, and every file it writes is re-read and
checked (sha256 against the source, and a PNG's own IHDR against the size in its directory
name). It also reads the size list from `kwcapture/_icons.py` itself rather than repeating it
here: one definition, so the package and the generator cannot disagree about which sizes exist.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # <repo>/logo
REPO = HERE.parent
PKG = REPO / "kwcapture"


def _load_pkg_icons():
    """Load `kwcapture/_icons.py` WITHOUT importing the package.

    `import kwcapture` pulls in numpy (house rule: keep that cheap) and needs the package to
    be importable at all. _icons.py is stdlib-only, so loading it by path gives us its
    `PNG_SIZES` and `png_size` — the same definitions the installer uses at runtime — with no
    dependency on the rest of the package.
    """
    spec = importlib.util.spec_from_file_location("_kwcapture_icons", PKG / "_icons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ICONS = _load_pkg_icons()
SIZES = ICONS.PNG_SIZES
SRC = HERE / "icon"          # the reviewed artwork
DEST = PKG / "icons"         # what ships

ATTRIBUTION = ('"kwcapture" logo \u00a9 2026 Tjandra Satria Gunawan, from '
               '[kwcapture](https://github.com/tjandrasg/kwcapture) \u00b7 licensed '
               '[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_has_alpha(path: Path) -> bool:
    """The package's own predicate — one implementation, so the generator cannot be more
    lenient than the installer that has to accept what it produces."""
    return ICONS.png_has_alpha(path)


def plan(src=SRC, dest=DEST):
    """[(source, destination, size_dir)] — the whole job, computed in one place.

    The theme name and the size list come from `kwcapture/_icons.py`, not from a copy here:
    the file that installs at runtime and the file that builds the package must not be able to
    disagree about where an icon goes. (They did once: the theme component `hicolor/` was
    missing, which put the files in a directory no icon lookup reads.)
    """
    # ONE artwork: `logo/kwcapture-mark.svg`, resized. The PNGs are its renders in icon/ and
    # the scalable entry is the SVG itself. Deliberately no monogram source: the owner's rule
    # (2026-10-11) is that the mark IS the icon and the only permitted transforms are resize
    # and re-render, so a second drawing cannot enter the package through this file.
    jobs = [(src / ("kwcapture-mark-%d.png" % n), dest / ICONS.THEME / ("%dx%d" % (n, n))
             / "apps" / "kwcapture.png", "%dx%d" % (n, n)) for n in SIZES]
    jobs.append((HERE / "kwcapture-mark.svg",
                 dest / ICONS.THEME / "scalable" / "apps" / "kwcapture.svg", "scalable"))
    return jobs


def provenance(jobs, dest=DEST) -> str:
    rows = "\n".join(
        "| `%s` | %d B | `%s` |" % (dst.relative_to(dest), src.stat().st_size, sha(src)[:16])
        for src, dst, _ in jobs)
    return """# The icon set inside this package

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

  > %s

* CC BY grants copyright, **not** trademarks: you may not ship software under this mark or
  imply this project endorsed yours.

## Provenance

`python3 logo/sync_package_icons.py` wrote these bytes from these sources (sha256, first 16):

| file | size | source sha256 |
|---|---|---|
%s

`python3 logo/sync_package_icons.py --check` re-verifies all of it, and
`tests/test_icons.py` runs that check as part of the test suite.
""" % (ATTRIBUTION, rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="verify kwcapture/icons/ against logo/icon/ and write nothing")
    # The two overrides exist for tests/test_icons.py: pointing --src at a scratch tree with
    # one doctored PNG is the only way to prove the *generator's* validation is wired up, as
    # opposed to the predicate existing. Defaults are the real trees, so normal use is one
    # command with no arguments.
    ap.add_argument("--src", default=str(SRC), help="artwork directory (default logo/icon)")
    ap.add_argument("--dest", default=str(DEST), help="package icons dir (default "
                                                      "kwcapture/icons)")
    args = ap.parse_args()
    src, dest = Path(args.src), Path(args.dest)

    jobs = plan(src, dest)
    missing = [str(s) for s, _, _ in jobs if not s.is_file()]
    if missing:
        print("missing source artwork (run `cd logo && bash icon/build.sh` first):\n  "
              + "\n  ".join(missing))
        return 1

    problems, wrote = [], []

    # ---- PASS 1: validate every source. Nothing is written until the whole set is good, so
    # a bad render cannot leave a half-synced kwcapture/icons/ behind.
    for src, dst, declared in jobs:
        if not dst.name.endswith(".png"):
            continue
        w, h = ICONS.png_size(src)
        want = int(declared.split("x")[0])
        if (w, h) != (want, want):
            problems.append("%s is %dx%d, expected %dx%d" % (src, w, h, want, want))
        elif not png_has_alpha(src):
            problems.append("%s has no alpha channel (a white square, not an icon)" % src)
    if problems:
        print("FAIL (bad artwork — nothing written)")
        for p in problems:
            print("  " + p)
        return 1

    # ---- PASS 2: check (or write) and verify what landed
    for src, dst, declared in jobs:
        if args.check:
            if not dst.is_file() or sha(dst) != sha(src):
                problems.append("%s is %s" % (
                    dst.relative_to(dest) if dest in dst.parents else dst,
                    "absent" if not dst.is_file() else "not the current artwork (drifted)"))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_file() and sha(dst) == sha(src):
            continue                                   # already byte-identical
        dst.write_bytes(src.read_bytes())
        if sha(dst) != sha(src):                       # never trust the write you just did
            problems.append("wrote %s but the bytes do not match" % dst)
            continue
        wrote.append(dst)

    if not args.check and not problems:
        cop = dest / "COPYING.md"
        body = provenance(jobs, dest)
        if not cop.is_file() or cop.read_text() != body:
            cop.parent.mkdir(parents=True, exist_ok=True)
            cop.write_text(body)
            wrote.append(cop)

    if problems:
        print("FAIL (drift or bad artwork)")
        for p in problems:
            print("  " + p)
        return 1

    print("%s %d icon files (%d written now)" % (
        "checked" if args.check else "synced", len(jobs), len(wrote)))
    for src, dst, declared in jobs:
        print("  %-44s %-9s %6d B  %s" % (
            dst.relative_to(dest) if dest in dst.parents else dst, declared,
            dst.stat().st_size, sha(src)[:12]))
    # the guard against a stray path: everything we touched must be under the icons dir
    for _, dst, _ in jobs:
        assert dest in dst.parents, "refusing to have written outside %s" % dest
    return 0


if __name__ == "__main__":
    sys.exit(main())
