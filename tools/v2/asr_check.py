"""Rough intelligibility check of TTS voices with pocketsphinx (relative comparison only)."""
import sys, re, numpy as np
from pocketsphinx import Decoder
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

M = "/tmp/claude-0/-home-claude/e1262836-2dc0-5244-b0d8-111f74c7d55a/scratchpad/tts/"
k = Kokoro(M + "kokoro-v1.0.onnx", M + "voices.bin")
dec = Decoder()

def asr(samples, sr):
    x = resample_poly(samples, 16000, sr) if sr != 16000 else samples
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()
    dec.start_utt(); dec.process_raw(pcm, full_utt=True); dec.end_utt()
    return dec.hyp().hypstr if dec.hyp() else ""

def norm(s): return re.sub(r"[^a-z' ]", " ", s.lower().replace("’", "'")).split()

def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + (r[i-1] != h[j-1]))
    return d[-1, -1], len(r)

PH = ["I live in an apartment.", "Can I get a latte?", "For here or to go?", "Sorry, could you say that again?",
      "Could you speak a bit slower?", "Excuse me, where's the station?", "Go straight and turn left.",
      "I'm just looking, thanks.", "Could you take a picture of us?", "Five more minutes.", "I'm running late!",
      "Have a good day!", "Nice to meet you.", "Thank you so much!", "No worries, take your time."]
for v in sys.argv[1:]:
    E = N = 0
    outs = []
    for p in PH:
        s, sr = k.create(p, voice=v, speed=0.92, lang="en-us")
        h = asr(s, sr); e, n = wer(p, h); E += e; N += n; outs.append(h)
    print(f"{v:12} WER {E/N:.2f}")
    for p, h in list(zip(PH, outs))[:15]:
        print("   ", p, "->", h)
