"""Smoke: GET /task/{id} includes result; GET /tasks does not load bodies."""
from __future__ import print_function

import json
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError


MASTER = "http://127.0.0.1:9000"


def get(path, timeout=8):
    try:
        resp = urlopen(Request(MASTER + path), timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}
    except Exception as exc:
        return None, {"error": str(exc)}


def post_json(path, payload, timeout=60):
    raw = json.dumps(payload).encode("utf-8")
    req = Request(MASTER + path, data=raw, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urlopen(req, timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}
    except Exception as exc:
        return None, {"error": str(exc)}


def main():
    failed = 0

    code, listing = get("/tasks?limit=5")
    tasks = ((listing.get("data") or {}).get("tasks") or []) if isinstance(listing, dict) else []
    if code == 200 and tasks and tasks[0].get("result") is not None:
        print("[FAIL] GET /tasks leaked result body")
        failed += 1
    elif code == 200:
        print("[PASS] GET /tasks result is null")
    else:
        print("[FAIL] GET /tasks %s %s" % (code, listing))
        failed += 1

    task_id = None
    for item in tasks:
        if item.get("status") == "COMPLETED" and item.get("result_exists"):
            task_id = item.get("task_id")
            break
    if not task_id:
        task_id = "tm-task-20260822-000001"

    code, detail = get("/task/" + task_id)
    payload = (detail.get("data") or {}) if isinstance(detail, dict) else {}
    result = payload.get("result")
    if code == 200 and isinstance(result, dict) and result:
        print("[PASS] GET /task/{id} has result (%s)" % task_id)
    else:
        print("[FAIL] GET /task/{id} missing result %s %s" % (code, payload.get("task_id")))
        failed += 1

    code, workers_body = get("/workers")
    workers = ((workers_body.get("data") or {}).get("workers") or []) if isinstance(workers_body, dict) else []
    online_01 = any(w.get("id") == "worker-01" and w.get("status") == "ONLINE" for w in workers)
    if not online_01:
        print("[SKIP] worker-01 offline, no new RSI")
    else:
        body = {
            "worker_type": "indicator-worker",
            "indicator": "RSI",
            "data": {
                "symbol": "EURUSD",
                "close": [1.082, 1.0835, 1.0828, 1.0841, 1.0836, 1.0845, 1.0839, 1.0852,
                          1.0848, 1.0855, 1.085, 1.0862, 1.0858, 1.087, 1.0865, 1.0878,
                          1.0872, 1.0885, 1.088, 1.0892, 1.0888, 1.0895, 1.089, 1.0898,
                          1.0893, 1.0902, 1.0897, 1.091, 1.0905, 1.0915]
            },
            "params": {"period": 14}
        }
        code, created = post_json("/task", body)
        new_id = ((created.get("data") or {}).get("task_id")) if isinstance(created, dict) else None
        if created.get("success") and new_id:
            code2, fresh = get("/task/" + new_id)
            latest = (((fresh.get("data") or {}).get("result") or {}).get("result") or {}).get("latest")
            if code2 == 200 and isinstance(latest, (int, float)):
                print("[PASS] default RSI latest=%s" % latest)
            else:
                print("[FAIL] new RSI missing latest %s" % fresh)
                failed += 1
        else:
            print("[FAIL] POST /task RSI %s %s" % (code, created))
            failed += 1

    if failed:
        print("SMOKE_07_FAIL")
        return 1
    print("SMOKE_07_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
