import paramiko, sys, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=120):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Try various Grafana arm64 URLs
urls = [
    "https://dl.grafana.com/oss/release/grafana_11.0.0_linux_arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana_10.4.2_linux_arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana_10.2.3_linux_arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana_9.5.15_linux_arm64.tar.gz",
]

found = False
for url in urls:
    r = ssh("curl -fsSL --max-time 15 -o /dev/null -w '%{http_code}' '" + url + "' 2>/dev/null", t=30)
    print(url.split("/")[-1] + " -> " + r)
    sys.stdout.flush()
    if r == "200":
        print("Downloading " + url.split("/")[-1] + "...")
        sys.stdout.flush()
        r = ssh("curl -fsSL --max-time 180 -o /tmp/grafana.tar.gz '" + url + "' && echo DOWNLOADED", t=240)
        print(r)
        sys.stdout.flush()
        found = True
        break

if not found:
    print("No Grafana arm64 URL found via curl. Trying pip3 grafana-server alternative...")
    sys.stdout.flush()

r = ssh("ls -la /tmp/grafana.tar.gz 2>/dev/null || echo NO_FILE")
print("File: " + r)
sys.stdout.flush()

if "NO_FILE" not in r and found:
    r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S tar xzf /tmp/grafana.tar.gz -C /opt/ 2>&1 && echo EXTRACTED", t=60)
    print("Extract: " + r)
    sys.stdout.flush()

    grafana_home = ssh("ls -d /opt/grafana-v*/ 2>/dev/null | head -1").strip().rstrip("/")
    print("Home: " + grafana_home)
    sys.stdout.flush()

    if grafana_home:
        cmd = "echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S nohup %s/bin/grafana-server --homepath=%s --config=%s/conf/defaults.ini web > /tmp/grafana.log 2>&1 &" % (grafana_home, grafana_home, grafana_home)
        ssh(cmd, t=10)
        time.sleep(5)
        r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null")
        print("Grafana: " + r)
        sys.stdout.flush()

print("\n=== Final Status ===")
sys.stdout.flush()
r = ssh("ss -tlnp | grep -E '(9090|9100|3000)'")
print("Ports:\n" + r)
sys.stdout.flush()
r = ssh("curl -s http://localhost:9090/-/healthy 2>/dev/null")
print("Prometheus: " + r)
sys.stdout.flush()
r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo NOT_RUNNING")
print("Grafana: " + r)
sys.stdout.flush()
r = ssh("curl -s http://localhost:9100/metrics 2>/dev/null | wc -l")
print("NodeExporter lines: " + r)
sys.stdout.flush()

c.close()
print("\nDONE")
