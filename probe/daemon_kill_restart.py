import os, signal, time
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
