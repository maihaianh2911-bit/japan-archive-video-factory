"""The catalogue of edits ("bảng cách edit") of an archive video: named ways to show one picture, each built from
the moves of the approved sample 00-video-mau/MAU-EDIT-20S.mp4 (whole picture at full width, a picture with a
detail box below, a ring that appears when the voice names the thing, a close crop with a gold caption, a tall
picture for the closing question) and the two moves the owner's guide adds for documents (whole map, then a slow
push to the named part; a slow drift).

A shot of picks.json may carry "edit": "<name>". The name only fills defaults for the fields a shot already has
(still, drift, the moment of a ring or a zoom); every field written in the shot wins over the preset. Where an edit
points at something (a ring, a zoom target, a detail box, a crop), Claude still gives the box: the preset fixes
when and how, not where. A shot without "edit" is planned exactly as before. "why" (a short Vietnamese reason) is
kept for the edit list and never drawn.

Used by build.py (the plan of both the preview and the render). The table in AGENT_ARC.md §2 says when to use each.
"""

# name → vi (name shown to the owner), look (what the viewer sees), use (when, by the meaning of the line),
#        set (defaults for shot fields), need (fields Claude must give), ring / zoom (moment as a share of the shot)
EDITS = {
    'toan-canh': {
        'vi': 'Toàn cảnh', 'look': 'cả tấm ảnh, rộng hết khung, trôi vào rất chậm',
        'use': 'câu nhắc một địa điểm, di tích, tòa nhà: cho thấy toàn bộ nơi đó',
        'set': {}, 'need': []},
    'toan-canh-chi-tiet': {
        'vi': 'Toàn cảnh + ô chi tiết', 'look': 'ảnh rộng ở trên, một ô phóng một phần của chính ảnh đó ở dưới',
        'use': 'câu nói "ở đâu" rồi "có gì ở đó": ảnh toàn cảnh rất ngang, cần thấy rõ thêm một chỗ',
        'set': {}, 'need': ['detail.view']},
    'so-sanh': {
        'vi': 'So sánh hai ảnh', 'look': 'hai ảnh khác nhau xếp trên dưới, đứng yên',
        'use': 'câu so sánh hai vật ("giống như…", "khác với…", trước và sau)',
        'set': {'still': True}, 'need': ['detail.img']},
    'khoanh': {
        'vi': 'Khoanh chi tiết', 'look': 'ảnh đứng yên, vòng khoanh hiện đúng lúc giọng đọc nhắc tới vật đó',
        'use': 'câu chỉ vào một cấu trúc hay vị trí trong ảnh (vòng cột đá, một căn phòng trên sơ đồ, một dấu trên bản đồ)',
        'set': {'still': True}, 'need': ['marks'], 'ring': 0.3},
    'can-canh': {
        'vi': 'Cận cảnh có chú thích', 'look': 'cắt sát vào chi tiết, dòng chú thích vàng nhỏ dưới ảnh',
        'use': 'câu nhắc một hình chạm khắc, dòng chữ, bộ phận của hiện vật: phải nhận ra được vật đó',
        'set': {}, 'need': ['view', 'caption']},
    'tai-lieu-zoom': {
        'vi': 'Tài liệu rồi phóng vào', 'look': 'cả tài liệu trước, rồi phóng chậm vào đúng phần được nhắc',
        'use': 'bản đồ, bản thảo, phiến đất sét, trang sách: người xem thấy nó là gì rồi mới thấy chỗ được nói tới',
        'set': {}, 'need': ['zoom.to'], 'zoom': 0.4, 'zoom_dur': 1.6},
    'dung-yen': {
        'vi': 'Đứng yên', 'look': 'cả tấm ảnh, không chuyển động',
        'use': 'bản đồ, trang chữ, sơ đồ cần thời gian đọc; cũng dùng để nghỉ giữa hai cảnh có chuyển động',
        'set': {'still': True}, 'need': []},
    'troi-cham': {
        'vi': 'Trôi chậm', 'look': 'cả tấm ảnh, trôi vào rõ hơn một chút',
        'use': 'truyền thuyết, thần thoại, cảnh trong tranh cổ, bản khắc: để người xem ngắm bức tranh',
        'set': {'drift': 0.09}, 'need': []},
    'chan-dung': {
        'vi': 'Chân dung', 'look': 'ảnh hoặc tranh người, giữ nguyên cả hình, chú thích tên và năm dưới ảnh',
        'use': 'câu nhắc một người có thật (nhà khảo cổ, vua, tác giả): chân dung thật của người đó',
        'set': {'drift': 0.03}, 'need': ['caption']},
    'so-lieu': {
        'vi': 'Con số / mốc thời gian', 'look': 'tiêu đề lớn đổi thành con số hay năm, ảnh đứng yên',
        'use': 'câu có con số, niên đại, kích thước, hoặc nhảy sang một thời khác ("năm 1887…", "ba nghìn năm trước…")',
        'set': {'still': True}, 'need': ['title']},
    'ket': {
        'vi': 'Câu hỏi kết', 'look': 'tấm ảnh ấn tượng nhất của chủ đề, trôi vào chậm đến hết video',
        'use': 'câu hỏi hoặc điều bí ẩn ở cuối video',
        'set': {'drift': 0.1}, 'need': []},
}


def _has(p, path):
    cur = p
    for k in path.split('.'):
        if not isinstance(cur, dict) or cur.get(k) in (None, '', []):
            return False
        cur = cur[k]
    return True


def expand(p, where):
    """Shot of picks.json → (shot with the preset's defaults filled in, timing).
    timing = {'ring': share of the shot after which a ring without "at" appears, 'zoom': the same for a zoom
    without "at"} — both None without a preset, so a shot without "edit" comes back unchanged.
    where = "cảnh 2, ảnh 1", for the error messages."""
    name = p.get('edit')
    if name is None:
        return p, {'ring': None, 'zoom': None}
    if name not in EDITS:
        raise SystemExit(f'picks.json {where}: không có kiểu edit "{name}". Các kiểu dùng được: {", ".join(EDITS)}')
    e = EDITS[name]
    q = {**e['set'], **p}   # what the shot says wins over the preset
    if name == 'so-sanh' and isinstance(q.get('detail'), dict) and not q['detail'].get('view'):
        q['detail'] = {'view': [0, 0, 1, 1], **{k: v for k, v in q['detail'].items() if k != 'view'}}
    missing = [f for f in e['need'] if not _has(q, f)]
    if name == 'khoanh' and not missing and not all(isinstance(m, dict) and m.get('box') for m in q['marks']):
        missing = ['marks[].box']
    if missing:
        raise SystemExit(f'picks.json {where}: kiểu edit "{name}" ({e["vi"]}) cần thêm {", ".join(f"`{m}`" for m in missing)} '
                         f'— kiểu này chỉ định sẵn cách và lúc hiện, còn vị trí / nội dung thì phải ghi trong ảnh đó.')
    if e.get('zoom_dur') and isinstance(q.get('zoom'), dict) and 'dur' not in q['zoom']:
        q['zoom'] = {**q['zoom'], 'dur': e['zoom_dur']}
    return q, {'ring': e.get('ring'), 'zoom': e.get('zoom')}


def moment(s, e, share, cap):
    """A point `share` of the way through a shot (s..e seconds), at most `cap` seconds after its start: the sample
    draws its rings 30 % into the shot, once the viewer has seen the picture."""
    return s + min(cap, share * (e - s))


def describe(p):
    """What a shot without a named edit does, in a few Vietnamese words (for the edit list)."""
    bits = []
    if p.get('detail'): bits.append('ô chi tiết')
    if p.get('zoom'): bits.append('phóng vào')
    if p.get('marks'): bits.append('khoanh')
    if p.get('caption'): bits.append('chú thích')
    if p.get('still'): bits.append('đứng yên')
    return 'tự đặt: ' + (', '.join(bits) if bits else 'cả ảnh, trôi chậm')


def table(rows):
    """edits.md: one row per shot (number, line, picture, edit, why), then the catalogue, so the owner can answer
    "cảnh 5 đổi sang kiểu khoanh". rows = [{'n', 'scene', 'shot', 'start', 'said', 'image', 'label', 'edit', 'why', 'auto'}]."""
    cell = lambda t: str(t).replace('|', '/').replace('\n', ' ').strip()
    out = ['# Cách edit từng cảnh', '',
           'Muốn đổi thì viết, ví dụ: "cảnh 5 đổi sang kiểu khoanh" hoặc "cảnh 3 đứng yên thôi".', '',
           '| Cảnh | Giây | Câu đọc | Ảnh | Kiểu edit | Vì sao |', '|---|---|---|---|---|---|']
    for r in rows:
        kind = f"`{r['edit']}` — {EDITS[r['edit']]['vi']}" if r.get('edit') else f"({r['auto']})"
        out.append(f"| {r['n']} | {r['start']:.1f} | {cell(' '.join(r['said'])) or '(tiếp câu trước)'} | {cell(r['label'] or r['image'])} | {kind} | {cell(r.get('why') or '')} |")
    run = 1
    for a, b in zip(rows, rows[1:]):
        run = run + 1 if a.get('edit') and a.get('edit') == b.get('edit') else 1
        if run == 3:
            out += ['', f"Lưu ý: ba cảnh liền nhau (đến cảnh {b['n']}) cùng một kiểu `{b['edit']}` — nên đổi một cảnh cho đỡ đều."]
    out += ['', '## Các kiểu edit có thể chọn', '', '| Kiểu | Trông thế nào | Dùng khi |', '|---|---|---|']
    out += [f"| `{k}` — {e['vi']} | {e['look']} | {e['use']} |" for k, e in EDITS.items()]
    return '\n'.join(out) + '\n'
