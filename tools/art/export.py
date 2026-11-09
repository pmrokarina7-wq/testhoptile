"""Shared exporters for the sprite pipeline.

Coordinates: 1.0 = one tile, Z up, turret heads face +Y. Sprites are 32 px per tile, like vanilla.
Every exporter writes straight into mod/sprites/<dir>/ with the exact names the content JSON expects,
and returns the composed "-full" preview (also saved) so QA sheets can be built from it.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SPR = os.environ.get('VG_SPRITES', os.path.join(REPO, 'mod', 'sprites'))
QA = os.environ.get('VG_QA', os.path.join(REPO, 'build', 'art'))

from rend import render_layer, outline, heat_sprite, over, hexc  # noqa: E402
from mats import MID  # noqa: E402

SS = 4
GLOWS = [MID[k] for k in ('glow', 'rglow', 'flame', 'pglow', 'gglow')]
FULL = {}


def save(a, d, n):
    os.makedirs(os.path.join(SPR, d), exist_ok=True)
    Image.fromarray(np.ascontiguousarray(np.asarray(a))).save(os.path.join(SPR, d, f'{n}.png'))


def blank(n):
    return np.zeros((n, n, 4), np.uint8)


def glowfn(mp, X, Y, g):
    return np.isin(mp, GLOWS).astype(float)


def matfn(*names, k=1.0):
    ids = [MID[m] for m in names]
    return lambda mp, X, Y, g: np.isin(mp, ids).astype(float) * k


def liquid_fill(bot, col, r, sq=True):
    f = np.asarray(bot).copy()
    n = f.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2
    m = (np.maximum(abs(xx - c), abs(yy - c)) < r) if sq else ((xx - c) ** 2 + (yy - c) ** 2 < r * r)
    m = m & (f[..., 3] > 0)
    f[m, :3] = (f[m, :3] * 0.35 + hexc(col) * 0.65).astype(np.uint8)
    f[m, 3] = 255
    return f


def turret(name, M, bc, tc, heat=None, parts=False, d='blocks/turrets', extra_parts=()):
    """ItemTurret/PowerTurret layers: -base (bc px), body + -outline (tc px), optional -barrel(+outline,+heat)
    for a recoiling RegionPart, otherwise an optional body -heat. extra_parts: [(suffix, groups, heatfn)]."""
    base, _ = render_layer(M, ['base'], ['base'], bc, SS)
    body, _ = render_layer(M, ['body'], ['body', 'barrel'] if parts else ['body'], tc, SS)
    save(base, d, f'{name}-base')
    save(body, d, name)
    save(outline(body), d, f'{name}-outline')
    off = (tc - bc) // 2
    f = over(blank(tc), base, off, off)
    f = over(f, outline(body))
    f = over(f, body)
    if parts:
        bar, hbar = render_layer(M, ['barrel'], ['barrel'], tc, SS, heat)
        save(bar, d, f'{name}-barrel')
        save(outline(bar), d, f'{name}-barrel-outline')
        save(heat_sprite(hbar), d, f'{name}-barrel-heat')
        f = over(f, outline(bar))
        f = over(f, bar)
    elif heat is not None:
        _, hb = render_layer(M, ['body'], ['body'], tc, SS, heat)
        save(heat_sprite(hb), d, f'{name}-heat')
    for suffix, groups, hf in extra_parts:
        p, hp = render_layer(M, groups, groups, tc, SS, hf)
        save(p, d, f'{name}{suffix}')
        save(outline(p), d, f'{name}{suffix}-outline')
        if hf is not None:
            save(heat_sprite(hp), d, f'{name}{suffix}-heat')
        f = over(f, outline(p))
        f = over(f, p)
    save(f, d, f'{name}-full')
    FULL[name] = np.asarray(f)
    return f


def layer(M, groups, canvas, heat=None, casters=None):
    """Render one layer; returns (rgba, heatmask)."""
    return render_layer(M, groups, casters or groups, canvas, SS, heat)


def qa_sheet(keys, fn, sc=2, cols=None, label=True):
    """Nearest-neighbour upscaled sheet of FULL previews (build/art/<fn>)."""
    from PIL import ImageDraw
    ims = [(k, Image.fromarray(FULL[k])) for k in keys if k in FULL]
    if not ims:
        return None
    cols = cols or len(ims)
    cell = max(max(i.width, i.height) for _, i in ims) * sc + 24
    rows = (len(ims) + cols - 1) // cols
    bg = Image.new('RGBA', (cols * cell + 24, rows * (cell + (18 if label else 0)) + 24), (34, 37, 44, 255))
    dr = ImageDraw.Draw(bg)
    for n, (k, i) in enumerate(ims):
        r, c = divmod(n, cols)
        j = i.resize((i.width * sc, i.height * sc), Image.NEAREST)
        x = 24 + c * cell + (cell - 24 - j.width) // 2
        y = 24 + r * (cell + (18 if label else 0)) + (cell - 24 - j.height) // 2
        bg.alpha_composite(j, (x, y))
        if label:
            dr.text((24 + c * cell, 24 + r * (cell + 18) + cell - 18), k, fill=(220, 220, 225, 255))
    os.makedirs(QA, exist_ok=True)
    out = os.path.join(QA, fn)
    bg.convert('RGB').save(out)
    return out
