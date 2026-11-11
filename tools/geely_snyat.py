"""Geely Galaxy: снять данные официального конфигуратора (matrix.geely.com/mall-design/overview/<productId>).
  python3 geely_snyat.py <productId> <папка проекта>   -> raw/geely-raw.json
API открытый, браузер не нужен; сайт не открывается с сервера в Нидерландах, запрос идёт напрямую и отвечает с перебоями (повторы).
productId – из ссылок «заказать» на galaxy.geely.com."""
import json, os, sys, subprocess, base64, gzip, time
B = 'https://matrix.geely.com/mall/v2'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def get(path, pid):
    for a in range(8):
        r = subprocess.run(['curl', '-s', '--max-time', '45', '-A', UA, '-H', f'Referer: https://matrix.geely.com/mall-design/overview/{pid}', B + path], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith('{'):
            j = json.loads(r.stdout)
            if j.get('code') == 200: return j['data']
        time.sleep(2 + a * 2)
    raise SystemExit('нет ответа: ' + path)

def snyat(pid, proj):
    out = {'pid': pid, 'product': get(f'/product/get?productId={pid}&channelCode=galaxy_pc', pid),
           'classify': get(f'/product/classify/list?productId={pid}', pid)}
    t = get(f'/product/sku/tree?productId={pid}', pid)
    out['tree'] = json.loads(gzip.decompress(base64.b64decode(t)).decode()) if isinstance(t, str) else t
    os.makedirs(f'{proj}/raw', exist_ok=True)
    json.dump(out, open(f'{proj}/raw/geely-raw.json', 'w'), ensure_ascii=False)
    print(out['product'].get('name'), out['product'].get('seriesCodeWeb'), 'сборок', len(out['product'].get('skuList') or []))

if __name__ == '__main__': snyat(sys.argv[1], sys.argv[2])
