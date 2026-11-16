#!/usr/bin/env python3
"""Check the posting caption of an archive video (arc/<N>/caption.txt, owner 16/11/2026: every video comes with
the text to paste when it is posted). Usage: caption.py <caption.txt> — prints the problems, exit 1 when there is one.

Format (Japanese, the channel's language; UTF-8; at most 2000 characters):
  line 1      hook title, at most 80 characters, true to the script
  lines 2–5   2–4 short sentences on what the video shows
  (blank line)
  5–8 hashtags on one line (#日本史 #歴史 … #shorts)
  (blank line)
  画像出典: … (the picture credits in short, or a pointer to credits.txt when they are too long)
Used by run.py before publishing the caption, and by Claude before pushing it.
"""
import re, sys

MAX_ALL, MAX_TITLE, TAGS = 2000, 80, (5, 8)
JA = re.compile(r'[぀-ヿ㐀-鿿]')   # kana and kanji


def problems(text):
    """List of problems of a caption, in Vietnamese (empty = good)."""
    out = []
    t = text.replace('\r\n', '\n').strip()
    if not t:
        return ['caption.txt rỗng']
    if len(t) > MAX_ALL:
        out.append(f'dài {len(t)} ký tự, tối đa {MAX_ALL}')
    lines = t.split('\n')
    title = lines[0].strip()
    if len(title) > MAX_TITLE:
        out.append(f'dòng tiêu đề dài {len(title)} ký tự, tối đa {MAX_TITLE}')
    if title.startswith('#') or not JA.search(title):
        out.append('dòng 1 phải là tiêu đề tiếng Nhật (không phải hashtag)')
    letters = [c for c in re.sub(r'#\S+|https?://\S+|画像出典.*', '', t) if c.isalpha()]
    if letters and sum(1 for c in letters if JA.match(c)) / len(letters) < 0.6:
        out.append('phần lớn chữ không phải tiếng Nhật (luật của chủ kênh: chỉ tiếng Nhật)')
    tags = re.findall(r'(?<!\S)#[^\s#]+', t)
    if not TAGS[0] <= len(tags) <= TAGS[1]:
        out.append(f'có {len(tags)} hashtag, cần {TAGS[0]}–{TAGS[1]}')
    if '画像出典' not in t:
        out.append('thiếu dòng "画像出典: …" (nguồn ảnh)')
    body = [l for l in lines[1:] if l.strip() and not l.lstrip().startswith(('#', '画像出典'))]
    if not body:
        out.append('thiếu 2–4 câu mô tả video sau dòng tiêu đề')
    return out


if __name__ == '__main__':
    bad = problems(open(sys.argv[1], encoding='utf-8').read())
    for p in bad:
        print(f'caption: {p}')
    if not bad:
        print('caption OK')
    sys.exit(1 if bad else 0)
