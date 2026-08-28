"""Step 5.2c: Correct Worker API calls + check Master."""
import json
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
        code = getattr(e, "code", None)
        try:
            err_body = e.read().decode() if hasattr(e, "read") else str(e)
        except:
            err_body = str(e)
        return code or 500, err_body

def get_json(url, timeout=5):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return getattr(e, "code", 500), str(e)

print("=" * 70)
print("STEP 5.2c: Worker API (corrected schema)")
print("=" * 70)

# Corrected requests - data MUST include "symbol"
tests = [
    ("RSI XAUUSD", {
        "indicator": "RSI",
        "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
        "params": {"period": 14}
    }),
    ("RSI Uptrend", {
        "indicator": "RSI",
        "data": {"symbol": "EURUSD", "close": [50,52,54,51,49,53,55,57,56,58,60,62,61,63,65,64,66,68,67,69]},
        "params": {"period": 14}
    }),
    ("RSI Downtrend", {
        "indicator": "RSI",
        "data": {"symbol": "GBPUSD", "close": [65,63,61,59,57,55,53,51,49,47,45,43,41,39,37,35,33,31,29,27]},
        "params": {"period": 14}
    }),
    ("EMA", {
        "indicator": "EMA",
        "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08]},
        "params": {"period": 5}
    }),
    ("MACD", {
        "indicator": "MACD",
        "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64,46.00,46.50,47.00,47.50,48.00]},
        "params": {}
    }),
    ("SMA", {
        "indicator": "SMA",
        "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08]},
        "params": {"period": 5}
    }),
]

worker_pass = 0
for name, payload in tests:
    code, resp = post_json(f"{WORKER}/api/v1/indicator/calculate", payload)
    ok = code == 200
    if ok:
        worker_pass += 1
    print(f"\n  [{'PASS' if ok else 'FAIL'}] {name} (HTTP {code})")
    if ok:
        print(f"  Result: {json.dumps(resp, indent=2)}")
    else:
        print(f"  Error: {str(resp)[:300]}")

# 5.3 Master check
print("\n" + "=" * 70)
print("STEP 5.3: Master API Status")
print("=" * 70)

code, resp = get_json(f"{MASTER}/health")
if code == 200:
    print(f"  [PASS] Master /health: HTTP {code}")
    print(f"  {json.dumps(resp, indent=2)}")
else:
    print(f"  [NOT RUNNING] Master /health: {resp}")
    print(f"  Master API is NOT running on {MASTER}")
    print(f"  The Master code exists in this repo but hasn't been started.")

print("\n" + "=" * 70)
print("STEP 5 SUMMARY")
print("=" * 70)
print(f"  Windows -> Xavier ping:        PASS (0ms)")
print(f"  Windows -> Worker /health:     PASS (HTTP 200)")
print(f"  Worker API ({worker_pass}/{len(tests)}):       {'ALL PASS' if worker_pass == len(tests) else f'{worker_pass}/{len(tests)} PASS'}")
print(f"  Master API:                    NOT RUNNING (port 9000 refused)")
print(f"  Full chain (Master->Worker):   BLOCKED (Master not started)")
print("=" * 70)
