"""Defence workstream (hero rework): shields, walls, nanite repairer.

    .venv/bin/python tools/art/g_defense.py

Regenerates into mod/sprites:
  blocks/defense/shield-emitter{,-top,-full}   UEF T1 ForceProjector 2x2
  blocks/defense/ed-shield{,-top,-full}        Cybran T2 ForceProjector 2x2
  blocks/defense/pulse-shield{,-top,-full}     UEF T3 ForceProjector 3x3
  blocks/defense/nanite-repairer{,-top,-full}  Cybran T3 MendProjector 2x2
  blocks/walls/steel-wall, steel-wall-large, wolfram-wall{,-full}, wolfram-wall-large{,-full}
ForceProjector draws `-top` additively (alpha = shield buildup), MendProjector draws it tinted with
baseColor and a pulsing alpha, so both `-top` layers are white masks of the emitter core / coils.
1.0 = one tile, Z up, origin = block centre.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *  # noqa: E402,F401
from mats import Model, MID  # noqa: E402
from hero import P, slope_plate, bolts_R, buttress, grille, cable, seam, antenna  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
import rend  # noqa: E402
from export import save, layer, FULL, qa_sheet, QA  # noqa: E402

# nanite slurry glow, matched to the repairer's baseColor (84f491) at ramp step 3
rend.add_material('nanite', ['1c5a26', '2f9a3e', '52d064', '84f491', 'b4fac0', 'e0ffe6'], glow=True)
# white-hot crystal facets (glow pixels only use ramp steps 1-3)
rend.add_material('rhot', ['ff4a60', 'ff7486', 'ffa3ae', 'ffd0d6', 'ffe8eb', 'ffffff'], glow=True)
rend.add_material('bhot', ['56b4f2', '8fd0fa', 'bfe6ff', 'e6f6ff', 'f4fbff', 'ffffff'], glow=True)

DEF = 'blocks/defense'
WAL = 'blocks/walls'


# ------------------------------------------------------------------ small geometry kit
def ngon(n, r, cx=0.0, cy=0.0, rot=0.0, sx=1.0, sy=1.0):
    return P([(cx+sx*r*math.cos(math.radians(rot+360.0*i/n)), cy+sy*r*math.sin(math.radians(rot+360.0*i/n))) for i in range(n)])


def circ(r, n, cx=0.0, cy=0.0, rot=0.0):
    a = np.radians(rot+np.arange(n)*360.0/n)
    return np.column_stack([cx+r*np.cos(a), cy+r*np.sin(a)])


def band(ri, ro, z, n=32, cx=0.0, cy=0.0, h=0.0, zi=None):
    """Flat (or conical when zi is given) annulus; h adds an outer skirt down to z-h."""
    zi = z if zi is None else zi
    T = [loft(ring(circ(ro, n, cx, cy), z), ring(circ(ri, n, cx, cy), zi), False, False)]
    if h > 0:
        T.append(loft(ring(circ(ro, n, cx, cy), z-h), ring(circ(ro, n, cx, cy), z), False, False))
    return np.concatenate(T)


def torus(M, g, R, r, z, m, n=28, k=8, a0=0.0, cx=0.0, cy=0.0):
    for i in range(n):
        a, b = math.radians(a0+360*i/n), math.radians(a0+360*(i+1)/n)
        M.add(g, cyl((cx+R*math.cos(a), cy+R*math.sin(a), z), (cx+R*math.cos(b), cy+R*math.sin(b), z), r, n=k), m)


def bipyr(n, r, zb, zm, zt, cx=0.0, cy=0.0, rot=0.0, sx=1.0, sy=1.0):
    mid = [np.array([x, y, zm]) for x, y in ngon(n, r, cx, cy, rot, sx, sy)]
    top = np.array([cx, cy, zt]); bot = np.array([cx, cy, zb])
    T = []
    for i in range(n):
        a, b = mid[i], mid[(i+1) % n]
        T.append([a, b, top]); T.append([b, a, bot])
    return clean(T)


def bipyr2(M, g, n, r, zb, zm, zt, ma, mb, cx=0.0, cy=0.0, rot=0.0):
    """Crystal with alternating facet materials."""
    mid = [np.array([x, y, zm]) for x, y in ngon(n, r, cx, cy, rot)]
    top = np.array([cx, cy, zt]); bot = np.array([cx, cy, zb])
    for i in range(n):
        a, b = mid[i], mid[(i+1) % n]
        M.add(g, [[a, b, top], [b, a, bot]], ma if i % 2 == 0 else mb)


def plate(M, g, bot, top, z0, z1, mb, mt, R=None):
    """Chamfered plate: bevel ring in mb (bright lit edge / dark shadow edge), face in mt."""
    M.add(g, tf(prism(bot, z0, z1, top_poly=top), R), mb)
    M.add(g, tf(prism(top, z1, z1+0.004), R), mt)


def rod(p0, p1, r0, r1=None, n=8):
    return cyl(p0, p1, r0, r1, n=n)


def B(x0, x1, y0, y1, z0, z1):
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1)


def rot_pts(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x*c-y*s, x*s+y*c) for x, y in pts]


def capacitor(M, g, x, y, z0, h, r, body='metal_light', band_m='yellow', cap='hull_mid', tip='glow', collar='hull_dark'):
    """Upright capacitor can: collar, ribbed body, coloured band, cap with two terminals + status light."""
    M.add(g, cyl((x, y, z0), (x, y, z0+0.05), r*1.18, n=16), collar)
    M.add(g, cyl((x, y, z0+0.05), (x, y, z0+h), r, n=16), body)
    M.add(g, cyl((x, y, z0+h*0.55), (x, y, z0+h*0.72), r*1.05, n=16), band_m)
    M.add(g, cyl((x, y, z0+h), (x, y, z0+h+0.035), r*0.98, r*0.80, n=16), cap)
    for s in (-1, 1):
        M.add(g, cyl((x+s*r*0.42, y, z0+h+0.03), (x+s*r*0.42, y, z0+h+0.075), r*0.20, n=8), 'metal')
    if tip:
        M.add(g, cyl((x, y+r*0.40, z0+h+0.03), (x, y+r*0.40, z0+h+0.05), r*0.17, n=8), tip)


def fin_bank(M, g, x0, x1, y0, y1, z0, z1, n, fin='metal', base='vent', frame='hull_light', glow=None, R=None):
    """Cooling fins: n thin plates across y, standing on a dark trough, framed at both ends."""
    def A(T, m): M.add(g, tf(T, R), m)
    A(B(x0, x1, y0, y1, z0-0.01, z0+0.01), base)
    if glow:
        A(B(x0+0.03, x1-0.03, y0+0.02, y1-0.02, z0-0.01, z0+0.016), glow)
    st = (y1-y0)/n
    for i in range(n):
        y = y0+st*(i+0.5)
        A(prism(rect((x0+x1)/2, y, (x1-x0)/2-0.01, st*0.24), z0, z1, top_poly=rect((x0+x1)/2, y, (x1-x0)/2-0.03, st*0.14)), fin)
    for yy in (y0-0.03, y1+0.03):
        A(B(x0-0.02, x1+0.02, yy-0.03, yy+0.03, z0-0.01, z1+0.02), frame)


def hazard(M, g, cx, cy, z, w, d, n=3, R=None):
    """Dark plate with n bold slanted yellow stripes (reads at 32 px/tile, unlike thin chevrons)."""
    M.add(g, tf(cbox(cx, cy, z+0.006, w, d, 0.012), R), 'hull_dark')
    sw = w/(2*n)
    for i in range(n):
        x = cx-w/2+(i+0.5)*w/n
        p = [(x-sw/2-d*0.25, cy-d*0.38), (x+sw/2-d*0.25, cy-d*0.38), (x+sw/2+d*0.25, cy+d*0.38), (x-sw/2+d*0.25, cy+d*0.38)]
        M.add(g, tf(prism(P(p), z+0.012, z+0.022), R), 'yellow')


def heatmask(weights):
    """heat fn from {material: weight}."""
    ids = {MID[k]: v for k, v in weights.items()}

    def f(mp, X, Y, g):
        out = np.zeros(mp.shape)
        for i, v in ids.items():
            out = np.where(mp == i, v, out)
        return out
    return f


# ================================================================== SHIELD EMITTER - UEF T1 (2x2)
def shield_emitter():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.985, 0.985, 0.26), 0.0, 0.08, 0.985), 'hull_dark')
    plate(M, g, cham_rect(0.93, 0.93, 0.28), cham_rect(0.87, 0.87, 0.26), 0.08, 0.20, 'hull_light', 'hull_mid')
    M.add(g, prism(cham_rect(0.70, 0.70, 0.22), 0.204, 0.208), 'hull_dark')        # deck seam ring
    M.add(g, prism(cham_rect(0.67, 0.67, 0.21), 0.204, 0.212), 'hull_mid')
    # corner capacitor cans (yellow-banded UEF stores) wired to the pedestal
    for sx in (-1, 1):
        for sy in (-1, 1):
            capacitor(M, g, sx*0.62, sy*0.62, 0.20, 0.24, 0.150)
            cable(M, g, [(sx*0.55, sy*0.50, 0.40), (sx*0.46, sy*0.40, 0.46), (sx*0.36, sy*0.30, 0.36)], 0.028, ends='yellow')
    # side cooling fin banks with blue glow in the trough
    for s in (-1, 1):
        fin_bank(M, g, 0.74, 0.92, -0.36, 0.36, 0.20, 0.34, 6, glow='glow', R=rz(0 if s > 0 else 180))
    # front: hazard plate + status lights; back: power intake box
    hazard(M, g, 0, -0.84, 0.212, 0.54, 0.14, n=3)
    for x in (-0.40, 0.40):
        light(M, g, x, -0.85, 0.212, 0.06, 0.04, 0.015)
    M.add(g, B(-0.30, 0.30, 0.72, 0.94, 0.20, 0.30), 'hull_light')
    M.add(g, B(-0.24, 0.24, 0.76, 0.90, 0.30, 0.315), 'vent')
    for x in (-0.16, 0.0, 0.16):
        M.add(g, B(x-0.035, x+0.035, 0.77, 0.89, 0.30, 0.33), 'yellow')
    bolts(M, g, [(-0.40, 0.84), (0.40, 0.84), (-0.84, -0.46), (0.84, -0.46), (-0.84, 0.46), (0.84, 0.46)], 0.20, r=0.024)
    # emitter pedestal: octagonal plinth with a lit bevel
    plate(M, g, ngon(8, 0.56, rot=22.5), ngon(8, 0.49, rot=22.5), 0.21, 0.31, 'hull_light', 'hull_mid')
    bolts(M, g, [(0.455*math.cos(math.radians(a)), 0.455*math.sin(math.radians(a))) for a in range(0, 360, 45)], 0.314, r=0.022)
    # copper field coil around the dish
    torus(M, g, 0.40, 0.045, 0.36, 'copper', n=28, k=8)
    for i in range(8):
        M.add(g, tf(cbox(0.40, 0, 0.36, 0.07, 0.05, 0.11), rz(22.5+45*i)), 'hull_dark')
    # projector dish: rim + concave glass bowl, emitter crystal on a mast and tripod
    M.add(g, band(0.33, 0.37, 0.42, n=32, h=0.08), 'metal_light')
    M.add(g, band(0.15, 0.33, 0.42, n=32, zi=0.33), 'glass')
    M.add(g, band(0.11, 0.15, 0.335, n=24), 'glow')
    M.add(g, band(0.0, 0.11, 0.33, n=20), 'hull_dark')
    for i in range(3):                                          # dish ribs
        a = math.radians(150+120*i)
        M.add(g, rod((0.16*math.cos(a), 0.16*math.sin(a), 0.345), (0.33*math.cos(a), 0.33*math.sin(a), 0.43), 0.016, n=6), 'metal')
    M.add(g, rod((0, 0, 0.33), (0, 0, 0.60), 0.045, n=10), 'metal')
    for i in range(3):
        a = math.radians(90+120*i)
        p0 = (0.35*math.cos(a), 0.35*math.sin(a), 0.43)
        M.add(g, rod(p0, (0.05*math.cos(a), 0.05*math.sin(a), 0.63), 0.024, 0.016, n=6), 'metal_light')
        M.add(g, cyl(p0, (p0[0], p0[1], p0[2]+0.03), 0.042, n=8), 'yellow')
    M.add(g, cyl((0, 0, 0.58), (0, 0, 0.63), 0.075, n=12), 'hull_mid')
    bipyr2(M, g, 6, 0.095, 0.60, 0.69, 0.84, 'glow', 'bhot', rot=30)
    return M


# ================================================================== ED SHIELD - Cybran T2 (2x2)
ED_LEG, ED_CHEEK, ED_DECK = 'hull_dark', 'hull_mid', 'cy_dark'


def ed_shield():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.97, 0.97, 0.40), 0.0, 0.09, 0.985), 'cy_dark')
    plate(M, g, cham_rect(0.86, 0.86, 0.40), cham_rect(0.80, 0.80, 0.37), 0.09, 0.21, 'cy_mid', ED_DECK)
    # diagonal Cybran legs with red inlays and glowing toes
    for k in range(4):
        buttress(M, g, 45+90*k, 0.58, 1.24, 0.21, 0.38, 0.12, z0=0.06, mat=ED_LEG, inlay='red_armor', tip='rglow')
    # front/back: sloped red-inlaid armour cheeks; left/right: red-lit vent grilles
    for k in range(4):
        S = rz(90*k)
        poly = [(-0.32, -0.50), (0.32, -0.50), (0.24, -0.88), (-0.24, -0.88)]
        zf = (lambda x, y: 0.34+(y+0.50)*0.32)
        if k % 2 == 0:
            slope_plate(M, g, poly, zf, ED_CHEEK, thick=0.14, inlay='red_armor', isc=0.56, ih=0.03, R=S)
            bolts_R(M, g, [(-0.22, -0.56), (0.22, -0.56), (-0.17, -0.82), (0.17, -0.82)], 0.0, S, r=0.022)
            M.add(g, tf(cbox(0, -0.84, zf(0, -0.84)+0.012, 0.18, 0.035, 0.03), S), 'rglow')
        else:
            M.add(g, tf(prism(P(poly), 0.20, 0.25, 0.95), S), 'cy_dark')
            grille(M, g, 0, -0.69, 0.25, 0.44, 0.22, n=6, glow='rglow', slat='cy_mid', frame='hull_dark', R=S)
    # hexagonal emitter housing with three red armour facets
    plate(M, g, ngon(6, 0.47), ngon(6, 0.41), 0.21, 0.36, 'metal', 'hull_dark')
    for i in range(3):
        zf = (lambda x, y: 0.42-(x-0.25)*0.45)
        slope_plate(M, g, [(0.25, -0.12), (0.38, -0.19), (0.38, 0.19), (0.25, 0.12)], zf, 'cy_mid', thick=0.07, inlay='rglow', isc=0.45, ih=0.012, R=rz(30+120*i))
    M.add(g, band(0.0, 0.25, 0.37, n=24), 'bore')
    M.add(g, band(0.20, 0.245, 0.385, n=24), 'rglow')
    # three claws hugging the crystal
    for i in range(3):
        a = math.radians(90+120*i)
        c, s = math.cos(a), math.sin(a)
        pts = [(0.38*c, 0.38*s, 0.37), (0.31*c, 0.31*s, 0.62), (0.17*c, 0.17*s, 0.80)]
        M.add(g, rod(pts[0], pts[1], 0.065, 0.05, n=6), 'cy_mid')
        M.add(g, rod(pts[1], pts[2], 0.05, 0.014, n=6), 'red_armor')
        M.add(g, sphereish(pts[1], 0.06, n=8), 'hull_dark')
    # the ED crystal: tall faceted red/white bipyramid on a dark collar
    M.add(g, cyl((0, 0, 0.37), (0, 0, 0.46), 0.13, 0.10, n=12), 'hull_dark')
    bipyr2(M, g, 6, 0.15, 0.42, 0.60, 1.00, 'rglow', 'rhot', rot=30)
    for k in range(4):
        cable(M, g, [(0.78, 0, 0.30), (0.62, 0.0, 0.42), (0.46, 0, 0.37)], 0.032, ends='red_armor', R=rz(45+90*k))
    return M


# ================================================================== PULSE SHIELD - UEF T3 (3x3)
def pulse_shield():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(1.48, 1.48, 0.42), 0.0, 0.10, 0.985), 'hull_dark')
    plate(M, g, cham_rect(1.38, 1.38, 0.46), cham_rect(1.31, 1.31, 0.43), 0.10, 0.26, 'hull_light', 'hull_mid')
    M.add(g, prism(cham_rect(1.12, 1.12, 0.40), 0.264, 0.268), 'hull_dark')        # deck seam ring
    M.add(g, prism(cham_rect(1.09, 1.09, 0.39), 0.264, 0.272), 'hull_mid')
    for k in range(4):                                         # diagonal yellow-inlaid buttresses with beacons
        buttress(M, g, 45+90*k, 1.02, 1.80, 0.20, 0.44, 0.14, z0=0.08, mat='hull_light', inlay='yellow', tip='glow')
    for k in (0, 2):                                           # front/back: three-can capacitor banks
        S = rz(90*k)
        plate(M, g, rect(0, -1.22, 0.64, 0.19), rect(0, -1.22, 0.60, 0.16), 0.26, 0.30, 'hull_light', 'hull_dark', R=S)
        for x in (-0.38, 0.0, 0.38):
            xx, yy, _ = S @ np.array([x, -1.22, 0])
            capacitor(M, g, xx, yy, 0.30, 0.26, 0.13)
        bolts_R(M, g, [(-0.58, -1.38), (0.58, -1.38), (-0.58, -1.06), (0.58, -1.06)], 0.304, S, r=0.024)
        for x in (-0.38, 0.38):
            cable(M, g, [(x, -1.10, 0.52), (x*0.8, -0.98, 0.62), (x*0.6, -0.86, 0.56)], 0.035, ends='yellow', R=S)
    for k in (1, 3):                                           # sides: heat-sink fin banks with lit trough
        S = rz(90*k)
        fin_bank(M, g, -0.58, 0.58, -1.42, -1.06, 0.26, 0.44, 1, R=S)    # frame only
        for i in range(9):
            x = -0.50+i*0.125
            M.add(g, tf(prism(rect(x, -1.24, 0.022, 0.17), 0.27, 0.46, top_poly=rect(x, -1.24, 0.012, 0.15)), S), 'metal')
        M.add(g, tf(B(-0.54, 0.54, -1.38, -1.10, 0.265, 0.285), S), 'glow')
        light(M, g, *tuple((S @ np.array([0, -0.96, 0]))[:2]), 0.272, 0.10, 0.03)
    # pulse ring: big copper-wound torus on four clamps
    z = 0.58
    M.add(g, band(0.86, 1.00, 0.30, n=48, h=0.04), 'metal')
    torus(M, g, 0.86, 0.10, z, 'metal_light', n=40, k=10)
    for i in range(16):
        a = 360*i/16+11.25
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        c = np.array([0.86*ca, 0.86*sa, z]); t = np.array([-sa, ca, 0])
        M.add(g, cyl(c-t*0.06, c+t*0.06, 0.135, n=12), 'copper')
        M.add(g, cyl(c-t*0.075, c-t*0.06, 0.145, n=12), 'hull_dark')
    for i in range(4):
        R = rz(45+90*i)
        M.add(g, tf(B(0.72, 1.02, -0.09, 0.09, 0.30, z+0.16), R), 'hull_light')
        M.add(g, tf(B(0.76, 0.98, -0.06, 0.06, z+0.16, z+0.18), R), 'yellow')
        M.add(g, tf(cyl((0.87, 0, z+0.18), (0.87, 0, z+0.21), 0.035, n=8), R), 'glow')
    # central pulse tower: three stepped drums with glow seams
    M.add(g, cyl((0, 0, 0.27), (0, 0, 0.44), 0.62, 0.58, n=40), 'hull_light')
    M.add(g, band(0.50, 0.58, 0.44, n=40), 'hull_mid')
    M.add(g, cyl((0, 0, 0.44), (0, 0, 0.58), 0.50, 0.46, n=36), 'hull_mid')
    M.add(g, band(0.44, 0.50, 0.585, n=36), 'glow')
    M.add(g, cyl((0, 0, 0.58), (0, 0, 0.70), 0.42, 0.36, n=32), 'metal')
    for i in range(8):
        M.add(g, tf(cbox(0.39, 0, 0.66, 0.08, 0.09, 0.10), rz(22.5+45*i)), 'hull_dark')
    M.add(g, band(0.0, 0.36, 0.70, n=32), 'hull_dark')
    bolts(M, g, [(0.53*math.cos(math.radians(a)), 0.53*math.sin(math.radians(a))) for a in range(0, 360, 30)], 0.44, r=0.022)
    # four converging emitter prongs and the pulse orb
    for i in range(4):
        a = math.radians(45+90*i); c, s = math.cos(a), math.sin(a)
        pts = [(0.30*c, 0.30*s, 0.70), (0.30*c, 0.30*s, 0.86), (0.20*c, 0.20*s, 0.98), (0.11*c, 0.11*s, 1.02)]
        M.add(g, tube_path(pts, 0.035, n=8), 'metal_light')
        M.add(g, cyl((0.30*c, 0.30*s, 0.70), (0.30*c, 0.30*s, 0.76), 0.06, n=10), 'yellow')
        M.add(g, cyl((0.30*c, 0.30*s, 0.82), (0.30*c, 0.30*s, 0.86), 0.05, n=10), 'copper')
    for i in range(4):
        M.add(g, tf(B(0.10, 0.30, -0.035, 0.035, 0.70, 0.72), rz(90*i)), 'glow')
    M.add(g, sphereish((0, 0, 1.0), 0.15, n=14), 'glow')
    M.add(g, sphereish((-0.04, 0.03, 1.07), 0.07, n=10), 'bhot')
    for s in (-1, 1):
        cable(M, g, [(s*0.98, 0.10, 0.30), (s*0.80, 0.10, 0.36), (s*0.62, 0.10, 0.40)], 0.035, ends='yellow')
    return M


# ================================================================== NANITE REPAIRER - Cybran T3 MendProjector (2x2)
def nanite_repairer():
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.97, 0.97, 0.34), 0.0, 0.09, 0.985), 'cy_dark')
    plate(M, g, cham_rect(0.88, 0.88, 0.34), cham_rect(0.82, 0.82, 0.32), 0.09, 0.20, 'cy_mid', 'hull_dark')
    # left/right: nanite feed pipes into the vat
    for s in (-1, 1):
        M.add(g, B(s*0.70, s*0.94, -0.30, 0.30, 0.20, 0.26), 'cy_dark')
        for y in (-0.16, 0.16):
            M.add(g, cyl((s*0.92, y, 0.30), (s*0.44, y, 0.30), 0.055, n=12), 'metal')
            for xc in (s*0.82, s*0.60):
                M.add(g, cyl((xc-0.025, y, 0.30), (xc+0.025, y, 0.30), 0.075, n=12), 'red_armor')
    # front/back: sloped red-inlaid armour with a status strip
    for k in (0, 2):
        S = rz(90*k)
        poly = [(-0.34, -0.56), (0.34, -0.56), (0.26, -0.90), (-0.26, -0.90)]
        zf = (lambda x, y: 0.32+(y+0.56)*0.30)
        slope_plate(M, g, poly, zf, 'cy_mid', thick=0.13, inlay='red_armor', isc=0.58, ih=0.03, R=S)
        M.add(g, tf(cbox(0, -0.84, zf(0, -0.84)+0.012, 0.16, 0.035, 0.03), S), 'rglow')
    # four corner emitters: hex housing, red collar, three-prong claw holding a nanite orb
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx*0.66, sy*0.66
            plate(M, g, ngon(6, 0.165, cx, cy, 30), ngon(6, 0.125, cx, cy, 30), 0.20, 0.34, 'cy_mid', 'hull_dark')
            M.add(g, cyl((cx, cy, 0.34), (cx, cy, 0.40), 0.10, 0.08, n=12), 'red_armor')
            ox, oy = cx*1.03, cy*1.03
            M.add(g, rod((cx, cy, 0.40), (ox, oy, 0.47), 0.04, 0.03, n=8), 'metal')
            for j in range(3):
                a = math.radians(120*j+(45 if sx*sy > 0 else -45))
                M.add(g, rod((ox+0.085*math.cos(a), oy+0.085*math.sin(a), 0.42), (ox+0.06*math.cos(a), oy+0.06*math.sin(a), 0.60), 0.022, 0.01, n=6), 'red_armor')
            M.add(g, sphereish((ox, oy, 0.52), 0.07, n=10), 'nanite')
            cable(M, g, [(cx*0.80, cy*0.80, 0.30), (cx*0.70, cy*0.70, 0.42), (cx*0.60, cy*0.60, 0.40)], 0.026, ends='red_armor')
    # the vat: armoured drum with red bands, glowing nanite slurry stirred into a three-arm vortex
    M.add(g, cyl((0, 0, 0.20), (0, 0, 0.40), 0.50, 0.475, n=36), 'cy_mid')
    for zb in (0.25, 0.36):
        M.add(g, cyl((0, 0, zb), (0, 0, zb+0.04), 0.505, n=36), 'red_armor')
    M.add(g, band(0.38, 0.47, 0.46, n=36, h=0.07), 'metal')
    for i in range(6):
        M.add(g, tf(cbox(0.425, 0, 0.465, 0.08, 0.06, 0.03), rz(30+60*i)), 'hull_dark')
    M.add(g, band(0.0, 0.38, 0.42, n=36), 'nanite')
    for j in range(3):
        prev = None
        for t in np.linspace(0, 1, 10):
            r = 0.10+0.27*t; a = math.radians(120*j+20+t*150)
            p = np.array([r*math.cos(a), r*math.sin(a), 0.43])
            if prev is not None:
                w = 0.030-0.014*t
                M.add(g, rod(prev, p, w, w, n=6), 'cy_dark')
            prev = p
    M.add(g, cyl((0, 0, 0.40), (0, 0, 0.48), 0.10, 0.09, n=14), 'cy_mid')
    M.add(g, cyl((0, 0, 0.48), (0, 0, 0.495), 0.075, n=12), 'red_armor')
    M.add(g, cyl((0, 0, 0.495), (0, 0, 0.51), 0.04, n=10), 'rglow')
    return M


# ================================================================== WALLS
# Every wall shares the same rim + chamfered plate edge so mixed rows tile cleanly; v = variant
# (1 is the icon design, 2..N vary only the inner details so long rows don't repeat).
def steel_wall(v=1):
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.495, 0.495, 0.07), 0.0, 0.08, top_poly=cham_rect(0.485, 0.485, 0.07)), 'hull_dark')
    plate(M, g, cham_rect(0.47, 0.47, 0.09), cham_rect(0.40, 0.40, 0.07), 0.08, 0.20, 'steel', 'hull_light')
    M.add(g, prism(cham_rect(0.29, 0.29, 0.06), 0.204, 0.208), 'hull_dark')            # groove
    plate(M, g, cham_rect(0.265, 0.265, 0.055), cham_rect(0.22, 0.22, 0.045), 0.204, 0.26, 'steel', 'hull_light')
    bolts(M, g, [(-0.335, -0.335), (0.335, -0.335), (-0.335, 0.335), (0.335, 0.335)], 0.204, r=0.036)
    if v in (1, 2):                                                                    # reinforcing rib
        R = None if v == 1 else rz(90)
        M.add(g, tf(B(-0.30, 0.30, -0.04, 0.04, 0.26, 0.29), R), 'hull_mid')
        M.add(g, tf(B(-0.27, 0.27, -0.02, 0.02, 0.29, 0.296), R), 'steel')
    else:                                                                              # vision-slit grille
        M.add(g, B(-0.17, 0.17, -0.15, 0.15, 0.262, 0.27), 'hull_mid')
        for y in (-0.08, 0.0, 0.08):
            M.add(g, B(-0.13, 0.13, y-0.022, y+0.022, 0.266, 0.274), 'vent')
    if v != 2:                                                                         # yellow hazard tab
        sy = -1 if v == 1 else 1
        for x0 in (-0.06, 0.06):
            M.add(g, prism(P([(x0, sy*0.37), (x0+0.10, sy*0.37), (x0+0.14, sy*0.31), (x0+0.04, sy*0.31)]), 0.204, 0.214), 'yellow')
    return M


def steel_wall_large(v=1):
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.995, 0.995, 0.12), 0.0, 0.08, top_poly=cham_rect(0.985, 0.985, 0.12)), 'hull_dark')
    plate(M, g, cham_rect(0.96, 0.96, 0.16), cham_rect(0.87, 0.87, 0.13), 0.08, 0.22, 'steel', 'hull_light')
    M.add(g, prism(cham_rect(0.66, 0.66, 0.16), 0.224, 0.228), 'hull_dark')            # groove
    plate(M, g, cham_rect(0.62, 0.62, 0.15), cham_rect(0.53, 0.53, 0.12), 0.224, 0.32, 'steel', 'hull_light')
    for q in (-0.78, -0.39, 0.39, 0.78):                                               # perimeter bolt ring
        bolts(M, g, [(q, -0.78), (q, 0.78), (-0.78, q), (0.78, q)], 0.224, r=0.034)
    bolts(M, g, [(0, 0.78), (-0.78, 0), (0.78, 0)], 0.224, r=0.034)
    R = None if v == 1 else rz(90)
    for y in (-0.30, 0.30):                                                            # two heavy ribs with brackets
        M.add(g, tf(B(-0.76, 0.76, y-0.06, y+0.06, 0.224, 0.38), R), 'hull_mid')
        M.add(g, tf(B(-0.72, 0.72, y-0.03, y+0.03, 0.38, 0.39), R), 'steel')
        for x in (-0.70, 0.70):
            M.add(g, tf(B(x-0.07, x+0.07, y-0.09, y+0.09, 0.224, 0.40), R), 'hull_light')
            M.add(g, tf(cyl((x, y, 0.40), (x, y, 0.415), 0.035, n=8), R), 'metal_light')
    plate(M, g, ngon(8, 0.19, rot=22.5), ngon(8, 0.15, rot=22.5), 0.324, 0.40, 'steel', 'hull_mid')   # central hatch
    M.add(g, cyl((0, 0, 0.404), (0, 0, 0.41), 0.08, n=12), 'hull_dark')
    bolts(M, g, [(0.115*math.cos(math.radians(a)), 0.115*math.sin(math.radians(a))) for a in (45, 135, 225, 315)], 0.404, r=0.02)
    hazard(M, g, 0, -0.78, 0.224, 0.46, 0.13, n=3)
    return M


def wolfram_wall(v=1):
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.495, 0.495, 0.08), 0.0, 0.10, top_poly=cham_rect(0.485, 0.485, 0.08)), 'tung')
    plate(M, g, cham_rect(0.475, 0.475, 0.11), cham_rect(0.385, 0.385, 0.09), 0.10, 0.26, 'metal', 'tung')
    plate(M, g, cham_rect(0.30, 0.30, 0.08), cham_rect(0.23, 0.23, 0.06), 0.264, 0.36, 'ore_wolf', 'tung')
    if v == 1:
        M.add(g, B(-0.15, 0.15, -0.025, 0.025, 0.36, 0.368), 'cobalt')
    elif v == 2:
        M.add(g, B(-0.025, 0.025, -0.15, 0.15, 0.36, 0.368), 'cobalt')
    else:                                                                              # laminated: two grooves + short slot
        for y in (-0.11, 0.11):
            seam(M, g, (-0.20, y), (0.20, y), 0.364, m='bore', w=0.03, h=0.006)
        M.add(g, B(-0.08, 0.08, -0.02, 0.02, 0.36, 0.368), 'cobalt')
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(g, cyl((sx*0.335, sy*0.335, 0.26), (sx*0.335, sy*0.335, 0.30), 0.05, 0.034, n=8), 'steel')
    return M


def wolfram_wall_large(v=1):
    M = Model(); g = 'main'
    M.add(g, prism(cham_rect(0.995, 0.995, 0.16), 0.0, 0.10, top_poly=cham_rect(0.985, 0.985, 0.16)), 'tung')
    plate(M, g, cham_rect(0.96, 0.96, 0.20), cham_rect(0.85, 0.85, 0.17), 0.10, 0.26, 'metal', 'tung')
    for sx in (-1, 1):                                                                 # corner L-brackets
        for sy in (-1, 1):
            L = P([(sx*0.80, sy*0.80), (sx*0.38, sy*0.80), (sx*0.38, sy*0.66), (sx*0.66, sy*0.66), (sx*0.66, sy*0.38), (sx*0.80, sy*0.38)])
            M.add(g, prism(L, 0.264, 0.34, 0.94), 'ore_wolf')
            M.add(g, cyl((sx*0.73, sy*0.73, 0.34), (sx*0.73, sy*0.73, 0.38), 0.055, 0.04, n=8), 'steel')
            for (x, y) in ((sx*0.50, sy*0.73), (sx*0.73, sy*0.50)):
                M.add(g, cyl((x, y, 0.34), (x, y, 0.365), 0.035, n=8), 'steel')
    if v == 1:
        plate(M, g, cham_rect(0.54, 0.54, 0.14), cham_rect(0.45, 0.45, 0.11), 0.264, 0.38, 'metal', 'ore_wolf')
        plate(M, g, cham_rect(0.33, 0.33, 0.09), cham_rect(0.26, 0.26, 0.07), 0.384, 0.46, 'metal', 'tung')
        M.add(g, B(-0.17, 0.17, -0.03, 0.03, 0.46, 0.47), 'cobalt')
        bolts(M, g, [(q, -0.40) for q in (-0.40, 0.40)] + [(q, 0.40) for q in (-0.40, 0.40)], 0.384, r=0.03, m='steel')
    else:                                                                              # diamond boss, laminated
        plate(M, g, ngon(4, 0.66, rot=0), ngon(4, 0.55, rot=0), 0.264, 0.38, 'metal', 'ore_wolf')
        plate(M, g, ngon(4, 0.40, rot=0), ngon(4, 0.32, rot=0), 0.384, 0.46, 'metal', 'tung')
        for y in (-0.10, 0.10):
            seam(M, g, (-0.16, y), (0.16, y), 0.464, m='bore', w=0.03, h=0.006)
        bolts(M, g, [(0.0, -0.50), (0.0, 0.50), (-0.50, 0.0), (0.50, 0.0)], 0.384, r=0.03, m='steel')
    return M


# ================================================================== driver
UEF_TOP = heatmask({'glow': 1.0, 'bhot': 1.0, 'copper': 0.7})
CY_TOP = heatmask({'rglow': 1.0, 'rhot': 1.0})
NANITE_TOP = heatmask({'nanite': 1.0, 'rglow': 0.4})
# variant counts must match "variants" in the wall JSON (Block.load reads name1..nameN)
WALLS = (('steel-wall', steel_wall, 32, 3, False), ('steel-wall-large', steel_wall_large, 64, 2, False),
         ('wolfram-wall', wolfram_wall, 32, 3, True), ('wolfram-wall-large', wolfram_wall_large, 64, 2, True))
VARIANTS = {}


def block(name, M, canvas, topfn, d=DEF):
    from rend import heat_sprite
    main, hm = layer(M, ['main'], canvas, heat=topfn)
    save(main, d, name)
    save(heat_sprite(hm), d, f'{name}-top')
    save(main, d, f'{name}-full')
    FULL[name] = np.asarray(main)
    print(f'{name:18s} {M.ntri():6d} tris  {canvas}px', flush=True)


def wall(name, fn, canvas, nvar, full):
    """name (icon / `-full` where it existed before) + name1..nameN variants; variant 1 == icon."""
    VARIANTS[name] = []
    for v in range(1, nvar+1):
        M = fn(v)
        a, _ = layer(M, ['main'], canvas)
        save(a, WAL, f'{name}{v}')
        VARIANTS[name].append(np.asarray(a))
        if v == 1:
            save(a, WAL, name)
            if full:
                save(a, WAL, f'{name}-full')
            FULL[name] = np.asarray(a)
        print(f'{name+str(v):18s} {M.ntri():6d} tris  {canvas}px', flush=True)


def wall_tiling_sheet(fn='g_defense-wall-rows.png', sc=3):
    """Mixed rows of 1x1/2x2 walls with game-like variant picks, to check that edges tile cleanly."""
    from PIL import Image
    rows = (('steel-wall', 'steel-wall-large'), ('wolfram-wall', 'wolfram-wall-large'))
    W, H = 12, 3
    out = Image.new('RGBA', (W*32*sc+24, len(rows)*(H*32*sc+16)+8), (40, 44, 52, 255))
    for r, (small, large) in enumerate(rows):
        y0 = 8+r*(H*32*sc+16)
        occ = set()
        for (tx, ty) in ((0, 1), (4, 0), (8, 1)):
            k = (tx*7+ty*3) % len(VARIANTS[large])
            out.alpha_composite(Image.fromarray(VARIANTS[large][k]).resize((64*sc, 64*sc), Image.NEAREST), (12+tx*32*sc, y0+ty*32*sc))
            occ |= {(tx, ty), (tx+1, ty), (tx, ty+1), (tx+1, ty+1)}
        for tx in range(W):
            for ty in range(H):
                if (tx, ty) in occ:
                    continue
                k = (tx*31+ty*17+r) % len(VARIANTS[small])
                out.alpha_composite(Image.fromarray(VARIANTS[small][k]).resize((32*sc, 32*sc), Image.NEAREST), (12+tx*32*sc, y0+ty*32*sc))
    p = os.path.join(QA, fn)
    out.convert('RGB').save(p)
    return p


def main():
    block('shield-emitter', shield_emitter(), 64, UEF_TOP)
    block('ed-shield', ed_shield(), 64, CY_TOP)
    block('pulse-shield', pulse_shield(), 96, UEF_TOP)
    block('nanite-repairer', nanite_repairer(), 64, NANITE_TOP)
    for name, fn, canvas, nvar, full in WALLS:
        wall(name, fn, canvas, nvar, full)
    print(qa_sheet(['shield-emitter', 'ed-shield', 'pulse-shield', 'nanite-repairer'], 'g_defense-blocks.png', sc=3))
    print(qa_sheet(['steel-wall', 'steel-wall-large', 'wolfram-wall', 'wolfram-wall-large'], 'g_defense-walls.png', sc=4))
    print(wall_tiling_sheet())


if __name__ == '__main__':
    main()
