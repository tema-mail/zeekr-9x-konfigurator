"""Geely Galaxy (matrix.geely.com) -> конфигуратор на общем движке. Цен нет намеренно.
  python3 geely_snyat.py <productId> <папка проекта>                              -> raw/geely-raw.json
  python3 geely.py sobrat <папка проекта> "<Geely Galaxy E5>" "<Galaxy E5>" <slug>
Производитель даёт до пяти видов кузова на сборку (спереди ¾, сбоку, сзади ¾, сзади, спереди) и фото салона на отделку.
На номерных рамках и крышке багажника у него китайские надписи – закрашиваются (MASKS, координаты в пикселях исходного кадра)."""
import json, os, re, sys, subprocess, hashlib, itertools, collections, shutil
from concurrent.futures import ThreadPoolExecutor

RU = {
 # кузов
 '奶盐米': 'Бежевый «Молочный»', '樱花粉': 'Розовый «Сакура»', '香颂紫': 'Фиолетовый «Шансон»', '可可米': 'Бежевый «Какао»', '罗勒青': 'Зелёный «Базилик»', '冰莓粉': 'Розовый «Ледяная ягода»',
 '奶盖白': 'Белый «Молочная пенка»', '慕斯银': 'Серебристый «Мусс»', '百事橙': 'Оранжевый', '无忧绿': 'Зелёный «Беззаботный»', '流光银': 'Серебристый «Блик»',
 '暖阳米': 'Бежевый «Тёплое солнце»', '镜湖银': 'Серебристый «Зеркальное озеро»', '晨雾灰': 'Серый «Утренний туман»', '曙光白': 'Белый «Рассвет»', '午夜黑': 'Чёрный «Полночь»',
 '拂柳绿': 'Зелёный «Ива»', '墨影黑': 'Чёрный «Тушь»', '烟波灰': 'Серый «Дымка»', '星海蓝': 'Синий «Звёздное море»', '流月银': 'Серебристый «Лунный свет»', '初雪白': 'Белый «Первый снег»',
 '丝锦银': 'Серебристый «Шёлк»', '砚染灰': 'Серый «Графит»', '曜变黑': 'Чёрный «Сияние»', '脂玉白': 'Белый «Нефрит»',
 # диски
 '16英寸铝合金花瓣轮毂': '16″ литые «Лепестки»', '16英寸铝合金四叶草轮毂': '16″ литые «Клевер»', '16英寸大轮毂+四叶草装饰罩': '16″ с колпаками «Клевер»', '16英寸铝合金运动轮毂': '16″ литые спортивные',
 # салон
 '香芋白': 'Белый «Таро»', '星空灰': 'Серый «Звёздное небо»', '沐光米内饰': 'Бежевый «Свет»', '曜石黑（黑橙）': 'Чёрный с оранжевым', '曜石黑（黑红）': 'Чёрный с красным',
 '薄暮灰': 'Серый «Сумерки»', '旭日棕': 'Коричневый «Восход»', '星石黑': 'Чёрный', '星石黑（选装生态麂皮套装）': 'Чёрный, экозамша', '薄暮蓝': 'Синий «Сумерки»',
 '秋韵棕': 'Коричневый «Осень»', '映雪白': 'Белый «Снег»', '星舰灰': 'Серый', '烟雨墨黛': 'Тёмно-серый «Тушь»', '冬日暖棕': 'Коричневый «Тёплая зима»',
 # опции
 '黑色悬浮车顶': 'Чёрная «парящая» крыша', '泊车舒享包': 'Пакет «Парковка и комфорт»', '生态麂皮套装': 'Пакет «Экозамша»', '23扬Flyme Sound无界之声': 'Аудиосистема Flyme Sound, 23 динамика',
 'CCD智能可变阻尼悬架': 'Адаптивная подвеска CCD', '嚞桂套装': 'Пакет отделки «Чжэгуй»', 'BMXS爆胎稳行系统': 'Система устойчивости при проколе шины BMXS',
 '16扬Flyme Sound无界之声': 'Аудиосистема Flyme Sound, 16 динамиков', '可开启全景天窗（含遮阳帘）': 'Панорамный люк со шторкой', '19 英寸铝合金轮毂+固特异轮胎': 'Диски 19″ с шинами Goodyear',
 '超清W-HUD抬头显示': 'Проекционный дисплей W-HUD',
}
TRIM = [('探索+', 'Explore+'), ('探索', 'Explore'), ('乘风', 'Wind'), ('向往', 'Dream'), ('激光', 'Laser'), ('启航', 'Start'), ('全球经典', 'Global Classic'),
        ('远航+', 'Voyage+'), ('远航版+', 'Voyage+'), ('远航', 'Voyage'), ('豪华', 'Luxury'), ('尊贵', 'Premium'), ('旗舰', 'Flagship')]
PHEV = {'geely-starshine-6'}
ROLE = {'颜色': ('paint', 'Цвет кузова'), '轮毂': ('wheel', 'Диски'), '内饰': ('int', 'Цвет салона')}
NOBUY = '不购买'
SHOT_LABEL = {'hero': 'Спереди', 'side': 'Сбоку', 'rear34': 'Сзади', 'rear': 'Вид сзади', 'front': 'Вид спереди'}
# надписи на кадрах: plate – табличка (заливка цветом её фона), body – шильдик на кузове (интерполяция по строке), left – у края кузова
MASKS = {
 'geely-e5': {'hero': [((490, 833, 660, 880), 'plate')], 'rear34': [((2203, 803, 2316, 853), 'plate'), ((2026, 657, 2101, 687), 'body')], 'front': [((1355, 856, 1640, 908), 'plate')]},
 'geely-starship-7': {'hero': [((683, 798, 910, 876), 'plate')],
                      'rear34': [((2258, 572, 2408, 638), 'plate'), ((2038, 559, 2128, 587), 'body'), ((2488, 553, 2516, 594), 'left')],
                      'rear': [((1340, 594, 1625, 672), 'plate'), ((1017, 578, 1120, 608), 'body'), ((1835, 576, 1945, 625), 'body')], 'front': [((1338, 810, 1626, 889), 'plate')]},
 'geely-starshine-6': {'hero': [((389, 882, 537, 935), 'plate')],
                       'rear34': [((2352, 621, 2500, 673), 'plate'), ((2182, 732, 2276, 764), 'body'), ((2577, 716, 2654, 748), 'body')],
                       'rear': [((1333, 566, 1625, 634), 'plate'), ((992, 696, 1127, 737), 'body'), ((1757, 694, 1956, 739), 'body')], 'front': [((1318, 916, 1616, 981), 'plate')]},
 'geely-xingyuan': {},
 # Galaxy E5 Global Classic: другой передний бампер и другие места надписей; у этих сборок пять видов
 'geely-e5:5': {'hero': [((360, 856, 495, 906), 'plate')], 'rear34': [((2531, 829, 2623, 878), 'plate'), ((2353, 623, 2429, 656), 'body')],
                'rear': [((1372, 829, 1606, 880), 'plate'), ((1052, 616, 1153, 649), 'body')], 'front': [((1328, 844, 1582, 897), 'plate')]},
}
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def vname(cn, slug):
    m = re.match(r'\s*(\d{3})\s*km\s*', cn); km = m.group(1) if m else ''
    rest = cn[m.end():] if m else cn
    word = next((en for zh, en in TRIM if zh in rest), None)
    lat = ' '.join(x for x in re.findall(r'[A-Za-z][A-Za-z+]*', rest) if x != 'EF')
    name = ' '.join(x for x in (word, lat) if x) or None
    if not name: raise SystemExit('нет перевода версии: ' + cn)
    tag = (f'{km} км на электричестве' if slug in PHEV else f'Запас хода {km} км') if km else ''
    return (name + (' ' + km if km else '')).strip(), tag

def ru(cn, interior=False):
    if cn in RU: return RU[cn]
    base = re.sub(r'（[^）]*版）$', '', cn)               # «香芋白（探索版）» – отделка та же, в скобках только версия
    if base in RU: return RU[base]
    raise SystemExit('нет перевода: ' + cn)

def curl(url, dst):
    from PIL import Image
    if os.path.exists(dst) and os.path.getsize(dst) > 800: return True
    if not url: return False
    for a in range(6):
        r = subprocess.run(['curl', '-s', '--max-time', '90', '-A', UA, '-o', dst + '.part', '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout == '200' and os.path.getsize(dst + '.part') > 800:
            try: Image.open(dst + '.part').load()
            except Exception: continue
            os.replace(dst + '.part', dst); return True
    if os.path.exists(dst + '.part'): os.remove(dst + '.part')
    return False

def inpaint(im, box, kind):
    px = im.load(); x0, y0, x1, y1 = box
    if kind == 'plate':
        edge = [px[x, y][:3] for x in range(x0, x1, 2) for y in (y0, y1 - 1)] + [px[x, y][:3] for y in range(y0, y1, 2) for x in (x0, x1 - 1)]
        c = tuple(sorted(e[i] for e in edge)[len(edge) // 2] for i in range(3))   # фон таблички – медиана по краю прямоугольника (край лежит вне букв)
        for y in range(y0, y1):
            for x in range(x0, x1): px[x, y] = c + (px[x, y][3],)
    elif kind == 'left':
        for y in range(y0, y1):
            l = px[x0 - 2, y]
            for x in range(x0, x1): px[x, y] = l[:3] + (px[x, y][3],)
    else:
        for y in range(y0, y1):
            l = px[x0 - 2, y]; r = px[x1 + 2, y]
            for x in range(x0, x1):
                t = (x - x0) / max(1, x1 - x0)
                px[x, y] = tuple(int(l[i] + (r[i] - l[i]) * t) for i in range(3)) + (px[x, y][3],)

def sobrat(proj, car, short, slug):
    from PIL import Image
    raw = json.load(open(f'{proj}/raw/geely-raw.json'))
    IMG = f'img/{slug}'; CACHE = f'{proj}/raw/cache'
    shutil.rmtree(f'{proj}/{IMG}/ext', ignore_errors=True)
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    cpath = lambda u: f'{CACHE}/{hashlib.md5(u.encode()).hexdigest()}.img'
    skus = raw['product']['skuList']
    flat, specs = {}, collections.OrderedDict()                       # attrId -> (specId, attr); specId -> spec с классом
    for c in raw['classify']:
        for sp in c['specsList']:
            specs[sp['id']] = dict(sp, ctype=c.get('type'))
            for a in sp['attrList']: flat[a['id']] = (sp['id'], a)
    urls = set()
    for s in skus: urls |= set(filter(None, (s.get('imgUrl') or '').split(',')))
    for sid, a in flat.values():
        for k in ('attrLitimg', 'attrMainImgs'): urls |= set(filter(None, (a.get(k) or '').split(',')))
    urls = sorted(urls)
    with ThreadPoolExecutor(6) as ex: got = dict(zip(urls, ex.map(lambda u: curl(u, cpath(u)), urls)))
    print('картинок у производителя', len(urls), 'не скачалось', sum(not g for g in got.values()), flush=True)
    vspec = next(sid for sid, sp in specs.items() if sp['ctype'] == 1)
    reg = {}
    def oid(letter, aid):
        if aid not in reg: reg[aid] = f'{letter}{len([k for k in reg.values() if k[0] == letter]) + 1}'
        return reg[aid]
    def shots_of(urllist):
        n = len(urllist)
        if n == 1: return ['hero']
        if n == 4: return ['hero', 'side', 'rear34', 'front']
        if n == 5: return ['hero', 'side', 'rear34', 'rear', 'front']
        raise SystemExit(f'неожиданное число видов кузова: {n}')
    todo, options, vers, have, ints, bad = {}, {}, [], {}, [], collections.defaultdict(set)
    masks = MASKS.get(slug)
    if masks is None: raise SystemExit('нет координат надписей для ' + slug + ': снять и добавить в MASKS')
    for va in specs[vspec]['attrList']:
        vs = [s for s in skus if va['id'] in s['attrIdList']]
        if not vs: continue
        vi = len(vers); pre = f'v{vi}-'
        name, tag = vname(va['name'], slug)
        rows = []                                                        # сборка: {specId: attrId}, картинки
        for s in vs:
            r = {flat[a][0]: a for a in s['attrIdList'] if a in flat and flat[a][0] != vspec}
            rows.append((r, tuple(filter(None, (s.get('imgUrl') or '').split(','))), bool(s.get('defaultFlag'))))
        base = next((r for r, _, d in rows if d), rows[0][0])
        choice = [sid for sid, sp in specs.items() if sp['ctype'] in (2, 3) and any(sid in r for r, _, _ in rows)]
        opts = [sid for sid, sp in specs.items() if sp['ctype'] == 4 and any(sid in r for r, _, _ in rows)]
        buy = {sid: next(a['id'] for a in specs[sid]['attrList'] if a['name'] != NOBUY) for sid in opts}
        on = lambda r, sid: r.get(sid) == buy[sid]
        included = [sid for sid in opts if all(on(r, sid) for r, _, _ in rows)]
        free = [sid for sid in opts if sid not in included and any(on(r, sid) for r, _, _ in rows)]
        # опция, которая целиком следует из выбранной отделки (салон «с пакетом экозамши»), – не отдельная галочка
        tied = [sid for sid in free if any(all(len({on(r, sid) for r, _, _ in rows if r.get(k) == x}) == 1 for x in {r.get(k) for r, _, _ in rows}) for k in choice)]
        free = [sid for sid in free if sid not in tied]
        secs = []
        for sid in choice:
            sp = specs[sid]
            if sp['name'] not in ROLE: raise SystemExit('неизвестная группа выбора: ' + sp['name'])
            role, title = ROLE[sp['name']]; ops = []
            for a in sp['attrList']:
                if not any(r.get(sid) == a['id'] for r, _, _ in rows): continue
                pc = oid(role[0], a['id']); lit = (a.get('attrLitimg') or '').split(',')[0]
                icon = f'{IMG}/options/{pc}.webp' if got.get(lit) else None
                if icon: todo[f'{proj}/{icon}'] = (cpath(lit), 'icon', None, None)
                options[pc] = {'name': ru(a['name']), 'note': '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': role}
                ops.append({'id': pc, 'def': base.get(sid) == a['id'], 'promo': False, 'promoTo': ''})
                main = (a.get('attrMainImgs') or '').split(',')[0]
                if role == 'int' and got.get(main):
                    code = pre + pc
                    if code not in ints: ints.append(code); todo[f'{proj}/{IMG}/int/{code}--int.webp'] = (cpath(main), 'int', None, None)
            secs.append({'sku': role, 'role': role, 'title': title, 'kind': 'option' if role == 'wheel' else 'swatch', 'img': 'int' if role == 'int' else 'ext', 'opts': ops, '_sid': sid})
        # от чего зависит кадр кузова
        keys = choice + free
        val = lambda r, k: on(r, k) if k in free else r.get(k)
        ext_keys = list(keys); order = {'int': 1, 'wheel': 2, 'paint': 3}
        for k in sorted(keys, key=lambda k: 0 if k in free else order[ROLE[specs[k]['name']][0]]):
            rest = [x for x in ext_keys if x != k]; seen = {}
            if all(seen.setdefault(tuple(val(r, x) for x in rest), im) == im for r, im, _ in rows): ext_keys = rest
        if not ext_keys: ext_keys = [choice[0]]
        sku_of = lambda k: ('pk' + reg_opt(k)) if k in free else ROLE[specs[k]['name']][0]
        def reg_opt(sid): return oid('k', buy[sid])[1:]
        for r, im, _ in rows:
            parts = []
            for k in ext_keys:
                if k in free: parts.append(oid('k', buy[k]) if on(r, k) else None)
                else: parts.append(oid(ROLE[specs[k]['name']][0], r[k]))
            code = pre + '_'.join(p for p in parts if p)
            if code in have or not im or not all(got.get(u) for u in im): continue
            names = shots_of(im); mk = MASKS.get(f'{slug}:{len(im)}', masks)     # у части версий своя внешность и свои координаты
            have[code] = names
            for n, u in zip(names, im): todo[f'{proj}/{IMG}/ext/{code}--{n}.webp'] = (cpath(u), 'ext', (n, len(im)), mk.get(n))
        for a, b in itertools.combinations(choice, 2):
            together = {(r.get(a), r.get(b)) for r, _, _ in rows}
            for x in {r.get(a) for r, _, _ in rows}:
                for y in {r.get(b) for r, _, _ in rows}:
                    if (x, y) not in together: bad[reg[x]].add((vi, reg[y]))
        extras = []
        for sid in included + free:
            pc = oid('k', buy[sid]); inc = sid in included
            options[pc] = {'name': ru(next(a['name'] for a in specs[sid]['attrList'] if a['id'] == buy[sid])), 'note': '', 'icon': None, 'mutex': [], 'cascade': [], 'sku': 'pk' + pc[1:]}
            extras.append({'sku': 'pk' + pc[1:], 'role': 'extra', 'title': options[pc]['name'], 'kind': 'check', 'img': 'ext' if sid in ext_keys else '',
                           'opts': [{'id': pc, 'def': inc, 'pre': (not inc) and on(base, sid), 'promo': False, 'promoTo': ''}]})
        extras.sort(key=lambda e: e['opts'][0]['def'])
        vsk = [('pk' + oid('k', buy[k])[1:]) if k in free else ROLE[specs[k]['name']][0] for k in ext_keys]
        for sc in secs: sc.pop('_sid')
        vers.append({'id': f'v{vi}', 'name': name, 'tag': tag, 'group': '', 'drive': '', 'level': [], 'secs': secs + extras, 'codePrefix': pre,
                     'vehicleSkus': vsk, 'interiorSkus': ['int'], 'ranges': {}})
    present = {i: {o['id'] for s in v['secs'] for o in s['opts']} for i, v in enumerate(vers)}
    for pc, pairs in bad.items():
        byopt = collections.defaultdict(set)
        for vi, other in pairs: byopt[other].add(vi)
        for other, vids in byopt.items():
            both = [vi for vi, ids in present.items() if pc in ids and other in ids]
            if both and all(vi in vids for vi in both): options[pc]['mutex'].append(other)
            elif any(vi in vids for vi in both): print('ВНИМАНИЕ: пара несовместима не во всех версиях, правило не поставлено:', options[pc]['name'], '/', options[other]['name'], flush=True)
    # общий прямоугольник обрезки для каждого вида: машина одного размера во всех цветах
    boxes = {}
    for dst, (src, kind, shot, m) in todo.items():
        if kind != 'ext': continue
        bb = Image.open(src).convert('RGBA').getbbox(); b = boxes.get(shot)
        boxes[shot] = bb if not b else (min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3]))
    def make(item):
        dst, (src, kind, shot, m) = item
        im = Image.open(src)
        if kind == 'icon': im = im.convert('RGBA'); im.thumbnail((112, 112)); im.save(dst + '.part', 'WEBP', quality=85, method=4)
        elif kind == 'int':                                        # у части фото внизу справа китайская сноска – нижние 10 % срезаем у всех одинаково
            im = im.convert('RGB'); im = im.crop((0, 0, im.width, int(im.height * 0.90))); im.thumbnail((1280, 1280)); im.save(dst + '.part', 'WEBP', quality=80, method=4)
        else:
            im = im.convert('RGBA')
            for box, mk in (m or []): inpaint(im, box, mk)
            b = boxes[shot]; pad = 24
            im = im.crop((max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad), min(im.height, b[3] + pad)))
            im.thumbnail((1400, 1400)); im.save(dst + '.part', 'WEBP', quality=82, method=4)
        os.replace(dst + '.part', dst)
    with ThreadPoolExecutor(6) as ex: list(ex.map(make, todo.items()))
    for v in vers:
        for s in v['secs']:
            if s['kind'] == 'swatch' and not all(options[o['id']]['icon'] for o in s['opts']): s['kind'] = 'seg'
        by = {sc['sku']: sc for sc in v['secs']}
        lists = [[o['id'] for o in by[k]['opts']] + ([None] if by[k]['role'] == 'extra' and not by[k]['opts'][0]['def'] else []) for k in v['vehicleSkus'] if k in by]
        allc = [c for c in itertools.product(*lists)
                if not any(b in options[a]['mutex'] or a in options[b]['mutex'] for a, b in itertools.combinations([x for x in c if x], 2))]
        miss = [c for c in (v['codePrefix'] + '_'.join(x for x in combo if x) for combo in allc) if c not in have]
        if miss: print(f'ВНИМАНИЕ: {v["name"]} – нет кадра для {len(miss)} сборок из {len(allc)}:', miss[:6], flush=True)
    used = sorted({n for s in have.values() for n in s}, key=list(SHOT_LABEL).index)
    shots = [{'id': n, 'label': SHOT_LABEL[n] if len(used) > 1 else 'Кузов', 'fit': 'contain'} for n in used] + [{'id': 'int', 'label': 'Салон', 'kind': 'int'}]
    data = {'car': car, 'short': short, 'groups': [], 'versions': vers, 'options': options, 'have': have, 'int': sorted(ints),
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': shots}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор matrix.geely.com, сняты скриптами tools/geely_snyat.py и tools/geely.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [(v['name'], v['tag'], v['vehicleSkus']) for v in vers], 'сборок кузова', len(have), 'видов', used, 'салонов', len(ints))

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
