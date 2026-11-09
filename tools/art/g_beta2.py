"""2.5.0-beta2 art: status icons (32x32) for the ACU modules, recall cooldown, ACU assembly and the older mod statuses
that had no icon (spotted, chrono-slow, corrosion, quantum-stasis).

    .venv/bin/python tools/art/g_beta2.py          (VG_SPRITES=<dir> writes elsewhere, for byte comparison)

Flat glyphs like the vanilla status icons: drawn 8x supersampled, box-reduced, alpha thresholded for crisp pixels,
then a 1 px dark outline ('25262b', as the item icons). QA sheet: build/art/g_beta2-icons.png (x4 on dark and light).
"""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT = os.environ.get('VG_SPRITES', os.path.join(ROOT, 'mod', 'sprites'))
SS, N = 8, 32
S = N * SS
OUTLINE = (0x25, 0x26, 0x2b, 255)


def hexc(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def canvas():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def P(x, y):
    """icon units (0..32) -> supersampled pixels"""
    return (x * SS, y * SS)


def poly(d, pts, col):
    d.polygon([P(x, y) for x, y in pts], fill=col)


def circle(d, cx, cy, r, col, width=0):
    box = [P(cx - r, cy - r), P(cx + r, cy + r)]
    if width:
        d.ellipse(box, outline=col, width=int(width * SS))
    else:
        d.ellipse(box, fill=col)


def line(d, pts, col, w):
    d.line([P(x, y) for x, y in pts], fill=col, width=int(w * SS), joint='curve')
    for x, y in (pts[0], pts[-1]):
        circle(d, x, y, w / 2, col)


def arc(d, cx, cy, r, a0, a1, col, w):
    d.arc([P(cx - r, cy - r), P(cx + r, cy + r)], a0, a1, fill=col, width=int(w * SS))


def finish(im):
    small = im.reduce(SS)
    px = small.load()
    for y in range(N):
        for x in range(N):
            r, g, b, a = px[x, y]
            if a >= 110:
                k = 255 / a
                px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), 255)
            else:
                px[x, y] = (0, 0, 0, 0)
    out = small.copy()
    po = out.load()
    for y in range(N):
        for x in range(N):
            if px[x, y][3] == 0 and any(0 <= x + dx < N and 0 <= y + dy < N and px[x + dx, y + dy][3] > 0
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                po[x, y] = OUTLINE
    return out


# ---------------------------------------------------------------- glyphs
def cannon():
    im, d = canvas()
    poly(d, [(5, 27), (9, 19), (14, 24)], hexc('5a6c80'))
    line(d, [(9, 23), (23, 9)], hexc('9fb3c8'), 5)
    line(d, [(10, 22), (22, 10)], hexc('d6e2ee'), 1.6)
    poly(d, [(20, 7), (26, 7), (26, 13)], hexc('ffd04a'))
    for a in range(0, 360, 45):
        r0, r1 = 2, 6 if a % 90 == 45 else 4
        line(d, [(26 + r0 * math.cos(math.radians(a)), 7 - r0 * math.sin(math.radians(a))),
                 (26 + r1 * math.cos(math.radians(a)), 7 - r1 * math.sin(math.radians(a)))], hexc('ffb347'), 1.6)
    circle(d, 9, 23, 3.4, hexc('ffd04a'))
    circle(d, 9, 23, 1.4, hexc('3c4a5a'))
    return im


def hexagon(cx, cy, r, rot=30):
    return [(cx + r * math.cos(math.radians(rot + 60 * k)), cy + r * math.sin(math.radians(rot + 60 * k))) for k in range(6)]


def shield():
    im, d = canvas()
    poly(d, hexagon(16, 16, 13), hexc('2f6fb8'))
    poly(d, hexagon(16, 16, 10), hexc('5aa6ff'))
    poly(d, hexagon(16, 16, 6.5), hexc('a9d4ff'))
    poly(d, [(16, 9), (21, 12), (21, 17), (16, 23), (11, 17), (11, 12)], hexc('e8f4ff'))
    poly(d, [(16, 11.5), (19, 13.3), (19, 16.6), (16, 20.5)], hexc('8fc4ff'))
    return im


def gear(d, cx, cy, r, teeth, col, hole):
    pts = []
    for k in range(teeth * 2):
        a = math.pi * 2 * k / (teeth * 2)
        rr = r if k % 2 == 0 else r * 0.74
        for da in (-0.17, 0.17):
            pts.append((cx + rr * math.cos(a + da * math.pi / teeth * 2), cy + rr * math.sin(a + da * math.pi / teeth * 2)))
    poly(d, pts, col)
    circle(d, cx, cy, hole, (0, 0, 0, 0))


def build():
    im, d = canvas()
    gear(d, 13, 18, 10, 8, hexc('ffd04a'), 0)
    circle(d, 13, 18, 5, hexc('c99a1e'))
    circle(d, 13, 18, 2.6, (0, 0, 0, 0))
    poly(d, [(22, 3), (29, 10), (25, 10), (25, 17), (19, 17), (19, 10), (15, 10)], hexc('8ff0a8'))
    poly(d, [(22, 5.5), (26, 9.5), (24, 9.5), (24, 15.5), (22, 15.5)], hexc('d8ffe2'))
    return im


def repair():
    im, d = canvas()
    circle(d, 16, 16, 13.5, hexc('2f8a4a'))
    circle(d, 16, 16, 11, hexc('5fd37f'))
    poly(d, [(13, 6), (19, 6), (19, 13), (26, 13), (26, 19), (19, 19), (19, 26), (13, 26), (13, 19), (6, 19), (6, 13), (13, 13)], hexc('f2fff5'))
    poly(d, [(14.5, 7.5), (17.5, 7.5), (17.5, 14.5), (24.5, 14.5), (24.5, 17.5), (14.5, 17.5)], hexc('c9f7d5'))
    return im


def missile(d, x, y, ang, L):
    ca, sa = math.cos(ang), math.sin(ang)

    def T(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    poly(d, [T(-L * 0.5, -3.4), T(-L * 0.5, 3.4), T(-L * 0.2, 2.2), T(-L * 0.2, -2.2)], hexc("ff7a3a"))
    poly(d, [T(-L * 0.45, -2.2), T(L * 0.3, -2.2), T(L * 0.3, 2.2), T(-L * 0.45, 2.2)], hexc("c8d0da"))
    poly(d, [T(-L * 0.4, -2.2), T(L * 0.28, -2.2), T(L * 0.28, -0.6), T(-L * 0.4, -0.6)], hexc("eef2f6"))
    poly(d, [T(L * 0.3, -2.2), T(L * 0.58, 0), T(L * 0.3, 2.2)], hexc("ffb347"))
    poly(d, [T(-L * 0.62, -1.4), T(-L * 0.45, 0), T(-L * 0.62, 1.4), T(-L * 0.92, 0)], hexc("ffe08a"))


def missiles():
    im, d = canvas()
    a = -math.pi / 4
    missile(d, 11, 15, a, 18)
    missile(d, 18, 22, a, 18)
    return im


def teleport():
    im, d = canvas()
    circle(d, 16, 16, 14, hexc('4a3a9a'))
    circle(d, 16, 16, 11.5, hexc('7b6cff'))
    circle(d, 16, 16, 8.5, hexc('b3a8ff'))
    circle(d, 16, 16, 5.5, hexc('ece8ff'))
    for k in range(3):
        a0 = k * 120 + 20
        arc(d, 16, 16, 13, a0, a0 + 50, hexc('d8d2ff'), 1.4)
    poly(d, [(16, 11), (20, 16), (17.5, 16), (17.5, 20), (14.5, 20), (14.5, 16), (12, 16)], hexc('4a3a9a'))
    return im


def tp_cooldown():
    im, d = canvas()
    poly(d, [(8, 4), (24, 4), (24, 7), (18, 16), (24, 25), (24, 28), (8, 28), (8, 25), (14, 16), (8, 7)], hexc('8fb8ff'))
    poly(d, [(10.5, 6.5), (21.5, 6.5), (16, 14.5)], hexc('e6f0ff'))
    poly(d, [(16, 19), (21, 25.5), (11, 25.5)], hexc('e6f0ff'))
    line(d, [(6, 4), (26, 4)], hexc('5a6c80'), 2.4)
    line(d, [(6, 28), (26, 28)], hexc('5a6c80'), 2.4)
    return im


def assembly_icon():
    im, d = canvas()
    poly(d, [(9, 9), (23, 9), (23, 23), (9, 23)], hexc('5a6c80'))
    poly(d, [(11, 11), (21, 11), (21, 21), (11, 21)], hexc('9fb3c8'))
    poly(d, [(13, 13), (19, 13), (19, 19), (13, 19)], hexc('ffd04a'))
    arc(d, 16, 16, 13.5, -90, 180, hexc('ffd37f'), 2.6)
    poly(d, [(2.5, 16), (5, 12.5), (7.5, 16)], hexc('ffd37f'))
    return im


def spotted():
    im, d = canvas()
    col = hexc('6ab8ff')
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cx, cy = 16 + sx * 11, 16 + sy * 11
        line(d, [(cx, cy - sy * 6), (cx, cy), (cx - sx * 6, cy)], col, 2.6)
    circle(d, 16, 16, 6, hexc('2f6fb8'))
    circle(d, 16, 16, 3.6, hexc('cfe8ff'))
    return im


def chrono():
    im, d = canvas()
    circle(d, 16, 16, 13, hexc('5a3a8a'))
    circle(d, 16, 16, 10.5, hexc('c890ff'))
    circle(d, 16, 16, 8.5, hexc('efe0ff'))
    line(d, [(16, 16), (16, 9)], hexc('5a3a8a'), 2.2)
    line(d, [(16, 16), (21, 19)], hexc('5a3a8a'), 2.2)
    for k in range(12):
        a = math.radians(k * 30)
        r0 = 7 if k % 3 else 6
        line(d, [(16 + r0 * math.cos(a), 16 + r0 * math.sin(a)), (16 + 8 * math.cos(a), 16 + 8 * math.sin(a))], hexc('a070d0'), 1)
    return im


def drop(d, cx, cy, r, col, hi):
    poly(d, [(cx, cy - r * 1.9), (cx + r * 0.8, cy - r * 0.6), (cx - r * 0.8, cy - r * 0.6)], col)
    circle(d, cx, cy, r, col)
    circle(d, cx - r * 0.35, cy - r * 0.2, r * 0.32, hi)


def corrosion():
    im, d = canvas()
    poly(d, [(3, 27), (29, 27), (29, 30), (3, 30)], hexc('5a6a2a'))
    drop(d, 11, 18, 6, hexc('9acd32'), hexc('e2ffa0'))
    drop(d, 22, 12, 4.5, hexc('b8e04a'), hexc('f2ffc8'))
    drop(d, 23, 24, 2.6, hexc('7aa82a'), hexc('d8f59a'))
    return im


def stasis():
    im, d = canvas()
    poly(d, [(16, 2), (27, 16), (16, 30), (5, 16)], hexc('3a8a6a'))
    poly(d, [(16, 5), (24, 16), (16, 27), (8, 16)], hexc('9df0a8'))
    poly(d, [(16, 5), (24, 16), (16, 16)], hexc('dcffe2'))
    poly(d, [(16, 16), (16, 27), (8, 16)], hexc('6ac890'))
    line(d, [(4, 9), (28, 23)], hexc('f4fff6'), 1.2)
    line(d, [(4, 23), (28, 9)], hexc('f4fff6'), 1.2)
    return im


ICONS = [
    ('acu-mod-cannon', cannon), ('acu-mod-shield', shield), ('acu-mod-build', build), ('acu-mod-repair', repair),
    ('acu-mod-missiles', missiles), ('acu-mod-teleport', teleport), ('acu-tp-cooldown', tp_cooldown),
    ('acu-assembly', assembly_icon), ('spotted', spotted), ('chrono-slow', chrono), ('corrosion', corrosion),
    ('quantum-stasis', stasis),
]


def main():
    d = os.path.join(OUT, 'status')
    os.makedirs(d, exist_ok=True)
    tiles = []
    for name, fn in ICONS:
        icon = finish(fn())
        icon.save(os.path.join(d, name + '.png'))
        tiles.append(icon)
        print('icon', name)
    k = 4
    sheet = Image.new('RGBA', (len(tiles) * (N * k + 8) + 8, 2 * (N * k + 8) + 8), (0, 0, 0, 0))
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([0, 0, sheet.width, N * k + 12], fill=(32, 33, 40, 255))
    dr.rectangle([0, N * k + 12, sheet.width, sheet.height], fill=(170, 172, 178, 255))
    for i, ic in enumerate(tiles):
        big = ic.resize((N * k, N * k), Image.NEAREST)
        for row in range(2):
            sheet.alpha_composite(big, (8 + i * (N * k + 8), 8 + row * (N * k + 8)))
    qa = os.path.join(ROOT, 'build', 'art')
    os.makedirs(qa, exist_ok=True)
    sheet.save(os.path.join(qa, 'g_beta2-icons.png'))
    print('sheet', os.path.join(qa, 'g_beta2-icons.png'))


if __name__ == '__main__':
    main()
