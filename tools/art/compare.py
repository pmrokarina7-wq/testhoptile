"""Comparison sheets for the art rework (acceptance artefact from the TZ).

    .venv/bin/python tools/art/compare.py <name> [<name> ...]

For each block/unit name writes build/art/compare/<name>-compare.png with four columns:
Scorpion reference | before (1:1) | after (1:1) | after (x3).
"before" comes from build/art-before/ (snapshot of the delivered 2.5.0-alpha1.1 sprites, made by
`compare.py --snapshot`), "after" from mod/sprites. The -full sprite is used when present.
"""
import glob
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SPR = os.path.join(REPO, 'mod', 'sprites')
BEFORE = os.path.join(REPO, 'build', 'art-before')
OUT = os.path.join(REPO, 'build', 'art', 'compare')
BG = (34, 37, 44, 255)


def find(root, name):
    for pat in (f'{name}-full.png', f'{name}.png'):
        hits = sorted(glob.glob(os.path.join(root, '**', pat), recursive=True))
        if hits:
            return Image.open(hits[0]).convert('RGBA')
    return None


def tile(im, sc):
    if im is None:
        return None
    return im.resize((im.width * sc, im.height * sc), Image.NEAREST)


def sheet(name):
    ref = find(SPR, 'scorpion')
    before = find(BEFORE, name)
    after = find(SPR, name)
    if after is None:
        print(f'{name}: no sprite in mod/sprites')
        return None
    small = max(after.width, after.height) <= 48
    k = 4 if small else 1
    cols = [('Scorpion (reference)', tile(ref, 1)), ('before 1:1', tile(before, k)),
            ('after 1:1', tile(after, k)), ('after x3', tile(after, 3 * k))]
    w = sum((c.width if c is not None else 64) for _, c in cols) + 40 * (len(cols) + 1)
    h = max((c.height if c is not None else 64) for _, c in cols) + 80
    bg = Image.new('RGBA', (w, h), BG)
    dr = ImageDraw.Draw(bg)
    dr.text((20, 10), f'{name}' + ('  (small sprites shown x4)' if small else ''), fill=(240, 200, 80, 255))
    x = 40
    for label, c in cols:
        if c is not None:
            bg.alpha_composite(c, (x, 40 + (h - 80 - c.height) // 2))
        dr.text((x, h - 30), label, fill=(210, 210, 215, 255))
        x += (c.width if c is not None else 64) + 40
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f'{name}-compare.png')
    bg.convert('RGB').save(out)
    print(out)
    return out


if __name__ == '__main__':
    if sys.argv[1:] == ['--snapshot']:
        if os.path.exists(BEFORE):
            sys.exit(f'{BEFORE} already exists')
        shutil.copytree(SPR, BEFORE)
        print('snapshot ->', BEFORE)
    else:
        for n in sys.argv[1:]:
            sheet(n)
