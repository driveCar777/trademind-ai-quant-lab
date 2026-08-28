"""Wait until Master :9000 and AI Gateway :9100 are healthy."""
from __future__ import print_function

import json
import sys
import time

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError


def get_json(url, timeout=4):
    req = Request(url)
    try:
        resp = urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", "replace")
        return resp.getcode(), json.loads(body)
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {}
    except (URLError, ValueError, OSError):
        return None, {}


def wait_master(seconds):
    url = "http://127.0.0.1:9000/health"
    deadline = time.time() + seconds
    while time.time() < deadline:
        code, data = get_json(url)
        if code == 200 and data.get("status") == "healthy":
            print("MASTER_OK version=%s" % data.get("version"))
            return True
        time.sleep(2)
    print("MASTER_FAIL")
    return False


def wait_gateway(seconds):
    url = "http://127.0.0.1:9100/health"
    deadline = time.time() + seconds
    last = "waiting"
    while time.time() < deadline:
        code, data = get_json(url)
        inner = data.get("data") or {}
        if code == 200 and inner.get("model_loaded"):
            print("GATEWAY_OK model=%s status=%s" % (
                inner.get("model_name"), inner.get("status")))
            return True
        if code == 200:
            last = "listening, model_loaded=%s" % inner.get("model_loaded")
        else:
            last = "not ready (%s)" % code
        print("  gateway: %s" % last)
        time.sleep(5)
    print("GATEWAY_FAIL %s" % last)
    return False


def main():
    master_ok = wait_master(60)
    gateway_ok = wait_gateway(180)
    if master_ok and gateway_ok:
        print("LOCAL_START_PASS")
        return 0
    print("LOCAL_START_FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
