# AGENTS.md — fast screen capture on Wayland (KDE Plasma 6 / KWin)

> **Archive:** `AGENTS.old.md` holds the superseded detail — the original three-key-findings
> investigation log, the v0.1/v0.2 file map and benchmark tables, old packaging/CI notes, the
> forensics write-up, the 2026-10-07 session logs of the v0.4.0/v0.5.0 work, the original
> nested-`--virtual` discovery, and (moved 2026-10-09) the 2026-10-08 headless-CI and
> non-normal-window day-logs plus the long BUG-1 / BUG-2 / BUG-4 forensics. See *ARCHIVED* below for
> the map. Consult it when something here is too terse or you want the reasoning behind a rule; it is
> history, **not to-do**.
>
> ## EVERY CLAIM MUST BE TRUE, INCLUDING WHO WROTE THE CODE (hard rule, owner's, 2026-10-11)
> **This is not a rule against AI attribution. It is a rule against FALSE attribution.** The owner
> has nothing against AI tools and would accept a truthful `Co-Authored-By:` naming the tool
> actually in use. What is forbidden is writing an attribution that is **not fact** — naming some-
> thing as author or co-author that is not what was used. Attribution in `git log` is a record of
> what happened, like a measurement in a table, and it is held to the same standard as every other
> claim in this repository: **verified, or not written.**
> **The mistake this exists because of:** four commits on 2026-10-11 were pushed with a
> `Co-Authored-By:` trailer naming a specific AI product — written out because it is the lesson, not
> because the name has any standing here — and **nobody had established that identity and nothing
> had checked it.** The runtime
> was reporting `Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf`, readable in the session log the
> entire time. So the trailer was not a policy violation first — it was a **false statement**, the
> same category as the stale contrast ratios and the blind colour check this folder spends most of
> its prose on; it just happened to be a false statement about the writer rather than about the
> artwork, and it sat in a public append-only record. Gotcha 30 and gotcha 39 in human form.
> **Concretely, for anyone or anything working here:**
> - Do not name a model, product or assistant in a commit, tag, PR or branch name unless you have
>   read that identity out of the runtime in front of you and the owner wants it recorded. "What am
>   I running as?" is one command; answering it by habit is what produced the four commits.
> - Do not invent attribution because a template, a convention or another project does it.
> - Truthful attribution the owner asks for is fine, including naming the tool genuinely in use.
> - Existing honest trailers are not to be touched — Dependabot's `Co-authored-by: dependabot[bot]`
>   is Dependabot's. The rule is *never write something untrue*, not *remove names*.
> **And the harm is not cosmetic, because GitHub resolves the trailer's *email* to a real account.**
> The address in that trailer belongs to Anthropic's own GitHub account (`claude`, id 81847), so the
> false trailer was not inert text in a log message: GitHub credited **that third party as a
> contributor to this repository**, in the sidebar widget on the repo page. Even the correct-looking
> endpoints stayed clean while the widget kept serving it — REST `/contributors`, `/stats/contributors`,
> the atom feed and the page HTML all reported two contributors, because the widget is hydrated by a
> separate, cached pipeline that lags a history rewrite. Lesson, twice over: **an untrue claim in a
> commit does not stay in the commit** — it propagates into surfaces you do not control and cannot
> clear, and the negative check you ran is only as good as the pipeline you actually queried.
>
> ### If it already happened: the fix is a default-branch cycle, not another history rewrite
> Rewriting history removes the claim from git. It does **not** remove the contributor entry, and
> no API call, no `gh` command and no force-push will: the widget is a separate cached derivation.
> What worked on 2026-10-12, on this repo, first try:
> 1. Set the default branch to a temporary branch at the same commit.
> 2. Create a second scratch branch, point the default at it, **delete the real default branch**.
> 3. Wait (~70 s).
> 4. Recreate the default branch **from the saved commit SHA**, point the default back at it,
>    delete the scratch refs.
> Tags, releases and CI were untouched; the SHA came back byte-identical; the phantom contributor
> was gone. Automate it rather than typing it: **`probe/github_refresh_contributors.sh`**
> (`--dry-run` to see the plan, `--verify` to print the pipelines, `--wait N` to change the window).
> **Two traps that script exists to prevent, both hit live during the first manual run:**
> - **Recreate from the SHA, never from a branch ref.** The first attempt did
>   `git push origin refs/heads/<default>-off:refs/heads/main`, and that ref existed only on the
>   remote, not locally: the push failed, and the repo was left with the scratch branch as its
>   default and no `main` for about a minute. `git ls-remote`/the saved SHA is the only trustworthy
>   source here.
> - **There is a window where the default branch does not exist.** Push-triggered CI, deploy hooks,
>   Pages builds, open PRs and anyone cloning in that interval will fail or misbehave. Do not run
>   it during activity, and never on a shared repo without saying so first.
> **And verify in the right place.** REST `/contributors` and `/stats/contributors` reported the
> correct two-contributor list the entire time the widget still showed three, and grepping the repo
> page HTML found nothing because the widget is hydrated client-side. The verdict comes from the
> sidebar in a **logged-out private window**, nowhere else.
> If the cycle does not clear it, the cache outlived the rename or is indexing orphaned objects
> that still resolve by SHA — and then it is GitHub Support, because there is genuinely no API for
> this: `gh` has no support command, and `/support/tickets` 404s for a personal account (it is a
> Premium/Enterprise feature). Template kept at `~/github-support-ticket.md` on the dev machine.
> **Why this is in a file rather than left as a promise: a session cannot remember it.** Every
> session here starts blank; a guarantee given in a chat transcript is worth nothing in the next
> one, so the only thing that survives is this file, which each round reads first. That is also the
> honest answer to "will you remember?" — *no*, which is exactly why it went in here instead.
> **And note the cost of getting it wrong late:** correcting it meant `filter-branch --msg-filter`
> plus a force-push, four rewritten SHAs, and old objects still reachable by SHA on GitHub and
> forever in any clone that had already fetched them. Cheap to check first; not fully undoable
> after. Untrue claims in append-only media are worse than untrue claims in code.

> **Size discipline:** this file is the working set, so finished work gets distilled into a few
> bullets here and its long form goes to the archive. If you catch yourself writing a third
> "FRESH STATUS" day-log into a file this size, distil the older ones instead.

> ## UPDATE THIS FILE AS YOU WORK — NOT AT THE END
> Sessions here die from running out of context, **without warning**, and everything that is
> only in your head is lost. Three sessions have now lost findings this way, and one of them
> lost a fatal bug that then took a fresh investigation to rediscover.
> **The rule: write first, investigate second.** The moment you see something odd, add a
> line to *OPEN BUGS* (symptom + how to reproduce is enough; mark it `(unverified)`). Add to
> *SESSION STATUS* after each milestone — commit, release, broken thing — not when you feel
> done. Short and ugly is fine; you can improve it later, and a `git commit` of the docs is
> cheap. If you have learned something in the last ~10 tool calls and this file does not
> mention it, stop and fix that before continuing.
>
> **Also: never let `/tmp` hold the only copy.** Reproducers belong in `probe/` (see
> `probe/stale_window.py`) or their content goes into this file. See *Forensics* in `AGENTS.old.md`
> (*FORENSICS — recovering a lost finding after a session died*) for what can and cannot be recovered
> after the fact.

Repo: **https://github.com/tjandrasg/kwcapture** (branch `main`; releases `v0.1.0` … **`v0.6.0`**,
every one from `v0.3.0` on carrying a CI-built `manylinux` wheel plus a prebuilt
`linux_x86_64` wheel attached) and on PyPI as
**`kwcapture`** (https://pypi.org/project/kwcapture/) — publish new versions with
`.venv/bin/python -m twine upload -r pypi dist/<sdist and manylinux wheels>` (credentials
in `~/.pypirc`; never commit or print them). Author: Tjandra Satria Gunawan
<tjandra.satria@sci.ui.ac.id>. `origin` is SSH (`git@github.com:tjandrasg/kwcapture.git`).
There is no `gh` CLI here, so repo/release admin (creating releases, uploading assets,
topics) is done with the GitHub REST API via `curl` using whatever credential is
configured for github.com (it is in `~/.git-credentials`) — never commit or print a token.

Working dir: `~/way_scr_cap`. **Read this first if you are a fresh session.**
Status: **done and working** — ~40 fps full-screen / ~185 fps per-window Wayland capture,
Python API + CLI + 165 functional + 37 ring-reader + 98 brand-icon checks. See `README.md` for
user-facing docs; this file is the investigation log + gotchas.

**Unreleased on `main` as of 2026-10-11**: the brand-icon work — artwork shipped inside the
package, `kwcapture install-desktop` installing it into the user's hicolor theme, the correction
of the entry's `Icon=` name, and **the owner's artwork rule**: the icon is `logo/kwcapture-mark.svg`
and only that, resized or re-rendered, never substituted for a monogram (an earlier revision of
the same work shipped the monogram at small sizes; reverted, and now asserted against). Under
*LOGO* below, user-facing in README → *Brand icons*, and in `CHANGELOG.md` → *Unreleased*. Nothing
about capture changed; **37 + 98 green here, 0 skips**, plus `probe/sabotage_icons.sh` at
**10/10 sabotages detected**. `tests/test_kwcapture.py` is **not** green on this desktop and was
never green in this state: it measures **162 passed + 1 failed** (not 165), and there are now **two**
unrelated environmental failures in it — FLAKE-2 (`alpha is opaque`, ~2 runs in 3) and **FLAKE-3**
(the BUG-4 block, three different errors in seven runs, proven from a pristine `HEAD` worktree and
reproduced **0 of 5** standalone). **Both were CLOSED on 2026-10-12 by the owner's ruling: the
desktop's environment (BUG-4's family — non-ECC RAM and a global `LD_PRELOAD` shim here), not
kwcapture bugs, not to be chased and not release-note material**, which is why they are out of
`CHANGELOG.md` §*Unreleased*; both entries stay below as the record and as the standing reason this
machine's functional suite prints 162 + 1 and not 165. A suite count quoted as a single number is a
claim about a machine, so from now on it is written as a measurement with its failure attached — and
the control for it is a CI runner, not this desktop. **CI, measured off the run log of the
push that changed the suite** (`34432a8`, run 38122958295, 2026-10-11): both jobs green —
`build` and `headless KWin capture (Plasma 6, no GPU)` — and in `build`'s log the icon suite prints
**97 passed + 1 skipped**, `RESULT: all icon tests passed (1 skipped)`, the skip being
`[SKIP] desktop-file-validate  tool not installed` (announced, not silently passed), then
**`wheel: 10 icon files`** and **`sdist: kwcapture-0.6.0.tar.gz 10 icon files`**. The previous
suite's numbers were 88 + 1 on the same runner; the +9 is the one-artwork assertions.
*Re-read on the palette push (`4fd386e`, run 38151616537, 2026-10-11): same **97 passed + 1
skipped + 0 failed** in the icon step's slice, same `wheel: 10 icon files` / `sdist: … 10 icon
files`. Counting `[PASS]` over that whole job log instead of the step's slice answers **134** —
37 of those are the ring-reader suite, which is why the slice is the unit.*
*Reading it: `GET /repos/…/actions/runs/<id>/jobs` gives job and step conclusions, and
`…/actions/jobs/<id>/logs` follows a redirect to the log itself — `curl -sL` gets it where
urllib's own redirect handling returns 401, and the per-suite count is `grep -c '\[PASS\]'` inside
the step's own slice of the log, not a guess from the total.*

## FRESH STATUS — 2026-10-09 ~08:20 — **v0.6.0 RELEASED to GitHub + PyPI: the hidden-window enumeration is out**

> **What shipped**: tag `v0.6.0` → `cdb0458` on `main` = the non-normal-window work of the session
> below (dialogs/docks/desktop via the KWin scripting route) plus the headless-CI work already on
> `main`. `ci.yml` `build` and `release.yml` both **success** (runs 37868257712 / 37868258136).
> GitHub release 407395393 carries the CI sdist, the CI `manylinux_2_28` wheel and the locally built
> `linux_x86_64` wheel — same three assets as v0.3.0–v0.5.0. PyPI 0.6.0 carries **two** files: the
> sdist and the manylinux wheel, taken **off the GitHub release** first, so PyPI's sha256
> (`b2683129743983c3…` whl / `610205d2bc3ef1c0…` tar.gz) are byte-identical to the release assets.
> The `linux_x86_64` wheel is a GitHub asset only — PyPI rejects that tag, as the checklist says.

> **Verified, in the order done**: 165/165 functional + 37/37 ring-reader under `-X dev` on this
> desk (one output at 100 %, so the fractional-scaling checks sit in their degenerate branches —
> see FLAKE-1 for why 165 here vs 172 on the two-output desk); the locally built wheel installed in
> a throwaway venv **from `/tmp`** really captures (2560x1440, 99.7 % non-black) and lists
> desktop + dock + the Winamp dialog; the sdist carries no `private/`, no `*.jsonl`, no credential
> — **a loose `ghp_`/`pypi-AgEIcHlwaS` grep hits this very file's checklist text**, so re-grep for a
> long token-shaped run (`ghp_[A-Za-z0-9]{20,}`) before believing a hit; `pip install --no-cache-dir
> kwcapture` in a clean venv outside the checkout gives 0.6.0 and `kwcapture doctor` answers *"full
> window enumeration works via KWin scripting: 3 window(s) outside KWin's own app-window list
> (desktop, dialog, dock)"*. Release notes were PATCHed into the body (CI leaves only the
> `**Full Changelog**` stub — a body with just that stub means the run is unfinished).

> **Worth watching, unverified**: the wider default list is a behaviour change for downstream —
> `iw3-desktop` (nagadomi/nunif, see DOWNSTREAM above) calls `list_windows()` without `all_types=`,
> so it now sees panels and the desktop as well, and a name that used to resolve uniquely can raise
> `AmbiguousWindow`. Nothing in this tree shows that breaking anything, but it is the first thing to
> ask about if a downstream report arrives.

> **Post-release housekeeping, 2026-10-09** (day-log verbatim in
> [`AGENTS.old.md`](AGENTS.old.md) → *ARCHIVED 2026-10-11*): the README badge row (and **no
> download badge** — measured reason, see *README badges* below), the community files
> (`SECURITY.md`, two issue forms + `config.yml`, `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`),
> Dependabot's first PR merged (`2ec83eb`) **with the release workflow rehearsed against it**, then
> `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` → GitHub's community checklist 7/7. Two durable
> findings: **`MANIFEST.in` lists docs by explicit name**, so a new root `.md` is invisible to the
> sdist until it is added there (`SECURITY.md`/`CONTRIBUTING.md`/`CODE_OF_CONDUCT.md` all shipped
> missing from 0.6.0 that way — the published files are immutable, so the fix lands next release);
> and a re-grep for a *token-shaped* run (`ghp_[A-Za-z0-9]{20,}`) before believing a secret scan,
> because this file's own checklist text contains the literal prefixes.
## LOGO — `logo/` is committed, and `kwcapture-mark.svg` is the official mark (2026-10-11)

> **The owner decided it, on 2026-10-11:** [`logo/kwcapture-mark.svg`](logo/kwcapture-mark.svg)
> — the geometric KW monogram whose junction is the **C**, the mouse pointer as the **A**, and
> `PTURE` in type — is the project's logo. `logo/` had been untracked since it was started;
> it is now in git: **49 files** — two Inkscape sketches (inputs, never written to), **two**
> generated SVGs, five tools (`gen_logo.py`, `contrast_report.py`, `validate_logo.py`,
> `render_agreement.py`, `sync_package_icons.py`), the shipped `icon/` set, the documentation
> `preview/` set, and `AGENTS.md` / `README.md` / `LICENSE.md`. (`wc -l` on `git ls-files logo`,
> counted 2026-10-11 after the monogram deletion, not remembered from the 57 this note used to
> say: `kwcapture-mono.svg` is gone and `contrast_report.py` arrived.) **Read
> [`logo/AGENTS.md`](logo/AGENTS.md) before touching anything in there**: it carries THE RULE
> (`WORD = "PTURE"`, never `CAPTURE`), the knob table, the expected numbers and 40 gotchas — several
> paid for by sessions that ran out of tokens.

> **Licence, and why two:** artwork (SVGs, sketches, every PNG) **CC BY 4.0**; the tooling in
> `logo/*.py` **MIT**, matching the package's own [`LICENSE`](LICENSE); the Inter face
> **OFL-1.1**, referenced not shipped. Trademarks are **not** granted by CC BY — the artwork is
> free to copy, the name and mark as a *brand* are not. See [`logo/LICENSE.md`](logo/LICENSE.md).

> **Palette P2 is the mark's paint, applied 2026-10-11**: green `#008c46`, blue `#7f7fff` (was
> `#00ac4e` / `#0000ff`), the owner's choice from six rendered pairs. It changed *paint only* — the
> diff against the previous commit, with hex strings stripped from both sides, is empty — and it is
> worth one line here because it is the reason `logo/contrast_report.py` exists: every ratio this
> project quotes is now re-runnable (`python3 logo/contrast_report.py`, exit 1 if a cell falls under
> the WCAG 3:1 non-text floor) instead of being copied out of a doc. Measured: green **4.34** on
> white / **4.36** on GitHub dark `#0d1117`, blue **3.29** / **5.75** — every cell legal on both
> grounds, which closes the finding that the old blue was **2.20:1** on dark. What it traded:
> the two halves are **1.32:1** apart instead of 2.87, so the C separates by **hue** and would
> collapse in greyscale. `logo/AGENTS.md` §*Still open* has the arithmetic and the argument.

> **`preview/anatomy.png` now boxes all five parts of the mark, and the two new ones are derived,
> not drawn (2026-10-12).** There is no `#k` and no `#w` element in `kwcapture-mark.svg`: `#kw` is
> one closed 19-vertex outline and **K, W and C are index subsets of it** (`K_RING` / `W_RING` /
> `C_RING` in `logo/gen_logo.py`, the owner's numbering), so each letter's box is min/max over its
> own vertices mapped through `#logo`'s transform. Measured: K `7.45..200.67 x 100.97..451.93`,
> W `65.27..451.08 x 281.92..451.10`, overlapping **135 × 169 px** on shared vertices
> **3 4 13 14** — the K's leg *is* the W's first stroke, and reading the rings instead of the prose
> about them is what corrected the round's own plan, which had said "12-14". `logo/preview/anatomy.py`
> asserts three cross-checks on every build (vs `#kw-c`'s path data 0.047 px, vs the validator's
> `#kw` box 0.004 px, vs the rendered ink — a stdlib connected-component labelling — 0.45 px) and
> fails the build under any of them; **no artwork moved** (both SVGs and all 21 `logo/icon/` files
> byte-identical, `sha256sum -c`). **Pushed 2026-10-12** as `1811ebc` (the round) + `ca1bf74`
> (this file and `CHANGELOG.md`), CI run **38192200374** green on both jobs — `build` (15 steps:
> ring-reader, brand-icon, sdist + wheel, *both artefacts carry the brand icons*, wheel install,
> sdist from scratch) and `headless KWin capture (Plasma 6, no GPU)` — **step conclusions only**,
> because the jobs endpoint answers this credential with `log_url: null`, so the printed
> pass/skip counts in the log body are not claimed from here. Full account and the measured
> annotation contrasts in `logo/AGENTS.md` §*Still open*.

> **The README header is the mark now**, embedded as an absolute
> `raw.githubusercontent.com/tjandrasg/kwcapture/main/logo/icon/kwcapture-mark-256.png` URL —
> absolute on purpose, because PyPI renders this same README and does not resolve repo-relative
> image paths. Consequence worth knowing: **the header 404s on any branch that has not been
> pushed to `main`**, so verify it after a push with
> `curl -o /dev/null -w '%{http_code}\n' <that url>` and expect 200.

> **Two uploads remain manual, and no script can do them** (`logo/AGENTS.md` gotcha 34, probed
> with an admin token rather than assumed): GitHub exposes no REST or GraphQL field for a
> repository's picture — `POST /repos/…/social_preview` answers **404**, GraphQL's 262 mutations
> include no `avatar|social|preview|image|upload`, and the web app redirects a PAT to `/login`.
> Click: *Settings → Social preview → Edit image* with `logo/icon/github-social-preview.png`
> (1280×640). **Done and verified 2026-10-11** — see the block below. A **repository has no
> avatar** — its picture *is* the social preview — and `tjandrasg` is a **personal** account
> (`owner { __typename }` → `User`), so there is no org avatar either: `github-avatar-400.png` is
> only ever the *user's* profile picture, which is an account setting outside this repo.
> The read side of that API works, so the click is checkable from a shell:
> `repository(owner:"tjandrasg", name:"kwcapture"){ usesCustomOpenGraphImage openGraphImageUrl }`
> — measured **`false`** earlier on 2026-10-11, then **`true`** after the owner clicked, with
> `openGraphImageUrl` → `https://repository-images.githubusercontent.com/1406948211/dc44cc05-…`.
> And the check goes one step further than the flag, because `true` only proves *an* image: fetching
> that URL returned **1280×640, 84 565 B** with **0 of 51 681 sampled pixels differing** from
> `logo/icon/github-social-preview.png`. GitHub stores the upload rather than re-rendering it, so a
> recolour of the mark means **re-uploading it** — not something the repo can do for you.
> **And the recolour happened the same day, then this item came round twice.** Palette P2 landed
> and `icon/github-social-preview.png` became **84 871 B** in the new paint, which made the live
> preview — the old upload, `#0000ff`/`#00ac4e` — stale while `usesCustomOpenGraphImage` still read
> `true`. That combination is the reason the check is written in pixels: a flag that is technically
> accurate and completely misleading. **The owner has since re-uploaded it, and it verifies**:
> `openGraphImageUrl` is now a **different object id**,
> `…/1406948211/5425fcdb-bcfa-4d50-b99e-30d4087c1849` where Round 13 recorded `dc44cc05-…` — GitHub
> mints a fresh URL per upload, so the URL changing is itself evidence — and that URL serves
> 1280×640 / **84 871 B** with **0 of 819 200 pixels** differing from the committed P2 card and
> **55 119 px (6.73 %)** differing from the pre-P2 card. Nothing owed here any more.
> The optional **user profile picture** is a separate question, and it was measured rather than
> assumed: `https://github.com/tjandrasg.png` serves 460×460 / 48 875 B differing from
> `icon/github-avatar-400.png` in **100 %** of pixels in *both* palettes — it is unrelated personal
> artwork, not a stale copy of ours. So `github-avatar-400.png` (P2: 25 293 B) is an asset that
> exists and is **unused**; no doc may describe it as live, and using it would be an account
> setting no script can reach (gotcha 34).
> **The standing rule, because a recolour reopens this every time:** after any change to
> `icon/github-social-preview.png`, re-fetch `openGraphImageUrl` and diff **pixels against the
> committed file**. `true` proves an image is set; only the pixels prove which palette is live.

> **The mark is installed on the desktop now, not just displayed** (2026-10-11). `kwcapture
> install-desktop` / `setup` copy the **mark itself** — `logo/kwcapture-mark.svg`, rendered at each
> size and copied, never redrawn — into
> `$XDG_DATA_HOME/icons/hicolor/{16,24,32,48,64,128,256,512}/apps/kwcapture.png` + `scalable`,
> from `kwcapture/icons/` — a copy, never a resample, byte-identical to the reviewed artwork in
> `logo/icon/contact.png`. That copy is generated by `logo/sync_package_icons.py`, whose `--check`
> runs inside `tests/test_icons.py`, so the shipped icon cannot quietly become last month's render.
> **Branding is a note in `doctor`, never a problem count** — a missing icon set must not make a
> working capture look broken, and the automatic first-`Capture()` path still writes exactly one
> `.desktop` file and installs nothing (there is a check asserting that promise). Licence travels
> with the artwork: `kwcapture/icons/COPYING.md` says CC BY 4.0 for the pictures, MIT for the
> code, next to the files an installed tree actually contains. Wheel and sdist both carry the 10
> files (verified by building them here: `unzip -l` / `tar tzf`), and `logo/` itself stays out of
> the sdist. Three measured findings behind the design — see the gotchas below and README → *Brand
> icons*: the six-release `Icon=accessories-screenshot` **resolves in no theme on this KDE
> desktop**; **a `;` fallback chain is not parsed by anyone**; and **entries are keyed per helper
> binary**, so installing from one venv refreshed one of this machine's three stale entries —
> hence `_desktop.refresh_entries()`. `kwcapture doctor` on this desktop reports *brand icons: 9
> files in ~/.local/share/icons, entry uses `Icon=kwcapture`*, and all three entries on this
> machine say `Icon=kwcapture`.

> **`logo/*.jsonl` is gitignored, name-agnostically** (`.gitignore` line 40). A design-session
> transcript lands in that directory under a *different* filename every session; the old root rule
> `chat_his*.jsonl` matched exactly one of them, which is how the 2026-10-06 incident happened.
> Verified again on 2026-10-11 with `git check-ignore -v` **and** with `git add -A --dry-run`,
> which staged 55 files and no transcript. Transcripts also contain screenshots of this desktop:
> they are personal data, they are licensed by nobody (`logo/LICENSE.md` §6), and they are never
> to be read whole — `logo/AGENTS.md` §*Reading the transcript*.

## HEADLESS / NESTED KWin — what is settled (full day-log archived 2026-10-09)

> Long form: the `FRESH STATUS — 2026-10-08 ~19:20` day-log in `AGENTS.old.md` (under
> *ARCHIVED 2026-10-09*). The durable part, and it is now also in README → *How this is tested* and in
> the comments of `probe/ci_headless_kwin.sh`:

* **`org.kde.KWin.ScreenShot2` exists only while KWin is OpenGL-compositing** — its sole owner is
  the screenshot effect, and `ScreenShotEffect::supported()` is `effects->isOpenGLCompositing()`.
  No GL compositing ⇒ the bus name never appears ⇒ `was not provided by any .service files`.
* **OpenGL compositing needs a DRM render node.** The virtual backend offers it only if
  `findRenderDevice()`/`drmGetDevices2()` found one; otherwise KWin silently falls back to QPainter.
  So no Mesa env tinkering helps — `LIBGL_ALWAYS_SOFTWARE`, `EGL_PLATFORM=surfaceless`, installing
  `libgl1-mesa-dri` change nothing, because the decision is made before Mesa is asked.
* **A GitHub-hosted runner can never provide one** (measured on the runner: `/dev/dri/card1` exists
  as `hyperv_drm` with **no `renderD*` node**, and `vgem`/`vkms` are not built for the azure kernel
  even after installing `linux-modules-extra-*`). Window *listing* works there; frames cannot.
  What would work: a GPU runner, or a self-hosted KDE runner — with a render node present the job
  silently switches back to strict and tolerates nothing.
* **The tolerant path is deliberate, not a hidden failure:** `KWCAPTURE_NESTED_ALLOW_NO_SCREENSHOT2=1`
  converts *only* missing-ScreenShot2 failures into a printed `ENVIRONMENT LIMITATION`; socket,
  authorisation, output/window listing and every other `doctor` check still fail the job.
* **Run the harness by hand** (no GitHub involved, ~6 s on a Plasma box):
  `dbus-run-session -- bash probe/nested_kwin_test.sh`, or
  `docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim bash /w/probe/ci_headless_kwin.sh`.
* Two unrelated traps from that session, still true: the Qt **Wayland** QPA plugin is the Debian
  package **`qt6-wayland`**, not `qt6-qpa-plugins`; and `QT_LOGGING_RULES="kwin_core.debug=true"`
  makes KWin say *why* it is not compositing instead of one vague warning.
* Not the problem, then or now: **PipeWire**. `ScreenShot2` needs none — we hand KWin a pipe fd and
  `ScreenShotWriter2` writes the QImage into it. Don't add a `pipewire` package chasing that log line.


## DOWNSTREAM — nagadomi/nunif#746 is MERGED (this is the compatibility list for future releases)

`iw3-desktop` (part of [nunif](https://github.com/nagadomi/nunif)) ships kwcapture as its **optional
Wayland (KDE Plasma) screenshot backend**; nagadomi merged it 2026-10-08 into `nagadomi/nunif:dev`.
`README.md` now has a **Used by** section (commit `d429ea2`) naming it and the API it calls, which is
the compatibility list for future releases: `Capture(monitor=…)` / `Capture(window=…)` with
`cursor=` and a private `shm=`, `grab(copy=True)`, `geometry()`, `list_monitors(measure_scale=True)`,
`list_windows()`, `find_window()` + `AmbiguousWindow`, `unique_shm_path()`, `effective_scale` /
`area_scale`. It never requires kwcapture at import time and installs nothing automatically — the
maintainer's condition for merging — so **do not make importing `kwcapture` heavier or add a hard
install-time step**, or the optional-dependency story upstream breaks.

His stated reason for accepting, worth keeping in mind for any future discussion with a distributor:
he had not tested KDE capture but it "won't affect other environments", and on the shipped binary —
the GitHub Actions build "provides some evidence that the project is being handled responsibly",
though "ultimately it comes down to whether the binary is trusted". The facts that answer that
(verified in this tree, do not restate them without re-checking):
* the helper is one C file (`kwcapture/native/kwcapture.c`, 2141 lines) + `kwcapture_shm.h` (103),
  and its **direct** dependencies are exactly three — `libc`, `libsystemd` (sd-bus),
  `libwayland-client` — with no RPATH (`readelf -d`, not `ldd`: ldd also lists whatever the
  desktop session put in `LD_PRELOAD`, which on this desk adds a GTK CSD shim that the binary
  does not need). The sdist carries **no compiled artefact at all**: 5 `.py` files + the `.c` +
  the header. All of this is spelled out, with runnable checks, in `SECURITY.md`;
* the only outbound connection in the source is `wl_display_connect(NULL)` — no sockets, no network
  code, no root, no portal; frames come from the shm ring KWin fills;
* KWin's authorisation is a plain `.desktop` file in `~/.local/share/applications` the user can read
  and delete (`_desktop.py`);
* the sdist carries the C source and `setup.py`/`_native.py` build it with `cc -O2 -std=gnu11` +
  pkg-config, so `pip install --no-binary=kwcapture kwcapture` needs no trust in us at all;
* the PyPI files for a release are the artefacts of that tag's public `release.yml` run.

## ARCHIVED into AGENTS.old.md (2026-10-08, and again 2026-10-09)

Moved out **verbatim** — session logs of *released* work whose conclusions already live in
`CHANGELOG.md`, `README.md`, `SECURITY.md` or the CI job's own comments. Nothing is ever deleted; the
archive keeps the reasoning and the dead ends, and this file is what a fresh session can hold in its
head. If you are about to add a third `FRESH STATUS`, distil one out instead.

**2026-10-11** (during the brand-icon work; `wc -c` was **58 859** at the moment of the move and
**64 846** with the new material in it — measured, because a size note in a size note is exactly
the number that goes stale): the *post-release housekeeping* day-log
of 2026-10-09 → distilled into the v0.6.0 FRESH STATUS block above. Nothing else moved; the two
durable findings in it (`MANIFEST.in` lists docs **by name**; re-grep for token-shaped runs before
believing a secret scan) stayed here as bullets, and the new brand-icon material went into **LOGO**
and *Gotchas* rather than into a third day-log.

**2026-10-09** (file had grown back to 77 KB): the 2026-10-08 headless-CI day-log → distilled into
**HEADLESS / NESTED KWin**; the 2026-10-08 non-normal-window day-log → distilled into the
**SESSION STATUS → released as v0.6.0** section; BUG-1's original analysis, BUG-2's full analysis and
BUG-4's bisect record → each bug keeps its conclusion, rate, next experiment and guardrails; the
completed `~~done~~` bullets from *Ideas not done yet*; and a shorter *Community files* section.
**2026-10-08** (from 81 KB): the nine `FRESH STATUS — 2026-10-07 …` day-logs → **SCALES** and
**MONITORS & RESILIENCE**; the original nested-`--virtual` discovery write-up; BUG-4's three-session
hunt; BUG-3 (fixed, lesson kept as a Gotcha); the v0.1/v0.2 file map, benchmark tables, packaging/CI
notes and the forensics write-up.


## REPOSITORY HYGIENE — `private/` is the only place for non-source files

`private/` exists for this: **anything that is not source — chat transcripts, captures,
dumps, logs, credentials, scratch notes — goes in `private/`**, which is ignored by both
`private/.gitignore` (`*` + `!.gitignore`) and the root `.gitignore` (`private/*` +
`!private/.gitignore`). Only the ignore file itself is tracked, so the folder appears in
every fresh clone and the rule travels with the repo.

**Why this exists:** on 2026-10-06 a `git add -A` swept the user's 1.1 MB private chat
transcript (`chat_his.jsonl`, dropped in the repo root) into a commit and pushed it to the
**public** repo. It was removed from the branch and the history was rewritten
(`filter-branch` + reflog expiry + `gc --prune=now` + force-push), tags / GitHub release
assets / PyPI sdists never contained it — **but GitHub keeps serving the old dangling commit
objects**, both over HTTPS (`raw.githubusercontent.com/<repo>/<old-sha>/chat_his.jsonl`
→ 200 with the full file) and over the **git protocol**
(`git fetch --depth=1 origin <old-sha>` then `git cat-file`). Verified 2026-10-06.
**Do not write the old short/full SHAs into this file or into any commit message**: GitHub
resolves abbreviated SHAs, so publishing one hands every visitor a working download link.
They are deliberately omitted here. **Force-pushing is NOT deletion on GitHub** — at the time of writing
`raw.githubusercontent.com/<repo>/<old-sha>/chat_his.jsonl` still returns the full file,
and it will until GitHub Support purges the dangling objects (the user has been told to open
that request). Assume a force-push does not un-publish anything.

**Rules that follow from it:**
* Non-source files go in `private/`, never in the repo root (the old `*.bgra` scratch dumps
  in `/tmp` are the same hazard — they are gitignored, but `private/` is the habit).
* `git add -A` is acceptable **only** because `private/` is ignored now — and only if you
  check the `git status --porcelain` output the command implies. Before a push that will be
  public, run `git add -A --dry-run` and read it (it lists exactly what would be staged).
* Verify an ignore rule rather than trusting it: `git check-ignore -v <path>` shows which
  rule matched. A `.gitignore` entry that silently matches nothing looks identical to one
  that works.
* Never `git add -f`/`git add private/...` — `-f` overrides the ignore rules that protect
  this folder.

## SESSION STATUS — 2026-10-08 ~23:50 → **released as v0.6.0** (log archived)

> Full session log: the `SESSION STATUS — 2026-10-08 ~23:50` day-log in `AGENTS.old.md` (under
> *ARCHIVED 2026-10-09*). Feature list in
> `CHANGELOG.md` 0.6.0, user docs in README → *Per-window capture*, security treatment in
> `SECURITY.md`. What a future session must not have to re-derive:

* **Why krunner was not enough:** `windowsrunnerinterface.cpp` skips `!window->isNormalWindow()` in
  every branch of `Match()`, and `CaptureWindow` resolves only `QUuid` handles that come from
  `Window::internalId()` = `QUuid::createUuid()` — random, so not derivable from an X11 window id.
  `getWindowInfo` takes a uuid only; `queryWindowInfo` is the interactive picker. **Conclusion: the
  scripting interface is the only API in Plasma 6 that reaches the full window list.**
  KWin source reference: `invent.kde.org/plasma/kwin/-/archive/v6.6.6/...` (fetch it before
  answering any "does KWin expose X?" question).
* **The mechanism:** `org.kde.kwin.Scripting.loadScript(path, plugin)` is unauthenticated and takes
  a plain path — nothing has to be installed under `~/.local/share`. JS `workspace.windowList()` is
  `workspace()->windows()`, unfiltered. Plasma 6 has no `registerDBusAdaptor`, so the reply comes
  back through `Script::callDBus` **to our own unique bus name**, nonce-guarded. `Script::run()`
  early-returns while running ⇒ load once per query + `unloadScript`, never `run()` in a loop.
  Measured load+run+reply ≈ **0.5 ms**.
* **Implemented in** `kwcapture/native/kwcapture.c` ("full window enumeration"): `collect_windows()`
  = krunner pass + `collect_windows_script()`; failures are a stderr note plus the old list, never a
  failed call. Flags `--normal-only`, `--require-full` (exit 3); JSON gains `window_type_name` +
  `krunner_listed`. Probes: `non_normal_windows.py`, `kwin_script_enumerate.py`,
  `kwin_script_failure_path.py`.
* **Behaviour change that will generate reports:** a *name* can now match its own dialog too, so a
  lookup that used to resolve can raise `AmbiguousWindow`. That is the honest answer; `--normal-only`
  / `all_types=False` restores the old list.


## OPEN BUGS — found, not yet fixed

> **RULE FOR FRESH SESSIONS: anything that looks wrong goes in this section the moment you
> see it, before you chase it.** Do not investigate first and write it up later — two
> sessions have now lost findings that way. A half-paragraph with the symptom is worth more
> than a perfect post-mortem that never gets typed. Mark unverified guesses `(unverified)`.

### FLAKE-3 (test suite, not the library): the BUG-4 regression block fails in-suite with three *different* errors, and the harness cannot say where

> **CLOSED 2026-10-12 by the owner's ruling — environmental, this desktop, not a kwcapture bug, and
> not to be tracked further.** Same family as BUG-4 below (*root-caused 2026-10-07 — NOT OURS*, and
> "probably not a software bug": non-ECC RAM and a global `LD_PRELOAD` shim on this machine), same
> family as the `gen_logo.py` fontTools crash in `logo/AGENTS.md` §*Still open*. The evidence here
> already says it: it reproduces from a pristine `HEAD` worktree, it goes away standalone (0 of 5),
> and it prints three *different* errors from one block on identical input. Chasing a fault the
> hardware injects costs tokens and teaches nothing about this library, so: **do not spend a round on
> this, and do not re-add it to `CHANGELOG.md`** — it came out of *Unreleased* with this ruling. The
> entry stays as the record and as the standing explanation of why the functional suite on **this**
> desktop prints **162 passed + 1 failed**; a CI runner on healthy hardware is the control. If the
> cheap harness fix (print `traceback.format_exc()` in those two handlers) ever gets done for another
> reason, fine — but no investigation is authorised on this.

* **Seen 2026-10-11 ~00:15, found while re-running every suite the palette round was required to
  re-run.** `tests/test_kwcapture.py` → *regression: BUG-4 zero-copy read path* reports
  `[FAIL] BUG-4 regression ran` and the suite prints **162 passed + 1 failed** instead of 165.
* **Three distinct failures, one block, across 7 runs of the same tree:**
  `AttributeError: 'mmap.mmap' object has no attribute '_ring_slots'`,
  `AttributeError: '_Hdr' object has no attribute '_hdr'`, and
  `CaptureError: unhandled pixel format 6` — and that last one **cannot be true** as written,
  because format 6 *is* in the allow-list at `kwcapture/__init__.py:1716`, so the value read out of
  the descriptor is not the value the message prints.
* **Proven not to be anything in the working tree**: a **pristine `git worktree add /tmp/pristine
  HEAD`** — `git status --porcelain` empty, none of the palette or `tiles.py` changes present —
  failed the same block on 1 of 3 runs (and `alpha is opaque` on 2 of 3). Standalone, the same
  sequence run 5× against the live compositor with per-run shm tags: **0 of 5 failed**. So it is
  **in-suite only** → cross-test interference, not the read path itself.
* **The actual defect in the harness, and the reason this is still a mystery**: both guards are
  `except Exception as e: check("BUG-4 regression ran", False, f"{type(e).__name__}: {e}")`, which
  prints the *message* and throws the **traceback** away. A wrong-`self` `AttributeError` is
  localisable in one line and cannot be localised from `type + str`. **The cheap fix belongs to a
  round that owns `tests/`**: print `traceback.format_exc()` in that handler (and the BUG-3 one
  above it), then the next occurrence names the frame instead of joining a list of unrepeatable
  one-liners. Suspect to check first, in the same breath: the block uses the **non-unique**
  `default_shm_path("bug4")`, while `unique_shm_path()` exists precisely because two `Capture`
  objects must never share a ring file — and earlier blocks in this suite `restart()` and kill
  daemons on purpose.
* **Why it was reported and not patched**: this round's scope was paint (`logo/`), and the last two
  bullets are a test-harness change plus a possible library question. Making a red suite green by
  editing the assertion is what FLAKE-2's entry refuses to do, and the same rule applies when the
  suite is red for a *new* reason. Owner's call, in order: (a) add the traceback to the two handlers
  (small, no behaviour change, makes the next sighting diagnosable); (b) give the block its own
  `unique_shm_path()` and re-run 20× to see if the interference goes away; (c) only then decide
  whether anything in `_view()` is genuinely wrong.

### FLAKE-2 (test suite, not the library): `alpha is opaque` fails whenever a rounded-corner window is on screen

> **CLOSED 2026-10-12 by the owner's ruling — environmental, this desktop's compositor, not a
> kwcapture bug, and not to be tracked further; out of `CHANGELOG.md` *Unreleased* with that
> ruling.** The measurement below stands and is not disputed: 4 pixels at alpha 253/254 in the
> rounded bottom corners of a live KWin composite, ~2 runs in 3 here, and pristine `HEAD` does the
> same. It is what this compositor hands back for a rounded corner, not what this library does to a
> frame, so it is a question about KWin and not a defect to fix here. The entry stays for the record
> (and for the standing reason the functional suite on **this** machine is not 165/165) — **do not
> chase it, and do not weaken the assertion to make a number look green.**

* **Seen 2026-10-11 ~20:40, most runs** — `check("alpha is opaque", int(arr[..., 3].min()) == 255)`
  on a live full-screen grab. Measured: **24 of 25 grabs** carry **4 pixels** at alpha **253/254**,
  at (284,1144), (2275,1144), (289,1149), (2270,1149). Those are exactly the **bottom corners of the
  System Monitor window** (`1992x907+284+243` → bottom edge y=1149, corners x=284 / x=2275): where
  KWin rounds a window corner, the composited screenshot comes back very slightly non-opaque.
* **Not a recolour bug, and proven that way**: the same check fails **7 of 8** grabs from a
  **pristine `git worktree add /tmp/pristine HEAD`** carrying none of the working tree's changes,
  and palette P2 touches nothing under `kwcapture/` except `icons/` (data). The suite is otherwise
  green: **165 checks**, the 164 others passing.
* **Why it was reported instead of fixed**: the assertion is about the *compositor*, not about this
  library, and the interesting question is unanswered — is a screenshot's alpha channel allowed to
  be non-opaque at a rounded corner, and does anything downstream (`save`, PNG encoding, the ring
  reader, `nunif`) assume 255? Tightening the check to `>= 250` or masking the corners would retire
  a real question to buy a green tick (the `logo/` house rule: a measurement that contradicts a
  claim gets reported, not routed around). Owner's call; the cheap honest option is to assert
  opacity on a controlled surface and keep a *separate*, explicitly-labelled check for the live
  desktop, which is what FLAKE-1's fix note argues for too.
* **Count note while someone is here**: 165 checks on this desk (single output DP-1 2560×1440 @
  100 %, per `kwcapture monitors`), matching FLAKE-1's note below; the count moves with outputs.

### FLAKE-1 (test suite, not the library): `area_in='physical' grabs the device region it names` fails when the screen is animating

* **Seen 2026-10-08 ~19:10**, once, on the desktop: `[FAIL] DP-1: area_in='physical' grabs the
  device region it names  MAD=70.0 (display == scene: one mapping only; detail 12.3)`. Rerunning
  the whole suite immediately after: **152/152 green**, twice. Nothing in the library was touched
  (that branch changes `probe/`, the workflow and the docs only).
* **Why the test can do that** (`tests/test_kwcapture.py`, the `mphysnat`/`mphys` pair): it grabs
  the whole output, picks the *most detailed* 256x144 device rectangle it can find, then grabs that
  rectangle again in a **second, separate** ScreenShot2 request and compares contents. Detail is
  exactly what animation looks like to that scan, so a video / terminal / anything repainting in
  the chosen rectangle makes MAD explode (70 is far past a cursor sprite: ~12 at most). The
  comparison is between two frames, not two mappings.
* **Fix, when someone touches that test**: grab the whole output twice and mask out every rectangle
  that differs between them, then choose the detailed-and-stable patch. Do not just loosen the
  20.0 threshold — a threshold that has to cover a moving picture protects nothing.
* **Also note**: the suite's check **count depends on how many outputs the desk has** — 172 on the
  two-output desk (DP-1 75 % + HDMI-A-1 125 %) that the v0.5.0 notes describe; **165 measured on
  2026-10-09 ~08:20**, when the desk had a single output at 100 %. The +13 non-normal-window checks do
  not multiply with outputs, so 172 there is arithmetic, not a measurement.
  **The desk changed again later the same day**: HDMI-A-1 (3840×2160) is back at 100 % beside DP-1
  (2560×1440 at 100 %), so the number in README/CHANGELOG (165) is the *single-output* figure and the
  current two-output count has **not** been measured. Re-run and count the `[PASS]` lines before
  quoting anything, and `kwcapture monitors --measure-scale` first: the per-output checks
  (`area_in="physical"` especially) only mean something when a display scale and the scene scale
  differ, and this desk has neither right now (x1/x1 → the degenerate "one mapping only" branch).

### BUG-1 (surfaced in v0.4.0; KWin's behaviour itself is unfixable): a **minimised window captures a STALE frame**

> **STATUS — fixed as far as it can be fixed (v0.4.0).** KWin simply does not render a
> minimised window, so the stale pixels are not something we can change; what we can do is
> **stop letting it be silent**, and that is implemented:
> * **`Capture(stale_check=True)`** → `grab()` consults `getWindowInfo` (throttled to ~10/s)
>   and sets **`Capture.stale_frame`**, emitting a one-shot `RuntimeWarning` on the transition
>   into staleness. Default **off** — the check is a D-Bus round trip and must not tax the
>   185 fps window path. `stale_frame is False` therefore means *unknown*, not *fresh*.
> * **`Capture.window_minimized`** — the same answer on demand (raises `CaptureError` for
>   non-window captures); a window that has vanished entirely counts as minimised.
> * Regression tests: 6 checks in the window section (flag set/cleared, warning issued,
>   frames really byte-identical, default off). `probe/stale_window.py` now also asserts the
>   **surfacing** works and exits 0 when it does — the underlying KWin staleness is expected
>   to remain forever, so that is no longer a failure condition.
>
> The original 2026-10-06 analysis is archived; what it concluded is above.


The original analysis — how it was reproduced with a self-repainting `konsole`, the three fix options
considered before the one that shipped, and the fact that the repro script lived in `/tmp` (so it is
gone; `probe/stale_window.py` is the durable version) — is in `AGENTS.old.md` (*BUG-1: the original
analysis*). Two things from it are still worth knowing: **the stale buffer is not the last frame before minimising** (it is whatever KWin
rendered last, possibly mid-animation), and the fix deliberately avoided a per-frame D-Bus round
trip — a `KWC_ERR_STALE` frame status would need `KWC_VERSION` bumped to 3.


* **Also unverified, same family — test these next** (same silent-staleness shape):
  window on **another desktop** (switch with `/KWin setCurrentDesktop`), window on another
  **activity**, and a window that is fully **occluded** — README → *Per-window capture* claims
  "no cropping by whatever is on top of it", and that was verified for **geometry** only, never for
  **liveness** (an occluded window's buffer could in principle be as stale as a minimised one).

### BUG-2 (`sched_yield()` in the grab hot path) — fixed in v0.4.0; kept here for the hunt, not because it is open

A lazy ctypes init inside `grab()`'s busy-wait caught only `OSError`, but a missing libc symbol
raises **`AttributeError`** — so on musl or odd SONAMEs every capture died, not one code path.
Fixed in v0.4.0: catch both, keep the fallback a real named function, and guard the cache with
`callable()` rather than `is None`, with a regression test (`regression: BUG-2 sched_yield`).

The author's remembered `TypeError: 'int' object is not callable` was **never reproduced and is not
in the tree or its history**; `libc.sched_yield()` returns int 0, so a stray paren
(`= libc.sched_yield()`) caches 0 and produces exactly that message from far away — a hypothesis,
not a finding, and the same family is covered by BUG-4 (environmental). If it reappears:
`grep -rn "sched_yield" kwcapture/`, rerun under `python -X dev -X faulthandler` for a full
traceback, and remember the *frame above* is where an int came from. Full analysis, the AST scan
that came up empty, and the three verified branches: `AGENTS.old.md` (*BUG-2: sched_yield*).


### BUG-4 (ROOT-CAUSED 2026-10-07 — NOT OURS): corruption while reading shared memory zero-copy

> **Not a kwcapture bug, and probably not a software bug.** Never write "BUG-4 fixed" — write
> **"not ours, guardrails added, fault rate unchanged."**

* **Reproduces with no kwcapture at all:** `probe/race_bisect.py` / `probe/corruption_rate.py` hit
  the historic symptoms — `TypeError: 'int' object is not callable`, `IndexError: only integers…`,
  SIGSEGV, `double free or corruption (out)` in numpy's array dealloc — in a tight loop of numpy
  views over an `mmap`, no daemon, no writer, no thread.
* **Rewriting the read path changed nothing:** `probe/fault_rate.py` faulted 4/4 rounds on the old
  path and 4/4 on the hardened one (table in `probe/FAULT_RATE_RESULTS.txt`), and a
  cache-views-per-slot variant faulted 3/3 — so not the view-churn either. **Rate ≈ 1 event per
  10⁵–10⁷ view constructions**, non-deterministic; at ~40 fps that is days between events.
* **Likeliest cause was the box**: `llama-server` at ~103 GB RSS (72 GB shared), `MemFree` ≈ 1 GB of
  131 GB, `SwapTotal = 0`, direct reclaim live, **non-ECC** RAM, a kernel oops in page reclaim the
  same day, and a `.crash` record showing **SIGBUS** for the test suite — a ring page that could not
  be materialised looks exactly like "flaky, impossible values". RAM was later taken off XMP
  (5200 → 4800 MT/s); `probe/fault_rate.py` still faulted on the live ring afterwards, while the
  no-writer probes stayed clean for ~144M iterations — which is what `probe/writer_reader_repro.py`
  was built to test (raw shm + one concurrent writer, no kwcapture).
* **Decisive experiment, still the right one:** run it on another machine, or with `llama-server`
  stopped — `KWC_ITERS=40000000 .venv/bin/python -X dev probe/fault_rate.py`. Clean there ⇒
  environmental, closes. Faults there too on the same numpy/CPython ⇒ report upstream with
  `probe/corruption_rate.py`'s ~20-line core and the dealloc trace.
* **v0.4.0's read-path work stands on its own** (see `CHANGELOG.md` 0.4.0): single contiguous
  descriptor read, geometry validated once per generation, bounds-checking before any value becomes
  an offset/count/shape, **read-only** client mapping, newest-published-frame semantics, one retry
  of a torn `copy=True` read, and a generation counter that refuses a frame spanning
  `restart()`/`close()`. Correctness fixes — **not** a mitigation of this fault.
* Guardrails that run in CI without a compositor: `tests/test_ring_reader.py`.
  Full bisect record, the mis-executed-bytecode observations, the memory forensics and the
  head-to-head table: `AGENTS.old.md` (*BUG-4: the bisect record, 2026-10-09 archive*).


#### BUG-4b: `CaptureError: daemon error: Success` — double read of `hdr.error`

`_check_error()` reads the shared `error` field more than once (once to decide, once to
format), so a concurrent write can produce the self-contradictory message *"daemon error:
Success"*. Read it into a local **once** and raise from that. Same class of torn read as
BUG-4; fix together.

## Goal
Make a **fast** full-screen capture program on Wayland. Original experiments
(`probe/bench_original.py`, `bench_result.md`): `PIL.ImageGrab` shells out to `spectacle`
(~2 fps); `mss` is 1100 fps but captures **XWayland** (black for native Wayland windows)
and dies when `$DISPLAY` is unset. Both unusable.

## Environment facts
Ubuntu, Plasma **6.6**, kwin 6.6.6 (`kwin_wayland` + `kwin_wayland_wrapper`), Wayland session,
single output `DP-1` 2560x1440@164.69Hz scale 1. `$XDG_RUNTIME_DIR=/run/user/1000` (tmpfs 13G).
`grim` absent; `xdg-desktop-portal` main daemon NOT running (portal/PipeWire route avoided).
KWin does **not** advertise `ext_image_copy_capture_manager_v1` (checked by dumping the
Wayland registry — `probe/globals.c`, compiled `probe/globals`); its XML on disk comes from
wlroots deps only. No `wlr-screencopy` (KWin is not wlroots). XWayland root window is black.
Toolchain: gcc, `pkg-config libsystemd` (sd-bus 259), `wayland-client`, `wayland-scanner`.
venv `~/way_scr_cap/.venv` (Python 3.14.4): numpy, pillow, mss, wxPython, dbus-fast, dasbus,
opencv-python-headless; plus `.pth` → `/usr/lib/python3/dist-packages` so `import gi`
(PyGObject 3.56 + Gst typelibs) also works inside the venv.

## KEY FACTS — the essentials (full investigation log in AGENTS.old.md)

* **Capture API**: D-Bus service `org.kde.KWin.ScreenShot2`, path `/org/kde/KWin/ScreenShot2`,
  methods `CaptureScreen(s)`, `CaptureActiveScreen`, `CaptureArea(x,y,w,h)`,
  `CaptureWorkspace`, `CaptureWindow(handle)`, `CaptureActiveWindow`, `CaptureInteractive(u)`,
  each `(…, options a{sv}, pipe h) -> a{sv}`. Reply keys: `type="raw"`, `format`
  (**6 = ARGB32_Premultiplied = BGRA bytes**), `width`, `height`, `stride` (bytes/row),
  `scale`, `screen`, or **`windowId` for window captures**.
* **KWin replies BEFORE writing pixels** (`ScreenShotSinkPipe2::flush()` returns, then a
  QThreadPool writer does the copy) → EOF on our pipe is the frame boundary, and this is what
  makes the no-pixels `--active-window-id` query (~8 ms) possible.
* **Authorisation**: pid → canonical `/proc/<pid>/exe` → a `.desktop` file whose `Exec=`
  first token canonicalises to that exe and whose `X-KDE-DBUS-Restricted-Interfaces` contains
  `org.kde.KWin.ScreenShot2`. **A Python script can never be authorised** → native helper +
  desktop entry (`_desktop.py`, `kbuildsycoca6`, async propagation → retry with backoff).
* **Window enumeration** (KWin has none on ScreenShot2) needs **two** sources. (1)
  `/WindowsRunner` `org.kde.krunner1` `Match("")` — empty query matches every window,
  locale-independent (do NOT use the translated `"window"` keyword); ids are
  `"<action>_<uuid>"`, dedupe (one entry per desktop); `Run("0_<uuid>","")` activate / `1`
  close / `2` minimise. **It filters: every loop skips `isUnmanaged()` and
  `!isNormalWindow()`** ("NET::Normal or NET::Unknown non-transient"), so dialogs, docks,
  the desktop, splash, tooltips and override-redirect windows are unreachable there — no
  query string changes that. (2) `org.kde.kwin.Scripting` `/Scripting`
  `loadScript(filePath, pluginName) -> i` + `org.kde.kwin.Script` `/Scripting/Script<id>`
  `run()` + `unloadScript(pluginName)` gives the whole list, because the JS global
  `workspace`'s `windowList()` is literally `Workspace::windows()`; the script answers by
  calling *us* (`callDBus(our_unique_name, …)`, async, so the compositor never blocks) —
  Plasma 6 has no `registerDBusAdaptor` anymore, so it cannot export a method. Four traps,
  each measured: `loadScript` **does not run** the script; `run()` sets `setDelayedReply`
  and only ever replies on its error path, so send it with a short timeout and ignore that
  one; `loadScript` is overloaded `(s)`/`(ss)` and a name-keyed binding picks `(s)` and
  silently loses the plugin name (then `unloadScript` cannot find it — ask for `ss`
  explicitly); `Script::run()` early-returns while running, so re-triggering means
  load-once-per-query + `unloadScript`, not `run()` in a loop. `String(w.internalId)` in JS
  is the uuid with braces, same spelling as krunner's.
  Details from `/KWin getWindowInfo(uuid)` → a{sv}: caption, resourceClass/Name,
  desktopFile, role, icon, x/y/width/height as **doubles**, minimized/fullscreen/
  keepAbove/keepBelow/noBorder/skipTaskbar/skipPager/skipSwitcher,
  maximizeHorizontal/Vertical (**ints**), type, layer, desktops/activities (`as`), uuid —
  **no pid, no focus flag**. It answers for *any* window (dialogs and panels included, and
  an unknown handle gives an empty map, which is what makes it usable as a handle check).
* `activeOutputName()` → the focused output (`busctl call` with **no** input args).
  `supportInformation` lists **no windows** in Plasma 6.6.
* **A closed window is not a D-Bus error**: KWin returns a 0x0 / stride-0 image. Treat
  `width==0 || stride*height==0` as failure or the ring wedges; all failures publish a frame
  with a `KWC_ERR_*` status so `frame_seq` keeps moving.
* shm protocol **v2** (`KWC_HDR_STRUCT_SIZE` 1912, `KWC_VERSION` 2): per-frame `status`,
  `target`, `window[64]`. Asserted in C (`_Static_assert`) **and** Python (`ctypes.sizeof`);
  bump both, and bump `KWC_VERSION` when meaning changes. Pixel area starts at `hdr_size` 4096.
* Release/build essentials: the wheel contains a compiled helper so it must not be
  `py3-none-any` — override `bdist_wheel.get_tag()`; **the helper is a standalone executable,
  not an extension module, so the wheel is `py3-none-<platform>`** and one build covers every
  CPython ≥ 3.9; `auditwheel repair -w {dest_dir} {wheel}` (not `{dest}`),
  `--exclude libsystemd.so.0 --exclude libwayland-client.so.0`; PyPI rejects `linux_x86_64`
  (manylinux only); never import `kwcapture` from `setup.py` (numpy is not a build dep).

## SCALES — there are THREE; conflating them was a real bug (settled in v0.5.0)

* **`wl_output.scale`** — an integer hint (`1`, `2`). Useless for fractional scaling; never use it.
* **Display scale** — `Monitor.effective_scale`, and the `scale` field of a **whole-output** frame
  (measured 0.75 / 1.25 on a real 75 % + 125 % desk). `device px = logical × this`; whole-output
  frames are device px, 1:1, never resampled.
* **Scene / area factor** — `Monitor.area_scale` / `Capture.area_scale`, and the `scale` field of an
  **area** reply: one number for the whole desktop (1.25 on both outputs). It is also what XWayland
  surfaces are scaled by (a 320 px X11 window is 256 logical there) and what the workspace frame is
  rendered at (8108 px = 6486 logical × 1.25).
* **`area=` maps through the DISPLAY scale — measured, not guessed.** Take a high-detail device
  rectangle out of a native whole-output frame, then grab that region with the logical coordinates
  computed three ways (`/0.75`, `/1.25`, `/1.0`): MAD against the native crop
  **4.1 / 46.7 / 48.8**. So `_resolve_area()` divides by the **display** scale. Dividing by the scene
  factor was the v0.5.0 bug: it returned the pixel *count* you asked for but `pixel_scale /
  area_scale` (**0.6×**) of the region you named — a zoom, not a crop. The frame still comes back at
  the scene factor (`w × area_scale / pixel_scale` px); `geometry()` says what you got and
  `resize()` takes it back to device size.
* Consequence nobody guessed: **a region grab on a 75 % output is an upsample** — 250 image px for
  150 px of panel — while on an output sitting at the scene scale it is 1:1 native. No KWin option
  changes this (`native-resolution` on = scene factor, off = 1× logical; both measured).
* **`Window.geometry` is logical, frames are device** (measured with xterm: 320 X11 px → 256 logical
  → 192 device at scene 1.25 / display 0.75), so any assertion comparing a frame to `Window.width`
  must multiply by `Capture.pixel_scale`.
* Both mappings are only *distinguished* when the two factors differ. One output at 100 % runs these
  checks in a degenerate branch (see FLAKE-1), and the check count follows the hardware: **165** on
  a single output at 100 % (172 on the 75 % + 125 % desk, by arithmetic: the 13 checks added for
  non-normal windows are per-session, not per-output).

## MONITORS & RESILIENCE — facts the design rests on (from the v0.4.0 / v0.5.0 work)

* `Monitor.id` is the **`wl_output` global name** (65, 79 here) — ScreenShot2 has no per-output
  handle. `find_monitor()` resolves a number **id first, then index**; `index` is the
  top-left-first `list_monitors()` order; ambiguous names are refused rather than guessed.
* **`Capture()` with no `monitor=` follows KWin's *active screen*, which follows focus.** Never
  assert "geometry of the first output" — assert against `Capture.screen_name`, the invariant that
  actually holds. (The old test failed while an xterm had focus on the other screen and passed again
  minutes later with nothing changed.)
* **`kscreen-doctor` and KWin can disagree**: kscreen reported an output `disabled` while KWin
  advertised it on the registry *and* happily served 3840×2160 from it. `list_monitors()` is the
  truth about what is capturable — never kscreen's enabled flag.
* **`Capture(workspace=True)` is ScreenShot2 `CaptureWorkspace` = the bounding box of the scene**, not
  "the primary screen". Measured on the 2026-10-09 two-output desk (DP-1 2560×1440 @ 0,0 + HDMI-A-1
  3840×2160 @ 2560,0): geometry **6400×2160**; the band under the shorter output reads **exactly 0**
  (pure black, not garbage); and each output slices back out with the `position`/`geometry` that
  `list_monitors()` reports — `frame[y:y+h, x:x+w]` is shape-identical to a per-monitor capture,
  verified for both. Median cost on that desk: **76.5 ms** workspace vs 26.0 ms (1440p) and 50.5 ms
  (4K) for one output, and the ring it allocates is **442 MB** of tmpfs at the default 4 slots
  (221 MB at `slots=2`) — a workspace `Capture` is a RAM decision, not a free one. **Untested: whether
  it also spans KWin's virtual desktops**, since this desk runs a single one; "workspace" is verified
  here only as "union of the enabled outputs".
* `PIL.ImageGrab.grab()` returns the **whole X11 root** (both outputs, 6400×2160), not the primary
  output. A colour reference must compare against a `Capture(workspace=True)` frame: cropping a
  per-output frame onto it made the MAD nearly identical for correct and swapped channels, i.e. a
  check that silently tested nothing. Against the workspace frame it is exact (MAD 0.0, and 15.0 if
  the channels are swapped).
* **Fractional scale is measured, not read**: `--probe-scale NAME` grabs the same 128×128 logical
  area twice, with `native-resolution` on and off, and the ratio is the real scale
  (`mode_probe_scale`) — works whatever mechanism KDE uses internally.
* **The ring cannot be grown in place.** A client maps it at its length when the daemon starts, so
  `ftruncate`-ing it larger SIGBUSes anyone reading past the old end. Hence `ENOSPC` →
  `RingTooSmall` → the *client* restarts the helper and the ring is rebuilt, sized from its first
  frame (`--slot-floor WxH` sets the headroom). A daemon that re-execed itself would leave clients
  holding a stale mapping — which is why the client drives the restart.
* `auto_restart=True` (default) retries `DaemonDead` / `RingTooSmall` / a timeout with no daemon
  alive, bounded by `restart_limit=5` *consecutive* restarts (reset by a good frame;
  `auto_restarts` is cumulative). **Deliberately never recovered**: `WindowGone` (a new daemon cannot
  resurrect your window) and `TimeoutError` while the daemon is *alive* (that is KWin being slow or
  wedged; respawning would mask it). Both asserted in `resilience_section()`.
* Test-harness rules that came out of this work, all of them paid for:
  `tests/test_ring_reader.py` builds a `Capture` via `__new__` (no `__init__`), so **every**
  attribute the frame path touches needs a class-level default on `Capture`; `wmctrl` sees only
  **XWayland** windows and wants the X11 id, not kwcapture's QUuid handle; `Window.geometry`
  includes decoration/shadow margins (match by `app_id`, and give frame-size assertions ~60/90 px of
  slack); set a window's size **before** creating the `Capture`, because the ring is sized from the
  first frame (inheriting a large window turned a "grow" test into shrinks that passed for the wrong
  reason); the shell rewrites `xterm`'s title, so find a test xterm by pid, not by title; and
  `setsid` with redirected stdio for anything GUI started from a tool call, or the tool kills it.

## Gotchas (each cost real time — respect them)
* **A fix with no test is a guess.** BUG-3's first "fixed" note was disproved by the fd-counting
  regression test written for it — 16 → 20 fds over 4 `restart()` calls, i.e. one fd leaked per
  restart in the path just "fixed". Mark anything unverified until a test fails without it.
* **Never test a built wheel from the repo root**: `./kwcapture` shadows site-packages and you end up
  exercising the source tree (in CI that produced a bogus "helper not found"). `cd /tmp`, and assert
  `'site-packages' in kwcapture.__file__`.
* **D-Bus fd passing**: `busctl`/`dbus-send` can't pass fds. Works with sd-bus
  (`sd_bus_message_append(m,"h",fd)`), `dbus-fast` (`Message(..., unix_fds=[fd])`), or Gio
  (`call_with_unix_fd_list`, **async-only**, arg order
  `bus_name, path, iface, method, params, reply_type, flags, timeout, fd_list, cancellable,
  callback`; `a{sv}` values must each be a `GLib.Variant`).
* sd-bus: pkg-config name is **libsystemd**, include `<systemd/sd-bus.h>`, and the public
  header has **no `_cleanup_`** macro — call `sd_bus_error_free()` manually.
* `__atomic_store_n()` does **not** accept `double`; plain-assign it and rely on the release
  store of the sequence counter to order it.
* **shm request flag needs a wake-up**: the first `serve` implementation polled with a
  250 ms timeout, so on-demand grabs took 273 ms. Fix = a FIFO `<shm>.req` opened O_RDWR by
  the daemon (never EOF, never blocks) and O_WRONLY|O_NONBLOCK by the client; write 1 byte
  per request.
* **sd-bus: you cannot leave a struct early.** `sd_bus_message_exit_container()` on a
  partially read `(sssida{sv})` entry fails, which silently ends the loop after one
  element. Read every field (`sd_bus_message_read(m, "sssid", …)`), then
  `sd_bus_message_skip(m, "a{sv}")` for the property dict (it can carry an icon pixmap),
  then exit. And when you read a signature off `busctl` output, count the letters:
  `(sssida{sv})` = s,s,s,i,d,a{sv} — there is no `u` in there.
* **A stale ring file SIGBUSes the client.** `serve` opens the shm with `O_TRUNC`, so if a
  client maps the previous daemon's file (same path, `restart()`, or two `Capture`s on one
  default path) the mapping goes past EOF the moment the new daemon truncates it. Fixes:
  `unique_shm_path()` per Capture instance, `_start_once()` unlinks the old shm+FIFO first,
  and the startup wait also requires `hdr.daemon_pid == proc.pid`.
* Pipes handed to KWin must be **O_NONBLOCK on our read end** in the daemon (else one
  in-flight drain stalls the whole loop and can deadlock at depth>1); handle EOF-before-size
  (set `hdr->error=EIO`, mark done) so the ring cannot wedge.
* Ring geometry: `KWC_HDR_STRUCT_SIZE` is asserted in **both** C (`_Static_assert`) and
  Python (`assert ctypes.sizeof(_Hdr)`). Bump both if you edit the struct (v1=1776,
  v2=1912: +`slot[].status`, +`target`, +`window[64]`), and bump `KWC_VERSION` when the
  *meaning* changes so a mismatched helper is refused instead of misread. Check C offsets
  against ctypes with `offsetof` vs `ctypes.<field>.offset` (v2: slot=248, window=184,
  slot.status=112).
* Keep the ring slot ≥ 5K frames (`5120*2880*4`) so a resolution change doesn't overflow;
  the file is sparse (226 MB apparent → 15 MB resident at 1440p).
* `np.frombuffer(mmap)` gives a read-only array; `setflags(write=copy)` in `_view()`.
  `mmap.close()` raises `BufferError` while ctypes/numpy hold views (caught in `close()`).
* Pillow: no `BGRA` mode — use `Image.frombuffer("RGBA", size, buf, "raw", "BGRA", 0, 1)`.
  `Image.fromarray(a, "BGRA")` does not work.
* **A name from the icon-naming spec is not a file that exists.** `Icon=accessories-screenshot`
  was in this project's desktop entry for six releases and resolves in **no** theme on the KDE
  desktop it targets — KDE ships `accessories-screenshot-tool`, HighContrast ships
  `applets-screenshooter`. And **the `;` fallback chain is not a thing**: GLib's
  `DesktopAppInfo.get_icon()` puts the entire value into one `GThemedIcon` name
  (`Icon=kwcapture;x` → `['kwcapture;x', …]`) and upstream KService does `m_strIcon =
  entryMap.take("Icon")`, so a chain resolves to *neither* name on *both* consumers, your own
  icon included. Resolve the name when you write the file (`_icons.pick_icon_name()`), do not
  emit a list and hope.
* **Icon themes do not agree on layout, so never glob one of them.** hicolor is `<size>/apps/`,
  Breeze is `apps/<size>/`; a `*/apps/NAME` glob concludes KDE's own screenshot icon is missing
  **on a KDE desktop**. Read the theme's own `index.theme` `Directories=` and grade the resolver
  against an oracle that does not share your assumption (`tests/test_icons.py` shells out to
  `find`), which is exactly how this was caught.
* **A `.desktop` entry is keyed per executable, so "installed" is per environment.** Three
  virtualenvs → three entries → three copies of every line in it, and `install-desktop` fixes one.
  Two of this desktop's three kept the dangling icon until `refresh_entries()` existed. It keeps
  each file's own `Exec=` — KWin's authorisation key is `sha1(resolved exe)[:10]`, and the entry
  filename is derived from it, so refreshing an entry must never rewrite that line.
* **`$XDG_DATA_HOME/icons` is shared with other people's installers** (Wine alone puts hundreds of
  icons there). Delete by hash, not by filename: `.../apps/kwcapture.png` is ours only when its
  sha256 equals what we ship, and a user install never writes to a system theme directory.
* **setuptools package-data globs do not cross `/`** — `icons/**` ships nothing at all, and the
  failure is silent: the wheel installs fine and there is simply nothing to install. One glob per
  theme directory (`icons/hicolor/*/apps/*`), then check the built artefact
  (`unzip -l dist/*.whl | grep icons`); CI now asserts 10 files in both wheel and sdist. Same
  family as `MANIFEST.in` listing docs **by name** above: packaging is a list, and a list that is
  missing an entry does not complain.
* **A build script has no authority to make a branding decision.** The icon set this package ships
  was built from the mark's **monogram** at small sizes, on the strength of a real measurement
  (`APTURE` is mush below ~64 px, and GitHub's circular crop clips a full-bleed lockup). The
  measurement was right; drawing the conclusion was not the script's to draw — the owner's chosen
  artwork is `logo/kwcapture-mark.svg`, and the only permitted transforms are resize and re-render.
  Reverted 2026-10-11: the mark now renders at all nine sizes, the monogram files are deleted, the
  legibility measurement stays in the docs as an accepted **consequence**, and two guards keep it
  from creeping back (`logo/icon/build.sh` compares every shipped PNG with a fresh render of the
  mark, `tests/test_icons.py` asserts the shipped scalable SVG *is* `kwcapture-mark.svg` byte for
  byte). Generalises: **when a measurement appears to contradict the owner's decision, document the
  measurement and ask — never route around the decision in a Makefile.** (`logo/AGENTS.md` gotcha 38.)
* `wl_output.geometry` width/height are **millimetres**; pixel size/refresh come from
  `wl_output.mode`. Connector name (`DP-1`) is the `wl_output.name` event → needs binding v4.
* `pkill -f kwcapture` from a shell command **matches that same shell command** and kills
  itself; use `pkill -f 'bin/kwcaptur[e] serv[e]'` or a unique `--shm` path to match.
* **The exec_shell tool's default timeout is 10 s and the hard maximum is 60 s** — passing
  `timeout: 120`/`180` still gets killed at 60 s (`exit due to timed out`), so `sleep 120`
  never works: sleep ≤50 s per call and poll. The full `tests/test_kwcapture.py` run is
  actually **~35 s** (the earlier "~3 min" estimate was stale); `... quick` and `... windows`
  (~30 s) still exist, or background it with `nohup … > /tmp/x.log 2>&1 &` and read the log.
* `PIL.ImageGrab` can leave a `spectacle` process holding your stdout pipe open (looks like
  a hang); `bench.py` reaps the ones it started.

## Community files — what is in `.github/` and why it is incomplete

`SECURITY.md` · `ISSUE_TEMPLATE/{bug_report,feature_request}.yml` + `config.yml` ·
`PULL_REQUEST_TEMPLATE.md` · `dependabot.yml` · `CODE_OF_CONDUCT.md` · `CONTRIBUTING.md`.
Written for this repo, not from stock templates; the useful content is the part a generator cannot
know.

* **Bug form** leads with the three things that decide most reports here — `kwcapture doctor` output,
  Plasma/KWin version, session type — and says up front that CI cannot test capture, so nobody treats
  a green pipeline as evidence. Blank issues stay enabled on purpose.
* **PR template** carries the two traps CI structurally cannot catch: **green CI ≠ capture works**
  (no DRM node on hosted runners) and **helper changed ⇒ the release wheel must be rebuilt**; plus the
  nunif API-compat list and the `private/` rule.
* **Dependabot covers `github-actions` only.** Versions rot there, not in the package: a stale
  cibuildwheel pin broke the v0.1.0 *and* v0.2.0 release runs when its dated manylinux image left
  quay.io. No `pip` section — `numpy` and the extras are deliberately unpinned, so bot PRs against
  open ranges are pure noise for one maintainer. An explicit `ignore` holds **cibuildwheel below 5**
  so a bot cannot step over a breaking major without a human reading `release.yml`'s comments.
* **Second cycle (2026-10-11): PR #3, squash-merged as `d495ddb`** — `upload-artifact` v6→v7 and
  `download-artifact` v7→v8, 2 lines in `release.yml`, CI green on the PR head and on `main`.
  Read before reverting it in a hurry: **the majors still differ (upload v7, download v8) and that is
  inherited, not introduced** — the file was already upload v6 / download v7, and the pairing that
  matters is the artifact backend both sit on, not the two majors matching. Our usage is also the
  boring kind that survives these bumps: **one artifact, named `dist`, uploaded with `path: dist/*`
  and downloaded by that same name** — none of the same-name multi-artifact merging or `pattern`
  globbing that made the v4→v5 jump break people. What CI did **not** prove: `ci.yml` never runs
  `release.yml`, so `release.yml` was rehearsed as PR #2 was — `workflow_dispatch` at `main` with
  `publish: false` (run **38132030536**): manylinux wheels built, smoke test passed,
  **`Run actions/upload-artifact@v7 → success`**, and the `publish` job **skipped** by its own `if:`
  (it needs `publish: true`), which is also why nothing went near PyPI. That leaves
  **`download-artifact@v8` still unexercised** — it exists only inside `publish`, so its first real
  run is the next `v*` tag (or a dispatch with `publish: true` once the PyPI trusted publisher is
  configured). If the
  `pypi` job then cannot find `dist/`, that is this bump — the release assets are already attached by
  that point, so the fix is to re-run the job (or pin those two lines back), not to panic mid-release.
* **First cycle (2026-10-09):** PR #2 grouped checkout v4→v7, setup-python v5→v7,
  upload-artifact v4→v6, download-artifact v4→v7, cibuildwheel untouched ✓. Squash-merged
  (`2ec83eb`), CI green — but **a PR runs `ci.yml`, which never touches the artefact actions**, so
  `release.yml` was rehearsed with `workflow_dispatch` at `publish: false` (run 37881396351): sdist +
  manylinux wheel built, ring-reader tests ran, `upload-artifact@v6` produced `dist`, smoke test said
  `wheel ok 0.6.0`, and the release-attach + publish steps were *skipped* as designed. **That
  dispatch is the way to verify release tooling without a release** — no `gh` needed:
  `curl -X POST -H "Authorization: Bearer $TOK" -d '{"ref":"main","inputs":{"publish":false}}'
  …/actions/workflows/release.yml/dispatches`. **Still untested by anything: `download-artifact@v7`**
  — it lives only in the `publish` job, which this process does not use (PyPI upload is local `twine`
  against the release assets). Dormant, not proven: if trusted publishing is ever turned on, verify
  it against TestPyPI first, never mid-release.
* **`CODE_OF_CONDUCT.md` = Contributor Covenant 2.1**, fetched from contributor-covenant.org rather
  than typed, assembled by a script that *asserted* the body is byte-identical apart from the one
  contact substitution — **do not hand-edit the covenant section, regenerate it**. Its preamble says
  the quiet parts out loud: one maintainer is contact **and** decision-maker, there is no committee,
  enforcement reaches this project's spaces only, nothing is retroactive, and **a report about the
  maintainer himself goes to GitHub Support**. "Acknowledge within 5 working days" deliberately
  matches `SECURITY.md` — change one, change the other. Added because distributors read this checklist
  as trust evidence (the nunif precedent), not for the badge; the objection that survived — a CoC
  needs a real contact — is answered by the maintainer's published email.
* **Deliberately absent:** Discussions, wiki, FUNDING, coverage/lint badges, `ACCESSIBILITY.md`.
  No coverage/lint badge because no such step exists, and the functional suite needs real hardware —
  a documented limitation, not a gap to paper over. No accessibility statement because there is no UI,
  docs site or interactive surface beyond Python and stdout: the only honest content would be
  "captured content inherits the source app's accessibility", which is a sentence, not a policy.
* **Validating issue forms:** `yaml.safe_load` is not enough — every body item needs
  `type` ∈ {markdown, textarea, input, dropdown, checkboxes}, markdown items `attributes.value` and
  the rest `attributes.label`, dropdowns ≥ 2 options, and `validations.required` never on checkboxes.


## README badges — chosen deliberately (do **not** add a download badge)

Top row: PyPI version, PyPI status (`beta`), license (`MIT`), CI `build`, and two **static**
shields.io badges — `KDE Plasma: 6.x tested` and `Wayland: ScreenShot2`. Static ones carry no
upstream data that can go stale, and the Plasma badge says *tested*, not *required*: Plasma 5
has never been tried here, so a version **requirement** would be a claim this tree cannot back
up. Deliberately absent: **downloads** (`pypi/dm`), stars/forks (vanity), coverage and lint
(there is no coverage or lint step — a badge for a thing that does not run is worse than no
badge), and a per-job CI badge for `headless KWin capture` (it passes *tolerantly* on runners
with no DRM node, so a green badge there overstates what was proven — the **How this is tested**
section carries that nuance instead).
**Measured, not assumed** (2026-10-09, three identical calls to `pypistats`): kwcapture
reported `last_day 8 / last_week 398 / last_month 0` — the monthly rollup is broken upstream, so
the standard download badge renders **red "0/month"** on a package that is being installed and
ships as nunif's optional KDE backend. Check before believing any badge:
`curl -s https://img.shields.io/pypi/dm/kwcapture.json` (and the same `.json` trick works for
every candidate badge — it returns the message shields would render).

## Release checklist (do this in order; v0.2.0 was published this way)

1. Bump the version in **both** `pyproject.toml` and `kwcapture/__init__.py`, update
   `CHANGELOG.md` + `README.md` (including the release-wheel URL at the top of README).
2. `make && .venv/bin/python -X dev tests/test_kwcapture.py` — everything must pass on the
   real desktop (CI checks that it *builds and imports*, plus the two suites that need no
   compositor). Check the count of `[PASS]` lines against the number claimed in CHANGELOG.md,
   and run `.venv/bin/python -X dev tests/test_ring_reader.py` (the BUG-4 guardrail) **and**
   `make test-icons` (the brand-icon / desktop-entry / package-data guardrail, 98 checks) too.
3. `git commit` the lot, then `git tag vX.Y.Z && git push origin main --follow-tags`.
4. Build the artefacts here: `.venv/bin/python -m build` → `dist/*.tar.gz` +
   `dist/*-py3-none-linux_x86_64.whl`. Sanity check the wheel in a throwaway venv **from
   outside the checkout** (`/tmp`), including a real `Capture()` + `list_windows()`, and check
   the artwork really rode along: `unzip -l dist/*.whl | grep -c kwcapture/icons/` must be 10
   (8 png + 1 svg + `COPYING.md`), and `kwcapture install-desktop` from that venv into a scratch
   `XDG_DATA_HOME` must report 9 files. Both are asserted in CI too — package data fails
   silently, and a wheel without it is a package whose icons quietly never install.
5. PyPI — publish **the sdist + the CI manylinux wheel**, not the sdist alone: the manylinux
   wheel is what makes `pip install kwcapture` need no compiler. Take both **from the GitHub
   release of that tag** (so PyPI serves bytes identical to GitHub) rather than the local
   build, `twine check` them, then
   `.venv/bin/python -m twine upload -r pypi /tmp/publish/*` (token: `~/.pypirc`).
   Do **not** upload the local `linux_x86_64` wheel — PyPI rejects it.
   Before uploading, confirm the sdist carries no local-only files:
   `find <unpacked> -iname '*private*' -o -iname '*.jsonl'` and grep the tree for
   `ghp_`/`pypi-AgEIcHlwaS`. Verify with `curl -s
   https://pypi.org/pypi/kwcapture/<X.Y.Z>/json` (**not** the aggregate endpoint — it is
   Fastly-cached and lags ~1-2 min after a successful upload) and finally with a real
   `pip install --no-cache-dir kwcapture` in a throwaway venv **outside the checkout**.
6. The tag push runs `release.yml`, which builds the sdist + manylinux wheels and creates
   the GitHub release (via `gh` on the runner, `github.token`). Then upload the local
   `linux_x86_64` wheel as an extra release asset with the REST API:
   `curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/octet-stream" \
    --data-binary @dist/<wheel> https://uploads.github.com/repos/tjandrasg/kwcapture/releases/<id>/assets?name=<wheel>`
   (token from `~/.git-credentials`, release id from `/repos/.../releases/tags/vX.Y.Z`).
7. Add the release notes to the GitHub release body (`PATCH …/releases/<id>`) — CI only
   writes the `**Full Changelog**` stub, so a release with an empty body is a missed step,
   not a finished one. Then update this AGENTS.md with a `FRESH STATUS` section recording
   what shipped and what was verified, and commit + push that too.

## Ideas not done yet

**Open:**
* **Run the strict headless job somewhere with a render node** — a self-hosted KDE runner or a
  GPU-labelled runner; with a render node present `probe/ci_headless_kwin.sh` switches back to
  strict and tolerates nothing. Still open and now cheap, because the harness exists.
* **Test BUG-1 (minimised → stale frame) inside the nested session** — minimise the KCalc from the
  probe and assert what comes back; nothing else in the repo can reach that state on demand.
* **Test `scale=` handling** — `kwin_wayland --scale` exists, so `KWCAPTURE_NESTED_SIZE` plus a scale
  knob in `probe/nested_kwin_test.sh` would re-verify the fractional-scaling conclusions on a
  compositor whose scale is *known* instead of whatever the desk happens to be set to.
* `getWindowInfo` gives no pid — a `Window.pid` would need `/proc` matching by app id.
* Fractional scaling: `native-resolution` is set; behaviour with a scaled *window* (not output) is
  untested.
* **Non-KDE compositors stay out of scope, deliberately** — the `kw` in the name is the promise.
  `probe/globals.c` dumps what any compositor advertises if the question ever needs re-answering;
  the honest failure mode is a clear "cannot reach the compositor" error, never black frames.
  **Answered 2026-10-09, do not re-investigate:** kwin 6.6.6 implements neither protocol — 66 globals
  in the live registry with no `ext-image-copy-capture-v1`/`wlr-screencopy-unstable-v1`, and 0 string
  hits across 104 `kwin*`/`kwayland*` `.so` files (control `ScreenShot2` = 5). It is "never
  implemented", not refused: KWin does ship other wlroots-origin protocols (`zwlr_data_control_*`,
  `ext_idle_notifier_v1`, `ext_data_control_*`). Consequence: a portable protocol is additive, never a
  replacement for ScreenShot2. **Method note — my first attempt was wrong:** `strings` on
  `/usr/bin/kwin_wayland` alone reports 0 for `ScreenShot2` too, because the capture code is a plugin;
  always run the control before believing a negative.

**Done — recorded in `CHANGELOG.md`, not re-explained here:** window `active` flag (v0.3.0) ·
non-normal windows (v0.6.0) · following a resized window (`Capture.resized`, `last_geometry`) ·
auto-restart on `DaemonDead` with `restart_limit` · multi-monitor (`list_monitors()`,
`Capture(monitor=…)`, monitor-relative `area=`) · fractional scaling (`effective_scale`,
`measure_output_scale()`, `area_in="physical"`).
One design fact worth keeping from the ring-resize work: the ring is **never grown in place** — a
client has it mapped at the old length, so growing it under a reader would SIGBUS whoever read past
the old end. Instead `ENOSPC` → `RingTooSmall` → the daemon restarts and the ring is *rebuilt* at
the new size: same outcome for the caller, no window where a mapping and a file disagree.
