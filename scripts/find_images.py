#!/usr/bin/env python3
"""Find free-to-use pictures for a video, with their licence, from open archives (no API keys needed).

Usage: find_images.py <out_dir> "<query 1>" "<query 2>" ...      or      find_images.py <out_dir> --spec <file.json>

Sources (the owner, 12/11: free pictures, Wikipedia/Wikimedia is not needed):
  openverse  Openverse: Flickr, museums, science sites … (CC0, public domain, CC BY, CC BY-SA; Wikimedia excluded)
  met        The Metropolitan Museum of Art, open access (CC0)
  aic        Art Institute of Chicago (public domain works)
  cleveland  Cleveland Museum of Art, open access (CC0)
  europeana  Europeana: European libraries, archives, museums (CC0, public domain, CC BY, CC BY-SA)
  loc        Library of Congress, photos and prints (loc.gov/photos/ only, not its maps collection;
             "No known restrictions on publication" only)
  commons    Wikimedia Commons (only when asked for with this prefix)
A query without prefix searches all sources except commons and mixes the results; `met: Gilgamesh` searches one.
Write queries in English (or the language of the archive). `File:<name>` fetches one exact Commons file.
With --spec, the JSON list may also hold pictures from any page Claude checked (journal figures under CC BY, a
museum page …): {"url": "<direct image url>", "page": "<page that states the licence>", "title": "...",
"artist": "...", "license": "CC BY 4.0", "date": "..."} — each becomes its own group with one picture.

For every query: up to 8 pictures, keeping only licences that allow use in a monetised video, dropping files under
400 px and duplicate scans of the same picture (also across earlier rounds listed in FIND_SEEN). Writes
<out_dir>/<k>-<n>.jpg (up to 4000 px), <out_dir>/index.json (query, source, page, licence, author, date, size) and
<out_dir>/sheet_<k>.jpg (contact sheet with numbers and source) so Claude can choose. A query whose search fails
(every source down, a timeout …) is logged and kept with no results and an "error" in index.json; only when every
query fails does the script exit with an error. Stdlib + Pillow.
"""
import http.client, io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageDraw

UA = 'JapanArchiveVideoFactory/0.1 (https://github.com/maihaianh2911-bit/japan-archive-video-factory; licence-checked picture search)'
SOURCES = ('openverse', 'met', 'aic', 'cleveland', 'europeana', 'loc')
MIN_SIDE = 400   # shorter side in pixels: smaller files only look blurred in the video
KEEP = 8         # pictures kept per query
NET = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)   # network errors worth a retry


def get(url, tries=4, raw=True):
    """GET with retries: 429/5xx (rate limits, busy servers) and network errors (timeout, reset, cut-off reply)."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                b = r.read()
                return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(8 * (i + 1)); continue
            raise
        except NET:
            if i < tries - 1:
                time.sleep(5 * (i + 1)); continue
            raise


def js(url):
    return get(url, raw=False)


def strip(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


def item(source, title, page, url, license, artist='', date='', description='', width=None, height=None):
    return {'source': source, 'title': strip(str(title or ''))[:160], 'page': page, 'thumb': url, 'license': license,
            'artist': strip(str(artist or ''))[:160], 'date': strip(str(date or ''))[:60], 'description': strip(str(description or ''))[:300],
            'width': width, 'height': height}


# ---- sources: each returns up to n results, newest API shapes checked 12/11/2026
def openverse(q, n):
    p = {'q': q, 'page_size': n, 'license': 'by,by-sa,cc0,pdm', 'excluded_source': 'wikimedia', 'mature': 'false'}
    out = []
    for r in js('https://api.openverse.org/v1/images/?' + urllib.parse.urlencode(p)).get('results', []):
        lic = {'cc0': 'CC0', 'pdm': 'Public domain'}.get(r['license'], f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip())
        out.append(item(f"openverse/{r.get('source')}", r.get('title') or r['url'].rsplit('/', 1)[-1], r.get('foreign_landing_url'), r['url'], lic,
                        r.get('creator'), '', '', r.get('width'), r.get('height')))
    return out


def met(q, n):
    ids = js('https://collectionapi.metmuseum.org/public/collection/v1.1/search?' + urllib.parse.urlencode({'q': q, 'hasImages': 'true', 'limit': 40})).get('objectIDs') or []
    out = []
    for i in ids[:30]:
        if len(out) >= n: break
        try: o = js(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}')
        except Exception: continue
        if o.get('isPublicDomain') and o.get('primaryImage'):
            out.append(item('met', o.get('title'), o.get('objectURL'), o['primaryImage'], 'CC0 (The Met Open Access)',
                            o.get('artistDisplayName') or o.get('culture'), o.get('objectDate'), ', '.join(filter(None, [o.get('culture'), o.get('medium')]))))
        time.sleep(0.2)
    return out


def aic(q, n):
    p = {'q': q, 'limit': 40, 'fields': 'id,title,image_id,is_public_domain,artist_display,date_display,thumbnail'}
    out = []
    for r in js('https://api.artic.edu/api/v1/artworks/search?' + urllib.parse.urlencode(p)).get('data', []):
        if len(out) >= n: break
        if r.get('is_public_domain') and r.get('image_id'):
            th = r.get('thumbnail') or {}
            out.append(item('aic', r.get('title'), f"https://www.artic.edu/artworks/{r['id']}",
                            f"https://www.artic.edu/iiif/2/{r['image_id']}/full/1686,/0/default.jpg", 'Public domain (Art Institute of Chicago, CC0)',
                            r.get('artist_display'), r.get('date_display'), '', th.get('width'), th.get('height')))
    return out


def cleveland(q, n):
    p = {'q': q, 'has_image': 1, 'cc0': 1, 'limit': n}
    out = []
    for r in js('https://openaccess-api.clevelandart.org/api/artworks/?' + urllib.parse.urlencode(p)).get('data', []):
        im = (r.get('images') or {}); best = im.get('print') or im.get('web') or {}
        if not best.get('url'): continue
        cr = ', '.join(c.get('description', '') for c in r.get('creators') or [])
        out.append(item('cleveland', r.get('title'), r.get('url'), best['url'], 'CC0 (Cleveland Museum of Art)', cr or ', '.join(r.get('culture') or []),
                        r.get('creation_date'), r.get('type'), int(best.get('width') or 0) or None, int(best.get('height') or 0) or None))
    return out


def eu_licence(u):
    u = u or ''
    if 'publicdomain/zero' in u: return 'CC0'
    if 'publicdomain/mark' in u: return 'Public domain'
    m = re.search(r'licenses/(by|by-sa)/([\d.]+)', u)
    return f'CC {m.group(1).upper()} {m.group(2)}' if m else None


def europeana(q, n):
    p = {'wskey': 'api2demo', 'query': q, 'reusability': 'open', 'media': 'true', 'qf': 'TYPE:IMAGE', 'rows': n * 2, 'profile': 'rich'}
    out = []
    for r in js('https://api.europeana.eu/record/v2/search.json?' + urllib.parse.urlencode(p)).get('items', []):
        if len(out) >= n: break
        lic = eu_licence((r.get('rights') or [''])[0]); url = (r.get('edmIsShownBy') or [''])[0]
        if not lic or not url: continue
        cr = [c for c in r.get('dcCreator') or [] if not c.startswith('http')]
        out.append(item('europeana', (r.get('title') or [''])[0], (r.get('guid') or '').split('?')[0], url, lic,
                        ', '.join(cr[:2]) or ', '.join((r.get('dataProvider') or [])[:1]), (r.get('year') or [''])[0], ', '.join((r.get('dataProvider') or [])[:1])))
    return out


def loc(q, n):
    out = []
    for r in js('https://www.loc.gov/photos/?' + urllib.parse.urlencode({'q': q, 'fo': 'json', 'c': n * 2})).get('results', []):
        if len(out) >= n: break
        imgs = r.get('image_url') or []
        if not imgs or not r.get('url'): continue
        try: it = js(r['url'] + '?fo=json').get('item', {})
        except Exception: continue
        adv = ' '.join(it.get('rights_advisory') or []) if isinstance(it.get('rights_advisory'), list) else str(it.get('rights_advisory') or '')
        if 'no known restrictions' not in adv.lower(): continue
        m = re.search(r'#h=(\d+)&w=(\d+)', imgs[-1])
        out.append(item('loc', r.get('title'), r['url'], imgs[-1].split('#')[0], 'No known restrictions (Library of Congress)',
                        ', '.join((it.get('contributor_names') or [])[:1]), r.get('date'), '', int(m.group(2)) if m else None, int(m.group(1)) if m else None))
        time.sleep(0.3)
    return out


COMMONS = 'https://commons.wikimedia.org/w/api.php'
OK = re.compile(r'^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)', re.I)


def commons(q, n):
    if q.startswith('File:'):   # one exact file; standard thumbnail sizes only (https://w.wiki/GHai)
        p = {'action': 'query', 'format': 'json', 'titles': q, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': 3840}
    else:
        p = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q, 'gsrnamespace': 6, 'gsrlimit': n,
             'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': 1920}
    d = js(COMMONS + '?' + urllib.parse.urlencode(p))
    out = []
    for pg in sorted((d.get('query') or {}).get('pages', {}).values(), key=lambda x: x.get('index', 0)):
        ii = (pg.get('imageinfo') or [{}])[0]
        if ii.get('mime') not in ('image/jpeg', 'image/png', 'image/tiff'): continue
        md = ii.get('extmetadata') or {}
        lic = strip((md.get('LicenseShortName') or {}).get('value'))
        if not OK.search(lic): continue
        url = ii.get('thumburl') or ii.get('url')
        if 'unscaled' in url and (ii.get('width') or 0) > 1920:   # originals are rate-limited: take the standard 1920 px size
            u = ii['url'].split('?')[0]; url = u.replace('/commons/', '/commons/thumb/', 1) + '/1920px-' + u.rsplit('/', 1)[1]
        out.append(item('commons', pg['title'][5:], ii.get('descriptionurl'), url, lic,
                        (md.get('Artist') or {}).get('value'), (md.get('DateTimeOriginal') or {}).get('value'),
                        (md.get('ImageDescription') or {}).get('value'), ii.get('width'), ii.get('height')))
    return out


FIND = {'openverse': openverse, 'met': met, 'aic': aic, 'cleveland': cleveland, 'europeana': europeana, 'loc': loc, 'commons': commons}


def search(q):
    """Results of one query string, in the order to show them."""
    if q.startswith('File:'):
        return commons(q, 1)
    m = re.match(r'^(\w+):\s*(.+)$', q)
    if m and m.group(1).lower() in FIND:
        return FIND[m.group(1).lower()](m.group(2), 12)
    per, lists, errors = 8, [], []
    for s in SOURCES:   # one source down or slow must not stop the search
        try: lists.append(FIND[s](q, per))
        except Exception as e: print(f'  {s}: {str(e)[:100]}'); errors.append(f'{s}: {str(e)[:60]}')
    if not lists:       # every source failed: the query is recorded as failed, not as "nothing found"
        raise RuntimeError('; '.join(errors))
    mixed = []
    for i in range(per):
        mixed += [l[i] for l in lists if i < len(l)]
    return mixed


def outside(q):
    """A picture from any page, described by Claude (licence checked on its page)."""
    return item('page', q.get('title') or q['url'].rsplit('/', 1)[-1], q.get('page', ''), q['url'], q.get('license', '?'),
                q.get('artist', ''), q.get('date', ''), q.get('description', ''))


def sheet(files, path, labels=None):
    """Numbered contact sheet; each tile says its size, licence and source."""
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(size=16)
    except Exception:
        font = None
    tiles = []
    for i, f in enumerate(files, 1):
        im = Image.open(f).convert('RGB'); im.thumbnail((360, 350))
        t = Image.new('RGB', (380, 410), (20, 20, 24)); t.paste(im, ((380 - im.width) // 2, 8))
        for k, row in enumerate((labels or {}).get(f, f'#{i}').split('\n')):
            ImageDraw.Draw(t).text((10, 364 + k * 20), row, fill=(255, 210, 90), font=font)
        tiles.append(t)
    if not tiles:
        return
    cols = 4; rows = (len(tiles) + cols - 1) // cols
    s = Image.new('RGB', (cols * 380, rows * 410), (10, 10, 12))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * 380, (i // cols) * 410))
    s.save(path, quality=85)


def dhash(im, n=8):
    """64-bit difference hash: two scans of the same picture differ in a few bits only."""
    if hasattr(im, 'draft'): im.draft('L', (256, 256))
    g = im.convert('L'); g.thumbnail((256, 256)); g = g.resize((n + 1, n), Image.LANCZOS)
    px = list(g.tobytes())
    return sum(1 << i for i in range(n * n) if px[(i // n) * (n + 1) + i % n] > px[(i // n) * (n + 1) + i % n + 1])


def same(a, b):
    return bin(a ^ b).count('1') <= 10


def seen_hashes():
    """Pictures of earlier search rounds of the same video (FIND_SEEN = dirs separated by ':') are not shown again."""
    hs = []
    for d in filter(None, os.environ.get('FIND_SEEN', '').split(':')):
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if re.match(r'^\d+-\d+\.jpg$', f):
                try: hs.append(dhash(Image.open(os.path.join(d, f))))
                except Exception: pass
    return hs


def main():
    out, queries = sys.argv[1], sys.argv[2:]
    if queries[:1] == ['--spec']:
        queries = json.load(open(queries[1], encoding='utf-8'))
    os.makedirs(out, exist_ok=True)
    index, kept_hashes, dropped = [], seen_hashes(), {'small': 0, 'duplicate': 0}
    for k, q in enumerate(queries, 1):
        exact = isinstance(q, dict) or q.startswith('File:')
        err = None
        try:
            found = [outside(q)] if isinstance(q, dict) else search(q)
        except Exception as e:
            err = str(e)[:200]; print(f'{k}. {q}: lỗi {err[:120]}'); found = []
        if isinstance(q, dict): q = q.get('title') or q['url']
        kept = []   # [(result, image, hash)] in search order; a duplicate inside this query keeps the bigger file
        for r in found:
            if len(kept) >= KEEP:
                break
            if not exact and r.get('width') and r.get('height') and min(r['width'], r['height']) < MIN_SIDE:
                dropped['small'] += 1; continue
            try:
                im = Image.open(io.BytesIO(get(r['thumb']))).convert('RGB')
            except Exception as e:
                r['error'] = str(e)[:120]; continue
            finally:
                time.sleep(0.5)
            if not exact and min(im.size) < MIN_SIDE:
                dropped['small'] += 1; continue
            r['width'], r['height'] = max(r.get('width') or 0, im.width), max(r.get('height') or 0, im.height)
            h = dhash(im)
            if not exact and any(same(h, x) for x in kept_hashes):   # an exact file asked for is always kept
                dropped['duplicate'] += 1; continue
            twin = next((i for i, (_, _, kh) in enumerate(kept) if same(h, kh)), None)
            if twin is not None:
                dropped['duplicate'] += 1
                if im.width * im.height > kept[twin][1].width * kept[twin][1].height:
                    kept[twin] = (r, im, h)
                continue
            kept.append((r, im, h))
        files, labels, results = [], {}, []
        for n, (r, im, h) in enumerate(kept, 1):
            im.thumbnail((4000, 4000))   # enough for crops of a detail; keeps the renders branch small
            p = f'{out}/{k}-{n}.jpg'; im.save(p, quality=90)
            r['file'] = p[len(out) + 1:]; files.append(p); results.append(r)
            lic = re.sub(r'(?i)public domain', 'PD', r['license']).split(' (')[0]
            labels[p] = f"#{n}  {im.width}x{im.height}  {lic}"[:40] + f"\n{r['source']}  {r['date']}"[:42]
        kept_hashes += [h for _, _, h in kept]
        sheet(files, f'{out}/sheet_{k}.jpg', labels)
        index.append({'k': k, 'query': q, 'results': results, **({'error': err} if err else {})})
        print(f'{k}. {q}: {len(results)} kept ({", ".join(sorted({r["source"] for r in results}))})')
    json.dump(index, open(f'{out}/index.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if index and all(e.get('error') for e in index):
        raise SystemExit('tìm ảnh: mọi từ khóa đều lỗi (mạng hoặc các kho ảnh không trả lời)')
    print(f"dropped: {dropped['small']} too small, {dropped['duplicate']} duplicates")


if __name__ == '__main__':
    main()
