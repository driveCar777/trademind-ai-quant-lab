"""Step 5.4-5.5: Full chain verification."""
import json
import urllib.request

MASTER = "http://127.0.0.1:9000"

def get_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read())

def post_json(url, data, timeout=30):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

print("=" * 70)
print("STEP 5.4: Master /workers")
print("=" * 70)
code, resp = get_json(f"{MASTER}/workers")
print(f"HTTP {code}")
print(json.dumps(resp, indent=2))

# Check worker-01 status
workers = resp.get("data", {}).get("workers", [])
w01 = [w for w in workers if w["id"] == "worker-01"]
if w01:
    w = w01[0]
    print(f"\n  Worker-01: status={w['status']}, latency={w.get('latency_ms')}ms")
else:
    print("\n  Worker-01 NOT FOUND in workers list!")

print("\n" + "=" * 70)
print("STEP 5.5: Full Chain — Master POST /task -> Worker RSI")
print("=" * 70)

task_payload = {
    "worker_type": "indicator-worker",
    "indicator": "RSI",
    "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
    "params": {"period": 14}
}

print("\n--- POST /task (RSI XAUUSD) ---")
code, resp = post_json(f"{MASTER}/task", task_payload)
print(f"HTTP {code}")
print(json.dumps(resp, indent=2))

# Check task result
data = resp.get("data", {})
task_id = data.get("task_id")
if task_id:
    print(f"\n--- GET /task/{task_id} ---")
    code2, resp2 = get_json(f"{MASTER}/task/{task_id}")
    print(f"HTTP {code2}")
    print(json.dumps(resp2, indent=2))

# Test more indicators
print("\n--- POST /task (EMA XAUUSD) ---")
ema_payload = {
    "worker_type": "indicator-worker",
    "indicator": "EMA",
    "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
    "params": {"period": 10}
}
code3, resp3 = post_json(f"{MASTER}/task", ema_payload)
print(f"HTTP {code3}")
print(json.dumps(resp3, indent=2))

print("\n--- POST /task (SMA XAUUSD) ---")
sma_payload = {
    "worker_type": "indicator-worker",
    "indicator": "SMA",
    "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
    "params": {"period": 10}
}
code4, resp4 = post_json(f"{MASTER}/task", sma_payload)
print(f"HTTP {code4}")
print(json.dumps(resp4, indent=2))

# Test worker_type that doesn't exist
print("\n--- POST /task (stock-factor — should fail gracefully) ---")
stock_payload = {
    "worker_type": "stock-factor-worker",
    "indicator": "ROE",
    "data": {"stock": "600519", "date": "20260724"},
    "params": {}
}
code5, resp5 = post_json(f"{MASTER}/task", stock_payload)
print(f"HTTP {code5}")
print(json.dumps(resp5, indent=2))

# Test wrong worker type
print("\n--- POST /task (backtest — should fail gracefully) ---")
bt_payload = {
    "worker_type": "backtest-worker",
    "indicator": "backtest",
    "data": {"strategy": "EMA_MACD", "symbol": "XAUUSD", "start": "2025-01-01"},
    "params": {}
}
code6, resp6 = post_json(f"{MASTER}/task", bt_payload)
print(f"HTTP {code6}")
print(json.dumps(resp6, indent=2))

# Summary
print("\n" + "=" * 70)
print("STEP 5 COMPLETE SUMMARY")
print("=" * 70)
print(f"  Master /health:          HTTP {get_json(f'{MASTER}/health')[0]}")
print(f"  Master /workers:         HTTP {code} ({resp.get('data',{}).get('count',0)} workers)")
w01_status = "OFFLINE"
for w in workers:
    if w["id"] == "worker-01":
        w01_status = w["status"]
print(f"  Worker-01 status:        {w01_status}")
print(f"  POST /task RSI:          HTTP {code} -> {'COMPLETED' if code == 200 else 'FAILED'}")
print(f"  POST /task EMA:          HTTP {code3} -> {'COMPLETED' if code3 == 200 else 'FAILED'}")
print(f"  POST /task SMA:          HTTP {code4} -> {'COMPLETED' if code4 == 200 else 'FAILED'}")
print(f"  POST stock-factor:       HTTP {code5} (expected fail — no worker-02)")
print(f"  POST backtest:           HTTP {code6} (expected fail — no worker-03)")
print("=" * 70)
