"""Step 1.2b: Compile and run CUDA deviceQuery on Jetson Xavier."""
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
echo "===== Step 1.2b: CUDA deviceQuery ====="

export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

echo
echo "===== nvcc --version ====="
nvcc --version 2>&1

echo
echo "===== Build deviceQuery ====="
cd /usr/local/cuda/samples/1_Utilities/deviceQuery
echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S make clean 2>&1 || true
echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S make 2>&1 | tail -20

echo
echo "===== Run deviceQuery ====="
if [ -x ./deviceQuery ]; then
  ./deviceQuery 2>&1 | tail -25
elif [ -f ./deviceQuery ]; then
  echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S ./deviceQuery 2>&1 | tail -25
else
  echo "deviceQuery binary not found after make"
  ls -la
fi
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
