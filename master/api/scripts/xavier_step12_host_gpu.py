"""Step 1.2: Jetson Host GPU verification (no nvidia-smi)."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
echo "===== Step 1.2: Jetson Host GPU Verification ====="

echo
echo "===== JetPack / OS ====="
cat /etc/nv_tegra_release 2>/dev/null || echo "nv_tegra_release not found"
uname -a

echo
echo "===== tegrastats ====="
which tegrastats 2>/dev/null || echo "tegrastats: NOT FOUND"
timeout 3 tegrastats 2>&1 || echo "tegrastats sample ended"

echo
echo "===== CUDA Toolkit ====="
ls -la /usr/local/cuda 2>/dev/null || echo "/usr/local/cuda: NOT FOUND"
ls -la /usr/local/cuda/bin/nvcc 2>/dev/null || true
nvcc --version 2>&1 || echo "nvcc: NOT FOUND"

echo
echo "===== CUDA deviceQuery ====="
DQ_DIR=""
for d in \
  /usr/local/cuda/samples/1_Utilities/deviceQuery \
  /usr/local/cuda-10.0/samples/1_Utilities/deviceQuery \
  /usr/src/cuda/samples/1_Utilities/deviceQuery \
  /usr/src/cuda-10.0/samples/1_Utilities/deviceQuery; do
  if [ -d "$d" ]; then DQ_DIR="$d"; break; fi
done

if [ -n "$DQ_DIR" ]; then
  echo "Found deviceQuery at: $DQ_DIR"
  cd "$DQ_DIR"
  make clean >/dev/null 2>&1 || true
  make 2>&1 | tail -15
  echo "--- deviceQuery output ---"
  ./deviceQuery 2>&1 | tail -30
else
  echo "deviceQuery sample: NOT FOUND in common paths"
  find /usr/local/cuda /usr/src -maxdepth 5 -name deviceQuery.cpp 2>/dev/null | head -5 || true
fi

echo
echo "===== GPU devices (Jetson) ====="
ls -la /dev/nvhost-gpu /dev/nvhost-ctrl-gpu 2>/dev/null || true
lsmod | grep -iE 'nvidia|tegra' | head -10 || true

echo
echo "===== Docker (unchanged, for Gate context) ====="
systemctl is-active docker
docker-compose --version 2>&1 || true
docker info 2>&1 | grep -i runtime || true
hostname -I | tr ' ' '\n' | grep 192.168.1.200 || true
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=300)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err)
client.close()
