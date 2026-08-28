import paramiko, sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.201', username='dji', password='<TRADEMIND_XAVIER_PASSWORD>', timeout=15, banner_timeout=15, auth_timeout=15)
print('CONNECTED'); sys.stdout.flush()

def ssh(cmd):
    _, out, err = c.exec_command(cmd, timeout=10)
    return out.read().decode('utf-8', errors='replace').strip()

print('health: ' + ssh('curl -s http://127.0.0.1:8080/health 2>/dev/null || echo NO_RESPONSE'))
print('factors: ' + ssh('curl -s http://127.0.0.1:8080/factors 2>/dev/null || echo NO_RESPONSE'))
print('pid: ' + ssh('pgrep -f server.py || echo DEAD'))
print('file_size: ' + ssh('wc -c < /home/dji/factor-worker-v1/server.py 2>/dev/null || echo 0'))
print('log: ' + ssh('tail -5 /tmp/factor.log 2>/dev/null || echo NO_LOG'))

import json as _json
payload = _json.dumps({"stock": "600519", "date": "20260731"})
test = ssh("curl -s -X POST http://127.0.0.1:8080/factor -H Content-Type:application/json -d '" + payload + "'")
print('factor_test: ' + test)

c.close()
print('DONE')
