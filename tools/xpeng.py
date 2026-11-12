"""Xpeng (store.xiaopeng.com) -> конфигуратор на общем движке. Цен нет намеренно.
  python3 xpeng_snyat.py GX <папка проекта>                              -> raw/xpeng-raw.json
  python3 xpeng.py sobrat <папка проекта> "<Xpeng GX>" "<GX>" <slug>
Производитель даёт на каждую сборку два вида кузова без фона (спереди ¾ и сбоку), на каждую отделку – фото салона
и две круговые панорамы (с первого и со второго ряда); из панорам вырезается обычный вид вперёд."""
import json, os, re, sys, subprocess, hashlib, itertools, collections
from concurrent.futures import ThreadPoolExecutor

RU = {
 '峡湾灰': 'Серый «Фьорд»', '新月银': 'Серебристый «Новолуние»', '极地黑': 'Чёрный «Полярный»', '珠峰白': 'Белый «Эверест»', '昆仑云境': 'Двухцветный «Куньлунь»: серебристый с серым',
 '云漠金（哑光）': 'Золотистый «Пустыня», матовый', '丹霞红': 'Бордовый «Данься»',
 '21英寸月刃低风阻轮毂': '21″ «Лунный клинок», аэродинамические', '21英寸星驰轮毂': '21″ «Звёздный путь»', '22英寸日冕轮毂': '22″ «Солнечная корона»',
 '林雾紫': 'Фиолетовый «Лесной туман»', '拂晓白': 'Белый «Рассвет»', '铂金棕': 'Коричневый «Платина»',
 '二排娱乐套装': 'Пакет развлечений для второго ряда', '电动迎宾踏板': 'Выдвижные электропороги', '科技升级包': 'Пакет технологий',
}
ROLE = {1: ('paint', 'Цвет кузова'), 4: ('wheel', 'Диски'), 2: ('int', 'Цвет салона')}
EXTRA_TYPES = (3, 6)
GROUP_RU = {'超级增程': ('Гибрид', 'с бензиновым генератором'), '纯电': ('Электро', '')}
VER = [('旗舰版', 'Flagship'), ('四驱', '')]
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def ru(cn):
    if cn not in RU: raise SystemExit('нет перевода: ' + cn)
    return RU[cn]

def vname(cn):
    m = re.match(r'\s*(\d{3,4})\s*', cn); km = m.group(1) if m else ''; s = cn[m.end():] if m else cn
    for zh, en in VER: s = s.replace(zh, en)
    s = ' '.join(s.split())
    if re.search(r'[㐀-鿿]', s) or not s: raise SystemExit('нет перевода версии: ' + cn)
    return (s + ' ' + km).strip(), '四驱' in cn

def curl(url, dst):
    from PIL import Image
    if os.path.exists(dst) and os.path.getsize(dst) > 300: return True
    if not url: return False
    for a in range(6):
        r = subprocess.run(['curl', '-s', '--max-time', '180', '-A', UA, '-o', dst + '.part', '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout == '200' and os.path.getsize(dst + '.part') > 300:
            try: Image.open(dst + '.part').load()
            except Exception: continue
            os.replace(dst + '.part', dst); return True
    if os.path.exists(dst + '.part'): os.remove(dst + '.part')
    return False

def vid_vpered(src, size=(1600, 1000), fov=95, pitch=-12):
    """Обычный вид вперёд из круговой панорамы (равнопромежуточная развёртка 2:1)."""
    import numpy as np
    from PIL import Image
    im = Image.open(src).convert('RGB'); W, H = im.size; pan = np.asarray(im)
    w, h = size; f = (w / 2) / np.tan(np.radians(fov) / 2)
    x, y = np.meshgrid(np.arange(w) - w / 2 + 0.5, np.arange(h) - h / 2 + 0.5)
    d = np.stack([x, y, np.full_like(x, f)], -1); d /= np.linalg.norm(d, axis=-1, keepdims=True)
    p = np.radians(pitch); cy, sy = np.cos(p), np.sin(p)
    Y = d[..., 1] * cy - d[..., 2] * sy; Z = d[..., 1] * sy + d[..., 2] * cy; X = d[..., 0]
    lon = np.arctan2(X, Z); lat = np.arcsin(np.clip(Y, -1, 1))
    u = ((lon / (2 * np.pi) + 0.5) * W).astype(int) % W; v = np.clip(((lat / np.pi + 0.5) * H).astype(int), 0, H - 1)
    return Image.fromarray(pan[v, u])

def sobrat(proj, car, short, slug):
    from PIL import Image
    raw = json.load(open(f'{proj}/raw/xpeng-raw.json'))
    IMG = f'img/{slug}'; CACHE = f'{proj}/raw/cache'
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    cpath = lambda u: f'{CACHE}/{hashlib.md5(u.encode()).hexdigest()}.img'
    first = lambda lst: (lst or [{}])[0].get('url')
    order = [(g, y, v) for g in raw['vgroups'] for y in g['carYearsList'] for v in y['carVersionList'] if v['carVersionCode'] in raw['specs']]
    urls = set()
    for g, y, v in order:
        code = v['carVersionCode']
        for c in raw['cars'].get(code, []): urls |= {x['url'] for x in c['pcImgList']}
        for gr in raw['specs'][code]:
            for s in gr['specList']:
                urls |= {u for u in (first(s.get('iconList')), first(s.get('pcImgList')) if gr['carSpecificationGroupType'] == 2 else None,
                                     first(s.get('frontPanoramaList')), first(s.get('backPanoramaList'))) if u}
    urls = sorted(urls)
    with ThreadPoolExecutor(6) as ex: got = dict(zip(urls, ex.map(lambda u: curl(u, cpath(u)), urls)))
    print('картинок у производителя', len(urls), 'не скачалось', sum(not g for g in got.values()), flush=True)
    chash = {}
    def content(u):
        if u not in chash: chash[u] = hashlib.md5(open(cpath(u), 'rb').read()).hexdigest() if got.get(u) else None
        return chash[u]
    reg = {}
    def oid(letter, cn):
        if (letter, cn) not in reg: reg[(letter, cn)] = f'{letter}{len([k for k in reg if k[0] == letter]) + 1}'
        return reg[(letter, cn)]
    todo, options, vers, have, ints, groups, bad = {}, {}, [], {}, [], [], collections.defaultdict(set)
    multi = len(raw['vgroups']) > 1
    for vi, (g, y, v) in enumerate(order):
        code = v['carVersionCode']; pre = f'v{vi}-'; cars = raw['cars'].get(code, [])
        if not cars: continue
        sg = raw['specs'][code]; byg = {gr['carSpecificationGroupCode']: gr for gr in sg}
        choice = [gr for gr in sg if gr['carSpecificationGroupType'] in ROLE]
        extra = [s for gr in sg if gr['carSpecificationGroupType'] in EXTRA_TYPES for s in gr['specList']]
        rows = []
        for c in cars:
            have_codes = {s['specCode'] for s in c['specList']}
            sel = {gr['carSpecificationGroupCode']: next((s['specCode'] for s in c['specList'] if s['groupCode'] == gr['carSpecificationGroupCode']), None) for gr in choice}
            if None in sel.values(): continue
            rows.append((sel, {e['carSpecificationCode']: e['carSpecificationCode'] in have_codes for e in extra}, [x['url'] for x in c['pcImgList']]))
        included = [e for e in extra if all(r[1][e['carSpecificationCode']] for r in rows)]
        free = [e for e in extra if e not in included and any(r[1][e['carSpecificationCode']] for r in rows)]
        secs = []
        for gr in choice:
            role, title = ROLE[gr['carSpecificationGroupType']]; gc = gr['carSpecificationGroupCode']; ops = []
            for s in sorted(gr['specList'], key=lambda s: s.get('sort') or 0):
                if not any(r[0][gc] == s['carSpecificationCode'] for r in rows): continue
                pc = oid(role[0], s['carSpecificationName']); iu = first(s.get('iconList'))
                icon = f'{IMG}/options/{pc}.webp' if got.get(iu) else None
                if icon: todo[f'{proj}/{icon}'] = ('icon', cpath(iu))
                options.setdefault(pc, {'name': ru(s['carSpecificationName']), 'note': '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': role})
                ops.append({'id': pc, 'def': bool(s.get('isDefault')), 'promo': False, 'promoTo': '', '_c': s['carSpecificationCode']})
                if role == 'int':
                    a, fp, bp = first(s.get('pcImgList')), first(s.get('frontPanoramaList')), first(s.get('backPanoramaList'))
                    if got.get(a):
                        ic = pre + pc; ints.append(ic); todo[f'{proj}/{IMG}/int/{ic}--int.webp'] = ('int', cpath(a))
                        if got.get(fp): todo[f'{proj}/{IMG}/int/{ic}--int2.webp'] = ('pano', cpath(fp))
                        if got.get(bp): todo[f'{proj}/{IMG}/int/{ic}--int3.webp'] = ('pano', cpath(bp))
            if ops and not any(o['def'] for o in ops): ops[0]['def'] = True
            secs.append({'sku': role, 'role': role, 'title': title, 'kind': 'option' if role == 'wheel' else 'swatch', 'img': 'int' if role == 'int' else 'ext', 'opts': ops, '_g': gc})
        c2o = {o['_c']: o['id'] for sc in secs for o in sc['opts']}
        # от чего зависит кадр кузова (сравнение по содержимому: одинаковые картинки лежат под разными адресами)
        keys = [sc['_g'] for sc in secs] + [e['carSpecificationCode'] for e in free]
        isx = {e['carSpecificationCode'] for e in free}; rolep = {sc['_g']: {'int': 1, 'wheel': 2, 'paint': 3}[sc['role']] for sc in secs}
        val = lambda r, k: r[1][k] if k in isx else r[0][k]
        sig = lambda r: tuple(content(u) for u in r[2])
        ext_keys = list(keys)
        for k in sorted(keys, key=lambda k: 0 if k in isx else rolep[k]):
            rest = [x for x in ext_keys if x != k]; seen = {}
            if all(seen.setdefault(tuple(val(r, x) for x in rest), sig(r)) == sig(r) for r in rows): ext_keys = rest
        if not ext_keys: ext_keys = [secs[0]['_g']]
        xid = {e['carSpecificationCode']: oid('k', e['carSpecificationName']) for e in extra}
        for r in rows:
            parts = [(xid[k] if r[1][k] else None) if k in isx else c2o[r[0][k]] for k in ext_keys]
            fc = pre + '_'.join(p for p in parts if p)
            if fc in have or len(r[2]) < 1 or not all(got.get(u) for u in r[2]): continue
            names = ['hero', 'side'][:len(r[2])]; have[fc] = names
            for n, u in zip(names, r[2]): todo[f'{proj}/{IMG}/ext/{fc}--{n}.webp'] = ('ext', cpath(u), n)
        for a, b in itertools.combinations(secs, 2):
            together = {(r[0][a['_g']], r[0][b['_g']]) for r in rows}
            for x in a['opts']:
                for y_ in b['opts']:
                    if (x['_c'], y_['_c']) not in together: bad[frozenset((x['id'], y_['id']))].add(vi)
        extras = []
        for e in included + free:
            pc = xid[e['carSpecificationCode']]; inc = e in included
            options[pc] = {'name': ru(e['carSpecificationName']), 'note': '', 'icon': None, 'mutex': [], 'cascade': [], 'sku': 'pk' + pc[1:]}
            extras.append({'sku': 'pk' + pc[1:], 'role': 'extra', 'title': options[pc]['name'], 'kind': 'check', 'img': 'ext' if e['carSpecificationCode'] in ext_keys else '',
                           'opts': [{'id': pc, 'def': inc, 'pre': (not inc) and bool(e.get('isDefault')), 'promo': False, 'promoTo': ''}]})
        extras.sort(key=lambda e: e['opts'][0]['def'])
        name, awd = vname(v['carVersionName'])
        tags = {t.get('title'): t.get('number') for t in json.loads(y.get('tagTitle') or '[]') if isinstance(t, dict)}
        total = next((n for t, n in tags.items() if t and '续航里程' in t and '纯电' not in t), None); ev = next((n for t, n in tags.items() if t and '纯电续航' in t), None)
        tag = ', '.join(x for x in ((f'{total} км общий запас хода' if ev else f'запас хода {total} км') if total else '', f'{ev} км на электричестве' if ev else '', 'полный привод' if awd else '') if x)
        gid = g['carYearTypeName'] if multi else ''
        if gid and gid not in [x['id'] for x in groups]:
            if gid not in GROUP_RU: raise SystemExit('нет перевода группы версий: ' + gid)
            groups.append({'id': gid, 'label': GROUP_RU[gid][0], 'sub': GROUP_RU[gid][1]})
        for sc in secs:
            sc.pop('_g')
            for o in sc['opts']: o.pop('_c')
        vsk = [('pk' + xid[k][1:]) if k in isx else ROLE[byg[k]['carSpecificationGroupType']][0] for k in ext_keys]
        vers.append({'id': f'v{vi}', 'name': name, 'tag': tag[:1].upper() + tag[1:], 'group': gid, 'drive': '', 'level': [], 'secs': secs + extras, 'codePrefix': pre,
                     'vehicleSkus': vsk, 'interiorSkus': ['int'], 'ranges': {}})
    gid2ru = {x['id']: f'g{n + 1}' for n, x in enumerate(groups)}                       # в данных не должно остаться иероглифов
    for x in groups: x['id'] = gid2ru[x['id']]
    for v in vers: v['group'] = gid2ru.get(v['group'], '')
    present = {i: {o['id'] for sc in v['secs'] for o in sc['opts']} for i, v in enumerate(vers)}
    for pair, vids in bad.items():
        a, b = sorted(pair); both = [i for i, ids in present.items() if a in ids and b in ids]
        if both and all(i in vids for i in both): options[a]['mutex'].append(b); options[b]['mutex'].append(a)
        elif any(i in vids for i in both): print('ВНИМАНИЕ: пара несовместима не во всех версиях, правило не поставлено:', options[a]['name'], '/', options[b]['name'], flush=True)
    boxes = {}
    for dst, job in todo.items():
        if job[0] != 'ext': continue
        bb = Image.open(job[1]).convert('RGBA').getbbox(); b = boxes.get(job[2])
        boxes[job[2]] = bb if not b else (min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3]))
    def make(item):
        dst, job = item
        if os.path.exists(dst) and os.path.getsize(dst) > 300: return
        if job[0] == 'pano': im = vid_vpered(job[1]); im.save(dst + '.part', 'WEBP', quality=84, method=4)
        else:
            im = Image.open(job[1])
            if job[0] == 'icon': im = im.convert('RGBA'); im.thumbnail((112, 112)); im.save(dst + '.part', 'WEBP', quality=88, method=4)
            elif job[0] == 'int': im = im.convert('RGB'); im.thumbnail((1600, 1600)); im.save(dst + '.part', 'WEBP', quality=84, method=4)
            else:
                im = im.convert('RGBA'); b = boxes[job[2]]; pad = 24
                im = im.crop((max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad), min(im.height, b[3] + pad)))
                im.thumbnail((1600, 1600)); im.save(dst + '.part', 'WEBP', quality=86, method=4)
        os.replace(dst + '.part', dst)
    with ThreadPoolExecutor(4) as ex: list(ex.map(make, todo.items()))
    for d in ('ext', 'int', 'options'):
        for fn in os.listdir(f'{proj}/{IMG}/{d}'):
            if f'{proj}/{IMG}/{d}/{fn}' not in todo: os.remove(f'{proj}/{IMG}/{d}/{fn}')
    ex_ = os.path.exists
    ints = sorted(c for c in set(ints) if ex_(f'{proj}/{IMG}/int/{c}--int.webp'))
    shots = [{'id': 'hero', 'label': 'Спереди', 'fit': 'contain'}, {'id': 'side', 'label': 'Сбоку', 'fit': 'contain'}, {'id': 'int', 'label': 'Салон', 'kind': 'int'}]
    if ints and all(ex_(f'{proj}/{IMG}/int/{c}--int2.webp') for c in ints): shots.append({'id': 'int2', 'label': 'За рулём', 'kind': 'int'})
    if ints and all(ex_(f'{proj}/{IMG}/int/{c}--int3.webp') for c in ints): shots.append({'id': 'int3', 'label': 'Из второго ряда', 'kind': 'int'})
    for v in vers:
        by = {sc['sku']: sc for sc in v['secs']}
        lists = [[o['id'] for o in by[k]['opts']] + ([None] if by[k]['role'] == 'extra' and not by[k]['opts'][0]['def'] else []) for k in v['vehicleSkus'] if k in by]
        allc = [c for c in itertools.product(*lists) if not any(b in options[a]['mutex'] for a, b in itertools.permutations([x for x in c if x], 2))]
        miss = [c for c in (v['codePrefix'] + '_'.join(x for x in combo if x) for combo in allc) if c not in have]
        if miss: print(f'ВНИМАНИЕ: {v["name"]} – нет кадра для {len(miss)} сборок из {len(allc)}:', miss[:6], flush=True)
    data = {'car': car, 'short': short, 'groups': groups, 'groupsTitle': 'Силовая установка', 'versions': vers, 'options': options, 'have': have, 'int': ints,
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': shots}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор store.xiaopeng.com, сняты скриптами tools/xpeng_snyat.py и tools/xpeng.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [(v['name'], v['tag'], v['group'], v['vehicleSkus']) for v in vers], 'сборок кузова', len(have), 'салонов', len(ints), 'видов', [s['id'] for s in shots])

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
