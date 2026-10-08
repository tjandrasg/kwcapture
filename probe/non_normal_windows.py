#!/usr/bin/env python3
"""PROBE: find and capture the windows KWin's own list hides.

The bug this was written against: Winamp's big skinned window is
``_NET_WM_WINDOW_TYPE_DIALOG``.  KWin's krunner interface filters on
``Window::isNormalWindow()``, so ``list_windows()`` only ever reported the tiny
``NORMAL`` winamp window -- while ``CaptureWindow(handle)`` would have captured the
dialog happily.  Same for the panel (dock), the desktop, tool windows, splash
screens and override-redirect popups.

This probe walks the whole list, splits it by ``krunner_listed``, captures every
window that KWin's own application-window list does not mention, and proves the
focus never moved.  Run it with the window you care about open and occluded:

    .venv/bin/python probe/non_normal_windows.py [substring]

It writes /tmp/kwcapture-special-<n>.png for each capture and exits non-zero if
any of it fails.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K  # noqa: E402


def _script_objects():
    """Number of /Scripting/Script<N> objects KWin exports (leak check)."""
    if not shutil_which("busctl"):
        return None
    r = subprocess.run(["busctl", "--user", "tree", "org.kde.KWin"],
                       capture_output=True, text=True)
    return r.stdout.count("/Scripting/Script")


def shutil_which(name):
    import shutil
    return shutil.which(name)


def main(needle=None):
    scripts_before = _script_objects()
    files_before = set(f for f in os.listdir(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
                       if f.startswith("kwcapture-winlist-"))

    full = K.list_windows(require_full=True)          # raises if the script route failed
    normal = K.list_windows(all_types=False)
    print(f"{len(full)} window(s) via KWin scripting, {len(normal)} via krunner "
          f"(/WindowsRunner); the difference is what KWin filters out\n")

    hidden = [w for w in full if not w.krunner_listed]
    for w in full:
        mark = "  " if w.krunner_listed else "**"
        print(f"  {mark} {w.window_type_name:<10} {w.id} "
              f"{w.width}x{w.height}+{w.x}+{w.y}  {(w.name or w.app_id or '?')[:44]!r}")
    print("\n  ** = only reachable through the scripting enumeration")

    if needle:
        low = needle.lower()
        hidden = [w for w in hidden
                  if low in (w.name or "").lower() or low in (w.app_id or "").lower()
                  or low in w.window_type_name]
        if not hidden:
            print(f"nothing matching {needle!r} among the hidden windows")
            return 1

    focus0 = K.active_window_id()
    bad = 0
    for i, w in enumerate(hidden):
        try:
            with K.Capture(window=w.id, shm=K.default_shm_path(f"nnw{i}")) as cap:
                frame = cap.grab()
                fw, fh = cap.geometry()
                png = cap.shot_png()
                path = f"/tmp/kwcapture-special-{i}.png"
                with open(path, "wb") as f:
                    f.write(png)
                mean, top = float(frame.mean()), int(frame[:, :, :3].max())
                ok = fw > 0 and fh > 0 and top > 8
                bad += 0 if ok else 1
                print(f"  {'ok  ' if ok else 'BAD '} {w.window_type_name:<10} "
                      f"{fw}x{fh} (kwin says {w.width}x{w.height}, x{cap.pixel_scale:g}) "
                      f"mean={mean:.1f} max={top} -> {path}  [{w.name or w.app_id}]")
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"  BAD  {w.window_type_name:<10} {w.id}  {type(e).__name__}: {e}")

    focus1 = K.active_window_id()
    if focus0 != focus1:
        bad += 1
        print(f"  BAD  focus moved: {focus0} -> {focus1}")
    else:
        print(f"  ok   focus never moved ({focus0})")

    files = set(f for f in os.listdir(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
                if f.startswith("kwcapture-winlist-")) - files_before
    scripts_after = _script_objects()
    print(f"  {'ok  ' if not files else 'BAD '} leftover enumeration scripts: "
          f"{sorted(files) or 'none'}")
    if scripts_before is not None:
        print(f"  {'ok  ' if scripts_after == scripts_before else 'BAD '} "
              f"scripts still loaded in KWin: {scripts_after} (was {scripts_before})")
        if scripts_after != scripts_before:
            bad += 1
    if files:
        bad += 1
    print("\n" + ("PROBE OK" if not bad else f"PROBE FAILED ({bad})"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
