import requests
import json
import sys

MASTER = "http://127.0.0.1:9000"

tests = [
    {"strategy": "EMA_MACD", "symbol": "XAUUSD", "start": "2025-01-01"},
    {"strategy": "RSI_REVERSAL", "symbol": "EURUSD", "start": "2025-06-01"},
    {"strategy": "BOLLINGER_BREAKOUT", "symbol": "GBPUSD", "start": "2025-03-01"},
    {"strategy": "TREND_FOLLOW", "symbol": "USDJPY", "start": "2025-01-01"},
    {"strategy": "MOMENTUM", "symbol": "GOLD", "start": "2025-01-01"},
]

completed = 0
for t in tests:
    payload = {
        "worker_type": "backtest-worker",
        "indicator": t["strategy"],
        "data": {"strategy": t["strategy"], "symbol": t["symbol"], "start": t["start"]},
        "params": {},
    }
    try:
        r = requests.post(f"{MASTER}/task", json=payload, timeout=30)
        result = r.json()
        data = result.get("data", {})
        status = data.get("status")
        worker = data.get("worker_id", "?")
        if status == "COMPLETED":
            completed += 1
        print(f"  [{status}] {t['strategy']:<25} {t['symbol']:<8} worker={worker}")
        sys.stdout.flush()
    except Exception as e:
        print(f"  [ERROR] {t['strategy']}: {e}")
        sys.stdout.flush()

print(f"\n  Result: {completed}/{len(tests)} COMPLETED")
sys.stdout.flush()
