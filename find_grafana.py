import paramiko, sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=60):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Try to find correct Grafana URL - check what the actual download page says
print("=== Finding Grafana URL ===")
sys.stdout.flush()

# Try more URLs
urls = [
    "https://dl.grafana.com/oss/release/grafana-11.0.0.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-10.4.2.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-10.2.3.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-10.0.0.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-9.5.15.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-9.5.0.linux-arm64.tar.gz",
    "https://dl.grafana.com/oss/release/grafana-8.5.27.linux-arm64.tar.gz",
]

for url in urls:
    r = ssh("curl -fsSL --max-time 10 -o /dev/null -w '%{http_code}' '" + url + "' 2>/dev/null", t=20)
    print(url.split("/")[-1] + " -> " + r)
    sys.stdout.flush()
    if r == "200":
        print("FOUND! Downloading...")
        r = ssh("curl -fsSL --max-time 180 -o /tmp/grafana.tar.gz '" + url + "' && ls -la /tmp/grafana.tar.gz && echo DOWNLOADED", t=240)
        print(r)
        sys.stdout.flush()
        break

# If no direct download, try the grafana-agent or use a lightweight alternative
r = ssh("ls -la /tmp/grafana.tar.gz 2>/dev/null || echo NO_GRAFANA")
print("\nGrafana file: " + r)
sys.stdout.flush()

if "NO_GRAFANA" in r:
    print("Trying apt-get install grafana...")
    sys.stdout.flush()
    r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S apt-get install -y grafana 2>&1 | tail -5", t=120)
    print(r)
    sys.stdout.flush()

c.close()
print("\nDONE")
