"""Step 1: Xavier Docker environment check via SSH."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

CMDS = """
echo "===== OS ====="
cat /etc/nv_tegra_release 2>/dev/null || echo "nv_tegra_release not found"
lsb_release -a 2>/dev/null || echo "lsb_release not found"

echo
echo "===== Docker ====="
docker version 2>&1
docker info 2>&1

echo
echo "===== Compose ====="
docker compose version 2>&1 || true
docker-compose --version 2>&1 || true

echo
echo "===== NVIDIA Runtime ====="
docker info 2>&1 | grep -i runtime || true

echo
echo "===== Docker Service ====="
systemctl status docker --no-pager 2>&1

echo
echo "===== Network ====="
hostname -I
ip addr 2>&1
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("192.168.1.200", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=90)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err)
client.close()
