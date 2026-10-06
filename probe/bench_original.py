import mss
import time
import numpy as np
from PIL import ImageGrab
sct = mss.MSS(with_cursor=True)
position = sct.monitors[1]
def shot_mss():
	shot = sct.grab(position)
	return np.asarray(shot)
def shot_pil():
	shot = ImageGrab.grab(include_layered_windows=True)
	if shot.mode != "RGB":
		shot = shot.convert("RGB")
	return np.asarray(shot)
funcs = [shot_mss,shot_pil]
for func in funcs:
	print("Bencmarking:",func.__name__,"...")
	tot,count=0,0
	start=time.time()
	for i in range(330):
		frame=func()
		tot=frame.sum()
		count+=1
	finish=time.time()
	fps=count/(finish-start)
	print("Tot:",tot,"\nFps:",fps)
	break
