"""Phase 3: SSH into Xavier-02 and check environment."""
import paramiko, sys

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e

echo "===== Xavier-02 System Info ====="
uname -a
echo
cat /etc/os-release 2>/dev/null | head -5
echo

echo "===== Docker Status ====="
docker --version 2>/dev/null || echo "Docker NOT installed"
docker-compose --version 2>/dev/null || docker compose version 2>/dev/null || echo "docker-compose NOT installed"
echo

echo "===== Running Containers ====="
docker ps -a 2>/dev/null || echo "No containers"
echo

echo "===== Port 8001 check ====="
ss -tlnp | grep 8001 || echo "Port 8001 is free"
echo

echo "===== Network check ====="
ping -c 1 -W 2 192.168.1.101 2>/dev/null && echo "Master reachable" || echo "Master NOT reachable"
echo

echo "===== Disk ====="
df -h /
echo

echo "===== Memory ====="
free -h
echo

echo "===== GPU ====="
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || echo "No GPU detected"
echo

echo "===== Existing worker files ====="
ls -la /home/dji/ 2>/dev/null || echo "No home dir files"
ls -la /home/dji/worker-02/ 2>/dev/null || echo "No worker-02 dir yet"
echo

echo "===== Home directories ====="
ls /home/ 2>/dev/null
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=30)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
