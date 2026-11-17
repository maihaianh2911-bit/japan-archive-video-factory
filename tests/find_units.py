#!/usr/bin/env python3
"""Unit tests of the picture search (scripts/find_images.py) on made-up archives and pictures: no network, no
ranking model (FIND_RANK=0; the choice "rank or not" is tested with a stand-in for CLIP). Run from the repo root:
python3 tests/find_units.py   (tests/arc_smoke.py runs it too)"""
import io, json, os, random, sys, tempfile, urllib.error
os.environ['FIND_RANK'] = '0'   # never load the 600 MB model in a test
os.environ.pop('FIND_SEEN', None)
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import find_images as F

real_find, real_js, real_sleep, real_open, real_picture, real_ranked, real_ready, real_commons = (
    dict(F.FIND), F.js, F.time.sleep, F.urllib.request.urlopen, F.picture, F.ranked, F.Clip.ready, F.commons)
F.time.sleep = lambda s: slept.append(s)   # no test waits
slept = []
def http(code, url='https://archive.example/'): return urllib.error.HTTPError(url, code, 'x', {}, None)

# ---- the owner's decision of 12/11 ("tìm ảnh tự do, k cần ảnh wiki"): a query without prefix asks no Wikimedia
# source; the Library of Congress (25 minutes for nothing on issue 4) is asked only by name
assert not set(F.SOURCES) & {'commons', 'wiki', 'geo', 'loc'}, F.SOURCES
assert set(F.SOURCES) == {'openverse', 'met', 'aic', 'cleveland', 'europeana'} and set(F.SOURCES) < set(F.FIND)
assert 'japan-archive-video-factory' in F.UA
# every prefix is in the runbook, with the rule that Wikimedia is asked only when nothing else has the document
doc = open(os.path.join(ROOT, 'AGENT_ARC.md'), encoding='utf-8').read()
for s in F.FIND: assert f'`{s}:' in doc, f'AGENT_ARC.md does not name the prefix {s}:'
assert '"want"' in doc and 'only when nothing else has the document' in doc

# ---- GET keeps its retries: network errors wait 5, 10, 15 s, a busy server 8, 16, 24 s; a 404 is not tried again;
# a picture download (two tries) gives up after one wait
def flaky(errors, body=b'{"ok": 1}'):
    left = list(errors)
    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def urlopen(req, timeout=None):
        calls.append((req.full_url, timeout, req.get_header('User-agent')))
        if left: raise left.pop(0)
        return R(body)
    return urlopen
try:
    calls = []; slept.clear(); F.urllib.request.urlopen = flaky([urllib.error.URLError('reset'), TimeoutError()])
    assert F.js('https://archive.example/a') == {'ok': 1} and slept == [5, 10] and calls[0][1:] == (60, F.UA), (slept, calls)
    calls = []; slept.clear(); F.urllib.request.urlopen = flaky([http(503), http(429), http(500)])
    assert F.get('https://archive.example/a') == b'{"ok": 1}' and slept == [8, 16, 24], slept
    calls = []; slept.clear(); F.urllib.request.urlopen = flaky([http(404)])
    try: F.get('https://archive.example/a'); raise AssertionError('a 404 must be raised')
    except urllib.error.HTTPError as e: assert e.code == 404 and slept == [] and len(calls) == 1
    calls = []; slept.clear(); F.urllib.request.urlopen = flaky([TimeoutError(), TimeoutError()])
    try: F.picture('https://dead.example/p.jpg'); raise AssertionError('a dead host must be given up')
    except TimeoutError: assert slept == [5] and [c[1] for c in calls] == [20, 20], (slept, calls)   # 45 s at most
finally:
    F.urllib.request.urlopen = real_open

# ---- an archive that answers 429 is asked once per run, not per query
asked = []
def refuses(q, n): asked.append(q); raise http(429)
try:
    F.FIND.update({s: (lambda q, n: []) for s in F.SOURCES}); F.FIND['openverse'] = refuses; F.REFUSED.clear()
    assert F.search('first') == [] and F.search('second') == [] and asked == ['first'] and F.REFUSED == {'openverse'}, asked
    # … also when it is asked by its prefix: the query is recorded as failed at once (Claude repeats it next round)
    try: F.search('openverse: third'); raise AssertionError('a refused archive must not be asked again')
    except RuntimeError as e: assert '429' in str(e) and asked == ['first']
    F.REFUSED.clear(); F.FIND['loc'] = refuses
    for q in ('loc: one', 'loc: two'):
        try: F.search(q); raise AssertionError('a failed search must be an error')
        except (urllib.error.HTTPError, RuntimeError): pass
    assert asked == ['first', 'one'] and F.REFUSED == {'loc'}, asked
    # every archive failing is an error of the query, not "nothing found"
    F.REFUSED.clear(); F.FIND.update({s: refuses for s in F.SOURCES})
    try: F.search('fourth'); raise AssertionError('search with every archive down must fail')
    except RuntimeError: pass
    try: F.search('fifth'); raise AssertionError('search with every archive refused must fail')
    except RuntimeError: pass
    # a failure that is not a refusal (a timeout, a server error) does not close the archive
    F.REFUSED.clear(); F.FIND.update({s: (lambda q, n: []) for s in F.SOURCES})
    def broken(q, n): raise http(503)
    F.FIND['met'] = broken
    assert F.search('sixth') == [] and F.REFUSED == set()
    # results of several archives are mixed one from each in turn, and know their place in their archive (the ranking uses it)
    F.FIND.update({s: (lambda q, n, s=s: [{'source': s, 'i': i} for i in range(2)]) for s in F.SOURCES})
    mixed = F.search('seventh')
    assert [(r['source'], r['rank']) for r in mixed] == [(s, i) for i in range(2) for s in F.SOURCES], mixed
    # how many are asked for: 8 from each archive (20 when ranked), 12 by prefix (30 when ranked), 60 for wiki: / geo:
    want_n = []
    F.FIND.update({s: (lambda q, n, s=s: want_n.append((s, n)) or []) for s in F.FIND})
    F.search('x'); F.search('x', deep=True); F.search('met: x'); F.search('met: x', deep=True); F.search('wiki: x'); F.search('geo: 1,2')
    assert want_n == [(s, 8) for s in F.SOURCES] + [(s, 20) for s in F.SOURCES] + [('met', 12), ('met', 30), ('wiki', 60), ('geo', 60)], want_n
finally:
    F.FIND.clear(); F.FIND.update(real_find); F.REFUSED.clear()
# a prefix asks one source; wiki: and geo: are sources too; other words with a colon are plain words
assert F.source_of('wiki: 亀ヶ岡石器時代遺跡') == ('wiki', '亀ヶ岡石器時代遺跡') and F.source_of('geo: 40.88,140.34 800')[0] == 'geo'
assert F.source_of('MET: Jomon') == ('met', 'Jomon') and F.source_of('loc: Commodore Perry')[0] == 'loc'
assert F.source_of('Edo: fire of 1657') == (None, 'Edo: fire of 1657') and F.source_of('dogu figurine') == (None, 'dogu figurine')

# ---- archives that cost one more request per picture (The Met, Library of Congress): a picture whose request fails
# is skipped, but a refusal (429) keeps what was found and stops asking — not 48 s of retries for every picture
def met_js(url, tries=4):
    asked.append(url)
    if '/search?' in url: return {'objectIDs': list(range(1, 11))}
    i = int(url.rsplit('/', 1)[1])
    if i == 2: raise http(404, url)
    if i == 4: raise http(429, url)
    return {'isPublicDomain': True, 'primaryImage': f'https://images.example/{i}.jpg', 'primaryImageSmall': f'https://images.example/{i}-small.jpg',
            'title': f'Object {i}', 'objectURL': f'https://www.metmuseum.org/art/collection/search/{i}', 'objectDate': 'ca. 1000 BCE', 'culture': 'Japan'}
def loc_js(url, tries=4):
    asked.append(url)
    if '/photos/?' in url:
        return {'results': [{'title': f'Print {i}', 'url': f'https://www.loc.gov/item/{i}/', 'date': '1853',
                             'image_url': [f'https://tile.example/{i}_150px.jpg#h=150&w=120', f'https://tile.example/{i}r.jpg#h=640&w=512',
                                           f'https://tile.example/{i}v.jpg#h=1024&w=820']} for i in range(1, 7)]}
    i = int(url.rstrip('/?fo=json').rsplit('/', 1)[1])
    if i == 3: raise http(429, url)
    return {'item': {'rights_advisory': ['No known restrictions on publication.'] if i != 2 else 'Rights status not evaluated', 'contributor_names': ['Heine, Wilhelm']}}
try:
    asked = []; F.js = met_js; F.REFUSED.clear()
    res = F.met('Jomon', 20)
    assert [r['title'] for r in res] == ['Object 1', 'Object 3'] and len(asked) == 5 and F.REFUSED == {'met'}, (res, asked)
    assert res[0]['thumb'].endswith('/1.jpg') and res[0]['preview'].endswith('/1-small.jpg') and res[0]['license'].startswith('CC0')
    asked = []; F.js = loc_js; F.REFUSED.clear()
    res = F.loc('Commodore Perry', 30)
    assert [r['title'] for r in res] == ['Print 1'] and len(asked) == 4 and F.REFUSED == {'loc'}, (res, asked)
    assert 'c=24' in asked[0], asked[0]   # never more than 12 pictures (24 looked at), also when the results are ranked
    assert res[0]['thumb'] == 'https://tile.example/1v.jpg' and res[0]['preview'] == 'https://tile.example/1r.jpg' and (res[0]['width'], res[0]['height']) == (820, 1024)
finally:
    F.js = real_js; F.REFUSED.clear()

# ---- Openverse refuses more than 20 a page without a key (401): never asked for more, also when the results are ranked
try:
    asked = []; F.js = lambda url, tries=4: asked.append(url) or {'results': [{'license': 'by', 'license_version': '2.0', 'url': 'https://live.example/1.jpg',
              'source': 'flickr', 'title': 'Dogu', 'foreign_landing_url': 'https://flickr.example/1', 'creator': 'A', 'width': 1024, 'height': 683, 'thumbnail': 'https://api.example/1/thumb/'}]}
    res = F.openverse('dogu', 30)
    assert 'page_size=20' in asked[0] and 'excluded_source=wikimedia' in asked[0] and res[0]['license'] == 'CC BY 2.0' and res[0]['preview'].endswith('/thumb/'), (asked, res)
    F.openverse('dogu', 8); assert 'page_size=8' in asked[1], asked
finally:
    F.js = real_js
assert F.Clip.UNFIT_MIN >= 0.24   # this channel's clay figurines and netsuke score up to 0.23 against "a nude person"

# ---- Commons pictures are taken in the standard sizes: the largest up to 1920 px (3840 for an exact file); a file
# under 960 px is taken whole; its 330 px version is the preview; a TIFF scan keeps its "lossy-page1-" thumbnail
# name; a licence that does not allow the video, and drawings (SVG), are left out
def _pg(title, w, h, lic='CC BY-SA 4.0', mime='image/jpeg', i=0, pre=''):
    name = title[5:].replace(' ', '_'); ext = '.jpg' if mime == 'image/tiff' else ''
    return {'title': title, 'index': i, 'imageinfo': [{'mime': mime, 'width': w, 'height': h, 'descriptionurl': 'https://commons.wikimedia.org/wiki/' + name,
            'url': f'https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}?utm=1',
            'thumburl': (f'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/{pre}330px-{name}{ext}?utm=2' if w > 330 else f'https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}?utm=1'),
            'extmetadata': {'LicenseShortName': {'value': lic}, 'Artist': {'value': '<a href="x">Someone</a>'}}}]}
res = F.commons_items([_pg('File:Big.jpg', 5100, 3000, i=1), _pg('File:Mid.jpg', 1400, 900, i=2), _pg('File:Small.jpg', 640, 480, i=3),
                       _pg('File:Tiny.jpg', 300, 300, i=4), _pg('File:Press.jpg', 3000, 2000, lic='All rights reserved', i=5),
                       _pg('File:Scan.tif', 6000, 4000, lic='Public domain', mime='image/tiff', i=6, pre='lossy-page1-'),
                       _pg('File:Locator map.svg', 2000, 2000, mime='image/svg+xml', i=7), _pg('File:330px-Old name.jpg', 2500, 2000, lic='PD-Japan', i=8)])
assert [r['title'] for r in res] == ['Big.jpg', 'Mid.jpg', 'Small.jpg', 'Tiny.jpg', 'Scan.tif', '330px-Old name.jpg'], res
assert res[0]['thumb'].endswith('/1920px-Big.jpg') and res[0]['preview'].endswith('/330px-Big.jpg') and res[0]['artist'] == 'Someone', res[0]
assert res[1]['thumb'].endswith('/1280px-Mid.jpg') and res[2]['thumb'].endswith('/ab/Small.jpg') and res[2]['preview'].endswith('/330px-Small.jpg'), res[1:3]
assert res[3]['thumb'] == res[3]['preview'] and '?' not in res[3]['thumb'], res[3]
assert res[4]['thumb'].endswith('/Scan.tif/lossy-page1-1920px-Scan.tif.jpg') and res[4]['preview'].endswith('/lossy-page1-330px-Scan.tif.jpg'), res[4]
assert res[5]['thumb'].endswith('/330px-Old_name.jpg/1920px-330px-Old_name.jpg'), res[5]
assert all(r['source'] == 'commons' and r['page'].startswith('https://commons.wikimedia.org/wiki/') for r in res)
assert F.commons_items([_pg('File:Big.jpg', 5100, 3000)], exact=True)[0]['thumb'].endswith('/3840px-Big.jpg')
# a list of titles comes back in the order asked, not in the API's
assert [r['title'] for r in F.commons_items([_pg('File:B.jpg', 2000, 2000), _pg('File:A.jpg', 2000, 2000)], order=['File:A.jpg', 'File:B.jpg'])] == ['A.jpg', 'B.jpg']
assert F.ICON.search('File:Commons-logo.svg') and F.ICON.search('File:Japan Aomori location map.jpg') and not F.ICON.search('File:Kamegaoka Site Dogu.jpg')
try: F.geo('Kamegaoka', 5); raise AssertionError('geo: without coordinates must be refused')
except ValueError: pass

# ---- wiki: the Wikidata item of a name → its own pictures, the pictures of its Japanese and English articles, its
# Commons category, photos taken at its coordinates; most to the point first, page furniture left out, each file once
def wiki_js(url, tries=4):
    from urllib.parse import urlsplit, parse_qs
    u = urlsplit(url); p = {k: v[0] for k, v in parse_qs(u.query).items()}; asked.append((u.netloc, p))
    if u.netloc == 'ja.wikipedia.org' and p.get('prop') == 'pageprops': return {'query': {'pages': {'-1': {'title': p['titles'], 'missing': ''}}}}
    if u.netloc == 'en.wikipedia.org' and p.get('prop') == 'pageprops': raise urllib.error.URLError('down')   # must be survived
    if p.get('action') == 'wbsearchentities': return {'search': [{'id': 'Q42'}] if p['language'] == 'ja' else []}
    if p.get('action') == 'wbgetentities':
        snak = lambda v: {'mainsnak': {'datavalue': {'value': v}}}
        return {'entities': {'Q42': {'labels': {'ja': {'value': '亀ヶ岡石器時代遺跡'}, 'en': {'value': 'Kamegaoka Site'}}, 'descriptions': {'en': {'value': 'Jomon site in Aomori'}},
                'claims': {'P18': [snak('Own.jpg')], 'P373': [snak('Kamegaoka Site')], 'P625': [snak({'latitude': 40.88333, 'longitude': 140.33889})]},
                'sitelinks': {'jawiki': {'title': '亀ヶ岡石器時代遺跡'}, 'enwiki': {'title': 'Kamegaoka Site'}}}}}
    if p.get('prop') == 'images':
        return {'query': {'pages': {'1': {'images': [{'title': 'ファイル:Own.jpg'}, {'title': 'ファイル:Article.jpg'}, {'title': 'ファイル:Commons-logo.svg'}]
                                          if u.netloc.startswith('ja.') else [{'title': 'File:English.jpg'}, {'title': 'File:Article.jpg'}]}}}}
    if p.get('list') == 'categorymembers':
        return {'query': {'categorymembers': ([{'title': 'File:Filed.jpg'}, {'title': 'File:Article.jpg'}] if p['cmtitle'] == 'Category:Kamegaoka Site' else [{'title': 'File:Sub.jpg'}])
                          if p['cmtype'] == 'file' else ([{'title': 'Category:Dogu from Kamegaoka'}] if p['cmtitle'] == 'Category:Kamegaoka Site' else [])}}
    if p.get('generator') == 'geosearch':
        return {'query': {'pages': {'1': _pg('File:Field 1.jpg', 2000, 1500, i=1), '2': _pg('File:Field 2.jpg', 2000, 1500, i=2), '3': _pg('File:Filed.jpg', 2000, 1500, i=3)}}}
    if 'titles' in p:   # the files themselves, answered in another order than asked
        return {'query': {'pages': {str(i): _pg(t, 2000, 1500) for i, t in enumerate(reversed(p['titles'].split('|')))}}}
    raise AssertionError(f'unexpected request {url}')
try:
    asked = []; F.js = wiki_js; F.WIKI_FOUND.clear()
    res = F.wiki(' 亀ヶ岡遺跡 ', 60)
    assert [(r['title'], r['source']) for r in res] == [('Own.jpg', 'commons/wiki'), ('Article.jpg', 'commons/wiki'), ('English.jpg', 'commons/wiki'),
            ('Filed.jpg', 'commons/category'), ('Sub.jpg', 'commons/category'), ('Field 1.jpg', 'commons/geo')], [(r['title'], r['source']) for r in res]
    assert F.WIKI_FOUND['亀ヶ岡遺跡'] == {'id': 'Q42', 'label': '亀ヶ岡石器時代遺跡', 'description': 'Jomon site in Aomori', 'coord': [40.88333, 140.33889]}, F.WIKI_FOUND
    assert [h for h, p in asked if p.get('prop') in ('pageprops', 'images')] == ['ja.wikipedia.org', 'en.wikipedia.org'] * 2   # Japanese first
    asked = []; assert F.wiki('Q42', 60) and not any(p.get('prop') == 'pageprops' or p.get('action') == 'wbsearchentities' for _, p in asked)   # an item id is taken as it is
finally:
    F.js = real_js

# ---- a whole search on made-up archives: what is kept, what index.json holds, when the results are ranked
def pic(seed, size=(800, 600)):
    rnd = random.Random(seed); g = Image.new('L', (9, 8)); g.putdata([rnd.randrange(256) for _ in range(72)])
    return g.resize(size, Image.NEAREST).convert('RGB')
def res_(src, i, w=800, h=600):
    return F.item(src, f'{src} {i}', f'https://{src}.example/page/{i}', f'https://{src}.example/full/{i}.jpg', 'CC0', 'Author', '1855', '', w, h, f'https://{src}.example/small/{i}.jpg')
def fake_picture(url, tries=2, timeout=20):   # every archive has its own pictures; its 5 is a bigger scan of its 3, its 7 is tiny
    loaded.append(url)
    src, i = url.split('/')[2].split('.')[0], int(url.rsplit('/', 1)[1].split('.')[0])
    if src == 'dead': raise TimeoutError('dead host')
    if '/small/' in url: return pic(f'{src}-{i}', (330, 250))
    return pic(f'{src}-{3 if i == 5 else i}', (1000, 760) if i == 5 else (300, 300) if i == 7 else (800, 600))
def run(spec, ranking=False):
    """find_images.main() on a spec; returns (index.json, the output folder, what each archive was asked for)."""
    out = tempfile.mkdtemp(prefix='find-units-'); sp = os.path.join(out, 'spec.json')
    json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False)
    calls.clear(); loaded.clear(); texts.clear(); F.REFUSED.clear()
    F.Clip.ready = classmethod(lambda cls: ranking)
    argv, sys.argv = sys.argv, ['find_images.py', os.path.join(out, 'img'), '--spec', sp]
    try: F.main()
    finally: sys.argv = argv
    return json.load(open(os.path.join(out, 'img', 'index.json'), encoding='utf-8')), os.path.join(out, 'img'), list(calls)
calls, loaded, texts = [], [], []
def archive(name, n_have=12):
    def f(q, n):
        calls.append((name, q, n))
        if q == 'down': raise urllib.error.URLError('no answer')
        return [res_(name, i) for i in range(1, min(n, n_have) + 1)]
    return f
def fake_ranked(found, text):   # stands for CLIP: the later a picture in its archive, the better it "fits"; the last one is unsuitable
    texts.append(text)
    for r in found: r['match'] = round(0.10 + 0.02 * r['rank'], 3)
    return sorted(found[:-1], key=lambda r: -r['match']), 1
try:
    F.picture, F.ranked = fake_picture, fake_ranked
    F.FIND.update({s: archive(s) for s in ('met', 'commons', 'wiki', 'geo', 'loc')}); F.FIND.update({s: archive(s, 0) for s in F.SOURCES if s != 'met'})
    # ranking off: an old plain query returns what it returned before — the first 8 of the archive in its order, minus
    # a file too small (7) and the smaller of two scans of one picture (3 and 5: the bigger one stays, in 3's place)
    idx, out, asked = run(['met: Jomon', 'Jomon vessel', {'url': 'https://journal.example/full/40.jpg', 'page': 'https://doi.example/1', 'title': 'Fig 1', 'artist': 'A. Author', 'license': 'CC BY 4.0'},
                           'met: down', {'q': 'commons: 鯰絵', 'want': 'a woodblock print of a giant catfish', 'keep': 3}])
    assert asked == [('met', 'Jomon', 12)] + [(s, 'Jomon vessel', 8) for s in F.SOURCES] + [('met', 'down', 12), ('commons', '鯰絵', 12)], asked
    assert [e['k'] for e in idx] == [1, 2, 3, 4, 5] and [e['query'] for e in idx] == ['met: Jomon', 'Jomon vessel', 'Fig 1', 'met: down', 'commons: 鯰絵']
    r1 = idx[0]['results']
    assert [r['title'] for r in r1] == [f'met {i}' for i in (1, 2, 5, 4, 6, 8, 9, 10)] and idx[0]['candidates'] == 12, [r['title'] for r in r1]
    assert set(r1[0]) == {'source', 'title', 'page', 'thumb', 'license', 'artist', 'date', 'description', 'width', 'height', 'file'}, set(r1[0])   # what build.py reads, and no more
    assert [r['file'] for r in r1] == [f'1-{n}.jpg' for n in range(1, 9)] and (r1[2]['width'], r1[2]['height']) == (1000, 760)
    assert all(os.path.exists(os.path.join(out, r['file'])) for e in idx for r in e['results']) and os.path.exists(os.path.join(out, 'sheet_1.jpg'))
    assert idx[1]['results'] == [] and 'error' not in idx[1]            # the same pictures again: nothing new, but not a failure
    assert idx[2]['results'][0]['source'] == 'page' and idx[2]['results'][0]['page'] == 'https://doi.example/1' and idx[2]['results'][0]['license'] == 'CC BY 4.0'
    assert idx[3]['results'] == [] and 'no answer' in idx[3]['error'] and not os.path.exists(os.path.join(out, 'sheet_4.jpg'))   # a failed query: Claude repeats it
    assert idx[4]['want'] == 'a woodblock print of a giant catfish' and [r['title'] for r in idx[4]['results']] == ['commons 1', 'commons 2', 'commons 3']
    assert texts == [] and not any('match' in r for e in idx for r in e['results'])   # "want" and "keep" are read; nothing is ranked without the model
    # a picture that cannot be downloaded falls back on its small version (dropped here: 330 px is too small to show)
    F.FIND['met'] = lambda q, n: [dict(res_('met', 21), thumb='https://dead.example/full/21.jpg'), res_('met', 22)]
    idx, out, _ = run(['met: fallback'])
    assert [r['title'] for r in idx[0]['results']] == ['met 22'] and 'https://met.example/small/21.jpg' in loaded, (idx, loaded)
    # ranking on (a stand-in for CLIP): more is asked for, the order is the ranking's, the score is in index.json
    F.FIND['met'] = archive('met', 40)
    F.commons = lambda q, n: calls.append(('File', q, n)) or [res_('commons', 7)]
    idx, out, asked = run(['met: Jomon vessel', 'commons: 鯰絵', {'q': 'loc: namazu-e 鯰絵', 'want': 'a woodblock print of a giant catfish', 'keep': 3},
                           'wiki: Namazu-e', {'q': 'geo: 35.9,140.6 500', 'want': 'a shrine gate'}, 'File:Namazu-e.jpg'], ranking=True)
    assert asked == [('met', 'Jomon vessel', 30), ('commons', '鯰絵', 12), ('loc', 'namazu-e 鯰絵', 30), ('wiki', 'Namazu-e', 60), ('geo', '35.9,140.6 500', 60),
                     ('File', 'File:Namazu-e.jpg', 1)], asked
    assert texts == ['Jomon vessel', 'a woodblock print of a giant catfish', 'a shrine gate'], texts   # English words, or the "want"; never Japanese words
    assert [r['title'] for r in idx[0]['results']] == [f'met {i}' for i in range(29, 21, -1)] and idx[0]['results'][0]['match'] == 0.66 and idx[0]['candidates'] == 30
    assert [r['title'] for r in idx[1]['results']] == [f'commons {i}' for i in (1, 2, 5, 4, 6, 8, 9, 10)] and 'match' not in idx[1]['results'][0]   # Japanese words: the archive's order
    assert [r['title'] for r in idx[2]['results']] == ['loc 11', 'loc 10', 'loc 9'] and idx[2]['candidates'] == 12 and idx[2]['results'][0]['match'] == 0.3
    assert len(idx[3]['results']) == 10 and [r['title'] for r in idx[3]['results']][:2] == ['wiki 1', 'wiki 2'] and 'match' not in idx[3]['results'][0]   # about the thing: its order
    assert [r['title'] for r in idx[4]['results']] == [f'geo {i}' for i in (11, 10, 9, 8, 6, 5)] and all(r['match'] >= F.MATCH_MIN for r in idx[4]['results']), idx[4]
    # (geo 12 was the unsuitable one, geo 1–4 do not show the "want" (under 0.18), geo 7 is too small)
    assert [r['title'] for r in idx[5]['results']] == ['commons 7'] and 'match' not in idx[5]['results'][0]   # an exact file: kept even tiny, never ranked
    F.FIND['wiki'] = archive('wiki', 40)
    idx, out, asked = run([{'q': 'wiki: Namazu-e', 'keep': 30}, 'wiki: Namazu-e'], ranking=True)
    assert len(idx[0]['results']) == 30 and [r['title'] for r in idx[1]['results']] == [f'wiki {i}' for i in range(33, 41)] and texts == []
    # (wiki: keeps 24, or "keep"; the same query again only shows what was not shown yet)
finally:
    F.FIND.clear(); F.FIND.update(real_find); F.REFUSED.clear()
    F.js, F.time.sleep, F.picture, F.ranked, F.Clip.ready, F.commons = real_js, real_sleep, real_picture, real_ranked, real_ready, real_commons
print('find_images unit tests OK')
