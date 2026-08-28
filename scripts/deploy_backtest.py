#!/usr/bin/env python3
"""Upload backtest-worker-v1 server.py to Xavier-03 and restart :8002."""
from __future__ import print_function

import os
import time

import paramiko

HOST = "192.168.1.202"
USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
PORT = 8002
LOCAL = os.path.join(os.path.dirname(__file__), "..", "backtest-worker-v1", "server.py")
DIRS = ["/home/dji/backtest-worker-v1", "/home/dji/backtest-worker"]


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    print("connected", HOST)
    stdin, stdout, _stderr = client.exec_command(
        "fuser -k %s/tcp 2>/dev/null; sleep 1" % PORT
    )
    stdout.read()
    sftp = client.open_sftp()
    remote_dir = None
    for path in DIRS:
        try:
            sftp.stat(path)
            remote_dir = path
            break
        except IOError:
            continue
    if remote_dir is None:
        remote_dir = DIRS[0]
        client.exec_command("mkdir -p %s" % remote_dir)
        time.sleep(0.4)
    remote = remote_dir + "/server.py"
    sftp.put(os.path.abspath(LOCAL), remote)
    sftp.close()
    print("uploaded", remote)
    client.exec_command(
        "cd %s && nohup python3 server.py > /tmp/backtest-worker.log 2>&1 < /dev/null &" % remote_dir
    )
    time.sleep(2)
    stdin, stdout, _stderr = client.exec_command("curl -s http://127.0.0.1:%s/version" % PORT)
    print("version", stdout.read().decode("utf-8", "replace").strip())
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
