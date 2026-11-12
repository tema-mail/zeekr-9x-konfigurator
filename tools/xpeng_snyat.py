"""Xpeng: снять данные официального конфигуратора (store.xiaopeng.com/configurate.html?carSeries=GX).
  python3 xpeng_snyat.py <код серии, напр. GX> <папка проекта>   -> raw/xpeng-raw.json
API открытый, браузер не нужен (сайт открывается и с сервера в Нидерландах):
  страница configurate.html – список версий в window.__INITIAL_STATE__ (vgroups);
  /api/v1/client/orion/configurator/allInOne?carSeriesSn=<серия> – опции каждой версии и все сборки с картинками."""
import json, os, re, sys, subprocess, time
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def get(url):
    for a in range(6):
        r = subprocess.run(['curl', '-sL', '--max-time', '90', '-A', UA, '-H', 'referer: https://store.xiaopeng.com/', url], capture_output=True, text=True)
        if r.returncode == 0 and len(r.stdout) > 500: return r.stdout
        time.sleep(2 + a * 2)
    raise SystemExit('нет ответа: ' + url)

def snyat(series, proj):
    html = get(f'https://store.xiaopeng.com/configurate.html?carSeries={series}')
    i = html.index('window.__INITIAL_STATE__='); st = json.loads(html[i + len('window.__INITIAL_STATE__='):html.index('</script>', i)].strip().rstrip(';'))
    all_ = json.loads(get(f'https://store.xiaopeng.com/api/v1/client/orion/configurator/allInOne?carSeriesSn={series}'))
    if all_.get('code') != 200: raise SystemExit('API: ' + str(all_.get('code')))
    out = {'series': series, 'vgroups': st['vgroups'], 'specs': all_['data']['carSpecGroupVoMap'], 'cars': all_['data']['carInfoVoMap']}
    os.makedirs(f'{proj}/raw', exist_ok=True); json.dump(out, open(f'{proj}/raw/xpeng-raw.json', 'w'), ensure_ascii=False)
    print(series, 'версий', len(out['specs']), 'сборок', sum(len(v) for v in out['cars'].values()))

if __name__ == '__main__': snyat(sys.argv[1], sys.argv[2])
