"""API integration tests."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.main import app

CALCULATE_PATH = "/api/v1/indicator/calculate"

SAMPLE_PAYLOAD = {
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


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "indicator-worker"


def test_ready_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["worker"] == "xavier-worker-01"
    assert body["queue"] == 0


def test_version_endpoint(client):
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "indicator-worker"
    assert body["version"] == "1.0.0"
    assert body["build"] == "2026-07"
    assert body["python"] == "3.8"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_list_indicators(client):
    response = client.get("/indicators")
    assert response.status_code == 200
    assert "RSI" in response.json()["indicators"]


def test_calculate_rsi(client):
    response = client.post(CALCULATE_PATH, json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["indicator"] == "RSI"
    assert body["result"]["latest"] is not None


def test_calculate_invalid_indicator(client):
    payload = {**SAMPLE_PAYLOAD, "indicator": "UNKNOWN"}
    response = client.post(CALCULATE_PATH, json=payload)
    assert response.status_code == 400


def test_calculate_empty_close(client):
    payload = {
        "indicator": "RSI",
        "data": {"symbol": "EURUSD", "timeframe": "M15", "close": []},
        "params": {"period": 14},
    }
    response = client.post(CALCULATE_PATH, json=payload)
    assert response.status_code == 422


def test_calculate_invalid_period(client):
    payload = {**SAMPLE_PAYLOAD, "params": {"period": 0}}
    response = client.post(CALCULATE_PATH, json=payload)
    assert response.status_code == 400


def test_calculate_mismatched_series_length(client):
    payload = {
        "indicator": "RSI",
        "data": {
            "symbol": "EURUSD",
            "timeframe": "M15",
            "close": [1.0, 2.0, 3.0],
            "high": [1.0, 2.0],
        },
        "params": {"period": 2},
    }
    response = client.post(CALCULATE_PATH, json=payload)
    assert response.status_code == 422


def test_calculate_large_dataset_performance(client):
    close = [100.0 + (i % 50) * 0.1 for i in range(100_000)]
    payload = {
        "indicator": "SMA",
        "data": {"symbol": "EURUSD", "timeframe": "M1", "close": close},
        "params": {"period": 20},
    }
    response = client.post(CALCULATE_PATH, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["latest"] is not None
    assert body["calculation_time_ms"] < 30_000


def test_concurrent_calculate_requests(client):
    def send_request(_):
        return client.post(CALCULATE_PATH, json=SAMPLE_PAYLOAD)

    with ThreadPoolExecutor(max_workers=8) as executor:
        responses = list(executor.map(send_request, range(16)))

    assert all(response.status_code == 200 for response in responses)
