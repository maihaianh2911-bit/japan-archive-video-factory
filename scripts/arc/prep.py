#!/usr/bin/env python3
"""Crop and size the pictures chosen in picks.json. Usage: prep.py <picks.json> <img_root> <out_dir>

picks.json "images": {"<name>": {"src": "<round>/<file>" (from the picture search) or "own/<file>" (arc/<N>/own/),
"rotate": 90 | -90 | 180 (optional, before the crop), "crop": [x0, y0, x1, y1] (0..1, optional: removes borders, captions, watermarks; the shown region is chosen per
shot with "view"), "mode": "keep" (default: true colours, as the sample) | "bw" (neutral black and white for
faded scans) | "warm" (slight warmth for very cold photos)}} → <out_dir>/<name>.jpg
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter


def prepare(it, root):
    """One picture of picks.json "images", cropped and graded (PIL image)."""
    im = Image.open(os.path.join(root, it['src'])).convert('RGB')
    if it.get('rotate'):   # degrees counter-clockwise (90: an aerial photo turned so the site fills a landscape box)
        im = im.rotate(it['rotate'], expand=True)
    if it.get('crop'):
        x0, y0, x1, y1 = it['crop']; W, H = im.size
        im = im.crop((round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H)))
    W, H = im.size
    if max(W, H) < 1400:  # small sources are enlarged here so the browser never scales them up
        k = 1400 / max(W, H); im = im.resize((round(W * k), round(H * k)), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=50, threshold=2))
    if max(im.size) > 3200:
        k = 3200 / max(im.size); im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    mode = it.get('mode', 'keep')
    if mode == 'keep':
        return im
    a = np.asarray(im).astype(np.float32) / 255
    if mode == 'bw':
        l = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        lo, hi = np.percentile(l, 0.5), np.percentile(l, 99.5)
        l = np.clip((l - lo) / max(1e-3, hi - lo), 0, 1)
        a = np.repeat(l[..., None], 3, axis=2) * np.array([1.0, 0.98, 0.94])
    elif mode == 'warm':
        a = np.clip(a * np.array([1.04, 1.0, 0.93]), 0, 1)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    picks, root, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    for name, it in json.load(open(picks, encoding='utf-8'))['images'].items():
        prepare(it, root).save(os.path.join(out, f'{name}.jpg'), quality=92)
        print(name, Image.open(os.path.join(out, f'{name}.jpg')).size)
