"""Lynk & Co: снять версии, опции и картинки серии через открытый API lynkco.com.cn (обычные запросы, браузер не нужен).
python3 lynkco_snyat.py <vcId серии> <папка проекта>  -> raw/lynk-raw.json. Сайт отвечает с перебоями – запросы с повторами."""
import json, sys, subprocess, time, os
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
def info(vc):
    for a in range(6):
        r = subprocess.run(['curl', '-s', '-m', '45', '-A', UA, '-H', 'referer: https://www.lynkco.com.cn/cars/model-config', f'https://www.lynkco.com.cn/api/geely/lynk/categrory/Info?vcId={vc}'], capture_output=True, text=True)
        try:
            j = json.loads(r.stdout)
            if j.get('code') == 200: return j['data']
        except ValueError: pass
        time.sleep(3 + a * 3)
    return None
sid, proj = sys.argv[1], sys.argv[2]
base = info(sid)
if not base: raise SystemExit('серия не отвечает')
tiers = []; c = base['categoryInfo']
while c: tiers.append({'name': c.get('tierSortName'), 'list': [{k: l.get(k) for k in ('id', 'name', 'frontName', 'pid', 'isShow', 'sequence')} for l in c['list']]}); c = c.get('child')
out = {'series': sid, 'tiers': tiers, 'versions': {}}
for l in tiers[-1]['list']:
    if l.get('isShow') == 0: continue
    d = info(l['id'])
    if not d: print(l['id'], l['name'], 'нет данных, пропуск', flush=True); continue
    out['versions'][str(l['id'])] = {'attrs': d['categoryVehicleAttribute'], 'vehicles': d['vehicles'], 'packages': d['packageForViewDtoList']}
    print(l['id'], l['name'], 'сборок', len(d['vehicles']), flush=True)
os.makedirs(f'{proj}/raw', exist_ok=True)
json.dump(out, open(f'{proj}/raw/lynk-raw.json', 'w'), ensure_ascii=False)
print('ярусы:', [(t['name'], [(x['id'], x['name'], x['pid']) for x in t['list']]) for t in tiers])
