#!/usr/bin/env python3
"""Find free-to-use pictures for a video, with their licence, from open archives (no API keys needed).

Usage: find_images.py <out_dir> "<query 1>" "<query 2>" ...      or      find_images.py <out_dir> --spec <file.json>

Sources (the owner, 12/11: free pictures, Wikipedia/Wikimedia is not needed):
  openverse  Openverse: Flickr, museums, science sites … (CC0, public domain, CC BY, CC BY-SA; Wikimedia excluded)
  met        The Metropolitan Museum of Art, open access (CC0)
  aic        Art Institute of Chicago (public domain works)
  cleveland  Cleveland Museum of Art, open access (CC0)
  europeana  Europeana: European libraries, archives, museums (CC0, public domain, CC BY, CC BY-SA)
A query without prefix searches these five and mixes the results; `met: Gilgamesh` searches one.
Only when asked for with their prefix:
  loc        Library of Congress, photos and prints (loc.gov/photos/ only, not its maps collection; "No known
             restrictions on publication" only). One more request per picture, and it refuses the GitHub runners
             when asked a lot (16/11/2026, issue 4: two queries, 25 minutes, no picture): aim it at what it holds.
  commons    Wikimedia Commons, full-text search
  wiki       every picture ABOUT one thing (a site, an object, a person, a building, a print), found through its
             Wikidata item: its own pictures, the pictures of its Wikipedia articles (Japanese and English), the
             files of its Wikimedia Commons category (and sub-categories), the photos taken at its coordinates.
             `wiki: 亀ヶ岡石器時代遺跡`, `wiki: Hachikō` or `wiki: Q1049738`.
  geo        Commons photos taken around a point, whatever they are called: `geo: 40.8833,140.3389 800` (metres)
Write queries in English (or the language of the archive). `File:<name>` fetches one exact Commons file.
With --spec, the JSON list may also hold
  {"q": "<query>", "want": "<what the picture must show, in English>", "keep": 12}   a query with its own wish
  {"url": "<direct image url>", "page": "<page that states the licence>", "title": "...", "artist": "...",
   "license": "CC BY 4.0", "date": "..."}   a picture from any page Claude checked (journal figures under CC BY, a
   museum page …): its own group with one picture.

Ranking (17/11/2026). A free-text query asks each archive for 20 pictures, not 8 (a prefixed one for 30, not 12;
Openverse gives 20 at most, the Library of Congress is asked for 12 as before),
looks at a small version of every one and keeps the 8 that fit the words best: CLIP (open_clip ViT-B/32, MIT;
weights from its GitHub release) scores picture against text ("want", else the query), and the archive's own order
counts a little too. The score is "match" in index.json and on the contact sheet (about 0.30 and more: it shows the
thing; under 0.22: it does not). Without torch/open_clip installed, or with FIND_RANK=0, the first 8 are kept as
before; so are the results of a query in another script (Japanese …) without a "want": CLIP reads English. `wiki:`
and `geo:` results keep their order (they are about the thing by construction) unless the query has a "want".

For every query: up to 8 pictures (24 for wiki, 12 for geo, or "keep"), only licences that allow use in a monetised
video, no files under 400 px, no duplicate scans of the same picture (also across earlier rounds listed in
FIND_SEEN). Commons pictures are taken in the standard sizes (https://w.wiki/GHai). Downloads run a few at a time
and give up on a dead host after two short tries. Writes <out_dir>/<k>-<n>.jpg (up to 4000 px),
<out_dir>/index.json (query, source, page, licence, author, date, size, match; for wiki the item found) and
<out_dir>/sheet_<k>.jpg (contact sheet with numbers and source) so Claude can choose. A query whose search fails
(every source down, a timeout …) is logged and kept with no results and an "error" in index.json; only when every
query fails does the script exit with an error. An archive that answers 429 (too many requests) is not asked again
in the same run: its later queries get an "error" at once (repeat them in the next round). Stdlib + Pillow
(+ torch and open_clip_torch for the ranking).
"""
import http.client, io, json, os, re, shutil, sys, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

UA = 'JapanArchiveVideoFactory/0.1 (https://github.com/maihaianh2911-bit/japan-archive-video-factory; licence-checked picture search)'
SOURCES = ('openverse', 'met', 'aic', 'cleveland', 'europeana')   # a query without prefix (owner, 12/11: no Wikimedia by default)
MIN_SIDE = 400   # shorter side in pixels: smaller files only look blurred in the video
KEEP, KEEP_WIKI, KEEP_GEO = 8, 24, 12   # pictures kept per query: free text, wiki:, geo:
DEEP = 20        # pictures asked from each archive when the results are ranked (else 8)
MATCH_MIN = 0.18 # a query with a "want": pictures that fit it less are dropped (about 0.30: shows it; 0.15: something else)
STD = (960, 1280, 1920, 3840)   # Commons serves these widths freely; other sizes and originals are rate-limited
LANGS = ('ja', 'en')            # the Wikipedias read by wiki:, the channel's language first
NET = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)   # network errors worth a retry
WIKIMEDIA = threading.BoundedSemaphore(2)   # Wikimedia asks for few requests at a time, whatever runs in parallel here


def get(url, tries=4, raw=True, timeout=60):
    """GET with retries: 429/5xx (rate limits, busy servers) and network errors (timeout, reset, cut-off reply)."""
    gentle = urllib.parse.urlsplit(url).netloc.endswith('wikimedia.org')
    for i in range(tries):
        try:
            if gentle: WIKIMEDIA.acquire()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout) as r:
                    b = r.read()
            finally:
                if gentle: time.sleep(0.05); WIKIMEDIA.release()
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(8 * (i + 1)); continue
            raise
        except NET:
            if i < tries - 1:
                time.sleep(5 * (i + 1)); continue
            raise


def js(url, tries=4):
    return get(url, tries=tries, raw=False)


def strip(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


def item(source, title, page, url, license, artist='', date='', description='', width=None, height=None, preview=None):
    """One result. thumb: the picture to keep; preview: a small version of it (for the ranking, and the fallback
    when the big one cannot be had)."""
    return {'source': source, 'title': strip(str(title or ''))[:160], 'page': page, 'thumb': url, 'license': license,
            'artist': strip(str(artist or ''))[:160], 'date': strip(str(date or ''))[:60], 'description': strip(str(description or ''))[:300],
            'width': width, 'height': height, 'preview': preview or url}


REFUSED = set()   # sources that answered 429 (too many requests) in this run: not asked again, see ask()


def refused(source, e):
    """True when the error is an archive's 429 (after the retries of get): the archive is then left alone for the
    rest of the run. Every refused request costs ~50 s of retries; on 16/11/2026 one Library of Congress query,
    refused picture by picture, took 19 minutes."""
    if not (isinstance(e, urllib.error.HTTPError) and e.code == 429):
        return False
    if source not in REFUSED:
        REFUSED.add(source); print(f'  {source}: bỏ qua nguồn này đến hết lượt chạy (429)')
    return True


# ---- sources: each returns up to n results, newest API shapes checked 12/11/2026
def openverse(q, n):
    n = min(n, 20)   # "page_size may not exceed 20 for anonymous requests" (401, seen 17/11/2026 with 30)
    p = {'q': q, 'page_size': n, 'license': 'by,by-sa,cc0,pdm', 'excluded_source': 'wikimedia', 'mature': 'false'}
    out = []
    for r in js('https://api.openverse.org/v1/images/?' + urllib.parse.urlencode(p)).get('results', []):
        lic = {'cc0': 'CC0', 'pdm': 'Public domain'}.get(r['license'], f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip())
        out.append(item(f"openverse/{r.get('source')}", r.get('title') or r['url'].rsplit('/', 1)[-1], r.get('foreign_landing_url'), r['url'], lic,
                        r.get('creator'), '', '', r.get('width'), r.get('height'), r.get('thumbnail')))
    return out


def met(q, n):
    ids = js('https://collectionapi.metmuseum.org/public/collection/v1.1/search?' + urllib.parse.urlencode({'q': q, 'hasImages': 'true', 'limit': 40})).get('objectIDs') or []
    out = []
    for i in ids[:30]:
        if len(out) >= n: break
        try: o = js(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}')
        except Exception as e:
            if refused('met', e): break   # keep what was found, stop asking
            continue
        if o.get('isPublicDomain') and o.get('primaryImage'):
            out.append(item('met', o.get('title'), o.get('objectURL'), o['primaryImage'], 'CC0 (The Met Open Access)',
                            o.get('artistDisplayName') or o.get('culture'), o.get('objectDate'), ', '.join(filter(None, [o.get('culture'), o.get('medium')])),
                            preview=o.get('primaryImageSmall')))
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
                            r.get('artist_display'), r.get('date_display'), '', th.get('width'), th.get('height'),
                            f"https://www.artic.edu/iiif/2/{r['image_id']}/full/400,/0/default.jpg"))
    return out


def cleveland(q, n):
    p = {'q': q, 'has_image': 1, 'cc0': 1, 'limit': n}
    out = []
    for r in js('https://openaccess-api.clevelandart.org/api/artworks/?' + urllib.parse.urlencode(p)).get('data', []):
        im = (r.get('images') or {}); best = im.get('print') or im.get('web') or {}
        if not best.get('url'): continue
        cr = ', '.join(c.get('description', '') for c in r.get('creators') or [])
        out.append(item('cleveland', r.get('title'), r.get('url'), best['url'], 'CC0 (Cleveland Museum of Art)', cr or ', '.join(r.get('culture') or []),
                        r.get('creation_date'), r.get('type'), int(best.get('width') or 0) or None, int(best.get('height') or 0) or None,
                        (im.get('web') or {}).get('url')))
    return out


def eu_licence(u):
    u = u or ''
    if 'publicdomain/zero' in u: return 'CC0'
    if 'publicdomain/mark' in u: return 'Public domain'
    m = re.search(r'licenses/(by|by-sa)/([\d.]+)', u)
    return f'CC {m.group(1).upper()} {m.group(2)}' if m else None


def europeana(q, n):
    p = {'wskey': 'api2demo', 'query': q, 'reusability': 'open', 'media': 'true', 'qf': 'TYPE:IMAGE', 'rows': min(100, n * 2), 'profile': 'rich'}
    out = []
    for r in js('https://api.europeana.eu/record/v2/search.json?' + urllib.parse.urlencode(p)).get('items', []):
        if len(out) >= n: break
        lic = eu_licence((r.get('rights') or [''])[0]); url = (r.get('edmIsShownBy') or [''])[0]
        if not lic or not url: continue
        cr = [c for c in r.get('dcCreator') or [] if not c.startswith('http')]
        out.append(item('europeana', (r.get('title') or [''])[0], (r.get('guid') or '').split('?')[0], url, lic,
                        ', '.join(cr[:2]) or ', '.join((r.get('dataProvider') or [])[:1]), (r.get('year') or [''])[0], ', '.join((r.get('dataProvider') or [])[:1]),
                        preview=(r.get('edmPreview') or [None])[0]))
    return out


def loc(q, n):
    n = min(n, 12)   # one more request per picture: never more than before the ranking
    out = []
    for r in js('https://www.loc.gov/photos/?' + urllib.parse.urlencode({'q': q, 'fo': 'json', 'c': n * 2})).get('results', []):
        if len(out) >= n: break
        imgs = r.get('image_url') or []
        if not imgs or not r.get('url'): continue
        try: it = js(r['url'] + '?fo=json').get('item', {})
        except Exception as e:
            if refused('loc', e): break   # keep what was found, stop asking
            continue
        adv = ' '.join(it.get('rights_advisory') or []) if isinstance(it.get('rights_advisory'), list) else str(it.get('rights_advisory') or '')
        if 'no known restrictions' not in adv.lower(): continue
        m = re.search(r'#h=(\d+)&w=(\d+)', imgs[-1])
        out.append(item('loc', r.get('title'), r['url'], imgs[-1].split('#')[0], 'No known restrictions (Library of Congress)',
                        ', '.join((it.get('contributor_names') or [])[:1]), r.get('date'), '', int(m.group(2)) if m else None, int(m.group(1)) if m else None,
                        imgs[min(1, len(imgs) - 1)].split('#')[0]))
        time.sleep(0.3)
    return out


COMMONS = 'https://commons.wikimedia.org/w/api.php'
WIKIDATA = 'https://www.wikidata.org/w/api.php'
OK = re.compile(r'^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)', re.I)
SMALL = 330   # the small version looked at for the ranking (a standard Commons width)
INFO = {'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': SMALL}
# page furniture of Wikipedia articles and maps that show no place: never a picture of the thing
# the last part of a Commons thumbnail address: "330px-Name.jpg", for a TIFF scan "lossy-page1-330px-Name.tif.jpg"
THUMB = re.compile(r'/((?:lossy-|lossless-)?(?:page\d+-)?)\d+px-([^/]+)$')
ICON = re.compile(r'(?i)(commons-logo|wik\w*[- ]logo|qsicon|oojs|red pog|loca\w+ map|\bicon\b|flag of|disambig|padlock|'
                  r'question book|ambox|edit-ltr|symbol \w+ vote|speaker|nuvola|crystal clear|\.svg$)')


def commons_items(pages, source='commons', exact=False, order=None):
    """Results from the pages of a Commons answer asked with INFO (a small version of every file). The picture kept
    is the largest standard size up to 1920 px (3840 for an exact file); a file under 960 px is taken whole."""
    pages = list(pages)
    if order:   # a list of titles: the API answers in its own order
        pos = {t.replace('_', ' '): i for i, t in enumerate(order)}
        pages.sort(key=lambda pg: pos.get(pg.get('title', ''), 1e9))
    else:
        pages.sort(key=lambda pg: pg.get('index', 0))
    out = []
    for pg in pages:
        ii = (pg.get('imageinfo') or [{}])[0]
        if ii.get('mime') not in ('image/jpeg', 'image/png', 'image/tiff'): continue
        md = ii.get('extmetadata') or {}
        lic = strip((md.get('LicenseShortName') or {}).get('value'))
        if not OK.search(lic): continue
        small = (ii.get('thumburl') or ii.get('url') or '').split('?')[0]
        w = ii.get('width') or 0
        m = THUMB.search(small)
        if m:   # a real thumbnail: the same file in another standard width
            top = [x for x in STD if x <= w and x <= (3840 if exact else 1920)]
            url = f'{small[:m.start()]}/{m.group(1)}{top[-1]}px-{m.group(2)}' if top else ii['url'].split('?')[0]
        else:
            url = small
        out.append(item(source, pg['title'][5:], ii.get('descriptionurl'), url, lic,
                        (md.get('Artist') or {}).get('value'), (md.get('DateTimeOriginal') or {}).get('value'),
                        (md.get('ImageDescription') or {}).get('value'), ii.get('width'), ii.get('height'), small))
    return out


def wiki_api(host=COMMONS, tries=4, **p):
    return js(host + '?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', **p}), tries=tries)


def commons(q, n):
    if q.startswith('File:'):   # one exact file
        d = wiki_api(titles=q, **INFO)
        return commons_items((d.get('query') or {}).get('pages', {}).values(), exact=True)
    d = wiki_api(generator='search', gsrsearch=q, gsrnamespace=6, gsrlimit=min(50, n), **INFO)
    return commons_items((d.get('query') or {}).get('pages', {}).values())


def commons_files(titles, source):
    """Results for a list of Commons file titles, in that order (files that are not on Commons, e.g. a non-free
    picture kept on one Wikipedia only, simply do not come back)."""
    out = []
    for i in range(0, len(titles), 50):
        d = wiki_api(titles='|'.join(titles[i:i + 50]), **INFO)
        out += commons_items((d.get('query') or {}).get('pages', {}).values(), source, order=titles[i:i + 50])
    return out


def geo(q, n):
    """Commons photos taken around a point: "<lat>,<lon> [<radius in metres>]" (default 500 m, 10 km at most)."""
    m = re.match(r'^\s*(-?\d+(?:\.\d+)?)\s*[,; ]\s*(-?\d+(?:\.\d+)?)(?:\s+(\d+))?\s*m?\s*$', q)
    if not m: raise ValueError(f'geo: expects "<lat>,<lon> [<metres>]", got "{q}"')
    rad = min(10000, max(10, int(m.group(3) or 500)))
    d = wiki_api(generator='geosearch', ggscoord=f'{m.group(1)}|{m.group(2)}', ggsradius=rad, ggsnamespace=6,
                 ggslimit=min(100, n * 2), **INFO)
    out, series = [], set()
    for r in commons_items((d.get('query') or {}).get('pages', {}).values(), 'commons/geo'):
        key = re.sub(r'\d+', '#', r['title'])   # survey tiles and photo series differ in their numbers only: one of each
        if key in series: continue
        series.add(key); out.append(r)
    return out


WIKI_FOUND = {}   # query -> the Wikidata item it was read as (for index.json: Claude checks it is the right thing)
# pictures an item names itself: image, panoramic view, aerial view, image of design plans, of grave, of interior, nighttime view
OWN = ('P18', 'P4291', 'P8592', 'P3311', 'P1442', 'P5775', 'P3451')


def wiki(q, n):
    """Every picture about one thing, through its Wikidata item (see the module text). Most to the point first: the
    item's own pictures, the pictures of its Wikipedia articles, its Commons category, then photos taken there."""
    q = q.strip()
    qid = q if re.fullmatch(r'Q\d+', q) else None
    for lang in LANGS:   # the exact title of a Wikipedia article first: "亀ヶ岡石器時代遺跡", "Hachikō"
        if qid: break
        try:
            d = wiki_api(f'https://{lang}.wikipedia.org/w/api.php', tries=2, titles=q, prop='pageprops', redirects=1)
        except Exception:
            continue
        for pg in (d.get('query') or {}).get('pages', {}).values():
            pp = pg.get('pageprops') or {}
            if pp.get('wikibase_item') and 'disambiguation' not in pp: qid = pp['wikibase_item']
    for lang in LANGS:   # else the item called so
        if qid: break
        hits = js(WIKIDATA + '?' + urllib.parse.urlencode({'action': 'wbsearchentities', 'search': q, 'language': lang, 'uselang': lang,
                                                           'type': 'item', 'limit': 3, 'format': 'json'})).get('search', [])
        if hits: qid = hits[0]['id']
    if not qid:
        raise RuntimeError(f'wiki: no Wikidata item named "{q}" (try the name of its Wikipedia article, or commons: {q})')
    e = js(WIKIDATA + '?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': qid, 'props': 'claims|sitelinks|labels|descriptions',
                                                    'languages': '|'.join(LANGS), 'format': 'json'}))['entities'][qid]
    claims, links = e.get('claims') or {}, e.get('sitelinks') or {}
    val = lambda p: [c['mainsnak']['datavalue']['value'] for c in claims.get(p, []) if c.get('mainsnak', {}).get('datavalue')]
    first = lambda d: next((d[l]['value'] for l in LANGS if l in d), '')
    coord = (val('P625') or [None])[0]
    WIKI_FOUND[q] = {'id': qid, 'label': first(e.get('labels') or {}), 'description': first(e.get('descriptions') or {}),
                     **({'coord': [round(coord['latitude'], 5), round(coord['longitude'], 5)]} if coord else {})}
    own = ['File:' + v for p in OWN for v in val(p) if isinstance(v, str)]
    article = []
    for site in (l + 'wiki' for l in LANGS):
        if site not in links: continue
        try:
            d = wiki_api(f'https://{site[:-4]}.wikipedia.org/w/api.php', tries=2, titles=links[site]['title'], prop='images', imlimit=500, redirects=1)
        except Exception as ex:
            print(f'  wiki: {site} {str(ex)[:80]}'); continue
        for pg in (d.get('query') or {}).get('pages', {}).values():
            article += ['File:' + i['title'].split(':', 1)[1] for i in pg.get('images', [])]   # "ファイル:…" on the Japanese one
    cat = (val('P373') or [links.get('commonswiki', {}).get('title', '')[9:] if links.get('commonswiki', {}).get('title', '').startswith('Category:') else ''])[0]
    members = lambda c, t, lim: [x['title'] for x in (wiki_api(list='categorymembers', cmtitle='Category:' + c, cmtype=t, cmlimit=lim).get('query') or {}).get('categorymembers', [])]
    filed = []
    if cat:
        filed = members(cat, 'file', 100)
        for sub in members(cat, 'subcat', 12):
            if len(filed) >= 150: break
            filed += members(sub[9:], 'file', 50)
    groups = [(own, 'commons/wiki'), (article, 'commons/wiki'), (filed, 'commons/category')]
    seen, out = set(), []
    for titles, source in groups:
        titles = [t for t in dict.fromkeys(titles) if t.replace('_', ' ') not in seen and not ICON.search(t)]
        seen.update(t.replace('_', ' ') for t in titles)
        out += commons_files(titles[:150], source)
    if coord:   # the place itself, whatever the photos are called
        try: out += [r for r in geo(f"{coord['latitude']},{coord['longitude']} 400", 20) if 'File:' + r['title'] not in seen]
        except Exception as ex: print(f'  wiki: geo {str(ex)[:80]}')
    return out[:max(n, 60)]


FIND = {'openverse': openverse, 'met': met, 'aic': aic, 'cleveland': cleveland, 'europeana': europeana, 'loc': loc, 'commons': commons,
        'wiki': wiki, 'geo': geo}
ABOUT = ('wiki', 'geo')   # sources whose results are about the thing by construction: kept in their order


class Clip:
    """Scores how well a picture fits a text (open_clip ViT-B/32, weights from its GitHub release, on the CPU)."""
    URL = 'https://github.com/mlfoundations/open_clip/releases/download/v0.2-weights/vit_b_32-quickgelu-laion400m_e32-46683a32.pt'
    # what a documentary for a general audience must not show by accident (Flickr has everything): pictures that look
    # like one of these are dropped from ranked results. Ordinary pictures stay under 0.18, but this channel's museum
    # pieces do not: of the 658 pictures its searches kept up to 17/11/2026, nine scored 0.21–0.23 (Jomon clay
    # figurines, a kappa netsuke, actor prints), none more. So the line is 0.24 here, not 0.21.
    UNFIT = ('a nude person', 'a woman in lingerie or underwear', 'an erotic photo')
    UNFIT_MIN = 0.24
    model = None; failed = False; unfit = None

    @classmethod
    def ready(cls):
        if cls.model is None and not cls.failed:
            try:
                if os.environ.get('FIND_RANK', '1') == '0': raise RuntimeError('FIND_RANK=0')
                import torch, open_clip
                path = os.environ.get('CLIP_MODEL') or os.path.expanduser('~/.cache/find-images/vit_b_32-quickgelu-laion400m_e32.pt')
                if not os.path.exists(path):
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with urllib.request.urlopen(urllib.request.Request(cls.URL, headers={'User-Agent': UA}), timeout=60) as r, open(path + '.part', 'wb') as f:
                        shutil.copyfileobj(r, f)   # 600 MB; a stalled download ends after 60 s without data
                    os.replace(path + '.part', path)
                model, _, pre = open_clip.create_model_and_transforms('ViT-B-32-quickgelu', pretrained=path)
                cls.model, cls.pre, cls.tok, cls.torch = model.eval(), pre, open_clip.get_tokenizer('ViT-B-32-quickgelu'), torch
            except Exception as e:
                cls.failed = True; print(f'ranking off, the first pictures of every archive are kept ({str(e)[:90]})')
        return cls.model is not None

    @classmethod
    def scores(cls, images, text):
        """For every picture: how well it fits the text, and how much it looks like something not to show."""
        t = cls.torch
        with t.no_grad():
            fi = t.cat([cls.model.encode_image(t.stack([cls.pre(im) for im in images[i:i + 32]])) for i in range(0, len(images), 32)])
            fi /= fi.norm(dim=-1, keepdim=True)
            ft = cls.model.encode_text(cls.tok([text, 'a photo of ' + text])); ft /= ft.norm(dim=-1, keepdim=True)
            if cls.unfit is None:
                cls.unfit = cls.model.encode_text(cls.tok(list(cls.UNFIT))); cls.unfit /= cls.unfit.norm(dim=-1, keepdim=True)
            return (fi @ ft.T).max(dim=1).values.tolist(), (fi @ cls.unfit.T).max(dim=1).values.tolist()


def picture(url, tries=2, timeout=20):   # a dead host costs 45 s at most, not minutes
    return Image.open(io.BytesIO(get(url, tries=tries, timeout=timeout))).convert('RGB')


def ranked(found, text):
    """The results ordered by how well their small version fits the text (CLIP), the archive's own order counting
    a little (0.004 per place: it decides between pictures CLIP finds alike, as for a name it does not know).
    Results whose small version cannot be loaded go last; pictures that look unsuitable (Clip.UNFIT) are left out.
    Sets r['match']. Returns (results, number left out)."""
    def small(r):
        try:
            im = picture(r['preview'], tries=1, timeout=15); im.thumbnail((448, 448)); return im   # one try: a slow host only loses its place
        except Exception:
            return None
    with ThreadPoolExecutor(6) as ex:
        ims = list(ex.map(small, found))
    ok = [(r, im) for r, im in zip(found, ims) if im is not None]
    if not ok: return found, 0
    fit, unfit = Clip.scores([im for _, im in ok], text)
    for (r, _), sc in zip(ok, fit):
        r['match'] = round(sc, 3)
    out = [r for (r, _), u in zip(ok, unfit) if u >= Clip.UNFIT_MIN]
    best = sorted((r for r, _ in ok if r not in out), key=lambda r: -(r['match'] - 0.004 * r.get('rank', 0)))
    return best + [r for r, im in zip(found, ims) if im is None], len(out)


def source_of(q):
    """(source name or None, the words) of a query string: "wiki: X" -> ("wiki", "X")."""
    m = re.match(r'^(\w+):\s*(.+)$', q)
    return (m.group(1).lower(), m.group(2)) if m and m.group(1).lower() in FIND else (None, q)


def ask(s, words, n):
    """Up to n results of one archive. An archive that answered 429 earlier in this run is not asked again."""
    if s in REFUSED:
        raise RuntimeError('not asked again: this archive answered 429 (too many requests) earlier in this run')
    try:
        return FIND[s](words, n)
    except Exception as e:
        refused(s, e); raise


def search(q, deep=False):
    """Results of one query string, in the order to show them. deep: ask for more than are kept (they are ranked)."""
    if q.startswith('File:'):
        return commons(q, 1)
    src, words = source_of(q)
    if src:
        found = ask(src, words, 60 if src in ABOUT else 30 if deep else 12)
        for i, r in enumerate(found): r['rank'] = i
        return found
    per, lists, errors = DEEP if deep else 8, [], []
    for s in SOURCES:   # one source down or slow must not stop the search
        try: lists.append(ask(s, q, per))
        except Exception as e: print(f'  {s}: {str(e)[:100]}'); errors.append(f'{s}: {str(e)[:60]}')
    if not lists:       # every source failed: the query is recorded as failed, not as "nothing found"
        raise RuntimeError('; '.join(errors))
    mixed = []
    for i in range(per):
        for l in lists:
            if i < len(l): l[i]['rank'] = i; mixed.append(l[i])
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
    index, kept_hashes = [], seen_hashes()
    dropped = {'small': 0, 'duplicate': 0, 'unfit': 0, 'unsuitable': 0, 'failed': 0}
    for k, q in enumerate(queries, 1):
        want = keep = None
        if isinstance(q, dict) and q.get('q'):   # a query with its own wish
            want, keep, q = q.get('want'), q.get('keep'), q['q']
        exact = isinstance(q, dict) or q.startswith('File:')
        src, words = (None, '') if exact else source_of(q)
        keep = int(keep or (KEEP_WIKI if src == 'wiki' else KEEP_GEO if src == 'geo' else KEEP))
        # ranked against "want", else against the query's own words when CLIP can read them (it reads English and
        # other Latin-script words; a query in Japanese keeps the archive's order)
        readable = bool(want) or not re.search(r'[^\x00-ɏ -⁯]', words)
        rank = not exact and (bool(want) or src not in ABOUT) and readable and Clip.ready()
        err, n_found = None, 0
        try:
            found = [outside(q)] if isinstance(q, dict) else search(q, deep=rank)
        except Exception as e:
            err = str(e)[:200]; print(f'{k}. {q}: lỗi {err[:120]}'); found = []
        if isinstance(q, dict): q = q.get('title') or q.get('url') or '?'
        if not exact:
            small = [r for r in found if r.get('width') and r.get('height') and min(r['width'], r['height']) < MIN_SIDE]
            dropped['small'] += len(small); found = [r for r in found if r not in small]
        n_found = len(found)
        if rank and len(found) > 1:
            found, n_out = ranked(found, want or words); dropped['unsuitable'] += n_out
            if want:   # asked for by a description: what does not show it is no use (CLIP under 0.18: something else)
                poor = [r for r in found if r.get('match', 1) < MATCH_MIN]
                dropped['unfit'] += len(poor); found = [r for r in found if r not in poor]

        def full(r):   # the picture to keep; when it cannot be had (a rate limit, a dead host), its small version
            try: return picture(r['thumb'])
            except Exception as e:
                r['error'] = str(e)[:120]
                if r.get('preview') and r['preview'] != r['thumb']:
                    try: return picture(r['preview'], timeout=20)
                    except Exception: pass
                return None
        kept = []   # [(result, image, hash)] in search order; a duplicate inside this query keeps the bigger file
        for i in range(0, len(found), 6):
            if len(kept) >= keep:
                break
            batch = found[i:i + 6]
            with ThreadPoolExecutor(3) as ex:   # a few at a time: the archives ask for it
                ims = list(ex.map(full, batch))
            for r, im in zip(batch, ims):
                if len(kept) >= keep:
                    break
                if im is None:
                    dropped['failed'] += 1; continue
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
            r['file'] = p[len(out) + 1:]; files.append(p)
            results.append({key: v for key, v in r.items() if key not in ('preview', 'rank', 'error')})
            lic = re.sub(r'(?i)public domain', 'PD', r['license']).split(' (')[0]
            fit = f"  ~{r['match']:.2f}" if 'match' in r else ''   # "~": the sheet's font has no "≈"
            labels[p] = f"#{n}  {im.width}x{im.height}  {lic}"[:40] + f"\n{r['source']}  {r['date']}"[:42 - len(fit)] + fit
        kept_hashes += [h for _, _, h in kept]
        sheet(files, f'{out}/sheet_{k}.jpg', labels)
        about = WIKI_FOUND.get(words.strip()) if src == 'wiki' else None
        index.append({'k': k, 'query': q, 'results': results, 'candidates': n_found, **({'want': want} if want else {}),
                      **({'wikidata': about} if about else {}), **({'error': err} if err else {})})
        print(f'{k}. {q}: {len(results)} kept of {n_found} ({", ".join(sorted({r["source"] for r in results}))})'
              + (f' = {about["id"]} {about["label"]}: {about["description"]}' if about else ''))
    json.dump(index, open(f'{out}/index.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if index and all(e.get('error') for e in index):
        raise SystemExit('tìm ảnh: mọi từ khóa đều lỗi (mạng hoặc các kho ảnh không trả lời)')
    print(f"dropped: {dropped['small']} too small, {dropped['duplicate']} duplicates, {dropped['unfit']} not showing what was asked, "
          f"{dropped['unsuitable']} unsuitable, {dropped['failed']} could not be downloaded")


if __name__ == '__main__':
    main()
