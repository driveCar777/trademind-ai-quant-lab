"""Fix: sudo docker + proper file transfer via heredoc."""
import paramiko, sys, os

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, label=""):
    print(f"\n--- {label} ---")
    # Use sudo for docker commands, regular for file ops
    stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        print(out)
    if err.strip() and "Warning" not in err:
        print("ERR:", err[-500:])
    return out

# 1. Fix docker group
print("===== Fix permissions =====")
run("echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S usermod -aG docker dji 2>/dev/null; echo 'group check done'", "add docker group")

# 2. Create directory
run(f"mkdir -p {REMOTE_DIR}/app", "create dirs")

# 3. Write files using cat heredoc (bypasses SFTP zero-byte issue)
main_py = open(r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\app\main.py", "r").read()
requirements = open(r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\requirements.txt", "r").read()
dockerfile = open(r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\Dockerfile", "r").read()

# Write main.py
encoded = main_py.encode("base64").decode()
run(f"echo '{encoded}' | base64 -d > {REMOTE_DIR}/app/main.py", "write main.py")
run(f"wc -c {REMOTE_DIR}/app/main.py", "verify main.py size")

# Write requirements.txt
encoded2 = requirements.encode("base64").decode()
run(f"echo '{encoded2}' | base64 -d > {REMOTE_DIR}/requirements.txt", "write requirements.txt")
run(f"wc -c {REMOTE_DIR}/requirements.txt", "verify requirements.txt size")

# Write Dockerfile
encoded3 = dockerfile.encode("base64").decode()
run(f"echo '{encoded3}' | base64 -d > {REMOTE_DIR}/Dockerfile", "write Dockerfile")
run(f"wc -c {REMOTE_DIR}/Dockerfile", "verify Dockerfile size")

# Verify content
run(f"head -5 {REMOTE_DIR}/app/main.py", "verify main.py content")
run(f"cat {REMOTE_DIR}/Dockerfile", "verify Dockerfile content")

# 4. Build with sudo
print("\n===== Building Docker image (sudo) =====")
build_out = run(
    f"echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S docker build -t trademind/factor-worker:1.0.0 {REMOTE_DIR} 2>&1",
    "docker build"
)

# 5. Check image
run("echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S docker images | grep factor-worker", "image check")

client.close()
print("\n[OK] Done")
