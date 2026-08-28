import paramiko
import time
import sys

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"

print("Connecting to Xavier-02...")
sys.stdout.flush()

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Connected OK")
    sys.stdout.flush()
except Exception as e:
    print(f"Connection FAILED: {e}")
    sys.exit(1)

def run_cmd(cmd, label="", timeout=15):
    print(f"\n--- {label} ---")
    sys.stdout.flush()
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        if out.strip():
            print(out.strip())
        if err.strip():
            print(f"  stderr: {err.strip()[:300]}")
        sys.stdout.flush()
        return out, err
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.stdout.flush()
        return "", str(e)

# Test
run_cmd("echo hello_xavier02", "basic connectivity")

# Check file
run_cmd("ls -la " + REMOTE_DIR + "/server.py && wc -c " + REMOTE_DIR + "/server.py", "file check")

# Kill old process
run_cmd("kill $(pgrep -f 'server.py') 2>/dev/null; echo 'killed'", "stop old")
time.sleep(1)

# Free port
run_cmd("fuser -k 8001/tcp 2>/dev/null; echo 'freed'", "free port 8001")
time.sleep(1)

# Start server - use setsid to fully detach
run_cmd(
    "cd " + REMOTE_DIR + " && setsid python3 server.py > /tmp/factor-worker.log 2>&1 &",
    "start server (detached)",
    timeout=5,
)
time.sleep(3)

# Check if alive
run_cmd("pgrep -f 'server.py' && echo 'ALIVE' || echo 'DEAD'", "process check")

# Health
run_cmd("curl -s --connect-timeout 5 http://127.0.0.1:8001/health 2>&1", "health check")

# Port
run_cmd("ss -tlnp | grep 8001", "port check")

# Logs
run_cmd("cat /tmp/factor-worker.log 2>/dev/null", "server logs")

# Test 600519
run_cmd(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"600519","date":"20260724"}\'',
    "POST /factor 600519",
)

# Test 000858
run_cmd(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"000858","date":"20260724"}\'',
    "POST /factor 000858",
)

# Test 300750
run_cmd(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"300750","date":"20260724"}\'',
    "POST /factor 300750",
)

# Test unknown stock
run_cmd(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"999999","date":"20260724"}\'',
    "POST /factor unknown",
)

# List factors
run_cmd("curl -s http://127.0.0.1:8001/factors", "GET /factors")

# Test from Master (192.168.1.101)
run_cmd(
    'curl -s --connect-timeout 5 http://192.168.1.201:8001/health 2>&1',
    "health from Master perspective (should fail if only bound to localhost)",
)

client.close()
print("\n[DONE] Xavier-02 factor-worker deployment complete")
sys.stdout.flush()
