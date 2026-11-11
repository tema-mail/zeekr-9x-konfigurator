"""Проверка опубликованного конфигуратора в браузере на сервере в Амстердаме (на маке браузер не запускается).
python3 proverka_vps.py <url> [папка для снимков]. Прокликивает все версии и опции, сверяет картинку с выбором,
проверяет загрузку всех картинок, ссылку на сборку, форму, ширину на 390 px, китайские символы в тексте страницы."""
import sys, json, base64, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vps import run
JS = r'''
async (page) => {
  const U = %URL%; const out = { errs: [], bad: [], fails: [] };
  page.on('pageerror', e => out.errs.push(String(e).slice(0, 200)));
  const seenBad = new Set(); page.on('response', r => { if (r.status() >= 400) seenBad.add(r.url()); });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(U + '?t=' + Date.now(), { waitUntil: 'load', timeout: 60000 }); await page.waitForTimeout(2500);
  out.title = await page.title();
  out.shots = await page.$$eval('[data-shot]', e => e.map(x => x.dataset.shot).join(','));
  const check = async (what) => {
    try { await page.waitForFunction(() => !document.querySelector('.z9__stage').classList.contains('is-loading'), null, { timeout: 10000 }); } catch (e) { out.fails.push(what + ': картинка не загрузилась'); }
    const r = await page.evaluate(() => { const im = document.querySelector('.z9__shot.is-front img'); const src = im.currentSrc.split('/').pop().replace('.webp', '').split('--')[0];
      const code = src.includes('-') ? src.split('-').slice(1).join('-') : src; const sel = window.ZeekrCfg.get().config;
      // ожидаемый кадр кузова: если точная сборка снята, на экране должна быть именно она (ловит картинку, которая не обновилась)
      const D = window.ZEEKR_CFG, det = window.ZeekrCfg.get(), V = D.versions.find(v => v.id === det.version);
      const want = V ? (V.codePrefix || '') + V.vehicleSkus.map(s => sel.find(c => D.options[c] && D.options[c].sku === s)).filter(Boolean).join('_') : null;
      const isExt = im.currentSrc.indexOf(D.paths.ext.split('{code}')[0]) !== -1 && /--hero\.webp/.test(im.currentSrc);
      return { alien: code.split('_').filter(t => t && sel.indexOf(t) === -1), w: im.naturalWidth, stale: (isExt && want && D.have[want] && src !== want) ? want + ' вместо него ' + src : '' }; });
    if (r.stale) out.fails.push(what + ': кадр кузова не тот, ждали ' + r.stale);
    if (r.alien.length) out.fails.push(what + ': на картинке чужие опции ' + r.alien.join(','));
    if (!r.w) {   // GitHub Pages иногда отвечает 503 на отдельный файл: даём вторую попытку, прежде чем считать кадр пустым
      await page.waitForTimeout(3000);
      const w2 = await page.evaluate(() => new Promise(res => { const im = document.querySelector('.z9__shot.is-front img'); const u = im.currentSrc.split('?')[0] + '?r=' + Date.now(); im.onload = () => res(im.naturalWidth); im.onerror = () => res(0); im.src = u; }));
      if (!w2) out.fails.push(what + ': картинка пустая');
    }
  };
  let clicks = 0;
  const groups = await page.$$eval('[data-group]', e => e.map(x => x.dataset.group));
  for (const g of (groups.length ? groups : [null])) {
    if (g) { await page.click('[data-group="' + g + '"]'); await page.waitForTimeout(200); }
    for (const v of await page.$$eval('[data-version]', e => e.map(x => x.dataset.version))) {
      await page.click('[data-version="' + v + '"]'); await page.waitForTimeout(150); await check('версия ' + v);
      for (const pc of await page.$$eval('[data-slot=groups] [data-pc]', e => e.map(x => x.dataset.pc))) {
        if (!(await page.locator('[data-pc="' + pc + '"]').count())) continue;
        await page.click('[data-pc="' + pc + '"]'); clicks++; await check('версия ' + v + ', опция ' + pc);
      }
      for (const cb of await page.$$eval('[data-extra]:not([disabled])', e => e.map(x => x.dataset.extra))) { await page.click('[data-extra="' + cb + '"]'); clicks++; await check('версия ' + v + ', галочка ' + cb); }
    }
  }
  out.clicks = clicks;
  const t = await page.evaluate(() => window.ZeekrCfg.get()); out.text = t.text.slice(0, 220);
  const p2 = await page.context().newPage(); await p2.goto(t.url, { waitUntil: 'load' }); await p2.waitForTimeout(1500);
  out.link = (await p2.evaluate(() => window.ZeekrCfg.get().text)) === t.text; await p2.close();
  out.images = await page.evaluate(async () => { const D = window.ZEEKR_CFG; let bad = [], list = [];
    for (const c in D.have) for (const s of D.have[c]) list.push(D.paths.ext.replace('{code}', c).replace('{shot}', s));
    for (const c in (D.ang || {})) for (const s of D.ang[c]) list.push(D.paths.ext.replace('{code}', c).replace('{shot}', s));
    for (const c of D.int) for (const sh of D.shots.filter(x => x.id === 'int' || x.kind === 'int')) list.push(D.paths.int.replace('{code}', c).replace('{shot}', sh.id));
    for (const k in D.options) if (D.options[k].icon) list.push(D.options[k].icon);
    list = [...new Set(list)];
    const head = async u => { try { const r = await fetch(u, { method: 'HEAD', cache: 'no-store' }); const n = +(r.headers.get('content-length') || 1e6); return r.ok && n > 150; } catch (e) { return false; } };   // пустой файл (0 байт) – тоже битая картинка
    for (let i = 0; i < list.length; i += 8) await Promise.all(list.slice(i, i + 8).map(async u => { if (!(await head(u))) bad.push(u); }));
    for (let a = 0; a < 3 && bad.length; a++) { await new Promise(r => setTimeout(r, 4000)); const still = []; for (const u of bad) if (!(await head(u))) still.push(u); bad = still; }   // 503 у Pages – временный
    return { n: list.length, bad: bad.slice(0, 5) }; });
  // ответы с ошибкой за время проверки: оставляем только те адреса, которые не открылись и повторно
  out.bad = await page.evaluate(async (urls) => { const res = []; for (const u of urls) { let ok = false; for (let a = 0; a < 3 && !ok; a++) { try { ok = (await fetch(u.split('?')[0], { method: 'HEAD', cache: 'no-store' })).ok; } catch (e) {} if (!ok) await new Promise(r => setTimeout(r, 3000)); } if (!ok) res.push(u.slice(-80)); } return res; }, [...seenBad]);
  out.cjk = await page.evaluate(() => (document.body.innerText.match(/[㐀-鿿＀-￯]+/g) || []).slice(0, 5));
  const shot = async () => (await page.screenshot({ type: 'jpeg', quality: 55 })).toString('base64');
  out.pic_d = await shot();
  await page.click('[data-send]'); out.formLocked = await page.$eval('form.z9__form button[type=submit]', e => e.disabled);
  await page.setViewportSize({ width: 390, height: 844 }); await page.goto(U + '?m=' + Date.now(), { waitUntil: 'load' }); await page.waitForTimeout(2000);
  out.w390 = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth ? 390 : document.documentElement.scrollWidth); out.pic_m = await shot();
  return out;
}'''
url = sys.argv[1]; outdir = sys.argv[2] if len(sys.argv) > 2 else None
r = run(JS.replace('%URL%', json.dumps(url)), 1500)
name = url.rstrip('/').split('/')[-1]
if outdir:
    os.makedirs(outdir, exist_ok=True)
    for k in ('pic_d', 'pic_m'): open(f'{outdir}/{name}-{k[-1]}.jpg', 'wb').write(base64.b64decode(r.pop(k)))
else: r.pop('pic_d', None); r.pop('pic_m', None)
ok = not r['errs'] and not r['bad'] and not r['fails'] and not r['images']['bad'] and r['link'] and r['formLocked'] and r['w390'] == 390 and not r['cjk']
print(name, '| ЧИСТО' if ok else '| ЕСТЬ ЗАМЕЧАНИЯ', '| виды:', r['shots'], '| кликов', r['clicks'], '| картинок', r['images']['n'], 'битых', r['images']['bad'],
      '| ссылка', r['link'], '| форма закрыта', r['formLocked'], '| ширина', r['w390'], '| иероглифы', r['cjk'], '| ошибки', r['errs'][:3], '| 4xx', r['bad'][:3], '| сбои', r['fails'][:4])
print('   ', r['text'])
sys.exit(0 if ok else 1)
