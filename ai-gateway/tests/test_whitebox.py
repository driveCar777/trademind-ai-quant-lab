"""White-box tests for AI Gateway V3.0 (no running server / no GPU required).

These verify that the code is *correctly wired* even before llama-cpp-python
is installed (Phase 1.5):

  * modules import cleanly
  * FastAPI routes are registered
  * /health reports degraded (model not loaded) but stays 200
  * /models lists the model with loaded=False
  * inference endpoints return 503 when the model is unavailable
  * InferenceEngine degrades gracefully when llama_cpp is absent

Run:
    .venv\\Scripts\\python.exe -m pytest tests\\test_whitebox.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import inference as inference_mod
import server


@pytest.fixture()
def client() -> TestClient:
    return TestClient(server.app)


def test_server_imports():
    assert server is not None
    assert hasattr(server, "app")


def test_routes_registered():
    paths = {route.path for route in server.app.routes}
    assert "/health" in paths
    assert "/models" in paths
    assert "/api/v1/ai/generate" in paths
    assert "/api/v1/ai/describe" in paths
    assert "/api/v1/ai/signal" in paths
    assert "/api/v1/ai/chat" in paths


def test_inference_engine_lazy_import():
    eng = inference_mod.InferenceEngine(model_path="models/qwen2.5-14b-instruct-q4_k_m.gguf")
    eng.load()
    assert eng.is_loaded is False
    assert eng.load_error is not None
    assert "llama_cpp" in eng.load_error.lower()


def test_inference_generate_raises_when_not_loaded():
    eng = inference_mod.InferenceEngine(model_path="models/qwen2.5-14b-instruct-q4_k_m.gguf")
    with pytest.raises(RuntimeError):
        eng.generate(messages=[{"role": "user", "content": "hi"}], max_tokens=8)


def test_inference_stats_initial():
    eng = inference_mod.InferenceEngine(model_path="models/does-not-exist.gguf")
    assert eng.stats == {"total_requests": 0, "total_tokens": 0, "avg_latency_ms": 0}


def test_health_degraded(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["service"] == "trademind-ai-gateway"
    assert data["version"] == "3.0.0"
    assert data["status"] == "degraded"
    assert data["model_loaded"] is False
    assert data["model_name"] == "Qwen2.5-14B-Instruct"


def test_models_listed_not_loaded(client: TestClient, monkeypatch):
    monkeypatch.delenv("TRADEMIND_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("TRADEMIND_CURSOR_API_KEY", raising=False)
    import providers
    providers._ds_cache = (0.0, None)
    providers._cu_cache = (0.0, None)
    resp = client.get("/models")
    assert resp.status_code == 200
    models = resp.json()["data"]["models"]
    assert len(models) >= 1
    assert models[0]["loaded"] is False
    assert models[0]["name"] == "Qwen2.5-14B-Instruct"
    assert models[0]["id"] == "local:qwen2.5-14b-instruct"
    ids = [m["id"] for m in models]
    assert "deepseek:deepseek-chat" in ids
    assert any(i.startswith("cursor:") for i in ids)
    ds = next(m for m in models if m["id"] == "deepseek:deepseek-chat")
    assert ds["available"] is False
    assert all(not m["available"] for m in models if m["provider"] == "cursor")


def test_unknown_model_400(client: TestClient):
    resp = client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "hi"}], "model": "nope:x"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "TM-1001"


def test_chat_503_when_model_unavailable(client: TestClient):
    resp = client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "你好"}]},
    )
    assert resp.status_code == 503


def test_generate_503_when_model_unavailable(client: TestClient):
    resp = client.post(
        "/api/v1/ai/generate",
        json={"type": "research_report", "context": {"stock": "600519"}},
    )
    assert resp.status_code == 503


def test_signal_503_when_model_unavailable(client: TestClient):
    resp = client.post(
        "/api/v1/ai/signal",
        json={"type": "signal_interpretation", "context": {"symbol": "EURUSD"}},
    )
    assert resp.status_code == 503
