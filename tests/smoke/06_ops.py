"""Smoke: ops routes exist; unknown worker uses TM-1001."""
from __future__ import print_function

import json
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError


def post(path):
    req = Request("http://127.0.0.1:9000" + path, data=b"", method="POST")
    try:
        resp = urlopen(req, timeout=20)
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}


def main():
    failed = 0
    code, data = post("/api/v1/ops/worker/worker-99/start")
    if data.get("code") == "TM-1001" and data.get("success") is False:
        print("[PASS] unknown worker TM-1001")
    else:
        print("[FAIL] unknown worker %s %s" % (code, data))
        failed += 1

    code, data = post("/api/v1/ops/worker/worker-02/start")
    hint = (data.get("data") or {}).get("hint", "")
    if data.get("success") and "已经在线" in hint:
        print("[PASS] worker-02 already up")
    elif data.get("success"):
        print("[PASS] worker-02 start accepted: %s" % hint)
    else:
        print("[FAIL] worker-02 start %s %s" % (code, data))
        failed += 1

    if failed:
        print("SMOKE_06_FAIL")
        return 1
    print("SMOKE_06_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
