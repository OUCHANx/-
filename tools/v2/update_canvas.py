"""Swap the reel strips in the page-1 schedule boards for the v2 versions.

usage: python3 update_canvas.py <json map date->blob url>
"""
import json, re, sys

ROOT = "/tmp/claude-0/-home-claude/e1262836-2dc0-5244-b0d8-111f74c7d55a/scratchpad/post01/project/"
new = json.load(open(sys.argv[1]))  # {"2026-10-25": "/_blob/<id>", ...}


def label_to_date(label):
    m, d = re.match(r"(\d+)/(\d+)", label).groups()
    return f"2026-{int(m):02d}-{int(d):02d}"


changed = {}
for n in range(1, 6):
    p = ROOT + f"schedule-week{n}.dc.html"
    s = open(p).read()
    m = re.search(r"const days = (\[.*?\]);", s, flags=re.S)
    days = json.loads(m.group(1))
    c = 0
    for d in days:
        date = label_to_date(d["label"])
        if date in new:
            d["reel"] = new[date]
            c += 1
    s = s[:m.start(1)] + json.dumps(days, ensure_ascii=False) + s[m.end(1):]
    s = s.replace("ストーリーズ 8:00 ・ カルーセル 12:30（月水金）・ リール 20:00",
                  "ストーリーズ 8:00 ・ カルーセル 12:30（月水金）・ リール 20:00（10/25から新しい作り：音声つき）")
    open(p, "w").write(s)
    changed[n] = c
print(changed)
