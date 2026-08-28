# V9.0 MT5 模拟盘 — Phase 1 Design

> **状态：** 已冻结。  
> **日期：** 2026-08-24

## 1. 纠正

原路线 V5 是「研究进 MT5」。后来收成只写本机 json，禁止 `order_send`。那不是你要的模拟盘。

V9 补上：黄金 / 欧美 / 原油 / 美日，**人手确认后在 MT5 模拟账户里挂出**，终端能看见。

**仍不做实盘发单。** 账户若是 live → 拒绝。

## 2. Xavier 为什么「不装 MT5」但仍算 MT5

MT5 终端只在 Windows 上跑。Xavier 是 ARM Linux，装不了官方终端，也调不了 `MetaTrader5` 包。

正确分工：

```
Windows Master  ←→  本机 MT5（拉 K 线 / 模拟盘下单）
       ↓ close[]
Xavier 指标 / 回测 Worker   （只算数，不知道 MT5）
```

所以不是 Xavier 没用，是 **Xavier 算 MT5 的数，不跑 MT5 程序**。

## 3. 同花顺

本机环境测不了同花顺官方下单/行情接口（没有可用的、能冒烟的 API）。  
A 股仍走现有因子 Worker + `moutai.csv`。同花顺实接另开模块，不在本版假装已经通。

## 4. 范围

| 做 | 不做 |
| --- | --- |
| 四品种：XAUUSD、EURUSD、原油（按终端里实际代码解析）、USDJPY | 实盘 `order_send` |
| `source=mt5` 拉收盘价，交给现有 indicator-worker | 改 Xavier 代码 |
| 人手 `confirm=true` 后，demo 才 `order_send` | 自动下单、队列 |
| 本机纸质单仍记账（有 ticket 号） | 同花顺下单 |
| 新端口 / 新 Worker | |

原油别名按终端探测：`XTIUSD` / `USOIL` / `CRUDE` / `WTICOUSD` 等，用第一个有报价的。

## 5. 接口

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/mt5/status` | 仍探测 demo/live；增加四品种是否有数 |
| `GET` | `/api/v1/mt5/quotes` | 四品种最新价（没有终端则空） |
| `POST` | `/api/v1/research/run` | 增加可选 `source=mt5`、`symbol` |
| `POST` | `/api/v1/orders/submit` | demo 才发到 MT5；live 拒绝 |

测试默认 `TRADEMIND_MT5_SEND=0`，避免冒烟误挂单。本机运行默认允许发模拟盘。

## 6. 实现对照

| 文件 | 作用 |
|------|------|
| `master/api/app/service/mt5_service.py` | 探测 / 拉 M15 / 模拟盘 `order_send` |
| `master/api/app/service/research_service.py` | `source=mt5` 只给 Xavier `{symbol, close}` |
| `master/api/app/service/order_service.py` | demo 才发终端；live 拒绝；SEND=0 纸质记账 |
| `dashboard/index.html` | 黄金/欧美/原油/美日芯片 |

不要接旧的 `master/api/app/mt5_bridge.py`（轮询 OHLCV，硬编码 IP）。
