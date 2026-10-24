#!/bin/sh
cd /home/claude/reel/v2
D=$(cd /home/claude/reel && python3 -c "
import content
print(' '.join(sorted({x['date'] for x in content.REELS if x['date']>'2026-10-25'})))
")
echo $D | tr ' ' '\n' | xargs -P 2 -I{} sh -c 'python3 reel_v2.py reel {} 2>&1 | grep -v INFO'
ls out/reels | wc -l
