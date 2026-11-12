"""Frame layout of an archive video, shared by build.py (the plan rendered by src/arc/ArcV.tsx) and preview.py.

Measured on the approved sample 00-video-mau/MAU-EDIT-20S.mp4 (720×1280) and scaled ×1.5 to 1080×1920:
dark brown background, a short gold bar, a small gold label (place / kind of document), a large cream title,
the picture in the middle with a thin border (full width for landscape pictures), the subtitle under the picture
(two rows), the credit small at the foot. Everything in pixels of the 1080×1920 frame.
"""
W, H = 1080, 1920
MARGIN = 69                 # left/right margin of picture and header
MAX_W = W - 2 * MARGIN      # 942: a landscape picture uses the full width
MAX_H = 915                 # tallest picture (portrait), as the P43 shot of the sample
HEAD = 297                  # gold bar top → picture top
BLOCK_CENTER = 832          # header + picture are centred around this height (sample: 830–832)
STACK_GAP = 47              # gap between a picture and its detail below (sample: panorama + detail)
STACK_SECOND = 0.88         # the detail is a little narrower than the picture above it
CAPTION_GAP, CAPTION_H = 46, 52
SUB_GAP, SUB_Y, SUB_MAX = 70, 1472, 1530   # the sample keeps the subtitle at one height (glyphs from y≈1489)
CREDIT_Y = 1745
TITLE_SIZE, TITLE_OPEN, TITLE_BOX = 90, 112, 942   # the opening title is larger (sample: 約1万2千年前)


def title_size(title, opening=False):
    """Title font size: 90 px (112 px on the first shot), smaller for a long title so it stays on one row.
    Half-width characters (digits, latin) count as half."""
    n = max(1.0, sum(0.55 if ord(c) < 0x2000 else 1.0 for c in (title or '')))
    return min(TITLE_OPEN if opening else TITLE_SIZE, int(TITLE_BOX / (n * 1.02)))


def fit(aspect, max_w, max_h):
    """Largest box of this aspect (w/h) inside max_w × max_h."""
    w = max_w; h = w / aspect
    if h > max_h:
        h = max_h; w = h * aspect
    return w, h


def shot_layout(aspects, caption=False):
    """Boxes for one shot. aspects = [w/h of the shown view] (1 picture, or 2 = picture + detail below).
    Returns {'bar': y, 'boxes': [[x, y, w, h], ...], 'caption': y | None, 'sub': y}."""
    if len(aspects) == 1:
        sizes = [fit(aspects[0], MAX_W, MAX_H)]
    else:
        a, b = aspects[:2]
        wa, ha = fit(a, MAX_W, MAX_H); wb, hb = fit(b, MAX_W * STACK_SECOND, MAX_H)
        k = min(1.0, (MAX_H - STACK_GAP) / (ha + hb))
        sizes = [(wa * k, ha * k), (wb * k, hb * k)]
    img_h = sum(h for _, h in sizes) + STACK_GAP * (len(sizes) - 1)
    block = HEAD + img_h + (CAPTION_GAP + CAPTION_H if caption else 0)
    bar = max(140, BLOCK_CENTER - block / 2)
    y = bar + HEAD; boxes = []
    for w, h in sizes:
        boxes.append([round((W - w) / 2, 1), round(y, 1), round(w, 1), round(h, 1)]); y += h + STACK_GAP
    bottom = y - STACK_GAP
    cap = None
    if caption:
        cap = round(bottom + CAPTION_GAP, 1); bottom = cap + CAPTION_H
    sub = round(min(SUB_MAX, max(SUB_Y, bottom + SUB_GAP)), 1)
    return {'bar': round(bar, 1), 'boxes': boxes, 'caption': cap, 'sub': sub}


def fit_view(view, aspect_px, img_w, img_h):
    """Grow view [x0, y0, x1, y1] (fractions of the picture) around its centre to the box aspect (w/h in pixels),
    then shift/shrink it to stay inside the picture."""
    x0, y0, x1, y1 = view
    vw, vh = (x1 - x0) * img_w, (y1 - y0) * img_h
    if vw / vh < aspect_px: vw = vh * aspect_px
    else: vh = vw / aspect_px
    if vw > img_w: vw = img_w; vh = vw / aspect_px
    if vh > img_h: vh = img_h; vw = vh * aspect_px
    cx, cy = (x0 + x1) / 2 * img_w, (y0 + y1) / 2 * img_h
    cx = min(img_w - vw / 2, max(vw / 2, cx)); cy = min(img_h - vh / 2, max(vh / 2, cy))
    return [round((cx - vw / 2) / img_w, 5), round((cy - vh / 2) / img_h, 5), round((cx + vw / 2) / img_w, 5), round((cy + vh / 2) / img_h, 5)]
