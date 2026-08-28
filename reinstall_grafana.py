import paramiko, sys, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=300):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

# Remove corrupted download and directory
print("Cleaning up...")
sys.stdout.flush()
ssh("rm -f /tmp/grafana.tar.gz")
ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S rm -rf /opt/grafana-v11.0.0/")

# Re-download with progress
print("Re-downloading Grafana 11.0.0 arm64...")
sys.stdout.flush()
r = ssh("curl -L --progress-bar --max-time 600 -o /tmp/grafana.tar.gz 'https://dl.grafana.com/oss/release/grafana-11.0.0.linux-arm64.tar.gz' 2>&1 | tail -5 && ls -la /tmp/grafana.tar.gz", t=660)
print(r)
sys.stdout.flush()

# Check file size - should be ~300MB
r = ssh("stat -c%s /tmp/grafana.tar.gz 2>/dev/null || echo 0")
print("File size: " + r + " bytes")
sys.stdout.flush()

if r.isdigit() and int(r) > 1000000:
    print("File looks good, extracting...")
    sys.stdout.flush()
    r = ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S tar xzf /tmp/grafana.tar.gz -C /opt/ 2>&1 && echo EXTRACTED", t=120)
    print(r)
    sys.stdout.flush()

    grafana_home = ssh("ls -d /opt/grafana-v*/ 2>/dev/null | head -1").strip()
    print("Home: " + grafana_home)
    sys.stdout.flush()

    if grafana_home:
        # Create dirs and fix perms
        ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S mkdir -p /var/lib/grafana /var/log/grafana")
        ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S useradd -r -s /bin/false grafana 2>/dev/null; echo done")
        ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S chown -R grafana:grafana /var/lib/grafana /var/log/grafana")
        
        # Start Grafana
        ssh("echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S nohup %s/bin/grafana-server --homepath=%s --config=%s/conf/defaults.ini web > /tmp/grafana.log 2>&1 &" % (grafana_home, grafana_home, grafana_home), t=10)
        
        time.sleep(8)
        r = ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo NOT_READY")
        print("Grafana: " + r)
        sys.stdout.flush()
else:
    print("Download too small, something wrong")
    sys.stdout.flush()

# Final status
print("\n=== ALL SERVICES ===")
sys.stdout.flush()
print("Prometheus: " + ssh("curl -s http://localhost:9090/-/healthy 2>/dev/null"))
sys.stdout.flush()
print("Grafana: " + ssh("curl -s http://localhost:3000/api/health 2>/dev/null || echo NOT_RUNNING"))
sys.stdout.flush()
ne = ssh("curl -s http://localhost:9100/metrics 2>/dev/null | wc -l")
print("NodeExporter: " + ne + " metric lines")
sys.stdout.flush()
print("\nPorts:")
print(ssh("ss -tlnp | grep -E '(9090|9100|3000)'"))
sys.stdout.flush()

c.close()
print("\nDONE")
