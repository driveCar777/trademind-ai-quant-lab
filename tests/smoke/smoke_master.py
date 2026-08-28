"""Master API smoke tests - requires Master (port 9000) and Indicator Worker (port 8000)."""

import sys
import time

import requests

MASTER_URL = "http://127.0.0.1:9000"
WORKER_URL = "http://127.0.0.1:8000"

SAMPLE_TASK = {
    "worker_type": "indicator",
    "indicator": "RSI",
    "data": {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "close": [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00,
            46.03, 46.41, 46.22, 45.64,
        ],
    },
    "params": {"period": 14},
}


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    return ok


def wait_for(url, path="/health", timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}{path}", timeout=2)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def main():
    results = []

    # 0. Pre-check worker
    if not wait_for(WORKER_URL):
        print(f"[FAIL] Worker not reachable at {WORKER_URL}")
        return 1

    # 1. Health
    r = requests.get(f"{MASTER_URL}/health", timeout=5)
    results.append(check("GET /health", r.status_code == 200 and r.json().get("status") == "healthy"))

    # 2. Workers list
    r = requests.get(f"{MASTER_URL}/workers", timeout=5)
    workers = r.json().get("workers", []) if r.status_code == 200 else []
    has_indicator = any(w.get("type") == "indicator" for w in workers)
    results.append(check("GET /workers", r.status_code == 200 and has_indicator, f"count={len(workers)}"))

    # 3. Submit task
    r = requests.post(f"{MASTER_URL}/task", json=SAMPLE_TASK, timeout=60)
    body = r.json() if r.status_code == 200 else {}
    task_id = body.get("task_id")
    results.append(check("POST /task", r.status_code == 200 and bool(task_id), f"task_id={task_id}"))

    # 4. Query task
    if task_id:
        r = requests.get(f"{MASTER_URL}/task/{task_id}", timeout=5)
        detail = r.json() if r.status_code == 200 else {}
        has_result = detail.get("status") == "completed" and detail.get("result") is not None
        results.append(check("GET /task/{id}", r.status_code == 200 and has_result, f"status={detail.get('status')}"))
    else:
        results.append(check("GET /task/{id}", False, "no task_id"))

    # 5. End-to-end RSI
    if task_id and detail.get("result"):
        rsi_ok = detail["result"].get("indicator") == "RSI" and detail["result"].get("success") is True
        results.append(check("E2E Master->Worker RSI", rsi_ok))
    else:
        results.append(check("E2E Master->Worker RSI", False))

    passed = all(results)
    print(f"\nSmoke test: {'ALL PASS' if passed else 'FAILED'} ({sum(results)}/{len(results)})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
