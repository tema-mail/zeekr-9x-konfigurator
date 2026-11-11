"""Проверка кадров перед выкладкой: каждый файл, на который ссылаются данные конфигуратора, есть на диске, не пустой и открывается.
  python3 proverka_kadrov.py <папка проекта>      – код возврата 1, если что-то не так.
Зачем: прерванная сборка оставляет файл в 0 байт; хостинг отдаёт его как существующий, а в конфигураторе пустое место (Avatr 07L, 11.11.2026)."""
import json, os, sys, glob
from PIL import Image
proj = sys.argv[1] if len(sys.argv) > 1 else '.'
d = json.loads(open(f'{proj}/js/zeekr-data.js').read().split('window.ZEEKR_CFG = ', 1)[1].rstrip().rstrip(';'))
need = set()
for c, shots in d['have'].items(): need |= {d['paths']['ext'].replace('{code}', c).replace('{shot}', s) for s in shots}
for c, shots in (d.get('ang') or {}).items(): need |= {d['paths']['ext'].replace('{code}', c).replace('{shot}', s) for s in shots}
for c in d['int']: need |= {d['paths']['int'].replace('{code}', c).replace('{shot}', s['id']) for s in d['shots'] if s['id'] == 'int' or s.get('kind') == 'int'}
need |= {o['icon'] for o in d['options'].values() if o.get('icon')}
bad = []
for f in sorted(need):
    p = f'{proj}/{f}'
    if not os.path.exists(p): bad.append(f + ' – нет файла'); continue
    if os.path.getsize(p) < 150: bad.append(f + f' – пустой ({os.path.getsize(p)} байт)'); continue
    try: Image.open(p).load()
    except Exception as e: bad.append(f + ' – не открывается')
junk = [f for f in glob.glob(f'{proj}/img/**/*', recursive=True) if os.path.isfile(f) and (os.path.getsize(f) < 150 or f.endswith('.part'))]
for f in junk: bad.append(os.path.relpath(f, proj) + ' – мусор от прерванной сборки')
print(f'кадров в данных {len(need)}, с ошибкой {len(bad)}')
if bad: print('\n'.join(bad[:20])); sys.exit(1)
