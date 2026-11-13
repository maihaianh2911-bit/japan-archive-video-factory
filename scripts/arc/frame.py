"""Draw one frame of a plan shot with PIL, laid out as ArcV (same boxes from layout.py, same themes), for the
framing preview. Text uses a local Japanese font (Noto CJK / IPAGothic when present), so glyph shapes differ a
little from the video; positions, picture regions, rings, zooms and drifts are exact."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

THEMES = {   # colours of src/arc/ArcV.tsx THEMES
    'warm': dict(bg=(27, 20, 16), bar=(233, 190, 134), label=(240, 201, 149), title=(255, 246, 230), sub=(255, 250, 240),
                 credit=(235, 225, 212), ring=(242, 192, 112), frame=(240, 201, 149), mat=0, backdrop=True),
    'paper': dict(bg=(239, 229, 207), bar=(168, 67, 42), label=(156, 63, 38), title=(43, 29, 18), sub=(36, 24, 15),
                  credit=(80, 62, 45), ring=(192, 57, 43), frame=(200, 190, 170), mat=12, backdrop=False),
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
    if not p.get('drift'): return p['view']
    k = min(1, max(0, (t - s) / max(0.5, e - s))) * p['drift'] / 2
    a, b, c, d = p['view']; w, h = c - a, d - b
    return [a + w * k, b + h * k, c - w * k, d - h * k]


def backdrop(src):
    """The picture blurred and darkened, covering the frame (warm theme)."""
    w, h = src.size; c = max(1080 / w, 1920 / h) * 1.25
    im = src.resize((max(1, round(w * c / 8)), max(1, round(h * c / 8)))).filter(ImageFilter.GaussianBlur(5))
    im = im.resize((round(w * c), round(h * c)))
    im = im.crop(((im.width - 1080) // 2, (im.height - 1920) // 2, (im.width - 1080) // 2 + 1080, (im.height - 1920) // 2 + 1920))
    return ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(1.45)).enhance(0.55)


def draw(shot, t, sub, img_of, theme='paper'):
    """Full 1080×1920 frame of `shot` at time t. img_of(src) → PIL image of a prepared picture."""
    th = THEMES.get(theme, THEMES['paper'])
    im = backdrop(img_of(shot['pics'][0]['src'])) if th['backdrop'] else Image.new('RGB', (1080, 1920), th['bg'])
    d = ImageDraw.Draw(im)
    b = shot['bar']
    d.rectangle((72, b, 72 + 92, b + 6), fill=th['bar'])
    if shot['label']: d.text((72, b + 46), shot['label'], fill=th['label'], font=font(40))
    if shot['title']: d.text((69, b + 135 - 0.02 * shot['titleSize']), shot['title'], fill=th['title'], font=font(shot['titleSize']))
    m = th['mat']
    for i, p in enumerate(shot['pics']):
        x, y, w, h = p['box']; v = view_at(p, t, shot['s'], shot['e']); src = img_of(p['src'])
        sw, sh = src.size
        reg = src.crop((round(v[0] * sw), round(v[1] * sh), round(v[2] * sw), round(v[3] * sh))).resize((round(w), round(h)), Image.LANCZOS)
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
            f = font(52); wdt = d.textlength(row, font=f)
            d.text(((1080 - wdt) / 2, shot['subY'] + 17 + k * 76), row, fill=th['sub'], font=f)
    if shot['credit']: d.text((72, 1751), shot['credit'], fill=th['credit'], font=font(25))
    return im
