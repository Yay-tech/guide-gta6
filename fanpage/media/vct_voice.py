"""Vice City Times : Shorts avec voix off (ElevenLabs).
Les pauses de la voix découpent les étapes ; les sous-titres suivent la voix mot par mot ;
la musique baisse automatiquement quand la voix parle ; l'accroche est entièrement visible dès la 1re image.
Usage : python3 vct_voice.py DOSSIER_SORTIE nom_du_short chemin_voix.mp3"""
import os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vct_v3 as V, vct_audio as A
from vct_scenes import SCENES

def load_voice(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(A.SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768

def speech_intervals(v, thr_db=-35, min_sil=0.18):
    win = int(0.02 * A.SR); n = len(v) // win
    rms = np.sqrt(np.mean(v[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12); loud = 20 * np.log10(rms) > thr_db
    ints, start, sil = [], None, 0
    for i, on in enumerate(loud):
        t = i * win / A.SR
        if on:
            if start is None: start = t
            sil = 0
        elif start is not None:
            sil += win / A.SR
            if sil >= min_sil: ints.append((start, t - sil + win / A.SR)); start, sil = None, 0
    if start is not None: ints.append((start, n * win / A.SR))
    return ints

def word_times(text, s0, s1, speech):
    """Répartit les mots d'une étape sur les plages de parole entre s0 et s1, au prorata du nombre de lettres."""
    words = text.split(); parts = [(max(a, s0), min(b, s1)) for a, b in speech if b > s0 and a < s1]
    total = sum(b - a for a, b in parts) or (s1 - s0); parts = parts or [(s0, s1)]
    weights = [len(re.sub(r"[^A-Za-z0-9]", "", w)) + 1 for w in words]; cum = np.cumsum([0] + weights) / sum(weights)
    def at(frac):
        acc = 0
        for a, b in parts:
            d = (b - a) / total
            if frac <= acc + d + 1e-9: return a + (frac - acc) / d * (b - a) if d else a
            acc += d
        return parts[-1][1]
    return [at(c) for c in cum[:-1]]

def mix(voice, theme, total, cuts, out):
    music, _ = A.song(theme, total); music = music[: len(music)]
    n = int(total * A.SR); v = np.zeros(n); v[: min(n, len(voice))] = voice[:n]
    v = v / (np.max(np.abs(v)) + 1e-9) * 0.95
    env = np.convolve(np.abs(v), np.ones(int(0.15 * A.SR)) / int(0.15 * A.SR), "same")
    duck = 1 - 0.75 * np.clip(env / (np.percentile(env, 90) + 1e-9), 0, 1)
    m = np.zeros(n); m[: len(music)] = music[:n]; m = m / (np.max(np.abs(m)) + 1e-9) * 0.42 * duck
    s, lead_in = A.sfx(A.THEMES[theme]["sfx"])
    for c in cuts:
        i = int((c - lead_in) * A.SR); j = min(n, i + len(s))
        if i >= 0: m[i:j] += s[: j - i] * 0.45
    out_a = np.tanh((v + m) * 1.1) * 0.9
    f = int(0.25 * A.SR); out_a[-f:] *= np.linspace(1, 0, f)
    st = (np.stack([out_a, out_a], 1) * 32767).astype(np.int16)
    with wave.open(out, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(A.SR); w.writeframes(st.tobytes())

def render(name, look, segs, credit, voice_path, out_dir, hook_text):
    L = V.LOOKS[look]; B = V.build_look(L); music = L.get("music", look)
    scene = SCENES[L["scene"]]() if L.get("scene") else None
    veil = B["veil"].copy(); veil.putalpha(veil.getchannel("A").point(lambda a: int(a * 0.7)))
    voice = load_voice(voice_path); vdur = len(voice) / A.SR; speech = speech_intervals(voice)
    total = vdur + 0.35; starts = [s for s, _, _ in segs]; ends = starts[1:] + [total]
    timings = [word_times(txt, s0, s1, speech) for (s0, _, txt), s1 in zip(segs, ends)]
    beat = 60 / A.THEMES[music]["bpm"]
    wav = os.path.join(out_dir, name + ".wav"); mix(voice, music, total, starts[1:], wav)
    mp4 = os.path.join(out_dir, name + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{V.W}x{V.H}", "-r", str(V.FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    for fr in range(int(total * V.FPS)):
        t = fr / V.FPS; i = max(j for j, s in enumerate(starts) if s <= t + 1e-9); st = t - starts[i]
        _, kicker, text = segs[i]
        if scene: im = scene(t); im.alpha_composite(veil)
        else: im = V.background(L, B, t)
        layer = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0))
        if i == 0:  # accroche courte, entière dès la 1re image
            V.captions(L, layer, hook_text, 99, 170)
        else:
            shown = sum(1 for wt in timings[i] if wt <= t + 0.05)
            V.captions(L, layer, text, max(shown, 1), 116)
        im.alpha_composite(layer)
        if kicker: V.sticker(L, im, kicker, st)
        d = ImageDraw.Draw(im); n = len(segs); gw = (V.W - 120 - (n - 1) * 10) / n
        for j in range(n):
            x0 = 60 + j * (gw + 10); d.rounded_rectangle([x0, 60, x0 + gw, 70], radius=5, fill=(255, 255, 255, 80))
            pr = 1 if j < i else ((t - starts[i]) / (ends[i] - starts[i]) if j == i else 0)
            if pr > 0: d.rounded_rectangle([x0, 60, x0 + gw * min(pr, 1), 70], radius=5, fill=V.WHITE)
        d.text((60, 90), "Vice City Times", font=V.F(V.SCRIPT, 62), fill=V.WHITE)
        pill = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([40, 1335, 760, 1450], radius=24, fill=(14, 4, 26, 190)); im.alpha_composite(pill)
        d = ImageDraw.Draw(im); d.text((62, 1345), V.HANDLE, font=V.F(V.POPB, 40), fill=V.WHITE); d.text((62, 1397), credit, font=V.F(V.POP, 27), fill=(255, 225, 240))
        rgb = im.convert("RGB")
        bp = (t % beat) / beat; punch = 0.025 * max(0, 1 - bp / 0.25) if (music != "mystery" and int(t / beat) % 2 == 0) else 0
        if i == 0 and t < 0.25: punch = 0.08 * (1 - t / 0.25)  # petit zoom d'entrée
        if punch > 0.001:
            z = 1 + punch; big = rgb.resize((int(V.W * z), int(V.H * z)), Image.BILINEAR); ox, oy = (big.width - V.W) // 2, (big.height - V.H) // 2
            rgb = big.crop((ox, oy, ox + V.W, oy + V.H))
        if i > 0: rgb = V.transition(L, rgb, st)
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait(); os.remove(wav); return total

# Étapes calées sur les pauses de la voix : (début en s, étiquette, texte dit)
SHORTS = {
 "vct5-01-portal-voice": ("portal", "SECRET *PORTAL* TO *VICE CITY*", [
   (0.0, None, "GTA 6 HAS A SECRET PORTAL TO THE ORIGINAL VICE CITY."),
   (3.8, "STEP 1", "GO TO THE *BADGER RADIO TOWER* ON KEY LENTO."),
   (6.8, "STEP 2", "A *MALIBU CLUB* LOGO APPEARS ON A TV."),
   (9.5, "STEP 3", "NOW FIND *TWELVE POWER SUBSTATIONS* AND FLIP THEIR SWITCHES IN ORDER."),
   (13.5, "THE CODE", "THEIR LETTERS SPELL A CLASSIC VICE CITY CHEAT: *LIFE IS PASSING ME BY*"),
   (18.3, "THE REWARD", "YOUR REWARD? A TRIP TO *2002 VICE CITY*, PLUS *TOMMY'S SHIRT AND BIKE*."),
   (23.6, None, "*FOLLOW* FOR MORE.")], "Found by Memeio · via Forbes / Dot Esports"),
 "vct5-02-house-voice": ("suburb", "GTA 6 WAS HIDDEN IN *2021*", [
   (0.0, None, "ROCKSTAR SHOWED US GTA 6 IN 2021, AND NOBODY NOTICED."),
   (4.55, "2021", "THAT YEAR, A *PHOTO OF A HOUSE* WAS ADDED TO THE *SAN ANDREAS* REMASTER."),
   (8.8, "THE THEORY", "FANS CALLED IT A *SECRET FIRST LOOK* AT GTA 6."),
   (12.25, "NOW", "NOW PLAYERS FOUND THE *EXACT SAME HOUSE* IN GTA 6, IN *BELVILLE*."),
   (17.0, "BONUS", "AND ITS GARAGE HIDES A *CONSPIRACY* EASTER EGG."),
   (20.1, None, "*FOLLOW* FOR MORE HIDDEN DETAILS.")], "Found by the GTA Wiki mapping project · via VGC / Dexerto"),
}

if __name__ == "__main__":
    out, nm, vp = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    look, hook, segs, credit = SHORTS[nm]
    print("ok", nm, round(render(nm, look, segs, credit, vp, out, hook), 1), "s", flush=True)
