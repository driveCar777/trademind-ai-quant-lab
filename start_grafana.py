import paramiko, sys, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=60):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Extract Grafana
print("=== Extract Grafana ===")
sys.stdout.flush()
r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S tar xzf /tmp/grafana.tar.gz -C /opt/ 2>&1 && echo EXTRACTED", t=30)
print(r)
sys.stdout.flush()

# Find directory
r = ssh("ls -d /opt/grafana*/ 2>/dev/null || echo NOT_FOUND")
print("Dir: " + r)
sys.stdout.flush()

grafana_home = r.strip().split("\n")[0].rstrip("/") if "NOT_FOUND" not in r else ""
print("Home: " + grafana_home)
sys.stdout.flush()

if grafana_home:
    # Create grafana user
    ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S useradd -r -s /bin/false grafana 2>/dev/null; echo done")
    
    # Fix permissions
    ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S chown -R grafana:grafana %s 2>&1 | tail -1" % grafana_home)
    
    # Create data and log dirs
    ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S mkdir -p /var/lib/grafana /var/log/grafana && echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S chown -R grafana:grafana /var/lib/grafana /var/log/grafana && echo DIRS_OK")
    
    # Start Grafana
    print("Starting Grafana...")
    sys.stdout.flush()
    ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S nohup %s/bin/grafana-server --homepath=%s --config=%s/conf/defaults.ini web > /tmp/grafana.log 2>&1 &" % (grafana_home, grafana_home, grafana_home), t=10)
    
    time.sleep(5)
    
    r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo NOT_READY")
    print("Grafana health: " + r)
    sys.stdout.flush()
    
    if "NOT_READY" in r:
        print("Waiting more...")
        time.sleep(5)
        r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo STILL_NOT_READY")
        print("Grafana health: " + r)
        sys.stdout.flush()
else:
    print("No Grafana extracted")
    sys.stdout.flush()

# Final comprehensive status
print("\n=== FINAL STATUS ===")
sys.stdout.flush()

print("Prometheus: " + ssh("curl -s http://localhost:9090/-/healthy 2>/dev/null"))
sys.stdout.flush()
print("Grafana: " + ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo NOT_RUNNING"))
sys.stdout.flush()
print("NodeExporter: " + ssh("curl -s http://localhost:9100/metrics 2>/dev/null | wc -l") + " metric lines")
sys.stdout.flush()

print("\nPorts:")
print(ssh("ss -tlnp | grep -E '(9090|9100|3000)'"))
sys.stdout.flush()

print("Prometheus targets:")
r = ssh("curl -s 'http://localhost:9090/api/v1/targets' 2>/dev/null")
print(r[:1000] if r else "NO RESPONSE")
sys.stdout.flush()

c.close()
print("\nDONE")
