"""Render one month of Jacob content from content.py.

usage:
  python3 month_gen.py preview            # contact sheets for every item
  python3 month_gen.py reel <date>        # export one reel mp4
  python3 month_gen.py stills             # carousels + stories (jpg)
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter
from reel_kit import (Reel, jacob, show, shake, flash, qmarks, choice, countdown, badge, mark_x, mark_o, pop_in,
                      RED, POSE)
from reel_lib import (W, H, INK, NAVY, ORANGE, MUTED, WHITE, PAPER, DOT, ZEN_B, ZEN, KLEE, NUN, text_img, card,
                      place, prog, sticker)
import content

OUT = "/home/claude/reel/month/"
os.makedirs(OUT + "reels", exist_ok=True)
os.makedirs(OUT + "carousels", exist_ok=True)
os.makedirs(OUT + "stories", exist_ok=True)
CREAM = (253, 233, 212)
SKY = (231, 242, 249)


# ---------- text helpers ----------
def fit(text, font_fn, color, max_w, size, min_size=30, spacing=12):
    while True:
        im = text_img(text, font_fn(size), color, spacing=spacing)
        if im.width <= max_w or size <= min_size:
            return im
        size -= 4


def en_font(t):
    return NUN


def phrase(en, ja, en_size=84, ja_size=50, width=860):
    e = fit(en, NUN, NAVY, width - 70, en_size, spacing=8)
    j = fit(ja, ZEN, INK, width - 70, ja_size)
    return card([e, j], width=width)


def title(text, size=84, color=INK, max_w=940):
    return fit(text, ZEN_B, color, max_w, size, spacing=18)


def note_card(text, size=52):
    return card([fit(text, ZEN_B, INK, 790, size, spacing=14)], width=860, pad_y=34)


def by_label(text, color=ORANGE):
    return badge(text, color, size=40) if text.isascii() else _jbadge(text, color)


def _jbadge(text, color):
    t = text_img(text, ZEN_B(40), WHITE)
    im = Image.new("RGBA", (t.width + 56, t.height + 26), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=color)
    im.alpha_composite(t, (28, 13))
    return im


def hook_scene(r, hook, pose):
    r.add(0, 2.6, show(title(hook, 88), W / 2, 520, fade_out=0.2))
    r.add(0.15, 2.6, show(jacob(pose), W / 2, 1230, start_scale=0.9, fade_out=0.2, bob=6))
    r.add(0.5, 2.6, qmarks)
    r.sound(0.12, "pop"); r.sound(0.4, "pop"); r.sound(0.6, "boing", 0.3)


def end_scene(r, s, e, text):
    r.add(s, e, show(jacob('peace2'), W / 2, 900, pop=0.45, bob=6))
    r.add(s + 0.4, e, show(fit(text, KLEE, INK, 900, 60, spacing=16), W / 2, 1480, angle=-1))
    r.sound(s, "sparkle", 0.35)


# ---------- reel templates ----------
def reel_mistake(d):
    r = Reel(24.0)
    hook_scene(r, d["hook"], "thinking")
    r.add(2.6, 6.0, show(title(d["setup"], 64), W / 2, 440))
    r.add(2.6, 6.0, show(jacob('fight'), W / 2, 1000, bob=10))
    r.add(3.0, 6.0, show(card([fit(d["wrong"], NUN, NAVY, 780, 110), text_img("（つい言っちゃう）", ZEN(44), MUTED)]),
                         W / 2, 1500, angle=-2))
    r.sound(2.6, "whoosh", 0.35); r.sound(3.0, "pop", 0.5)
    r.add(6.0, 9.5, show(jacob('surprised', 640), W / 2, 1030, pop=0.25))
    r.add(6.0, 9.5, shake(mark_x(380), W / 2, 520, amp=16))
    r.add(6.35, 9.5, show(note_card(d["wrong_note"]), W / 2, 1590))
    r.add(6.0, 6.3, flash)
    r.sound(6.0, "buzzer", 0.4); r.sound(6.35, "pop", 0.4); r.mute.append((6.0, 7.2))
    r.add(9.5, 15.5, show(title("こう言えばOK！", 80), W / 2, 430))
    r.add(9.5, 15.5, show(jacob('cheer', 700), W / 2, 980, bob=8))
    r.add(9.8, 15.5, show(phrase(d["right"], d["right_ja"], en_size=96), W / 2, 1460, angle=-1.5))
    r.sound(9.5, "correct", 0.45); r.sound(9.8, "pop", 0.5)
    r.add(15.5, 20.5, show(title("あわせて覚えよう", 72), W / 2 - 150, 430))
    r.add(15.5, 20.5, show(jacob('peace1', 340), 900, 600, bob=6))
    (e1, j1), (e2, j2) = d["extras"]
    r.add(15.8, 20.5, show(phrase(e1, j1, en_size=80, ja_size=44), W / 2, 1000, angle=-1.5))
    r.add(16.9, 20.5, show(phrase(e2, j2, en_size=80, ja_size=44), W / 2, 1340, angle=1.2))
    r.sound(15.8, "pop", 0.5); r.sound(16.9, "pop", 0.5)
    end_scene(r, 20.5, 24.0, d["end"])
    return r


def reel_quiz(d):
    r = Reel(23.0)
    hook_scene(r, d["hook"], "thinking")
    letters = "ABC"
    ys = [560, 720, 880]
    r.add(2.6, 9.6, show(title("いちばん自然なのは？", 70), W / 2, 400))
    for k, (t, y) in enumerate(zip(d["options"], ys)):
        r.add(2.8 + 0.2 * k, 9.6, show(choice(letters[k], t), W / 2, y))
        r.sound(2.8 + 0.2 * k, "pop2", 0.35)

    def timer(fr, lt, span):
        place(fr, countdown(280, 1 - (lt % 1.0), max(1, 5 - int(lt))), 720, 1230)
    r.add(3.6, 8.6, timer)
    r.add(3.4, 9.6, show(jacob('thinking', 470), 330, 1260, bob=6))
    for k in range(5):
        r.sound(3.6 + k, "tick", 0.5)
    r.sound(8.6, "drum", 0.35)
    ans = d["answer"]

    def answer(fr, lt, span):
        for k, (t, y) in enumerate(zip(d["options"], ys)):
            if k == ans:
                place(fr, choice(letters[k], t, highlight=(220, 238, 214)), W / 2, y,
                      scale=1 + 0.04 * math.sin(min(lt, 0.5) * math.pi * 2))
            else:
                place(fr, choice(letters[k], t), W / 2, y, alpha=0.35)
        place(fr, mark_o(170, RED), 880, ys[ans], scale=pop_in(prog(lt, 0, 0.3)))
    r.add(9.6, 13.5, answer)
    r.add(9.6, 13.5, show(title(f"正解は {letters[ans]}！", 96, NAVY), W / 2, 1110))
    r.add(9.8, 13.5, show(jacob('cheer', 470), W / 2, 1450, bob=8))
    r.sound(9.6, "correct", 0.5)
    r.add(13.5, 19.5, show(note_card(d["note"], 50), W / 2, 540))
    (e1, j1), (e2, j2) = d["extras"]
    r.add(14.6, 19.5, show(phrase(e1, j1, en_size=84, ja_size=46), W / 2, 960, angle=-1.5))
    r.add(15.8, 19.5, show(phrase(e2, j2, en_size=72, ja_size=42), W / 2, 1300, angle=1.2))
    r.sound(13.5, "pop", 0.45); r.sound(14.6, "pop", 0.5); r.sound(15.8, "pop", 0.5)
    end_scene(r, 19.5, 23.0, "A・B・C、どれだと思った？\nコメントで教えてね")
    return r


def reel_ranking(d):
    r = Reel(26.0)
    hook_scene(r, d["hook"], "surprised")
    r.add(2.6, 5.2, show(title(d["title"], 100), W / 2, 540, pop=0.4))
    r.add(2.8, 5.2, show(jacob('happy', 640), W / 2, 1240, bob=6))
    r.sound(2.6, "level", 0.45)
    cols = [ORANGE, (160, 112, 63), NAVY]
    poses = ['peace1', 'happy', 'cheer']
    spans = [(5.2, 10.2), (10.2, 15.2), (15.2, 21.0)]
    for i, ((en, ja, hint), (s, e)) in enumerate(zip(d["ranks"], spans)):
        b = f"No.{3 - i}"
        delay = 1.0 if i == 2 else 0.0
        if delay:
            r.add(s, s + delay, show(title("第1位は…", 90), W / 2, 760)); r.sound(s, "drum", 0.4)
        r.add(s + delay, e, show(badge(b, cols[i], size=64), W / 2, 420, angle=-3))
        r.add(s + delay, e, show(jacob(poses[i], 560), W / 2, 820, bob=6))
        r.add(s + delay + 0.25, e, show(phrase(en, ja, en_size=88), W / 2, 1300, angle=-1.2))
        r.add(s + delay + 1.2, e, show(fit(hint, KLEE, MUTED, 900, 48), W / 2, 1530))
        r.sound(s + delay, "correct" if i == 2 else "level", 0.45)
        r.sound(s + delay + 0.25, "pop", 0.5); r.sound(s + delay + 1.2, "pop2", 0.25)

    def recap(fr, lt, span):
        place(fr, title("まとめ", 76), W / 2, 400, scale=pop_in(prog(lt, 0, 0.3)))
        for k, (en, ja, hint) in enumerate(reversed(d["ranks"])):
            a = prog(lt, 0.2 + 0.2 * k, 0.3)
            y = 560 + 170 * k
            place(fr, badge(f"No.{k + 1}", list(reversed(cols))[k], size=40), 170, y, scale=pop_in(a), alpha=min(1, a * 3))
            place(fr, fit(en, NUN, NAVY, 700, 58), 620, y - 22, scale=pop_in(a), alpha=min(1, a * 3))
            place(fr, fit(ja, ZEN, INK, 700, 42), 620, y + 42, alpha=min(1, a * 3))
        place(fr, fit(d["end"].replace("\n", ""), KLEE, INK, 900, 56), W / 2, 1110, alpha=prog(lt, 1.0, 0.4), angle=-1)
    r.add(21.0, 26.0, recap)
    r.add(21.4, 26.0, show(jacob('peace2', 440), W / 2, 1400, bob=6))
    r.sound(21.0, "pop", 0.45); r.sound(22.0, "sparkle", 0.35)
    return r


def reel_skit(d):
    r = Reel(24.0)
    hook_scene(r, d["hook"], "thinking")
    line_by = d.get("line_by", "ジェイコブ")
    reply_by = d.get("reply_by", "相手")
    # scene + line
    r.add(2.6, 9.0, show(_jbadge(d["scene"], MUTED), W / 2, 420))
    r.add(2.6, 9.0, show(jacob(d.get("line_pose", "happy"), 620), W / 2, 880, bob=8))
    r.add(3.0, 9.0, show(_jbadge(line_by, ORANGE), 250, 1250))
    r.add(3.1, 9.0, show(phrase(*d["line"], en_size=84), W / 2, 1450, angle=-1.5))
    r.sound(2.6, "whoosh", 0.35); r.sound(3.1, "pop", 0.5)
    # reply
    r.add(9.0, 14.5, show(_jbadge(reply_by, NAVY), 250, 560))
    r.add(9.0, 14.5, show(phrase(*d["reply"], en_size=84), W / 2, 760, angle=1.2))
    r.add(9.2, 14.5, show(jacob('cheer', 520), W / 2, 1300, bob=8))
    r.sound(9.0, "pop", 0.5)
    # answer / follow-up
    r.add(14.5, 20.5, show(title("こう返せばOK！", 76), W / 2, 430))
    r.add(14.6, 20.5, show(phrase(*d["answer"], en_size=84), W / 2, 760, angle=-1.2))
    r.add(15.6, 20.5, show(note_card(d["note"], 50), W / 2, 1150))
    r.add(15.0, 20.5, show(jacob('peace1', 360), 830, 1550, bob=6))
    r.sound(14.5, "correct", 0.45); r.sound(14.6, "pop", 0.5); r.sound(15.6, "pop2", 0.3)
    end_scene(r, 20.5, 24.0, d["end"])
    return r


REEL_FN = {"mistake": reel_mistake, "quiz": reel_quiz, "ranking": reel_ranking, "skit": reel_skit}
AUDIO = {"mistake": dict(key=0, bpm=100), "quiz": dict(key=2, bpm=104), "ranking": dict(key=-2, bpm=92),
         "skit": dict(key=5, bpm=96)}
PREV_T = {"mistake": (1.2, 4.5, 7.5, 12.5, 18.5, 22.5), "quiz": (1.2, 6.0, 11.0, 17.5, 21.5),
          "ranking": (1.2, 4.0, 8.0, 13.0, 18.0, 24.0), "skit": (1.2, 6.0, 12.0, 18.0, 22.5)}


# ---------- stills: carousel + story ----------
def paper(w, h):
    im = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(im)
    for y in range(17, h, 34):
        for x in range(17, w, 34):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=DOT)
    return im.convert("RGBA")


def put(fr, im, cx, cy, angle=0.0):
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    fr.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def panel(w, h, fill=WHITE, radius=40, border=None):
    im = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((20, 32, 20 + w, 32 + h), radius, fill=50)
    sh = Image.new("RGBA", im.size, INK + (255,)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + w, 20 + h), radius, fill=fill, outline=border,
                                         width=5 if border else 0)
    return im


def header(fr, n, total, w=1080):
    lab = text_img("Talk with Jacob!", NUN(40), WHITE)
    pill = Image.new("RGBA", (lab.width + 56, lab.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), pill.height // 2, fill=NAVY)
    pill.alpha_composite(lab, (28, 12))
    put(fr, pill, 80 + pill.width / 2, 100, angle=2)
    if n:
        pg = text_img(f"{n} / {total}", NUN(34), MUTED)
        put(fr, pg, w - 80 - pg.width / 2, 100)


def stacked(lines, width=900, fill=WHITE):
    """lines: list of rendered images, centered on a panel."""
    h = sum(l.height for l in lines) + 30 * (len(lines) - 1) + 120
    p = panel(width, h, fill=fill)
    y = 20 + 60
    for l in lines:
        p.alpha_composite(l, (20 + (width - l.width) // 2, y)); y += l.height + 30
    return p


SJ = {}


def J(pose, h):
    k = (pose, h)
    if k not in SJ:
        SJ[k] = sticker(POSE[pose], h)
    return SJ[k]


def carousel(d, idx):
    out = OUT + f"carousels/{d['date']}/"
    os.makedirs(out, exist_ok=True)
    T = 6
    files = []

    def save(fr, n):
        p = out + f"slide_{n}.jpg"; fr.convert("RGB").save(p, quality=92); files.append(p)

    # 1 cover
    fr = paper(1080, 1350); header(fr, 1, T)
    put(fr, title(d["hook"], 96), 540, 380)
    put(fr, J("thinking", 580), 500, 950)
    put(fr, text_img("めくってね →", KLEE(46), INK), 860, 1270, angle=-3)
    save(fr, 1)
    # 2 scene
    fr = paper(1080, 1350); header(fr, 2, T)
    put(fr, title("こんなとき、なんて言う？", 64), 540, 250)
    put(fr, stacked([fit(d["scene"], ZEN_B, INK, 780, 64, spacing=16)], fill=CREAM), 540, 560, angle=-1)
    put(fr, J("worried", 520), 540, 1040)
    save(fr, 2)
    # 3 main answer
    fr = paper(1080, 1350); header(fr, 3, T)
    put(fr, title("こう言えばOK！", 72, ORANGE), 540, 250)
    en, ja = d["main"]
    put(fr, stacked([fit(en, NUN, NAVY, 800, 104, spacing=8), fit(ja, ZEN_B, INK, 800, 56)]), 540, 540, angle=-1.5)
    put(fr, J("cheer", 560), 540, 1050)
    save(fr, 3)
    # 4 uses
    fr = paper(1080, 1350); header(fr, 4, T)
    put(fr, title("場面で使い分けよう", 70), 540, 250)
    y = 470
    for k, (e, who) in enumerate(d["uses"]):
        col = [CREAM, SKY, (241, 230, 217)][k]
        p = stacked([fit(e, NUN, NAVY, 780, 70, spacing=6), fit(who, ZEN_B, INK, 780, 42)], fill=col)
        put(fr, p, 540, y, angle=[-1, 1, -0.6][k])
        y += p.height + 10
    save(fr, 4)
    # 5 caution / reply
    fr = paper(1080, 1350); header(fr, 5, T)
    a, b, c = d["caution"]
    put(fr, title("ワンポイント", 80), 540, 250)
    put(fr, stacked([fit(a, ZEN_B, INK, 800, 54), fit(b, ZEN_B, ORANGE, 800, 60, spacing=12)]), 540, 520)
    cfont = NUN if c.isascii() else ZEN_B
    put(fr, stacked([fit(c, cfont, NAVY, 800, 70 if c.isascii() else 52, spacing=10)], fill=SKY), 540, 860, angle=-1)
    put(fr, J("thinking", 360), 880, 1160)
    save(fr, 5)
    # 6 CTA
    fr = paper(1080, 1350); header(fr, 6, T)
    put(fr, title("今日のひとこと", 72), 540, 240)
    put(fr, stacked([fit(en, NUN, NAVY, 800, 84, spacing=8), fit(ja, ZEN, INK, 800, 46)]), 540, 470, angle=-1)
    put(fr, J("peace2jump", 520), 540, 930)
    put(fr, fit(d["cta"], KLEE, INK, 900, 56, spacing=12), 540, 1255, angle=-1)
    save(fr, 6)
    return files


STORY_POSES = ["thinking", "worried", "surprised", "yawn", "happy", "peace1"]


def story(r, i=0):
    fr = paper(1080, 1920)
    header(fr, None, None)
    put(fr, _jbadge("今日のクイズ", ORANGE), 540, 360)
    put(fr, stacked([fit(r["story"], ZEN_B, INK, 820, 92, spacing=20)]), 540, 660, angle=-1.5)
    put(fr, J(STORY_POSES[i % len(STORY_POSES)], 820), 540, 1290)
    put(fr, fit("答えは今夜8時のリールで", KLEE, INK, 900, 60), 540, 1760, angle=-1)
    p = OUT + f"stories/{r['date']}.jpg"
    fr.convert("RGB").save(p, quality=92)
    return p


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "reel":
        d = next(x for x in content.REELS if x["date"] == sys.argv[2])
        rr = REEL_FN[d["kind"]](d)
        rr.export(OUT + f"reels/{d['date']}.mp4", AUDIO[d["kind"]])
        print("done", d["date"])
    elif cmd == "preview":
        for d in content.REELS:
            if d["kind"] == "existing":
                continue
            rr = REEL_FN[d["kind"]](d)
            rr.stills(PREV_T[d["kind"]], OUT + f"prev_reel_{d['date']}.png")
        print("previews done")
    elif cmd == "stills":
        for i, d in enumerate(content.CAROUSELS):
            carousel(d, i)
        for i, r in enumerate(content.REELS):
            story(r, i)
        print("stills done")
