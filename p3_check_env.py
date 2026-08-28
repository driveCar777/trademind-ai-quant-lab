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

    def run(cmd, timeout=30):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        return out

    print("[2] Check Python env...")
    print("  python3:", run("python3 --version"))
    print("  pip3:", run("python3 -m pip --version 2>/dev/null || pip3 --version 2>/dev/null || echo no-pip"))
    print("  python3.8:", run("python3.8 --version 2>/dev/null || echo not-found"))
    print("  python3.10:", run("python3.10 --version 2>/dev/null || echo not-found"))

    print("[3] Try pip install directly...")
    run("sudo pip3 install fastapi uvicorn pydantic 2>&1 || echo pip-failed")
    run("python3 -m pip install fastapi uvicorn pydantic 2>&1 || echo pip-m-failed")

    print("[4] Check if packages installed...")
    print("  fastapi:", run("python3 -c 'import fastapi; print(fastapi.__version__)' 2>&1 || echo no"))
    print("  uvicorn:", run("python3 -c 'import uvicorn; print(uvicorn.__version__)' 2>&1 || echo no"))
    print("  pydantic:", run("python3 -c 'import pydantic; print(pydantic.__version__)' 2>&1 || echo no"))

    client.close()

if __name__ == "__main__":
    main()
