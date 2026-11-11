#!/bin/bash
# Собрать и выложить конфигуратор модели Xiaomi. Перед этим снять raw/xiaomi-api.json (tools/xiaomi_snyat.py <goodsId> .)
# Запуск: xiaomi-model.sh <slug> "<Xiaomi SU7>" "<SU7>"     (NOPUSH=1 – без выкладки)
set -e
SLUG=$1; CAR=$2; SHORT=$3
SRC=~/Sites/zeekr-9x-konfigurator
D=~/Sites/xiaomi-$SLUG-konfigurator
cd "$D"
[ -d .git ] || git init -q -b main
mkdir -p css js tools .github/workflows
cp $SRC/css/konfigurator.css css/; cp $SRC/js/konfigurator.js js/
rm -f tools/proverka.py tools/xiaomi.py; cp $SRC/tools/xiaomi_api.py $SRC/tools/xiaomi_snyat.py $SRC/tools/xiaomi-model.sh $SRC/tools/proverka_vps.py $SRC/tools/proverka_kadrov.py $SRC/tools/vps.py $SRC/tools/srv_run.py $SRC/tools/ikonki-list.py tools/
cp $SRC/.github/workflows/pages.yml .github/workflows/; cp $SRC/robots.txt $SRC/.gitignore $SRC/.nojekyll .
sed "s/Zeekr 9X/$CAR/g" $SRC/index.html > index.html
[ -f raw/xiaomi-api.json ] || { echo "нет raw/xiaomi-api.json: сначала python3 tools/xiaomi_snyat.py <goodsId> ."; exit 1; }
python3 tools/xiaomi_api.py sobrat . "$CAR" "$SHORT" "xiaomi-$SLUG"
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

Посмотреть: https://tema-mail.github.io/lixiang-{slug}-konfigurator/ (закрыт от индексации).
Локально: `python3 -m http.server 8940`, затем http://127.0.0.1:8940/

## Что выбирает человек
Версия ({vers}); {', '.join(g.lower() for g in groups)}{('; дополнительно – ' + ', '.join(x.lower() for x in ex)) if ex else ''}.
Варианты и несовместимые сочетания взяты из официального конфигуратора Xiaomi (xiaomiev.com).

## Картинки
Официальные кадры конфигуратора Xiaomi EV в студии: пять видов кузова (спереди, сбоку, сзади, строго спереди и строго сзади)
для каждого сочетания версии, цвета и дисков и два вида салона для каждой отделки. Готовых кадров Xiaomi не отдаёт:
кадр собирается из слоёв сцены 5000×2812 по правилу самого сайта (фон, кузов, диски), затем машина вырезается крупно, 1600×1000.
Значки цвета, дисков и салона – официальные. Китайский шильдик на крышке багажника закрашен.
{len(d['have'])} сборок кузова, {len(d['int'])} вариантов салона, всё в WebP.

{embed}## Как обновить данные
1. `python3 tools/xiaomi_snyat.py <goodsId> .` – пишет `raw/xiaomi-api.json` (goodsId – из адреса xiaomiev.com/configurator/select-version?goodsId=…).
   API открытый, браузер не нужен; с сервера в Нидерландах сайт не открывается, запрос идёт напрямую.
2. `tools/xiaomi-model.sh {slug} "{car}" "{car.replace('Xiaomi ', '')}"` – слои, кадры, данные, проверки и выкладка (NOPUSH=1 – без выкладки).
   Новое китайское название сборка не пропустит: перевод добавить в RU в tools/xiaomi_api.py. Координаты закраски шильдика – MASKS там же.
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
