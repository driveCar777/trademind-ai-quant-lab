import paramiko, sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.203", username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=20, banner_timeout=20, auth_timeout=20)
print("CONNECTED")
sys.stdout.flush()

def ssh(cmd, t=60):
    _, out, err = c.exec_command(cmd, timeout=t)
    return out.read().decode("utf-8", errors="replace").strip()

print("=== Prometheus Config ===")
print(ssh("cat /etc/prometheus/prometheus.yml"))
sys.stdout.flush()

print("=== Service Status ===")
print(ssh("systemctl status prometheus 2>&1 | head -5"))
sys.stdout.flush()
print(ssh("systemctl status prometheus-node-exporter 2>&1 | head -5"))
sys.stdout.flush()

print("=== Ports ===")
print(ssh("ss -tlnp | grep -E '(9090|9100|3000)'"))
sys.stdout.flush()

c.close()
print("DONE")
