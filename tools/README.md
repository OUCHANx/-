# Jacob reel tools

Scripts that render the Jacob (@jacob_chillx) reels, carousels and stories.

- `reel_lib.py`, `reel_kit.py`: drawing helpers, timeline engine, synthesized BGM/SFX
- `content.py`: month 1 content (10/23–11/21)
- `month_gen.py`: v1 templates, carousels and stories
- `v2/reel_v2.py`: v2 reels (hook visible from frame 0, English voice, shorter, UI-safe layout, custom covers)

Needs: the character PNGs in `/mnt/user-data/uploads/ChatGPT*.png`, fonts in `/home/claude/reel/fonts`
(Zen Maru Gothic, Nunito, Klee One), and the Kokoro TTS model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin`
from github.com/thewh1teagle/kokoro-onnx releases).
