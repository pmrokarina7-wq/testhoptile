"""Hero-level remakes of the direct-fire / anti-air line (art workstream g_turrets).

    .venv/bin/python tools/art/g_turrets.py [name ...]

Rivet (T1 UEF twin MG, 2x2), Sparrow (T1 UEF twin flak, 2x2), Lash (T2 Cybran twin pulse laser, 2x2),
Hydra (T3 Cybran 8-cell missile battery, 3x3), Wasp (T3 Cybran quad-rail AA launcher, 3x3).
Groups: base (static), body (rotating head), barrel (recoiling RegionPart "-barrel").
SPEC[name] holds the numbers the block JSON depends on: shootY (muzzle, world units) and the
ShootAlternate spread (distance between the two barrel axes, world units)."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from geom import *  # noqa: E402,F401
from mats import Model, MID  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
from hero import *  # noqa: E402,F401
import export  # noqa: E402
from rend import dilate  # noqa: E402

SPEC = {}


def B(x0, x1, y0, y1, z0, z1):
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def missile(M, g, x, y0, y1, z, r, body='metal_light', tip='red_armor', band='red_armor', fin='hull_mid', fins=True):
    """Missile lying along +Y: motor nozzle, body, warning band, nose cone, cruciform tail fins."""
    L = y1 - y0
    yn = y1 - L * 0.24
    M.add(g, cyl((x, y0, z), (x, y0 + 0.035, z), r * 0.70, r * 0.92, n=12), 'hull_dark')
    M.add(g, cyl((x, y0 + 0.035, z), (x, yn, z), r, n=12), body)
    M.add(g, cyl((x, yn - 0.06, z), (x, yn - 0.035, z), r * 1.04, n=12), band)
    M.add(g, cyl((x, yn, z), (x, y1, z), r, r * 0.18, n=12), tip)
    if fins:
        fw, fl = r * 1.3, L * 0.22
        for s in (-1, 1):
            p = ccw([(x + s * r * 0.8, y0 + 0.03), (x + s * (r + fw), y0 + 0.03), (x + s * (r + fw), y0 + fl * 0.45), (x + s * r * 0.8, y0 + fl)])
            M.add(g, prism(p, z - 0.01, z + 0.01), fin)
        M.add(g, B(x - 0.01, x + 0.01, y0 + 0.03, y0 + fl, z + r * 0.8, z + r + fw), fin)
        for s in (-1, 1):                                         # canards
            p = ccw([(x + s * r * 0.8, yn - 0.16), (x + s * (r + fw * 0.45), yn - 0.12), (x + s * r * 0.8, yn - 0.08)])
            M.add(g, prism(p, z - 0.008, z + 0.008), fin)


def dish(M, g, c, r, R, ribs=6, face='metal_light', rim='hull_mid', horn='glow', depth=0.35):
    """Parabolic dish of radius r centred at c, oriented by rotation R (local +Z = boresight)."""
    rings = [(0.18 * r, -depth * r), (0.55 * r, -depth * r * 0.55), (r, 0.0)]
    pts = [np.array([(rr * math.cos(a), rr * math.sin(a), dz) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)]) for rr, dz in rings]
    for a, b in zip(pts[:-1], pts[1:]):
        M.add(g, tf(loft(a, b, cap_b=False, cap_t=False), R, c), face)
    M.add(g, tf(loft(pts[0], pts[0] + [0, 0, 0.01]), R, c), face)
    for k in range(22):
        a, b = math.radians(360 * k / 22), math.radians(360 * (k + 1) / 22)
        M.add(g, tf(cyl((r * math.cos(a), r * math.sin(a), 0), (r * math.cos(b), r * math.sin(b), 0), 0.014, n=6), R, c), rim)
    for k in range(ribs):
        a = math.radians(360 * k / ribs + 30)
        M.add(g, tf(cyl((0.2 * r * math.cos(a), 0.2 * r * math.sin(a), -depth * r), (r * math.cos(a), r * math.sin(a), 0.004), 0.008, n=5), R, c), rim)
    for k in range(3):
        a = math.radians(120 * k + 90)
        M.add(g, tf(cyl((0.95 * r * math.cos(a), 0.95 * r * math.sin(a), 0), (0, 0, r * 0.62), 0.007, n=5), R, c), 'metal')
    M.add(g, tf(cyl((0, 0, r * 0.58), (0, 0, r * 0.70), 0.032, 0.022, n=10), R, c), horn)


# ================================================================== Rivet - T1 UEF twin machine gun (2x2)
def rivet():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 1.0, top=0.18)
    g = 'body'
    hull = cham_rect(0.50, 0.58, 0.16, cy=-0.12)
    M.add(g, prism(hull, z, z + 0.16, 0.94), 'hull_mid')
    M.add(g, prism(scale_poly(hull, 0.88), z + 0.16, z + 0.21, 0.96), 'hull_light')
    top = z + 0.21
    zg = top + 0.15
    # gun mantlet: chamfered armour block with hazard stripes, the guns ride on top of it
    M.add(g, prism(cham_rect(0.29, 0.14, 0.05, cy=0.36), top - 0.02, top + 0.07, 0.90), 'hull_light')
    bolts(M, g, [(-0.255, 0.26), (0.255, 0.26), (-0.255, 0.46), (0.255, 0.46)], top + 0.07, r=0.015)
    for s in (-1, 1):
        cx = s * 0.52
        # ammunition can (one per gun) with lid, straps, stencil band, handle and belt feed
        M.add(g, B(cx - 0.13, cx + 0.13, -0.52, 0.10, z + 0.02, top + 0.10), 'steel')
        M.add(g, B(cx - 0.115, cx + 0.115, -0.50, 0.08, top + 0.10, top + 0.115), 'hull_mid')
        M.add(g, B(cx - 0.115, cx + 0.115, 0.0, 0.05, top + 0.115, top + 0.125), 'yellow')
        for y in (-0.42, -0.18):
            M.add(g, B(cx - 0.135, cx + 0.135, y - 0.02, y + 0.02, z + 0.02, top + 0.122), 'hull_dark')
        M.add(g, tube_path([(cx + s * 0.03, -0.36, top + 0.12), (cx + s * 0.03, -0.36, top + 0.16), (cx + s * 0.03, -0.24, top + 0.16), (cx + s * 0.03, -0.24, top + 0.12)], 0.012, n=6), 'metal_light')
        M.add(g, B(cx - s * 0.115, cx - s * 0.03, -0.22, -0.02, top + 0.115, top + 0.13), 'vent')   # belt mouth
        for i in range(6):                                          # brass belt arching into the feed tray
            t = i / 5.0
            bx = cx - s * (0.06 + t * 0.20); by = -0.17 + t * 0.15
            bz = top + 0.15 + math.sin(t * math.pi) * 0.05 + t * 0.03
            M.add(g, cyl((bx, by - 0.06, bz), (bx, by + 0.05, bz), 0.027, n=8), 'copper')
            M.add(g, cyl((bx, by + 0.05, bz), (bx, by + 0.09, bz), 0.027, 0.008, n=8), 'metal_light')
            M.add(g, B(bx - 0.022, bx + 0.022, by - 0.045, by - 0.025, bz - 0.03, bz + 0.03), 'hull_dark')
        chevrons(M, g, s * 0.38, 0.34, top, 0.16, 0.12, n=3)
        light(M, g, s * 0.40, 0.17, top - 0.02, 0.04, 0.03)
        M.add(g, cyl((s * 0.30, -0.64, top - 0.06), (s * 0.30, -0.64, top + 0.08), 0.045, n=10), 'metal')
        M.add(g, cyl((s * 0.30, -0.64, top + 0.08), (s * 0.30, -0.64, top + 0.09), 0.055, n=10), 'hull_dark')
        M.add(g, cyl((s * 0.30, -0.64, top + 0.09), (s * 0.30, -0.64, top + 0.095), 0.032, n=8), 'heat')
    # static gun cradle between the receivers (stays put while the guns recoil)
    M.add(g, B(-0.11, 0.11, -0.30, 0.24, top - 0.02, zg + 0.0), 'hull_dark')
    M.add(g, B(-0.08, 0.08, -0.26, 0.20, zg, zg + 0.015), 'hull_mid')
    M.add(g, B(-0.03, 0.03, -0.20, -0.12, zg + 0.015, zg + 0.025), 'glow')
    M.add(g, B(-0.03, 0.03, 0.06, 0.14, zg + 0.015, zg + 0.025), 'yellow')
    # rear deck: cooling grille, antenna, seams
    grille(M, g, 0, -0.56, top, 0.36, 0.11, n=6, glow='glow')
    antenna(M, g, (0.16, -0.68, top), (0.22, -0.92, top + 0.40))
    seam(M, g, (-0.36, -0.10), (0.36, -0.10), top, w=0.02, h=0.01)
    bolts(M, g, [(-0.38, -0.62), (0.38, -0.62), (-0.38, 0.20), (0.38, 0.20)], top, r=0.016)
    # ---- two machine guns, each its own recoiling part (alternate fire)
    for x in (-0.19, 0.19):
        s = 1 if x > 0 else -1
        g = 'barrel_l' if s < 0 else 'barrel_r'
        M.add(g, B(x - 0.075, x + 0.075, -0.36, 0.24, zg - 0.07, zg + 0.06), 'hull_light')        # receiver
        M.add(g, B(x - 0.06, x + 0.06, -0.32, 0.20, zg + 0.06, zg + 0.085), 'hull_mid')           # top cover
        M.add(g, B(x - 0.05, x + 0.05, 0.08, 0.16, zg + 0.085, zg + 0.095), 'yellow')
        M.add(g, B(x + s * 0.075, x + s * 0.105, -0.12, 0.08, zg - 0.03, zg + 0.05), 'metal')        # feed tray
        M.add(g, B(x - 0.05, x + 0.05, -0.44, -0.36, zg - 0.05, zg + 0.04), 'metal')              # buffer
        M.add(g, B(x - 0.025, x + 0.025, -0.48, -0.44, zg - 0.03, zg + 0.02), 'hull_dark')
        bolts(M, g, [(x - 0.035, -0.27), (x + 0.035, -0.27), (x - 0.035, 0.0), (x + 0.035, 0.0)], zg + 0.085, r=0.011)
        for k in range(8):                                                                        # perforated jacket
            y = 0.24 + k * 0.075
            M.add(g, cyl((x, y, zg), (x, y + 0.05, zg), 0.066, n=14), 'metal')
            M.add(g, cyl((x, y + 0.05, zg), (x, y + 0.075, zg), 0.054, n=14), 'vent')
        M.add(g, cyl((x, 0.84, zg), (x, 0.87, zg), 0.072, n=14), 'hull_mid')
        M.add(g, cyl((x, 0.87, zg), (x, 1.10, zg), 0.034, n=12), 'metal_light')
        M.add(g, cyl((x, 0.98, zg), (x, 1.01, zg), 0.042, n=12), 'hull_mid')
        M.add(g, cyl((x, 1.10, zg), (x, 1.24, zg), 0.05, n=12), 'hull_dark')                     # flash hider
        for a in (45, 135, 225, 315):
            M.add(g, tf(B(-0.012, 0.012, 1.12, 1.23, 0.043, 0.055), ry(a), (x, 0, zg)), 'metal')
        M.add(g, cyl((x, 1.24, zg), (x, 1.25, zg), 0.03, n=10), 'bore')
        M.add(g, B(x - 0.04, x + 0.04, 0.60, 0.66, zg - 0.03, zg + 0.075), 'hull_mid')           # front sight block
        M.add(g, B(x - 0.03, x + 0.03, 0.61, 0.65, zg + 0.075, zg + 0.085), 'yellow')
    SPEC['rivet'] = dict(shootY=1.25 * 8, spread=0.38 * 8)
    return M


heat_rivet = heat_grad(0.50, 1.25, mats=('metal', 'metal_light', 'hull_dark', 'bore', 'vent', 'hull_mid'), always=())


# ================================================================== Sparrow - T1 UEF twin flak, Gepard layout (2x2)
def sparrow():
    M = Model(); g = 'base'
    z = uef_hero_base(M, g, 1.0, top=0.18)
    g = 'body'
    hull = cham_rect(0.31, 0.52, 0.10, cy=-0.10)
    M.add(g, prism(hull, z, z + 0.20, 0.94), 'hull_mid')
    M.add(g, prism(scale_poly(hull, 0.88), z + 0.20, z + 0.26, 0.95), 'hull_light')
    top = z + 0.26
    for s in (-1, 1):
        M.add(g, B(s * 0.26, s * 0.34, -0.20, 0.16, z, top - 0.04), 'hull_light')                             # trunnion bracket
        M.add(g, cyl((s * 0.29, -0.02, top - 0.08), (s * 0.34, -0.02, top - 0.08), 0.10, n=16), 'metal')       # trunnion
        M.add(g, B(s * 0.20, s * 0.29, -0.52, -0.24, top - 0.005, top + 0.012), 'yellow')                     # feed hatches
        M.add(g, B(s * 0.21, s * 0.28, -0.50, -0.26, top + 0.012, top + 0.02), 'hull_mid')
        # sloped front cheek armour with yellow inlay
        zf = (lambda x, y: top + 0.03 - (y - 0.06) * 0.30)
        slope_plate(M, g, [(s * 0.08, 0.06), (s * 0.27, 0.06), (s * 0.27, 0.30), (s * 0.14, 0.38)], zf, 'hull_light', thick=0.08, inlay='yellow', isc=0.55, ih=0.014)
        light(M, g, s * 0.22, 0.36, top - 0.04, 0.03, 0.03)
        M.add(g, cyl((s * 0.22, -0.66, top - 0.10), (s * 0.22, -0.66, top + 0.04), 0.04, n=10), 'metal')
        M.add(g, cyl((s * 0.22, -0.66, top + 0.04), (s * 0.22, -0.66, top + 0.045), 0.026, n=8), 'heat')
    # commander hatch with periscopes
    M.add(g, cyl((0.12, -0.12, top - 0.01), (0.12, -0.12, top + 0.06), 0.09, n=16), 'hull_mid')
    M.add(g, cyl((0.12, -0.12, top + 0.06), (0.12, -0.12, top + 0.075), 0.065, n=16), 'hull_light')
    for a in (60, 120):
        M.add(g, tf(cbox(0.085, 0, top + 0.07, 0.03, 0.05, 0.03), rz(a), (0.12, -0.12, 0)), 'glass')
    M.add(g, B(-0.22, -0.02, -0.16, -0.10, top, top + 0.012), 'vent')
    seam(M, g, (-0.24, 0.06), (0.24, 0.06), top, w=0.02, h=0.01)
    bolts(M, g, [(-0.24, 0.32), (0.24, 0.32), (-0.24, -0.58), (0.24, -0.58)], top, r=0.015)
    # tracking radar: dish on a pedestal at the front, looking forward-up
    M.add(g, cyl((0, 0.24, top - 0.01), (0, 0.24, top + 0.08), 0.06, n=12), 'hull_dark')
    dish(M, g, (0, 0.26, top + 0.15), 0.16, rx(-32), ribs=6)
    # search radar: wide slotted bar antenna on a mast at the rear
    M.add(g, cyl((0, -0.44, top - 0.01), (0, -0.44, top + 0.16), 0.045, n=12), 'metal')
    R = rx(18); c = (0, -0.46, top + 0.20)
    M.add(g, tf(B(-0.34, 0.34, -0.05, 0.05, -0.035, 0.035), R, c), 'hull_light')
    M.add(g, tf(B(-0.31, 0.31, -0.03, 0.03, 0.035, 0.045), R, c), 'vent')
    for i in range(9):
        xx = -0.28 + i * 0.07
        M.add(g, tf(B(xx - 0.012, xx + 0.012, -0.028, 0.028, 0.035, 0.052), R, c), 'metal_light')
    M.add(g, tf(B(-0.36, 0.36, 0.05, 0.065, -0.03, 0.03), R, c), 'yellow')
    M.add(g, tf(cyl((-0.37, 0, 0), (-0.39, 0, 0), 0.02, n=8), R, c), 'glow')
    M.add(g, tf(cyl((0.37, 0, 0), (0.39, 0, 0), 0.02, n=8), R, c), 'glow')
    # ---- outboard twin flak gun pods, each its own recoiling part (alternate fire)
    for x in (-0.43, 0.43):
        s = 1 if x > 0 else -1
        g = 'gun_l' if s < 0 else 'gun_r'
        pod = cham_rect(0.10, 0.34, 0.045, cx=x, cy=-0.09)
        M.add(g, prism(pod, -0.10, 0.07, 0.94), 'hull_light')                                  # gun pod / cradle
        M.add(g, prism(scale_poly(pod, (0.80, 0.92)), 0.07, 0.09, 0.95), 'hull_mid')
        M.add(g, B(x - 0.06, x + 0.06, 0.12, 0.17, 0.09, 0.10), 'yellow')
        M.add(g, B(x - 0.06, x + 0.06, -0.33, -0.29, 0.09, 0.10), 'yellow')
        bolts(M, g, [(x - 0.045, -0.20), (x + 0.045, -0.20), (x - 0.045, 0.04), (x + 0.045, 0.04)], 0.09, r=0.011)
        M.add(g, B(x + s * 0.085, x + s * 0.115, -0.18, -0.02, -0.06, 0.02), 'copper')           # casing chute
        M.add(g, B(x - s * 0.085, x - s * 0.11, -0.30, 0.10, -0.08, 0.0), 'metal')               # feed chute
        M.add(g, cyl((x, 0.23, 0), (x, 0.44, 0), 0.062, n=16), 'hull_dark')                        # recoil sleeve
        for y in (0.27, 0.38):
            M.add(g, cyl((x, y, 0), (x, y + 0.03, 0), 0.074, n=16), 'metal_light')
        M.add(g, cyl((x, 0.44, 0), (x, 1.04, 0), 0.042, 0.037, n=12), 'metal')
        M.add(g, cyl((x, 0.70, 0), (x, 0.73, 0), 0.045, n=12), 'hull_mid')
        M.add(g, cyl((x, 0.92, 0), (x, 0.95, 0), 0.045, n=12), 'hull_mid')
        muzzle_brake(M, g, 1.04, 0.15, 0.055, x=x, nb=2, trim='yellow', bore_r=0.026, out=0.026)
        M.add(g, B(x - 0.03, x + 0.03, 0.96, 1.02, 0.04, 0.075), 'hull_mid')                          # muzzle-velocity radar
        M.add(g, B(x - 0.02, x + 0.02, 0.97, 1.01, 0.075, 0.082), 'glow')
    pv = (0, -0.02, top - 0.08)
    elevate(M, 22, pv, 'gun_l', 'barrel_l'); elevate(M, 22, pv, 'gun_r', 'barrel_r')
    my, _ = muzzle_world(22, pv, 1.04 + 0.15 + 0.022)
    SPEC['sparrow'] = dict(shootY=my * 8, spread=0.86 * 8)
    return M


heat_sparrow = heat_grad(0.55, 1.10, mats=('metal', 'metal_light', 'hull_dark', 'bore', 'hull_mid'), always=())


# ================================================================== Lash - T2 Cybran twin pulse laser (2x2)
def lash():
    M = Model(); g = 'base'
    z = cy_hero_base(M, g, 2 / 3)
    g = 'body'
    hull = mirror_half([(0, 0.40), (0.22, 0.40), (0.40, 0.12), (0.44, -0.32), (0.30, -0.62), (0, -0.70)])
    M.add(g, prism(hull, z, z + 0.16, 0.90), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.80, (0, 0)), z + 0.16, z + 0.22, 0.92), 'hull_mid')
    top = z + 0.22
    for s in (1, -1):
        # swept wing armour (Scorpion family): silver plate, red inlay, red tip light
        W = [(0.32, 0.24), (0.56, 0.04), (0.70, -0.52), (0.62, -0.76), (0.46, -0.52), (0.32, -0.14)]
        zw = (lambda x, y: top - 0.02 - (abs(x) - 0.32) * 0.42)
        slope_plate(M, g, [(s * x, y) for x, y in W], zw, 'hull_light', thick=0.12, inlay='red_armor', isc=0.62, ih=0.02)
        M.add(g, cbox(s * 0.63, -0.64, zw(0.63, 0) + 0.01, 0.04, 0.08, 0.03), 'rglow')
        bolts_on(M, g, [(s * 0.36, 0.12), (s * 0.40, -0.30), (s * 0.56, -0.50)], zw, r=0.016)
        # forward claw plate
        cp = [(s * 0.30, 0.30), (s * 0.44, 0.20), (s * 0.48, 0.02), (s * 0.36, 0.06)]
        M.add(g, prism(P(cp), top - 0.10, top + 0.02, 0.85), 'red_armor')
        cable(M, g, [(s * 0.24, -0.44, top + 0.08), (s * 0.27, -0.16, top + 0.10), (s * 0.22, 0.02, top + 0.12)], 0.022)
    # capacitor bank (glows with charge: body heat layer)
    for y in (-0.20, -0.38):
        M.add(g, cyl((-0.22, y, top + 0.06), (0.22, y, top + 0.06), 0.068, n=14), 'hull_dark')
        for x in np.arange(-0.17, 0.18, 0.068):
            M.add(g, cyl((x - 0.02, y, top + 0.06), (x + 0.02, y, top + 0.06), 0.076, n=14), 'coil')
        for sx in (-0.23, 0.23):
            M.add(g, cyl((sx - 0.015, y, top + 0.06), (sx + 0.015, y, top + 0.06), 0.085, n=14), 'red_armor')
    # heat-sink fins + rear vent glow
    for i in range(7):
        x = -0.18 + i * 0.06
        M.add(g, B(x - 0.012, x + 0.012, -0.62, -0.48, top - 0.03, top + 0.06), 'metal')
    M.add(g, B(-0.21, 0.21, -0.63, -0.47, top - 0.04, top - 0.02), 'rglow')
    antenna(M, g, (-0.20, -0.56, top), (-0.26, -0.80, top + 0.30), tip='rglow')
    # static emitter yoke between the prongs, with the charge core light
    ze = top + 0.15
    M.add(g, prism(P([(-0.12, -0.12), (0.12, -0.12), (0.14, 0.10), (0.08, 0.28), (-0.08, 0.28), (-0.14, 0.10)]), top - 0.02, ze + 0.03, 0.88), 'hull_dark')
    M.add(g, prism(P([(-0.06, -0.06), (0.06, -0.06), (0.04, 0.20), (-0.04, 0.20)]), ze + 0.03, ze + 0.05, 0.9), 'red_armor')
    M.add(g, cbox(0, 0.07, ze + 0.055, 0.03, 0.10, 0.012), 'rglow')
    # ---- twin emitter prongs with coils and focusing lens stacks, each its own recoiling part
    for x in (-0.18, 0.18):
        s = 1 if x > 0 else -1
        g = 'barrel_l' if s < 0 else 'barrel_r'
        hx = [(x - 0.08, -0.16), (x + 0.08, -0.16), (x + 0.09, 0.10), (x + 0.065, 0.42), (x - 0.065, 0.42), (x - 0.09, 0.10)]
        M.add(g, prism(P(hx), ze - 0.07, ze + 0.06, 0.88), 'hull_dark')
        M.add(g, prism(P([(x - 0.055, -0.12), (x + 0.055, -0.12), (x + 0.045, 0.36), (x - 0.045, 0.36)]), ze + 0.06, ze + 0.085, 0.9), 'red_armor')
        M.add(g, B(x - 0.012, x + 0.012, -0.10, 0.30, ze + 0.085, ze + 0.095), 'hull_light')
        coil_jacket(M, g, 0.42, 4, 0.07, 0.06, band='red_armor', coil='coil', x=x, z=ze)
        M.add(g, cyl((x, 0.70, ze), (x, 0.74, ze), 0.072, n=14), 'hull_mid')
        for y, r in ((0.74, 0.058), (0.84, 0.052), (0.93, 0.046)):                              # focusing lens stack
            M.add(g, cyl((x, y, ze), (x, y + 0.05, ze), r * 0.72, n=14), 'metal')
            M.add(g, cyl((x, y + 0.05, ze), (x, y + 0.058, ze), r * 1.30, n=16), 'hull_light')
            M.add(g, cyl((x, y + 0.058, ze), (x, y + 0.072, ze), r * 1.16, n=16), 'rglow')
            M.add(g, cyl((x, y + 0.072, ze), (x, y + 0.08, ze), r * 1.30, n=16), 'hull_light')
        M.add(g, cyl((x, 1.005, ze), (x, 1.07, ze), 0.036, 0.016, n=12), 'rglow')
        M.add(g, prism(P([(x + s * 0.09, 0.02), (x + s * 0.12, 0.08), (x + s * 0.11, 0.52), (x + s * 0.08, 0.60)]), ze - 0.05, ze + 0.04), 'red_armor')
    SPEC['lash'] = dict(shootY=1.07 * 8, spread=0.36 * 8)
    return M


heat_lash = heat_grad(0.62, 1.07, mats=('metal', 'hull_mid', 'glass', 'metal_light'), always=('coil', 'rglow'))
heat_lash_body = (lambda mp, X, Y, g: np.isin(mp, [MID['coil']]).astype(float) * 0.9)


# ================================================================== Hydra - T3 Cybran 8-cell missile battery (3x3)
def hydra():
    M = Model(); g = 'base'
    z = cy_hero_base(M, g, 1.0)
    g = 'body'
    hull = mirror_half([(0, 0.66), (0.22, 0.64), (0.36, 0.32), (0.40, -0.44), (0.30, -0.86), (0, -0.94)])
    M.add(g, prism(hull, z, z + 0.26, 0.90), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.80, (0, 0)), z + 0.26, z + 0.34, 0.92), 'hull_mid')
    top = z + 0.34
    for s in (1, -1):
        sp = [(s * 0.14, 0.24), (s * 0.30, 0.20), (s * 0.32, -0.40), (s * 0.22, -0.62), (s * 0.12, -0.50)]
        zf = (lambda x, y: top + 0.06 - (abs(x) - 0.12) * 0.30)
        slope_plate(M, g, sp, zf, 'hull_light', thick=0.08, inlay='red_armor', isc=0.58, ih=0.018)
        bolts_on(M, g, [(s * 0.17, 0.16), (s * 0.27, -0.36)], zf, r=0.018)
    for i, y in enumerate((0.16, -0.08, -0.32)):
        M.add(g, B(-0.03, 0.03, y - 0.06, y + 0.06, top, top + 0.07), 'red_armor')
        M.add(g, B(-0.015, 0.015, y - 0.04, y + 0.04, top + 0.07, top + 0.08), 'rglow')
    # targeting head with sensor eye
    M.add(g, prism(P([(-0.18, 0.34), (0.18, 0.34), (0.13, 0.66), (-0.13, 0.66)]), top - 0.04, top + 0.10, 0.85), 'hull_light')
    M.add(g, prism(P([(-0.10, 0.40), (0.10, 0.40), (0.07, 0.60), (-0.07, 0.60)]), top + 0.10, top + 0.13, 0.9), 'hull_mid')
    M.add(g, cyl((0, 0.52, top + 0.13), (0, 0.52, top + 0.17), 0.065, 0.05, n=14), 'glass')
    M.add(g, cyl((0, 0.52, top + 0.17), (0, 0.52, top + 0.18), 0.028, n=10), 'rglow')
    # rear magazine drum, exhaust caps, pylons, feed cables
    M.add(g, cyl((-0.30, -0.70, top - 0.06), (0.30, -0.70, top - 0.06), 0.16, n=20), 'metal')
    for x in (-0.20, 0.0, 0.20):
        M.add(g, cyl((x - 0.02, -0.70, top - 0.06), (x + 0.02, -0.70, top - 0.06), 0.175, n=20), 'red_armor')
    for s in (-1, 1):
        M.add(g, cyl((s * 0.30, -0.70, top - 0.06), (s * 0.34, -0.70, top - 0.06), 0.11, n=14), 'hull_dark')
        M.add(g, cyl((s * 0.34, -0.70, top - 0.06), (s * 0.35, -0.70, top - 0.06), 0.05, n=10), 'rglow')
        M.add(g, B(s * 0.30, s * 0.44, -0.30, 0.22, z + 0.02, top - 0.04), 'hull_light')
        cable(M, g, [(s * 0.12, -0.56, top + 0.04), (s * 0.26, -0.48, top + 0.08), (s * 0.40, -0.40, top + 0.04)], 0.028)
    antenna(M, g, (0.16, -0.86, top), (0.24, -1.16, top + 0.40), tip='rglow')
    # ---- two 4-cell pods: hatch covers slid back, missile noses in the open cells (recoiling part)
    g = 'barrel_local'; XS = (-0.72, 0.72)
    for x in XS:
        s = 1 if x > 0 else -1
        pod = cham_rect(0.27, 0.74, 0.08, cx=x, cy=-0.04)
        M.add(g, prism(pod, -0.22, 0.02, 0.97), 'hull_dark')                                      # pod hull
        for xw in (x - 0.245, x + 0.245):
            M.add(g, B(xw - 0.025, xw + 0.025, -0.70, 0.62, 0.02, 0.11), 'hull_mid')                # side walls
            M.add(g, B(xw - 0.008, xw + 0.008, -0.70, 0.60, 0.11, 0.12), 'metal_light')              # hatch rail
        M.add(g, B(x - 0.27, x + 0.27, 0.62, 0.70, -0.20, 0.11), 'hull_mid')                          # front frame
        M.add(g, B(x - 0.014, x + 0.014, -0.10, 0.64, 0.0, 0.08), 'hull_mid')                         # cell divider
        for mx in (x - 0.115, x + 0.115):
            M.add(g, B(mx - 0.095, mx + 0.095, -0.10, 0.62, -0.01, 0.0), 'vent')
            missile(M, g, mx, -0.12, 0.74, 0.055, 0.072, fins=False)
            M.add(g, cyl((mx, 0.60, 0.055), (mx, 0.70, 0.055), 0.095, n=16, caps=False), 'hull_dark')  # tube collar
            M.add(g, cyl((mx, 0.69, 0.055), (mx, 0.705, 0.055), 0.10, n=16), 'red_armor')
        # hatch cover slid back over the rear cells: silver plate, red inlay, hinge bars, ready lights
        M.add(g, prism(cham_rect(0.25, 0.30, 0.06, cx=x, cy=-0.40), 0.11, 0.17, 0.94), 'hull_light')
        M.add(g, prism(cham_rect(0.15, 0.20, 0.04, cx=x, cy=-0.42), 0.17, 0.19, 0.90), 'red_armor')
        M.add(g, B(x - 0.22, x + 0.22, -0.13, -0.09, 0.11, 0.18), 'hull_mid')
        for k in range(4):
            M.add(g, B(x - 0.17 + k * 0.105, x - 0.13 + k * 0.105, -0.115, -0.095, 0.18, 0.19), 'rglow')
        bolts(M, g, [(x - 0.20, -0.64), (x + 0.20, -0.64), (x - 0.20, -0.18), (x + 0.20, -0.18)], 0.17, r=0.018)
        M.add(g, B(x - 0.23, x + 0.23, -0.88, -0.74, -0.18, -0.02), 'hull_mid')                      # back-blast grille
        M.add(g, B(x - 0.20, x + 0.20, -0.86, -0.76, -0.02, 0.0), 'vent')
        for k in range(6):
            M.add(g, B(x - 0.19 + k * 0.076, x - 0.17 + k * 0.076, -0.86, -0.76, 0.0, 0.02), 'metal')
        M.add(g, cyl((x - s * 0.27, -0.02, -0.08), (x - s * 0.33, -0.02, -0.08), 0.10, n=14), 'metal')  # trunnion
        so = [(x + s * 0.27, -0.62), (x + s * 0.35, -0.50), (x + s * 0.35, 0.44), (x + s * 0.27, 0.60)]
        M.add(g, prism(P(so), -0.18, 0.06, 0.85), 'hull_light')                                         # outer armour
        M.add(g, prism(P([(x + s * 0.29, -0.40), (x + s * 0.33, -0.34), (x + s * 0.33, 0.28), (x + s * 0.29, 0.36)]), 0.06, 0.075), 'red_armor')
        for yy in (-0.50, 0.40):
            M.add(g, cbox(x + s * 0.32, yy, 0.07, 0.03, 0.05, 0.02), 'rglow')
    pv = (0, 0.04, top + 0.12); elevate(M, 10, pv)
    my, _ = muzzle_world(10, pv, 0.74)
    SPEC['hydra'] = dict(shootY=my * 8, spread=1.44 * 8)
    return M


def heat_hydra(mp, X, Y, g):
    rear = np.isin(mp, [MID['vent'], MID['metal']]) & (Y < -0.60)
    mouth = np.isin(mp, [MID['hull_dark'], MID['red_armor']]) & (Y > 0.62)
    return np.where(rear, 0.85, 0.0) + np.where(mouth, 0.6, 0.0)


# ================================================================== Wasp - T3 Cybran quad-rail AA launcher (3x3)
def wasp():
    M = Model(); g = 'base'
    z = cy_hero_base(M, g, 1.0)
    g = 'body'
    hull = mirror_half([(0, 0.44), (0.28, 0.42), (0.44, 0.12), (0.46, -0.48), (0.34, -0.88), (0, -0.96)])
    M.add(g, prism(hull, z, z + 0.22, 0.90), 'hull_dark')
    M.add(g, prism(scale_poly(hull, 0.80, (0, 0)), z + 0.22, z + 0.30, 0.92), 'hull_mid')
    top = z + 0.30
    for s in (1, -1):
        W = [(0.40, 0.20), (0.66, -0.06), (0.82, -0.66), (0.72, -0.94), (0.50, -0.64), (0.42, -0.22)]
        zw = (lambda x, y: top - 0.04 - (abs(x) - 0.40) * 0.40)
        slope_plate(M, g, [(s * x, y) for x, y in W], zw, 'hull_light', thick=0.12, inlay='red_armor', isc=0.62, ih=0.02)
        M.add(g, cbox(s * 0.73, -0.82, zw(0.73, 0) + 0.01, 0.05, 0.10, 0.03), 'rglow')
        bolts_on(M, g, [(s * 0.44, 0.08), (s * 0.50, -0.40), (s * 0.66, -0.60)], zw, r=0.018)
    # phased-array sensor panel on a mast, tilted back, with an emitter grid
    M.add(g, cyl((0, -0.66, top - 0.01), (0, -0.66, top + 0.20), 0.07, n=12), 'metal')
    M.add(g, B(-0.12, 0.12, -0.58, -0.46, top - 0.01, top + 0.12), 'hull_mid')
    M.add(g, B(-0.08, 0.08, -0.56, -0.48, top + 0.12, top + 0.13), 'rglow')
    pc = (0, -0.68, top + 0.26)
    R = rx(-38)
    def SA(T, m): M.add(g, tf(T, R, pc), m)
    SA(B(-0.42, 0.42, -0.22, 0.22, -0.05, 0.0), 'hull_dark')
    SA(B(-0.38, 0.38, -0.19, 0.19, 0.0, 0.012), 'cy_dark')
    for i in range(7):
        for j in range(3):
            xx = -0.33 + i * 0.11; yy = -0.13 + j * 0.13
            SA(B(xx - 0.035, xx + 0.035, yy - 0.04, yy + 0.04, 0.012, 0.026), 'rglow' if (i + j) % 2 == 0 else 'red_armor')
    SA(B(-0.44, 0.44, 0.19, 0.24, -0.06, 0.03), 'red_armor')
    SA(B(-0.44, 0.44, -0.24, -0.19, -0.06, 0.03), 'hull_light')
    for sx in (-0.42, 0.42):
        SA(B(sx - 0.035, sx + 0.035, -0.24, 0.24, -0.06, 0.04), 'hull_light')
    # secondary sensor dome + cables
    M.add(g, cyl((0.24, 0.16, top - 0.01), (0.24, 0.16, top + 0.08), 0.09, 0.08, n=16), 'hull_light')
    M.add(g, sphereish((0.24, 0.16, top + 0.08), 0.065, n=12), 'glass')
    M.add(g, cbox(0.24, 0.22, top + 0.13, 0.04, 0.02, 0.02), 'rglow')
    cable(M, g, [(-0.10, -0.30, top + 0.05), (-0.20, -0.05, top + 0.10), (-0.30, 0.10, top + 0.10)], 0.024)
    cable(M, g, [(0.10, -0.30, top + 0.05), (0.22, -0.05, top + 0.06)], 0.024)
    # ---- quad launch rails (two twin-rail beams) with exposed missiles (recoiling part)
    g = 'barrel_local'; XS = (-0.52, 0.52)
    M.add(g, cyl((-0.70, 0.0, -0.04), (0.70, 0.0, -0.04), 0.07, n=14), 'metal')                          # cross shaft
    M.add(g, B(-0.28, 0.28, -0.14, 0.14, -0.12, 0.06), 'hull_mid')
    M.add(g, B(-0.18, 0.18, -0.10, 0.10, 0.06, 0.08), 'red_armor')
    M.add(g, B(-0.04, 0.04, -0.06, 0.06, 0.08, 0.09), 'rglow')
    for x in XS:
        s = 1 if x > 0 else -1
        M.add(g, B(x - 0.19, x + 0.19, -0.42, 0.32, -0.10, 0.0), 'hull_dark')                          # launcher spine
        M.add(g, prism(P([(x - 0.17, 0.32), (x + 0.17, 0.32), (x + 0.11, 1.10), (x - 0.11, 1.10)]), -0.08, -0.01), 'hull_mid')
        M.add(g, B(x - 0.19, x + 0.19, -0.50, -0.42, -0.10, 0.04), 'metal')
        for rx_ in (x - 0.095, x + 0.095):
            M.add(g, B(rx_ - 0.02, rx_ + 0.02, -0.40, 1.12, 0.0, 0.03), 'metal_light')                  # rail
            missile(M, g, rx_, -0.32, 1.16, 0.09, 0.056)
            for yy in (0.10, 0.66):
                M.add(g, B(rx_ - 0.03, rx_ + 0.03, yy, yy + 0.06, 0.0, 0.05), 'hull_dark')                # shoes
            M.add(g, cyl((rx_, -0.50, -0.02), (rx_, -0.54, -0.02), 0.045, n=10), 'rglow')
        so = [(x + s * 0.19, -0.46), (x + s * 0.25, -0.38), (x + s * 0.25, 0.26), (x + s * 0.19, 0.38)]
        M.add(g, prism(P(so), -0.12, 0.08, 0.85), 'hull_light')                                         # outer cheek
        M.add(g, prism(P([(x + s * 0.205, -0.32), (x + s * 0.235, -0.26), (x + s * 0.235, 0.18), (x + s * 0.205, 0.24)]), 0.08, 0.095), 'red_armor')
        hydraulic(M, g, x - s * 0.25, -0.06, -0.38, 0.0, 0.20, r=0.04)
    pv = (0, 0.04, top + 0.16); elevate(M, 24, pv)
    my, _ = muzzle_world(24, pv, 1.16)
    SPEC['wasp'] = dict(shootY=my * 8, spread=1.04 * 8)
    return M


def heat_wasp(mp, X, Y, g):
    return np.where(np.isin(mp, [MID['hull_dark'], MID['metal'], MID['rglow']]) & (Y < -0.30), 0.8, 0.0)


# ================================================================== driver
D = 'blocks/turrets'
TWIN = (('-barrel-l', 'barrel_l'), ('-barrel-r', 'barrel_r'))
ASSETS = [
    # name, model, base px, body px, part heat, body heat (None -> no body -heat sprite), twin (per-gun parts)
    ('rivet', rivet, 64, 96, heat_rivet, None, True),
    ('sparrow', sparrow, 64, 96, heat_sparrow, None, True),
    ('lash', lash, 64, 96, heat_lash, heat_lash_body, True),
    ('hydra', hydra, 96, 128, heat_hydra, None, False),
    ('wasp', wasp, 96, 128, heat_wasp, None, False),
]


def turret_twin(name, M, bc, tc, heat):
    """export.turret(parts=True) for two independently recoiling guns (RegionPart recoilIndex 0 = left, 1 = right):
    -base, body + -outline, -barrel-l / -barrel-r (+ -outline, -heat) and the composed -full icon."""
    groups = [g for _, g in TWIN]
    base, _ = export.layer(M, ['base'], bc)
    body, _ = export.layer(M, ['body'], tc, casters=['body'] + groups)
    export.save(base, D, f'{name}-base')
    export.save(body, D, name)
    export.save(export.outline(body), D, f'{name}-outline')
    off = (tc - bc) // 2
    f = export.over(export.blank(tc), base, off, off)
    f = export.over(f, export.outline(body))
    f = export.over(f, body)
    for suffix, g in TWIN:
        p, hp = export.layer(M, [g], tc, heat)
        export.save(p, D, f'{name}{suffix}')
        export.save(export.outline(p), D, f'{name}{suffix}-outline')
        export.save(export.heat_sprite(hp), D, f'{name}{suffix}-heat')
        f = export.over(f, export.outline(p))
        f = export.over(f, p)
    export.save(f, D, f'{name}-full')
    export.FULL[name] = np.asarray(f)


def body_heat(name, M, tc, fn, parts):
    """Body -heat sprite (DrawTurret draws it above the parts), masked where a part covers it."""
    _, hb = export.layer(M, ['body'], tc, fn, casters=['body'] + parts)
    for g in parts:
        p, _ = export.layer(M, [g], tc)
        hb[dilate(p[..., 3] > 0, 2)] = 0
    export.save(export.heat_sprite(hb), D, f'{name}-heat')


def main(names=None):
    for name, fn, bc, tc, heat, bheat, twin in ASSETS:
        if names and name not in names:
            continue
        M = fn()
        if twin:
            turret_twin(name, M, bc, tc, heat)
            parts, made = [g for _, g in TWIN], [s for s, _ in TWIN]
        else:
            export.turret(name, M, bc, tc, heat, parts=True)
            parts, made = ['barrel'], ['-barrel']
        if bheat is not None:
            body_heat(name, M, tc, bheat, parts)
            made.append('-heat')
        # drop layers this asset no longer uses (old body heat, the other part layout)
        for suf in ('-heat', '-barrel', '-barrel-l', '-barrel-r'):
            if suf not in made:
                for tail in ('', '-outline', '-heat'):
                    stale = os.path.join(export.SPR, D, f'{name}{suf}{tail}.png')
                    if suf == '-heat' and tail:
                        continue
                    if os.path.exists(stale):
                        os.remove(stale)
        sp = SPEC[name]
        print(f'{name:8s} tris {M.ntri():6d} ' + ' '.join(f'{k}={sum(len(T) for T, _ in M.parts.get(k, []))}' for k in ['base', 'body'] + parts)
              + f'  shootY={sp["shootY"]:.2f} spread={sp["spread"]:.2f}')
    print('sheet:', export.qa_sheet([a[0] for a in ASSETS if a[0] in export.FULL], 'g_turrets.png', sc=3))


if __name__ == '__main__':
    main(sys.argv[1:])
