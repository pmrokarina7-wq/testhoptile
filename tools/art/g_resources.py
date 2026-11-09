"""Art workstream g_resources: T1-T3 item icons, chlorine gas icon and the six ore overlays (all 32 px).

    .venv/bin/python tools/art/g_resources.py [name ...]     (no args = everything)

Items/liquid: one low-poly model each, rendered with rend.render_layer and exported like the T4 items
(outline '25262b', r=1). Ores: three scattered clusters per ore, no outline: v146 OreBlock.createIcons adds
its own 30% black drop shadow 3 px below every opaque pixel at load time, so chunks stay fully opaque.
Mineral veins/specks are painted per sub-triangle on coplanar subdivisions (shading stays faceted).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import box, cbox, cyl, loft, rx, ry, rz, tf, clean, cham_rect, prism  # noqa: E402
from hero import P  # noqa: E402
from mats import Model  # noqa: E402
from rend import render_layer, outline, add_material  # noqa: E402
from export import save, FULL, SS, REPO  # noqa: E402

# ---------------------------------------------------------------- materials (append-only)
add_material('rock_m', ['141317', '1e1c22', '2a272e', '38343c', '49444d', '5e5862'])      # matrix stone
add_material('fer_vein', ['4a1a0c', '6e2812', '963918', 'bc4e20', 'dc672a', 'f48c44'])    # bright rust
add_material('fer_hem', ['161012', '231a1d', '33272b', '45363b', '5c4b50', '7d6a6f'])     # haematite band
add_material('salt_rock', ['2a2622', '3a3530', '4c4640', '5f5850', '736b62', '898076'])   # saltpeter host rock
add_material('baux_mx', ['2a1008', '3e180b', '55210f', '6e2c14', '88391a', 'a14822'])     # lateritic clay
add_material('baux_pale', ['6a5038', '86684a', 'a2835e', 'bc9d74', 'd4b78c', 'eccfa6'])   # gibbsite specks
add_material('cob_hi', ['16305e', '1f4382', '2c5aa8', '3b74cc', '5592e8', '86b8ff'])      # cobaltite cubes
add_material('wolf_hi', ['121216', '1d1e24', '2b2d35', '424652', '6a7182', 'b4bccc'])     # submetallic blades
add_material('neo_hi', ['4a1a3c', '6e2658', '963676', 'bc4a96', 'e064b8', 'ff96dc'])      # neodymite crystal
add_material('brass', ['3a2808', '5a3e0e', '7e5816', 'a4741e', 'c8952c', 'ecbc4c'])       # cartridge brass
add_material('magnet_red', ['3a0c10', '5c1218', '861a22', 'ae242e', 'd0343c', 'ee5a5c'])  # magnet paint
add_material('chlor_gas', ['1c3e10', '285a16', '357a1e', '449a28', '5ab836', '86d85a'])    # gas body
add_material('steel_b', ['1a1f27', '28303b', '3a4452', '505c6c', '6c7a8c', '93a2b5'])     # blued rolled steel
add_material('salt_x', ['4a4d55', '6b6e75', '8f9298', 'b5b7b9', 'd9dad5', 'f7f6ee'])      # nitre crystals
add_material('quartz', ['48484c', '64656a', '84858a', 'a4a5a8', 'c3c4c4', 'e0e0dc'])      # vein quartz
add_material('wolf_met', ['0b0c0f', '15171c', '20232a', '2e323b', '464c59', '9aa3b6'])    # wolframite lustre
rng0 = np.random.default_rng


# ---------------------------------------------------------------- geometry helpers
def subdiv_until(T, emax):
    """Split triangles 1->4 until every edge is shorter than emax (coplanar, so shading is unchanged)."""
    T = np.asarray(T, float)
    done = []
    for _ in range(8):
        e = np.max(np.stack([np.linalg.norm(T[:, i] - T[:, (i + 1) % 3], axis=1) for i in range(3)]), 0)
        big = e > emax
        done.append(T[~big])
        T = T[big]
        if not len(T):
            break
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        T = np.concatenate([np.stack(q, 1) for q in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))])
    done.append(T)
    return np.concatenate(done)


def paint(M, g, T, base, rules, emax=0.02, R=None, t=(0, 0, 0)):
    """Add T with per-sub-triangle materials: rules = [(fn(centroids) -> bool mask, mat)], later rules win.
    Rules see the untransformed coordinates; R/t place the result. Only faces seen from above are split.
    M.src counts the modelled (pre-split) triangles."""
    T = clean(T)
    M.src = getattr(M, 'src', 0) + len(T)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    nw = n @ (np.eye(3) if R is None else np.asarray(R).T)
    up = nw[:, 2] > 0.05
    M.add(g, tf(T[~up], R, t), base)
    S = subdiv_until(T[up], emax)
    cen = S.mean(1)
    lab = np.array([base] * len(S), dtype=object)
    for fn, m in rules:
        lab[fn(cen)] = m
    for m in dict.fromkeys(lab):
        M.add(g, tf(S[lab == m], R, t), m)


def add(M, T, m, g='main'):
    M.src = getattr(M, 'src', 0) + len(clean(T))
    M.add(g, T, m)


def loft3(rings, cap_t=True):
    out = []
    for i in range(len(rings) - 1):
        out.append(loft(rings[i], rings[i + 1], cap_b=(i == 0), cap_t=cap_t and (i == len(rings) - 2)))
    return np.concatenate(out)


def tablet(L, w, h, bev=0.03, tip=0.5):
    """Tabular crystal lying along +Y: bevelled long edges catch the light, chisel-cut tip."""
    hl = L / 2
    bot = [(-w, -hl), (w, -hl), (w, hl - w * tip * 1.4), (w * 0.1, hl), (-w, hl - w * tip * 0.4)]
    top = [(-w + bev, -hl + bev), (w - bev, -hl + bev), (w - bev, hl - w * tip * 1.4 - bev * 0.4), (w * 0.1, hl - bev * 1.2),
           (-w + bev, hl - w * tip * 0.4 - bev * 0.8)]
    return prism(P(bot), 0, h, top_poly=P(top))


def nugget(rng, r=0.16, h=0.14, n=7, ell=(1.0, 1.0), rot=0.0, mid=(0.5, 0.94), top=0.58, tilt=0.30, jit=0.22,
           at=(0.0, 0.0, 0.0), z0=0.0):
    """Faceted rock: base ring -> jittered shoulder ring -> flat (tilted) top facet. Returns triangles."""
    a0 = rng.uniform(0, 2 * math.pi)
    ang = a0 + (np.arange(n) + rng.uniform(-0.28, 0.28, n)) * 2 * math.pi / n
    rad = r * (1 + jit * rng.uniform(-1, 1, n))
    c, s = np.cos(ang), np.sin(ang)
    base = np.stack([rad * c * ell[0], rad * s * ell[1]], 1)
    R2 = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]])
    base = base @ R2.T
    sh = base * (mid[1] * (1 + 0.06 * rng.uniform(-1, 1, n)))[:, None]
    zs = z0 + h * mid[0] * (1 + 0.25 * rng.uniform(-1, 1, n))
    off = rng.uniform(-0.12, 0.12, 2) * r
    tp = base * top + off
    gx, gy = rng.uniform(-1, 1, 2) * tilt * h / max(r, 1e-6)
    zt = z0 + h + gx * (tp[:, 0] - off[0]) + gy * (tp[:, 1] - off[1])
    rings = [np.column_stack([base, np.full(n, z0)]), np.column_stack([sh, zs]), np.column_stack([tp, zt])]
    return tf(loft3(rings), None, at)


def crystal(L, r, tip=0.30, sides=6, taper=0.92, phase=0.0):
    """Prismatic crystal along +Z with a pyramidal termination."""
    a = phase + np.arange(sides) * 2 * math.pi / sides
    r0 = np.column_stack([r * np.cos(a), r * np.sin(a), np.zeros(sides)])
    zt = L * (1 - tip)
    r1 = np.column_stack([r * taper * np.cos(a), r * taper * np.sin(a), np.full(sides, zt)])
    T = list(loft(r0, r1, cap_b=True, cap_t=False))
    apex = np.array([0, 0, L])
    for i in range(sides):
        T.append([r1[i], r1[(i + 1) % sides], apex])
    return clean(T)


def blade(L, w, t, cut=0.72):
    """Tabular (bladed) crystal: width along X, thickness along Y, grows along +Z, chisel tip, bevelled faces."""
    poly = P([(-w, 0), (w, 0), (w, L * cut), (w * 0.1, L), (-w, L * (cut + 0.14))])
    return tf(prism(poly, -t / 2, t / 2, 0.86), rx(90))


def ellipsoid(c, rr, nlon=14, nlat=7, top_only=False):
    c = np.asarray(c, float)
    T = []
    l0 = 0 if not top_only else nlat // 2
    for i in range(l0, nlat):
        t0 = math.pi * i / nlat - math.pi / 2
        t1 = math.pi * (i + 1) / nlat - math.pi / 2
        for j in range(nlon):
            p0 = 2 * math.pi * j / nlon
            p1 = 2 * math.pi * (j + 1) / nlon

            def Q(t, p):
                return c + np.array([rr[0] * math.cos(t) * math.cos(p), rr[1] * math.cos(t) * math.sin(p), rr[2] * math.sin(t)])
            T.append([Q(t0, p0), Q(t0, p1), Q(t1, p1)])
            T.append([Q(t0, p0), Q(t1, p1), Q(t1, p0)])
    return clean(T)


def veins(rng, c, nv=2, w=0.014, wob=0.018, flat=0.5):
    """Bands where planes cut the rock (wobbled) -> thin mineral veins following the facets."""
    pl = []
    for _ in range(nv):
        n = rng.normal(size=3)
        n[2] *= flat
        n /= np.linalg.norm(n)
        pl.append((n, rng.uniform(-0.05, 0.05), rng.uniform(22, 40), rng.uniform(0, 6.3), rng.uniform(0.85, 1.25)))
    c = np.asarray(c, float)

    def f(Pc):
        q = Pc - c
        m = np.zeros(len(q), bool)
        for n, off, k, ph, ww in pl:
            d = q @ n - off + wob * np.sin(k * (q[:, 0] - 0.7 * q[:, 1]) + ph)
            m |= np.abs(d) < w * ww
        return m
    return f


def specks(rng, p, cell=0.03):
    """Random specks on a 3D grid of `cell` size, so a speck covers ~1 px regardless of the subdivision."""
    seed = int(rng.integers(1 << 30))

    def f(Pc):
        q = np.floor(Pc / cell).astype(np.int64)
        h = (q[:, 0] * 73856093) ^ (q[:, 1] * 19349663) ^ (q[:, 2] * 83492791) ^ seed
        return ((h % 100003) / 100003.0) < p
    return f


def chamfer_bar(hx, hy, h, ch=0.035, top_in=0.045):
    """Ingot-style bar: chamfered footprint, sloped sides, smaller top."""
    return prism(cham_rect(hx, hy, ch), 0, h, top_poly=cham_rect(hx - top_in, hy - top_in, ch * 0.8))


# ================================================================ raw ores (items)
def item_ferrolite():
    """Angular haematite-rich boulders: rust-red faces, dark haematite bands, bright rust and metal glints."""
    M = Model()
    rng = rng0(21)
    rocks = ((-0.05, 0.05, 0.33, 0.30, 0.5, 9, (1.0, 0.86)), (0.25, -0.20, 0.15, 0.17, 1.9, 7, (1.0, 0.9)),
             (-0.26, -0.25, 0.10, 0.11, 0.8, 6, (1.0, 1.0)))
    for (x, y, r, h, rot, n, ell) in rocks:
        T = nugget(rng, r=r, h=h, n=n, rot=rot, ell=ell, top=0.5, tilt=0.5, jit=0.15, at=(x, y, 0))
        paint(M, 'main', T, 'ore_fer', [(veins(rng, (x, y, h * 0.6), nv=2, w=0.018), 'fer_hem'),
                                       (specks(rng, 0.07), 'fer_vein'), (specks(rng, 0.025), 'metal_light')], emax=0.02)
    return M


def item_saltpeter():
    """Radiating sheaf of white prismatic nitre crystals out of a salt-crusted host rock."""
    M = Model()
    rng = rng0(22)
    T = nugget(rng, r=0.33, h=0.12, n=9, ell=(1.0, 0.70), rot=0.05, top=0.62, tilt=0.15, at=(0.0, -0.10, 0))
    paint(M, 'main', T, 'salt_rock', [(specks(rng, 0.22), 'salt_x'), (veins(rng, (0, -0.10, 0.08), nv=1, w=0.016), 'salt_x')])
    # (x, y, length, radius, yaw: 0 = +Y, tilt from vertical)
    spec = ((-0.14, -0.20, 0.50, 0.085, -58, 70, 'ore_salt'), (-0.03, -0.18, 0.60, 0.090, -14, 66, 'salt_x'),
            (0.12, -0.20, 0.52, 0.085, 34, 68, 'ore_salt'), (0.20, -0.26, 0.30, 0.065, 82, 70, 'salt_x'),
            (-0.22, -0.28, 0.26, 0.060, -100, 66, 'salt_x'))
    for (x, y, L, r, yaw, tilt, m) in spec:
        add(M, tf(crystal(L, r, tip=0.22, taper=0.95, phase=0.0), rz(yaw) @ rx(-tilt), (x, y, 0.07)), m)
    return M


def item_bauxite():
    """Lateritic clay lump studded with round pisoliths (orange-brown) and pale gibbsite specks."""
    M = Model()
    rng = rng0(13)
    T = nugget(rng, r=0.36, h=0.16, n=9, ell=(1.0, 0.86), rot=0.4, top=0.66, tilt=0.15, jit=0.10, at=(0, 0, 0))
    paint(M, 'main', T, 'baux_mx', [(specks(rng, 0.10), 'baux_pale')], emax=0.025)
    pis = ((-0.15, 0.07, 0.115), (0.06, 0.13, 0.10), (0.17, -0.04, 0.115), (-0.04, -0.14, 0.10), (0.21, 0.19, 0.07),
           (-0.25, -0.11, 0.07), (-0.01, 0.01, 0.085), (0.10, -0.21, 0.065), (-0.21, 0.22, 0.06), (0.28, -0.17, 0.05),
           (-0.08, 0.26, 0.05))
    for (x, y, r) in pis:
        z = 0.16 - 0.06 * (abs(x) + abs(y)) / 0.3
        add(M, ellipsoid((x, y, z - r * 0.35), (r, r * 0.95, r * 0.85), nlon=12, nlat=6), 'ore_baux')
    return M


def item_cobaltite():
    """Intergrown cobaltite cubes on a dark matrix: each cube shows a lit top and two shaded faces."""
    M = Model()
    rng = rng0(24)
    T = nugget(rng, r=0.32, h=0.08, n=9, ell=(1.0, 0.8), rot=0.2, top=0.7, tilt=0.1, at=(0.0, -0.03, 0))
    paint(M, 'main', T, 'rock_m', [(specks(rng, 0.12), 'ore_cob')])
    cubes = ((-0.10, 0.06, 0.29, 12, 'cob_hi'), (0.23, 0.16, 0.20, 38, 'ore_cob'), (0.17, -0.21, 0.19, -18, 'cob_hi'),
             (-0.24, -0.21, 0.14, 48, 'ore_cob'), (-0.27, 0.27, 0.11, 70, 'cob_hi'))
    for (x, y, s, yaw, m) in cubes:
        R = rz(yaw) @ rx(28) @ ry(-34)
        add(M, tf(cbox(0, 0, 0, s, s, s), R, (x, y, 0.06 + s * 0.35)), m)
    return M


def item_wolframite():
    """Heavy dark wolframite lump bristling with bladed crystals (bevelled, striated, metallic glints), quartz specks."""
    M = Model()
    rng = rng0(25)
    T = nugget(rng, r=0.30, h=0.08, n=8, ell=(1.0, 0.72), rot=0.65, top=0.66, tilt=0.2, jit=0.14, at=(0.0, -0.04, 0))
    paint(M, 'main', T, 'quartz', [(specks(rng, 0.08), 'ore_wolf')])

    def grooves(w):
        return lambda Pc: (np.abs(np.abs(Pc[:, 0]) - 0.42 * w) < 0.011) & (Pc[:, 2] > 0.03)
    # (cx, cy, z, length, half-width, height, yaw, lift, roll): parallel group of thick bladed crystals
    tabs = ((-0.08, 0.06, 0.05, 0.66, 0.13, 0.14, 32, 14, -24), (0.10, -0.06, 0.04, 0.52, 0.115, 0.12, 40, 12, 20),
            (-0.20, -0.18, 0.03, 0.26, 0.08, 0.09, 60, 8, -10))
    for (x, y, z, L, w, h, yaw, lift, roll) in tabs:
        paint(M, 'main', tablet(L, w, h, bev=0.04, tip=0.7), 'wolf_met', [(grooves(w), 'ore_wolf')], emax=0.015,
              R=rz(yaw) @ rx(lift) @ ry(roll), t=(x, y, z))
    return M


def item_neodymite():
    """Split geode: dark rind, pale chalcedony band, cavity packed with magenta neodymite crystals."""
    M = Model()
    rng = rng0(26)
    n = 11
    a = np.arange(n) * 2 * math.pi / n + 0.15 + rng.uniform(-0.12, 0.12, n)
    rr = 0.39 * (1 + 0.10 * rng.uniform(-1, 1, n))
    outer = np.stack([rr * np.cos(a), rr * 0.84 * np.sin(a)], 1)
    z = 0.18
    zr = z + 0.03 * rng.uniform(-1, 1, n)          # broken, uneven rim

    def R_(p, zz):
        return np.column_stack([p, np.broadcast_to(zz, (len(p),))])
    G = []
    G.append((loft3([R_(outer * 0.90, 0), R_(outer, z * 0.5), R_(outer * 0.94, zr)], cap_t=False), 'rock_m'))
    G.append((loft(R_(outer * 0.94, zr), R_(outer * 0.84, zr - 0.01), False, False), 'rock_m'))
    G.append((loft(R_(outer * 0.84, zr - 0.01), R_(outer * 0.79, zr - 0.025), False, False), 'baux_pale'))
    G.append((loft(R_(outer * 0.79, zr - 0.025), R_(outer * 0.70, 0.04), False, True), 'magnet'))
    pts = []
    for gx in np.arange(-0.27, 0.28, 0.095):
        for gy in np.arange(-0.22, 0.23, 0.095):
            x, y = gx + rng.uniform(-0.02, 0.02), gy + rng.uniform(-0.02, 0.02)
            if (x / 0.28) ** 2 + (y / 0.235) ** 2 < 1.0:
                pts.append((x, y))
    for (x, y) in pts:
        d = math.hypot(x / 0.28, y / 0.235)
        ang = math.degrees(math.atan2(y, x))
        L = 0.13 + 0.05 * rng.random()
        R = rz(ang - 90 + rng.uniform(-20, 20)) @ rx(-(8 + 30 * d))     # lean outwards towards the rim
        G.append((tf(crystal(L, rng.uniform(0.050, 0.060), tip=0.5, sides=6, phase=rng.uniform(0, 1)), R, (x, y, 0.04)), 'neo_hi'))
    Rt = rx(16)                                      # tip the half-geode so its outer rind shows at the bottom
    for T, m in G:
        add(M, tf(T, Rt, (0, 0.03, 0)), m)
    return M


# ================================================================ products
def item_steel():
    """Heavy rolled-steel billet: chamfered ingot, recessed stamping panel with raised mark, bright bevels."""
    M = Model()
    R = rz(28)
    hx, hy, h = 0.40, 0.23, 0.18
    th = h - 0.03
    add(M, tf(chamfer_bar(hx, hy, th, ch=0.07, top_in=0.065), R), 'steel_b')
    ix, iy = hx - 0.065, hy - 0.065
    fw = 0.05
    for (x0, x1, y0, y1) in ((-ix + 0.05, ix - 0.05, iy - fw, iy), (-ix + 0.05, ix - 0.05, -iy, -iy + fw),
                             (-ix, -ix + fw, -iy + 0.03, iy - 0.03), (ix - fw, ix, -iy + 0.03, iy - 0.03)):
        add(M, tf(box(x0, x1, y0, y1, th, h), R), 'steel_b')
    add(M, tf(box(-0.18, 0.14, -0.035, 0.035, th, th + 0.022), R), 'steel')
    add(M, tf(box(0.19, 0.24, -0.07, 0.07, th, th + 0.022), R), 'yellow')
    for (x, y) in ((-0.26, 0.08), (-0.26, -0.08)):
        add(M, tf(cyl((x, y, th), (x, y, th + 0.02), 0.024, n=8), R), 'steel')
    return M


def item_charge():
    """Pair of modular propellant charges: combustible case, brass end rings, red igniter band, primer pad."""
    M = Model()
    R = rz(-22)
    for (dx, dy, L) in ((-0.14, -0.03, 0.72), (0.14, 0.05, 0.66)):
        r = 0.125
        y0, y1 = -L / 2, L / 2
        z = r + 0.01

        def C(a, b, rad, m, rad2=None, n=18):
            add(M, tf(cyl((dx, a, z), (dx, b, z), rad, rad2, n=n), R, (0, dy, 0)), m)
        C(y0 + 0.05, y1 - 0.07, r, 'charge')
        C(y0, y0 + 0.05, r * 1.06, 'copper')
        C(y1 - 0.07, y1 - 0.02, r * 1.06, 'copper')
        C(y1 - 0.02, y1 + 0.03, r * 0.86, 'copper', r * 0.55)
        C(-0.035, 0.035, r * 1.03, 'red_armor')
        C(y0 - 0.015, y0, r * 0.45, 'hull_dark')
        for yy in (y0 + 0.17, y1 - 0.19):
            C(yy, yy + 0.018, r * 1.01, 'yellow')
    return M


def item_aluminum():
    """Stack of rolled aluminium sheet: two flat sheets under a corrugated profile sheet, bright cut edges."""
    M = Model()
    for k, (rot, dx, dy) in enumerate(((-38, -0.04, -0.06), (2, 0.05, 0.03))):
        z0 = 0.03 * k
        add(M, tf(prism(cham_rect(0.37, 0.25, 0.03), z0, z0 + 0.026, 0.97), rz(rot), (dx, dy, 0)), 'alu')
        add(M, tf(box(-0.30, -0.22, 0.12, 0.20, z0 + 0.026, z0 + 0.03), rz(rot), (dx, dy, 0)), 'metal')
    R = rz(-18)
    waves, hy, hx, z0, amp = 4, 0.22, 0.33, 0.065, 0.035
    N = waves * 8
    prof = [(-hy + 2 * hy * i / N, z0 + amp * (1 + math.sin(i / 8 * 2 * math.pi))) for i in range(N + 1)]
    T = []
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
        T += [[(-hx, ya, za), (hx, ya, za), (hx, yb, zb)], [(-hx, ya, za), (hx, yb, zb), (-hx, yb, zb)]]
        for x in (-hx, hx):
            T += [[(x, ya, z0), (x, ya, za), (x, yb, zb)], [(x, ya, z0), (x, yb, zb), (x, yb, z0)]]
    add(M, tf(np.array(T), R, (0.0, 0.03, 0)), 'alu')
    return M


def item_cobalt_alloy():
    """Bullion stack of three cobalt-alloy bars (two below, one across), bright chamfers + alloy stamp tag."""
    M = Model()
    R = rz(-30)
    for x in (-0.14, 0.14):
        add(M, tf(tf(chamfer_bar(0.13, 0.37, 0.12, ch=0.035, top_in=0.035), None, (x, 0, 0)), R), 'cobalt')
    add(M, tf(tf(chamfer_bar(0.39, 0.13, 0.12, ch=0.035, top_in=0.035), None, (0, 0.03, 0.12)), R), 'cob_hi')
    add(M, tf(box(-0.17, 0.17, -0.005, 0.065, 0.24, 0.252), R), 'alu')
    for x in (-0.28, 0.28):
        add(M, tf(cyl((x, 0.03, 0.24), (x, 0.03, 0.255), 0.024, n=8), R), 'metal_light')
    return M


def item_tungsten_core():
    """APFSDS penetrator: long tungsten rod, ogive tip, segmented brass sabot collar, four tail fins."""
    M = Model()
    R = rz(-45)
    z = 0.11
    add(M, tf(cyl((0, -0.42, z), (0, 0.27, z), 0.06, n=12), R), 'tung')
    add(M, tf(cyl((0, 0.27, z), (0, 0.47, z), 0.06, 0.008, n=12), R), 'metal_light')
    add(M, tf(cyl((0, -0.07, z), (0, 0.15, z), 0.11, n=14), R), 'brass')
    for y in (-0.07, 0.035, 0.13):
        add(M, tf(cyl((0, y, z), (0, y + 0.02, z), 0.116, n=14), R), 'hull_dark')
    for a in (0, 90, 180, 270):
        F = tf(prism(P([(0.045, -0.44), (0.17, -0.47), (0.17, -0.38), (0.045, -0.25)]), -0.013, 0.013), ry(a + 45))
        add(M, tf(F, R, (0, 0, z)), 'metal')
    add(M, tf(cyl((0, -0.47, z), (0, -0.42, z), 0.045, n=10), R), 'yellow')
    return M


def item_magnet():
    """Neodymium horseshoe: square-section red body, steel pole shoes, magenta N-core inlay on the crown."""
    M = Model()
    R = rz(0)
    Rr, w, hz, leg, cy0 = 0.235, 0.105, 0.13, 0.17, 0.12
    path = [(-Rr, cy0 - leg, None)]
    for i in range(15):
        a = math.radians(180 - 180 * i / 14)
        path.append((Rr * math.cos(a), cy0 + Rr * math.sin(a), a))
    path.append((Rr, cy0 - leg, None))
    rings = []
    for (x, y, a) in path:
        nx, ny = (1.0, 0.0) if a is None else (math.cos(a), math.sin(a))
        o, i_ = (x + nx * w, y + ny * w), (x - nx * w, y - ny * w)
        rings.append([(o[0], o[1], 0.0), (o[0], o[1], hz), (i_[0], i_[1], hz), (i_[0], i_[1], 0.0)])
    T = []
    for A, Bq in zip(rings[:-1], rings[1:]):
        for k in range(4):
            T += [[A[k], A[(k + 1) % 4], Bq[(k + 1) % 4]], [A[k], Bq[(k + 1) % 4], Bq[k]]]
    add(M, tf(clean(T), R), 'magnet')
    for s in (-1, 1):
        add(M, tf(prism(cham_rect(w, 0.08, 0.022, s * Rr, cy0 - leg - 0.08), 0, hz + 0.006, 0.9), R), 'magnet_red' if s < 0 else 'metal_light')
        add(M, tf(box(s * Rr - w, s * Rr + w, cy0 - leg - 0.012, cy0 - leg + 0.006, 0, hz + 0.014), R), 'hull_dark')
    # neodymium core inlay along the crown
    for i in range(9):
        a0, a1 = math.radians(160 - 140 * i / 9), math.radians(160 - 140 * (i + 1) / 9)
        p0 = (Rr * math.cos(a0), cy0 + Rr * math.sin(a0), hz)
        p1 = (Rr * math.cos(a1), cy0 + Rr * math.sin(a1), hz)
        add(M, tf(cyl(p0, p1, 0.022, n=6), R), 'neo_hi')
    return M


def swirl(c, phi0, phi1, R0, R1, wfn, N=72, K=10, hk=0.85):
    """Domed ribbon swept along a shrinking spiral (vanilla gas 'curl'), width wfn(u), u = 0..1 along the path."""
    T = []
    secs = []
    for i in range(N + 1):
        u = i / N
        ph = phi0 + (phi1 - phi0) * u
        Rp = R0 + (R1 - R0) * u ** 1.15
        w = wfn(u)
        rad = np.array([math.cos(ph), math.sin(ph), 0.0])
        cen = np.array([c[0], c[1], 0.0]) + Rp * rad
        secs.append([cen - w * math.cos(math.pi * k / K) * rad + np.array([0, 0, hk * w * math.sin(math.pi * k / K)])
                     for k in range(K + 1)])
    for A, B in zip(secs[:-1], secs[1:]):
        for k in range(K):
            T += [[A[k], A[k + 1], B[k + 1]], [A[k], B[k + 1], B[k]]]
    return clean(T), secs


def liquid_chlorine():
    """Chlorine gas: a domed green curl (vanilla gas language) with a glossy glint, cf. liquid-nitrogen's drop."""
    M = Model()
    c = (0.03, 0.05)

    def wfn(u):
        return 0.03 + 0.085 * math.sin(math.pi / 2 * min(u / 0.32, 1.0)) - 0.035 * max(0.0, (u - 0.32) / 0.68)
    T, secs = swirl(c, math.radians(-35), math.radians(-470), 0.36, 0.115, wfn)
    add(M, T, 'chlor')
    end = np.mean([secs[-1][0], secs[-1][-1]], 0)
    we = wfn(1.0)
    add(M, ellipsoid(end, (we, we, 0.85 * we), nlon=16, nlat=8, top_only=True), 'chlor')
    # glossy glints on the lit (upper-left) part of the outer coil
    for (ph, ln, wd) in ((150, 0.07, 0.022), (118, 0.03, 0.016)):
        a = math.radians(ph)
        rr = 0.36 + (0.115 - 0.36) * ((-35 - (ph - 360)) / 435) ** 1.15
        p = (c[0] + (rr + 0.03) * math.cos(a), c[1] + (rr + 0.03) * math.sin(a), 0.085)
        add(M, tf(ellipsoid((0, 0, 0), (wd, ln, 0.012), nlon=10, nlat=4), rz(ph), p), 'gglow')
    return M


# ================================================================ ore overlays
def place(rng, n, rmin, rmax, lim=0.42, gap=0.03):
    out = []
    tries = 0
    while len(out) < n and tries < 5000:
        tries += 1
        r = rng.uniform(rmin, rmax)
        x, y = rng.uniform(-lim + r, lim - r, 2)
        if all(math.hypot(x - a, y - b) > r + c + gap for a, b, c in out):
            out.append((x, y, r))
    return out


def ore_chunks(kind, v):
    M = Model()
    rng = rng0(900 + 37 * v + 101 * ORES.index(kind))
    n = (5, 4, 5)[v]
    spots = place(rng, n, 0.115, 0.18, lim=0.44, gap=0.02)
    for (x, y, r) in spots:
        if kind == 'ferrolite':
            T = nugget(rng, r=r, h=r * 0.85, n=7, rot=rng.uniform(0, 6), ell=(1, 0.85), top=0.55, tilt=0.35, jit=0.15, at=(x, y, 0))
            paint(M, 'main', T, 'ore_fer', [(veins(rng, (x, y, r * 0.5), nv=1, w=0.015), 'fer_hem'),
                                           (specks(rng, 0.06), 'fer_vein')])
        elif kind == 'saltpeter':
            add(M, nugget(rng, r=r * 0.95, h=r * 0.4, n=7, at=(x, y, 0)), 'salt_rock')
            y0 = rng.uniform(0, 360)
            for j in range(4):
                yaw = y0 + 90 * j + rng.uniform(-25, 25)
                add(M, tf(crystal(r * rng.uniform(1.0, 1.35), r * 0.32, tip=0.3), rz(yaw) @ rx(-rng.uniform(40, 62)),
                          (x + rng.uniform(-0.25, 0.25) * r, y + rng.uniform(-0.25, 0.25) * r, r * 0.25)), 'salt_x')
        elif kind == 'bauxite':
            add(M, nugget(rng, r=r, h=r * 0.35, n=7, at=(x, y, 0)), 'baux_mx')
            for (dx, dy, k) in ((0.0, 0.05, 0.62), (-0.45, -0.35, 0.40), (0.42, -0.30, 0.42)):
                if k < 0.5 and rng.random() < 0.3:
                    continue
                rr = r * k
                add(M, ellipsoid((x + dx * r, y + dy * r, r * 0.25), (rr, rr * 0.95, rr * 0.8), nlon=12, nlat=6), 'ore_baux')
        elif kind == 'cobaltite':
            add(M, nugget(rng, r=r * 0.9, h=r * 0.3, n=7, at=(x, y, 0)), 'rock_m')
            s = r * 1.0
            add(M, tf(cbox(0, 0, 0, s, s, s), rz(rng.uniform(0, 90)) @ rx(24) @ ry(-30), (x, y, r * 0.3 + s * 0.3)), 'cob_hi')
            if rng.random() < 0.6:
                s2 = s * 0.55
                ang = rng.uniform(0, 2 * math.pi)
                add(M, tf(cbox(0, 0, 0, s2, s2, s2), rz(rng.uniform(0, 90)) @ rx(24) @ ry(-30),
                          (x + math.cos(ang) * r * 0.75, y + math.sin(ang) * r * 0.75, r * 0.3)), 'cob_hi')
        elif kind == 'wolframite':
            add(M, nugget(rng, r=r, h=r * 0.55, n=7, top=0.55, at=(x, y, 0)), 'ore_wolf')
            yaw = rng.uniform(0, 180)
            add(M, tf(tablet(r * 1.8, r * 0.42, r * 0.45, bev=r * 0.14), rz(yaw) @ rx(10) @ ry(25), (x, y, r * 0.30)), 'wolf_hi')
            if rng.random() < 0.7:
                add(M, tf(tablet(r * 1.2, r * 0.32, r * 0.35, bev=r * 0.12), rz(yaw + rng.choice([-1, 1]) * rng.uniform(55, 80)) @ rx(8) @ ry(-25),
                          (x + rng.uniform(-0.2, 0.2) * r, y + rng.uniform(-0.2, 0.2) * r, r * 0.5)), 'wolf_hi')
            add(M, ellipsoid((x - r * 0.45, y - r * 0.35, r * 0.2), (r * 0.25, r * 0.22, r * 0.2), nlon=8, nlat=4), 'quartz')
        elif kind == 'neodymite':
            add(M, nugget(rng, r=r * 0.9, h=r * 0.35, n=7, at=(x, y, 0)), 'rock_m')
            y0 = rng.uniform(0, 360)
            for j in range(4):
                add(M, tf(crystal(r * rng.uniform(1.0, 1.45), r * 0.34, tip=0.45), rz(y0 + 90 * j + rng.uniform(-25, 25)) @ rx(-rng.uniform(25, 55)),
                          (x + rng.uniform(-0.25, 0.25) * r, y + rng.uniform(-0.25, 0.25) * r, r * 0.2)), 'neo_hi')
    return M


# ================================================================ driver
ITEMS = {'ferrolite': item_ferrolite, 'saltpeter': item_saltpeter, 'bauxite': item_bauxite, 'cobaltite': item_cobaltite,
         'wolframite': item_wolframite, 'neodymite': item_neodymite, 'steel': item_steel, 'charge': item_charge,
         'aluminum': item_aluminum, 'cobalt-alloy': item_cobalt_alloy, 'tungsten-core': item_tungsten_core, 'magnet': item_magnet}
ORES = ['ferrolite', 'saltpeter', 'bauxite', 'cobaltite', 'wolframite', 'neodymite']
BUILD = os.path.join(REPO, 'build', 'g_resources')


def render_icon(M):
    a, _ = render_layer(M, ['main'], ['main'], 32, SS)
    return outline(a, '25262b', r=1)


def tris(M):
    return f'{getattr(M, "src", M.ntri()):5d} modelled / {M.ntri():6d} rendered tris'


def preview(keys, fn, k=4):
    """x4 sheet; ore overlays are shown alternately on a dark and a light floor."""
    ims = [(n, FULL[n]) for n in keys if n in FULL]
    c = 32 * k + 20
    cols = 9
    rows = (len(ims) + cols - 1) // cols
    bg = Image.new('RGB', (cols * c + 20, rows * (c + 14) + 20), (54, 57, 64))
    d = ImageDraw.Draw(bg)
    for i, (n, a) in enumerate(ims):
        r, cc = divmod(i, cols)
        x, y = 20 + cc * c, 20 + r * (c + 14)
        im = Image.fromarray(a).resize((32 * k, 32 * k), Image.NEAREST)
        if n.startswith('ore-'):
            d.rectangle([x, y, x + 32 * k - 1, y + 32 * k - 1], fill=(46, 44, 50) if i % 2 == 0 else (156, 146, 128))
        bg.paste(im, (x, y), im)
        d.text((x, y + 32 * k + 1), n, fill=(220, 220, 225))
    os.makedirs(BUILD, exist_ok=True)
    out = os.path.join(BUILD, fn)
    bg.save(out)
    return out


def main(only=()):
    def want(n):
        return not only or n in only
    for name, fn in ITEMS.items():
        if want(name):
            M = fn()
            a = render_icon(M)
            save(a, 'items', name)
            FULL[name] = np.asarray(a)
            print(f'items/{name:24s} {tris(M)}')
    if want('chlorine'):
        M = liquid_chlorine()
        a = render_icon(M)
        save(a, 'liquids', 'chlorine')
        FULL['chlorine'] = np.asarray(a)
        print(f'liquids/{"chlorine":22s} {tris(M)}')
    for ore in ORES:
        if want(ore) or want('ore-' + ore):
            for v in range(3):
                M = ore_chunks(ore, v)
                a, _ = render_layer(M, ['main'], ['main'], 32, SS)
                save(a, 'blocks/ores', f'ore-{ore}{v + 1}')
                FULL[f'ore-{ore}{v + 1}'] = np.asarray(a)
                print(f'blocks/ores/ore-{ore}{v + 1:<{14 - len(ore)}d} {tris(M)}')
    keys = list(ITEMS) + ['chlorine'] + [f'ore-{o}{v}' for o in ORES for v in (1, 2, 3)]
    print(preview(keys, 'preview-x4.png'))


if __name__ == '__main__':
    main(tuple(sys.argv[1:]))
