"""Jacob reels v2: hook visible from frame 0, native English voice, shorter, UI-safe layout, custom covers.

usage:
  python3 reel_v2.py voices                 # synthesize + check every voiced line
  python3 reel_v2.py reel <date> [...]      # export reels (mp4) for dates
  python3 reel_v2.py all                    # every reel from 10/25
  python3 reel_v2.py covers                 # cover jpgs (also 10/23, 10/24)
  python3 reel_v2.py sheet <date>           # contact sheet of key frames
"""
import math, os, re, sys, wave, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reel")
import month_gen as mg
from month_gen import title, fit, phrase, note_card, _jbadge, badge
from reel_kit import (Reel, jacob, show, shake, flash, qmarks, choice, countdown, mark_x, mark_o, pop_in, RED,
                      build_audio, _sfx, SR, BG, LABEL)
from reel_lib import (W, H, FPS, INK, NAVY, ORANGE, MUTED, WHITE, ZEN_B, ZEN, KLEE, NUN, text_img, place, prog,
                      ease_out, clock, speed_lines)
import content

OUT = "/home/claude/reel/v2/out/"
for sub in ("reels", "covers", "sheets", "voice"):
    os.makedirs(OUT + sub, exist_ok=True)
TTS_DIR = "/tmp/claude-0/-home-claude/e1262836-2dc0-5244-b0d8-111f74c7d55a/scratchpad/tts/"
JACOB_VOICE, MODEL_VOICE = "am_fenrir", "af_heart"

# ---------------------------------------------------------------- voice
_kokoro = None


def clean(t):
    t = t.replace("\n", " ").replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    return re.sub(r"\s+", " ", t.replace("…", "...")).strip()


def tts(text, who=MODEL_VOICE, speed=0.92):
    """Return float32 mono at SR (44.1k), peak-normalised, cached on disk."""
    global _kokoro
    t = clean(text)
    key = re.sub(r"[^a-z0-9]+", "_", f"{who}_{speed}_{t}".lower())[:120]
    path = OUT + f"voice/{key}.npy"
    if os.path.exists(path):
        return np.load(path)
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(TTS_DIR + "kokoro-v1.0.onnx", TTS_DIR + "voices.bin")
    from scipy.signal import resample_poly
    s, sr = _kokoro.create(t, voice=who, speed=speed, lang="en-us")
    s = resample_poly(s.astype(np.float64), 147, 80)  # 24k -> 44.1k
    # trim leading/trailing near-silence, keep 40 ms
    idx = np.where(np.abs(s) > 0.01)[0]
    if len(idx):
        s = s[max(0, idx[0] - int(0.04 * SR)): idx[-1] + int(0.06 * SR)]
    s = (s / (np.max(np.abs(s)) + 1e-9) * 0.9).astype(np.float32)
    np.save(path, s)
    return s


def vdur(text, who=MODEL_VOICE, speed=0.92):
    return len(tts(text, who, speed)) / SR


class Reel2(Reel):
    def __init__(self, dur=60.0):
        super().__init__(dur)
        self.voices = []  # (t, text, who, speed)

    def say(self, t, text, who=MODEL_VOICE, speed=0.92):
        self.voices.append((t, text, who, speed))
        return t + vdur(text, who, speed)

    def export(self, out, audio_kwargs=None):
        wav = out.replace(".mp4", ".wav")
        build_audio2(self, wav, **(audio_kwargs or {}))
        import subprocess
        n = int(round(self.dur * FPS))
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(FPS), "-i", "-", "-i", wav, "-shortest", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out,
        ], stdin=subprocess.PIPE)
        for i in range(n):
            ff.stdin.write(self.frame(i / FPS).tobytes())
        ff.stdin.close()
        ff.wait()
        os.remove(wav)


def build_audio2(r, path, key=0, bpm=96):
    """BGM (ducked under voice) + SFX + voice."""
    n = int(SR * r.dur)
    tmp = path + ".bgm.wav"
    build_audio(r.dur, [], r.mute, tmp, key=key, bpm=bpm, bgm_gain=0.62)
    with wave.open(tmp) as w:
        bgm = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32767
    os.remove(tmp)
    bgm = bgm[:n]
    duck = np.ones(n)
    ramp = int(0.08 * SR)
    for t, text, who, speed in r.voices:
        a = int(t * SR) - ramp
        b = int((t + vdur(text, who, speed)) * SR) + ramp
        duck[max(0, a):min(n, b)] = 0.25
    duck = np.convolve(duck, np.ones(ramp) / ramp, mode="same")
    mix = bgm * duck[:, None] * 0.30
    L, R = mix[:, 0].copy(), mix[:, 1].copy()

    def put(sig, t0, g, pan=0.0):
        i = int(t0 * SR)
        if i >= n:
            return
        sig = sig[: n - i] * g
        L[i:i + len(sig)] += sig * (1 - max(0, pan))
        R[i:i + len(sig)] += sig * (1 + min(0, pan))

    for t, name, gain, pan in r.sfx:
        put(_sfx(name), t, gain * 0.8, pan)
    for t, text, who, speed in r.voices:
        put(tts(text, who, speed).astype(np.float64), t, 0.95)
    out = np.tanh(np.stack([L, R], 1) * 1.05)
    out = out / np.max(np.abs(out)) * 0.9
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- visuals
def hook_lines(text):
    """Split a hook into lines of (segment, highlighted); a quote may continue onto the next line."""
    out, inq = [], False
    for line in text.split("\n"):
        segs, cur, cur_hi = [], "", inq
        for ch in line:
            if ch in "「“" and not inq:
                if cur:
                    segs.append((cur, cur_hi))
                cur, inq, cur_hi = ch, True, True
            elif ch in "」”" and inq:
                segs.append((cur + ch, True))
                cur, inq, cur_hi = "", False, False
            else:
                cur += ch
        if cur:
            segs.append((cur, cur_hi))
        out.append(segs)
    return out


def two_tone_line(segs, size, base=INK, hi=ORANGE):
    f = ZEN_B(size)
    total = sum(f.getlength(s) for s, _ in segs)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(total) + 24, asc + desc + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 12
    for s, h in segs:
        d.text((x, 12), s, font=f, fill=hi if h else base)
        x += f.getlength(s)
    return im.crop(im.getbbox())


def hook_title(text, size=108, max_w=900, min_size=60):
    while True:
        lines = [two_tone_line(segs, size) for segs in hook_lines(text)]
        if max(l.width for l in lines) <= max_w or size <= min_size:
            break
        size -= 4
    gap = int(size * 0.30)
    lh = int(size * 1.02)
    h = lh * len(lines) + gap * (len(lines) - 1)
    im = Image.new("RGBA", (max(l.width for l in lines) + 8, h + 8), (0, 0, 0, 0))
    y = 4
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y + (lh - l.height) // 2))
        y += lh + gap
    return im


def show_now(im, x, y, angle=0.0, punch=0.07, bob=0.0, fade_out=0.0):
    """Fully visible from the first frame; a small scale punch instead of a pop-in."""
    def fn(fr, lt, span):
        sc = 1 + punch * (1 - ease_out(prog(lt, 0, 0.3)))
        out = 1 - prog(lt, span - fade_out, fade_out) if fade_out else 1
        place(fr, im, x, y + bob * math.sin(lt * 3), scale=sc, angle=angle, alpha=out)
    return fn


def pop(im, x, y, angle=0.0, bob=0.0):
    return show(im, x, y, angle=angle, pop=0.25, bob=bob)


def speaker_pill(text, color):
    return _jbadge(text, color)


def sound_badge():
    t = text_img("音声つき", ZEN_B(34), WHITE)
    im = Image.new("RGBA", (t.width + 92, t.height + 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=NAVY)
    cx, cy = 36, im.height // 2  # tiny speaker icon
    d.polygon([(cx - 14, cy - 7), (cx - 6, cy - 7), (cx + 4, cy - 15), (cx + 4, cy + 15), (cx - 6, cy + 7),
               (cx - 14, cy + 7)], fill=WHITE)
    d.arc((cx - 2, cy - 12, cx + 16, cy + 12), -50, 50, fill=WHITE, width=4)
    im.alpha_composite(t, (60, 13))
    return im


SERIES = {"mistake": ("それ、ちがうかも？", RED), "quiz": ("3択クイズ", NAVY), "ranking": ("言い方3選", ORANGE),
          "skit": ("この場面どう言う？", (60, 140, 96)), "story": ("ジェイコブの朝", (160, 112, 63)),
          "existing_fight": ("それ、ちがうかも？", RED), "existing_quiz": ("3択クイズ", NAVY)}
HOOK_POSE = {"mistake": "thinking", "quiz": "thinking", "ranking": "surprised", "skit": "thinking", "story": "thinking"}
POSE_CYCLE = {"mistake": ["thinking", "worried", "surprised"], "quiz": ["thinking", "worried"],
              "ranking": ["surprised", "happy"], "story": ["thinking"]}


def hook_pose(d, kind=None):
    """Vary the opening pose so the profile grid doesn't repeat the same Jacob."""
    kind = kind or d["kind"]
    if kind == "skit":
        return d.get("line_pose", "thinking")
    cyc = POSE_CYCLE.get(kind, [HOOK_POSE.get(kind, "thinking")])
    same = sorted(x["date"] for x in content.REELS if x["kind"] == kind)
    i = same.index(d["date"]) if d.get("date") in same else 0
    return cyc[i % len(cyc)]


def hook_scene(r, d, kind, end=1.5):
    ht = hook_title(d["hook"])
    hy = 330 + ht.height // 2
    r.add(0, end, show_now(ht, W / 2, hy))
    r.add(0, end, show_now(jacob(hook_pose(d, kind), 640), W / 2, 1200, punch=0.0, bob=6))
    r.add(0.12, end, qmarks)
    r.sound(0.0, "pop", 0.5); r.sound(0.18, "boing", 0.28)


def end_scene(r, s, text, dur=2.6):
    r.add(s, s + dur, pop(jacob('peace2', 640), W / 2, 820, bob=6))
    r.add(s + 0.3, s + dur, pop(fit(text, KLEE, INK, 900, 62, spacing=16), W / 2, 1300, angle=-1))
    r.sound(s, "sparkle", 0.35)
    return s + dur


# ---------------------------------------------------------------- templates
def reel_mistake(d):
    r = Reel2()
    hook_scene(r, d, "mistake")
    s = 1.5
    r.add(s, s + 2.8, pop(title(d["setup"], 64), W / 2, 400))
    r.add(s, s + 2.8, pop(jacob('fight', 560), W / 2, 820, bob=8))
    r.add(s + 0.3, s + 2.8, pop(card_wrong(d["wrong"]), W / 2, 1300, angle=-2))
    r.sound(s, "whoosh", 0.3); r.sound(s + 0.3, "pop", 0.5)
    s += 2.8
    r.add(s, s + 2.6, pop(jacob('surprised', 560), W / 2, 860))
    r.add(s, s + 2.6, shake(mark_x(340), W / 2, 420, amp=16))
    r.add(s + 0.3, s + 2.6, pop(note_card(d["wrong_note"]), W / 2, 1300))
    r.add(s, s + 0.3, flash)
    r.sound(s, "buzzer", 0.4); r.sound(s + 0.3, "pop", 0.4); r.mute.append((s, s + 1.2))
    s += 2.6
    # right answer, heard twice
    v1 = s + 0.5
    e1 = r.say(v1, d["right"])
    e2 = r.say(e1 + 0.6, d["right"])
    end = e2 + 0.7
    r.add(s, end, pop(title("こう言えばOK！", 80, ORANGE), W / 2, 400))
    r.add(s, end, pop(jacob('cheer', 520), W / 2, 790, bob=8))
    r.add(s + 0.2, end, pop(phrase(d["right"], d["right_ja"], en_size=96), W / 2, 1270, angle=-1.5))
    r.sound(s, "correct", 0.4); r.sound(s + 0.2, "pop", 0.45)
    s = end
    # extras, each voiced
    (x1, j1), (x2, j2) = d["extras"]
    a = r.say(s + 0.45, x1)
    b0 = a + 0.45
    b = r.say(b0 + 0.25, x2)
    end = b + 0.9
    r.add(s, end, pop(title("あわせて覚えよう", 70), W / 2 - 140, 400))
    r.add(s, end, pop(jacob('peace1', 300), 900, 560, bob=6))
    r.add(s + 0.2, end, pop(phrase(x1, j1, en_size=78, ja_size=44), W / 2, 830, angle=-1.5))
    r.add(b0, end, pop(phrase(x2, j2, en_size=78, ja_size=44), W / 2, 1200, angle=1.2))
    r.sound(s + 0.2, "pop", 0.45); r.sound(b0, "pop", 0.45)
    r.dur = end_scene(r, end, d["end"])
    return r


def card_wrong(en):
    from reel_lib import card
    return card([fit(en, NUN, NAVY, 760, 104), text_img("（つい言っちゃう）", ZEN(44), MUTED)], width=820)


def reel_quiz(d):
    r = Reel2()
    hook_scene(r, d, "quiz")
    letters, ys = "ABC", [560, 720, 880]
    s = 1.5
    q_end = s + 4.1
    r.add(s, q_end, pop(title("いちばん自然なのは？", 70), W / 2, 400))
    for k, (t, y) in enumerate(zip(d["options"], ys)):
        r.add(s + 0.15 * k, q_end, pop(choice(letters[k], t), W / 2, y))
        r.sound(s + 0.15 * k, "pop2", 0.35)
    c0 = s + 0.8

    def timer(fr, lt, span):
        place(fr, countdown(250, 1 - (lt % 1.0), max(1, 3 - int(lt))), 730, 1180)
    r.add(c0, c0 + 3.0, timer)
    r.add(s + 0.4, q_end, pop(jacob('thinking', 420), 330, 1200, bob=6))
    for k in range(3):
        r.sound(c0 + k, "tick", 0.5)
    r.sound(c0 + 3.0, "drum", 0.3)
    ans = d["answer"]
    s = q_end
    say_at = s + 0.45
    e = r.say(say_at, d["options"][ans])
    end = e + 1.0

    def answer(fr, lt, span):
        for k, (t, y) in enumerate(zip(d["options"], ys)):
            if k == ans:
                place(fr, choice(letters[k], t, highlight=(220, 238, 214)), W / 2, y,
                      scale=1 + 0.04 * math.sin(min(lt, 0.5) * math.pi * 2))
            else:
                place(fr, choice(letters[k], t), W / 2, y, alpha=0.35)
        place(fr, mark_o(170, RED), 880, ys[ans], scale=pop_in(prog(lt, 0, 0.3)))
    r.add(s, end, answer)
    r.add(s, end, pop(title(f"正解は {letters[ans]}！", 96, NAVY), W / 2, 400))
    r.add(s + 0.2, end, pop(jacob('cheer', 400), W / 2, 1200, bob=8))
    r.sound(s, "correct", 0.45)
    s = end
    (x1, j1), (x2, j2) = d["extras"]
    a = r.say(s + 0.9, x1)
    b0 = a + 0.4
    b = r.say(b0 + 0.25, x2)
    end = b + 0.9
    r.add(s, end, pop(note_card(d["note"], 48), W / 2, 470))
    r.add(s + 0.7, end, pop(phrase(x1, j1, en_size=80, ja_size=44), W / 2, 880, angle=-1.5))
    r.add(b0, end, pop(phrase(x2, j2, en_size=70, ja_size=40), W / 2, 1230, angle=1.2))
    r.sound(s, "pop", 0.4); r.sound(s + 0.7, "pop", 0.45); r.sound(b0, "pop", 0.45)
    r.dur = end_scene(r, end, "A・B・C、どれだと思った？\nコメントで教えてね")
    return r


def reel_ranking(d):
    r = Reel2()
    hook_scene(r, d, "ranking")
    s = 1.5
    r.add(s, s + 1.6, pop(title(d["title"], 100), W / 2, 520))
    r.add(s, s + 1.6, pop(jacob('happy', 560), W / 2, 1180, bob=6))
    r.sound(s, "level", 0.45)
    s += 1.6
    cols = [ORANGE, (160, 112, 63), NAVY]
    poses = ['peace1', 'happy', 'cheer']
    for i, (en, ja, hint) in enumerate(d["ranks"]):
        if i == 2:
            r.add(s, s + 0.8, pop(title("第1位は…", 90), W / 2, 700)); r.sound(s, "drum", 0.35)
            s += 0.8
        v = s + 0.35
        e = r.say(v, en)
        end = max(e + 1.5, s + 3.0)
        r.add(s, end, pop(badge(f"No.{3 - i}", cols[i], size=64), W / 2, 390, angle=-3))
        r.add(s, end, pop(jacob(poses[i], 480), W / 2, 740, bob=6))
        r.add(s + 0.15, end, pop(phrase(en, ja, en_size=88), W / 2, 1150, angle=-1.2))
        r.add(e + 0.1, end, pop(fit(hint, KLEE, MUTED, 900, 50), W / 2, 1400))
        r.sound(s, "correct" if i == 2 else "level", 0.4); r.sound(s + 0.15, "pop", 0.45)
        s = end

    def recap(fr, lt, span):
        place(fr, title("まとめ", 76), W / 2, 380, scale=pop_in(prog(lt, 0, 0.3)))
        for k, (en, ja, hint) in enumerate(reversed(d["ranks"])):
            a = prog(lt, 0.2 + 0.2 * k, 0.3)
            y = 540 + 170 * k
            place(fr, badge(f"No.{k + 1}", list(reversed(cols))[k], size=40), 170, y, scale=pop_in(a), alpha=min(1, a * 3))
            place(fr, fit(en, NUN, NAVY, 700, 58), 620, y - 22, scale=pop_in(a), alpha=min(1, a * 3))
            place(fr, fit(ja, ZEN, INK, 700, 42), 620, y + 42, alpha=min(1, a * 3))
        place(fr, fit(d["end"].replace("\n", ""), KLEE, INK, 900, 56), W / 2, 1080, alpha=prog(lt, 1.0, 0.4), angle=-1)
    r.add(s, s + 3.6, recap)
    r.add(s + 0.4, s + 3.6, pop(jacob('peace2', 360), W / 2, 1330, bob=6))
    r.sound(s, "pop", 0.45); r.sound(s + 1.0, "sparkle", 0.35)
    r.dur = s + 3.6
    return r


def who(label):
    return JACOB_VOICE if label == "ジェイコブ" else MODEL_VOICE


def reel_skit(d):
    r = Reel2()
    hook_scene(r, d, "skit")
    line_by = d.get("line_by", "ジェイコブ")
    reply_by = d.get("reply_by", "相手")
    s = 1.5
    e = r.say(s + 0.45, d["line"][0], who(line_by))
    end = e + 1.4
    r.add(s, end, pop(_jbadge(d["scene"], MUTED), W / 2, 390))
    r.add(s, end, pop(jacob(d.get("line_pose", "happy"), 520), W / 2, 780, bob=8))
    r.add(s + 0.15, end, pop(_jbadge(line_by, ORANGE), 250, 1080))
    r.add(s + 0.2, end, pop(phrase(*d["line"], en_size=80), W / 2, 1260, angle=-1.5))
    r.sound(s, "whoosh", 0.3); r.sound(s + 0.2, "pop", 0.45)
    s = end
    e = r.say(s + 0.35, d["reply"][0], who(reply_by))
    end = e + 1.3
    r.add(s, end, pop(_jbadge(reply_by, NAVY), 250, 420))
    r.add(s + 0.05, end, pop(phrase(*d["reply"], en_size=80), W / 2, 620, angle=1.2))
    r.add(s + 0.2, end, pop(jacob('cheer', 480), W / 2, 1140, bob=8))
    r.sound(s, "pop", 0.45)
    s = end
    e = r.say(s + 0.45, d["answer"][0], JACOB_VOICE)
    end = e + 1.9
    r.add(s, end, pop(title("こう返せばOK！", 76, ORANGE), W / 2, 390))
    r.add(s + 0.1, end, pop(phrase(*d["answer"], en_size=80), W / 2, 680, angle=-1.2))
    r.add(e + 0.1, end, pop(note_card(d["note"], 48), W / 2, 1050))
    r.add(s + 0.4, end, pop(jacob('peace1', 320), 820, 1360, bob=6))
    r.sound(s, "correct", 0.4); r.sound(s + 0.1, "pop", 0.45); r.sound(e + 0.1, "pop2", 0.3)
    r.dur = end_scene(r, end, d["end"])
    return r


STORY_1026 = {
    "date": "2026-10-26", "kind": "story",
    "hook": "「あと5分だけ…」って\n英語でなんて言うか\n知ってる？",
    "end": "朝が弱い友だちに\n送ってあげてね",
}


def reel_story_1026(d=STORY_1026):
    from reel_lib import card
    r = Reel2()
    hook_scene(r, d, "story")
    s = 1.5
    # 7:00 alarm
    r.add(s, s + 2.0, pop(title("朝7時。ジェイコブは…", 72), W / 2, 400))
    r.add(s, s + 2.0, pop(jacob('yawn', 560), W / 2, 820, bob=4))

    def ring(fr, lt, span):
        place(fr, clock(280, "7:00"), 300 + 6 * math.sin(lt * 60), 1180, angle=8 * math.sin(lt * 40))
        place(fr, text_img("ジリリリ…！", KLEE(52), ORANGE), 700, 1180, angle=-4)
    r.add(s + 0.1, s + 2.0, ring)
    for k in range(6):
        r.sound(s + 0.1 + k * 0.28, "tick", 0.55)
    s += 2.0
    # five more minutes (sleepy)
    v = s + 0.4
    e = r.say(v, "Five more minutes...", JACOB_VOICE, 0.82)
    end = e + 1.6
    sub = card([text_img("Five more minutes…", NUN(84), NAVY), text_img("あと5分だけ…", ZEN(54), INK)], width=860)
    r.add(s, end, pop(title("ねぼすけジェイコブ", 72), W / 2, 400))
    r.add(s, end, pop(jacob('yawn', 560), W / 2, 820, bob=3))
    r.add(s + 0.2, end, pop(sub, W / 2, 1260, angle=-1.2))
    r.sound(s + 0.2, "pop", 0.45)
    s = end
    # 8:30!?
    r.add(s, s + 1.9, shake(clock(300, "8:30"), W / 2, 470, amp=10))
    r.add(s, s + 1.9, pop(jacob('surprised', 560), W / 2, 930))
    r.add(s + 0.3, s + 1.9, pop(title("…え、もう8時半！？", 70), W / 2, 1330))
    r.add(s, s + 0.25, flash)
    r.sound(s, "sting", 0.35); r.sound(s + 0.3, "boing", 0.3)
    s += 1.9
    # I'm late!
    e = r.say(s + 0.35, "I'm late!", JACOB_VOICE, 1.0)
    end = e + 1.5
    late = card([text_img("I’m late!", NUN(100), NAVY), text_img("遅刻しちゃう！", ZEN(54), INK)], width=760)

    def run(fr, lt, span):
        speed_lines(fr, W / 2 + 40, 820, min(1, lt * 3))
    r.add(s, end, run)
    r.add(s, end, pop(jacob('peace2jump', 560), W / 2 + 40, 820, bob=10))
    r.add(s + 0.15, end, pop(late, W / 2, 1280, angle=-1.5))
    r.sound(s, "whoosh", 0.4); r.sound(s + 0.15, "pop", 0.45)
    s = end
    # sign-off
    e = r.say(s + 0.4, "See you tomorrow!", JACOB_VOICE, 0.95)
    end = e + 1.8
    bye = card([text_img("See you tomorrow!", NUN(84), NAVY), text_img("また明日ね！", ZEN(54), INK)], width=860)
    r.add(s, end, pop(jacob('peace2', 600), W / 2, 760, bob=6))
    r.add(s + 0.2, end, pop(bye, W / 2, 1200, angle=-1))
    r.add(e + 0.1, end, pop(fit(d["end"], KLEE, INK, 900, 56, spacing=14), W / 2, 1450, angle=-1))
    r.sound(s, "sparkle", 0.35)
    r.dur = end
    return r


TEMPLATE = {"mistake": reel_mistake, "quiz": reel_quiz, "ranking": reel_ranking, "skit": reel_skit}
AUDIO = mg.AUDIO


def spec(date):
    if date == "2026-10-26":
        return STORY_1026, reel_story_1026, dict(key=-2, bpm=92)
    d = next(x for x in content.REELS if x["date"] == date)
    return d, TEMPLATE[d["kind"]], AUDIO[d["kind"]]


# ---------------------------------------------------------------- covers
EXISTING = {
    "2026-10-23": {"hook": "「がんばれ！」を\n“Fight!” って\n言ってない？", "kind": "existing_fight", "pose": "fight"},
    "2026-10-24": {"hook": "「いただきます」\n英語で言える？", "kind": "existing_quiz", "pose": "thinking"},
}


def cover(date):
    if date in EXISTING:
        d = EXISTING[date]; kind = d["kind"]; pose = d["pose"]
    else:
        d, _, _ = spec(date); kind = d["kind"]; pose = hook_pose(d, kind)
    fr = BG.copy()
    tag, col = SERIES[kind]
    place(fr, _jbadge(tag, col), W / 2, 390, angle=-2)
    ht = hook_title(d["hook"], size=112)
    place(fr, ht, W / 2, 470 + ht.height // 2)
    place(fr, jacob(pose, 640), W / 2, 1230)
    place(fr, sound_badge(), W / 2 + 300, 1560, angle=-3) if date not in EXISTING else None
    p = OUT + f"covers/{date}.jpg"
    fr.convert("RGB").save(p, quality=92)
    return p


# ---------------------------------------------------------------- cli
def render(date):
    d, fn, au = spec(date)
    r = fn(d)
    r.export(OUT + f"reels/{date}.mp4", au)
    return r.dur


def sheet(date, times=None):
    d, fn, au = spec(date)
    r = fn(d)
    times = times or [0, 0.5, 1.6, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, r.dur - 0.5]
    times = [t for t in times if t < r.dur]
    cols = 5
    rows = math.ceil(len(times) / cols)
    sh = Image.new("RGB", (cols * 280, rows * 520), "black")
    for i, t in enumerate(times):
        im = r.frame(t).resize((270, 480))
        ImageDraw.Draw(im).text((8, 456), f"{t:.1f}s", fill=(255, 0, 0))
        sh.paste(im, ((i % cols) * 280, (i // cols) * 520))
    p = OUT + f"sheets/{date}.png"
    sh.save(p)
    return p, r.dur, [(round(t, 2), txt) for t, txt, w_, s_ in r.voices]


def voiced_lines():
    out = []
    for d in content.REELS:
        if d["date"] < "2026-10-25" or d["kind"] == "existing":
            continue
        k = d["kind"]
        if k == "mistake":
            out += [(d["right"], MODEL_VOICE, .92)] + [(e, MODEL_VOICE, .92) for e, _ in d["extras"]]
        elif k == "quiz":
            out += [(d["options"][d["answer"]], MODEL_VOICE, .92)] + [(e, MODEL_VOICE, .92) for e, _ in d["extras"]]
        elif k == "ranking":
            out += [(e, MODEL_VOICE, .92) for e, _, _ in d["ranks"]]
        elif k == "skit":
            out += [(d["line"][0], who(d.get("line_by", "ジェイコブ")), .92),
                    (d["reply"][0], who(d.get("reply_by", "相手")), .92), (d["answer"][0], JACOB_VOICE, .92)]
    out += [("Five more minutes...", JACOB_VOICE, .82), ("I'm late!", JACOB_VOICE, 1.0),
            ("See you tomorrow!", JACOB_VOICE, .95)]
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    dates = sorted({x["date"] for x in content.REELS if x["date"] >= "2026-10-25"})
    if cmd == "voices":
        lines = voiced_lines()
        for t, w_, sp in lines:
            tts(t, w_, sp)
        json.dump([[clean(t), w_, sp] for t, w_, sp in lines], open(OUT + "voiced_lines.json", "w"), ensure_ascii=False)
        print(len(lines), "lines ok")
    elif cmd == "reel":
        for dt in sys.argv[2:]:
            print(dt, round(render(dt), 2))
    elif cmd == "all":
        for dt in dates:
            print(dt, round(render(dt), 2), flush=True)
    elif cmd == "covers":
        for dt in ["2026-10-23", "2026-10-24"] + dates:
            cover(dt)
        print("covers ok")
    elif cmd == "sheet":
        for dt in sys.argv[2:]:
            print(sheet(dt))
