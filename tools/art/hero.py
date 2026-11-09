"""Hero kit: building blocks at the Cybran-LRA detail level.
Sloped armour with inlays, buttress legs, toothed turntables, lit grilles, coil jackets,
hydraulics, muzzle brakes, cables, shells, antennas, seams. 1.0 = one tile, Z up, heads face +Y."""
import numpy as np, math
from geom import *

def P(pts): return ccw([tuple(map(float, p)) for p in pts])

def zring(poly, zfn, dz=0.0):
    return np.column_stack([poly, [zfn(x, y)+dz for x, y in poly]])

def slope_plate(M, g, poly, zfn, mat, thick=0.10, inlay=None, isc=0.80, ih=0.032, R=None, t=(0, 0, 0), top_sc=0.95):
    p = P(poly); tp = scale_poly(p, top_sc)
    M.add(g, tf(loft(zring(p, zfn, -thick), zring(tp, zfn)), R, t), mat)
    if inlay:
        ip = scale_poly(p, isc)
        M.add(g, tf(loft(zring(ip, zfn, 0.003), zring(scale_poly(ip, 0.9), zfn, ih)), R, t), inlay)

def bolts_on(M, g, pts, zfn, r=0.024, m='metal_light', R=None):
    for (x, y) in pts:
        z = zfn(x, y)
        M.add(g, tf(cyl((x, y, z-0.01), (x, y, z+0.02), r, n=8), R), m)

def bolts_R(M, g, pts, z, R=None, r=0.026, m='metal_light'):
    for (x, y) in pts:
        M.add(g, tf(cyl((x, y, z), (x, y, z+0.02), r, n=8), R), m)

def buttress(M, g, ang, u0, u1, w, zhi, zlo, z0=0.08, mat='hull_dark', inlay='red_armor', tip='glow', bm='metal_light'):
    """Diagonal sloped leg (Cybran LRA base style) with inlay plate, tip light and bolts."""
    R = rz(ang)
    def zt(u): return zhi - (u-u0)/(u1-u0)*(zhi-zlo)
    L = u1-u0
    um, un = u0+L*0.45, u0+L*0.80
    bot = ccw([(u0, -w), (um, -w*0.78), (un, -w*0.42), (u1, 0.0), (un, w*0.42), (um, w*0.78), (u0, w)])
    top = ccw([(u0+0.02, -w*0.68), (um, -w*0.50), (un-0.01, -w*0.24), (u1-0.03, 0.0), (un-0.01, w*0.24), (um, w*0.50), (u0+0.02, w*0.68)])
    M.add(g, tf(loft(ring(bot, z0), np.column_stack([top, [zt(u) for u, _ in top]])), R), mat)
    if inlay:
        cp = ccw([(u0+L*0.09, -w*0.46), (um, -w*0.35), (un-L*0.03, -w*0.16), (un-L*0.03, w*0.16), (um, w*0.35), (u0+L*0.09, w*0.46)])
        cb = np.column_stack([cp, [zt(u)+0.004 for u, _ in cp]])
        cps = scale_poly(cp, (0.97, 0.75))
        ct = np.column_stack([cps, [zt(u)+0.038 for u, _ in cps]])
        M.add(g, tf(loft(cb, ct), R), inlay)
    if tip:
        ut = u1-L*0.15
        M.add(g, tf(cbox(ut, 0, zt(ut)+0.02, 0.07, 0.05, 0.05), R), tip)
    for v in (-w*0.55, w*0.55):
        uu = u0+L*0.06
        M.add(g, tf(cyl((uu, v, zt(uu)-0.02), (uu, v, zt(uu)+0.025), 0.033, n=8), R), bm)
    for s in (-1, 1):
        sp = ccw([(u0+L*0.33, s*w*0.72), (u0+L*0.48, s*w*0.72), (u0+L*0.40, s*w*1.25)])
        M.add(g, tf(loft(ring(sp, z0+0.04), ring(scale_poly(sp, 0.4), zt(u0+L*0.40)-0.10)), R), 'hull_light' if mat != 'hull_light' else 'hull_mid')

def turntable(M, g, r, z0, mid='hull_mid', dark='hull_dark', trim='glow', teeth=32, nb=12, rim='metal'):
    M.add(g, cyl((0, 0, z0), (0, 0, z0+0.12), r, n=44), mid)
    M.add(g, cyl((0, 0, z0+0.112), (0, 0, z0+0.122), r*1.01, n=44), trim)
    M.add(g, cyl((0, 0, z0+0.12), (0, 0, z0+0.16), r, r*0.94, n=44), rim)
    M.add(g, cyl((0, 0, z0+0.16), (0, 0, z0+0.17), r*0.87, n=44), dark)
    M.add(g, cyl((0, 0, z0+0.17), (0, 0, z0+0.175), r*0.62, n=40), 'vent')
    M.add(g, cyl((0, 0, z0+0.175), (0, 0, z0+0.19), r*0.30, n=24), mid)
    for i in range(nb):
        a = math.radians(360*i/nb+15); x, y = r*0.75*math.cos(a), r*0.75*math.sin(a)
        M.add(g, cyl((x, y, z0+0.17), (x, y, z0+0.19), 0.03, n=8), 'metal_light')
    for i in range(teeth):
        M.add(g, tf(cbox(r+0.03, 0, z0+0.06, 0.06, 0.07, 0.10), rz(360*i/teeth)), rim)
    return z0+0.175

def grille(M, g, cx, cy, z, w, d, n=6, glow='glow', slat='metal', frame='hull_light', R=None):
    def A(T, m): M.add(g, tf(T, R), m)
    A(box(cx-w/2, cx+w/2, cy-d/2, cy+d/2, z-0.01, z+0.008), 'vent')
    if glow: A(box(cx-w/2+0.035, cx+w/2-0.035, cy-d/2+0.03, cy+d/2-0.03, z-0.01, z+0.013), glow)
    for i in range(n):
        x = cx-w/2+w*(i+0.5)/n
        A(box(x-0.018, x+0.018, cy-d/2+0.015, cy+d/2-0.015, z+0.013, z+0.042), slat)
    for yy in (cy-d/2-0.025, cy+d/2+0.025):
        A(box(cx-w/2-0.04, cx+w/2+0.04, yy-0.025, yy+0.025, z-0.01, z+0.05), frame)

def coil_jacket(M, g, y0, n, step, r, band='red_armor', coil='coil', core='hull_dark', x=0.0, z=0.0, seg=24):
    M.add(g, cyl((x, y0-0.04, z), (x, y0+n*step+0.04, z), r*0.82, n=seg), core)
    for k in range(n):
        y = y0+k*step
        M.add(g, cyl((x, y, z), (x, y+step*0.33, z), r, n=seg), band)
        M.add(g, cyl((x, y+step*0.33, z), (x, y+step, z), r*0.88, n=seg), coil)

def hydraulic(M, g, x, z, y0, y1, ye, r=0.06, body='metal_light', rod='metal', collar='hull_mid'):
    M.add(g, cyl((x, y0, z), (x, y1, z), r, n=14), body)
    M.add(g, cyl((x, y1, z), (x, ye, z), r*0.55, n=12), rod)
    for y in (y0+0.05, y1-0.10):
        M.add(g, cyl((x, y, z), (x, y+0.06, z), r*1.25, n=14), collar)
    M.add(g, cyl((x, ye-0.03, z), (x, ye+0.04, z), r*1.1, n=12), collar)

def muzzle_brake(M, g, y0, L, hw, x=0.0, z=0.0, nb=3, body='hull_dark', trim='red_armor', baffle='metal_light', bore_r=0.07, out=None, bore_m='bore'):
    out = hw if out is None else out
    M.add(g, box(x-hw, x+hw, y0, y0+L, z-hw*0.85, z+hw*0.85), body)
    M.add(g, box(x-hw*0.55, x+hw*0.55, y0+0.02, y0+L-0.02, z+hw*0.70, z+hw*0.95), trim)
    st = (L-0.06)/nb
    for i in range(nb):
        yb = y0+0.03+i*st
        for s in (-1, 1):
            a, b = sorted((x+s*hw, x+s*(hw+out)))
            M.add(g, box(a, b, yb, yb+st*0.62, z-hw*0.70, z+hw*0.70), baffle)
    M.add(g, cyl((x, y0+L, z), (x, y0+L+0.015, z), bore_r*1.5, n=16), body)
    M.add(g, cyl((x, y0+L, z), (x, y0+L+0.022, z), bore_r, n=14), bore_m)

def cable(M, g, pts, r=0.03, m='cable', ends='red_armor', R=None):
    M.add(g, tf(tube_path(pts, r, n=10), R), m)
    if ends:
        for a, b in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            a = np.asarray(a, float); b = np.asarray(b, float); d = b-a; d /= np.linalg.norm(d)
            M.add(g, tf(cyl(a, a+d*0.06, r*1.7, n=10), R), ends)

def shell(M, g, x, y, z, L=0.36, r=0.05, case='yellow', tip='metal', band='copper'):
    a = np.array([x, y-L/2, z]); b = np.array([x, y+L*0.20, z]); c = np.array([x, y+L/2, z])
    M.add(g, cyl(a, b, r, n=10), case)
    M.add(g, cyl(b, c, r, r*0.30, n=10), tip)
    M.add(g, cyl(a+(b-a)*0.82, a+(b-a)*0.94, r*1.1, n=10), band)
    M.add(g, cyl(a-np.array([0, 0.012, 0]), a+np.array([0, 0.02, 0]), r*1.12, n=10), 'copper')

def antenna(M, g, p0, p1, r=0.022, tip='glow', baseM='hull_mid'):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    M.add(g, cyl(p0+np.array([0, 0, -0.01]), p0+np.array([0, 0, 0.035]), r*2.6, n=10), baseM)
    M.add(g, cyl(p0, p1, r, r*0.6, n=8), 'metal')
    d = p1-p0; d /= np.linalg.norm(d)
    M.add(g, cyl(p1, p1+d*0.045, r*1.9, n=8), tip)

def seam(M, g, p0, p1, z, m='hull_dark', w=0.03, h=0.02):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1-p0
    L = float(np.linalg.norm(d)); a = math.degrees(math.atan2(d[1], d[0])); c = (p0+p1)/2
    M.add(g, tf(cbox(0, 0, z+h/2, L, w, h), rz(a), (c[0], c[1], 0)), m)

def elevate(M, deg, pivot, src='barrel_local', dst='barrel'):
    M.parts[dst] = [(tf(T, rx(deg), pivot), m) for T, m in M.parts.pop(src)]

def muzzle_world(deg, pivot, y_local):
    a = math.radians(deg)
    return pivot[1]+y_local*math.cos(a), pivot[2]+y_local*math.sin(a)

# ------------------------------------------------------------------ foundations
def uef_hero_base(M, g, h, top=0.20):
    """Armoured UEF bunker pad: two tiers, 4 diagonal yellow-inlaid buttresses, lit side grilles, toothed ring."""
    M.add(g, prism(cham_rect(h*0.985, h*0.985, h*0.30), 0.0, 0.09, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(h*0.88, h*0.88, h*0.32), 0.09, top, 0.95), 'hull_mid')
    M.add(g, prism(cham_rect(h*0.70, h*0.70, h*0.28), top, top+0.012, 0.97), 'hull_dark')
    for k in range(4):
        buttress(M, g, 45+90*k, h*0.84, h*1.30, h*0.15, top+0.06, 0.11, z0=0.05, mat='hull_light', inlay='yellow', tip='glow')
        S = rz(90*k)
        grille(M, g, 0, -h*0.80, top, h*0.60, h*0.085, n=max(5, int(h*6)), glow='glow', R=S)
        for x in (-h*0.50, h*0.50):
            M.add(g, tf(cbox(x, -h*0.93, 0.10, 0.10, 0.06, 0.04), S), 'metal')
            M.add(g, tf(cyl((x, -h*0.93, 0.12), (x, -h*0.93, 0.15), 0.025, n=8), S), 'metal_light')
        bolts_R(M, g, [(-h*0.60, -h*0.62), (h*0.60, -h*0.62)], top+0.012, S)
        seam(M, g, (-h*0.40, -h*0.70), (h*0.40, -h*0.70), top+0.012, w=0.025, h=0.012)
    return turntable(M, g, h*0.66, top+0.012, teeth=int(28+h*6))

def cy_hero_base(M, g, f, glow='rglow'):
    """Port of the Cybran LRA foundation, scaled by f (f=1 -> 3x3)."""
    def S2(p): return [(x*f, y*f) for x, y in p]
    M.add(g, prism(cham_rect(1.47*f, 1.47*f, 0.42*f), 0.0, 0.12, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(1.27*f, 1.27*f, 0.52*f), 0.12, 0.27, 0.93), 'hull_mid')
    M.add(g, prism(cham_rect(1.08*f, 1.08*f, 0.46*f), 0.27, 0.30, 0.97), 'hull_dark')
    for k in range(4):
        R = rz(45+90*k)
        u0, u1 = 0.80*f, 1.74*f
        def zt(u, u0=u0, u1=u1): return 0.50-(u-u0)/(u1-u0)*0.32
        bot = ccw(S2([(0.80, -0.22), (1.20, -0.17), (1.52, -0.09), (1.74, 0.0), (1.52, 0.09), (1.20, 0.17), (0.80, 0.22)]))
        tp = ccw(S2([(0.82, -0.15), (1.20, -0.11), (1.50, -0.05), (1.71, 0.0), (1.50, 0.05), (1.20, 0.11), (0.82, 0.15)]))
        M.add(g, tf(loft(ring(bot, 0.12), np.column_stack([tp, [zt(u) for u, _ in tp]])), R), 'hull_dark')
        cp = ccw(S2([(0.90, -0.10), (1.25, -0.075), (1.48, -0.035), (1.48, 0.035), (1.25, 0.075), (0.90, 0.10)]))
        cb = np.column_stack([cp, [zt(u)+0.004 for u, _ in cp]])
        cps = scale_poly(cp, (0.97, 0.75))
        M.add(g, tf(loft(cb, np.column_stack([cps, [zt(u)+0.04 for u, _ in cps]])), R), 'red_armor')
        M.add(g, tf(cbox(1.60*f, 0, zt(1.60*f)+0.02, 0.07*f, 0.05*f, 0.05), R), glow)
        for v in (-0.12*f, 0.12*f):
            M.add(g, tf(cyl((0.86*f, v, zt(0.86*f)-0.02), (0.86*f, v, zt(0.86*f)+0.025), 0.035, n=8), R), 'metal_light')
        for s in (-1, 1):
            sp_b = ccw(S2([(1.10, s*0.15), (1.24, s*0.15), (1.17, s*0.27)]))
            M.add(g, tf(loft(ring(sp_b, 0.12), ring(scale_poly(sp_b, 0.4), 0.26)), R), 'hull_light')
        S = rz(90*k)
        M.add(g, tf(box(-0.34*f, 0.34*f, 0.86*f, 1.10*f, 0.27, 0.278), S), 'vent')
        M.add(g, tf(box(-0.29*f, 0.29*f, 0.90*f, 1.06*f, 0.27, 0.283), S), glow)
        for i in range(int(6*f)):
            x = (-0.25+i*0.5/(int(6*f)-1))*f
            M.add(g, tf(box(x-0.022, x+0.022, 0.88*f, 1.08*f, 0.283, 0.31), S), 'metal')
        M.add(g, tf(box(-0.38*f, 0.38*f, 1.10*f, 1.15*f, 0.27, 0.32), S), 'hull_light')
        M.add(g, tf(box(-0.38*f, 0.38*f, 0.81*f, 0.86*f, 0.27, 0.32), S), 'hull_light')
        for sx in (-0.55*f, 0.55*f):
            pts = [(sx, 1.40*f, 0.15), (sx*0.93, 1.18*f, 0.30), (sx*0.80, 1.00*f, 0.38)]
            M.add(g, tf(tube_path(pts, 0.045, n=10), S), 'cable')
            M.add(g, tf(cyl((sx, 1.42*f, 0.15), (sx, 1.34*f, 0.19), 0.065, n=10), S), 'red_armor')
        for x in (-1.0, -0.8, 0.8, 1.0):
            M.add(g, tf(cyl((x*f, 1.36*f, 0.11), (x*f, 1.36*f, 0.145), 0.032, n=8), S), 'metal_light')
    r = 0.99*f
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.42), r, n=48), 'hull_mid')
    M.add(g, cyl((0, 0, 0.42), (0, 0, 0.46), r, r*0.94, n=48), 'metal')
    M.add(g, cyl((0, 0, 0.46), (0, 0, 0.47), r*0.87, n=48), 'hull_dark')
    M.add(g, cyl((0, 0, 0.47), (0, 0, 0.475), r*0.63, n=40), 'vent')
    M.add(g, cyl((0, 0, 0.475), (0, 0, 0.49), r*0.30, n=24), 'hull_mid')
    for i in range(12):
        a = math.radians(360*i/12+15)
        M.add(g, cyl((0.74*r*math.cos(a), 0.74*r*math.sin(a), 0.47), (0.74*r*math.cos(a), 0.74*r*math.sin(a), 0.49), 0.03, n=8), 'metal_light')
    nt = int(32*f)
    for i in range(nt):
        M.add(g, tf(cbox(r+0.035, 0, 0.36, 0.06, 0.07, 0.10), rz(360*i/nt)), 'metal')
    M.add(g, cyl((0, 0, 0.415), (0, 0, 0.425), r*1.01, n=48), glow)
    return 0.46

def heat_grad(y0, y1, mats=('metal', 'hull_dark', 'bore', 'hull_mid', 'metal_light'), always=('coil',)):
    from mats import MID
    ids = [MID[m] for m in mats]; al = [MID[m] for m in always]
    def f(mp, X, Y, g):
        return np.maximum(np.isin(mp, al).astype(float)*0.9, np.where(np.isin(mp, ids), np.clip((Y-y0)/(y1-y0), 0, 1)*0.85, 0))
    return f
