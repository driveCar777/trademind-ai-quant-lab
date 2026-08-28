#!/usr/bin/env python3
"""Redeploy fixed monitor-worker to Xavier-04 and test POST."""
import paramiko, time, json
from urllib.request import Request, urlopen

NODE = "192.168.1.203"
USER = "dji"
PASS = "<TRADEMIND_XAVIER_PASSWORD>"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(NODE, username=USER, password=PASS, timeout=15,
          allow_agent=False, look_for_keys=False)

# Kill old
c.exec_command("fuser -k 8080/tcp 2>/dev/null")
time.sleep(1)

# Upload
sftp = c.open_sftp()
sftp.put(r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\monitor-worker\server.py",
         "/home/dji/monitor-worker/server.py")
sz = sftp.stat("/home/dji/monitor-worker/server.py").st_size
sftp.close()
print("Uploaded: %d bytes" % sz)

# Start
c.exec_command("setsid python3 /home/dji/monitor-worker/server.py > /tmp/monitor.log 2>&1 &")
time.sleep(3)

# Health check (local on Xavier)
stdin, stdout, stderr = c.exec_command("curl -s http://127.0.0.1:8080/health")
print("Health:", stdout.read().decode().strip())

# POST test (local on Xavier)
stdin, stdout, stderr = c.exec_command(
    "curl -s -X POST http://127.0.0.1:8080/monitor "
    "-d '{\"type\":\"metrics\"}' "
    "-H 'Content-Type: application/json' "
    "--connect-timeout 5 --max-time 15"
)
post_result = stdout.read().decode("utf-8", errors="replace").strip()
print("POST local:", post_result[:800])

# POST test (from Windows)
try:
    req = Request("http://%s:8080/monitor" % NODE,
                  data=b'{"type":"metrics"}',
                  headers={"Content-Type": "application/json"})
    resp = urlopen(req, timeout=15)
    data = json.loads(resp.read().decode("utf-8"))
    print("POST from Windows: success")
    print("  cluster nodes:", data.get("cluster", {}).get("total_nodes"))
    print("  healthy:", data.get("cluster", {}).get("healthy_nodes"))
    for w in data.get("workers", []):
        print("  %s: %s (latency=%sms)" % (
            w["id"], "REACHABLE" if w.get("reachable") else "DOWN", w.get("latency_ms")))
except Exception as e:
    print("POST from Windows: FAILED -", e)

c.close()
