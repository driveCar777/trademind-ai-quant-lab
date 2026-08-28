#!/usr/bin/env python3
"""Deploy monitor-worker to Xavier-04 (192.168.1.203) via paramiko."""
import sys
import os
import paramiko
import time

XAVIER_HOST = "192.168.1.203"
XAVIER_USER = "dji"
XAVIER_PASS = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
XAVIER_PORT = 22
MONITOR_PORT = 9090
LOCAL_SERVER = os.path.join(os.path.dirname(__file__), "..", "monitor-worker", "server.py")
REMOTE_DIR = "/home/dji/monitor-worker"
REMOTE_SERVER = os.path.join(REMOTE_DIR, "server.py")

def run():
    # 1. Connect
    print("[1/5] Connecting to %s ..." % XAVIER_HOST)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(XAVIER_HOST, port=XAVIER_PORT, username=XAVIER_USER,
                   password=XAVIER_PASS, timeout=15)
    print("  OK - connected")

    # 2. Kill existing process on port 9090
    print("[2/5] Killing any process on port %d ..." % MONITOR_PORT)
    stdin, stdout, stderr = client.exec_command(
        "fuser -k %d/tcp 2>/dev/null; sleep 1" % MONITOR_PORT
    )
    stdout.read()
    print("  OK - port freed")

    # 3. Create remote dir + upload server.py
    print("[3/5] Uploading server.py ...")
    client.exec_command("mkdir -p %s" % REMOTE_DIR)
    time.sleep(0.5)

    sftp = client.open_sftp()
    sftp.put(os.path.abspath(LOCAL_SERVER), REMOTE_SERVER)
    sftp.close()
    print("  OK - uploaded to %s" % REMOTE_SERVER)

    # 4. Start the monitor worker
    print("[4/5] Starting monitor-worker on port %d ..." % MONITOR_PORT)
    cmd = "setsid python3 %s > /tmp/monitor-worker.log 2>&1 &" % REMOTE_SERVER
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.read()
    time.sleep(2)
    print("  OK - process started")

    # 5. Verify health
    print("[5/5] Verifying health endpoint ...")
    stdin, stdout, stderr = client.exec_command(
        "curl -s http://127.0.0.1:%d/health" % MONITOR_PORT
    )
    health = stdout.read().decode().strip()
    if health:
        print("  Health: %s" % health)
    else:
        print("  WARNING: no response from health endpoint")
        # Check log
        stdin, stdout, stderr = client.exec_command("tail -20 /tmp/monitor-worker.log")
        print("  Log:\n%s" % stdout.read().decode())

    # Check metrics
    stdin, stdout, stderr = client.exec_command(
        "curl -s http://127.0.0.1:%d/version" % MONITOR_PORT
    )
    version = stdout.read().decode().strip()
    if version:
        print("  Version: %s" % version)

    client.close()
    print("\nDone! Monitor Worker deployed at %s:%d" % (XAVIER_HOST, MONITOR_PORT))

if __name__ == "__main__":
    run()
