#!/bin/bash
# Собрать и выложить конфигуратор модели Geely Galaxy. Перед этим снять raw/geely-raw.json (tools/geely_snyat.py)
# Запуск: geely-model.sh <slug> "<Geely Galaxy E5>" "<Galaxy E5>"     (NOPUSH=1 – без выкладки)
set -e
SLUG=$1; CAR=$2; SHORT=$3
SRC=~/Sites/zeekr-9x-konfigurator
D=~/Sites/geely-$SLUG-konfigurator
cd "$D"
[ -d .git ] || git init -q -b main
mkdir -p css js tools .github/workflows
cp $SRC/css/konfigurator.css css/; cp $SRC/js/konfigurator.js js/
cp $SRC/tools/geely.py $SRC/tools/geely_snyat.py $SRC/tools/geely-model.sh $SRC/tools/proverka_vps.py $SRC/tools/proverka_kadrov.py $SRC/tools/vps.py $SRC/tools/srv_run.py $SRC/tools/ikonki-list.py tools/
cp $SRC/.github/workflows/pages.yml .github/workflows/; cp $SRC/robots.txt $SRC/.gitignore $SRC/.nojekyll .
CARH=${CAR//&/\\&amp;}; sed "s/Zeekr 9X/$CARH/g" $SRC/index.html > index.html
python3 tools/geely.py sobrat . "$CAR" "$SHORT" "geely-$SLUG"
python3 tools/proverka_kadrov.py .
python3 - "$CAR" "$SLUG" <<'EOF'
import json, sys, os
car, slug = sys.argv[1:3]
d = json.loads(open('js/zeekr-data.js').read().split('window.ZEEKR_CFG = ', 1)[1].rstrip().rstrip(';'))
vers = ', '.join(v['name'] for v in d['versions'])
groups = []
for v in d['versions']:
    for g in v['secs']:
        if g['role'] != 'extra' and g['title'] not in groups: groups.append(g['title'])
ex = sorted({d['options'][g['opts'][0]['id']]['name'] for v in d['versions'] for g in v['secs'] if g['role'] == 'extra'})
t = open(os.path.expanduser('~/Sites/zeekr-9x-konfigurator/README.md')).read()
embed = t[t.index('## Встраивание в сайт'):t.index('## Как обновить данные')]
open('README.md', 'w').write(f'''# Конфигуратор {car}

Только конфигуратор: без шапки, логотипа, подвала и цен. Его собирают в сборку и встраивают в страницу модели на сайте.

Посмотреть: https://tema-mail.github.io/geely-{slug}-konfigurator/ (закрыт от индексации).
Локально: `python3 -m http.server 8940`, затем http://127.0.0.1:8940/

## Что выбирает человек
Версия ({vers}); {', '.join(g.lower() for g in groups)}{('; дополнительно – ' + ', '.join(x.lower() for x in ex)) if ex else ''}.
Варианты и их сочетания взяты из официального конфигуратора Geely Galaxy (matrix.geely.com): чего производитель не собирает, выбрать нельзя.
Названия версий у производителя только китайские, здесь даны по смыслу (Explore, Voyage, Laser и т. п.).

## Картинки
Официальные рендеры Geely без фона: до пяти видов кузова на сборку (спереди, сбоку, сзади, строго сзади и строго спереди) и фото салона на отделку.
Китайские надписи убраны: текст на номерных рамках и шильдики на крышке багажника закрашены, сноска на фото салона срезана.
{len(d['have'])} сборок кузова, {len(d['int'])} вариантов салона, всё в WebP.

{embed}## Как обновить данные
1. `python3 tools/geely_snyat.py <productId> .` – пишет `raw/geely-raw.json`. Браузер не нужен, у Geely открытый API;
   с сервера в Нидерландах сайт не открывается, запрос идёт напрямую. productId – из ссылки «заказать» на galaxy.geely.com.
2. `tools/geely-model.sh {slug} "{car}" "<короткое имя>"` – картинки, данные, проверки и выкладка (NOPUSH=1 – без выкладки).
   Новое китайское название сборка не пропустит: перевод добавить в RU и TRIM в tools/geely.py.
   Координаты закраски надписей – MASKS в tools/geely.py (в пикселях исходного кадра), у каждой модели и внешности свои; после сборки смотреть кадры глазами.
3. Проверка выложенной страницы в браузере на сервере: `python3 tools/proverka_vps.py https://tema-mail.github.io/geely-{slug}-konfigurator/`
Движок и стили общие с конфигураторами Zeekr, мастер-копия – репозиторий tema-mail/zeekr-9x-konfigurator.

Данные сняты 11.11.2026.
''')
EOF
grep -rn "—" index.html README.md js css && { echo "длинное тире"; exit 1; } || true
python3 - <<'PYCJK'
import glob, re, sys
bad = [f'{f}: {m}' for f in glob.glob('*.html') + glob.glob('js/*.js') + glob.glob('css/*.css') + glob.glob('*.md')
       for m in re.findall(r'[㐀-鿿＀-￯]+', open(f, encoding='utf8').read())]
if bad: sys.exit('китайский текст на странице: ' + '; '.join(bad[:10]))
PYCJK
[ -n "$NOPUSH" ] && { echo "собрано без выкладки: $D"; exit 0; }
git add -A
git commit -q -m "Конфигуратор $CAR: сборка без цен, рендеры Geely под каждую сборку, отправка менеджеру

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
if ! ~/.local/bin/gh repo view tema-mail/geely-$SLUG-konfigurator >/dev/null 2>&1; then
  ~/.local/bin/gh repo create tema-mail/geely-$SLUG-konfigurator --public --source . --push -d "Конфигуратор $CAR для встраивания на сайт" >/dev/null
  ~/.local/bin/gh api -X POST repos/tema-mail/geely-$SLUG-konfigurator/pages -f build_type=workflow >/dev/null
  ~/.local/bin/gh workflow run Pages -R tema-mail/geely-$SLUG-konfigurator
else
  git push -q
fi
echo "готово: https://tema-mail.github.io/geely-$SLUG-konfigurator/"
