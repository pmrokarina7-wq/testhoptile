"""Beta-1 art, part 2 (2.5.0-beta1): command cores, ACU Mk II-III, engineers T2-T3.

    .venv/bin/python tools/art/g_beta1b.py [name ...]     (no args = everything)

Upgrades are built on the approved Mk I / T1 models from g_units.py: the original stays in the middle and gets
the upgrade hardware (cores: an outer ring of works; ACUs: shield / stealth hardware and armour, then scaled up;
engineers: extra lift pods and arms, scaled up). Layer names and composition match g_units (mech / flyer / core).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import *  # noqa: E402,F401,F403
from mats import Model  # noqa: E402
from models import bolts, light, chevrons  # noqa: E402
from hero import P, grille, cable, seam, buttress, slope_plate  # noqa: E402
from export import save, layer, FULL, qa_sheet  # noqa: E402
from rend import over  # noqa: E402
import g_units as GU  # noqa: E402
import g_industry_b as IB  # noqa: E402


def scaled(M, s):
    for g in M.parts:
        M.parts[g] = [(T * s, m) for T, m in M.parts[g]]
    return M


def bbox(M, groups):
    tri, _, _ = M.arrays(groups)
    p = tri.reshape(-1, 3)
    return p.min(0), p.max(0)


# ================================================================== ACU Mk II / Mk III
def acu_uef_mk(mk):
    M = GU.acu_uef()
    lo, hi = bbox(M, ['body'])
    zt = hi[2]
    g = 'body'
    # Mk II: personal shield generator on the backpack (dome emitter with a glowing ring), armoured collar
    cy = lo[1] + 0.10
    M.add(g, cyl((0, cy, zt - 0.10), (0, cy, zt + 0.04), 0.20, 0.18, n=24), 'hull_light')
    M.add(g, cyl((0, cy, zt + 0.04), (0, cy, zt + 0.07), 0.15, n=24), 'glow')
    M.add(g, cyl((0, cy, zt + 0.07), (0, cy, zt + 0.12), 0.10, 0.06, n=20), 'metal_light')
    for s in (-1, 1):
        M.add(g, cbox(s * 0.20, cy, zt - 0.02, 0.06, 0.24, 0.06), 'yellow')
    if mk >= 3:
        # Mk III: twin shoulder missile racks and a sensor mast
        for s in (-1, 1):
            x = s * (hi[0] - 0.12)
            M.add(g, cbox(x, 0.05, zt - 0.02, 0.18, 0.34, 0.10), 'hull_mid')
            for i in range(3):
                for j in range(2):
                    M.add(g, cyl((x - 0.05 + 0.10 * j, -0.07 + 0.11 * i, zt + 0.03), (x - 0.05 + 0.10 * j, -0.07 + 0.11 * i, zt + 0.05), 0.035, n=8), 'bore')
            M.add(g, cbox(x, 0.22, zt + 0.03, 0.18, 0.03, 0.02), 'yellow')
        M.add(g, cyl((0.10, cy - 0.12, zt), (0.10, cy - 0.12, zt + 0.30), 0.015, n=6), 'metal')
        M.add(g, cyl((0.10, cy - 0.12, zt + 0.30), (0.10, cy - 0.12, zt + 0.33), 0.03, n=8), 'glow')
    return scaled(M, 1.15 if mk == 2 else 1.30)


def acu_cybran_mk(mk):
    M = GU.acu_cybran()
    lo, hi = bbox(M, ['body'])
    zt = hi[2]
    g = 'body'
    # Mk II: stealth field generator - twin red-lit fins on the back and a glowing emitter
    cy = lo[1] + 0.12
    for s in (-1, 1):
        fin = P([(s * 0.06, cy - 0.10), (s * 0.26, cy - 0.30), (s * 0.30, cy - 0.14), (s * 0.10, cy + 0.12)])
        M.add(g, prism(fin, zt - 0.12, zt + 0.06, 0.8), 'cy_dark')
        M.add(g, prism(scale_poly(fin, 0.5), zt + 0.06, zt + 0.075), 'rglow')
    M.add(g, cyl((0, cy, zt - 0.08), (0, cy, zt + 0.05), 0.09, n=16), 'red_armor')
    M.add(g, cyl((0, cy, zt + 0.05), (0, cy, zt + 0.07), 0.06, n=12), 'rglow')
    if mk >= 3:
        # Mk III: armoured spine with three glowing nodes and blade spurs on the shoulders
        for i, y in enumerate((0.15, -0.05, -0.25)):
            M.add(g, cbox(0, y, zt + 0.01, 0.10, 0.12, 0.05), 'red_armor')
            M.add(g, cbox(0, y, zt + 0.04, 0.05, 0.05, 0.02), 'rglow')
        for s in (-1, 1):
            spur = P([(s * (hi[0] - 0.20), 0.10), (s * (hi[0] + 0.08), 0.30), (s * (hi[0] - 0.05), -0.05)])
            M.add(g, prism(spur, zt - 0.10, zt + 0.02, 0.7), 'cy_mid')
    return scaled(M, 1.15 if mk == 2 else 1.30)


# ================================================================== engineers T2 / T3
def engineer_t(t):
    M = GU.engineer()
    lo, hi = bbox(M, ['body'])
    zt = hi[2]
    g = 'body'
    # T2: second pair of lift pods at the rear and a tool rack; T3: + glowing nano-forge on the deck
    for s in (-1, 1):
        x, y = s * (hi[0] - 0.06), lo[1] + 0.10
        M.add(g, cyl((x, y, zt - 0.10), (x, y, zt - 0.02), 0.12, n=18), 'hull_light')
        M.add(g, cyl((x, y, zt - 0.02), (x, y, zt), 0.09, n=16), 'vent')
        for k in range(3):
            M.add(g, tf(cbox(0.045, 0, zt + 0.005, 0.08, 0.02, 0.01), rz(60 * k + 15 * s), (x, y, 0)), 'metal_light')
        M.add(g, cyl((x, y, zt), (x, y, zt + 0.012), 0.025, n=8), 'glow')
    M.add(g, cbox(0, lo[1] + 0.12, zt - 0.03, 0.16, 0.08, 0.04), 'yellow')
    if t >= 3:
        M.add(g, cyl((0, 0.02, zt - 0.02), (0, 0.02, zt + 0.04), 0.09, n=18), 'hull_mid')
        M.add(g, cyl((0, 0.02, zt + 0.04), (0, 0.02, zt + 0.055), 0.065, n=16), 'glow')
        for s in (-1, 1):
            M.add(g, cyl((s * 0.10, 0.10, zt), (s * 0.04, 0.32, zt - 0.02), 0.018, n=6), 'metal')
    return scaled(M, 1.2 if t == 2 else 1.4)


# ================================================================== command cores (T3 5x5, T5 6x6)
def outer_works_uef(M, h0, h, top=0.22):
    """UEF outer ring between half-size h0 (original core) and h: armoured deck, corner gun towers, radar, tanks."""
    g = 'main'
    ring = cham_rect(h * 0.985, h * 0.985, h * 0.22)
    M.add(g, prism(ring, 0.0, 0.10, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(h * 0.94, h * 0.94, h * 0.22), 0.10, top - 0.08, 0.98), 'hull_mid')
    w = h - h0
    for k in range(4):
        S = rz(90 * k)
        # side grilles and seams on the outer deck
        grille(M, g, 0, -(h - w * 0.45), top - 0.08, h * 0.9, w * 0.32, n=int(6 + h * 2), glow='glow', R=S)
        seam(M, g, *[tuple((S @ np.array([x, -(h0 + 0.06), 0]))[:2]) for x in (-h0 * 0.9, h0 * 0.9)], top - 0.08, w=0.03, h=0.012)
        chevrons(M, g, 0, -(h - 0.12), top - 0.08, h * 0.5, 0.10, n=6, ang=90 * k)
        # corner gun tower
        c = rz(45 + 90 * k) @ np.array([(h - w * 0.45) * math.sqrt(2) * 0.92, 0, 0])
        M.add(g, cyl((c[0], c[1], 0.05), (c[0], c[1], top + 0.14), w * 0.42, w * 0.38, n=20), 'hull_light')
        M.add(g, cyl((c[0], c[1], top + 0.14), (c[0], c[1], top + 0.17), w * 0.30, n=20), 'hull_dark')
        a = math.radians(45 + 90 * k + 180)
        M.add(g, cyl((c[0], c[1], top + 0.20), (c[0] + 0.40 * w * math.cos(a), c[1] + 0.40 * w * math.sin(a), top + 0.22), 0.05, n=8), 'metal')
        M.add(g, cyl((c[0], c[1], top + 0.17), (c[0], c[1], top + 0.19), 0.06, n=10), 'team')
    # radar dish on the north-east works and fuel tanks on the south-west
    rx_, ry_ = h - w * 0.5, h * 0.35
    M.add(g, cyl((rx_, ry_, top - 0.08), (rx_, ry_, top + 0.10), 0.07, n=10), 'metal')
    M.add(g, tf(cyl((0, 0, 0), (0, 0, 0.05), w * 0.34, w * 0.30, n=20), rx(25), (rx_, ry_, top + 0.12)), 'metal_light')
    M.add(g, cyl((rx_, ry_ + 0.04, top + 0.18), (rx_, ry_ + 0.04, top + 0.21), 0.03, n=8), 'glow')
    for i in range(2):
        tx = -(h - w * 0.5)
        ty = -h * 0.30 - i * w * 0.55
        M.add(g, cyl((tx, ty, top - 0.08), (tx, ty, top + 0.06), w * 0.22, n=18), 'steel')
        M.add(g, cyl((tx, ty, top + 0.06), (tx, ty, top + 0.09), w * 0.16, n=16), 'yellow')


def outer_works_cybran(M, h0, h, top=0.22):
    g = 'main'
    M.add(g, prism(cham_rect(h * 0.985, h * 0.985, h * 0.30), 0.0, 0.10, 0.985), 'hull_dark')
    M.add(g, prism(cham_rect(h * 0.93, h * 0.93, h * 0.32), 0.10, top - 0.08, 0.97), 'cy_mid')
    w = h - h0
    for k in range(4):
        S = rz(90 * k)
        # red armour plates along each side, glowing slits between them
        for x in (-h0 * 0.55, h0 * 0.55):
            plate = P([(x - h0 * 0.36, -(h - 0.08)), (x + h0 * 0.36, -(h - 0.08)), (x + h0 * 0.30, -(h0 + 0.10)), (x - h0 * 0.30, -(h0 + 0.10))])
            zf = (lambda xx, yy: top - 0.02 + (abs(yy) - h0) * 0.10)
            slope_plate(M, g, plate, zf, 'red_armor', thick=0.08, inlay='cy_dark', isc=0.6, ih=0.012, R=S)
        M.add(g, tf(cbox(0, -(h - w * 0.5), top - 0.02, 0.08, w * 0.6, 0.02), S), 'rglow')
        # corner spire
        c = rz(45 + 90 * k) @ np.array([(h - w * 0.45) * math.sqrt(2) * 0.92, 0, 0])
        base = P([(c[0] + w * 0.30 * math.cos(math.radians(a)), c[1] + w * 0.30 * math.sin(math.radians(a))) for a in range(0, 360, 60)])
        M.add(g, prism(base, 0.05, top + 0.10, 0.75), 'cy_dark')
        M.add(g, cyl((c[0], c[1], top + 0.10), (c[0], c[1], top + 0.40), w * 0.10, 0.01, n=6), 'red_armor')
        M.add(g, cyl((c[0], c[1], top + 0.08), (c[0], c[1], top + 0.12), w * 0.14, n=10), 'rglow')
        M.add(g, cyl((c[0], c[1], top + 0.02), (c[0], c[1], top + 0.06), w * 0.24, n=12), 'team')


def core_mk(faction, size):
    M = GU.core_uef() if faction == 'uef' else GU.core_cybran()
    (outer_works_uef if faction == 'uef' else outer_works_cybran)(M, 2.0, size / 2.0)
    return M


# ------------------------------------------------------------------ exporters
def do_core(name, faction, size):
    M = core_mk(faction, size)
    canvas = size * 32
    main, hm = layer(M, ['main'], canvas, GU.teamfn)
    team = GU.cell_of(main, hm)
    d = 'blocks/cores'
    save(main, d, name)
    save(team, d, f'{name}-team')
    f = over(main.copy(), GU.tint(team, GU.TEAM_PREVIEW))
    save(f, d, f'{name}-full')
    FULL[name] = f
    print(f'{name:16s}{M.ntri():6d} tris  {canvas} px', flush=True)


def do_acu(name, build, guns, canvas, wcanvas):
    M = build()
    GU.mech(name, M, guns, canvas=canvas, wcanvas=wcanvas)
    print(f'{name:16s}{M.ntri():6d} tris  {canvas} px', flush=True)


def do_eng(name, t):
    M = engineer_t(t)
    canvas = 48 if t == 2 else 56
    GU.flyer(name, M, canvas=canvas)
    print(f'{name:16s}{M.ntri():6d} tris  {canvas} px', flush=True)


def acu_jobs():
    out = []
    for mk, s in ((2, 1.15), (3, 1.30)):
        cv, wc = (96, 56) if mk == 2 else (104, 64)
        out.append((f'acu-uef-mk{mk}', lambda mk=mk, s=s, cv=cv, wc=wc: do_acu(f'acu-uef-mk{mk}', lambda: acu_uef_mk(mk), [
            ('gunR', f'acu-uef-mk{mk}-cannon', 6.0 * s, 0.5 * s, GU.heat_of(('glow',), (0.30 * s, 0.70 * s))),
            ('gunL', f'acu-uef-mk{mk}-launcher', -6.0 * s, 0.5 * s, None)], cv, wc)))
        out.append((f'acu-cybran-mk{mk}', lambda mk=mk, s=s, cv=cv, wc=wc: do_acu(f'acu-cybran-mk{mk}', lambda: acu_cybran_mk(mk), [
            ('gunR', f'acu-cybran-mk{mk}-laser', 5.75 * s, 0.75 * s, GU.heat_of(('rglow',), (0.30 * s, 0.74 * s))),
            ('gunL', f'acu-cybran-mk{mk}-emp', -5.75 * s, 0.75 * s, GU.heat_of(('rglow',), (0.15 * s, 0.46 * s)))], cv, wc)))
    return out


JOBS = dict([('core-uef-2', lambda: do_core('core-uef-2', 'uef', 5)), ('core-cybran-2', lambda: do_core('core-cybran-2', 'cybran', 5)),
             ('core-uef-3', lambda: do_core('core-uef-3', 'uef', 6)), ('core-cybran-3', lambda: do_core('core-cybran-3', 'cybran', 6)),
             ('engineer-2', lambda: do_eng('engineer-2', 2)), ('engineer-3', lambda: do_eng('engineer-3', 3))] + acu_jobs())


def main(only=()):
    for name, fn in JOBS.items():
        if not only or name in only:
            fn()
    cores = [k for k in ('core-uef-2', 'core-uef-3', 'core-cybran-2', 'core-cybran-3') if k in FULL]
    units = [k for k in ('acu-uef-mk2', 'acu-uef-mk3', 'acu-cybran-mk2', 'acu-cybran-mk3', 'engineer-2', 'engineer-3') if k in FULL]
    if cores:
        print('sheet', qa_sheet(cores, 'g_beta1b-cores.png', sc=2, cols=4))
    if units:
        print('sheet', qa_sheet(units, 'g_beta1b-units.png', sc=4, cols=6))


if __name__ == '__main__':
    main(sys.argv[1:])
