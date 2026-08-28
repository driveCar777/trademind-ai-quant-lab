"""Step 4: Deep health + API verification on Xavier."""
import subprocess, sys
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
echo "===== Step 4: Deep Health + API Verification ====="

echo
echo "===== 4.1 Container status ====="
docker ps | grep indicator
echo

echo "===== 4.2 /health x5 (stability) ====="
for i in 1 2 3 4 5; do
  RESP=$(curl -s -w "\n%{http_code}" http://192.168.1.200:8000/health)
  CODE=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | head -1)
  echo "[$i] HTTP=$CODE $BODY"
done

echo
echo "===== 4.3 Response time (5 calls) ====="
for i in 1 2 3 4 5; do
  TIME=$(curl -s -o /dev/null -w "%{time_total}" http://192.168.1.200:8000/health)
  echo "[$i] ${TIME}s"
done

echo
echo "===== 4.4 GET / (root) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/ 2>&1

echo
echo "===== 4.5 GET /docs (Swagger) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/docs 2>&1 | head -5

echo
echo "===== 4.6 GET /openapi.json ====="
curl -s http://192.168.1.200:8000/openapi.json 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    paths = list(data.get('paths', {}).keys())
    print('Endpoints found:')
    for p in paths:
        methods = [m.upper() for m in data['paths'][p].keys()]
        print(f'  {\" \".join(methods)} {p}')
    print(f'Total: {len(paths)} endpoints')
except:
    print('Failed to parse OpenAPI')
"

echo
echo "===== 4.7 GET /indicators (list supported) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/indicators 2>&1

echo
echo "===== 4.8 POST /task (RSI test) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" -X POST http://192.168.1.200:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"indicator","symbol":"XAUUSD","indicators":["RSI"],"params":{"rsi_period":14},"data":{"close":[44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]}}' 2>&1

echo
echo "===== 4.9 GET /task/{id} (if task created) ====="
# Try to get the task ID from the POST response above
TASK_ID=$(curl -s -X POST http://192.168.1.200:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"indicator","symbol":"EURUSD","indicators":["RSI"],"params":{"rsi_period":14},"data":{"close":[1.1,1.12,1.11,1.13,1.14,1.15,1.16,1.17,1.18,1.19,1.20,1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28,1.29]}}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('task_id',''))" 2>/dev/null || true)
echo "Task ID: $TASK_ID"
if [ -n "$TASK_ID" ]; then
  curl -s -w "\nHTTP_CODE=%{http_code}\n" "http://192.168.1.200:8000/task/$TASK_ID" 2>&1
else
  echo "No task_id returned (endpoint may differ)"
fi

echo
echo "===== 4.10 POST /calculate (direct indicator calc) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" -X POST http://192.168.1.200:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"indicator":"RSI","data":{"close":[44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},"params":{"period":14}}' 2>&1

echo
echo "===== 4.11 GET /task/list ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/task/list 2>&1

echo
echo "===== 4.12 GET /metrics (Prometheus) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/metrics 2>&1 | head -15

echo
echo "===== 4.13 Container uptime & resource ====="
docker stats indicator-worker-01 --no-stream 2>&1

echo
echo "===== 4.14 Port check ====="
ss -tlnp | grep 8000

echo
echo "===== 4.15 Final health ====="
curl -s http://192.168.1.200:8000/health 2>&1 | python3 -m json.tool
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=120)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
