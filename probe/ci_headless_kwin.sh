#!/bin/bash
# The Debian-trixie (Plasma 6 / KWin 6) half of the headless CI job: install KWin + a Wayland
# client, install kwcapture from a checkout, authorise the helper, capture a nested KWin.
#
#     docker run --rm --device /dev/dri -v "$PWD:/w" debian:trixie-slim bash /w/probe/ci_headless_kwin.sh
#
# Run that on your own machine and you have the CI job, minus GitHub; drop --device to see what a
# GPU-less container does (which is *not* a success -- see the DRM note below and AGENTS.md).
#
# WHY THIS IS NOT JUST STEPS IN ci.yml: the nested KWin can only take screenshots when it is
# OpenGL-compositing (the org.kde.KWin.ScreenShot2 name is registered by KWin's screenshot effect,
# whose supported() is effects->isOpenGLCompositing()), and KWin's --virtual backend offers OpenGL
# only when drmGetDevices2() finds a DRM node. So the container needs /dev/dri passed in from the
# host, and passing a device is a `docker run` argument, not something a `container:` job step can
# do. The caller therefore starts this container itself; see the headless-kwin job in .github/
# workflows/ci.yml.
#
# Debian trixie rather than Ubuntu 24.04 because Plasma 6 is required: Ubuntu still ships KWin
# 5.27, whose window handles and ScreenShot2 flags are not what kwcapture speaks (Plasma 6 hands
# out {uuid} window ids).
set -eu

SRC="${SRC:-/w}"
# No GPU anywhere in this job: llvmpipe. `surfaceless` lets the Qt offscreen QPA that KWin itself
# runs on create an EGL display with no window system; note it does NOT satisfy the DRM
# requirement above -- KWin's virtual backend asks for EGL_PLATFORM_GBM_KHR explicitly, on the
# node it found with drmGetDevices2().
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export EGL_PLATFORM="${EGL_PLATFORM:-surfaceless}"
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg-run}"
export XDG_RUNTIME_DIR
mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  build-essential pkg-config libsystemd-dev libwayland-dev libcap2-bin \
  libgl1-mesa-dri qt6-qpa-plugins qt6-wayland \
  python3 python3-venv python3-pip \
  dbus dbus-x11 xkb-data \
  kwin-wayland kwin-common kcalc

# Debian's postinst grants CAP_SYS_NICE to kwin_wayland so it can raise its scheduling priority.
# A binary with file capabilities cannot be exec'd in a container running with
# no-new-privileges -- which is how GitHub runs container jobs -- and every attempt dies with
# `Operation not permitted`. KWin does not need the capability, so remove it.
setcap -r /usr/bin/kwin_wayland
echo "capabilities after setcap -r: '$(getcap /usr/bin/kwin_wayland)'"
kwin_wayland --version 2>&1 | head -2

echo "DRM devices: $(ls /dev/dri 2>/dev/null | tr '\n' ' ' || true)(empty => KWin cannot OpenGL-composite => no ScreenShot2)"
# What the probe depends on, printed so a failure is not a mystery: /WindowsRunner comes from
# kwin's krunnerintegration plugin, the client needs the Qt Wayland platform plugin (package
# `qt6-wayland`, NOT qt6-qpa-plugins), and OpenGL compositing needs some GL driver (llvmpipe).
echo "kwin plugins: $(ls /usr/lib/x86_64-linux-gnu/qt6/plugins/kwin/plugins/ 2>/dev/null | tr '\n' ' ')"
echo "qt platforms: $(ls /usr/lib/x86_64-linux-gnu/qt6/plugins/platforms/ 2>/dev/null | tr '\n' ' ')"
echo "dri drivers: $(ls /usr/lib/x86_64-linux-gnu/dri/ 2>/dev/null | tr '\n' ' ')"

python3 -m venv /tmp/venv
/tmp/venv/bin/pip install --quiet --upgrade pip
/tmp/venv/bin/pip install --quiet "$SRC"
/tmp/venv/bin/kwcapture --version
# the nested KWin authorises the helper through this file, exactly like Plasma does
/tmp/venv/bin/kwcapture install-desktop
ls -l "${XDG_DATA_HOME:-$HOME/.local/share/applications}"/io.github.kwcapture-*.desktop

# NOT from the checkout: a cwd inside the tree puts ./kwcapture on sys.path ahead of the
# installed package, and the source tree has no compiled helper -- doctor then reports
# "helper not found" for a perfectly good install. The installed-package path is the one users
# take anyway.
cd /tmp
dbus-run-session -- env PYTHON=/tmp/venv/bin/python \
  KWCAPTURE_NESTED_REQUIRE_WINDOW=1 \
  KWCAPTURE_NESTED_KWIN_DEBUG=1 \
  bash "$SRC/probe/nested_kwin_test.sh"
