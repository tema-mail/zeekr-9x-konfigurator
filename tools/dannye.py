import json, re, sys, os
m=json.load(open(os.environ.get('Z9_MODEL','model.json')))
O=m['opts']
RU={
 # кузов
 'Z011PC002':('Чёрный «Полярная ночь»','极夜黑'),'Z011PC003':('Белый «Полярный день»','极昼白'),'Z011PC045':('Коричневый «Исследователь»','探野棕'),
 'Z011PC004':('Серебристый «Ледник»','冰川银'),'Z011PC005':('Серый «Звёздный свод»','星穹灰'),'Z011PC006':('Фиолетовый «Тёмная ночь»','暗夜紫'),
 # обвес
 'Z011PC021':('Матовый серебристый хром','решётка, молдинги и декор кузова'),'Z011PC020':('Решётка в цвет кузова','декор в цвет машины'),
 'Z011PC022':('Глянцевый серебристый хром','яркий хром решётки и декора'),'Z011PC023':('Чёрный декор «Яохэй»','решётка и декор в чёрном'),
 'Z011PC038':('Пакет «Яохэй»','чёрный декор и чёрные кованые диски'),
 # диски
 'Z011PC026':('22″ кованые «Синъяо»','4-поршневые суппорты'),'Z011PC027':('22″ кованые «Синъяо»','6-поршневые оранжевые суппорты'),
 'Z011PC028':('22″ кованые зеркальные','6-поршневые оранжевые суппорты'),'Z011PC039':('22″ кованые чёрные «Яохэй»','6-поршневые оранжевые суппорты'),
 # салон
 'Z011PC008':('Белый «Полярный»','极地白'),'Z011PC007':('Синий «Лунная тень»','月影蓝'),'Z011PC009':('Коричневый «Янтарь»','琥珀棕'),
 'Z011PC047':('Бордовый «Бургундия»','勃艮第红'),'Z011PC040':('Чёрный с золотом «Яохэй»','曜夜鎏金'),
 # экран
 'Z011PC033':('Два экрана 16″','водителю и пассажиру'),'Z011PC016':('Один экран 16″','по центру'),
 # уровень версии
 'Z011PC010':('55 кВт·ч',''),'Z011PC001':('70 кВт·ч',''),'Z011PC011':('H7','1 лидар · NVIDIA Thor-U · 700 TOPS'),'Z011PC012':('H9','5 лидаров · 2× NVIDIA Thor-U · 1400 TOPS'),
 'Z011PC036':('2 мотора, полный привод',''),'Z011PC037':('3 мотора, полный привод',''),
 # доп
 'Z011PC017':('Поворотные кресла второго ряда',''),'Z011PC018':('Электрический фаркоп',''),
}
VN={'54':('Max','6'),'55':('Ultra','6'),'56':('Hyper','6'),'57':('«Яохэй»','6'),'84':('Ultra','5'),'85':('Hyper','5'),'86':('«Яохэй»','5')}
TAG={'Max':'Начальная','Ultra':'Выбор батареи и дисков','Hyper':'3 мотора, всё включено','«Яохэй»':'Чёрная спецверсия'}
def ico(pc):
    return f'img/zeekr-9x/options/{pc}.webp'
vers=[]
for V in m['vers']:
    name,seats=VN[V['id']]
    keys=list(V['combos'])
    first=V['combos'][keys[0]]
    lvl=V['level']
    bats=[{'id':pc,'name':RU[pc][0],'def':bool(dflt)} for pc,_,dflt in lvl['Z011SC001']['opts']]
    adas=[{'id':pc,'name':RU[pc][0],'note':RU[pc][1],'def':bool(dflt)} for pc,_,dflt in lvl['Z011SC004']['opts']]
    drive=RU[lvl['Z011SC016']['opts'][0][0]][0]
    ranges={}
    for key in keys:
        bat=key.split('_')[0]
        for pc,o in O.items():
            c=o['comment'].get(V['id']+'|'+key)
            if c and o['sku']=='Z011SC013' and pc in [w for w,_ in V['combos'][key]['avail']['wheel']]:
                mm=re.findall(r'(\d+)km',c); ranges[bat]={'ev':int(mm[0]),'total':int(mm[1])}
    def lst(k): return [{'id':pc,'def':dflt} for pc,dflt in first['avail'][k]]
    vers.append({'id':V['id'],'name':name,'seats':int(seats),'tag':TAG[name],'drive':drive,'batteries':bats,'adas':adas,
      'paints':lst('paint'),'kits':lst('kit'),'wheels':lst('wheel'),'interiors':lst('int'),'screens':lst('screen'),
      'extras':[{'id':pc,'def':dflt} for pc,dflt in first['extra']],'ranges':ranges})
options={}
for pc in RU:
    o=O.get(pc,{})
    options[pc]={'name':RU[pc][0],'note':RU[pc][1],'icon':ico(pc) if o.get('cover') else None,'mutex':o.get('mutex',[]),'cascade':o.get('cascade',[])}
import os
IMG=os.environ.get('Z9_IMG','img/zeekr-9x')
have={c:[s for s in ['hero','front34','side','rear34'] if os.path.exists(f'{IMG}/ext/{c}--{s}.webp')] for c in m['ext']}
data={'car':'Zeekr 9X','have':have,'versions':vers,'options':options,'ext':m['ext'],'int':m['int'],
 'paths':{'ext':'img/zeekr-9x/ext/{code}--{shot}.webp','int':'img/zeekr-9x/int/{code}.webp'},
 'shots':[{'id':'hero','label':'Студия'},{'id':'front34','label':'Спереди ¾'},{'id':'side','label':'Сбоку'},{'id':'rear34','label':'Сзади ¾'},{'id':'int','label':'Салон'}]}
open(sys.argv[1],'w').write('/* Данные конфигуратора Zeekr 9X. Собрано из официального конфигуратора zeekrlife.com (модель 10, 2025–2026 модельный год), '+
  'снято 11.11.2026 скриптом tools/. Цены намеренно не хранятся. */\nwindow.ZEEKR_9X = '+json.dumps(data,ensure_ascii=False,indent=1)+';\n')
print('версий',len(vers)); [print(v['id'],v['name'],v['seats'],[b['name'] for b in v['batteries']],[a['name'] for a in v['adas']],v['ranges'],len(v['paints']),len(v['kits']),len(v['wheels']),len(v['interiors']),[e['id'] for e in v['extras']]) for v in vers]
