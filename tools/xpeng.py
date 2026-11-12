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
 # кузов (в списке цветов у Xpeng стоят и пакеты оформления)
 '星云白': 'Белый «Туманность»', '暗夜黑': 'Чёрный «Ночь»', '星暮紫': 'Фиолетовый «Звёздные сумерки»', '星昼灰': 'Серый «Звёздный день»', '星际绿': 'Зелёный «Межзвёздный»',
 '新月银（哑光）': 'Серебристый «Новолуние», матовый', '哑光新月银': 'Серебристый «Новолуние», матовый', '托斯卡纳绿': 'Зелёный «Тоскана»', '普罗旺斯紫': 'Фиолетовый «Прованс»',
 '黑金套件': 'Пакет «Чёрное золото»', '极夜黑': 'Чёрный «Полярная ночь»', '黑武士套件': 'Пакет «Чёрный воин»', '黑武士套装': 'Пакет «Чёрный воин»', '星云紫': 'Фиолетовый «Туманность»',
 '星舰灰(哑光)': 'Серый «Звездолёт», матовый', '极光青': 'Бирюзовый «Аврора»', '律动黄': 'Жёлтый «Ритм»', '星瀚绿': 'Зелёный «Галактика»', '微星灰': 'Серый «Звёздная пыль»',
 '星芒蓝': 'Синий «Сияние звёзд»', '暗夜骑士套装': 'Пакет «Тёмный рыцарь»', '星曜骑士套装': 'Пакет «Звёздный рыцарь»', '星阙灰': 'Серый «Звёздные врата»', '星镜蓝': 'Синий «Звёздное зеркало»',
 '罗兰紫': 'Фиолетовый «Фиалка»', '牛油果绿': 'Зелёный «Авокадо»', '微月灰': 'Серый «Полумесяц»', '樱珞粉主题套装': 'Тема «Розовая сакура»', '罗兰紫主题套装': 'Тема «Фиалка»',
 '牛油果绿主题套装': 'Тема «Авокадо»', '星瀚米': 'Бежевый «Галактика»', '极光紫': 'Фиолетовый «Аврора»', '乌梅子酱': 'Сливовый «Умэ»', '尤加利灰': 'Серо-зелёный «Эвкалипт»',
 '新月银ROAM主题套装': 'Тема ROAM, серебристый «Новолуние»', '极光紫ROAM主题套装': 'Тема ROAM, фиолетовый «Аврора»', '乌梅子酱ROAM主题套装': 'Тема ROAM, сливовый «Умэ»',
 '星暮紫ROAM主题套装': 'Тема ROAM, фиолетовый «Звёздные сумерки»', '仙踪绿ROAM主题套装': 'Тема ROAM, зелёный «Волшебный лес»', '罗兰紫ROAM主题套装': 'Тема ROAM, фиолетовый «Фиалка»',
 '微月灰ROAM主题套装': 'Тема ROAM, серый «Полумесяц»', '晶曜黑': 'Чёрный «Кристалл»', '仙踪绿': 'Зелёный «Волшебный лес»',
 # салон
 '气宇灰': 'Серый «Воздух»', '深空灰': 'Тёмно-серый «Космос»', '秘境蓝': 'Синий «Тайный край»', '暖阳橙': 'Оранжевый «Тёплое солнце»', '月影咖': 'Кофейный «Лунная тень»',
 '晨辉棕': 'Коричневый «Утренний свет»', '撒哈拉橙': 'Оранжевый «Сахара»', '波尔多红': 'Красный «Бордо»', '陨石黑': 'Чёрный «Метеорит»', '云间玫棕': 'Розово-коричневый «Облака»',
 '星球紫': 'Фиолетовый «Планета»', '引力红': 'Красный «Гравитация»', '熔岩灰': 'Серый «Лава»', '橙耀灰': 'Серый с оранжевым', '柔光紫': 'Фиолетовый «Мягкий свет»', '晨雾蓝': 'Голубой «Утренний туман»',
 '晨雾灰': 'Серый «Утренний туман»', '夜幕灰': 'Тёмно-серый «Ночь»', '拂晓紫': 'Фиолетовый «Рассвет»', '维奥拉紫': 'Фиолетовый «Виола»', '樱雾粉': 'Розовый «Сакура»',
 '星脉紫': 'Фиолетовый «Звёздный»', '鸢尾紫': 'Фиолетовый «Ирис»', '钛荧绿': 'Зелёный «Титан»',
 # диски
 '18英寸低风阻轮毂': '18″ аэродинамические', '19英寸低风阻轮毂': '19″ аэродинамические', '20英寸低风阻轮毂': '20″ аэродинамические', '20英寸五辐轮毂': '20″ пятиспицевые',
 '黑武士升级套装': 'Диски пакета «Чёрный воин»', '月光骑士升级套装': 'Диски пакета «Лунный рыцарь»', '20英寸运动轮毂': '20″ спортивные', '21英寸多辐轮毂': '21″ многоспицевые',
 '21英寸漩涡轮毂': '21″ «Вихрь»', '22英寸花瓣运动轮毂': '22″ спортивные «Лепестки»', '22英寸黑金轮毂': '22″ «Чёрное золото»', '19英寸星云低风阻轮毂': '19″ «Туманность», аэродинамические',
 '20英寸星耀悬浮轮毂': '20″ «Звёздный блеск», парящая эмблема', '20英寸星刃运动轮毂': '20″ спортивные «Звёздный клинок»', '20英寸六辐运动轮毂': '20″ спортивные шестиспицевые',
 '21英寸锻造轮毂': '21″ кованые', '21英寸哑灰锻造轮毂': '21″ кованые, матовые серые', '19英寸六辐亮面运动轮毂': '19″ спортивные шестиспицевые, полированные',
 '19英寸六辐熏黑运动轮毂': '19″ спортивные шестиспицевые, тёмные', '19英寸五辐樱珞粉轮毂': '19″ пятиспицевые, розовые', '19英寸五辐罗兰紫轮毂': '19″ пятиспицевые, фиолетовые',
 '19英寸五辐牛油果绿轮毂': '19″ пятиспицевые, зелёные', '20英寸五辐运动轮毂': '20″ спортивные пятиспицевые', '20英寸ROAM轮毂（乌梅子酱）': '20″ ROAM, сливовые', '20英寸ROAM轮毂（紫色）': '20″ ROAM, фиолетовые',
 '20英寸ROAM轮毂套装（仙踪绿）': '20″ ROAM, зелёные', '20英寸ROAM轮毂套装（罗兰紫）': '20″ ROAM, фиолетовые', '20英寸ROAM轮毂套装（微月灰）': '20″ ROAM, серые',
 # опции
 'Ultra SE智能升级包': 'Пакет умных функций Ultra SE', 'Ultra智能升级包': 'Пакет умных функций Ultra', '副驾零重力座椅': 'Кресло пассажира «невесомость»', '二排娱乐屏': 'Экран для второго ряда',
 '主副驾AI座椅套装': 'Пакет умных кресел водителя и пассажира', '智能电动行政中岛': 'Электрическая консоль второго ряда', '星舰尾翼': 'Спойлер «Звездолёт»', '座舱舒享套装': 'Пакет «Комфорт салона»',
 '电动升降尾翼': 'Выдвижной спойлер', '前排无框车门': 'Безрамочные передние двери', '前排14点云朵按摩座椅': 'Передние кресла с массажем, 14 точек', '前排座椅14点云朵按摩': 'Передние кресла с массажем, 14 точек',
 '20扬声器高级定制音响': 'Аудиосистема, 20 динамиков', 'RNC主动降噪模块': 'Активное шумоподавление RNC', 'AI智能底盘': 'Умное шасси с ИИ', '前排座椅升级套装': 'Пакет улучшенных передних кресел',
 '后排17.3英寸娱乐屏套装': 'Экран 17,3″ для задних пассажиров',
}
ROLE = {1: ('paint', 'Цвет кузова'), 4: ('wheel', 'Диски'), 2: ('int', 'Цвет салона')}
EXTRA_TYPES = (3, 6)
GROUP_RU = {'超级增程': ('Гибрид', 'с бензиновым генератором'), '纯电': ('Электро', ''), '四驱': ('Полный привод', ''), '后驱': ('Задний привод', '')}
VER = [('旗舰版', 'Flagship'), ('科技版', 'Tech'), ('超长续航', ''), ('长续航', ''), ('四驱', '')]
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def ru(cn):
    if cn not in RU: raise SystemExit('нет перевода: ' + cn)
    return RU[cn]

def vname(cn):
    m = re.match(r'\s*(\d{3,4})\s*', cn); km = m.group(1) if m else ''; s = cn[m.end():] if m else cn
    wing = '鹏翼' in s; s = s.replace('鹏翼', ' ')                      # версия с дверями-крыльями
    for zh, en in VER: s = s.replace(zh, ' ' + en + ' ')
    s = ' '.join(s.split()) + (' Wing' if wing else '')
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

# Экраны с читаемым китайским текстом закрашиваем как выключенные: модель → вид → многоугольники в координатах готового кадра.
# У G9 на экране пассажира магазин игр с крупной надписью иероглифами.
MASKS = {'xpeng-g9': {'int': [[(1423, 307), (1536, 313), (1480, 437), (1391, 411)]], 'int2': [[(951, 373), (1242, 373), (1258, 520), (951, 520)]]}}
def zakrasit(im, poly, color=(15, 16, 19)):
    from PIL import Image, ImageDraw
    k = 4; m = Image.new('L', (im.width * k, im.height * k), 0)
    ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in poly], fill=255)
    im = im.convert('RGB'); im.paste(Image.new('RGB', im.size, color), (0, 0), m.resize(im.size, Image.LANCZOS)); return im

def gruppy(raw):
    """Группы версий. У серий с гибридом и электро vgroups – список групп с carYearsList; у остальных – сразу список версий-годов."""
    vg = raw['vgroups']
    if vg and 'carYearsList' in vg[0]: return vg
    return [{'carYearTypeName': '', 'carYearsList': vg}]

def sobrat(proj, car, short, slug):
    from PIL import Image
    raw = json.load(open(f'{proj}/raw/xpeng-raw.json'))
    IMG = f'img/{slug}'; CACHE = f'{proj}/raw/cache'
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    cpath = lambda u: f'{CACHE}/{hashlib.md5(u.encode()).hexdigest()}.img'
    first = lambda lst: (lst or [{}])[0].get('url')
    order = [(g, y, v) for g in gruppy(raw) for y in g['carYearsList'] for v in y['carVersionList'] if v['carVersionCode'] in raw['specs']]
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
    # Салон: у части версий производитель не даёт фото отделки или кладёт не ту панораму (у L03 – вид на панель вместо второго ряда).
    # Фото берём у той же отделки из соседней версии, одиночную панораму, не похожую на остальные, заменяем типичной.
    byname = collections.defaultdict(lambda: collections.defaultdict(list)); swap = {}
    for vi, (g, y, v) in enumerate(order):
        for gr in raw['specs'][v['carVersionCode']]:
            if gr['carSpecificationGroupType'] != 2: continue
            for s in gr['specList']:
                for k in ('pcImgList', 'frontPanoramaList', 'backPanoramaList'):
                    if got.get(first(s.get(k))): byname[s['carSpecificationName']][k].append((vi, first(s.get(k))))
    import statistics
    for k in ('pcImgList', 'frontPanoramaList', 'backPanoramaList'):     # рисунок кадра (где окна, где кресла) у всех отделок модели один; чужой кадр выбивается
        allu = sorted({u for kinds in byname.values() for _, u in kinds[k]})
        if len(allu) < 3: continue
        t = {}
        for u in allu:
            px = list(Image.open(cpath(u)).convert('L').resize((32, 16)).tobytes()); mu = sum(px) / 512; sd = (sum((x - mu) ** 2 for x in px) / 512) ** .5 or 1
            t[u] = [(x - mu) / sd for x in px]
        like = {u: statistics.median(sum(x * z for x, z in zip(t[u], t[o])) / 512 for o in allu if o != u) for u in allu}
        for nm, kinds in byname.items():
            for vi, u in kinds[k]:
                if like[u] >= 0.5 or u in swap: continue
                good = [(i, x) for i, x in kinds[k] if like[x] >= 0.5]
                swap[u] = min(good, key=lambda x: abs(x[0] - vi))[1] if good else None
                print(f'  салон {ru(nm)}, {k}: у версий {[i for i, x in kinds[k] if x == u]} чужой кадр (похожесть {like[u]:.2f})' + (', взят кадр той же отделки из другой версии' if good else ', ЗАМЕНЫ НЕТ – кадр убран'), flush=True)
    def pic(s, k, vi):
        u = first(s.get(k))
        if got.get(u): return swap[u] if u in swap else u
        lst = byname[s['carSpecificationName']][k] if k == 'pcImgList' else []
        return min(lst, key=lambda x: abs(x[0] - vi))[1] if lst else None
    reg = {}
    def oid(letter, cn):
        if (letter, cn) not in reg: reg[(letter, cn)] = f'{letter}{len([k for k in reg if k[0] == letter]) + 1}'
        return reg[(letter, cn)]
    todo, options, vers, have, ints, groups, bad = {}, {}, [], {}, [], [], collections.defaultdict(set)
    multi = len(gruppy(raw)) > 1
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
                code_ = s['carSpecificationCode']
                if not any(r[0][gc] == code_ for r in rows): continue
                sh = oid(role[0], s['carSpecificationName']); pc = f'{sh}v{vi}'; iu = first(s.get('iconList'))   # код опции свой у каждой версии: правила совместимости у версий разные
                icon = f'{IMG}/options/{sh}.webp' if got.get(iu) else None
                if icon: todo[f'{proj}/{icon}'] = ('icon', cpath(iu))
                options.setdefault(pc, {'name': ru(s['carSpecificationName']), 'note': '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': role})
                old = next((o for o in ops if o['id'] == pc), None)                 # одно название под двумя кодами (у P7 салон с креслом «невесомость» и без) – один вариант
                if old: old['_c'].add(code_); old['def'] = old['def'] or bool(s.get('isDefault'))
                else: ops.append({'id': pc, 'def': bool(s.get('isDefault')), 'promo': False, 'promoTo': '', '_c': {code_}})
                if role == 'int':
                    a, fp, bp = pic(s, 'pcImgList', vi), pic(s, 'frontPanoramaList', vi), pic(s, 'backPanoramaList', vi)
                    if got.get(a):
                        ic = pre + pc; ints.append(ic); todo[f'{proj}/{IMG}/int/{ic}--int.webp'] = ('int', cpath(a))
                        if got.get(fp): todo[f'{proj}/{IMG}/int/{ic}--int2.webp'] = ('pano', cpath(fp))
                        if got.get(bp): todo[f'{proj}/{IMG}/int/{ic}--int3.webp'] = ('pano', cpath(bp))
            if ops and not any(o['def'] for o in ops): ops[0]['def'] = True
            secs.append({'sku': role, 'role': role, 'title': title, 'kind': 'option' if role == 'wheel' else 'swatch', 'img': 'int' if role == 'int' else 'ext', 'opts': ops, '_g': gc})
        c2o = {c: o['id'] for sc in secs for o in sc['opts'] for c in o['_c']}
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
        # показываем только то, для чего у производителя есть кадр: цвет или диск без единой картинки убираем, пару без картинки запрещаем
        mine = [set(fc[len(pre):].split('_')) for fc in have if fc.startswith(pre)]; used = set().union(*mine) if mine else set()
        vis = [sc for sc in secs if sc['_g'] in ext_keys]
        for sc in vis:
            gone = [options[o['id']]['name'] for o in sc['opts'] if o['id'] not in used]
            if gone: print(f'  {v["carVersionName"][:20]}: нет кадров, убрано из выбора:', sc['title'], gone, flush=True)
            sc['opts'] = [o for o in sc['opts'] if o['id'] in used]
            if sc['opts'] and not any(o['def'] for o in sc['opts']): sc['opts'][0]['def'] = True
        for a, b in itertools.combinations(vis, 2):
            for x in a['opts']:
                for y_ in b['opts']:
                    if not any(x['id'] in m and y_['id'] in m for m in mine): bad[frozenset((x['id'], y_['id']))].add(vi)
        # опция и вариант: у производителя вариант бывает только с опцией (need) или только без неё (запрет)
        for e in free:
            ec = e['carSpecificationCode']
            for sc in secs:
                for o in sc['opts']:
                    rs = [r[1][ec] for r in rows if r[0][sc['_g']] in o['_c']]
                    if rs and all(rs): options[o['id']].setdefault('need', []).append(xid[ec])
                    elif rs and not any(rs): bad[frozenset((o['id'], xid[ec]))].add(vi)
        for e1, e2 in itertools.combinations(free, 2):                                     # две опции, которых у производителя нет вместе (пакеты Ultra и Ultra SE)
            if not any(r[1][e1['carSpecificationCode']] and r[1][e2['carSpecificationCode']] for r in rows): bad[frozenset((xid[e1['carSpecificationCode']], xid[e2['carSpecificationCode']]))].add(vi)
        for a, b in itertools.combinations(secs, 2):
            together = {(c2o[r[0][a['_g']]], c2o[r[0][b['_g']]]) for r in rows}
            for x in a['opts']:
                for y_ in b['opts']:
                    if (x['id'], y_['id']) not in together: bad[frozenset((x['id'], y_['id']))].add(vi)
        extras = []
        for e in included + free:
            pc = xid[e['carSpecificationCode']]; inc = e in included
            options[pc] = {'name': ru(e['carSpecificationName']), 'note': '', 'icon': None, 'mutex': [], 'cascade': [], 'sku': 'pk' + pc[1:]}
            extras.append({'sku': 'pk' + pc[1:], 'role': 'extra', 'title': options[pc]['name'], 'kind': 'check', 'img': 'ext' if e['carSpecificationCode'] in ext_keys else '',
                           'opts': [{'id': pc, 'def': inc, 'pre': (not inc) and bool(e.get('isDefault')), 'promo': False, 'promoTo': ''}]})
        extras.sort(key=lambda e: e['opts'][0]['def'])
        name, awd = vname(v['carVersionName'])
        tags = {t.get('title'): t.get('number') for t in json.loads(y.get('tagTitle') or '[]') if isinstance(t, dict)}
        km = re.match(r'\s*(\d{3,4})', v['carVersionName']); ev = next((n for t, n in tags.items() if t and '纯电续航' in t), None)
        total = int(km.group(1)) if km else next((n for t, n in tags.items() if t and '续航里程' in t and '纯电' not in t), None)
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
    gtitle = 'Привод' if any(x['id'] in ('四驱', '后驱') for x in groups) else 'Силовая установка'
    gid2ru = {x['id']: f'g{n + 1}' for n, x in enumerate(groups)}                       # в данных не должно остаться иероглифов
    for x in groups: x['id'] = gid2ru[x['id']]
    for v in vers: v['group'] = gid2ru.get(v['group'], '')
    present = {i: {o['id'] for sc in v['secs'] for o in sc['opts']} for i, v in enumerate(vers)}
    for pair, vids in bad.items():
        a, b = sorted(pair); both = [i for i, ids in present.items() if a in ids and b in ids]
        if both and all(i in vids for i in both): options[a]['mutex'].append(b); options[b]['mutex'].append(a)
        elif any(i in vids for i in both): print('ВНИМАНИЕ: пара несовместима не во всех версиях, правило не поставлено:', options[a]['name'], '/', options[b]['name'], flush=True)
    for v in vers:                                                   # у каждой отделки, которую можно выбрать, должна быть картинка
        noint = [options[o['id']]['name'] for sc in v['secs'] if sc['role'] == 'int' for o in sc['opts'] if v['codePrefix'] + o['id'] not in ints]
        if noint: raise SystemExit(f'{v["name"]}: у отделки салона нет картинки: {noint}')
    for k, o in options.items():
        both_ = set(o.get('need', [])) & set(o['mutex'])
        if both_: raise SystemExit(f'опция {k} {o["name"]}: одновременно требует и исключает {both_}')
    for v in vers:
        ids_ = [o['id'] for sc in v['secs'] for o in sc['opts']]
        if len(ids_) != len(set(ids_)): raise SystemExit(f'{v["name"]}: вариант повторяется в списке: ' + ', '.join(sorted({i for i in ids_ if ids_.count(i) > 1})))
        by = {sc['sku']: sc for sc in v['secs']}
        lists = [[o['id'] for o in by[k]['opts']] + ([None] if by[k]['role'] == 'extra' and not by[k]['opts'][0]['def'] else []) for k in v['vehicleSkus'] if k in by]
        allc = [c for c in itertools.product(*lists) if not any(b in options[a]['mutex'] for a, b in itertools.permutations([x for x in c if x], 2))
                and all(n in c for x in c if x for n in options[x].get('need', []) if 'pk' + n[1:] in v['vehicleSkus'])]
        miss = [c for c in (v['codePrefix'] + '_'.join(x for x in combo if x) for combo in allc) if c not in have]
        left = []
        for c in miss:                                               # нет кадра с опцией – берём кадр той же сборки без неё
            base = v['codePrefix'] + '_'.join(t for t in c[len(v['codePrefix']):].split('_') if not t.startswith('k'))
            if base in have and base != c:
                have[c] = list(have[base])
                for n in have[base]: todo[f'{proj}/{IMG}/ext/{c}--{n}.webp'] = todo[f'{proj}/{IMG}/ext/{base}--{n}.webp']
            else: left.append(c)
        if miss: print(f'  {v["name"]}: у {len(miss) - len(left)} сборок с опцией нет своего кадра, показан кадр без опции', flush=True)
        if left: print(f'ВНИМАНИЕ: {v["name"]} – нет кадра для {len(left)} сборок из {len(allc)}:', left[:6], flush=True)
    boxes = {}
    for dst, job in todo.items():
        if job[0] != 'ext': continue
        bb = Image.open(job[1]).convert('RGBA').getbbox(); b = boxes.get(job[2])
        boxes[job[2]] = bb if not b else (min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3]))
    def make(item):
        dst, job = item
        if not os.environ.get('FORCE') and os.path.exists(dst) and os.path.getsize(dst) > 300: return   # FORCE=1 – пересобрать все кадры (нужно, когда у кадра сменился источник)
        masks = MASKS.get(slug, {}).get(dst.rsplit('--', 1)[1].split('.')[0], []) if job[0] in ('pano', 'int') else []
        if job[0] == 'pano':
            im = vid_vpered(job[1])
            for poly in masks: im = zakrasit(im, poly)
            im.save(dst + '.part', 'WEBP', quality=84, method=4)
        else:
            im = Image.open(job[1])
            if job[0] == 'icon': im = im.convert('RGBA'); im.thumbnail((112, 112)); im.save(dst + '.part', 'WEBP', quality=88, method=4)
            elif job[0] == 'int':
                im = im.convert('RGB'); im.thumbnail((1600, 1600))
                for poly in masks: im = zakrasit(im, poly)
                im.save(dst + '.part', 'WEBP', quality=84, method=4)
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
    data = {'car': car, 'short': short, 'groups': groups, 'groupsTitle': gtitle, 'versions': vers, 'options': options, 'have': have, 'int': ints,
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': shots}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор store.xiaopeng.com, сняты скриптами tools/xpeng_snyat.py и tools/xpeng.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [(v['name'], v['tag'], v['group'], v['vehicleSkus']) for v in vers], 'сборок кузова', len(have), 'салонов', len(ints), 'видов', [s['id'] for s in shots])

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:6])
