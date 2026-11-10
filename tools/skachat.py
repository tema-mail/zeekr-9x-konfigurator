import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
m=json.load(open('model.json'))
B='https://zeekrlife-oss.zeekrlife.com/showcar/'
jobs=[]
os.makedirs('raw/ext',exist_ok=True); os.makedirs('raw/int',exist_ok=True); os.makedirs('raw/ico',exist_ok=True)
for code in m['ext']:
    v=m['where'][code]
    jobs.append((f'{B}vehicle/10/{v}/{code}.png',f'raw/ext/{code}--hero.png'))
    jobs.append((f'{B}carPic/left_front/10/{v}/v5/{code}.png',f'raw/ext/{code}--front34.png'))
    jobs.append((f'{B}carPic/left/10/{v}/v4/{code}.png',f'raw/ext/{code}--side.png'))
    jobs.append((f'{B}carPic/right_rear/10/{v}/v5/{code}.png',f'raw/ext/{code}--rear34.png'))
for code in m['int']:
    v=m['where']['I'+code]
    jobs.append((f'{B}Interior/10/{v}/{code}.png',f'raw/int/{code}.png'))
for pc,o in m['opts'].items():
    for k in ('cover','detail'):
        if o.get(k): jobs.append((o[k],f'raw/ico/{pc}--{k}.png'))
def get(j):
    u,f=j
    if os.path.exists(f) and os.path.getsize(f)>2000: return 'skip'
    for a in range(4):
        r=subprocess.run(['curl','-s','--max-time','120','-o',f+'.part','-w','%{http_code}',u],capture_output=True,text=True)
        if r.stdout=='200' and os.path.getsize(f+'.part')>2000:
            os.replace(f+'.part',f); return 'ok'
    return 'FAIL '+r.stdout+' '+u
with ThreadPoolExecutor(6) as ex: res=list(ex.map(get,jobs))
fails=[r for r in res if r.startswith('FAIL')]
print(len(jobs),'задач, ошибок',len(fails)); print('\n'.join(fails[:20]))
