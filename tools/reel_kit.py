"""Shared toolkit for Jacob reels: characters, components, a tiny timeline engine, audio, export."""
import glob, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
from reel_lib import (W, H, FPS, INK, NAVY, ORANGE, MUTED, WHITE, ZEN_B, ZEN, KLEE, NUN, prog, ease_out,
                      ease_back, background, sticker, text_img, card, place, clock, speed_lines)

RED = (205, 78, 64)
GREEN = (60, 140, 96)

files = sorted(glob.glob("/mnt/user-data/uploads/ChatGPT*.png"))
_names = ['peace2', 'peace1', 'worried', 'happy', 'surprised', 'crying', 'thinking', 'cheer', 'yawn', 'fight',
          'peace2jump']
POSE = dict(zip(_names, files))
_cache = {}


def jacob(pose, height=760):
    key = (pose, height)
    if key not in _cache:
        _cache[key] = sticker(POSE[pose], height)
    return _cache[key]


BG = background()
LABEL = card([text_img("Talk with Jacob!", NUN(48), WHITE)], width=470, pad_y=18, border=NAVY, fill=NAVY)


def pop_in(p):
    return ease_back(p) if p < 1 else 1


# ---------- components ----------
def mark_x(size=360, color=RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m, w = size * 0.16, int(size * 0.13)
    d.line((m, m, size - m, size - m), fill=color, width=w)
    d.line((size - m, m, m, size - m), fill=color, width=w)
    return im


def mark_o(size=360, color=RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    w = int(size * 0.12)
    ImageDraw.Draw(im).ellipse((w, w, size - w, size - w), outline=color, width=w)
    return im


def choice(letter, text, width=840, highlight=None):
    """A quiz option row: lettered circle + English text on a paper card."""
    fill = WHITE if highlight is None else highlight
    h = 132
    im = Image.new("RGBA", (width + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 10 + width, 10 + h), 40, fill=fill, outline=INK, width=6)
    d.ellipse((34, 32, 34 + 88, 32 + 88), fill=NAVY)
    L = text_img(letter, NUN(56), WHITE)
    im.alpha_composite(L, (34 + 44 - L.width // 2, 32 + 44 - L.height // 2 - 2))
    T = text_img(text, NUN(60), INK)
    im.alpha_composite(T, (150, 10 + (h - T.height) // 2))
    return im


def countdown(size, frac, number):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = 18
    d.ellipse((w, w, size - w, size - w), fill=WHITE, outline=(226, 214, 198), width=w)
    if frac > 0:
        d.arc((w, w, size - w, size - w), -90, -90 + 360 * frac, fill=ORANGE, width=w)
    n = text_img(str(number), NUN(int(size * 0.42)), INK)
    im.alpha_composite(n, (size // 2 - n.width // 2, size // 2 - n.height // 2 - 4))
    return im


def badge(text, color=ORANGE, fg=WHITE, size=56):
    t = text_img(text, NUN(size), fg)
    im = Image.new("RGBA", (t.width + 60, t.height + 28), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=color)
    im.alpha_composite(t, (30, 14))
    return im


def phrase_card(en, ja, en_size=80, ja_size=54, width=840):
    return card([text_img(en, NUN(en_size), NAVY), text_img(ja, ZEN(ja_size), INK)], width=width)


# ---------- timeline engine ----------
class Reel:
    """Elements are (start, end, draw(frame, local_t, span)) drawn in order."""

    def __init__(self, dur):
        self.dur = dur
        self.items = []
        self.sfx = []      # (time, name, gain, pan)
        self.mute = []     # (start, end) BGM gaps

    def add(self, start, end, fn):
        self.items.append((start, end, fn))

    def sound(self, t, name, gain=0.45, pan=0.0):
        self.sfx.append((t, name, gain, pan))

    def frame(self, t):
        fr = BG.copy()
        place(fr, LABEL, 80 + LABEL.width / 2, 250, angle=2)
        for s, e, fn in self.items:
            if s <= t < e:
                fn(fr, t - s, e - s)
        return fr.convert("RGB")

    def stills(self, times, path):
        sheet = Image.new("RGB", (370 * len(times), 640), "black")
        for i, s in enumerate(times):
            sheet.paste(self.frame(s).resize((360, 640)), (i * 370, 0))
        sheet.save(path)

    def export(self, out, audio_kwargs=None):
        wav = out.replace(".mp4", ".wav")
        build_audio(self.dur, self.sfx, self.mute, wav, **(audio_kwargs or {}))
        n = int(self.dur * FPS)
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(FPS), "-i", "-", "-i", wav, "-shortest", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out,
        ], stdin=subprocess.PIPE)
        for i in range(n):
            ff.stdin.write(self.frame(i / FPS).tobytes())
        ff.stdin.close()
        ff.wait()


# ---------- common animated pieces ----------
def show(im, x, y, angle=0.0, pop=0.35, fade_out=0.0, bob=0.0, start_scale=1.0):
    def fn(fr, lt, span):
        a = prog(lt, 0, pop)
        out = 1 - prog(lt, span - fade_out, fade_out) if fade_out else 1
        sc = start_scale * pop_in(a)
        place(fr, im, x, y + bob * math.sin(lt * 3), scale=sc, angle=angle, alpha=min(1, a * 3) * out)
    return fn


def shake(im, x, y, amp=14, dur=0.8, pop=0.3):
    def fn(fr, lt, span):
        s = amp * math.sin(lt * 70) * (1 - prog(lt, 0, dur))
        place(fr, im, x + s, y, scale=pop_in(prog(lt, 0, pop)))
    return fn


def flash(fr, lt, span):
    a = 1 - prog(lt, 0, span)
    fr.alpha_composite(Image.new("RGBA", (W, H), WHITE + (int(255 * a * 0.85),)))


def qmarks(fr, lt, span):
    for k, (q, x, y, ang) in enumerate(((text_img("?", NUN(130), NAVY), 230, 860, 12),
                                        (text_img("?", NUN(96), ORANGE), 850, 900, -10))):
        qa = prog(lt, 0.2 * k, 0.3)
        place(fr, q, x, y - 14 * math.sin(lt * 5 + k), scale=pop_in(qa), angle=ang, alpha=min(1, qa * 3))


# ---------- audio ----------
SR = 44100
_rng = np.random.default_rng(7)


def _tt(d): return np.arange(int(d * SR)) / SR
def _env(d, a=0.005, decay=6.0):
    x = _tt(d); return np.exp(-x * decay) * np.clip(x / a, 0, 1)
def _hz(m): return 440 * 2 ** ((m - 69) / 12)
def _noise(d): return _rng.uniform(-1, 1, int(d * SR))
def _lp(s, k): return np.convolve(s, np.ones(k) / k, mode="same")


def _pluck(m, d=0.9, decay=5.0, bright=0.35):
    x = _tt(d); f = _hz(m)
    return (np.sin(2 * np.pi * f * x) + bright * np.sin(8 * np.pi * f * x) * np.exp(-x * 18)) * _env(d, 0.004, decay)


def _bass(m, d=0.6):
    x = _tt(d); f = _hz(m)
    return (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * _env(d, 0.01, 4.0)


def _sweep(f0, f1, d, decay):
    x = _tt(d); f = np.linspace(f0, f1, len(x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(d, 0.002, decay)


def _seq(notes, step, d=0.9, decay=6.0, bright=0.1):
    s = np.zeros(int((step * len(notes) + d) * SR))
    for j, m in enumerate(notes):
        tone = _pluck(m, d, decay, bright); i = int(j * step * SR); s[i:i + len(tone)] += tone
    return s


def _sfx(name):
    if name == "pop": return _sweep(420, 980, 0.11, 30)
    if name == "pop2": return _sweep(600, 1150, 0.08, 34)
    if name == "boing":
        x = _tt(0.45); f = 260 + 340 * (1 - np.exp(-x * 9)) + 18 * np.sin(2 * np.pi * 14 * x)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(0.45, 0.003, 7)
    if name == "buzzer":
        x = _tt(0.7); ph = (150 * x) % 1.0
        s = (2 * ph - 1) + 0.6 * (2 * ((153 * x) % 1.0) - 1)
        return _lp(s, 6) * np.clip(x / 0.01, 0, 1) * np.clip((0.7 - x) / 0.08, 0, 1)
    if name == "correct": return _seq([79, 84, 88, 91], 0.09, 0.8, 5.0, 0.15)
    if name == "tick": return _sweep(1800, 1700, 0.05, 80)
    if name == "drum":  # little reveal roll
        s = np.zeros(int(1.0 * SR))
        for j in range(14):
            hit = _lp(_noise(0.06), 4) * _env(0.06, 0.001, 50) * (0.4 + j / 20)
            i = int(j * 0.065 * SR); s[i:i + len(hit)] += hit
        return s
    if name == "whoosh":
        s = _noise(0.5); s = _lp(s, 18) * np.sin(np.pi * np.linspace(0, 1, len(s))) ** 2 * 3
        return s
    if name == "sparkle": return _seq([84, 88, 91, 96, 100], 0.07, 0.9, 6.0, 0.1)
    if name == "sting":
        d = 1.2; x = _tt(d); s = np.zeros(len(x))
        for m in (43, 46, 50):
            ph = np.cumsum(_hz(m) * np.linspace(1.0, 0.88, len(x))) / SR; s += 2 * (ph % 1.0) - 1
        s = _lp(s, 9) * _env(d, 0.004, 2.6); hit = _lp(_noise(0.25), 6) * _env(0.25, 0.001, 20)
        s[: len(hit)] += hit * 1.5
        return s
    if name == "level": return _seq([72, 76, 79], 0.08, 0.6, 7.0, 0.2)
    raise KeyError(name)


def build_audio(dur, sfx, mute, path, key=0, bpm=96, bgm_gain=1.0):
    n = int(SR * dur); L = np.zeros(n); R = np.zeros(n)
    bl = np.zeros(n); br = np.zeros(n)

    def put(bufL, bufR, sig, t0, g, pan):
        i = int(t0 * SR)
        if i >= n: return
        sig = sig[: n - i] * g
        bufL[i:i + len(sig)] += sig * (1 - max(0, pan)); bufR[i:i + len(sig)] += sig * (1 + min(0, pan))

    beat = 60 / bpm; bar = beat * 4
    chords = [(60, [60, 64, 67, 72]), (57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (55, [55, 59, 62, 67])]
    arp = [0, 1, 2, 3, 2, 1, 2, 3]
    t0, k = 0.0, 0
    while t0 < dur:
        root, notes = chords[k % 4]
        for j in range(8):
            put(bl, br, _pluck(notes[arp[j]] + 12 + key, 0.8, 5.5), t0 + j * beat / 2, 0.15 * bgm_gain,
                -0.25 if j % 2 else 0.25)
        put(bl, br, _bass(root - 12 + key, beat * 1.6), t0, 0.3 * bgm_gain, 0)
        put(bl, br, _bass(root - 12 + key, beat * 1.6), t0 + beat * 2, 0.22 * bgm_gain, 0)
        for j in range(4):
            put(bl, br, _lp(_noise(0.07), 3) * _env(0.07, 0.002, 60), t0 + j * beat + beat / 2, 0.05 * bgm_gain, 0.4)
        t0 += bar; k += 1
    g = np.ones(n); ramp = int(0.35 * SR)
    for a, b in mute:
        ia, ib = int(a * SR), int(b * SR)
        g[ia:ib] = 0; g[ib:ib + ramp] = np.minimum(g[ib:ib + ramp], np.linspace(0, 1, len(g[ib:ib + ramp])))
    fo = int(0.8 * SR); g[-fo:] *= np.linspace(1, 0, fo)
    L += bl * g; R += br * g
    for t, name, gain, pan in sfx:
        put(L, R, _sfx(name), t, gain, pan)
    mix = np.tanh(np.stack([L, R], 1) * 1.1)
    mix = mix / np.max(np.abs(mix)) * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
