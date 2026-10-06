"""Micro-benchmarks for the frames after the grab: RGB copy, downscale, encoding."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kwcapture as K
from PIL import Image


def timeit(label, fn, n=30):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        out = fn()
    dt = (time.perf_counter() - t0) / n * 1e3
    shape = getattr(out, "shape", None) or (len(out) if isinstance(out, (bytes, bytearray)) else None)
    print(f"  {label:<42} {dt:7.2f} ms   {shape}")
    return dt


with K.Capture() as cap:
    print(f"screen {cap.geometry()}")
    bgra = cap.grab()                     # (H,W,4) BGRA view, zero copy
    print("grab bgra view:", cap.bench(60)["fps"], "fps")
    print("rgb view (negative strides):", cap.bench(60, rgb=True)["fps"], "fps")

    print("\npost-processing from a shared-memory view:")
    timeit("np.ascontiguousarray(rgb view)", lambda: np.ascontiguousarray(bgra[..., 2::-1]))
    timeit("rgb copy via grab(copy=True,rgb=True)", lambda: cap.grab(rgb=True, copy=True))
    timeit("PIL BOX 1280 from contiguous rgb",
           lambda: K.resize(np.ascontiguousarray(bgra[..., 2::-1]), width=1280))
    rgb_nc = bgra[..., 2::-1]
    timeit("PIL BOX 1280 from strided rgb view", lambda: K.resize(rgb_nc, width=1280))
    timeit("PIL BOX 1024 from strided rgb view", lambda: K.resize(rgb_nc, width=1024))

    def pil_from_bgra():
        img = Image.frombuffer("RGBA", bgra.shape[1::-1], memoryview(bgra), "raw", "BGRA", 0, 1)
        img = img.resize((1280, 720), Image.Resampling.BOX)
        return np.asarray(img)
    timeit("Image.frombuffer(BGRA)+resize+asarray", pil_from_bgra)

    def strided2():
        return np.ascontiguousarray(bgra[::2, ::2, 2::-1])
    timeit("numpy strided ::2 (exact /2)", strided2)

    img_small = K.resize(np.ascontiguousarray(bgra[..., 2::-1]), width=1280)
    print()
    timeit("PNG encode 1280 (compress_level=1)", lambda: K.png_bytes(img_small))
    timeit("JPEG encode 1280 q85", lambda: K.jpeg_bytes(img_small, 85))
    timeit("JPEG encode 2560 q85", lambda: K.jpeg_bytes(np.ascontiguousarray(bgra[..., 2::-1]), 85))
    timeit("shot(width=1280) end to end", lambda: cap.shot(width=1280))
    timeit("shot(width=1280) + jpeg", lambda: (cap.shot(width=1280), K.jpeg_bytes(img_small, 85)))
