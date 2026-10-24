"""Jacob reel: 朝が弱いジェイコブ “Five more minutes…” (1080x1920, 15s, 30fps)."""
import glob, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 17.6
N = int(FPS * DUR)
F = "/home/claude/reel/fonts/"

PAPER = (246, 239, 227)
DOT = (230, 217, 198)
INK = (58, 45, 36)
NAVY = (44, 74, 140)
ORANGE = (217, 130, 43)
MUTED = (122, 102, 86)
WHITE = (255, 253, 248)


def font(name, size, var=None):
    f = ImageFont.truetype(F + name, size)
    if var:
        f.set_variation_by_name(var)
    return f


ZEN_B = lambda s: font("ZenMaruGothic-Black.ttf", s)
ZEN = lambda s: font("ZenMaruGothic-Bold.ttf", s)
KLEE = lambda s: font("KleeOne-SemiBold.ttf", s)
NUN = lambda s: font("Nunito[wght].ttf", s, b"Black")

# ---------- helpers ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_back(p, s=1.9):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def background():
    bg = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(bg)
    for y in range(17, H, 34):
        for x in range(17, W, 34):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=DOT)
    return bg.convert("RGBA")


def sticker(path, height, outline=12):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    w = round(im.width * height / im.height)
    im = im.resize((w, height), Image.LANCZOS)
    pad = outline * 3
    canvas = Image.new("RGBA", (w + pad * 2, height + pad * 2), (0, 0, 0, 0))
    a = Image.new("L", canvas.size, 0)
    a.paste(im.getchannel("A"), (pad, pad))
    ring = a.point(lambda v: 255 if v > 20 else 0).filter(ImageFilter.MaxFilter(outline * 2 + 1))
    shadow = ring.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.16))
    sh = Image.new("RGBA", canvas.size, INK + (0,))
    sh.putalpha(shadow)
    canvas.alpha_composite(sh, (0, 12))
    white = Image.new("RGBA", canvas.size, WHITE + (0,))
    white.putalpha(ring)
    canvas.alpha_composite(white)
    canvas.alpha_composite(im, (pad, pad))
    return canvas


def text_img(text, fnt, fill, stroke=0, stroke_fill=None, spacing=10):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    box = [int(math.floor(v)) if k < 2 else int(math.ceil(v)) for k, v in enumerate(d.multiline_textbbox((0, 0), text, font=fnt, stroke_width=stroke, spacing=spacing, align="center"))]
    im = Image.new("RGBA", (box[2] - box[0] + 8, box[3] - box[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((4 - box[0], 4 - box[1]), text, font=fnt, fill=fill, stroke_width=stroke,
                                      stroke_fill=stroke_fill, spacing=spacing, align="center")
    return im


def card(lines, width=840, pad_y=40, gap=14, border=INK, fill=WHITE):
    """lines: list of RGBA images stacked and centered on a rounded paper card."""
    h = pad_y * 2 + sum(l.height for l in lines) + gap * (len(lines) - 1)
    im = Image.new("RGBA", (width + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, 20 + width, 30 + h), 46, fill=60)
    im.paste((58, 45, 36, 255), (0, 0, im.width, im.height), sh.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.5)))
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + width, 20 + h), 46, fill=fill, outline=border, width=6)
    y = 20 + pad_y
    for l in lines:
        im.alpha_composite(l, (20 + (width - l.width) // 2, y))
        y += l.height + gap
    return im


def place(frame, im, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    if alpha <= 0 or scale <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BICUBIC)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    paste_clipped(frame, im, round(cx - im.width / 2), round(cy - im.height / 2))


def paste_clipped(frame, im, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    frame.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def clock(size=300, time_text="7:00"):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s // 2
    r = int(s * 0.36)
    # bells
    for dx in (-1, 1):
        bx = c + dx * int(r * 0.72)
        d.pieslice((bx - 52, c - r - 62, bx + 52, c - r + 42), 180, 360, fill=ORANGE, outline=INK, width=8)
    # legs
    d.line((c - r * 0.6, c + r * 0.8, c - r * 0.85, c + r * 1.15), fill=INK, width=10)
    d.line((c + r * 0.6, c + r * 0.8, c + r * 0.85, c + r * 1.15), fill=INK, width=10)
    d.ellipse((c - r, c - r, c + r, c + r), fill=WHITE, outline=INK, width=10)
    t = text_img(time_text, NUN(int(s * 0.17)), INK)
    im.alpha_composite(t, (c - t.width // 2, c - t.height // 2))
    return im


def speed_lines(frame, cx, cy, p):
    d = ImageDraw.Draw(frame)
    for i, (dy, ln) in enumerate([(-120, 170), (-40, 230), (40, 200), (120, 150)]):
        x = cx - 330 - i * 12
        d.line((x - ln, cy + dy, x, cy + dy), fill=MUTED + (int(255 * p),), width=10)


