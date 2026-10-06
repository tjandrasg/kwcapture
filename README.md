# kwcapture — fast screen capture on Wayland (KDE Plasma)

**`PIL.ImageGrab` runs at ~2 fps on Wayland** (it shells out to `spectacle`) and **`mss`
captures XWayland**, which is black for native Wayland windows. `kwcapture` talks to the
KWin compositor directly: **~40 fps at 2560×1440**, real pixels, ~26 ms from "give me a
frame" to a JPEG ready for a vision model.

```
method                        fps      median latency
mss (XWayland)              1113.8      0.9 ms   <-- BLACK, useless on Wayland
PIL.ImageGrab (spectacle)      2.7    357.1 ms
kwcapture raw BGRA view       38.4     25.8 ms   real pixels, zero copy
kwcapture RGB full res        37.9     26.0 ms
kwcapture JPEG 1280 wide      35.6     28.0 ms   includes downscale + encode
```

```python
import kwcapture as K

cap  = K.Capture()                      # starts the helper, first frame in ~50 ms
arr  = cap.grab()                       # (H, W, 4) BGRA view into shared memory
rgb  = cap.shot(width=1280)             # (720, 1280, 3) uint8, contiguous
blob = cap.shot_jpeg(1280, quality=85)  # bytes for a vision API
cap.stats()                             # {'grab_ms': 20.1, 'total_ms': 27.8, ...}
cap.close()
```

## Install

```bash
pip install kwcapture                     # PyPI
pip install "kwcapture[fast]"             # + OpenCV: ~8x faster resize/encode

# straight from GitHub (builds the helper for your machine):
pip install "kwcapture @ git+https://github.com/tjandrasg/kwcapture.git"

# or the prebuilt linux x86-64 wheel from the release page (no compiler needed):
pip install https://github.com/tjandrasg/kwcapture/releases/download/v0.1.0/kwcapture-0.1.0-py3-none-linux_x86_64.whl
```

Needs **KDE Plasma with KWin on Wayland** and a C compiler plus `libsystemd`/`wayland-client`
headers (the wheel builds a small native helper; on Debian/Ubuntu:
`sudo apt install build-essential libsystemd-dev libwayland-dev`). Only `numpy` is a
runtime dependency.

Then, in the graphical session:

```bash
kwcapture doctor          # checks session, helper, KWin authorisation, capture
```

The first `Capture()` writes the one file KWin needs to authorise us
(`~/.local/share/applications/io.github.kwcapture-<hash>.desktop`) — no manual setup step.
Extras: `pip install "kwcapture[fast]"` (OpenCV: ~8x faster resize/encode) or
`"kwcapture[pil]"` (Pillow).

## Why a native helper (the interesting bit)

KWin exports `org.kde.KWin.ScreenShot2` over D-Bus: you hand it a file descriptor and it
writes raw ARGB32-premultiplied (BGRA in memory) pixels into it. But it **authorises
callers by `/proc/<pid>/exe`**: that binary must match the `Exec=` of a `.desktop` file
declaring `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2` — the trick
Spectacle uses. A Python interpreter can never satisfy that, so:

```
kwcapture.py  ──poke──▶  helper (serve)  ──D-Bus──▶  kwin_wayland
      ◀──mmap ring────        ◀──pipe(fd)────────
```

The helper keeps one D-Bus connection open and publishes frames into a shared-memory ring,
so a grab is a byte to a FIFO, a spin on a sequence counter, and a zero-copy numpy view:
no process per frame, no serialisation, no PNG round trip. KWin sends the reply *before*
the pixels land, so EOF on the pipe — not the reply — is the frame boundary.

## CLI

```bash
kwcapture doctor [--fix] [--build]     # is everything OK? (--fix also authorises)
kwcapture setup                        # build the helper + authorise it
kwcapture install-desktop [--uninstall]# manage the KWin authorisation file
kwcapture screens                      # DP-1 2560x1440 @164.69Hz pos 0,0 scale 1
kwcapture grab -o shot.png --width 1280
kwcapture grab -o frame.bgra --raw     # pure BGRA bytes
kwcapture demo --frames 60 --save f.png
kwcapture bench --frames 200
```

## Python API

`Capture(...)` arguments:

| argument | meaning |
|---|---|
| `screen="DP-1"` | which output (default: active screen) |
| `area=(x, y, w, h)` | capture a region instead of a whole output |
| `workspace=True` | capture the entire virtual desktop |
| `cursor=True` | include the hardware cursor |
| `decoration=True` | include window decorations and shadows |
| `slots=4` | ring depth — how many frames until a returned view is overwritten |
| `depth=2` | requests in flight to KWin (2 is optimal; more adds latency, not fps) |
| `fps=30` | continuous capture mode; read with `latest()` for zero-latency access |
| `idle_exit=300` | helper quits when untouched for this many seconds |
| `binary=…`, `allow_build=…` | override / disable locating-or-building the helper |
| `install_desktop=False` | don't touch `~/.local/share/applications` |
| `verbose=True` | report build/authorisation steps |

Methods: `grab(rgb=False, copy=False, fresh=True)`, `latest()`, `shot(width=…, resample=…)`,
`shot_png()`, `shot_jpeg()`, `stats()`, `geometry()`, `screen_name`, `bench(frames)`,
`restart()`, `close()` (also a context manager). Module helpers: `list_screens()`,
`to_rgb()`, `resize()`, `png_bytes()`, `jpeg_bytes()`, `find_binary()`,
`install_desktop_file()`.

Notes:

* `grab()` returns a **read-only view** of the shared ring, overwritten after `slots`
  further frames — use `copy=True` (or `.copy()`) to keep a frame, or `shot()`/`to_rgb()`.
* `latest()` returns the newest published frame **without** asking KWin for one.
* `hide_caller_windows=True` by default: KWin hides the capturing process' own windows,
  so your overlay/terminal does not end up in the shot (`--no-hide-caller` to disable).
* Each `Capture` gets its own ring in `$XDG_RUNTIME_DIR`, so several can run at once
  (e.g. one per monitor). The helper also dies with its client (`PR_SET_PDEATHSIG`).

## Performance notes (2560×1440@165 Hz, Plasma 6.6, i9-13900K)

* ~11 ms is a fixed cost inside KWin (a 320×180 grab still takes 11 ms); 1440p adds ~7 ms
  of grab and ~5 ms to move 14 MB across the pipe.
* **~47 fps is the hard ceiling** — KWin serialises screenshot jobs. `depth=2` reaches it;
  `depth=3/4` only add latency (37/59/81 ms per frame).
* Post-processing: OpenCV `INTER_AREA` 2560→1280 ≈ 0.1 ms, `cvtColor` ≈3 ms, JPEG
  1280 ≈3.5 ms / 2560 ≈4.5 ms, PNG ≈23 ms (prefer JPEG), Pillow resize ≈17 ms.
* Without OpenCV *or* Pillow, downscaling falls back to numpy (box-average on integer
  factors, nearest otherwise) and image encoding raises a hint to install an extra.
* The ring file looks like 226 MB but is sparse: 15 MB resident at 1440p.

## Repo layout

```
kwcapture/
  __init__.py            Python API (Capture, grab/shot, shm ctypes mirror)
  __main__.py            CLI: doctor / setup / install-desktop / screens / grab / demo / bench
  _native.py             find or compile the helper ($KWCAPTURE_BIN, wheel, cache, source)
  _desktop.py            the KWin authorisation desktop entry
  native/kwcapture.c     the capture daemon (sd-bus + shm ring + wl_output listing)
  native/include/kwcapture_shm.h   shared-memory protocol (asserted on both sides)
tests/test_kwcapture.py  27 functional tests (also `pytest tests/`)
bench.py                 comparison against mss and PIL.ImageGrab
probe/                   the reverse-engineering experiments (Wayland global dumper, etc.)
AGENTS.md                investigation log — how the KWin API and its auth really work
```

Development:

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pillow opencv-python-headless
make setup          # build the helper into kwcapture/bin + authorise
make test bench     # tests, then the comparison table
make wheel          # dist/*.whl
```

## Troubleshooting

| symptom | cause / fix |
|---|---|
| `The process is not authorized to take a screenshot` | `kwcapture install-desktop`, then retry (KDE's service cache notices the new file asynchronously — `Capture` already retries for a few seconds) |
| `no frame within 2.0s` | helper died: `Capture.restart()`, or `Capture(daemon_stderr=sys.stderr)` to see its log; `kwcapture doctor` |
| `failed to compile the kwcapture helper` | install `build-essential libsystemd-dev libwayland-dev`, or build it yourself and set `KWCAPTURE_BIN` |
| `frame needs N bytes, slot has M` | resolution went above ~5K: restart the helper |
| works in a terminal but not from cron/SSH | you need `WAYLAND_DISPLAY` **and** `DBUS_SESSION_BUS_ADDRESS` of the graphical session |
| colours wrong somewhere | `grab()` is BGRA; `shot()`/`to_rgb()` are RGB |

Non-KDE compositors need `ext-image-copy-capture-v1` / `wlr-screencopy-unstable-v1`
instead (kwcapture does not implement those; `probe/globals.c` shows how to check what a
compositor advertises).

## License

MIT — see `LICENSE`. `AGENTS.md` documents the reverse engineering behind it.
