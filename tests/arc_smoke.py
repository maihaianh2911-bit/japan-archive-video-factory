#!/usr/bin/env python3
"""Smoke test of the archive pipeline on made-up data (no 11labs, no picture search, no network):
pictures → prep.py → build.py → fonts.py (when FONTSOURCE is set) → preview.py → checks, and with --still two
Remotion frames of the ArcV composition (before and after a ring appears). Run from the repo root:
python3 tests/arc_smoke.py [--still]"""
import json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'arc'))
import ff, layout

N = '0'
tmp = tempfile.mkdtemp(prefix='arc-smoke-')
job, pub, imgsrc, out = (os.path.join(tmp, d) for d in ('job', 'public', 'imgsrc', 'out'))
voice = os.path.join(pub, 'arc', N, 'voice')
for d in (job, os.path.join(imgsrc, '1'), voice, out): os.makedirs(d)
run = lambda *a: subprocess.run(a, check=True, cwd=ROOT)

# pictures: a landscape site photo, a wide panorama, a tall pillar photo
rng = np.random.RandomState(1)
for name, (w, h) in {'1-1.jpg': (1600, 1200), '1-2.jpg': (2400, 830), '1-3.jpg': (900, 1350)}.items():
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.stack([150 + 60 * np.sin(xx / 70.0), 110 + 50 * np.cos(yy / 50.0), 80 + 0 * xx], axis=2) + rng.normal(0, 10, (h, w, 3))
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(os.path.join(imgsrc, '1', name), quality=90)
json.dump([{'k': 1, 'query': 'test', 'results': [
    {'title': 'Site.jpg', 'source': 'openverse/flickr', 'page': 'https://commons.wikimedia.org/wiki/File:Site.jpg', 'license': 'CC BY-SA 4.0', 'artist': 'A', 'date': '2010', 'file': '1-1.jpg'},
    {'title': 'Pano.jpg', 'page': 'https://commons.wikimedia.org/wiki/File:Pano.jpg', 'license': 'CC BY-SA 3.0', 'artist': 'B', 'date': '', 'file': '1-2.jpg'},
    {'title': 'Pillar.jpg', 'page': 'https://commons.wikimedia.org/wiki/File:Pillar.jpg', 'license': 'CC BY 4.0', 'artist': 'C', 'date': '2012', 'file': '1-3.jpg'}]}],
    open(os.path.join(imgsrc, '1', 'index.json'), 'w'))

# voice: silent lines of known length
lines = ['この遺跡は、約1万2千年前に造られた。', 'トルコ南東部のギョベクリ・テペ。', 'T字形の石柱が、円を描くように並んでいる。', '人々は、なぜここに石柱を建てたのか？']
durs = [3.6, 2.4, 3.9, 3.7]; rows = []
for i, (t, d) in enumerate(zip(lines, durs), 1):
    f = f'line_{i:02d}.mp3'
    ff.run('-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', str(d), '-c:a', 'libmp3lame', '-q:a', '5', os.path.join(voice, f))
    rows.append({'i': i, 'text': t, 'tts': t, 'voice': 'clone_190', 'file': f, 'duration': round(ff.duration(os.path.join(voice, f)), 3)})
json.dump(rows, open(os.path.join(voice, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False)

json.dump({'title': 'ギョベクリ・テペ', 'voice': 'clone_190', 'lines': lines,
           'scenes': [{'lines': [1, 1], 'title': '約1万2千年前'}, {'lines': [2, 2], 'title': 'ギョベクリ・テペ'},
                      {'lines': [3, 3], 'title': '円形に並ぶ石柱'}, {'lines': [4, 4], 'title': 'なぜ、ここに石柱を？'}],
           'hl': {'3': ['円を描く']}, 'queries': ['test']}, open(os.path.join(job, 'script.json'), 'w', encoding='utf-8'), ensure_ascii=False)
json.dump({'images': {'site': {'src': '1/1-1.jpg'}, 'pano': {'src': '1/1-2.jpg'}, 'pillar': {'src': '1/1-3.jpg', 'mode': 'bw'}},
           'scenes': [
               {'shots': [{'img': 'site', 'label': 'ギョベクリ・テペの発掘現場', 'credit': 'A / CC BY-SA 4.0'}]},
               {'shots': [{'img': 'pano', 'label': 'トルコ南東部', 'detail': {'view': [0.3, 0.3, 0.75, 1.0]}, 'credit': 'B / CC BY-SA 3.0'}]},
               {'shots': [{'img': 'site', 'label': '発掘現場の航空写真', 'credit': 'A / CC BY-SA 4.0', 'still': True,
                           'marks': [{'at': 3.3, 'box': [0.55, 0.2, 0.8, 0.5]}, {'at': 3.3, 'box': [0.4, 0.45, 0.6, 0.75]}]}]},
               {'shots': [{'img': 'pillar', 'label': 'ギョベクリ・テペ / 石柱 P43', 'credit': 'C / CC BY 4.0', 'caption': '石柱の浮き彫り'},
                          {'at': 4.5, 'img': 'site', 'view': [0, 0, 1, 1], 'zoom': {'to': [0.5, 0.5, 0.9, 0.9]}, 'credit': 'A / CC BY-SA 4.0'}]}]},
          open(os.path.join(job, 'picks.json'), 'w', encoding='utf-8'), ensure_ascii=False)

S = os.path.join(ROOT, 'scripts', 'arc')
run(sys.executable, os.path.join(S, 'prep.py'), os.path.join(job, 'picks.json'), imgsrc, os.path.join(pub, 'arc', N, 'img'))
run(sys.executable, os.path.join(S, 'build.py'), job, pub, N, imgsrc, out)
plan_p = os.path.join(out, 'plan.json')
if os.environ.get('FONTSOURCE'):
    run(sys.executable, os.path.join(S, 'fonts.py'), plan_p, os.environ['FONTSOURCE'], pub)
rend = os.path.join(tmp, 'renders'); os.makedirs(rend)
shutil.copytree(voice, os.path.join(rend, 'voice')); shutil.copytree(imgsrc, os.path.join(rend, 'img'))
run(sys.executable, os.path.join(S, 'preview.py'), job, rend, os.path.join(out, 'preview.jpg'))

plan = json.load(open(plan_p, encoding='utf-8'))
speech = sum(r['duration'] for r in rows)
assert speech + 1 < plan['duration'] < speech + 4, plan['duration']
sh = plan['shots']
assert [(x['scene'], x['shot']) for x in sh] == [(1, 1), (2, 1), (3, 1), (4, 1), (4, 2)]
assert sh[0]['s'] == 0 and sh[-1]['e'] == plan['duration'] and all(a['e'] == b['s'] for a, b in zip(sh, sh[1:]))   # no gaps
v = {x['s']: x for x in plan['voice']}; v3 = plan['voice'][2]['s']
assert abs(sh[2]['marks'][0]['s'] - (v3 + 0.3 * rows[2]['duration'])) < 0.01                    # ring at 30 % of line 3
assert sh[4]['s'] > plan['voice'][3]['s'] + 1                                                       # at 4.5 = mid-line 4
assert len(sh[1]['pics']) == 2 and sh[1]['pics'][1]['box'][2] < sh[1]['pics'][0]['box'][2]          # detail below, narrower
b0 = sh[0]['pics'][0]['box']; assert abs(b0[2] - layout.MAX_W) < 1 and abs(b0[0] - layout.MARGIN) < 1  # landscape: full width
bt = sh[3]['pics'][0]['box']; assert abs(bt[3] - layout.MAX_H) < 1 or bt[3] + 2 * layout.CAPTION_H > layout.MAX_H - 200   # portrait: tall
for x in sh: assert x['pics'][-1]['box'][1] + x['pics'][-1]['box'][3] < x['subY'] < 1600 and x['bar'] >= 140
assert sh[4]['pics'][0]['zoom']['to'][0] > 0.3 and sh[4]['pics'][0]['drift'] == 0
assert sh[0]['pics'][0]['drift'] > 0 and sh[2]['pics'][0]['drift'] == 0 and plan['theme'] == 'paper'          # slow push-in unless still/zoom
assert any(s['hl'] == ['円を描く'] for s in plan['subs'])
for sb in plan['subs']:
    r = sb['text'].split('\n'); assert len(r) <= 2 and max(map(len, r)) <= 19, sb['text']
assert ''.join(s['text'].replace('\n', '') for s in plan['subs']) == ''.join(lines)
srt = open(os.path.join(out, 'subtitles.srt'), encoding='utf-8').read(); assert srt.count('-->') == len(plan['subs'])
cred = open(os.path.join(out, 'credits.txt'), encoding='utf-8').read()
assert 'Site.jpg' in cred and 'CC BY 4.0' in cred and 'commons.wikimedia.org' in cred
src = json.load(open(os.path.join(out, 'sources.json'), encoding='utf-8'))
assert len(src['shots']) == 5 and src['shots'][2]['marks'] and src['shots'][0]['said'] and src['shots'][0]['page']
assert os.path.getsize(os.path.join(pub, 'arc', N, 'bed.wav')) > 100000
assert Image.open(os.path.join(out, 'preview.jpg')).size[0] > 1000
if os.environ.get('FONTSOURCE'):
    plan = json.load(open(plan_p, encoding='utf-8')); assert len(plan['fonts']) > 5 and all(os.path.exists(os.path.join(pub, f['file'])) for f in plan['fonts'])

if '--still' in sys.argv:
    t_ring = sh[2]['marks'][0]['s']
    run('node', os.path.join(S, 'stills.mjs'), plan_p, pub, os.path.join(out, 'still'), f'{t_ring - 0.3:.2f}', f'{t_ring + 0.6:.2f}')
    a = np.asarray(Image.open(os.path.join(out, f'still_{t_ring - 0.3:.2f}.png')).convert('RGB')).astype(int)
    b = np.asarray(Image.open(os.path.join(out, f'still_{t_ring + 0.6:.2f}.png')).convert('RGB')).astype(int)
    assert a.shape[:2] == (960, 540), a.shape
    assert abs(a[5:60, 5:60].mean(axis=(0, 1)) - np.array([228, 214, 184])).max() < 30, a[5:60, 5:60].mean(axis=(0, 1))   # ivory paper
    bx = sh[2]['pics'][0]['box']; y0, y1, x0, x1 = int(bx[1] / 2) + 6, int((bx[1] + bx[3]) / 2) - 6, int(bx[0] / 2) + 6, int((bx[0] + bx[2]) / 2) - 6
    assert a[y0:y1, x0:x1].std() > 15, 'picture missing'
    assert (np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).sum(axis=2) > 80).sum() > 300, 'ring was not drawn'
    sy = int(sh[2]['subY'] / 2)
    assert (a[sy:sy + 80] < 70).all(axis=2).mean() > 0.003, 'no subtitle text'   # dark ink on paper
print('arc smoke test OK:', round(plan['duration'], 1), 's,', len(plan['subs']), 'cues,', tmp)
