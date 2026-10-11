#!/usr/bin/env bash
# Is tests/test_icons.py actually capable of failing?
#
#   bash probe/sabotage_icons.sh
#
# CONTRIBUTING.md's rule is "a fix without a test is a guess"; the logo/ docs add the corollary
# that cost a whole round there (gotcha 24, met twice in one day): **a check that has never been
# seen to fail is not evidence.** So each rule the icon code enforces is broken on purpose, the
# suite is run, the file restored, and the outcome compared with what we expected.
#
# Every line below wants `fail`: the suite must notice. Measured 2026-10-11: **10/10 detected**,
# clean tree green. The `gap` want still exists in `check_sabotage` — a rule the suite genuinely
# cannot cover belongs in the list as a KNOWN GAP rather than being deleted, because a probe that
# quietly reports "all covered" is how you end up trusting a decorative check.
#
# The trap matters more here than in most scripts: this one edits **tracked source files**, so a
# Ctrl-C or a session that dies mid-run must not leave `kwcapture/_icons.py` sabotaged.
set -u
cd "$(dirname "$0")/.."
BK=$(mktemp -d)
cp kwcapture/_icons.py kwcapture/_desktop.py logo/sync_package_icons.py "$BK"/
undetected=0

cleanup() { restore; rm -rf "$BK"; }
trap cleanup EXIT INT TERM

run() {   # prints the verdict: the RESULT line, or that the suite died
  out=$(python3 tests/test_icons.py 2>&1); rc=$?
  line=$(printf '%s' "$out" | grep -E "^RESULT" | head -1)
  if [ -n "$line" ]; then printf '%s' "$line"; else printf 'suite died (exit %s)' "$rc"; fi
}

sabotage() {                          # $1 file, $2 old, $3 new (called with 3 args)
  python3 - "$1" "$2" "$3" <<'PY'
import sys, pathlib
f, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(f); t = p.read_text()
if old not in t:
    print("PATTERN-NOT-FOUND"); sys.exit(0)
p.write_text(t.replace(old, new, 1))
PY
}
restore() {
  cp "$BK/_icons.py" kwcapture/_icons.py
  cp "$BK/_desktop.py" kwcapture/_desktop.py
  cp "$BK/sync_package_icons.py" logo/sync_package_icons.py
}

check_sabotage() {                    # $1 label, $2 file, $3 old, $4 new, $5 want(fail|gap)
  printf '  %-46s ' "$1"
  r=$(sabotage "$2" "$3" "$4")
  if [ "$r" = "PATTERN-NOT-FOUND" ]; then
    printf 'SABOTAGE PATTERN NOT FOUND -- the code moved, update this probe\n'; undetected=$((undetected+1))
    restore; return
  fi
  verdict=$(run); restore
  case "$verdict" in
    *"all icon tests passed"*)
      if [ "$5" = "gap" ]; then printf 'KNOWN GAP  (%s)\n' "$verdict"
      else printf 'NOT DETECTED (%s)\n' "$verdict"; undetected=$((undetected+1)); fi ;;
    *)  if [ "$5" = "gap" ]; then printf 'detected (expected a gap; even better)\n'
      else printf 'detected: %s\n' "$verdict"; fi ;;
  esac
}

echo "== sabotage matrix -- every 'fail'-want line must be detected"
check_sabotage "uninstall: drop the sha256 guard" kwcapture/_icons.py \
'        if ours_only:
            try:
                if _sha256(dst) != _sha256(src):' \
'        if False:
            try:
                if _sha256(dst) != _sha256(src):' fail

check_sabotage "install: skip source size validation" kwcapture/_icons.py \
'        if (w, h) != (exp, exp):
            raise IOError("shipped icon %s is %dx%d but %s requires %dx%d"' \
'        if False:
            raise IOError("shipped icon %s is %dx%d but %s requires %dx%d"' fail

check_sabotage "install: skip source alpha validation" kwcapture/_icons.py \
'        if not png_has_alpha(src):
            raise IOError("shipped icon %s has no alpha channel' \
'        if False:
            raise IOError("shipped icon %s has no alpha channel' fail

check_sabotage "install: stop comparing what was written" kwcapture/_icons.py \
'        if dst.read_bytes() != want:
            raise IOError("icon copy does not match the source: %s" % dst)' \
'        if False:
            raise IOError("icon copy does not match the source: %s" % dst)' fail

check_sabotage "paths: lose the hicolor/ theme component" kwcapture/_icons.py \
'    want = ["%s/%s/kwcapture.png" % (THEME, _theme_rel(s, "png")) for s in PNG_SIZES]' \
'    want = ["%s/kwcapture.png" % _theme_rel(s, "png") for s in PNG_SIZES]' fail

check_sabotage "entry: hard-code the old dangling Icon=" kwcapture/_desktop.py \
'icon=_icons.pick_icon_name())' \
'icon="accessories-screenshot")' fail

check_sabotage "resolution: assume the hicolor layout only" kwcapture/_icons.py \
'    _DIR_CACHE[key] = out' \
'    out = ["*/apps"]   # sabotage: the layout Breeze does not use
    _DIR_CACHE[key] = out' fail

check_sabotage "refresh: rewrite every .desktop, ours or not" kwcapture/_desktop.py \
'    for path in sorted(applications_dir().glob(f"{PREFIX}*.desktop")):' \
'    for path in sorted(applications_dir().glob("*.desktop")):' fail

check_sabotage "generator: neuter its alpha guard" logo/sync_package_icons.py \
'        elif not png_has_alpha(src):' \
'        elif False:' fail

check_sabotage "generator: write before validating" logo/sync_package_icons.py \
'    if problems:
        print("FAIL (bad artwork — nothing written)")' \
'    if False:
        print("FAIL (bad artwork — nothing written)")' fail

echo "== restored"
printf '  %-46s ' "clean tree"; run
echo
if [ "$undetected" -gt 0 ]; then
  echo "VERDICT: $undetected sabotage(s) that should have been detected were NOT."
  exit 1
fi
echo "VERDICT: every check the icon code enforces is covered by a failing test."
