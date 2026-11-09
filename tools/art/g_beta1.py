"""Beta-1 art workstream (2.5.0-alpha4): T1-T4 economy and logistics gaps from the plan (TZ 2.4).

    .venv/bin/python tools/art/g_beta1.py [name ...]     (no args = everything)

UEF (blue-grey steel, yellow trim, blue glow): prospector drill, heat engine, hydrocarbon plant, heavy mass
driver, cargo hub, cargo receiver. Cybran (black, red armour, red glow): nanite vat, lance drill.
Plus icons for molten iron and nanite slurry and wall-ore crystals for iridite and tritium ice.
How v146 composes the layers:
  prospector-drill   Drill: main, -rotator (spinSprite: C4 symmetric), -top (static cap), vanilla item marker
  lance-drill        BeamDrill: main (static), -top (rotated with the block, faces +x), beams, -glow (rotated)
  heavy-driver       MassDriver: -base (static), main = head (rotation - 90, so it faces +y), baked outline
  nanite-vat         -bottom, DrawLiquidTile (slurry), main (open vat), -glow
  cargo-receiver     main, -top tinted with the configured item colour (shaded white lumps in the bin)
1.0 = one tile, Z up, origin = block centre.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *  # noqa: E402,F401,F403
from mats import Model, MID  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
from hero import P, grille, cable, seam, bolts_R, buttress, uef_hero_base, cy_hero_base, slope_plate, coil_jacket  # noqa: E402
import rend  # noqa: E402
from rend import outline, heat_sprite, over  # noqa: E402
from export import save, layer, FULL, qa_sheet, matfn  # noqa: E402
import g_industry_a as IA  # noqa: E402
import g_industry_b as IB  # noqa: E402

rend.add_material('oil', ['0a0806', '120e0a', '1b1610', '252016', '302a1e', '3e3628'])
rend.add_material('nanite', ['1c4a26', '2a6a36', '3c8c4a', '56b064', '78d282', 'a8f2b0'])
rend.add_material('nglow', ['2a8a3a', '3caa4c', '5cc868', '84f491', 'b0ffbc', 'e0ffe6'], glow=True)

B = IA.B
CRA, PWR, DRL, DIS, UNI = 'blocks/crafting', 'blocks/power', 'blocks/drills', 'blocks/distribution', 'blocks/units'


def plate2(M, g, h, c, top, mid='hull_mid'):
    """Two-tier chamfered UEF floor plate; returns the top height."""
    M.add(g, prism(cham_rect(h * 0.985, h * 0.985, c), 0.0, 0.09, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(h * 0.90, h * 0.90, c * 1.05), 0.09, top, 0.95), mid)
    return top


def crate(M, g, x, y, z, s=0.22, rot=0.0, body='hull_light', strap='yellow'):
    R = rz(rot)
    M.add(g, tf(cbox(0, 0, z + s * 0.45, s, s, s * 0.9), R, (x, y, 0)), body)
    M.add(g, tf(cbox(0, 0, z + s * 0.9 + 0.006, s * 0.80, s * 0.80, 0.012), R, (x, y, 0)), 'hull_mid')
    for v in (-s * 0.28, s * 0.28):
        M.add(g, tf(cbox(0, v, z + s * 0.45, s + 0.012, 0.035, s * 0.92), R, (x, y, 0)), strap)


# ================================================================== PROSPECTOR DRILL - T1 UEF (2x2)
def prospector_drill():
    M = Model()
    g = 'main'
    IB.holed(M, g, cham_rect(0.985, 0.985, 0.26), 0.64, 0.0, 0.10, 'hull_dark', n=32)
    IB.holed(M, g, cham_rect(0.90, 0.90, 0.28), 0.68, 0.10, 0.22, 'hull_mid', n=32, r_top=0.72)
    M.add(g, cyl((0, 0, 0.0), (0, 0, 0.03), 0.68, n=32), 'bore')
    IB.annulus(M, g, 0.62, 0.70, 0.04, 0.25, 'metal', n=36, r1t=0.69)
    IB.hazard_ring(M, g, 0.71, 0.79, 0.21, 0.236, n=16, a0=11.25)
    IA.corner_caps(M, g, 0.90, 0.28, 0.22)
    IA.motor(M, g, 0.66, 0.90, 0.0, 0.32, 0.08)
    M.add(g, B(0.60, 0.72, -0.06, 0.06, 0.22, 0.30), 'hull_light')
    grille(M, g, -0.80, 0.0, 0.22, 0.12, 0.40, n=4, glow='glow', R=rz(0))
    bolts(M, g, [(0.0, 0.84), (0.0, -0.84), (-0.84, 0.42), (-0.84, -0.42)], 0.22, r=0.022)
    g = 'rotator'                                        # four-arm auger head (90 deg symmetric for spinSprite)
    M.add(g, cyl((0, 0, 0.03), (0, 0, 0.10), 0.60, 0.57, n=36), 'tung')
    for i in range(24):
        M.add(g, tf(cbox(0.605, 0, 0.07, 0.04, 0.05, 0.07), rz(15 * i)), 'metal')
    for k in range(4):
        R = rz(90 * k)
        M.add(g, tf(prism(P([(0.10, -0.11), (0.56, -0.03), (0.57, 0.06), (0.10, 0.11)]), 0.10, 0.20, 0.85), R), 'hull_light')
        M.add(g, tf(prism(P([(0.16, -0.035), (0.50, 0.0), (0.50, 0.035), (0.16, 0.05)]), 0.20, 0.212), R), 'steel')
        for u in (0.26, 0.40, 0.52):
            M.add(g, tf(cyl((u, -0.04, 0.18), (u, -0.04, 0.235), 0.022, n=6), R), 'metal_light')
    M.add(g, cyl((0, 0, 0.10), (0, 0, 0.24), 0.14, 0.12, n=20), 'metal')
    g = 'top'                                            # gearbox cap on two straps
    for s in (-1, 1):
        M.add(g, IB.beam((s * 0.84, 0, 0.30), (s * 0.18, 0, 0.42), 0.07, 0.05), 'hull_mid')
        M.add(g, IB.beam((s * 0.80, 0, 0.36), (s * 0.24, 0, 0.46), 0.03, 0.012), 'hull_light')
        M.add(g, B(s * 0.78, s * 0.92, -0.10, 0.10, 0.22, 0.34), 'hull_light')
    M.add(g, cyl((0, 0, 0.30), (0, 0, 0.48), 0.21, 0.19, n=24), 'hull_light')
    M.add(g, cyl((0, 0, 0.48), (0, 0, 0.50), 0.14, n=20), 'hull_dark')
    IB.hazard_ring(M, g, 0.14, 0.19, 0.475, 0.485, n=8)
    M.add(g, cyl((0, 0, 0.50), (0, 0, 0.52), 0.05, n=12), 'yellow')
    return M


# ================================================================== HEAT ENGINE - T1 UEF steam generator (2x2)
def heat_engine():
    M = Model()
    g = 'main'
    top = plate2(M, g, 1.0, 0.22, 0.18)
    # firebox (-y): refractory housing, glowing grate under a slatted roof hatch, coal hopper
    M.add(g, prism(cham_rect(0.64, 0.33, 0.08, cy=-0.47), top, top + 0.26, 0.93), 'hull_light')
    zf = top + 0.26
    M.add(g, cbox(-0.16, -0.47, zf + 0.004, 0.62, 0.36, 0.01), 'vent')
    M.add(g, cbox(-0.16, -0.47, zf + 0.010, 0.54, 0.28, 0.01), 'ga_ember')
    for x in np.linspace(-0.40, 0.08, 6):
        M.add(g, cbox(x, -0.47, zf + 0.025, 0.035, 0.32, 0.03), 'metal')
    IA.hopper(M, g, 0.42, -0.47, 0.15, 0.22, zf - 0.06, zf + 0.08, 'cable', 7, n=7, s=0.04)
    # boiler drum (+y) with bands, steam dome and safety valve
    zd = top + 0.25
    M.add(g, cyl((-0.74, 0.42, zd), (0.50, 0.42, zd), 0.25, n=24), 'steel')
    for x in (-0.66, -0.30, 0.06, 0.42):
        M.add(g, cyl((x, 0.42, zd), (x + 0.05, 0.42, zd), 0.265, n=24), 'hull_dark')
    M.add(g, cyl((-0.80, 0.42, zd), (-0.74, 0.42, zd), 0.22, n=24), 'hull_light')
    M.add(g, cyl((-0.12, 0.42, zd + 0.18), (-0.12, 0.42, zd + 0.34), 0.10, 0.09, n=16), 'hull_light')
    M.add(g, cyl((-0.12, 0.42, zd + 0.34), (-0.12, 0.42, zd + 0.37), 0.06, n=12), 'yellow')
    M.add(g, cyl((0.24, 0.42, zd + 0.20), (0.24, 0.42, zd + 0.30), 0.04, n=10), 'copper')
    # chimney (+x, +y corner) and dynamo in the middle strip, fed by a steam line
    cx, cy = 0.72, 0.62
    M.add(g, cyl((cx, cy, top), (cx, cy, top + 0.72), 0.14, 0.12, n=18), 'hull_light')
    M.add(g, cyl((cx, cy, top + 0.66), (cx, cy, top + 0.76), 0.15, n=18), 'hull_dark')
    M.add(g, cyl((cx, cy, top + 0.70), (cx, cy, top + 0.765), 0.09, n=14), 'ga_ember')
    IA.motor(M, g, -0.42, 0.42, -0.02, top + 0.11, 0.09)
    IA.pipe(M, g, [(-0.12, 0.30, zd + 0.10), (-0.20, 0.10, zd + 0.02), (-0.36, -0.02, top + 0.14)], 0.035, m='metal_light')
    IA.wheel(M, g, -0.20, 0.12, zd + 0.06, r=0.05)
    cable(M, g, [(0.42, -0.02, top + 0.12), (0.62, -0.04, top + 0.10), (0.86, -0.06, top + 0.02)], 0.026, ends='yellow')
    IA.corner_caps(M, g, 0.90, 0.24, top, k_list=(1, 2, 3))
    return M


# ================================================================== HYDROCARBON PLANT - T2 UEF oil turbine (3x3)
def hydrocarbon_plant():
    M = Model()
    g = 'main'
    top = plate2(M, g, 1.5, 0.36, 0.20)
    # crude tank (-x, +y): banded wall, shallow cone roof, filler hatch showing oil, warning segment
    tx, ty, tr = -0.55, 0.45, 0.66
    M.add(g, cyl((tx, ty, top), (tx, ty, top + 0.48), tr, n=40), 'hull_light')
    for z in (top + 0.12, top + 0.30):
        M.add(g, cyl((tx, ty, z), (tx, ty, z + 0.04), tr + 0.02, n=40), 'hull_dark')
    M.add(g, cyl((tx, ty, top + 0.48), (tx, ty, top + 0.56), tr, tr * 0.25, n=40), 'metal_light')
    IB.annulus(M, g, tr * 0.80, tr * 0.86, top + 0.495, top + 0.50, 'yellow', n=40, cx=tx, cy=ty)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        seam(M, g, (tx + 0.14 * math.cos(a), ty + 0.14 * math.sin(a)), (tx + 0.50 * math.cos(a), ty + 0.50 * math.sin(a)), top + 0.52, w=0.025, h=0.01)
    M.add(g, cyl((tx + 0.40, ty - 0.30, top + 0.48), (tx + 0.40, ty - 0.30, top + 0.54), 0.10, n=14), 'hull_dark')
    M.add(g, cyl((tx + 0.40, ty - 0.30, top + 0.54), (tx + 0.40, ty - 0.30, top + 0.545), 0.075, n=12), 'oil')
    M.add(g, cyl((tx, ty, top + 0.56), (tx, ty, top + 0.60), 0.09, n=12), 'hull_dark')
    # gas turbine along -y: intake bell, ribbed compressor, burner ring, exhaust duct
    y0, zt = -0.78, top + 0.22
    M.add(g, cyl((-1.25, y0, zt), (-1.05, y0, zt), 0.30, 0.22, n=24), 'metal')
    M.add(g, cyl((-1.05, y0, zt), (-0.30, y0, zt), 0.22, 0.26, n=24), 'hull_light')
    for x in np.linspace(-0.95, -0.40, 6):
        M.add(g, cyl((x, y0, zt), (x + 0.03, y0, zt), 0.255, n=24), 'metal')
    M.add(g, cyl((-0.30, y0, zt), (0.10, y0, zt), 0.32, n=24), 'hull_mid')
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        p = np.array([-0.10, y0 + 0.33 * math.cos(a), zt + 0.33 * math.sin(a)])
        if p[2] > zt - 0.05:
            M.add(g, cyl(p, p + np.array([0, 0.05 * math.cos(a), 0.05 * math.sin(a)]), 0.045, n=10), 'flame')
    M.add(g, cyl((0.10, y0, zt), (0.80, y0, zt), 0.26, 0.20, n=24), 'steel')
    for x in (0.30, 0.60):
        M.add(g, cyl((x, y0, zt), (x + 0.04, y0, zt), 0.24, n=24), 'hull_dark')
    # exhaust stacks (+x) and the duct elbow
    for sy in (-0.78, 0.0):
        M.add(g, cyl((1.05, sy, top), (1.05, sy, top + 0.80), 0.17, 0.15, n=20), 'hull_light')
        M.add(g, cyl((1.05, sy, top + 0.74), (1.05, sy, top + 0.84), 0.18, n=20), 'hull_dark')
        M.add(g, cyl((1.05, sy, top + 0.78), (1.05, sy, top + 0.845), 0.11, n=16), 'heat')
    IA.pipe(M, g, [(0.80, y0, zt), (0.95, y0, zt + 0.06), (1.05, y0, top + 0.40)], 0.12, m='steel')
    IA.pipe(M, g, [(0.40, y0 + 0.26, zt), (0.70, -0.30, top + 0.30), (1.05, -0.02, top + 0.40)], 0.07, m='metal')
    # fuel line tank -> burner with valve, generator housing (+x, +y)
    IA.pipe(M, g, [(tx + 0.40, ty - 0.50, top + 0.10), (-0.10, -0.20, top + 0.14), (-0.10, y0 + 0.30, zt + 0.10)], 0.045, m='ga_slag',
            fl=[((-0.10, -0.20, top + 0.14), (1, 0, 0))])
    IA.wheel(M, g, -0.02, -0.26, top + 0.22, r=0.06)
    M.add(g, prism(cham_rect(0.36, 0.30, 0.08, cx=0.62, cy=0.78), top, top + 0.30, 0.92), 'hull_light')
    grille(M, g, 0.62, 0.78, top + 0.30, 0.46, 0.30, n=6, glow='glow')
    cable(M, g, [(0.62, 0.48, top + 0.24), (0.40, 0.25, top + 0.14), (0.20, 0.05, top + 0.05)], 0.03, ends='yellow')
    IA.corner_caps(M, g, 1.35, 0.38, top, k_list=(0, 3))
    bolts(M, g, [(-1.30, -0.30), (-1.30, 0.30), (1.30, 0.40), (0.0, 1.30)], top, r=0.024)
    return M


# ================================================================== NANITE VAT - T3 Cybran (3x3)
def nanite_vat():
    M = Model()
    g = 'bottom'
    M.add(g, prism(cham_rect(1.47, 1.47, 0.42), 0.0, 0.06, 0.985), 'cy_dark')
    M.add(g, cyl((0, 0, 0.06), (0, 0, 0.07), 0.98, n=48), 'bore')
    for i in range(6):
        M.add(g, tf(B(0.20, 0.95, -0.02, 0.02, 0.07, 0.075), rz(30 + 60 * i)), 'cy_mid')
    g = 'main'
    IB.holed(M, g, cham_rect(1.47, 1.47, 0.42), 0.98, 0.0, 0.14, 'hull_dark', n=48, out_sc=0.985)
    IB.holed(M, g, cham_rect(1.30, 1.30, 0.50), 1.02, 0.14, 0.30, 'cy_mid', n=48, out_sc=0.96, r_top=1.06)
    for i in range(6):                                   # red armour rim segments with glowing gaps
        a0 = 60 * i + 6
        IB.annulus(M, g, 0.98, 1.12, 0.28, 0.38, 'red_armor', n=10, a0=a0, a1=a0 + 48, r1t=1.10, r0t=1.00)
        a = math.radians(a0 + 54)
        M.add(g, cyl((1.05 * math.cos(a), 1.05 * math.sin(a), 0.30), (1.05 * math.cos(a), 1.05 * math.sin(a), 0.34), 0.04, n=8), 'rglow')
    IB.annulus(M, g, 0.94, 0.99, 0.10, 0.31, 'metal', n=48)
    # stirrer bridge with drive motor and glowing status ring
    for s in (-1, 1):
        M.add(g, IB.beam((s * 1.18, 0, 0.36), (s * 0.24, 0, 0.46), 0.09, 0.05, ch=0.02), 'cy_dark')
        M.add(g, IB.beam((s * 1.10, 0, 0.40), (s * 0.30, 0, 0.49), 0.035, 0.012), 'red_armor')
    M.add(g, cyl((0, 0, 0.36), (0, 0, 0.60), 0.24, 0.22, n=28), 'cy_mid')
    M.add(g, cyl((0, 0, 0.60), (0, 0, 0.64), 0.18, n=24), 'hull_dark')
    M.add(g, cyl((0, 0, 0.555), (0, 0, 0.57), 0.235, n=28), 'rglow')
    M.add(g, cyl((0, 0, 0.64), (0, 0, 0.66), 0.07, n=12), 'red_armor')
    # corner modules: silicon hopper, spore hopper, water inlet, control spire
    IA.hopper(M, g, 0, 0, 0.17, 0.17, 0.26, 0.40, 'metal', 21, rim='cy_mid', n=7, s=0.035, R=rz(45), t=(-1.04, -1.04, 0))
    IA.hopper(M, g, 0, 0, 0.17, 0.17, 0.26, 0.40, 'magnet', 22, rim='cy_mid', n=7, s=0.035, R=rz(45), t=(1.04, -1.04, 0))
    IA.pipe(M, g, [(1.18, 1.18, 0.30), (1.02, 1.02, 0.40), (0.90, 0.90, 0.40)], 0.06, m='glass',
            fl=[((1.10, 1.10, 0.36), (1, 1, 0))])
    IA.wheel(M, g, 1.20, 0.98, 0.38, r=0.055, m='red_armor')
    sp = P([(-1.30, 0.86), (-0.86, 1.30), (-1.05, 1.36), (-1.36, 1.05)])
    M.add(g, prism(sp, 0.28, 0.62, 0.70), 'cy_dark')
    M.add(g, prism(scale_poly(sp, 0.5), 0.62, 0.66), 'rglow')
    cable(M, g, [(-1.0, 0.90, 0.50), (-1.16, 0.40, 0.42), (-1.16, 0.06, 0.40)], 0.03, ends='red_armor')
    return M


# ================================================================== LANCE DRILL - T3 Cybran beam drill (3x3)
def lance_drill():
    M = Model()
    z = cy_hero_base(M, 'main', 1.0)
    g = 'top'
    hull = P([(-0.95, -0.66), (0.30, -1.12), (1.22, -1.12), (1.34, -0.95), (1.34, 0.95), (1.22, 1.12), (0.30, 1.12), (-0.95, 0.66)])
    M.add(g, prism(hull, z, z + 0.20, 0.94), 'cy_dark')
    M.add(g, prism(scale_poly(hull, 0.86), z + 0.20, z + 0.26, 0.96), 'cy_mid')
    zt = z + 0.26
    for s in (-1, 1):
        plate = P([(-0.70, s * 0.30), (0.20, s * 0.40), (0.95, s * 0.40), (0.95, s * 0.92), (0.30, s * 0.98), (-0.70, s * 0.56)])
        zf = (lambda x, y: zt + 0.10 - (abs(y) - 0.30) * 0.10)
        slope_plate(M, g, plate, zf, 'red_armor', thick=0.10, inlay='cy_dark', isc=0.6, ih=0.015)
    for y in (-1.0, 0.0, 1.0):                           # one emitter per tile row, aimed along +x
        yy = max(-0.88, min(0.88, y))
        M.add(g, cyl((0.70, yy, zt + 0.08), (1.30, yy, zt + 0.08), 0.15, 0.13, n=18), 'cy_mid')
        for x in (0.82, 0.98, 1.14):
            M.add(g, cyl((x, yy, zt + 0.08), (x + 0.05, yy, zt + 0.08), 0.17, n=18), 'red_armor')
        M.add(g, cyl((1.30, yy, zt + 0.08), (1.40, yy, zt + 0.08), 0.12, 0.10, n=16), 'hull_dark')
        M.add(g, cyl((1.40, yy, zt + 0.08), (1.43, yy, zt + 0.08), 0.08, n=14), 'rglow')
    M.add(g, cyl((-0.35, 0, zt), (-0.35, 0, zt + 0.22), 0.34, 0.30, n=28), 'cy_mid')
    M.add(g, cyl((-0.35, 0, zt + 0.17), (-0.35, 0, zt + 0.19), 0.345, n=28), 'rglow')
    M.add(g, cyl((-0.35, 0, zt + 0.22), (-0.35, 0, zt + 0.26), 0.20, n=20), 'hull_dark')
    M.add(g, prism(P([(-0.45, -0.06), (-0.25, -0.06), (-0.25, 0.06), (-0.45, 0.06)]), zt + 0.26, zt + 0.27), 'rglow')
    for s in (-1, 1):
        cable(M, g, [(-0.10, s * 0.20, zt + 0.12), (0.30, s * 0.30, zt + 0.16), (0.70, s * 0.55, zt + 0.12)], 0.03, ends='red_armor')
        for x in (-0.86, -0.74, -0.62):
            M.add(g, B(x - 0.03, x + 0.03, s * 0.30, s * 0.62, z + 0.10, zt + 0.04), 'metal')
    return M


# ================================================================== HEAVY MASS DRIVER - T4 UEF (4x4)
def heavy_driver():
    M = Model()
    z = uef_hero_base(M, 'base', 2.0)
    g = 'head'
    body = cham_rect(1.10, 0.95, 0.30, cy=-0.55)
    M.add(g, prism(body, z, z + 0.36, 0.95), 'hull_dark')
    M.add(g, prism(cham_rect(0.94, 0.80, 0.26, cy=-0.55), z + 0.36, z + 0.46, 0.96), 'hull_mid')
    zc = z + 0.62
    coil_jacket(M, g, 0.10, 7, 0.30, 0.34, band='yellow', coil='coil', core='hull_dark', x=0, z=zc)
    for s in (-1, 1):                                    # twin guide rails with insulators
        M.add(g, B(s * 0.40, s * 0.56, -1.30, 2.45, zc - 0.22, zc + 0.10), 'steel')
        M.add(g, B(s * 0.44, s * 0.52, -1.25, 2.40, zc + 0.10, zc + 0.13), 'metal_light')
        for y in np.arange(0.0, 2.3, 0.45):
            M.add(g, B(s * 0.36, s * 0.60, y, y + 0.08, zc - 0.26, zc + 0.14), 'hull_light')
        # capacitor banks beside the breech
        for y in (-1.15, -0.80, -0.45):
            M.add(g, cyl((s * 0.86, y, z + 0.46), (s * 0.86, y, z + 0.74), 0.13, n=16), 'metal_light')
            M.add(g, cyl((s * 0.86, y, z + 0.74), (s * 0.86, y, z + 0.78), 0.10, n=14), 'glow')
        cable(M, g, [(s * 0.86, -0.30, z + 0.60), (s * 0.70, 0.05, zc - 0.05), (s * 0.40, 0.25, zc)], 0.035, ends='yellow')
    M.add(g, B(-0.40, 0.40, -1.30, 2.45, zc - 0.24, zc - 0.18), 'bore')
    # breech: item hopper and hazard chevrons
    IA.hopper(M, g, 0, -1.10, 0.30, 0.24, z + 0.46, z + 0.62, 'copper', 41, n=9, s=0.05)
    chevrons(M, g, 0, -1.45, z + 0.36, 0.80, 0.10, n=5)
    # muzzle frame with a glowing acceleration ring
    M.add(g, B(-0.66, 0.66, 2.30, 2.50, zc - 0.30, zc + 0.20), 'hull_light')
    M.add(g, B(-0.30, 0.30, 2.30, 2.52, zc - 0.10, zc + 0.10), 'vent')
    M.add(g, cyl((0, 2.40, zc), (0, 2.53, zc), 0.30, n=24), 'glow')
    M.add(g, cyl((0, 2.38, zc), (0, 2.54, zc), 0.20, n=20), 'bore')
    bolts(M, g, [(-0.58, 2.40), (0.58, 2.40)], zc + 0.20, r=0.03)
    return M


# ================================================================== CARGO HUB - T2 UEF drone pad (3x3)
def cargo_hub():
    M = Model()
    g = 'main'
    top = plate2(M, g, 1.5, 0.38, 0.18)
    M.add(g, cyl((0, 0, top), (0, 0, top + 0.06), 0.82, 0.80, n=48), 'hull_light')
    IB.hazard_ring(M, g, 0.82, 0.94, top - 0.01, top + 0.05, n=24)
    IB.annulus(M, g, 0.52, 0.57, top + 0.06, top + 0.065, 'yellow', n=40)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        light(M, g, 0.70 * math.cos(a), 0.70 * math.sin(a), top + 0.06, 0.05, 0.05)
    for i in range(8):
        a = math.radians(22.5 * 2 * i)
        M.add(g, cyl((0.30 * math.cos(a), 0.30 * math.sin(a), top + 0.06), (0.30 * math.cos(a), 0.30 * math.sin(a), top + 0.075), 0.03, n=8), 'metal_light')
    # crate stack (-x,-y), crane (+x,+y), charging pylon (+x,-y), item intake (-x,+y)
    for (x, y, z, r) in ((-1.10, -0.92, top, 0), (-0.86, -1.12, top, 8), (-1.04, -1.06, top + 0.20, 20)):
        crate(M, g, x, y, z, s=0.21, rot=r)
    px, py = 1.06, 1.06
    M.add(g, cyl((px, py, top), (px, py, top + 0.60), 0.08, n=14), 'hull_light')
    M.add(g, IB.beam((px, py, top + 0.62), (0.50, 0.50, top + 0.70), 0.05, 0.04), 'yellow')
    M.add(g, cyl((0.50, 0.50, top + 0.55), (0.50, 0.50, top + 0.70), 0.012, n=6), 'cable')
    M.add(g, cbox(0.50, 0.50, top + 0.53, 0.10, 0.06, 0.04), 'metal')
    for (x, y) in ((1.10, -0.95), (0.92, -1.12)):
        M.add(g, cyl((x, y, top), (x, y, top + 0.36), 0.07, 0.06, n=12), 'metal_light')
        M.add(g, cyl((x, y, top + 0.36), (x, y, top + 0.40), 0.05, n=10), 'glow')
    cable(M, g, [(1.01, -1.03, top + 0.20), (0.80, -0.80, top + 0.10), (0.62, -0.62, top + 0.06)], 0.025, ends='yellow')
    IA.hopper(M, g, -1.02, 1.02, 0.24, 0.24, top - 0.02, top + 0.16, 'copper', 51, n=8, s=0.04)
    for k in range(4):
        grille(M, g, 0, -1.32, top, 0.70, 0.10, n=7, glow='glow', R=rz(90 * k))
    return M


# ================================================================== CARGO RECEIVER - T2 UEF unload point (2x2)
def cargo_receiver():
    M = Model()
    g = 'main'
    top = plate2(M, g, 1.0, 0.26, 0.16)
    M.add(g, prism(cham_rect(0.50, 0.50, 0.08), top, top + 0.16, 0.94), 'hull_light')
    M.add(g, B(-0.42, 0.42, -0.42, 0.42, top + 0.06, top + 0.165), 'hull_dark')
    for k in range(4):
        S = rz(90 * k)
        chevrons(M, g, 0, -0.80, top, 0.60, 0.08, n=4, ang=90 * k)
        q = S @ np.array([0.76, 0.76, 0])
        M.add(g, tf(prism(P([(0.62, 0.62), (0.90, 0.62), (0.90, 0.90), (0.62, 0.90)]), top, top + 0.10, 0.85), rz(90 * k)), 'hull_mid')
        light(M, g, q[0], q[1], top + 0.10, 0.06, 0.06)
    bolts(M, g, [(-0.48, 0), (0.48, 0), (0, 0.48), (0, -0.48)], top + 0.16, r=0.02)
    g = 'tray'                                           # bin contents: white lumps, the engine tints them with the item colour
    IA.lumps(M, g, 0, 0, top + 0.10, 0.34, 0.34, 'team', 61, n=14, s=0.07)
    return M


# ------------------------------------------------------------------ resources
def liquid_drop(fluid, hi, dots=False):
    M = Model()
    drop = P([(0.27 * math.cos(a), -0.08 + 0.27 * math.sin(a)) for a in np.radians(np.linspace(150, 390, 22))] + [(0, 0.42)])
    M.add('main', prism(drop, 0, 0.16, 0.80), fluid)
    M.add('main', prism(P([(-0.14, -0.06), (-0.06, -0.20), (-0.02, -0.04)]), 0.16, 0.17), hi)
    if dots:
        for (x, y) in ((0.08, 0.04), (0.12, -0.14), (-0.02, 0.16)):
            M.add('main', cyl((x, y, 0.15), (x, y, 0.175), 0.028, n=8), hi)
    return M


def wall_ore(kind, v):
    rng = np.random.default_rng(900 + 31 * v + (0 if kind == 'iridite' else 500))
    M = Model()
    spots = []
    for _ in range(400):
        if len(spots) == (3, 4, 3)[v]:
            break
        x, y = rng.uniform(-0.22, 0.22, 2)
        if all((x - a) ** 2 + (y - b) ** 2 > 0.24 ** 2 for a, b in spots):
            spots.append((x, y))
    for x, y in spots:
        M.add('main', cyl((x, y, -0.02), (x, y, 0.03), 0.11, 0.09, n=8), 'tung')
        k = int(rng.integers(2, 4))
        yaw0 = rng.uniform(0, 360)
        for j in range(k):
            L = rng.uniform(0.15, 0.22)
            if kind == 'iridite':
                T = prism(rect(0, 0, L * 0.30, L * 0.30), 0, L, 0.6)
                M.add('main', tf(T, rz(yaw0 + 360 * j / k) @ rx(rng.uniform(20, 40)), (x, y, 0.0)), 'magnet')
            else:
                T = prism(hexp6(L * 0.42), 0, L, 0.35)
                M.add('main', tf(T, rz(yaw0 + 360 * j / k) @ rx(rng.uniform(22, 42)), (x, y, 0.0)), 'glass')
        if kind == 'tritium-ice':
            M.add('main', cyl((x, y, 0.06), (x, y, 0.10), 0.035, n=8), 'glow')
    return M


def hexp6(r):
    return P([(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i))) for i in range(6)])


# ------------------------------------------------------------------ exporters
def tris(M):
    return f'{M.ntri():6d} tris'


def icon(M):
    a, _ = layer(M, ['main'], 32)
    return outline(a, '25262b', r=1)


def do_prospector():
    M = prospector_drill()
    main, _ = layer(M, ['main'], 64, casters=['main', 'top'])
    rot, _ = layer(M, ['rotator'], 64)
    top, _ = layer(M, ['top'], 64)
    save(main, DRL, 'prospector-drill'); save(rot, DRL, 'prospector-drill-rotator'); save(top, DRL, 'prospector-drill-top')
    f = over(over(main, rot), top)
    save(f, DRL, 'prospector-drill-full'); FULL['prospector-drill'] = np.asarray(f)
    print(f'prospector-drill   {tris(M)}  64 px', flush=True)


def do_simple(name, fn, canvas, d, glow):
    M = fn()
    main, hm = layer(M, ['main'], canvas, heat=glow)
    save(main, d, name)
    save(heat_sprite(hm), d, f'{name}-glow')
    save(main, d, f'{name}-full'); FULL[name] = np.asarray(main)
    print(f'{name:19s}{tris(M)}  {canvas} px', flush=True)


def do_vat():
    M = nanite_vat()
    bot, _ = layer(M, ['bottom'], 96, casters=['bottom', 'main'])
    main, hm = layer(M, ['main'], 96, heat=matfn('rglow'))
    save(bot, CRA, 'nanite-vat-bottom'); save(main, CRA, 'nanite-vat'); save(heat_sprite(hm), CRA, 'nanite-vat-glow')
    f = IA.liquid_tile(bot, '84f491', 0.85)
    f = over(f, main)
    save(f, CRA, 'nanite-vat-full'); FULL['nanite-vat'] = np.asarray(f)
    print(f'nanite-vat         {tris(M)}  96 px', flush=True)


def do_lance():
    M = lance_drill()
    main, _ = layer(M, ['main'], 96)
    top, hm = layer(M, ['top'], 96, heat=matfn('rglow'))
    top = outline(top, r=2)
    save(main, DRL, 'lance-drill'); save(top, DRL, 'lance-drill-top'); save(heat_sprite(hm), DRL, 'lance-drill-glow')
    f = over(main, top)
    save(f, DRL, 'lance-drill-full'); FULL['lance-drill'] = np.asarray(f)
    print(f'lance-drill        {tris(M)}  96 px', flush=True)


def do_driver():
    M = heavy_driver()
    base, _ = layer(M, ['base'], 128)
    head, _ = layer(M, ['head'], 160)
    head = outline(head, r=2)
    save(base, DIS, 'heavy-driver-base'); save(head, DIS, 'heavy-driver')
    f = over(np.zeros((160, 160, 4), np.uint8), base, 16, 16)
    f = over(f, head)
    save(f, DIS, 'heavy-driver-full'); FULL['heavy-driver'] = np.asarray(f)
    print(f'heavy-driver       {tris(M)}  base 128 / head 160 px', flush=True)


def do_hub():
    M = cargo_hub()
    main, _ = layer(M, ['main'], 96)
    save(main, UNI, 'cargo-hub'); save(main, UNI, 'cargo-hub-full'); FULL['cargo-hub'] = np.asarray(main)
    print(f'cargo-hub          {tris(M)}  96 px', flush=True)


def do_receiver():
    M = cargo_receiver()
    main, _ = layer(M, ['main'], 64, casters=['main', 'tray'])
    tray, _ = layer(M, ['tray'], 64, casters=['main', 'tray'])
    save(main, UNI, 'cargo-receiver'); save(tray, UNI, 'cargo-receiver-top')
    t = np.asarray(tray).copy()
    t[..., :3] = (t[..., :3] * np.array([1.0, 0.62, 0.40])).astype(np.uint8)    # preview tinted copper
    f = over(main, t)
    save(f, UNI, 'cargo-receiver-full'); FULL['cargo-receiver'] = np.asarray(f)
    print(f'cargo-receiver     {tris(M)}  64 px', flush=True)


def do_resources():
    for name, M in (('molten-iron', liquid_drop('flame', 'ga_melt')), ('nanite-slurry', liquid_drop('nanite', 'nglow', dots=True))):
        a = icon(M)
        save(a, 'liquids', name); FULL[name] = np.asarray(a)
        print(f'liquids/{name:22s}{tris(M)}', flush=True)
    for kind in ('iridite', 'tritium-ice'):
        for v in range(3):
            a = icon(wall_ore(kind, v))
            save(a, 'blocks/ores', f'wall-ore-{kind}{v + 1}'); FULL[f'wall-ore-{kind}{v + 1}'] = np.asarray(a)
        print(f'wall-ore-{kind:13s} 3 variants', flush=True)


JOBS = {'prospector-drill': do_prospector,
        'heat-engine': lambda: do_simple('heat-engine', heat_engine, 64, PWR, matfn('ga_ember', 'glow')),
        'hydrocarbon-plant': lambda: do_simple('hydrocarbon-plant', hydrocarbon_plant, 96, PWR, matfn('flame', 'heat', 'glow')),
        'nanite-vat': do_vat, 'lance-drill': do_lance, 'heavy-driver': do_driver, 'cargo-hub': do_hub,
        'cargo-receiver': do_receiver, 'resources': do_resources}


def main(only=()):
    for name, fn in JOBS.items():
        if not only or name in only:
            fn()
    blocks = [k for k in ('heavy-driver', 'hydrocarbon-plant', 'nanite-vat', 'lance-drill', 'cargo-hub', 'heat-engine',
                          'prospector-drill', 'cargo-receiver') if k in FULL]
    small = [k for k in FULL if k not in blocks]
    if blocks:
        print('sheet', qa_sheet(blocks, 'g_beta1-blocks.png', sc=3, cols=4))
    if small:
        print('sheet', qa_sheet(small, 'g_beta1-resources.png', sc=6, cols=4))


if __name__ == '__main__':
    main(sys.argv[1:])
