"""Vice City Times : musique synthwave originale et bruitages doux, une ambiance par thème."""
import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def lp(x, f, order=2): return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)

def reverb(x, secs=1.6, wet=0.22, seed=4):
    rng = np.random.default_rng(seed); n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 4.5); ir = lp(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
    return x * (1 - wet) + fftconvolve(x, ir)[: len(x)] * wet * 0.6

def adsr(n, a=0.005, d=0.1, s=0.6, r=0.1):
    t = np.arange(n) / SR; total = n / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((total - t) / r, 0, 1); return e * rel

def saw(f, n, detune=0.0):
    t = np.arange(n) / SR; return 2 * ((t * f * (1 + detune)) % 1) - 1

def tri(f, n):
    t = np.arange(n) / SR; return 2 * np.abs(2 * ((t * f) % 1) - 1) - 1

# Thèmes : tempo, accords (notes MIDI fondamentales + qualité), motif de mélodie (degrés en demi-tons, durées en croches)
THEMES = {
    # mystère / découverte : la mineur, calme et intrigant, mélodie en cloches
    "mystery": dict(bpm=96, key=57, prog=[(57, "m"), (53, "M"), (48, "M"), (55, "M")], lead="bell",
                    motif=[(12, 2), (15, 1), (19, 1), (17, 2), (15, 2), (12, 3), (10, 1), (12, 4), (None, 4),
                           (15, 2), (17, 1), (19, 1), (22, 2), (19, 2), (17, 2), (15, 2), (12, 4), (None, 4)],
                    hats=False, sfx="shimmer"),
    # hype / news : do majeur, énergique, mélodie lead chaude
    "hype": dict(bpm=116, key=60, prog=[(48, "M"), (55, "M"), (57, "m"), (53, "M")], lead="saw",
                 motif=[(16, 1), (19, 1), (24, 2), (23, 1), (21, 1), (19, 2), (16, 1), (19, 1), (21, 2), (19, 2), (None, 4),
                        (16, 1), (19, 1), (24, 2), (26, 1), (24, 1), (23, 2), (21, 2), (19, 4), (None, 2)],
                 hats=True, sfx="riser"),
    # astuces / liste : fa majeur, joyeux et rebondissant, pluck façon marimba
    "tips": dict(bpm=108, key=53, prog=[(53, "M"), (55, "M"), (52, "m"), (57, "m")], lead="pluck",
                 motif=[(12, 1), (16, 1), (19, 1), (16, 1), (21, 2), (19, 2), (16, 1), (14, 1), (12, 2), (None, 4),
                        (12, 1), (16, 1), (19, 1), (24, 1), (23, 2), (21, 2), (19, 1), (16, 1), (14, 2), (None, 4)],
                 hats=True, sfx="pop"),
}

def chord(root, q): return [root, root + (4 if q == "M" else 3), root + 7]

def song(theme, dur, seed=1):
    th = THEMES[theme]; beat = 60 / th["bpm"]; n = int(dur * SR) + SR
    rng = np.random.default_rng(seed)
    drums, bass, pad, lead, side = (np.zeros(n) for _ in range(5))
    def put(buf, sig, st):
        i = int(st * SR); j = min(n, i + len(sig))
        if 0 <= i < n: buf[i:j] += sig[: j - i]
    nbeats = int(dur / beat) + 2
    for b in range(nbeats):
        st = b * beat; bar = b // 4; root, q = th["prog"][bar % 4]
        # kick doux et rond
        m = int(0.4 * SR); x = np.arange(m) / SR; f = 45 + 70 * np.exp(-x * 30)
        k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 7); put(drums, k * 0.9, st)
        sc = 1 - 0.55 * np.exp(-np.arange(int(beat * SR)) / SR * 9); put(side, sc - 1, st)  # sidechain
        if b % 2 == 1:  # snare filtrée + réverb
            m = int(0.3 * SR); x = np.arange(m) / SR
            s = bp(rng.standard_normal(m), 900, 5000) * np.exp(-x * 14) * 0.5 + np.sin(2 * np.pi * 185 * x) * np.exp(-x * 22) * 0.4
            put(drums, s, st)
        if th["hats"]:
            for h in (0.5,):
                m = int(0.05 * SR); x = np.arange(m) / SR
                put(drums, hp(rng.standard_normal(m), 7000) * np.exp(-x * 70) * 0.06, st + h * beat)
        # basse : fondamentale en croches, filtrée chaude
        for k8 in range(2):
            m = int(beat / 2 * SR); f0 = hz(root - 12 + (12 if (k8 == 1 and b % 2 == 1) else 0))
            sg = saw(f0, m) * 0.6 + np.sin(2 * np.pi * f0 * np.arange(m) / SR) * 0.6
            put(bass, lp(sg, 380) * adsr(m, 0.004, 0.12, 0.5, 0.05) * 0.5, st + k8 * beat / 2)
    # nappe d'accords désaccordée et filtrée
    for bar in range(nbeats // 4 + 1):
        root, q = th["prog"][bar % 4]; m = int(4 * beat * SR)
        sg = sum(saw(hz(nt + 12), m, d) for nt in chord(root, q) for d in (-0.004, 0.004))
        put(pad, lp(sg, 1400, 4) * adsr(m, 0.25, 0.4, 0.8, 0.35) * 0.09, bar * 4 * beat)
    # mélodie
    t8 = beat / 2; pos = 0.0; i = 0; mot = th["motif"]
    while pos < dur:
        semi, ln = mot[i % len(mot)]; i += 1
        if semi is not None:
            bar = int(pos / (4 * beat)); root, _ = th["prog"][bar % 4]
            f0 = hz(th["key"] + semi); m = int(ln * t8 * SR); x = np.arange(m) / SR
            if th["lead"] == "bell":
                sg = (np.sin(2 * np.pi * f0 * x) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * x) * np.exp(-x * 6)) * np.exp(-x * 2.2) * 0.45
            elif th["lead"] == "saw":
                vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * x) * np.clip(x / 0.2, 0, 1)
                sg = lp(saw(f0, m) * 0.5 + tri(f0, m) * 0.5, 2600) * adsr(m, 0.01, 0.15, 0.7, 0.08) * 0.32
            else:  # pluck
                sg = (tri(f0, m) * 0.7 + np.sin(2 * np.pi * f0 * 2 * x) * 0.3) * np.exp(-x * 7) * 0.5
            put(lead, sg, pos)
        pos += ln * t8
    # délai sur la mélodie
    dl = int(beat * 0.75 * SR); echo = np.zeros(n); echo[dl:] = lead[:-dl] * 0.3; lead = lead + echo
    duck = 1 + np.clip(side, -0.6, 0)
    mix = drums * 0.8 + (bass * 0.9 + pad) * duck + reverb(lead, 1.8, 0.3) * 0.9
    mix = lp(reverb(mix, 1.2, 0.12), 9000)
    return mix[: int(dur * SR)], beat

def sfx(kind):
    if kind == "shimmer":  # montée douce de cloches inversées
        m = int(0.7 * SR); x = np.arange(m) / SR
        s = sum(np.sin(2 * np.pi * hz(nt) * x) for nt in (81, 84, 88, 93)) * (x / x[-1]) ** 2.5
        return reverb(s * 0.12, 1.0, 0.4), 0.65
    if kind == "riser":  # souffle filtré montant + impact grave
        m = int(0.6 * SR); x = np.arange(m) / SR; nz = np.random.default_rng(9).standard_normal(m)
        r = np.zeros(m)
        for k in range(6):
            a, b = int(k * m / 6), int((k + 1) * m / 6); c = 400 + 2600 * (k / 6)
            r[a:b] = bp(nz, c, c * 1.6)[a:b]
        r = lp(r, 4000) * (x / x[-1]) ** 2 * 0.25
        boom = np.sin(2 * np.pi * np.cumsum(55 + 40 * np.exp(-np.arange(int(0.5 * SR)) / SR * 20)) / SR) * np.exp(-np.arange(int(0.5 * SR)) / SR * 6) * 0.6
        return np.concatenate([r, boom]), 0.6
    # pop : petite bulle agréable
    m = int(0.18 * SR); x = np.arange(m) / SR; f = 900 * np.exp(-x * 9) + 300
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 22) * 0.35
    return s, 0.02

def write(path, theme, dur, cuts):
    a, beat = song(theme, dur); kind = THEMES[theme]["sfx"]; s, lead_in = sfx(kind)
    for c in cuts:
        i = int((c - lead_in) * SR); j = min(len(a), i + len(s))
        if i >= 0: a[i:j] += s[: j - i]
    f = int(0.6 * SR); a[-f:] *= np.linspace(1, 0, f); a[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    a = np.tanh(a / (np.max(np.abs(a)) + 1e-9) * 1.4) * 0.85
    st = (np.stack([a, a], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    return beat
