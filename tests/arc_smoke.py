#!/usr/bin/env python3
"""Smoke test of the archive pipeline on made-up data (no 11labs, no picture search, no network):
pictures → prep.py → build.py → fonts.py (when FONTSOURCE is set) → preview.py → checks, and with --still two
Remotion frames of the ArcV composition (before and after a ring appears). The picks use named edits of the
catalogue (scripts/arc/edits.py) next to a plain shot; wrong edits must be refused. The picture search has its own
tests on made-up archives (tests/find_units.py), run from here first. Run from the repo root:
python3 tests/arc_smoke.py [--still]"""
import json, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'arc'))
import ff, layout

N = '0'
os.environ['ARC_MIN_SECONDS'] = '0'   # the made-up video is 17 s; the 60-s rule is checked below
tmp = tempfile.mkdtemp(prefix='arc-smoke-')
job, pub, imgsrc, out = (os.path.join(tmp, d) for d in ('job', 'public', 'imgsrc', 'out'))
voice = os.path.join(pub, 'arc', N, 'voice')
for d in (job, os.path.join(imgsrc, '1'), voice, out): os.makedirs(d)
run = lambda *a: subprocess.run(a, check=True, cwd=ROOT)
run(sys.executable, os.path.join(ROOT, 'tests', 'find_units.py'))   # the picture search: made-up archives, no network

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
           'hl': {'3': ['円を描く']}, 'queries': ['test'], 'fade': 0.6, 'hook': '一万二千年前の\\n謎の遺跡', 'hook_hl': ['謎'],
           'cards': [{'at': 3, 'text': '第2位\\n円形の石柱', 'hl': ['第2位']}]}, open(os.path.join(job, 'script.json'), 'w', encoding='utf-8'), ensure_ascii=False)
json.dump({'images': {'site': {'src': '1/1-1.jpg'}, 'pano': {'src': '1/1-2.jpg'}, 'pillar': {'src': '1/1-3.jpg', 'mode': 'bw'}},
           'scenes': [
               {'shots': [{'img': 'site', 'edit': 'toan-canh', 'why': 'câu nhắc cả di tích', 'label': 'ギョベクリ・テペの発掘現場', 'credit': 'A / CC BY-SA 4.0'}]},
               {'shots': [{'img': 'pano', 'edit': 'toan-canh-chi-tiet', 'label': 'トルコ南東部', 'detail': {'view': [0.3, 0.3, 0.75, 1.0]}, 'credit': 'B / CC BY-SA 3.0'}]},
               {'shots': [{'img': 'site', 'edit': 'khoanh', 'why': 'giọng đọc chỉ vào hai vòng cột', 'label': '発掘現場の航空写真', 'credit': 'A / CC BY-SA 4.0',
                           'marks': [{'box': [0.55, 0.2, 0.8, 0.5]}, {'box': [0.4, 0.45, 0.6, 0.75]}]}]},   # no "at", no "still": the edit sets them
               {'shots': [{'img': 'pillar', 'label': 'ギョベクリ・テペ / 石柱 P43', 'credit': 'C / CC BY 4.0', 'caption': '石柱の浮き彫り'},   # plain shot, no edit
                          {'at': 4.5, 'img': 'site', 'edit': 'tai-lieu-zoom', 'view': [0, 0, 1, 1], 'zoom': {'to': [0.5, 0.5, 0.9, 0.9]}, 'credit': 'A / CC BY-SA 4.0'}]}]},
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

r60 = subprocess.run([sys.executable, os.path.join(S, 'build.py'), job, pub, N, imgsrc, os.path.join(tmp, 'out60')], cwd=ROOT,
                     env={**os.environ, 'ARC_MIN_SECONDS': '60'}, capture_output=True, text=True)
assert r60.returncode != 0 and 'dưới 60 giây' in r60.stderr, r60.stderr   # owner's rule: under 60 s nothing is rendered
fast = json.load(open(os.path.join(job, 'script.json'), encoding='utf-8')); fast['pace'] = 'fast'
fast.update({'loudness': -14.7, 'style': 'horror', 'intro': {'title': '最恐の都市伝説\\n四選', 'pick': 2, 'name_at': 2, 'until': 3, 'items': [
    {'img': 'site', 'name': '一'}, {'img': 'pano', 'name': '二'}, {'img': 'pillar', 'name': '三'}, {'img': 'site', 'name': '四'}]},
    'head': {'label': '怖い都市伝説', 'title': '口裂け女の真実', 'hl': ['真実']}})
jf = os.path.join(tmp, 'jobfast'); shutil.copytree(job, jf); json.dump(fast, open(os.path.join(jf, 'script.json'), 'w', encoding='utf-8'), ensure_ascii=False)
run(sys.executable, os.path.join(S, 'build.py'), jf, pub, N, imgsrc, os.path.join(tmp, 'outfast'))
pf = json.load(open(os.path.join(tmp, 'outfast', 'plan.json'), encoding='utf-8')); d_fast = pf['duration']
# horror look + the series' board (owner 18/11): the item named on line 2 lights up, the board ends when line 3 starts
assert pf['theme'] == 'horror' and pf['intro']['pick'] == 1 and len(pf['intro']['items']) == 4 and 0 < pf['intro']['mid'] < pf['intro']['e']
assert abs(pf['intro']['e'] - (pf['voice'][2]['s'] - 0.15)) < 0.01 and pf['intro']['title'] == '最恐の都市伝説\n四選'
# the fixed header (owner 19/11): title at the top in the brush font, subtitles 60 px in rows of at most 16 characters
assert pf['head']['title'] == '口裂け女の真実' and pf['display'] == 'Yuji Boku' and pf['subSize'] == 60
assert max(len(r) for x in pf['subs'] for r in x['text'].split('\n')) <= 16, [x['text'] for x in pf['subs']]
assert os.path.getsize(os.path.join(pub, pf['grain'])) > 50000 and os.path.getsize(os.path.join(pub, pf['sfx'])) > 100000
run(sys.executable, os.path.join(S, 'preview.py'), jf, rend, os.path.join(tmp, 'outfast', 'preview.jpg'))
plan = json.load(open(plan_p, encoding='utf-8'))
speech = sum(r['duration'] for r in rows)
assert speech + 1 < plan['duration'] < speech + 4, plan['duration']
assert plan['duration'] - d_fast > 0.4, (plan['duration'], d_fast)   # pace fast: shorter pauses between lines
sh = plan['shots']
assert [(x['scene'], x['shot']) for x in sh] == [(1, 1), (2, 1), (3, 1), (4, 1), (4, 2)]
assert sh[0]['s'] == 0 and sh[-1]['e'] == plan['duration'] and all(a['e'] == b['s'] for a, b in zip(sh, sh[1:]))   # no gaps
v = {x['s']: x for x in plan['voice']}; v3 = plan['voice'][2]['s']
assert abs(sh[2]['marks'][0]['s'] - (sh[2]['s'] + 0.3 * (sh[2]['e'] - sh[2]['s']))) < 0.01 and sh[2]['marks'][0]['s'] > v3   # "khoanh": ring 30 % into the shot
assert [x.get('edit') for x in sh] == ['toan-canh', 'toan-canh-chi-tiet', 'khoanh', None, 'tai-lieu-zoom']
z4 = sh[4]['pics'][0]['zoom']; assert abs(z4['s'] - (sh[4]['s'] + 0.4 * (sh[4]['e'] - sh[4]['s']))) < 0.01 and abs(z4['e'] - z4['s'] - 1.6) < 0.01   # whole document first
ed = open(os.path.join(out, 'edits.md'), encoding='utf-8').read()
assert '| 3 |' in ed and '`khoanh` — Khoanh chi tiết' in ed and 'giọng đọc chỉ vào hai vòng cột' in ed and '(tự đặt: chú thích)' in ed and '`ket`' in ed
assert open(os.path.join(out, 'preview.jpg.edits.md'), encoding='utf-8').read() == ed
# a wrong edit stops the build with a message Claude can act on: an unknown name lists the valid ones, a missing box is named
good = json.load(open(os.path.join(job, 'picks.json'), encoding='utf-8'))
def refused(change):
    bad = json.loads(json.dumps(good)); change(bad['scenes'])
    bj = os.path.join(tmp, 'badjob'); shutil.rmtree(bj, ignore_errors=True); os.makedirs(bj)
    shutil.copy(os.path.join(job, 'script.json'), bj); json.dump(bad, open(os.path.join(bj, 'picks.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, os.path.join(S, 'build.py'), bj, pub, N, imgsrc, os.path.join(tmp, 'badout')], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode != 0, 'a wrong edit was accepted'
    return r.stderr
e1 = refused(lambda sc: sc[0]['shots'][0].update(edit='xoay-vong')); assert 'xoay-vong' in e1 and 'khoanh' in e1 and 'tai-lieu-zoom' in e1, e1
e2 = refused(lambda sc: sc[2]['shots'][0].pop('marks')); assert 'khoanh' in e2 and 'marks' in e2 and 'cảnh 3' in e2, e2
e3 = refused(lambda sc: sc[3]['shots'][1].pop('zoom')); assert 'zoom.to' in e3, e3
assert sh[4]['s'] > plan['voice'][3]['s'] + 1                                                       # at 4.5 = mid-line 4
assert len(sh[1]['pics']) == 2 and sh[1]['pics'][1]['box'][2] < sh[1]['pics'][0]['box'][2]          # detail below, narrower
b0 = sh[0]['pics'][0]['box']; assert abs(b0[2] - layout.MAX_W) < 1 and abs(b0[0] - layout.MARGIN) < 1  # landscape: full width
assert b0[2] / b0[3] < 1.05   # a moving landscape shot fills a squarer box and pans across it
bt = sh[3]['pics'][0]['box']; assert abs(bt[3] - layout.MAX_H) < 1 or bt[3] + 2 * layout.CAPTION_H > layout.MAX_H - 200   # portrait: tall
for x in sh: assert x['pics'][-1]['box'][1] + x['pics'][-1]['box'][3] < x['subY'] < 1600 and x['bar'] >= 140
assert sh[4]['pics'][0]['zoom']['to'][0] > 0.3 and sh[4]['pics'][0]['drift'] == 0 and 'move' not in sh[4]['pics'][0]
mv = sh[0]['pics'][0]['move']; assert mv['from'] != mv['to'] and sh[0]['pics'][0]['drift'] == 0   # owner 17/11: moving shots
assert 'move' not in sh[2]['pics'][0] and sh[2]['pics'][0]['drift'] == 0 and plan['theme'] == 'paper'  # a ring shot stays still
assert 'move' not in sh[1]['pics'][0] and len(sh[1]['pics']) == 2                                       # picture + detail: no pan
mv3 = sh[3]['pics'][0]['move']; assert abs((mv3['to'][2] - mv3['to'][0]) - (mv3['from'][2] - mv3['from'][0]) * 0.88) < 0.02 or mv3['from'][0] > mv3['to'][0]
assert any(s['hl'] == ['円を描く'] for s in plan['subs']) and plan['fade'] == 0.6
assert plan['loudness'] == -15.0 and pf['loudness'] == -14.7   # script.json "loudness" reaches the final encode
assert plan['hook']['text'] == '一万二千年前の\n謎の遺跡' and 2.0 <= plan['hook']['e'] <= sh[0]['e']   # the hook stays over the first picture
cd = plan['cards'][0]; assert abs(cd['s'] - sh[2]['s']) < 0.05 and 1.6 <= cd['e'] - cd['s'] <= 3.0 and cd['text'] == '第2位\n円形の石柱'   # a countdown card
for sb in plan['subs']:
    r = sb['text'].split('\n'); assert len(r) <= 2 and max(map(len, r)) <= 19, sb['text']
assert ''.join(s['text'].replace('\n', '') for s in plan['subs']) == ''.join(lines)
srt = open(os.path.join(out, 'subtitles.srt'), encoding='utf-8').read(); assert srt.count('-->') == len(plan['subs'])
cue_t = [[sum(float(x) * k for x, k in zip(re.split('[:,]', v), (3600, 60, 1, .001))) for v in m] for m in re.findall(r'(\S+) --> (\S+)', srt)]
assert all(a[0] < a[1] <= b[0] + 1e-6 for a, b in zip(cue_t, cue_t[1:])), cue_t      # .srt cues never overlap
cred = open(os.path.join(out, 'credits.txt'), encoding='utf-8').read()
assert 'Site.jpg' in cred and 'CC BY 4.0' in cred and 'commons.wikimedia.org' in cred
src = json.load(open(os.path.join(out, 'sources.json'), encoding='utf-8'))
assert len(src['shots']) == 5 and src['shots'][2]['marks'] and src['shots'][0]['said'] and src['shots'][0]['page']
assert os.path.getsize(os.path.join(pub, 'arc', N, 'bed.wav')) > 100000
assert Image.open(os.path.join(out, 'preview.jpg')).size[0] > 1000
if os.environ.get('FONTSOURCE'):
    plan = json.load(open(plan_p, encoding='utf-8')); assert len(plan['fonts']) > 5 and all(os.path.exists(os.path.join(pub, f['file'])) for f in plan['fonts'])

# posting caption (owner 16/11/2026): the checker accepts the format of AGENT_ARC.md and names what is wrong
import caption as C
good_cap = ('三千年前の土偶の正体は？\n縄文時代の土偶を紹介します。\n大きな目の意味を考えます。\n\n'
            '#土偶 #縄文時代 #考古学 #日本史 #歴史 #shorts\n\n画像出典: 作者不詳（パブリックドメイン）')
assert C.problems(good_cap) == [], C.problems(good_cap)
assert any('hashtag' in p for p in C.problems(good_cap.replace(' #歴史 #shorts', '')))
assert any('tiếng Nhật' in p for p in C.problems('The mystery of the dogu figurine and its eyes\nA clay figure from Japan seen up close.\n\n#a #b #c #d #e\n\n画像出典: x'))
assert any('画像出典' in p for p in C.problems(good_cap.split('\n\n画像出典')[0]))

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
    t_mix = sh[2]['s'] + 0.3   # half-way through the dissolve from the panorama (shot 2) into the site (shot 3)
    run('node', os.path.join(S, 'stills.mjs'), plan_p, pub, os.path.join(out, 'still'), f'{sh[2]["s"] - 0.05:.2f}', f'{t_mix:.2f}')
    p_ = np.asarray(Image.open(os.path.join(out, f'still_{sh[2]["s"] - 0.05:.2f}.png')).convert('RGB')).astype(int)
    m_ = np.asarray(Image.open(os.path.join(out, f'still_{t_mix:.2f}.png')).convert('RGB')).astype(int)
    d_prev, d_next = np.abs(m_ - p_).mean(), np.abs(m_ - a).mean()
    assert d_prev > 3 and d_next > 3, ('no dissolve', d_prev, d_next)
    sy = int(sh[2]['subY'] / 2)
    assert (a[sy:sy + 80] < 70).all(axis=2).mean() > 0.003, 'no subtitle text'   # dark ink on paper
print('arc smoke test OK:', round(plan['duration'], 1), 's,', len(plan['subs']), 'cues,', tmp)
