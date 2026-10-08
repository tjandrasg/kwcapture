#!/usr/bin/env python3
"""PROBE: does the kwcapture enumeration script's *failure* path work?

The real script (built in kwcapture/native/kwcapture.c) posts `Windows(nonce, ids)`
on our bus name; if anything throws inside KWin it posts `Failed(nonce, reason)`
instead, so a broken script shows up as a message instead of a timeout.  This
loads a deliberately broken variant and checks we get the reason back.

Run:  .venv/bin/python probe/kwin_script_failure_path.py
"""
import asyncio
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kwin_script_enumerate as P  # noqa: E402

BROKEN = """
(function () {
    var ids = [];
    try {
        var ws = workspace.windowList();
        for (var i = 0; i < ws.length; ++i) ids.push(String(ws[i].internalId));
        throw new Error("deliberate failure: " + ids.length + " windows seen");
    } catch (e) {
        callDBus("%(dest)s", "%(path)s", "%(iface)s", "Failed", "%(nonce)s", String(e));
        return;
    }
})();
"""


async def main():
    bus = await P.MessageBus(bus_type=P.BusType.SESSION).connect()
    recv = P.Receiver()
    bus.export("/org/kde/kwcapture", recv)
    plugin = "kwcapture-probe-fail-" + os.urandom(3).hex()
    nonce = "n" + os.urandom(4).hex()
    fd, path = tempfile.mkstemp(prefix="kwcapture-probe-", suffix=".js",
                                dir=os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    with os.fdopen(fd, "w") as f:
        f.write(BROKEN % {"dest": bus.unique_name, "path": "/org/kde/kwcapture",
                          "iface": "org.kde.kwcapture.Probe", "nonce": nonce})
    os.chmod(path, 0o600)
    try:
        [sid] = await P.dbus_call(bus, "org.kde.KWin", "/Scripting",
                                  "org.kde.kwin.Scripting", "loadScript", "ss",
                                  (path, plugin))
        await P.dbus_call(bus, "org.kde.KWin", f"/Scripting/Script{sid}",
                          "org.kde.kwin.Script", "run")
        await asyncio.wait_for(recv.got.wait(), 6.0)
        got_nonce, blob = recv.payload
        print("nonce match:", got_nonce == nonce)
        print("payload:", blob)
        ok = got_nonce == nonce and "deliberate failure" in blob
        # a stale script must NOT be accepted by the C helper's handler either;
        # the probe's handler has no nonce check, so assert on the helper instead.
        helper = re.search(r"strcmp\(nonce, st->nonce\)",
                           open(os.path.join(os.path.dirname(os.path.dirname(
                               os.path.abspath(__file__))),
                               "kwcapture", "native", "kwcapture.c")).read())
        print("the C handler rejects a foreign nonce:", bool(helper))
        return 0 if ok and helper else 1
    finally:
        await P.dbus_call(bus, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting",
                          "unloadScript", "s", (plugin,))
        os.unlink(path)
        bus.disconnect()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
