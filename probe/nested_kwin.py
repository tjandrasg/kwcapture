"""Does kwcapture work against a KWin nobody is looking at?

Runs against the nested/headless KWin started by `nested_kwin_test.sh` (a `kwin_wayland
--virtual` instance on its own private D-Bus session) and asserts that it really composited
something: the geometry must match the *nested* output, not whatever the machine's desktop
resolution is, and neither the screen frame nor the window frame may be black.

    dbus-run-session -- bash probe/nested_kwin_test.sh      # do that one, it starts everything

Expected output on a nested session with one KCalc inside:

    monitors: [('Virtual-0', (1024, 640))]
    windows: 1 [('KCalc', (640, 508))]
    screen grab: (640, 1024, 4) mean B/G/R = [22.0, 20.4, 19.0] max = 255
    window grab: (480, 640, 4) 5.7 ms mean B/G/R = [43.4, 40.1, 37.3] max = 255

Why the D-Bus session matters (the finding this probe exists for): the screenshot interface
`org.kde.KWin.ScreenShot2` is D-Bus, so a nested KWin only answers when it *owns*
`org.kde.KWin` -- started against the desktop session's bus instead, this probe prints the
nested `Virtual-0` monitor but lists the *desktop's* windows and returns a frame at the
*desktop's* resolution (verified 2026-10-08). That split is the reason the runner uses
`dbus-run-session`, and the reason the size asserts above exist at all: a black-or-wrong size
tells the two apart: an all-black frame of the right size means the nested session is simply
empty (no client running in it), a frame at the *other* size means it came from the other
KWin. Both were observed on 2026-10-08.
"""
import os
import sys
import time

import kwcapture as K

# The nested output size the shell script asks KWin for; overridable so the assert tracks it.
W, H = (int(x) for x in os.environ.get("KWCAPTURE_NESTED_SIZE", "1024x640").lower().split("x"))


def main() -> int:
    failures = []
    print("WAYLAND_DISPLAY =", os.environ.get("WAYLAND_DISPLAY"))
    print("DBUS_SESSION_BUS_ADDRESS =", os.environ.get("DBUS_SESSION_BUS_ADDRESS"))

    monitors = K.list_monitors()
    print("monitors:", [(m.name, m.geometry) for m in monitors])
    if not monitors:
        failures.append("no monitors: the nested KWin did not answer")
    elif monitors[0].width != W or monitors[0].height != H:
        failures.append(f"expected the nested {W}x{H} output, got {monitors[0].name} "
                        f"{monitors[0].width}x{monitors[0].height}")

    windows = K.list_windows()
    print("windows:", len(windows), [(w.name, w.geometry) for w in windows[:4]])

    with K.Capture(shm=K.unique_shm_path("nested")) as cap:
        frame = cap.grab(copy=True, timeout=20)
        mean = [round(float(frame[..., i].mean()), 1) for i in range(3)]
        print("screen grab:", frame.shape, "mean B/G/R =", mean, "max =", int(frame.max()))
        if frame.shape[:2] != (H, W):
            failures.append(f"screen frame is {frame.shape[1]}x{frame.shape[0]}, "
                            f"expected {W}x{H} -> the capture came from another compositor")
        if frame.max() <= 16:
            failures.append("screen frame is black (empty nested session? start a client in it)")

    if windows:
        with K.Capture(window=windows[0].id, shm=K.unique_shm_path("nestedw")) as win_cap:
            tick = time.perf_counter()
            wf = win_cap.grab(copy=True, timeout=20)
            ms = (time.perf_counter() - tick) * 1000
            print("window grab:", wf.shape, f"{ms:.1f} ms",
                  "mean B/G/R =", [round(float(wf[..., i].mean()), 1) for i in range(3)],
                  "max =", int(wf.max()))
            if wf.max() <= 16:
                failures.append(f"window frame for {windows[0].name!r} is black")
    else:
        print("NOTE: no window in the nested session, only the screen path was checked")

    for f in failures:
        print("FAIL:", f, file=sys.stderr)
    print("OK: nested KWin composites and kwcapture captured it" if not failures else
          "FAILED: see above", file=sys.stderr if failures else sys.stdout)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
