"""Phase 3.5: Master integration test — Worker-02 through Master API."""
import json
import sys
import time
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
print("  PHASE 3.5: Master Integration Test — Worker-02")
print("=" * 70)

# 1. Master health
print("\n--- Master Health ---")
code, resp = get_json(f"{MASTER}/health")
print(f"  HTTP {code}: {resp.get('status')} v{resp.get('version')}")

# 2. Workers status
print("\n--- Worker Status ---")
code, resp = get_json(f"{MASTER}/workers")
workers = resp.get("data", {}).get("workers", [])
for w in workers:
    icon = "+" if w["status"] == "ONLINE" else "-"
    latency = f"{w.get('latency_ms', -1)}ms" if w.get("latency_ms", -1) > 0 else "N/A"
    print(f"  [{icon}] {w['id']:<12} {w['status']:<8} {latency:<10} {w['worker_type']}")

# 3. Test stock-factor-worker through Master
print("\n--- POST /task (stock-factor-worker) via Master ---")

stocks = [
    ("600519", "贵州茅台"),
    ("000858", "五粮液"),
    ("601318", "中国平安"),
    ("300750", "宁德时代"),
    ("002594", "比亚迪"),
]

results = []
for code_str, name in stocks:
    payload = {
        "worker_type": "stock-factor-worker",
        "indicator": "factor",
        "data": {"stock": code_str, "date": "20260724"},
        "params": {}
    }
    start = time.time()
    http_code, resp = post_json(f"{MASTER}/task", payload)
    elapsed_ms = (time.time() - start) * 1000
    data = resp.get("data", {})
    status = data.get("status", "UNKNOWN")
    ok = status == "COMPLETED"
    results.append(ok)
    print(f"  [{code_str}] {name:<8} HTTP {http_code} status={status} ({elapsed_ms:.0f}ms) worker={data.get('worker_id', '?')}")

print(f"\n  Result: {sum(results)}/{len(results)} COMPLETED")

# 4. Test indicator-worker still works
print("\n--- Verify Worker-01 (indicator) still works ---")
payload = {
    "worker_type": "indicator-worker",
    "indicator": "RSI",
    "data": {"symbol": "EURUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
    "params": {"period": 14}
}
code, resp = post_json(f"{MASTER}/task", payload)
data = resp.get("data", {})
print(f"  RSI EURUSD: {data.get('status')} worker={data.get('worker_id')}")

# 5. Final summary
print("\n" + "=" * 70)
print("  PHASE 3.5 SUMMARY")
print("=" * 70)
print(f"  Master /health:      HTTP {get_json(f'{MASTER}/health')[0]}")
w01 = [w for w in workers if w["id"] == "worker-01"]
w02 = [w for w in workers if w["id"] == "worker-02"]
print(f"  Worker-01:           {w01[0]['status'] if w01 else 'NOT FOUND'}")
print(f"  Worker-02:           {w02[0]['status'] if w02 else 'NOT FOUND'} ({w02[0].get('latency_ms', -1)}ms)" if w02 else "  Worker-02:           NOT FOUND")
print(f"  Factor tasks:        {sum(results)}/{len(results)} COMPLETED")
print(f"  Indicator tasks:     {data.get('status')}")
print("=" * 70)
