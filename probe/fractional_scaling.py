"""Ground truth for fractional scaling: what scale does KWin apply, and where?

`wl_output.scale` is an integer hint (a 125 % display says 1, a 75 % display says 1 or 2),
so every number in kwcapture that claims to be a *scale* has to be checked against the
compositor instead of against that hint.  This probe measures, on the live desktop:

  1. the monitor table: device geometry, `wl_output.scale`, the measured effective scale,
     the measured area factor, and the logical layout -- plus an independent proof that the
     measured scale is right: output positions are logical and neighbours abut, so
     `neighbour.x == (left.x + left.width) / left_scale` must hold.
  2. per output: does a whole-output frame report the same scale it was measured at?
  3. area semantics: `area=(w, h)` comes back `w * area_scale` device pixels (KWin treats
     `CaptureArea` as logical), and `area_in="physical"` comes back exactly `w`.
  4. workspace: the stitched frame is device pixels of the whole virtual desktop, so its
     size is the sum of `logical_size * own_scale` per output, not the sum of device sizes.
  5. XWayland windows: the client's own pixels, KWin's logical geometry and the captured
     frame disagree by exactly the scaling factors -- which is what tests must allow for.

Run against a live Plasma session (it starts short-lived daemons and one xterm):

    .venv/bin/python probe/fractional_scaling.py            # 1-4
    .venv/bin/python probe/fractional_scaling.py --xwayland  # + 5 (needs xterm + wmctrl)
"""
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K  # noqa: E402
import numpy as np  # noqa: E402

FAILS = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)
    return ok


def monitors_table():
    print("\n== 1. monitors: measured scales and the layout proof ==")
    mons = K.list_monitors(measure_scale=True)
    for m in mons:
        print(f"  {m.name:<12} id={m.id:<4} device={m.width}x{m.height} pos=({m.x},{m.y}) "
              f"wl_scale={m.scale} effective={m.effective_scale} area_scale={m.area_scale} "
              f"logical={m.logical_geometry}")
    check("every output has a measured scale",
          all(m.effective_scale and m.effective_scale > 0 for m in mons))
    check("effective_scale != wl_output.scale hint somewhere (the hint cannot express it)",
          any(abs(m.scale - m.effective_scale) > 0.01 for m in mons) or
          all(abs(m.effective_scale - round(m.effective_scale)) < 1e-9 for m in mons),
          str([(m.name, m.scale, m.effective_scale) for m in mons]))
    # The proof: neighbours abut in *logical* space. Sort by x, compare the right edge of
    # the left output with the x of the next one.
    for left, right in zip(mons, mons[1:]):
        if left.y != right.y:
            continue
        edge = left.x + left.width / left.effective_scale
        check(f"{right.name}.x == {left.name} logical right edge",
              abs(edge - right.x) <= 2.0,
              f"{right.x} vs {edge:.1f} (= {left.width}/{left.effective_scale}); "
              f"at wl scale {left.scale} it would be {left.x + left.width / left.scale:.1f}")
    return mons


def whole_output(mons):
    print("\n== 2. whole-output frames report the measured scale ==")
    for m in mons:
        with K.Capture(monitor=m, shm=K.default_shm_path("fs_whole")) as cap:
            f = cap.grab(copy=True, timeout=10)
            check(f"{m.name}: frame is device resolution",
                  (f.shape[1], f.shape[0]) == (m.width, m.height),
                  f"{f.shape[1]}x{f.shape[0]} vs {m.width}x{m.height}")
            check(f"{m.name}: Capture.scale == measured effective_scale",
                  abs(cap.scale - m.effective_scale) < 0.02,
                  f"frame {cap.scale} vs measured {m.effective_scale}")
            check(f"{m.name}: pixel_scale agrees", abs(cap.pixel_scale - cap.scale) < 1e-9,
                  str(cap.pixel_scale))


def areas(mons):
    print("\n== 3. area= is logical; area_in='physical' is device ==")
    for m in mons:
        la, sa = m.effective_scale, m.area_scale
        with K.Capture(monitor=m, area=(0, 0, 200, 120),
                       shm=K.default_shm_path("fs_log")) as cap:
            f = cap.grab(copy=True, timeout=10)
            want = (round(200 * cap.area_scale), round(120 * cap.area_scale))
            check(f"{m.name}: logical area (200,120) -> device size",
                  (f.shape[1], f.shape[0]) == want,
                  f"{f.shape[1]}x{f.shape[0]}, want {want} (area_scale={cap.area_scale})")
            check(f"{m.name}: area scale is the scene factor, not the display scale",
                  abs(cap.area_scale - sa) < 1e-9 and cap.area_scale != 0,
                  f"area_scale={cap.area_scale} display_scale={la}")
        with K.Capture(monitor=m, area=(0, 0, 200, 120), area_in="physical",
                       shm=K.default_shm_path("fs_phy")) as cap:
            f = cap.grab(copy=True, timeout=10)
            check(f"{m.name}: physical area (200,120) -> exactly 200x120",
                  (f.shape[1], f.shape[0]) == (200, 120), f"{f.shape[1]}x{f.shape[0]}")
    # a point that means the same thing on both sides of a mixed-DPI desk
    if len(mons) >= 2:
        m = mons[-1]
        print(f"  note: on {m.name}, logical (0,0) is device "
              f"{m.to_physical(0, 0)}; logical 100,100 is device {m.to_physical(100, 100)}")


def area_content(mons):
    """Is an area frame the *native* pixels of that region, or a resample?

    `area=` is logical and KWin renders the scene at one global factor (`area_scale`), so
    on an output whose display scale differs from it the region cannot be native: on a 75 %
    output a 200-logical-wide area is 150 native pixels upscaled to 250.  Compare a crop of
    the native whole-output frame with the area frame, resized to match -- if they agree
    closely, the geometry mapping (offset * display scale) is right.
    """
    print("\n== 3b. area frames: offset mapping and (re)sampling ==")
    try:
        import cv2
    except ImportError:
        print("  [skip] needs opencv for the resample comparison")
        return
    for m in mons:
        with K.Capture(monitor=m, shm=K.default_shm_path("fs_nat")) as cap:
            whole = cap.grab(copy=True, timeout=10)
        ax, ay, aw, ah = 100, 80, 320, 200
        with K.Capture(monitor=m, area=(ax, ay, aw, ah),
                       shm=K.default_shm_path("fs_area")) as cap:
            f = cap.grab(copy=True, timeout=10)
            s, a = cap.scale, cap.area_scale
        # the region in *device* pixels of this output
        dx, dy = round(ax * s), round(ay * s)
        dw, dh = round(aw * s), round(ah * s)
        crop = whole[dy:dy + dh, dx:dx + dw]
        if crop.shape[0] < 8 or crop.shape[1] < 8:
            print(f"  [skip] {m.name}: crop degenerate {crop.shape}")
            continue
        near = cv2.resize(crop, (f.shape[1], f.shape[0]), interpolation=cv2.INTER_LINEAR)
        mad = float(np.abs(near[..., :3].astype(int) - f[..., :3].astype(int)).mean())
        # the same crop at the WRONG mapping (logical used as device) must be clearly worse
        wx, wy = ax, ay
        bad = whole[wy:wy + dh, wx:wx + dw]
        if bad.shape[:2] == crop.shape[:2]:
            badmad = float(np.abs(cv2.resize(bad, (f.shape[1], f.shape[0]),
                                             interpolation=cv2.INTER_LINEAR)[..., :3].astype(int)
                                  - f[..., :3].astype(int)).mean())
        else:
            badmad = float("inf")
        print(f"  {m.name}: scale={s} area_scale={a}: frame {f.shape[1]}x{f.shape[0]} "
              f"from {dw}x{dh} native px -> {'resample' if (dw, dh) != (f.shape[1], f.shape[0]) else 'native 1:1'}"
              f" | MAD={mad:.1f} (wrong mapping {badmad:.1f})")
        check(f"{m.name}: area offset/size maps through the display scale",
              mad < max(14.0, badmad), f"MAD={mad:.1f}, wrong-map MAD={badmad:.1f}")


def workspace():
    print("\n== 4. workspace frame == device pixels of the whole virtual desktop ==")
    mons = K.list_monitors(measure_scale=True)
    with K.Capture(workspace=True, shm=K.default_shm_path("fs_ws")) as cap:
        f = cap.grab(copy=True, timeout=10)
        right = max((m.x + m.width / m.effective_scale) for m in mons)
        bottom = max((m.y + m.height / m.effective_scale) for m in mons)
        print(f"  frame {f.shape[1]}x{f.shape[0]}; logical extent {right:.0f}x{bottom:.0f}")
        check("workspace frame is at least the logical extent",
              f.shape[1] + 2 >= right and f.shape[0] + 2 >= bottom,
              f"{f.shape[1]}x{f.shape[0]} vs {right:.1f}x{bottom:.1f}")


def xwayland():
    print("\n== 5. XWayland window: client px vs KWin logical vs captured device px ==")
    if not (shutil.which("xterm") and shutil.which("wmctrl")):
        print("  [skip] needs xterm + wmctrl")
        return
    subprocess.run(["pkill", "-f", "xterm -name kwcpfs"], timeout=10)
    time.sleep(0.5)

    def _x11():
        out = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True).stdout
        return [ln.split()[0] for ln in out.splitlines() if len(ln.split()) >= 1]

    before = set(_x11())
    proc = subprocess.Popen(["xterm", "-name", "kwcpfs", "-title", "KWCPFS",
                             "-geometry", "40x10"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        xid, win = None, None
        deadline = time.time() + 15
        while time.time() < deadline and not (xid and win):
            # the shell rewrites xterm's title, so find it as "the X11 window that was not
            # there before", never by title
            new = [x for x in _x11() if x not in before]
            xid = sorted(new)[0] if new else None
            cands = [w for w in K.list_windows() if (w.app_id or "") == "XTerm"]
            win = cands[0] if len(cands) == 1 else None
            time.sleep(0.3)
        if not check("launched an xterm", bool(xid and win), f"x11={xid} kwin={win}"):
            return
        for (w, h) in ((320, 200), (480, 300)):
            subprocess.run(["wmctrl", "-i", "-r", xid, "-e", f"0,60,60,{w},{h}"], timeout=10)
            time.sleep(1.0)
            out = subprocess.run(["wmctrl", "-l", "-G"], capture_output=True, text=True).stdout
            row = next((ln for ln in out.splitlines() if xid and ln.startswith(xid)), "")
            cols = row.split()
            x11 = (int(cols[3]), int(cols[4]), int(cols[5]), int(cols[6])) if cols else None
            again = [x for x in K.list_windows() if (x.app_id or "") == "XTerm"]
            lg = again[0].geometry if len(again) == 1 else None
            with K.Capture(window=win.id, shm=K.default_shm_path("fs_x")) as cap:
                f = cap.grab(copy=True, timeout=10)
            print(f"  asked {w}x{h} (X11 px) -> wmctrl {x11}  kwin logical {lg}  "
                  f"frame {f.shape[1]}x{f.shape[0]}  Capture.scale={cap.scale}")
            if lg and x11:
                print(f"     kwin/x11 = {lg[2] / x11[2]:.4f}   frame/kwin = "
                      f"{f.shape[1] / lg[2]:.4f}   frame/x11 = {f.shape[1] / x11[2]:.4f}")
    finally:
        subprocess.run(["pkill", "-f", "xterm -name kwcpfs"], timeout=10)
        if proc.poll() is None:
            proc.kill()


def main():
    mons = monitors_table()
    whole_output(mons)
    areas(mons)
    area_content(mons)
    workspace()
    if "--xwayland" in sys.argv:
        xwayland()
    print("\nRESULT:", "all checks passed" if not FAILS else f"{len(FAILS)} failed: {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
