"""T6 art workstream (2.5.0-alpha3): Seraphim tier. Every sprite here is new.

    .venv/bin/python tools/art/g_t6.py [name ...]     (no args = everything)

Design language (docs/VANGUARD-TZ.md 2.3): Seraphim = white organic hull, pale gold, violet glowing glyphs,
crescents and swirls; antimatter is hot magenta, singularities are near-black with a violet accretion glow.
1.0 = one tile, Z up, origin = block centre, turret heads face +Y. Reuses the Aeon geometry kit from g_t5.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g_t5 import *  # noqa: E402,F401,F403  (geometry kit, exporters, Aeon materials)
import rend  # noqa: E402
from rend import outline, heat_sprite, over  # noqa: E402
from export import save, layer, turret, FULL, qa_sheet, SPR  # noqa: E402
from hero import elevate, muzzle_world, slope_plate  # noqa: E402
from mats import Model, MID  # noqa: E402

# ------------------------------------------------------------------ materials (append-only)
rend.add_material('sera_white', ['3b3947', '5b5969', '817f91', 'a9a7b9', 'd0cede', 'f3f1fb'])
rend.add_material('sera_gold', ['3d2d12', '644b1e', '8f6f2e', 'bb9742', 'ddbd64', 'f7e4a4'])
rend.add_material('sera_dark', ['0e0a15', '171120', '211a2d', '2c243c', '382e4c', '473b5e'])
rend.add_material('glyph', ['5c2c9c', '7c3ece', '9e5cf2', 'c28cff', 'ddbaff', 'f5eaff'], glow=True)
rend.add_material('void', ['040307', '0a0610', '100b19', '171024', '1f1631', '291d40'])
rend.add_material('anti', ['8c1c6c', 'ba2a90', 'e242b6', 'ff72da', 'ffaaea', 'ffe2f7'], glow=True)
rend.add_material('anti_liq', ['4a0e3a', '74185c', 'a02a82', 'cc44a8', 'ec72c8', 'ffb0e6'])
rend.add_material('serite', ['3f3558', '605482', '8678ac', 'ada0d2', 'd2c8ee', 'f2ecff'])
rend.add_material('singul', ['130b1f', '25153b', '3b2161', '57318b', '7b49b9', 'a171e1'])

TUR, DEF, CRA, PWR, DRL = 'blocks/turrets', 'blocks/defense', 'blocks/crafting', 'blocks/power', 'blocks/drills'
SPEC6 = {}

# Seraphim defaults for the Aeon helpers (green glow / olive bed / ivory caps otherwise)
_channel5, _node5 = channel, node


def channel(M, g, pts, z, w=0.07, glow='glyph', bed='sera_dark'):
    _channel5(M, g, pts, z, w=w, glow=glow, bed=bed)


def node(M, g, x, y, z, r=0.07, glow='glyph', rim='sera_gold', h=0.03):
    _node5(M, g, x, y, z, r=r, glow=glow, rim=rim, h=h)


# ------------------------------------------------------------------ Seraphim kit
def sera_pad(M, g, h, z1=0.24, k=2.8, n=120):
    """Organic foundation: violet-black skirt, white rounded slab, pale-gold rim inlay."""
    M.add(g, rslab(sqc(h * 0.99, n, k), 0.0, 0.10, r=0.04, steps=2), 'sera_dark')
    M.add(g, rslab(sqc(h * 0.94, n, k), 0.08, z1, r=min(0.12, (z1 - 0.08) * 0.8), steps=3), 'sera_white')
    rim = sqc(h * 0.94 - 0.14, n, k)
    M.add(g, loft(ring(rim, z1 + 0.002), ring(inset(rim, 0.05), z1 + 0.002), False, False), 'sera_gold')
    return z1


def glyph_ring(M, g, r, z, n=12, span=0.55, w=0.07, phase=0.0, dots=True):
    """Ring of engraved glyph strokes (glowing arcs) with gold-set dots between them."""
    step = 360.0 / n
    for i in range(n):
        a0 = phase + i * step
        a1 = a0 + step * span
        channel(M, g, arc_pts(r, a0, a1, 6), z, w=w, glow='glyph', bed='sera_dark')
        if dots:
            q = rot2([(r, 0)], a1 + step * (1 - span) / 2)[0]
            node(M, g, q[0], q[1], z, r=w * 0.55, glow='glyph', rim='sera_gold')


def crescent_poly(R, t, a0, a1, n=20, cx=0.0, cy=0.0):
    """Crescent along a circle of radius R: full thickness t in the middle, tapering to points."""
    A = np.radians(np.linspace(a0, a1, n))
    S = np.linspace(0, 1, n)
    outer = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in A]
    inner = []
    for a, s in zip(A[::-1], S[::-1]):
        ri = R - t * max(math.sin(math.pi * s), 0.10)
        inner.append((cx + ri * math.cos(a), cy + ri * math.sin(a)))
    return P(outer + inner)


def crescent_plate(M, g, R, t, a0, a1, z0, z1, mat='sera_gold', glyph=True, cx=0.0, cy=0.0):
    M.add(g, prism(crescent_poly(R, t, a0, a1, 22, cx, cy), z0, z1), mat)
    if glyph:
        d = (a1 - a0) * 0.2
        channel(M, g, arc_pts(R - t * 0.45, a0 + d, a1 - d, 10, cx, cy), z1, w=min(0.07, t * 0.3), glow='glyph', bed='sera_dark')


def spire(M, g, x, y, z, L, r, mat='serite', core='glyph', n_side=3, phase=0.0):
    """Crystal spire on a gold plinth with leaning side crystals."""
    M.add(g, cyl((x, y, z - 0.02), (x, y, z + 0.06), r * 2.0, r * 1.8, n=20), 'sera_gold')
    M.add(g, tf(crystal(L, r, tip=0.35), None, (x, y, z + 0.05)), mat)
    M.add(g, tf(crystal(L * 0.62, r * 0.5, tip=0.35, phase=0.5), None, (x, y, z + L * 0.25)), core)
    for j in range(n_side):
        a = phase + 360.0 * j / n_side
        b = rz(a) @ np.array([r * 1.3, 0, 0])
        M.add(g, tf(crystal(L * 0.5, r * 0.45, tip=0.4), rz(a) @ ry(32), (x + b[0], y + b[1], z + 0.05)), mat)


def gimbal6(M, g, R_, r, z, tilt, yaw, glow, k=8):
    Rm = rz(yaw) @ rx(tilt)
    torus(M, g, R_, r, z, 'sera_gold', n=64, k=10, Rm=Rm)
    for i in range(k):
        a = 2 * math.pi * (i + 0.5) / k
        p = Rm @ np.array([R_ * math.cos(a), R_ * math.sin(a), 0.0]) + np.array([0.0, 0.0, z])
        M.add(g, sphereish(p, r * 1.4, n=8), glow)


def tank6(M, g, x, y, z0, h, r, fluid, glow):
    M.add(g, cyl((x, y, z0 - 0.02), (x, y, z0 + 0.05), r * 1.18, n=28), 'sera_dark')
    M.add(g, cyl((x, y, z0 + 0.05), (x, y, z0 + h), r, r * 0.96, n=28), 'sera_white')
    M.add(g, cyl((x, y, z0 + h - 0.03), (x, y, z0 + h + 0.02), r * 1.04, n=28), 'sera_gold')
    M.add(g, cyl((x, y, z0 + h + 0.02), (x, y, z0 + h + 0.03), r * 0.86, n=28), fluid)
    M.add(g, dome(x, y, z0 + h + 0.02, r * 0.62, r * 0.30, n=24, lat=4), 'sera_white')
    node(M, g, x, y, z0 + h + 0.02 + r * 0.30 - 0.015, r=r * 0.17, glow=glow, rim='sera_gold')


def hopper6(M, g, cx, cy, hx, hy, z1, mat, seed, kind='crystal'):
    """White intake bin with a dark mouth heaped with the input resource."""
    M.add(g, rslab(cham_rect(hx, hy, 0.07, cx=cx, cy=cy), z1 - 0.02, z1 + 0.16, r=0.05), 'sera_white')
    M.add(g, B(cx - hx + 0.07, cx + hx - 0.07, cy - hy + 0.07, cy + hy - 0.07, z1 + 0.10, z1 + 0.165), 'sera_dark')
    rng = np.random.default_rng(seed)
    for _ in range(int(hx * hy * 50) + 3):
        x = cx + rng.uniform(-hx + 0.13, hx - 0.13)
        y = cy + rng.uniform(-hy + 0.12, hy - 0.12)
        if kind == 'crystal':
            M.add(g, bipyr(5, 0.06, z1 + 0.12, z1 + 0.16, z1 + 0.25, cx=x, cy=y, rot=rng.uniform(0, 72)), mat)
        elif kind == 'cube':
            M.add(g, tf(cbox(0, 0, 0, 0.09, 0.09, 0.09), rz(rng.uniform(0, 90)) @ rx(25), (x, y, z1 + 0.18)), mat)
        else:
            M.add(g, sphereish((x, y, z1 + 0.16), 0.055, n=8), mat)


def blade_poly(r0, r1, sweep, w0, w1, n=12):
    """Swept rotor blade: centre line spirals from r0 to r1 over `sweep` degrees, width w0 -> w1."""
    S = np.linspace(0, 1, n)
    C = [np.array([(r0 + (r1 - r0) * s) * math.cos(math.radians(sweep * s)),
                   (r0 + (r1 - r0) * s) * math.sin(math.radians(sweep * s))]) for s in S]
    left, right = [], []
    for i, s in enumerate(S):
        d = C[min(i + 1, n - 1)] - C[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        nr = np.array([-d[1], d[0]])
        w = (w0 + (w1 - w0) * s) / 2
        left.append(tuple(C[i] + nr * w))
        right.append(tuple(C[i] - nr * w))
    return P(left + right[::-1]), [tuple(c) for c in C]


def dome_ribs(M, g, zd, R, H, n, mat='sera_gold', r=0.035, t1=72, phase=0.0):
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        pts = [(R * 1.01 * math.cos(t) * math.cos(a), R * 1.01 * math.cos(t) * math.sin(a), zd + H * math.sin(t) + 0.005)
               for t in np.radians(np.linspace(2, t1, 5))]
        M.add(g, tube_path(pts, r, n=6), mat)


def dome_band(M, g, zd, R, H, zz, mat, r=0.05, n=64):
    """Torus lying on a dome() surface at height zz above its base."""
    s = min(zz / H, 0.999)
    torus(M, g, R * math.sqrt(1 - s * s), r, zd + zz, mat, n=n, k=6)


# ================================================================== REQUIEM - T6 Seraphim artillery (10x10)
BX6 = (-1.25, 0.0, 1.25)          # ShootAlternate spread 10 world units


def requiem():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 5.0, z1=0.26, k=3.2)
    glyph_ring(M, g, 4.30, z1, n=16, span=0.6, w=0.08)
    for k in range(4):
        a = 45 + 90 * k
        crescent_plate(M, g, 4.05, 0.55, a - 22, a + 22, z1 - 0.02, z1 + 0.16)
        p = rz(a) @ np.array([3.62, 0, 0])
        spire(M, g, p[0], p[1], z1, 0.95, 0.16, phase=a)
        # cardinal heat intakes: gold sockets with glyph grilles
        T = rz(90 * k)
        M.add(g, tf(rslab(cham_rect(0.95, 0.30, 0.12, cy=-4.22), z1 - 0.02, z1 + 0.12, r=0.05), T), 'sera_gold')
        for x in (-0.6, -0.2, 0.2, 0.6):
            M.add(g, tf(cbox(x, -4.22, z1 + 0.125, 0.16, 0.38, 0.012), T), 'glyph')
        for s in (-1, 1):
            q = rot2([(s * 1.55, -3.78)], 90 * k)[0]
            node(M, g, q[0], q[1], z1, r=0.06, glow='glyph', rim='sera_gold')
    M.add(g, annulus(3.05, 3.38, z1 - 0.02, z1 + 0.10, n=112), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.06), 3.05, n=112), 'sera_dark')
    glyph_ring(M, g, 3.21, z1 + 0.10, n=24, span=0.5, w=0.06, dots=False)
    zb = z1 + 0.10

    # ---- rotating body: teardrop hull, dorsal crest, swept wing plates, antimatter pods
    g = 'body'
    hull = mirror_half([(0, 2.7), (1.15, 2.35), (2.25, 1.2), (2.8, -0.5), (2.55, -2.1), (1.6, -3.0), (0, -3.25)])
    M.add(g, prof(hull, [(0.0, zb), (0.0, zb + 0.30), (0.10, zb + 0.46), (0.28, zb + 0.56), (0.55, zb + 0.62)]), 'sera_white')
    top = zb + 0.62
    band = inset(hull, 0.66)
    M.add(g, loft(ring(band, top + 0.003), ring(inset(band, 0.07), top + 0.003), False, False), 'sera_gold')
    crest = mirror_half([(0, 1.9), (0.35, 1.5), (0.55, -0.4), (0.42, -2.2), (0, -2.6)])
    M.add(g, prof(crest, [(0.0, top - 0.01), (0.0, top + 0.12), (0.08, top + 0.22), (0.20, top + 0.27)]), 'sera_white')
    channel(M, g, [(0, -2.25), (0, 1.5)], top + 0.27, w=0.10)
    for s in (-1, 1):
        wing = P([(s * 0.9, 1.3), (s * 2.0, 0.6), (s * 2.3, -0.8), (s * 2.0, -2.1), (s * 1.2, -2.45), (s * 0.75, -0.6)])
        zf = (lambda x, y: top + 0.12 - (abs(x) - 0.75) * 0.06)
        slope_plate(M, g, wing, zf, 'sera_gold', thick=0.12, inlay='sera_white', isc=0.62, ih=0.02)
        channel(M, g, [(s * 1.05, 0.75), (s * 1.6, 0.15), (s * 1.8, -0.9), (s * 1.5, -1.9)], zf(1.5, 0) + 0.025, w=0.07)
        node(M, g, s * 1.95, -0.85, zf(1.95, 0), r=0.07, glow='glyph', rim='sera_white')
        capsule(M, g, (s * 1.35, -2.72, top + 0.06), (s * 0.40, -2.92, top + 0.06), 0.15, 'anti', band='sera_gold', cap='sera_white')
        # trunnion cheeks carrying the barrel cradle
        M.add(g, rslab(cham_rect(0.22, 0.65, 0.08, cx=s * 2.08, cy=1.0), top - 0.10, top + 0.42, r=0.06), 'sera_white')
        M.add(g, cyl((s * 1.85, 1.0, top + 0.30), (s * 2.36, 1.0, top + 0.30), 0.22, n=20), 'sera_gold')
        node(M, g, s * 2.08, 1.55, top + 0.42, r=0.06, glow='glyph', rim='sera_gold')
    crescent_plate(M, g, 2.4, 0.42, 238, 302, top - 0.10, top + 0.06, cy=-0.95)

    # ---- three-barrel cradle (recoiling part)
    g = 'barrel_local'
    M.add(g, rslab(cham_rect(1.95, 0.70, 0.30, cy=-0.30), -0.30, 0.12, r=0.06), 'sera_white')
    channel(M, g, [(-1.7, -0.55), (1.7, -0.55)], 0.12, w=0.06)
    for x in BX6:
        M.add(g, rslab(cham_rect(0.42, 0.62, 0.14, cx=x, cy=-0.25), 0.05, 0.36, r=0.06), 'sera_white')
        M.add(g, cbox(x, -0.25, 0.37, 0.16, 0.78, 0.02), 'glyph')
        M.add(g, cyl((x, 0.3, 0), (x, 5.6, 0), 0.36, 0.29, n=22), 'sera_white')
        for y in (0.55, 1.6, 2.7, 3.8, 4.8):
            M.add(g, cyl((x, y, 0), (x, y + 0.12, 0), 0.40 - y * 0.015, n=22), 'sera_gold')
        for y in (1.05, 2.15, 3.25, 4.3):
            M.add(g, cyl((x, y, 0), (x, y + 0.22, 0), 0.37 - y * 0.015, n=22), 'glyph')
        for s in (-1, 1):
            claw = P([(x + s * 0.14, 5.30), (x + s * 0.42, 5.55), (x + s * 0.42, 5.95), (x + s * 0.24, 6.15), (x + s * 0.27, 5.75)])
            M.add(g, prism(claw, -0.12, 0.14), 'sera_gold')
        M.add(g, cyl((x, 5.6, 0), (x, 5.75, 0), 0.20, n=18), 'glyph')
    for y0 in (1.42, 3.55):                                           # barrel clamps
        M.add(g, box(-1.62, 1.62, y0, y0 + 0.14, -0.18, 0.30), 'sera_gold')
    pv = (0, 1.0, top + 0.30)
    elevate(M, 6, pv)
    SPEC6['requiem'] = muzzle_world(6, pv, 6.0)[0]
    return M


def heat_requiem(mp, X, Y, g):
    ids = [MID[m] for m in ('sera_white', 'sera_gold')]
    grad = np.where(np.isin(mp, ids), np.clip((Y - 4.6) / (7.0 - 4.6), 0, 1) * 0.85, 0)
    return np.maximum(grad, np.isin(mp, [MID['glyph']]).astype(float) * 0.9)


# ================================================================== OBELISK - T6 continuous beam (8x8)
def obelisk():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 4.0, z1=0.24, k=3.0)
    glyph_ring(M, g, 3.42, z1, n=12, span=0.6, w=0.08)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([3.05, 0, 0])
        spire(M, g, p[0], p[1], z1, 0.85, 0.15, phase=a)
        crescent_plate(M, g, 3.0, 0.40, a + 18, a + 72, z1 - 0.02, z1 + 0.10)
    M.add(g, annulus(2.35, 2.60, z1 - 0.02, z1 + 0.10, n=96), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.06), 2.35, n=96), 'sera_dark')
    glyph_ring(M, g, 2.47, z1 + 0.10, n=20, span=0.5, w=0.05, dots=False)
    zb = z1 + 0.10

    g = 'body'
    hull = mirror_half([(0, 2.4), (0.7, 1.9), (1.45, 0.5), (1.65, -0.9), (1.3, -2.0), (0.6, -2.5), (0, -2.6)])
    M.add(g, prof(hull, [(0.0, zb), (0.0, zb + 0.25), (0.12, zb + 0.42), (0.35, zb + 0.58), (0.7, zb + 0.70)]), 'sera_white')
    top = zb + 0.70
    spine = mirror_half([(0, 1.7), (0.30, 1.1), (0.42, -0.6), (0.30, -1.9), (0, -2.2)])
    M.add(g, prof(spine, [(0.0, top - 0.02), (0.0, top + 0.20), (0.12, top + 0.42), (0.26, top + 0.55)]), 'sera_gold')
    channel(M, g, [(0, -1.8), (0, 1.3)], top + 0.55, w=0.09)
    for s in (-1, 1):
        horn = P([(s * 0.45, 1.2), (s * 1.25, 1.6), (s * 1.35, 2.6), (s * 0.95, 3.4), (s * 0.80, 3.15), (s * 0.98, 2.5), (s * 0.75, 1.75)])
        M.add(g, prism(horn, zb + 0.30, top + 0.15), 'sera_gold')
        channel(M, g, [(s * 0.72, 1.55), (s * 1.15, 2.05), (s * 1.10, 2.85)], top + 0.15, w=0.06)
        fin = P([(s * 1.3, 0.2), (s * 2.2, -0.6), (s * 2.35, -1.6), (s * 1.5, -1.6)])
        M.add(g, prism(fin, zb + 0.15, zb + 0.40, 0.9), 'sera_white')
        node(M, g, s * 1.9, -1.1, zb + 0.40, r=0.07, glow='glyph', rim='sera_gold')
        groove(M, g, [(s * 0.55, -2.0), (s * 1.05, -1.2), (s * 1.15, 0.0)], top, w=0.03, m='sera_dark')
    M.add(g, cyl((0, 2.55, top), (0, 3.25, top), 0.30, 0.38, n=24), 'sera_white')
    M.add(g, cyl((0, 3.25, top), (0, 3.40, top), 0.34, n=24), 'sera_gold')
    M.add(g, sphereish((0, 3.42, top), 0.26, n=14), 'glyph')
    SPEC6['obelisk'] = 3.45
    return M


# ================================================================== SERAPHIM NET - T6 universal interceptor (6x6)
def seraphim_net():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 3.0, z1=0.22, k=2.6)
    glyph_ring(M, g, 2.55, z1, n=12, span=0.55, w=0.07)
    for k in range(3):
        a = 90 + 120 * k
        crescent_plate(M, g, 2.25, 0.45, a - 35, a + 35, z1 - 0.02, z1 + 0.12)
        p = rz(a + 60) @ np.array([2.25, 0, 0])
        spire(M, g, p[0], p[1], z1, 0.7, 0.12, phase=a)
    M.add(g, annulus(1.55, 1.75, z1 - 0.02, z1 + 0.08, n=72), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.04), 1.55, n=72), 'sera_dark')
    zh = z1 + 0.08

    g = 'head'
    M.add(g, dome(0, 0, zh, 1.05, 0.95, n=48, lat=8), 'sera_white')
    torus(M, g, 1.02, 0.06, zh + 0.10, 'sera_gold', n=56, k=8)
    dome_band(M, g, zh, 1.05, 0.95, 0.62, 'glyph', r=0.035, n=48)
    dome_ribs(M, g, zh, 1.05, 0.95, 6, r=0.03, t1=58, phase=30)
    node(M, g, 0, 0, zh + 0.93, r=0.10, glow='glyph', rim='sera_gold')
    for k in range(3):                              # three curling emitter arms (C3), the first one points forward
        R = rz(120 * k)
        pts = [(0.0, 0.80, zh + 0.55), (0.0, 1.35, zh + 0.60), (0.35, 1.85, zh + 0.50), (0.75, 2.05, zh + 0.38)]
        pts = [tuple(R @ np.array(p)) for p in pts]
        M.add(g, tube_path(pts, 0.10, n=10), 'sera_gold')
        M.add(g, sphereish(np.array(pts[-1]), 0.14, n=10), 'glyph')
    M.add(g, sphereish((0, 1.0, zh + 0.40), 0.16, n=12), 'glyph')
    return M


# ================================================================== CHRONOFIELD - T6 time field (7x7, OverdriveProjector)
def chronofield():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.5, z1=0.22, k=2.4)
    M.add(g, annulus(2.70, 2.95, z1 - 0.02, z1 + 0.10, n=96), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.02), 2.70, n=96), 'sera_dark')
    for i in range(12):                                             # dial: gold hour bars + glyph minute dots
        a = 90 - 30 * i
        q = rot2([(2.45, 0)], a)[0]
        if i % 3 == 0:
            M.add(g, tf(rslab(cham_rect(0.09, 0.22, 0.03), z1, z1 + 0.10, r=0.03), rz(a - 90), (q[0], q[1], 0)), 'sera_gold')
            node(M, g, q[0], q[1], z1 + 0.10, r=0.045, glow='glyph', rim='sera_gold')
        else:
            node(M, g, q[0], q[1], z1 + 0.02, r=0.06, glow='glyph', rim='sera_gold')
    for r, w, ph in ((2.10, 0.06, 0), (1.62, 0.05, 15), (1.15, 0.05, 30)):
        for q in range(4):
            arc(M, g, r - w, r + w, ph + 90 * q + 8, ph + 90 * q + 82, z1 + 0.02, z1 + 0.07, 'sera_gold', n=14)
    glyph_ring(M, g, 1.86, z1 + 0.02, n=8, span=0.45, w=0.06)
    crescent_plate(M, g, 1.95, 0.32, 40, 115, z1 + 0.06, z1 + 0.16)       # the two hands
    crescent_plate(M, g, 1.38, 0.28, 175, 245, z1 + 0.06, z1 + 0.16)
    M.add(g, cyl((0, 0, z1 + 0.02), (0, 0, z1 + 0.14), 0.62, 0.55, n=40), 'sera_white')
    torus(M, g, 0.60, 0.04, z1 + 0.14, 'sera_gold', n=40, k=6)
    for i in range(6):
        a = 30 + 60 * i
        M.add(g, tf(crystal(0.62, 0.11, tip=0.35), rz(a) @ ry(62), (0, 0, z1 + 0.18)), 'serite')
    M.add(g, bipyr(6, 0.20, z1 + 0.12, z1 + 0.30, z1 + 0.70), 'glyph')
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([3.05, 0, 0])
        spire(M, g, p[0], p[1], z1, 0.75, 0.13, phase=a)
    return M


# ================================================================== SERAPHIM DOME - T6 shield (9x9, ForceProjector)
def seraphim_dome():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 4.5, z1=0.24, k=2.6)
    glyph_ring(M, g, 4.0, z1, n=18, span=0.6, w=0.08)
    zd = z1 + 0.10
    M.add(g, annulus(1.55, 1.85, z1 - 0.02, zd, n=96), 'sera_gold')
    for i in range(6):
        a = 30 + 60 * i
        R = rz(a)
        zf = (lambda x, y: zd + 0.34 - (x - 1.65) * 0.20)
        slope_plate(M, g, leaf(1.65, 0.48, n=12, back=1.65), zf, 'sera_white', thick=0.10, inlay='sera_gold', isc=0.5, ih=0.02, R=R)
        p = R @ np.array([2.55, 0, 0])
        node(M, g, p[0], p[1], zf(2.55, 0) + 0.02, r=0.06, glow='glyph', rim='sera_gold')
        b = rz(a + 30) @ np.array([3.30, 0, 0])
        spire(M, g, b[0], b[1], z1, 0.85, 0.14, phase=a)
    M.add(g, dome(0, 0, zd, 1.55, 1.05, n=64, lat=9), 'sera_white')
    dome_ribs(M, g, zd, 1.55, 1.05, 6, t1=74)
    dome_band(M, g, zd, 1.55, 1.05, 0.62, 'glyph', r=0.045)
    dome_band(M, g, zd, 1.55, 1.05, 0.92, 'glyph', r=0.035, n=48)
    M.add(g, cyl((0, 0, zd + 1.00), (0, 0, zd + 1.10), 0.28, 0.22, n=20), 'sera_gold')
    M.add(g, sphereish((0, 0, zd + 1.16), 0.16, n=12), 'glyph')
    return M


# ================================================================== GRAVITY EXTRACTOR - T6 drill (6x6)
def gravity_extractor():
    """Drill layers: main (housing + well floor, drawn first), -rotator (spinSprite: C4 symmetric), -top (static cap)."""
    M = Model()
    g = 'main'
    M.add(g, rslab(sqc(2.98, 96, 3.0), 0.0, 0.06, r=0.03, steps=2), 'sera_dark')
    M.add(g, cyl((0, 0, 0.06), (0, 0, 0.07), 2.05, n=80), 'void')
    for r in (0.9, 1.5):
        M.add(g, annulus(r, r + 0.04, 0.07, 0.078, n=72), 'glyph')
    top = 0.30
    holed(M, g, sqc(2.98, 96, 3.0), 2.02, 0.0, 0.16, 'sera_dark')
    holed(M, g, sqc(2.86, 96, 3.0), 2.08, 0.14, top, 'sera_white', zi=top - 0.05)
    M.add(g, annulus(1.98, 2.18, top - 0.08, top + 0.06, n=96, zi=top + 0.01), 'sera_gold')
    glyph_ring(M, g, 2.40, top - 0.01, n=16, span=0.5, w=0.06)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([2.85, 0, 0])
        spire(M, g, p[0], p[1], top - 0.02, 0.70, 0.12, phase=a)
        q = rot2([(0, -2.60)], 90 * k)[0]
        tank6(M, g, q[0], q[1], top - 0.02, 0.22, 0.22, 'anti_liq', 'anti')

    g = 'rotator'
    M.add(g, annulus(1.80, 1.95, 0.10, 0.17, n=96), 'sera_gold')
    for i in range(4):
        poly, C = blade_poly(0.42, 1.86, 62, 0.42, 0.20)
        M.add(g, prism(P(rot2(list(poly), 90 * i)), 0.11, 0.21, 0.92), 'sera_white')
        channel(M, g, rot2(C[1:-1], 90 * i), 0.21, w=0.05)
        tip = rot2([C[-2]], 90 * i)[0]
        M.add(g, sphereish((tip[0], tip[1], 0.22), 0.08, n=8), 'glyph')
    M.add(g, cyl((0, 0, 0.10), (0, 0, 0.24), 0.52, n=40), 'sera_white')

    g = 'top'
    for i in range(4):                                      # static bridge arms holding the cap over the rotor
        M.add(g, tf(box(0.70, 2.02, -0.06, 0.06, 0.32, 0.40), rz(45 + 90 * i)), 'sera_gold')
    M.add(g, annulus(0.55, 0.82, 0.30, 0.42, n=48), 'sera_gold')
    M.add(g, dome(0, 0, 0.30, 0.56, 0.34, n=40, lat=6), 'void')
    torus(M, g, 0.66, 0.035, 0.44, 'glyph', n=48, k=6)
    return M


# ================================================================== ANTIMATTER TRAP - T6 crafter (5x5)
def antimatter_trap():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 2.5, z1=0.22, k=2.6)
    glyph_ring(M, g, 2.15, z1, n=12, span=0.5, w=0.06)
    M.add(g, annulus(0.95, 1.30, z1 - 0.02, z1 + 0.14, n=72, zi=z1 + 0.06), 'sera_white')
    M.add(g, annulus(1.30, 1.40, z1 - 0.02, z1 + 0.11, n=72), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.0), 0.96, n=64), 'void')
    torus(M, g, 0.80, 0.03, z1 + 0.01, 'anti', n=48, k=6)
    for k in range(4):                                              # Penning coils on the cardinals
        R = rz(90 * k)
        M.add(g, tf(B(-0.16, 0.16, 1.15, 1.55, z1 - 0.02, z1 + 0.16), R), 'sera_gold')
        M.add(g, tf(cyl((0, 1.05, z1 + 0.30), (0, 1.55, z1 + 0.30), 0.22, n=18), R), 'sera_white')
        for y in np.linspace(1.10, 1.45, 4):
            M.add(g, tf(cyl((0, y, z1 + 0.30), (0, y + 0.05, z1 + 0.30), 0.25, n=18), R), 'glyph')
        M.add(g, tf(cyl((0, 1.55, z1 + 0.30), (0, 1.62, z1 + 0.30), 0.27, n=18), R), 'sera_gold')
    zc = z1 + 0.62
    M.add(g, sphereish((0, 0, zc), 0.30, n=16), 'anti')
    gimbal6(M, g, 0.55, 0.035, zc, 60, 0, 'glyph', k=6)
    gimbal6(M, g, 0.55, 0.035, zc, 60, 90, 'glyph', k=6)
    gimbal6(M, g, 0.78, 0.04, zc - 0.10, 12, 45, 'glyph', k=8)
    for k in range(4):
        p = rz(45 + 90 * k) @ np.array([2.0, 0, 0])
        if k % 2 == 0:
            tank6(M, g, p[0], p[1], z1, 0.30, 0.30, 'qcond', 'quantum')
        else:
            tank6(M, g, p[0], p[1], z1, 0.30, 0.30, 'anti_liq', 'anti')
    return M


# ================================================================== SERAPHITE REFINERY - T6 crafter (6x6)
def seraphite_refinery():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.0, z1=0.22, k=2.6)
    glyph_ring(M, g, 2.62, z1, n=14, span=0.5, w=0.06)
    M.add(g, annulus(1.15, 1.55, z1 - 0.02, z1 + 0.16, n=80, zi=z1 + 0.08), 'sera_white')
    M.add(g, annulus(1.55, 1.65, z1 - 0.02, z1 + 0.13, n=80), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.02), 1.16, n=72), 'sera_dark')
    M.add(g, cyl((0, 0, z1 + 0.02), (0, 0, z1 + 0.035), 1.02, n=72), 'glyph')
    for i in range(6):
        a = 30 + 60 * i
        b = rz(a) @ np.array([0.32, 0, 0])
        M.add(g, tf(crystal(0.55, 0.10, tip=0.35), rz(a) @ ry(38), (b[0], b[1], z1 + 0.10)), 'serite')
    M.add(g, bipyr(6, 0.24, z1 + 0.20, z1 + 0.45, z1 + 1.0, rot=15), 'serite')
    M.add(g, bipyr(6, 0.10, z1 + 0.35, z1 + 0.50, z1 + 1.04), 'glyph')
    for k in range(4):                                              # swirl channels into the pool
        a0 = 45 + 90 * k
        pts = [((1.70 + 0.55 * s) * math.cos(math.radians(a0 + 40 * s)), (1.70 + 0.55 * s) * math.sin(math.radians(a0 + 40 * s)))
               for s in np.linspace(0, 1, 8)]
        channel(M, g, pts, z1, w=0.08)
    hopper6(M, g, 0, -2.18, 0.55, 0.28, z1, 'serite', 31, kind='crystal')
    hopper6(M, g, 2.18, 0, 0.28, 0.55, z1, 'quantum', 32, kind='cube')
    M.add(g, rslab(cham_rect(0.26, 0.70, 0.08, cx=-2.18), z1 - 0.02, z1 + 0.08, r=0.04), 'sera_white')
    capsule(M, g, (-2.18, -0.62, z1 + 0.22), (-2.18, 0.62, z1 + 0.22), 0.17, 'anti', band='sera_gold', cap='sera_white')
    crescent_plate(M, g, 2.30, 0.34, 62, 118, z1 - 0.02, z1 + 0.10)
    for k in range(4):
        p = rz(45 + 90 * k) @ np.array([2.62, 0, 0])
        spire(M, g, p[0], p[1], z1, 0.6, 0.11, phase=45 + 90 * k)
    return M


# ================================================================== SINGULARITY COLLIDER - T6 crafter (7x7)
def singularity_collider():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.5, z1=0.24, k=2.8)
    glyph_ring(M, g, 3.12, z1, n=16, span=0.5, w=0.06)
    zr = z1 + 0.34
    for i in range(6):                                              # ring supports
        M.add(g, tf(rslab(cham_rect(0.16, 0.10, 0.04, cx=2.2), z1 - 0.02, zr, r=0.04), rz(30 + 60 * i)), 'sera_gold')
    torus(M, g, 2.20, 0.22, zr, 'sera_white', n=72, k=12)
    for i in range(12):
        a = math.radians(30 * i)
        c = np.array([2.2 * math.cos(a), 2.2 * math.sin(a), zr])
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        M.add(g, cyl(c - t * 0.05, c + t * 0.05, 0.26, n=16), 'sera_gold')
        torus(M, g, 2.20, 0.232, zr, 'glyph', n=4, k=10, a0=30 * i + 9, a1=30 * i + 21)
    M.add(g, annulus(0.95, 1.55, z1 - 0.02, z1 + 0.10, n=80, zi=z1 + 0.02), 'sera_dark')
    M.add(g, annulus(1.55, 1.65, z1 - 0.02, z1 + 0.12, n=80), 'sera_gold')
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.0), 0.96, n=64), 'void')
    M.add(g, annulus(0.50, 0.92, z1 + 0.30, z1 + 0.32, n=72), 'glyph')
    M.add(g, annulus(0.44, 0.52, z1 + 0.31, z1 + 0.33, n=48), 'anti')
    M.add(g, sphereish((0, 0, z1 + 0.32), 0.42, n=18), 'void')
    for k in range(3):                                              # injector arms aimed at the core
        R = rz(120 * k)
        pts = [tuple(R @ np.array(p)) for p in ((0, 2.45, zr + 0.05), (0, 1.75, zr + 0.25), (0, 1.15, z1 + 0.45))]
        M.add(g, tube_path(pts, 0.09, n=10), 'sera_gold')
        M.add(g, sphereish(np.array(pts[-1]), 0.12, n=10), 'glyph')
    for k, (mat, kind) in enumerate((('singul', 'crystal'), ('sera_white', 'orb'), (None, None))):
        a = 45 + 90 * k
        p = rz(a) @ np.array([3.0, 0, 0])
        if mat is None:
            q0, q1 = rz(a) @ np.array([3.0, -0.38, 0]), rz(a) @ np.array([3.0, 0.38, 0])
            capsule(M, g, (q0[0], q0[1], z1 + 0.20), (q1[0], q1[1], z1 + 0.20), 0.15, 'anti', band='sera_gold', cap='sera_white')
        else:
            hopper6(M, g, p[0], p[1], 0.30, 0.30, z1, mat, 40 + k, kind=kind)
    p = rz(315) @ np.array([3.0, 0, 0])
    spire(M, g, p[0], p[1], z1, 0.8, 0.14, phase=315)
    return M


# ================================================================== ANNIHILATION REACTOR - T6 power + heat (7x7, HeaterGenerator)
def annihilation_reactor():
    """main (unrotated) + 'top' group = heat nozzle facing +x (rendered as -top1, rotated by the engine)."""
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.5, z1=0.24, k=3.0)
    glyph_ring(M, g, 2.32, z1, n=16, span=0.55, w=0.07)
    zd = z1 + 0.10
    M.add(g, annulus(1.75, 2.05, z1 - 0.02, zd, n=96), 'sera_gold')
    M.add(g, dome(0, 0, zd, 1.75, 1.25, n=72, lat=10), 'sera_white')
    for zz in (0.32, 0.72):
        dome_band(M, g, zd, 1.75, 1.25, zz, 'anti', r=0.06, n=72)
    dome_ribs(M, g, zd, 1.75, 1.25, 8, t1=70, phase=22.5)
    M.add(g, cyl((0, 0, zd + 1.18), (0, 0, zd + 1.28), 0.30, 0.24, n=20), 'sera_gold')
    M.add(g, sphereish((0, 0, zd + 1.34), 0.17, n=12), 'anti')
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([2.80, 0, 0])
        M.add(g, cyl((p[0], p[1], z1 - 0.02), (p[0], p[1], z1 + 0.58), 0.30, 0.22, n=20), 'sera_white')
        for zz in (0.18, 0.32, 0.46):
            M.add(g, cyl((p[0], p[1], z1 + zz), (p[0], p[1], z1 + zz + 0.05), 0.29 - zz * 0.12, n=20), 'glyph')
        M.add(g, cyl((p[0], p[1], z1 + 0.58), (p[0], p[1], z1 + 0.64), 0.26, n=20), 'sera_gold')
        node(M, g, p[0], p[1], z1 + 0.64, r=0.08, glow='anti', rim='sera_gold')
        q = rz(a) @ np.array([1.62, 0, 0])
        M.add(g, tube_path([(p[0], p[1], z1 + 0.60), ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z1 + 0.85), (q[0], q[1], zd + 0.55)], 0.05, n=8), 'sera_gold')
        T = rz(90 * k)
        M.add(g, tf(rslab(cham_rect(0.30, 0.40, 0.10, cx=2.75), z1 - 0.02, z1 + 0.14, r=0.05), T), 'sera_gold')
        M.add(g, tf(cbox(2.75, 0, z1 + 0.145, 0.42, 0.56, 0.012), T), 'sera_dark')

    g = 'top'
    z = z1 + 0.36
    M.add(g, cyl((1.55, 0, z), (3.02, 0, z), 0.34, 0.30, n=24), 'sera_white')
    for x in (1.95, 2.55):
        M.add(g, cyl((x, 0, z), (x + 0.10, 0, z), 0.37, n=24), 'sera_gold')
    for x in (2.12, 2.24, 2.70, 2.82):
        M.add(g, cyl((x, 0, z), (x + 0.06, 0, z), 0.35, n=24), 'glyph')
    M.add(g, cyl((3.02, 0, z), (3.30, 0, z), 0.40, 0.46, n=24), 'sera_gold')
    M.add(g, cyl((3.30, 0, z), (3.34, 0, z), 0.34, n=24), 'anti')
    for s in (-1, 1):
        claw = P([(2.95, s * 0.30), (3.35, s * 0.52), (3.45, s * 0.36), (3.30, s * 0.22)])
        M.add(g, prism(claw, z - 0.10, z + 0.16), 'sera_gold')
    return M


def heat_nozzle(mp, X, Y, g):
    hot = np.isin(mp, [MID['anti'], MID['glyph']]).astype(float)
    shell = np.where(np.isin(mp, [MID['sera_white'], MID['sera_gold']]), np.clip((X - 2.3) / 1.0, 0, 1) * 0.7, 0)
    return np.maximum(hot, shell)


# ------------------------------------------------------------------ resources (32 px)
def item_seraphite():
    M = Model()
    for L, r, yaw, tilt in ((0.60, 0.14, 200, 48), (0.50, 0.12, 320, 56), (0.44, 0.11, 90, 58), (0.30, 0.10, 20, 28)):
        M.add('main', tf(crystal(L, r, tip=0.28, sides=5, taper=0.9), rz(yaw) @ rx(tilt), (0, -0.04, 0.04)), 'serite')
    M.add('main', tf(crystal(0.26, 0.06, tip=0.35), rz(150) @ rx(52), (0.02, -0.04, 0.10)), 'glyph')
    return M


def item_singularite():
    M = Model()
    for L, r, yaw, tilt in ((0.62, 0.13, 160, 50), (0.52, 0.12, 280, 56), (0.46, 0.11, 40, 58), (0.28, 0.10, 330, 25)):
        M.add('main', tf(crystal(L, r, tip=0.45, sides=4, taper=0.85), rz(yaw) @ rx(tilt), (0, -0.02, 0.04)), 'singul')
    M.add('main', tf(crystal(0.22, 0.05, tip=0.4), rz(220) @ rx(50), (0.0, -0.02, 0.10)), 'glyph')
    return M


def item_seraphimium():
    M = Model()
    for dx, dy, z0 in ((-0.05, -0.10, 0.0), (0.06, 0.10, 0.14)):
        R = rz(-25)
        M.add('main', tf(rslab(cham_rect(0.36, 0.16, 0.06), z0, z0 + 0.14, r=0.05), R, (dx, dy, 0)), 'sera_white')
        M.add('main', tf(cbox(0, 0, z0 + 0.145, 0.44, 0.05, 0.012), R, (dx, dy, 0)), 'glyph')
        for s in (-1, 1):
            M.add('main', tf(cbox(s * 0.31, 0, z0 + 0.075, 0.06, 0.33, 0.15), R, (dx, dy, 0)), 'sera_gold')
    return M


def item_singular_core():
    M = Model()
    T = rx(55) @ rz(15)
    M.add('main', sphereish((0, 0, 0.30), 0.20, n=14), 'void')
    M.add('main', tf(annulus(0.24, 0.38, -0.012, 0.012, n=40), T, (0, 0, 0.30)), 'glyph')
    torus(M, 'main', 0.43, 0.03, 0.30, 'sera_gold', n=40, k=6, Rm=rx(-35) @ rz(70))
    return M


def floor_ore(kind, v):
    """Floor ore overlay (drawn over the floor, transparent background): crystal clusters on dark rubble."""
    rng = np.random.default_rng(800 + 37 * v + (0 if kind == 'seraphite' else 400))
    mat, tip, sides = ('serite', 0.28, 5) if kind == 'seraphite' else ('singul', 0.45, 4)
    M = Model()
    spots = []
    want = (4, 3, 4)[v]
    for _ in range(500):
        if len(spots) == want:
            break
        x, y = rng.uniform(-0.30, 0.30, 2)
        if all((x - a) ** 2 + (y - b) ** 2 > 0.25 ** 2 for a, b in spots):
            spots.append((x, y))
    for x, y in spots:
        M.add('main', cyl((x, y, 0.0), (x, y, 0.03), 0.10, 0.08, n=7), 'sera_dark')
        k = int(rng.integers(2, 4))
        yaw0 = rng.uniform(0, 360)
        for j in range(k):
            L = rng.uniform(0.14, 0.21)
            M.add('main', tf(crystal(L, L * rng.uniform(0.38, 0.46), tip=tip, sides=sides, taper=0.9),
                             rz(yaw0 + 360 * j / k + rng.uniform(-25, 25)) @ rx(rng.uniform(25, 45)), (x, y, 0.02)), mat)
        if kind == 'singularite':
            M.add('main', tf(crystal(0.12, 0.035, tip=0.4), None, (x, y, 0.03)), 'glyph')
    return M


# ------------------------------------------------------------------ exporters
def tris(M):
    return f'{M.ntri():6d} tris'


def do_requiem():
    M = requiem()
    turret('requiem', M, 320, 480, heat=heat_requiem, parts=True)
    print(f'requiem             {tris(M)}  base 320 / body 480 px  muzzle y={SPEC6["requiem"]:.3f} -> shootY {SPEC6["requiem"] * 8:.1f}', flush=True)


def do_obelisk():
    M = obelisk()
    turret('obelisk', M, 256, 288, heat=heatmask({'glyph': 1.0, 'serite': 0.4}))
    print(f'obelisk             {tris(M)}  base 256 / body 288 px  emitter y={SPEC6["obelisk"]:.2f} -> shootY {SPEC6["obelisk"] * 8:.1f}', flush=True)


def do_net():
    M = seraphim_net()
    export_pd('seraphim-net', M, 192)
    print(f'seraphim-net        {tris(M)}  192 px', flush=True)


def do_chrono():
    M = chronofield()
    export_block('chronofield', M, 224, DEF, glow=heatmask({'glyph': 1.0, 'serite': 0.35}), glow_suffix='-top')
    print(f'chronofield         {tris(M)}  224 px', flush=True)


def do_dome():
    M = seraphim_dome()
    export_block('seraphim-dome', M, 288, DEF, glow=heatmask({'glyph': 1.0, 'serite': 0.5}), glow_suffix='-top', glow_tint='d8b8ff')
    print(f'seraphim-dome       {tris(M)}  288 px', flush=True)


def do_gravity():
    M = gravity_extractor()
    main, _ = layer(M, ['main'], 192)
    rot, _ = layer(M, ['rotator'], 192)
    top, _ = layer(M, ['top'], 192)
    save(main, DRL, 'gravity-extractor')
    save(rot, DRL, 'gravity-extractor-rotator')
    save(top, DRL, 'gravity-extractor-top')
    # @-item (mined-ore indicator, tinted with the ore colour): small white gem in the centre of the cap
    item = np.zeros((192, 192, 4), np.uint8)
    yy, xx = np.mgrid[0:192, 0:192]
    gem = (np.abs(xx - 95.5) + np.abs(yy - 95.5)) <= 6
    item[gem] = (255, 255, 255, 255)
    save(item, DRL, 'gravity-extractor-item')
    f = over(over(main, rot), top)
    save(f, DRL, 'gravity-extractor-full')
    FULL['gravity-extractor'] = np.asarray(f)
    print(f'gravity-extractor   {tris(M)}  192 px', flush=True)


def do_crafters():
    for name, fn, canvas, d, glow in (
            ('antimatter-trap', antimatter_trap, 160, CRA, {'anti': 1.0, 'glyph': 0.8, 'quantum': 0.5}),
            ('seraphite-refinery', seraphite_refinery, 192, CRA, {'glyph': 1.0, 'anti': 0.7, 'serite': 0.3}),
            ('singularity-collider', singularity_collider, 224, CRA, {'glyph': 1.0, 'anti': 0.8})):
        M = fn()
        export_block(name, M, canvas, d, glow=heatmask(glow))
        print(f'{name:20s}{tris(M)}  {canvas} px', flush=True)


def do_reactor():
    M = annihilation_reactor()
    main, hm = layer(M, ['main'], 224, heat=heatmask({'anti': 1.0, 'glyph': 0.8}))
    top, ht = layer(M, ['top'], 224, heat=heat_nozzle)
    save(main, PWR, 'annihilation-reactor')
    save(heat_sprite(hm), PWR, 'annihilation-reactor-glow')
    save(top, PWR, 'annihilation-reactor-top1')
    save(np.ascontiguousarray(top[::-1]), PWR, 'annihilation-reactor-top2')   # used for rotations 2-3
    save(heat_sprite(ht), PWR, 'annihilation-reactor-heat')
    f = over(main, top)
    save(f, PWR, 'annihilation-reactor-full')
    FULL['annihilation-reactor'] = np.asarray(f)
    print(f'annihilation-reactor{tris(M)}  224 px', flush=True)


def do_resources6():
    for d, name, M in (('items', 'seraphite', item_seraphite()), ('items', 'singularite', item_singularite()),
                       ('items', 'seraphimium', item_seraphimium()), ('items', 'singular-core', item_singular_core()),
                       ('liquids', 'antimatter', liquid_drop('anti_liq', 'anti'))):
        a = icon(M)
        save(a, d, name)
        FULL[name] = np.asarray(a)
        print(f'{d}/{name:22s}{tris(M)}', flush=True)
    for kind in ('seraphite', 'singularite'):
        for v in range(3):
            a, _ = layer(floor_ore(kind, v), ['main'], 32)
            save(a, 'blocks/ores', f'ore-{kind}{v + 1}')
            FULL[f'ore-{kind}{v + 1}'] = np.asarray(a)
        print(f'ore-{kind:18s} 3 variants', flush=True)


JOBS6 = {'requiem': do_requiem, 'obelisk': do_obelisk, 'seraphim-net': do_net, 'chronofield': do_chrono,
         'seraphim-dome': do_dome, 'gravity-extractor': do_gravity, 'crafters': do_crafters,
         'annihilation-reactor': do_reactor, 'resources': do_resources6}


def main6(only=()):
    for name, fn in JOBS6.items():
        if not only or name in only:
            fn()
    big = [k for k in ('requiem', 'obelisk', 'seraphim-net') if k in FULL]
    mid = [k for k in ('seraphim-dome', 'chronofield', 'annihilation-reactor', 'singularity-collider', 'seraphite-refinery',
                       'gravity-extractor', 'antimatter-trap') if k in FULL]
    small = [k for k in FULL if k not in big + mid]
    for keys, fn, sc in ((big, 'g_t6-turrets.png', 2), (mid, 'g_t6-blocks.png', 2), (small, 'g_t6-resources.png', 6)):
        if keys:
            print('sheet', qa_sheet(keys, fn, sc=sc, cols=min(len(keys), 4)))


if __name__ == '__main__':
    main6(sys.argv[1:])
