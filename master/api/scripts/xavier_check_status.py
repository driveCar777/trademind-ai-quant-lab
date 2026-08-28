"""Check Xavier build status after timeout."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
echo "===== Docker status ====="
systemctl is-active docker
docker version 2>&1 | head -6
echo
echo "===== daemon.json ====="
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json"
echo
echo "===== DNS test in container ====="
docker run --rm python:3.8-slim cat /etc/resolv.conf 2>&1
echo
echo "===== Docker images ====="
docker images | head -10
echo
echo "===== Running containers ====="
docker ps -a
echo
echo "===== Build log if exists ====="
tail -50 /tmp/step2_build_F.log 2>/dev/null || echo "no build log"
echo
echo "===== Disk ====="
df -h /
echo
echo "===== containerd symlink ====="
ls -la /usr/bin/containerd-shim-runc-v2 2>/dev/null || echo "symlink missing"
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=60)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
