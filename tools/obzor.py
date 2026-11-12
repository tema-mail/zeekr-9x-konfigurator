"""Обзорные листы кадров конфигуратора – смотреть глазами перед выкладкой (правило после салона Xiaomi без руля, 12.11.2026).
  python3 obzor.py <папка проекта> <папка для листов>
Салон: КАЖДЫЙ разный кадр салона (одинаковые по содержимому показываются один раз, с числом повторов).
Кузов: по каждой версии – все виды сборки по умолчанию и главный кадр каждого цвета.
На что смотреть: руль, сиденья, экраны, зеркала, диски, антикрыло на месте; нет обрезанной машины, пустых областей, иероглифов."""
import json, os, sys, hashlib, collections
from PIL import Image, ImageDraw
proj, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
name = os.path.basename(os.path.abspath(proj)).replace('-konfigurator', '')
d = json.loads(open(f'{proj}/js/zeekr-data.js').read().split('window.ZEEKR_CFG = ', 1)[1].rstrip().rstrip(';'))
def sheet(cells, cols, cw, ch, path, per=28):
    files = []
    for part in range(0, len(cells), per):
        ch_ = cells[part:part + per]; rows = (len(ch_) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cw, rows * (ch + 14)), (238, 238, 238)); dr = ImageDraw.Draw(sh)
        for n, (f, label) in enumerate(ch_):
            x, y = (n % cols) * cw, (n // cols) * (ch + 14)
            try:
                im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (238, 238, 238, 255)); bg.alpha_composite(im); im = bg.convert('RGB'); im.thumbnail((cw - 4, ch)); sh.paste(im, (x + 2, y + 13))
            except Exception as e: dr.text((x + 4, y + 30), 'НЕ ОТКРЫВАЕТСЯ', fill=(255, 0, 0))
            dr.text((x + 3, y + 1), label[:int(cw / 6.2)], fill=(0, 0, 0))
        p = f'{path}-{part // per + 1}.png'; sh.save(p); files.append(p)
    return files
ish = [s['id'] for s in d['shots'] if s['id'] == 'int' or s.get('kind') == 'int']
seen = collections.OrderedDict()
for c in d['int']:
    for s in ish:
        f = f'{proj}/' + d['paths']['int'].replace('{code}', c).replace('{shot}', s)
        if not os.path.exists(f): continue
        h = hashlib.md5(open(f, 'rb').read()).hexdigest(); seen.setdefault(h, [f, f'{c} {s}', 0]); seen[h][2] += 1
files = sheet([(f, f'{lab} ×{n}') for f, lab, n in seen.values()], 4, 350, 220, f'{out}/{name}-salon', 24)
cells = []
for v in d['versions']:
    by = {s['sku']: s for s in v['secs']}
    def code(sel): return v.get('codePrefix', '') + '_'.join(x for x in (sel.get(k) for k in v['vehicleSkus']) if x)
    dsel = {k: (next((o['id'] for o in s['opts'] if o['def']), s['opts'][0]['id']) if s['role'] != 'extra' else (s['opts'][0]['id'] if s['opts'][0]['def'] or s['opts'][0].get('pre') else None)) for k, s in by.items()}
    c0 = code(dsel); shots = (['hero'] + [x for x in ((d.get('ang') or {}).get(c0) or d['have'].get(c0) or []) if x != 'hero'])
    for s in shots:
        f = f'{proj}/' + d['paths']['ext'].replace('{code}', c0).replace('{shot}', s)
        cells.append((f, f'{v["name"]} | {s}'))
    paint = next((s for s in v['secs'] if s['role'] == 'paint'), None)
    for o in (paint['opts'] if paint else []):
        c = code(dict(dsel, **{paint['sku']: o['id']}))
        if c != c0 and c in d['have']: cells.append((f'{proj}/' + d['paths']['ext'].replace('{code}', c).replace('{shot}', 'hero'), f'{v["name"]} | {d["options"][o["id"]]["name"]}'))
files += sheet(cells, 4, 350, 220, f'{out}/{name}-kuzov', 24)
print(name, 'разных кадров салона', len(seen), 'кадров кузова в обзоре', len(cells)); print('\n'.join(files))
