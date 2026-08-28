# V5.0 模拟纸质单 — Design

> **状态：** ✅ FROZEN（2026-08-23）。  
> **日期：** 2026-08-23

## 1. 拍板（不再空着）

用户要求连续做下去。本版按实验室默认锁死：

- **只模拟纸质单。** V5.0 禁止 `order_send`，避免误打实盘。
- **必须人手确认。** 控制台点「确认挂模拟单」，请求带 `confirm=true`。
- **研究不自动开单。** `init()` 与 `/research/run` 都不碰订单。
- Master 只在 Windows 探测本机 MT5。Xavier 不装、不调 MT5。

这就是最终目标里「交易辅助」的第一块可运行形态：人能看见「若下单会是什么」，并留下可核对记录。仍不是券商。

## 2. 范围

| 做 | 不做 |
|----|------|
| 读已有研究 → 拟单 → 人手确认后落 `data/orders/` | 实盘、`order_send`、止损止盈、仓位管理 |
| 探测 MT5 包/连接/demo\|live | 新端口 9200、改冻结 Worker |
| 同一研究只接受一张 ACCEPTED | 队列、库、自动定时 |

旧文件 `master/api/app/mt5_bridge.py` 是拉 K 线脚本，本版不改、不接入控制台。

## 3. 拟单规则

- 指标研究、摘要能读出 RSI：超买空、超卖多，中间拒绝。
- 因子 / 回测 / 监控：拒绝（不是外汇下单信号）。

## 4. 冒烟

1. 无 `confirm` → TM-1001。  
2. 不存在的研究 → TM-1003。  
3. 已有 indicator 研究提交 → 落盘，`mode=paper`，有 `reason` 或 `ACCEPTED`。  
4. 同一研究再提交 → TM-1005。  
5. 控制台有「确认挂模拟单」，`init()` 不调用 `/orders/submit`。

## 5. 五步

| 步 | 状态 |
|----|------|
| 1 Design | ✅ 本文 + SPEC §18 + Decision 026 |
| 2 Implement | ✅ |
| 3 Smoke | ✅ `tests/smoke/14_paper_order.py` |
| 4 Stability | ✅ `tests/stability/03_paper_order.py` |
| 5 Freeze | ✅ |
