import paramiko, sys, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=120):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Step 1: Write Prometheus config with all worker targets
prom_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: trademind

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  - job_name: node-exporter
    static_configs:
      - targets: ['localhost:9100']

  - job_name: trademind-master
    static_configs:
      - targets: ['192.168.1.101:9000']

  - job_name: trademind-workers
    static_configs:
      - targets:
        - '192.168.1.200:8000'
        - '192.168.1.201:8001'
        - '192.168.1.202:8002'
"""

sftp = c.open_sftp()
with sftp.open("/tmp/prometheus.yml", "w") as f:
    f.write(prom_config)
sftp.close()
print("Config written")
sys.stdout.flush()

r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S cp /tmp/prometheus.yml /etc/prometheus/prometheus.yml && echo COPIED")
print("Copy: " + r)
sys.stdout.flush()

r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S systemctl restart prometheus && echo RESTARTED", t=30)
print("Restart: " + r)
sys.stdout.flush()

time.sleep(2)
r = ssh("curl -s http://localhost:9090/-/healthy 2>/dev/null")
print("Prom health: " + r)
sys.stdout.flush()

# Step 2: Install Grafana
print("\n=== Install Grafana ===")
sys.stdout.flush()
r = ssh("curl -fsSL https://dl.grafana.com/oss/release/grafana_10.4.2_linux_arm64.tar.gz -o /tmp/grafana.tar.gz 2>&1 | tail -3", t=120)
print("Download: " + r)
sys.stdout.flush()

r = ssh("ls -la /tmp/grafana.tar.gz 2>/dev/null", t=10)
print("File: " + r)
sys.stdout.flush()

r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S tar xzf /tmp/grafana.tar.gz -C /opt/ 2>&1 && echo EXTRACTED", t=30)
print("Extract: " + r)
sys.stdout.flush()

r = ssh("ls /opt/grafana-v10.4.2/bin/ 2>/dev/null || ls /opt/grafana*/bin/ 2>/dev/null || echo NOT_FOUND")
print("Binaries: " + r)
sys.stdout.flush()

# Start Grafana
r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S /opt/grafana-v10.4.2/bin/grafana-server --homepath=/opt/grafana-v10.4.2 --config=/opt/grafana-v10.4.2/conf/defaults.ini web > /tmp/grafana.log 2>&1 &", t=10)
print("Grafana start: " + r)
sys.stdout.flush()

time.sleep(5)
r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null")
print("Grafana health: " + r)
sys.stdout.flush()

# Step 3: Final checks
print("\n=== Final Status ===")
sys.stdout.flush()
r = ssh("ss -tlnp | grep -E '(9090|9100|3000)'")
print("Ports:\n" + r)
sys.stdout.flush()

r = ssh("curl -s http://localhost:9090/api/v1/targets 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(t['labels'].get('job','?'), t['health']) for t in d['data']['activeTargets']]\" 2>/dev/null")
print("Targets:\n" + r)
sys.stdout.flush()

c.close()
print("\nDONE")
