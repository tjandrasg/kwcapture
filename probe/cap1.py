"""Probe: call KWin ScreenShot2 CaptureScreen, try file-backed fd (no reader thread needed)."""
import os, sys, time, mmap
import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

SERVICE = "org.kde.KWin.ScreenShot2"
PATH = "/org/kde/KWin/ScreenShot2"
IFACE = "org.kde.KWin.ScreenShot2"

conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)

def capture_file(screen, path="/dev/shm/kwcap_test", opts=None):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    fdlist = Gio.UnixFDList()
    idx = fdlist.append(fd)
    opts = opts or {"native-resolution": GLib.Variant("b", True)}
    params = GLib.Variant("(sa{sv}h)", (screen, opts, idx))
    reply = conn.call_with_unix_fd_list(
        SERVICE, PATH, IFACE, "CaptureScreen",
        params, GLib.VariantType("a{sv}"), Gio.DBusCallFlags.NONE, 10000,
        fdlist, None)
    meta = reply.unpack()
    os.close(fd)
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = f.read()
    return meta, data

if __name__ == "__main__":
    screen = sys.argv[1] if len(sys.argv) > 1 else "DP-1"
    t0 = time.perf_counter()
    meta, data = capture_file(screen)
    dt = (time.perf_counter() - t0) * 1000
    print("meta:", meta)
    print(f"bytes={len(data)} first16={data[:16].hex()}")
    print(f"elapsed={dt:.1f}ms")
    # single-shot timing loop
    n = 10
    t0 = time.perf_counter()
    for _ in range(n):
        meta, data = capture_file(screen)
    print(f"avg {(time.perf_counter()-t0)/n*1000:.1f}ms per frame over {n}")
