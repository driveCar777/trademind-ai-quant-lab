"""Check Step 2 build status on Xavier."""
import subprocess, sys
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

CMDS = f"""
echo "===== Directory ====="
ls -la {REMOTE_DIR} 2>/dev/null || echo "DIR NOT FOUND"
echo
echo "===== Docker images ====="
docker images | grep -E "indicator|REPOSITORY" || docker images | head -8
echo
echo "===== Build log tail (if exists) ====="
if [ -f /tmp/step2_build.log ]; then tail -60 /tmp/step2_build.log; else echo "no build log file"; fi
echo
echo "===== Running docker processes ====="
ps aux | grep -E "docker|compose" | grep -v grep | head -5 || echo "none"
echo
echo "===== Containers ====="
docker ps -a | grep indicator || echo "no indicator containers"
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
