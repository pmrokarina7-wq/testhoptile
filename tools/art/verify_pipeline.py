"""Pipeline check: re-renders the delivered T4 Monolith into a temp dir and compares it with mod/sprites.
Run: .venv/bin/python tools/art/verify_pipeline.py"""
import os
import sys
import tempfile

import numpy as np
from PIL import Image

tmp = tempfile.mkdtemp()
os.environ['VG_SPRITES'] = tmp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export  # noqa: E402
from hero import heat_grad  # noqa: E402
from models6 import monolith6  # noqa: E402

export.turret('monolith', monolith6(), 160, 320, heat_grad(2.2, 4.6), parts=True)
bad = 0
for f in sorted(os.listdir(os.path.join(tmp, 'blocks/turrets'))):
    a = np.asarray(Image.open(os.path.join(tmp, 'blocks/turrets', f)).convert('RGBA'))
    b = np.asarray(Image.open(os.path.join(export.REPO, 'mod/sprites/blocks/turrets', f)).convert('RGBA'))
    diff = int((a != b).any(-1).sum()) if a.shape == b.shape else -1
    bad += diff != 0
    print(f'{f:32s} {a.shape} differing px: {diff}')
print('PIPELINE OK' if bad == 0 else f'PIPELINE DIFFERS in {bad} files')
