# Benchmark results

Run on: KDE Plasma **6.6** (kwin 6.6.6) on Wayland, single output `DP-1` **2560x1440 @
164.69 Hz**, scale 1, Intel i9-13900K, Ubuntu. Reproduce with `.venv/bin/python bench.py 3`
(3 s per method). Full-resolution output unless stated otherwise.

```
method                        fps      median latency
mss (XWayland)              1113.8      0.9 ms   <-- BLACK, useless on Wayland
PIL.ImageGrab (spectacle)      2.7    357.1 ms
kwcapture raw BGRA view       38.4     25.8 ms   real pixels, zero copy
kwcapture RGB full res        37.9     26.0 ms
kwcapture RGB 1280 wide       38.0     26.1 ms
kwcapture RGB 1024 wide       35.3     28.0 ms
kwcapture JPEG 1280           35.6     28.0 ms   grab + downscale + JPEG encode
kwcapture latest()          551704.      0.0 ms   view of an already-published frame
```

## Original experiment (kept for context)
* `PIL.ImageGrab` — uses `spectacle` under the hood, **~2 fps**: slow because it starts a
  KDE app, takes a PNG and decodes it.
* `mss` — >150 fps but reads **XWayland** (image is black on a Wayland session), and it
  throws if `$DISPLAY` is unset.

## Where the time goes (kwcapture, 2560x1440)
| stage | cost |
|---|---|
| KWin grab (D-Bus call → reply) | 18–25 ms; ~11 ms is a fixed floor (a 320x180 area still takes 11 ms) |
| drain 14 MB over the pipe | 4–7 ms (~3 GB/s) |
| BGRA → RGB contiguous | 8 ms numpy, ~3 ms `cv2.cvtColor` |
| downscale to 1280 wide | 0.1 ms cv2 INTER_AREA / 17 ms Pillow |
| encode JPEG | 3.5 ms @1280, 4.5 ms @2560 (cv2); PNG 23 ms |

Throughput ceiling ≈ **47 fps** (KWin serialises screenshot jobs). Pipeline depth:
`depth=1` 39.5 fps, `depth=2` 47.5 fps, `depth=3/4` 46.7 fps with per-frame grab latency
rising to 59/81 ms → **depth 2 is the sweet spot** (default).

## Verification
* Pixels are real and correctly ordered: `tests.py` compares a full-resolution `shot()`
  against an independent Spectacle capture — mean absolute difference **0.0**
  (it would be 9.7 if R and B were swapped).
* `tests.py`: 27/27 PASS (geometry, non-black frames, opaque alpha, read-only views,
  region capture, workspace capture, two concurrent instances, daemon kill → detected →
  `restart()`, idle-exit, JPEG/PNG validity, >15 fps sanity).
