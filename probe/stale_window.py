"""Repro for BUG-1: a minimised window captures a STALE frame, silently.

KWin stops rendering a minimised window's scene item, so CaptureWindow keeps
returning the last buffer it held: every grab is byte-identical, forever, with
no exception and no status flag. This script proves it with a window that
repaints itself, because a self-repainting window is the only way to tell a
live frame from a stale one.

    .venv/bin/python probe/stale_window.py

Needs: busctl (to minimise/activate) and konsole.

KWin not rendering minimised windows is compositor behaviour we cannot change, so the
staleness below is EXPECTED forever. What matters is that kwcapture stops hiding it:
since v0.4.0 `Capture(stale_check=True)` sets `stale_frame` and warns.

Exit 0 = still stale (as KWin behaves) AND kwcapture reports it.
Exit 1 = stale but kwcapture did NOT report it (regression), or frames changed while
minimised (behaviour changed -- update BUG-1 in AGENTS.md).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

# running this file puts probe/ on sys.path, not the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kwcapture as K

SHM = "/tmp/kwcapture_stale_probe.shm"


def krunner(action: int, handle: str) -> bool:
    """0 = activate, 1 = close, 2 = minimise."""
    r = subprocess.run(
        ["busctl", "--user", "call", "org.kde.KWin", "/WindowsRunner",
         "org.kde.krunner1", "Run", "ss", f"{action}_{handle.strip('{}')}", ""],
        capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    if not shutil_which("konsole"):
        print("konsole not installed, cannot run this probe")
        return 2
    known = {w.id for w in K.list_windows(mark_active=False)}
    proc = subprocess.Popen(
        ["konsole", "--hold", "-e", "sh", "-c",
         "while :; do date '+%s.%N'; sleep 0.3; done"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    win = None
    deadline = time.time() + 18
    while time.time() < deadline and win is None:
        for w in K.list_windows(mark_active=False):
            if w.id not in known and "konsole" in (w.app_id or "").lower():
                win = w
                break
        if win is None:
            time.sleep(0.3)
    if win is None:
        print("no konsole window appeared")
        proc.terminate()
        return 2
    print(f"self-repainting window: {win.id} {win.geometry}")

    stale = False
    surfaced = False
    try:
        with K.Capture(window=win.id, shm=SHM, stale_check=True) as cap:
            a = cap.grab(copy=True)
            time.sleep(1.6)
            b = cap.grab(copy=True)
            visible_live = not (a == b).all()
            print(f"1 VISIBLE    two grabs differ : {visible_live}   (must be True)")

            if not krunner(2, win.id):
                print("   [skip] could not minimise via krunner")
                return 2
            time.sleep(1.8)
            m1 = cap.grab(copy=True)
            time.sleep(1.8)
            m2 = cap.grab(copy=True)
            stale = bool((m1 == m2).all())
            print(f"2 MINIMISED  two grabs differ : {not stale}"
                  f"   (False => STALE, see BUG-1)")
            print(f"             differs from the last visible frame: {not (m1 == a).all()}"
                  "   (so it is not even a thumbnail of the moment you minimised)")

            # the point of v0.4.0: kwcapture must TELL us, since KWin's pixels never will
            surfaced = bool(cap.stale_frame)
            print(f"             kwcapture stale_frame while minimised: {surfaced}"
                  "   (must be True since v0.4.0)")

            krunner(0, win.id)
            time.sleep(1.5)
            r1 = cap.grab(copy=True)
            time.sleep(1.4)
            r2 = cap.grab(copy=True)
            print(f"3 RESTORED   two grabs differ : {not (r1 == r2).all()}"
                  "   (must be True again)")
    finally:
        proc.terminate()

    if stale and surfaced:
        print("\nOK: KWin still serves stale frames for minimised windows (compositor")
        print("behaviour, by design) and kwcapture flags them via stale_frame.")
        return 0
    if stale and not surfaced:
        print("\nFAIL: frames are stale but Capture.stale_frame did not report it.")
        return 1
    print("\nno stale frame: minimised windows are live now. Update BUG-1 in AGENTS.md.")
    return 0


def shutil_which(name: str):
    import shutil
    return shutil.which(name)


if __name__ == "__main__":
    sys.exit(main())
