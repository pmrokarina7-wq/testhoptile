"""Vanguard Arsenal 2.0 - stage 1 models (UEF style: blue-grey armour, yellow trim, blue lights).
Units: 1.0 = one Mindustry tile. Turret heads face +Y."""
import numpy as np, math
from geom import *
from mats import Model

N = 18

def bolts(M, g, pts, z, r=0.028, h=0.018, m='metal_light'):
    for (x, y) in pts:
        M.add(g, cyl((x, y, z), (x, y, z+h), r, n=8), m)

def light(M, g, x, y, z, sx=0.07, sy=0.07, h=0.02):
    M.add(g, cbox(x, y, z+h/2, sx+0.03, sy+0.03, h*0.8), 'hull_dark')
    M.add(g, cbox(x, y, z+h/2+0.008, sx, sy, h), 'glow')

def vent(M, g, cx, cy, z, w, d, slats=5, along='x'):
    if along == 'x':
        M.add(g, cbox(cx, cy, z+0.006, w, d, 0.012), 'vent')
        for i in range(slats):
            x = cx - w/2 + (i+0.5)*w/slats
            M.add(g, cbox(x, cy, z+0.012, w/slats*0.45, d*0.9, 0.016), 'metal')
    else:
        M.add(g, cbox(cx, cy, z+0.006, w, d, 0.012), 'vent')
        for i in range(slats):
            y = cy - d/2 + (i+0.5)*d/slats
            M.add(g, cbox(cx, y, z+0.012, w*0.9, d/slats*0.45, 0.016), 'metal')

def chevrons(M, g, cx, cy, z, w, d, n=3, ang=0):
    """yellow/dark hazard stripes plate"""
    T = []
    M.add(g, tf(cbox(0, 0, z+0.006, w, d, 0.012), rz(ang), (cx, cy, 0)), 'hull_dark')
    for i in range(n):
        x = -w/2 + (i+0.5)*w/n
        p = np.array([(x-0.22*w/n, -d/2*0.85), (x+0.12*w/n, -d/2*0.85), (x+0.22*w/n, d/2*0.85), (x-0.12*w/n, d/2*0.85)])
        M.add(g, tf(prism(ccw(p), z+0.012, z+0.02), rz(ang), (cx, cy, 0)), 'yellow')

def uef_base(M, g, half, top=0.17, corner=True, vents=True, lights=True):
    """armoured UEF foundation pad for an NxN block (half = N/2)."""
    h = half
    M.add(g, prism(cham_rect(h*0.985, h*0.985, h*0.28), 0, 0.09, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(h*0.87, h*0.87, h*0.27), 0.09, top, 0.965), 'hull_mid')
    # perimeter seam
    M.add(g, prism(cham_rect(h*0.80, h*0.80, h*0.25), top, top+0.006), 'hull_dark')
    M.add(g, prism(cham_rect(h*0.78, h*0.78, h*0.245), top+0.006, top+0.012), 'hull_mid')
    if corner:
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = np.array([sx, sy])*h*0.73
                p = rect(0, 0, h*0.13, h*0.07)
                T = prism(p, 0.09, top+0.05, 0.85)
                M.add(g, tf(T, rz(45*sx*sy), (c[0], c[1], 0)), 'hull_light')
                T = prism(rect(0, 0, h*0.10, h*0.025), top+0.05, top+0.06)
                M.add(g, tf(T, rz(45*sx*sy), (c[0], c[1], 0)), 'yellow')
    if vents:
        for k in range(4):
            R = rz(90*k)
            T = []
            sub = Model()
            vent(sub, 'v', 0, -h*0.83, 0.09, h*0.55, h*0.09, slats=max(4, int(6*h)))
            for TT, m in sub.parts['v']:
                M.add(g, tf(TT, R), m)
    if lights:
        for sx in (-1, 1):
            for sy in (-1, 1):
                light(M, g, sx*h*0.55, sy*h*0.84, 0.09, 0.05*h, 0.03*h, 0.015)
    pts = []
    for k in range(8):
        a = math.radians(22.5+45*k)
        pts.append((math.cos(a)*h*0.80, math.sin(a)*h*0.80))
    bolts(M, g, pts, top, r=0.025*h+0.01)

# ---------------------------------------------------------------- HOWL (T1 UEF mortar, 2x2)
ELEV_HOWL = 34

def howl():
    M = Model(); g = 'base'
    uef_base(M, g, 1.0)
    M.add(g, cyl((0, 0, 0.17), (0, 0, 0.205), 0.62, n=28), 'metal')
    M.add(g, cyl((0, 0, 0.205), (0, 0, 0.212), 0.55, n=28), 'hull_dark')
    for k in range(12):
        a = 2*math.pi*k/12
        M.add(g, cyl((math.cos(a)*0.585, math.sin(a)*0.585, 0.205), (math.cos(a)*0.585, math.sin(a)*0.585, 0.215), 0.018, n=6), 'metal_light')
    # cable runs to turntable
    M.add(g, tube_path([(0.80, -0.30, 0.19), (0.66, -0.30, 0.20), (0.56, -0.18, 0.20)], 0.022, n=8), 'cable')
    M.add(g, tube_path([(-0.80, 0.30, 0.19), (-0.66, 0.30, 0.20), (-0.56, 0.18, 0.20)], 0.022, n=8), 'cable')

    g = 'body'
    z0 = 0.205
    hull = mirror_half([(0.0, 0.60), (0.26, 0.57), (0.44, 0.40), (0.49, -0.18), (0.42, -0.44), (0.20, -0.52), (0.0, -0.52)])
    M.add(g, prism(hull, z0, 0.43, 0.9), 'hull_mid')
    top = scale_poly(hull, 0.9)
    M.add(g, prism(scale_poly(top, 0.96), 0.43, 0.455, 0.94), 'hull_light')
    # side armour skirts with hazard stripes
    for s in (-1, 1):
        sk = ccw([(s*0.47, -0.36), (s*0.60, -0.30), (s*0.60, 0.26), (s*0.47, 0.34)])
        M.add(g, prism(sk, z0, 0.37, top_poly=ccw([(s*0.47, -0.33), (s*0.55, -0.28), (s*0.55, 0.24), (s*0.47, 0.31)])), 'hull_light')
        for i in range(3):
            y = -0.22 + i*0.2
            st = ccw([(s*0.49, y), (s*0.545, y+0.04), (s*0.545, y+0.10), (s*0.49, y+0.06)])
            M.add(g, prism(st, 0.37, 0.378), 'yellow')
        bolts(M, g, [(s*0.515, -0.30), (s*0.515, 0.28)], 0.37, r=0.018)
    # rear magazine with shell rack
    M.add(g, box(-0.34, 0.34, -0.74, -0.46, z0, 0.36), 'hull_dark')
    M.add(g, box(-0.35, 0.35, -0.70, -0.66, 0.30, 0.365), 'yellow')
    M.add(g, box(-0.30, 0.30, -0.64, -0.49, 0.36, 0.372), 'vent')
    for i, x in enumerate((-0.2, 0.0, 0.2)):
        M.add(g, cyl((x, -0.62, 0.40), (x, -0.52, 0.40), 0.045, n=10), 'copper')
        M.add(g, cyl((x, -0.52, 0.40), (x, -0.48, 0.40), 0.045, 0.018, n=10), 'metal_light')
    # trunnion cheeks + axle
    for s in (-1, 1):
        ch = ccw([(s*0.17, -0.12), (s*0.29, -0.12), (s*0.29, 0.20), (s*0.17, 0.28)])
        M.add(g, prism(ch, 0.45, 0.64, 0.92), 'hull_dark')
        M.add(g, cyl((s*0.29, 0.06, 0.58), (s*0.33, 0.06, 0.58), 0.075, n=14), 'metal_light')
        M.add(g, cyl((s*0.33, 0.06, 0.58), (s*0.345, 0.06, 0.58), 0.04, n=10), 'yellow')
    # commander hatch, sensor, antenna, lights
    M.add(g, cyl((-0.27, -0.25, 0.455), (-0.27, -0.25, 0.48), 0.09, n=14), 'hull_light')
    M.add(g, box(-0.32, -0.22, -0.26, -0.24, 0.48, 0.495), 'metal_light')
    M.add(g, box(0.20, 0.36, -0.36, -0.20, 0.455, 0.53), 'hull_dark')
    M.add(g, box(0.22, 0.34, -0.205, -0.19, 0.47, 0.52), 'glass')
    light(M, g, 0.28, -0.29, 0.53, 0.05, 0.04, 0.012)
    M.add(g, cyl((0.38, -0.40, 0.455), (0.38, -0.40, 0.80), 0.012, n=6), 'metal_light')
    M.add(g, cyl((0.38, -0.40, 0.80), (0.38, -0.40, 0.83), 0.022, n=6), 'glow')
    light(M, g, -0.40, 0.30, 0.43, 0.04, 0.04, 0.012)
    light(M, g, 0.40, 0.30, 0.43, 0.04, 0.04, 0.012)
    bolts(M, g, [(-0.12, -0.40), (0.12, -0.40), (-0.30, 0.42), (0.30, 0.42)], 0.455, r=0.016)

    g = 'barrel'
    B = []
    def add(T, m): B.append((T, m))
    L = 1.10
    add(cyl((0, -0.22, 0), (0, L, 0), 0.155, n=N), 'metal')
    add(box(-0.19, 0.19, -0.30, 0.20, -0.17, 0.17), 'hull_mid')
    add(box(-0.17, 0.17, -0.34, -0.30, -0.14, 0.14), 'hull_dark')
    add(box(-0.12, 0.12, -0.30, 0.18, 0.17, 0.19), 'hull_light')
    add(box(-0.13, 0.13, -0.08, 0.02, 0.19, 0.198), 'yellow')
    for y in (0.36, 0.62, 0.86):
        add(cyl((0, y, 0), (0, y+0.045, 0), 0.175, n=N), 'metal_light')
    add(cyl((0, 0.47, 0), (0, 0.53, 0), 0.170, n=N), 'yellow')
    for s in (-1, 1):
        add(cyl((s*0.10, -0.05, -0.15), (s*0.10, 0.62, -0.15), 0.035, n=8), 'metal_light')
        add(cyl((s*0.10, 0.62, -0.15), (s*0.10, 0.66, -0.15), 0.045, n=8), 'hull_dark')
    add(box(-0.205, 0.205, 0.98, 1.16, -0.115, 0.115), 'hull_dark')
    for s in (-1, 1):
        for y in (1.02, 1.09):
            add(box(s*0.205, s*0.215, y, y+0.045, -0.07, 0.07), 'vent')
    add(cyl((0, 1.159, 0), (0, 1.17, 0), 0.105, n=N), 'bore')
    R = rx(ELEV_HOWL); t = (0, 0.06, 0.58)
    for T, m in B:
        M.add(g, tf(T, R, t), m)
    return M

def heat_howl_barrel(mp, X, Y, g):
    from mats import MID
    hot = np.isin(mp, [MID['metal'], MID['hull_dark'], MID['bore'], MID['metal_light'], MID['vent']])
    return np.where(hot, np.clip((Y-0.45)/0.5, 0, 1)*0.9, 0)
