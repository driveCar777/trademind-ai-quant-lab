"""Transfer factor-worker-v1 to Xavier-02 and build Docker image."""
import paramiko, sys, os, time

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
LOCAL_DIR = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1"
REMOTE_DIR = "/home/dji/factor-worker-v1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

# Create remote directory
print("===== Creating remote directory =====")
stdin, stdout, stderr = client.exec_command(f"mkdir -p {REMOTE_DIR}/app", timeout=10)
stdout.read()
print("[OK] Remote directory created")

# Upload files via SFTP
sftp = client.open_sftp()
local_files = {
    "app/main.py": "app/main.py",
    "requirements.txt": "requirements.txt",
    "Dockerfile": "Dockerfile",
}

for local_name, remote_name in local_files.items():
    local_path = os.path.join(LOCAL_DIR, local_name)
    remote_path = f"{REMOTE_DIR}/{remote_name}"
    print(f"  Uploading {local_name} -> {remote_name}")
    sftp.put(local_path, remote_path)

sftp.close()
print("[OK] All files uploaded")

# Verify
print("\n===== Verifying files on Xavier-02 =====")
stdin, stdout, stderr = client.exec_command(f"ls -la {REMOTE_DIR}/ && echo '---' && cat {REMOTE_DIR}/Dockerfile", timeout=10)
out = stdout.read().decode()
print(out)

# Build Docker image (aarch64 - use python:3.10-slim which supports arm64)
print("===== Building Docker image =====")
build_cmd = f"cd {REMOTE_DIR} && docker build -t trademind/factor-worker:1.0.0 . 2>&1"
stdin, stdout, stderr = client.exec_command(build_cmd, timeout=300)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out[-2000:] if len(out) > 2000 else out)
if err.strip():
    print("STDERR:", err[-1000:])

# Check build result
print("\n===== Image check =====")
stdin, stdout, stderr = client.exec_command("docker images | grep factor-worker", timeout=10)
print(stdout.read().decode())

client.close()
print("\n[OK] Transfer and build complete")
