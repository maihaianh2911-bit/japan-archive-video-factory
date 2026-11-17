#!/usr/bin/env python3
"""Plan of an archive video for the ArcV composition, plus music bed, subtitles and picture credits.

Usage: build.py <job_dir arc/N> <public_dir> <N> <img_src_dir> <out_dir>
Reads <job_dir>/script.json (lines, scenes), <job_dir>/picks.json (shots per scene), <public_dir>/arc/<N>/voice/
lines.json (measured line lengths) and the prepared pictures in <public_dir>/arc/<N>/img/. Writes
<out_dir>/plan.json, subtitles.srt, credits.txt, sources.json, edits.md and <public_dir>/arc/<N>/bed.wav.
A shot of picks.json may name an edit of the catalogue ("edit", see edits.py): it fills defaults for the shot's
fields; edits.md lists every shot with its line, picture, edit and reason, for the owner.
Timing: every line starts after the previous one plus a pause (0.45 s after a sentence end, 0.25 s otherwise;
0.3 / 0.12 s with script.json "pace": "fast");
a shot that starts on a line ("at", fractional = part-way through the line) cuts in just before it is spoken;
a mark ("at") appears at that moment of the voice. Cuts are hard, as in the sample, unless script.json "fade" (seconds)
asks for a dissolve between pictures.
"""
import json, os, re, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import music_gen as mg
import layout as L
import edits as E

job, pub, N, imgsrc, out = sys.argv[1:6]
base = f'arc/{N}'
spec = json.load(open(f'{job}/script.json', encoding='utf-8'))
picks = json.load(open(f'{job}/picks.json', encoding='utf-8'))
lines = json.load(open(f'{pub}/{base}/voice/lines.json', encoding='utf-8'))
dur = {r['i']: r['duration'] for r in lines}
text = {r['i']: r['text'] for r in lines}
os.makedirs(out, exist_ok=True)
STYLE = spec.get('style', 'paper')   # paper (default, owner 13/11) | warm | classic — see src/arc/ArcV.tsx
scenes_in = spec['scenes']
if len(lines) != len(spec['lines']):
    raise SystemExit(f'giọng đọc có {len(lines)} câu, script.json có {len(spec["lines"])} câu: chạy lại bước prepare')
# scenes[].lines must cover 1..len(lines) in order, without gap or overlap: a line left out would be dropped silently
span = lambda a, b: f'câu {a}' if a == b else f'câu {a}–{b}'
nxt = 1
for si, sc in enumerate(scenes_in, 1):
    r = sc.get('lines')
    if not (isinstance(r, list) and len(r) == 2 and all(type(x) is int for x in r) and r[0] <= r[1]):
        raise SystemExit(f'script.json cảnh {si}: "lines" phải là [câu đầu, câu cuối] (số nguyên), đang là {r!r}')
    if r[0] != nxt:
        raise SystemExit(f'script.json cảnh {si}: "lines" {r} phải bắt đầu ở câu {nxt} '
                         + (f'({span(nxt, r[0] - 1)} không thuộc cảnh nào)' if r[0] > nxt else '(trùng với cảnh trước)'))
    nxt = r[1] + 1
if nxt != len(lines) + 1:
    raise SystemExit(f'script.json: các cảnh phủ câu 1–{nxt - 1}, nhưng có {len(lines)} câu '
                     + (f'({span(nxt, len(lines))} không thuộc cảnh nào)' if nxt <= len(lines) else '(cảnh trỏ tới câu không có)'))
if len(picks['scenes']) != len(scenes_in):
    raise SystemExit(f'picks.json có {len(picks["scenes"])} cảnh, script.json có {len(scenes_in)} cảnh')
# named edits → plain shot fields (a shot without "edit" comes back as it is); unknown names and missing boxes stop here
picked = [[E.expand(p, f'cảnh {si}, ảnh {j}') for j, p in enumerate(ps['shots'], 1)] for si, ps in enumerate(picks['scenes'], 1)]

# ---- subtitles: a spoken line becomes one cue of up to two rows, or two cues when it is too long
ROW = 17   # characters per row (50 px)
PUNCT, PART = '、。」？！', 'をにへはがでとものやて'   # て: 〜として|受け継ぐ
def is_kana(c): return '぀' <= c <= 'ゟ'
def breaks(t):
    out = []
    for k in range(2, len(t) - 1):
        if t[k - 1] in PUNCT and t[k] not in PUNCT: out.append((k, 0))
        elif t[k - 1] in PART and not is_kana(t[k]) and t[k] not in PUNCT: out.append((k, 3.0 if t[k - 1] in 'のや' else 2.5))
    return out
def two_rows(t):
    best = min(breaks(t) or [(len(t) // 2, 6)], key=lambda b: max(b[0], len(t) - b[0]) + b[1])
    return [t[:best[0]], t[best[0]:]]
def cues(t):
    if len(t) <= 11 or (len(t) <= ROW and not breaks(t)): return [[t]]   # the sample shows most lines on two rows
    r = two_rows(t)
    if max(map(len, r)) <= ROW + 1: return [r]
    cand = [b for b in breaks(t) if b[1] == 0] or breaks(t) or [(len(t) // 2, 0)]
    k = min(cand, key=lambda b: abs(b[0] - len(t) / 2))[0]
    return cues(t[:k]) + cues(t[k:])

# ---- pictures prepared by prep.py
size = {}
def img_size(name):
    if name not in size:
        if name not in picks['images']: raise SystemExit(f'picks.json: không có ảnh "{name}" trong "images"')
        size[name] = Image.open(f'{pub}/{base}/img/{name}.jpg').size
    return size[name]

# ---- timeline
LEAD, TAIL = 0.25, 1.4
# pauses after a sentence end / after a comma; "pace": "fast" (owner 17/11: "nhịp nhanh lên chút") tightens them
GAP_END, GAP = (0.3, 0.12) if spec.get('pace') == 'fast' else (0.45, 0.25)
t = LEAD; starts = {}; subs = []; voice = []
for sc in scenes_in:
    a, b = sc['lines']
    for i in range(a, b + 1):
        starts[i] = t
        voice.append({'s': round(t, 3), 'src': f'{base}/voice/{lines[i - 1]["file"]}'})
        parts = cues(text[i]); n_all = len(text[i])
        if len(parts) > 1 and min(len(''.join(cu)) for cu in parts) / n_all * dur[i] < 1.0: parts = [two_rows(text[i])]
        done = 0
        for cu in parts:   # cues share the line's time in proportion to their length; a line's first cue comes in with the cut
            cs = t + dur[i] * done / n_all - (0.15 if done == 0 else 0); done += len(''.join(cu)); ce = t + dur[i] * done / n_all
            subs.append({'s': round(cs, 3), 'e': round(ce, 3), 'text': '\n'.join(cu), 'hl': spec.get('hl', {}).get(str(i), [])})
        t += dur[i] + (GAP_END if text[i].endswith(('。', '」', '？', '！')) else GAP)
total = round(t - 0.25 + TAIL, 3)
# owner's iron rule (16/11/2026): no video under 60 s; under 60 s nothing is rendered
MIN_S = float(os.environ.get('ARC_MIN_SECONDS', '60'))
if total < MIN_S:
    raise SystemExit(f'video chỉ dài {total:.1f} giây, dưới {MIN_S:.0f} giây: không dựng (luật của chủ kênh). '
                     'Viết thêm câu vào script.json rồi đẩy lại cùng picks.json.')
# a cue stays until the next one (no flicker between lines of one scene); the last one until the end
for x, y in zip(subs, subs[1:]): x['e'] = round(max(x['e'], min(y['s'], x['e'] + 0.6)), 3)
subs[-1]['e'] = round(total - 0.3, 3)

def at_time(li):
    """Moment of line number li (fractional = part-way through the line), on the voice timeline."""
    k = int(li); k = min(max(starts), max(min(starts), k))
    return starts[k] + (li - int(li)) * dur[k]

def motion(v, aspect, box_aspect, k, drift):
    """Move of a moving shot: {'from': view, 'to': view} (fractions of the picture), eased over the shot.
    A picture wider than its box pans across its whole width (left→right on even shots, right→left on odd ones);
    otherwise it pushes in (even) or pulls out (odd) by 10–22 % (more for the edits that ask for a stronger drift),
    centred a little above the middle (faces, inscriptions)."""
    x0, y0, x1, y1 = v
    if aspect > box_aspect * 1.02:
        vw = (x1 - x0) * box_aspect / aspect
        left, right = [x0, y0, x0 + vw, y1], [x1 - vw, y0, x1, y1]
        a, b = (left, right) if k % 2 == 0 else (right, left)
    else:
        amt = max(0.1, min(0.22, drift * 2 + 0.02))
        w, h = (x1 - x0) * (1 - amt), (y1 - y0) * (1 - amt)
        cx, cy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.45
        cx = min(x1 - w / 2, max(x0 + w / 2, cx)); cy = min(y1 - h / 2, max(y0 + h / 2, cy))
        inner = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
        a, b = (list(v), inner) if k % 2 == 0 else (inner, list(v))
    return {'from': [round(x, 5) for x in a], 'to': [round(x, 5) for x in b]}


shots = []
for si, (sc, ps) in enumerate(zip(scenes_in, picks['scenes'])):
    a, b = sc['lines']; s0 = 0.0 if si == 0 else starts[a] - 0.15
    e0 = total if si == len(scenes_in) - 1 else starts[scenes_in[si + 1]['lines'][0]] - 0.15
    n = len(ps['shots'])
    bounds = [s0] + [at_time(p['at']) - 0.15 if p.get('at') else s0 + (e0 - s0) * j / n for j, p in enumerate(ps['shots'][1:], 1)] + [e0]
    for j, (p, when) in enumerate(picked[si]):
        s, e = bounds[j], bounds[j + 1]
        if e - s < 0.5: raise SystemExit(f'cảnh {si + 1}, ảnh {j + 1}: chỉ hiện {e - s:.2f} s (kiểm tra "at")')
        pics = []
        main = {'img': p['img'], 'view': p.get('view') or [0, 0, 1, 1]}
        pics.append(main)
        if p.get('detail'):
            pics.append({'img': p['detail'].get('img', p['img']), 'view': p['detail']['view']})
        aspects = []
        for q in pics:
            w, h = img_size(q['img']); x0, y0, x1, y1 = q['view']
            aspects.append((x1 - x0) * w / ((y1 - y0) * h))
        # a moving shot (owner 17/11: "video gần như không chuyển động"): one picture, no ring, zoom, detail or "still":
        # a wide picture fills a squarer box and pans across, others push in or pull out; directions alternate
        moving = (STYLE != 'classic' and len(pics) == 1 and not p.get('still') and not p.get('zoom') and not p.get('marks')
                  and p.get('move', True) is not False)   # "move": false keeps a shot as before
        box_aspects = [L.fill_aspect(aspects[0])] if moving else aspects
        lay = L.shot_layout(box_aspects, caption=bool(p.get('caption')))
        boxes = []
        for q, box, asp in zip(pics, lay['boxes'], aspects):
            w, h = img_size(q['img'])
            boxes.append({'src': f"{base}/img/{q['img']}.jpg", 'w': w, 'h': h, 'box': box, 'view': q['view'],
                          'drift': 0 if p.get('still') or STYLE == 'classic' or moving else p.get('drift', 0.05)})   # slow push-in
        if moving:
            boxes[0]['move'] = motion(boxes[0]['view'], aspects[0], box_aspects[0], len(shots), p.get('drift', 0.05))
            boxes[0]['view'] = boxes[0]['move']['from']
        z = p.get('zoom')
        if z:   # slow push into a detail of the main picture (e.g. the southern edge of a map)
            w, h = img_size(p['img'])
            zs = at_time(z['at']) if z.get('at') else E.moment(s, e, when['zoom'], 2.5) if when['zoom'] else s + 0.4
            boxes[0]['zoom'] = {'to': L.fit_view(z['to'], aspects[0], w, h), 's': round(zs, 3), 'e': round(zs + z.get('dur', 1.4), 3)}
        ring = E.moment(s, e, when['ring'], 1.5) if when['ring'] else s   # a ring without "at"
        marks = [{'s': round(at_time(m['at']) if m.get('at') else ring, 3), 'box': m['box'], 'shape': m.get('shape', 'ellipse'),
                  'on': m.get('on', 0)} for m in p.get('marks', [])]
        title = p.get('title', sc.get('title', ''))
        if z: boxes[0]['drift'] = 0
        shots.append({'s': round(s, 3), 'e': round(e, 3), 'scene': si + 1, 'shot': j + 1,
                      'label': p.get('label', sc.get('label', '')), 'title': title, 'titleSize': L.title_size(title, opening=not shots),
                      'caption': p.get('caption', ''), 'credit': p.get('credit', ''), 'bar': lay['bar'], 'captionY': lay['caption'],
                      'subY': lay['sub'], 'pics': boxes, 'marks': marks,
                      **({'edit': p['edit']} if p.get('edit') else {})})   # only read by the preview and the shot sheet

# ---- music bed: a quiet score made for this length (sample: ~11 dB under the voice)
mu = {'style': 'documentary', 'key': 'D', 'mode': 'minor', 'bpm': 60, 'energy': 0.2, **spec.get('music', {})}
music = mg.render([{'from': 0, 'to': total, **mu}], lambda v: v, total)
bed = music / (np.abs(music).max() or 1) * 0.8
mg.write_wav(f'{pub}/{base}/bed.wav', bed)

plan = {'duration': total, 'theme': STYLE, 'fade': min(1.2, max(0.0, float(spec.get('fade', 0)))), 'shots': shots, 'subs': subs, 'voice': voice, 'music': f'{base}/bed.wav',
        'musicVolume': spec.get('music_volume', 0.16), 'fonts': []}
json.dump(plan, open(f'{out}/plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def ts(v):
    ms = int(round(v * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s_:02d},{ms:03d}'
with open(f'{out}/subtitles.srt', 'w', encoding='utf-8') as f:
    for k, sb in enumerate(subs, 1): f.write(f"{k}\n{ts(sb['s'])} --> {ts(sb['e'])}\n{sb['text']}\n\n")

# ---- sources: every picture used (title, author, date, licence, page), for the description and the record
idx = {}
for rnd in sorted(os.listdir(imgsrc)) if os.path.isdir(imgsrc) else []:
    ip = os.path.join(imgsrc, rnd, 'index.json')
    if os.path.exists(ip):
        for q in json.load(open(ip, encoding='utf-8')):
            for r in q['results']:
                if r.get('file'): idx[f"{rnd}/{r['file']}"] = r
seen, rows, src_rows = set(), [], []
for name, it in picks['images'].items():
    r = idx.get(it['src']) or {}
    page = it.get('page') or r.get('page') or ''
    key = page or it['src']
    if key in seen: continue
    seen.add(key)
    date = re.sub(r'date QS.*', '', r.get('date') or '').strip()
    artist = it.get('artist') or re.sub(r'\s+', ' ', r.get('artist') or '').strip()
    lic = it.get('license') or r.get('license') or '?'
    title = it.get('title') or r.get('title') or it['src']
    srcname = r.get('source', 'own' if it['src'].startswith('own/') else '')
    rows.append(f"- {title} — {artist}{f' ({date})' if date else ''} — {lic}{f' [{srcname}]' if srcname else ''}" + (f"\n  {page}" if page else ''))
    src_rows.append({'name': name, 'src': it['src'], 'title': title, 'artist': artist, 'date': date, 'license': lic, 'page': page})
open(f'{out}/credits.txt', 'w', encoding='utf-8').write(
    'Nguồn ảnh (ảnh CC BY và CC BY-SA phải ghi tên tác giả và giấy phép trong mô tả video):\n\n' + '\n'.join(rows) + '\n')
# per shot: line, subtitle, picture, page, credit, view, mark times (the record the guide asks for)
shot_rows = []; edit_rows = []
for sh, ps in zip(shots, [p for sc in picked for p, _ in sc]):
    said = [sb['text'].replace('\n', '') for sb in subs if sh['s'] - 0.01 <= sb['s'] < sh['e']]
    edit_rows.append({'n': len(edit_rows) + 1, 'scene': sh['scene'], 'shot': sh['shot'], 'start': sh['s'], 'said': said, 'image': ps['img'],
                      'label': sh['label'], 'edit': ps.get('edit'), 'why': ps.get('why'), 'auto': E.describe(ps)})
    shot_rows.append({'scene': sh['scene'], 'shot': sh['shot'], 'start': sh['s'], 'end': sh['e'], 'said': said,
                      'label': sh['label'], 'title': sh['title'], 'image': ps['img'],
                      'page': next((x['page'] for x in src_rows if x['name'] == ps['img']), ''),
                      'credit': sh['credit'], 'view': ps.get('view'), 'detail': ps.get('detail'), 'zoom': ps.get('zoom'),
                      'marks': [{'at_s': m['s'], 'box': m['box']} for m in sh['marks']],
                      **({k: ps[k] for k in ('edit', 'why') if ps.get(k)})})
json.dump({'pictures': src_rows, 'shots': shot_rows}, open(f'{out}/sources.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(f'{out}/edits.md', 'w', encoding='utf-8').write(E.table(edit_rows))
print(f'total {total} s; {len(shots)} shots; ' + ', '.join(f"{x['scene']}-{x['shot']}:{x['s']:.1f}–{x['e']:.1f}" for x in shots))
