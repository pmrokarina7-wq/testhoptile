"""Art workstream "industry B" (T3 UEF heat industry): heater, heat conduit, tungsten forge,
magnet factory, percussion drill, engineering bay.

    .venv/bin/python tools/art/g_industry_b.py

Writes every layer straight into mod/sprites (same names/canvases as before) and prints triangle counts.
Coordinates: 1.0 = one tile, Z up, origin = block centre. How v146 composes the layers:
  heater / heat-conduit  DrawDefault (main, unrotated) + DrawHeatOutput: -top1/-top2 rotated with the block
                          (-top2 = -top1 flipped, used for rotation 2/3), -heat rotated (output side = +x),
                          -glow unrotated; conduit also DrawHeatInput: -heat rotated toward every input side.
  tungsten-forge         main + DrawHeatInput (-heat = +x inlet, rotated per side) + DrawGlowRegion (-glow).
  magnet-factory         -bottom, -spinner (spinSprite around the centre), main (open in the middle), -glow.
  percussion-drill       main, -rotator (spins), -top, then the vanilla item marker in the centre.
  engineering-bay        main, -out (rotated, output = +x), unit, -top (drawn over the unit).
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *  # noqa: E402,F401,F403
from hero import *  # noqa: E402,F401,F403
from mats import Model, MID  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
import export  # noqa: E402
from export import save, layer, FULL  # noqa: E402
from rend import heat_sprite, over  # noqa: E402


# ------------------------------------------------------------------ helpers
def B(x0, x1, y0, y1, z0, z1):
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1)


def octp(r, cx=0.0, cy=0.0, rot=22.5):
    return P([(cx + r * math.cos(math.radians(rot + 45 * i)), cy + r * math.sin(math.radians(rot + 45 * i))) for i in range(8)])


def ray_hit(poly, a):
    d = (math.cos(a), math.sin(a))
    p = np.asarray(poly, float)
    best = 1e9
    for i in range(len(p)):
        A = p[i]
        E = p[(i + 1) % len(p)] - A
        den = -d[0] * E[1] + d[1] * E[0]
        if abs(den) < 1e-12:
            continue
        t = (-A[0] * E[1] + A[1] * E[0]) / den
        s = (d[0] * A[1] - d[1] * A[0]) / den
        if t > 1e-9 and -1e-9 <= s <= 1 + 1e-9:
            best = min(best, t)
    return best


def _quad(M, g, bot, top, z0, z1, m):
    bot = np.asarray(bot, float)
    top = np.asarray(top, float)
    if area(bot) < 0:
        bot, top = bot[::-1], top[::-1]
    M.add(g, loft(ring(bot, z0), ring(top, z1)), m)


def holed(M, g, outer, r_in, z0, z1, m, n=48, out_sc=1.0, r_top=None):
    """Plate with a round hole in the middle (built from wedges so earclip never sees a hole)."""
    r_top = r_in if r_top is None else r_top
    angs = sorted(set([round(math.atan2(p[1], p[0]) % (2 * math.pi), 6) for p in np.asarray(outer)] +
                      [round(2 * math.pi * i / n, 6) for i in range(n)]))
    angs.append(angs[0] + 2 * math.pi)
    for a0, a1 in zip(angs[:-1], angs[1:]):
        d0 = np.array([math.cos(a0), math.sin(a0)])
        d1 = np.array([math.cos(a1), math.sin(a1)])
        o0 = ray_hit(outer, a0) * d0
        o1 = ray_hit(outer, a1) * d1
        _quad(M, g, [r_in * d0, r_in * d1, o1, o0], [r_top * d0, r_top * d1, o1 * out_sc, o0 * out_sc], z0, z1, m)


def annulus(M, g, r0, r1, z0, z1, m, r0t=None, r1t=None, n=40, a0=0.0, a1=360.0, cx=0.0, cy=0.0):
    r0t = r0 if r0t is None else r0t
    r1t = r1 if r1t is None else r1t
    c = np.array([cx, cy])
    for i in range(n):
        b0 = math.radians(a0 + (a1 - a0) * i / n)
        b1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        e0 = np.array([math.cos(b0), math.sin(b0)])
        e1 = np.array([math.cos(b1), math.sin(b1)])
        _quad(M, g, [c + r0 * e0, c + r0 * e1, c + r1 * e1, c + r1 * e0],
              [c + r0t * e0, c + r0t * e1, c + r1t * e1, c + r1t * e0], z0, z1, m)


def beam(p0, p1, hw0, hh0, hw1=None, hh1=None, ch=0.0):
    """Straight beam between two 3D centre points; rectangular (optionally chamfered) section."""
    hw1 = hw0 if hw1 is None else hw1
    hh1 = hh0 if hh1 is None else hh1
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    s = np.array([-d[1], d[0], 0.0])
    s = s / np.linalg.norm(s) if np.linalg.norm(s) > 1e-9 else np.array([1.0, 0, 0])
    z = np.cross(d / np.linalg.norm(d), s)
    if z[2] < 0:
        z = -z

    def sec(p, hw, hh):
        c = min(ch, hw * 0.45, hh * 0.45)
        if c > 0:
            pts = [(-hw + c, -hh), (hw - c, -hh), (hw, -hh + c), (hw, hh - c), (hw - c, hh), (-hw + c, hh), (-hw, hh - c), (-hw, -hh + c)]
        else:
            pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        return np.array([p + s * a + z * b for a, b in pts])
    return loft(sec(p0, hw0, hh0), sec(p1, hw1, hh1))


def torus(M, g, R, r, z, m, n=28, k=10, cx=0.0, cy=0.0):
    for i in range(n):
        a, b = math.radians(360 * i / n), math.radians(360 * (i + 1) / n)
        M.add(g, cyl((cx + R * math.cos(a), cy + R * math.sin(a), z), (cx + R * math.cos(b), cy + R * math.sin(b), z), r, n=k), m)


def chevron(s=1.0):
    """'>'-shaped arrow pointing +x, about 0.2*s tiles tall."""
    return P([(-0.06 * s, -0.10 * s), (0.0, -0.10 * s), (0.07 * s, 0.0), (0.0, 0.10 * s), (-0.06 * s, 0.10 * s), (0.01 * s, 0.0)])


def bolt_ring(M, g, r, n, z, a0=0.0, rb=0.022, cx=0.0, cy=0.0, m='metal_light'):
    for i in range(n):
        a = math.radians(a0 + 360 * i / n)
        M.add(g, cyl((cx + r * math.cos(a), cy + r * math.sin(a), z - 0.01), (cx + r * math.cos(a), cy + r * math.sin(a), z + 0.02), rb, n=8), m)


def hazard_ring(M, g, r0, r1, z0, z1, n=16, a0=0.0, cx=0.0, cy=0.0):
    """Alternating yellow / dark ring segments (UEF hazard trim)."""
    for i in range(n):
        annulus(M, g, r0, r1, z0, z1 + (0.004 if i % 2 else 0.0), 'yellow' if i % 2 == 0 else 'hull_dark',
                n=3, a0=a0 + 360 * i / n, a1=a0 + 360 * (i + 1) / n, cx=cx, cy=cy)


def ore_pile(M, g, cx, cy, z, hw, hd, mat, n=7, seed=1, s=0.07):
    rng = np.random.RandomState(seed)
    for i in range(n):
        x = cx + rng.uniform(-hw, hw)
        y = cy + rng.uniform(-hd, hd)
        r = s * rng.uniform(0.7, 1.15)
        poly = P([(x + r * math.cos(a), y + r * math.sin(a) * 0.85) for a in np.radians(rng.uniform(0, 60) + np.arange(5) * 72)])
        M.add(g, prism(poly, z, z + r * rng.uniform(0.8, 1.3), 0.45), mat)


def rot_group(M, src, dst, R):
    M.parts.setdefault(dst, [])
    for T, m in M.parts.pop(src):
        M.parts[dst].append((tf(T, R), m))


# ================================================================== HEATER (2x2 HeatProducer, nozzle +x)
def heater():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.24), 0.0, 0.08, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(0.93, 0.93, 0.26), 0.08, 0.20, 0.955), 'hull_mid')
    # four side ports: louvred heat vents; the active one is hidden under the rotating nozzle (-top1)
    for k in range(4):
        S = rz(90 * k)
        M.add(g, tf(B(0.58, 0.95, -0.30, 0.30, 0.18, 0.225), S), 'hull_dark')
        M.add(g, tf(B(0.62, 0.92, -0.23, 0.23, 0.18, 0.21), S), 'heat')
        for y in (-0.165, -0.055, 0.055, 0.165):
            M.add(g, tf(B(0.62, 0.92, y - 0.026, y + 0.026, 0.18, 0.245), S), 'metal')
        M.add(g, tf(B(0.58, 0.61, -0.30, 0.30, 0.225, 0.25), S), 'yellow')
        for sy in (-1, 1):
            M.add(g, tf(cyl((0.88, sy * 0.36, 0.20), (0.88, sy * 0.36, 0.225), 0.022, n=8), S), 'metal_light')
    # corner chamfer plates with yellow tabs
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(g, prism(P([(sx * 0.93, sy * 0.52), (sx * 0.93, sy * 0.67), (sx * 0.67, sy * 0.93), (sx * 0.52, sy * 0.93)]), 0.20, 0.215), 'hull_dark')
    # --- heat-exchanger fin bank + burner chamber (centre)
    M.add(g, cyl((0, 0, 0.20), (0, 0, 0.34), 0.53, n=40), 'heat')
    nf = 20
    for i in range(nf):
        M.add(g, tf(B(0.27, 0.545, -0.03, 0.03, 0.20, 0.42), rz(360 * i / nf + 9)), 'metal')
    annulus(M, g, 0.545, 0.585, 0.20, 0.43, 'hull_dark', r1t=0.575, n=40)
    M.add(g, cyl((0, 0, 0.20), (0, 0, 0.52), 0.31, 0.30, n=32), 'hull_light')
    annulus(M, g, 0.17, 0.30, 0.52, 0.56, 'metal', r1t=0.27, r0t=0.19, n=32)
    M.add(g, cyl((0, 0, 0.50), (0, 0, 0.545), 0.19, n=28), 'hull_dark')
    M.add(g, cyl((0, 0, 0.50), (0, 0, 0.55), 0.14, n=24), 'flame')
    for x in (-0.07, 0.0, 0.07):
        M.add(g, B(x - 0.018, x + 0.018, -0.15, 0.15, 0.54, 0.575), 'metal')
    bolt_ring(M, g, 0.235, 8, 0.555, a0=22.5)
    for i in range(3):                                   # fuel injectors on the burner head
        a = math.radians(135 + 120 * i)
        x, y = 0.30 * math.cos(a), 0.30 * math.sin(a)
        M.add(g, cyl((x, y, 0.50), (x, y, 0.62), 0.045, n=10), 'metal_light')
        M.add(g, cyl((x, y, 0.56), (x, y, 0.59), 0.06, n=10), 'yellow')
    # --- corner TL: propellant hopper (charge bags)
    cx, cy = -0.63, 0.63
    M.add(g, prism(cham_rect(0.27, 0.27, 0.07, cx, cy), 0.20, 0.50, 0.93), 'hull_light')
    M.add(g, prism(cham_rect(0.19, 0.19, 0.05, cx, cy), 0.50, 0.505), 'vent')
    for dy in (-0.11, 0.0, 0.11):
        M.add(g, cyl((cx - 0.15, cy + dy, 0.49), (cx + 0.15, cy + dy, 0.49), 0.05, n=10), 'charge')
        M.add(g, cyl((cx - 0.02, cy + dy, 0.49), (cx + 0.02, cy + dy, 0.49), 0.055, n=10), 'copper')
    M.add(g, B(cx - 0.25, cx + 0.25, cy + 0.205, cy + 0.25, 0.49, 0.52), 'yellow')
    bolts(M, g, [(cx - 0.21, cy - 0.21), (cx + 0.21, cy - 0.21)], 0.48, r=0.02)
    cable(M, g, [(cx + 0.20, cy - 0.20, 0.38), (-0.30, 0.30, 0.52), (-0.21, 0.21, 0.60)], 0.03, m='metal_light', ends='yellow')
    # --- corner TR: exhaust stack
    cx, cy = 0.64, 0.64
    M.add(g, cyl((cx, cy, 0.20), (cx, cy, 0.30), 0.19, 0.17, n=20), 'hull_dark')
    M.add(g, cyl((cx, cy, 0.30), (cx, cy, 0.72), 0.135, n=20), 'metal')
    M.add(g, cyl((cx, cy, 0.58), (cx, cy, 0.62), 0.15, n=20), 'hull_mid')
    annulus(M, g, 0.085, 0.135, 0.72, 0.735, 'heat', r1t=0.125, n=20, cx=cx, cy=cy)
    M.add(g, cyl((cx, cy, 0.70), (cx, cy, 0.725), 0.085, n=16), 'bore')
    M.add(g, beam((0.28, 0.28, 0.42), (cx - 0.08, cy - 0.08, 0.42), 0.05, 0.05), 'hull_dark')
    # --- corner BL: igniter / control box
    cx, cy = -0.63, -0.63
    M.add(g, prism(cham_rect(0.25, 0.22, 0.06, cx, cy), 0.20, 0.42, 0.90), 'hull_light')
    M.add(g, B(cx - 0.17, cx + 0.05, cy + 0.06, cy + 0.15, 0.42, 0.435), 'glass')
    light(M, g, cx + 0.13, cy + 0.10, 0.42, 0.05, 0.05)
    M.add(g, B(cx - 0.18, cx + 0.18, cy - 0.14, cy - 0.10, 0.42, 0.44), 'yellow')
    bolts(M, g, [(cx - 0.17, cy - 0.04), (cx + 0.17, cy - 0.04)], 0.42, r=0.018)
    cable(M, g, [(cx + 0.16, cy + 0.16, 0.36), (-0.30, -0.30, 0.46), (-0.20, -0.20, 0.58)], 0.03, ends='yellow')
    # --- corner BR: combustion-air blower
    cx, cy = 0.62, -0.62
    M.add(g, cyl((cx, cy, 0.20), (cx, cy, 0.36), 0.25, 0.23, n=28), 'hull_mid')
    M.add(g, cyl((cx, cy, 0.34), (cx, cy, 0.37), 0.19, n=28), 'vent')
    for i in range(7):
        a = 360 * i / 7
        M.add(g, tf(prism(P([(0.03, -0.022), (0.18, -0.05), (0.18, 0.01), (0.03, 0.022)]), 0.35, 0.385), rz(a), (cx, cy, 0)), 'metal')
    M.add(g, cyl((cx, cy, 0.36), (cx, cy, 0.40), 0.05, n=12), 'metal_light')
    annulus(M, g, 0.19, 0.25, 0.36, 0.40, 'metal', r1t=0.235, n=28, cx=cx, cy=cy)
    for s in (-1, 1):                                    # finger guard
        M.add(g, tf(B(-0.20, 0.20, -0.012, 0.012, 0.395, 0.41), rz(45 + s * 45), (cx, cy, 0)), 'hull_dark')

    # ================= -top1: output duct + nozzle facing +x
    g = 'top'
    M.add(g, prism(rect(0.66, -0.01, 0.33, 0.335), 0.20, 0.235, 0.97), 'hull_dark')
    M.add(g, beam((0.27, 0, 0.36), (0.80, 0, 0.345), 0.25, 0.13, 0.215, 0.115, ch=0.05), 'hull_light')
    M.add(g, beam((0.31, 0, 0.36), (0.37, 0, 0.36), 0.265, 0.145, ch=0.05), 'yellow')
    for x in np.linspace(0.44, 0.72, 5):
        M.add(g, B(x - 0.024, x + 0.024, -0.235, 0.235, 0.24, 0.515), 'metal')
    M.add(g, B(0.42, 0.745, -0.17, 0.17, 0.30, 0.485), 'heat')
    M.add(g, beam((0.80, 0, 0.345), (0.87, 0, 0.345), 0.30, 0.16, ch=0.05), 'hull_dark')
    for y in (-0.24, -0.08, 0.08, 0.24):
        M.add(g, cyl((0.835, y, 0.49), (0.835, y, 0.515), 0.02, n=8), 'metal_light')
    M.add(g, beam((0.87, 0, 0.34), (0.985, 0, 0.34), 0.24, 0.125, ch=0.04), 'metal')
    M.add(g, B(0.895, 0.99, -0.175, 0.175, 0.24, 0.475), 'heat')
    for y in (-0.09, 0.0, 0.09):
        M.add(g, B(0.89, 0.99, y - 0.017, y + 0.017, 0.24, 0.49), 'metal')
    for sy in (-1, 1):                                   # side clamps
        M.add(g, B(0.50, 0.62, sy * 0.21, sy * 0.30, 0.20, 0.36), 'hull_mid')
        M.add(g, cyl((0.56, sy * 0.265, 0.36), (0.56, sy * 0.265, 0.38), 0.022, n=8), 'metal_light')
    return M


def heater_glow(mp, X, Y, g):
    ang = np.degrees(np.arctan2(Y, X))
    diag = np.abs(((ang + 45) % 90) - 45) > 22
    r = np.hypot(X, Y)
    fl = (mp == MID['flame']).astype(float)
    fins = ((mp == MID['heat']) & diag & (r < 0.56)).astype(float) * 0.55
    stack = ((mp == MID['heat']) & (np.hypot(X - 0.64, Y - 0.64) < 0.16)).astype(float) * 0.7
    return np.maximum(fl, np.maximum(fins, stack))


def heater_heat(mp, X, Y, g):
    h = mp == MID['heat']
    return np.where(h & (X > 0.86), 1.0, np.where(h, 0.6, 0.0))


# ================================================================== HEAT CONDUIT (1x1, input -x, output +x)
def heat_conduit():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(0.49, 0.49, 0.10), 0.0, 0.06, 0.98), 'hull_dark')
    M.add(g, prism(cham_rect(0.45, 0.45, 0.11), 0.06, 0.13, 0.93), 'hull_mid')
    M.add(g, B(-0.47, 0.47, -0.12, 0.12, 0.12, 0.135), 'vent')
    M.add(g, B(-0.12, 0.12, -0.47, 0.47, 0.12, 0.135), 'vent')
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(g, prism(P([(sx * 0.43, sy * 0.25), (sx * 0.43, sy * 0.34), (sx * 0.34, sy * 0.43), (sx * 0.25, sy * 0.43)]), 0.13, 0.165, 0.85), 'hull_light')
            M.add(g, cyl((sx * 0.20, sy * 0.36, 0.125), (sx * 0.20, sy * 0.36, 0.15), 0.025, n=8), 'metal_light')
    g = 'top'
    zc, r = 0.27, 0.15
    for y in (-0.21, 0.21):                              # cradle rails (carry the pipe's own shadow)
        M.add(g, B(-0.47, 0.47, y - 0.045, y + 0.045, 0.12, 0.16), 'hull_dark')
    M.add(g, cyl((-0.42, 0, zc), (0.42, 0, zc), r * 0.80, n=16), 'heat')
    for a, b in ((-0.29, -0.11), (0.11, 0.29)):          # insulation jacket with rib bands
        M.add(g, cyl((a, 0, zc), (b, 0, zc), r, n=18), 'hull_light')
        M.add(g, cyl(((a + b) / 2 - 0.025, 0, zc), ((a + b) / 2 + 0.025, 0, zc), r * 1.08, n=18), 'hull_mid')
    # centre clamp block with the flow arrow
    M.add(g, B(-0.11, 0.11, -0.20, 0.20, 0.12, zc + r + 0.02), 'hull_dark')
    M.add(g, B(-0.11, 0.11, -0.20, -0.16, 0.12, zc + r + 0.035), 'yellow')
    M.add(g, B(-0.11, 0.11, 0.16, 0.20, 0.12, zc + r + 0.035), 'yellow')
    M.add(g, prism(P([(-0.07, -0.11), (0.09, 0.0), (-0.07, 0.11)]), zc + r + 0.02, zc + r + 0.045), 'yellow')
    for s in (-1, 1):                                    # end flanges
        M.add(g, cyl((s * 0.41, 0, zc), (s * 0.495, 0, zc), 0.205, n=18), 'metal')
        M.add(g, cyl((s * 0.395, 0, zc), (s * 0.41, 0, zc), 0.19, n=18), 'hull_dark')
        for y in (-0.12, 0.12):
            zt = zc + math.sqrt(max(0.205 ** 2 - y * y, 0))
            M.add(g, cyl((s * 0.452, y, zt - 0.01), (s * 0.452, y, zt + 0.018), 0.022, n=6), 'metal_light')
    return M


def conduit_heat(mp, X, Y, g):
    return (mp == MID['heat']).astype(float)


# ================================================================== TUNGSTEN FORGE (3x3 HeatCrafter)
def tungsten_forge():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(1.485, 1.485, 0.34), 0.0, 0.12, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.40, 1.40, 0.36), 0.12, 0.28, 0.96), 'hull_mid')
    # heat inlets on every side (the +x one is masked into -heat and rotated by the engine)
    for k in range(4):
        S = rz(90 * k)
        M.add(g, tf(prism(rect(1.28, 0, 0.17, 0.33), 0.12, 0.44, 0.90), S), 'hull_light')
        M.add(g, tf(B(1.40, 1.49, -0.24, 0.24, 0.16, 0.38), S), 'heat')
        for u in (1.16, 1.36):
            M.add(g, tf(B(u - 0.03, u + 0.03, -0.355, 0.355, 0.12, 0.465), S), 'tung')
        M.add(g, tf(B(1.21, 1.31, -0.20, 0.20, 0.40, 0.46), S), 'heat')
        bolts_R(M, g, [(1.26, -0.27), (1.26, 0.27)], 0.44, S, r=0.022)
        M.add(g, tf(cyl((1.14, 0, 0.40), (0.80, 0, 0.40), 0.11, n=14), S), 'heat')
        M.add(g, tf(cyl((0.94, 0, 0.40), (1.01, 0, 0.40), 0.145, n=14), S), 'tung')
        for t in (-0.64, 0.64):                          # deck bolts
            bolts_R(M, g, [(1.30, t - 0.06), (1.30, t + 0.06)], 0.28, S, r=0.024)
    # --- central furnace housing with inset panels
    M.add(g, prism(cham_rect(0.88, 0.88, 0.26), 0.28, 0.52, 0.94), 'hull_light')
    for k in range(4):
        S = rz(90 * k)
        for t0, t1 in ((-0.66, -0.20), (0.20, 0.66)):
            M.add(g, tf(prism(rect(0.70, (t0 + t1) / 2, 0.08, (t1 - t0) / 2), 0.50, 0.535, 0.9), S), 'hull_mid')
    bolts(M, g, [(-0.72, -0.72), (0.72, -0.72), (-0.72, 0.72), (0.72, 0.72)], 0.52, r=0.026)
    # crucible: hollow tungsten pot on trunnions, molten pool inside
    cx, cy = -0.30, 0.10
    annulus(M, g, 0.36, 0.50, 0.50, 0.84, 'tung', r1t=0.46, n=36, cx=cx, cy=cy)
    annulus(M, g, 0.35, 0.46, 0.84, 0.88, 'metal', r0t=0.37, r1t=0.43, n=36, cx=cx, cy=cy)
    M.add(g, cyl((cx, cy, 0.50), (cx, cy, 0.76), 0.37, n=32), 'flame')
    for (dx, dy, s) in ((-0.14, 0.13, 0.075), (0.15, -0.08, 0.05), (-0.04, -0.20, 0.045), (0.06, 0.21, 0.04)):     # slag crust
        M.add(g, prism(P([(cx + dx + s * math.cos(a), cy + dy + s * 0.8 * math.sin(a)) for a in np.radians(np.arange(6) * 60 + 13)]), 0.75, 0.775, 0.6), 'tung')
    M.add(g, B(cx + 0.40, cx + 0.62, cy - 0.09, cy + 0.09, 0.70, 0.85), 'tung')             # pour lip
    M.add(g, B(cx + 0.36, cx + 0.62, cy - 0.04, cy + 0.04, 0.80, 0.86), 'flame')
    for sy in (-1, 1):
        M.add(g, cyl((cx, cy + sy * 0.48, 0.70), (cx, cy + sy * 0.62, 0.70), 0.09, n=14), 'metal_light')
        M.add(g, cyl((cx, cy + sy * 0.62, 0.70), (cx, cy + sy * 0.66, 0.70), 0.10, n=14), 'yellow')
        M.add(g, B(cx - 0.12, cx + 0.12, cy + sy * 0.58, cy + sy * 0.72, 0.52, 0.66), 'hull_dark')
    # forging press (portal frame, hydraulic ram, hammer, glowing billet)
    px, py = 0.44, -0.14
    M.add(g, prism(cham_rect(0.26, 0.34, 0.06, px, py), 0.52, 0.66, 0.92), 'tung')
    M.add(g, B(px - 0.20, px + 0.20, py - 0.30, py + 0.32, 0.66, 0.72), 'flame')
    for t in (-0.18, 0.06, 0.24):
        M.add(g, B(px - 0.21, px + 0.21, py + t - 0.02, py + t + 0.02, 0.66, 0.73), 'tung')
    for yy in (py + 0.52, py - 0.52):
        M.add(g, cyl((px, yy, 0.52), (px, yy, 0.58), 0.13, n=16), 'hull_dark')
        M.add(g, cyl((px, yy, 0.58), (px, yy, 1.06), 0.09, n=16), 'hull_light')
    M.add(g, B(px - 0.18, px + 0.18, py - 0.16, py + 0.12, 0.84, 1.02), 'tung')              # hammer head
    M.add(g, prism(rect(px, py, 0.10, 0.60), 1.02, 1.14, 0.92), 'hull_light')                   # crossbeam
    for t in (-0.46, -0.30, 0.30, 0.46):
        M.add(g, tf(prism(chevron(0.55), 1.14, 1.15), rz(90 if t < 0 else -90), (px, py + t, 0)), 'yellow')
    M.add(g, cyl((px, py, 1.14), (px, py, 1.27), 0.15, 0.145, n=20), 'metal_light')
    annulus(M, g, 0.06, 0.15, 1.27, 1.29, 'hull_dark', r1t=0.13, n=20, cx=px, cy=py)
    M.add(g, cyl((px, py, 1.27), (px, py, 1.33), 0.06, n=12), 'metal')
    cable(M, g, [(px + 0.10, py + 0.08, 1.24), (px + 0.36, py + 0.30, 1.05), (0.96, 0.46, 0.62), (1.04, 0.62, 0.40)], 0.035, ends='yellow')
    # --- corner TL: wolframite hopper + feed chute
    cx, cy = -1.06, 1.06
    M.add(g, prism(cham_rect(0.31, 0.31, 0.08, cx, cy), 0.28, 0.66, 0.92), 'hull_light')
    M.add(g, prism(cham_rect(0.23, 0.23, 0.06, cx, cy), 0.66, 0.665), 'vent')
    ore_pile(M, g, cx, cy, 0.62, 0.15, 0.15, 'ore_wolf', n=9, seed=4, s=0.075)
    M.add(g, B(cx - 0.29, cx + 0.29, cy + 0.255, cy + 0.30, 0.64, 0.68), 'yellow')
    M.add(g, beam((cx + 0.22, cy - 0.22, 0.72), (-0.58, 0.48, 0.90), 0.055, 0.04, ch=0.015), 'hull_mid')
    M.add(g, beam((cx + 0.18, cy - 0.18, 0.70), (cx + 0.26, cy - 0.26, 0.72), 0.085, 0.06), 'hull_dark')
    # --- corner TR: flue stack
    cx, cy = 1.06, 1.06
    M.add(g, cyl((cx, cy, 0.28), (cx, cy, 0.40), 0.26, 0.24, n=24), 'hull_dark')
    M.add(g, cyl((cx, cy, 0.40), (cx, cy, 0.98), 0.19, 0.17, n=24), 'metal')
    for z0 in (0.56, 0.78):
        M.add(g, cyl((cx, cy, z0), (cx, cy, z0 + 0.05), 0.195, n=24), 'hull_mid')
    annulus(M, g, 0.115, 0.175, 0.98, 1.00, 'heat', r1t=0.16, n=24, cx=cx, cy=cy)
    M.add(g, cyl((cx, cy, 0.96), (cx, cy, 0.99), 0.115, n=20), 'bore')
    for a in (200, 250):                                 # stay brackets
        M.add(g, tf(B(0.17, 0.30, -0.03, 0.03, 0.28, 0.50), rz(a), (cx, cy, 0)), 'hull_dark')
    # --- corner BL: control cabin
    cx, cy = -1.06, -1.06
    M.add(g, prism(cham_rect(0.30, 0.27, 0.07, cx, cy), 0.28, 0.62, 0.90), 'hull_light')
    M.add(g, B(cx - 0.20, cx + 0.12, cy + 0.10, cy + 0.20, 0.62, 0.635), 'glass')
    light(M, g, cx + 0.18, cy + 0.15, 0.62, 0.06, 0.06)
    M.add(g, B(cx - 0.24, cx + 0.24, cy - 0.20, cy - 0.15, 0.62, 0.645), 'yellow')
    antenna(M, g, (cx - 0.16, cy - 0.04, 0.62), (cx - 0.22, cy - 0.04, 1.00))
    cable(M, g, [(cx + 0.24, cy + 0.10, 0.50), (-0.62, -0.72, 0.60), (-0.10, -0.78, 0.56)], 0.035, ends='yellow')
    # --- corner BR: rack of finished tungsten cores
    cx, cy = 1.06, -1.06
    M.add(g, prism(cham_rect(0.30, 0.28, 0.06, cx, cy), 0.28, 0.38, 0.95), 'hull_dark')
    for i, dy in enumerate((-0.16, -0.05, 0.06, 0.17)):
        y = cy + dy
        M.add(g, cyl((cx - 0.22, y, 0.44), (cx + 0.12, y, 0.44), 0.05, n=10), 'tung')
        M.add(g, cyl((cx + 0.12, y, 0.44), (cx + 0.24, y, 0.44), 0.05, 0.012, n=10), 'metal_light')
        M.add(g, cyl((cx - 0.24, y, 0.44), (cx - 0.20, y, 0.44), 0.055, n=10), 'copper')
    for x in (cx - 0.13, cx + 0.05):
        M.add(g, B(x - 0.025, x + 0.025, cy - 0.25, cy + 0.25, 0.38, 0.47), 'yellow')
    return M


def forge_glow(mp, X, Y, g):
    fl = (mp == MID['flame']).astype(float)
    flue = ((mp == MID['heat']) & (np.hypot(X - 1.06, Y - 1.06) < 0.2)).astype(float) * 0.7
    return np.maximum(fl, flue)


def forge_heat(mp, X, Y, g):
    return ((mp == MID['heat']) & (X > 0.78) & (np.abs(Y) < 0.40)).astype(float)


# ================================================================== MAGNET FACTORY (2x2, winding drum spinner)
RIN = 0.44


def magnet_factory():
    M = Model()
    g = 'bottom'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.24), 0.0, 0.08, 0.985), 'hull_dark')
    M.add(g, cyl((0, 0, 0.08), (0, 0, 0.09), 0.52, n=32), 'vent')
    annulus(M, g, 0.405, 0.52, 0.08, 0.13, 'magnet', r0t=0.41, n=32)
    for i in range(16):
        M.add(g, tf(cbox(0.42, 0, 0.125, 0.04, 0.035, 0.05), rz(22.5 * i)), 'metal')
    # --- spinner: winding drum (6 wound poles), drawn rotating under the housing
    g = 'spinner'
    zb = 0.10
    M.add(g, cyl((0, 0, zb), (0, 0, zb + 0.05), 0.395, 0.385, n=36), 'hull_dark')
    annulus(M, g, 0.33, 0.39, zb + 0.05, zb + 0.08, 'metal', r1t=0.375, n=36)
    for i in range(6):
        R = rz(60 * i)
        M.add(g, tf(prism(rect(0.24, 0, 0.11, 0.045), zb + 0.05, zb + 0.13, 0.9), R), 'magnet')
        M.add(g, tf(prism(rect(0.215, 0, 0.075, 0.088), zb + 0.05, zb + 0.17, 0.86), R), 'copper')
        M.add(g, tf(B(0.205, 0.225, -0.09, 0.09, zb + 0.05, zb + 0.175), R), 'coil')
        M.add(g, tf(prism(P([(0.30, -0.10), (0.37, -0.12), (0.37, 0.12), (0.30, 0.10)]), zb + 0.05, zb + 0.15, 0.9), R), 'magnet')
    M.add(g, tf(B(0.32, 0.37, -0.03, 0.03, zb + 0.15, zb + 0.165), None), 'yellow')        # index mark
    M.add(g, cyl((0, 0, zb), (0, 0, zb + 0.20), 0.12, 0.11, n=20), 'hull_light')
    M.add(g, cyl((0, 0, zb + 0.20), (0, 0, zb + 0.215), 0.055, n=12), 'metal_light')
    bolt_ring(M, g, 0.085, 3, zb + 0.20, a0=30, rb=0.018)
    # --- main housing (open in the middle)
    g = 'main'
    holed(M, g, cham_rect(0.985, 0.985, 0.24), RIN + 0.02, 0.0, 0.10, 'hull_dark', n=32, out_sc=0.985)
    holed(M, g, cham_rect(0.93, 0.93, 0.26), RIN + 0.05, 0.10, 0.24, 'hull_mid', n=32, out_sc=0.955)
    annulus(M, g, RIN, RIN + 0.085, 0.18, 0.31, 'metal', r0t=RIN + 0.02, r1t=RIN + 0.07, n=36)
    annulus(M, g, RIN, RIN + 0.02, 0.18, 0.295, 'pglow', n=36)
    bolt_ring(M, g, RIN + 0.105, 12, 0.24, a0=15, rb=0.018)
    for k in range(4):
        a = 45 + 90 * k
        R = rz(a)
        M.add(g, tf(prism(rect(0.66, 0, 0.12, 0.085), 0.24, 0.40, 0.86), R), 'magnet')       # stator yoke
        M.add(g, tf(B(0.56, 0.60, -0.09, 0.09, 0.24, 0.42), R), 'hull_dark')
        cx, cy = 0.99 * math.cos(math.radians(a)), 0.99 * math.sin(math.radians(a))
        # magnetising coil: copper winding seen end-on around a neodymium core with a glowing pole
        M.add(g, cyl((cx, cy, 0.24), (cx, cy, 0.30), 0.225, n=20), 'hull_dark')
        M.add(g, cyl((cx, cy, 0.30), (cx, cy, 0.46), 0.205, n=20), 'coil')
        annulus(M, g, 0.15, 0.205, 0.30, 0.49, 'copper', r1t=0.19, r0t=0.155, n=20, cx=cx, cy=cy)
        annulus(M, g, 0.105, 0.15, 0.30, 0.47, 'coil', n=20, cx=cx, cy=cy)
        M.add(g, cyl((cx, cy, 0.30), (cx, cy, 0.52), 0.105, 0.095, n=16), 'magnet')
        M.add(g, cyl((cx, cy, 0.52), (cx, cy, 0.53), 0.055, n=12), 'pglow')
        for s in (-1, 1):                                # clamp straps across the winding
            M.add(g, tf(B(-0.215, 0.215, s * 0.02 - 0.018, s * 0.02 + 0.018, 0.30, 0.50), rz(a + 90 + s * 45), (cx, cy, 0)), 'hull_mid')
    # +y: chlorine feed line with valve
    M.add(g, B(-0.40, 0.40, 0.70, 0.86, 0.24, 0.27), 'hull_dark')
    M.add(g, cyl((-0.46, 0.78, 0.33), (0.46, 0.78, 0.33), 0.055, n=12), 'chlor')
    for x in (-0.30, 0.30):
        M.add(g, cyl((x - 0.025, 0.78, 0.33), (x + 0.025, 0.78, 0.33), 0.085, n=12), 'metal')
    M.add(g, cyl((0, 0.78, 0.33), (0, 0.78, 0.44), 0.04, n=10), 'metal')
    M.add(g, cyl((0, 0.78, 0.44), (0, 0.78, 0.47), 0.10, n=14), 'yellow')
    M.add(g, cyl((0, 0.78, 0.47), (0, 0.78, 0.48), 0.035, n=10), 'hull_dark')
    M.add(g, beam((0.0, 0.70, 0.30), (0.0, 0.56, 0.28), 0.05, 0.04), 'chlor')
    # -y: power bus
    M.add(g, prism(rect(0, -0.78, 0.36, 0.10), 0.24, 0.36, 0.88), 'hull_light')
    chevrons(M, g, 0, -0.78, 0.36, 0.56, 0.12, n=5)
    light(M, g, -0.30, -0.78, 0.36, 0.04, 0.05)
    light(M, g, 0.30, -0.78, 0.36, 0.04, 0.05)
    # -x: neodymite intake hopper
    M.add(g, prism(rect(-0.79, 0, 0.11, 0.30), 0.24, 0.44, 0.88), 'hull_light')
    M.add(g, prism(rect(-0.79, 0, 0.07, 0.24), 0.44, 0.445), 'vent')
    ore_pile(M, g, -0.79, 0.0, 0.41, 0.04, 0.17, 'ore_neo', n=5, seed=7, s=0.055)
    # +x: output tray of finished magnets
    M.add(g, prism(rect(0.79, 0, 0.11, 0.30), 0.24, 0.34, 0.92), 'hull_dark')
    for y in (-0.18, -0.06, 0.06, 0.18):
        M.add(g, prism(rect(0.79, y, 0.07, 0.04), 0.34, 0.40, 0.85), 'magnet')
        M.add(g, B(0.73, 0.75, y - 0.04, y + 0.04, 0.34, 0.405), 'red_armor')
    M.add(g, B(0.68, 0.90, 0.28, 0.31, 0.34, 0.38), 'yellow')
    return M


def magnet_glow(mp, X, Y, g):
    return np.isin(mp, [MID['pglow'], MID['glow']]).astype(float)


# ================================================================== PERCUSSION DRILL (3x3)
RW = 0.86


def percussion_drill():
    M = Model()
    g = 'main'
    holed(M, g, cham_rect(1.485, 1.485, 0.36), RW + 0.02, 0.0, 0.12, 'hull_dark', n=32, out_sc=0.985)
    holed(M, g, cham_rect(1.40, 1.40, 0.38), RW + 0.10, 0.12, 0.30, 'hull_mid', n=32, out_sc=0.96, r_top=RW + 0.14)
    M.add(g, cyl((0, 0, 0.0), (0, 0, 0.03), RW + 0.06, n=32), 'bore')
    annulus(M, g, RW - 0.01, RW + 0.10, 0.04, 0.34, 'metal', r0t=RW + 0.01, r1t=RW + 0.09, n=40)
    hazard_ring(M, g, RW + 0.13, RW + 0.24, 0.28, 0.315, n=20, a0=4.5)
    for k in range(4):
        a = 45 + 90 * k
        buttress(M, g, a, 1.12, 1.84, 0.22, 0.50, 0.16, z0=0.10, mat='hull_light', inlay='yellow', tip='glow')
    for k in (0, 2):                                     # drive motors with pinions (+x, -x)
        S = rz(90 * k)
        M.add(g, tf(prism(rect(1.24, 0, 0.16, 0.40), 0.28, 0.40, 0.92), S), 'hull_dark')
        M.add(g, tf(cyl((1.24, -0.36, 0.52), (1.24, 0.30, 0.52), 0.15, n=18), S), 'hull_light')
        for y in np.linspace(-0.26, 0.20, 6):
            M.add(g, tf(cyl((1.24, y, 0.52), (1.24, y + 0.03, 0.52), 0.17, n=14), S), 'metal')
        M.add(g, tf(cyl((1.24, 0.30, 0.52), (1.24, 0.38, 0.52), 0.13, n=18), S), 'hull_dark')
        M.add(g, tf(cyl((1.24, -0.42, 0.52), (1.24, -0.36, 0.52), 0.16, n=18), S), 'yellow')
        M.add(g, tf(cyl((1.24, 0.38, 0.52), (1.24, 0.41, 0.52), 0.06, n=12), S), 'metal_light')
        M.add(g, tf(cyl((1.02, 0, 0.30), (1.02, 0, 0.44), 0.10, n=16), S), 'metal')
        for i in range(8):
            M.add(g, tf(cbox(0.105, 0, 0.37, 0.04, 0.035, 0.12), rz(45 * i), (1.02, 0, 0)), 'metal')
        M.add(g, tf(beam((1.02, 0, 0.42), (1.24, 0, 0.42), 0.05, 0.04), S), 'metal_light')
    for k in (1, 3):                                     # hydraulic power packs for the hammer (+y, -y)
        S = rz(90 * k)
        M.add(g, tf(prism(rect(1.22, 0, 0.16, 0.42), 0.28, 0.38, 0.92), S), 'hull_dark')
        for t in (-0.25, 0.25):
            M.add(g, tf(cyl((1.22, t, 0.38), (1.22, t, 0.64), 0.12, n=18), S), 'metal_light')
            M.add(g, tf(cyl((1.22, t, 0.64), (1.22, t, 0.68), 0.10, 0.08, n=18), S), 'yellow')
            M.add(g, tf(cyl((1.22, t, 0.48), (1.22, t, 0.51), 0.125, n=18), S), 'hull_mid')
        grille(M, g, 1.22, 0, 0.38, 0.14, 0.20, n=3, glow="glow", R=S)
    bolt_ring(M, g, RW + 0.36, 16, 0.30, a0=11.25, rb=0.024)

    # --- rotator: percussion drill head (3 cutter arms, carbide buttons, rim teeth)
    g = 'rotator'
    R0 = 0.80
    M.add(g, cyl((0, 0, 0.03), (0, 0, 0.16), R0, R0 - 0.04, n=40), 'tung')
    for i in range(30):
        M.add(g, tf(cbox(R0 + 0.015, 0, 0.10, 0.05, 0.06, 0.10), rz(12 * i)), 'metal')
    for k in range(3):
        R = rz(120 * k)
        M.add(g, tf(prism(P([(0.12, -0.15), (0.78, -0.11), (0.80, 0.0), (0.78, 0.11), (0.12, 0.15)]), 0.16, 0.30, 0.88), R), 'hull_light')
        M.add(g, tf(prism(P([(0.20, -0.05), (0.70, -0.035), (0.70, 0.035), (0.20, 0.05)]), 0.30, 0.31), R), 'steel')
        for u in (0.34, 0.50, 0.66):
            for v in (-0.075, 0.075):
                M.add(g, tf(cyl((u, v, 0.28), (u, v, 0.33), 0.032, n=8), R), 'metal_light')
        Rf = rz(120 * k + 60)
        M.add(g, tf(prism(P([(0.34, -0.035), (0.76, -0.10), (0.76, 0.10), (0.34, 0.035)]), 0.15, 0.165), Rf), 'bore')
        for (u, dv) in ((0.46, -0.20), (0.62, -0.25), (0.46, 0.20), (0.62, 0.25), (0.30, 0.0)):
            a = math.radians(120 * k + 60) + dv
            M.add(g, cyl((u * math.cos(a), u * math.sin(a), 0.14), (u * math.cos(a), u * math.sin(a), 0.19), 0.03, n=8), 'metal_light')
    M.add(g, cyl((0, 0, 0.16), (0, 0, 0.34), 0.20, 0.18, n=24), 'metal')

    # --- top: four-leg hammer frame with the percussion hammer housing in the centre
    g = 'top'
    for k in range(4):
        a = 45 + 90 * k
        R = rz(a)
        M.add(g, tf(prism(rect(1.30, 0, 0.13, 0.15), 0.30, 0.56, 0.88), R), 'hull_dark')
        M.add(g, tf(beam((1.30, 0, 0.60), (0.28, 0, 0.99), 0.09, 0.06, 0.075, 0.055, ch=0.03), R), 'hull_mid')
        M.add(g, tf(beam((1.24, 0, 0.64), (0.36, 0, 0.98), 0.045, 0.012), R, (0, 0, 0.05)), 'hull_light')
        for u in (1.02, 0.62):                           # strut clamp bands
            zc = 0.60 + (1.30 - u) / 1.02 * 0.39
            M.add(g, tf(B(u - 0.03, u + 0.03, -0.10, 0.10, zc - 0.07, zc + 0.075), R), 'metal')
        cable(M, g, [tuple(R @ np.array([1.26, 0.14, 0.52])), tuple(R @ np.array([0.80, 0.12, 0.80])), tuple(R @ np.array([0.36, 0.11, 0.96]))], 0.025, ends='yellow')
        M.add(g, tf(cyl((1.30, 0, 0.56), (1.30, 0, 0.66), 0.075, n=12), R), 'metal_light')
        M.add(g, tf(B(1.36, 1.42, -0.15, 0.15, 0.30, 0.565), R), 'yellow')
        Rh = rz(90 * k)                                  # hammer actuators between the legs
        M.add(g, tf(cyl((0.37, 0, 0.62), (0.37, 0, 0.98), 0.07, n=14), Rh), 'metal_light')
        M.add(g, tf(cyl((0.37, 0, 0.98), (0.37, 0, 1.02), 0.085, 0.07, n=14), Rh), 'hull_dark')
    M.add(g, cyl((0, 0, 0.86), (0, 0, 1.06), 0.31, 0.29, n=32), 'hull_light')
    annulus(M, g, 0.19, 0.29, 1.06, 1.10, 'metal', r1t=0.27, r0t=0.20, n=32)
    hazard_ring(M, g, 0.205, 0.255, 1.095, 1.105, n=12)
    M.add(g, cyl((0, 0, 1.06), (0, 0, 1.11), 0.19, n=28), 'hull_dark')
    M.add(g, prism(cham_rect(0.10, 0.10, 0.025), 1.11, 1.115), 'vent')
    bolt_ring(M, g, 0.145, 6, 1.11, a0=0, rb=0.018)
    return M


# ================================================================== ENGINEERING BAY (3x3 UnitFactory)
def engineering_bay():
    M = Model()
    g = 'main'
    M.add(g, prism(cham_rect(1.485, 1.485, 0.32), 0.0, 0.10, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.41, 1.41, 0.34), 0.10, 0.22, 0.97), 'hull_mid')
    # assembly pad: octagon, hazard ring, grating, guide lights
    M.add(g, prism(octp(0.92), 0.22, 0.30, 0.955), 'hull_light')
    M.add(g, prism(octp(0.80), 0.30, 0.31), 'hull_dark')
    for i in range(8):
        a0 = 22.5 + 45 * i
        pa = [(0.80 * math.cos(math.radians(a0)), 0.80 * math.sin(math.radians(a0))),
              (0.80 * math.cos(math.radians(a0 + 45)), 0.80 * math.sin(math.radians(a0 + 45)))]
        pb = [(0.73 * math.cos(math.radians(a0 + 45)), 0.73 * math.sin(math.radians(a0 + 45))),
              (0.73 * math.cos(math.radians(a0)), 0.73 * math.sin(math.radians(a0)))]
        q = np.array(pa + pb)
        for j in range(3):                               # slanted yellow hazard bars on each octagon side
            t0, t1 = (j * 2 + 0.3) / 6.0, (j * 2 + 1.3) / 6.0
            s0, s1 = t0 + 0.07, t1 + 0.07
            A = q[0] + (q[1] - q[0]) * t0
            Bp = q[0] + (q[1] - q[0]) * t1
            C = q[3] + (q[2] - q[3]) * s1
            D = q[3] + (q[2] - q[3]) * s0
            M.add(g, prism(P([A, Bp, C, D]), 0.31, 0.318), 'yellow')
    M.add(g, prism(octp(0.70), 0.30, 0.312), 'vent')
    ap = 0.70 * math.cos(math.radians(22.5)) - 0.02
    for t in np.arange(-0.56, 0.57, 0.14):
        L = min(ap, ap * math.sqrt(2) - abs(t)) - 0.02
        M.add(g, B(-L, L, t - 0.016, t + 0.016, 0.30, 0.326), 'hull_mid')
        M.add(g, B(t - 0.016, t + 0.016, -L, L, 0.30, 0.322), 'hull_mid')
    for i in range(8):
        a = math.radians(45 * i)
        light(M, g, 0.83 * math.cos(a), 0.83 * math.sin(a), 0.30, 0.045, 0.045, 0.014)
    # bay doors on every side (the output side is covered by -out)
    for k in range(4):
        S = rz(90 * k)
        M.add(g, tf(B(0.96, 1.46, -0.42, 0.42, 0.20, 0.25), S), 'hull_dark')
        for y in np.linspace(-0.30, 0.30, 5):
            M.add(g, tf(prism(rect(1.21, y, 0.23, 0.05), 0.22, 0.29, 0.86), S), 'metal')
        for sy in (-1, 1):
            M.add(g, tf(B(0.98, 1.44, sy * 0.38, sy * 0.44, 0.22, 0.33), S), 'yellow')
        # utilities between the door and the corner towers
        grille(M, g, 1.20, -0.68, 0.22, 0.30, 0.16, n=4, glow='glow', R=S @ rz(0))
        M.add(g, tf(prism(rect(1.20, 0.68, 0.14, 0.12), 0.22, 0.36, 0.86), S), 'hull_light')
        M.add(g, tf(cyl((1.20, 0.68, 0.36), (1.20, 0.68, 0.38), 0.05, n=10), S), 'metal_light')
        cable(M, g, [tuple(S @ np.array([1.08, 0.68, 0.30])), tuple(S @ np.array([0.84, 0.60, 0.30])), tuple(S @ np.array([0.70, 0.46, 0.31]))], 0.03, ends='yellow')
    for sx in (-1, 1):                                   # tower footings
        for sy in (-1, 1):
            M.add(g, prism(cham_rect(0.25, 0.25, 0.07, sx * 1.14, sy * 1.14), 0.22, 0.30, 0.92), 'hull_light')
            M.add(g, prism(P([(sx * 1.38, sy * 0.92), (sx * 1.38, sy * 1.00), (sx * 1.00, sy * 1.38), (sx * 0.92, sy * 1.38)]), 0.22, 0.24), 'yellow')

    # --- -out: open launch ramp with chevrons (+x side, rotated by the engine)
    g = 'out'
    M.add(g, B(0.96, 1.47, -0.43, 0.43, 0.20, 0.27), 'hull_dark')
    M.add(g, prism(rect(1.22, 0, 0.23, 0.34), 0.27, 0.29, 0.97), 'vent')
    for x in (1.06, 1.20, 1.34):
        M.add(g, tf(prism(chevron(1.6), 0.29, 0.31), None, (x, 0, 0)), 'yellow')
    for sy in (-1, 1):
        M.add(g, B(0.97, 1.46, sy * 0.36, sy * 0.43, 0.27, 0.36), 'hull_light')
        M.add(g, B(1.00, 1.43, sy * 0.38, sy * 0.41, 0.36, 0.37), 'yellow')
        light(M, g, 1.40, sy * 0.395, 0.37, 0.05, 0.035)
        light(M, g, 1.02, sy * 0.395, 0.37, 0.05, 0.035)

    # --- -top: corner gantry towers + manipulator arms (drawn over the unit)
    g = 'top'
    for k in range(4):
        a = 45 + 90 * k
        Rd = rz(a)
        S = rz(90 * k)
        cx, cy = 1.14, 1.14
        M.add(g, tf(prism(cham_rect(0.19, 0.19, 0.05, cx, cy), 0.30, 1.00, 0.93), S), 'hull_light')
        M.add(g, tf(prism(cham_rect(0.21, 0.21, 0.06, cx, cy), 1.00, 1.06, 0.92), S), 'hull_mid')
        for j in range(4):                               # hazard-striped L on the outer edges of the cap
            t0 = -0.20 + j * 0.10
            m = 'yellow' if j % 2 == 0 else 'hull_dark'
            M.add(g, tf(B(cx + 0.11, cx + 0.20, cy + t0, cy + t0 + 0.10, 1.06, 1.076), S), m)
            M.add(g, tf(B(cx + t0, cx + t0 + 0.10, cy + 0.11, cy + 0.20, 1.06, 1.076), S), m)
        M.add(g, tf(cyl((cx + 0.155, cy + 0.155, 1.06), (cx + 0.155, cy + 0.155, 1.10), 0.04, n=10), S), 'glow')
        u0 = 1.14 * math.sqrt(2)
        M.add(g, tf(cyl((u0 - 0.08, 0, 1.06), (u0 - 0.08, 0, 1.14), 0.11, n=16), Rd), 'metal')
        M.add(g, tf(beam((u0 - 0.08, 0, 1.15), (1.04, 0, 1.13), 0.075, 0.045, ch=0.025), Rd), 'hull_light')
        M.add(g, tf(cyl((u0 - 0.20, 0.085, 1.10), (1.10, 0.085, 1.08), 0.03, n=8), Rd), 'metal_light')
        M.add(g, tf(cyl((1.04, 0, 1.06), (1.04, 0, 1.19), 0.08, n=14), Rd), 'metal_light')
        M.add(g, tf(cyl((1.04, 0, 1.19), (1.04, 0, 1.20), 0.04, n=10), Rd), 'yellow')
        M.add(g, tf(beam((1.04, 0, 1.08), (0.78, 0, 0.96), 0.05, 0.035, ch=0.015), Rd), 'hull_mid')
        M.add(g, tf(cyl((0.76, 0, 0.86), (0.76, 0, 1.00), 0.06, n=12), Rd), 'hull_dark')
        M.add(g, tf(cyl((0.74, 0, 0.92), (0.64, 0, 0.84), 0.022, n=8), Rd), 'metal')
        M.add(g, tf(cyl((0.65, 0, 0.85), (0.62, 0, 0.83), 0.032, n=8), Rd), 'glow')
        bolts(M, g, [tuple((S @ np.array([cx + p, cy + q, 0]))[:2]) for p, q in ((0.08, -0.14), (-0.14, 0.08))], 1.06, r=0.02)
    return M


# ================================================================== render driver
def _flipv(a):
    return np.ascontiguousarray(np.asarray(a)[::-1])


def run():
    t0 = time.time()
    counts = {}

    d = 'blocks/heat'
    M = heater(); counts['heater'] = M.ntri()
    main, hg = layer(M, ['main'], 64, heater_glow, casters=['main'])
    top, ht = layer(M, ['top'], 64, heater_heat, casters=['top'])
    save(main, d, 'heater'); save(heat_sprite(hg), d, 'heater-glow')
    save(top, d, 'heater-top1'); save(_flipv(top), d, 'heater-top2'); save(heat_sprite(ht), d, 'heater-heat')
    f = over(main, top); save(f, d, 'heater-full'); FULL['heater'] = f

    M = heat_conduit(); counts['heat-conduit'] = M.ntri()
    main, _ = layer(M, ['main'], 32, casters=['main'])
    top, ht = layer(M, ['top'], 32, conduit_heat, casters=['top'])
    save(main, d, 'heat-conduit'); save(top, d, 'heat-conduit-top1'); save(_flipv(top), d, 'heat-conduit-top2')
    save(heat_sprite(ht), d, 'heat-conduit-heat')
    f = over(main, top); save(f, d, 'heat-conduit-full'); FULL['heat-conduit'] = f

    d = 'blocks/crafting'
    M = tungsten_forge(); counts['tungsten-forge'] = M.ntri()
    main, hg = layer(M, ['main'], 96, forge_glow)
    _, hh = layer(M, ['main'], 96, forge_heat)
    save(main, d, 'tungsten-forge'); save(heat_sprite(hg), d, 'tungsten-forge-glow'); save(heat_sprite(hh), d, 'tungsten-forge-heat')
    save(main, d, 'tungsten-forge-full'); FULL['tungsten-forge'] = main

    M = magnet_factory(); counts['magnet-factory'] = M.ntri()
    bot, _ = layer(M, ['bottom'], 64, casters=['bottom', 'main'])
    spin, _ = layer(M, ['spinner'], 64, casters=['spinner'])
    main, hg = layer(M, ['main'], 64, magnet_glow, casters=['main'])
    save(bot, d, 'magnet-factory-bottom'); save(spin, d, 'magnet-factory-spinner'); save(main, d, 'magnet-factory')
    save(heat_sprite(hg), d, 'magnet-factory-glow')
    f = over(over(bot, spin), main); save(f, d, 'magnet-factory-full'); FULL['magnet-factory'] = f

    d = 'blocks/drills'
    M = percussion_drill(); counts['percussion-drill'] = M.ntri()
    main, _ = layer(M, ['main'], 96, casters=['main', 'top'])
    rot, _ = layer(M, ['rotator'], 96, casters=['rotator'])
    top, _ = layer(M, ['top'], 96, casters=['top'])
    save(main, d, 'percussion-drill'); save(rot, d, 'percussion-drill-rotator'); save(top, d, 'percussion-drill-top')
    f = over(over(main, rot), top); save(f, d, 'percussion-drill-full'); FULL['percussion-drill'] = f

    d = 'blocks/units'
    M = engineering_bay(); counts['engineering-bay'] = M.ntri()
    main, _ = layer(M, ['main'], 96, casters=['main', 'top'])
    out, _ = layer(M, ['out'], 96, casters=['out'])
    top, _ = layer(M, ['top'], 96, casters=['top'])
    save(main, d, 'engineering-bay'); save(out, d, 'engineering-bay-out'); save(top, d, 'engineering-bay-top')
    f = over(over(main, out), top); save(f, d, 'engineering-bay-full'); FULL['engineering-bay'] = f

    for k, v in counts.items():
        print(f'{k:18s} {v:6d} triangles')
    print('g_industry_b done in', round(time.time() - t0, 1), 's')
    return counts


if __name__ == '__main__':
    run()
