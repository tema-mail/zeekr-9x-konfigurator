"""Lynk & Co (lynkco.com.cn) -> конфигуратор на общем движке. Цен нет намеренно.
  python3 lynkco_snyat.py <vcId серии> <папка проекта>                       -> raw/lynk-raw.json
  python3 lynkco.py sobrat <папка проекта> "<Lynk & Co 900>" "<900>" <slug>
Производитель даёт одну картинку кузова на сборку (спереди, без фона) и одно фото салона на отделку;
остальные виды у них – трёхмерная модель, её не берём. Сайт не открывается с сервера в Нидерландах, отвечает с перебоями."""
import json, os, re, sys, subprocess, tempfile, itertools, collections
from concurrent.futures import ThreadPoolExecutor

RU = {
 # кузов
 '曜日银': 'Серебристый «Солнце»', '晨晖蓝': 'Голубой «Рассвет»', '极夜黑': 'Чёрный «Полярная ночь»', '云晞灰': 'Серый «Облако»', '拂晓白': 'Белый «Заря»', '山茶白': 'Белый «Камелия»',
 '沙丘米': 'Бежевый «Дюна»', '白黑': 'Белый с чёрной крышей', '黑': 'Чёрный', '拂晓白黑': 'Белый «Заря» с чёрной крышей', '极光银黑': 'Серебристый «Аврора» с чёрной крышей', '灰': 'Серый',
 '白': 'Белый', '鎏光金黑': 'Золотистый с чёрной крышей', '日冕金': 'Золотистый «Корона»', '跃动橙黑': 'Оранжевый с чёрной крышей', '安可拉红': 'Красный «Анкора»', '跃动24黄': 'Жёлтый «24»',
 '银色山泉': 'Серебристый «Родник»', '鸢尾紫': 'Фиолетовый «Ирис»',
 # салон
 '星夜蓝': 'Синий «Звёздная ночь»', '暗夜蓝': 'Тёмно-синий', '暗曜黑': 'Чёрный', '棕': 'Коричневый', '灰色': 'Серый', '运动': 'Спортивный', '云绒棕': 'Коричневый «Велюр»',
 '日光米': 'Бежевый «Солнечный»', '暖云沙': 'Песочный', '白紫': 'Белый с фиолетовым', '赤霞橘': 'Оранжевый «Закат»', '暗影红': 'Тёмно-красный',
 # диски
 '18英寸': '18″', '19英寸': '19″', '20英寸': '20″', '19英寸叠星轮毂': '19″ «Звёзды»', '19英寸熏黑运动轮毂': '19″ спортивные тёмные', '20英寸光旋轮毂': '20″ «Световой вихрь»',
 '20英寸璀钻轮毂': '20″ «Бриллиант»', '21英寸光晖轮毂': '21″ «Сияние»', '21英寸光翼轮毂': '21″ «Световое крыло»', '18英寸战斧轮毂': '18″ «Томагавк»', '18英寸风纹轮毂': '18″ «Ветер»',
 '19英寸风逸轮毂': '19″ «Бриз»', '21英寸光曜轮毂': '21″ «Блеск»',
 # крыша
 '撞色车顶': 'Контрастная', '车身同色': 'В цвет кузова', '全景天幕': 'Панорамная крыша', '全景天窗': 'Панорамный люк',
 # пакеты
 '31扬哈曼卡顿Performance升级包': 'Аудиосистема Harman Kardon Performance, 31 динамик', '31扬哈曼卡顿performance升级包': 'Аудиосистема Harman Kardon Performance, 31 динамик',
 '37.5L前备箱冰柜': 'Холодильник в переднем багажнике, 37,5 л', '6.8L中扶手冷暖冰箱': 'Холодильник в подлокотнике, 6,8 л', 'CCD连续可变阻尼悬架': 'Адаптивная подвеска CCD',
 '副驾座椅电动4向调节': 'Электрорегулировка кресла пассажира', '副驾零重力座椅': 'Кресло пассажира «невесомость»', '千里浩瀚H7辅助驾驶方案': 'Пакет помощи водителю H7',
 '千里浩瀚安全辅助驾驶H7方案': 'Пакет помощи водителю H7', '哈曼卡顿23扬豪华音响': 'Аудиосистема Harman Kardon, 23 динамика', '感应电动后尾门': 'Электропривод двери багажника с датчиком',
 '手机UWB/NFC钥匙': 'Ключ в телефоне (UWB/NFC)', '智能电动拖车钩': 'Электрический фаркоп', '电动前备箱(可敲击感应开闭)': 'Электропривод переднего багажника', '电动拖车钩': 'Электрический фаркоп',
 '电动踏板': 'Выдвижные пороги', '破风尾翼': 'Спойлер', '贯穿式科技交互屏': 'Экран на всю ширину панели', '闭式双腔空气悬架': 'Двухкамерная пневмоподвеска',
}
SKU = {'外观': ('paint', 'Цвет кузова', 'paint'), '轮毂': ('wheel', 'Диски', 'wheel'), '内饰': ('int', 'Цвет салона', 'int'), '车顶颜色': ('roof', 'Крыша', 'choice'),
       '天窗': ('sunroof', 'Остекление крыши', 'choice'), '动力': ('power', 'Силовая установка', 'choice')}
GROUP_RU = {'六座': ('6 мест', 'второй ряд – два кресла'), '五座': ('5 мест', 'второй ряд – диван')}
HYBRID = {'lynkco-900', 'lynkco-09', 'lynkco-08', 'lynkco-07'}
SHOTS = [{'id': 'hero', 'label': 'Кузов', 'fit': 'contain'}, {'id': 'int', 'label': 'Салон', 'kind': 'int'}]
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def vname(cn, slug):
    """Название версии: латинская часть + число запаса хода; китайские слова – в подпись."""
    if '飞驰' in cn: return 'Feichi', 'Особая серия'
    tag = []
    m = re.match(r'(\d{3})(超长续航|长续航|四驱性能)', cn)
    num = m.group(1) if m else ''
    if m: tag.append(f'{num} км' + (' на электричестве' if slug in HYBRID else ''))
    if '四驱' in cn: tag.append('полный привод')
    if '碳纤维尾翼' in cn: tag.append('карбоновый спойлер')
    lat = ' '.join(re.findall(r'[A-Za-z0-9.+]+', re.sub(r'^\d{3}', '', cn)))
    if '探索版' in cn: lat = (lat + ' Explorer').strip()
    if '碳纤维尾翼' in cn: lat = (lat + ' Carbon').strip()
    name = (lat + (' ' + num if num else '')).strip() or 'Стандартная'
    return name, ', '.join(tag).capitalize() if tag else ''

def curl(url, dst):
    """Скачать картинку как есть (с повторами); True, если файл целый."""
    from PIL import Image
    if os.path.exists(dst) and os.path.getsize(dst) > 800: return True
    if not url: return False
    for a in range(6):
        r = subprocess.run(['curl', '-s', '--max-time', '60', '-A', UA, '-o', dst + '.part', '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout == '200' and os.path.getsize(dst + '.part') > 800:
            try: Image.open(dst + '.part').load()
            except Exception: continue
            os.replace(dst + '.part', dst); return True
    if os.path.exists(dst + '.part'): os.remove(dst + '.part')
    return False

def webp(src, dst, kind):
    from PIL import Image
    if os.path.exists(dst) and os.path.getsize(dst) > 150: return
    im = Image.open(src)
    if kind == 'icon': im = im.convert('RGBA'); im.thumbnail((112, 112)); im.save(dst + '.part', 'WEBP', quality=85, method=4)
    elif kind == 'ext': im = im.convert('RGBA'); im.thumbnail((1400, 1400)); im.save(dst + '.part', 'WEBP', quality=82, method=4)
    else: im = im.convert('RGB'); im.thumbnail((1280, 1280)); im.save(dst + '.part', 'WEBP', quality=80, method=4)
    os.replace(dst + '.part', dst)

def sobrat(proj, car, short, slug):
    import hashlib, shutil
    raw = json.load(open(f'{proj}/raw/lynk-raw.json'))
    IMG = f'img/{slug}'; CACHE = f'{proj}/raw/cache'
    shutil.rmtree(f'{proj}/{IMG}/ext', ignore_errors=True)          # имена кадров зависят от разбора, старые не оставляем
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    cpath = lambda u: f'{CACHE}/{hashlib.md5(u.encode()).hexdigest()}.png'
    # 1. все картинки одним заходом в кэш (сырьё не в репозитории)
    urls = set()
    for v in raw['versions'].values():
        urls |= {x['image'] for x in v['vehicles'] if x.get('image')}
        for a in v['attrs']:
            for x in a['attrs']:
                if x.get('thumbnail'): urls.add(x['thumbnail'])
                if x.get('topImages'): urls.add(x['topImages'][0])
    urls = sorted(urls)
    with ThreadPoolExecutor(6) as ex: got = dict(zip(urls, ex.map(lambda u: curl(u, cpath(u)), urls)))
    print('картинок у производителя', len(urls), 'не скачалось', sum(not g for g in got.values()), flush=True)
    chash = {}
    def content(u):                                                # одинаковые картинки лежат у них под разными адресами
        if u not in chash: chash[u] = hashlib.md5(open(cpath(u), 'rb').read()).hexdigest() if got.get(u) else None
        return chash[u]
    def ru(cn):
        if cn not in RU: raise SystemExit('нет перевода: ' + cn)
        return RU[cn]
    reg = {}                                                       # (группа, китайское имя) -> код опции
    def oid(sku, cn):
        if (sku, cn) not in reg: reg[(sku, cn)] = f'{sku[0]}{len([k for k in reg if k[0] == sku]) + 1}'
        return reg[(sku, cn)]
    tiers = raw['tiers']; leaf = tiers[-1]['list']; parents = {str(l['id']): l for l in (tiers[-2]['list'] if len(tiers) > 2 else [])}
    use_groups = len([p for p in parents.values() if any(str(l['pid']) == str(p['id']) and str(l['id']) in raw['versions'] for l in leaf)]) > 1
    todo, options, vers, have, ints, groups, bad = [], {}, [], {}, [], [], collections.defaultdict(set)
    for l in leaf:
        v = raw['versions'].get(str(l['id']))
        if not v or not v['vehicles']: continue
        pre = f'v{l["id"]}-'
        name, tag = vname(l['name'], slug)
        packs = {str(p['id']): p for p in v['packages']}
        forced = {i for i, p in packs.items() if p.get('type') == 1 and p.get('isForceSelected')}
        free = [i for i, p in packs.items() if p.get('type') == 1 and not p.get('isForceSelected')]
        # машина = атрибуты + выбранные пакеты; берём только те, где обязательные пакеты стоят
        cars = []
        for veh in v['vehicles']:
            at = {a['attrKey']: a['attrVal'] for a in veh['attrs']}
            ps = set(filter(None, (veh.get('packageIdStr') or '').split(',')))
            cars.append((at, ps, veh.get('image')))
        if forced and any(forced <= ps for _, ps, _ in cars): cars = [c for c in cars if forced <= c[1]]
        vals = collections.OrderedDict()
        for at, _, _ in cars:
            for k, x in at.items():
                if x not in vals.setdefault(k, []): vals[k].append(x)
        for k in vals:
            if k not in SKU and k != '配置' and len(vals[k]) > 1: raise SystemExit(f'неизвестная группа выбора: {k} {vals[k]}')
        meta = {a['attrKey']: {x['name']: x for x in a['attrs']} for a in v['attrs']}
        keys = [k for k in vals if k in SKU and (len(vals[k]) > 1 or SKU[k][2] in ('paint', 'wheel', 'int'))]
        # группа, которая целиком следует из другой (крыша из цвета кузова), – не выбор: её не показываем
        for k in [x for x in keys if SKU[x][2] == 'choice']:
            for j in keys:
                if j != k and all(len({at[k] for at, _, _ in cars if at[j] == x}) == 1 for x in vals[j]): keys.remove(k); break
        battr = cars[0][0]
        secs = []
        for k in keys:
            sku, title, role = SKU[k]; ops = []
            order = [x['name'] for x in next(a for a in v['attrs'] if a['attrKey'] == k)['attrs'] if x['name'] in vals[k]] or vals[k]
            for cn in order:
                pc = oid(sku, cn); mt = meta.get(k, {}).get(cn, {})
                icon = f'{IMG}/options/{pc}.webp' if (got.get(mt.get('thumbnail')) and role in ('paint', 'wheel', 'int')) else None
                if icon: todo.append((cpath(mt['thumbnail']), f'{proj}/{icon}', 'icon'))
                options.setdefault(pc, {'name': ru(cn), 'note': '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': sku})
                ops.append({'id': pc, 'def': battr.get(k) == cn, 'promo': False, 'promoTo': ''})
                top = (mt.get('topImages') or [None])[0]
                if role == 'int' and got.get(top):
                    code = pre + pc
                    if code not in ints: ints.append(code); todo.append((cpath(top), f'{proj}/{IMG}/int/{code}--int.webp', 'int'))
            kind = {'paint': 'swatch', 'int': 'swatch', 'wheel': 'option'}.get(role, 'seg')
            secs.append({'sku': sku, 'role': role, 'title': title, 'kind': kind, 'img': 'int' if role == 'int' else 'ext', 'opts': ops})
        # от чего зависит картинка кузова: выкидываем всё, без чего она всё ещё определяется однозначно (сравнение по содержимому)
        rows = [({**{k: at[k] for k in keys}, **{'pk' + i: (i in ps) for i in free}}, content(img)) for at, ps, img in cars if got.get(img)]
        srcs = {tuple(sorted(r.items())): img for (at, ps, img), r in zip([c for c in cars if got.get(c[2])], [r for r, _ in rows])}
        ext_keys = keys + ['pk' + i for i in free]
        prio = {'choice': 1, 'int': 2, 'wheel': 3, 'paint': 4}
        for k in sorted(ext_keys, key=lambda x: 0 if x.startswith('pk') else prio[SKU[x][2]]):
            rest = [x for x in ext_keys if x != k]; seen = {}
            if all(seen.setdefault(tuple(r[x] for x in rest), h) == h for r, h in rows): ext_keys = rest
        if not ext_keys: ext_keys = [keys[0]]                       # у версии одна картинка: код кадра всё равно не пустой
        def code_of(r):
            return pre + '_'.join(c for c in ((('k' + k[2:]) if r[k] else None) if k.startswith('pk') else oid(SKU[k][0], r[k]) for k in ext_keys) if c)
        for r, h in rows:
            code = code_of(r)
            if code not in have: have[code] = ['hero']; todo.append((cpath(srcs[tuple(sorted(r.items()))]), f'{proj}/{IMG}/ext/{code}--hero.webp', 'ext'))
        # несовместимые пары: значения, которые ни в одной сборке версии не встречаются вместе
        for a, b in itertools.combinations(keys, 2):
            together = {(at[a], at[b]) for at, _, _ in cars}
            for x in vals[a]:
                for y in vals[b]:
                    if (x, y) not in together: bad[oid(SKU[a][0], x)].add((l['id'], oid(SKU[b][0], y)))
        extras = []
        for i, p in packs.items():
            pc = 'k' + i; inc = p.get('type') == 4 or i in forced
            options[pc] = {'name': ru(p['name']), 'note': '', 'icon': None, 'mutex': [], 'cascade': [], 'sku': 'pk' + i}
            extras.append({'sku': 'pk' + i, 'role': 'extra', 'title': options[pc]['name'], 'kind': 'check', 'img': 'ext' if ('pk' + i) in ext_keys else '',
                           'opts': [{'id': pc, 'def': inc, 'pre': bool(p.get('isDefaultSelected')) and not inc, 'promo': False, 'promoTo': ''}]})
        extras.sort(key=lambda e: e['opts'][0]['def'])               # сначала то, что можно выбрать
        par = parents.get(str(l['pid']), {})
        gid = str(par.get('id', '')) if use_groups else ''
        if gid and gid not in [g['id'] for g in groups]:
            lab = GROUP_RU.get(par.get('frontName')) or GROUP_RU.get(par.get('name'))
            if not lab: raise SystemExit('нет перевода группы версий: ' + str(par.get('frontName')) + ' / ' + str(par.get('name')))
            groups.append({'id': gid, 'label': lab[0], 'sub': lab[1]})
        rank = {'paint': 0, 'choice': 1, 'wheel': 2, 'int': 3}
        secs.sort(key=lambda s: rank[s['role']])
        vers.append({'id': str(l['id']), 'name': name, 'tag': tag, 'group': gid, 'drive': '', 'level': [], 'secs': secs + extras, 'codePrefix': pre,
                     'vehicleSkus': [k if k.startswith('pk') else SKU[k][0] for k in ext_keys], 'interiorSkus': ['int'], 'ranges': {}})
    # несовместимость общая для опции, только если пара не встречается ни в одной версии, где есть обе опции
    present = {int(v['id']): {o['id'] for s in v['secs'] for o in s['opts']} for v in vers}
    for pc, pairs in bad.items():
        byopt = collections.defaultdict(set)
        for vid, other in pairs: byopt[other].add(vid)
        for other, vids in byopt.items():
            both = [vid for vid, ids in present.items() if pc in ids and other in ids]
            if both and all(vid in vids for vid in both): options[pc]['mutex'].append(other)
            elif any(vid in vids for vid in both): print('ВНИМАНИЕ: пара несовместима не во всех версиях, правило не поставлено:', options[pc]['name'], '/', options[other]['name'], flush=True)
    todo = list({t[1]: t for t in todo}.values())
    with ThreadPoolExecutor(6) as ex: list(ex.map(lambda t: webp(*t), todo))
    data = {'car': car, 'short': short, 'groups': groups, 'versions': vers, 'options': options, 'have': have, 'int': sorted(ints),
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': SHOTS}
    for v in vers:
        for s in v['secs']:
            if s['kind'] == 'swatch' and not all(options[o['id']]['icon'] for o in s['opts']): s['kind'] = 'seg'
        # каждая достижимая сборка версии должна иметь кадр
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор lynkco.com.cn, сняты скриптами tools/lynkco_snyat.py и tools/lynkco.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [(v['name'], v['tag'], v['vehicleSkus']) for v in vers], 'сборок кузова', len(have), 'салонов', len(ints))

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
