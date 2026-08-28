"""Step 5.2-5.5: Full Worker API test + Master check from Windows."""
import json
import time
import urllib.request

WORKER = "http://192.168.1.200:8000"
MASTER = "http://192.168.1.101:9000"

def post_json(url, data, timeout=10):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return getattr(e, "code", 500), str(e)

def get_json(url, timeout=10):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return getattr(e, "code", 500), str(e)

print("=" * 70)
print("STEP 5: Master-Worker Integration Test")
print("=" * 70)

# 5.1 already confirmed: ping + health from Windows

# 5.2 Direct Worker API tests
print("\n--- 5.2 Direct Worker API Tests ---")

tests = [
    ("RSI XAUUSD", {"indicator": "RSI", "data": {"close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]}, "params": {"period": 14}}),
    ("RSI Uptrend", {"indicator": "RSI", "data": {"close": [50,52,54,51,49,53,55,57,56,58,60,62,61,63,65,64,66,68,67,69]}, "params": {"period": 14}}),
    ("RSI Downtrend", {"indicator": "RSI", "data": {"close": [65,63,61,59,57,55,53,51,49,47,45,43,41,39,37,35,33,31,29,27]}, "params": {"period": 14}}),
    ("EMA", {"indicator": "EMA", "data": {"close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08]}, "params": {"period": 5}}),
    ("MACD", {"indicator": "MACD", "data": {"close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64,46.00,46.50,47.00,47.50,48.00]}, "params": {}}),
    ("SMA", {"indicator": "SMA", "data": {"close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08]}, "params": {"period": 5}}),
]

worker_ok = 0
for name, payload in tests:
    code, resp = post_json(f"{WORKER}/api/v1/indicator/calculate", payload)
    status = "PASS" if code == 200 else "FAIL"
    if code == 200:
        worker_ok += 1
    print(f"\n  [{status}] {name} (HTTP {code})")
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

print(f"\n  Worker API: {worker_ok}/{len(tests)} passed")

# 5.3 Master API status
print("\n--- 5.3 Master API Status ---")
code, resp = get_json(f"{MASTER}/health")
if code == 200:
    print(f"  [PASS] Master /health: HTTP {code}")
    print(f"  Response: {json.dumps(resp, indent=2)}")
else:
    print(f"  [WARN] Master /health: HTTP {code}")
    print(f"  Response: {resp}")
    print(f"  Master may not be running on port 9000")

# 5.4 Master /workers
print("\n--- 5.4 Master /workers ---")
code, resp = get_json(f"{MASTER}/workers")
if code == 200:
    print(f"  [PASS] Master /workers: HTTP {code}")
    print(f"  Workers: {json.dumps(resp, indent=2)}")
else:
    print(f"  [INFO] Master /workers: HTTP {code}")
    print(f"  Response: {str(resp)[:200]}")

# 5.5 Full chain: Master -> Worker
print("\n--- 5.5 Full Chain Test ---")
task_payload = {
    "task_type": "indicator",
    "symbol": "XAUUSD",
    "indicator": "RSI",
    "params": {"period": 14},
    "data": {
        "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]
    }
}
code, resp = post_json(f"{MASTER}/api/v1/task", task_payload)
if code in (200, 201):
    print(f"  [PASS] Master POST /api/v1/task: HTTP {code}")
    print(f"  Response: {json.dumps(resp, indent=2)}")
else:
    print(f"  [INFO] Master POST /api/v1/task: HTTP {code}")
    print(f"  Response: {str(resp)[:300]}")

# Summary
print("\n" + "=" * 70)
print("STEP 5 SUMMARY")
print("=" * 70)
print(f"  Windows -> Xavier ping:    PASS")
print(f"  Windows -> Worker /health: PASS")
print(f"  Worker API ({worker_ok}/{len(tests)}):    {'PASS' if worker_ok == len(tests) else 'PARTIAL'}")
print(f"  Master API:               {'RUNNING' if code != 500 and 'refused' not in str(resp).lower() else 'NOT RUNNING'}")
print("=" * 70)
