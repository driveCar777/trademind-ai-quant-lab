"""Step 6: 10 consecutive tasks stress test."""
import json
import time
import urllib.request

MASTER = "http://127.0.0.1:9000"

def post_json(url, data, timeout=30):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def get_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read())

print("=" * 70)
print("STEP 6: 10 Consecutive Tasks — Stress Test")
print("=" * 70)

symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
           "USDCAD", "NZDUSD", "USDCHF", "XAGUSD", "BTCUSD"]
indicators = ["RSI", "EMA", "SMA", "RSI", "EMA",
              "SMA", "RSI", "EMA", "RSI", "SMA"]

results = []
total_start = time.time()

for i in range(10):
    sym = symbols[i]
    ind = indicators[i]
    payload = {
        "worker_type": "indicator-worker",
        "indicator": ind,
        "data": {
            "symbol": sym,
            "close": [44.0 + i*0.5, 44.34+i*0.3, 44.09+i*0.7, 43.61+i*0.2, 44.33+i*0.6,
                       44.83+i*0.4, 45.10+i*0.8, 45.42+i*0.5, 45.84+i*0.3, 46.08+i*0.6,
                       45.89+i*0.4, 46.03+i*0.7, 45.61+i*0.2, 46.28+i*0.5, 46.28+i*0.3,
                       46.00+i*0.6, 46.03+i*0.4, 46.41+i*0.8, 46.22+i*0.5, 45.64+i*0.3]
        },
        "params": {"period": 14}
    }

    start = time.time()
    code, resp = post_json(f"{MASTER}/task", payload)
    elapsed = (time.time() - start) * 1000

    data = resp.get("data", {})
    status = data.get("status", "UNKNOWN")
    task_id = data.get("task_id", "")
    ok = status == "COMPLETED"
    results.append(ok)

    print(f"  [{i+1:2d}] {ind:4s} {sym:8s} -> {status:10s} ({elapsed:7.1f}ms) task={task_id}")

total_ms = (time.time() - total_start) * 1000
passed = sum(results)

print(f"\n{'='*70}")
print(f"STRESS TEST RESULT: {passed}/10 PASSED in {total_ms:.0f}ms total")
print(f"{'='*70}")

# Verify all results exist
print("\n--- Verifying task results ---")
for i in range(10):
    task_id = f"tm-task-20260724-{i+6:06d}"
    code, resp = get_json(f"{MASTER}/task/{task_id}")
    data = resp.get("data", {})
    exists = data.get("result_exists", False)
    status = data.get("status", "UNKNOWN")
    print(f"  [{i+1:2d}] {task_id}: status={status} result_exists={exists}")

# Final health check
print("\n--- Final health ---")
code, resp = get_json(f"{MASTER}/health")
print(f"  Master: HTTP {code}, uptime={resp.get('uptime_seconds', 0):.0f}s")

code2, resp2 = get_json(f"http://192.168.1.200:8000/health")
print(f"  Worker: HTTP {code2}, uptime={resp2.get('uptime_seconds', 0):.0f}s")
