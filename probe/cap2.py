"""Probe 2: KWin ScreenShot2 CaptureScreen via Gio async+finish.

Two fd strategies:
  --file  : hand KWin a tmpfs file fd (no flow control; we read it after the reply)
  --pipe  : hand KWin a pipe write end, drain concurrently in a thread
"""
import argparse, os, sys, threading, time
import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

SERVICE = "org.kde.KWin.ScreenShot2"
PATH = "/org/kde/KWin/ScreenShot2"
IFACE = "org.kde.KWin.ScreenShot2"

conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
loop = GLib.MainLoop()


def _call(member, params, fdlist):
    """Blocking D-Bus method call that may carry unix fds. Returns (reply_variant, fd_list)."""
    box = {}

    def cb(src, res, user_data=None):
        try:
            box["reply"], box["fds"] = src.call_with_unix_fd_list_finish(res)
        except Exception as e:  # GLib.Error and friends
            box["err"] = e
        loop.quit()

    conn.call_with_unix_fd_list(SERVICE, PATH, IFACE, member, params,
                                GLib.VariantType("a{sv}"), Gio.DBusCallFlags.NONE,
                                15000, fdlist, None, callback=cb)
    if not loop.is_running():
        GLib.timeout_add(20000, lambda: (loop.quit(), False)[1])
        loop.run()
    if "err" in box:
        raise box["err"]
    return box["reply"], box.get("fds")


def capture_file(screen, path="/dev/shm/kwcap_test", opts=None):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    fdlist = Gio.UnixFDList()
    idx = fdlist.append(fd)
    os.close(fd)
    opts = opts or {"native-resolution": GLib.Variant("b", True)}
    params = GLib.Variant("(sa{sv}h)", (screen, opts, idx))
    reply, _ = _call("CaptureScreen", params, fdlist)
    meta = reply.unpack()
    with open(path, "rb") as f:
        data = f.read()
    return meta, data


def capture_pipe(screen, opts=None):
    r, w = os.pipe()
    chunks = []

    def drain():
        while True:
            b = os.read(r, 1 << 20)
            if not b:
                break
            chunks.append(b)

    t = threading.Thread(target=drain)
    t.start()
    fdlist = Gio.UnixFDList()
    idx = fdlist.append(w)
    os.close(w)
    opts = opts or {"native-resolution": GLib.Variant("b", True)}
    params = GLib.Variant("(sa{sv}h)", (screen, opts, idx))
    try:
        reply, _ = _call("CaptureScreen", params, fdlist)
        meta = reply.unpack()
    finally:
        t.join()
        os.close(r)
    return meta, b"".join(chunks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("screen", nargs="?", default="DP-1")
    ap.add_argument("--pipe", action="store_true")
    ap.add_argument("-n", type=int, default=10)
    a = ap.parse_args()
    fn = capture_pipe if a.pipe else capture_file

    meta, data = fn(a.screen)
    print("meta:", meta)
    print(f"bytes={len(data)} head={data[:16].hex()}")
    want = meta.get("stride", 0) * meta.get("height", 0)
    print(f"expected {want} bytes -> {'MATCH' if want == len(data) else 'MISMATCH'}")

    t0 = time.perf_counter()
    for _ in range(a.n):
        meta, data = fn(a.screen)
    dt = (time.perf_counter() - t0) / a.n * 1000
    print(f"avg {dt:.2f} ms/frame  => {1000/dt:.1f} fps")
