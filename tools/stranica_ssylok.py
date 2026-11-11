"""Одна страница со ссылками на все конфигураторы: ~/Sites/razbory/konfiguratory-2f6c81a4/index.html. Числа берутся из данных проектов."""
import json, os, html, datetime
S = os.path.expanduser('~/Sites')
BRANDS = [
 ('Zeekr', 'zeekr', [('9x', '9X'), ('8x', '8X'), ('7x', '7X'), ('x', 'X'), ('001', '001'), ('001-fr', '001 FR'), ('007', '007'), ('007-gt', '007 GT'), ('009', '009'), ('009-grand', '009 Grand'), ('mix', 'MIX')]),
 ('Li Auto', 'lixiang', [('l9', 'L9'), ('l8', 'L8'), ('l6', 'L6'), ('i6', 'i6'), ('i8', 'i8'), ('i9', 'i9'), ('mega', 'MEGA')]),
 ('Xiaomi', 'xiaomi', [('su7', 'SU7'), ('su7-ultra', 'SU7 Ultra'), ('yu7', 'YU7')]),
 ('Avatr', 'avatr', [('07l', '07L'), ('07', '07'), ('06', '06'), ('06t', '06T'), ('12', '12')]),
 ('Lynk & Co', 'lynkco', [('900', '900'), ('09', '09 EM-P'), ('08', '08 EM-P'), ('07', '07 EM-P'), ('z20', 'Z20')]),
 ('Geely Galaxy', 'geely', [('e5', 'Galaxy E5 (EX5)'), ('xingyuan', 'Xingyuan (EX2)'), ('starship-7', 'Starship 7'), ('starshine-6', 'Starshine 6')]),
]
def pl(n, a, b, c):
    n10, n100 = n % 10, n % 100
    return f'{n} ' + (a if n10 == 1 and n100 != 11 else b if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else c)
rows, total = [], 0
for brand, pref, models in BRANDS:
    cards = []
    for slug, name in models:
        proj = f'{pref}-{slug}-konfigurator'
        d = json.loads(open(f'{S}/{proj}/js/zeekr-data.js').read().split('window.ZEEKR_CFG = ', 1)[1].rstrip().rstrip(';'))
        ext = sum(1 for s in d['shots'] if not (s['id'] == 'int' or s.get('kind') == 'int')); inn = len(d['shots']) - ext
        note = ', '.join([pl(len(d['versions']), 'версия', 'версии', 'версий'), pl(len(d['have']), 'сборка кузова', 'сборки кузова', 'сборок кузова'),
                          pl(ext, 'вид кузова', 'вида кузова', 'видов кузова')] + ([pl(inn, 'вид салона', 'вида салона', 'видов салона')] if d['int'] else ['без фото салона']))
        url = f'https://tema-mail.github.io/{proj}/'
        cards.append(f'<a class="card" href="{url}" target="_blank" rel="noopener"><b>{html.escape(brand)} {html.escape(name)}</b><span>{note}</span><i>{url.replace("https://", "")}</i></a>')
        total += 1
    rows.append(f'<section><h2>{html.escape(brand)} <small>{len(models)}</small></h2><div class="grid">{"".join(cards)}</div></section>')
today = datetime.date.today().strftime('%d.%m.%Y')
page = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Конфигураторы новых авто из Китая – все ссылки</title>
<script>(function(){{var t;try{{t=localStorage.getItem('tema')}}catch(e){{}}if(!t){{var h=new Date().getHours();t=(h>=19||h<7||(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches))?'dark':'light'}}document.documentElement.setAttribute('data-theme',t)}})();</script>
<style>
:root{{--bg:#f4f5f7;--card:#fff;--text:#16181c;--muted:#6a6f78;--line:#e1e4e9;--acc:#0b6b66}}
html[data-theme=dark]{{--bg:#141518;--card:#1f2125;--text:#e8e8e6;--muted:#a3a6ad;--line:#33363c;--acc:#5fd4c9;color-scheme:dark}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 16px 80px}}h1{{font-size:clamp(1.5rem,1.1rem + 1.8vw,2.2rem);line-height:1.15;margin:0 0 10px}}
.lead{{color:var(--muted);max-width:760px;margin:0 0 6px}}h2{{font-size:1.25rem;margin:34px 0 12px}}h2 small{{color:var(--muted);font-weight:400;font-size:.9rem;margin-left:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}}
.card{{display:grid;gap:6px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--card);color:inherit;text-decoration:none;transition:border-color .2s,transform .2s}}
.card:hover{{border-color:var(--acc);transform:translateY(-2px)}}.card b{{font-size:1.05rem}}.card span{{color:var(--muted);font-size:.875rem}}.card i{{font-style:normal;color:var(--acc);font-size:.75rem;word-break:break-all}}
#tema{{position:fixed;right:14px;bottom:14px;width:44px;height:44px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--text);font-size:20px;cursor:pointer}}
@media (max-width:520px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Конфигураторы новых авто из Китая</h1>
<p class="lead">Все {total} конфигураторов одной страницей. В каждом только сам конфигуратор: без шапки, логотипа и цен, с кнопкой «Отправить сборку менеджеру» и ссылкой на сборку. Картинки – официальные рендеры производителя под выбранную сборку.</p>
<p class="lead">Обновлено {today}. Страницы закрыты от поиска.</p>
{"".join(rows)}
</main><button id="tema" type="button" aria-label="Сменить тему">☾</button>
<script>(function(){{var b=document.getElementById('tema'),r=document.documentElement;function s(){{b.textContent=r.getAttribute('data-theme')==='dark'?'☀':'☾'}}s();b.onclick=function(){{var t=r.getAttribute('data-theme')==='dark'?'light':'dark';r.setAttribute('data-theme',t);try{{localStorage.setItem('tema',t)}}catch(e){{}}s()}}}})();</script>
</body></html>'''
assert '—' not in page
out = f'{S}/razbory/konfiguratory-2f6c81a4'; os.makedirs(out, exist_ok=True); open(out + '/index.html', 'w').write(page); print('готово', total, out)
