"""Step 1.5: Configure NVIDIA container runtime on Xavier via SSH."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST = "192.168.1.200"
USER = "dji"
PASSWORD = "<TRADEMIND_XAVIER_PASSWORD>"

STEP15 = r"""
set -e
echo "===== Step 1.5: NVIDIA Runtime Fix ====="

echo
echo "===== Check existing packages ====="
which nvidia-container-runtime 2>/dev/null || echo "nvidia-container-runtime: NOT FOUND"
dpkg -l | grep -i nvidia-container || true
dpkg -l | grep -i nvidia-docker || true

echo
echo "===== Check nvidia-smi ====="
nvidia-smi 2>&1 | head -5 || echo "nvidia-smi failed"

echo
echo "===== Attempt install nvidia-container-runtime ====="
if ! command -v nvidia-container-runtime >/dev/null 2>&1; then
  echo "Installing nvidia-container-runtime..."
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S apt-get update -qq 2>&1 | tail -3
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S apt-get install -y nvidia-container-runtime 2>&1 | tail -10
else
  echo "nvidia-container-runtime already installed"
fi

echo
echo "===== Configure daemon.json ====="
if command -v nvidia-container-runtime >/dev/null 2>&1; then
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S mkdir -p /etc/docker
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S tee /etc/docker/daemon.json > /dev/null <<'EOF'
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
  echo "daemon.json written"
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S systemctl restart docker
  sleep 3
  echo "Docker restarted"
else
  echo "SKIP daemon.json - nvidia-container-runtime not available"
fi

echo
echo "===== Re-verify Gate ====="
echo "--- Docker Service ---"
systemctl is-active docker

echo "--- Compose ---"
docker-compose --version 2>&1 || true

echo "--- NVIDIA Runtime ---"
docker info 2>&1 | grep -i runtime || true

echo "--- Network ---"
hostname -I
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
stdin, stdout, stderr = client.exec_command(STEP15, timeout=300)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err)
client.close()
