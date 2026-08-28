"""Step 5.4-5.5 retry: workers.json fixed (port 8000)."""
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
print("STEP 5.4: Master /workers (after fix)")
print("=" * 70)
code, resp = get_json(f"{MASTER}/workers")
print(f"HTTP {code}")
print(json.dumps(resp, indent=2))

workers = resp.get("data", {}).get("workers", [])
w01 = [w for w in workers if w["id"] == "worker-01"]
w01_status = w01[0]["status"] if w01 else "NOT FOUND"
print(f"\n  Worker-01: {w01_status}")

if w01_status == "ONLINE":
    print("\n" + "=" * 70)
    print("STEP 5.5: Full Chain — Master POST /task -> Worker")
    print("=" * 70)

    tests = [
        ("RSI XAUUSD", {
            "worker_type": "indicator-worker",
            "indicator": "RSI",
            "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
            "params": {"period": 14}
        }),
        ("EMA XAUUSD", {
            "worker_type": "indicator-worker",
            "indicator": "EMA",
            "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
            "params": {"period": 10}
        }),
        ("SMA XAUUSD", {
            "worker_type": "indicator-worker",
            "indicator": "SMA",
            "data": {"symbol": "XAUUSD", "close": [44.0,44.34,44.09,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,46.41,46.22,45.64]},
            "params": {"period": 10}
        }),
    ]

    chain_pass = 0
    for name, payload in tests:
        print(f"\n--- {name} ---")
        code, resp = post_json(f"{MASTER}/task", payload)
        data = resp.get("data", {})
        status = data.get("status", "UNKNOWN")
        task_id = data.get("task_id", "")
        ok = status == "COMPLETED"
        if ok:
            chain_pass += 1
        print(f"  task_id: {task_id}")
        print(f"  status:  {status}")
        print(f"  worker:  {data.get('worker_id', 'N/A')}")

        if task_id:
            code2, resp2 = get_json(f"{MASTER}/task/{task_id}")
            d2 = resp2.get("data", {})
            result_exists = d2.get("result_exists", False)
            print(f"  result_exists: {result_exists}")
            if result_exists:
                print(f"  result_path:   {d2.get('result_path')}")

    print("\n" + "=" * 70)
    print("STEP 5 FINAL SUMMARY")
    print("=" * 70)
    print(f"  Master /health:     HTTP {get_json(f'{MASTER}/health')[0]}")
    print(f"  Master /workers:    HTTP {code} ({resp.get('data',{}).get('count',0)} workers)")
    print(f"  Worker-01:          {w01_status} (latency={w01[0].get('latency_ms')}ms)")
    print(f"  Full chain:         {chain_pass}/{len(tests)} tasks COMPLETED")
    print(f"  RSI/EMA/SMA:        ALL PASS" if chain_pass == len(tests) else f"  PARTIAL: {chain_pass}/{len(tests)}")
    print("=" * 70)
else:
    print(f"\n  Worker-01 is {w01_status} — cannot proceed with chain test")
    print("  Check Xavier Worker-01 container is running")
