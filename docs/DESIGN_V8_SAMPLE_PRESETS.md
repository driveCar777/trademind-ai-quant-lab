# V8.0 因子 / 回测本机样本 — Phase 1 Design

> **状态：** ✅ FROZEN（2026-08-24）。  
> **日期：** 2026-08-24

## 1. 要解决什么

V7 只把指标收盘价搬进了 `data/samples/eurusd.csv`。  
茅台因子、黄金回测的参数还写在 `PRESETS` 里，人看不见、换不了。

V8：这两个预设也改成本机 csv。Master 只读文件、拼出 **Worker 已经认识的 payload**。不改 Xavier、不发行情、不发 MT5。

```
茅台因子  → data/samples/moutai.csv   → {stock, date}
黄金回测  → data/samples/xauusd.csv   → {strategy, symbol, start}
欧元美元  → data/samples/eurusd.csv   → {symbol, close}   （V7 已有）
```

Worker 仍用自己的内置库算。本模块不把 K 线塞进因子/回测节点。

## 2. 冻结范围

| 做 | 不做 |
| --- | --- |
| 内置 `moutai.csv` / `xauusd.csv`，内容与旧硬编码相同 | 改 Worker、改板上表 |
| `GET /api/v1/samples` 带 `kind` | 上传控件、数据库、行情 |
| 默认：factor=`moutai`，backtest=`xauusd` | 监控也改文件 |
| 种类和预设对不上 → `TM-1001` | `order_send` |
| 两步链不带 `sample_id`，每步用各自默认 | 一个 sample_id 同时喂两步 |

## 3. 文件

| 文件 | kind | 表头 | 默认给 |
|------|------|------|--------|
| `eurusd.csv` | indicator | `symbol,close` | 指标 |
| `moutai.csv` | factor | `stock,date` | 因子 |
| `xauusd.csv` | backtest | `strategy,symbol,start` | 回测 |

`sample_id` 规则同 V7。监控带 `sample_id` → `TM-1001`。

## 4. 验收

1. 三个内置文件在，`GET /samples` 都能看到且 `kind` 对。  
2. `PRESETS` 不再写死 600519 / EMA_MACD。  
3. `eurusd` 拿去跑因子 → `TM-1001`。  
4. 控制台 `init()` 仍不自动研究。  
5. 不发 MT5。
