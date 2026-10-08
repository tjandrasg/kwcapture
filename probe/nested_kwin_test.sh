#!/bin/bash
# Capture a headless KDE Plasma compositor with kwcapture -- no monitor, no GPU, no login.
#
#     dbus-run-session -- bash probe/nested_kwin_test.sh
#
# What it does: starts `kwin_wayland --virtual` (a nested KWin rendering to a virtual
# framebuffer) inside a PRIVATE D-Bus session, puts one client in it (KCalc, any Wayland app
# will do), and runs probe/nested_kwin.py against it. Verified on Plasma 6.6 / KWin 6.6.6 in
# about 6 seconds:
#
#     monitors: [('Virtual-0', (1024, 640))]
#     windows: 1 [('KCalc', (640, 508))]
#     screen grab: (640, 1024, 4) mean B/G/R = [22.0, 20.4, 19.0] max = 255
#     window grab: (480, 640, 4) 5.7 ms  mean B/G/R = [43.4, 40.1, 37.3] max = 255
#
# WHY dbus-run-session IS MANDATORY: ScreenShot2 lives on the session bus as part of
# `org.kde.KWin`, which the desktop's own KWin already owns. Nested KWin on the *desktop* bus
# answers output listing (that follows WAYLAND_DISPLAY) while windows and frames still come
# from the real desktop -- so a test would silently capture the developer's screen instead of
# the compositor under test. On a private bus the nested KWin owns the name and everything it
# returns is its own.
#
# The desktop-entry authorisation is unchanged: the helper binary is authorised by the
# `X-KDE-DBUS-Restricted-Interfaces` entry in ~/.local/share/applications (see kwcapture
# install-desktop), which the nested KWin reads the same way.
#
# Needs: kwin_wayland (Debian/Ubuntu: kwin-wayland, Fedora: kwin-wayland, Arch: kwin),
# a Wayland client for the window path (kcalc/konsole/gtk4-demo/...), and a built helper.
set -u

SOCK="${KWCAPTURE_NESTED_SOCKET:-kwcapture-test}"
SIZE="${KWCAPTURE_NESTED_SIZE:-1024x640}"
WIDTH="${SIZE%x*}"
HEIGHT="${SIZE#*x}"
CLIENT="${KWCAPTURE_NESTED_CLIENT:-kcalc}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ] || [[ "$DBUS_SESSION_BUS_ADDRESS" != unix:path=/tmp/dbus-* ]]; then
    echo "warning: this does not look like a private D-Bus session;"
    echo "         run it as:  dbus-run-session -- bash $0"
    echo "         (otherwise the desktop KWin answers and the test proves nothing)"
fi

cleanup() {
    [ -n "${CLIENT_PID:-}" ] && kill "$CLIENT_PID" 2>/dev/null
    [ -n "${KWIN_PID:-}" ] && kill "$KWIN_PID" 2>/dev/null
    sleep 1
    [ -n "${CLIENT_PID:-}" ] && kill -9 "$CLIENT_PID" 2>/dev/null
    [ -n "${KWIN_PID:-}" ] && kill -9 "$KWIN_PID" 2>/dev/null
}
trap cleanup EXIT

kwin_wayland --virtual --socket "$SOCK" --width "$WIDTH" --height "$HEIGHT" \
    --no-lockscreen --no-global-shortcuts &
KWIN_PID=$!
for _ in $(seq 1 40); do
    [ -S "${XDG_RUNTIME_DIR:-/tmp}/$SOCK" ] && break
    sleep 0.5
done
if [ ! -S "${XDG_RUNTIME_DIR:-/tmp}/$SOCK" ]; then
    echo "FAIL: kwin_wayland did not create ${XDG_RUNTIME_DIR:-/tmp}/$SOCK"
    echo "      (is kwin_wayland installed? does it need --x11 / a different backend here?)"
    exit 1
fi
echo "nested KWin: pid $KWIN_PID, socket $SOCK, output ${WIDTH}x${HEIGHT}, bus $DBUS_SESSION_BUS_ADDRESS"

if command -v "$CLIENT" >/dev/null 2>&1; then
    QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY="$SOCK" "$CLIENT" >/dev/null 2>&1 &
    CLIENT_PID=$!
    sleep 4
    echo "client: $CLIENT alive: $(kill -0 "$CLIENT_PID" 2>/dev/null && echo yes || echo no)"
else
    echo "client: $CLIENT not found -- the screen path is still tested, the window path is not"
fi

WAYLAND_DISPLAY="$SOCK" XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE \
    KWCAPTURE_NESTED_SIZE="$SIZE" "$PYTHON" "$HERE/nested_kwin.py"
RC=$?

# Benign on teardown, for the record: KWin logs `kwin_screenshot: ... pipe is broken` when the
# screenshot pipe closes while a request is still queued (helper shut down first). It is KWin's
# own writer complaining, not a failed capture.
exit $RC
