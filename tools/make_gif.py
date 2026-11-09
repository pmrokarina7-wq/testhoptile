"""Assembles test-stand frames (build/shots/gif-*.png) into an animated GIF."""
import glob
import sys

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "build/shots"
out = sys.argv[2] if len(sys.argv) > 2 else "build/shots/battle.gif"
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6

frames = []
for path in sorted(glob.glob(f"{src}/gif-*.png")):
    im = Image.open(path).convert("RGB")
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    frames.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
if not frames:
    sys.exit("no frames")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print(out, len(frames), "frames")
