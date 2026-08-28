# V10.0 测通模拟盘 — Phase 1 Design

> **状态：** 已冻结。  
> **日期：** 2026-08-24

## 1. 纠正

V9 能拉 Ava 的 `GOLD`，但第 4 步只在 RSI≤30 / ≥70 才允许确认。黄金现价 RSI≈64 → `rsi_neutral` → 按钮灰掉。人以为「没法模拟交易」，其实是**信号门**挡住了**通路测试**。

进终端 ≠ 策略有效。本版只补通路。

## 2. 范围

| 做 | 不做 |
| --- | --- |
| 指标研究有品种时，人手选 BUY/SELL，`confirm=true` 后 demo 发 0.01 | 自动下单 |
| RSI 极端仍走原拟单 | 实盘 |
| 文案写明：测通不是预测 | 新因子、新回测、同花顺 |

## 3. 接口

`POST /api/v1/orders/submit` 增加可选 `side=BUY|SELL`。

- 无 `side`：仍按 RSI 门（中性拒绝）
- 有 `side`：仅 `preset=indicator` 且有品种；`reason=wire_test`
- 非法 `side` → `TM-1001`
- 仍须 `confirm=true`。live 拒绝。测试 `TRADEMIND_MT5_SEND=0`

## 4. 有效性（写进控制台，不当成已实现）

测通只证明：Master 能在模拟账户下 0.01 手。  
不证明：能赚钱、因子对、没有过拟合。
