"""Hero-level artillery remakes at the Cybran LRA detail budget.
Howl (T1 UEF mortar 2x2), Redoubt (T2 UEF fortified triple howitzer 3x3),
Mantis (T3 Cybran heavy artillery with a Scathis 6-barrel drum, 4x4).
Groups: base (static), body (rotating head), barrel (recoiling, elevated)."""
import numpy as np, math
from geom import *
from mats import Model, MID
from models import bolts, light, chevrons
from hero import *

SPEC = {}

# ================================================================== Howl, T1 UEF mortar
def howl5():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 1.0, top=0.18)
    g = 'body'
    hull = mirror_half([(0, 0.66), (0.40, 0.60), (0.62, 0.30), (0.66, -0.20), (0.54, -0.56), (0.26, -0.72), (0, -0.74)])
    M.add(g, prism(hull, z, z+0.24, 0.92), 'hull_mid')
    deck = scale_poly(hull, 0.84, (0, 0))
    M.add(g, prism(deck, z+0.24, z+0.29, 0.95), 'hull_light')
    top = z+0.29
    for s in (-1, 1):
        pl = [(s*0.14, 0.50), (s*0.34, 0.46), (s*0.48, 0.22), (s*0.16, 0.18)]
        zf = (lambda x, y: top+0.08-(y-0.18)*0.24)
        slope_plate(M, g, pl, zf, 'hull_light', thick=0.10, inlay='yellow', isc=0.62, ih=0.02)
        bolts_on(M, g, [(s*0.21, 0.24), (s*0.38, 0.28)], zf, r=0.018)
        light(M, g, s*0.47, 0.36, top, 0.045, 0.04)
        # ammo boxes with lid, hazard strip, handle and feed cable
        M.add(g, cbox(s*0.48, -0.24, top+0.06, 0.20, 0.44, 0.12), 'hull_dark')
        M.add(g, cbox(s*0.48, -0.24, top+0.125, 0.16, 0.38, 0.012), 'hull_mid')
        M.add(g, cbox(s*0.48, -0.43, top+0.133, 0.14, 0.035, 0.008), 'yellow')
        bolts(M, g, [(s*0.42, -0.07), (s*0.54, -0.07), (s*0.42, -0.41), (s*0.54, -0.41)], top+0.125, r=0.016)
        M.add(g, tube_path([(s*0.43, -0.18, top+0.13), (s*0.43, -0.18, top+0.165), (s*0.53, -0.18, top+0.165), (s*0.53, -0.18, top+0.13)], 0.012, n=6), 'metal_light')
        cable(M, g, [(s*0.38, -0.10, top+0.09), (s*0.25, -0.04, top+0.11), (s*0.14, 0.02, top+0.08)], 0.026)
        # trunnion caps
        M.add(g, cyl((s*0.20, 0.06, top), (s*0.31, 0.06, top), 0.11, n=18), 'metal')
        M.add(g, cyl((s*0.31, 0.06, top), (s*0.35, 0.06, top), 0.085, n=16), 'hull_dark')
        M.add(g, cyl((s*0.35, 0.06, top), (s*0.362, 0.06, top), 0.04, n=10), 'glow')
        # exhausts
        M.add(g, cyl((s*0.26, -0.64, top-0.02), (s*0.26, -0.64, top+0.08), 0.045, n=10), 'metal')
        M.add(g, cyl((s*0.26, -0.64, top+0.08), (s*0.26, -0.64, top+0.085), 0.03, n=8), 'heat')
    grille(M, g, 0, -0.50, top, 0.36, 0.12, n=6, glow='glow')
    antenna(M, g, (0.16, -0.62, top), (0.22, -0.88, top+0.42))
    seam(M, g, (-0.30, -0.02), (0.30, -0.02), top, w=0.022, h=0.012)
    g = 'barrel_local'
    M.add(g, box(-0.19, 0.19, -0.38, 0.10, -0.14, 0.14), 'hull_mid')
    M.add(g, box(-0.13, 0.13, -0.32, 0.04, 0.14, 0.18), 'yellow')
    M.add(g, box(-0.08, 0.08, -0.30, 0.02, 0.18, 0.192), 'hull_dark')
    M.add(g, box(-0.14, 0.14, -0.46, -0.38, -0.10, 0.10), 'metal')
    M.add(g, cyl((0, -0.46, 0), (0, -0.50, 0), 0.06, n=12), 'glow')
    M.add(g, cyl((0, 0.08, 0), (0, 0.46, 0), 0.20, n=24), 'hull_dark')
    for y in (0.12, 0.32):
        M.add(g, cyl((0, y, 0), (0, y+0.05, 0), 0.225, n=24), 'metal_light')
    for s in (-1, 1):
        hydraulic(M, g, s*0.25, 0.02, -0.28, 0.38, 0.60, r=0.048)
    M.add(g, cyl((0, 0.46, 0), (0, 1.00, 0), 0.165, 0.152, n=24), 'metal')
    for y in (0.62, 0.82):
        M.add(g, cyl((0, y-0.025, 0), (0, y+0.025, 0), 0.178, n=24), 'hull_mid')
    M.add(g, cyl((0, 1.00, 0), (0, 1.16, 0), 0.18, 0.205, n=24), 'hull_dark')
    M.add(g, cyl((0, 1.16, 0), (0, 1.172, 0), 0.16, n=22), 'metal_light')
    M.add(g, cyl((0, 1.16, 0), (0, 1.18, 0), 0.12, n=20), 'bore')
    pv = (0, 0.06, top); elevate(M, 30, pv)
    SPEC['howl'] = muzzle_world(30, pv, 1.18)
    return M

# ================================================================== Redoubt, T2 UEF fortified howitzer
def redoubt5():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 1.5, top=0.20)
    g = 'body'
    hull = mirror_half([(0, 1.06), (0.52, 1.00), (0.98, 0.60), (1.14, 0.02), (1.10, -0.62), (0.86, -1.06), (0.40, -1.24), (0, -1.26)])
    M.add(g, prism(hull, z, z+0.30, 0.93), 'hull_dark')
    deck = scale_poly(hull, 0.86, (0, 0))
    M.add(g, prism(deck, z+0.30, z+0.38, 0.96), 'hull_mid')
    top = z+0.38
    for s in (-1, 1):
        sp = [(s*0.60, 0.50), (s*0.92, 0.32), (s*1.02, -0.40), (s*0.84, -0.86), (s*0.60, -0.72)]
        zf = (lambda x, y: top+0.12-(abs(x)-0.60)*0.34)
        slope_plate(M, g, sp, zf, 'hull_light', thick=0.14, inlay='yellow', isc=0.60, ih=0.018)
        bolts_on(M, g, [(s*0.66, 0.38), (s*0.92, -0.04), (s*0.88, -0.56), (s*0.66, -0.62)], zf, r=0.022)
        light(M, g, s*0.70, 0.30, zf(0.70, 0)-0.01, 0.05, 0.04)
        # exhaust stacks + whip antennas
        ex, ey = s*0.76, -0.98
        M.add(g, cyl((ex, ey, z+0.28), (ex, ey, top+0.16), 0.07, n=12), 'metal')
        M.add(g, cyl((ex, ey, top+0.16), (ex, ey, top+0.19), 0.085, n=12), 'hull_dark')
        M.add(g, cyl((ex, ey, top+0.19), (ex, ey, top+0.196), 0.05, n=10), 'heat')
        antenna(M, g, (s*0.50, -1.00, top), (s*0.62, -1.44, top+0.70))
        # trunnion blocks at mantlet sides
        M.add(g, cyl((s*0.62, 0.62, top+0.16), (s*0.74, 0.62, top+0.16), 0.13, n=18), 'metal')
        M.add(g, cyl((s*0.74, 0.62, top+0.16), (s*0.80, 0.62, top+0.16), 0.10, n=16), 'hull_dark')
        M.add(g, cyl((s*0.80, 0.62, top+0.16), (s*0.815, 0.62, top+0.16), 0.05, n=12), 'glow')
        bolts(M, g, [(s*0.50, 0.50), (s*0.50, 0.84)], top+0.25, r=0.02)
    # mantlet
    M.add(g, prism(cham_rect(0.64, 0.25, 0.10, cy=0.68), top-0.04, top+0.22, 0.93), 'hull_light')
    M.add(g, prism(cham_rect(0.54, 0.17, 0.08, cy=0.66), top+0.22, top+0.25, 0.96), 'hull_mid')
    M.add(g, cbox(0, 0.86, top+0.255, 0.86, 0.035, 0.01), 'yellow')
    # open magazine with 6 shells in a rack
    M.add(g, box(-0.50, 0.50, -0.92, -0.44, top-0.03, top+0.01), 'vent')
    for i in range(6):
        shell(M, g, -0.40+i*0.16, -0.68, top+0.03, L=0.40, r=0.055)
    for y in (-0.92, -0.44):
        M.add(g, box(-0.55, 0.55, y-0.03, y+0.03, top-0.02, top+0.11), 'hull_light')
    for x in (-0.55, 0.55):
        M.add(g, box(x-0.03, x+0.03, -0.95, -0.41, top-0.02, top+0.11), 'hull_light')
    bolts(M, g, [(-0.55, -0.92), (0.55, -0.92), (-0.55, -0.44), (0.55, -0.44)], top+0.11, r=0.02)
    chevrons(M, g, 0, -1.00, top, 0.56, 0.07, n=6)
    # commander cupola with periscopes (right) and sensor dish (left)
    cx, cy = 0.48, -0.22
    M.add(g, cyl((cx, cy, top-0.01), (cx, cy, top+0.13), 0.17, 0.155, n=18), 'hull_light')
    M.add(g, cyl((cx, cy, top+0.13), (cx, cy, top+0.16), 0.12, n=18), 'hull_mid')
    for i in range(6):
        M.add(g, tf(cbox(0.135, 0, top+0.145, 0.04, 0.06, 0.03), rz(60*i+30), (cx, cy, 0)), 'glass')
    M.add(g, cyl((cx, cy, top+0.16), (cx, cy, top+0.18), 0.055, n=12), 'metal_light')
    M.add(g, cbox(cx, cy+0.09, top+0.17, 0.07, 0.025, 0.015), 'glow')
    dx, dy = -0.48, -0.22
    M.add(g, cyl((dx, dy, top-0.01), (dx, dy, top+0.08), 0.07, n=10), 'metal')
    M.add(g, cyl((dx, dy, top+0.08), (dx, dy, top+0.15), 0.18, 0.15, n=20), 'hull_light')
    M.add(g, cyl((dx, dy, top+0.15), (dx, dy, top+0.16), 0.12, n=18), 'hull_dark')
    for i in range(3):
        a = math.radians(120*i+90)
        M.add(g, cyl((dx+0.13*math.cos(a), dy+0.13*math.sin(a), top+0.155), (dx, dy, top+0.25), 0.011, n=6), 'metal')
    M.add(g, sphereish((dx, dy, top+0.25), 0.03, n=8), 'glow')
    seam(M, g, (-0.30, -0.40), (0.30, -0.40), top, w=0.024, h=0.012)
    # ---- triple howitzer
    g = 'barrel_local'; XS = (-0.34, 0.0, 0.34)
    M.add(g, box(-0.58, 0.58, -0.48, 0.22, -0.14, 0.12), 'hull_mid')
    M.add(g, box(-0.50, 0.50, -0.42, 0.16, 0.12, 0.16), 'hull_light')
    for y0 in (-0.10, 0.06):
        M.add(g, box(-0.46, 0.46, y0, y0+0.05, 0.16, 0.172), 'yellow')
    bolts(M, g, [(-0.44, -0.36), (0.44, -0.36), (-0.44, 0.12), (0.44, 0.12)], 0.16, r=0.02)
    for x in XS:
        M.add(g, box(x-0.10, x+0.10, -0.62, -0.48, -0.09, 0.09), 'metal')
        M.add(g, cyl((x, -0.62, 0), (x, -0.66, 0), 0.05, n=10), 'glow')
        M.add(g, cyl((x, 0.22, 0), (x, 0.70, 0), 0.125, n=20), 'hull_dark')
        for y in (0.28, 0.54):
            M.add(g, cyl((x, y, 0), (x, y+0.05, 0), 0.145, n=20), 'metal_light')
        M.add(g, cyl((x, 0.70, 0), (x, 1.40, 0), 0.098, n=20), 'metal')
        M.add(g, cyl((x, 1.40, 0), (x, 1.90, 0), 0.086, n=18), 'metal')
        for y in (1.12, 1.40, 1.66):
            M.add(g, cyl((x, y-0.025, 0), (x, y+0.025, 0), 0.11, n=18), 'hull_mid')
        muzzle_brake(M, g, 1.90, 0.30, 0.105, x=x, nb=3, trim='yellow', bore_r=0.05, out=0.045)
        cable(M, g, [(x+0.07, -0.30, 0.17), (x+0.09, 0.05, 0.17), (x+0.07, 0.30, 0.13)], 0.022)
    for s in (-1, 1):
        hydraulic(M, g, s*0.58, 0.0, -0.36, 0.70, 1.02, r=0.06)
    M.add(g, box(-0.52, 0.52, 0.96, 1.04, -0.05, 0.06), 'hull_mid')
    M.add(g, box(-0.20, 0.20, 0.97, 1.03, 0.06, 0.08), 'yellow')
    pv = (0, 0.58, top+0.30); elevate(M, 14, pv)
    SPEC['redoubt'] = muzzle_world(14, pv, 2.222)
    return M

# ================================================================== Mantis, T3 Cybran heavy artillery + Scathis drum
def mantis5():
    M = Model(); g = 'base'
    cy_hero_base(M, g, 4/3)
    g = 'body'; F = 1.3
    def B(x0, x1, y0, y1, z0, z1): return box(x0*F, x1*F, y0*F, y1*F, z0, z1)
    def CB(cx, cy, cz, sx, sy, sz): return cbox(cx*F, cy*F, cz, sx*F, sy*F, sz)
    def C(p0, p1, r0, r1=None, n=20): return cyl((p0[0]*F, p0[1]*F, p0[2]), (p1[0]*F, p1[1]*F, p1[2]), r0*F, None if r1 is None else r1*F, n=n)
    def PP(pts): return P([(x*F, y*F) for x, y in pts])
    HH = [(0, 1.0), (0.36, 0.90), (0.60, 0.58), (0.74, 0.12), (0.70, -0.42), (0.56, -0.86), (0.28, -1.08), (0, -1.14)]
    hull = PP(mirror_half(HH))
    M.add(g, prism(hull, 0.46, 0.80, 0.86), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.80, (0, 0)), 0.79, 0.90, 0.84), 'hull_mid')
    sh = [(0.17, 0.32), (0.40, 0.22), (0.45, -0.30), (0.34, -0.58), (0.17, -0.48)]
    for s in (1, -1):
        M.add(g, prism(PP([(s*x, y) for x, y in sh]), 0.90, 0.96, 0.86), 'red_armor')
        for (x, y) in ((0.36, 0.12), (0.36, -0.36), (0.22, -0.40)):
            M.add(g, C((s*x, y, 0.955), (s*x, y, 0.975), 0.025, n=8), 'metal_light')
    for i, y in enumerate((0.18, -0.04, -0.26, -0.48)):
        b = rect(0, y*F, 0.075*F, 0.075*F); t = rect(0, (y-0.07)*F, 0.022*F, 0.03*F)
        M.add(g, loft(ring(b, 0.90), ring(t, 1.08-i*0.012)), 'hull_light')
        M.add(g, B(-0.03, 0.03, y-0.115, y-0.095, 0.90, 0.925), 'rglow')
    M.add(g, B(-0.36, 0.36, -0.70, -0.52, 0.895, 0.905), 'vent')
    M.add(g, B(-0.32, 0.32, -0.68, -0.54, 0.895, 0.912), 'heat')
    for i in range(9):
        x = -0.28+i*0.07
        M.add(g, B(x-0.014, x+0.014, -0.69, -0.53, 0.912, 0.94), 'metal')
    # rear reactor drum + side exhausts
    M.add(g, C((-0.42, -0.92, 0.80), (0.42, -0.92, 0.80), 0.27, n=24), 'metal')
    for x in (-0.30, -0.10, 0.10, 0.30):
        M.add(g, C((x-0.025, -0.92, 0.80), (x+0.025, -0.92, 0.80), 0.295, n=24), 'red_armor')
    for s in (-1, 1):
        M.add(g, C((s*0.42, -0.92, 0.80), (s*0.48, -0.92, 0.80), 0.19, n=16), 'hull_dark')
        M.add(g, C((s*0.48, -0.92, 0.80), (s*0.51, -0.92, 0.80), 0.08, n=12), 'rglow')
        M.add(g, C((s*0.46, -0.80, 0.62), (s*0.50, -1.12, 0.62), 0.085, n=12), 'hull_dark')
        M.add(g, C((s*0.50, -1.11, 0.62), (s*0.505, -1.135, 0.62), 0.055, n=10), 'heat')
    # sensor pods
    M.add(g, CB(-0.42, 0.52, 0.86, 0.26, 0.32, 0.17), 'hull_mid')
    M.add(g, CB(-0.42, 0.50, 0.955, 0.18, 0.20, 0.03), 'hull_light')
    M.add(g, C((-0.42, 0.67, 0.87), (-0.42, 0.72, 0.87), 0.09, n=14), 'metal')
    M.add(g, C((-0.42, 0.70, 0.87), (-0.42, 0.735, 0.87), 0.062, n=14), 'rglow')
    M.add(g, CB(0.42, 0.56, 0.84, 0.16, 0.22, 0.12), 'hull_light')
    M.add(g, C((0.42, 0.66, 0.85), (0.42, 0.70, 0.85), 0.045, n=10), 'rglow')
    antenna(M, g, (0.34*F, -0.52*F, 0.93), (0.62*F, -1.30*F, 1.40), tip='rglow')
    antenna(M, g, (-0.30*F, -0.56*F, 0.93), (-0.46*F, -1.12*F, 1.25), tip='rglow')
    # gun mount, trunnions, struts, feed cables, heat strips
    M.add(g, CB(0, 0.55, 0.94, 0.50, 0.46, 0.28), 'hull_mid')
    M.add(g, CB(0, 0.55, 1.085, 0.32, 0.30, 0.03), 'hull_light')
    for s in (-1, 1):
        M.add(g, C((s*0.25, 0.55, 1.0), (s*0.36, 0.55, 1.0), 0.12, n=16), 'metal')
        M.add(g, C((s*0.36, 0.55, 1.0), (s*0.38, 0.55, 1.0), 0.06, n=10), 'red_armor')
        a = np.array([s*0.17, -0.16, 0.92]); b = np.array([s*0.17, 0.40, 1.05]); m = a+(b-a)*0.55
        M.add(g, C(a, m, 0.058, n=12), 'hull_dark'); M.add(g, C(m, b, 0.034, n=10), 'metal_light')
        M.add(g, tube_path([(s*0.12*F, -0.74*F, 1.06), (s*0.14*F, -0.34*F, 0.98), (s*0.14*F, 0.20*F, 1.00), (s*0.11*F, 0.38*F, 1.07)], 0.04, n=10), 'cable')
        for y in (0.30, 0.10, -0.10):
            M.add(g, CB(s*0.66, y, 0.70, 0.05, 0.12, 0.05), 'heat')
    # wings (static on the head)
    W = [(0.56, 0.58), (0.94, 0.26), (1.12, -0.30), (1.03, -0.80), (1.20, -1.32), (0.66, -1.00), (0.62, -0.40), (0.64, 0.14)]
    def zt(x): return 0.82-(x/F-0.56)*0.40
    for s in (1, -1):
        Wp = PP([(s*x, y) for x, y in W]); tp = scale_poly(Wp, 0.95)
        M.add(g, loft(ring(Wp, 0.50), np.column_stack([tp, [zt(abs(x)) for x, _ in tp]])), 'hull_light')
        stp = PP([(s*x, y) for x, y in [(0.74, 0.30), (0.93, 0.12), (1.02, -0.32), (0.95, -0.72), (0.84, -0.44), (0.78, 0.04)]])
        s2 = scale_poly(stp, 0.9)
        M.add(g, loft(np.column_stack([stp, [zt(abs(x))+0.003 for x, _ in stp]]), np.column_stack([s2, [zt(abs(x))+0.035 for x, _ in s2]])), 'red_armor')
        for (x, y) in ((1.04, 0.0), (1.07, -0.30), (1.02, -0.62)):
            M.add(g, cbox(s*x*F, y*F, zt(x*F)+0.02, 0.06*F, 0.10*F, 0.04), 'rglow')
        for (x, y) in ((0.72, 0.30), (0.70, -0.20), (0.74, -0.70)):
            M.add(g, cyl((s*x*F, y*F, zt(x*F)-0.01), (s*x*F, y*F, zt(x*F)+0.03), 0.03, n=8), 'metal_light')
        M.add(g, cyl((s*0.92*F, -1.0*F, zt(0.92*F)-0.02), (s*1.10*F, -1.26*F, zt(1.10*F)-0.04), 0.035, 0.015, n=8), 'metal')
    # ---- Scathis-style rotating drum with 6 barrels
    g = 'barrel_local'
    M.add(g, box(-0.32, 0.32, -0.70, 0.20, -0.24, 0.20), 'hull_mid')
    M.add(g, box(-0.22, 0.22, -0.62, 0.10, 0.20, 0.25), 'red_armor')
    M.add(g, box(-0.12, 0.12, -0.56, 0.04, 0.25, 0.27), 'hull_dark')
    for y in (-0.48, -0.30, -0.12):
        M.add(g, box(-0.08, 0.08, y, y+0.04, 0.27, 0.285), 'rglow')
    M.add(g, cyl((0, -0.70, 0), (0, -0.84, 0), 0.20, n=20), 'metal')
    M.add(g, cyl((0, -0.84, 0), (0, -0.88, 0), 0.12, n=16), 'rglow')
    coil_jacket(M, g, 0.20, 5, 0.17, 0.36)
    for y0, y1 in ((1.05, 1.17), (1.78, 1.86), (2.40, 2.48)):
        M.add(g, cyl((0, y0, 0), (0, y1, 0), 0.35, n=6, phase=math.pi/6), 'hull_dark')
        M.add(g, cyl((0, y0+0.035, 0), (0, y1-0.035, 0), 0.362, n=6, phase=math.pi/6), 'red_armor')
    M.add(g, cyl((0, 1.10, 0), (0, 2.62, 0), 0.07, n=12), 'coil')
    for k in range(6):
        a = k*math.pi/3+math.pi/6; x = 0.23*math.cos(a); zz = 0.23*math.sin(a)
        M.add(g, cyl((x, 1.10, zz), (x, 2.52, zz), 0.078, n=14), 'metal')
        for y in (1.40, 2.14):
            M.add(g, cyl((x, y-0.02, zz), (x, y+0.02, zz), 0.09, n=14), 'hull_mid')
        M.add(g, cyl((x, 2.52, zz), (x, 2.68, zz), 0.092, n=14), 'hull_dark')
        M.add(g, cyl((x, 2.68, zz), (x, 2.695, zz), 0.05, n=12), 'rglow')
    for s in (-1, 1):
        hydraulic(M, g, s*0.46, 0.0, -0.50, 1.0, 1.60, r=0.075)
        x0, x1 = sorted((s*0.34, s*0.40)); M.add(g, box(x0, x1, 0.20, 1.04, 0.10, 0.18), 'metal_light')
        x0, x1 = sorted((s*0.355, s*0.385)); M.add(g, box(x0, x1, 0.26, 0.98, 0.18, 0.195), 'coil')
        cable(M, g, [(s*0.20, -0.60, 0.25), (s*0.30, -0.20, 0.30), (s*0.30, 0.15, 0.30)], 0.03)
    pv = (0, 0.72, 1.02); elevate(M, 12, pv)
    SPEC['mantis'] = muzzle_world(12, pv, 2.695)
    return M

heat_howl5 = heat_grad(0.72, 1.10, always=())
heat_redoubt5 = heat_grad(2.05, 2.72, always=())
heat_mantis5 = heat_grad(2.65, 3.36, always=('coil', 'rglow'))
