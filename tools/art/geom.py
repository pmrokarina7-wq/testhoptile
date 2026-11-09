import numpy as np, math

# ---------- 2D helpers ----------
def area(p):
    p = np.asarray(p, float)
    return 0.5*np.sum(p[:,0]*np.roll(p[:,1],-1) - np.roll(p[:,0],-1)*p[:,1])

def ccw(p):
    p = np.asarray(p, float)
    return p if area(p) > 0 else p[::-1].copy()

def cham_rect(hx, hy, c, cx=0, cy=0):
    return ccw([(cx+hx-c,cy-hy),(cx+hx,cy-hy+c),(cx+hx,cy+hy-c),(cx+hx-c,cy+hy),
                (cx-hx+c,cy+hy),(cx-hx,cy+hy-c),(cx-hx,cy-hy+c),(cx-hx+c,cy-hy)])

def rect(cx, cy, hx, hy):
    return ccw([(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy)])

def scale_poly(p, s, about=None):
    p = np.asarray(p, float)
    c = p.mean(0) if about is None else np.asarray(about, float)
    s = np.asarray(s, float)
    return c + (p-c)*s

def mirror_half(half):
    """half: right side points from front (x>=0) to back; returns full ccw polygon"""
    h = [tuple(q) for q in half]
    left = [(-x, y) for (x, y) in reversed(h) if abs(x) > 1e-9]
    return ccw(h + left)

def ring(poly, z):
    p = np.asarray(poly, float)
    zz = np.full(len(p), float(z)) if np.isscalar(z) else np.asarray(z, float)
    return np.column_stack([p, zz])

# ---------- triangulation ----------
def newell(pts):
    n = np.zeros(3)
    for i in range(len(pts)):
        a = pts[i]; b = pts[(i+1) % len(pts)]
        n += [(a[1]-b[1])*(a[2]+b[2]), (a[2]-b[2])*(a[0]+b[0]), (a[0]-b[0])*(a[1]+b[1])]
    return n/(np.linalg.norm(n)+1e-12)

def earclip(p2):
    idx = list(range(len(p2))); tris = []
    def a2(a, b, c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def inside(p, a, b, c):
        return a2(a,b,p) >= -1e-12 and a2(b,c,p) >= -1e-12 and a2(c,a,p) >= -1e-12
    guard = 0
    while len(idx) > 3 and guard < 5000:
        guard += 1; found = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k-1], idx[k], idx[(k+1) % len(idx)]
            a, b, c = p2[i0], p2[i1], p2[i2]
            if a2(a, b, c) <= 1e-12: continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2): continue
                if inside(p2[j], a, b, c): ok = False; break
            if ok:
                tris.append((i0, i1, i2)); idx.pop(k); found = True; break
        if not found: break
    if len(idx) == 3: tris.append(tuple(idx))
    elif len(idx) > 3:
        for k in range(1, len(idx)-1): tris.append((idx[0], idx[k], idx[k+1]))
    return tris

def cap(pts, want):
    pts = np.asarray(pts, float)
    n = newell(pts)
    if np.dot(n, want) < 0: n = -n
    t = np.array([0,0,1.0]) if abs(n[2]) < 0.9 else np.array([1.0,0,0])
    u = np.cross(t, n); u /= np.linalg.norm(u); v = np.cross(n, u)
    c = pts.mean(0)
    p2 = np.column_stack([(pts-c)@u, (pts-c)@v])
    order = list(range(len(pts)))
    if area(p2) < 0: order = order[::-1]
    tri = earclip(p2[order])
    out = []
    for (a, b, cc) in tri:
        A, B, C = pts[order[a]], pts[order[b]], pts[order[cc]]
        nn = np.cross(B-A, C-A)
        out.append([A, B, C] if np.dot(nn, want) >= 0 else [A, C, B])
    return out

def clean(T):
    T = np.asarray(T, float).reshape(-1, 3, 3)
    cr = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0])
    return T[np.linalg.norm(cr, axis=1) > 1e-11]

def loft(bot, top, cap_b=True, cap_t=True):
    bot = np.asarray(bot, float); top = np.asarray(top, float); n = len(bot)
    T = []
    for i in range(n):
        j = (i+1) % n
        T.append([bot[i], bot[j], top[j]]); T.append([bot[i], top[j], top[i]])
    axis = top.mean(0)-bot.mean(0)
    if np.linalg.norm(axis) < 1e-9: axis = np.array([0,0,1.0])
    if cap_t: T += cap(top, axis)
    if cap_b: T += cap(bot, -axis)
    return clean(T)

def prism(poly, z0, z1, top_scale=1.0, top_poly=None):
    tp = scale_poly(poly, top_scale) if top_poly is None else top_poly
    return loft(ring(poly, z0), ring(tp, z1))

def box(x0, x1, y0, y1, z0, z1):
    return prism(rect((x0+x1)/2, (y0+y1)/2, abs(x1-x0)/2, abs(y1-y0)/2), z0, z1)

def cbox(cx, cy, cz, sx, sy, sz):
    return box(cx-sx/2, cx+sx/2, cy-sy/2, cy+sy/2, cz-sz/2, cz+sz/2)

def basis(axis):
    a = np.asarray(axis, float); a = a/np.linalg.norm(a)
    t = np.array([0,0,1.0]) if abs(a[2]) < 0.9 else np.array([1.0,0,0])
    u = np.cross(t, a); u /= np.linalg.norm(u); v = np.cross(a, u)
    return u, v, a

def cyl(p0, p1, r0, r1=None, n=20, caps=True, phase=0.0):
    r1 = r0 if r1 is None else r1
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    u, v, a = basis(p1-p0)
    ang = phase + np.arange(n)*2*np.pi/n
    circ = np.outer(np.cos(ang), u)+np.outer(np.sin(ang), v)
    return loft(p0+r0*circ, p1+r1*circ, caps, caps)

def tube_path(pts, r, n=12, collar=None):
    out = []
    pts = [np.asarray(p, float) for p in pts]
    for a, b in zip(pts[:-1], pts[1:]):
        out.append(cyl(a, b, r, n=n))
    for p in pts[1:-1]:
        out.append(sphereish(p, r, n))
    return np.concatenate(out)

def sphereish(c, r, n=12):
    # low-poly sphere (lat-long)
    c = np.asarray(c, float); T = []
    lat = 6
    for i in range(lat):
        t0 = math.pi*i/lat - math.pi/2; t1 = math.pi*(i+1)/lat - math.pi/2
        for j in range(n):
            p0 = 2*math.pi*j/n; p1 = 2*math.pi*(j+1)/n
            def P(t, p): return c + r*np.array([math.cos(t)*math.cos(p), math.cos(t)*math.sin(p), math.sin(t)])
            T.append([P(t0,p0), P(t0,p1), P(t1,p1)]); T.append([P(t0,p0), P(t1,p1), P(t1,p0)])
    return clean(T)

# ---------- transforms ----------
def rx(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def ry(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rz(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def tf(T, R=None, t=(0,0,0)):
    T = np.asarray(T, float)
    if R is not None: T = T @ np.asarray(R).T
    return T + np.asarray(t, float)

def mirror_x(T):
    T = np.asarray(T, float)*np.array([-1,1,1.0])
    return T[:, [0,2,1], :]
