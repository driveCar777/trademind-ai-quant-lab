import paramiko
import time

HOST = "192.168.1.201"
USER = "dji"
PASS = "<TRADEMIND_XAVIER_PASSWORD>"

def main():
    print("[1] Connecting...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("  Connected")

    sftp = client.open_sftp()

    print("[2] Writing Dockerfile...")
    with sftp.open("/home/dji/factor-worker/Dockerfile", "w") as f:
        f.write("FROM python:3.8-slim" + "\n")
        f.write("ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1" + "\n")
        f.write("WORKDIR /app" + "\n")
        f.write("COPY worker/requirements.txt ." + "\n")
        f.write("RUN pip install --no-cache-dir -r requirements.txt" + "\n")
        f.write("COPY worker/ /app/worker/" + "\n")
        f.write("EXPOSE 8001" + "\n")
        f.write('CMD ["uvicorn", "worker.app.main:app", "--host", "0.0.0.0", "--port", "8001"]' + "\n")

    print("[3] Writing docker-compose.yml...")
    with sftp.open("/home/dji/factor-worker/docker-compose.yml", "w") as f:
        f.write("version: 3.8" + "\n")
        f.write("services:" + "\n")
        f.write("  factor-worker-02:" + "\n")
        f.write("    build:" + "\n")
        f.write("      context: ." + "\n")
        f.write("      dockerfile: Dockerfile" + "\n")
        f.write("    container_name: factor-worker-02" + "\n")
        f.write("    restart: unless-stopped" + "\n")
        f.write("    ports:" + "\n")
        f.write("      - 8001:8001" + "\n")
        f.write("    environment:" + "\n")
        f.write("      - FACTOR_SERVICE_NAME=factor-worker" + "\n")
        f.write("      - FACTOR_VERSION=1.0.0" + "\n")
        f.write("      - FACTOR_PORT=8001" + "\n")
        f.write("      - FACTOR_WORKER_ID=xavier-worker-02" + "\n")
        f.write("      - FACTOR_LOG_LEVEL=INFO" + "\n")

    print("[4] Writing requirements.txt...")
    with sftp.open("/home/dji/factor-worker/worker/requirements.txt", "w") as f:
        f.write("fastapi>=0.100.0" + "\n")
        f.write("uvicorn[standard]>=0.23.0" + "\n")
        f.write("pydantic>=2.0" + "\n")
        f.write("pydantic-settings>=2.0" + "\n")

    sftp.close()
    print("  Files written")

    def run(cmd, timeout=30):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip()

    print("[5] Verify...")
    print("  Dockerfile lines:", run("wc -l < /home/dji/factor-worker/Dockerfile"))
    print("  compose lines:", run("wc -l < /home/dji/factor-worker/docker-compose.yml"))
    print("  main.py exists:", run("test -f /home/dji/factor-worker/worker/app/main.py && echo yes || echo no"))
    print("  routes.py exists:", run("test -f /home/dji/factor-worker/worker/app/api/routes.py && echo yes || echo no"))
    print("  schemas.py exists:", run("test -f /home/dji/factor-worker/worker/app/model/schemas.py && echo yes || echo no"))
    print("  factor_service.py exists:", run("test -f /home/dji/factor-worker/worker/app/service/factor_service.py && echo yes || echo no"))
    print("  settings.py exists:", run("test -f /home/dji/factor-worker/worker/app/config/settings.py && echo yes || echo no"))

    print("[6] Build Docker image...")
    out = run("cd /home/dji/factor-worker && docker build -t trademind/factor-worker:1.0.0 . 2>&1", timeout=600)
    lines = out.split("\n")
    for line in lines[-25:]:
        print("  " + line)
    if "Successfully built" in out:
        print("  BUILD SUCCESS")
    else:
        print("  BUILD STATUS: check output above")

    print("[7] Stop old + start new...")
    run("docker rm -f factor-worker-02 2>/dev/null")
    time.sleep(1)
    out = run("cd /home/dji/factor-worker && docker-compose up -d 2>&1")
    print("  " + out)

    print("[8] Wait 10s...")
    time.sleep(10)

    print("[9] Container status:")
    print("  " + run("docker ps | grep factor"))

    print("[10] Health check:")
    print("  " + run("curl -s http://localhost:8001/health"))

    client.close()
    print("\n=== PHASE 3 BUILD DONE ===")

if __name__ == "__main__":
    main()
