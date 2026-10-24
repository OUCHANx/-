"""5-frame strips of the v2 reels for the canvas overview (1350x480, same as before)."""
import glob, os, subprocess
from PIL import Image

SRC = "/home/claude/reel/v2/out/reels/"
OUT = "/home/claude/reel/v2/out/strips/"
os.makedirs(OUT, exist_ok=True)
tmp = "/tmp/claude-0/-home-claude/e1262836-2dc0-5244-b0d8-111f74c7d55a/scratchpad/strip_tmp/"
os.makedirs(tmp, exist_ok=True)
for f in sorted(glob.glob(SRC + "*.mp4")):
    date = os.path.basename(f)[:-4]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "csv=p=0", f]).decode())
    ts = [0.0, dur * 0.22, dur * 0.45, dur * 0.66, dur * 0.86]
    strip = Image.new("RGB", (1350, 480), "white")
    for i, t in enumerate(ts):
        p = tmp + f"{date}_{i}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1", "-vf",
                        "scale=270:480", p], check=True)
        strip.paste(Image.open(p).convert("RGB"), (i * 270, 0))
    strip.save(OUT + f"r2_{date}.jpg", quality=85)
print(len(glob.glob(OUT + "*.jpg")), "strips")
