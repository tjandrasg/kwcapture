# Changelog

## 0.1.0

First public release.

- `bin/kwcapture` native helper (sd-bus, single file C): one-shot, `--bench`, `--list`,
  and a `serve` daemon that keeps a D-Bus connection open and publishes frames into a
  shared-memory ring.
- Python API: `Capture` (`grab` / `shot` / `shot_jpeg` / `latest` / `stats` / `bench`),
  `list_screens()`, zero-copy BGRA views, optional OpenCV-accelerated downscale+encode.
- Automatic setup on first use: compiles the helper if the wheel did not ship one, and
  writes the `~/.local/share/applications` desktop entry KWin requires to authorise
  `org.kde.KWin.ScreenShot2`.
- CLI: `kwcapture doctor|setup|install-desktop|screens|grab|demo|bench`.
- Tested against KDE Plasma 6.6 / kwin 6.6.6 on X86-64; ~40 fps at 2560x1440.
