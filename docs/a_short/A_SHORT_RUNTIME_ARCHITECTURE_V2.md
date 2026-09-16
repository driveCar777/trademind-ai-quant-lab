# A_SHORT_RUNTIME_ARCHITECTURE_V2.md

> Runtime v2（Phase 1.1）。在 v1 基础上修正：**Prediction/Recommendation/Execution 三层边界**、**通知与 GUI 解耦**、**GUI 生命周期**、**执行时序**。
> v1（`A_SHORT_RUNTIME_ARCHITECTURE.md`）的进程拓扑与状态机仍有效；本文覆盖其中被修订的部分。

---

## 1. 三层边界（§2、§3、§4）——硬区分，不混算

```
        ┌──────────────────────────────────────────────┐
        │ 1) PREDICTION  (Quant, 数学事实)               │
        │    P(T+1>+5%)=0.61 · 期望收益 · 概率 · 置信     │
        │    不看账户, 不分级, 不下单                      │
        └───────────────────────┬──────────────────────┘
                                ▼
        ┌──────────────────────────────────────────────┐
        │ 2) RECOMMENDATION  (Alpha/Information 层)       │
        │    A/B/S 分级 · Quant⊕Info 融合 · 双可信度      │
        │    immutable RECOMMENDATION_{date}.json         │
        │    不看账户资金 (§3)                             │
        └───────────────────────┬──────────────────────┘
                                ▼
        ┌──────────────────────────────────────────────┐
        │ 3) PAPER EXECUTION  (Portfolio/Execution 层)   │
        │    看: capital/max_capital/cash/lot/T+1/        │
        │        holdings/correlation/liquidity/涨跌停/    │
        │        execution feasibility                    │
        │    BUY 100 @ 09:30 open → Ledger                │
        └───────────────────────┬──────────────────────┘
                                ▼
                    Ledger → Outcome (predicted vs paper)
```

**三条不变量**：
1. Prediction 是数学事实（Quant），**不分级、不看钱、不下单**。
2. Recommendation 是 Alpha/信息层，**不看账户资金**（§3、§4）；immutable。
3. Paper Execution 是 Portfolio 层，看钱/手数/T+1/可执行；**资金变化只改可执行组合，绝不改 Prediction/Recommendation 的 alpha**（§4）。

例：¥2,000 账户、推荐价 ¥100 → 一手 ¥10,000 买不起 → `Alpha=YES, Executable=NO`，**不改 alpha score**（§4）。

三层落在 [A_SHORT_DATA_FLOW_V2.md](A_SHORT_DATA_FLOW_V2.md) 与 [A_SHORT_PAPER_LEDGER_SPEC.md](A_SHORT_PAPER_LEDGER_SPEC.md) 同步。

---

## 2. 进程边界（v2 修订：通知解耦）

```
┌ GUI (PySide6, 独立进程) ─ 只读+控制台, 关闭不停后台 (Decision A-002)
│    ↑ 只读通知历史 NOTIFICATIONS.json
│    │ HTTP :9002
▼    │
┌ A-Short Backend (:9002, 常驻) ──────────────────────────┐
│   Orchestrator/StateMachine                              │
│   Data / Research / LLM / Fusion / Paper / Outcome       │
│   Notification Service ── Windows Toast (无需 GUI)  ◀── Decision A-004
│   独占锁 CURRENT.json · run_id · ASHORT_SESSIONS.json    │
└──────────────────────────────────────────────────────────┘
     ▲ curl POST (幂等)
Windows 任务计划 (phase tasks + notify @用户会话)
```
- **通知发送归后台 Notification Service**，不再依赖 `QSystemTrayIcon`（§5、Decision A-004、[通知文档](A_SHORT_NOTIFICATION_SPEC.md)）。
- GUI 三种生命周期 `OPEN / CLOSE / MINIMIZE-TRAY`（§6），**均不影响** Backend/Scheduler/Paper/Notification。

---

## 3. 执行时序（v2 新增，§1、§8）

```
~08:58 Recommendation Freeze   (Recommendation Timestamp)
 09:00 Windows Notification     (后台直发)
 09:25 Pre-open status          (读竞价/停牌/涨跌停 → 可执行性)
 09:30 Paper Execution          (T 日开盘价成交, Execution Timestamp)
```
**Recommendation Timestamp ≠ Execution Timestamp**；不得用不存在的 09:00 成交价（详见 [执行时序文档](A_SHORT_PAPER_EXECUTION_TIMELINE.md)）。

---

## 4. 每日 Runtime Timeline（v2，§8）

设计起点（最终由数据/API latency、重试预算、任务计划精度、A 股时段决定，全部落 `config/ashort.yaml`，不写死）：

```
06:30        overnight global / macro refresh
07:00–08:15  news / policy / announcements incremental
08:15–08:25  market-state preparation
08:25–08:35  theme / leader / capital update
08:35–08:45  local candidate generation
08:40–08:52  LLM intelligence
08:50–08:55  red-team review
08:55–08:58  fusion
~08:58       RECOMMENDATION_FREEZE
09:00        WINDOWS_NOTIFICATION
09:25        PRE_OPEN_STATUS
09:30        PAPER_EXECUTION
```
**硬约束**：推荐不得在凌晨很早冻结后一直等（§8）；冻结尽量贴近 08:58；各阶段增量、缺数据降级不阻塞（`DEGRADED`）。

---

## 5. 状态机（对齐三层 + 执行时序）

```
INIT → DATA_REFRESH → DATA_VALIDATE → PIT_VALIDATE → MARKET_ANALYSIS
     → CANDIDATE_GENERATION → LLM_ANALYSIS → RED_TEAM → FUSION
     → PREDICTION → RECOMMENDATION_FREEZE → NOTIFICATION
     → PRE_OPEN → PAPER_EXECUTION → LEDGER → OUTCOME_TRACKING → COMPLETE
失败态: DATA_FAILED / LLM_PARTIAL / PIPELINE_FAILED / PAPER_FAILED / SYSTEM_FAILED
```
- `exit 0 ≠ success`；失败态不得伪装成 `NO_EDGE`（§18）。
- 每 run 一个 `run_id`，贯穿 prediction→recommendation→notification→execution→ledger→outcome。

---

## 6. 与治理裁决的绑定

- GUI = Decision A-002（独立进程/只读/不发单/关闭不停后台）。
- 通知 = Decision A-004（后台直发，GUI 只读历史）。
- LLM 参与 Prediction 输入与 Recommendation 融合的**决策支持**，但**无交易权**（Decision A-001）；Paper Execution 由 Local/Portfolio Engine 控制。
- 短周期研究（涨停/龙头/主题）= Decision A-003（新合同，禁重开 V33）。
