"""2.5.0-alpha3 art: T6 Seraphim tier ("inoplanetarium"): white hull, gold, violet glyphs, organic forms.

    .venv/bin/python tools/art/g_t6.py [job ...]

Writes every layer straight into mod/sprites with the names the content JSON expects and prints triangle counts.
Coordinates: 1.0 = one tile, Z up, origin = block centre, turret heads face +Y (BeamDrill heads face +X).
How v146 composes the layers:
  requiem / obelisk   DrawTurret: -base, body (+ -outline), requiem -barrel (+outline, +heat) recoils, obelisk -heat
  seraphim-net        PointDefenseTurret: -base + rotating head
  chronofield         MendProjector: main + -top (white, tinted with baseColor and pulsed)
  seraphim-dome       ForceProjector: main + -top (drawn untinted when hit, so it is pre-tinted violet)
  gravity-extractor   BeamDrill: main + -top (rotates, faces +X, one lens per tile row) + -glow
  crafters            DrawDefault + DrawGlowRegion (-glow)
  annihilation-reactor HeaterGenerator: main + -top1/-top2 (rotated, port on +X) + -heat (rotated) + -glow
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *  # noqa: E402,F401
from mats import Model  # noqa: E402
import rend  # noqa: E402
from rend import outline, heat_sprite, over  # noqa: E402
from export import save, layer, turret, FULL, qa_sheet  # noqa: E402
from g_t5 import (B, circ, sqc, inset, lofts, rslab, prof, dome, annulus, arc, torus, strip, arc_pts, crystal,  # noqa: E402
                  bipyr, leaf, node, channel, groove, inlay, rot2, heatmask, tint, export_pd, export_block, capsule,
                  icon, liquid_drop, P, TUR, DEF, CRA, PWR, DRL)

# ------------------------------------------------------------------ materials (append-only)
rend.add_material('sera_white', ['3a3844', '5c5a68', '87849a', 'b3b0c4', 'dcd9ea', 'f8f6ff'])        # pearl hull
rend.add_material('sera_gold', ['3b2a0c', '624614', '8f6a1f', 'bb912f', 'dfba4e', 'fbe58e'])         # gold trim
rend.add_material('sera_dark', ['0d0a14', '161120', '201a2e', '2b233c', '372d4c', '45395e'])         # violet-black recess
rend.add_material('glyph', ['5a2ea0', '7a44d0', '9a6af0', 'c49bff', 'e4c8ff', 'f8f0ff'], glow=True)  # Seraphim glyph light
rend.add_material('seraphite', ['3c3456', '5a5080', '8478ae', 'aea2d6', 'd6ccf2', 'f4f0ff'])         # pale violet crystal
rend.add_material('singul', ['08050f', '120c22', '1f1638', '30224f', '45336e', '5e4a94'])            # collapsed matter
rend.add_material('antimat', ['6a2a8a', '8c3cb0', 'b05ad6', 'd38cf0', 'ebbcff', 'fbeaff'], glow=True)
rend.add_material('antimat_l', ['3e1652', '5a2276', '7e349e', 'a050c4', 'c47ee0', 'e6b8f6'])          # antimatter (liquid icon)
rend.add_material('voidm', ['0a0716', '140f2a', '1f1840', '2c2358', '3e3274', '574a96'])             # void matter

W_, G_, D_, GL = 'sera_white', 'sera_gold', 'sera_dark', 'glyph'
SPEC = {}


def tris(M):
    return f'{M.ntri():6d} tris'


# ------------------------------------------------------------------ Seraphim kit
def snode(M, g, x, y, z, r=0.07, glow=GL):
    node(M, g, x, y, z, r=r, glow=glow, rim=G_)


def schannel(M, g, pts, z, w=0.07, glow=GL):
    channel(M, g, pts, z, w=w, glow=glow, bed=D_)


def sera_pad(M, g, h, z1=0.24, k=3.2, n=96):
    """Seraphim foundation: violet-black skirt, pearl slab with a soft bevel, gold rim, engraved inner border."""
    M.add(g, rslab(sqc(h * 0.99, n, k), 0.0, 0.10, r=0.04, steps=2), D_)
    M.add(g, rslab(sqc(h * 0.93, n, k), 0.08, z1, r=min(0.11, (z1 - 0.08) * 0.8), steps=3), W_)
    rim = sqc(h * 0.93 - 0.13, n, k)
    M.add(g, loft(ring(rim, z1 + 0.002), ring(inset(rim, 0.06), z1 + 0.002), False, False), G_)
    M.add(g, loft(ring(rim, z1 - 0.004), ring(rim, z1 + 0.002), False, False), G_)
    in2 = sqc(h * 0.93 - 0.30, n, k)
    M.add(g, loft(ring(in2, z1 + 0.003), ring(inset(in2, 0.03), z1 + 0.003), False, False), D_)
    return z1


def rune(M, g, cx, cy, z, s=0.22, rot=0.0, kind=0):
    """Seraphim glyph: arcs, strokes and dots cut into the hull and lit violet."""
    def R(pts):
        return rot2([(cx + 0 * 0, cy)], 0) and [(cx + x * c - y * sn, cy + x * sn + y * c) for x, y in pts]
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    w = s * 0.16
    if kind % 4 == 0:      # crescent over a stem
        schannel(M, g, R(arc_pts(s * 0.55, 200, 340, 7, 0, s * 0.25)), z, w=w)
        schannel(M, g, R([(0, s * 0.25), (0, -s * 0.6)]), z, w=w)
        snode(M, g, *R([(0, s * 0.75)])[0], z, r=w * 0.7)
    elif kind % 4 == 1:    # open eye
        schannel(M, g, R(arc_pts(s * 0.6, 20, 160, 7, 0, -s * 0.25)), z, w=w)
        schannel(M, g, R(arc_pts(s * 0.6, 200, 340, 7, 0, s * 0.25)), z, w=w)
        snode(M, g, *R([(0, 0)])[0], z, r=w * 0.8)
    elif kind % 4 == 2:    # forked strokes
        schannel(M, g, R([(0, -s * 0.6), (0, s * 0.1), (-s * 0.4, s * 0.55)]), z, w=w)
        schannel(M, g, R([(0, s * 0.1), (s * 0.4, s * 0.55)]), z, w=w)
        snode(M, g, *R([(-s * 0.45, -s * 0.35)])[0], z, r=w * 0.6)
        snode(M, g, *R([(s * 0.45, -s * 0.35)])[0], z, r=w * 0.6)
    else:                  # ring with a tail
        schannel(M, g, R(arc_pts(s * 0.38, 0, 330, 10, 0, s * 0.15)), z, w=w)
        schannel(M, g, R([(0, -s * 0.23), (0, -s * 0.7)]), z, w=w)


def blade(M, g, x, y, ang, L, w, z0, z1, mat=W_, trim=G_, line=True, back=0.0):
    """Organic fin: pearl leaf with a soft bevel, gold rim and a glyph vein along its spine."""
    lf = rot2(leaf(L, w, n=14, back=back), ang, (x, y))
    M.add(g, rslab(P(lf), z0, z1, r=min(0.05, (z1 - z0) * 0.7), steps=2), mat)
    M.add(g, loft(ring(inset(P(lf), 0.02), z1 + 0.002), ring(inset(P(lf), 0.06), z1 + 0.002), False, False), trim)
    if line:
        a = math.radians(ang)
        p0 = (x + math.cos(a) * (back + L * 0.15), y + math.sin(a) * (back + L * 0.15))
        p1 = (x + math.cos(a) * (back + L * 0.80), y + math.sin(a) * (back + L * 0.80))
        schannel(M, g, [p0, p1], z1, w=max(0.035, w * 0.18))


def spire(M, g, x, y, z, L, r, mat='seraphite', tip=GL, n=3, seed=0, plinth=0.30):
    """Crystal cluster on a gold-rimmed plinth: a tall central crystal and n tilted side crystals."""
    rng = np.random.default_rng(900 + seed)
    M.add(g, rslab(circ(plinth, 28, x, y), z - 0.02, z + 0.10, r=0.03), W_)
    M.add(g, annulus(plinth, plinth + 0.06, z - 0.02, z + 0.08, n=28, cx=x, cy=y), G_)
    M.add(g, tf(crystal(L, r, tip=0.32), rz(rng.uniform(0, 60)), (x, y, z + 0.08)), mat)
    M.add(g, tf(crystal(L * 0.55, r * 0.5, tip=0.35, phase=0.5), None, (x, y, z + 0.10 + L * 0.35)), tip)
    for j in range(n):
        a = 360 * j / n + rng.uniform(-20, 20)
        q = rz(a) @ np.array([r * 1.3, 0, 0])
        M.add(g, tf(crystal(L * rng.uniform(0.45, 0.6), r * 0.55, tip=0.4), rz(a) @ ry(rng.uniform(26, 38)),
                    (x + q[0], y + q[1], z + 0.08)), mat)


def halo_ring(M, g, R_, r, z, tilt=0.0, yaw=0.0, beads=0, glow=GL):
    Rm = rz(yaw) @ rx(tilt)
    torus(M, g, R_, r, z, G_, n=64, k=10, Rm=Rm)
    for i in range(beads):
        a = 2 * math.pi * (i + 0.5) / beads
        p = Rm @ np.array([R_ * math.cos(a), R_ * math.sin(a), 0.0]) + np.array([0.0, 0.0, z])
        M.add(g, sphereish(p, r * 1.4, n=8), glow)


def orb(M, g, x, y, z, r, mat=GL, rim=True):
    M.add(g, sphereish((x, y, z), r, n=20), mat)
    if rim:
        torus(M, g, r * 1.12, r * 0.12, z, G_, n=40, k=8, cx=x, cy=y)


def roots(M, g, angs, r0, L, w, z0, z1):
    for a in angs:
        p = rz(a) @ np.array([r0, 0, 0])
        blade(M, g, p[0], p[1], a, L, w, z0, z1)


# ================================================================== REQUIEM - T6 Seraphim artillery (10x10)
BARREL_X = [-1.25, 0.0, 1.25]   # ShootAlternate spread 10 world units
MUZZLE_Y = 7.25


def requiem():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 5.0, z1=0.26, k=3.0)
    M.add(g, annulus(3.10, 3.48, z1 - 0.02, z1 + 0.08, n=96), G_)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.01), 3.11, n=96), D_)
    torus(M, g, 3.29, 0.03, z1 + 0.09, GL, n=96, k=6)
    roots(M, g, [45, 135, 225, 315], 3.25, 1.75, 0.50, z1 - 0.02, z1 + 0.16)
    roots(M, g, [0, 90, 180, 270], 3.40, 1.05, 0.34, z1 - 0.02, z1 + 0.12)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([6.05, 0, 0])
        spire(M, g, p[0] * 0.70, p[1] * 0.70, z1, 0.95, 0.20, seed=k)
        for s in (-1, 1):
            q = rot2([(4.05, s * 1.75)], 90 * k)[0]
            rune(M, g, q[0], q[1], z1, s=0.30, rot=90 * k + 90, kind=k + (s > 0))
    # ---------------- body (rotates): teardrop hull with sweeping wing-blades
    g = 'body'
    zb = 0.34
    hull = mirror_half([(0, 3.10), (0.70, 2.90), (1.55, 2.10), (2.20, 0.90), (2.45, -0.40), (2.25, -1.90),
                        (1.55, -3.05), (0.70, -3.55), (0, -3.70)])
    M.add(g, prof(hull, [(0.0, zb), (0.0, zb + 0.30), (0.10, zb + 0.52), (0.28, zb + 0.68), (0.55, zb + 0.78)]), W_)
    top = zb + 0.78
    inner = inset(hull, 0.55)
    M.add(g, loft(ring(inset(inner, 0.0), top + 0.002), ring(inset(inner, 0.07), top + 0.002), False, False), G_)
    # spine ridge with glyph vein
    sp = P([(0, 2.70), (0.30, 1.80), (0.36, -1.40), (0.22, -2.80), (0, -3.10), (-0.22, -2.80), (-0.36, -1.40), (-0.30, 1.80)])
    M.add(g, rslab(sp, top - 0.02, top + 0.20, r=0.08), G_)
    schannel(M, g, [(0, 2.30), (0, -2.60)], top + 0.20, w=0.08)
    # wing blades sweeping back from the shoulders
    for s in (-1, 1):
        blade(M, g, s * 1.70, 1.10, 90 - s * 128, 2.80, 0.55, zb + 0.10, zb + 0.62)
        blade(M, g, s * 2.10, -0.60, 90 - s * 150, 2.30, 0.42, zb + 0.06, zb + 0.50)
        blade(M, g, s * 1.10, -2.60, 90 - s * 165, 1.40, 0.30, top - 0.10, top + 0.06, line=False)
        for i, y in enumerate((1.6, 0.2, -1.2)):
            rune(M, g, s * 1.15, y, top, s=0.30, rot=0, kind=i + (s > 0) * 2)
        snode(M, g, s * 1.95, -1.30, zb + 0.70, r=0.07)
        snode(M, g, s * 1.60, 2.20, zb + 0.70, r=0.06)
    # rear core: gold ring + violet orb + crystal crown
    orb(M, g, 0, -2.25, top + 0.22, 0.42)
    halo_ring(M, g, 0.62, 0.05, top + 0.18, tilt=0, beads=6)
    for j in range(3):
        a = 90 + 120 * j
        q = rz(a) @ np.array([0.70, 0, 0])
        M.add(g, tf(crystal(0.55, 0.10, tip=0.4), rz(a) @ ry(-35), (q[0], -2.25 + q[1], top + 0.10)), 'seraphite')
    # front collar the barrels sit in
    M.add(g, rslab(cham_rect(2.05, 0.36, 0.22, cy=2.55), top - 0.10, top + 0.24, r=0.08), W_)
    M.add(g, B(-1.95, 1.95, 2.48, 2.62, top + 0.24, top + 0.27), G_)
    # ---------------- barrels (recoil): three tapered prongs with glyph veins and claw crowns
    g = 'barrel'
    zc = top + 0.30
    for bx in BARREL_X:
        M.add(g, cyl((bx, 2.20, zc), (bx, 3.40, zc), 0.44, 0.42, n=24), W_)
        M.add(g, cyl((bx, 3.40, zc), (bx, 3.56, zc), 0.47, n=24), G_)
        M.add(g, cyl((bx, 3.56, zc), (bx, 6.55, zc), 0.33, 0.25, n=24), W_)
        for y in (4.55, 5.70):
            M.add(g, cyl((bx, y, zc), (bx, y + 0.12, zc), 0.34 - (y - 3.5) * 0.025, n=24), G_)
        M.add(g, strip([(bx, 3.70), (bx, 6.40)], 0.07, zc + 0.24, zc + 0.30), D_)
        M.add(g, strip([(bx, 3.70), (bx, 6.40)], 0.035, zc + 0.24, zc + 0.315), GL)
        # crown: three claws around a glowing muzzle orb
        M.add(g, cyl((bx, 6.55, zc), (bx, 6.75, zc), 0.30, 0.34, n=24), G_)
        for a in (-90, 30, 150):
            q = (bx + 0.24 * math.cos(math.radians(a)), zc + 0.24 * math.sin(math.radians(a)))
            M.add(g, tf(prism(P(leaf(0.62, 0.11, n=10)), -0.04, 0.04), rz(90), (q[0], 6.62, q[1])), W_)
        M.add(g, sphereish((bx, 6.95, zc), 0.17, n=16), GL)
    M.add(g, B(-1.30, 1.30, 2.95, 3.15, zc + 0.10, zc + 0.36), G_)
    M.add(g, B(-1.30, 1.30, 5.05, 5.18, zc + 0.02, zc + 0.20), D_)
    SPEC['requiem'] = MUZZLE_Y
    return M


def heat_requiem(mp, X, Y, g):
    return heatmask({GL: 1.0, 'seraphite': 0.35}, ymin=2.0)(mp, X, Y, g)


# ================================================================== OBELISK - T6 Seraphim beam tower (8x8)
def obelisk():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 4.0, z1=0.24, k=3.0)
    M.add(g, annulus(2.45, 2.78, z1 - 0.02, z1 + 0.07, n=80), G_)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.01), 2.46, n=80), D_)
    torus(M, g, 2.62, 0.025, z1 + 0.08, GL, n=80, k=6)
    roots(M, g, [45, 135, 225, 315], 2.60, 1.30, 0.40, z1 - 0.02, z1 + 0.14)
    for k in range(4):
        q = rot2([(3.20, 0)], 90 * k)[0]
        rune(M, g, q[0], q[1], z1, s=0.32, rot=90 * k + 90, kind=k)
    g = 'body'
    zb = 0.30
    pil = mirror_half([(0, 3.10), (0.80, 1.90), (1.22, 0.10), (1.05, -1.80), (0.55, -2.70), (0, -2.95)])
    M.add(g, prof(pil, [(0.0, zb), (0.0, zb + 0.70), (0.18, zb + 1.10), (0.42, zb + 1.35), (0.62, zb + 1.45)]), W_)
    top = zb + 1.45
    # gold edge ribs running up the facets
    for s in (-1, 1):
        inlay(M, g, [(s * 0.10, 2.70), (s * 0.66, 1.62), (s * 1.02, 0.10), (s * 0.88, -1.55), (s * 0.46, -2.42)], zb + 0.95, w=0.06, h=0.03)
        blade(M, g, s * 1.05, -0.40, 90 - s * 115, 1.90, 0.40, zb + 0.20, zb + 0.75)
        blade(M, g, s * 0.95, 1.10, 90 - s * 70, 1.10, 0.26, zb + 0.20, zb + 0.60, line=False)
        snode(M, g, s * 0.55, -1.70, top, r=0.06)
    schannel(M, g, [(0, -2.10), (0, 2.20)], top, w=0.12)
    for i, y in enumerate((-1.20, 0.10, 1.30)):
        rune(M, g, 0, y, top + 0.004, s=0.34, kind=i + 1)
    # emitter crystal along +Y in gold clamps
    M.add(g, tf(crystal(1.55, 0.30, tip=0.30), rx(-90), (0, 2.75, top - 0.25)), 'seraphite')
    M.add(g, tf(crystal(1.20, 0.15, tip=0.35, phase=0.5), rx(-90), (0, 2.95, top - 0.18)), GL)
    for y in (2.95, 3.40):
        M.add(g, cyl((0, y, top - 0.25), (0, y + 0.10, top - 0.25), 0.36 - (y - 2.95) * 0.12, n=20), G_)
    # rear counterweight orb
    orb(M, g, 0, -2.35, top - 0.05, 0.32)
    SPEC['obelisk'] = 2.75 + 1.55
    return M


# ================================================================== SERAPHIM NET - T6 counter-battery (6x6)
def seraphim_net():
    M = Model()
    g = 'base'
    z1 = sera_pad(M, g, 3.0, z1=0.22, k=3.0)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.01), 1.45, n=64), D_)
    M.add(g, annulus(1.45, 1.62, z1 - 0.02, z1 + 0.07, n=64), G_)
    pts = [rot2([(2.25, 0)], 30 + 60 * i)[0] for i in range(6)]
    for i in range(6):          # hexagram web between the pylons
        schannel(M, g, [pts[i], pts[(i + 2) % 6]], z1 + 0.003, w=0.06)
    torus(M, g, 2.25, 0.05, z1 + 0.10, G_, n=72, k=8)
    for i, p in enumerate(pts):
        spire(M, g, p[0], p[1], z1, 0.80, 0.15, n=2, seed=10 + i, plinth=0.26)
    for k in range(4):
        q = rot2([(2.62, 0)], 90 * k)[0]
        snode(M, g, q[0], q[1], z1, r=0.07)
    g = 'head'
    zh = 0.30
    M.add(g, cyl((0, 0, zh - 0.05), (0, 0, zh + 0.10), 1.25, 1.18, n=64), W_)
    torus(M, g, 1.20, 0.05, zh + 0.10, G_, n=64, k=8)
    tail = mirror_half([(0, 0.6), (0.55, 0.4), (0.62, -0.6), (0.30, -1.55), (0, -1.75)])
    M.add(g, rslab(tail, zh + 0.10, zh + 0.36, r=0.08), W_)
    schannel(M, g, [(0, -0.4), (0, -1.40)], zh + 0.36, w=0.07)
    for s in (-1, 0, 1):        # three-pronged claw aiming +Y
        L = 2.15 if s == 0 else 1.55
        ang = 90 - s * 22
        blade(M, g, s * 0.34, 0.45, ang, L, 0.30 if s == 0 else 0.24, zh + 0.18, zh + 0.52)
        a = math.radians(ang)
        tip = (s * 0.34 + math.cos(a) * L * 0.92, 0.45 + math.sin(a) * L * 0.92)
        M.add(g, sphereish((tip[0], tip[1], zh + 0.50), 0.09, n=10), GL)
    orb(M, g, 0, 0.10, zh + 0.62, 0.48)
    halo_ring(M, g, 0.70, 0.05, zh + 0.52, tilt=58, beads=6)
    return M


# ================================================================== CHRONOFIELD - T6 time-dilation field (7x7)
def chronofield():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.5, z1=0.22, k=4.0)
    M.add(g, rslab(circ(3.05, 96), z1 - 0.02, z1 + 0.10, r=0.05), W_)
    zd = z1 + 0.10
    M.add(g, annulus(2.92, 3.05, zd - 0.01, zd + 0.03, n=96), G_)
    M.add(g, cyl((0, 0, zd - 0.01), (0, 0, zd + 0.005), 2.30, n=96), D_)
    for i in range(12):         # hour marks
        L0, L1 = (2.32, 2.86) if i % 3 == 0 else (2.48, 2.80)
        q = rot2([(L0, 0), (L1, 0)], 90 - 30 * i)
        schannel(M, g, q, zd, w=0.10 if i % 3 == 0 else 0.06)
    for i in range(60):
        if i % 5:
            q = rot2([(2.72, 0)], 90 - 6 * i)[0]
            M.add(g, cyl((q[0], q[1], zd), (q[0], q[1], zd + 0.02), 0.022, n=6), G_)
    torus(M, g, 1.62, 0.04, zd + 0.02, G_, n=80, k=8)
    torus(M, g, 1.10, 0.025, zd + 0.02, GL, n=64, k=6)
    for k in range(4):
        q = rot2([(1.95, 0)], 45 + 90 * k)[0]
        rune(M, g, q[0], q[1], zd, s=0.26, rot=45 + 90 * k - 90, kind=k)
    # clock hands
    blade(M, g, 0, 0, 60, 2.05, 0.20, zd + 0.30, zd + 0.38, mat=G_, trim=G_, line=False)
    blade(M, g, 0, 0, 205, 1.35, 0.24, zd + 0.40, zd + 0.48, mat=G_, trim=G_, line=False)
    # floating time crystal in crossed gimbals
    M.add(g, cyl((0, 0, zd), (0, 0, zd + 0.30), 0.32, 0.22, n=24), G_)
    M.add(g, bipyr(6, 0.42, zd + 0.30, zd + 0.70, zd + 1.20), 'seraphite')
    M.add(g, bipyr(6, 0.20, zd + 0.45, zd + 0.72, zd + 1.25, rot=30), GL)
    halo_ring(M, g, 0.78, 0.045, zd + 0.70, tilt=64, yaw=20, beads=6)
    halo_ring(M, g, 0.78, 0.045, zd + 0.70, tilt=64, yaw=110, beads=6)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([4.55, 0, 0])
        spire(M, g, p[0] * 0.70, p[1] * 0.70, z1, 0.55, 0.13, n=2, seed=20 + k, plinth=0.22)
    return M


# ================================================================== SERAPHIM DOME - T6 shield (9x9)
def seraphim_dome():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 4.5, z1=0.24, k=3.4)
    for i in range(6):          # petals around the dome
        a = 90 + 60 * i
        blade(M, g, *rot2([(2.55, 0)], a)[0], a, 1.75, 0.62, z1 - 0.02, z1 + 0.20)
    for i in range(6):
        a = 60 * i
        q = rot2([(3.55, 0)], a)[0]
        snode(M, g, q[0], q[1], z1, r=0.08)
    M.add(g, annulus(2.25, 2.62, z1 - 0.02, z1 + 0.16, n=96, zi=z1 + 0.10), G_)
    zd = z1 + 0.12
    M.add(g, dome(0, 0, zd, 2.28, 1.30, n=72, lat=9), W_)
    for k, (rr, zz) in enumerate(((2.02, 0.48), (1.62, 0.86), (1.05, 1.15))):
        torus(M, g, rr, 0.045, zd + zz, GL if k != 1 else G_, n=72, k=8)
    for i in range(6):          # gold meridian ribs
        a = math.radians(30 + 60 * i)
        pts = []
        for t in np.linspace(0.05, 0.92, 9):
            th = t * math.pi / 2
            pts.append(np.array([2.30 * math.cos(th) * math.cos(a), 2.30 * math.cos(th) * math.sin(a), zd + 1.32 * math.sin(th)]))
        for p0, p1 in zip(pts[:-1], pts[1:]):
            M.add(g, cyl(p0, p1, 0.05, n=8), G_)
    spire(M, g, 0, 0, zd + 1.25, 0.70, 0.17, n=3, seed=31, plinth=0.32)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([5.75, 0, 0])
        spire(M, g, p[0] * 0.70, p[1] * 0.70, z1, 0.75, 0.16, n=2, seed=40 + k)
        q = rot2([(3.70, 0)], 90 * k + 30)[0]
        rune(M, g, q[0], q[1], z1, s=0.30, rot=90 * k + 120, kind=k)
    return M


# ================================================================== GRAVITATIONAL EXTRACTOR - T6 beam drill (6x6)
def gravity_extractor():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.0, z1=0.20, k=3.4)
    M.add(g, annulus(2.10, 2.38, z1 - 0.02, z1 + 0.06, n=80), G_)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.02), 2.10, n=80), D_)
    torus(M, g, 2.24, 0.022, z1 + 0.065, GL, n=80, k=6)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([3.62, 0, 0])
        spire(M, g, p[0] * 0.72, p[1] * 0.72, z1, 0.50, 0.12, n=2, seed=50 + k, plinth=0.22)
    g = 'top'
    zt = z1 + 0.06
    M.add(g, cyl((0, 0, zt - 0.04), (0, 0, zt + 0.08), 2.00, 1.94, n=80), W_)
    hull = P([(2.10, 1.90), (1.20, 1.85), (-0.40, 1.55), (-1.55, 0.95), (-1.85, 0.0),
              (-1.55, -0.95), (-0.40, -1.55), (1.20, -1.85), (2.10, -1.90)])
    M.add(g, prof(hull, [(0.0, zt), (0.0, zt + 0.12), (0.06, zt + 0.22), (0.16, zt + 0.30), (0.30, zt + 0.34)]), W_)
    hz = zt + 0.34
    # emitter bar on +X with one lens per tile row
    M.add(g, rslab(cham_rect(0.32, 2.88, 0.16, cx=2.42), zt, zt + 0.40, r=0.08), W_)
    M.add(g, prism(cham_rect(0.08, 2.76, 0.05, cx=2.72), zt + 0.04, zt + 0.36, 0.95), G_)
    for y in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):
        M.add(g, cyl((2.30, y, zt + 0.26), (2.86, y, zt + 0.26), 0.17, n=18), G_)
        M.add(g, cyl((2.86, y, zt + 0.26), (2.93, y, zt + 0.26), 0.12, n=16), GL)
        snode(M, g, 2.18, y, zt + 0.40, r=0.05)
        schannel(M, g, [(1.95, y * 0.55), (2.18, y)], hz, w=0.05)
    # gravity lens: singularity in a gold ring with a glowing accretion disk
    M.add(g, annulus(0.95, 1.30, hz - 0.02, hz + 0.10, n=72), G_)
    M.add(g, cyl((0, 0, hz - 0.02), (0, 0, hz + 0.01), 0.96, n=72), D_)
    M.add(g, tf(annulus(0.48, 0.86, -0.012, 0.012, n=64), rx(16), (0, 0, hz + 0.22)), 'antimat')
    M.add(g, sphereish((0, 0, hz + 0.24), 0.42, n=24), 'singul')
    halo_ring(M, g, 1.10, 0.045, hz + 0.30, tilt=24, yaw=90, beads=8)
    for s in (-1, 1):
        rune(M, g, -1.05, s * 0.95, hz - 0.01, s=0.28, rot=0, kind=1 + (s > 0))
        for x in (-1.20, -0.80, -0.40, 0.0, 0.40, 0.80):
            fin = P([(x - 0.12, s * 1.55), (x + 0.12, s * 1.55), (x + 0.08, s * 1.95), (x - 0.08, s * 1.95)])
            M.add(g, prism(fin, zt + 0.04, zt + 0.24, 0.9), G_ if x == 0.0 else W_)
    return M


# ================================================================== ANTIMATTER TRAP (5x5)
def antimatter_trap():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 2.5, z1=0.22, k=3.6)
    M.add(g, annulus(1.20, 1.45, z1 - 0.02, z1 + 0.10, n=72, zi=z1 + 0.05), W_)
    M.add(g, annulus(1.45, 1.55, z1 - 0.02, z1 + 0.09, n=72), G_)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.0), 1.21, n=72), D_)
    for i in range(8):
        schannel(M, g, rot2([(0.62, 0), (1.12, 0)], 22.5 + 45 * i), z1, w=0.05)
    M.add(g, sphereish((0, 0, z1 + 0.62), 0.40, n=24), 'antimat')
    halo_ring(M, g, 0.66, 0.05, z1 + 0.62, tilt=70, yaw=0, beads=5)
    halo_ring(M, g, 0.80, 0.05, z1 + 0.62, tilt=70, yaw=60, beads=5)
    halo_ring(M, g, 0.94, 0.05, z1 + 0.62, tilt=70, yaw=120, beads=5)
    for k in range(4):          # condensate intake cells on the sides, piped to the bottle
        T = 90 * k
        p0, p1 = rot2([(-0.62, -1.92), (0.62, -1.92)], T)
        capsule(M, g, (p0[0], p0[1], z1 + 0.20), (p1[0], p1[1], z1 + 0.20), 0.18, 'qcond', band=G_, cap=W_)
        schannel(M, g, rot2([(0, -1.70), (0, -1.50)], T), z1, w=0.06)
        q = rot2([(1.98, 1.98)], T)[0]
        snode(M, g, q[0], q[1], z1, r=0.08)
    return M


# ================================================================== SERAPHITE PURIFIER (6x6)
def sera_hopper(M, g, cx, cy, hx, hy, z1, mat, seed, cubes=False):
    M.add(g, rslab(cham_rect(hx, hy, 0.08, cx=cx, cy=cy), z1 - 0.02, z1 + 0.16, r=0.05), W_)
    M.add(g, B(cx - hx + 0.08, cx + hx - 0.08, cy - hy + 0.08, cy + hy - 0.08, z1 + 0.10, z1 + 0.165), D_)
    rng = np.random.default_rng(seed)
    for _ in range(int(hx * hy * 55) + 3):
        x = cx + rng.uniform(-hx + 0.14, hx - 0.14)
        y = cy + rng.uniform(-hy + 0.13, hy - 0.13)
        if cubes:
            M.add(g, tf(cbox(0, 0, 0, 0.09, 0.09, 0.09), rz(rng.uniform(0, 90)), (x, y, z1 + 0.20)), mat)
        else:
            M.add(g, bipyr(5, 0.065, z1 + 0.12, z1 + 0.16, z1 + 0.26, cx=x, cy=y, rot=rng.uniform(0, 72)), mat)


def seraphite_purifier():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.0, z1=0.22, k=3.4)
    hexo = [rot2([(1.85, 0)], 60 * i)[0] for i in range(6)]
    M.add(g, rslab(P(hexo), z1 - 0.02, z1 + 0.18, r=0.06), W_)
    M.add(g, rslab(P([rot2([(1.55, 0)], 60 * i)[0] for i in range(6)]), z1 + 0.10, z1 + 0.19, r=0.02), G_)
    M.add(g, rslab(P([rot2([(1.42, 0)], 60 * i)[0] for i in range(6)]), z1 + 0.12, z1 + 0.20, r=0.02), D_)
    M.add(g, cyl((0, 0, z1 + 0.19), (0, 0, z1 + 0.205), 1.05, n=48), 'antimat')
    rng = np.random.default_rng(61)
    for j in range(5):          # purified crystals growing from the pool
        a = 72 * j + 15
        r = 0.0 if j == 0 else 0.62
        q = rot2([(r, 0)], a)[0]
        L = 1.25 if j == 0 else rng.uniform(0.60, 0.85)
        R = None if j == 0 else rz(a) @ ry(24)
        M.add(g, tf(crystal(L, 0.22 if j == 0 else 0.14, tip=0.30), R, (q[0], q[1], z1 + 0.18)), 'seraphite')
    M.add(g, tf(crystal(0.85, 0.10, tip=0.35, phase=0.5), None, (0, 0, z1 + 0.45)), GL)
    for i in range(3):          # gold lattice arches over the basin
        torus(M, g, 1.35, 0.045, z1 + 0.20, G_, n=40, k=8, a0=0, a1=180, Rm=rz(60 * i) @ rx(90))
    for i in range(6):
        schannel(M, g, [hexo[i], hexo[(i + 1) % 6]], z1 + 0.18, w=0.05)
    sera_hopper(M, g, -2.15, 1.40, 0.40, 0.70, z1, 'seraphite', 62)
    sera_hopper(M, g, -2.15, -1.40, 0.40, 0.70, z1, 'quantum', 63, cubes=True)
    for s in (-1, 1):
        M.add(g, cyl((2.25, s * 1.30, z1 - 0.02), (2.25, s * 1.30, z1 + 0.36), 0.36, 0.32, n=28), W_)
        M.add(g, cyl((2.25, s * 1.30, z1 + 0.36), (2.25, s * 1.30, z1 + 0.40), 0.30, n=28), 'antimat')
        snode(M, g, 2.25, s * 1.30, z1 + 0.40, r=0.07)
        schannel(M, g, [(1.95, s * 1.20), (1.55, s * 0.80)], z1, w=0.06)
        rune(M, g, s * 0.4, -2.55, z1, s=0.26, kind=s + 1)
    return M


# ================================================================== SINGULARITY COLLIDER (7x7)
def singularity_collider():
    M = Model()
    g = 'main'
    z1 = sera_pad(M, g, 3.5, z1=0.22, k=3.6)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.01), 2.20, n=96), D_)
    torus(M, g, 2.55, 0.30, z1 + 0.26, W_, n=96, k=16)
    for i in range(12):         # magnet segments and glyph beads around the accelerator ring
        a = math.radians(30 * i)
        c = np.array([2.55 * math.cos(a), 2.55 * math.sin(a), z1 + 0.26])
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        M.add(g, cyl(c - t * 0.10, c + t * 0.10, 0.36, n=20), G_)
        b = np.array([2.55 * math.cos(a + math.pi / 12), 2.55 * math.sin(a + math.pi / 12), z1 + 0.56])
        M.add(g, sphereish(b, 0.07, n=8), GL)
    for k in range(4):          # spokes to the core
        a = 45 + 90 * k
        p0, p1 = rot2([(0.95, 0), (2.30, 0)], a)
        M.add(g, cyl((p0[0], p0[1], z1 + 0.20), (p1[0], p1[1], z1 + 0.24), 0.08, n=10), G_)
        snode(M, g, *rot2([(1.62, 0)], a)[0], z1 + 0.30, r=0.06)
    M.add(g, tf(annulus(0.62, 1.10, -0.012, 0.012, n=72), rx(18), (0, 0, z1 + 0.62)), 'antimat')
    M.add(g, sphereish((0, 0, z1 + 0.64), 0.55, n=28), 'singul')
    halo_ring(M, g, 0.74, 0.04, z1 + 0.64, tilt=78, yaw=0, beads=0)
    for k in range(4):
        a = 45 + 90 * k
        p = rz(a) @ np.array([4.60, 0, 0])
        spire(M, g, p[0] * 0.70, p[1] * 0.70, z1, 0.55, 0.13, n=2, seed=70 + k, plinth=0.22)
        q = rot2([(3.10, 0)], 90 * k)[0]
        rune(M, g, q[0], q[1], z1, s=0.28, rot=90 * k + 90, kind=k)
    return M


# ================================================================== ANNIHILATION REACTOR (7x7, HeaterGenerator)
def annihilation_reactor():
    M = Model()
    g = 'main'
    z1 = 0.24
    M.add(g, rslab(cham_rect(3.46, 3.46, 1.05), 0.0, 0.10, r=0.04, steps=2), D_)
    M.add(g, rslab(cham_rect(3.25, 3.25, 1.00), 0.08, z1, r=0.10), W_)
    oc = cham_rect(3.08, 3.08, 0.94)
    M.add(g, loft(ring(oc, z1 + 0.002), ring(inset(oc, 0.06), z1 + 0.002), False, False), G_)
    M.add(g, annulus(1.55, 1.95, z1 - 0.02, z1 + 0.22, n=80, zi=z1 + 0.12), W_)
    M.add(g, annulus(1.95, 2.05, z1 - 0.02, z1 + 0.20, n=80), G_)
    M.add(g, cyl((0, 0, z1 - 0.02), (0, 0, z1 + 0.04), 1.56, n=80), D_)
    for i in range(16):
        schannel(M, g, rot2([(1.62, 0), (1.90, 0)], 11.25 + 22.5 * i), z1 + 0.17, w=0.04)
    M.add(g, sphereish((0, 0, z1 + 0.62), 0.62, n=28), 'antimat')
    halo_ring(M, g, 0.92, 0.07, z1 + 0.62, tilt=68, yaw=30, beads=6)
    halo_ring(M, g, 1.08, 0.07, z1 + 0.62, tilt=68, yaw=120, beads=6)
    torus(M, g, 1.30, 0.05, z1 + 0.30, G_, n=72, k=8)
    for k in range(4):          # radiator wings on the diagonals
        a = 45 + 90 * k
        blade(M, g, *rot2([(1.85, 0)], a)[0], a, 1.75, 0.55, z1 - 0.02, z1 + 0.26)
        for j in (-1, 1):
            fp = rot2([(2.40, j * 0.42), (3.00, j * 0.30)], a)
            M.add(g, strip(fp, 0.08, z1 + 0.26, z1 + 0.30), 'heat')
    for k in range(4):
        q = rot2([(2.55, 0)], 90 * k + 90)[0]
        rune(M, g, q[0], q[1], z1, s=0.30, rot=90 * k + 180, kind=k)
    # ---------------- -top1: heat port facing +X (rotated with the block)
    g = 'top'
    M.add(g, rslab(cham_rect(0.48, 1.30, 0.22, cx=2.80), z1, z1 + 0.30, r=0.08), W_)
    M.add(g, rslab(cham_rect(0.30, 1.08, 0.16, cx=2.96), z1 + 0.22, z1 + 0.40, r=0.05), G_)
    for y in (-0.72, -0.36, 0.0, 0.36, 0.72):
        M.add(g, B(2.74, 3.28, y - 0.10, y + 0.10, z1 + 0.40, z1 + 0.43), 'heat')
        M.add(g, B(2.74, 3.28, y + 0.10, y + 0.16, z1 + 0.40, z1 + 0.46), G_)
    snode(M, g, 2.48, 0, z1 + 0.30, r=0.07)
    return M


# ================================================================== resources
def item_seraphite():
    M = Model()
    g = 'main'
    for (x, y, L, r, yaw, tilt) in ((0.0, 0.0, 0.62, 0.15, 0, 0), (-0.13, -0.06, 0.40, 0.10, 200, 34), (0.14, -0.04, 0.44, 0.11, 330, 30)):
        M.add(g, tf(crystal(L, r, tip=0.32), rz(yaw) @ ry(tilt) @ rx(-25), (x, y - 0.10, 0.10)), 'seraphite')
    M.add(g, tf(crystal(0.36, 0.05, tip=0.4), rx(-25), (0, -0.05, 0.16)), GL)
    return M


def item_seraphimium():
    M = Model()
    g = 'main'
    hx = mirror_half([(0, 0.30), (0.20, 0.22), (0.30, 0.0), (0.20, -0.22), (0, -0.30)])
    R = rz(35)
    M.add(g, tf(prism(hx, 0.0, 0.16, 0.78), R), W_)
    M.add(g, tf(prism(scale_poly(hx, 0.78, (0, 0)), 0.16, 0.19, 0.9), R), G_)
    M.add(g, tf(strip([(0, -0.16), (0, 0.16)], 0.05, 0.19, 0.205), R), GL)
    return M


def item_singularite():
    M = Model()
    g = 'main'
    M.add(g, tf(bipyr(5, 0.24, 0.0, 0.18, 0.62, rot=15), rx(-30), (0, -0.12, 0.05)), 'singul')
    M.add(g, tf(bipyr(5, 0.10, 0.10, 0.22, 0.48, rot=51), rx(-30), (0, -0.12, 0.10)), GL)
    M.add(g, tf(bipyr(4, 0.12, 0.0, 0.10, 0.30, rot=0), rz(150) @ ry(40), (-0.16, -0.10, 0.04)), 'singul')
    return M


def item_singularity_core():
    M = Model()
    g = 'main'
    M.add(g, tf(annulus(0.20, 0.33, -0.015, 0.015, n=40), rx(62) @ rz(0), (0, 0, 0.30)), 'antimat')
    M.add(g, sphereish((0, 0, 0.30), 0.17, n=16), 'singul')
    torus(M, g, 0.30, 0.03, 0.30, G_, n=40, k=6, Rm=rz(90) @ rx(90))
    return M


def wall_ore(kind, v):
    """Crystals growing out of a rock face (drawn over static walls): crystals only, transparent background."""
    rng = np.random.default_rng(1700 + 37 * v + (0 if kind == 'seraphite' else 400))
    mat, tip = ('seraphite', 0.30) if kind == 'seraphite' else ('singul', 0.22)
    M = Model()
    g = 'main'
    spots = []
    want = (3, 4, 3)[v]
    for _ in range(400):
        if len(spots) == want:
            break
        x, y = rng.uniform(-0.22, 0.22, 2)
        if all((x - a) ** 2 + (y - b) ** 2 > 0.24 ** 2 for a, b in spots):
            spots.append((x, y))
    for x, y in spots:
        M.add(g, cyl((x, y, -0.02), (x, y, 0.03), 0.11, 0.09, n=8), D_)
        k = int(rng.integers(2, 4))
        yaw0 = rng.uniform(0, 360)
        for j in range(k):
            L = rng.uniform(0.16, 0.24)
            yaw = yaw0 + 360 * j / k + rng.uniform(-25, 25)
            M.add(g, tf(crystal(L, L * rng.uniform(0.40, 0.48), tip=tip, taper=0.9), rz(yaw) @ rx(rng.uniform(22, 42)), (x, y, 0.0)), mat)
        M.add(g, tf(crystal(0.15, 0.045, tip=0.4), None, (x, y, 0.02)), GL)
    return M


# ================================================================== exporters
def do_requiem():
    M = requiem()
    turret('requiem', M, 320, 512, heat=heat_requiem, parts=True)
    print(f'requiem            {tris(M)}  base 320 / body 512 px  muzzle y={SPEC["requiem"]:.2f} -> shootY {SPEC["requiem"] * 8:.1f}', flush=True)


def do_obelisk():
    M = obelisk()
    turret('obelisk', M, 256, 320, heat=heatmask({GL: 1.0, 'seraphite': 0.5}))
    print(f'obelisk            {tris(M)}  base 256 / body 320 px  emitter y={SPEC["obelisk"]:.2f} -> shootY {SPEC["obelisk"] * 8:.1f}', flush=True)


def do_net():
    M = seraphim_net()
    export_pd('seraphim-net', M, 192)
    print(f'seraphim-net       {tris(M)}  192 px', flush=True)


def do_chrono():
    M = chronofield()
    export_block('chronofield', M, 224, DEF, glow=heatmask({GL: 1.0, 'seraphite': 0.6}), glow_suffix='-top')
    print(f'chronofield        {tris(M)}  224 px', flush=True)


def do_dome():
    M = seraphim_dome()
    export_block('seraphim-dome', M, 288, DEF, glow=heatmask({GL: 1.0, 'seraphite': 0.5, W_: 0.12}), glow_suffix='-top', glow_tint='d8bcff')
    print(f'seraphim-dome      {tris(M)}  288 px', flush=True)


def do_extractor():
    M = gravity_extractor()
    main, _ = layer(M, ['main'], 192)
    top, hm = layer(M, ['top'], 192, heat=heatmask({GL: 1.0, 'antimat': 1.0}))
    top = outline(top, r=2)
    save(main, DRL, 'gravity-extractor')
    save(top, DRL, 'gravity-extractor-top')
    save(heat_sprite(hm), DRL, 'gravity-extractor-glow')
    f = over(main, top)
    save(f, DRL, 'gravity-extractor-full')
    FULL['gravity-extractor'] = np.asarray(f)
    print(f'gravity-extractor  {tris(M)}  192 px', flush=True)


def do_crafters():
    for name, fn, canvas in (('antimatter-trap', antimatter_trap, 160), ('seraphite-purifier', seraphite_purifier, 192),
                             ('singularity-collider', singularity_collider, 224)):
        M = fn()
        export_block(name, M, canvas, CRA, glow=heatmask({GL: 1.0, 'antimat': 1.0, 'seraphite': 0.35}))
        print(f'{name:19s}{tris(M)}  {canvas} px', flush=True)


def do_reactor():
    M = annihilation_reactor()
    main, hg = layer(M, ['main'], 224, heat=heatmask({'antimat': 1.0, GL: 0.9, 'heat': 0.6}), casters=['main'])
    top, ht = layer(M, ['top'], 224, heat=heatmask({'heat': 1.0}), casters=['top'])
    save(main, PWR, 'annihilation-reactor')
    save(heat_sprite(hg), PWR, 'annihilation-reactor-glow')
    save(top, PWR, 'annihilation-reactor-top1')
    save(np.ascontiguousarray(np.asarray(top)[::-1]), PWR, 'annihilation-reactor-top2')
    save(heat_sprite(ht), PWR, 'annihilation-reactor-heat')
    f = over(main, top)
    save(f, PWR, 'annihilation-reactor-full')
    FULL['annihilation-reactor'] = np.asarray(f)
    print(f'annihilation-reactor {tris(M)}  224 px', flush=True)


def do_resources():
    for d, name, M in (('items', 'seraphite', item_seraphite()), ('items', 'seraphimium', item_seraphimium()),
                       ('items', 'singularite', item_singularite()), ('items', 'singularity-core', item_singularity_core()),
                       ('liquids', 'antimatter', liquid_drop('antimat_l', 'antimat')),
                       ('liquids', 'void-matter', liquid_drop('voidm', GL, ring_=True))):
        a = icon(M)
        save(a, d, name)
        FULL[name] = np.asarray(a)
        print(f'{d}/{name:22s}{tris(M)}', flush=True)
    for kind in ('seraphite', 'singularite'):
        for v in range(3):
            a = icon(wall_ore(kind, v))
            save(a, 'blocks/ores', f'wall-ore-{kind}{v + 1}')
            FULL[f'wall-ore-{kind}{v + 1}'] = np.asarray(a)
        print(f'wall-ore-{kind:13s} 3 variants', flush=True)


JOBS = {'requiem': do_requiem, 'obelisk': do_obelisk, 'seraphim-net': do_net, 'chronofield': do_chrono,
        'seraphim-dome': do_dome, 'gravity-extractor': do_extractor, 'crafters': do_crafters,
        'annihilation-reactor': do_reactor, 'resources': do_resources}


def main(only=()):
    for name, fn in JOBS.items():
        if not only or name in only:
            fn()
    big = [k for k in ('requiem', 'obelisk', 'seraphim-net') if k in FULL]
    mid = [k for k in ('seraphim-dome', 'chronofield', 'singularity-collider', 'annihilation-reactor', 'seraphite-purifier',
                       'gravity-extractor', 'antimatter-trap') if k in FULL]
    small = [k for k in FULL if k not in big + mid]
    for keys, fn, sc in ((big, 'g_t6-turrets.png', 1), (mid, 'g_t6-blocks.png', 2), (small, 'g_t6-resources.png', 6)):
        if keys:
            print('sheet', qa_sheet(keys, fn, sc=sc, cols=min(len(keys), 4)))


if __name__ == '__main__':
    main(sys.argv[1:])
