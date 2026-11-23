"""Décors animés façon Vice City, un par sujet. Chaque fonction build_*() renvoie draw(t) -> image RGBA 1080x1920."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
INK = (16, 6, 28)
def lerp(a, b, t): t = max(0, min(1, t)); return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def gradient(stops, h=H):
    im = Image.new("RGB", (W, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1: d.line([(0, y), (W, y)], fill=lerp(c0, c1, (t - p0) / (p1 - p0 + 1e-9))); break
    return im.convert("RGBA")

def stars(im, n=80, ymax=700, seed=3):
    d = ImageDraw.Draw(im); rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, ymax); r = int(rng.choice([1, 1, 2])); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 255))

def glow(layer, radius=18, strength=2):
    g = layer.filter(ImageFilter.GaussianBlur(radius)); out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    for _ in range(strength): out.alpha_composite(g)
    out.alpha_composite(layer); return out

def palm(h, lean=1, col=INK):
    w = int(h * 0.9); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bx, by = w // 2, h; cx, cy = w // 2 + lean * int(h * 0.12), int(h * 0.18)
    for i in range(41):
        t = i / 40; x = (1 - t) ** 2 * bx + 2 * (1 - t) * t * (bx + lean * h * 0.02) + t * t * cx
        y = (1 - t) ** 2 * by + 2 * (1 - t) * t * (h * 0.55) + t * t * cy; r = int(h * 0.026 * (1 - 0.55 * t)) + 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
    for ang in (-170, -140, -110, -70, -40, -10, 15):
        a = math.radians(ang); L = h * 0.42; tx, ty = cx + math.cos(a) * L, cy + math.sin(a) * L * 0.55 + L * 0.35
        mx, my = cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5 - h * 0.04
        sp = [((1 - t) ** 2 * cx + 2 * (1 - t) * t * mx + t * t * tx, (1 - t) ** 2 * cy + 2 * (1 - t) * t * my + t * t * ty) for t in [i / 24 for i in range(25)]]
        for j, (x, y) in enumerate(sp[1:], 1):
            px, py = sp[j - 1]; nx, ny = -(y - py), (x - px); n = math.hypot(nx, ny) or 1; wd = h * 0.05 * math.sin(math.pi * j / 25)
            d.polygon([(px, py), (x + nx / n * wd, y + ny / n * wd), (x, y)], fill=col + (255,))
        d.line(sp, fill=col + (255,), width=max(3, int(h * 0.008)))
    return im

# ---------- 1. Portail : façade de club néon + vortex ----------
def build_portal():
    base = gradient([(0, (10, 4, 30)), (0.55, (60, 10, 90)), (1, (20, 4, 40))]); stars(base, 60, 600)
    d = ImageDraw.Draw(base)
    d.rectangle([90, 1150, W - 90, H], fill=(28, 10, 48))  # façade
    for x in range(110, W - 110, 70): d.rectangle([x, 1180, x + 40, H], fill=(36, 14, 60))
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nd = ImageDraw.Draw(neon)
    nd.rounded_rectangle([150, 1180, W - 150, 1290], radius=30, outline=(255, 70, 190), width=8)
    nd.line([(90, 1150), (W - 90, 1150)], fill=(80, 230, 255), width=8)
    for k in range(5): nd.line([(130 + k * 200, 1330), (180 + k * 200, 1330)], fill=(80, 230, 255), width=6)
    neon = glow(neon, 14, 2)
    p1, p2 = palm(1000, 1), palm(850, -1).transpose(Image.FLIP_LEFT_RIGHT)
    def draw(t):
        im = base.copy(); vort = Image.new("RGBA", (W, H), (0, 0, 0, 0)); vd = ImageDraw.Draw(vort)
        cx, cy = W // 2, 700
        for k in range(18):  # anneaux du portail qui tournent
            r = 60 + k * 26 + 10 * math.sin(t * 3 + k); a0 = (t * (120 + k * 9) + k * 40) % 360
            col = (int(120 + 135 * (k % 2)), int(60 + 10 * k), 255)
            vd.arc([cx - r, cy - r * 1.15, cx + r, cy + r * 1.15], a0, a0 + 230, fill=col + (200,), width=10)
        vd.ellipse([cx - 70, cy - 80, cx + 70, cy + 80], fill=(255, 255, 255, 220))
        im.alpha_composite(glow(vort, 22, 2))
        flick = 0.85 + 0.15 * (math.sin(t * 17) > -0.8)
        n2 = neon.copy(); n2.putalpha(n2.getchannel("A").point(lambda v: int(v * flick))); im.alpha_composite(n2)
        im.alpha_composite(p1, (-330, H - 1000)); im.alpha_composite(p2, (W - 520, H - 850))
        return im
    return draw

# ---------- 2. Désert au crépuscule : route, cactus, poteaux, enseigne de motel ----------
def build_desert():
    base = gradient([(0, (40, 12, 60)), (0.42, (220, 80, 80)), (0.58, (255, 170, 90)), (0.6, (60, 24, 40)), (1, (30, 12, 26))]); stars(base, 30, 380)
    d = ImageDraw.Draw(base)
    sun_y = int(H * 0.5)
    d.ellipse([W // 2 - 230, sun_y - 230, W // 2 + 230, sun_y + 230], fill=(255, 200, 110))
    d.rectangle([0, int(H * 0.6), W, H], fill=(52, 20, 34))
    for i in range(6):  # mesas au loin
        x = i * 220 - 60; d.polygon([(x, int(H * 0.6)), (x + 40, int(H * 0.53) + (i % 3) * 20), (x + 170, int(H * 0.53) + (i % 3) * 20), (x + 210, int(H * 0.6))], fill=(110, 40, 60))
    def cactus(x, y, s):
        d.rounded_rectangle([x, y - 300 * s, x + 60 * s, y], radius=int(28 * s), fill=INK)
        d.rounded_rectangle([x - 70 * s, y - 210 * s, x - 20 * s, y - 120 * s], radius=int(22 * s), fill=INK)
        d.rectangle([x - 40 * s, y - 140 * s, x + 10 * s, y - 110 * s], fill=INK)
        d.rounded_rectangle([x + 80 * s, y - 250 * s, x + 130 * s, y - 160 * s], radius=int(22 * s), fill=INK)
        d.rectangle([x + 50 * s, y - 180 * s, x + 110 * s, y - 150 * s], fill=INK)
    cactus(90, H - 120, 1.4); cactus(W - 230, H - 260, 0.9)
    for k in range(7):  # poteaux électriques
        x = 150 + k * 140; top = int(H * 0.6) - 260 + k * 20; d.line([(x, top), (x, int(H * 0.6) + 10)], fill=INK, width=6); d.line([(x - 30, top + 20), (x + 30, top + 20)], fill=INK, width=5)
    sign = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sign)
    sd.rounded_rectangle([700, 1060, 960, 1150], radius=16, outline=(255, 90, 160), width=7); sd.line([(830, 1150), (830, 1300)], fill=INK, width=10)
    sd.line([(730, 1105), (930, 1105)], fill=(80, 230, 255), width=7)
    sign = glow(sign, 10, 2)
    def draw(t):
        im = base.copy(); dd = ImageDraw.Draw(im)
        road_top = int(H * 0.6)
        dd.polygon([(W // 2 - 20, road_top), (W // 2 + 20, road_top), (W - 60, H), (60, H)], fill=(36, 14, 30))
        off = (t * 1.6) % 1
        for k in range(10):  # lignes de route qui défilent
            z0, z1 = (k + off) / 10, (k + off + 0.45) / 10
            y0, y1 = road_top + (H - road_top) * z0 ** 2, road_top + (H - road_top) * z1 ** 2
            w0, w1 = 3 + 20 * z0, 3 + 20 * z1
            dd.polygon([(W // 2 - w0, y0), (W // 2 + w0, y0), (W // 2 + w1, y1), (W // 2 - w1, y1)], fill=(255, 210, 90))
        flick = 1 if math.sin(t * 9) > -0.9 else 0.4
        s2 = sign.copy(); s2.putalpha(s2.getchannel("A").point(lambda v: int(v * flick))); im.alpha_composite(s2)
        return im
    return draw

# ---------- 3. Banlieue la nuit : maisons, lampadaires, lune, palmiers ----------
def build_suburb():
    base = gradient([(0, (6, 10, 34)), (0.6, (40, 30, 90)), (0.69, (110, 60, 140)), (0.7, (18, 10, 30)), (1, (12, 6, 22))]); stars(base, 110, 900)
    d = ImageDraw.Draw(base)
    d.ellipse([720, 260, 900, 440], fill=(240, 235, 255)); d.ellipse([760, 250, 930, 420], fill=(30, 26, 80))  # croissant de lune
    ground = int(H * 0.7)
    houses = [(40, 300, 230), (380, 320, 260), (740, 300, 220)]
    for x, w, h in houses:
        d.rectangle([x, ground - h, x + w, ground], fill=(26, 16, 50)); d.polygon([(x - 20, ground - h), (x + w / 2, ground - h - 110), (x + w + 20, ground - h)], fill=(20, 12, 40))
        d.rectangle([x + w * 0.38, ground - 110, x + w * 0.62, ground], fill=(14, 8, 26))
    win = Image.new("RGBA", (W, H), (0, 0, 0, 0)); wd = ImageDraw.Draw(win)
    for x, w, h in houses:
        for wx in (x + 30, x + w - 90):
            wd.rectangle([wx, ground - h + 50, wx + 60, ground - h + 120], fill=(255, 200, 110, 255))
    win = glow(win, 12, 1)
    lamp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lamp)
    for lx in (300, 760):
        ld.line([(lx, ground + 260), (lx, ground - 120)], fill=INK, width=10); ld.ellipse([lx - 24, ground - 150, lx + 24, ground - 104], fill=(255, 220, 150, 255))
    lamp = glow(lamp, 24, 2)
    pl = palm(900, 1); pr = palm(760, -1).transpose(Image.FLIP_LEFT_RIGHT)
    def draw(t):
        im = base.copy(); dd = ImageDraw.Draw(im); dd.rectangle([0, ground, W, H], fill=(18, 10, 30))
        w2 = win.copy()
        # une fenêtre qui clignote : quelqu'un est là...
        if math.sin(t * 2.2) > 0.6: ImageDraw.Draw(w2).rectangle([380 + 30, ground - 260 + 50, 380 + 90, ground - 260 + 120], fill=(0, 0, 0, 0))
        im.alpha_composite(w2); im.alpha_composite(lamp)
        fog = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fog)
        for k in range(4):
            y = ground + 40 + k * 60; x = int((t * 40 * (k + 1)) % (W + 600)) - 600
            fd.ellipse([x, y, x + 900, y + 90], fill=(180, 160, 255, 26))
        im.alpha_composite(fog.filter(ImageFilter.GaussianBlur(20)))
        im.alpha_composite(pl, (-300, H - 900)); im.alpha_composite(pr, (W - 470, H - 760))
        return im
    return draw

SCENES = {"portal": build_portal, "desert": build_desert, "suburb": build_suburb}
