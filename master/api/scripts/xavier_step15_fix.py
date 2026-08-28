"""Step 1.5: Fix NVIDIA runtime on JetPack R32.1 Xavier."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -x
SUDO='echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S'

echo "===== Step 1.5: NVIDIA Runtime Fix (JetPack R32.1) ====="

echo
echo "===== Clean bad NVIDIA container apt sources ====="
eval $SUDO rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list
eval $SUDO rm -f /etc/apt/sources.list.d/libnvidia-container.list
eval $SUDO rm -f /etc/apt/sources.list.d/nvidia-container-runtime.list
ls -la /etc/apt/sources.list.d/ 2>/dev/null | grep -i nvidia || echo "no nvidia list files"

echo
echo "===== Installed nvidia/l4t packages ====="
dpkg -l | grep -iE 'nvidia-docker|nvidia-l4t|nvidia-container' | head -30

echo
echo "===== apt-cache search nvidia-docker ====="
apt-cache search nvidia-docker 2>&1 | head -10
apt-cache policy nvidia-docker2 2>&1 | head -10

echo
echo "===== GPU driver probe ====="
lsmod | grep -i nvidia || echo "no nvidia kernel module loaded"
ls -la /dev/nvhost* 2>/dev/null | head -5 || true
ls -la /usr/bin/nvidia-smi /usr/sbin/nvidia-smi 2>/dev/null || true
which tegrastats 2>/dev/null || true
tegrastats --help 2>&1 | head -2 || true

echo
echo "===== Install nvidia-docker2 ====="
eval $SUDO apt-get update -qq 2>&1 | tail -8
eval $SUDO apt-get install -y nvidia-docker2 2>&1 | tail -20

echo
echo "===== Check runtime binaries after install ====="
which nvidia-container-runtime 2>/dev/null || echo "nvidia-container-runtime: NOT FOUND"
which nvidia-container-toolkit 2>/dev/null || true
ls -la /usr/bin/nvidia-container-runtime 2>/dev/null || true
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json"

echo
echo "===== Restart Docker ====="
eval $SUDO systemctl restart docker
sleep 4
systemctl is-active docker

echo
echo "===== Gate Re-check ====="
docker version 2>&1 | head -6
docker-compose --version 2>&1 || true
docker info 2>&1 | grep -i runtime || true
hostname -I | tr ' ' '\n' | grep 192.168.1.200 || true

echo
echo "===== Optional GPU container smoke (if nvidia runtime exists) ====="
if docker info 2>&1 | grep -qi nvidia; then
  docker run --rm --runtime=nvidia busybox echo "nvidia runtime ok" 2>&1 || true
else
  echo "SKIP gpu container test - no nvidia runtime"
fi
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=600)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err)
client.close()
