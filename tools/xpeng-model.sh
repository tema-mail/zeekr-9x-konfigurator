#!/bin/bash
# Собрать и выложить конфигуратор модели Xpeng. Перед этим снять raw/xpeng-raw.json (tools/xpeng_snyat.py <серия> .)
# Запуск: xpeng-model.sh <slug> "<Xpeng GX>" "<GX>"     (NOPUSH=1 – без выкладки)
set -e
SLUG=$1; CAR=$2; SHORT=$3
SRC=~/Sites/zeekr-9x-konfigurator
D=~/Sites/xpeng-$SLUG-konfigurator
cd "$D"
[ -d .git ] || git init -q -b main
mkdir -p css js tools .github/workflows
cp $SRC/css/konfigurator.css css/; cp $SRC/js/konfigurator.js js/
cp $SRC/tools/xpeng.py $SRC/tools/xpeng_snyat.py $SRC/tools/xpeng-model.sh $SRC/tools/obzor.py $SRC/tools/proverka_vps.py $SRC/tools/proverka_kadrov.py $SRC/tools/vps.py $SRC/tools/srv_run.py $SRC/tools/ikonki-list.py tools/
cp $SRC/.github/workflows/pages.yml .github/workflows/; cp $SRC/robots.txt $SRC/.gitignore $SRC/.nojekyll .
CARH=${CAR//&/\\&amp;}; sed "s/Zeekr 9X/$CARH/g" $SRC/index.html > index.html
python3 tools/xpeng.py sobrat . "$CAR" "$SHORT" "xpeng-$SLUG"
python3 tools/proverka_kadrov.py .
mkdir -p raw/obzor && python3 tools/obzor.py . raw/obzor | tail -n +2   # листы для просмотра глазами: каждый кадр салона, кузов по версиям
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

Посмотреть: https://tema-mail.github.io/xpeng-{slug}-konfigurator/ (закрыт от индексации).
Локально: `python3 -m http.server 8940`, затем http://127.0.0.1:8940/

## Что выбирает человек
Версия ({vers}); {', '.join(g.lower() for g in groups)}{('; дополнительно – ' + ', '.join(x.lower() for x in ex)) if ex else ''}.
Варианты и их сочетания взяты из официального конфигуратора Xpeng (store.xiaopeng.com): чего производитель не собирает, выбрать нельзя.

## Картинки
Официальные рендеры Xpeng без фона: два вида кузова на сборку (спереди и сбоку) – других ракурсов кузова у производителя нет.
Салон: фото каждой отделки и два вида вперёд (с места водителя и со второго ряда), вырезанные из круговых панорам производителя.
{len(d['have'])} сборок кузова, {len(d['int'])} вариантов салона, всё в WebP.

{embed}## Как обновить данные
1. `python3 tools/xpeng_snyat.py <код серии> .` – пишет `raw/xpeng-raw.json` (код серии – из адреса store.xiaopeng.com/configurate.html?carSeries=…).
   API открытый, браузер не нужен.
2. `tools/xpeng-model.sh {slug} "{car}" "{car.replace('Xpeng ', '')}"` – картинки, данные, проверки и выкладка (NOPUSH=1 – без выкладки).
   Новое китайское название сборка не пропустит: перевод добавить в RU в tools/xpeng.py.
3. До выкладки просмотреть глазами листы в raw/obzor (каждый кадр салона, кузов по версиям).
4. Проверка выложенной страницы в браузере на сервере: `python3 tools/proverka_vps.py https://tema-mail.github.io/xpeng-{slug}-konfigurator/`
Движок и стили общие с конфигураторами Zeekr, мастер-копия – репозиторий tema-mail/zeekr-9x-konfigurator.

Данные сняты 12.11.2026.
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
git commit -q -m "Конфигуратор $CAR: сборка без цен, рендеры Xpeng под каждую сборку, отправка менеджеру

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
if ! ~/.local/bin/gh repo view tema-mail/xpeng-$SLUG-konfigurator >/dev/null 2>&1; then
  ~/.local/bin/gh repo create tema-mail/xpeng-$SLUG-konfigurator --public --source . --push -d "Конфигуратор $CAR для встраивания на сайт" >/dev/null
  ~/.local/bin/gh api -X POST repos/tema-mail/xpeng-$SLUG-konfigurator/pages -f build_type=workflow >/dev/null
  ~/.local/bin/gh workflow run Pages -R tema-mail/xpeng-$SLUG-konfigurator
else
  git push -q
fi
echo "готово: https://tema-mail.github.io/xpeng-$SLUG-konfigurator/"
