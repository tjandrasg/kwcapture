"""Downscale/encode backends: cv2 vs numpy vs PIL, from the shared-memory view."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K


def timeit(label, fn, n=40):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        out = fn()
    dt = (time.perf_counter() - t0) / n * 1e3
    size = getattr(out, "shape", None) or (len(out) if isinstance(out, (bytes, bytearray)) else "")
    print(f"  {label:<44} {dt:7.2f} ms  {size}")


with K.Capture() as cap:
    bgra = cap.grab()          # (1440, 2560, 4) contiguous BGRA view
    print("input", bgra.shape, "contiguous:", bgra.flags["C_CONTIGUOUS"])
    try:
        import cv2
        print(f"\ncv2 {cv2.__version__} available")
        timeit("cv2.resize BGRA->1280 INTER_AREA",
               lambda: cv2.resize(bgra, (1280, 720), interpolation=cv2.INTER_AREA))
        timeit("cv2.resize BGRA->1280 then rgb copy",
               lambda: np.ascontiguousarray(
                   cv2.resize(bgra, (1280, 720), interpolation=cv2.INTER_AREA)[..., 2::-1]))
        timeit("cv2.resize BGRA->1024 INTER_AREA + rgb",
               lambda: np.ascontiguousarray(
                   cv2.resize(bgra, (1024, 576), interpolation=cv2.INTER_AREA)[..., 2::-1]))
        small = cv2.resize(bgra, (1280, 720), interpolation=cv2.INTER_AREA)[..., ::-1]
        timeit("cv2.imencode JPEG q85 (1280)", lambda: cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes())
        big = np.ascontiguousarray(bgra[..., ::-1])
        timeit("cv2.imencode JPEG q85 (2560)", lambda: cv2.imencode(".jpg", big, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes())
        timeit("cv2.imencode PNG (1280)", lambda: cv2.imencode(".png", small)[1].tobytes())
    except ImportError as e:
        print("no cv2:", e)

    print("\nnumpy-only paths:")
    timeit("exact /2 strided + copy", lambda: np.ascontiguousarray(bgra[::2, ::2, 2::-1]))
    timeit("exact /2 strided -> jpeg(PIL)",
           lambda: K.jpeg_bytes(np.ascontiguousarray(bgra[::2, ::2, 2::-1])))
    timeit("full-res rgb contiguous (PIL jpeg)",
           lambda: K.jpeg_bytes(np.ascontiguousarray(bgra[..., 2::-1])))

    print("\nend to end (fresh grab each time):")
    timeit("grab + cv2 1280 rgb",
           lambda: np.ascontiguousarray(
               cv2.resize(cap.grab(), (1280, 720), interpolation=cv2.INTER_AREA)[..., 2::-1]))
    timeit("grab + cv2 1280 rgb + jpeg",
           lambda: cv2.imencode(".jpg", np.ascontiguousarray(
               cv2.resize(cap.grab(), (1280, 720), interpolation=cv2.INTER_AREA)[..., ::-1]),
               [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes())
