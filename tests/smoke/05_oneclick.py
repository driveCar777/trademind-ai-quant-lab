"""Smoke: local one-click services are up."""
from __future__ import print_function

import json
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError


def get(url, timeout=8):
    try:
        resp = urlopen(Request(url), timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        return exc.code, {}
    except Exception as exc:
        return None, {"error": str(exc)}


def main():
    failed = 0
    code, data = get("http://127.0.0.1:9000/health")
    if code == 200 and data.get("status") == "healthy":
        print("[PASS] Master /health")
    else:
        print("[FAIL] Master /health %s %s" % (code, data))
        failed += 1

    code, data = get("http://127.0.0.1:9100/health")
    inner = data.get("data") or {}
    if code == 200 and inner.get("model_loaded"):
        print("[PASS] Gateway model_loaded %s" % inner.get("model_name"))
    else:
        print("[FAIL] Gateway /health %s loaded=%s" % (code, inner.get("model_loaded")))
        failed += 1

    code, data = get("http://127.0.0.1:9000/api/v1/ai/health")
    inner = (data.get("data") or {}) if isinstance(data, dict) else {}
    if code == 200 and (inner.get("model_loaded") or inner.get("status") in ("healthy", "degraded")):
        print("[PASS] Master proxy /api/v1/ai/health")
    else:
        print("[FAIL] Master proxy AI %s %s" % (code, data))
        failed += 1

    if failed:
        print("SMOKE_05_FAIL")
        return 1
    print("SMOKE_05_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
