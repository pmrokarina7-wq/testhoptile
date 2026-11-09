"""Version 2.5 stage 1 - T4 hero models: Monolith, Bastion, Suppressor, Citadel, T4 industry, items."""
import math, numpy as np
from geom import *
from mats import Model
from models import bolts, light, chevrons
from hero import *

SPEC = {}
def B(x0, x1, y0, y1, z0, z1): return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1)
def hexp(r, rot=30, sx=1.0, sy=1.0, cx=0.0, cy=0.0):
    return P([(cx+sx*r*math.cos(math.radians(rot+60*i)), cy+sy*r*math.sin(math.radians(rot+60*i))) for i in range(6)])
def octp(r, cx=0.0, cy=0.0):
    return P([(cx+r*math.cos(math.radians(22.5+45*i)), cy+r*math.sin(math.radians(22.5+45*i))) for i in range(8)])
def torus(M, g, R, r, z, m, n=28, k=10, a0=0.0):
    for i in range(n):
        a, b = math.radians(a0+360*i/n), math.radians(a0+360*(i+1)/n)
        M.add(g, cyl((R*math.cos(a), R*math.sin(a), z), (R*math.cos(b), R*math.sin(b), z), r, n=k), m)
def pad(M, g, h, hi=0.30, mat1='hull_dark', mat2='hull_mid'):
    M.add(g, prism(cham_rect(h*0.985, h*0.985, h*0.22), 0.0, 0.12, 0.985), mat1)
    M.add(g, prism(cham_rect(h*0.88, h*0.88, h*0.24), 0.12, hi, 0.95), mat2)

# ================================================================== Monolith - T4 UEF strategic artillery (5x5)
def monolith6():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 2.5, top=0.24)
    g = 'body'
    hull = mirror_half([(0, 1.50), (0.78, 1.42), (1.40, 0.96), (1.66, 0.12), (1.62, -0.92), (1.30, -1.70), (0.62, -2.02), (0, -2.08)])
    M.add(g, prism(hull, z, z+0.40, 0.94), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.88, (0, 0)), z+0.40, z+0.50, 0.96), 'hull_mid')
    top = z+0.50
    for s in (-1, 1):
        sp = [(s*0.92, 0.88), (s*1.40, 0.60), (s*1.54, -0.58), (s*1.24, -1.44), (s*0.92, -1.26)]
        zf = (lambda x, y: top+0.16-(abs(x)-0.92)*0.30)
        slope_plate(M, g, P(sp), zf, 'hull_light', thick=0.16, inlay='yellow', isc=0.62, ih=0.02)
        bolts_on(M, g, [(s*1.00, 0.74), (s*1.40, 0.36), (s*1.42, -0.66), (s*1.04, -1.20)], zf, r=0.026)
        light(M, g, s*1.10, 0.62, zf(1.10, 0)-0.01, 0.06, 0.05)
        for i in range(8):                                    # heat-exchanger fin bank (fires only with heat)
            y = -1.10+i*0.17
            M.add(g, B(s*1.60, s*1.76, y-0.04, y+0.04, z+0.06, z+0.44), 'metal')
            if i < 7: M.add(g, B(s*1.62, s*1.70, y+0.04, y+0.13, z+0.06, z+0.30), 'heat')
        M.add(g, B(s*1.58, s*1.80, -1.20, 0.26, z+0.44, z+0.48), 'hull_light')
        M.add(g, cyl((s*1.62, -1.45, z+0.20), (s*1.86, -1.45, z+0.20), 0.11, n=14), 'hull_mid')
        M.add(g, cyl((s*1.86, -1.45, z+0.20), (s*1.90, -1.45, z+0.20), 0.08, n=12), 'heat')
        M.add(g, B(s*0.62, s*0.98, 0.45, 1.05, top-0.02, top+0.26), 'hull_light')      # trunnion cheeks
        M.add(g, cyl((s*0.66, 0.75, top+0.40), (s*0.86, 0.75, top+0.40), 0.20, n=22), 'metal')
        M.add(g, cyl((s*0.86, 0.75, top+0.40), (s*0.94, 0.75, top+0.40), 0.15, n=20), 'hull_dark')
        M.add(g, cyl((s*0.94, 0.75, top+0.40), (s*0.96, 0.75, top+0.40), 0.07, n=12), 'glow')
        bolts(M, g, [(s*0.70, 0.52), (s*0.90, 0.52), (s*0.70, 0.98), (s*0.90, 0.98)], top+0.26, r=0.022)
        ex, ey = s*0.98, -1.62
        M.add(g, cyl((ex, ey, z+0.30), (ex, ey, top+0.30), 0.10, n=14), 'metal')
        M.add(g, cyl((ex, ey, top+0.30), (ex, ey, top+0.34), 0.12, n=14), 'hull_dark')
        M.add(g, cyl((ex, ey, top+0.34), (ex, ey, top+0.345), 0.07, n=12), 'heat')
        antenna(M, g, (s*0.70, -1.80, top), (s*0.86, -2.30, top+0.9))
    # rear ammo hoist with heavy shells + loader arm
    M.add(g, B(-0.70, 0.70, -1.86, -0.92, top-0.02, top+0.04), 'vent')
    for i in range(5):
        shell(M, g, -0.52+i*0.26, -1.40, top+0.06, L=0.70, r=0.095)
    for y in (-1.86, -0.92):
        M.add(g, B(-0.76, 0.76, y-0.04, y+0.04, top-0.02, top+0.16), 'hull_light')
    for x in (-0.76, 0.76):
        M.add(g, B(x-0.04, x+0.04, -1.90, -0.88, top-0.02, top+0.16), 'hull_light')
    bolts(M, g, [(-0.76, -1.86), (0.76, -1.86), (-0.76, -0.92), (0.76, -0.92)], top+0.16, r=0.024)
    M.add(g, cyl((0.30, -0.90, top), (0.30, -0.90, top+0.45), 0.08, n=12), 'metal')
    cable(M, g, [(0.30, -0.90, top+0.45), (0.10, -0.40, top+0.62), (0.0, 0.05, top+0.55)], 0.045, m='metal_light', ends='yellow')
    chevrons(M, g, 0, -1.98, top, 0.9, 0.09, n=8)
    # commander cupola (left) + fire-control radar (right)
    cx, cy = -0.62, -0.42
    M.add(g, cyl((cx, cy, top-0.01), (cx, cy, top+0.16), 0.24, 0.22, n=20), 'hull_light')
    M.add(g, cyl((cx, cy, top+0.16), (cx, cy, top+0.20), 0.17, n=20), 'hull_mid')
    for i in range(8):
        M.add(g, tf(cbox(0.20, 0, top+0.18, 0.05, 0.075, 0.035), rz(45*i+22.5), (cx, cy, 0)), 'glass')
    M.add(g, cbox(cx, cy+0.12, top+0.215, 0.09, 0.03, 0.02), 'glow')
    dx, dy = 0.62, -0.42
    M.add(g, cyl((dx, dy, top-0.01), (dx, dy, top+0.30), 0.08, n=12), 'metal')
    M.add(g, tf(box(-0.30, 0.30, -0.05, 0.05, -0.12, 0.12), rx(-20), (dx, dy, top+0.36)), 'hull_light')
    M.add(g, tf(box(-0.26, 0.26, 0.05, 0.07, -0.09, 0.09), rx(-20), (dx, dy, top+0.36)), 'glow')
    seam(M, g, (-0.50, -0.70), (0.50, -0.70), top, w=0.03, h=0.014)
    seam(M, g, (-0.40, 0.25), (0.40, 0.25), top, w=0.03, h=0.014)
    grille(M, g, 0, -0.20, top, 0.70, 0.22, n=8)
    # ---- one huge long-range gun
    g = 'barrel_local'
    M.add(g, box(-0.60, 0.60, -1.20, 0.40, -0.22, 0.20), 'hull_mid')
    M.add(g, box(-0.52, 0.52, -1.12, 0.32, 0.20, 0.25), 'hull_light')
    for y0 in (-0.90, -0.40, 0.08):
        M.add(g, box(-0.48, 0.48, y0, y0+0.07, 0.25, 0.262), 'yellow')
    bolts(M, g, [(-0.46, -1.06), (0.46, -1.06), (-0.46, 0.26), (0.46, 0.26), (0, -1.06)], 0.25, r=0.024)
    M.add(g, box(-0.42, 0.42, -1.50, -1.20, -0.18, 0.18), 'metal')
    M.add(g, cyl((0, -1.50, 0), (0, -1.56, 0), 0.12, n=14), 'glow')
    for s in (-1, 1):
        M.add(g, cyl((s*0.30, 0.0, 0.18), (s*0.30, 1.55, 0.18), 0.075, n=12), 'metal_light')
        for y in (0.30, 0.80, 1.30):
            M.add(g, cyl((s*0.30, y, 0.18), (s*0.30, y+0.06, 0.18), 0.095, n=12), 'hull_dark')
        M.add(g, cyl((s*0.30, 1.55, 0.18), (s*0.30, 1.62, 0.18), 0.10, n=12), 'hull_mid')
        hydraulic(M, g, s*0.68, 0.0, -0.90, 0.40, 1.10, r=0.08)
        cable(M, g, [(s*0.22, -0.60, 0.25), (s*0.26, 0.20, 0.24), (s*0.24, 1.00, 0.22)], 0.03)
    M.add(g, cyl((0, 0.40, 0), (0, 1.35, 0), 0.25, n=24), 'hull_dark')
    for y in np.arange(0.48, 1.30, 0.11):
        M.add(g, cyl((0, y, 0), (0, y+0.04, 0), 0.29, n=24), 'metal')
    M.add(g, cyl((0, 1.35, 0), (0, 2.55, 0), 0.20, n=24), 'metal')
    M.add(g, cyl((0, 2.55, 0), (0, 3.45, 0), 0.175, n=22), 'metal')
    for y in (1.40, 1.95, 2.55, 3.00):
        M.add(g, cyl((0, y-0.04, 0), (0, y+0.04, 0), 0.23, n=22), 'hull_mid')
    M.add(g, box(-0.05, 0.05, 1.45, 3.35, 0.17, 0.215), 'yellow')
    muzzle_brake(M, g, 3.45, 0.40, 0.23, nb=4, trim='yellow', bore_r=0.10, out=0.09)
    pv = (0, 0.75, top+0.40); elevate(M, 12, pv)
    SPEC['monolith'] = muzzle_world(12, pv, 3.85)
    return M

# ================================================================== Bastion - T4 UEF railgun (4x4)
def bastion6():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 2.0, top=0.22)
    g = 'body'
    hull = mirror_half([(0, 1.12), (0.62, 1.06), (1.10, 0.66), (1.30, 0.0), (1.24, -0.80), (0.92, -1.38), (0.42, -1.60), (0, -1.62)])
    M.add(g, prism(hull, z, z+0.34, 0.93), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.86, (0, 0)), z+0.34, z+0.42, 0.96), 'hull_mid')
    top = z+0.42
    for s in (-1, 1):
        M.add(g, B(s*0.58, s*1.06, -1.20, 0.40, top-0.02, top+0.02), 'hull_dark')
        for x in (0.70, 0.94):                                 # capacitor banks with charge rings
            X = s*x
            M.add(g, cyl((X, -1.10, top+0.11), (X, 0.30, top+0.11), 0.11, n=16), 'metal_light')
            M.add(g, cyl((X, 0.30, top+0.11), (X, 0.36, top+0.11), 0.125, n=16), 'hull_dark')
            M.add(g, cyl((X, -1.16, top+0.11), (X, -1.10, top+0.11), 0.125, n=16), 'hull_dark')
            for y in np.arange(-0.98, 0.25, 0.20):
                M.add(g, cyl((X, y, top+0.11), (X, y+0.03, top+0.11), 0.118, n=16), 'glow')
        for y in (-1.16, -0.40, 0.36):
            M.add(g, B(s*0.56, s*1.08, y-0.03, y+0.03, top-0.02, top+0.24), 'hull_light')
        sp = [(s*1.08, 0.55), (s*1.26, 0.05), (s*1.20, -0.78), (s*1.00, -1.10)]
        zf = (lambda x, y: top+0.10-(abs(x)-1.08)*0.4)
        slope_plate(M, g, P(sp), zf, 'hull_light', thick=0.12, inlay='yellow', isc=0.55, ih=0.016)
        light(M, g, s*0.86, 0.55, top+0.02, 0.05, 0.04)
        cable(M, g, [(s*0.82, 0.36, top+0.20), (s*0.55, 0.50, top+0.30), (s*0.30, 0.40, top+0.36)], 0.035)
    grille(M, g, 0, -1.25, top, 0.80, 0.24, n=8)
    chevrons(M, g, 0, -1.52, top, 0.6, 0.07, n=6)
    M.add(g, B(-0.30, 0.30, -0.90, -0.45, top-0.01, top+0.16), 'hull_light')   # targeting optics
    M.add(g, cyl((0, -0.45, top+0.08), (0, -0.40, top+0.08), 0.07, n=14), 'glass')
    M.add(g, cbox(0, -0.68, top+0.165, 0.18, 0.05, 0.01), 'glow')
    antenna(M, g, (0.40, -1.30, top), (0.52, -1.75, top+0.6))
    antenna(M, g, (-0.40, -1.30, top), (-0.52, -1.75, top+0.6))
    # ---- twin rails
    g = 'barrel_local'
    M.add(g, box(-0.50, 0.50, -0.95, 0.30, -0.20, 0.18), 'hull_mid')
    M.add(g, box(-0.44, 0.44, -0.88, 0.24, 0.18, 0.22), 'hull_light')
    M.add(g, box(-0.40, 0.40, -0.20, -0.12, 0.22, 0.232), 'yellow')
    bolts(M, g, [(-0.40, -0.80), (0.40, -0.80), (-0.40, 0.18), (0.40, 0.18)], 0.22, r=0.022)
    for s in (-1, 1):
        M.add(g, B(s*0.10, s*0.24, 0.30, 3.00, -0.12, 0.12), 'metal')
        M.add(g, B(s*0.085, s*0.10, 0.34, 2.96, -0.08, 0.08), 'copper')
        M.add(g, B(s*0.12, s*0.22, 0.34, 2.96, 0.12, 0.15), 'hull_dark')
        for y in np.arange(0.45, 2.90, 0.12):
            M.add(g, B(s*0.13, s*0.21, y, y+0.05, 0.15, 0.19), 'metal_light')
        cable(M, g, [(s*0.42, -0.70, 0.20), (s*0.40, 0.20, 0.20), (s*0.33, 0.60, 0.20)], 0.035)
        hydraulic(M, g, s*0.50, -0.05, -0.85, 0.10, 0.45, r=0.06)
    M.add(g, box(-0.085, 0.085, 0.34, 2.96, -0.04, -0.01), 'glow')
    for y in np.arange(0.55, 2.80, 0.42):                       # field coils
        M.add(g, box(-0.36, 0.36, y, y+0.12, 0.15, 0.21), 'hull_dark')
        for s in (-1, 1):
            M.add(g, B(s*0.26, s*0.36, y, y+0.12, -0.21, 0.21), 'hull_dark')
            M.add(g, B(s*0.36, s*0.39, y+0.02, y+0.10, -0.15, 0.15), 'coil')
        M.add(g, box(-0.05, 0.05, y+0.03, y+0.09, 0.21, 0.225), 'glow')
    M.add(g, box(-0.34, 0.34, 3.00, 3.20, -0.16, 0.16), 'hull_mid')
    M.add(g, box(-0.30, 0.30, 3.18, 3.20, -0.10, 0.17), 'yellow')
    M.add(g, box(-0.08, 0.08, 3.00, 3.205, -0.06, 0.06), 'glow')
    pv = (0, 0.55, top+0.28); elevate(M, 0, pv)
    SPEC['bastion'] = muzzle_world(0, pv, 3.20)
    return M

# ================================================================== Suppressor - T4 Cybran EMP projector (3x3)
def suppressor6():
    M = Model()
    z = cy_hero_base(M, 'base', 1.0)
    g = 'body'
    M.add(g, prism(hexp(0.98, rot=90, sy=1.05), z, z+0.24, 0.92), 'cy_dark')
    M.add(g, prism(hexp(0.84, rot=90, sy=1.05), z+0.24, z+0.30, 0.95), 'cy_mid')
    top = z+0.30
    zf = (lambda x, y: top+0.10-(math.hypot(x, y)-0.58)*0.30)
    for k in range(6):
        a = 120+60*k
        pts = [(rr*math.cos(math.radians(a+da)), rr*math.sin(math.radians(a+da))) for rr, da in ((0.60, -20), (0.92, -24), (0.92, 24), (0.60, 20))]
        red = k in (0, 1, 4, 5)
        slope_plate(M, g, P(pts), zf, 'red_armor' if red else 'cy_mid', thick=0.10, inlay='rglow' if red else 'cy_dark', isc=0.42, ih=0.012)
    cx, cy = 0.0, -0.12                                          # tesla tower
    M.add(g, cyl((cx, cy, top), (cx, cy, top+0.10), 0.40, 0.36, n=24), 'metal')
    for i in range(5):
        z0 = top+0.10+i*0.085
        M.add(g, cyl((cx, cy, z0), (cx, cy, z0+0.05), 0.31-0.02*i, n=22), 'coil')
        M.add(g, cyl((cx, cy, z0+0.05), (cx, cy, z0+0.085), 0.24-0.02*i, n=20), 'cy_dark')
    zt = top+0.10+5*0.085
    M.add(g, cyl((cx, cy, zt), (cx, cy, zt+0.04), 0.20, n=20), 'red_armor')
    M.add(g, sphereish((cx, cy, zt+0.12), 0.15, n=12), 'rglow')
    for i in range(6):
        a = math.radians(60*i)
        M.add(g, cyl((cx+0.36*math.cos(a), cy+0.36*math.sin(a), top+0.08), (cx+0.22*math.cos(a), cy+0.22*math.sin(a), zt+0.04), 0.022, n=6), 'metal_light')
    for s in (-1, 1):                                             # emitter fork
        M.add(g, B(s*0.14, s*0.30, 0.30, 1.40, top-0.04, top+0.14), 'cy_dark')
        M.add(g, B(s*0.15, s*0.29, 0.34, 1.30, top+0.14, top+0.18), 'red_armor')
        M.add(g, B(s*0.13, s*0.145, 0.40, 1.34, top+0.01, top+0.11), 'rglow')
        for y in (0.55, 0.85, 1.15):
            M.add(g, B(s*0.12, s*0.32, y, y+0.06, top+0.18, top+0.20), 'metal_light')
        M.add(g, B(s*0.16, s*0.30, 1.40, 1.52, top-0.02, top+0.10), 'metal')
    M.add(g, cyl((0, 0.30, top+0.06), (0, 1.05, top+0.06), 0.06, n=12), 'metal')
    M.add(g, cyl((0, 1.05, top+0.06), (0, 1.38, top+0.06), 0.085, n=14), 'coil')
    M.add(g, cyl((0, 1.38, top+0.06), (0, 1.46, top+0.06), 0.10, n=14), 'rglow')
    for a in (215, 270, 325):                                     # capacitor pylons
        r_ = math.radians(a); px, py = 0.66*math.cos(r_), 0.66*math.sin(r_)
        M.add(g, cyl((px, py, top), (px, py, top+0.34), 0.095, n=14), 'cy_mid')
        for j in range(3):
            M.add(g, cyl((px, py, top+0.06+j*0.09), (px, py, top+0.09+j*0.09), 0.11, n=14), 'coil')
        M.add(g, cyl((px, py, top+0.34), (px, py, top+0.38), 0.07, n=12), 'rglow')
        cable(M, g, [(px, py, top+0.30), ((px+cx)/2, (py+cy)/2, top+0.40), (cx+0.25*math.cos(r_), cy+0.25*math.sin(r_), top+0.30)], 0.03)
    bolts(M, g, [(0.80*math.cos(math.radians(a)), 0.84*math.sin(math.radians(a))) for a in range(30, 360, 60)], top, r=0.022)
    antenna(M, g, (0.55, -0.55, top), (0.85, -1.05, top+0.55), tip='rglow')
    return M

# ================================================================== Citadel - T4 UEF shield dome (4x4)
def citadel6():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(1.97, 1.97, 0.55), 0.0, 0.12, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.80, 1.80, 0.58), 0.12, 0.30, 0.95), 'hull_mid')
    M.add(g, prism(cham_rect(1.50, 1.50, 0.46), 0.30, 0.32, 0.97), 'hull_dark')
    for k in range(4):
        S = rz(90*k)
        grille(M, g, 0, -1.62, 0.30, 1.10, 0.16, n=10, R=S)
        bolts_R(M, g, [(-0.80, -1.40), (0.80, -1.40), (-0.40, -1.40), (0.40, -1.40)], 0.32, S)
        M.add(g, tf(cbox(0, -1.86, 0.13, 0.60, 0.05, 0.02), S), 'yellow')
        R = rz(45+90*k)
        buttress(M, g, 45+90*k, 1.20, 1.95, 0.22, 0.42, 0.14, z0=0.10, mat='hull_light', inlay='yellow', tip='glow')
        M.add(g, tf(prism(octp(0.30, cx=1.55), 0.30, 0.42, 0.92), R), 'hull_light')
        M.add(g, tf(prism(octp(0.22, cx=1.55), 0.42, 0.95, 0.70), R), 'hull_light')
        M.add(g, tf(cyl((1.55, 0, 0.60), (1.55, 0, 0.66), 0.20, n=16), R), 'yellow')
        M.add(g, tf(cyl((1.55, 0, 0.95), (1.55, 0, 1.02), 0.12, n=14), R), 'metal')
        M.add(g, tf(sphereish((1.55, 0, 1.08), 0.10, n=10), R), 'glow')
        cable(M, g, [(1.40, 0, 0.55), (1.12, 0, 0.66), (0.86, 0, 0.52)], 0.04, R=R)
        light(M, g, *tuple((R @ np.array([1.10, 0.30, 0]))[:2]), 0.32, 0.05, 0.04)
    M.add(g, cyl((0, 0, 0.32), (0, 0, 0.44), 0.98, n=48), 'metal')
    M.add(g, cyl((0, 0, 0.44), (0, 0, 0.48), 0.98, 0.92, n=48), 'hull_dark')
    for i in range(16):
        a = math.radians(22.5*i); x, y = 0.84*math.cos(a), 0.84*math.sin(a)
        M.add(g, cyl((x, y, 0.48), (x, y, 0.62), 0.07, n=10), 'coil')
        M.add(g, cyl((x, y, 0.62), (x, y, 0.65), 0.05, n=10), 'glow')
    M.add(g, sphereish((0, 0, 0.40), 0.66, n=20), 'glass')
    for i in range(8):
        a = math.radians(45*i+22.5)
        pts = [(0.675*math.cos(t)*math.cos(a), 0.675*math.cos(t)*math.sin(a), 0.40+0.675*math.sin(t)) for t in np.radians([5, 30, 55, 78])]
        M.add(g, tube_path(pts, 0.025, n=6), 'hull_light')
    M.add(g, cyl((0, 0, 0.98), (0, 0, 1.08), 0.20, 0.13, n=16), 'metal_light')
    M.add(g, cyl((0, 0, 1.08), (0, 0, 1.10), 0.10, n=14), 'glow')
    return M

# ================================================================== T4 industry
def cryocondenser():                                   # 2x2, water -> liquid nitrogen
    M = Model()
    M.add('bottom', prism(cham_rect(0.98, 0.98, 0.18), 0, 0.08, 0.98), 'hull_dark')
    M.add('bottom', box(-0.42, 0.42, -0.42, 0.42, 0.08, 0.10), 'vent')
    g = 'main'
    for (x0, x1, y0, y1) in ((-0.96, 0.96, 0.42, 0.96), (-0.96, 0.96, -0.96, -0.42), (-0.96, -0.42, -0.42, 0.42), (0.42, 0.96, -0.42, 0.42)):
        M.add(g, box(x0, x1, y0, y1, 0.08, 0.28), 'hull_mid')
    for (x0, x1, y0, y1) in ((-0.46, 0.46, 0.40, 0.46), (-0.46, 0.46, -0.46, -0.40), (-0.46, -0.40, -0.40, 0.40), (0.40, 0.46, -0.40, 0.40)):
        M.add(g, box(x0, x1, y0, y1, 0.28, 0.31), 'metal')
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx*0.68, sy*0.68
            M.add(g, cyl((cx, cy, 0.28), (cx, cy, 0.40), 0.24, 0.22, n=18), 'metal_light')
            M.add(g, cyl((cx, cy, 0.40), (cx, cy, 0.42), 0.18, n=18), 'vent')
            for i in range(4):
                M.add(g, tf(cbox(0, 0, 0.425, 0.30, 0.035, 0.01), rz(45*i+15), (cx, cy, 0)), 'metal')
            M.add(g, cyl((cx, cy, 0.42), (cx, cy, 0.45), 0.045, n=8), 'glow')
        M.add(g, tube_path([(sx*0.90, -0.42, 0.33), (sx*0.90, 0.42, 0.33)], 0.065, n=10), 'glass')
        for y in (-0.30, 0.0, 0.30):
            M.add(g, cyl((sx*0.90, y-0.02, 0.33), (sx*0.90, y+0.02, 0.33), 0.08, n=10), 'hull_light')
        M.add(g, cbox(0, sx*0.69, 0.29, 0.20, 0.03, 0.01), 'glow')
    bolts(M, g, [(-0.52, 0.0), (0.52, 0.0), (0.0, 0.52), (0.0, -0.52)], 0.28, r=0.02)
    return M

def iridium_smelter():                                 # 3x3 HeatCrafter: iridite -> iridium alloy
    M = Model(); g = 'main'
    pad(M, g, 1.5)
    for k in range(4):                                       # heat input ports on every side
        S = rz(90*k)
        M.add(g, tf(box(1.16, 1.48, -0.36, 0.36, 0.12, 0.36), S), 'hull_light')
        M.add(g, tf(box(1.40, 1.49, -0.26, 0.26, 0.16, 0.32), S), 'heat')
        M.add(g, tf(box(1.18, 1.40, -0.38, -0.33, 0.36, 0.40), S), 'yellow')
        M.add(g, tf(box(1.18, 1.40, 0.33, 0.38, 0.36, 0.40), S), 'yellow')
        bolts_R(M, g, [(1.24, -0.28), (1.24, 0.28)], 0.36, S)
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.62), 0.74, 0.68, n=36), 'hull_light')
    for z0 in (0.38, 0.50):
        M.add(g, cyl((0, 0, z0), (0, 0, z0+0.04), 0.745, n=36), 'hull_dark')
    M.add(g, cyl((0, 0, 0.62), (0, 0, 0.66), 0.68, 0.60, n=36), 'metal')
    M.add(g, cyl((0, 0, 0.60), (0, 0, 0.665), 0.50, n=32), 'flame')
    for i in range(3):                                       # graphite electrodes on clamp arms
        a = math.radians(90+120*i)
        ex, ey = 0.28*math.cos(a), 0.28*math.sin(a)
        mx, my = 0.98*math.cos(a+0.5), 0.98*math.sin(a+0.5)
        M.add(g, cyl((ex, ey, 0.55), (ex, ey, 1.00), 0.08, n=12), 'hull_dark')
        M.add(g, cyl((ex, ey, 0.82), (ex, ey, 0.90), 0.12, n=12), 'copper')
        M.add(g, cyl((mx, my, 0.30), (mx, my, 1.00), 0.07, n=12), 'metal')
        M.add(g, cyl((ex, ey, 0.86), (mx, my, 0.86), 0.05, n=10), 'metal_light')
        cable(M, g, [(mx, my, 0.95), ((mx+ex)/2, (my+ey)/2, 1.02), (ex, ey, 0.98)], 0.03, m='cable', ends='copper')
    for sx in (-1, 1):
        for sy in (-1, 1):
            light(M, g, sx*1.02, sy*1.02, 0.30, 0.05, 0.05)
    return M

def sc_chamber():                                      # 3x3 superconductor chamber
    M = Model(); g = 'main'
    pad(M, g, 1.5)
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.80), 0.78, n=40), 'metal_light')
    for i in range(5):
        z0 = 0.34+i*0.09
        M.add(g, cyl((0, 0, z0), (0, 0, z0+0.045), 0.81, n=40), 'coil')
    M.add(g, cyl((0, 0, 0.80), (0, 0, 0.86), 0.76, 0.68, n=40), 'hull_mid')
    M.add(g, cyl((0, 0, 0.86), (0, 0, 0.88), 0.50, n=32), 'glass')
    M.add(g, cyl((0, 0, 0.88), (0, 0, 0.89), 0.22, n=24), 'glow')
    torus(M, g, 0.60, 0.025, 0.87, 'glow', n=32, k=6)
    bolts(M, g, [(0.70*math.cos(math.radians(a)), 0.70*math.sin(math.radians(a))) for a in range(0, 360, 30)], 0.86, r=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx*1.04, sy*1.04
            M.add(g, box(cx-0.20, cx+0.20, cy-0.20, cy+0.20, 0.12, 0.56), 'magnet')
            M.add(g, box(cx-0.16, cx+0.16, cy-0.16, cy+0.16, 0.56, 0.60), 'hull_dark')
            M.add(g, cyl((cx, cy, 0.60), (cx, cy, 0.63), 0.06, n=10), 'glow')
            cable(M, g, [(cx*0.86, cy*0.86, 0.50), (cx*0.78, cy*0.78, 0.66), (cx*0.62, cy*0.62, 0.60)], 0.04)
    for k in range(4):
        S = rz(90*k)
        M.add(g, tf(tube_path([(1.40, -0.40, 0.36), (1.40, 0.40, 0.36)], 0.07, n=10), S), 'glass')
        M.add(g, tf(cbox(1.40, 0, 0.36, 0.12, 0.10, 0.10), S), 'hull_light')
    return M

def plasma_heater():                                   # 3x3 HeatProducer, nozzle faces +x
    M = Model(); g = 'main'
    pad(M, g, 1.5)
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.34), 0.86, n=36), 'metal')
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.50), 0.38, n=28), 'pglow')
    torus(M, g, 0.58, 0.17, 0.48, 'coil', n=24, k=12)
    torus(M, g, 0.58, 0.06, 0.66, 'pglow', n=24, k=8)
    for i in range(8):
        M.add(g, tf(box(0.32, 0.84, -0.06, 0.06, 0.30, 0.70), rz(45*i+22.5)), 'hull_dark')
        M.add(g, tf(box(0.36, 0.80, -0.065, 0.065, 0.68, 0.72), rz(45*i+22.5)), 'hull_light')
    for y in (-0.62, 0.62):                                  # tritium fuel tanks at the rear
        M.add(g, cyl((-1.30, y, 0.42), (-0.86, y, 0.42), 0.21, n=16), 'glass')
        M.add(g, cyl((-1.36, y, 0.42), (-1.30, y, 0.42), 0.23, n=16), 'hull_dark')
        M.add(g, cyl((-0.86, y, 0.42), (-0.80, y, 0.42), 0.23, n=16), 'hull_dark')
        M.add(g, cyl((-1.10, y, 0.42), (-1.06, y, 0.42), 0.225, n=16), 'glow')
        cable(M, g, [(-0.80, y, 0.46), (-0.62, y*0.8, 0.58), (-0.48, y*0.6, 0.52)], 0.04)
    for sy in (-1, 1):
        light(M, g, 0.80, sy*1.10, 0.30, 0.05, 0.05)
        bolts(M, g, [(-0.30, sy*1.15), (0.30, sy*1.15), (0.90, sy*1.15)], 0.30, r=0.02)
    g = 'top'
    M.add(g, prism(P([(0.70, -0.44), (1.48, -0.30), (1.48, 0.30), (0.70, 0.44)]), 0.30, 0.62, 0.92), 'hull_light')
    for y in np.linspace(-0.24, 0.24, 5):
        M.add(g, box(0.85, 1.40, y-0.02, y+0.02, 0.60, 0.68), 'metal')
    M.add(g, box(0.74, 0.80, -0.40, 0.40, 0.60, 0.64), 'yellow')
    M.add(g, box(1.40, 1.49, -0.22, 0.22, 0.36, 0.56), 'heat')
    return M

def fusion_reactor():                                  # 4x4 ConsumeGenerator - tokamak
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(1.97, 1.97, 0.50), 0, 0.12, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.80, 1.80, 0.55), 0.12, 0.28, 0.95), 'hull_mid')
    for k in range(4):
        S = rz(90*k)
        grille(M, g, 0, -1.62, 0.28, 0.90, 0.16, n=9, R=S)
        M.add(g, tf(box(-0.18, 0.18, 1.60, 1.97, 0.12, 0.36), S), 'copper')
        M.add(g, tf(box(-0.12, 0.12, 1.66, 1.97, 0.36, 0.40), S), 'glow')
        a = math.radians(45+90*k); cx, cy = 1.42*math.cos(a), 1.42*math.sin(a)
        M.add(g, cyl((cx, cy, 0.28), (cx, cy, 0.70), 0.24, n=18), 'glass')
        M.add(g, cyl((cx, cy, 0.40), (cx, cy, 0.44), 0.255, n=18), 'yellow')
        M.add(g, cyl((cx, cy, 0.70), (cx, cy, 0.76), 0.25, 0.20, n=18), 'hull_light')
        M.add(g, cyl((cx, cy, 0.76), (cx, cy, 0.78), 0.06, n=10), 'glow')
        cable(M, g, [(cx*0.85, cy*0.85, 0.60), (cx*0.70, cy*0.70, 0.75), (cx*0.55, cy*0.55, 0.62)], 0.045, m='glass', ends='hull_light')
    M.add(g, cyl((0, 0, 0.28), (0, 0, 0.40), 1.30, n=48), 'hull_dark')
    torus(M, g, 0.90, 0.30, 0.70, 'metal_light', n=36, k=14)
    torus(M, g, 0.90, 0.07, 1.00, 'glow', n=36, k=8)
    for i in range(12):
        R = rz(30*i)
        M.add(g, tf(box(0.52, 1.28, -0.07, 0.07, 0.36, 1.04), R), 'hull_dark')
        M.add(g, tf(box(0.56, 1.24, -0.075, 0.075, 0.98, 1.06), R), 'coil')
    M.add(g, cyl((0, 0, 0.40), (0, 0, 1.05), 0.40, n=28), 'hull_mid')
    for i in range(4):
        M.add(g, cyl((0, 0, 0.50+i*0.13), (0, 0, 0.56+i*0.13), 0.42, n=28), 'coil')
    M.add(g, cyl((0, 0, 1.05), (0, 0, 1.10), 0.34, n=28), 'hull_light')
    M.add(g, cyl((0, 0, 1.10), (0, 0, 1.12), 0.18, n=20), 'glow')
    bolts(M, g, [(0.27*math.cos(math.radians(a)), 0.27*math.sin(math.radians(a))) for a in range(0, 360, 45)], 1.10, r=0.02)
    return M

# ================================================================== items / liquid (32 px)
def _crystals(mat, core, spec, base=None):
    M = Model()
    if base: M.add('main', prism(P([(-0.34, -0.20), (0.10, -0.36), (0.38, -0.08), (0.22, 0.30), (-0.24, 0.30)]), 0, 0.10, 0.85), base)
    for (x, y, s, a) in spec:
        T = prism(hexp(s*0.45, rot=0), 0, s*1.7, 0.25)
        M.add('main', tf(T, rz(a) @ rx(55), (x, y, 0.08)), mat)
        if core: M.add('main', tf(prism(hexp(s*0.18, rot=0), s*0.2, s*1.45, 0.3), rz(a) @ rx(55), (x, y, 0.09)), core)
    return M
def item_iridite():
    return _crystals('magnet', None, ((-0.12, -0.06, 0.24, 20), (0.14, -0.02, 0.19, 75), (0.0, 0.15, 0.21, 140), (-0.20, 0.16, 0.14, 205), (0.20, 0.20, 0.13, 265)), base='tung')
def item_tritium():
    return _crystals('glass', 'glow', ((-0.10, -0.06, 0.27, 30), (0.12, -0.02, 0.23, 95), (-0.02, 0.13, 0.22, 160), (0.17, 0.17, 0.15, 250), (-0.19, 0.12, 0.14, 210)), base='alu')
def item_iridium():
    M = Model()
    for (dx, dy, z0) in ((-0.06, -0.10, 0.0), (0.07, 0.10, 0.15)):
        R = rz(-25)
        M.add('main', tf(prism(rect(0, 0, 0.36, 0.17), z0, z0+0.15, top_poly=rect(0, 0, 0.28, 0.11)), R, (dx, dy, 0)), 'metal_light')
        M.add('main', tf(prism(rect(0, 0, 0.20, 0.025), z0+0.15, z0+0.158), R, (dx, dy, 0)), 'pglow')
    return M
def item_superconductor():
    M = Model(); R = rz(-35)
    M.add('main', tf(cyl((0, -0.38, 0.14), (0, 0.38, 0.14), 0.11, n=14), R), 'hull_dark')
    for y in np.arange(-0.30, 0.28, 0.08):
        M.add('main', tf(cyl((0, y, 0.14), (0, y+0.045, 0.14), 0.14, n=14), R), 'copper')
    for y in (-0.42, 0.38):
        M.add('main', tf(cyl((0, y, 0.14), (0, y+0.04, 0.14), 0.09, n=12), R), 'glow')
    return M
def liquid_nitrogen():
    M = Model()
    drop = P([(0.27*math.cos(a), -0.08+0.27*math.sin(a)) for a in np.radians(np.linspace(150, 390, 22))] + [(0, 0.42)])
    M.add('main', prism(drop, 0, 0.16, 0.80), 'glass')
    M.add('main', tf(prism(P([(-0.14, -0.06), (-0.06, -0.20), (-0.02, -0.04)]), 0.16, 0.17), np.eye(3), (0, 0, 0)), 'glow')
    return M
