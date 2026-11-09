"""Art rework (Scorpion level): command cores, ACU mechs and the engineer drone.

    .venv/bin/python tools/art/g_units.py

Writes straight into mod/sprites (same names/canvases as 2.5.0-alpha1.1):
  blocks/cores/core-{uef,cybran}{,-team,-full}.png          CoreBlock 4x4, 128 px, -team = team-colour mask
  units/acu-{uef,cybran}{,-base,-leg,-cell,-outline,-full}  MechUnit 80 px (leg = right leg, mirrored by the engine)
  units/weapons/acu-*{,-outline,-cell,-heat}.png            48 px, centred on the weapon mount (x/y in the unit JSON)
  units/engineer{,-cell,-outline,-full}.png                 flying drone 40 px
Units face +Y. 1.0 = one tile = 32 px = 8 world units, so a weapon at x=6 sits 0.75 tile right of the centre.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from geom import *  # noqa: E402,F401
from mats import Model, MID  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
from hero import (P, zring, slope_plate, bolts_on, grille, coil_jacket, hydraulic, muzzle_brake,  # noqa: E402
                  cable, antenna, seam)
import export  # noqa: E402
from export import save, blank, layer, FULL  # noqa: E402
from rend import outline, heat_sprite, over, hexc  # noqa: E402

TEAM_PREVIEW = 'ffd37f'  # sharded yellow, only for the -full previews


# ------------------------------------------------------------------ helpers
def ngon(r, n, cx=0.0, cy=0.0, ph=0.0, sx=1.0, sy=1.0):
    return P([(cx + sx * r * math.cos(math.radians(ph + 360.0 * k / n)),
               cy + sy * r * math.sin(math.radians(ph + 360.0 * k / n))) for k in range(n)])


def octp(r, cx=0.0, cy=0.0):
    return ngon(r, 8, cx, cy, 22.5)


def B(x0, x1, y0, y1, z0, z1):
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1)


def ring_frame(M, g, outer, inner, z0, z1, m):
    """Annulus between two polygons with the same vertex count."""
    o = np.asarray(outer)
    i = np.asarray(inner)
    n = len(o)
    for k in range(n):
        q = P([tuple(o[k]), tuple(o[(k + 1) % n]), tuple(i[(k + 1) % n]), tuple(i[k])])
        M.add(g, prism(q, z0, z1), m)


def torus(M, g, R, r, z, m, n=28, k=8, cx=0.0, cy=0.0):
    for i in range(n):
        a, b = math.radians(360 * i / n), math.radians(360 * (i + 1) / n)
        M.add(g, cyl((cx + R * math.cos(a), cy + R * math.sin(a), z), (cx + R * math.cos(b), cy + R * math.sin(b), z), r, n=k), m)


def spike(M, g, base_pts, z0, tip, m):
    """Faceted spike from a ground polygon to a single tip point."""
    b = np.asarray(P(base_pts), float)
    tp = np.asarray(tip, float)
    top = np.column_stack([b[:, 0] * 0.06 + tp[0] * 0.94, b[:, 1] * 0.06 + tp[1] * 0.94, np.full(len(b), tp[2])])
    M.add(g, loft(ring(b, z0), top), m)


def decal(M, g, poly, zfn, m, h=0.014, dz=0.004):
    """Thin plate that follows a sloped surface zfn (stripes, emblems)."""
    p = P(poly)
    M.add(g, loft(zring(p, zfn, dz), zring(p, zfn, dz + h)), m)


def xs(s, pts):
    return [(s * x, y) for x, y in pts]


def frustum(M, g, poly, z0, z1, sc, m, cap=None, cap_sc=0.86, cap_h=0.015):
    """Tapered armour block (wide sloped facets catch the light) with an optional inset cap plate."""
    p = P(poly)
    M.add(g, prism(p, z0, z1, sc), m)
    if cap:
        M.add(g, prism(scale_poly(p, sc * cap_sc), z1, z1 + cap_h), cap)
    return scale_poly(p, sc)


# ================================================================== UEF ACU "Страж"
def acu_uef():
    M = Model()
    # ---------------------------------------------------------- leg (right; the engine mirrors it for the left)
    g = 'leg'
    X = 0.40
    sole = P([(X - 0.13, -0.34), (X + 0.13, -0.34), (X + 0.17, -0.22), (X + 0.17, 0.36), (X + 0.12, 0.47),
              (X - 0.12, 0.47), (X - 0.17, 0.36), (X - 0.17, -0.22)])
    M.add(g, prism(sole, 0.0, 0.05, 0.96), 'hull_dark')
    for tx in (-0.075, 0.075):
        tp = [(X + tx - 0.07, 0.14), (X + tx + 0.07, 0.14), (X + tx + 0.07, 0.38), (X + tx + 0.04, 0.45),
              (X + tx - 0.04, 0.45), (X + tx - 0.07, 0.38)]
        slope_plate(M, g, tp, lambda x, y: 0.17 - (y - 0.14) * 0.28, 'hull_mid', thick=0.12, inlay='yellow', isc=0.55, ih=0.018)
        bolts(M, g, [(X + tx, 0.18)], 0.165, r=0.022)
    M.add(g, B(X - 0.006, X + 0.006, 0.14, 0.46, 0.04, 0.12), 'vent')
    M.add(g, prism(cham_rect(0.15, 0.10, 0.04, cx=X, cy=-0.24), 0.04, 0.16, 0.9), 'hull_mid')
    M.add(g, prism(cham_rect(0.11, 0.07, 0.03, cx=X, cy=-0.25), 0.16, 0.175), 'hull_dark')
    for i in range(4):
        M.add(g, B(X - 0.10, X + 0.10, -0.33 + i * 0.045, -0.315 + i * 0.045, 0.16, 0.185), 'metal')
    M.add(g, cyl((X - 0.15, -0.04, 0.17), (X + 0.15, -0.04, 0.17), 0.085, n=16), 'metal')
    for s in (-1, 1):
        M.add(g, cyl((X + s * 0.15, -0.04, 0.17), (X + s * 0.175, -0.04, 0.17), 0.07, n=14), 'hull_dark')
        M.add(g, cyl((X + s * 0.175, -0.04, 0.17), (X + s * 0.18, -0.04, 0.17), 0.035, n=10), 'yellow')
    M.add(g, prism(cham_rect(0.10, 0.11, 0.04, cx=X, cy=-0.02), 0.12, 0.36, 0.86), 'hull_mid')
    kg = [(X - 0.12, -0.10), (X + 0.12, -0.10), (X + 0.13, 0.10), (X + 0.07, 0.22), (X - 0.07, 0.22), (X - 0.13, 0.10)]
    kz = lambda x, y: 0.44 - (y + 0.10) * 0.42 - abs(x - X) * 0.25
    slope_plate(M, g, kg, kz, 'hull_light', thick=0.10, inlay='hull_mid', isc=0.62, ih=0.02)
    decal(M, g, [(X - 0.08, 0.10), (X + 0.08, 0.10), (X + 0.06, 0.14), (X - 0.06, 0.14)], kz, 'yellow', h=0.02)
    bolts_on(M, g, [(X - 0.09, -0.06), (X + 0.09, -0.06)], kz, r=0.022)
    hydraulic(M, g, X, 0.24, -0.36, -0.22, -0.10, r=0.05)
    # ---------------------------------------------------------- base (pelvis, turns with the legs)
    g = 'base'
    hip = mirror_half([(0, 0.22), (0.20, 0.20), (0.30, 0.10), (0.30, -0.12), (0.22, -0.24), (0, -0.26)])
    M.add(g, prism(hip, 0.24, 0.40, 0.86), 'hull_mid')
    M.add(g, prism(scale_poly(hip, 0.74, (0, 0)), 0.40, 0.42, 0.96), 'hull_dark')
    for s in (-1, 1):
        M.add(g, cyl((s * 0.24, 0, 0.36), (s * 0.50, 0, 0.36), 0.11, n=18), 'metal')
        for xx in (0.33, 0.43):
            M.add(g, cyl((s * xx, 0, 0.36), (s * (xx + 0.03), 0, 0.36), 0.125, n=18), 'hull_mid')
        M.add(g, cyl((s * 0.50, 0, 0.36), (s * 0.55, 0, 0.36), 0.09, n=16), 'hull_dark')
        M.add(g, cyl((s * 0.55, 0, 0.36), (s * 0.56, 0, 0.36), 0.045, n=12), 'yellow')
        fp = xs(s, [(0.30, 0.13), (0.52, 0.13), (0.50, 0.26), (0.32, 0.27)])
        slope_plate(M, g, fp, lambda x, y: 0.50 - (y - 0.13) * 0.55, 'hull_light', thick=0.08, inlay='hull_mid', isc=0.6, ih=0.012)
        decal(M, g, xs(s, [(0.33, 0.23), (0.49, 0.225), (0.49, 0.245), (0.33, 0.25)]), lambda x, y: 0.50 - (y - 0.13) * 0.55, 'yellow')
        rp = xs(s, [(0.30, -0.13), (0.52, -0.13), (0.50, -0.25), (0.32, -0.26)])
        slope_plate(M, g, rp, lambda x, y: 0.48 + (y + 0.13) * 0.50, 'hull_mid', thick=0.08)
        bolts(M, g, [(s * 0.41, 0.17)], 0.47, r=0.02)
    M.add(g, cyl((0, 0, 0.42), (0, 0, 0.45), 0.23, n=28), 'hull_dark')
    for i in range(18):
        M.add(g, tf(cbox(0.235, 0, 0.435, 0.03, 0.035, 0.03), rz(i * 20)), 'metal')
    M.add(g, cyl((0, 0, 0.45), (0, 0, 0.47), 0.11, n=18), 'metal')
    slope_plate(M, g, [(-0.15, 0.20), (0.15, 0.20), (0.11, 0.33), (-0.11, 0.33)], lambda x, y: 0.42 - (y - 0.2) * 0.6, 'hull_mid', thick=0.08, inlay='yellow', isc=0.6)
    grille(M, g, 0, -0.30, 0.38, 0.30, 0.08, n=5)
    # ---------------------------------------------------------- body (torso)
    g = 'body'
    tor = mirror_half([(0, 0.40), (0.20, 0.38), (0.31, 0.24), (0.35, -0.06), (0.29, -0.30), (0, -0.34)])
    M.add(g, prism(tor, 0.40, 0.66, 0.80), 'hull_mid')
    # chest armour with headlights and the nano-fabricator emitter at the front (build beam origin)
    cp = [(-0.24, 0.14), (0.24, 0.14), (0.25, 0.30), (0.16, 0.42), (-0.16, 0.42), (-0.25, 0.30)]
    cz = lambda x, y: 0.76 - (y - 0.14) * 0.50 - abs(x) * 0.14
    slope_plate(M, g, cp, cz, 'hull_light', thick=0.18, inlay='hull_mid', isc=0.80, ih=0.022)
    decal(M, g, [(-0.14, 0.36), (0.14, 0.36), (0.11, 0.395), (-0.11, 0.395)], cz, 'yellow', h=0.03)
    for s in (-1, 1):
        light(M, g, s * 0.16, 0.28, cz(0.16, 0.28) + 0.01, 0.045, 0.035, 0.016)
        grille(M, g, s * 0.10, 0.20, cz(0.10, 0.20) + 0.02, 0.10, 0.07, n=3)
    M.add(g, cyl((0, 0.36, cz(0, 0.36)), (0, 0.46, 0.60), 0.05, 0.042, n=14), 'metal')
    M.add(g, cyl((0, 0.46, 0.60), (0, 0.49, 0.595), 0.033, n=12), 'glow')
    # faceted helmet with visor, crest and side sensors
    frustum(M, g, octp(0.145, 0, 0.02), 0.66, 0.90, 0.62, 'hull_mid', cap='hull_light', cap_sc=0.75)
    M.add(g, prism(P([(-0.085, 0.10), (0.085, 0.10), (0.07, 0.165), (-0.07, 0.165)]), 0.72, 0.78), 'glow')
    M.add(g, B(-0.014, 0.014, -0.08, 0.08, 0.90, 0.93), 'yellow')
    for s in (-1, 1):
        M.add(g, B(s * 0.12, s * 0.18, -0.05, 0.06, 0.66, 0.78), 'hull_light')
        M.add(g, B(s * 0.15, s * 0.17, -0.03, 0.05, 0.78, 0.79), 'glow')
    # collar ridge with the team mark
    frustum(M, g, cham_rect(0.26, 0.06, 0.02, cy=-0.14), 0.66, 0.78, 0.82, 'hull_light', cap='hull_dark')
    M.add(g, prism(cham_rect(0.065, 0.03, 0.01, cy=-0.14), 0.795, 0.81), 'team')
    # pauldrons: tapered armour blocks, inset plate, yellow front trim, team emblem, light, bolts, cables
    for s in (-1, 1):
        pp = xs(s, [(0.27, 0.22), (0.47, 0.24), (0.58, 0.14), (0.59, -0.18), (0.49, -0.29), (0.27, -0.27)])
        M.add(g, cyl((s * 0.30, -0.02, 0.60), (s * 0.60, -0.02, 0.60), 0.12, n=16), 'metal')
        top = frustum(M, g, pp, 0.50, 0.86, 0.72, 'hull_light')
        inner = scale_poly(top, 0.80)
        M.add(g, prism(inner, 0.86, 0.875), 'hull_mid')
        c = np.asarray(inner).mean(0)
        M.add(g, B(c[0] - 0.09, c[0] + 0.09, c[1] + 0.13, c[1] + 0.155, 0.86, 0.885), 'yellow')
        M.add(g, prism(cham_rect(0.045, 0.045, 0.015, cx=c[0], cy=c[1] - 0.03), 0.875, 0.888), 'team')
        light(M, g, c[0] + s * 0.07, c[1] + 0.07, 0.875, 0.025, 0.03, 0.012)
        bolts(M, g, [(c[0] - 0.075, c[1] - 0.14), (c[0] + 0.075, c[1] - 0.14), (c[0] - s * 0.075, c[1] + 0.07)], 0.875, r=0.019, h=0.014)
        cable(M, g, [(s * 0.14, -0.30, 0.86), (s * 0.24, -0.24, 0.90), (s * 0.31, -0.19, 0.89)], 0.026, m='cable', ends='yellow')
    # backpack: reactor block with lit grille between twin jump-jet pods
    rb = cham_rect(0.15, 0.16, 0.05, cy=-0.35)
    M.add(g, prism(rb, 0.50, 0.86, 0.84), 'hull_dark')
    grille(M, g, 0, -0.34, 0.86, 0.17, 0.16, n=4)
    for s in (-1, 1):
        px = s * 0.25
        M.add(g, cyl((px, -0.12, 0.70), (px, -0.45, 0.70), 0.105, n=20), 'hull_mid')
        M.add(g, cyl((px, -0.10, 0.70), (px, -0.12, 0.70), 0.08, n=16), 'hull_dark')
        for y, m in ((-0.20, 'metal_light'), (-0.28, 'yellow'), (-0.37, 'metal_light')):
            M.add(g, cyl((px, y, 0.70), (px, y - 0.03, 0.70), 0.116, n=20), m)
        M.add(g, cyl((px, -0.45, 0.70), (px, -0.50, 0.70), 0.105, 0.092, n=20), 'metal')
        M.add(g, cyl((px, -0.50, 0.70), (px, -0.505, 0.70), 0.066, n=14), 'heat')
    antenna(M, g, (-0.25, -0.40, 0.80), (-0.31, -0.62, 1.06))
    bolts(M, g, [(-0.28, 0.27), (0.28, 0.27)], 0.62, r=0.02)
    seam(M, g, (-0.12, -0.21), (0.12, -0.21), 0.86, w=0.02, h=0.012)

    # ---------------------------------------------------------- right arm: plasma cannon (weapon-local coords)
    g = 'gunR'
    M.add(g, cyl((-0.15, -0.30, 0.42), (0.15, -0.30, 0.42), 0.10, n=18), 'metal')
    for s in (-1, 1):
        M.add(g, cyl((s * 0.15, -0.30, 0.42), (s * 0.17, -0.30, 0.42), 0.075, n=14), 'hull_dark')
        M.add(g, cyl((s * 0.17, -0.30, 0.42), (s * 0.175, -0.30, 0.42), 0.035, n=10), 'yellow')
    frustum(M, g, cham_rect(0.165, 0.25, 0.06, cy=-0.06), 0.28, 0.56, 0.78, 'hull_mid')
    M.add(g, prism(cham_rect(0.105, 0.17, 0.04, cy=-0.07), 0.56, 0.572), 'hull_dark')
    M.add(g, B(-0.032, 0.032, -0.19, 0.05, 0.572, 0.582), 'team')
    chevrons(M, g, 0, -0.205, 0.56, 0.19, 0.05, n=3)
    for s in (-1, 1):
        M.add(g, B(s * 0.07, s * 0.095, -0.16, 0.06, 0.572, 0.58), 'yellow')
    bolts(M, g, [(-0.09, -0.24), (0.09, -0.24), (-0.09, 0.10), (0.09, 0.10)], 0.56, r=0.018)
    M.add(g, cyl((0, 0.13, 0.44), (0, 0.44, 0.44), 0.08, n=18), 'hull_dark')
    for i in range(3):
        y = 0.15 + i * 0.09
        M.add(g, cyl((0, y, 0.44), (0, y + 0.032, 0.44), 0.108, n=20), 'metal_light')
        M.add(g, cyl((0, y + 0.032, 0.44), (0, y + 0.065, 0.44), 0.09, n=20), 'glow')
    M.add(g, cyl((0, 0.42, 0.44), (0, 0.60, 0.44), 0.052, n=16), 'metal')
    muzzle_brake(M, g, 0.575, 0.115, 0.058, z=0.44, nb=2, body='hull_dark', trim='yellow', baffle='metal_light', bore_r=0.03)
    for s in (-1, 1):
        cable(M, g, [(s * 0.13, -0.14, 0.50), (s * 0.135, 0.06, 0.50), (s * 0.09, 0.17, 0.48)], 0.024, ends='yellow')
    # ---------------------------------------------------------- left arm: tactical missile pod (2 tubes = 2-shot salvo)
    g = 'gunL'
    M.add(g, cyl((-0.15, -0.30, 0.42), (0.15, -0.30, 0.42), 0.10, n=18), 'metal')
    for s in (-1, 1):
        M.add(g, cyl((s * 0.15, -0.30, 0.42), (s * 0.17, -0.30, 0.42), 0.075, n=14), 'hull_dark')
        M.add(g, cyl((s * 0.17, -0.30, 0.42), (s * 0.175, -0.30, 0.42), 0.035, n=10), 'yellow')
    frustum(M, g, cham_rect(0.175, 0.27, 0.05, cy=-0.02), 0.28, 0.52, 0.86, 'hull_mid')
    frustum(M, g, cham_rect(0.15, 0.07, 0.03, cy=-0.22), 0.52, 0.60, 0.85, 'hull_light')
    chevrons(M, g, 0, -0.22, 0.60, 0.20, 0.06, n=4)
    for tx in (-0.078, 0.078):
        M.add(g, cyl((tx, -0.15, 0.56), (tx, 0.27, 0.56), 0.072, n=18), 'hull_light')
        for y in (-0.10, 0.06, 0.20):
            M.add(g, cyl((tx, y, 0.56), (tx, y + 0.035, 0.56), 0.08, n=18), 'team' if y == 0.06 else 'metal')
        M.add(g, cyl((tx, 0.27, 0.56), (tx, 0.30, 0.56), 0.078, n=18), 'hull_dark')
        M.add(g, cyl((tx, 0.30, 0.56), (tx, 0.36, 0.56), 0.046, 0.012, n=14), 'red_armor')
    bolts(M, g, [(-0.15, -0.26), (0.15, -0.26), (-0.15, 0.20), (0.15, 0.20)], 0.52, r=0.018)
    cable(M, g, [(0.0, -0.30, 0.52), (0.0, -0.17, 0.62), (0.0, 0.02, 0.64)], 0.022, ends='yellow')
    return M


# ================================================================== Cybran ACU "Призрак"
def acu_cybran():
    M = Model()
    # ---------------------------------------------------------- leg: three-claw foot, blade shin, knee spur
    g = 'leg'
    X = 0.38
    M.add(g, cyl((X, 0.0, 0.0), (X, 0.0, 0.14), 0.095, 0.075, n=6, phase=math.radians(30)), 'cy_mid')
    toe = [(-0.065, 0.0), (0.065, 0.0), (0.05, 0.25), (0.0, 0.37), (-0.05, 0.25)]
    for a in (-26, 0, 26):
        L = 1.0 if a == 0 else 0.88
        T = P([(x, y * L) for x, y in toe])
        R = rz(a)
        M.add(g, tf(prism(T, 0.0, 0.09, 0.70), R, (X, 0.04, 0)), 'cy_dark')
        M.add(g, tf(prism(P([(-0.024, 0.05), (0.024, 0.05), (0.016, 0.24 * L), (-0.016, 0.24 * L)]), 0.085, 0.10), R, (X, 0.04, 0)), 'red_armor')
        tip = tf(np.array([[0.0, 0.34 * L, 0.03]]), R, (X, 0.04, 0))[0]
        M.add(g, cyl(tip, tip + np.array([0, 0, 0.05]), 0.024, n=6), 'metal_light')
    M.add(g, tf(prism(P([(-0.06, 0.0), (0.06, 0.0), (0.0, 0.26)]), 0.0, 0.08, 0.7), rz(180), (X, -0.02, 0)), 'cy_dark')
    M.add(g, cyl((X - 0.11, -0.01, 0.15), (X + 0.11, -0.01, 0.15), 0.07, n=6), 'metal')
    shin = [(X - 0.09, -0.17), (X + 0.09, -0.17), (X + 0.10, 0.04), (X, 0.21), (X - 0.10, 0.04)]
    sz = lambda x, y: 0.42 - (y + 0.17) * 0.28 - abs(x - X) * 0.7
    slope_plate(M, g, shin, sz, 'cy_mid', thick=0.18, inlay='red_armor', isc=0.6, ih=0.024)
    M.add(g, cbox(X, 0.14, sz(X, 0.14) + 0.012, 0.035, 0.045, 0.03), 'rglow')
    spike(M, g, [(X - 0.04, -0.12), (X + 0.04, -0.12), (X, -0.06)], 0.30, (X, -0.32, 0.40), 'red_armor')
    hydraulic(M, g, X, 0.22, -0.28, -0.16, -0.05, r=0.038, body='cy_mid', rod='metal', collar='cy_dark')
    # ---------------------------------------------------------- base: angular hip with glowing joints
    g = 'base'
    hip = mirror_half([(0, 0.20), (0.14, 0.18), (0.27, 0.07), (0.29, -0.08), (0.18, -0.21), (0, -0.25)])
    M.add(g, prism(hip, 0.24, 0.38, 0.84), 'cy_dark')
    M.add(g, prism(scale_poly(hip, 0.70, (0, 0)), 0.38, 0.42, 0.92), 'cy_mid')
    for s in (-1, 1):
        M.add(g, cyl((s * 0.22, 0, 0.34), (s * 0.48, 0, 0.34), 0.10, n=6, phase=math.radians(30)), 'cy_mid')
        M.add(g, cyl((s * 0.36, 0, 0.34), (s * 0.40, 0, 0.34), 0.11, n=6, phase=math.radians(30)), 'red_armor')
        M.add(g, cyl((s * 0.48, 0, 0.34), (s * 0.50, 0, 0.34), 0.06, n=12), 'rglow')
        fp = xs(s, [(0.28, 0.10), (0.50, 0.08), (0.46, 0.24), (0.30, 0.20)])
        slope_plate(M, g, fp, lambda x, y: 0.48 - (y - 0.08) * 0.5, 'cy_mid', thick=0.08, inlay='red_armor', isc=0.55, ih=0.015)
        spike(M, g, xs(s, [(0.30, -0.10), (0.46, -0.10), (0.36, -0.16)]), 0.36, (s * 0.46, -0.34, 0.44), 'cy_dark')
    M.add(g, cyl((0, 0, 0.42), (0, 0, 0.46), 0.20, n=6, phase=math.radians(30)), 'cy_dark')
    M.add(g, cyl((0, 0, 0.46), (0, 0, 0.475), 0.10, n=6, phase=math.radians(30)), 'cy_mid')
    for k in range(6):
        M.add(g, tf(B(-0.012, 0.012, 0.12, 0.18, 0.46, 0.468), rz(60 * k)), 'rglow')
    # ---------------------------------------------------------- body: arrowhead torso with keel, flank armour, glowing core
    g = 'body'
    tor = mirror_half([(0, 0.46), (0.12, 0.38), (0.26, 0.18), (0.32, -0.04), (0.27, -0.28), (0.14, -0.44), (0, -0.50)])
    M.add(g, prism(tor, 0.40, 0.62, 0.80), 'cy_dark')
    for s in (-1, 1):
        fl = xs(s, [(0.08, 0.30), (0.20, 0.16), (0.26, -0.04), (0.22, -0.24), (0.12, -0.36), (0.08, -0.10)])
        slope_plate(M, g, fl, lambda x, y: 0.72 - (abs(x) - 0.08) * 0.55, 'red_armor', thick=0.10, inlay='cy_dark', isc=0.55, ih=0.012)
    keel = P([(0, 0.40), (0.09, 0.24), (0.11, -0.10), (0.07, -0.40), (0, -0.46), (-0.07, -0.40), (-0.11, -0.10), (-0.09, 0.24)])
    M.add(g, loft(ring(keel, 0.62), ring(scale_poly(keel, (0.25, 0.94), (0, -0.03)), 0.80)), 'cy_mid')
    # reactor core on the keel: hex housing, glowing ring, white-hot centre, radial slits
    M.add(g, prism(ngon(0.15, 6, 0, 0.05, 30), 0.72, 0.84, 0.82), 'cy_mid')
    M.add(g, prism(ngon(0.11, 6, 0, 0.05, 30), 0.84, 0.845), 'cy_dark')
    M.add(g, cyl((0, 0.05, 0.84), (0, 0.05, 0.86), 0.085, n=18), 'rglow')
    M.add(g, cyl((0, 0.05, 0.86), (0, 0.05, 0.865), 0.06, n=16), 'cy_dark')
    M.add(g, sphereish((0, 0.05, 0.87), 0.04, n=10), 'rglow')
    for k in range(6):
        M.add(g, tf(cbox(0.155, 0, 0.78, 0.035, 0.022, 0.03), rz(60 * k), (0, 0.05, 0)), 'rglow')
    # head: sharp wedge with visor slit and mandibles
    hw = P([(0, 0.54), (0.08, 0.45), (0.10, 0.30), (0.06, 0.24), (-0.06, 0.24), (-0.10, 0.30), (-0.08, 0.45)])
    M.add(g, loft(ring(hw, 0.60), ring(scale_poly(hw, (0.45, 0.80), (0, 0.36)), 0.82)), 'cy_mid')
    M.add(g, prism(P([(-0.07, 0.40), (0.07, 0.40), (0.05, 0.43), (-0.05, 0.43)]), 0.72, 0.78), 'rglow')
    for s in (-1, 1):
        spike(M, g, xs(s, [(0.07, 0.36), (0.12, 0.31), (0.11, 0.42)]), 0.58, (s * 0.12, 0.60, 0.62), 'red_armor')
    # shoulder blades: faceted ridged blades swept back, red ridge cap, team mark, spines, glow slit
    for s in (-1, 1):
        bl = P(xs(s, [(0.24, 0.18), (0.46, 0.13), (0.60, -0.02), (0.62, -0.22), (0.55, -0.38), (0.40, -0.31), (0.26, -0.21)]))
        M.add(g, cyl((s * 0.24, -0.04, 0.60), (s * 0.60, -0.04, 0.60), 0.10, n=6, phase=math.radians(30)), 'cy_mid')
        ridge = scale_poly(bl, (0.34, 0.86))
        M.add(g, loft(ring(bl, 0.54), ring(ridge, 0.86)), 'cy_mid')
        M.add(g, prism(scale_poly(ridge, (0.8, 0.9)), 0.86, 0.875), 'red_armor')
        c = np.asarray(ridge).mean(0)
        M.add(g, prism(P([(c[0] - 0.035, c[1] - 0.02), (c[0] + 0.035, c[1] - 0.02), (c[0] + 0.03, c[1] + 0.07), (c[0] - 0.03, c[1] + 0.07)]), 0.875, 0.888), 'team')
        spike(M, g, xs(s, [(0.50, -0.24), (0.60, -0.22), (0.56, -0.32)]), 0.62, (s * 0.72, -0.62, 0.62), 'cy_dark')
        spike(M, g, xs(s, [(0.36, -0.24), (0.46, -0.24), (0.42, -0.30)]), 0.66, (s * 0.50, -0.58, 0.68), 'red_armor')
        M.add(g, tf(B(-0.012, 0.012, -0.10, 0.10, -0.02, 0.02), rz(s * 20), (s * 0.55, -0.04, 0.70)), 'rglow')
        cable(M, g, [(s * 0.10, -0.10, 0.76), (s * 0.20, -0.14, 0.82), (s * 0.30, -0.15, 0.84)], 0.024, ends='red_armor')
        M.add(g, tf(B(-0.045, 0.045, -0.07, 0.07, -0.03, 0.03), rz(-s * 20), (s * 0.18, -0.36, 0.66)), 'cy_dark')
        M.add(g, tf(B(-0.03, 0.03, -0.055, 0.055, 0.03, 0.04), rz(-s * 20), (s * 0.18, -0.36, 0.66)), 'rglow')
        antenna(M, g, (s * 0.10, -0.42, 0.70), (s * 0.18, -0.76, 0.94), r=0.018, tip='rglow', baseM='cy_mid')
    for i, y in enumerate((-0.16, -0.25, -0.34)):
        b = rect(0, y, 0.05 - i * 0.006, 0.04)
        t = rect(0, y - 0.03, 0.014, 0.012)
        M.add(g, loft(ring(b, 0.76), ring(t, 0.88 - i * 0.02)), 'cy_mid')
        M.add(g, B(-0.02, 0.02, y + 0.04, y + 0.052, 0.76, 0.78), 'rglow')
    cybran_arms(M)
    return M


def cybran_arms(M):
    # ---------------------------------------------------------- right arm: microwave laser
    g = 'gunR'
    M.add(g, cyl((-0.13, -0.30, 0.42), (0.13, -0.30, 0.42), 0.085, n=6, phase=math.radians(30)), 'cy_mid')
    hous = mirror_half([(0, 0.20), (0.08, 0.17), (0.13, 0.06), (0.13, -0.24), (0.07, -0.36), (0, -0.39)])
    top = frustum(M, g, hous, 0.28, 0.54, 0.66, 'cy_dark')
    M.add(g, prism(scale_poly(top, (0.70, 0.88)), 0.54, 0.552), 'cy_mid')
    M.add(g, B(-0.018, 0.018, -0.12, 0.10, 0.552, 0.562), 'red_armor')
    M.add(g, prism(P([(-0.03, -0.22), (0.03, -0.22), (0.0, -0.14)]), 0.552, 0.564), 'team')
    for y in (-0.06, 0.02):
        M.add(g, B(-0.06, 0.06, y, y + 0.025, 0.552, 0.558), 'rglow')
    spike(M, g, [(0.10, -0.22), (0.135, -0.10), (0.10, -0.04)], 0.42, (0.22, -0.34, 0.46), 'red_armor')
    M.add(g, cyl((0, 0.10, 0.44), (0, 0.60, 0.44), 0.035, n=12), 'metal')
    for i in range(4):
        y = 0.14 + i * 0.085
        M.add(g, cyl((0, y, 0.44), (0, y + 0.038, 0.44), 0.078 - i * 0.006, n=6, phase=math.radians(30)), 'cy_mid')
        M.add(g, cyl((0, y + 0.038, 0.44), (0, y + 0.062, 0.44), 0.062 - i * 0.005, n=14), 'rglow')
    for s in (-1, 1):
        pr = P([(s * 0.03, 0.46), (s * 0.08, 0.48), (s * 0.065, 0.74), (s * 0.04, 0.70)])
        M.add(g, prism(pr, 0.40, 0.48, 0.80), 'cy_mid')
        M.add(g, cbox(s * 0.056, 0.715, 0.475, 0.024, 0.045, 0.02), 'red_armor')
    M.add(g, sphereish((0, 0.665, 0.44), 0.036, n=10), 'rglow')
    cable(M, g, [(0.09, -0.16, 0.50), (0.10, 0.06, 0.48), (0.06, 0.15, 0.46)], 0.022, ends='red_armor')
    bolts(M, g, [(-0.06, -0.28), (0.06, -0.28)], 0.54, r=0.016)
    # ---------------------------------------------------------- left arm: EMP discharger
    g = 'gunL'
    M.add(g, cyl((-0.13, -0.30, 0.42), (0.13, -0.30, 0.42), 0.085, n=6, phase=math.radians(30)), 'cy_mid')
    hous = mirror_half([(0, 0.13), (0.10, 0.11), (0.145, 0.0), (0.145, -0.26), (0.08, -0.37), (0, -0.40)])
    frustum(M, g, hous, 0.28, 0.46, 0.76, 'cy_dark')
    spike(M, g, [(-0.11, -0.22), (-0.145, -0.10), (-0.11, -0.04)], 0.40, (-0.24, -0.34, 0.44), 'red_armor')
    M.add(g, cyl((0, -0.27, 0.52), (0, 0.10, 0.52), 0.10, n=8, phase=math.radians(22.5)), 'cy_mid')
    for y in (-0.21, -0.12, -0.03, 0.06):
        M.add(g, cyl((0, y, 0.52), (0, y + 0.032, 0.52), 0.116, n=8, phase=math.radians(22.5)), 'team' if y < -0.1 else 'red_armor')
    M.add(g, B(-0.028, 0.028, -0.26, 0.09, 0.615, 0.625), 'rglow')
    for a in (-1, 0, 1):
        p0 = np.array([a * 0.09, 0.10, 0.50 + (0.05 if a == 0 else 0.0)])
        p1 = np.array([a * 0.035, 0.40, 0.46])
        M.add(g, cyl(p0, p1, 0.028, 0.018, n=6), 'cy_mid')
        M.add(g, cyl(p0 + (p1 - p0) * 0.45, p0 + (p1 - p0) * 0.57, 0.036, n=6), 'red_armor')
    torus(M, g, 0.065, 0.013, 0.46, 'cy_mid', n=14, k=6, cy=0.44)
    M.add(g, sphereish((0, 0.445, 0.46), 0.046, n=10), 'rglow')
    cable(M, g, [(-0.12, -0.16, 0.46), (-0.13, 0.02, 0.48), (-0.08, 0.12, 0.50)], 0.022, ends='red_armor')
    bolts(M, g, [(-0.10, -0.30), (0.10, -0.30)], 0.46, r=0.018)


# ================================================================== engineer (UEF hover construction drone)
def engineer():
    M = Model()
    g = 'body'
    hull = mirror_half([(0, 0.26), (0.11, 0.25), (0.18, 0.15), (0.19, -0.16), (0.12, -0.27), (0, -0.29)])
    top = frustum(M, g, hull, 0.10, 0.27, 0.80, 'hull_mid')
    M.add(g, prism(scale_poly(top, 0.82), 0.27, 0.285), 'hull_dark')
    # side lift-fan pods on pylons: duct, rim, fan blades, glowing hub ring, team mark
    for s in (-1, 1):
        cx = s * 0.36
        M.add(g, B(s * 0.15, s * 0.24, -0.06, 0.06, 0.14, 0.20), 'metal')
        M.add(g, cyl((cx, 0, 0.06), (cx, 0, 0.20), 0.165, 0.150, n=24), 'hull_mid')
        ring_frame(M, g, ngon(0.152, 24, cx, 0), ngon(0.118, 24, cx, 0), 0.20, 0.225, 'hull_light')
        M.add(g, cyl((cx, 0, 0.19), (cx, 0, 0.20), 0.12, n=24), 'vent')
        M.add(g, cyl((cx, 0, 0.20), (cx, 0, 0.203), 0.085, n=20), 'glow')
        for k in range(5):
            M.add(g, tf(prism(P([(0.02, -0.018), (0.112, -0.03), (0.112, 0.012), (0.02, 0.018)]), 0.203, 0.215), rz(72 * k + 18 * s), (cx, 0, 0)), 'metal_light')
        M.add(g, cyl((cx, 0, 0.20), (cx, 0, 0.23), 0.035, n=10), 'hull_dark')
        M.add(g, tf(B(-0.03, 0.03, 0.118, 0.152, 0.20, 0.232), None, (cx, 0, 0)), 'team')
        M.add(g, tf(B(-0.03, 0.03, -0.152, -0.118, 0.20, 0.232), None, (cx, 0, 0)), 'yellow')
    # construction arms with nozzles converging on the build point (buildBeamOffset 3.4 = 0.425 tile)
    for s in (-1, 1):
        cable(M, g, [(s * 0.10, 0.17, 0.27), (s * 0.135, 0.29, 0.30), (s * 0.07, 0.39, 0.28)], 0.03, m='yellow', ends='metal')
        M.add(g, cyl((s * 0.07, 0.39, 0.28), (s * 0.035, 0.435, 0.27), 0.03, 0.022, n=10), 'metal_light')
        M.add(g, cyl((s * 0.035, 0.435, 0.27), (s * 0.025, 0.45, 0.268), 0.018, n=8), 'glow')
    # sensor head with glass and lens
    frustum(M, g, octp(0.08, 0, 0.13), 0.28, 0.34, 0.75, 'hull_light')
    M.add(g, prism(P([(-0.05, 0.18), (0.05, 0.18), (0.04, 0.205), (-0.04, 0.205)]), 0.30, 0.33), 'glow')
    M.add(g, cyl((0, 0.12, 0.34), (0, 0.12, 0.352), 0.035, n=10), 'glass')
    # deck: team stripe, hazard chevrons, antenna, bolts; rear thruster (engineOffset 6 = 0.75 tile behind)
    M.add(g, B(-0.075, 0.075, -0.02, 0.03, 0.285, 0.296), 'team')
    chevrons(M, g, 0, -0.13, 0.285, 0.18, 0.06, n=3)
    M.add(g, cyl((0, -0.22, 0.20), (0, -0.46, 0.18), 0.075, 0.085, n=16), 'metal')
    M.add(g, cyl((0, -0.32, 0.19), (0, -0.35, 0.19), 0.092, n=16), 'yellow')
    M.add(g, cyl((0, -0.46, 0.18), (0, -0.52, 0.18), 0.095, 0.085, n=16), 'hull_dark')
    M.add(g, cyl((0, -0.52, 0.18), (0, -0.525, 0.18), 0.06, n=12), 'heat')
    antenna(M, g, (-0.10, -0.18, 0.285), (-0.14, -0.36, 0.40), r=0.012)
    bolts(M, g, [(-0.12, 0.13), (0.12, 0.13), (-0.12, -0.19), (0.12, -0.19)], 0.27, r=0.016, h=0.012)
    return M


# ================================================================== UEF command complex (core 4x4)
def core_uef():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(1.97, 1.97, 0.50), 0.0, 0.10, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.86, 1.86, 0.50), 0.10, 0.24, 0.95), 'hull_mid')
    M.add(g, prism(cham_rect(1.70, 1.70, 0.44), 0.24, 0.26, 0.985), 'hull_dark')
    DZ = 0.26
    # deck seams and bolts
    for v in (-1.10, 1.10):
        seam(M, g, (-1.0, v), (1.0, v), DZ, w=0.025, h=0.01)
        seam(M, g, (v, -1.0), (v, 1.0), DZ, w=0.025, h=0.01)
    # ---- landing pad with iris hatch
    M.add(g, prism(octp(1.02), DZ, 0.32, 0.97), 'hull_mid')
    M.add(g, prism(octp(0.95), 0.32, 0.325), 'hull_dark')
    # hazard ring: continuous yellow band with dark diagonal stripes
    ring_frame(M, g, octp(0.90), octp(0.78), 0.325, 0.335, 'yellow')
    for k in range(32):
        a = math.radians(360 * k / 32)
        q = [(0.79, -0.018), (0.79, 0.018), (0.89, 0.040), (0.89, 0.004)]
        M.add(g, tf(prism(P(q), 0.334, 0.338), rz(360 * k / 32)), 'hull_dark')
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        light(M, g, 0.955 * math.cos(a), 0.955 * math.sin(a), 0.32, 0.04, 0.04, 0.014)
    for k in range(4):
        M.add(g, tf(prism(P([(-0.10, 0.60), (0.10, 0.60), (0.0, 0.50)]), 0.325, 0.34), rz(90 * k)), 'team')
        M.add(g, tf(B(-0.10, 0.10, 0.63, 0.66, 0.325, 0.34), rz(90 * k)), 'team')
    M.add(g, cyl((0, 0, 0.325), (0, 0, 0.36), 0.52, n=32), 'hull_light')
    M.add(g, cyl((0, 0, 0.36), (0, 0, 0.365), 0.47, n=32), 'glow')
    for k in range(8):
        pet = P([(0, 0), (0.46 * math.cos(math.radians(-21)), 0.46 * math.sin(math.radians(-21))),
                 (0.46 * math.cos(math.radians(21)), 0.46 * math.sin(math.radians(21)))])
        pet = scale_poly(pet, 0.94)
        M.add(g, tf(prism(pet, 0.36, 0.385 + 0.012 * (k % 2), 0.90), rz(45 * k + 22.5)), 'hull_mid' if k % 2 else 'metal')
    M.add(g, cyl((0, 0, 0.36), (0, 0, 0.405), 0.09, n=16), 'hull_mid')
    M.add(g, cyl((0, 0, 0.405), (0, 0, 0.41), 0.05, n=12), 'glow')
    # ---- corner bastions, each with its own fixture
    for i, (sx, sy) in enumerate(((-1, 1), (1, 1), (1, -1), (-1, -1))):
        cx, cy = sx * 1.42, sy * 1.42
        M.add(g, prism(octp(0.44, cx, cy), 0.10, 0.50, 0.86), 'hull_mid')
        M.add(g, prism(octp(0.36, cx, cy), 0.50, 0.56, 0.93), 'hull_light')
        ring_frame(M, g, octp(0.31, cx, cy), octp(0.26, cx, cy), 0.56, 0.575, 'yellow')
        M.add(g, prism(octp(0.26, cx, cy), 0.56, 0.565), 'hull_dark')
        light(M, g, cx + sx * 0.36, cy + sy * 0.10, 0.40, 0.035, 0.05, 0.014)
        light(M, g, cx + sx * 0.10, cy + sy * 0.36, 0.40, 0.05, 0.035, 0.014)
        bolts(M, g, [(cx + 0.33 * math.cos(math.radians(a)), cy + 0.33 * math.sin(math.radians(a))) for a in range(0, 360, 60)], 0.555, r=0.022)
        if i == 0:      # comm mast: lattice tower with dish and beacon
            for a in (45, 135, 225, 315):
                p0 = (cx + 0.20 * math.cos(math.radians(a)), cy + 0.20 * math.sin(math.radians(a)), 0.565)
                M.add(g, cyl(p0, (cx, cy, 1.30), 0.022, 0.012, n=6), 'metal_light')
            for z, r in ((0.80, 0.13), (1.02, 0.08)):
                ring_frame(M, g, ngon(r + 0.02, 4, cx, cy, 45), ngon(r, 4, cx, cy, 45), z, z + 0.02, 'metal')
            M.add(g, cyl((cx, cy, 1.30), (cx, cy, 1.34), 0.04, n=8), 'team')
            M.add(g, tf(cyl((0, 0, 0), (0, 0, 0.05), 0.17, 0.20, n=18), ry(-35) @ rz(0), (cx + 0.15, cy - 0.04, 0.95)), 'metal_light')
            M.add(g, tf(cyl((0, 0, 0.05), (0, 0, 0.055), 0.14, n=18), ry(-35), (cx + 0.15, cy - 0.04, 0.95)), 'hull_dark')
            M.add(g, tf(cyl((0, 0, 0.05), (0, 0, 0.16), 0.012, n=6), ry(-35), (cx + 0.15, cy - 0.04, 0.95)), 'metal')
        elif i == 1:    # big radar dish on a pedestal
            M.add(g, cyl((cx, cy, 0.565), (cx, cy, 0.70), 0.09, n=12), 'metal')
            T0 = tf(cyl((0, 0, 0), (0, 0, 0.10), 0.18, 0.34, n=24), ry(28) @ rz(10), (cx, cy, 0.76))
            M.add(g, T0, 'metal_light')
            M.add(g, tf(cyl((0, 0, 0.10), (0, 0, 0.105), 0.30, n=24), ry(28), (cx, cy, 0.76)), 'steel')
            for a in (0, 120, 240):
                p0 = tf(np.array([[0.28 * math.cos(math.radians(a)), 0.28 * math.sin(math.radians(a)), 0.10]]), ry(28), (cx, cy, 0.76))[0]
                p1 = tf(np.array([[0, 0, 0.30]]), ry(28), (cx, cy, 0.76))[0]
                M.add(g, cyl(p0, p1, 0.012, n=6), 'metal')
            p1 = tf(np.array([[0, 0, 0.30]]), ry(28), (cx, cy, 0.76))[0]
            M.add(g, sphereish(p1, 0.035, n=8), 'glow')
        elif i == 2:    # sensor dome
            M.add(g, cyl((cx, cy, 0.565), (cx, cy, 0.62), 0.25, n=24), 'hull_mid')
            for k in range(4):
                z0, z1 = 0.62 + k * 0.05, 0.62 + (k + 1) * 0.05
                r0 = 0.23 * math.cos(math.asin(min(0.99, k / 4))); r1 = 0.23 * math.cos(math.asin(min(0.99, (k + 1) / 4.2)))
                M.add(g, cyl((cx, cy, z0), (cx, cy, z1), r0, r1, n=24), 'glass')
            for a in range(0, 360, 45):
                M.add(g, tf(B(-0.008, 0.008, 0.0, 0.22, 0.62, 0.78), rz(a), (cx, cy, 0)), 'metal')
            M.add(g, cyl((cx, cy, 0.80), (cx, cy, 0.83), 0.05, n=10), 'team')
        else:           # power node: stacked capacitor rings
            M.add(g, cyl((cx, cy, 0.565), (cx, cy, 0.90), 0.16, 0.13, n=20), 'hull_dark')
            for k in range(4):
                z = 0.60 + k * 0.075
                M.add(g, cyl((cx, cy, z), (cx, cy, z + 0.035), 0.20 - k * 0.01, n=20), 'metal_light')
                M.add(g, cyl((cx, cy, z + 0.035), (cx, cy, z + 0.05), 0.17 - k * 0.01, n=20), 'glow')
            M.add(g, cyl((cx, cy, 0.90), (cx, cy, 0.93), 0.10, n=16), 'hull_light')
            M.add(g, cyl((cx, cy, 0.93), (cx, cy, 0.95), 0.045, n=10), 'glow')
    # ---- north: command bunker with window strip, roof vents and emblem
    bk = cham_rect(0.86, 0.30, 0.10, cy=1.52)
    M.add(g, prism(bk, DZ, 0.62, 0.92), 'hull_mid')
    slope_plate(M, g, [(-0.80, 1.24), (0.80, 1.24), (0.80, 1.40), (-0.80, 1.40)], lambda x, y: 0.62 + (y - 1.24) * 0.6, 'hull_light', thick=0.12)
    M.add(g, B(-0.70, 0.70, 1.255, 1.30, 0.60, 0.66), 'glass')
    for x in np.linspace(-0.62, 0.62, 7):
        M.add(g, B(x - 0.012, x + 0.012, 1.25, 1.31, 0.60, 0.675), 'metal')
    M.add(g, prism(cham_rect(0.80, 0.18, 0.08, cy=1.60), 0.66, 0.72, 0.95), 'hull_light')
    M.add(g, B(-0.78, 0.78, 1.405, 1.43, 0.72, 0.735), 'yellow')
    grille(M, g, -0.42, 1.60, 0.72, 0.42, 0.18, n=6)
    M.add(g, prism(cham_rect(0.12, 0.08, 0.03, cx=0.42, cy=1.60), 0.72, 0.74), 'team')
    for x in (0.20, 0.64):
        M.add(g, cyl((x, 1.64, 0.72), (x, 1.64, 0.82), 0.05, n=10), 'metal')
        M.add(g, cyl((x, 1.64, 0.82), (x, 1.64, 0.84), 0.065, n=10), 'hull_dark')
    antenna(M, g, (0.05, 1.70, 0.72), (0.05, 1.70, 1.10))
    # ---- south: access ramp with hazard stripes and side rails
    rmp = lambda x, y: 0.27 + (y + 1.90) * 0.10
    M.add(g, loft(zring(rect(0, -1.51, 0.56, 0.39), rmp, -0.04), zring(rect(0, -1.51, 0.55, 0.38), rmp)), 'hull_dark')
    for k in range(6):
        y0 = -1.84 + k * 0.11
        decal(M, g, [(-0.50, y0), (-0.20, y0), (-0.14, y0 + 0.05), (-0.44, y0 + 0.05)], rmp, 'yellow')
        decal(M, g, [(0.20, y0), (0.50, y0), (0.44, y0 + 0.05), (0.14, y0 + 0.05)], rmp, 'yellow')
    decal(M, g, rect(0, -1.51, 0.06, 0.35), rmp, 'metal')
    for x in (-0.62, 0.62):
        M.add(g, B(x - 0.05, x + 0.05, -1.90, -1.12, 0.10, 0.40), 'hull_light')
        M.add(g, B(x - 0.02, x + 0.02, -1.86, -1.16, 0.40, 0.42), 'yellow')
        bolts(M, g, [(x, -1.82), (x, -1.20)], 0.42, r=0.02)
    # ---- east / west: gantry rails, bridge crane over the pad, fuel tanks, side grilles
    for s in (-1, 1):
        for y in (-0.80, 0.0, 0.80):
            M.add(g, B(s * 1.08, s * 1.18, y - 0.05, y + 0.05, DZ, 0.70), 'metal')
        M.add(g, B(s * 1.06, s * 1.20, -0.96, 0.96, 0.70, 0.76), 'hull_light')
        M.add(g, B(s * 1.10, s * 1.16, -0.94, 0.94, 0.76, 0.78), 'metal')
        M.add(g, B(s * 1.06, s * 1.20, -0.98, -0.94, 0.76, 0.80), 'yellow')
        M.add(g, B(s * 1.06, s * 1.20, 0.94, 0.98, 0.76, 0.80), 'yellow')
        for y in (-0.45, 0.45):
            M.add(g, cyl((s * 1.60, y - 0.36, 0.30), (s * 1.60, y + 0.36, 0.30), 0.13, n=18), 'hull_mid')
            for yy in (y - 0.30, y, y + 0.27):
                M.add(g, cyl((s * 1.60, yy, 0.30), (s * 1.60, yy + 0.03, 0.30), 0.145, n=18), 'hull_dark')
            M.add(g, cyl((s * 1.60, y + 0.36, 0.30), (s * 1.60, y + 0.40, 0.30), 0.09, n=14), 'hull_mid')
        cable(M, g, [(s * 1.60, -0.05, 0.30), (s * 1.45, 0.0, 0.34), (s * 1.10, 0.0, 0.30), (s * 0.98, 0.0, 0.34)], 0.035, m='cable', ends='yellow')
        grille(M, g, 0, -1.80, 0.24, 0.56, 0.08, n=6, R=rz(-s * 90))
    # bridge crane parked near the north edge of the pad
    yb = 0.70
    M.add(g, B(-1.22, 1.22, yb - 0.09, yb + 0.09, 0.80, 0.90), 'hull_light')
    M.add(g, B(-1.22, 1.22, yb - 0.10, yb - 0.07, 0.78, 0.92), 'hull_mid')
    M.add(g, B(-1.22, 1.22, yb + 0.07, yb + 0.10, 0.78, 0.92), 'hull_mid')
    for x in np.linspace(-1.0, 1.0, 9):
        M.add(g, B(x - 0.012, x + 0.012, yb - 0.07, yb + 0.07, 0.90, 0.915), 'yellow')
    for s in (-1, 1):
        M.add(g, B(s * 1.04, s * 1.24, yb - 0.14, yb + 0.14, 0.78, 0.94), 'hull_mid')
        M.add(g, B(s * 1.08, s * 1.20, yb - 0.10, yb + 0.10, 0.94, 0.96), 'yellow')
    M.add(g, B(0.10, 0.44, yb - 0.15, yb + 0.15, 0.90, 1.02), 'hull_mid')
    M.add(g, B(0.14, 0.40, yb - 0.11, yb + 0.11, 1.02, 1.04), 'hull_light')
    M.add(g, B(0.16, 0.30, yb - 0.05, yb + 0.05, 1.04, 1.05), 'team')
    M.add(g, cyl((0.36, yb, 1.04), (0.36, yb, 1.07), 0.035, n=10), 'glow')
    M.add(g, cyl((0.27, yb - 0.15, 0.80), (0.27, yb - 0.30, 0.55), 0.016, n=6), 'metal_light')
    M.add(g, B(0.22, 0.32, yb - 0.36, yb - 0.28, 0.48, 0.56), 'yellow')
    # pipes from the power node and the fuel farm into the pad ring
    cable(M, g, [(-1.20, -1.20, 0.30), (-1.0, -1.0, 0.31), (-0.74, -0.74, 0.33)], 0.045, m='metal', ends='yellow')
    cable(M, g, [(1.20, -1.20, 0.30), (1.0, -1.0, 0.31), (0.74, -0.74, 0.33)], 0.035, m='cable', ends='yellow')
    return M


# ================================================================== Cybran node (core 4x4)
def core_cybran():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(1.97, 1.97, 0.72), 0.0, 0.10, 0.985), 'cy_dark')
    M.add(g, prism(cham_rect(1.80, 1.80, 0.68), 0.10, 0.24, 0.94), 'cy_mid')
    M.add(g, prism(cham_rect(1.62, 1.62, 0.62), 0.24, 0.26, 0.985), 'cy_dark')
    DZ = 0.26
    # four diagonal buttresses (sloped, red inlay, glowing tips)
    for k in range(4):
        R = rz(45 + 90 * k)
        u0, u1 = 1.05, 2.42

        def zt(u, u0=u0, u1=u1):
            return 0.62 - (u - u0) / (u1 - u0) * 0.46
        bot = P([(u0, -0.30), (1.70, -0.24), (2.15, -0.13), (u1, 0.0), (2.15, 0.13), (1.70, 0.24), (u0, 0.30)])
        tp = P([(u0 + 0.02, -0.20), (1.70, -0.15), (2.12, -0.07), (u1 - 0.04, 0.0), (2.12, 0.07), (1.70, 0.15), (u0 + 0.02, 0.20)])
        M.add(g, tf(loft(ring(bot, 0.10), np.column_stack([tp, [zt(u) for u, _ in tp]])), R), 'cy_dark')
        cp = P([(1.15, -0.13), (1.70, -0.10), (2.05, -0.045), (2.05, 0.045), (1.70, 0.10), (1.15, 0.13)])
        cb = np.column_stack([cp, [zt(u) + 0.004 for u, _ in cp]])
        cps = scale_poly(cp, (0.97, 0.72))
        M.add(g, tf(loft(cb, np.column_stack([cps, [zt(u) + 0.045 for u, _ in cps]])), R), 'red_armor')
        M.add(g, tf(cbox(2.22, 0, zt(2.22) + 0.03, 0.10, 0.06, 0.05), R), 'rglow')
        chev = np.asarray(P([(1.22, -0.10), (1.34, 0.0), (1.22, 0.10), (1.27, 0.10), (1.39, 0.0), (1.27, -0.10)]))
        M.add(g, tf(loft(np.column_stack([chev, [zt(u) + 0.05 for u, _ in chev]]),
                         np.column_stack([chev, [zt(u) + 0.065 for u, _ in chev]])), R), 'team')
        for v in (-0.16, 0.16):
            M.add(g, tf(cyl((1.12, v, zt(1.12) - 0.02), (1.12, v, zt(1.12) + 0.03), 0.035, n=8), R), 'metal_light')
        for s in (-1, 1):
            sp = P([(1.45, s * 0.22), (1.65, s * 0.22), (1.55, s * 0.40)])
            M.add(g, tf(loft(ring(sp, 0.10), ring(scale_poly(sp, 0.4), 0.36)), R), 'cy_mid')
    # four cardinal spires leaning outwards, collars and glowing tips
    for k in range(4):
        R = rz(90 * k)
        M.add(g, tf(prism(ngon(0.30, 6, 0, 1.30, 0), DZ, 0.36, 0.85), R), 'cy_dark')
        M.add(g, tf(prism(ngon(0.26, 6, 0, 1.30, 0), 0.36, 0.375), R), 'team')
        # four-faceted blade spire leaning outwards: dark and red halves, glowing ridge, collar, hot tip
        tip = (0.0, 1.50, 1.36)
        spike(M, g, [(0, 1.02), (0, 1.60), (-0.18, 1.30)], 0.375, tip, 'cy_mid')
        spike(M, g, [(0, 1.02), (0.18, 1.30), (0, 1.60)], 0.375, tip, 'red_armor')
        for a, b in (((0, 1.04, 0.40), (0, 1.47, 1.30)), ((0, 1.58, 0.40), (0, 1.51, 1.30))):
            M.add(g, tf(cyl(a, b, 0.014, n=6), R), 'rglow')
        M.add(g, tf(prism(P([(0, 1.12), (0.13, 1.33), (0, 1.53), (-0.13, 1.33)]), 0.70, 0.76, 0.92), R), 'cy_dark')
        M.add(g, tf(sphereish(tip, 0.045, n=8), R), 'rglow')
        # blade fins on the spire flanks
        for s in (-1, 1):
            spike(M, g, [(s * 0.20, 1.18), (s * 0.30, 1.30), (s * 0.20, 1.40)], 0.36, (s * 0.46, 1.10, 0.62), 'red_armor')
        # side vents on the slope between buttress and spire
        for s in (-1, 1):
            M.add(g, tf(B(s * 0.55, s * 0.95, 1.62, 1.72, 0.20, 0.24), R), 'cy_dark')
            M.add(g, tf(B(s * 0.58, s * 0.92, 1.64, 1.70, 0.23, 0.245), R), 'rglow')
            for i in range(5):
                x = s * (0.60 + i * 0.075)
                M.add(g, tf(B(x - 0.015, x + 0.015, 1.62, 1.72, 0.245, 0.27), R), 'cy_mid')
            cable(M, g, [(s * 0.50, 1.54, 0.20), (s * 0.40, 1.20, 0.34), (s * 0.34, 0.90, 0.40)], 0.04, ends='red_armor', R=R)
    # ---- central node: octagonal frame, red ring, claws over a glowing quantum core
    ring_frame(M, g, octp(1.02), octp(0.80), DZ, 0.52, 'cy_mid')
    ring_frame(M, g, octp(0.96), octp(0.86), 0.52, 0.54, 'cy_dark')
    ring_frame(M, g, octp(0.80), octp(0.70), DZ, 0.46, 'red_armor')
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        M.add(g, cbox(0.91 * math.cos(a), 0.91 * math.sin(a), 0.545, 0.06, 0.06, 0.02), 'rglow')
    M.add(g, cyl((0, 0, DZ), (0, 0, 0.36), 0.70, n=8, phase=math.radians(22.5)), 'cy_dark')
    M.add(g, cyl((0, 0, 0.36), (0, 0, 0.37), 0.56, n=32), 'rglow')
    M.add(g, cyl((0, 0, 0.37), (0, 0, 0.40), 0.48, n=32), 'cy_dark')
    for k in range(12):
        M.add(g, tf(B(-0.018, 0.018, 0.20, 0.46, 0.40, 0.41), rz(30 * k + 15)), 'rglow' if k % 2 else 'cy_mid')
    # claws: three curved angular arms from the frame over the core
    for k in range(3):
        R = rz(90 + 120 * k)
        pts = [(0.0, 0.92, 0.54), (0.0, 0.62, 0.86), (0.0, 0.34, 0.92), (0.0, 0.18, 0.84)]
        for (a, b), w0, w1 in zip(zip(pts[:-1], pts[1:]), (0.10, 0.085, 0.07), (0.085, 0.07, 0.04)):
            a = np.asarray(a); b = np.asarray(b)
            sq0 = np.array([[-w0, 0, -w0 * 0.6], [w0, 0, -w0 * 0.6], [w0 * 0.5, 0, w0 * 0.7], [-w0 * 0.5, 0, w0 * 0.7]]) + a
            sq1 = np.array([[-w1, 0, -w1 * 0.6], [w1, 0, -w1 * 0.6], [w1 * 0.5, 0, w1 * 0.7], [-w1 * 0.5, 0, w1 * 0.7]]) + b
            M.add(g, tf(loft(sq0, sq1), R), 'cy_mid')
        M.add(g, tf(B(-0.03, 0.03, 0.40, 0.66, 0.90, 0.93), R), 'red_armor')
        M.add(g, tf(cbox(0, 0.20, 0.84, 0.05, 0.05, 0.05), R), 'rglow')
    # quantum core: faceted crystal with a glowing heart
    M.add(g, cyl((0, 0, 0.40), (0, 0, 0.52), 0.26, 0.20, n=6), 'cy_mid')
    M.add(g, cyl((0, 0, 0.52), (0, 0, 0.53), 0.21, n=6), 'red_armor')
    spike(M, g, ngon(0.17, 6, 0, 0, 30), 0.53, (0, 0, 1.02), 'rglow')
    for k in range(6):
        a = math.radians(60 * k)
        M.add(g, tf(B(-0.012, 0.012, 0.12, 0.22, 0.52, 0.56), rz(60 * k)), 'cy_dark')
    # hex deck panels between the arms
    for k in range(4):
        R = rz(45 + 90 * k)
        for (u, v) in ((1.12, -0.38), (1.12, 0.38)):
            M.add(g, tf(prism(ngon(0.10, 6, u, v, 0), DZ, DZ + 0.03, 0.85), R), 'cy_mid')
            M.add(g, tf(cyl((u, v, DZ + 0.03), (u, v, DZ + 0.04), 0.03, n=6), R), 'rglow')
    return M


# ================================================================== render driver
def teamfn(mp, X, Y, g):
    return (mp == MID['team']).astype(float)


def cell_of(spr, hm):
    out = np.zeros_like(spr)
    m = (hm > 0.45) & (spr[..., 3] > 0)
    out[m] = spr[m]
    out[m, 3] = 255
    return out


def tint(spr, col):
    o = spr.astype(float)
    o[..., :3] = o[..., :3] * hexc(col) / 255.0
    return o.astype(np.uint8)


def paste_c(dst, src, cx, cy):
    """Composite src centred at pixel (cx, cy) of dst."""
    D = Image.fromarray(dst)
    S = Image.fromarray(src)
    L = Image.new('RGBA', D.size, (0, 0, 0, 0))
    L.paste(S, (int(round(cx - S.width / 2)), int(round(cy - S.height / 2))), S)
    return np.array(Image.alpha_composite(D, L))


def outline_pad(spr, r):
    """rend.outline dilates with np.roll, which wraps parts near the canvas edge (muzzles) to the opposite edge."""
    p = r + 1
    return outline(np.pad(spr, ((p, p), (p, p), (0, 0))), r=r)[p:-p, p:-p]


def heat_pad(hm):
    return heat_sprite(np.pad(hm, 2))[2:-2, 2:-2]


def heat_of(names, grad=None):
    """Heat mask: glowing materials always, plus an optional (y0, y1) gradient on barrel metals toward the muzzle."""
    ids = [MID[m] for m in names]
    met = [MID[m] for m in ('metal', 'metal_light', 'hull_dark', 'cy_mid', 'cy_dark', 'bore')]

    def f(mp, X, Y, g):
        h = np.isin(mp, ids).astype(float)
        if grad:
            y0, y1 = grad
            h = np.maximum(h, np.where(np.isin(mp, met), np.clip((Y - y0) / (y1 - y0), 0, 1) * 0.8, 0))
        return h
    return f


def mech(name, M, guns, canvas=80, wcanvas=48):
    d = 'units'
    body, hm = layer(M, ['body'], canvas, teamfn)
    cell = cell_of(body, hm)
    body_ol = outline_pad(body, 3)
    save(body, d, name)
    save(body_ol, d, f'{name}-outline')
    save(cell, d, f'{name}-cell')
    leg = outline_pad(layer(M, ['leg'], canvas)[0], 2)
    base = outline_pad(layer(M, ['base'], canvas)[0], 2)
    save(leg, d, f'{name}-leg')
    save(base, d, f'{name}-base')
    # -full in engine order: legs, base, body + weapon outlines, body, cell, weapons (+cells) on top
    f = over(blank(canvas), leg)
    f = over(f, np.ascontiguousarray(leg[:, ::-1]))
    f = over(f, base)
    f = over(f, body_ol)
    tops = []
    for grp, wname, wx, wy, heat in guns:
        w, whm = layer(M, [grp], wcanvas, teamfn)
        wc = cell_of(w, whm)
        wol = outline_pad(w, 2)
        save(w, 'units/weapons', wname)
        save(wol, 'units/weapons', f'{wname}-outline')
        save(wc, 'units/weapons', f'{wname}-cell')
        if heat is not None:
            _, hh = layer(M, [grp], wcanvas, heat)
            save(heat_pad(hh), 'units/weapons', f'{wname}-heat')
        cx, cy = canvas / 2 + wx * 4, canvas / 2 - wy * 4
        f = paste_c(f, wol, cx, cy)
        tops.append((over(w, tint(wc, TEAM_PREVIEW)), cx, cy))
    f = over(f, body)
    f = over(f, tint(cell, TEAM_PREVIEW))
    for w, cx, cy in tops:
        f = paste_c(f, w, cx, cy)
    save(f, d, f'{name}-full')
    FULL[name] = f


def flyer(name, M, canvas=40):
    d = 'units'
    body, hm = layer(M, ['body'], canvas, teamfn)
    cell = cell_of(body, hm)
    ol = outline_pad(body, 2)
    save(body, d, name)
    save(ol, d, f'{name}-outline')
    save(cell, d, f'{name}-cell')
    f = over(over(blank(canvas), ol), body)
    f = over(f, tint(cell, TEAM_PREVIEW))
    save(f, d, f'{name}-full')
    FULL[name] = f


def core(name, M):
    d = 'blocks/cores'
    main, hm = layer(M, ['main'], 128, teamfn)
    team = cell_of(main, hm)
    save(main, d, name)
    save(team, d, f'{name}-team')
    f = over(main.copy(), tint(team, TEAM_PREVIEW))
    save(f, d, f'{name}-full')
    FULL[name] = f


def ntri(M, groups):
    return sum(len(T) for g in groups for T, _ in M.parts.get(g, []))


def main():
    only = set(sys.argv[1:])
    jobs = [
        ('acu-uef', acu_uef, lambda M: mech('acu-uef', M, [
            ('gunR', 'acu-uef-cannon', 6.0, 0.5, heat_of(('glow',), (0.30, 0.70))),
            ('gunL', 'acu-uef-launcher', -6.0, 0.5, None)]),
         ['leg', 'base', 'body', 'gunR', 'gunL']),
        ('acu-cybran', acu_cybran, lambda M: mech('acu-cybran', M, [
            ('gunR', 'acu-cybran-laser', 5.75, 0.75, heat_of(('rglow',), (0.30, 0.74))),
            ('gunL', 'acu-cybran-emp', -5.75, 0.75, heat_of(('rglow',), (0.15, 0.46)))]),
         ['leg', 'base', 'body', 'gunR', 'gunL']),
        ('engineer', engineer, lambda M: flyer('engineer', M), ['body']),
        ('core-uef', core_uef, lambda M: core('core-uef', M), ['main']),
        ('core-cybran', core_cybran, lambda M: core('core-cybran', M), ['main']),
    ]
    for name, build, render, groups in jobs:
        if only and name not in only:
            continue
        M = build()
        parts = ', '.join(f'{g} {ntri(M, [g])}' for g in groups)
        print(f'{name:12s} {M.ntri():6d} tris  ({parts})', flush=True)
        render(M)
    out = export.qa_sheet([k for k in ('acu-uef', 'acu-cybran', 'engineer', 'core-uef', 'core-cybran') if k in FULL],
                          'g_units-sheet.png', sc=3)
    if out:
        print('QA sheet:', out)


if __name__ == '__main__':
    main()
