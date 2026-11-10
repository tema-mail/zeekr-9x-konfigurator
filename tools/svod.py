import json, itertools
d=json.load(open('z9x-raw.json'))
SC={'paint':'Z011SC002','kit':'Z011SC012','wheel':'Z011SC013','int':'Z011SC003','screen':'Z011SC008'}
opts={}   # productCode -> info
vers=[]
for v in d['versions']:
    V={'id':v['id'],'name':v['name'],'group':v['group'],'level':v['level'],'combos':{}}
    for key,items in v['items'].items():
        avail={k:[] for k in SC}; extra=[]
        for g in items:
            for s in g['skuResultList']:
                for x in s['subSkuResultList']:
                    pc=x['productCode']
                    opts.setdefault(pc,{'pc':pc,'cn':x['subSkuName'],'sku':s['skuCode'],'skuName':s['itemName'],'cover':x['coverImg'],'detail':x['detailImg'],'mutex':set(),'cascade':set(),'comment':{}})
                    o=opts[pc]; o['mutex'].update(x['mutexProduct']); o['cascade'].update(x['cascadeProduct'])
                    if x.get('configComment'): o['comment'][v['id']+'|'+key]=x['configComment']
                    if not x['isValidOption']: continue
                    for k,sc in SC.items():
                        if s['skuCode']==sc: avail[k].append((pc,bool(x['isDefaultSelected'])))
                    if s['skuCode'] in ('Z011SC009','Z011SC010'): extra.append((pc,bool(x['isDefaultSelected'])))
        V['combos'][key]={'avail':avail,'extra':extra}
    vers.append(V)
def ok(sel):
    for a in sel:
        for b in sel:
            if a!=b and (b in opts[a]['mutex'] or a in opts[b]['mutex']): return False
    return True
ext=set(); intr=set(); where={}
for V in vers:
    for key,c in V['combos'].items():
        adas=key.split('_')[-1]
        av=c['avail']
        for p,_ in av['paint']:
            for k,_ in av['kit']:
                for w,_ in av['wheel']:
                    if not ok([p,k,w]): continue
                    if opts[k]['cascade'] and w not in opts[k]['cascade']: continue
                    code=f'{adas}_{p}_{k}_{w}'; ext.add(code); where.setdefault(code,V['id'])
        for i,_ in av['int']:
            for s,_ in av['screen']:
                code=f'{i}_{adas}_{s}'; intr.add(code); where.setdefault('I'+code,V['id'])
print('внешних сборок',len(ext),'салонов',len(intr))
json.dump({'opts':{k:{**v,'mutex':sorted(v['mutex']),'cascade':sorted(v['cascade'])} for k,v in opts.items()},'vers':vers,'ext':sorted(ext),'int':sorted(intr),'where':where},open('model.json','w'),ensure_ascii=False,indent=0)
