"""V3.0 smoke: Master AI Gateway proxy + Dashboard AI entry.

Does not load the Qwen model. Offline / mock path is the default.
If Master is already running on :9000, also hits the live proxy health route.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
MASTER_API = ROOT / "master" / "api"
DASHBOARD = ROOT / "dashboard" / "index.html"
sys.path.insert(0, str(MASTER_API))

from app.config.settings import AIGatewaySettings, Settings  # noqa: E402
from app.service.ai_gateway_proxy import AIGatewayProxy  # noqa: E402


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_proxy_offline():
    proxy = AIGatewayProxy(
        Settings(ai_gateway=AIGatewaySettings(url="http://127.0.0.1:19999", timeout_seconds=1))
    )
    original = requests.request

    def boom(**kwargs):
        raise requests.ConnectionError("gateway down")

    requests.request = boom
    try:
        resp = proxy.forward("GET", "/health")
    finally:
        requests.request = original
    body = json.loads(resp.body)
    assert resp.status_code == 503
    assert body["success"] is False
    assert body["code"] == "TM-1002"
    assert "offline" in body["message"].lower()
    print("[PASS] proxy offline -> 503 TM-1002")


def test_proxy_timeout():
    proxy = AIGatewayProxy(
        Settings(ai_gateway=AIGatewaySettings(url="http://127.0.0.1:19999", timeout_seconds=1))
    )
    original = requests.request

    def boom(**kwargs):
        raise requests.Timeout("gateway timeout")

    requests.request = boom
    try:
        resp = proxy.forward("GET", "/health")
    finally:
        requests.request = original
    body = json.loads(resp.body)
    assert resp.status_code == 504
    assert body["code"] == "TM-1004"
    print("[PASS] proxy timeout -> 504 TM-1004")


def test_proxy_success():
    proxy = AIGatewayProxy(
        Settings(ai_gateway=AIGatewaySettings(url="http://127.0.0.1:9100", timeout_seconds=5))
    )
    payload = {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "trademind-ai-gateway",
            "model_name": "Qwen2.5-14B-Instruct",
            "model_loaded": True,
        },
    }

    def fake_request(**kwargs):
        assert kwargs["url"] == "http://127.0.0.1:9100/health"
        return _FakeResponse(200, payload)

    original = requests.request
    requests.request = fake_request
    try:
        resp = proxy.forward("GET", "/health")
        body = json.loads(resp.body)
        assert resp.status_code == 200
        assert body["success"] is True
        assert body["data"]["model_name"] == "Qwen2.5-14B-Instruct"
    finally:
        requests.request = original
    print("[PASS] proxy success -> Qwen2.5-14B-Instruct")


def test_dashboard_ai_entry():
    html = DASHBOARD.read_text(encoding="utf-8")
    assert "AI 网关" in html or "AI 助手" in html
    assert "问 AI" in html
    assert "通义千问" in html
    assert "/api/v1/ai/chat" in html
    assert "/api/v1/ai/generate" in html
    assert "GPT-5.6" not in html
    print("[PASS] dashboard AI entry present (Chinese), no GPT-5.6")


def test_master_routes_registered():
    from app.main import app

    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/ai/health",
        "/api/v1/ai/models",
        "/api/v1/ai/generate",
        "/api/v1/ai/describe",
        "/api/v1/ai/signal",
        "/api/v1/ai/chat",
    ):
        assert path in paths, path
    print("[PASS] Master AI proxy routes registered")


def test_live_master_optional():
    try:
        r = requests.get("http://127.0.0.1:9000/api/v1/ai/health", timeout=3)
    except requests.RequestException:
        print("[SKIP] live Master :9000 not running")
        return
    body = r.json()
    assert "success" in body
    assert body.get("code") in (None, "TM-0000", "TM-1002", "TM-1003", "TM-1004")
    print(f"[PASS] live Master proxy health HTTP {r.status_code} code={body.get('code')}")


def main():
    test_proxy_offline()
    test_proxy_timeout()
    test_proxy_success()
    test_dashboard_ai_entry()
    test_master_routes_registered()
    test_live_master_optional()
    print("04_ai_gateway: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
