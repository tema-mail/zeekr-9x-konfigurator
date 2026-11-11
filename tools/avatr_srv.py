#!/usr/bin/env python3
"""Работает НА СЕРВЕРЕ (Амстердам): снять дерево конфигуратора Avatr и адреса кадров каждой сборки.
python3 avatr_srv.py <productCarId> <out.json>.  Пишет ход в <out.json>.log; результат – одним файлом в конце."""
import json, sys, time, itertools, urllib.request
PID, OUT = sys.argv[1], sys.argv[2]
URL = 'https://www.avatr.com/api-gateway/hermes/v4/car-config/config-detail/no-login/app'
H = {'content-type': 'application/json', 'language': 'zh', 'login-token': '', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'}
EXT_EXTRA = ('rearview_mirror', 'sports_package', 'ex_upgrade_kit')      # необязательные опции, которые видно снаружи
calls = 0
def log(*a):
    open(OUT + '.log', 'a').write(' '.join(str(x) for x in a) + '\n')
def post(body):
    global calls
    for a in range(4):
        try:
            calls += 1
            r = urllib.request.urlopen(urllib.request.Request(URL, data=json.dumps(body, ensure_ascii=False).encode(), headers=H, method='POST'), timeout=40)
            j = json.loads(r.read().decode())
            if j.get('code') == 0: return j['result']
            err = j.get('message')
        except Exception as e: err = repr(e)[:120]
        time.sleep(1.5 + a * 2)
    raise RuntimeError(err)
def types(res): return [c for g in res['respGroupList'] for sg in g['respSubGroupList'] for c in sg['respCarConfigList']]
def selected(res):
    return {c['carConfigTypeCode']: next(x for x in c['respCarConfigDetailList'] if x.get('selected')) for c in types(res) if any(x.get('selected') for x in c['respCarConfigDetailList'])}
def detail(res=None, change=None, group=164):
    if res is None: return post({"salesType": 0, "imageDeviceType": 1, "carConfigDeviceType": 1, "changeCarConfigType": "ORDER_CHANGE", "selectedList": [], "productId": PID, "skipRights": False})
    sel = selected(res); lst = []
    for c in types(res):
        t = c['carConfigTypeCode']
        d = next(x for x in c['respCarConfigDetailList'] if x['carConfigCode'] == change[1]) if (change and t == change[0]) else sel.get(t)
        if d: lst.append({"carConfigTypeCode": t, "carConfigCode": d['carConfigCode'], "price": d.get('price') or 0})
    ed = change[1] if (change and change[0] == 'sys_car_version') else sel['sys_car_version']['carConfigCode']
    return post({"salesType": 0, "imageDeviceType": 1, "carConfigDeviceType": 1, "changeCarConfigType": "ORDER_CHANGE", "selectedList": lst, "productId": PID, "skipRights": False,
                 "groupId": group, "changedCarConfigTypeCode": change[0] if change else None, "editionCode": ed})
def imgs(res): return [i['imageUrl'] for i in sorted(res['carConfigImageList'], key=lambda i: i['angle'])]
def avail(c): return [d for d in c['respCarConfigDetailList'] if not d.get('disabled') and not d.get('hidden')]
def slim(c):
    return {'code': c['carConfigTypeCode'], 'name': c['carConfigTypeName'], 'required': bool(c.get('required')),
            'opts': [{'code': d['carConfigCode'], 'name': d['carConfigName'], 'pic': d.get('picUrl'), 'selected': bool(d.get('selected')), 'standard': bool(d.get('standard')), 'desc': d.get('desc')} for d in avail(c)]}

out = {'pid': PID, 'versions': []}
base = detail()
T = {c['carConfigTypeCode']: c for c in types(base)}
for e in T['sys_car_energy']['respCarConfigDetailList']:
    if e.get('disabled') or e.get('hidden'): continue
    re_ = base if e.get('selected') else detail(base, ('sys_car_energy', e['carConfigCode']))
    if selected(re_)['sys_car_energy']['carConfigCode'] != e['carConfigCode']: continue
    Te = {c['carConfigTypeCode']: c for c in types(re_)}
    for v in avail(Te['sys_car_version']):
        rv = re_ if v.get('selected') else detail(re_, ('sys_car_version', v['carConfigCode']))
        if selected(rv)['sys_car_version']['carConfigCode'] != v['carConfigCode']: continue
        Tv = {c['carConfigTypeCode']: c for c in types(rv)}
        ver = {'energy': e['carConfigCode'], 'energyName': e['carConfigName'], 'code': v['carConfigCode'], 'name': v['carConfigName'], 'desc': v.get('desc'),
               'types': [slim(c) for t, c in Tv.items() if t not in ('sys_car_energy', 'sys_car_version')], 'ext': {}, 'int': {}}
        colors = [d['carConfigCode'] for d in avail(Tv['sys_car_body_color'])]
        wheels = [d['carConfigCode'] for d in avail(Tv['sys_car_S6690'])]
        inters = [d['carConfigCode'] for d in avail(Tv['sys_car_S7010'])]
        mats = [d['carConfigCode'] for d in avail(Tv['sys_car_material'])] if 'sys_car_material' in Tv else [None]
        extras = [(t, avail(c)[0]['carConfigCode']) for t, c in Tv.items() if any(k in t for k in EXT_EXTRA) and avail(c) and not avail(c)[0].get('standard')]
        ver['extDims'] = ['sys_car_body_color', 'sys_car_S6690', 'sys_car_S7010'] + [t for t, _ in extras]
        ver['intDims'] = ['sys_car_S7010'] + (['sys_car_material'] if mats != [None] else [])
        def step(res, t, code):
            if selected(res).get(t, {}).get('carConfigCode') == code: return res
            r = detail(res, (t, code))
            return r if selected(r).get(t, {}).get('carConfigCode') == code else None
        for col in colors:
            rc = step(rv, 'sys_car_body_color', col)
            if not rc: continue
            for wh in wheels:
                rw = step(rc, 'sys_car_S6690', wh)
                if not rw: continue
                for it in inters:
                    ri = step(rw, 'sys_car_S7010', it)
                    if not ri: continue
                    for mask in itertools.product([0, 1], repeat=len(extras)):
                        rx = ri; ok = True
                        for on, (t, code) in zip(mask, extras):
                            if on:
                                rx = step(rx, t, code)
                                if not rx: ok = False; break
                        if not ok: continue
                        key = '_'.join([col, wh, it] + [code if on else '0' for on, (t, code) in zip(mask, extras)])
                        ver['ext'][key] = imgs(rx)
            log(v['carConfigName'], col, 'сборок', len(ver['ext']), 'запросов', calls)
        # салон: кадры группы 166 по отделке (и материалу), цвет кузова по умолчанию
        for it in inters:
            ri = step(rv, 'sys_car_S7010', it)
            if not ri: continue
            for m in mats:
                rm = step(ri, 'sys_car_material', m) if m else ri
                if not rm: continue
                x = detail(rm, ('sys_car_S7010', it), group=166)
                ver['int']['_'.join([it] + ([m] if m else []))] = imgs(x)
        out['versions'].append(ver)
        log('== версия готова', e['carConfigName'], v['carConfigName'], 'кузов', len(ver['ext']), 'салон', len(ver['int']))
json.dump(out, open(OUT, 'w'), ensure_ascii=False)
log('ГОТОВО запросов', calls)
