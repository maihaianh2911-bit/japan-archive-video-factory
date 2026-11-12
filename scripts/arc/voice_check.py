#!/usr/bin/env python3
"""Check that the voice read every line right. Usage: voice_check.py <voice_dir> <check.md>

Each line_XX.mp3 is transcribed with Whisper; the transcript and the text that was sent to the voice are both
turned into hiragana (pykakasi) and compared, so homophones (代償/大将) do not count as errors while misreadings
(刑場 read as けいば) do. A line is listed for Claude to judge when a stretch of 2+ kana differs (stretches where
Whisper wrote digits are ignored). Tested on 走れメロス: all 4 real misreadings listed, plus ~7 Whisper mishearings
(mostly katakana names) that Claude dismisses. lines.json gets "heard", "score" and "diff".
"""
import difflib, json, os, re, sys
import pykakasi
from faster_whisper import WhisperModel

vd, out = sys.argv[1], sys.argv[2]
rows = json.load(open(os.path.join(vd, 'lines.json'), encoding='utf-8'))
kks = pykakasi.kakasi()
def kana(t):
    t = re.sub(r'[\s、。，．,.!?！？「」『』（）()…・—–\-]', '', t)
    return ''.join(x['hira'] for x in kks.convert(t))
m = WhisperModel('small', device='cpu', compute_type='int8')
bad = []
for r in rows:
    segs, _ = m.transcribe(os.path.join(vd, r['file']), language='ja', beam_size=5)
    heard = ''.join(s.text for s in segs).strip()
    a, b = kana(r.get('tts') or r['text']), kana(heard)
    sm = difflib.SequenceMatcher(None, a, b)
    diff = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
    r['heard'], r['score'] = heard, round(sm.ratio(), 2)
    r['diff'] = [f'{x}→{y}' for x, y in diff if len(x) >= 2 and not re.search(r'[0-9０-９]', y)]
    if r['diff']:
        bad.append(r)
    print(r['i'], r['score'], heard, flush=True)
json.dump(rows, open(os.path.join(vd, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
md = [f'# Kiểm tra giọng đọc ({len(rows)} câu, {len(bad)} câu cần xem)', '',
      'Whisper nghe lại từng câu và so theo cách đọc (hiragana). Câu nào lệch từ 2 âm trở lên được liệt kê: có thể giọng đọc sai, '
      'hoặc chỉ là Whisper nghe nhầm (hay gặp với tên katakana).', '']
if bad:
    md += ['| Câu | Văn bản gửi đọc | Whisper nghe được | Chỗ lệch (đúng→nghe) |', '|---|---|---|---|']
    md += [f"| {r['i']} | {r.get('tts') or r['text']} | {r['heard']} | {', '.join(r['diff'])} |" for r in bad]
else:
    md += ['Không có câu nào đáng ngờ.']
open(out, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
