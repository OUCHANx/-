import json, re, numpy as np, sys
sys.path.insert(0, "/home/claude/reel/v2")
from asr_check import asr, wer
import reel_v2 as rv
lines = json.load(open(rv.OUT + "voiced_lines.json"))
bad = 0; E = N = 0
for t, w, sp in lines:
    s = rv.tts(t, w, sp)
    h = asr(s.astype(np.float64), rv.SR)
    e, n = wer(t, h); E += e; N += n
    k = rv._kokoro.tokenizer.phonemize(rv.clean(t), "en-us") if rv._kokoro else ""
    flag = "  <-- CHECK" if n and e / n > 0.34 else ""
    if flag: bad += 1
    print(f"{w:9} {len(s)/rv.SR:4.2f}s | {t:40} | {h}{flag}")
print("overall WER", round(E / N, 3), "flagged", bad, "of", len(lines))
