# Data Layer V0.1

Windows Master 本地市场历史数据层。不接 V11.7，不接 Master API，不接 Xavier。

权威说明：`docs/DATA_LAYER_V0.1.md`

## 职责

- 只读 MT5 行情（`copy_rates_range` 优先）
- 校验 OHLCV + UTC timestamp
- 写入不可覆盖的 dataset + manifest + SHA256
- 本地 Python API：`DatasetRepository`

## 禁止

- `order_send` 及任何交易执行 API
- 覆盖已冻结 dataset
- 用 close 合成 volume
- 把新数据送进 V11.7 / 自动回测

## 入口

```text
master/api/.venv/Scripts/python.exe scripts/data_layer_fetch.py --matrix
master/api/.venv/Scripts/python.exe -m unittest discover -s tests/data_layer -v
```
