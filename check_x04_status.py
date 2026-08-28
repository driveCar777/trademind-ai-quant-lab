import paramiko, sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=30):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Check Prometheus targets status
print("=== Prometheus Targets ===")
sys.stdout.flush()
r = ssh("curl -s 'http://localhost:9090/api/v1/targets' 2>/dev/null")
import json
try:
    data = json.loads(r)
    for t in data["data"]["activeTargets"]:
        job = t["labels"].get("job", "?")
        inst = t["labels"].get("instance", "?")
        health = t["health"]
        err = t.get("lastError", "")[:50]
        print("  %-25s %-25s %-8s %s" % (job, inst, health, err))
        sys.stdout.flush()
except Exception as e:
    print("Parse error: " + str(e))
    sys.stdout.flush()

# Check Grafana download progress
print("\n=== Grafana Download ===")
sys.stdout.flush()
r = ssh("stat -c%s /tmp/grafana.tar.gz 2>/dev/null || echo 0")
print("Size: " + r + " bytes")
sys.stdout.flush()

# Check if Grafana download is still running
r = ssh("pgrep -f 'curl.*grafana' && echo DOWNLOADING || echo DONE_OR_FAILED")
print("Status: " + r)
sys.stdout.flush()

# Check disk
r = ssh("df -h / | tail -1")
print("Disk: " + r)
sys.stdout.flush()

# System temps
r = ssh("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -5")
print("Temps: " + r)
sys.stdout.flush()

c.close()
print("\nDONE")
