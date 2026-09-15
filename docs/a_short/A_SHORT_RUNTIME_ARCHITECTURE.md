# A_SHORT_RUNTIME_ARCHITECTURE.md

> GUI / Research Core / Paper Core / Scheduler / Notification / Data Layer / LLM Layer / Fusion / Ledger 及**进程边界**。
> 硬约束：GUI 不是系统生命（§8）；GUI 可关闭而后台继续（§9）；当前 PAPER ONLY / LONG ONLY / 禁 `order_send`（§10）。

---

## 1. 顶层进程拓扑

```
┌──────────────────────────────────────────────────────────────────────┐
│  Windows 桌面（owner 的机器，唯一运行地）                               │
│                                                                        │
│   ┌───────────────┐        ┌──────────────────────────────────────┐   │
│   │  A-Short GUI  │        │  Windows 任务计划 (Task Scheduler)     │   │
│   │  PySide6 桌面 │        │  ashort_session.bat @ 06:30/07:00/... │   │
│   │  + 托盘 + toast│        │  08:20/08:30.../08:58/09:00 (可配)    │   │
│   └───────┬───────┘        └───────────────┬──────────────────────┘   │
│           │ HTTP(JSON)                      │ curl POST(幂等)          │
│           │ localhost:9002                  │ localhost:9002           │
│           ▼                                 ▼                          │
│   ┌────────────────────────────────────────────────────────────────┐  │
│   │  A-Short Backend Service  (FastAPI, app.ashort_main:app :9002)  │  │
│   │  —— 常驻；GUI 关闭它照跑 ——                                       │  │
│   │                                                                  │  │
│   │  Orchestrator / State Machine (INIT→...→COMPLETE)                │  │
│   │      │                                                           │  │
│   │      ├─ Data Layer  ── BaoStock/东财/Yahoo 增量 → Raw → PIT      │  │
│   │      ├─ Research Core ─ features → quant alpha → candidates      │  │
│   │      ├─ LLM Layer  ──── cursor_cloud / ai-gateway 分析师(角色)   │  │
│   │      ├─ Fusion  ─────── Quant⊕LLM → 排名 → Recommendation(冻结)  │  │
│   │      ├─ Paper Core  ─── Portfolio 构建 → T+1 撮合 → Ledger       │  │
│   │      ├─ Notification ── 09:00 决定「今日有无推荐」→ toast        │  │
│   │      └─ Outcome  ────── T+1/T+3/T+5 结算 → 评估                  │  │
│   │                                                                  │  │
│   │  独占锁 CURRENT.json · 会话账本 ASHORT_SESSIONS.json · 原子写    │  │
│   └───────────────────────────┬──────────────────────────────────┘  │
│                               │ 只读复用（子进程/import）              │
│                               ▼                                        │
│   ┌────────────────────────────────────────────────────────────────┐  │
│   │  既有冻结资产（不可写）：frozen pack / 信息层 / ML1 / V33 / 合同 │  │
│   │  live/ 增量：bars, features(ashort), models(ashort), ledger      │  │
│   └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

**唯一运行地 = owner 的 Windows。** 云端 Cloud Agent 只能写代码/文档，跑不了实盘增量（数据在 `D:` 盘、BaoStock/东财需本地网络、MT5 更是本地终端）。本架构因此按「Windows 常驻服务 + 桌面前端」设计，Linux 云端仅用于开发与离线回测。

---

## 2. 进程边界（三条硬边界）

### 边界 A：GUI ⟷ 后台服务（§8、§9）
- GUI 是 **Operator Console / Visualization Layer**，**不承载**数据采集/调度/LLM/推荐/记账。
- GUI 与后台之间**只有** localhost HTTP(JSON)（沿用现有 `dashboard/*.html` 的 poll-only 契约，零后端改动即可换前端）。
- **GUI 关闭 → 后台服务不受影响**：任务计划继续 `curl` 后台端点，后台继续采集/分析/推荐/记账/发通知。GUI 只是「连上来看」。
- 通知层归属：09:00 toast 由**后台**决定是否该发（有无推荐），发送动作走 GUI 进程的 `QSystemTrayIcon.showMessage()`（若 GUI 未开，退化为 Windows 通知中心/日志，见 Scheduler 文档「错过窗口重放」）。

### 边界 B：Recommendation ⟷ Paper Execution（§15、§16、§42）
- **Alpha 层（Recommendation）** 与 **Portfolio 层（Paper Execution）** 严格分层、分文件、分快照：
  - Recommendation 只依据 alpha/信息，**不看账户资金**；产出 immutable `RECOMMENDATION_{date}.json`。
  - Paper Execution 依据 `capital / lot / 已有持仓 / 相关性 / T+1 / 成本` 决定「可执行组合」，产出 `PAPER_PLAN_{date}.json` + Ledger。
  - **资金规模改变可执行组合，但绝不改 Alpha model**（§16）。改本金 → 不重算 alpha；改 universe → 才可能重算 signal（§53，GUI 须显式标注「该设置改 Alpha / 只改 Portfolio」）。

### 边界 C：研究/回测 ⟷ 前向/纸面（PIT trust boundary）
- 研究/回测读**冻结**窗口，遵守禁用窗锁、不读未来。
- 前向/纸面读 `live/`，`asof < frozen_end` 直接拒绝（沿用 `daily.py::REFUSING_TO_WRITE_STATUS`）。
- **手动刷新不得绕过 PIT**（§24）：GUI 的「立即更新」按钮和自动任务进入**同一** pipeline（§25），只是触发方式不同；PIT 门在 pipeline 内部，与触发者无关。

---

## 3. 各层职责与复用锚点

| 层 | 职责 | 复用锚点 | 新增 |
|----|------|----------|------|
| **Data Layer** | 增量拉取 D1（未来分钟）、Raw 落盘、PIT 归位、freshness/coverage | `ml1_live/panel.py`、`layers.py`、`cn_a_share/pit.py`、`data_sources/registry.py` | 分钟数据；每源 STATUS/latency/fallback |
| **Research Core** | 短周期特征 → 本地 quant alpha → 候选生成（5000→1200→200→50） | `ml_v25/model.py`、`features.py::ranked_row`、`opportunity/score_v2.py`、`ml_v33` 骨架 | 短窗特征、短周期基准、候选漏斗 |
| **LLM Layer** | 新闻/政策/主题/事件**理解**、假设生成、红队；结构化 JSON+证据 | `paper_fusion.py`（角色/schema/`enforce`/`priced_in`）、`cursor_cloud.py`、`ai-gateway` | 多角色编排、证据库、token/$ 账本、红队代码 |
| **Fusion** | Quant⊕LLM → 机会排名 → T+1/T+3/T+5 预测 → **冻结** Recommendation | `v8_fusion/states.py`、`paper_fusion.enforce` | 融合规则、双可信度（Quant/Information）、immutable 快照 |
| **Paper Core** | Portfolio 构建（资金/手数/相关/T+1）→ 撮合 → Ledger → Outcome | `paper_ops.py::derive_account`、`capital_ref.py`、`top_n_book.py::_exit_fill` | 动态持仓数、真 T+1 sellable、contribution/withdrawal |
| **Scheduler** | 定时触发（不加库）+ 幂等 + 恢复 + 09:00 | `hot_fusion_session.bat` + Task Scheduler、`paper_fusion_fill.py` 会话闸 | `ashort_session.bat`、09:00 任务、错过重放 |
| **Notification** | 有推荐才提醒；不塞完整分析 | 无（NEW） | `QSystemTrayIcon.showMessage()` + dedupe/quiet-hours |
| **GUI** | 可视化 + 手动触发 + 设置 | `dashboard/paper.html` 概念 | PySide6 桌面 + 托盘 + 可关窗 |

---

## 4. 状态机（§55）

```
INIT → DATA_REFRESH → DATA_VALIDATE → PIT_VALIDATE → MARKET_ANALYSIS
     → CANDIDATE_GENERATION → LLM_ANALYSIS → FUSION → RECOMMENDATION_FREEZE
     → NOTIFICATION → PAPER_EXECUTION → LEDGER → OUTCOME_TRACKING → COMPLETE
失败态：DATA_FAILED / LLM_PARTIAL / PAPER_FAILED / SYSTEM_FAILED
```
- 每个 `run` 有 `run_id`（沿用 hot desk `job_id = uuid[:10]` 惯例），贯穿日志/通知/账本，便于 Run Audit（§54）。
- **`exit 0 ≠ success`**：完成态必须是 `COMPLETE`；核心数据失败 → `DATA_FAILED` 且 `NO RECOMMENDATION`（§27）；非核心失败 → 降级 `LLM_PARTIAL`/`Quant-only` 且打标 `DEGRADED`（§28）。
- 状态落 `STATUS.json`（增量写，非仅末尾），GUI 首页显示当前态 + 上次结果。

---

## 5. 端口 / 命名（不硬编码，`config/ashort.yaml`）

| 项 | 值（默认，可配） | 依据 |
|----|------------------|------|
| A-Short 后台端口 | `TRADEMIND_ASHORT_PORT=9002` | 避开 9000(Master)/9001(hot)/9100(gateway)；SPEC §29.9「禁占 9000」 |
| app 模块 | `app.ashort_main:app`（仿 `hot_main.py`） | 不碰冻结的 :9000 surface |
| 发单开关 | `TRADEMIND_ASHORT_SEND=0`（默认关，当前阶段永远 0） | 仿 `TRADEMIND_MT5_SEND`/`HOT_GROK_SEND` kill-switch 惯例 |
| 只读开关 | `TRADEMIND_ASHORT_READONLY`（真正实现，不像 `PAPER_READONLY` 仅文档） | 修复审计发现的「文档有代码无」 |

---

## 6. 为什么不违反 AGENTS.md 的「V1.1 禁 Qt/调度库」

AGENTS.md V1.1 禁令（前端禁 Qt/WebSocket、调度禁 Cron/APScheduler）写于 V1.1 极简阶段；此后项目**已实际超越**该阶段（`:9001` hot desk、fusion desk、Task Scheduler 都已落地并写入 SPEC §29）。本架构遵循项目**实际采用**的两条既定模式：
1. **调度**：不加进程内调度库，用 **OS 任务计划 + curl + 幂等端点**（SPEC §29.11a 已认可）。
2. **前端**：桌面 GUI 用 PySide6，但**只读、不发单、独立进程**（与既有 web 前端并存，不改 :9000）。

> 但这**仍是与治理文本的显式张力**，已在 [A_SHORT_GAPS_AND_RISKS.md](A_SHORT_GAPS_AND_RISKS.md) 记为「需一次 Decision/Amendment 批准桌面 GUI + 9002 服务」。实现前需 owner 拍板。
