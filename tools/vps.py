"""Запуск Playwright-кода в общем браузере на сервере в Амстердаме (служба vps-browser). На маке браузер не запускается.
Задание уходит на сервер, выполняется там в фоне (переживает обрыв ssh), результат забирается файлом.
  python3 vps.py run <файл.js> [секунд ожидания]      – функция вида async (page) => {…; return данные}
  from vps import run;  data = run(open('x.js').read())"""
import json, subprocess, sys, time, uuid

def ssh(cmd, inp=None, timeout=60):
    for a in range(5):
        try:
            r = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', '-o', 'BatchMode=yes', '-o', 'ControlMaster=auto', '-o', 'ControlPath=~/.ssh/cm-konfig-%C', '-o', 'ControlPersist=300', 'claude-vps', cmd], input=inp, capture_output=True, text=True, timeout=timeout)
            if r.returncode != 255: return r
        except subprocess.TimeoutExpired: pass
        time.sleep(4 + a * 4)
    raise SystemExit('сервер не отвечает по ssh')

def run(code, wait=900):
    job = 'j' + uuid.uuid4().hex[:10]; d = 'tools/konfig'
    ssh(f'mkdir -p {d}/jobs && cat > {d}/jobs/{job}.js', inp=code)
    if ssh(f'test -f {d}/srv_run.py && echo y').stdout.strip() != 'y':
        ssh(f'cat > {d}/srv_run.py', inp=open(__file__.replace('vps.py', 'srv_run.py')).read())
    # запуск один раз, даже если ssh повторит команду: метка .started
    ssh(f'cd {d} && [ -f jobs/{job}.started ] || {{ touch jobs/{job}.started; setsid nohup python3 srv_run.py jobs/{job}.js jobs/{job}.json > jobs/{job}.log 2>&1 < /dev/null & }}')
    t0 = time.time()
    while time.time() - t0 < wait:
        time.sleep(6)
        r = ssh(f'test -f {d}/jobs/{job}.json && cat {d}/jobs/{job}.json', timeout=120)
        if r.returncode == 0 and r.stdout.strip():
            ssh(f'rm -f {d}/jobs/{job}.js {d}/jobs/{job}.json {d}/jobs/{job}.log {d}/jobs/{job}.started')
            res = json.loads(r.stdout)
            if not res.get('ok'): raise RuntimeError(json.dumps(res.get('error') or res.get('result'), ensure_ascii=False)[:800])
            return res['result']
    raise SystemExit('задание на сервере не завершилось за %d с' % wait)

if __name__ == '__main__' and sys.argv[1] == 'run':
    r = run(open(sys.argv[2]).read(), int(sys.argv[3]) if len(sys.argv) > 3 else 900)
    print(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False, indent=1))
