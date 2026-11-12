"""Draw one frame of a plan shot with PIL, laid out exactly as ArcV (same boxes from layout.py), for the framing
preview. Text uses a local Japanese font (IPAGothic / Noto CJK when present), so glyph shapes differ slightly
from the video; positions, picture regions, rings and zooms are exact."""
import os
from PIL import Image, ImageDraw, ImageFont

BG, GOLD, LABEL, CREAM, SUB, RING = (33, 26, 24), (233, 190, 134), (239, 195, 145), (251, 246, 234), (255, 253, 245), (230, 180, 110)
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


def view_at(p, t):
    z = p.get('zoom')
    if not z: return p['view']
    k = ease((t - z['s']) / max(0.1, z['e'] - z['s']))
    return [v + (w - v) * k for v, w in zip(p['view'], z['to'])]


def draw(shot, t, sub, img_of):
    """Full 1080×1920 frame of `shot` at time t. img_of(src) → PIL image of a prepared picture."""
    im = Image.new('RGB', (1080, 1920), BG); d = ImageDraw.Draw(im)
    b = shot['bar']
    d.rectangle((72, b, 72 + 92, b + 6), fill=GOLD)
    if shot['label']: d.text((72, b + 46), shot['label'], fill=LABEL, font=font(40))
    if shot['title']: d.text((69, b + 135 - 0.02 * shot['titleSize']), shot['title'], fill=CREAM, font=font(shot['titleSize']))
    for i, p in enumerate(shot['pics']):
        x, y, w, h = p['box']; v = view_at(p, t); src = img_of(p['src'])
        sw, sh = src.size
        reg = src.crop((round(v[0] * sw), round(v[1] * sh), round(v[2] * sw), round(v[3] * sh))).resize((round(w), round(h)), Image.LANCZOS)
        im.paste(reg, (round(x), round(y)))
        d.rectangle((x - 1, y - 1, x + w, y + h), outline=(214, 190, 156), width=2)
        for m in shot['marks']:
            if m.get('on', 0) != i or t < m['s']: continue
            X = lambda f: x + (f - v[0]) / (v[2] - v[0]) * w; Y = lambda f: y + (f - v[1]) / (v[3] - v[1]) * h
            a, bb, c, e = m['box']; box = (X(a), Y(bb), X(c), Y(e))
            (d.rectangle if m.get('shape') == 'rect' else d.ellipse)(box, outline=RING, width=5)
    if shot.get('caption') and shot.get('captionY') is not None:
        d.text((72, shot['captionY'] + 6), shot['caption'], fill=LABEL, font=font(38))
    if sub:
        for k, row in enumerate(sub.split('\n')):
            f = font(52); wdt = d.textlength(row, font=f)
            d.text(((1080 - wdt) / 2, shot['subY'] + 17 + k * 76), row, fill=SUB, font=f)
    if shot['credit']: d.text((72, 1751), shot['credit'], fill=(214, 205, 200), font=font(25))
    return im
