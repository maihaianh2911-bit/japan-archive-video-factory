#!/usr/bin/env python3
"""Minimal client for the 11labs.id.vn external API (stdlib only).

Commands:
  balance                         -> print quota info
  voices [--language Japanese]    -> write voices markdown list
  tts --text-file F --out DIR [--voice ID] [--speed 1.0]
       voice ids starting with "clone_" are sent to /clone.php, others to /tts.php

Safety rules (from the provider docs):
  * the key is read from the VN11_API_KEY env var only, never printed;
  * a create request is sent at most once; after that we only poll;
  * 401/403 stop immediately (bad key / no quota); 429/500/502/503/504 on polling are retried;
  * GET requests (balance, status, downloads) are retried on network errors, unreadable answers and busy-server
    answers (429, 500, 502, 503, 504); the POST that creates a job is never retried after a timeout or a 5xx (it
    may have been received and billed), only after a 429 (the server refused it, nothing was created);
  * the balance shown around a tts job is information only: when it cannot be read, the job goes on;
  * results are downloaded right away (MP3 kept only ~6 h on the provider side).
"""
import argparse, http.client, json, os, sys, time, uuid, urllib.request, urllib.error

BASE = os.environ.get('VN11_API_BASE', 'https://11labs.id.vn/api/external/v1')
KEY = os.environ.get('VN11_API_KEY', '')
UA = 'japan-archive-video-factory/0.1'


def die(msg, code=1):
    print(f'::error::{msg}')
    sys.exit(code)


NET = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)   # HTTPError is caught first
BUSY = (429, 500, 502, 503, 504)   # rate limit or a busy server / gateway: worth another try


def req(method, path, data=None, headers=None, raw=False, timeout=60, tries=None):
    tries = tries or (4 if method == 'GET' else 3)   # a POST is only sent again after a 429, see below
    h = {'x-api-key': KEY, 'User-Agent': UA}
    h.update(headers or {})
    for i in range(tries):
        r = urllib.request.Request(BASE.rstrip('/') + '/' + path.lstrip('/'), data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                body = resp.read()
                return resp.status, (body if raw else json.loads(body.decode('utf-8') or '{}'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')
            try:
                j = json.loads(body)
            except Exception:
                j = {'error': body[:300]}
            if i < tries - 1 and (e.code in BUSY if method == 'GET' else e.code == 429):
                print(f'::warning::11labs {method} {path.split("?")[0]}: HTTP {e.code}, thử lại', flush=True)
                time.sleep(10 * (i + 1)); continue
            return e.code, j
        except (*NET, ValueError) as e:   # ValueError: JSONDecodeError, UnicodeDecodeError
            if i == tries - 1 or method != 'GET':   # a POST that timed out may have been received: never sent twice
                raise
            print(f'::warning::11labs {method} {path.split("?")[0]}: {type(e).__name__}, thử lại', flush=True)
            time.sleep(5 * (i + 1))


def multipart(fields):
    b = uuid.uuid4().hex
    out = b''
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n'.encode() + str(v).encode('utf-8') + b'\r\n'
    out += f'--{b}--\r\n'.encode()
    return out, {'Content-Type': f'multipart/form-data; boundary={b}'}


def check_create(code, j):
    if code == 401: die('11labs: API key sai hoặc hết hạn (401). Kiểm tra secret VN11_API_KEY.')
    if code == 403: die('11labs: hết hạn mức (403). Cần nạp thêm ký tự.')
    if code >= 400: die(f'11labs: lỗi khi tạo job ({code}): {j.get("error", j)}')
    if not j.get('job_id'): die(f'11labs: không nhận được job_id: {j}')


def download(url, dest, tries=4):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(r, timeout=120) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            if e.code not in BUSY or i == tries - 1: raise
            time.sleep(5 * (i + 1))
        except NET:
            if i == tries - 1: raise
            print('::warning::11labs: tải file lỗi mạng, thử lại', flush=True)
            time.sleep(5 * (i + 1))
    with open(dest, 'wb') as f:
        f.write(body)
    return os.path.getsize(dest)


def cmd_balance(_):
    code, j = req('GET', 'user.php')
    if code != 200: die(f'11labs balance lỗi ({code}): {j.get("error", j)}')
    info = {k: j.get(k) for k in ('quota_total', 'quota_used', 'remaining_quota', 'expires_at')}
    print(json.dumps(info, ensure_ascii=False))
    return info


def balance_info():
    """The balance around a tts job, for the log only: {} when it cannot be read (the paid job must not stop for it)."""
    try:
        code, j = req('GET', 'user.php')
        if code == 200:
            info = {k: j.get(k) for k in ('quota_total', 'quota_used', 'remaining_quota', 'expires_at')}
            print(json.dumps(info, ensure_ascii=False))
            return info
        print(f'::warning::11labs: không đọc được số dư ({code}), vẫn làm tiếp', flush=True)
    except Exception as e:
        print(f'::warning::11labs: không đọc được số dư ({type(e).__name__}), vẫn làm tiếp', flush=True)
    return {}


def cmd_voices(a):
    rows, page = [], 1
    while True:
        q = f'voices.php?page={page}&page_size=200'
        if a.language: q += f'&language={urllib.parse.quote(a.language)}'
        code, j = req('GET', q)
        if code != 200: die(f'11labs voices lỗi ({code}): {j.get("error", j)}')
        rows += j.get('voices', [])
        if not j.get('has_more'): break
        page += 1
        if page > 20: break
    code, jc = req('GET', 'voices.php?provider=clone&page_size=200')
    clones = jc.get('voices', []) if code == 200 else []
    lines = ['## Giọng clone của bạn', '', '| Tên | voice_id |', '|---|---|']
    lines += [f"| {v.get('name')} | `{v.get('voice_id')}` |" for v in clones] or ['| (không có) | |']
    lines += ['', f'## Giọng {a.language or "tất cả"} ({len(rows)})', '', '| Tên | Nhà cung cấp | voice_id | Nghe thử |', '|---|---|---|---|']
    for v in rows[:300]:
        lines.append(f"| {v.get('name')} | {v.get('provider')} | `{v.get('voice_id')}` | {('[nghe](' + v['preview_url'] + ')') if v.get('preview_url') else ''} |")
    md = '\n'.join(lines)
    open(a.out, 'w').write(md)
    print(f'{len(clones)} clone voices, {len(rows)} voices')


def cmd_tts(a):
    text = open(a.text_file, encoding='utf-8').read().strip()
    if not text: die('Văn bản rỗng')
    os.makedirs(a.out, exist_ok=True)
    before = balance_info()
    voice = a.voice or os.environ.get('VN11_VOICE_ID') or ''
    if voice.startswith('clone_'):
        body, h = multipart({'text': text, 'clone_voice_id': voice})
        code, j = req('POST', 'clone.php', data=body, headers=h, timeout=120)
    else:
        payload = {'text': text, 'voice_settings': {'language': 'Japanese', 'speed': a.speed, 'normalization': False, 'expressive_optimize': False}}
        if voice: payload['voice_id'] = voice
        code, j = req('POST', 'tts.php', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, timeout=120)
    check_create(code, j)
    job = j['job_id']
    json.dump({'job_id': job, 'voice': voice, 'create_response': j}, open(os.path.join(a.out, 'job.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'job {job} created (voice={voice or "default"})')
    t0 = time.time(); st = {}
    while time.time() - t0 < a.timeout:
        time.sleep(4)
        code, st = req('GET', f'status.php?job_id={urllib.parse.quote(job)}')
        if code in BUSY: time.sleep(10); continue
        if code != 200: die(f'11labs status lỗi ({code}): {st.get("error", st)}')
        s = st.get('status')
        if s == 'completed': break
        if s == 'failed': die(f'11labs job {job} failed: {st}')
    else:
        die(f'11labs job {job} chưa xong sau {a.timeout}s (job vẫn được lưu, có thể lấy tiếp).')
    n = download(st['download_url'], os.path.join(a.out, 'voice.mp3'))
    if st.get('srt_url'):
        try: download(st['srt_url'], os.path.join(a.out, 'voice.srt'))
        except Exception as e: print(f'::warning::không tải được SRT: {e}')
    after = balance_info()
    known = before.get('remaining_quota') is not None and after.get('remaining_quota') is not None
    used = before['remaining_quota'] - after['remaining_quota'] if known else None
    usage = {'job_id': job, 'voice': voice, 'chars_in_text': len(text), 'quota_used_this_job': used, 'remaining_quota': after.get('remaining_quota'), 'mp3_bytes': n}
    json.dump(usage, open(os.path.join(a.out, 'usage.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(usage, ensure_ascii=False))


if __name__ == '__main__':
    import urllib.parse
    if not KEY: die('Thiếu secret VN11_API_KEY')
    p = argparse.ArgumentParser(); sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('balance')
    v = sp.add_parser('voices'); v.add_argument('--language', default='Japanese'); v.add_argument('--out', default='voices.md')
    t = sp.add_parser('tts'); t.add_argument('--text-file', required=True); t.add_argument('--out', required=True)
    t.add_argument('--voice', default=''); t.add_argument('--speed', type=float, default=1.0); t.add_argument('--timeout', type=int, default=900)
    a = p.parse_args()
    {'balance': cmd_balance, 'voices': cmd_voices, 'tts': cmd_tts}[a.cmd](a)
