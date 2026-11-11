"""Xiaomi EV: снять данные официального конфигуратора (xiaomiev.com/configurator/select-version?goodsId=…).
  python3 xiaomi_snyat.py <goodsId> <папка проекта>   -> raw/xiaomi-api.json
API открытый (website-api.xiaomiev.com/mtop/guidemarketing/…), тело запроса – массив из одного объекта. Браузер не нужен;
с сервера в Нидерландах сайт не открывается, запрос идёт напрямую.
Готовых кадров Xiaomi не отдаёт: materialV2 даёт слои сцены 5000×2812 – кузов в цвете с фоном и накладку дисков с координатами."""
import json, os, sys, subprocess, time
B = 'https://website-api.xiaomiev.com/mtop/guidemarketing/product'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def post(path, obj):
    for a in range(6):
        r = subprocess.run(['curl', '-s', '--max-time', '60', '-A', UA, '-H', 'content-type: application/json', '-H', 'origin: https://www.xiaomiev.com',
                            '-H', 'referer: https://www.xiaomiev.com/', '-X', 'POST', '-d', json.dumps([obj]), B + path], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith('{'):
            j = json.loads(r.stdout)
            if j.get('code') == 0: return j['data']
        time.sleep(2 + a * 2)
    raise SystemExit('нет ответа: ' + path + ' ' + json.dumps(obj))

def snyat(goods, proj):
    det = post('/car/versionList', {'goodsId': str(goods), 'inventoryChannel': 'NORMAL', 'detailMode': 1})['detail']
    out = {'goodsId': str(goods), 'versions': []}
    for s in det['ssuList']:
        cfg = post('/car-configurator/get', {'itemId': str(s['itemId']), 'carSsuId': str(s['ssuId']), 'inventoryChannel': 'NORMAL'})['carSsuDetail']
        mat = post('/materialV2', {'itemId': str(s['itemId']), 'ssuId': str(s['ssuId']), 'type': 'PC'})
        out['versions'].append({'ssuId': s['ssuId'], 'itemId': s['itemId'], 'cfg': cfg, 'mat': mat})
        print(cfg.get('name'), cfg.get('engCode'), s['ssuId'], flush=True)
    os.makedirs(f'{proj}/raw', exist_ok=True)
    json.dump(out, open(f'{proj}/raw/xiaomi-api.json', 'w'), ensure_ascii=False)

if __name__ == '__main__': snyat(sys.argv[1], sys.argv[2])
