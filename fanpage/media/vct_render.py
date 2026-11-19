"""Vice City Times : rendu des visuels de marque et des Shorts (anglais)."""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FDIR = "/tmp/claude-0/-home-claude/2ab8e476-59d4-5325-8939-887b73990260/scratchpad/fonts"
ANTON = FDIR + "/fontsource-anton-5.3.0/package/files/anton-latin-400-normal.woff2"
SCRIPT = FDIR + "/fontsource-yellowtail-5.3.0/package/files/yellowtail-latin-400-normal.woff2"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POPB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
HANDLE = "@ViceCitytimes6"
F = lambda p, s: ImageFont.truetype(p, s)

TOP, MID, LOW = (38, 16, 66), (196, 62, 140), (255, 150, 92)
PINK, YEL, WHITE, INK = (255, 70, 160), (255, 214, 92), (255, 255, 255), (18, 8, 30)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def sky(w, h, horizon):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / horizon if y < horizon else 1
        c = lerp(TOP, MID, t / 0.6) if t < 0.6 else lerp(MID, LOW, (t - 0.6) / 0.4)
        d.line([(0, y), (w, y)], fill=c)
    return im

def sun(r):
    s = Image.new("RGB", (2 * r, 2 * r)); d = ImageDraw.Draw(s)
    for y in range(2 * r): d.line([(0, y), (2 * r, y)], fill=lerp(YEL, (255, 96, 120), y / (2 * r)))
    m = Image.new("L", (2 * r, 2 * r), 0); md = ImageDraw.Draw(m); md.ellipse([0, 0, 2 * r, 2 * r], fill=255)
    gap, y, k = 6, int(r * 1.0), 0
    while y < 2 * r:
        md.rectangle([0, y, 2 * r, y + gap], fill=0); k += 1; y += int(r * 0.16) - k * 2 + gap; gap += 3
    return s, m

def palm(h, lean=1):
    """Silhouette de palmier noire sur fond transparent."""
    w = int(h * 0.9); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bx, by = w // 2, h; cx, cy = w // 2 + lean * int(h * 0.12), int(h * 0.18)
    pts = []
    for i in range(41):
        t = i / 40; x = (1 - t) ** 2 * bx + 2 * (1 - t) * t * (bx + lean * h * 0.02) + t * t * cx
        y = (1 - t) ** 2 * by + 2 * (1 - t) * t * (h * 0.55) + t * t * cy
        pts.append((x, y)); r = int(h * 0.028 * (1 - 0.55 * t)) + 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=INK + (255,))
    for ang in (-170, -140, -110, -70, -40, -10, 15):
        a = math.radians(ang); L = h * 0.42
        tipx, tipy = cx + math.cos(a) * L, cy + math.sin(a) * L * 0.55 + L * 0.35
        midx, midy = cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5 - h * 0.04
        spine = [((1 - t) ** 2 * cx + 2 * (1 - t) * t * midx + t * t * tipx, (1 - t) ** 2 * cy + 2 * (1 - t) * t * midy + t * t * tipy) for t in [i / 24 for i in range(25)]]
        for j, (x, y) in enumerate(spine[1:], 1):
            px, py = spine[j - 1]; nx, ny = -(y - py), (x - px); n = math.hypot(nx, ny) or 1
            wdt = h * 0.05 * math.sin(math.pi * j / 25)
            d.polygon([(px, py), (x + nx / n * wdt, y + ny / n * wdt), (x, y), (x - nx / n * wdt * 0.3, y - ny / n * wdt * 0.3)], fill=INK + (255,))
        d.line(spine, fill=INK + (255,), width=max(3, int(h * 0.008)))
    return im

def skyline(w, h, seed=7):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 0; s = seed
    while x < w:
        s = (s * 1103515245 + 12345) % 2**31; bw = 40 + s % 90; bh = int(h * (0.25 + (s % 1000) / 1600))
        d.rectangle([x, h - bh, x + bw, h], fill=(30, 10, 48, 255)); x += bw + 4
    return im

def scanlines(w, h):
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for y in range(0, h, 4): d.line([(0, y), (w, y)], fill=22)
    return m

def wrap(d, text, font, maxw):
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: out.append(cur); cur = word
    out.append(cur); return out

def shadow_text(base, xy, text, font, fill, shadow=PINK, off=6):
    d = ImageDraw.Draw(base)
    d.text((xy[0] + off, xy[1] + off), text, font=font, fill=shadow)
    d.text(xy, text, font=font, fill=fill, stroke_width=3, stroke_fill=INK)

# ---------- marque ----------
def avatar():
    S = 1080; im = sky(S, S, int(S * 0.8)).convert("RGBA")
    s, m = sun(300); im.paste(s, (240, 170), m)
    sk = skyline(S, 260); im.alpha_composite(sk, (0, S - 260))
    p1 = palm(820, 1); im.alpha_composite(p1, (-160, S - 820))
    p2 = palm(620, -1).transpose(Image.FLIP_LEFT_RIGHT); im.alpha_composite(p2, (S - 470, S - 620))
    d = ImageDraw.Draw(im); f = F(SCRIPT, 230); t = "VCT"; w = d.textlength(t, font=f)
    shadow_text(im, ((S - w) / 2, 560), t, f, WHITE, off=8)
    im.convert("RGB").save(f"{OUT}/avatar-vice-city-times.png")

def banner():
    W, H = 2560, 1440; im = sky(W, H, 1000).convert("RGBA")
    s, m = sun(330); im.paste(s, (W // 2 - 330, 380), m)
    im.alpha_composite(skyline(W, 420), (0, H - 420))
    im.alpha_composite(palm(1100, 1), (420, H - 1100)); im.alpha_composite(palm(900, -1).transpose(Image.FLIP_LEFT_RIGHT), (W - 1220, H - 900))
    d = ImageDraw.Draw(im); f = F(SCRIPT, 210); t = "Vice City Times"; w = d.textlength(t, font=f)
    shadow_text(im, ((W - w) / 2, 520), t, f, WHITE, off=9)
    f2 = F(ANTON, 70); t2 = "GTA 6 TIPS  •  HIDDEN SECRETS  •  VERIFIED NEWS"; w2 = d.textlength(t2, font=f2)
    d.text(((W - w2) / 2, 790), t2, font=f2, fill=WHITE, stroke_width=3, stroke_fill=INK)
    f3 = F(POP, 34); t3 = "Fan page · not affiliated with Rockstar Games"; w3 = d.textlength(t3, font=f3)
    d.text(((W - w3) / 2, 890), t3, font=f3, fill=(255, 230, 240))
    im.convert("RGB").save(f"{OUT}/banner-vice-city-times-2560x1440.png")

# ---------- Shorts ----------
W, H, FPS = 1080, 1920, 30
BG_SKY = sky(W, H + 200, 1450).convert("RGBA")
SUN, SUNM = sun(330)
SKY_L = skyline(W, 380)
PALM_L = palm(1150, 1); PALM_R = palm(950, -1).transpose(Image.FLIP_LEFT_RIGHT)
SCAN = scanlines(W, H)
VIGN = Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - int(min(v, 255) * 0.45))

def ease(t): return 1 - (1 - min(max(t, 0), 1)) ** 3

def frame(t, total, seg_i, seg_t, segs, slide):
    im = BG_SKY.crop((0, int(100 - 60 * t / total), W, int(100 - 60 * t / total) + H)).copy()
    sy = int(1080 - 120 * t / total); im.paste(SUN, (W // 2 - 330, sy), SUNM)
    im.alpha_composite(SKY_L, (0, H - 380))
    sway = math.sin(t * 1.6) * 1.2
    pl = PALM_L.rotate(sway, center=(PALM_L.width // 2, PALM_L.height), resample=Image.BICUBIC)
    pr = PALM_R.rotate(-sway, center=(PALM_R.width // 2, PALM_R.height), resample=Image.BICUBIC)
    im.alpha_composite(pl, (-330, H - 1150 + 40)); im.alpha_composite(pr, (W - 560, H - 950 + 60))
    # voile sombre derrière le texte pour la lisibilité
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0)); vd = ImageDraw.Draw(veil)
    vd.rounded_rectangle([60, 470, W - 60, 1290], radius=40, fill=(18, 8, 30, 150)); im.alpha_composite(veil)
    d = ImageDraw.Draw(im)
    # barres de progression façon stories
    n = len(segs); gw = (W - 120 - (n - 1) * 10) / n
    for i in range(n):
        x0 = 60 + i * (gw + 10); d.rounded_rectangle([x0, 70, x0 + gw, 80], radius=5, fill=(255, 255, 255, 90))
        p = 1 if i < seg_i else (seg_t / segs[i] if i == seg_i else 0)
        if p > 0: d.rounded_rectangle([x0, 70, x0 + gw * p, 80], radius=5, fill=WHITE)
    d.text((60, 105), "Vice City Times", font=F(SCRIPT, 64), fill=WHITE)
    kicker, text, hook = slide
    a = ease(seg_t / 0.35)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    if kicker: ld.text((110, 520), kicker, font=F(SCRIPT, 92 if not hook else 0 or 92), fill=YEL)
    size = 150 if hook else 112
    while True:
        f = F(ANTON, size); lines = wrap(ld, text, f, W - 220)
        if len(lines) * size * 1.08 <= 620 or size < 70: break
        size -= 6
    y = 640 + (620 - len(lines) * size * 1.08) / 2 - (40 if not kicker else 0)
    for l in lines:
        ld.text((110 + 6, y + 6), l, font=f, fill=PINK); ld.text((110, y), l, font=f, fill=WHITE, stroke_width=3, stroke_fill=INK); y += size * 1.08
    sc = 0.88 + 0.12 * a
    lw, lh = int(W * sc), int(H * sc); lay = layer.resize((lw, lh), Image.BICUBIC)
    alpha = lay.getchannel("A").point(lambda v: int(v * a)); lay.putalpha(alpha)
    im.alpha_composite(lay, ((W - lw) // 2, (H - lh) // 2))
    pill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([40, 1322, 700, 1432], radius=24, fill=(18, 8, 30, 170)); im.alpha_composite(pill)
    d = ImageDraw.Draw(im)
    d.text((60, 1335), HANDLE, font=F(POPB, 40), fill=WHITE)
    d.text((60, 1385), "Fan page · not affiliated with Rockstar Games", font=F(POP, 28), fill=(255, 225, 240))
    rgb = im.convert("RGB")
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    rgb = Image.composite(dark, rgb, SCAN)
    rgb = Image.composite(rgb, dark, VIGN)
    return rgb

def render(name, slides, segs):
    total = sum(segs); nfr = int(total * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", f"{OUT}/{name}.mp4"], stdin=subprocess.PIPE)
    for k in range(nfr):
        t = k / FPS; acc = 0
        for i, s in enumerate(segs):
            if t < acc + s or i == len(segs) - 1: break
            acc += s
        fr = frame(t, total, i, t - acc, segs, slides[i]); p.stdin.write(fr.tobytes())
        if k == int(0.6 * FPS) and name.endswith("01"): fr.save(f"{OUT}/_preview_{name}.png")
    p.stdin.close(); p.wait()

SHORTS = [
 ("vct-short-01", [
   (None, "GTA 6 IS OUT: 3 THINGS TO DO BEFORE YOU PLAY", True),
   ("Tip 1", "FREE UP SPACE. ON PS5 IT NEEDS UP TO 212 GB.", False),
   ("Tip 2", "BOUGHT THE BOX? IT HOLDS A DOWNLOAD CODE. NO DISC.", False),
   ("Tip 3", "STANDARD HAS THE FULL STORY. ULTIMATE ONLY ADDS EXTRAS.", False),
   (None, "FOLLOW FOR A NEW GTA 6 TIP EVERY DAY", True)], [2.2, 3.2, 3.4, 3.6, 2.4]),
 ("vct-short-02", [
   (None, "PS5 FULL? FREE UP SPACE FOR GTA 6", True),
   ("Step 1", "SETTINGS, THEN STORAGE, THEN CONSOLE STORAGE.", False),
   ("Step 2", "DELETE GAMES YOU FINISHED. YOUR SAVES STAY ON THE CONSOLE.", False),
   ("Step 3", "AIM FOR 212 GB FREE BEFORE YOU DOWNLOAD.", False),
   (None, "SAVE THIS SO YOU DON'T FORGET", True)], [2.2, 3.0, 3.6, 3.0, 2.2]),
 ("vct-short-03", [
   (None, "GTA 6 ON PC? THE REAL ANSWER", True),
   ("Right now", "GTA 6 IS ONLY ON PS5 AND XBOX SERIES X|S.", False),
   ("PC version", "ROCKSTAR HAS NOT ANNOUNCED A PC DATE.", False),
   ("Watch out", "SITES SELLING \"GTA 6 PC\" TODAY ARE SCAMS.", False),
   (None, "FOLLOW: WE POST THE MOMENT ROCKSTAR ANNOUNCES IT", True)], [2.2, 3.0, 3.0, 3.4, 2.6]),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    avatar(); banner()
    only = sys.argv[2:] or [s[0] for s in SHORTS]
    for name, slides, segs in SHORTS:
        if name in only: render(name, slides, segs); print("ok", name, sum(segs), "s")
