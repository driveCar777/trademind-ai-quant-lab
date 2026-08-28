"""Step 3: docker-compose up + health check on Xavier."""
import subprocess, sys
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
cd /home/dji/worker-01/indicator-worker

echo "===== Step 3: docker-compose up -d ====="
docker-compose up -d 2>&1
echo
echo "Compose exit: $?"

echo
echo "===== Wait 8s for startup ====="
sleep 8

echo
echo "===== Container status ====="
docker ps -a | grep -E "indicator|NAMES" || docker ps -a

echo
echo "===== Container logs ====="
docker logs indicator-worker 2>&1 | tail -30

echo
echo "===== Health check (curl) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://192.168.1.200:8000/health 2>&1

echo
echo "===== Health check (localhost) ====="
curl -s -w "\nHTTP_CODE=%{http_code}\n" http://localhost:8000/health 2>&1

echo
echo "===== Port binding ====="
ss -tlnp | grep 8000 || netstat -tlnp 2>/dev/null | grep 8000 || echo "port check done"

echo
echo "===== Container inspect ====="
docker inspect indicator-worker --format 'Status={{.State.Status}} Health={{.State.Health.Status}} StartedAt={{.State.StartedAt}}' 2>/dev/null || echo "inspect failed"

echo
echo "===== Docker health state ====="
docker inspect indicator-worker --format '{{json .State.Health}}' 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "no health data yet"

echo
echo "===== Disk ====="
df -h /
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
