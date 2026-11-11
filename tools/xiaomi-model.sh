#!/bin/bash
# Перенести конфигуратор модели Xiaomi из проекта сайта на общий движок и выложить
# Запуск: xiaomi-model.sh <slug> "<Xiaomi SU7>" "<SU7>"     (NOPUSH=1 – без выкладки)
set -e
SLUG=$1; CAR=$2; SHORT=$3
SRC=~/Sites/zeekr-9x-konfigurator
D=~/Sites/xiaomi-$SLUG-konfigurator
cd "$D"
[ -d .git ] || git init -q -b main
mkdir -p css js tools .github/workflows
cp $SRC/css/konfigurator.css css/; cp $SRC/js/konfigurator.js js/
cp $SRC/tools/xiaomi.py $SRC/tools/xiaomi-model.sh $SRC/tools/proverka.py $SRC/tools/ikonki-list.py tools/
cp $SRC/.github/workflows/pages.yml .github/workflows/; cp $SRC/robots.txt $SRC/.gitignore $SRC/.nojekyll .
sed "s/Zeekr 9X/$CAR/g" $SRC/index.html > index.html
SITE=~/Documents/evolution-car-by
mkdir -p raw
~/.local/node/bin/node --input-type=module -e "const m=await import('$SITE/src/content/models/xiaomi-$SLUG-config.ts');(await import('node:fs')).writeFileSync('raw/xiaomi-raw.json',JSON.stringify({...m}));" 2>/dev/null
python3 tools/xiaomi.py sobrat . "$CAR" "$SHORT" "xiaomi-$SLUG" "$SITE/public/img/xiaomi-$SLUG"
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

Посмотреть: https://tema-mail.github.io/lixiang-{slug}-konfigurator/ (закрыт от индексации).
Локально: `python3 -m http.server 8940`, затем http://127.0.0.1:8940/

## Что выбирает человек
Версия ({vers}); {', '.join(g.lower() for g in groups)}{('; дополнительно – ' + ', '.join(x.lower() for x in ex)) if ex else ''}.
Варианты взяты из официального конфигуратора Xiaomi (xiaomiev.com).

## Картинки
Официальные кадры конфигуратора Xiaomi EV: три вида кузова в студии (сбоку, спереди, сзади) для каждого сочетания
цвета и дисков и два вида салона для каждой отделки. Кадры собраны из слоёв сцены Xiaomi: фон, кузов, диски.
{len(d['have'])} сборок кузова, {len(d['int'])} вариантов салона, всё в WebP.

{embed}## Как обновить данные
Исходные кадры и переводы лежат в проекте сайта evolution-car-by (src/content/models/xiaomi-*-config.ts, public/img/xiaomi-*).
`tools/xiaomi-model.sh {slug} "{car}" "{car.replace('Xiaomi ', '')}"` переносит их на общий движок, проверяет и выкладывает (NOPUSH=1 – без выкладки).
Сайт xiaomiev.com с сервера в Нидерландах не открывается; новый съём – с адреса, которому сайт отвечает.
Движок и стили общие с конфигураторами Zeekr, мастер-копия – репозиторий tema-mail/zeekr-9x-konfigurator.

Кадры сняты 17.10.2026.
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
git commit -q -m "Конфигуратор $CAR: сборка без цен, кадры Xiaomi под каждую сборку, отправка менеджеру

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
if ! ~/.local/bin/gh repo view tema-mail/xiaomi-$SLUG-konfigurator >/dev/null 2>&1; then
  ~/.local/bin/gh repo create tema-mail/xiaomi-$SLUG-konfigurator --public --source . --push -d "Конфигуратор $CAR для встраивания на сайт" >/dev/null
  ~/.local/bin/gh api -X POST repos/tema-mail/xiaomi-$SLUG-konfigurator/pages -f build_type=workflow >/dev/null
  ~/.local/bin/gh workflow run Pages -R tema-mail/xiaomi-$SLUG-konfigurator
else
  git push -q
fi
echo "готово: https://tema-mail.github.io/xiaomi-$SLUG-konfigurator/"
