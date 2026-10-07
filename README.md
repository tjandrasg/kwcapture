# kwcapture — fast screen capture on Wayland (KDE Plasma)

**`PIL.ImageGrab` runs at ~2 fps on Wayland** (it shells out to `spectacle`) and **`mss`
captures XWayland**, which is black for native Wayland windows. `kwcapture` talks to the
KWin compositor directly: **~40 fps at 2560×1440**, real pixels, ~26 ms from "give me a
frame" to a JPEG ready for a vision model. Whole screen, a region, **one window by
name or id**, or **one monitor by name or id** — `list_windows()` and `list_monitors()`
give you both.

> **Scope: KDE Plasma only.** The `kw` in the name is the design. kwcapture speaks
> `org.kde.KWin.ScreenShot2` and nothing else; compositors that only offer
> `wlr-screencopy` / `ext-image-copy-capture-v1` are out of scope, and it will say so
> rather than half-work on them.

```
method                        fps      median latency
mss (XWayland)              1113.8      0.9 ms   <-- BLACK, useless on Wayland
PIL.ImageGrab (spectacle)      2.7    357.1 ms
kwcapture raw BGRA view       38.4     25.8 ms   real pixels, zero copy
kwcapture RGB full res        37.9     26.0 ms
kwcapture JPEG 1280 wide      35.6     28.0 ms   includes downscale + encode
kwcapture one 692x440 window 185.4      4.7 ms   per-window capture, not clipped
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

**Per-window capture** — the window handle is KWin's own id, so no geometry juggling and
no cropping by whatever is on top of it:

```python
for w in K.list_windows():                # name + handle of every capturable window
    print(w.id, w.name, w.app_id, w.geometry, w.active)   # active == has focus

win = K.Capture(window="Kate")            # by name, caption or app id …
kon = K.Capture(window="{e0b1aab4-4e10-…}")   # … or by the handle it came with
act = K.Capture(active_window=True)       # whatever has focus
win.grab()                                # 692x440 KCalc window: ~5 ms, ~185 fps
win.shot_jpeg(quality=90)                 # just that window

K.active_window()                         # the focused window, as a Window
K.active_window_id()                      # … or just its KWin handle (~8 ms)
```

**A minimised window returns stale pixels** — KWin stops rendering it, so every grab repeats
the same buffer and nothing tells you. Ask explicitly, or opt in to a per-grab check:

```python
win = K.Capture(window="Kate", stale_check=True)   # opt-in: one throttled query per grab
frame = win.grab()
if win.stale_frame:             # the window is minimised -> frame is an old snapshot
    ...
win.window_minimized            # ask KWin right now (a D-Bus round trip; not per frame)
```

`stale_check` is off by default because the check costs a round trip; without it
`stale_frame` stays `False`, which means *unknown* rather than *fresh*.

## Install

```bash
pip install kwcapture                     # PyPI
pip install "kwcapture[fast]"             # + OpenCV: ~8x faster resize/encode

# straight from GitHub (builds the helper for your machine):
pip install "kwcapture @ git+https://github.com/tjandrasg/kwcapture.git"

# or the prebuilt wheel straight from the release page:
pip install https://github.com/tjandrasg/kwcapture/releases/download/v0.5.0/kwcapture-0.5.0-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
```

Needs **KDE Plasma with KWin on Wayland**. The PyPI wheel ships the small native helper
prebuilt for x86-64 Linux (glibc ≥ 2.17), so **no compiler is required**; if your distro or
architecture has no wheel, pip compiles it on install, which needs a C compiler and
`libsystemd`/`wayland-client` headers (on Debian/Ubuntu:
`sudo apt install build-essential libsystemd-dev libwayland-dev`). Only `numpy` is a
runtime dependency; the helper links `libsystemd` and `libwayland-client`, which any KDE
desktop already has.

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
kwcapture windows                      # every capturable window: handle, name, app, size
kwcapture windows -f kcalc --json      # filter by name/app id; machine-readable
kwcapture grab -o shot.png --width 1280
kwcapture grab -o frame.bgra --raw     # pure BGRA bytes
kwcapture grab --window Kate -o kate.png
kwcapture grab --window '{e0b1aab4-4e10-…}' --decoration -o win.png
kwcapture grab --active-window -o focused.png   # the window that has focus
kwcapture demo --frames 60 --save f.png
kwcapture bench --frames 200
```

`kwcapture windows` looks like this:

```
WINDOW HANDLE (id)                      NAME                          APP_ID              SIZE    POSITION  FLAGS
{e0b1aab4-4e10-47fd-ae46-77a4ee6bc4d8}  build-pgo : llama-server      org.kde.konsole  2560x1394      +0,+0  maximized
{2c14f294-93ea-48bf-bbea-f501d59f6fe5}  KCalc                         org.kde.kcalc      692x468  +1563,+738
```

## Python API

`Capture(...)` arguments:

| argument | meaning |
|---|---|
| `screen="DP-1"` | which output (default: active screen) |
| `area=(x, y, w, h)` | capture a region instead of a whole output |
| `workspace=True` | capture the entire virtual desktop |
| `window="Kate"` | capture **one window**: a handle from `list_windows()`, or its caption / app id |
| `active_window=True` | capture the window that has focus |
| `cursor=True` | include the hardware cursor |
| `decoration=True` | include window decorations (and their shadow); off = client area only |
| `slots=4` | ring depth — how many frames until a returned view is overwritten |
| `depth=2` | requests in flight to KWin (2 is optimal; more adds latency, not fps) |
| `fps=30` | continuous capture mode; read with `latest()` for zero-latency access |
| `idle_exit=300` | helper quits when untouched for this many seconds |
| `binary=…`, `allow_build=…` | override / disable locating-or-building the helper |
| `install_desktop=False` | don't touch `~/.local/share/applications` |
| `verbose=True` | report build/authorisation steps |

Methods: `grab(rgb=False, copy=False, fresh=True)`, `latest()`, `shot(width=…, resample=…)`,
`shot_png()`, `shot_jpeg()`, `stats()`, `geometry()`, `screen_name`, `target`,
`window_id`/`window_name`, `bench(frames)`, `restart()`, `close()` (also a context
manager). Module helpers: `list_screens()`, `list_windows()`, `find_window()`,
`is_window_handle()`, `to_rgb()`, `resize()`, `png_bytes()`, `jpeg_bytes()`,
`default_shm_path()`, `unique_shm_path()`, `find_binary()`, `install_desktop_file()`.
`grab()` / `shot()` also take the target keys (`window=`, `screen=`, …) and keep one
helper process alive per distinct target.

Notes:

* `grab()` returns a **read-only view** of the shared ring, overwritten after `slots`
  further frames — use `copy=True` (or `.copy()`) to keep a frame, or `shot()`/`to_rgb()`.
  The ring is mapped read-only, so a view can never write into it, and a view stays
  readable after `close()` — frozen at the frame that was current when you closed.
* `latest()` returns the newest published frame **without** asking KWin for one.
* `hide_caller_windows=True` by default: KWin hides the capturing process' own windows,
  so your overlay/terminal does not end up in the shot (`--no-hide-caller` to disable).
* Each `Capture` gets its **own** ring file in `$XDG_RUNTIME_DIR` (see
  `unique_shm_path()`), so any number of them can run at once — one per monitor, one per
  window. The helper also dies with its client (`PR_SET_PDEATHSIG`).

## Per-window capture

```python
import kwcapture as K

for w in K.list_windows():                 # every window KWin considers capturable
    print(f"{w.id}  {w.name}  {w.app_id}  {w.width}x{w.height}+{w.x}+{w.y}")

win = K.Capture(window="Kate")             # caption, app id, desktop file or handle
try:
    frame = win.grab()                     # (H, W, 4) BGRA, same as a screen grab
except K.WindowGone:                       # someone closed the window
    win.close()
    win = K.Capture(window="Kate")         # a new window with the same name

focused = K.Capture(active_window=True)    # whatever has focus right now
```

`Window` fields: `id` (the KWin handle — pass it back as `window=`), `name`, `app_id`,
`resource_name`, `desktop_file`, `role`, `icon`, `x`, `y`, `width`, `height`, `minimized`,
`fullscreen`, `maximized`, `keep_above/keep_below`, `no_border`, `skip_taskbar/pager/switcher`,
`window_type`, `layer`, `desktops`, plus `geometry`/`position`/`visible`.

How the handles are found (and what they can and cannot do):

* KWin's `org.kde.KWin.ScreenShot2` **`CaptureWindow(handle)`** takes a window's internal
  id (a `QUuid`). There is no list method on that interface, so the helper asks KWin's
  krunner interface (`/WindowsRunner`, empty query → every window) for the ids and
  `org.kde.KWin` **`getWindowInfo(handle)`** for the details. Neither needs the
  desktop-file authorisation; only the pixel grab does.
* **Normal application windows only.** Panels/docks, the desktop/wallpaper and overlay
  windows are not in `list_windows()` (that is KWin's own filter). If you get hold of one
  of their handles anyway, `Capture(window=…)` captures it.
* `decoration=False` (default) grabs the client area; `decoration=True` grabs the window
  with its title bar and shadow — the shadow area is **transparent** (alpha 0), so
  composite it or drop the alpha channel before saving a JPEG.
* A window that is **covered by other windows is not clipped**: KWin renders that
  window's own buffer, so you get the whole client area, and nothing of the windows on
  top. A **minimised** window returns a frame, but it is a **stale snapshot**: KWin stops
  rendering windows that are minimised, so you get the last buffer it held — the same bytes
  every time. `Capture(stale_check=True)` makes `grab()` consult KWin (throttled) and set
  **`stale_frame`** so this cannot pass unnoticed, and warn once when a window goes stale;
  `Capture.window_minimized` asks on demand. Capture the window while it is mapped if you
  need its current contents.
* A handle is only valid while the window lives. If the window is closed, `grab()`/`latest()`
  raise **`WindowGone`** — the helper stays alive, the other captures are unaffected, and
  `list_windows()` no longer reports it.
* Names are resolved by ranking: exact caption > exact caption/app id (any case) > unique
  substring. Several equally-good matches raise **`AmbiguousWindow`** (with `.candidates`),
  none raises **`WindowNotFound`** (the message lists what *is* available).

| fps, 2560×1440 Plasma 6.6 | median |
|---|---|
| whole screen | 26 ms (≈40 fps) |
| 692×440 window | **4.7 ms (≈185 fps)** |

A window grab is cheap because the compositor only has to render and ship that window —
fine for watching a handful of windows in a loop.


## Monitors: list them, capture one by name or id

```bash
kwcapture monitors                    # index, id, name, make/model, size, scale, position
kwcapture monitors --json             # machine-readable
kwcapture monitors --measure-scale    # also probe the real scale (125% / 150% displays)
kwcapture grab --monitor HDMI-A-1 -o tv.png
kwcapture grab --monitor 0 -o left.png
```

```python
import kwcapture as K

for m in K.list_monitors():
    print(m.index, m.id, m.name, m.position, m.geometry, m.refresh_hz, m.scale)
# 0 65 DP-1     (0, 0)    (2560, 1440) 164.69 1
# 1 79 HDMI-A-1 (2560, 0) (3840, 2160)  60.0  1
```

Three ways to name the same screen — `list_monitors()` returns them as `Monitor` objects,
and `Capture(monitor=...)` takes any of them (or a `Monitor`):

| you pass | what it is |
|---|---|
| `"DP-1"` | the connector name — what KWin addresses screens by. Substrings work (`"hdmi"`) |
| `65` | the **compositor's own id** for the output (its `wl_output` global name) |
| `0` | the `list_monitors()` **index**, top-left monitor first |

```python
K.Capture(monitor="HDMI-A-1")     # by name
K.Capture(monitor=79)             # by compositor id
K.Capture(monitor=1)              # by index
K.Capture(monitor=K.find_monitor("lg tv"))    # by make/model, via the finder
```

An id is stable for the session and unique; a name is stable across sessions and readable;
an index shifts if you plug a monitor in on the left. `find_monitor()` raises
`MonitorNotFound` listing what exists, or `AmbiguousMonitor` (with `.candidates`) when a
substring matches several — it never picks one silently. Because the name is resolved
*eagerly*, a typo raises immediately instead of failing deep inside the compositor.

With `monitor=` set, **`area=` is relative to that monitor**, which is usually what you
want on a mixed-DPI desk:

```python
K.Capture(monitor="HDMI-A-1", area=(0, 0, 800, 600))   # top-left 800x600 of the TV
K.Capture(area=(0, 0, 800, 600))                       # unchanged: global scene coords
```

Only **enabled** outputs are listed — a connected-but-disabled monitor has no image to
capture (`kscreen-doctor -o` shows those and switches them on).

## Fractional scaling (75 %, 125 %, 150 %, ...)

A **whole-output** frame is always device resolution — every pixel the panel shows, never a
rescale. What scaling changes is that the numbers you see in the UI are no longer numbers
in the image, and there is more than one scale involved. On a desk measured live (DP-1 at
75 %, HDMI-A-1 at 125 %):

| what | where you see it | this desk |
| --- | --- | --- |
| integer hint | `Monitor.scale` (`wl_output`) | 1 and 2 — cannot express fractions |
| **display scale** | `Monitor.effective_scale`, `Capture.scale` of a whole-output frame | 0.75 and 1.25 |
| **scene factor** | `Monitor.area_scale`, `Capture.area_scale`, `Capture.scale` of a *region* frame | 1.25 on both |

`device pixels = logical pixels x display scale` — that is the relation that governs output
geometry, window geometry and whole-output frames. kwcapture **measures** it (grabbing one
small area in device pixels and once composited, and reading a whole-output frame), because
`wl_output` can only advertise an integer.

```python
m = K.list_monitors(measure_scale=True)[0]
m.scale             # 1     <- what wl_output advertises (integer hint)
m.effective_scale   # 0.75  <- what the display is actually running
m.area_scale        # 1.25  <- the scene-wide factor region captures come back at
m.fractional        # True
m.logical_geometry  # device size / display scale
m.to_physical(100, 60)    # logical -> device pixels
m.to_logical(150, 90)     # device pixels -> logical

cap = K.Capture(monitor=m)
cap.scale        # scale KWin applied to these frames (cheap, straight from the frame)
cap.pixel_scale  # this output's measured display scale (cached after the first probe)
```

**Region captures are the exception.** `area=` is in logical scene coordinates, and KWin
answers a region at the *scene* factor — one number for the whole desktop, not the scale of
the output the region is on. So `area=(0, 0, w, h)` hands you a `w*area_scale x h*area_scale`
image, and where `area_scale != pixel_scale` those pixels are a **resample** of the
`w*pixel_scale` device pixels the region really covers (on a 75 % output, a region grab is
an upsample; on an output at the scene scale it is 1:1). If that bothers you — and for
pixel-exact work it should — grab the monitor and slice the array instead, below.

`area_in="physical"` means *the rectangle is in device pixels of that output* (it needs
`monitor=`, since device pixels only mean something within one output). It is converted
through the display scale, so you get exactly the region you named — while the image itself
stays at the scene factor, i.e. `w * area_scale/pixel_scale` px wide:

```python
K.Capture(monitor="DP-1", area=(0, 0, 640, 360), area_in="physical")
```

For cropping, the simplest exact route is to grab the whole monitor and slice the numpy
array — no rounding, no coordinate maths:

```python
frame = K.Capture(monitor="DP-1").grab()
crop = frame[100:460, 640:1280]      # device pixels, exactly
```

For cropping, the simplest exact route is to grab the whole monitor and slice the numpy
array — no rounding, no coordinate maths:

```python
frame = K.Capture(monitor="DP-1").grab()
crop = frame[100:460, 640:1280]      # device pixels, exactly
```


## Resilience: resolution changes, window resizes and a dead daemon

Long-running captures outlive their setup. Unplugging a monitor, switching mode, or
maximising the window you are watching all change the frame size, and the helper is a
separate process that can be killed, crash, or quit after sitting idle. By default
`grab()` **heals all of these by itself** — you keep getting frames:

```python
import kwcapture as K

cap = K.Capture(window="Dolphin")     # auto_restart=True is the default

while True:
    frame = cap.grab()               # survives a restart, a mode change, a resize
    if cap.resized:                  # the frame we just got differs in size from the last
        print("now", cap.last_geometry)   # e.g. (2560, 1440) -> (1920, 1080)
```

* **Window resized / maximised** — frames simply come back at the new size; there is no
  need to re-create the `Capture`. `resized` is True on the frame where it changed, and
  `last_geometry` is the size of the frame you just got.
* **Monitor mode change** — same thing for a screen capture: `geometry()` always reports
  what the compositor is capturing *now*, and the ring is sized for it.
* **A frame bigger than the ring** (a bigger monitor, a window grown past the headroom)
  raises **`RingTooSmall`**. The ring cannot be grown in place — a client has it mapped at
  the old length — so the helper reports it and exits, and a new one is started with a ring
  sized for the new geometry. `grab()` does that for you; watch `auto_restarts` and
  `last_restart_reason` if you care that it happened.
* **Daemon killed, crashed, or reaped for being idle** — restarted transparently and the
  frame retaken. An outstanding zero-copy view from *before* the restart stays readable
  (frozen at its last frame) rather than turning into invalid memory.

Knobs, all on `Capture`:

| parameter | default | meaning |
|---|---|---|
| `auto_restart` | `True` | recover inside `grab()`; `False` restores the old "raise `DaemonDead`" behaviour |
| `restart_limit` | `5` | give up after this many *consecutive* restarts (resets on the next good frame) |
| `slot_floor` | `(5120, 2880)` | room left in each ring slot for a frame that grows later; raise it for 6K/8K displays |

What is deliberately **not** auto-recovered, because restarting would hide a real bug:

* **`WindowGone`** — the window you were capturing was closed. Restarting cannot bring your
  window back. (If the *app* is reopened under the same name, the `Capture` follows it to
  the new window handle.)
* **`TimeoutError` while the daemon is alive** — KWin is being slow or is wedged. Spawning
  another daemon would just hide that.

```python
cap = K.Capture(auto_restart=False)   # old behaviour: report it, do nothing about it
try:
    cap.grab()
except K.RingTooSmall:
    cap.restart()                     # re-open the ring at the current geometry
except K.DaemonDead:
    ...                               # you own the restart
```


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
  __init__.py            Python API (Capture, Window, grab/shot, shm ctypes mirror)
  __main__.py            CLI: doctor / setup / install-desktop / screens / windows /
                         grab / demo / bench
  _native.py             find or compile the helper ($KWCAPTURE_BIN, wheel, cache, source)
  _desktop.py            the KWin authorisation desktop entry
  native/kwcapture.c     the capture daemon (sd-bus + shm ring + output and window listing)
  native/include/kwcapture_shm.h   shared-memory protocol (asserted on both sides)
tests/test_kwcapture.py  159 functional checks (also `pytest tests/`)
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
| `no window matches 'x'` | `kwcapture windows` for the handles; the error lists what is there. Matching is exact caption/app id, or a unique substring |
| `AmbiguousWindow` | several windows share that name/caption — pass the handle from `kwcapture windows` |
| `WindowGone: the window has nothing to capture` | the window was closed (or is being unmapped). The helper is fine: `list_windows()` again and make a new `Capture` |
| `unsupported kwcapture ABI 1` | an old helper binary (`$KWCAPTURE_BIN`, or a stale `kwcapture/bin`): rebuild with `kwcapture setup` |
| `frame N reports an invalid geometry` / `outside the …-byte ring` | the client refused a frame descriptor that cannot fit the ring (old/mismatched helper, or a ring truncated under it). `Capture.restart()`; if it repeats, `kwcapture setup` to rebuild the helper |
| `the ring was replaced by restart()/close() while this frame was being read` | you grabbed from another thread while something called `restart()`; a single `Capture` is not thread-safe for lifecycle + reads |
| works in a terminal but not from cron/SSH | you need `WAYLAND_DISPLAY` **and** `DBUS_SESSION_BUS_ADDRESS` of the graphical session |
| colours wrong somewhere | `grab()` is BGRA; `shot()`/`to_rgb()` are RGB |

Non-KDE compositors need `ext-image-copy-capture-v1` / `wlr-screencopy-unstable-v1`
instead (kwcapture does not implement those; `probe/globals.c` shows how to check what a
compositor advertises).

## License

MIT — see `LICENSE`. `AGENTS.md` documents the reverse engineering behind it.
