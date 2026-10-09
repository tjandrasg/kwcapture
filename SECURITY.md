# Security policy

For the `kwcapture` Python package and its native helper. Short version: **it has no
privileges your desktop session does not already have, it contains no network code, and it
writes four kinds of file — all inside your own account.** The details, and the parts worth
arguing about, are below.

## Reporting a vulnerability

* **Privately, please.** Use the [Report a vulnerability](https://github.com/tjandrasg/kwcapture/security/advisories/new)
  form on the security tab (visible to you and the maintainer only), or email
  `tjandra.satria@sci.ui.ac.id` with "kwcapture" in the subject.
* **Please do not open a public issue** for anything you believe is exploitable. If you have
  already done so, edit it and add a comment saying so.
* **What to include:** `kwcapture --version`, how it was installed (PyPI wheel, source build,
  git), distro, KDE Plasma / KWin version, `echo $XDG_SESSION_TYPE`, the output of
  `kwcapture doctor`, and the shortest reproducer you can manage.
* **Response:** acknowledgement within 5 working days. For a confirmed issue we aim to ship a
  fix or a documented mitigation in the current release within 30 days, and to coordinate
  disclosure with you — public within 90 days at the outside, and with your name in the
  advisory if you want it.

**Supported versions:** the latest release only, actively. There is no LTS branch — this is one
person's project — but fixes get backported when the tree allows it. Please reproduce against
the newest release before reporting: several classes of problem (a leaked fd and mapping per
`restart()`, reads from a writable ring, a crash in the grab hot path) were fixed in 0.4.0 and
later.

## What kwcapture actually does

The whole native side is **one C file**, `kwcapture/native/kwcapture.c`, plus a small shared
header. It is not a Python extension module: it is a standalone executable that the Python
package starts as a per-`Capture` daemon.

* **No network code.** There is no `socket()`, `connect()`, `getaddrinfo()`, `bind()`, `AF_INET`
  or HTTP client anywhere in the helper; the only connection it opens is
  `wl_display_connect(NULL)` — the Wayland socket of your own session — plus, through libsystemd's
  `sd-bus`, your own **session** D-Bus. Frames go from KWin into a shared-memory ring and from
  there to your process. Nothing leaves the machine, and there is no telemetry, no update check
  and no crash reporting. Diagnostics go to stderr.
* **No privileges.** Not setuid, not setgid, no polkit prompt, no root, no systemd unit, no
  autostart entry, no D-Bus *system* bus, no portal. It runs as you, at your uid.
* **Three shared libraries, all from your own system:** `libc`, `libsystemd` (for sd-bus) and
  `libwayland-client`, linked dynamically, nothing vendored, no `RPATH`/`RUNPATH`. Check it
  yourself below.
* **Interfaces it talks to (the complete list):**

  | D-Bus name | object | used for |
  |---|---|---|
  | `org.kde.KWin.ScreenShot2` | `/org/kde/KWin/ScreenShot2` | the capture itself (screen / window / active window) |
  | `org.kde.KWin` | `/KWin` | `getWindowInfo` — details of one window by handle |
  | `org.kde.krunner1` | `/WindowsRunner` | KWin's own application-window list |
  | `org.kde.kwin.Scripting`, `org.kde.kwin.Script` | `/Scripting` | the full window list (since 0.6.0, see below) |
  | `org.kde.kwcapture.WinList` | `/org/kde/kwcapture` | **our own** service, exported on our own private connection, as the reply channel for the line above |

* **Fails closed.** On a compositor that is not KWin it exits with a clear "cannot reach the
  compositor" error rather than returning black frames or guessing.

### The four kinds of file it writes

| file | what for | how to remove |
|---|---|---|
| `~/.local/share/applications/io.github.kwcapture-<hash>.desktop` | KWin authorises callers of the restricted `ScreenShot2` interface by matching `/proc/<pid>/exe` against the `Exec=` of a desktop entry declaring `X-KDE-DBUS-Restricted-Interfaces` — this is how KDE's own Spectacle is allowed in. One entry per helper binary location, plain text, readable by you. | `kwcapture install-desktop --uninstall` removes them all; `kwcapture doctor --fix` deletes entries whose helper no longer exists. |
| `$XDG_RUNTIME_DIR/kwcapture-winlist-*.js` | the window-list script, see next section | created and deleted within one call; if a crash ever leaves one behind it is inert until KWin is told to load it |
| `$XDG_RUNTIME_DIR/kwcapture-<uid>…-<pid>-<n>.shm` + a request FIFO | the frame ring between helper and Python | removed on exit; both created `0600` on tmpfs. With `XDG_RUNTIME_DIR` unset it falls back to `/tmp` — the *path* is then guessable, though the file is still `0600`. |
| whatever **your** code writes | `shot()`, `shot_jpeg()`, saved PNGs | not kwcapture's doing, but see *Data* below |

### The window-list script route (0.6.0) — the part to read closely

KWin's normal window-listing interface filters out anything that is not a "normal" window, so
dialogs, panels, the desktop and popups can be captured but not found. To list them, the helper
generates a small JavaScript file, asks KWin to load it, and asks it to post the list back:

* the script is written `0600` with `O_CREAT | O_EXCL` into `$XDG_RUNTIME_DIR` (a `0700`
  directory only your user can write), with a random name;
* it answers on **the helper's own unique bus name**, addressed with a random nonce generated
  from `/dev/urandom`, so another client on the session bus cannot forge the reply it waits for;
* the wait is bounded (1.5 s), the script is then **unloaded and unlinked**, and a failure here
  is a stderr note and the ordinary filtered list — never a crash and never a silent wrong answer;
* **nothing is installed**: not under `~/.local/share/kwin/scripts`, nothing persists between
  calls, no KWin configuration is touched (a KWin script's own config group is read-only to JS);
* `--normal-only` (CLI) or `list_windows(all_types=False)` (API) skips this route entirely. If
  "no third-party script is ever loaded into my KWin" is a policy line for you, that flag is
  the whole answer, and the rest of the package works without it.

### Data

A frame is whatever KWin rendered: a screen or region grab contains every window visible there —
passwords, chat, tokens included. A **per-window** grab returns that window's own buffer, which
includes content currently hidden behind other windows; that is the feature, and it is also a
reason to be deliberate about which window you hand to `Capture`.

kwcapture never transmits or persists a frame on its own initiative. But the documented use case
is feeding frames to a vision model, so the security boundary is **your** code: what you do with
the bytes from `shot()` / `shot_jpeg()` is yours, and images you save inherit your umask.

## Trust model, stated plainly

The desktop-entry mechanism is **not** an access-control boundary that kwcapture is sneaking past:
any binary running as your uid inside your session bus can write itself an entry and call the
same interface, which is why KWin treats `ScreenShot2` as restricted-per-binary rather than
restricted-per-app. So kwcapture gains nothing your session did not already have, and correspond-
ingly: a process that already runs as your uid can read your ring files and take its own
screenshots. That is your login session being compromised, not a kwcapture vulnerability.

What we *do* want reported: anything where pixels cross to **another** user or another session;
a way for a different session client to read your ring, FIFO or the reply of the script route;
path or symlink trouble in how `$XDG_RUNTIME_DIR` / `/tmp` paths are created, followed or cleaned
up; a way for our code to authorise a binary other than the shipped helper; any crash reachable
from a malformed ring, a hostile compositor reply, or an unusually shaped window geometry; and
anything where kwcapture reports success while handing back stale or wrong pixels (that family —
`stale_frame`, `RingTooSmall`, frame-descriptor validation — is treated as a correctness bug and
fixed, and it is the closest thing this project has to a memory-safety surface).

## Out of scope

* Non-KDE compositors and non-Wayland sessions (`wlr-screencopy`, `ext-image-copy-capture-v1`,
  portals, X11/XWayland capture) — out of scope by design, see the README's scope note.
* Bugs in KWin, sd-bus, glibc or Wayland themselves → report to KDE
  ([security.kde.org](https://security.kde.org/)). Known example that will never be "fixed" here:
  a **minimised window returns a stale frame**, because KWin stops rendering it; 0.4.0 added
  `stale_check` / `stale_frame` / `window_minimized` so it is at least visible.
* Vulnerabilities in dependencies — numpy, opencv-python-headless, pillow — go to those projects.
* Attacks that require already running code as your uid, or physical access to an unlocked
  session (where Spectacle is always one keystroke away).

## Verify it yourself

The strongest answer to "why should I trust this binary" is that you do not have to: the sdist
carries the C source and `setup.py` builds it with `cc` + pkg-config, so a build from source
involves no prebuilt blob at all.

```bash
# fetch exactly what PyPI serves as source, and look at the whole file list:
# the .py files, kwcapture.c and one header — nothing compiled, no blob to trust.
pip download kwcapture --no-binary :all: -d /tmp/kc && tar xf /tmp/kc/kwcapture-*.tar.gz -C /tmp/kc
SRC=/tmp/kc/kwcapture-*/kwcapture
find $SRC -type f | sort

# no network code (expect only error-message strings, no calls)
grep -nE '\b(socket|connect|getaddrinfo|bind|send|recv|inet_|AF_INET[6]?|curl|http)\b' $SRC/native/kwcapture.c

# exactly three direct library dependencies and no RPATH — checked on the helper you ran
HELPER=$(python -c 'from kwcapture._native import find_binary; print(find_binary())')
readelf -d "$HELPER" | grep -E 'NEEDED|RUNPATH|RPATH'

# what authorisation was granted, and where the frames live
cat ~/.local/share/applications/io.github.kwcapture-*.desktop
ls -ld "$XDG_RUNTIME_DIR"                 # drwx------ — only you
grep -n '0600' $SRC/native/kwcapture.c    # ring, FIFO and window-list script are all 0600
```

Use `readelf -d`, **not** `ldd`, for the dependency list: `ldd` also resolves whatever your desktop
session put in `LD_PRELOAD` and will show libraries this binary does not actually need.
