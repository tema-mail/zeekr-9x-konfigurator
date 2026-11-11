"""Avatr (avatr.com) -> конфигуратор на общем движке. Цен нет намеренно.
Съём дерева опций и адресов кадров идёт на сервере в Амстердаме (tools/avatr_srv.py, открытый API, браузер не нужен):
  ssh claude-vps 'cd tools/konfig && python3 avatr_srv.py <productCarId> avatr/<slug>.json'  -> скопировать в <проект>/raw/avatr-raw.json
  python3 avatr.py sobrat <папка проекта> "<Avatr 07L>" "<07L>" <slug>
Кадр кузова у Avatr зависит от версии, цвета, дисков, салона, электронных зеркал и спортивного обвеса.
На кадрах производителя есть китайский текст: строка-оговорка внизу (обрезается), надпись на номерной рамке
спереди и шильдик на двери багажника (закрашиваются по координатам MASKS; перед выкладкой смотреть глазами)."""
import json, os, re, sys, subprocess, tempfile, collections
from concurrent.futures import ThreadPoolExecutor

RU = {
 # кузов
 '弦月银': 'Серебристый «Полумесяц»', '星紫': 'Фиолетовый «Звезда»', '岩灰': 'Серый «Скала»', '漠白': 'Белый «Пустыня»', '墨黑': 'Чёрный «Тушь»', '晴蓝': 'Голубой «Ясное небо»',
 '苍绿': 'Зелёный «Лес»', '曜黑': 'Чёрный «Сияние»', '曜灰': 'Серый «Сияние»', '皓白/黑顶': 'Белый с чёрной крышей', '云紫': 'Фиолетовый «Облако»',
 '烟紫/黑顶': 'Дымчато-фиолетовый с чёрной крышей', '丹红/黑顶': 'Красный с чёрной крышей', '皓白': 'Белый «Сияние»', '鎏棕': 'Коричневый с золотом',
 '烟紫/曜黑双拼': 'Двухцветный: дымчато-фиолетовый с чёрным', '曦金灰': 'Серо-золотой «Рассвет»',
 # диски
 '20英寸旋叶轮毂': '20″ «Лопасти»', '21英寸气旋轮毂': '21″ «Циклон»', '20英寸低风阻轮毂': '20″ аэродинамические', '21英寸运动多辐轮毂': '21″ спортивные многоспицевые',
 '20英寸气旋五辐运动轮毂': '20″ спортивные «Циклон», 5 спиц', '20英寸气旋五辐运动轮毂(配米其林高性能轮胎)': '20″ спортивные «Циклон» с шинами Michelin',
 '20英寸星旋五辐锻造轮毂': '20″ кованые «Звёздный вихрь»', '21英寸光束多辐运动轮毂': '21″ спортивные «Луч»', '21英寸气旋五辐运动轮毂': '21″ спортивные «Циклон», 5 спиц',
 # салон
 '枫红/云白': 'Красный с белым', '暮紫/烟白': 'Фиолетовый с белым', '深紫': 'Тёмно-фиолетовый', '白棕': 'Белый с коричневым', '岩棕': 'Коричневый «Скала»', '岱红': 'Красный',
 '亲肤套装': 'Мягкая экокожа', '尊享套装': 'Кожа Nappa',
 # дополнительно
 '超清电子外后视镜': 'Электронные зеркала с камерами', '超清电子外后视镜套装': 'Электронные зеркала с камерами', '智能车载冷暖箱': 'Холодильник с подогревом',
 '副驾零重力座椅': 'Кресло пассажира «невесомость»', '主驾零重力座椅': 'Кресло водителя «невесомость»', 'HUAWEI SOUND® 25扬声器 SUPERIOR 卓越系列音响': 'Аудиосистема Huawei Sound, 25 динамиков',
 '英国之宝·卓越之声音响系统(25扬)': 'Аудиосистема Meridian, 25 динамиков', '舒享套装': 'Пакет «Комфорт»', '前排智能电动门': 'Электропривод передних дверей',
 '运动套件': 'Спортивный обвес', '运动套装': 'Спортивный обвес', '豪华影院套装': 'Пакет «Кинотеатр»',
}
RU_BY_TYPE = {('car_deluxe_set', '尊享套装'): 'Пакет «Премиум»: кожа Nappa', ('sys_car_S7010', '墨黑'): 'Чёрный'}
TITLE = {'sys_car_body_color': 'Цвет кузова', 'sys_car_S6690': 'Диски', 'sys_car_S7010': 'Цвет салона', 'sys_car_material': 'Отделка салона'}
ROLE = {'sys_car_body_color': 'paint', 'sys_car_S6690': 'wheel', 'sys_car_S7010': 'int'}
SKIP_TYPES = {'sys_car_seat_amount'}
ENERGY = {'ev': ('Электро', ''), 'reev': ('Гибрид', 'с бензиновым генератором')}
SHOTS = [{'id': 'hero', 'label': 'Спереди', 'fit': 'contain'}, {'id': 'side', 'label': 'Сбоку', 'fit': 'contain'}, {'id': 'rear34', 'label': 'Сзади', 'fit': 'contain'},
         {'id': 'int', 'label': 'Салон', 'kind': 'int'}, {'id': 'int2', 'label': 'Сбоку', 'kind': 'int'}, {'id': 'int3', 'label': 'Задний ряд', 'kind': 'int'}]
# Китайские надписи на машине: (x0, y0, x1, y1) в пикселях исходного кадра; 'plate' – закрасить цветом рамки, 'body' – цветом кузова по соседним пикселям
MASKS = {
 'avatr-07l': {'hero': [((217, 613, 251, 637), 'plate')], 'rear34': [((1118, 537, 1164, 559), 'body')]},
 'avatr-06':  {'hero': [((232, 606, 288, 646), 'plate')], 'rear34': [((1118, 519, 1162, 539), 'body')]},
 'avatr-06t': {'hero': [((218, 616, 259, 650), 'plate')], 'rear34': [((1146, 535, 1182, 551), 'body')]},
 'avatr-12':  {'hero': [((335, 578, 409, 618), 'plate')], 'rear34': [((1052, 513, 1106, 536), 'body')]},
 'avatr-07':  {'hero': [((246, 524, 314, 564), 'plate')], 'rear34': [((898, 482, 950, 501), 'body')]},
}

def oid(code): return code.replace('_', 'u')          # в именах файлов «_» разделяет опции

def vname(cn):
    if '猎装骑士' in cn: return 'Knight', 'Особая серия'
    if '皇家剧院' in cn: return 'Royal Theatre', 'Особая серия'
    lat = re.match(r'[A-Za-z+ ]+', cn); name = lat.group(0).strip() if lat else cn
    tag = '3 мотора' if '三电机' in cn else ('2 мотора' if '双电机' in cn else '')
    return name, tag

def inpaint(im, box, kind):
    """Закрасить прямоугольник: plate – медианой тёмных пикселей рамки, body – построчной интерполяцией между краями."""
    px = im.load(); x0, y0, x1, y1 = box
    if kind == 'plate':
        cols = sorted(px[x, y][:3] for x in range(x0, x1) for y in range(y0, y1))
        c = cols[len(cols) // 5]                              # тёмная пятая часть – фон рамки, не буквы
        for y in range(y0, y1):
            for x in range(x0, x1): px[x, y] = c + (px[x, y][3],)
    elif kind == 'left':                                       # у края кузова: тянем цвет слева
        for y in range(y0, y1):
            l = px[x0 - 2, y]
            for x in range(x0, x1): px[x, y] = l[:3] + (px[x, y][3],)
    else:
        for y in range(y0, y1):
            l = px[x0 - 2, y]; r = px[x1 + 2, y]
            for x in range(x0, x1):
                t = (x - x0) / max(1, x1 - x0)
                px[x, y] = tuple(int(l[i] + (r[i] - l[i]) * t) for i in range(3)) + (px[x, y][3],)

def fetch_img(url, dst, kind, masks=None):
    from PIL import Image
    if os.path.exists(dst): return 'skip'
    if not url: return 'нет'
    tmp = tempfile.mktemp(suffix='.png')
    try:
        for a in range(3):
            r = subprocess.run(['curl', '-s', '--max-time', '90', '-o', tmp, '-w', '%{http_code}', url], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout == '200' and os.path.getsize(tmp) > 1500:
                try: im = Image.open(tmp); im.load()
                except Exception: continue
                if kind == 'icon':
                    im = im.convert('RGBA'); im.thumbnail((112, 112)); im.save(dst, 'WEBP', quality=85, method=6)
                elif kind == 'ext':
                    im = im.convert('RGBA'); w, h = im.size
                    for box, mk in (masks or []): inpaint(im, box, mk)
                    im = im.crop((0, int(h * 0.16), w, int(h * 0.78)))          # без строки-оговорки внизу
                    im.thumbnail((1400, 1400)); im.save(dst, 'WEBP', quality=82, method=6)
                else:
                    im = im.convert('RGB'); w, h = im.size
                    im = im.crop((0, 0, w, int(h * 0.80)))                       # оговорка поверх нижней части кадра
                    im = im.resize((1280, int(1280 * im.size[1] / w)), Image.LANCZOS); im.save(dst, 'WEBP', quality=78, method=6)
                return 'ok'
        return 'нет'
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def sobrat(proj, car, short, slug):
    raw = json.load(open(f'{proj}/raw/avatr-raw.json'))
    IMG = f'img/{slug}'
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    def ru(tcode, cn):
        if (tcode, cn) in RU_BY_TYPE: return RU_BY_TYPE[(tcode, cn)]
        if cn not in RU: raise SystemExit('нет перевода: ' + cn + ' (' + tcode + ')')
        return RU[cn]
    masks = MASKS.get(slug, {})
    jobs, options, vers, have, ang, ints = [], {}, [], {}, {}, []
    energies = []
    for vi, v in enumerate(raw['versions']):
        if v['energy'] not in energies: energies.append(v['energy'])
        pre = f'v{vi}-'
        name, tag = vname(v['name'])
        secs, extras = [], []
        for t in v['types']:
            tc = t['code']
            if tc in SKIP_TYPES or not t['opts']: continue
            for o in t['opts']:
                pc = oid(o['code']); role = ROLE.get(tc)
                icon = f'{IMG}/options/{pc}.webp' if (o.get('pic') and role) else None
                if icon: jobs.append((o['pic'], f'{proj}/{icon}', 'icon', None))
                options[pc] = {'name': ru(tc, o['name']), 'note': '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': tc}
            mk = lambda o, **kw: dict({'id': oid(o['code']), 'def': o['selected'], 'promo': False, 'promoTo': ''}, **kw)
            if tc in ROLE:
                secs.append({'sku': tc, 'role': ROLE[tc], 'title': TITLE[tc], 'kind': 'option' if ROLE[tc] == 'wheel' else 'swatch', 'img': 'int' if ROLE[tc] == 'int' else 'ext', 'opts': [mk(o) for o in t['opts']]})
            elif t['required'] and len(t['opts']) > 1:
                if tc not in TITLE: raise SystemExit('нет перевода группы: ' + t['name'])
                secs.append({'sku': tc, 'role': 'choice', 'title': TITLE[tc], 'kind': 'seg', 'img': 'int' if tc in v['intDims'] else '', 'opts': [mk(o) for o in t['opts']]})
            elif not t['required'] or len(t['opts']) == 1:
                o = t['opts'][0]; std = o['selected'] and (o['standard'] or t['required'])
                extras.append({'sku': tc, 'role': 'extra', 'title': options[oid(o['code'])]['name'], 'kind': 'check', 'img': 'ext' if tc in v['extDims'] else '',
                               'opts': [{'id': oid(o['code']), 'def': bool(std), 'pre': bool(o['selected'] and not std), 'promo': False, 'promoTo': ''}]})
        order = {'paint': 0, 'wheel': 1, 'int': 2, 'choice': 3}
        secs.sort(key=lambda s: order[s['role']])
        # у производителя часть вариантов в списке есть, а собрать с ними машину нельзя (остатки модели): показываем только то, для чего снят кадр
        colors = sorted((o['code'] for t in v['types'] if t['code'] == 'sys_car_body_color' for o in t['opts']), key=len, reverse=True)
        seen = set()
        for key in v['ext']:
            col = next(c for c in colors if key.startswith(c + '_'))
            seen |= {oid(p) for p in [col] + key[len(col) + 1:].split('_') if p != '0'}
        for sc in secs:
            if sc['sku'] in v['extDims']:
                gone = [options[o['id']]['name'] for o in sc['opts'] if o['id'] not in seen]
                if gone: print('  нет в продаже, убрано:', name, sc['title'], gone, flush=True)
                sc['opts'] = [o for o in sc['opts'] if o['id'] in seen]
                if sc['opts'] and not any(o['def'] for o in sc['opts']): sc['opts'][0]['def'] = True
        extras = [e for e in extras if e['sku'] not in v['extDims'] or e['opts'][0]['id'] in seen or e['opts'][0]['def']]
        colors = sorted((o['code'] for t in v['types'] if t['code'] == 'sys_car_body_color' for o in t['opts']), key=len, reverse=True)
        for key, urls in v['ext'].items():
            col = next(c for c in colors if key.startswith(c + '_'))          # код цвета может содержать «_»
            code = pre + '_'.join(oid(p) for p in [col] + key[len(col) + 1:].split('_') if p != '0')
            if len(urls) < 3: continue
            have[code] = ['hero']; ang[code] = ['side', 'rear34']
            for shot, u in zip(['hero', 'side', 'rear34'], urls): jobs.append((u, f'{proj}/{IMG}/ext/{code}--{shot}.webp', 'ext', masks.get(shot)))
        for key, urls in v['int'].items():
            code = pre + '_'.join(oid(p) for p in key.split('_'))
            if len(urls) < 3: continue
            ints.append(code)
            for shot, u in zip(['int', 'int2', 'int3'], urls): jobs.append((u, f'{proj}/{IMG}/int/{code}--{shot}.webp', 'int', None))
        vers.append({'id': v['code'], 'name': name, 'tag': tag, 'group': v['energy'], 'drive': '', 'level': [], 'secs': secs + extras, 'codePrefix': pre,
                     'vehicleSkus': v['extDims'], 'angleSkus': v['extDims'], 'interiorSkus': v['intDims'], 'ranges': {}})
    with ThreadPoolExecutor(12) as ex: res = list(ex.map(lambda j: fetch_img(*j), jobs))
    print('картинки', collections.Counter(res), flush=True)
    ex_ = lambda f: os.path.exists(f'{proj}/{f}')
    have = {c: s for c, s in have.items() if ex_(f'{IMG}/ext/{c}--hero.webp')}
    ang = {c: [x for x in s if ex_(f'{IMG}/ext/{c}--{x}.webp')] for c, s in ang.items() if c in have}
    ints = sorted(c for c in ints if all(ex_(f'{IMG}/int/{c}--{x}.webp') for x in ('int', 'int2', 'int3')))
    for o in options.values():
        if o['icon'] and not ex_(o['icon']): o['icon'] = None
    for v in vers:
        for s in v['secs']:
            if s['kind'] == 'swatch' and not all(options[o['id']]['icon'] for o in s['opts']): s['kind'] = 'seg'
    groups = [{'id': e, 'label': ENERGY[e][0], 'sub': ENERGY[e][1]} for e in energies] if len(energies) > 1 else []
    if not groups:
        for v in vers: v['group'] = ''
    import itertools
    for v in vers:
        by = {sc['sku']: sc for sc in v['secs']}
        lists = [[o['id'] for o in by[k]['opts']] + ([None] if by[k]['role'] == 'extra' and not by[k]['opts'][0]['def'] else []) for k in v['vehicleSkus'] if k in by]
        miss = [c for c in (v['codePrefix'] + '_'.join(x for x in combo if x) for combo in itertools.product(*lists)) if c not in have]
        if miss: print(f'ВНИМАНИЕ: {v["name"]} – нет кадра для {len(miss)} сборок из {len(list(itertools.product(*lists)))}:', miss[:6], flush=True)
    data = {'car': car, 'short': short, 'groups': groups, 'groupsTitle': 'Силовая установка', 'versions': vers, 'options': options, 'have': have, 'ang': ang, 'int': ints,
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': SHOTS}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор avatr.com, сняты скриптами tools/avatr_srv.py и tools/avatr.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), 'сборок кузова', len(have), 'салонов', len(ints))

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
