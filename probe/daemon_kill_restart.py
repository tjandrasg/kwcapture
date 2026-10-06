"""SIGKILL the daemon under a live Capture, then restart() and grab again.

Recovered from the previous session's /tmp/repro.py -- /tmp often does not survive, so it
lives here now. Run it under -X dev:

    .venv/bin/python -X dev probe/daemon_kill_restart.py

Expect no ResourceWarning and "done" as the last line. It is what exposed BUG-3
(the leaked <shm>.log handle on every restart) -- see OPEN BUGS in AGENTS.md.
"""

import os
import signal
import time
import sys

# running this file puts probe/ on sys.path, not the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kwcapture as K
cap = K.Capture()
print("started", cap.geometry(), flush=True)
pid = cap.stats()["pid"]
os.kill(pid, signal.SIGKILL)
deadline = time.time() + 5
while time.time() < deadline and cap.alive:
    time.sleep(0.05)
print("alive after kill:", cap.alive, flush=True)
try:
    cap.grab(timeout=1.0)
except K.CaptureError as e:
    print("CaptureError as expected", flush=True)
print("restarting...", flush=True)
cap.restart()
print("restart ok", cap.geometry(), flush=True)
print("grab:", cap.grab().shape, flush=True)
cap.close()
print("done", flush=True)
