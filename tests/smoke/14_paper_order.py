"""Smoke: V5 paper order from existing research. No broker send."""
from __future__ import print_function

import json
import os
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER = "http://127.0.0.1:9000"
DASH = os.path.join(ROOT, "dashboard", "index.html")
RESEARCH = "tm-research-20260823-000001"


class LiveApi(object):
    def post(self, path, payload, timeout=30):
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

    def get(self, path, timeout=15):
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


class AppApi(object):
    def __init__(self):
        api_root = os.path.join(ROOT, "master", "api")
        sys.path.insert(0, api_root)
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def post(self, path, payload, timeout=30):
        resp = self.client.post(path, json=payload)
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"raw": resp.text}

    def get(self, path, timeout=15):
        resp = self.client.get(path)
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"raw": resp.text}


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    with open(DASH, "r", encoding="utf-8") as fh:
        html = fh.read()
    if ("确认挂模拟盘" in html or "确认挂模拟单" in html) and "function submitPaperOrder(" in html:
        print("[PASS] dashboard has confirm order button")
    else:
        print("[FAIL] dashboard missing paper order button")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/orders/submit" not in init:
        print("[PASS] init() does not auto-submit orders")
    else:
        print("[FAIL] init() submits orders")
        failed += 1

    src = open(os.path.join(ROOT, "master", "api", "app", "service", "order_service.py"), "r", encoding="utf-8").read()
    if "order_send(" not in src and "mt5.order_send" not in src:
        print("[PASS] service does not send broker orders")
    else:
        print("[FAIL] broker send present in order_service")
        failed += 1

    api = AppApi()
    code, data = api.post("/api/v1/orders/submit", {"research_id": RESEARCH})

    if data.get("code") == "TM-1001":
        print("[PASS] missing confirm TM-1001")
    else:
        print("[FAIL] missing confirm %s %s" % (code, data))
        failed += 1

    code, data = api.post("/api/v1/orders/submit", {"research_id": "tm-research-missing", "confirm": True})
    if data.get("code") == "TM-1003":
        print("[PASS] missing research TM-1003")
    else:
        print("[FAIL] missing research %s %s" % (code, data))
        failed += 1

    code, body = api.post("/api/v1/orders/submit", {"research_id": RESEARCH, "confirm": True})
    payload = body.get("data") or {}
    if body.get("success") and payload.get("mode") in ("paper", "demo") and payload.get("order_id"):
        print("[PASS] paper submit %s %s %s" % (payload.get("order_id"), payload.get("side"), payload.get("status")))
    elif body.get("code") == "TM-1005":
        print("[PASS] paper already ACCEPTED TM-1005")
    else:
        print("[FAIL] paper submit %s %s" % (code, body))
        failed += 1

    code2, body2 = api.post("/api/v1/orders/submit", {"research_id": RESEARCH, "confirm": True})
    if body2.get("code") == "TM-1005":
        print("[PASS] duplicate ACCEPTED TM-1005")
    else:
        print("[FAIL] duplicate %s %s" % (code2, body2))
        failed += 1

    scode, status = api.get("/api/v1/mt5/status")
    if status.get("success") and "account_mode" in (status.get("data") or {}):
        print("[PASS] mt5 status %s" % ((status.get("data") or {}).get("account_mode")))
    else:
        print("[FAIL] mt5 status %s %s" % (scode, status))
        failed += 1

    if failed:
        print("SMOKE_14_FAIL")
        return 1
    print("SMOKE_14_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
