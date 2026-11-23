"""Vice City Times v3 : même ADN, mais chaque Short a son ambiance (couleurs, transitions, musique, bruitage).
Usage : python3 vct_v3.py DOSSIER_SORTIE [nom_du_short ...]"""
import glob, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vct_audio

ANTON = os.path.join(HERE, "fonts/anton-latin-400-normal.woff2")
SCRIPT = os.path.join(HERE, "fonts/yellowtail-latin-400-normal.woff2")
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POPB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
W, H, FPS = 1080, 1920, 30
HANDLE = "@ViceCitytimes6"
WHITE, INK = (255, 255, 255), (16, 6, 28)
_fc = {}
def F(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * max(0, min(1, t))) for i in range(3))

# Ambiances visuelles : même ADN (soleil rayé, ville, grille, typo), couleurs et transitions différentes
LOOKS = {
    "mystery": dict(top=(8, 10, 40), mid=(60, 30, 120), low=(40, 170, 200), sun=((150, 240, 255), (120, 80, 220)),
                    grid=(80, 220, 255), accent=(90, 230, 255), accent_ink=INK, hi=(130, 245, 255), shadow=(90, 40, 180), trans="dark_zoom"),
    "hype": dict(top=(30, 10, 58), mid=(200, 50, 150), low=(255, 150, 90), sun=((255, 218, 80), (255, 70, 130)),
                 grid=(255, 60, 200), accent=(255, 64, 160), accent_ink=WHITE, hi=(255, 218, 80), shadow=(255, 64, 160), trans="glitch"),
    "rumor": dict(top=(20, 4, 30), mid=(150, 20, 80), low=(255, 90, 80), sun=((255, 120, 90), (200, 20, 90)),
                  grid=(255, 50, 110), accent=(255, 50, 90), accent_ink=WHITE, hi=(255, 210, 90), shadow=(180, 20, 70), trans="wipe"),
    "tips": dict(top=(60, 16, 70), mid=(240, 90, 90), low=(255, 190, 90), sun=((255, 240, 150), (255, 110, 70)),
                 grid=(255, 170, 70), accent=(255, 218, 80), accent_ink=INK, hi=(255, 218, 80), shadow=(230, 60, 90), trans="slide"),
}
HOR = 1100

def build_look(L):
    sky = Image.new("RGB", (W, H)); d = ImageDraw.Draw(sky)
    for y in range(H):
        t = min(y / HOR, 1)
        c = lerp(L["top"], L["mid"], t / 0.7) if t < 0.7 else lerp(L["mid"], L["low"], (t - 0.7) / 0.3)
        if y > HOR: c = lerp(INK, (30, 10, 50), 0.5)
        d.line([(0, y), (W, y)], fill=c)
    rng = np.random.default_rng(5)
    for _ in range(90):
        x, y = rng.integers(0, W), rng.integers(0, 650); r = int(rng.choice([1, 1, 2]))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 255))
    r = 300; sun = Image.new("RGB", (2 * r, 2 * r)); sd = ImageDraw.Draw(sun)
    for y in range(2 * r): sd.line([(0, y), (2 * r, y)], fill=lerp(L["sun"][0], L["sun"][1], y / (2 * r)))
    m = Image.new("L", (2 * r, 2 * r), 0); md = ImageDraw.Draw(m); md.ellipse([0, 0, 2 * r, 2 * r], fill=255)
    y, gap = int(r * 1.05), 5
    while y < 2 * r: md.rectangle([0, y, 2 * r, y + gap], fill=0); y += 38; gap += 4
    city = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(city); x, s = 0, 11
    while x < W:
        s = (s * 1103515245 + 12345) % 2**31; bw = 35 + s % 80; bh = 60 + s % 220
        cd.rectangle([x, 300 - bh, x + bw, 300], fill=(22, 8, 40, 255))
        for wy in range(300 - bh + 12, 290, 22):
            for wx in range(x + 8, x + bw - 8, 16):
                if (wx * 7 + wy * 3 + s) % 5 == 0: cd.rectangle([wx, wy, wx + 5, wy + 8], fill=L["accent"] + (190,))
        x += bw + 3
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0)); vd = ImageDraw.Draw(veil)
    for y in range(440, 1380): vd.line([(0, y), (W, y)], fill=(14, 4, 26, int(115 * math.sin(math.pi * (y - 440) / 940))))
    return dict(sky=sky.convert("RGBA"), sun=sun, sunm=m, city=city, veil=veil)

def background(L, B, t):
    im = B["sky"].copy(); im.paste(B["sun"], (W // 2 - 300, HOR - 520 + int(10 * math.sin(t))), B["sunm"])
    im.alpha_composite(B["city"], (0, HOR - 290)); d = ImageDraw.Draw(im)
    sp = (t * 1.2) % 1
    for k in range(14):
        z = (k + sp) / 14; y = HOR + int((H - HOR) * z ** 2.2); d.line([(0, y), (W, y)], fill=L["grid"], width=2 + int(3 * z))
    for k in range(-12, 13): d.line([(W / 2 + k * 18, HOR), (W / 2 + k * 260, H)], fill=L["grid"], width=2)
    im.alpha_composite(B["veil"]); return im

def parse(text):
    out, inside = [], False
    for w in text.split():
        starts = w.startswith("*"); ends = w.rstrip(".,?:!'\"").endswith("*"); hi = inside or starts
        if starts and not ends: inside = True
        if ends: inside = False
        out.append((w.replace("*", ""), hi))
    return out

def captions(L, layer, text, shown, size):
    d = ImageDraw.Draw(layer); words = parse(text)
    while True:
        f = F(ANTON, size); lines, cur = [], []
        for w, _ in words:
            if cur and d.textlength(" ".join(cur + [w]), font=f) > W - 170: lines.append(cur); cur = [w]
            else: cur.append(w)
        lines.append(cur)
        if len(lines) * size * 1.06 <= 700 or size < 80: break
        size -= 6
    y = 900 - len(lines) * size * 1.06 / 2; idx = 0
    for ln in lines:
        x = (W - d.textlength(" ".join(ln), font=f)) / 2
        for _ in ln:
            word, hi = words[idx]
            if idx < shown:
                d.text((x + 7, y + 7), word, font=f, fill=L["shadow"])
                d.text((x, y), word, font=f, fill=L["hi"] if hi else WHITE, stroke_width=4, stroke_fill=INK)
            x += d.textlength(word + " ", font=f); idx += 1
        y += size * 1.06

def sticker(L, im, text, st):
    a = min(max(st / 0.2, 0), 1)
    if a <= 0: return
    f = F(ANTON, 84); tmp = Image.new("RGBA", (800, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=f); d.rounded_rectangle([10, 10, tw + 80, 150], radius=26, fill=L["accent"] + (255,))
    d.text((45, 24), text, font=f, fill=L["accent_ink"], stroke_width=2 if L["accent_ink"] == WHITE else 0, stroke_fill=INK)
    tmp = tmp.rotate(4, resample=Image.BICUBIC, expand=True)
    s = 0.6 + 0.4 * (1 - (1 - a) ** 3) + 0.08 * math.sin(a * math.pi)
    tmp = tmp.resize((int(tmp.width * s), int(tmp.height * s)), Image.BICUBIC); im.alpha_composite(tmp, (60, 330))

def transition(L, rgb, st):
    k = L["trans"]
    if k == "glitch" and st < 0.12:
        r, g, b = rgb.split(); sh = int(18 * (1 - st / 0.12))
        rgb = Image.merge("RGB", (ImageChops.offset(r, sh, 0), g, ImageChops.offset(b, -sh, 0)))
        return Image.blend(rgb, Image.new("RGB", (W, H), WHITE), 0.3 * (1 - st / 0.12))
    if k == "dark_zoom" and st < 0.3:  # sortie du noir avec zoom doux et flou léger
        p = st / 0.3; z = 1.12 - 0.12 * (1 - (1 - p) ** 2)
        big = rgb.resize((int(W * z), int(H * z)), Image.BILINEAR); ox, oy = (big.width - W) // 2, (big.height - H) // 2
        rgb = big.crop((ox, oy, ox + W, oy + H))
        if p < 0.5: rgb = rgb.filter(ImageFilter.BoxBlur(int(8 * (1 - p * 2))))
        return Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), rgb, 0.35 + 0.65 * p)
    if k == "slide" and st < 0.18:  # la nouvelle carte glisse depuis la droite
        p = 1 - (1 - st / 0.18) ** 3; off = int(W * (1 - p))
        bg = Image.new("RGB", (W, H), lerp(L["top"], INK, 0.3)); bg.paste(rgb, (off, 0)); return bg
    if k == "wipe" and st < 0.22:  # barre lumineuse qui balaie l'écran de gauche à droite
        p = st / 0.22; x = int(W * p); base = Image.new("RGB", (W, H), (20, 4, 30)); base.paste(rgb.crop((0, 0, x, H)), (0, 0))
        d = ImageDraw.Draw(base); d.rectangle([x - 14, 0, x + 14, H], fill=L["accent"]); return base
    return rgb

def render(name, look, segs, credit, out_dir):
    L = LOOKS[look]; B = build_look(L)
    bpm = vct_audio.THEMES[look]["bpm"]; beat = 60 / bpm
    durs = [nb * beat for _, _, nb in segs]; total = sum(durs); starts = [0] + list(np.cumsum(durs)[:-1])
    wav = os.path.join(out_dir, name + ".wav"); vct_audio.write(wav, look, total, starts[1:])
    mp4 = os.path.join(out_dir, name + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    for fr in range(int(total * FPS)):
        t = fr / FPS; i = max(j for j, s in enumerate(starts) if s <= t + 1e-9); st = t - starts[i]
        kicker, text, _ = segs[i]; hook = i == 0
        im = background(L, B, t); layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shown = len(text.split()) if (hook and st > 0.05) else int(st / (0.11 if hook else 0.16)) + 1
        captions(L, layer, text, shown, 150 if hook else 118); im.alpha_composite(layer)
        if kicker: sticker(L, im, kicker, st)
        d = ImageDraw.Draw(im); n = len(segs); gw = (W - 120 - (n - 1) * 10) / n
        for j in range(n):
            x0 = 60 + j * (gw + 10); d.rounded_rectangle([x0, 60, x0 + gw, 70], radius=5, fill=(255, 255, 255, 80))
            pr = 1 if j < i else (st / durs[i] if j == i else 0)
            if pr > 0: d.rounded_rectangle([x0, 60, x0 + gw * min(pr, 1), 70], radius=5, fill=WHITE)
        d.text((60, 90), "Vice City Times", font=F(SCRIPT, 62), fill=WHITE)
        if look == "rumor":  # badge permanent : on assume que c'est une rumeur
            bf = F(ANTON, 46); bt = "RUMOR · NOT CONFIRMED"; bw = d.textlength(bt, font=bf)
            d.rounded_rectangle([W - bw - 100, 96, W - 50, 170], radius=16, fill=(255, 255, 255)); d.text((W - bw - 75, 104), bt, font=bf, fill=(200, 20, 70))
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([40, 1335, 760, 1450], radius=24, fill=(14, 4, 26, 190)); im.alpha_composite(pill)
        d = ImageDraw.Draw(im); d.text((62, 1345), HANDLE, font=F(POPB, 40), fill=WHITE); d.text((62, 1397), credit, font=F(POP, 27), fill=(255, 225, 240))
        rgb = im.convert("RGB")
        bp = (t % beat) / beat; punch = 0.03 * max(0, 1 - bp / 0.25) if (look != "mystery" and int(t / beat) % 2 == 0) else 0
        if punch > 0.001:
            z = 1 + punch; big = rgb.resize((int(W * z), int(H * z)), Image.BILINEAR); ox, oy = (big.width - W) // 2, (big.height - H) // 2
            rgb = big.crop((ox, oy, ox + W, oy + H))
        if i > 0: rgb = transition(L, rgb, st)
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait(); os.remove(wav); return total

# nb = durée de chaque étape en temps (beats) ; *mots* = surlignés
SHORTS = {
 "vct3-04-pc-rumor": ("rumor", [
   (None, "GTA 6 ON PC *WAY SOONER* THAN GTA 5?", 4),
   ("THE REPORT", "4 SOURCES TOLD GAMESBEAT: PC IN *JANUARY TO MARCH 2027*", 7),
   ("THE ANALYST", "MICHAEL PACHTER BETS ON *SPRING 2027*", 5),
   ("FOR CONTEXT", "GTA 5 TOOK *19 MONTHS* TO HIT PC. RED DEAD 2 TOOK *ABOUT A YEAR*", 7),
   ("OFFICIAL", "ROCKSTAR HAS *NOT* ANNOUNCED A PC VERSION. YET.", 5),
   ("WARNING", "\"GTA 6 PC\" DOWNLOADS ONLINE TODAY = *SCAMS AND MALWARE*", 6),
   (None, "FOLLOW: WE POST THE *MINUTE* IT'S OFFICIAL", 4)], "Rumor via GamesBeat & Gameblog · not confirmed by Rockstar"),
 "vct3-01-egg-secret": ("mystery", [
   (None, "PLAYERS FOUND A *SECRET* *CUTSCENE* IN GTA 6", 4),
   ("STEP 1", "CLIMB ONE OF THE *TALLEST* RADIO TOWERS", 5),
   ("STEP 2", "IT TAKES AROUND *7 MINUTES* TO REACH THE TOP", 5),
   ("STEP 3", "UP THERE: A NEST WITH *COLORFUL EGGS*", 5),
   ("STEP 4", "THROW ONE AT A CAR ON THE ROAD *BELOW*", 5),
   ("THE PAYOFF", "A *VICE CITY* CALLBACK CUTSCENE PLAYS", 5),
   (None, "FOLLOW FOR MORE *GTA 6 SECRETS*", 4)], "Found by players · via GamingBible / TechRadar"),
 "vct3-02-gta7-tease": ("hype", [
   (None, "GTA 6 IS ALREADY *TEASING* *GTA 7*?", 4),
   ("WHERE", "OPEN *SNAPMATIC*, THE IN-GAME SOCIAL APP", 6),
   ("THE POST", "A USER IS MAD *BARNYARD BLUE* CAME OUT BEFORE *RACE AND CHASE 7*", 8),
   ("THE CATCH", "RACE AND CHASE WAS THE *ORIGINAL NAME* OF THE FIRST GTA", 7),
   ("SO", "RACE AND CHASE 7 = *GTA 7*. ROCKSTAR KNOWS WHAT IT'S DOING", 7),
   (None, "FOLLOW FOR *HIDDEN DETAILS* EVERY DAY", 4)], "Spotted by players · via Journal du Geek"),
 "vct3-03-never-tells-you": ("tips", [
   (None, "4 THINGS GTA 6 *NEVER* TELLS YOU", 4),
   ("#1", "GET WASTED OR ARRESTED AND YOU *LOSE YOUR CASH*. BANK IT AT AN ATM FIRST", 8),
   ("#2", "WANT TO *KEEP* A STOLEN CAR? *REGISTER* IT AT PAY 'N' SPRAY", 7),
   ("#3", "CAR TOO FAR? THE *SCOOTER BROS* APP DELIVERS IT", 6),
   ("#4", "MISSION NOT SHOWING UP? CHECK THE *MISSION LIST* ON THE MAP", 7),
   (None, "SAVE THIS. *FOLLOW* FOR PART 2", 4)], "Tips via TechRadar launch coverage"),
}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for nm in (sys.argv[2:] or list(SHORTS)):
        look, segs, credit = SHORTS[nm]; print("ok", nm, look, round(render(nm, look, segs, credit, out), 1), "s", flush=True)
