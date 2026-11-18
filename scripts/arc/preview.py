#!/usr/bin/env python3
"""Preview every shot before rendering, laid out exactly as the video (same plan as the render): for each shot a
frame at its start and, when it has rings or a zoom, a frame after the last ring / at the end of the zoom, with the
times. Catches wrong pictures, cut subjects and misplaced rings before a 20-minute render.

Usage: preview.py <arc/N dir with script.json + picks.json> <renders arc/N dir with voice/ and img/> <out.jpg>
Every tile is headed "#<shot number> <scene>-<shot> <time> <edit name>" ("*" = the frame after the ring / zoom).
Also writes next to the sheet <out>.plan.json (timings of every shot and ring) and <out>.edits.md (per shot: line,
picture, edit, reason — the list the owner gets in the closing comment)."""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import frame

job, rend, out = sys.argv[1:4]
tmp = tempfile.mkdtemp(prefix='arc-preview-')
pub = os.path.join(tmp, 'public'); base = os.path.join(pub, 'arc', 'P')
os.makedirs(base); shutil.copytree(os.path.join(rend, 'voice'), os.path.join(base, 'voice'))
imgsrc = os.path.join(tmp, 'img'); shutil.copytree(os.path.join(rend, 'img'), imgsrc)
if os.path.isdir(os.path.join(job, 'own')): shutil.copytree(os.path.join(job, 'own'), os.path.join(imgsrc, 'own'), dirs_exist_ok=True)
run = lambda *a: subprocess.run([sys.executable, *a], check=True, stdout=subprocess.DEVNULL, env={**os.environ, 'ARC_MIN_SECONDS': '0'})
run(os.path.join(HERE, 'prep.py'), os.path.join(job, 'picks.json'), imgsrc, os.path.join(base, 'img'))
run(os.path.join(HERE, 'build.py'), job, pub, 'P', imgsrc, os.path.join(tmp, 'out'))
plan = json.load(open(os.path.join(tmp, 'out', 'plan.json'), encoding='utf-8'))
if plan['duration'] < 60:
    print(f"CẢNH BÁO: video dài {plan['duration']:.1f} giây, dưới 60 giây: máy sẽ không dựng (luật của chủ kênh). Thêm câu.", file=sys.stderr)
cache = {}
def img_of(src):
    if src not in cache: cache[src] = Image.open(os.path.join(pub, src)).convert('RGB')
    return cache[src]
def sub_at(t):
    return next((s['text'] for s in plan['subs'] if s['s'] <= t < s['e']), '')

tiles = []
TW, TH = 270, 480
for k, sh in enumerate(plan['shots'], 1):
    times = [sh['s'] + 0.05]
    late = [m['s'] + 0.2 for m in sh['marks']] + [p['zoom']['e'] + 0.05 for p in sh['pics'] if p.get('zoom')] \
           + [sh['e'] - 0.05 for p in sh['pics'] if p.get('move')]   # a pan / push: its last frame too
    if late: times.append(min(sh['e'] - 0.05, max(late)))
    for t in times:
        f = frame.draw(sh, t, sub_at(t), img_of, plan.get('theme', 'paper'), [plan.get('hook')] + plan.get('cards', [])).resize((TW, TH), Image.LANCZOS)
        tile = Image.new('RGB', (TW, TH + 24), (10, 10, 12)); tile.paste(f, (0, 24))
        ImageDraw.Draw(tile).text((4, 6), f"#{k} {sh['scene']}-{sh['shot']} {t:.1f}s{'*' if t != times[0] else ''} {sh.get('edit', '')}", fill=(255, 210, 90))
        tiles.append(tile)
cols = 6; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (TW + 8), rows * (TH + 32)), (0, 0, 0))
for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * (TW + 8), (i // cols) * (TH + 32)))
sheet.save(out, quality=85)
json.dump({'duration': plan['duration'], 'shots': [{k: sh[k] for k in ('scene', 'shot', 's', 'e', 'label', 'title')} | {'marks': [m['s'] for m in sh['marks']]} for sh in plan['shots']]},
          open(out + '.plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
shutil.copy(os.path.join(tmp, 'out', 'edits.md'), out + '.edits.md')
print(out, len(tiles), 'frames', f"{plan['duration']:.1f}s")
shutil.rmtree(tmp, ignore_errors=True)
