#!/usr/bin/env python3
"""Shot sheet of the finished video for the final check: the full frame of every shot (just after it starts, and
after its last ring / zoom), labelled scene-shot and time. Usage: sheet.py <video.mp4> <plan.json> <out.jpg>"""
import json, sys, tempfile
from PIL import Image, ImageDraw
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff

video, plan, out = sys.argv[1:4]
plan = json.load(open(plan, encoding='utf-8'))
tmp = tempfile.mkdtemp()
def grab(t):
    ff.run('-ss', f'{t:.2f}', '-i', video, '-frames:v', '1', f'{tmp}/f.png')
    return Image.open(f'{tmp}/f.png').convert('RGB')
tiles = []
TW, TH = 270, 480
for sh in plan['shots']:
    times = [min(sh['e'] - 0.1, sh['s'] + 0.4)]
    late = [m['s'] + 0.3 for m in sh['marks']] + [p['zoom']['e'] + 0.1 for p in sh['pics'] if p.get('zoom')]
    if late: times.append(min(sh['e'] - 0.1, max(late)))
    for t in times:
        im = grab(t).resize((TW, TH), Image.LANCZOS)
        tile = Image.new('RGB', (TW, TH + 24), (10, 10, 12)); tile.paste(im, (0, 24))
        ImageDraw.Draw(tile).text((4, 6), f"{sh['scene']}-{sh['shot']}  {t:.1f}s", fill=(255, 210, 90))
        tiles.append(tile)
cols = 6; rows = (len(tiles) + cols - 1) // cols
s = Image.new('RGB', (cols * (TW + 8), rows * (TH + 32)), (12, 12, 14))
for i, t in enumerate(tiles): s.paste(t, ((i % cols) * (TW + 8), (i // cols) * (TH + 32)))
s.save(out, quality=85)
print(out, len(tiles), 'frames')
