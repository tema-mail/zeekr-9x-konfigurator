"""Xiaomi (xiaomiev.com) -> конфигуратор на общем движке. Цен нет намеренно.
Кадры и переводы берутся из проекта сайта ~/Documents/evolution-car-by (сняты 17.10.2026 с официального конфигуратора
Xiaomi EV: кадр собран из слоёв сцены – фон, кузов в цвете, диски). Сайт Xiaomi с сервера в Нидерландах не открывается.
  node --input-type=module -e "…import('<проект>/src/content/models/xiaomi-su7-config.ts')…" > raw/xiaomi-raw.json   (см. xiaomi-model.sh)
  python3 xiaomi.py sobrat <папка проекта> "<Xiaomi SU7>" "<SU7>" <slug> <папка img модели в проекте сайта>"""
import json, os, re, sys, shutil
from PIL import Image
SHOTS = [{'id': 'hero', 'label': 'Сбоку', 'fit': 'cover'}, {'id': 'front34', 'label': 'Спереди'}, {'id': 'rear34', 'label': 'Сзади'},
         {'id': 'int', 'label': 'Салон', 'kind': 'int'}, {'id': 'int2', 'label': 'Второй ряд', 'kind': 'int'}]
SRC_SHOT = {'hero': 'side', 'front34': 'front', 'rear34': 'rear', 'int': 'dash', 'int2': 'rear-seats'}
oid = lambda s: s.replace('-', '')

def sobrat(proj, car, short, slug, src):
    raw = json.load(open(f'{proj}/raw/xiaomi-raw.json'))
    IMG = f'img/{slug}'
    for d in ('ext', 'int', 'options'): os.makedirs(f'{proj}/{IMG}/{d}', exist_ok=True)
    trims = raw['configTrims']; per_trim = '{trim}' in raw['renderPaths']['exterior']
    options, vers, have, ang, ints = {}, [], {}, {}, []
    groups = [('paint', raw['paints'], 'Цвет кузова', 'swatch', 'ext', 'paint-'), ('wheel', raw['wheels'], 'Диски', 'option', 'ext', 'wheel-'), ('int', raw['interiors'], 'Цвет салона', 'swatch', 'int', 'trim-')]
    for role, lst, title, kind, img, pref in groups:
        for o in lst:
            icon = f'{IMG}/options/{pref}{o["id"]}.webp'
            if os.path.exists(f'{src}/options/{pref}{o["id"]}.webp'):
                im = Image.open(f'{src}/options/{pref}{o["id"]}.webp').convert('RGBA'); im.thumbnail((112, 112)); im.save(f'{proj}/{icon}', 'WEBP', quality=85)
            else: icon = None
            options[oid(o['id'])] = {'name': o['name'], 'note': (o.get('note') or '') if role == 'wheel' else '', 'icon': icon, 'mutex': [], 'cascade': [], 'sku': role}
    def ext_frame(srcf, dst):
        if os.path.exists(dst): return
        im = Image.open(srcf).convert('RGB'); w, h = im.size
        cw = int(w * 0.66); ch = int(cw * 10 / 16); x0 = (w - cw) // 2; y0 = int(h * 0.535 - ch / 2)     # машина в кадре мелкая – приближаем
        im.crop((x0, y0, x0 + cw, y0 + ch)).resize((1280, 800), Image.LANCZOS).save(dst, 'WEBP', quality=80, method=6)
    for t in trims:
        name = t['name'].replace(short, '', 1).strip(' ,–-') or 'Стандартная'
        name = name[0].upper() + name[1:]
        pre = oid(t['id']) + '-' if per_trim else ''
        secs = []
        for role, lst, title, kind, img, pref in groups:
            op = [{'id': oid(o['id']), 'def': False, 'promo': False, 'promoTo': ''} for o in lst if o['avail'].get(t['id']) is not None]
            if op: op[0]['def'] = True; secs.append({'sku': role, 'role': role, 'title': title, 'kind': kind, 'img': img, 'opts': op})
        P = [o for o in raw['paints'] if o['avail'].get(t['id']) is not None]; W = [o for o in raw['wheels'] if o['avail'].get(t['id']) is not None]
        for p in P:
            for w in W:
                base = (f'{t["id"]}--' if per_trim else '') + f'{p["id"]}--{w["id"]}'
                code = f'{pre}{oid(p["id"])}_{oid(w["id"])}'
                if not os.path.exists(f'{src}/render/{base}--side.webp'): continue
                have[code] = ['hero']; ang[code] = []
                for shot in ('hero', 'front34', 'rear34'):
                    f = f'{src}/render/{base}--{SRC_SHOT[shot]}.webp'
                    if os.path.exists(f):
                        ext_frame(f, f'{proj}/{IMG}/ext/{code}--{shot}.webp')
                        if shot != 'hero': ang[code].append(shot)
        vers.append({'id': oid(t['id']), 'name': name, 'tag': t['rows'][0]['value'] if t.get('rows') else '', 'group': '', 'drive': '', 'level': [], 'secs': secs, 'codePrefix': pre,
                     'vehicleSkus': ['paint', 'wheel'], 'angleSkus': ['paint', 'wheel'], 'interiorSkus': ['int'], 'ranges': {}})
    for o in raw['interiors']:
        fs = {s: f'{src}/render/{o["id"]}--{SRC_SHOT[s]}.webp' for s in ('int', 'int2')}
        if all(os.path.exists(f) for f in fs.values()):
            for pre in sorted({v['codePrefix'] for v in vers}):          # движок ищет салон с меткой версии
                for s, f in fs.items():
                    dst = f'{proj}/{IMG}/int/{pre}{oid(o["id"])}--{s}.webp'
                    if not os.path.exists(dst): Image.open(f).convert('RGB').save(dst, 'WEBP', quality=80, method=6)
                ints.append(pre + oid(o['id']))
    data = {'car': car, 'short': short, 'groups': [], 'versions': vers, 'options': options, 'have': have, 'ang': ang, 'int': ints,
            'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}--{shot}.webp'}, 'shots': SHOTS}
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    cjk = sorted(set(re.findall(r'[㐀-鿿＀-￯][^"]{0,20}', js)))
    if cjk: raise SystemExit('в данных остался китайский текст: ' + ', '.join(cjk[:20]))
    os.makedirs(f'{proj}/js', exist_ok=True)
    open(f'{proj}/js/zeekr-data.js', 'w').write('/* Данные конфигуратора ' + car + ': официальный конфигуратор xiaomiev.com (снято 17.10.2026), перенос скриптом tools/xiaomi.py. Цен нет намеренно. */\nwindow.ZEEKR_CFG = ' + js + ';\n')
    print(car, 'версий', len(vers), [v['name'] for v in vers], 'сборок кузова', len(have), 'салонов', len(ints))

if __name__ == '__main__' and sys.argv[1] == 'sobrat': sobrat(*sys.argv[2:7])
