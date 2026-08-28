# V6.0 今日台账 — Design

> **状态：** ✅ FROZEN（2026-08-23）。  
> **日期：** 2026-08-23

## 1. 要解决什么

V5 已能落纸质单，但人看不清「这笔研究会挂成什么样」。  
V6：先看拟单，再确认；当天研究和纸质单放在一起。**仍不往 MT5 发单。**

## 2. 范围

| 做 | 不做 |
|----|------|
| `GET /api/v1/desk/today` 只读当天档案 | `order_send`、实盘、新行情 |
| 弹窗先 preview 再允许确认 | 研究结束自动 submit |
| 今日台账计数 | 队列、库、改 Worker |

## 3. 冒烟

1. `GET /desk/today` 有 `date` 与两个列表。  
2. preview `000001` → `SELL` / `paper`，不新增订单文件。  
3. 控制台源码：`showResearch` 调用 `/orders/preview`；`init()` 不 submit。  
4. 服务仍无 broker send。

## 4. 五步

| 步 | 状态 |
|----|------|
| 1 Design | 本文 + SPEC §19 + Decision 027 |
| 2 Implement | ✅ |
| 3 Smoke | ✅ `tests/smoke/15_paper_desk.py` |
| 4 Stability | ✅ `tests/stability/04_paper_desk.py` |
| 5 Freeze | ✅ |
