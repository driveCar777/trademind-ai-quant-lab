"""Smoke tests for AI Gateway V3.0."""
import requests
import json
import sys

BASE = "http://localhost:9100"


def test_health():
    """GET /health"""
    r = requests.get(f"{BASE}/health", timeout=10)
    data = r.json()
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    assert data["success"] is True
    assert data["data"]["service"] == "trademind-ai-gateway"
    print(f"[PASS] /health -> {data['data']['status']}, model_loaded={data['data']['model_loaded']}")
    return data


def test_models():
    """GET /models"""
    r = requests.get(f"{BASE}/models", timeout=10)
    data = r.json()
    assert r.status_code == 200
    assert data["success"] is True
    models = data["data"]["models"]
    assert len(models) > 0
    print(f"[PASS] /models -> {len(models)} model(s), loaded={models[0]['loaded']}")
    return data


def test_chat():
    """POST /api/v1/ai/chat"""
    payload = {
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍你自己。"}
        ],
        "params": {"max_tokens": 128, "temperature": 0.3},
    }
    r = requests.post(f"{BASE}/api/v1/ai/chat", json=payload, timeout=120)
    data = r.json()
    assert r.status_code == 200, f"Chat failed: {r.status_code} {data}"
    assert data["success"] is True
    reply = data["data"]["reply"]
    assert len(reply) > 0
    print(f"[PASS] /api/v1/ai/chat -> {reply[:80]}...")
    return data


def test_generate():
    """POST /api/v1/ai/generate"""
    payload = {
        "type": "research_report",
        "context": {
            "stock": "600519",
            "stock_name": "贵州茅台",
            "sector": "白酒",
            "factors": {"roe": 30.12, "pe": 28.5},
            "score": {"total": 82, "grade": "A"},
            "indicators": {"rsi_14": 55.3, "macd_signal": "bullish"},
            "market_comment": "白酒板块近期资金流入",
        },
        "params": {"max_tokens": 512, "temperature": 0.3},
    }
    r = requests.post(f"{BASE}/api/v1/ai/generate", json=payload, timeout=120)
    data = r.json()
    assert r.status_code == 200, f"Generate failed: {r.status_code} {data}"
    assert data["success"] is True
    report = data["data"]["report"]
    assert len(report) > 50
    print(f"[PASS] /api/v1/ai/generate -> {len(report)} chars, {data['data']['tokens_used']} tokens")
    return data


def test_describe():
    """POST /api/v1/ai/describe"""
    payload = {
        "type": "strategy_description",
        "context": {
            "strategy": "EMA_MACD",
            "symbol": "XAUUSD",
            "params": {"short": 12, "long": 26, "signal": 9},
            "result": {
                "profit": -12.31,
                "max_drawdown": 21.41,
                "win_rate": 20.0,
                "total_trades": 30,
                "sharpe_ratio": -0.839,
                "profit_factor": 0.53,
            },
        },
        "params": {"max_tokens": 512, "temperature": 0.3},
    }
    r = requests.post(f"{BASE}/api/v1/ai/describe", json=payload, timeout=120)
    data = r.json()
    assert r.status_code == 200, f"Describe failed: {r.status_code} {data}"
    assert data["success"] is True
    desc = data["data"]["description"]
    assert len(desc) > 50
    print(f"[PASS] /api/v1/ai/describe -> {len(desc)} chars")
    return data


def test_signal():
    """POST /api/v1/ai/signal"""
    payload = {
        "type": "signal_interpretation",
        "context": {
            "symbol": "EURUSD",
            "indicators": {"rsi_14": 28.5, "macd_histogram": -0.0032},
            "price": {"current": 1.0815, "high_24h": 1.0890, "low_24h": 1.0780},
            "timeframe": "H4",
        },
        "params": {"max_tokens": 256, "temperature": 0.2},
    }
    r = requests.post(f"{BASE}/api/v1/ai/signal", json=payload, timeout=120)
    data = r.json()
    assert r.status_code == 200, f"Signal failed: {r.status_code} {data}"
    assert data["success"] is True
    interp = data["data"]["interpretation"]
    assert len(interp) > 20
    print(f"[PASS] /api/v1/ai/signal -> {len(interp)} chars")
    return data


def main():
    print("=" * 60)
    print("  AI Gateway V3.0 Smoke Tests")
    print("=" * 60)

    tests = [
        ("Health", test_health),
        ("Models", test_models),
        ("Chat", test_chat),
        ("Generate", test_generate),
        ("Describe", test_describe),
        ("Signal", test_signal),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except requests.ConnectionError:
            print(f"[SKIP] {name} - Gateway not running")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {name} - {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
