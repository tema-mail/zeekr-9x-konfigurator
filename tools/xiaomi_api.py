"""Xiaomi EV -> конфигуратор на общем движке, кадры в полном качестве из официальных слоёв. Цен нет намеренно.
  python3 xiaomi_snyat.py <goodsId> <папка проекта>                         -> raw/xiaomi-api.json
  python3 xiaomi_api.py sobrat <папка проекта> "<Xiaomi SU7>" "<SU7>" <slug>
Готовых кадров Xiaomi не отдаёт: materialV2 даёт слои сцены 5000×2812 и правило их сборки (combinationRule):
фон (у SU7 – вместе с кузовом в цвете), кузов, диски, капот, антикрыло и т. д. Кадр собирается так же, как на их сайте,
и из сцены вырезается машина крупно (у них она занимает треть кадра). Значки цвета, дисков и салона – официальные."""
import json, os, re, sys, subprocess, hashlib, shutil, collections
from concurrent.futures import ThreadPoolExecutor

VIEWS = [('hero', 'front_left_45deg', 'Спереди'), ('side', 'side', 'Сбоку'), ('rear34', 'behind_45deg', 'Сзади'), ('front', 'front', 'Вид спереди'), ('rear', 'behind', 'Вид сзади')]
RU = {
 '卡布里蓝': 'Капри, синий', '赤霞红': 'Алая заря', '雅灰': 'Благородный серый', '靛石绿': 'Индиговый зелёный', '流金粉': 'Золотисто-розовый', '珍珠白': 'Жемчужно-белый',
 '霞光紫': 'Пурпурная заря', '曜石黑': 'Обсидиановый чёрный', '闪电黄': 'Молния, жёлтый', '太空银': 'Космическое серебро', '鹦鹉绿': 'Изумрудный «попугай»',
 '钛金属色': 'Титановый', '车厘子红': 'Вишнёвый красный', '火山灰': 'Вулканический пепел', '宝石绿': 'Изумрудный зелёный',
 '迷雾紫': 'Туманный фиолетовый', '砂陶米': 'Песочно-бежевый', '暮光红': 'Сумеречный красный', '暗夜黑': 'Ночной чёрный',
 '明黄（黄黑双色）': 'Жёлтый с чёрным', '黑黄双色': 'Чёрный с жёлтым', '黑红双色': 'Чёрный с красным', '暮影蓝': 'Сумеречный синий',
 '鸢尾紫（紫灰双色）': 'Ирис: фиолетовый с серым', '松石灰（绿灰双色）': 'Бирюзовый с серым', '珊瑚橙': 'Коралловый оранжевый', '赛道红（红黑双色）': 'Гоночный красный с чёрным', '夜焰黑': 'Чёрный «Ночное пламя»',
 '19英寸钻石轮毂': '19″ «Алмаз»', '20英寸梅花轮毂': '20″ «Слива»', '20英寸米型轮毂': '20″ «Рисовое зерно»', '20英寸锋刃轮毂': '20″ «Лезвие»',
 '21英寸双层锻造梅花轮毂': '21″ кованые «Слива», двухслойные', '20英寸米型轮毂车漆同色轮圈': '20″ «Рисовое зерно», обод в цвет кузова', '21英寸幻刃轮毂': '21″ «Клинок»',
 '21英寸锻造梅花轮毂悬浮车标': '21″ кованые «Слива», парящая эмблема', '21英寸花瓣锻造轮毂悬浮车标': '21″ кованые «Лепесток», парящая эмблема',
 '21英寸五辐双层锻造轮毂碳黑': '21″ кованые пятиспицевые, чёрные', '21英寸五辐双层锻造轮毂镜面银': '21″ кованые пятиспицевые, зеркальное серебро', '21英寸低风阻幻刃轮毂': '21″ «Клинок», аэродинамические',
 '21英寸U型轮毂': '21″ U-образные, чёрные', '21英寸U型轮毂黄轮廓圈': '21″ U-образные с жёлтым кантом', '21英寸U型锻造轮毂石墨黑': '21″ кованые, графит', '21英寸U型锻造轮毂金属钕色': '21″ кованые, неодим', '21英寸U型锻造轮毂金属钕': '21″ кованые, неодим',
}
TYRE = [('长续航胎', 'шины для дальних поездок'), ('高性能胎', 'спортивные шины'), ('运动胎', 'спортивные шины')]
VER = [('选配赛道专业套装', 'Track Package'), ('纽北限量版', 'Nürburgring Limited'), ('标准版', 'Standard'), ('长续航版', 'Long Range')]
# китайский шильдик на крышке багажника: координаты в системе сцены 5000×2812, по модели и виду; закрашивается интерполяцией по строке
MASKS = {
 'xiaomi-su7': {'rear': [(2137, 1378, 2216, 1414)], 'rear34': [(3194, 1443, 3235, 1469)]},
 'xiaomi-yu7': {'rear': [(2100, 1479, 2168, 1513)], 'rear34': [(2858, 1479, 2914, 1505)]},
 'xiaomi-su7-ultra': {'rear': [(2141, 1331, 2217, 1365)], 'rear34': [(2919, 1373, 2977, 1404)]},
}
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
OUT_W, OUT_H = 1600, 1000

def name_ru(cn, role):
    s = re.sub(r'\s+', '', cn); note = ''
    if role == 'wheel':
        for zh, ru in TYRE:
            if zh in s: s = s.replace(zh, ''); note = ru
    if s not in RU: raise SystemExit(f'нет перевода ({role}): {cn}')
    return RU[s], note

def vname(cn, short):
    s = cn.replace(short, '', 1).strip()
    for zh, en in VER: s = s.replace(zh, en)
    s = s.strip() or 'Standard'
    if re.search(r'[㐀-鿿]', s): raise SystemExit('нет перевода версии: ' + cn)
    return s

def curl(url, dst):
    from PIL import Image
    if os.path.exists(dst) and os.path.getsize(dst) > 300: return True
    for a in range(6):
        r = subprocess.run(['curl', '-s', '--max-time', '180', '-A', UA, '-o', dst + '.part', '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout == '200' and os.path.getsize(dst + '.part') > 300:
            try: Image.open(dst + '.part').load()
            except Exception: continue
            os.replace(dst + '.part', dst); return True
    if os.path.exists(dst + '.part'): os.remove(dst + '.part')
    return False

def items_of(cfg):
    """Плоский список опций: (вкладка, группа, опция). У дисков SU7 Ultra опция – родитель с вариантами шин: берём первый вариант."""
    for t in cfg['configurator']['tabList']:
        for g in t['groupList']:
            for sg in g['subGroupList']:
                for i in sg.get('itemList') or []:
                    if 'ssuId' not in i and i.get('itemList'):
                        ch = i['itemList'][0]; img = dict(ch.get('configValueImage') or {}); img.update({k: v for k, v in (i.get('configValueImage') or {}).items() if v})
                        yield t, g, dict(ch, name=i['name'], defaultSelect=any(c.get('defaultSelect') for c in i['itemList']), configValueImage=img, _all=[c['ssuId'] for c in i['itemList']])
                    elif 'ssuId' in i: yield t, g, i

def layers(v, sel, view):
    """Слои кадра по правилу сборки Xiaomi: [(url, x, y, w, h)] снизу вверх."""
    page = v['mat']['pageMap']['CAR_CONFIG_OUTCOMEOUTSIDE_PAGE']; dp = page['dataPool']; out = []
    for rule in page['componentMap']['COLOR_PAGE_OUTCOME']['combinationRule']:
        for el in rule['elementList']:
            ssus = [sel.get(i) for i in el.split(',')]
            if any(s is None for s in ssus): continue
            mv = (dp.get('PC_' + rule['componentId'] + ':' + ':'.join(str(s) for s in ssus)) or {}).get('materialValueList') or []
            for x in mv:
                if x.get('viewIdentityEnum') == view and x.get('payload') and x['width'] > 1: out.append((x['payload'], x['xCoordinate'], x['yCoordinate'], x['width'], x['height']))
    return out

def sobrat(proj, car, short, slug):
    from PIL import Image
    raw = json.load(open(f'{proj}/raw/xiaomi-api.json'))
    IMG = f'img/{slug}'; CACHE = f'{proj}/raw/cache'
    for d in ('ext', 'int', 'options'):                                   # FORCE=1 – пересобрать все кадры (после смены рамки вырезки или координат закраски)
        if os.environ.get('FORCE'): shutil.rmtree(f'{proj}/{IMG}/{d}', ignore_errors=True)
        os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    cpath = lambda u: f'{CACHE}/{hashlib.md5(u.encode()).hexdigest()}.img'
    reg = {}
    def oid(role, cn):
        k = (role, re.sub(r'\s+', '', cn))
        if k not in reg: reg[k] = f'{role[0]}{len([x for x in reg if x[0] == role]) + 1}'
        return reg[k]
    options, vers, have, ints, frames, icons, intjobs, mut = {}, [], {}, [], [], {}, {}, collections.defaultdict(set)
    for vi, v in enumerate(raw['versions']):
        cfg = v['cfg']; pre = f'v{vi}-'; pm = v['mat']['pageMap']
        dflt = dict(cfg['configurator']['defaultConfigSsuInfo']); dflt['0_BB'] = v['ssuId']
        ins = (pm.get('INSIDE_PAGE') or {}).get('dataPool') or {}
        byrole = {'paint': [], 'wheel': [], 'int': []}; ssu2opt = {}
        for t, g, i in items_of(cfg):
            role = {'1_WG': 'paint', '1_LG': 'wheel', '1_NSYS': 'int'}.get(i.get('itemIdentifier'))
            if not role or (role == 'wheel' and 'HalfStyle' in (g.get('groupType'), g.get('groupTag'))): continue        # диски, идущие только пакетом с обвесом, не берём
            byrole[role].append(i)
        views = [(sid, code, lab) for sid, code, lab in VIEWS if code in (v['mat']['pageConfig'].get('outside') or {}).get('viewList', [])]
        # диск берём, только если для него есть слой с каждым цветом
        def has_pair(w, p):
            sel = dict(dflt, **{'1_WG': p['ssuId'], '1_LG': w['ssuId']}); no = dict(sel); no.pop('1_LG')
            return len(layers(v, sel, 'side')) > len(layers(v, no, 'side'))
        def has_wheel(w): return any(has_pair(w, p) for p in byrole['paint'])       # диск берём, если слой есть хотя бы с одним цветом
        byrole['wheel'] = [w for w in byrole['wheel'] if has_wheel(w)]
        secs = []
        for role, title, kind, img in (('paint', 'Цвет кузова', 'swatch', 'ext'), ('wheel', 'Диски', 'option', 'ext'), ('int', 'Цвет салона', 'swatch', 'int')):
            ops = []
            for i in byrole[role]:
                pc = oid(role, i['name']); nm, note = name_ru(i['name'], role); ssu2opt[i['ssuId']] = pc
                for s in i.get('_all') or []: ssu2opt[s] = pc
                ci = i.get('configValueImage') or {}; iu = ci.get('mainUrl') or ci.get('bigSaleAttrImage') or ci.get('rectangleIconImg')
                icon = f'{IMG}/options/{pc}.webp' if iu else None
                if iu: icons[f'{proj}/{icon}'] = iu
                options.setdefault(pc, {'name': nm, 'note': note, 'icon': icon, 'mutex': [], 'cascade': [], 'sku': role})
                ops.append({'id': pc, 'def': bool(i.get('defaultSelect')) or dflt.get(i.get('itemIdentifier')) in ([i['ssuId']] + (i.get('_all') or [])), 'promo': False, 'promoTo': ''})
                if role == 'int':
                    mv = {x.get('viewIdentityEnum'): x['payload'] for x in (ins.get(f'PC_INSIDE_CAR_CONFIG_OUTCOME_CROPPING:{i["ssuId"]}') or {}).get('materialValueList') or [] if x.get('width', 0) > 1}   # 1×1 – заглушка
                    a, b = mv.get('2d_frontRow_DRIVER') or mv.get('2d_frontRow_PAX'), mv.get('2d_backRow_CNTR')
                    if a:
                        code = pre + pc; ints.append(code); intjobs[f'{proj}/{IMG}/int/{code}--int.webp'] = a
                        if b: intjobs[f'{proj}/{IMG}/int/{code}--int2.webp'] = b
            if ops:
                if not any(o['def'] for o in ops): ops[0]['def'] = True
                secs.append({'sku': role, 'role': role, 'title': title, 'kind': kind, 'img': img, 'opts': ops})
        for role in byrole:                                                  # несовместимости – из данных Xiaomi (mutexMap)
            for i in byrole[role]:
                for lst in (i.get('mutexMap') or {}).values():
                    for s in lst:
                        if s in ssu2opt and ssu2opt[s] != ssu2opt[i['ssuId']]: mut[frozenset((ssu2opt[i['ssuId']], ssu2opt[s]))].add(vi)
        for p in byrole['paint']:
            for w in byrole['wheel']:
                if not has_pair(w, p): mut[frozenset((oid('paint', p['name']), oid('wheel', w['name'])))].add(vi); continue      # такого сочетания у Xiaomi нет
                code = pre + oid('paint', p['name']) + '_' + oid('wheel', w['name']); sel = dict(dflt, **{'1_WG': p['ssuId'], '1_LG': w['ssuId']}); got = []
                for sid, vcode, lab in views:
                    ls = layers(v, sel, vcode)
                    if len(ls) >= 2 or (ls and ls[0][3] >= 4000): frames.append((f'{proj}/{IMG}/ext/{code}--{sid}.webp', sid, ls, layers(v, sel, vcode))); got.append(sid)
                if 'hero' in got: have[code] = got
        at = {a.get('identityEnum'): a.get('attributeValueName') for a in cfg.get('attributeList') or []}
        tag = ', '.join(x for x in ((at['3_CTLC'] + ' км (CLTC)') if at.get('3_CTLC') else '', (at['3_power'] + ' л. с.') if at.get('3_power') else '') if x)
        vers.append({'id': f'v{vi}', 'name': vname(cfg['name'], short), 'tag': tag, 'group': '', 'drive': '', 'level': [], 'secs': secs, 'codePrefix': pre,
                     'vehicleSkus': ['paint', 'wheel'], 'interiorSkus': ['int'], 'ranges': {}})
    present = {i: {o['id'] for sc in v['secs'] for o in sc['opts']} for i, v in enumerate(vers)}
    for pair, vids in mut.items():                                           # правило общее, только если действует во всех версиях, где есть обе опции
        a, b = sorted(pair); both = [i for i, ids in present.items() if a in ids and b in ids]
        if options[a]['sku'] == options[b]['sku']: continue
        if all(i in vids for i in both): options[a]['mutex'].append(b); options[b]['mutex'].append(a)
        else: print('ВНИМАНИЕ: пара несовместима не во всех версиях, правило не поставлено:', options[a]['name'], '/', options[b]['name'], flush=True)
    # скачать слои
    urls = sorted({l[0] for f in frames for l in f[2]} | set(icons.values()) | set(intjobs.values()))
    with ThreadPoolExecutor(6) as ex: got = dict(zip(urls, ex.map(lambda u: curl(u, cpath(u)), urls)))
    print('слоёв и значков', len(urls), 'не скачалось', sum(not g for g in got.values()), flush=True)
    # рамка вырезки на вид: по слою дисков первой сборки (центр по горизонтали, колёса на 2/3 высоты), ширина одна на модель
    sl = [l for f in frames if f[1] == 'side' for l in f[2] if l[3] < 4000]
    mw = max(l[3] for l in sl); body = max(l[4] for l in sl) >= 400            # есть отдельный слой кузова (YU7, Ultra) или только диски (SU7)
    W = int(mw * (1.25 if body else 1.55))
    H = int(W * OUT_H / OUT_W); boxes = {}
    for dst, sid, ls, _ in frames:
        if sid in boxes: continue
        parts = [l for l in ls if l[3] < 4000]
        x0 = min(l[1] for l in parts); x1 = max(l[1] + l[3] for l in parts); y1 = max(l[2] + l[4] for l in parts)
        cx = (x0 + x1) // 2; bx = max(0, min(5000 - W, cx - W // 2)); by = max(0, min(2812 - H, int(y1 - H * 0.68)))
        boxes[sid] = (bx, by, bx + W, by + H)
    print('рамки вырезки', boxes, flush=True)
    if slug not in MASKS: raise SystemExit('нет координат надписей для ' + slug + ': посмотреть корму и добавить в MASKS (можно пустой список)')
    masks = MASKS[slug]
    done = {}
    def make(fr):
        dst, sid, ls, _ = fr; sig = (sid,) + tuple(l[0] for l in ls)
        if sig in done: return
        done[sig] = dst; box = boxes[sid]; canvas = None
        if os.path.exists(dst) and os.path.getsize(dst) > 300: return
        for u, x, y, w, h in ls:
            if not got.get(u): return
            im = Image.open(cpath(u))
            if im.size != (w, h): im = im.resize((w, h), Image.LANCZOS)
            if canvas is None:
                canvas = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), (20, 20, 20))
            im = im.convert('RGBA'); canvas.paste(im, (x - box[0], y - box[1]), im)
        px = canvas.load()
        for x0, y0, x1, y1 in masks.get(sid, []):
            x0 -= box[0]; x1 -= box[0]; y0 -= box[1]; y1 -= box[1]
            for y in range(y0, y1):
                l = px[x0 - 2, y]; r = px[x1 + 2, y]
                for x in range(x0, x1):
                    t = (x - x0) / max(1, x1 - x0); px[x, y] = tuple(int(l[i] + (r[i] - l[i]) * t) for i in range(3))
        canvas.resize((OUT_W, OUT_H), Image.LANCZOS).save(dst + '.part', 'WEBP', quality=86, method=4); os.replace(dst + '.part', dst)
    uniq = {}
    for fr in frames: uniq.setdefault((fr[1],) + tuple(l[0] for l in fr[2]), fr)
    with ThreadPoolExecutor(4) as ex: list(ex.map(make, uniq.values()))
    for dst, sid, ls, _ in frames:                                           # одинаковые сборки разных версий – копией
        src = done.get((sid,) + tuple(l[0] for l in ls))
        if src and src != dst and os.path.exists(src) and not os.path.exists(dst): shutil.copyfile(src, dst)
    def small(item, size, q):
        dst, u = item
        if not got.get(u) or (os.path.exists(dst) and os.path.getsize(dst) > 300): return
        im = Image.open(cpath(u)); im = im.convert('RGBA' if size[0] < 200 else 'RGB'); im.thumbnail(size); im.save(dst + '.part', 'WEBP', quality=q, method=4); os.replace(dst + '.part', dst)
    for it in icons.items(): small(it, (112, 112), 88)
    for it in intjobs.items(): small(it, (1600, 1600), 84)
    keep = {f[0] for f in frames} | set(icons) | set(intjobs)                 # кадры от прежних сборок, которых больше нет в данных, убираем
    for d in ('ext', 'int', 'options'):
        for fn in os.listdir(f'{proj}/{IMG}/{d}'):
            if f'{proj}/{IMG}/{d}/{fn}' not in keep: os.remove(f'{proj}/{IMG}/{d}/{fn}')
    ex_ = os.path.exists
    have = {c: [s for s in ss if ex_(f'{proj}/{IMG}/ext/{c}--{s}.webp')] for c, ss in have.items()}
    have = {c: ss for c, ss in have.items() if 'hero' in ss}
    ints = sorted(c for c in set(ints) if ex_(f'{proj}/{IMG}/int/{c}--int.webp'))
    two = all(ex_(f'{proj}/{IMG}/int/{c}--int2.webp') for c in ints)
    for o in options.values():
        if o['icon'] and not ex_(f'{proj}/{o["icon"]}'): o['icon'] = None
    used = [sid for sid, _, _ in VIEWS if any(sid in ss for ss in have.values())]
    shots = [{'id': sid, 'label': lab, 'fit': 'cover'} for sid, _, lab in VIEWS if sid in used] + [{'id': 'int', 'label': 'Салон', 'kind': 'int'}] + ([{'id': 'int2', 'label': 'Второй ряд', 'kind': 'int'}] if two else [])
    for v in vers:
        by = {s['sku']: s for s in v['secs']}
        miss = [c for c in (v['codePrefix'] + p['id'] + '_' + w['id'] for p in by['paint']['opts'] for w in by['wheel']['opts'] if w['id'] not in options[p['id']]['mutex']) if c not in have]
        if miss: print(f'ВНИМАНИЕ: {v["name"]} – нет кадра для {len(miss)} сборок:', miss[:6], flush=True)
    data = {'car': car, 'short': short, 'groups': [], 'versions': vers, 'options': options, 'have': have, 'int': ints,
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': shots}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор xiaomiev.com, сняты скриптами tools/xiaomi_snyat.py и tools/xiaomi_api.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [(v['name'], [(s['title'], len(s['opts'])) for s in v['secs']]) for v in vers], 'сборок кузова', len(have), 'видов', used, 'салонов', len(ints), 'несовместимости', {k: o['mutex'] for k, o in options.items() if o['mutex']})

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
