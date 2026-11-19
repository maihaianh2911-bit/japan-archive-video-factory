"""Draw one frame of a plan shot with PIL, laid out as ArcV (same boxes from layout.py, same themes), for the
framing preview. Text uses a local Japanese font (Noto CJK / IPAGothic when present), so glyph shapes differ a
little from the video; positions, picture regions, rings, zooms and drifts are exact."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

THEMES = {   # colours of src/arc/ArcV.tsx THEMES
    'warm': dict(bg=(27, 20, 16), bar=(233, 190, 134), label=(240, 201, 149), title=(255, 246, 230), sub=(255, 250, 240),
                 credit=(235, 225, 212), ring=(242, 192, 112), frame=(240, 201, 149), mat=0, backdrop=True),
    'paper': dict(bg=(239, 229, 207), bar=(168, 67, 42), label=(156, 63, 38), title=(43, 29, 18), sub=(36, 24, 15),
                  credit=(80, 62, 45), ring=(192, 57, 43), frame=(200, 190, 170), mat=12, backdrop=False, wash=0.3),
    'horror': dict(bg=(10, 5, 5), bar=(193, 18, 31), label=(181, 172, 166), title=(244, 238, 232), sub=(255, 255, 255),
                   credit=(150, 144, 140), ring=(255, 42, 42), frame=(90, 90, 90), mat=0, backdrop=True, dark=0.3, grade=(0.5, 0.8), outline=5),
    'classic': dict(bg=(33, 26, 24), bar=(233, 190, 134), label=(239, 195, 145), title=(251, 246, 234), sub=(255, 253, 245),
                    credit=(214, 205, 200), ring=(230, 180, 110), frame=(214, 190, 156), mat=0, backdrop=False),
}
FONTS = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf',
         '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']
_fonts = {}


def font(px):
    if px not in _fonts:
        f = next((p for p in FONTS if os.path.exists(p)), None)
        _fonts[px] = ImageFont.truetype(f, px) if f else ImageFont.load_default()
    return _fonts[px]


def ease(x):
    p = min(1, max(0, x)); return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def view_at(p, t, s, e):
    z = p.get('zoom')
    if z:
        k = ease((t - z['s']) / max(0.1, z['e'] - z['s']))
        return [v + (w - v) * k for v, w in zip(p['view'], z['to'])]
    mv = p.get('move')
    if mv:   # pan / push of a moving shot (owner 17/11), sine-eased over the shot as in ArcV
        import math
        k = (1 - math.cos(math.pi * min(1, max(0, (t - s) / max(0.5, e - s))))) / 2
        return [a + (b - a) * k for a, b in zip(mv['from'], mv['to'])]
    if not p.get('drift'): return p['view']
    k = min(1, max(0, (t - s) / max(0.5, e - s))) * p['drift'] / 2
    a, b, c, d = p['view']; w, h = c - a, d - b
    return [a + w * k, b + h * k, c - w * k, d - h * k]


def backdrop(src, dark=0.55, colour=1.45):
    """The picture blurred and darkened, covering the frame (warm theme; darker and paler for horror)."""
    w, h = src.size; c = max(1080 / w, 1920 / h) * 1.25
    im = src.resize((max(1, round(w * c / 8)), max(1, round(h * c / 8)))).filter(ImageFilter.GaussianBlur(5))
    im = im.resize((round(w * c), round(h * c)))
    im = im.crop(((im.width - 1080) // 2, (im.height - 1920) // 2, (im.width - 1080) // 2 + 1080, (im.height - 1920) // 2 + 1920))
    return ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(colour)).enhance(dark)


def cover(src, w, h):
    """src scaled and cropped to fill w × h."""
    c = max(w / src.width, h / src.height); im = src.resize((max(w, round(src.width * c)), max(h, round(src.height * c))))
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def graded(im, th):
    g = th.get('grade')
    return ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(g[0])).enhance(g[1]) if g else im


def draw_intro(it, t, sub, img_of, th):
    """The series' board (ArcV Intro): title, four pictures with numbers and names, this video's one framed once named."""
    im = Image.new('RGB', (1080, 1920), th['bg']); d = ImageDraw.Draw(im)
    rows = it['title'].split('\n'); n = max(1, max(sum(0.55 if ord(c) < 0x2000 else 1 for c in r) for r in rows))
    f = font(min(104, int(980 / n / 1.04))); lh = round(f.size * 1.2); top = 250 - lh * len(rows) / 2
    for k, r in enumerate(rows):
        d.text(((1080 - d.textlength(r, font=f)) / 2, top + k * lh), r, fill=th['ring'] if k == len(rows) - 1 and len(rows) > 1 else th['title'], font=f, stroke_width=5, stroke_fill=(0, 0, 0))
    picked = t >= it['mid']
    for i, p in enumerate(it['items']):
        x, y = (56, 554)[i % 2], (392, 928)[i // 2]; me = i == it['pick']
        tile = graded(cover(img_of(p['src']), 470, 440), th)
        if picked and not me: tile = ImageEnhance.Brightness(tile).enhance(0.3)
        im.paste(tile, (x, y))
        d.rectangle((x, y, x + 470, y + 440), outline=th['ring'] if picked and me else (120, 120, 120), width=5 if picked and me else 2)
        d.text((x + 14, y + 4), str(i + 1), fill=th['ring'] if picked and me else (255, 255, 255), font=font(60), stroke_width=4, stroke_fill=(0, 0, 0))
        nf = font(40); col = th['ring'] if picked and me else ((110, 105, 100) if picked else th['title'])
        d.text((x + (470 - d.textlength(p['name'], font=nf)) / 2, y + 452), p['name'], fill=col, font=nf, stroke_width=3, stroke_fill=(0, 0, 0))
    if sub:
        for k, row in enumerate(sub.split('\n')):
            sf = font(52); d.text(((1080 - d.textlength(row, font=sf)) / 2, 1517 + k * 76), row, fill=th['sub'], font=sf, stroke_width=th.get('outline', 0), stroke_fill=(0, 0, 0))
    if it.get('credit'): d.text((72, 1751), it['credit'], fill=th['credit'], font=font(23))
    return im


def draw(shot, t, sub, img_of, theme='paper', hook=None, intro=None, head=None):
    """Full 1080×1920 frame of `shot` at time t. img_of(src) → PIL image of a prepared picture. hook: the plan's
    hook, drawn over the first shot while it is on (ArcV Hook). head: the plan's fixed header (ArcV Head, owner 19/11):
    label + title at the top, the shot's label small over the picture, subtitles 60 px."""
    th = THEMES.get(theme, THEMES['paper'])
    if intro and t < intro['e']:
        return draw_intro(intro, t, sub, img_of, th)
    im = (backdrop(img_of(shot['pics'][0]['src']), th.get('dark', 0.55), 0.4 if th.get('grade') else 1.45) if th['backdrop']
          else Image.new('RGB', (1080, 1920), th['bg']))
    if th.get('wash'):   # paper: the picture blurred, sepia and faint over the paper (ArcV Wash)
        src = img_of(shot['pics'][0]['src']); w, h = src.size; c = max(1080 / w, 1920 / h) * 1.15
        bl = src.resize((max(1, round(w * c / 8)), max(1, round(h * c / 8)))).filter(ImageFilter.GaussianBlur(3.5)).resize((round(w * c), round(h * c)))
        bl = bl.crop(((bl.width - 1080) // 2, (bl.height - 1920) // 2, (bl.width - 1080) // 2 + 1080, (bl.height - 1920) // 2 + 1920))
        g = bl.convert('L'); sep = Image.merge('RGB', [g.point(lambda v: min(255, v * 1.07)), g.point(lambda v: v * 0.93), g.point(lambda v: v * 0.76)])
        im = Image.blend(im, Image.blend(bl, sep, 0.55), th['wash'])
    d = ImageDraw.Draw(im)
    b = shot['bar']
    if isinstance(hook, list):   # [hook or None, *cards]: the one on at t over this shot (ArcV Hook)
        hook = next((c for c in hook if c and c['s'] <= t < c['e'] and (c is not hook[0] or (shot.get('scene') == 1 and shot.get('shot') == 1))), None)
    hooked = bool(hook) and t < hook['e'] and abs(hook['s'] - shot['s']) < 0.4 or (hook and hook['s'] == 0 and shot.get('scene') == 1 and shot.get('shot') == 1 and t < hook['e'])
    if head:
        if shot['label']: d.text((shot['pics'][0]['box'][0] + 4, shot['pics'][0]['box'][1] - 46), shot['label'], fill=th['label'], font=font(30))
    elif not hooked:
        d.rectangle((72, b, 72 + 92, b + 6), fill=th['bar'])
        if shot['label']: d.text((72, b + 46), shot['label'], fill=th['label'], font=font(40))
        if shot['title']: d.text((69, b + 135 - 0.02 * shot['titleSize']), shot['title'], fill=th['title'], font=font(shot['titleSize']))
    m = th['mat']
    for i, p in enumerate(shot['pics']):
        x, y, w, h = p['box']; v = view_at(p, t, shot['s'], shot['e']); src = img_of(p['src'])
        sw, sh = src.size
        reg = graded(src.crop((round(v[0] * sw), round(v[1] * sh), round(v[2] * sw), round(v[3] * sh))).resize((round(w), round(h)), Image.LANCZOS), th)
        if m: d.rectangle((x - m, y - m, x + w + m, y + h + m), fill=(251, 248, 241))
        im.paste(reg, (round(x), round(y)))
        d.rectangle((x - m - 1, y - m - 1, x + w + m, y + h + m), outline=th['frame'], width=2)
        for mk in shot['marks']:
            if mk.get('on', 0) != i or t < mk['s']: continue
            X = lambda f: x + (f - v[0]) / (v[2] - v[0]) * w; Y = lambda f: y + (f - v[1]) / (v[3] - v[1]) * h
            a, bb, c, e = mk['box']; box = (X(a), Y(bb), X(c), Y(e))
            (d.rectangle if mk.get('shape') == 'rect' else d.ellipse)(box, outline=th['ring'], width=5)
    if shot.get('caption') and shot.get('captionY') is not None:
        d.text((72, shot['captionY'] + 6 + m), shot['caption'], fill=th['label'], font=font(38))
    if sub:
        for k, row in enumerate(sub.split('\n')):
            f = font(60 if head else 52); wdt = d.textlength(row, font=f)
            d.text(((1080 - wdt) / 2, shot['subY'] + 17 + k * (83 if head else 76)), row, fill=th['sub'], font=f,
                   stroke_width=th.get('outline', 0) + (1 if head else 0), stroke_fill=(0, 0, 0))
    if shot['credit']: d.text((72, 1751), shot['credit'], fill=th['credit'], font=font(25))
    if hook and hook['s'] <= t < hook['e']:
        x, y, w, h = shot['pics'][0]['box']
        dark = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(dark).rectangle((0, y, 1080, y + h), fill=(0, 0, 0, 110))
        im = Image.alpha_composite(im.convert('RGBA'), dark).convert('RGB'); d = ImageDraw.Draw(im)
        rows = hook['text'].split('\n'); n = max(sum(0.55 if ord(c) < 0x2000 else 1 for c in r) for r in rows)
        f = font(min(150, int(980 / max(1, n) / 1.04 / 1.08))); lh = round(f.size * 1.18); top = y + h / 2 - lh * len(rows) / 2
        for k, r in enumerate(rows):
            d.text(((1080 - d.textlength(r, font=f)) / 2, top + k * lh), r, fill=(255, 255, 255), font=f, stroke_width=7, stroke_fill=(0, 0, 0))
    if head:
        if head.get('label'):
            lf = font(50); d.text(((1080 - d.textlength(head['label'], font=lf)) / 2, 78), head['label'], fill=th['ring'], font=lf)
        n = max(1.0, sum(0.55 if ord(c) < 0x2000 else 1 for c in head['title']))
        tf = font(min(128, int(980 / n / 1.06)))
        d.text(((1080 - d.textlength(head['title'], font=tf)) / 2, 150), head['title'], fill=th['title'], font=tf, stroke_width=3, stroke_fill=(0, 0, 0))
    return im
