"""Vice City Times v2 : Shorts dynamiques (grille rétro animée, sous-titres mot par mot,
coups de zoom et glitch calés sur le tempo, musique synthwave originale générée).
Usage : python3 vct_v2.py DOSSIER_SORTIE [nom_du_short ...]
Option : mettre des images officielles dans media/official/ pour les utiliser en fond."""
import glob, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.environ.get("VCT_FONTS", "/tmp/claude-0/-home-claude/2ab8e476-59d4-5325-8939-887b73990260/scratchpad/fonts")
ANTON = FD + "/fontsource-anton-5.3.0/package/files/anton-latin-400-normal.woff2"
SCRIPT = FD + "/fontsource-yellowtail-5.3.0/package/files/yellowtail-latin-400-normal.woff2"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POPB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
W, H, FPS, BPM, SR = 1080, 1920, 30, 112, 44100
BEAT = 60 / BPM
HANDLE = "@ViceCitytimes6"
PINK, YEL, WHITE, INK, CYAN = (255, 64, 160), (255, 218, 80), (255, 255, 255), (16, 6, 28), (80, 230, 255)
_fc = {}
def F(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

# ---------------- musique originale ----------------
def synth(dur, seed=1):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    rng = np.random.default_rng(seed)
    def env(length, a=0.005, d=0.2):
        x = np.arange(int(length * SR)) / SR
        return np.minimum(x / a, 1) * np.exp(-x / d)
    def add(sig, start):
        i = int(start * SR); j = min(n, i + len(sig))
        if i < n: out[i:j] += sig[: j - i]
    roots = [45, 41, 36, 43]  # A, F, C, G (notes MIDI basses)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    beats = int(dur / BEAT) + 1
    for b in range(beats):
        st = b * BEAT; bar = b // 4; root = roots[bar % 4]
        # kick
        x = np.arange(int(0.35 * SR)) / SR; f = 50 + 90 * np.exp(-x * 28)
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) * 0.9, st)
        # snare sur 2 et 4
        if b % 2 == 1:
            x = np.arange(int(0.25 * SR)) / SR
            add((rng.standard_normal(len(x)) * 0.35 + np.sin(2 * np.pi * 190 * x) * 0.3) * np.exp(-x * 16), st)
        # charleston en croches
        for h in (0, 0.5):
            x = np.arange(int(0.06 * SR)) / SR; nz = rng.standard_normal(len(x))
            add(np.diff(np.concatenate([[0], nz])) * np.exp(-x * 60) * 0.12, st + h * BEAT)
        # basse en croches (onde en dent de scie filtrée)
        for k in range(2):
            x = np.arange(int(BEAT / 2 * SR)) / SR; fr = hz(root)
            saw = 2 * ((x * fr) % 1) - 1; saw = np.convolve(saw, np.ones(12) / 12, "same")
            add(saw * env(BEAT / 2, 0.003, 0.18)[: len(x)] * 0.32, st + k * BEAT / 2)
        # arpège en doubles croches
        chord = [root + 24, root + 28 if bar % 4 in (2, 3) else root + 27, root + 31, root + 36]
        for k in range(4):
            x = np.arange(int(BEAT / 4 * SR)) / SR; fr = hz(chord[(b * 4 + k) % 4])
            sq = np.sign(np.sin(2 * np.pi * fr * x)) * 0.5 + np.sin(2 * np.pi * fr * 2 * x) * 0.2
            add(sq * env(BEAT / 4, 0.002, 0.07)[: len(x)] * 0.10, st + k * BEAT / 4)
    # nappe
    for bar in range(beats // 4 + 1):
        root = roots[bar % 4]; x = np.arange(int(4 * BEAT * SR)) / SR
        pad = sum(np.sin(2 * np.pi * hz(root + 12 + iv) * x * (1 + d)) for iv in (0, 7, 12) for d in (-0.003, 0.003))
        add(pad * np.minimum(x / 0.4, 1) * np.minimum((4 * BEAT - x) / 0.4, 1) * 0.025, bar * 4 * BEAT)
    # écho simple
    dl = int(BEAT * 0.75 * SR); echo = np.zeros(n); echo[dl:] = out[:-dl] * 0.25; out += echo
    out /= np.max(np.abs(out)) + 1e-9
    return out * 0.85

def whoosh(dur=0.45):
    x = np.arange(int(dur * SR)) / SR; nz = np.random.default_rng(3).standard_normal(len(x))
    k = np.convolve(nz, np.ones(30) / 30, "same"); return k * np.sin(np.pi * x / dur) ** 2 * 0.6

def write_audio(path, dur, cuts):
    a = synth(dur)
    for c in cuts:
        w = whoosh(); i = max(0, int((c - 0.25) * SR)); j = min(len(a), i + len(w)); a[i:j] += w[: j - i]
    fade = int(0.4 * SR); a[-fade:] *= np.linspace(1, 0, fade)
    a = np.clip(a / (np.max(np.abs(a)) + 1e-9) * 0.9, -1, 1)
    st = (np.stack([a, a], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(st.tobytes())

# ---------------- décor ----------------
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
HOR = 1100
def make_sky():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = min(y / HOR, 1)
        c = lerp((30, 10, 58), (200, 50, 150), t / 0.7) if t < 0.7 else lerp((200, 50, 150), (255, 150, 90), (t - 0.7) / 0.3)
        if y > HOR: c = (22, 6, 40)
        d.line([(0, y), (W, y)], fill=c)
    rng = np.random.default_rng(5)
    for _ in range(90):
        x, y = rng.integers(0, W), rng.integers(0, 650); r = rng.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 230, 255))
    return im.convert("RGBA")
def make_sun(r=300):
    s = Image.new("RGB", (2 * r, 2 * r)); d = ImageDraw.Draw(s)
    for y in range(2 * r): d.line([(0, y), (2 * r, y)], fill=lerp(YEL, (255, 70, 130), y / (2 * r)))
    m = Image.new("L", (2 * r, 2 * r), 0); md = ImageDraw.Draw(m); md.ellipse([0, 0, 2 * r, 2 * r], fill=255)
    y, gap = int(r * 1.05), 5
    while y < 2 * r: md.rectangle([0, y, 2 * r, y + gap], fill=0); y += 38; gap += 4
    return s, m
def make_skyline():
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x, s = 0, 11
    while x < W:
        s = (s * 1103515245 + 12345) % 2**31; bw = 35 + s % 80; bh = 60 + s % 220
        d.rectangle([x, 300 - bh, x + bw, 300], fill=(26, 8, 46, 255))
        for wy in range(300 - bh + 12, 290, 22):
            for wx in range(x + 8, x + bw - 8, 16):
                if (wx * 7 + wy * 3 + s) % 5 == 0: d.rectangle([wx, wy, wx + 5, wy + 8], fill=(255, 200, 120, 200))
        x += bw + 3
    return im
def make_veil():
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(v)
    for y in range(440, 1380):
        a = int(110 * math.sin(math.pi * (y - 440) / 940)); d.line([(0, y), (W, y)], fill=(14, 4, 26, a))
    return v
VEIL = make_veil()
SKY = make_sky(); SUN, SUNM = make_sun(); SKYL = make_skyline()
OFFICIAL = sorted(glob.glob(os.path.join(HERE, "official", "*.[jp][pn]g")))

def background(t, seg_i):
    if OFFICIAL:  # images officielles en fond, effet Ken Burns
        src = Image.open(OFFICIAL[seg_i % len(OFFICIAL)]).convert("RGB")
        sc = max(W / src.width, H / src.height) * (1.12 + 0.05 * math.sin(t * 0.4))
        im = src.resize((int(src.width * sc), int(src.height * sc)), Image.BILINEAR)
        ox = int((im.width - W) / 2 + 40 * math.sin(t * 0.3)); oy = int((im.height - H) / 2)
        im = im.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        tint = Image.new("RGBA", (W, H), (60, 10, 80, 90)); im.alpha_composite(tint); return im
    im = SKY.copy(); im.paste(SUN, (W // 2 - 300, HOR - 520 + int(10 * math.sin(t))), SUNM)
    im.alpha_composite(SKYL, (0, HOR - 290))
    d = ImageDraw.Draw(im)
    speed = (t * 1.2) % 1
    for k in range(14):  # lignes horizontales de la grille qui avancent
        z = (k + speed) / 14; y = HOR + int((H - HOR) * z ** 2.2)
        d.line([(0, y), (W, y)], fill=(255, 60, 200), width=2 + int(3 * z))
    for k in range(-12, 13):  # lignes de fuite
        d.line([(W / 2 + k * 18, HOR), (W / 2 + k * 260, H)], fill=(255, 60, 200), width=2)
    return im

# ---------------- texte ----------------
def wrap_words(d, words, font, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and d.textlength(test, font=font) > maxw: lines.append(cur); cur = [w]
        else: cur.append(w)
    lines.append(cur); return lines

def parse(text):
    out, inside = [], False
    for w in text.split():
        starts = w.startswith("*"); ends = w.rstrip(".,?:!'\"").endswith("*")
        hi = inside or starts
        if starts and not ends: inside = True
        if ends: inside = False
        out.append((w.replace("*", ""), hi))
    return out

def captions(layer, text, shown, size, y0, hook):
    d = ImageDraw.Draw(layer); words = parse(text)
    while True:
        f = F(ANTON, size); lines = wrap_words(d, [w for w, _ in words], f, W - 170)
        if len(lines) * size * 1.06 <= 700 or size < 80: break
        size -= 6
    y = y0 - len(lines) * size * 1.06 / 2; idx = 0
    for ln in lines:
        lw = d.textlength(" ".join(ln), font=f); x = (W - lw) / 2
        for _ in ln:
            word, hi = words[idx]
            if idx < shown:
                d.text((x + 7, y + 7), word, font=f, fill=(200, 30, 110) if hi else PINK)
                d.text((x, y), word, font=f, fill=YEL if hi else WHITE, stroke_width=4, stroke_fill=INK)
            x += d.textlength(word + " ", font=f); idx += 1
        y += size * 1.06

def sticker(im, text, t_in):
    a = min(max(t_in / 0.2, 0), 1)
    if a <= 0: return
    f = F(ANTON, 84); tmp = Image.new("RGBA", (800, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=f); d.rounded_rectangle([10, 10, tw + 80, 150], radius=26, fill=PINK + (255,))
    d.text((40, 22), text, font=f, fill=WHITE, stroke_width=2, stroke_fill=INK)
    tmp = tmp.rotate(4, resample=Image.BICUBIC, expand=True)
    s = 0.6 + 0.4 * (1 - (1 - a) ** 3) + 0.08 * math.sin(a * math.pi)
    tmp = tmp.resize((int(tmp.width * s), int(tmp.height * s)), Image.BICUBIC)
    im.alpha_composite(tmp, (60, 330))

# ---------------- rendu ----------------
def render(name, segs, credit, out_dir):
    durs = [nb * BEAT for _, _, nb in segs]; total = sum(durs); cuts = list(np.cumsum(durs)[:-1])
    wav = os.path.join(out_dir, name + ".wav"); write_audio(wav, total, cuts)
    mp4 = os.path.join(out_dir, name + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    starts = [0] + cuts
    for k in range(int(total * FPS)):
        t = k / FPS; i = max(j for j, s in enumerate(starts) if s <= t + 1e-9); st = t - starts[i]
        kicker, text, _ = segs[i]; hook = i == 0
        im = background(t, i)
        im.alpha_composite(VEIL)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        nwords = len(text.split()); rate = 0.11 if hook else 0.16
        shown = nwords if hook and st > 0.05 else int(st / rate) + 1
        captions(layer, text, shown, 150 if hook else 118, 900, hook)
        im.alpha_composite(layer)
        if kicker: sticker(im, kicker, st)
        d = ImageDraw.Draw(im)
        n = len(segs); gw = (W - 120 - (n - 1) * 10) / n
        for j in range(n):
            x0 = 60 + j * (gw + 10); d.rounded_rectangle([x0, 60, x0 + gw, 70], radius=5, fill=(255, 255, 255, 80))
            pr = 1 if j < i else (st / durs[i] if j == i else 0)
            if pr > 0: d.rounded_rectangle([x0, 60, x0 + gw * min(pr, 1), 70], radius=5, fill=WHITE)
        d.text((60, 90), "Vice City Times", font=F(SCRIPT, 62), fill=WHITE)
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([40, 1335, 760, 1450], radius=24, fill=(14, 4, 26, 190)); im.alpha_composite(pill)
        d = ImageDraw.Draw(im)
        d.text((62, 1345), HANDLE, font=F(POPB, 40), fill=WHITE)
        d.text((62, 1397), credit, font=F(POP, 27), fill=(255, 220, 240))
        rgb = im.convert("RGB")
        # coup de zoom sur chaque temps fort
        bp = (t % BEAT) / BEAT; punch = 0.035 * max(0, 1 - bp / 0.25) if (int(t / BEAT) % 2 == 0) else 0
        if st < 0.2: punch = max(punch, 0.06 * (1 - st / 0.2))
        if punch > 0.001:
            z = 1 + punch; big = rgb.resize((int(W * z), int(H * z)), Image.BILINEAR)
            ox, oy = (big.width - W) // 2, (big.height - H) // 2; rgb = big.crop((ox, oy, ox + W, oy + H))
        # glitch RGB + flash aux coupes
        if st < 0.12 and i > 0:
            r, g, b = rgb.split(); sh = int(18 * (1 - st / 0.12))
            rgb = Image.merge("RGB", (ImageChops.offset(r, sh, 0), g, ImageChops.offset(b, -sh, 0)))
            rgb = Image.blend(rgb, Image.new("RGB", (W, H), WHITE), 0.35 * (1 - st / 0.12))
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    return total

# texte : les *mots* entre astérisques sont surlignés en jaune ; nb = durée en temps (beats)
SHORTS = {
 "vct2-01-egg-secret": ([
   (None, "PLAYERS FOUND A *SECRET* *CUTSCENE* IN GTA 6", 4),
   ("STEP 1", "CLIMB ONE OF THE *TALLEST* RADIO TOWERS", 6),
   ("STEP 2", "IT TAKES AROUND *7 MINUTES* TO REACH THE TOP", 6),
   ("STEP 3", "UP THERE: A NEST WITH *COLORFUL EGGS*", 6),
   ("STEP 4", "THROW ONE AT A CAR ON THE ROAD *BELOW*", 6),
   ("THE PAYOFF", "A *VICE CITY* CALLBACK CUTSCENE PLAYS", 6),
   (None, "FOLLOW FOR MORE *GTA 6 SECRETS*", 4)], "Found by players · via GamingBible / TechRadar"),
 "vct2-02-gta7-tease": ([
   (None, "GTA 6 IS ALREADY *TEASING* *GTA 7*?", 4),
   ("WHERE", "OPEN *SNAPMATIC*, THE IN-GAME SOCIAL APP", 6),
   ("THE POST", "A USER IS MAD *BARNYARD BLUE* CAME OUT BEFORE *RACE AND CHASE 7*", 8),
   ("THE CATCH", "RACE AND CHASE WAS THE *ORIGINAL NAME* OF THE FIRST GTA", 7),
   ("SO", "RACE AND CHASE 7 = *GTA 7*. ROCKSTAR KNOWS WHAT IT'S DOING", 7),
   (None, "FOLLOW FOR *HIDDEN DETAILS* EVERY DAY", 4)], "Spotted by players · via Journal du Geek"),
 "vct2-03-never-tells-you": ([
   (None, "4 THINGS GTA 6 *NEVER* TELLS YOU", 4),
   ("#1", "GET WASTED OR ARRESTED AND YOU *LOSE YOUR CASH*. BANK IT AT AN ATM FIRST", 8),
   ("#2", "WANT TO *KEEP* A STOLEN CAR? *REGISTER* IT AT PAY 'N' SPRAY", 7),
   ("#3", "CAR TOO FAR? THE *SCOOTER BROS* APP DELIVERS IT", 6),
   ("#4", "MISSION NOT SHOWING UP? CHECK THE *MISSION LIST* ON THE MAP", 7),
   (None, "SAVE THIS. *FOLLOW* FOR PART 2", 4)], "Tips via TechRadar launch coverage"),
}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    names = sys.argv[2:] or list(SHORTS)
    for nm in names:
        segs, credit = SHORTS[nm]; print("ok", nm, round(render(nm, segs, credit, out), 1), "s", flush=True)
