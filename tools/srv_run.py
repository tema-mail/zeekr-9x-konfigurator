#!/usr/bin/env python3
"""Работает НА СЕРВЕРЕ: выполнить Playwright-функцию в общем браузере (служба vps-browser, localhost:8931) и записать результат в файл.
python3 srv_run.py <код.js> <результат.json>     – в файле {"ok": true, "result": …} или {"ok": false, "error": …}"""
import json, sys, urllib.request, urllib.error
URL = 'http://localhost:8931/mcp'; st = {'sid': None, 'proto': None, 'n': 0}
def post(msg, timeout=1500):
    h = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if st['sid']: h['Mcp-Session-Id'] = st['sid']
    if st['proto']: h['MCP-Protocol-Version'] = st['proto']
    r = urllib.request.urlopen(urllib.request.Request(URL, data=json.dumps(msg).encode(), headers=h, method='POST'), timeout=timeout)
    if r.headers.get('Mcp-Session-Id'): st['sid'] = r.headers['Mcp-Session-Id']
    if r.status == 202: return None
    body = r.read().decode('utf-8')
    if 'text/event-stream' in r.headers.get('Content-Type', ''):
        out = None
        for chunk in body.split('\n\n'):
            data = '\n'.join(l[5:].lstrip() for l in chunk.split('\n') if l.startswith('data:'))
            if data:
                try:
                    m = json.loads(data)
                    if 'id' in m and ('result' in m or 'error' in m): out = m
                except ValueError: pass
        return out
    return json.loads(body)
def call(method, params):
    st['n'] += 1
    return post({'jsonrpc': '2.0', 'id': st['n'], 'method': method, 'params': params})
res = {'ok': False}
try:
    r = call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'konfigurator', 'version': '1'}})
    st['proto'] = r['result'].get('protocolVersion')
    post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    r = call('tools/call', {'name': 'browser_run_code_unsafe', 'arguments': {'code': open(sys.argv[1]).read()}})
    if 'error' in r: res['error'] = r['error']
    else:
        t = '\n'.join(c.get('text', '') for c in r['result'].get('content', []) if c.get('type') == 'text')
        i = t.find('### Result')
        if i != -1:
            body = t[i + 10:].split('\n### ')[0].strip()
            try: res = {'ok': True, 'result': json.loads(body)}
            except ValueError: res = {'ok': True, 'result': body}
        else: res = {'ok': not r['result'].get('isError'), 'result': t[:20000]}
except Exception as e:
    res['error'] = repr(e)[:500]
finally:
    try: call('tools/call', {'name': 'browser_close', 'arguments': {}})
    except Exception: pass
    try: urllib.request.urlopen(urllib.request.Request(URL, headers={'Mcp-Session-Id': st['sid'] or ''}, method='DELETE'), timeout=10)
    except Exception: pass
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False)
