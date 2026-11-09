import numpy as np, math
from PIL import Image, ImageFilter
from geom import basis
from mats import MATS, MID

def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)

RAMPS = {
 'hull_dark':  ['15191f','1d222b','272e3a','333c4b','424d5f','566276'],
 'hull_mid':   ['1b2029','262d39','343d4c','45505f','5a6678','748194'],
 'hull_light': ['272d37','363e4b','4b5566','636e81','7f8b9f','a1acbf'],
 'red_armor':  ['2a0b10','45121a','631923','88222f','ad2d3b','cf4252'],
 'metal':      ['24262c','373a42','50545f','6d717e','8e939f','b3b7c2'],
 'metal_light':['31343c','4a4e58','686d79','8b909c','adb2bd','d0d4dc'],
 'cable':      ['101216','191c22','23272f','2e333c','3a3f4a','484e5a'],
 'vent':       ['0b0c0f','111317','17191e','1e2026','25282f','2d3038'],
 'bore':       ['050607','08090b','0b0c0e','0f1013','131418','17191d'],
 'coil':       ['3a1406','5a1f08','7a2b0c','9a3810','ba4614','d85a1c'],
 'heat':       ['30140a','48200e','603012','784016','90501c','a86422'],
 'glow':       ['1b4f7a','2272b0','2f95e0','56b4f2','8fd0fa','cdeeff'],
 'ground':     ['2b2c33','34353d','3d3e47','474852','52535e','5e5f6b'],
 'yellow':     ['3b2d07','5c450b','846312','ad841a','d6a624','f5c84a'],
 'glass':      ['0e1c27','15293a','1e3b51','29506c','376a8b','4c87ab'],
 'copper':     ['3a1d10','5a2e18','7f4322','a65a2e','c9743e','e8955a'],
 'flame':      ['8a2a06','c2420a','f06414','ff8c2a','ffb45a','ffe0a0'],
 'ore_fer':    ['2a1410','46201a','663024','86402e','a6553c','c26e50'],
 'ore_salt':   ['5c5d5c','7c7d7a','9d9e99','bdbeb7','d9dad2','f2f2ec'],
 'steel':      ['2a3038','3f4752','58626f','76818f','98a3b0','c2cbd5'],
 'charge':     ['2a2812','433f1c','615b28','817936','a19946','c3ba5c'],
 'rglow':      ['a3132a','d81c38','ff2b45','ff4a60','ff7486','ff9eab'],
 'team':       ['5a5a5e','77777c','98989d','b9b9be','dadade','ffffff'],
 'cy_dark':    ['0c0a0d','141116','1d1920','28232c','352f3a','453d4b'],
 'cy_mid':     ['16131a','211d26','2e2934','3e3746','514859','685d72'],
 'alu':        ['3a4048','56606b','76818d','99a4b0','bcc6d0','e2e8ee'],
 'cobalt':     ['0f1c3a','182b57','223d78','2f5399','4470bb','6592d8'],
 'tung':       ['16171a','202226','2c2f34','3a3e45','4b5059','636973'],
 'magnet':     ['221a2c','332742','463656','5b4770','735b8b','9277aa'],
 'ore_baux':   ['3a1a0c','5a2a12','7c3c18','9e5020','bd6a2c','d9883e'],
 'ore_cob':    ['0e1f3d','15305c','1f437e','2b5aa0','3f76c2','5f96e0'],
 'ore_wolf':   ['18181c','24252b','32343c','42454f','555965','6c7180'],
 'ore_neo':    ['3a1830','582448','783262','9a4280','ba58a0','d878c0'],
 'chlor':      ['1a3a12','245a18','2f7a20','3c9a2a','52b83a','74d45a'],
 'pglow':      ['5a2a9a','7838c8','9a50f0','b070ff','c898ff','e2c8ff'],
 'gglow':      ['2a7a1a','3aa024','52c832','70e048','98f070','c8ffa8'],
}
RAMP = np.stack([np.stack([hexc(c) for c in RAMPS[m]]) for m in MATS])  # (nm,6,3)
UNLIT = {MID['glow'], MID['flame'], MID['rglow'], MID['pglow'], MID['gglow']}


def add_material(name, ramp6, glow=False):
    """Append a material at runtime (6 hex colours, dark -> light). Append-only, so existing ids never shift."""
    global RAMP
    if name in MID:
        return MID[name]
    MATS.append(name)
    MID[name] = len(MATS) - 1
    RAMPS[name] = list(ramp6)
    RAMP = np.concatenate([RAMP, np.stack([hexc(c) for c in ramp6])[None]], 0)
    if glow:
        UNLIT.add(MID[name])
        GLOW_TIE.append(name)
    return MID[name]


GLOW_TIE = ['glow', 'flame', 'rglow']

def tri_normals(T):
    n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0])
    return n/(np.linalg.norm(n, axis=1, keepdims=True)+1e-12)

def raster(scr, W, H):
    zbuf = np.full((H, W), -np.inf, np.float64); ids = np.full((H, W), -1, np.int32)
    xs = scr[..., 0]; ys = scr[..., 1]
    X0 = np.floor(xs.min(1)).astype(int); X1 = np.ceil(xs.max(1)).astype(int)
    Y0 = np.floor(ys.min(1)).astype(int); Y1 = np.ceil(ys.max(1)).astype(int)
    for t in range(len(scr)):
        x0 = max(X0[t], 0); x1 = min(X1[t], W-1); y0 = max(Y0[t], 0); y1 = min(Y1[t], H-1)
        if x0 > x1 or y0 > y1: continue
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = scr[t]
        den = (by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den) < 1e-12: continue
        X, Y = np.meshgrid(np.arange(x0, x1+1)+0.5, np.arange(y0, y1+1)+0.5)
        w0 = ((by-cy)*(X-cx)+(cx-bx)*(Y-cy))/den
        w1 = ((cy-ay)*(X-cx)+(ax-cx)*(Y-cy))/den
        w2 = 1-w0-w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        z = w0*az+w1*bz+w2*cz
        zs = zbuf[y0:y1+1, x0:x1+1]; isub = ids[y0:y1+1, x0:x1+1]
        u = m & (z > zs)
        zs[u] = z[u]; isub[u] = t
    return zbuf, ids

def box1(a, r, axis):
    pw = [(0, 0), (0, 0)]; pw[axis] = (r+1, r)
    p = np.pad(a, pw, mode='edge')
    cs = np.cumsum(p, axis=axis)
    n = a.shape[axis]
    hi = np.take(cs, np.arange(2*r+1, 2*r+1+n), axis=axis)
    lo = np.take(cs, np.arange(0, n), axis=axis)
    return (hi-lo)/(2*r+1)

def blur(a, r, it=3):
    for _ in range(it):
        a = box1(box1(a, r, 0), r, 1)
    return a

class ShadowMap:
    def __init__(self, tri, L, res_per_unit=160, margin=0.2):
        self.L = np.asarray(L, float)/np.linalg.norm(L)
        self.u, self.v, _ = basis(self.L)
        a = tri @ self.u; b = tri @ self.v; d = tri @ self.L
        self.a0 = a.min()-margin; self.b0 = b.min()-margin
        self.k = res_per_unit
        W = int((a.max()+margin-self.a0)*self.k)+2; H = int((b.max()+margin-self.b0)*self.k)+2
        scr = np.stack([(a-self.a0)*self.k, (b-self.b0)*self.k, d], -1)
        self.z, _ = raster(scr, W, H)
        self.W, self.H = W, H
    def lit(self, P, bias=0.025):
        a = ((P @ self.u)-self.a0)*self.k; b = ((P @ self.v)-self.b0)*self.k; d = P @ self.L
        ia = np.clip(a.astype(int), 0, self.W-1); ib = np.clip(b.astype(int), 0, self.H-1)
        occ = np.zeros(P.shape[:-1])
        for oa, ob in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
            z = self.z[np.clip(ib+ob, 0, self.H-1), np.clip(ia+oa, 0, self.W-1)]
            occ += (z > d+bias)
        return 1.0 - occ/5.0

EMI = ['3aa8ff', '9fdcff']
LIGHT_TD = np.array([-0.55, 0.38, 0.75])

def render_layer(M, groups, casters, canvas, ss=4, heat_fn=None, L=LIGHT_TD):
    """Top-down orthographic render -> quantized pixel sprite (RGBA) + heat mask."""
    tri, mat, grp = M.arrays(groups)
    s = 32.0*ss; W = canvas*ss; c = W/2
    scr = np.stack([c+tri[..., 0]*s, c-tri[..., 1]*s, tri[..., 2]], -1)
    zbuf, ids = raster(scr, W, W)
    cov = ids >= 0
    n = tri_normals(tri); n[n[:, 2] < 0] *= -1
    Ln = L/np.linalg.norm(L)
    ndl = np.clip(n @ Ln, 0, 1)
    yy, xx = np.mgrid[0:W, 0:W]
    X = (xx+0.5-c)/s; Y = (c-(yy+0.5))/s
    Z = np.where(cov, zbuf, 0)
    P = np.stack([X, Y, Z], -1)
    ctri, _, _ = M.arrays(casters)
    sm = ShadowMap(ctri, Ln, res_per_unit=s)
    lit = sm.lit(P)
    tid = np.where(cov, ids, 0)
    diff = ndl[tid]
    shade = 0.36 + 0.64*diff*(0.45+0.55*lit)
    bg = np.nanmin(np.where(cov, zbuf, np.inf)) if cov.any() else 0
    zf = np.where(cov, zbuf, bg)
    zb = blur(zf, max(2, ss*2), 2)
    ao = 1.0 - np.clip((zb-zf)*1.6, 0, 0.35)
    v = shade*ao
    edge = np.zeros_like(cov)
    zneg = np.where(cov, zbuf, -1e9)
    for d in (1, 2):
        for dy, dx in ((d,0),(-d,0),(0,d),(0,-d)):
            nb = np.roll(np.roll(zneg, dy, 0), dx, 1)
            edge |= cov & (nb-zneg > 0.06)
    mp = np.where(cov, mat[tid], -1)
    heat = np.zeros((W, W))
    if heat_fn is not None:
        heat = np.where(cov, heat_fn(mp, X, Y, grp[tid]), 0)
    # ---- downsample
    N = canvas; k = ss*ss
    def blk(a): return a.reshape(N, ss, N, ss).transpose(0, 2, 1, 3).reshape(N, N, k)
    mpb = blk(mp); vb = blk(v); eb = blk(edge); hb = blk(heat)
    covn = (mpb >= 0).sum(-1)
    cnt = np.stack([(mpb == i).sum(-1) for i in range(len(MATS))], -1)
    # glow wins ties when present strongly (tiny lights shouldn't vanish)
    for _g in GLOW_TIE: cnt[..., MID[_g]] = (cnt[..., MID[_g]]*1.8).astype(int)
    mode = cnt.argmax(-1)
    sel = mpb == mode[..., None]
    vm = (vb*sel).sum(-1)/np.maximum(sel.sum(-1), 1)
    ef = (eb & (mpb >= 0)).sum(-1)/np.maximum(covn, 1)
    idx = np.clip(np.round(vm*6.7-1.1), 0, 5).astype(int)
    idx = idx - (ef >= 0.22).astype(int)
    gl = np.isin(mode, [MID[_g] for _g in GLOW_TIE])
    idx = np.where(gl, np.where(ef >= 0.3, 1, np.where(vm > 0.75, 3, 2)), idx)
    idx = np.clip(idx, 0, 5)
    rgb = RAMP[mode, idx]
    alpha = (covn >= k*0.5)
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = rgb.astype(np.uint8); out[..., 3] = alpha*255
    hm = np.clip(hb.mean(-1)*1.25, 0, 1)
    return out, hm

def dilate(mask, r):
    out = mask.copy()
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            if dx*dx+dy*dy <= r*r+r*0.8:
                out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out

def heat_sprite(hm):
    N = hm.shape[0]
    a = hm.copy()
    m = a > 0.05
    bloom = np.zeros_like(a)
    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
        bloom = np.maximum(bloom, np.roll(np.roll(a, dy, 0), dx, 1)*0.45)
    a = np.maximum(a, bloom)
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = 255; out[..., 3] = (np.clip(a, 0, 1)*255).astype(np.uint8)
    out[out[..., 3] < 12] = 0
    return out

def outline(spr, color='404049', r=3):
    a = spr[..., 3] > 0
    d = dilate(a, r) & ~a
    out = spr.copy()
    out[d, :3] = hexc(color); out[d, 3] = 255
    return out

def over(dst, src, ox=0, oy=0):
    """alpha composite src (RGBA uint8) over dst at offset (centered canvases use ox/oy=0)"""
    D = Image.fromarray(dst); S = Image.fromarray(src)
    D.alpha_composite(S, (ox, oy))
    return np.array(D)

# ------------------------------------------------------------------ showcase
def render_view(tri, mat, grp, cam, light, W, H, ss=2, ground=None, fit_tri=None,
                margin=0.10, glow_coils=0.0, bg_top='26262c', bg_bot='101013'):
    Wh, Hh = W*ss, H*ss
    c = np.asarray(cam, float); c /= np.linalg.norm(c)
    f = -c; up = np.array([0, 0, 1.0])
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    ft = tri if fit_tri is None else fit_tri
    px, py = ft @ r, ft @ u
    sx = (px.max()-px.min()); sy = (py.max()-py.min())
    scale = min(Wh*(1-2*margin)/sx, Hh*(1-2*margin)/sy)
    mx = (px.max()+px.min())/2; my = (py.max()+py.min())/2
    allt = tri; allm = mat; allg = grp
    if ground is not None:
        g = ground
        gt = np.array([[[-g,-g,0],[g,-g,0],[g,g,0]],[[-g,-g,0],[g,g,0],[-g,g,0]]], float)
        allt = np.concatenate([tri, gt]); allm = np.concatenate([mat, [MID['ground']]*2])
        allg = np.concatenate([grp, ['ground']*2])
    scr = np.stack([Wh/2+((allt@r)-mx)*scale, Hh/2-((allt@u)-my)*scale, allt@c], -1)
    zbuf, ids = raster(scr, Wh, Hh)
    cov = ids >= 0; tid = np.where(cov, ids, 0)
    yy, xx = np.mgrid[0:Hh, 0:Wh]
    sxp = (xx+0.5-Wh/2)/scale+mx; syp = (Hh/2-(yy+0.5))/scale+my
    P = sxp[..., None]*r + syp[..., None]*u + np.where(cov, zbuf, 0)[..., None]*c
    n = tri_normals(allt); flip = (n @ c) < 0; n[flip] *= -1
    N = n[tid]
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    sm = ShadowMap(tri, L, res_per_unit=scale*0.9)
    lit = sm.lit(P, bias=0.02)
    m = np.where(cov, allm[tid], -1)
    alb = RAMP[np.clip(m, 0, None), 3]/255.0
    ndl = np.clip(N @ L, 0, 1)
    F = np.array([0.7, -0.5, 0.35]); F /= np.linalg.norm(F)
    fill = np.clip(N @ F, 0, 1)*0.22
    hemi = 0.20 + 0.14*N[..., 2]
    Hh_ = (L + c); Hh_ /= np.linalg.norm(Hh_)
    spec_k = np.isin(m, [MID['metal'], MID['metal_light'], MID['hull_light'], MID['red_armor'], MID['steel'], MID['yellow'], MID['glass']])
    spec = np.clip(N @ Hh_, 0, 1)**36 * lit * np.where(spec_k, 0.9, 0.25)
    zf = np.where(cov, zbuf, zbuf[cov].min() if cov.any() else 0)
    zb = blur(zf, int(6*ss), 2)
    ao = 1.0 - np.clip((zb-zf)*2.2, 0, 0.45)
    light_term = (hemi + fill + 1.25*ndl*lit)*ao
    col = alb*light_term[..., None] + spec[..., None]
    gnd = m == MID['ground']
    if ground is not None:
        gx, gy = P[..., 0], P[..., 1]
        fx = np.abs(((gx+0.5) % 1.0)-0.5); fy = np.abs(((gy+0.5) % 1.0)-0.5)
        seam = (np.minimum(0.5-fx, 0.5-fy) < 0.018)
        bev = ((0.5-fx) < 0.05) | ((0.5-fy) < 0.05)
        tint = np.where(seam, 0.55, np.where(bev, 0.85, 1.0))
        rnd = (np.sin(np.floor(gx)*12.9898+np.floor(gy)*78.233)*43758.5453) % 1.0
        tint = tint*(0.93+0.1*rnd)
        dist = np.sqrt(gx**2+gy**2)
        fog = np.clip(1.0-(dist-2.0)/4.2, 0.0, 1.0)
        col = np.where(gnd[..., None], col*tint[..., None]*(0.35+0.65*fog)[..., None], col)
    emi = np.zeros((Hh, Wh, 3))
    gm = np.isin(m, [MID['glow'], MID['flame'], MID['rglow']])
    emi[gm] = hexc(EMI[0])/255.0
    col[gm] = hexc(EMI[1])/255.0
    if glow_coils > 0:
        cm = np.isin(m, [MID['coil'], MID['heat']])
        emi[cm] = hexc('ff2a3c')/255.0*glow_coils
        col[cm] = col[cm]*0.4 + hexc('ff4b5a')/255.0*glow_coils
    t = (yy/Hh)[..., None]
    bgc = (hexc(bg_top)*(1-t)+hexc(bg_bot)*t)/255.0
    img = np.where(cov[..., None], col, bgc)
    e = np.stack([blur(emi[..., i], int(5*ss), 2) for i in range(3)], -1)
    e2 = np.stack([blur(emi[..., i], int(18*ss), 2) for i in range(3)], -1)
    img = img + e*0.9 + e2*0.8
    img = 1-np.exp(-img*1.25)
    img = np.clip(img*1.08, 0, 1)
    im = Image.fromarray((img*255).astype(np.uint8))
    if ss > 1: im = im.resize((W, H), Image.LANCZOS)
    return im
