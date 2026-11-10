"""model.json -> js/zeekr-data.js для конфигуратора. Цен нет намеренно.
Запуск: python3 dannye.py model.json js/zeekr-data.js "Zeekr 9X" 9X [img-папка]
Группы версий (места у 9X) задаются в GROUPS ниже по номеру группы Zeekr."""
import json, os, re, sys
m = json.load(open(sys.argv[1])); OUT = sys.argv[2]; CAR = sys.argv[3]; SHORT = sys.argv[4]
IMG = sys.argv[5] if len(sys.argv) > 5 else 'img/zeekr'
O = m['opts']

RU = {
 # кузов
 '极夜黑': ('Чёрный «Полярная ночь»', ''), '极昼白': ('Белый «Полярный день»', ''), '探野棕': ('Коричневый «Исследователь»', ''),
 '冰川银': ('Серебристый «Ледник»', ''), '星穹灰': ('Серый «Звёздный свод»', ''), '暗夜紫': ('Фиолетовый «Тёмная ночь»', ''),
 '云珀红': ('Янтарно-красный', ''), '月海灰': ('Тёмно-серый «Лунное море»', ''), '玄武灰': ('Светло-серый «Базальт»', ''),
 '猎空蓝': ('Голубой «Охотник»', ''), '哑光星际灰': ('Матовый серый «Звёздный»', 'матовая плёнка'),
 # декор
 '哑光银镀铬外观套件': ('Матовый серебристый хром', 'решётка, молдинги и декор кузова'), '车身同色格栅套件': ('Решётка в цвет кузова', 'декор в цвет машины'),
 '高亮银镀铬外观套件': ('Глянцевый серебристый хром', 'яркий хром решётки и декора'), '曜黑外观套件': ('Чёрный декор «Яохэй»', 'решётка и декор в чёрном'),
 '曜黑套装': ('Пакет «Яохэй»', 'чёрный декор и чёрные кованые диски'),
 '曜夜外观套件': ('Чёрный декор «Яое»', 'решётка и декор в чёрном'), '曜夜套装': ('Пакет «Яое»', 'чёрный декор и чёрные диски'),
 # диски
 '20英寸星脉轮毂带四活塞卡钳': ('20″ «Синмай»', '4-поршневые суппорты'), '21英寸星脉轮毂带四活塞卡钳': ('21″ «Синмай»', '4-поршневые суппорты'),
 '22英寸星耀锻造轮毂带四活塞卡钳': ('22″ кованые «Синъяо»', '4-поршневые суппорты'), '22英寸星耀锻造轮毂带六活塞橙色卡钳': ('22″ кованые «Синъяо»', '6-поршневые оранжевые суппорты'),
 '22英寸镜面锻造轮毂带六活塞橙色卡钳': ('22″ кованые зеркальные', '6-поршневые оранжевые суппорты'), '22英寸曜黑锻造轮毂带六活塞橙色卡钳': ('22″ кованые чёрные «Яохэй»', '6-поршневые оранжевые суппорты'),
 '20英寸光曜轮毂': ('20″ «Гуанъяо»', 'без Brembo'), '21英寸星曜运动轮毂带Brembo四活塞卡钳': ('21″ спортивные «Синъяо»', 'Brembo, 4 поршня'),
 '21英寸双曜轮毂带Brembo四活塞卡钳': ('21″ «Шуанъяо»', 'Brembo, 4 поршня'), '21英寸空气动力学轮毂带Brembo四活塞卡钳': ('21″ аэродинамические', 'Brembo, 4 поршня'),
 '22英寸辉曜轮毂带Brembo四活塞卡钳': ('22″ «Хуэйяо»', 'Brembo, 4 поршня'), '22英寸辉曜轮毂带Brembo四活塞卡钳+双阀CCD电磁减振器': ('22″ «Хуэйяо»', 'Brembo, 4 поршня + амортизаторы CCD'),
 '22英寸曜夜轮毂带Brembo四活塞卡钳': ('22″ чёрные «Яое»', 'Brembo, 4 поршня'), '22英寸曜夜轮毂带Brembo四活塞卡钳+双阀CCD电磁减振器': ('22″ чёрные «Яое»', 'Brembo, 4 поршня + амортизаторы CCD'),
 '22英寸曜夜轮毂带Brembo六活塞卡钳': ('22″ чёрные «Яое»', 'Brembo, 6 поршней'), '22英寸凌波锻造轮毂带Brembo六活塞卡钳': ('22″ кованые «Линбо»', 'Brembo, 6 поршней'),
 '22英寸凌波锻造熏黑轮毂带Brembo六活塞卡钳': ('22″ кованые «Линбо», тёмные', 'Brembo, 6 поршней'),
 # салон
 '极地白': ('Белый «Полярный»', ''), '月影蓝': ('Синий «Лунная тень»', ''), '琥珀棕': ('Коричневый «Янтарь»', ''), '勃艮第红': ('Бордовый «Бургундия»', ''),
 '曜夜鎏金': ('Чёрный с золотом «Яохэй»', ''), '棕黑': ('Коричневый с чёрным', ''), '白黑': ('Белый с чёрным', ''), '纯黑': ('Полностью чёрный', ''),
 '赤影红': ('Красный «Алая тень»', ''), '黑橙': ('Чёрный с оранжевым', ''),
 # экран, кресла
 '中控双联屏': ('Два экрана', 'водителю и пассажиру'), '16英寸中控单屏': ('Один экран 16″', 'по центру'),
 '一体式运动座椅': ('Спортивные ковши', 'цельные спинки'), '栖云舒享座椅套装': ('Комфортные кресла «Циюнь»', 'с массажем и вентиляцией'),
 # дополнительно
 'Naim殿堂之声音响系统': ('Аудиосистема Naim', ''), '主动稳定杆': ('Активные стабилизаторы', ''), '二排双旋转座椅': ('Поворотные кресла второго ряда', ''),
 '六座悦享包': ('6-местный салон', 'два кресла во втором ряду'), '后排吸顶屏套装': ('Потолочный экран для задних', ''), '智能电动拖车钩': ('Электрический фаркоп', ''),
 '电动踏板': ('Выдвижные пороги', ''), '飞翼式滑移屏': ('Выдвижной экран «Фэйи»', ''),
 # уровень версии
 '55kWh电池': ('55 кВт·ч', ''), '70kWh电池': ('70 кВт·ч', ''), '千里浩瀚H7': ('H7', '1 лидар · NVIDIA Thor-U · 700 TOPS'),
 '千里浩瀚H9': ('H9', 'несколько лидаров · 2× NVIDIA Thor-U · 1400 TOPS'),
 '双电机四驱': ('2 мотора, полный привод', ''), '三电机四驱': ('3 мотора, полный привод', ''),
}
VNAME = {'Max': ('Max', 'Начальная'), 'Ultra+': ('Ultra+', 'Лучшее шасси'), 'Ultra': ('Ultra', 'Выбор батареи и дисков'), 'Hyper': ('Hyper', '3 мотора, всё включено'),
         '曜黑': ('«Яохэй»', 'Чёрная спецверсия'), '曜影': ('Shadow «Яоин»', '3 мотора, спортивная')}
GROUPS = {'10': {'3': ('6 мест', 'второй ряд – два кресла'), '4': ('5 мест', 'второй ряд – диван')}}
MID = sys.argv[6] if len(sys.argv) > 6 else ''

def ru(cn):
    if cn not in RU: raise SystemExit('нет перевода: ' + cn)
    return RU[cn]

options = {}
for pc, o in O.items():
    if o['cn'] not in RU: continue
    n, note = ru(o['cn'])
    icon = f'{IMG}/options/{pc}.webp' if (o.get('cover') and os.path.exists(f'{IMG}/options/{pc}.webp')) else None
    options[pc] = {'name': n, 'note': note, 'icon': icon, 'mutex': o['mutex'], 'cascade': o['cascade'], 'sku': o['sku']}

vers = []
for V in m['vers']:
    key = next((k for k in VNAME if k in V['cn'] and not (k == 'Ultra' and 'Ultra+' in V['cn'])), None)
    if not key: raise SystemExit('нет имени версии: ' + V['cn'])
    level, drive = [], ''
    for sku, l in V['level'].items():
        if l['cn'] == '电池容量': level.append({'sku': sku, 'role': 'battery', 'opts': [{'id': o['id'], 'def': o['def']} for o in l['opts']]})
        elif l['cn'] == '辅助驾驶方案': level.append({'sku': sku, 'role': 'adas', 'opts': [{'id': o['id'], 'def': o['def']} for o in l['opts']]})
        elif l['cn'] == '驱动系统': drive = ru(l['opts'][0]['cn'])[0]
    level.sort(key=lambda x: x['role'] != 'battery')
    bat_sku = next(x['sku'] for x in level if x['role'] == 'battery')
    wheel_ids = [o['id'] for s in V['secs'] if s['role'] == 'wheel' for o in s['opts']]
    ranges = {}
    for key2 in V['levelKeys']:
        bat = next(p for p in key2.split('_') if O[p]['sku'] == bat_sku)
        for w in wheel_ids:
            c = O[w]['comment'].get(key2)
            if c:
                mm = re.findall(r'(\d+)km', c)
                if len(mm) >= 2: ranges.setdefault(bat, {})[w] = {'ev': int(mm[0]), 'total': int(mm[1])}
    secs = [{'sku': s['sku'], 'role': s['role'], 'opts': [{'id': o['id'], 'def': o['def'], 'promo': o['promo'], 'promoTo': o.get('promoTo', '')} for o in s['opts'] if o['id'] in options]} for s in V['secs']]
    secs = [s for s in secs if s['opts']]
    gl = GROUPS.get(MID, {}).get(V['group'])
    vers.append({'id': V['id'], 'name': VNAME[key][0], 'tag': VNAME[key][1], 'group': V['group'] if gl else '', 'drive': drive,
                 'level': level, 'secs': secs, 'vehicleSkus': V['vehicleSkus'], 'interiorSkus': V['interiorSkus'], 'ranges': ranges})
groups = [{'id': g, 'label': l[0], 'sub': l[1]} for g, l in GROUPS.get(MID, {}).items()]
have = {c: [s for s in ['hero', 'front34', 'side', 'rear34'] if os.path.exists(f'{IMG}/ext/{c}--{s}.webp')] for c in m['ext']}
have = {c: s for c, s in have.items() if 'hero' in s}
ints = [c for c in m['int'] if os.path.exists(f'{IMG}/int/{c}.webp')]
data = {'car': CAR, 'short': SHORT, 'groups': groups, 'versions': vers, 'options': options, 'have': have, 'int': ints,
        'paths': {'ext': IMG + '/ext/{code}--{shot}.webp', 'int': IMG + '/int/{code}.webp'},
        'shots': [{'id': 'hero', 'label': 'Студия'}, {'id': 'front34', 'label': 'Спереди ¾'}, {'id': 'side', 'label': 'Сбоку'}, {'id': 'rear34', 'label': 'Сзади ¾'}, {'id': 'int', 'label': 'Салон'}]}
open(OUT, 'w').write('/* Данные конфигуратора ' + CAR + ': официальный конфигуратор zeekrlife.com, снято 11.11.2026 скриптами tools/. Цен нет намеренно. */\n'
                     'window.ZEEKR_CFG = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(CAR, 'версий', len(vers), 'сборок с кадрами', len(have), 'салонов', len(ints))
