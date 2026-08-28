# TradeMind Worker SDK

Python 客户端，供 Master 调用 Worker。

## 目标 API（V1.2）

```python
from trademind_client import WorkerClient

client = WorkerClient("192.168.1.111")

rsi = client.calculate(
    worker="indicator",
    indicator="RSI",
    data={"symbol": "EURUSD", "timeframe": "M15", "close": [...]},
    params={"period": 14},
)
```

## 状态

骨架占位，V1.2 开发。

## 相关

- [ROADMAP.md](../ROADMAP.md) — V1.2 Master ↔ Worker
