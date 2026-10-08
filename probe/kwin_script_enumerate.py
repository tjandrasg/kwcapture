#!/usr/bin/env python3
"""PROBE: can a throwaway KWin JS script enumerate *all* KWin windows?

Why this exists
---------------
``kwcapture --list-windows`` gets its handles from KWin's krunner interface
(``/WindowsRunner`` ``Match("")``), and that runner filters on
``Window::isNormalWindow()`` ("NET::Normal or NET::Unknown non-transient", see
kwin src/window.h).  So dialogs, utility/toolbar windows, docks, the desktop,
splash screens and override-redirect (unmanaged) windows are invisible to
list_windows() even though ``CaptureWindow(uuid)`` would happily capture them --
see the Winamp window in AGENTS.md: its big skinned window is
``_NET_WM_WINDOW_TYPE_DIALOG`` and only the tiny ``NORMAL`` winamp window shows
up.

The only thing missing is the ``QUuid`` (``Window::internalId``) of those
windows.  KWin exposes exactly one API that reaches ``Workspace::windows()``
from the outside: its scripting interface

    org.kde.kwin.Scripting  /Scripting   loadScript(filePath, pluginName) -> i
                                         isScriptLoaded(pluginName) -> b
                                         unloadScript(pluginName) -> b

Two gotchas, both measured here (see AGENTS.md):
  * ``loadScript`` does **not** run the script -- only ``Scripting::start()``
    calls ``runScripts()``.  ``run()`` has to be called on the per-script object
    ``/Scripting/Script<id>`` with interface ``org.kde.kwin.Script``.
  * ``loadScript`` is overloaded ``(s)``/``(ss)``, and a high-level binding that
    keys methods by name picks the one-arg one and quietly drops the plugin
    name (then ``isScriptLoaded``/``unloadScript`` cannot find it again).  So
    this probe sends raw messages with an explicit ``ss`` signature.

A script cannot export a D-Bus method in Plasma 6 (``registerDBusAdaptor`` is
gone from the source), but it *can* call out with ``callDBus(service, path,
interface, method, args..., callback)``, asynchronously -- so the script posts
the list back to us on *our* unique bus name, which nobody else can own.

Run:  .venv/bin/python probe/kwin_script_enumerate.py [--keep]
"""

import asyncio
import json
import os
import sys
import tempfile
import time

from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method
from dbus_fast import BusType, Message, MessageType

SCRIPT_TMPL = """
// kwcapture probe: hand out every KWin window handle we can see.
(function () {
    var rows = [];
    try {
        var ws = workspace.windowList();
        for (var i = 0; i < ws.length; ++i) {
            var w = ws[i];
            rows.push({
                id: String(w.internalId),
                caption: String(w.caption),
                resourceClass: String(w.resourceClass),
                windowType: String(w.windowType),
                normal: typeof w.normalWindow === 'undefined' ? null : w.normalWindow,
                unmanaged: typeof w.unmanaged === 'undefined' ? null : w.unmanaged,
                minimized: typeof w.minimized === 'undefined' ? null : w.minimized,
                gx: w.geometry ? w.geometry.x : null,
                gy: w.geometry ? w.geometry.y : null,
                gw: w.geometry ? w.geometry.width : null,
                gh: w.geometry ? w.geometry.height : null,
            });
        }
    } catch (e) {
        callDBus("%(dest)s", "/org/kde/kwcapture", "org.kde.kwcapture.Probe",
                 "Failed", "%(nonce)s", String(e));
        return;
    }
    callDBus("%(dest)s", "/org/kde/kwcapture", "org.kde.kwcapture.Probe",
             "Windows", "%(nonce)s", JSON.stringify(rows));
})();
"""


class Receiver(ServiceInterface):
    def __init__(self):
        super().__init__("org.kde.kwcapture.Probe")
        self.got = asyncio.Event()
        self.payload = None

    @method()
    def Windows(self, nonce: "s", blob: "s"):  # noqa: N802
        self.payload = (nonce, blob)
        self.got.set()

    @method()
    def Failed(self, nonce: "s", why: "s"):  # noqa: N802
        self.payload = (nonce, "FAILED: " + why)
        self.got.set()


async def dbus_call(bus, dest, path, interface, member, signature="", body=()):
    reply = await bus.call(Message(destination=dest, path=path, interface=interface,
                                  member=member, signature=signature, body=list(body)))
    if reply is None:
        raise RuntimeError(f"{member}: no reply")
    if reply.message_type == MessageType.ERROR:
        raise RuntimeError(f"{member} failed: {reply.body}")
    return reply.body


async def main(timeout=6.0, keep=False, repeat=1):
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    recv = Receiver()
    bus.export("/org/kde/kwcapture", recv)
    dest = bus.unique_name
    print("our unique name:", dest)

    plugin = "kwcapture-probe-" + os.urandom(3).hex()
    nonce = "n" + os.urandom(4).hex()
    script = SCRIPT_TMPL % {"dest": dest, "nonce": nonce}
    fd, path = tempfile.mkstemp(prefix="kwcapture-probe-", suffix=".js",
                                dir=os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    with os.fdopen(fd, "w") as f:
        f.write(script)
    os.chmod(path, 0o600)
    print("script:", path, "plugin:", plugin)

    rc = 1
    try:
        t0 = time.perf_counter()
        [script_id] = await dbus_call(bus, "org.kde.KWin", "/Scripting",
                                      "org.kde.kwin.Scripting", "loadScript", "ss",
                                      (path, plugin))
        t1 = time.perf_counter()
        print("loadScript -> %d  (%.1f ms)" % (script_id, 1e3 * (t1 - t0)))
        print("isScriptLoaded:", await dbus_call(bus, "org.kde.KWin", "/Scripting",
                                                 "org.kde.kwin.Scripting",
                                                 "isScriptLoaded", "s", (plugin,)))
        await dbus_call(bus, "org.kde.KWin", f"/Scripting/Script{script_id}",
                        "org.kde.kwin.Script", "run")
        t2 = time.perf_counter()
        try:
            await asyncio.wait_for(recv.got.wait(), timeout)
        except asyncio.TimeoutError:
            print("TIMEOUT: the script never called us back")
        t3 = time.perf_counter()
        print("run() -> payload: %.1f ms" % (1e3 * (t3 - t2)))
        for _ in range(max(0, repeat - 1)):
            recv.got.clear()
            p2 = plugin + "-%d" % _
            body = SCRIPT_TMPL % {"dest": dest, "nonce": nonce}
            with open(path, "w") as f:
                f.write(body)
            [sid] = await dbus_call(bus, "org.kde.KWin", "/Scripting",
                                    "org.kde.kwin.Scripting", "loadScript", "ss",
                                    (path, p2))
            a = time.perf_counter()
            await dbus_call(bus, "org.kde.KWin", f"/Scripting/Script{sid}",
                            "org.kde.kwin.Script", "run")
            try:
                await asyncio.wait_for(recv.got.wait(), timeout)
            except asyncio.TimeoutError:
                print("  iteration %d: TIMEOUT" % _)
                break
            b = time.perf_counter()
            await dbus_call(bus, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting",
                            "unloadScript", "s", (p2,))
            print("  iteration %d: load+run+reply %.1f ms" % (_, 1e3 * (b - a)))
        if recv.payload:
            got_nonce, blob = recv.payload
            print("nonce match:", got_nonce == nonce)
            try:
                rows = json.loads(blob)
            except Exception:
                print("payload:", blob[:2000])
            else:
                print("windows from windowList(): %d" % len(rows))
                for w in rows:
                    print("  {id} {t:<22} {c!r:<34} {rc!r:<24} "
                          "{gw}x{gh}+{gx}+{gy} normal={n} unmanaged={u}".format(
                              id=w["id"], t=w["windowType"], c=w["caption"][:30],
                              rc=w["resourceClass"], gx=w["gx"], gy=w["gy"],
                              gw=w["gw"], gh=w["gh"], n=w["normal"], u=w["unmanaged"]))
                rc = 0
    finally:
        if not keep:
            print("unloadScript ->", await dbus_call(bus, "org.kde.KWin", "/Scripting",
                                                     "org.kde.kwin.Scripting",
                                                     "unloadScript", "s", (plugin,)))
        os.unlink(path)
        bus.disconnect()
    return rc


if __name__ == "__main__":
    rep = 1
    if "--repeat" in sys.argv:
        rep = int(sys.argv[sys.argv.index("--repeat") + 1])
    sys.exit(asyncio.run(main(keep="--keep" in sys.argv, repeat=rep)))
