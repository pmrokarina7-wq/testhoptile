"""Workstream g_industry_a: hero remakes of the T1-T2 UEF industry blocks.

    .venv/bin/python tools/art/g_industry_a.py

Steel smelter, propellant press, mass separator I/II, bauxite electrolyzer, alloy furnace.
Writes every layer straight into mod/sprites/blocks/crafting (same names and canvas sizes as before)
and prints triangle counts. 1.0 = one tile, Z up, origin = block centre.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rend  # noqa: E402
from geom import *  # noqa: E402,F401
from mats import Model, MID  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
from hero import P, grille, cable, seam, bolts_R  # noqa: E402
from export import save, over, heat_sprite, hexc, SS, FULL, qa_sheet  # noqa: E402

# private materials (append-only; separate ids let the -glow masks pick exactly the hot parts)
rend.add_material('ga_refr', ['2a1c18', '3b2820', '50362a', '684636', '825a44', '9e7056'])    # refractory brick
rend.add_material('ga_ember', ['4a1206', '701c08', '9a2a0c', 'c23e12', 'e05a1a', 'f47c30'])   # hot throat / tuyere
rend.add_material('ga_coil', ['3a1d10', '5a2e18', '7f4322', 'a65a2e', 'c9743e', 'e8955a'])    # induction coil copper
rend.add_material('ga_slag', ['4a1c06', '6e2c0a', '96400e', 'c05a16', 'e07a24', 'ffa166'])    # slag band / pipe paint
rend.add_material('ga_amber', ['6a4208', '9a620c', 'c88a14', 'eeb030', 'ffd060', 'fff0b0'], glow=True)  # amber lamp
rend.add_material('ga_ti', ['2c2f45', '40456a', '5a6290', '7884b4', '9aa6d4', 'c0caf0'])      # titanium
rend.add_material('ga_die', ['30140a', '4a2010', '6a3014', '8c4418', 'ac5a1e', 'c87028'])     # heated press die band
rend.add_material('ga_melt', ['ffa040', 'ffb85a', 'ffcc74', 'ffdc92', 'ffeab4', 'fff6dc'], glow=True)  # hottest melt

D = 'blocks/crafting'


# ------------------------------------------------------------------ helpers
def B(x0, x1, y0, y1, z0, z1):
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1)


def octp(r, cx=0.0, cy=0.0, rot=22.5):
    return P([(cx + r * math.cos(math.radians(rot + 45 * i)), cy + r * math.sin(math.radians(rot + 45 * i))) for i in range(8)])


def hexp(r, cx=0.0, cy=0.0, rot=0.0):
    return P([(cx + r * math.cos(math.radians(rot + 60 * i)), cy + r * math.sin(math.radians(rot + 60 * i))) for i in range(6)])


def circ(r, n=32, cx=0.0, cy=0.0, a0=0.0):
    return P([(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)])


def add_R(M, g, T, m, R=None, t=(0, 0, 0)):
    M.add(g, tf(T, R, t), m)


def holed_plate(M, g, H, c, hole, z0, z1, mat, inset=0.0):
    """Chamfered square plate (half H, chamfer c) with an opening, built as 4 mirrored simple quadrants.
    hole: quadrant boundary points from the +y axis to the +x axis, e.g. ('circle', r) / ('rect', hx, hy) /
    ('cross', W, E). inset shrinks the top face edge (slanted outer walls)."""
    kind = hole[0]
    if kind == 'circle':
        r = hole[1]; n = 12
        hp = [(r * math.cos(math.radians(90 - 90 * i / n)), r * math.sin(math.radians(90 - 90 * i / n))) for i in range(n + 1)]
    elif kind == 'rect':
        hp = [(0, hole[2]), (hole[1], hole[2]), (hole[1], 0)]
    else:
        W, E = hole[1], hole[2]
        hp = [(0, E), (W, E), (W, W), (E, W), (E, 0)]

    def quad(Ho, cc):
        return [(Ho, 0), (Ho, Ho - cc), (Ho - cc, Ho), (0, Ho)] + hp
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = [(sx * x, sy * y) for x, y in quad(H, c)]
            t = [(sx * x, sy * y) for x, y in quad(H - inset, c * (H - inset) / H)]
            if sx * sy < 0:
                b, t = b[::-1], t[::-1]
            M.add(g, loft(ring(b, z0), ring(t, z1)), mat)


def annulus(cx, cy, ro, ri, z0, z1, n=32, ro_t=None, ri_t=None, a0=0.0, a1=360.0):
    """Ring (or ring sector) solid. ro_t/ri_t: radii of the top face (chamfers)."""
    ro_t = ro if ro_t is None else ro_t
    ri_t = ri if ri_t is None else ri_t
    T = []
    full = abs(a1 - a0) >= 359.9
    k = n if full else max(2, int(n * abs(a1 - a0) / 360))
    angs = [math.radians(a0 + (a1 - a0) * i / k) for i in range(k + 1)]

    def p(r, a, z):
        return np.array([cx + r * math.cos(a), cy + r * math.sin(a), z])
    for i in range(k):
        a, b = angs[i], angs[i + 1]
        ob0, ob1, ot0, ot1 = p(ro, a, z0), p(ro, b, z0), p(ro_t, a, z1), p(ro_t, b, z1)
        ib0, ib1, it0, it1 = p(ri, a, z0), p(ri, b, z0), p(ri_t, a, z1), p(ri_t, b, z1)
        T += [[ob0, ob1, ot1], [ob0, ot1, ot0]]          # outer wall (faces out)
        T += [[ib1, ib0, it0], [ib1, it0, it1]]          # inner wall (faces the axis)
        T += [[ot0, ot1, it1], [ot0, it1, it0]]          # top
        T += [[ob0, ib1, ob1], [ob0, ib0, ib1]]          # bottom
    if not full:
        for a in (angs[0], angs[-1]):
            T += [[p(ri, a, z0), p(ro, a, z0), p(ro_t, a, z1)], [p(ri, a, z0), p(ro_t, a, z1), p(ri_t, a, z1)]]
    return clean(T)


def lumps(M, g, cx, cy, z, hx, hy, mat, seed, n=8, s=0.045, R=None):
    """Heap of low-poly rock lumps (6-sided frustums) inside a hx*hy area."""
    r = np.random.default_rng(seed)
    for i in range(n):
        x, y = r.uniform(-hx, hx), r.uniform(-hy, hy)
        ss = s * (0.7 + 0.6 * r.random())
        zz = z + 0.6 * ss * (1 - max(abs(x) / hx, abs(y) / hy))
        T = prism(hexp(ss, x, y, rot=r.uniform(0, 60)), zz, zz + ss * 0.9, 0.45)
        M.add(g, tf(T, R, (cx, cy, 0)) if R is not None else tf(T, None, (cx, cy, 0)), mat)


def hopper(M, g, cx, cy, hx, hy, z0, z1, ore, seed, rim='hull_light', n=9, s=0.045, R=None, t=(0, 0, 0)):
    """Open feed hopper: rim frame, sloped inner walls, ore heap inside."""
    def A(T, m):
        M.add(g, tf(T, R, t), m)
    w = 0.035
    A(B(cx - hx, cx + hx, cy + hy - w, cy + hy, z0, z1), rim)
    A(B(cx - hx, cx + hx, cy - hy, cy - hy + w, z0, z1), rim)
    A(B(cx - hx, cx - hx + w, cy - hy, cy + hy, z0, z1), rim)
    A(B(cx + hx - w, cx + hx, cy - hy, cy + hy, z0, z1), rim)
    zb = z0 + 0.02
    inner_b = rect(cx, cy, (hx - w) * 0.45, (hy - w) * 0.45)
    inner_t = rect(cx, cy, hx - w, hy - w)
    A(loft(ring(inner_b, zb), ring(inner_t, z1 - 0.005), True, False), 'hull_dark')
    rr = np.random.default_rng(seed)
    for i in range(n):
        x, y = rr.uniform(-(hx - w) * 0.75, (hx - w) * 0.75), rr.uniform(-(hy - w) * 0.75, (hy - w) * 0.75)
        ss = s * (0.75 + 0.6 * rr.random())
        zz = z1 - 0.10 + 0.05 * (1 - max(abs(x) / hx, abs(y) / hy))
        A(prism(hexp(ss, cx + x, cy + y, rot=rr.uniform(0, 60)), zz, zz + ss * 1.1, 0.45), ore)
    for (x, y) in ((cx - hx + 0.03, cy - hy + 0.03), (cx + hx - 0.03, cy - hy + 0.03), (cx - hx + 0.03, cy + hy - 0.03), (cx + hx - 0.03, cy + hy - 0.03)):
        A(cyl((x, y, z1), (x, y, z1 + 0.012), 0.016, n=6), 'metal_light')


def corner_caps(M, g, H, c, z, k_list=(0, 1, 2, 3), lamp='glow'):
    """Armour wedge on each chamfered corner: light plate, yellow inlay, bolts and a lamp."""
    for k in k_list:
        R = rz(45 + 90 * k)
        u1 = (H - c / 2) * math.sqrt(2) - 0.02
        half = c / math.sqrt(2) * 0.95
        poly = P([(u1 - 0.17, -half * 0.60), (u1, -half), (u1, half), (u1 - 0.17, half * 0.60)])
        M.add(g, tf(prism(poly, z - 0.02, z + 0.06, 0.88), R), 'hull_light')
        M.add(g, tf(prism(scale_poly(poly, (0.45, 0.62)), z + 0.06, z + 0.072), R), 'yellow')
        for v in (-half * 0.62, half * 0.62):
            M.add(g, tf(cyl((u1 - 0.05, v, z + 0.05), (u1 - 0.05, v, z + 0.075), 0.018, n=6), R), 'metal_light')
        if lamp:
            M.add(g, tf(cbox(u1 - 0.14, 0, z + 0.035, 0.045, 0.06, 0.03), R), 'hull_dark')
            M.add(g, tf(cbox(u1 - 0.14, 0, z + 0.05, 0.03, 0.045, 0.02), R), lamp)


def pipe(M, g, pts, r, m='metal', flange='hull_light', fl=()):
    M.add(g, tube_path(pts, r, n=10), m)
    for (p, d) in fl:
        p = np.asarray(p, float); d = np.asarray(d, float); d /= np.linalg.norm(d)
        M.add(g, cyl(p - d * 0.018, p + d * 0.018, r * 1.45, n=10), flange)


def wheel(M, g, x, y, z, r=0.07, m='yellow'):
    """Valve hand-wheel seen from above."""
    for i in range(8):
        a0, a1 = 2 * math.pi * i / 8, 2 * math.pi * (i + 1) / 8
        M.add(g, cyl((x + r * math.cos(a0), y + r * math.sin(a0), z), (x + r * math.cos(a1), y + r * math.sin(a1), z), 0.014, n=6), m)
    for i in range(2):
        a = math.pi / 2 * i + math.pi / 4
        M.add(g, cyl((x - r * math.cos(a), y - r * math.sin(a), z), (x + r * math.cos(a), y + r * math.sin(a), z), 0.010, n=6), m)
    M.add(g, cyl((x, y, z - 0.03), (x, y, z + 0.016), 0.022, n=8), 'hull_dark')


def fins(M, g, x0, x1, y0, y1, z0, z1, n, along='y', m='metal_light', gap='vent'):
    """Heat-exchanger fin bank: dark well with n bright fins."""
    M.add(g, B(x0, x1, y0, y1, z0, z0 + 0.01), gap)
    for i in range(n):
        if along == 'y':
            y = y0 + (y1 - y0) * (i + 0.5) / n; w = (y1 - y0) / n * 0.36
            M.add(g, B(x0 + 0.01, x1 - 0.01, y - w, y + w, z0, z1), m)
        else:
            x = x0 + (x1 - x0) * (i + 0.5) / n; w = (x1 - x0) / n * 0.36
            M.add(g, B(x - w, x + w, y0 + 0.01, y1 - 0.01, z0, z1), m)


def ingots(M, g, cx, cy, z, mat, nx=2, ny=3, L=0.20, w=0.07, layers=2, R=None):
    """Stack of trapezoid ingots, alternate layers crossed."""
    for l in range(layers):
        zz = z + l * 0.05
        for i in range(nx):
            for j in range(ny):
                if l % 2 == 0:
                    x = cx + (i - (nx - 1) / 2) * (L + 0.02); y = cy + (j - (ny - 1) / 2) * (w + 0.02)
                    T = prism(rect(x, y, L / 2, w / 2), zz, zz + 0.045, top_poly=rect(x, y, L / 2 - 0.02, w / 2 - 0.015))
                else:
                    x = cx + (j - (ny - 1) / 2) * (w + 0.02) * 0.9; y = cy + (i - (nx - 1) / 2) * (L + 0.02) * 0.55
                    T = prism(rect(x, y, w / 2, L / 2 * 0.55), zz, zz + 0.045, top_poly=rect(x, y, w / 2 - 0.015, L / 2 * 0.55 - 0.02))
                M.add(g, tf(T, R), mat)


def beam(M, g, p0, p1, w, t, m, t0=0.0, t1=1.0):
    """Flat rectangular beam from p0 to p1 (any pitch), top face kept level across its width."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1 - p0
    L = float(np.linalg.norm(d)); hz = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    M.add(g, tf(box(L * t0, L * t1, -w / 2, w / 2, -t / 2, t / 2), rz(hz) @ ry(-pitch), p0), m)


def wmat(**w):
    """Glow-mask function from per-material weights."""
    ids = [(MID[k], v) for k, v in w.items()]

    def f(mp, X, Y, g):
        out = np.zeros(mp.shape)
        for i, v in ids:
            out = np.where(mp == i, v, out)
        return out
    return f


def rl(M, groups, casters, canvas, heat=None, L=None):
    return rend.render_layer(M, groups, casters, canvas, SS, heat, rend.LIGHT_TD if L is None else np.asarray(L, float))


def glow_sprite(hm):
    g = heat_sprite(hm)
    return g


# ================================================================== Steel smelter (2x2) - UEF blast furnace
def steel_smelter():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.26), 0.0, 0.08, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(0.91, 0.91, 0.25), 0.08, 0.16, 0.965), 'hull_mid')
    top = 0.16
    corner_caps(M, g, 0.91, 0.25, top, k_list=(0, 1), lamp='glow')
    # side heat-exchanger banks (cooling-water jackets)
    for s in (-1, 1):
        x0, x1 = s * 0.72, s * 0.90
        M.add(g, B(x0, x1, -0.40, 0.34, top - 0.01, top + 0.03), 'hull_dark')
        fins(M, g, min(x0, x1) + 0.01, max(x0, x1) - 0.01, -0.36, 0.30, top + 0.03, top + 0.13, 7, along='y')
        M.add(g, B(x0, x1, 0.30, 0.36, top, top + 0.16), 'hull_light')
        M.add(g, B(x0, x1, -0.42, -0.36, top, top + 0.16), 'hull_light')
        # cooling pipes: jacket header -> furnace ring
        pipe(M, g, [(s * 0.81, 0.33, top + 0.18), (s * 0.81, 0.46, top + 0.18), (s * 0.56, 0.46, top + 0.30)], 0.035,
             m='glass', fl=[((s * 0.81, 0.40, top + 0.18), (0, 1, 0))])
        pipe(M, g, [(s * 0.81, -0.39, top + 0.18), (s * 0.81, -0.50, top + 0.18), (s * 0.58, -0.40, top + 0.30)], 0.035,
             m='glass', fl=[((s * 0.81, -0.46, top + 0.18), (0, 1, 0))])
    # front apron: hazard stripes + ingot mould fed by the tap spout
    chevrons(M, g, 0, -0.84, top - 0.006, 0.44, 0.07, n=6)
    fx, fy = 0.0, 0.10
    M.add(g, B(-0.17, 0.17, -0.78, -0.52, top, top + 0.07), 'hull_light')
    M.add(g, B(-0.13, 0.13, -0.74, -0.56, top + 0.07, top + 0.075), 'hull_dark')
    M.add(g, prism(rect(0, -0.65, 0.09, 0.06), top + 0.03, top + 0.08, top_poly=rect(0, -0.65, 0.075, 0.045)), 'flame')
    M.add(g, B(-0.055, 0.055, -0.56, -0.30, top + 0.10, top + 0.16), 'metal')
    M.add(g, B(-0.03, 0.03, -0.56, -0.30, top + 0.16, top + 0.168), 'flame')
    for s in (-1, 1):
        M.add(g, B(s * 0.055, s * 0.075, -0.56, -0.30, top + 0.10, top + 0.185), 'hull_dark')
    # furnace plinth + shell
    M.add(g, prism(octp(0.60, fx, fy), top, top + 0.06, 0.97), 'hull_dark')
    M.add(g, cyl((fx, fy, top + 0.06), (fx, fy, top + 0.40), 0.48, 0.455, n=32), 'steel')
    for z in (top + 0.13, top + 0.27):
        M.add(g, cyl((fx, fy, z), (fx, fy, z + 0.035), 0.49, n=32), 'hull_dark')
    # bustle pipe (hot-blast ring) + tuyeres
    for i in range(16):
        a0, a1 = 2 * math.pi * i / 16, 2 * math.pi * (i + 1) / 16
        M.add(g, cyl((fx + 0.55 * math.cos(a0), fy + 0.55 * math.sin(a0), top + 0.30),
                     (fx + 0.55 * math.cos(a1), fy + 0.55 * math.sin(a1), top + 0.30), 0.045, n=8), 'metal')
    for i in range(6):
        a = math.radians(30 + 60 * i)
        M.add(g, cyl((fx + 0.55 * math.cos(a), fy + 0.55 * math.sin(a), top + 0.30),
                     (fx + 0.47 * math.cos(a), fy + 0.47 * math.sin(a), top + 0.36), 0.028, n=8), 'metal_light')
        M.add(g, cyl((fx + 0.555 * math.cos(a), fy + 0.555 * math.sin(a), top + 0.33),
                     (fx + 0.555 * math.cos(a), fy + 0.555 * math.sin(a), top + 0.35), 0.03, n=8), 'ga_ember')
    # throat: rim, refractory lining, molten pool with crust
    M.add(g, annulus(fx, fy, 0.465, 0.40, top + 0.40, top + 0.46, 32, ro_t=0.44), 'metal_light')
    M.add(g, annulus(fx, fy, 0.40, 0.31, top + 0.38, top + 0.445, 32, ri_t=0.33), 'ga_refr')
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        M.add(g, cyl((fx + 0.43 * math.cos(a), fy + 0.43 * math.sin(a), top + 0.45),
                     (fx + 0.43 * math.cos(a), fy + 0.43 * math.sin(a), top + 0.47), 0.018, n=6), 'hull_dark')
    M.add(g, cyl((fx, fy, top + 0.30), (fx, fy, top + 0.415), 0.32, n=28), 'flame')
    M.add(g, cyl((fx - 0.04, fy + 0.03, top + 0.40), (fx - 0.04, fy + 0.03, top + 0.42), 0.14, n=18), 'ga_melt')
    rr = np.random.default_rng(7)
    for i in range(5):
        a = rr.uniform(0, 2 * math.pi); d = rr.uniform(0.16, 0.26)
        M.add(g, prism(hexp(0.035 + 0.02 * rr.random(), fx + d * math.cos(a), fy + d * math.sin(a), rr.uniform(0, 60)),
                       top + 0.41, top + 0.43, 0.7), 'heat')
    # charging skips: hopper -> enclosed inclined chute -> furnace mouth
    for s, ore, seed in ((-1, 'ore_fer', 3), (1, 'tung', 5)):
        hx0, hy0 = s * 0.62, -0.60
        hopper(M, g, hx0, hy0, 0.19, 0.17, top, top + 0.20, ore, seed, n=8, s=0.042)
        M.add(g, B(hx0 - 0.19, hx0 + 0.19, hy0 + 0.17, hy0 + 0.20, top + 0.14, top + 0.215), 'yellow')
        p0 = (hx0 + s * 0.02, hy0 + 0.15, top + 0.20); p1 = (s * 0.30, fy - 0.27, top + 0.47)
        beam(M, g, p0, p1, 0.12, 0.05, 'hull_light')                       # skip incline
        beam(M, g, p0, p1, 0.07, 0.056, 'cable', t0=0.08, t1=0.96)          # belt
        for t in (0.30, 0.55, 0.80):
            q = np.asarray(p0) + (np.asarray(p1) - np.asarray(p0)) * t
            M.add(g, prism(hexp(0.026, q[0], q[1], rot=30 * t * 7), q[2] + 0.025, q[2] + 0.06, 0.5), ore)
        for t in (0.0, 1.0):
            beam(M, g, p0, p1, 0.15, 0.07, 'yellow' if t == 0 else 'hull_dark', t0=max(0, t - 0.06), t1=min(1, t + 0.06))
    # gas uptakes + twin stacks at the back
    for s in (-1, 1):
        cx, cy = s * 0.64, 0.64
        M.add(g, prism(octp(0.19, cx, cy), top, top + 0.05, 0.95), 'hull_dark')
        M.add(g, cyl((cx, cy, top + 0.05), (cx, cy, top + 0.62), 0.135, 0.125, n=18), 'metal')
        M.add(g, cyl((cx, cy, top + 0.40), (cx, cy, top + 0.45), 0.142, n=18), 'yellow')
        M.add(g, cyl((cx, cy, top + 0.62), (cx, cy, top + 0.66), 0.15, n=18), 'hull_dark')
        M.add(g, annulus(cx, cy, 0.15, 0.10, top + 0.66, top + 0.68, 18), 'metal_light')
        M.add(g, cyl((cx, cy, top + 0.55), (cx, cy, top + 0.665), 0.10, n=16), 'ga_ember')
        pipe(M, g, [(s * 0.26, fy + 0.30, top + 0.44), (s * 0.36, 0.52, top + 0.56), (s * 0.52, 0.60, top + 0.56)], 0.06,
             m='steel', fl=[((s * 0.45, 0.575, top + 0.56), (1, 0.3, 0))])
    # power feed (right) + control light strip
    cable(M, g, [(0.93, -0.52, top + 0.02), (0.84, -0.72, top + 0.06), (0.62, -0.84, top + 0.04)], 0.028, ends='yellow')
    light(M, g, -0.38, -0.86, top - 0.01, 0.08, 0.025, 0.012)
    light(M, g, 0.38, -0.86, top - 0.01, 0.08, 0.025, 0.012)
    bolts(M, g, [(-0.84, -0.84 + 0.25), (0.84, -0.84 + 0.25), (-0.30, 0.86), (0.30, 0.86)], top, r=0.02)
    seam(M, g, (-0.30, 0.84), (0.30, 0.84), top, w=0.022, h=0.01)
    return M


def render_steel_smelter():
    M = steel_smelter()
    hf = wmat(flame=1.0, ga_melt=1.0, ga_ember=0.85, heat=0.35)
    main, hm = rl(M, ['main'], ['main'], 64, hf)
    save(main, D, 'steel-smelter')
    save(glow_sprite(hm), D, 'steel-smelter-glow')
    save(main, D, 'steel-smelter-full')
    FULL['steel-smelter'] = main
    return M


# ================================================================== Propellant press (2x2) - 4-ram hydraulic press
PW, PE = 0.19, 0.47           # channel half-width, channel end (cylinder gland)


def propellant_press():
    M = Model()
    # ---- bottom: press bed, slide rails, stroke marks, powder in the die pocket
    g = 'bottom'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.26), 0.0, 0.08, 0.985), 'hull_dark')
    M.add(g, B(-0.56, 0.56, -0.56, 0.56, 0.08, 0.10), 'cable')
    for k in range(4):
        R = rz(90 * k)
        for s in (-1, 1):
            add_R(M, g, B(0.10, 0.56, s * 0.150, s * 0.180, 0.10, 0.125), 'metal', R)
        for x in (0.20, 0.30, 0.40):
            add_R(M, g, B(x - 0.012, x + 0.012, -0.135, 0.135, 0.10, 0.104), 'hull_mid', R)
        add_R(M, g, B(0.43, 0.46, -0.14, 0.14, 0.10, 0.11), 'yellow', R)
    M.add(g, B(-0.13, 0.13, -0.13, 0.13, 0.095, 0.10), 'vent')
    lumps(M, g, 0, 0, 0.10, 0.09, 0.09, 'ore_salt', 21, n=6, s=0.025)
    # ---- piston (32 px sprite, +x = outward): wedge ram head + chrome rod + collar
    g = 'piston'
    head = P([(-0.30, -0.012), (-0.30, 0.012), (-0.175, 0.135), (-0.135, 0.135), (-0.135, -0.135), (-0.175, -0.135)])
    M.add(g, prism(head, 0.10, 0.22, 0.94), 'steel')
    M.add(g, prism(scale_poly(head, (0.62, 0.70)), 0.22, 0.235, 0.9), 'yellow')
    M.add(g, B(-0.165, -0.145, -0.11, 0.11, 0.22, 0.24), 'hull_dark')
    M.add(g, cyl((-0.14, 0, 0.17), (-0.10, 0, 0.17), 0.075, n=14), 'hull_mid')
    M.add(g, cyl((-0.10, 0, 0.17), (0.38, 0, 0.17), 0.052, n=14), 'metal_light')
    for x in (0.02, 0.20):
        M.add(g, cyl((x, 0, 0.17), (x + 0.012, 0, 0.17), 0.056, n=14), 'metal')
    # ---- main: frame with a cross-shaped opening, 4 tie-rod cylinders, hoppers and charge racks
    g = 'main'
    holed_plate(M, g, 0.985, 0.26, ('cross', PW, PE), 0.0, 0.09, 'hull_dark')
    holed_plate(M, g, 0.90, 0.24, ('cross', PW + 0.03, PE), 0.09, 0.20, 'hull_mid', inset=0.02)
    top = 0.20
    for k in range(4):
        R = rz(90 * k)
        for s in (-1, 1):                                       # yellow safety lips along the channel
            add_R(M, g, B(PW + 0.07, PE - 0.01, s * (PW + 0.03), s * (PW + 0.06), top, top + 0.016), 'yellow', R)
        # tie-rod hydraulic cylinder
        add_R(M, g, B(0.44, 0.53, -0.165, 0.165, top - 0.02, top + 0.22), 'hull_light', R)
        add_R(M, g, B(0.46, 0.51, -0.12, 0.12, top + 0.22, top + 0.235), 'hull_mid', R)
        add_R(M, g, cyl((0.53, 0, top + 0.12), (0.83, 0, top + 0.12), 0.125, n=18), 'steel', R)
        for x in (0.60, 0.74):
            add_R(M, g, cyl((x, 0, top + 0.12), (x + 0.02, 0, top + 0.12), 0.132, n=18), 'hull_dark', R)
        add_R(M, g, B(0.83, 0.92, -0.165, 0.165, top - 0.02, top + 0.22), 'hull_light', R)
        for s in (-1, 1):
            add_R(M, g, cyl((0.43, s * 0.125, top + 0.21), (0.935, s * 0.125, top + 0.21), 0.017, n=6), 'metal_light', R)
            for x in (0.425, 0.935):
                add_R(M, g, cyl((x, s * 0.125, top + 0.21), (x + (0.012 if x > 0.5 else -0.012), s * 0.125, top + 0.21), 0.03, n=6), 'metal', R)
        add_R(M, g, cyl((0.875, 0.06, top + 0.22), (0.875, 0.06, top + 0.27), 0.03, n=8), 'copper', R)
        add_R(M, g, cyl((0.875, -0.06, top + 0.22), (0.875, -0.06, top + 0.25), 0.024, n=8), 'ga_amber', R)
    # corners: saltpeter + coal hoppers (back), charge cartridge racks (front)
    hopper(M, g, 0.60, 0.60, 0.17, 0.17, top, top + 0.17, 'ore_salt', 31, n=9, s=0.04)
    hopper(M, g, -0.60, 0.60, 0.17, 0.17, top, top + 0.17, 'tung', 33, n=9, s=0.04)
    for s in (-1, 1):
        cx, cy = s * 0.60, -0.58
        M.add(g, B(cx - 0.20, cx + 0.20, cy - 0.17, cy + 0.15, top - 0.01, top + 0.03), 'hull_dark')
        for j, y in enumerate((cy - 0.11, cy - 0.01, cy + 0.09)):
            x0, x1 = cx - 0.16, cx + 0.16
            M.add(g, cyl((x0 + 0.03, y, top + 0.085), (x1 - 0.03, y, top + 0.085), 0.045, n=10), 'charge')
            M.add(g, cyl((x0, y, top + 0.085), (x0 + 0.03, y, top + 0.085), 0.047, n=10), 'copper')
            M.add(g, cyl((x1 - 0.03, y, top + 0.085), (x1, y, top + 0.085), 0.04, 0.025, n=10), 'hull_mid')
            M.add(g, cyl((cx - 0.02, y, top + 0.085), (cx + 0.02, y, top + 0.085), 0.049, n=10), 'yellow')
        for x in (cx - 0.20, cx + 0.18):
            M.add(g, B(x, x + 0.02, cy - 0.17, cy + 0.15, top - 0.01, top + 0.13), 'hull_light')
    bolts(M, g, [(0.84, 0.30), (-0.84, 0.30), (0.84, -0.30), (-0.84, -0.30), (0.30, 0.84), (-0.30, 0.84), (0.30, -0.84), (-0.30, -0.84)], top, r=0.02)
    # ---- top: heated die on a 4-strut crown
    g = 'top'
    for k in range(4):
        R = rz(45 + 90 * k)
        add_R(M, g, B(0.12, 0.47, -0.04, 0.04, top + 0.17, top + 0.22), 'hull_light', R)
        add_R(M, g, B(0.16, 0.42, -0.014, 0.014, top + 0.22, top + 0.228), 'hull_mid', R)
        add_R(M, g, B(0.40, 0.50, -0.06, 0.06, top - 0.01, top + 0.235), 'hull_mid', R)
        add_R(M, g, cyl((0.45, 0, top + 0.235), (0.45, 0, top + 0.25), 0.022, n=6), 'metal_light', R)
    M.add(g, prism(octp(0.165), top - 0.02, top + 0.20, 0.93), 'steel')
    M.add(g, annulus(0, 0, 0.15, 0.115, top + 0.20, top + 0.225, 24, ro_t=0.14), 'metal_light')
    M.add(g, annulus(0, 0, 0.115, 0.075, top + 0.20, top + 0.215, 24), 'ga_die')
    M.add(g, cyl((0, 0, top + 0.20), (0, 0, top + 0.25), 0.075, 0.06, n=16), 'hull_mid')
    M.add(g, cyl((0, 0, top + 0.25), (0, 0, top + 0.26), 0.03, n=10), 'ga_amber')
    return M


def render_propellant_press():
    M = propellant_press()
    bot, _ = rl(M, ['bottom'], ['bottom', 'main'], 64)
    pis, _ = rl(M, ['piston'], ['piston'], 32, L=(0.0, 0.0, 1.0))   # rotated 4 ways in game: symmetric light
    main, hm1 = rl(M, ['main'], ['main', 'top'], 64, wmat(ga_amber=0.9))
    top, hm2 = rl(M, ['top'], ['top'], 64, wmat(ga_die=1.0, ga_amber=0.9))
    for a, n in ((bot, '-bottom'), (pis, '-piston'), (main, ''), (top, '-top')):
        save(a, D, 'propellant-press' + n)
    save(glow_sprite(np.maximum(hm1, hm2)), D, 'propellant-press-glow')
    # icon: pistons at mid stroke like DrawPistons (len = lenOffset + sinMag/2 world units, 4 px per unit)
    from PIL import Image
    f = bot.copy()
    Pi = Image.fromarray(pis)
    ln = (2.5 + 1.1) * 4
    for k in range(4):
        img = Image.new('RGBA', (64, 64))
        img.alpha_composite(Pi, (16 + int(round(ln)), 16))
        img = img.rotate(90 * k, resample=Image.NEAREST)
        f = over(f, np.array(img))
    f = over(f, main); f = over(f, top)
    save(f, D, 'propellant-press-full')
    FULL['propellant-press'] = f
    return M


# ================================================================== Mass separators - slag centrifuges
def sep_bottom(M, h, rb):
    g = 'bottom'
    M.add(g, prism(cham_rect(h * 0.985, h * 0.985, h * 0.26), 0.0, 0.06, 0.985), 'hull_dark')
    M.add(g, cyl((0, 0, 0.06), (0, 0, 0.07), rb, n=40), 'vent')
    for r in (rb * 0.55, rb * 0.85):
        M.add(g, annulus(0, 0, r + 0.02, r, 0.07, 0.076, 40), 'hull_dark')
    for i in range(8):
        add_R(M, g, B(rb * 0.20, rb * 0.95, -0.018, 0.018, 0.07, 0.074), 'cable', rz(22.5 + 45 * i))


def sep_spinner(M, R0, arms):
    """C4-symmetric swing-bucket rotor (spinSprite cross-fades r and r-90, so 90 deg symmetry is required)."""
    g = 'spinner'
    sc = R0 / 0.52
    M.add(g, annulus(0, 0, R0, R0 - 0.045 * sc, 0.10, 0.15, 48, ro_t=R0 - 0.01), 'metal')
    for i in range(arms * 2):
        add_R(M, g, B(R0 - 0.05 * sc, R0 - 0.005, -0.012, 0.012, 0.15, 0.158), 'hull_dark', rz(360 * i / (arms * 2) + 180 / (arms * 2)))
    M.add(g, cyl((0, 0, 0.10), (0, 0, 0.13), R0 * 0.62, n=40), 'steel')
    for i in range(arms):
        a = 360 * i / arms
        R = rz(a)
        add_R(M, g, B(0.08 * sc, R0 - 0.04 * sc, -0.042 * sc, 0.042 * sc, 0.13, 0.19), 'metal', R)
        add_R(M, g, B(0.12 * sc, R0 * 0.55, -0.016 * sc, 0.016 * sc, 0.19, 0.198), 'metal_light', R)
        # swing bucket on a pin
        bx = R0 * 0.70
        add_R(M, g, cyl((bx, -0.10 * sc, 0.20), (bx, 0.10 * sc, 0.20), 0.016 * sc, n=8), 'metal_light', R)
        add_R(M, g, prism(cham_rect(0.085 * sc, 0.075 * sc, 0.03 * sc, bx, 0), 0.12, 0.24, 0.92), 'hull_light', R)
        add_R(M, g, prism(cham_rect(0.058 * sc, 0.050 * sc, 0.02 * sc, bx, 0), 0.24, 0.245, 0.9), 'ga_slag', R)
        add_R(M, g, B(bx + 0.06 * sc, bx + 0.085 * sc, -0.05 * sc, 0.05 * sc, 0.24, 0.25), 'yellow', R)
        # lightening hole between arms
        a2 = math.radians(a + 180 / arms)
        M.add(g, cyl((R0 * 0.42 * math.cos(a2), R0 * 0.42 * math.sin(a2), 0.13), (R0 * 0.42 * math.cos(a2), R0 * 0.42 * math.sin(a2), 0.132),
                     0.05 * sc, n=12), 'vent')
    M.add(g, cyl((0, 0, 0.13), (0, 0, 0.26), 0.13 * sc, 0.12 * sc, n=24), 'hull_light')
    M.add(g, annulus(0, 0, 0.12 * sc, 0.075 * sc, 0.26, 0.275, 24), 'hull_mid')
    M.add(g, cyl((0, 0, 0.26), (0, 0, 0.29), 0.06 * sc, n=16), 'yellow')
    for i in range(4):
        a = math.radians(45 + 90 * i)
        M.add(g, cyl((0.098 * sc * math.cos(a), 0.098 * sc * math.sin(a), 0.275), (0.098 * sc * math.cos(a), 0.098 * sc * math.sin(a), 0.29),
                     0.016 * sc, n=6), 'metal_light')


def sep_housing(M, h, ri, top):
    g = 'main'
    holed_plate(M, g, h * 0.985, h * 0.26, ('circle', ri), 0.0, 0.10, 'hull_dark')
    holed_plate(M, g, h * 0.90, h * 0.24, ('circle', ri + 0.03), 0.10, top, 'hull_mid', inset=0.02)
    M.add(g, annulus(0, 0, ri + 0.15, ri - 0.01, top, top + 0.07, 48, ro_t=ri + 0.13, ri_t=ri + 0.01), 'hull_light')
    M.add(g, annulus(0, 0, ri + 0.045, ri - 0.015, top + 0.07, top + 0.085, 48), 'metal')
    M.add(g, annulus(0, 0, ri + 0.012, ri - 0.012, top + 0.085, top + 0.092, 48), 'glow')
    nb = 12 if h < 1.2 else 16
    for i in range(nb):
        a = math.radians(360 * i / nb + 180 / nb)
        x, y = (ri + 0.095) * math.cos(a), (ri + 0.095) * math.sin(a)
        M.add(g, cyl((x, y, top + 0.06), (x, y, top + 0.085), 0.019, n=6), 'metal_light')
    ns = 16 if h < 1.2 else 24
    for i in range(ns):
        M.add(g, annulus(0, 0, ri + 0.20, ri + 0.15, top - 0.01, top + 0.02, 4, a0=360 * i / ns, a1=360 * (i + 1) / ns),
              'yellow' if i % 2 == 0 else 'hull_dark')
    for i in range(8):                                                    # blue status ring
        a = math.radians(45 * i)
        x, y = (ri + 0.175) * math.cos(a), (ri + 0.175) * math.sin(a)
        M.add(g, cyl((x, y, top + 0.015), (x, y, top + 0.035), 0.022, n=8), 'glow')


def motor(M, g, x0, x1, y, z, r, cable_to=None):
    """Electric drive motor lying along x: ribbed can, end bell, terminal box, shaft coupling."""
    s = 1 if x1 > x0 else -1
    M.add(g, B(min(x0, x1), max(x0, x1), y - r * 0.9, y + r * 0.9, z - r - 0.04, z - r * 0.3), 'hull_dark')
    M.add(g, cyl((x0, y, z), (x1, y, z), r, n=16), 'hull_light')
    L = x1 - x0
    for t in np.linspace(0.18, 0.82, 5):
        x = x0 + L * t
        M.add(g, cyl((x - 0.012, y, z), (x + 0.012, y, z), r * 1.12, n=16), 'metal')
    M.add(g, cyl((x0 - s * 0.04, y, z), (x0, y, z), r * 0.85, n=16), 'hull_dark')
    M.add(g, cyl((x1, y, z), (x1 + s * 0.06, y, z), r * 0.45, n=12), 'metal_light')
    M.add(g, cbox(x0 + L * 0.5, y, z + r * 0.95, abs(L) * 0.32, r * 0.9, 0.05), 'hull_mid')
    M.add(g, cbox(x0 + L * 0.5, y, z + r * 0.95 + 0.03, abs(L) * 0.20, r * 0.5, 0.012), 'yellow')
    if cable_to is not None:
        cable(M, g, [(x0 + L * 0.5, y, z + r * 1.0), cable_to[0], cable_to[1]], 0.026, ends='yellow')


def bin_diag(M, g, k, d, hu, hv, z0, z1, ore, seed, H):
    """Output bin rotated onto the chamfered corner k."""
    R = rz(45 + 90 * k)
    hopper(M, g, d, 0, hu, hv, z0, z1, ore, seed, n=7, s=0.036 * max(1.0, H), R=R)


def mass_separator():
    M = Model(); h = 1.0; top = 0.20; ri = 0.55
    sep_bottom(M, h, 0.62)
    sep_spinner(M, 0.52, 4)
    sep_housing(M, h, ri, top)
    g = 'main'
    for k, ore in enumerate(('ore_fer', 'ore_salt', 'ore_fer', 'ore_salt')):
        bin_diag(M, g, k, 0.97, 0.10, 0.20, top - 0.03, top + 0.13, ore, 40 + k, h)
    # slag intake (+x): flanged pipe, slag band, valve wheel, junction box on the flange
    pipe(M, g, [(0.99, 0.0, top + 0.06), (0.74, 0.0, top + 0.12)], 0.065, m='metal',
         fl=[((0.93, 0.0, top + 0.075), (1, 0, 0.2)), ((0.80, 0.0, top + 0.105), (1, 0, 0.2))])
    M.add(g, cyl((0.86, 0, top + 0.09), (0.83, 0, top + 0.098), 0.07, n=10), 'ga_slag')
    M.add(g, B(0.66, 0.78, -0.09, 0.09, top, top + 0.16), 'hull_light')
    wheel(M, g, 0.72, 0.0, top + 0.20, r=0.06)
    # drive motor (-x)
    motor(M, g, -0.95, -0.70, 0.0, top + 0.13, 0.12, cable_to=((-0.86, -0.22, top + 0.10), (-0.92, -0.36, top - 0.02)))
    # edge grilles + lights
    for s in (-1, 1):
        grille(M, g, 0, s * 0.82, top - 0.01, 0.40, 0.08, n=6, glow='glow', R=None)
    bolts(M, g, [(0.84, 0.34), (0.84, -0.34), (-0.84, 0.34), (-0.84, -0.34)], top, r=0.02)
    return M


def mass_separator_2():
    M = Model(); h = 1.5; top = 0.24; ri = 0.86
    sep_bottom(M, h, 0.94)
    sep_spinner(M, 0.82, 8)
    sep_housing(M, h, ri, top)
    g = 'main'
    for k, ore in enumerate(('ore_baux', 'ore_cob', 'ore_wolf', 'ore_neo')):
        bin_diag(M, g, k, 1.47, 0.13, 0.27, top - 0.03, top + 0.16, ore, 60 + k, h)
    # rare outputs: iridite + tritium-ice canisters on the side flanks
    for (cx, cy, m, cap) in ((-1.20, -0.62, 'magnet', 'hull_light'), (1.20, 0.62, 'glass', 'glow')):
        M.add(g, cyl((cx, cy, top - 0.02), (cx, cy, top + 0.18), 0.12, n=16), 'hull_light')
        M.add(g, cyl((cx, cy, top + 0.18), (cx, cy, top + 0.20), 0.09, n=16), m)
        M.add(g, cyl((cx, cy, top + 0.20), (cx, cy, top + 0.215), 0.04, n=10), cap)
        M.add(g, cyl((cx, cy, top + 0.10), (cx, cy, top + 0.13), 0.128, n=16), 'yellow')
    # slag intake (+x) with valve
    pipe(M, g, [(1.49, -0.20, top + 0.08), (1.14, -0.20, top + 0.14), (1.04, -0.10, top + 0.14)], 0.075, m='metal',
         fl=[((1.42, -0.20, top + 0.095), (1, 0, 0.17)), ((1.24, -0.20, top + 0.125), (1, 0, 0.17))])
    M.add(g, cyl((1.34, -0.20, top + 0.11), (1.30, -0.20, top + 0.12), 0.082, n=12), 'ga_slag')
    M.add(g, B(0.98, 1.12, -0.24, 0.04, top, top + 0.17), 'hull_light')
    wheel(M, g, 1.05, -0.10, top + 0.22, r=0.07)
    # twin drive motors (-x)
    for y in (-0.30, 0.30):
        motor(M, g, -1.42, -1.04, y, top + 0.15, 0.14)
        M.add(g, B(-1.10, -0.98, y - 0.09, y + 0.09, top - 0.01, top + 0.20), 'hull_mid')
    M.add(g, B(-1.40, -1.18, -0.08, 0.08, top - 0.01, top + 0.10), 'hull_dark')
    M.add(g, cbox(-1.29, 0, top + 0.105, 0.14, 0.05, 0.012), 'glow')
    for s in (-1, 1):
        grille(M, g, 0, s * 1.24, top - 0.01, 0.62, 0.10, n=8, glow='glow')
        light(M, g, s * 0.55, s * 1.24, top - 0.01, 0.05, 0.05)
    bolts(M, g, [(1.26, 0.20), (-1.26, 0.62), (1.26, -0.62), (-1.26, -0.62)], top, r=0.022)
    return M


def render_separator(name, M, canvas):
    bot, _ = rl(M, ['bottom'], ['bottom', 'main'], canvas)
    spin, _ = rl(M, ['spinner'], ['spinner'], canvas)
    main, hm = rl(M, ['main'], ['main'], canvas, wmat(glow=1.0))
    save(bot, D, f'{name}-bottom'); save(spin, D, f'{name}-spinner'); save(main, D, name)
    save(glow_sprite(hm), D, f'{name}-glow')
    f = liquid_tile(bot, 'ffa166', 0.80)
    f = over(over(f, spin), main)
    save(f, D, f'{name}-full')
    FULL[name] = f
    return M


def liquid_tile(bot, col, a):
    """DrawLiquidTile preview: liquid over the whole block area (behind the housing)."""
    f = np.asarray(bot).copy()
    m = f[..., 3] > 0
    f[m, :3] = (f[m, :3] * (1 - a) + hexc(col) * a).astype(np.uint8)
    return f


# ================================================================== Bauxite electrolyzer (2x2) - Hall-Heroult cell
EBX, EBY = 0.54, 0.40          # bath opening half-sizes


def electrolyzer():
    M = Model()
    g = 'bottom'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.26), 0.0, 0.06, 0.985), 'hull_dark')
    M.add(g, B(-0.60, 0.60, -0.46, 0.46, 0.06, 0.07), 'vent')
    for x in np.linspace(-0.45, 0.45, 6):
        M.add(g, B(x - 0.05, x + 0.05, -0.40, 0.40, 0.07, 0.074), 'cable')
    g = 'main'
    holed_plate(M, g, 0.985, 0.26, ('rect', EBX, EBY), 0.0, 0.10, 'hull_dark')
    holed_plate(M, g, 0.90, 0.24, ('rect', EBX + 0.03, EBY + 0.03), 0.10, 0.20, 'hull_mid', inset=0.02)
    top = 0.20
    # bath rim: steel lip with inner chamfer
    for (x0, x1, y0, y1) in ((-EBX - 0.08, EBX + 0.08, EBY, EBY + 0.08), (-EBX - 0.08, EBX + 0.08, -EBY - 0.08, -EBY),
                             (-EBX - 0.08, -EBX, -EBY, EBY), (EBX, EBX + 0.08, -EBY, EBY)):
        M.add(g, B(x0, x1, y0, y1, top, top + 0.04), 'metal')
    # electrode stack: alternating graphite anodes / aluminium cathodes, hung from two copper bus bars
    xs = [-0.40, -0.20, 0.0, 0.20, 0.40]
    for i, x in enumerate(xs):
        an = i % 2 == 0
        M.add(g, B(x - 0.032, x + 0.032, -0.33, 0.33, 0.08, 0.26), 'tung' if an else 'alu')
        M.add(g, B(x - 0.02, x + 0.02, -0.31, 0.31, 0.26, 0.268), 'hull_dark' if an else 'metal_light')
        yl = 0.29 if an else -0.29
        M.add(g, B(x - 0.04, x + 0.04, yl - 0.05, yl + 0.05, 0.24, 0.36), 'copper')
        M.add(g, cyl((x, yl, 0.36), (x, yl, 0.375), 0.02, n=6), 'metal_light')
    for s, mat in ((1, 'copper'), (-1, 'copper')):
        M.add(g, B(-0.62, 0.62, s * 0.29 - 0.045, s * 0.29 + 0.045, 0.33, 0.40), mat)
        M.add(g, B(-0.60, 0.60, s * 0.29 - 0.018, s * 0.29 + 0.018, 0.40, 0.405), 'heat')
    # bus terminals (sides) + rectifier cables
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(g, B(sx * 0.60, sx * 0.80, sy * 0.29 - 0.09, sy * 0.29 + 0.09, top - 0.01, top + 0.22), 'hull_light')
            M.add(g, B(sx * 0.63, sx * 0.77, sy * 0.29 - 0.06, sy * 0.29 + 0.06, top + 0.22, top + 0.23), 'yellow' if sy > 0 else 'hull_dark')
            bolts(M, g, [(sx * 0.66, sy * 0.29), (sx * 0.74, sy * 0.29)], top + 0.23, r=0.017)
    for s in (-1, 1):
        cable(M, g, [(-0.90, s * 0.08, top - 0.02), (-0.86, s * 0.16, top + 0.12), (-0.80, s * 0.29, top + 0.20)], 0.03, ends='copper')
    M.add(g, B(-0.95, -0.84, -0.14, 0.14, top - 0.01, top + 0.05), 'hull_light')
    M.add(g, cbox(-0.895, 0, top + 0.055, 0.04, 0.16, 0.01), 'yellow')
    # chlorine collection header (back) with three vent stacks + outlet valve (+x)
    pipe(M, g, [(-0.62, 0.64, top + 0.10), (0.62, 0.64, top + 0.10), (0.96, 0.64, top + 0.06)], 0.06, m='steel',
         fl=[((-0.30, 0.64, top + 0.10), (1, 0, 0)), ((0.30, 0.64, top + 0.10), (1, 0, 0)), ((0.88, 0.64, top + 0.07), (1, 0, -0.12))])
    M.add(g, cyl((-0.62, 0.64, top + 0.10), (-0.66, 0.64, top + 0.10), 0.07, n=10), 'hull_light')
    for x in (-0.44, 0.0, 0.44):
        M.add(g, B(x - 0.05, x + 0.05, 0.42, 0.58, top + 0.02, top + 0.14), 'steel')
        M.add(g, cyl((x, 0.64, top + 0.10), (x, 0.64, top + 0.34), 0.06, n=12), 'metal')
        M.add(g, cyl((x, 0.64, top + 0.24), (x, 0.64, top + 0.27), 0.068, n=12), 'chlor')
        M.add(g, cyl((x, 0.64, top + 0.34), (x, 0.64, top + 0.36), 0.075, n=12), 'hull_dark')
        M.add(g, cyl((x, 0.64, top + 0.355), (x, 0.64, top + 0.362), 0.045, n=10), 'gglow')
    wheel(M, g, 0.74, 0.64, top + 0.20, r=0.055, m='chlor')
    M.add(g, cyl((0.86, 0.64, top + 0.075), (0.90, 0.64, top + 0.07), 0.068, n=10), 'chlor')
    # bauxite feed hopper (front-left) + aluminium ingot stack (front-right) + hazard strip
    hopper(M, g, -0.50, -0.68, 0.22, 0.16, top - 0.02, top + 0.16, 'ore_baux', 51, n=9, s=0.04)
    M.add(g, B(-0.50 - 0.04, -0.50 + 0.04, -0.52, -0.44, top + 0.04, top + 0.12), 'hull_light')
    M.add(g, B(0.30, 0.74, -0.86, -0.50, top - 0.01, top + 0.02), 'hull_dark')
    ingots(M, g, 0.52, -0.68, top + 0.02, 'alu', nx=2, ny=2, L=0.19, w=0.11, layers=2)
    # rectifier cabinet between them (fins + status lamp)
    M.add(g, B(-0.17, 0.17, -0.82, -0.50, top - 0.01, top + 0.12), 'hull_light')
    fins(M, g, -0.14, 0.14, -0.79, -0.60, top + 0.12, top + 0.16, 5, along='x', m='metal')
    M.add(g, cbox(0, -0.55, top + 0.125, 0.18, 0.05, 0.012), 'gglow')
    chevrons(M, g, 0, -0.89, top - 0.012, 0.30, 0.05, n=4)
    for (x, y) in ((-0.84, 0.84 - 0.30), (0.84, 0.84 - 0.30)):
        M.add(g, cbox(x, y, top + 0.01, 0.07, 0.07, 0.02), 'hull_dark')
        M.add(g, cbox(x, y, top + 0.02, 0.045, 0.045, 0.02), 'gglow')
    bolts(M, g, [(-0.84, -0.40), (0.84, -0.40)], top, r=0.02)
    return M


def render_electrolyzer():
    M = electrolyzer()
    name = 'bauxite-electrolyzer'
    bot, _ = rl(M, ['bottom'], ['bottom', 'main'], 64)
    main, hm = rl(M, ['main'], ['main'], 64, wmat(gglow=1.0, chlor=0.45, heat=0.25))
    # electrolyte shimmer: soft glow over the open bath (between the electrodes)
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    X = (xx + 0.5 - 32) / 32; Y = (32 - (yy + 0.5)) / 32
    bath = (np.abs(X) < EBX) & (np.abs(Y) < EBY) & (main[..., 3] == 0)
    hm = np.maximum(hm, bath * 0.42)
    save(bot, D, f'{name}-bottom'); save(main, D, name); save(glow_sprite(hm), D, f'{name}-glow')
    f = over(liquid_tile(bot, '74d45a', 0.55), main)
    save(f, D, f'{name}-full')
    FULL[name] = f
    return M


# ================================================================== Alloy furnace (3x3) - cobalt induction furnace
def alloy_furnace():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(1.48, 1.48, 0.38), 0.0, 0.10, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.37, 1.37, 0.36), 0.10, 0.24, 0.97), 'hull_mid')
    top = 0.24
    corner_caps(M, g, 1.37, 0.36, top, k_list=(0, 1, 2, 3), lamp='glow')
    for k in range(4):
        grille(M, g, 0, -1.26, top - 0.01, 0.62 if k in (1, 3) else 0.50, 0.09, n=8, glow='glow', R=rz(90 * k))
    fx, fy = 0.0, 0.06
    # platform + coil assembly
    M.add(g, prism(octp(1.00, fx, fy), top, top + 0.06, 0.97), 'hull_dark')
    M.add(g, annulus(fx, fy, 0.90, 0.60, top + 0.06, top + 0.12, 48), 'hull_mid')
    M.add(g, annulus(fx, fy, 0.92, 0.86, top + 0.06, top + 0.20, 48, ro_t=0.90), 'metal')
    nturn = 30
    for i in range(nturn):
        a = 360 * i / nturn
        if i % 5 == 0:
            continue
        add_R(M, g, B(0.63, 0.85, -0.032, 0.032, top + 0.12, top + 0.21), 'ga_coil', rz(a), (fx, fy, 0))
    for i in range(6):                                             # cobalt flux yokes
        R = rz(360 * i / 6)
        add_R(M, g, B(0.60, 0.94, -0.075, 0.075, top + 0.06, top + 0.26), 'cobalt', R, (fx, fy, 0))
        add_R(M, g, B(0.66, 0.90, -0.05, 0.05, top + 0.26, top + 0.27), 'hull_dark', R, (fx, fy, 0))
        add_R(M, g, cyl((0.86, 0, top + 0.26), (0.86, 0, top + 0.285), 0.02, n=6), 'metal_light', R, (fx, fy, 0))
        add_R(M, g, cyl((0.70, 0, top + 0.26), (0.70, 0, top + 0.285), 0.02, n=6), 'metal_light', R, (fx, fy, 0))
    # crucible: refractory wall, chamfered steel rim, molten pool with dross
    M.add(g, annulus(fx, fy, 0.62, 0.47, top + 0.06, top + 0.34, 40, ri_t=0.48), 'ga_refr')
    M.add(g, annulus(fx, fy, 0.625, 0.50, top + 0.34, top + 0.38, 40, ro_t=0.58), 'metal_light')
    for i in range(10):
        a = math.radians(18 + 36 * i)
        M.add(g, cyl((fx + 0.565 * math.cos(a), fy + 0.565 * math.sin(a), top + 0.37),
                     (fx + 0.565 * math.cos(a), fy + 0.565 * math.sin(a), top + 0.392), 0.02, n=6), 'hull_dark')
    M.add(g, cyl((fx, fy, top + 0.20), (fx, fy, top + 0.31), 0.48, n=36), 'flame')
    M.add(g, cyl((fx + 0.05, fy + 0.04, top + 0.30), (fx + 0.05, fy + 0.04, top + 0.315), 0.20, n=24), 'ga_melt')
    rr = np.random.default_rng(17)
    for i in range(7):
        a = rr.uniform(0, 2 * math.pi); d = rr.uniform(0.12, 0.36)
        M.add(g, prism(hexp(0.035 + 0.03 * rr.random(), fx + d * math.cos(a), fy + d * math.sin(a), rr.uniform(0, 60)),
                       top + 0.30, top + 0.318, 0.7), 'heat')
    # pouring lip -> trough -> ingot moulds (front centre)
    M.add(g, B(-0.08, 0.08, -0.98, -0.50, top + 0.20, top + 0.27), 'metal')
    M.add(g, B(-0.045, 0.045, -0.98, -0.50, top + 0.27, top + 0.278), 'flame')
    for s in (-1, 1):
        M.add(g, B(s * 0.08, s * 0.10, -0.98, -0.50, top + 0.20, top + 0.30), 'hull_dark')
    M.add(g, B(-0.30, 0.30, -1.22, -0.98, top - 0.01, top + 0.08), 'hull_light')
    for x in (-0.18, 0.0, 0.18):
        M.add(g, B(x - 0.07, x + 0.07, -1.18, -1.02, top + 0.08, top + 0.085), 'hull_dark')
        M.add(g, prism(rect(x, -1.10, 0.055, 0.06), top + 0.04, top + 0.09, top_poly=rect(x, -1.10, 0.04, 0.045)),
              'flame' if x == 0.0 else 'cobalt')
    # input hoppers (back): cobaltite left, titanium right; feed chutes into the crucible
    for s, ore, seed in ((-1, 'ore_cob', 71), (1, 'ga_ti', 73)):
        cx, cy = s * 0.86, 0.92
        hopper(M, g, cx, cy, 0.24, 0.20, top - 0.02, top + 0.22, ore, seed, n=10, s=0.05)
        M.add(g, B(cx - 0.24, cx + 0.24, cy - 0.23, cy - 0.20, top + 0.14, top + 0.23), 'yellow')
        M.add(g, tf(prism(rect(0, 0, 0.06, 0.20), 0, 0.05), rz(-s * 40), (s * 0.55, 0.60, top + 0.36)), 'metal')
        M.add(g, tf(prism(rect(0, 0, 0.035, 0.18), 0.05, 0.055), rz(-s * 40), (s * 0.55, 0.60, top + 0.36)), ore)
    # steel ingot stack (front-left), cobalt-alloy output rack (front-right)
    M.add(g, B(-1.12, -0.62, -1.12, -0.70, top - 0.01, top + 0.03), 'hull_dark')
    ingots(M, g, -0.87, -0.91, top + 0.03, 'steel', nx=2, ny=4, L=0.20, w=0.075, layers=2)
    M.add(g, B(0.62, 1.12, -1.12, -0.70, top - 0.01, top + 0.03), 'hull_dark')
    ingots(M, g, 0.87, -0.91, top + 0.03, 'cobalt', nx=2, ny=4, L=0.20, w=0.075, layers=2)
    for x in (-1.12, -0.64, 0.62, 1.10):
        M.add(g, B(x, x + 0.02, -1.12, -0.70, top - 0.01, top + 0.14), 'hull_light')
    # slag inlet (+x side) with valve; capacitor bank + copper bus (-x side)
    pipe(M, g, [(1.49, 0.06, top + 0.06), (1.10, 0.06, top + 0.14), (0.92, 0.06, top + 0.26)], 0.07, m='metal',
         fl=[((1.40, 0.06, top + 0.08), (1, 0, 0.2)), ((1.18, 0.06, top + 0.12), (1, 0, 0.2))])
    M.add(g, cyl((1.30, 0.06, top + 0.10), (1.26, 0.06, top + 0.11), 0.078, n=12), 'ga_slag')
    wheel(M, g, 1.10, 0.26, top + 0.16, r=0.06)
    M.add(g, cyl((1.10, 0.26, top), (1.10, 0.26, top + 0.14), 0.03, n=8), 'metal')
    for y in (-0.36, 0.06, 0.48):
        M.add(g, cyl((-1.16, y, top - 0.01), (-1.16, y, top + 0.24), 0.14, n=18), 'hull_light')
        M.add(g, cyl((-1.16, y, top + 0.24), (-1.16, y, top + 0.27), 0.12, n=18), 'cobalt')
        M.add(g, cyl((-1.16, y, top + 0.15), (-1.16, y, top + 0.18), 0.145, n=18), 'yellow')
        M.add(g, cyl((-1.12, y + 0.04, top + 0.27), (-1.12, y + 0.04, top + 0.31), 0.025, n=8), 'copper')
        M.add(g, B(-1.12, -0.86, y - 0.03, y + 0.03, top + 0.28, top + 0.31), 'copper')
    # exhaust hood with glowing throat (back centre)
    M.add(g, B(-0.22, 0.22, 1.02, 1.32, top - 0.01, top + 0.14), 'hull_light')
    M.add(g, cyl((0, 1.16, top + 0.14), (0, 1.16, top + 0.40), 0.12, 0.11, n=16), 'metal')
    M.add(g, cyl((0, 1.16, top + 0.40), (0, 1.16, top + 0.43), 0.13, n=16), 'hull_dark')
    M.add(g, cyl((0, 1.16, top + 0.35), (0, 1.16, top + 0.432), 0.08, n=14), 'ga_ember')
    pipe(M, g, [(0, 0.70, top + 0.40), (0, 0.92, top + 0.42), (0, 1.06, top + 0.36)], 0.05, m='steel')
    cable(M, g, [(1.30, -0.62, top + 0.02), (1.12, -0.50, top + 0.14), (0.90, -0.40, top + 0.18)], 0.03, ends='yellow')
    bolts(M, g, [(-1.26, 0.92), (1.26, 0.92), (-1.26, -0.92), (1.26, -0.92)], top, r=0.022)
    return M


def render_alloy_furnace():
    M = alloy_furnace()
    main, hm = rl(M, ['main'], ['main'], 96, wmat(flame=1.0, ga_melt=1.0, ga_ember=0.85, ga_coil=0.45, heat=0.35))
    save(main, D, 'alloy-furnace')
    save(glow_sprite(hm), D, 'alloy-furnace-glow')
    save(main, D, 'alloy-furnace-full')
    FULL['alloy-furnace'] = main
    return M


# ================================================================== driver
JOBS = [
    ('steel-smelter', render_steel_smelter),
    ('propellant-press', render_propellant_press),
    ('mass-separator', lambda: render_separator('mass-separator', mass_separator(), 64)),
    ('mass-separator-2', lambda: render_separator('mass-separator-2', mass_separator_2(), 96)),
    ('bauxite-electrolyzer', render_electrolyzer),
    ('alloy-furnace', render_alloy_furnace),
]

if __name__ == '__main__':
    only = sys.argv[1:]
    for name, fn in JOBS:
        if only and name not in only:
            continue
        M = fn()
        per = {g: sum(len(T) for T, _ in v) for g, v in M.parts.items()}
        print(f'{name:22s} {M.ntri():6d} tris  ' + '  '.join(f'{g}={n}' for g, n in per.items()))
    qa_sheet([n for n, _ in JOBS], 'g_industry_a.png', sc=3, cols=3)
