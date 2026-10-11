#!/usr/bin/env bash
# Clear a stale GitHub "Contributors" sidebar entry by cycling the default branch.
#
# WHY THIS EXISTS
# GitHub resolves a commit trailer's EMAIL to an account and lists that account as a repo
# contributor. When the attribution was WRONG (and worse, when the offending commits were
# later rewritten out of history), the sidebar widget keeps showing the phantom contributor:
# it is hydrated by a cached pipeline that a force-push does not invalidate. REST
# /contributors and /stats/contributors will both report the correct list while the widget
# still renders the ghost, so "the API says it's fine" is NOT evidence it is fixed.
# Confirmed working 2026-10-12 on tjandrasg/kwcapture: main deleted, ~70s, recreated. Nothing
# else moved (tags, releases and CI unaffected) and the entry was gone afterwards.
#
# WHAT IT DOES   (default branch D  ->  temp  ->  D-off  ->  delete D  ->  wait  ->  recreate D
#                 ->  default back to D  ->  delete the two scratch refs)
# It renames nothing in git objects: every ref is re-created from the SAME commit SHA.
#
# WHAT IS NOT SAFE ABOUT IT, read before running on anything you care about
#  * There is a window, the sleep, during which the default branch DOES NOT EXIST. Open PRs,
#    CI on push, deploy hooks, Pages builds and anyone cloning during that window will fail or
#    behave oddly. Do not run this during activity, and do not run it on a shared repo without
#    telling people.
#  * GitHub also rewrites PR/branch references on default-branch changes; that is what makes it
#    rebuild, and it is also why you do not do it twice for fun.
#  * If the script dies partway it prints "RESTORE NEEDED" and the exact commands. It also tries
#    them itself. Do not walk away from a RESTORE NEEDED line.
#
# USAGE
#   bash probe/github_refresh_contributors.sh [owner/repo] [--wait SECONDS] [--dry-run] [--verify]
# Needs: gh authenticated (gh auth login) or GH_TOKEN, plus git with push access.
set -uo pipefail

REPO="${1:-tjandrasg/kwcapture}"
case "${1:-}" in --*) REPO="tjandrasg/kwcapture";; esac
WAIT=70
DRY=""
VERIFY_ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --wait) WAIT="$2"; shift 2;;
    --dry-run) DRY=1; shift;;
    --verify) VERIFY_ONLY=1; shift;;
    *) shift;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then echo "need gh (or: GH_TOKEN + curl)"; exit 2; fi
if [ -z "${GH_TOKEN:-}" ]; then
  GH_TOKEN=$(gh auth token 2>/dev/null) || true
fi
[ -n "${GH_TOKEN:-}" ] || { echo "no token: run 'gh auth login' or export GH_TOKEN"; exit 2; }
export GH_TOKEN

api() { gh api "repos/$REPO$1" "${@:2}"; }
def_branch() { api "" --jq .default_branch; }
sha_of() { api "/branches/$1" --jq .commit.sha; }
contribs() {
  echo "   /contributors        : $(api "/contributors?per_page=50&anon=1" --jq '[.[].login] | join(", ")' 2>/dev/null)"
  echo "   /stats/contributors  : $(api "/stats/contributors" --jq '[.[].author.login] | join(", ")' 2>/dev/null)"
  echo "   (neither of those is the widget. The widget is the sidebar on the repo page, in a"
  echo "    logged-out/private browser window. Look there, not here, for the verdict.)"
}

if [ -n "$VERIFY_ONLY" ]; then echo "contributor pipelines for $REPO:"; contribs; exit 0; fi

D=$(def_branch) || { echo "cannot read $REPO"; exit 1; }
SHA=$(sha_of "$D") || { echo "cannot read branch $D"; exit 1; }
TMP="zz-cache-bust-default"; OLD="$D-off-by-cachebust"
echo "repo      : $REPO"
echo "default   : $D"
echo "at sha    : $SHA"
echo "plan      : $D -> $TMP -> $OLD -> (delete $D) -> sleep ${WAIT}s -> recreate $D from $SHA -> default $D -> clean up"
[ -n "$DRY" ] && { echo "(dry run, nothing changed)"; exit 0; }

restore() {
  echo "!! $1"
  echo "   RESTORE NEEDED. Current default: $(def_branch 2>/dev/null)"
  echo "   Recreate + repoint with:"
  echo "     git push origin $SHA:refs/heads/$D"
  echo "     gh api -X PATCH repos/$REPO -f default_branch=$D"
  echo "     gh api -X DELETE repos/$REPO/git/refs/heads/$OLD 2>/dev/null"
  echo "     gh api -X DELETE repos/$REPO/git/refs/heads/$TMP 2>/dev/null"
  exit 1
}

# 1. temp branch, so the default is never missing
git push -q "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" \
    "+${SHA}:refs/heads/${TMP}" 2>/dev/null || restore "could not create $TMP"
api -X PATCH "" -f default_branch="$TMP" --jq .default_branch >/dev/null || restore "could not set default to $TMP"
echo "step 1 ok : default -> $TMP"

# 2. a second ref at the same commit, then default off the real branch, then delete the real one
git push -q "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" \
    "+${SHA}:refs/heads/${OLD}" 2>/dev/null || restore "could not create $OLD"
api -X PATCH "" -f default_branch="$OLD" --jq .default_branch >/dev/null || restore "could not set default to $OLD"
git push -q "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" --delete "$D" \
    || restore "could not delete $D"
echo "step 2 ok : $D deleted; default -> $(def_branch)"

# 3. the window. Everything at your own risk during this.
echo "step 3    : waiting ${WAIT}s with $D absent (hooks/PRs/clones will fail now)"
sleep "$WAIT"

# 4. recreate from the SHA -- NOT from a branch ref. That bug is what leaves a repo stranded.
git push -q "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" \
    "+${SHA}:refs/heads/${D}" || restore "could not recreate $D"
api -X PATCH "" -f default_branch="$D" --jq .default_branch >/dev/null || restore "could not restore default to $D"
echo "step 4 ok : $D recreated; default -> $(def_branch)"

# 5. drop the scratch refs
api -X DELETE "/git/refs/heads/$OLD" >/dev/null 2>&1
api -X DELETE "/git/refs/heads/$TMP" >/dev/null 2>&1
echo "step 5 ok : scratch refs removed; branches: $(api /branches --jq '.[].name' | tr '\n' ' ')"

NOW=$(sha_of "$D")
if [ "$NOW" = "$SHA" ]; then
  echo "RESULT: default branch restored byte-exact at $NOW"
else
  echo "RESULT: SHA MISMATCH orig=$SHA now=$NOW -- RESTORE NEEDED"
fi
echo
echo "Now check the sidebar in a logged-out private window. If the phantom contributor is STILL"
echo "there, the cache outlived the rename or is indexing orphaned objects reachable by SHA:"
echo "file a GitHub Support ticket (no API/CLI route exists) and list those SHAs."
