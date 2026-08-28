"""Step 1.6: Diagnose GPU + install nvidia-container-toolkit on Xavier."""
import subprocess, sys, time
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
echo "===== GPU Driver Probe ====="
ls -la /usr/bin/nvidia-smi 2>/dev/null || true
ls -la /usr/sbin/nvidia-smi 2>/dev/null || true
which tegra 2>/dev/null || true
cat /proc/driver/nvidia/version 2>/dev/null || echo "no /proc/driver/nvidia"
cat /etc/nv_tegra_release 2>/dev/null || true
dpkg -l | grep -iE 'nvidia-l4t|cuda|tegra' | head -20 || true

echo
echo "===== Container Toolkit Packages ====="
dpkg -l | grep -iE 'nvidia-container|nvidia-docker' || true
which nvidia-ctk 2>/dev/null || echo "nvidia-ctk: NOT FOUND"
which nvidia-container-runtime 2>/dev/null || echo "nvidia-container-runtime: NOT FOUND"

echo
echo "===== Wait apt lock ====="
for i in 1 2 3 4 5; do
  if sudo -n true 2>/dev/null; then SUDO="sudo -n"; else SUDO="echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S"; fi
  if ! fuser /var/lib/apt/lists/lock >/dev/null 2>&1 && ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    echo "apt lock clear"
    break
  fi
  echo "waiting apt lock... $i"
  sleep 5
done

echo
echo "===== Install nvidia-container-toolkit ====="
eval $SUDO apt-get update -qq 2>&1 | tail -5
eval $SUDO apt-get install -y nvidia-container-toolkit 2>&1 | tail -15

echo
echo "===== Configure runtime ====="
if command -v nvidia-ctk >/dev/null 2>&1; then
  eval $SUDO nvidia-ctk runtime configure --runtime=docker 2>&1
  eval $SUDO systemctl restart docker
  sleep 3
  echo "configured via nvidia-ctk"
elif command -v nvidia-container-runtime >/dev/null 2>&1; then
  eval $SUDO mkdir -p /etc/docker
  eval $SUDO tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "runtimes": {
    "nvidia": {
      "path": "/usr/bin/nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia"
}
EOF
  eval $SUDO systemctl restart docker
  sleep 3
  echo "configured via daemon.json"
else
  echo "SKIP configure - no toolkit/runtime binary"
fi

echo
echo "===== Gate Re-check ====="
systemctl is-active docker
docker-compose --version 2>&1 || true
docker info 2>&1 | grep -i runtime || true
hostname -I | tr ' ' '\n' | grep 192.168.1.200 || true
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
