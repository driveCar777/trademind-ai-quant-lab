# TradeMind — 开发路线

> **2026-09-05 起，路线以 `docs/MASTER_PLAN_V2.md` 为准**（用户授权修改规划）。本文其余内容为 V1–V9 平台期历史对照；平台（Xavier / AI Gateway / 预置策略 / MT5 Bridge）已冻结、不再投入。研究状态见 `TODO.md`。

**各阶段目标（一句话 + 完成定义）：** `docs/STAGE_GOALS.md`  
下列旧勾选条目有过时内容，状态以 `TODO.md` / `STAGE_GOALS.md` 为准。

---

## V1.0 — Worker Template ✅

- [x] FastAPI Worker 模板
- [x] REST API `/api/v1/`
- [x] Prometheus `/metrics`
- [x] Docker Compose
- [x] `TRADEMIND_*` 配置
- [x] 测试套件

**状态：已完成，冻结。**

---

## V1.1 — Master 骨架

- [ ] Master 目录结构
- [ ] API / Scheduler / Dispatcher 模块占位
- [ ] Database / Result-Center 占位
- [ ] AI Gateway 占位
- [ ] Worker SDK 骨架

**目标：搭好骨架，不写业务。**

---

## V1.2 — Master ↔ Worker 通信

- [ ] `POST /task` — Master 下发任务
- [ ] Worker 执行计算
- [ ] `POST /result` — Worker 回传结果
- [ ] 数据库持久化
- [ ] Worker SDK `client.calculate(...)`

**目标：跑通 Master → Worker → Master 链路。**

---

## V1.3 — Dashboard

- [ ] 任务状态可视化
- [ ] Worker 健康监控
- [ ] 计算结果展示

---

## V2.0 — Factor Worker

- [ ] 复制 Worker Template
- [ ] 因子计算逻辑

---

## V2.1 — Backtest Worker

- [ ] 复制 Worker Template
- [ ] 回测引擎

---

## V3.0 — AI Gateway

- [ ] Arc A770M LLM 接入
- [ ] Research Agent 基础

---

## V4.0 — Research Agent ✅ 已冻结（2026-08-23）

- [x] Phase 1 Design：`docs/DESIGN_V4_RESEARCH_AGENT.md`
- [x] 实现：人点「研究一笔」= 1 次计算 + 至多 1 次 AI
- [x] 冒烟 12 / 稳定 01 / 冻结

第一冻不做：自动发现异常、AI 发明策略、连跑回测、MT5。

---

## V4.1 — 两步研究 ✅ 已冻结（2026-08-23）

- [x] 可选 `chain`，最多两步现有预设
- [x] 控制台「因子后再回测」
- [x] Smoke 13 / Stability 02 / 冻结

---

## V5.0 — 模拟纸质单 ✅ 已冻结（2026-08-23）

- [x] 人手确认、只落 `data/orders/`
- [x] 探测本机 MT5（demo/live），不发单
- [x] Smoke 14 / Stability 03 / 冻结

---

## V6.0 — 今日台账 ✅ 已冻结（2026-08-23）

- [x] 先 preview 再确认
- [x] `GET /api/v1/desk/today`
- [x] 仍不向 MT5 发单

---

## V7.0 — 本机样本 CSV ✅ 已冻结（2026-08-24）

- [x] `data/samples/eurusd.csv` 作为指标研究数据
- [x] `GET /api/v1/samples`
- [x] Smoke 16 / Stability 05 / 冻结

---

## V8.0 — 因子 / 回测本机样本 ✅ 已冻结（2026-08-24）

- [x] `moutai.csv` / `xauusd.csv`
- [x] `GET /samples` 带 `kind`
- [x] Smoke 17 / Stability 06 / 冻结

---

## 之后（未开始）

- 把 K 线/因子表从本机文件喂给 Worker（需改板上节点，另写设计）
- 向 MT5 发单：已否决，保持纸质单，除非另写设计
