#!/usr/bin/env python3
import paramiko, time, json, sys, traceback
from urllib.request import Request, urlopen

OUT = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\monitor_test_result.txt"

with open(OUT, "w", encoding="utf-8") as f:
    f.write("=== Monitor Worker Redeploy + Test ===\n")
    f.flush()
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=15,
                  allow_agent=False, look_for_keys=False)
        f.write("SSH connected to Xavier-04\n")
        f.flush()

        # Kill old process
        c.exec_command("fuser -k 8080/tcp 2>/dev/null")
        time.sleep(1)

        # Upload fixed server.py
        sftp = c.open_sftp()
        sftp.put(r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\monitor-worker\server.py",
                 "/home/dji/monitor-worker/server.py")
        sz = sftp.stat("/home/dji/monitor-worker/server.py").st_size
        sftp.close()
        f.write("Uploaded: %d bytes\n" % sz)
        f.flush()

        # Start
        c.exec_command("setsid python3 /home/dji/monitor-worker/server.py > /tmp/monitor.log 2>&1 &")
        time.sleep(3)

        # Health check
        _, stdout, _ = c.exec_command("curl -s http://127.0.0.1:8080/health")
        health = stdout.read().decode().strip()
        f.write("Health: %s\n" % health)
        f.flush()

        # POST test locally
        _, stdout, _ = c.exec_command(
            'curl -s -X POST http://127.0.0.1:8080/monitor '
            "-d '{\"type\":\"metrics\"}' "
            "-H 'Content-Type: application/json' "
            "--connect-timeout 5 --max-time 20"
        )
        post_local = stdout.read().decode("utf-8", errors="replace").strip()
        f.write("POST local: %s\n" % post_local[:1000])
        f.flush()

        c.close()
    except Exception as e:
        f.write("SSH ERROR: %s\n%s\n" % (e, traceback.format_exc()))
        f.flush()

    # POST test from Windows
    f.write("\n=== POST from Windows ===\n")
    f.flush()
    try:
        req = Request("http://192.168.1.203:8080/monitor",
                      data=b'{"type":"metrics"}',
                      headers={"Content-Type": "application/json"})
        resp = urlopen(req, timeout=20)
        data = json.loads(resp.read().decode("utf-8"))
        f.write("SUCCESS!\n")
        cluster = data.get("cluster", {})
        f.write("  cluster nodes: %s\n" % cluster.get("total_nodes"))
        f.write("  healthy: %s\n" % cluster.get("healthy_nodes"))
        for w in data.get("workers", []):
            f.write("  %s: %s (latency=%sms)\n" % (
                w["id"], "OK" if w.get("reachable") else "DOWN", w.get("latency_ms")))
    except Exception as e:
        f.write("FAILED: %s\n" % str(e))

    f.write("\nDONE\n")
    print("Results written to %s" % OUT)
