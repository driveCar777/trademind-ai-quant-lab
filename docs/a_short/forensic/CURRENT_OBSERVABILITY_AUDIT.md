# CURRENT_OBSERVABILITY_AUDIT.md

> A-Short forensic/observability 现状审计（**只读，无代码改动**）。回答：现有能力 / 缺失能力 / 推荐最小实现 / 风险点。
> 阶段纪律：Audit First → Design Second → Minimal Implementation Third。本轮 = **Audit + Design（docs only）**，未实现观测代码。

---

## 0. 结论（先说）
`cn_a_short` **已经内建了约 70% 的 Run Manifest 元数据**（`run_baseline._meta`）和**丰富的逐笔生命周期字段**（`baseline.top_k_period`），但这些**大多是内存 dict / 单文件 artifact**，**没有**统一的 `runs/RUN_ID/` 持久化布局、**没有** DATA_SNAPSHOT（股票池构成/质量分布）、**没有**逐日 SIGNALS（含 feature/eligibility/reject reason）、**没有**完整 trade lifecycle 状态机、**没有** attribution（β/size/momentum/selection）、**没有**错误分类系统、**没有**自动 REPORT.md。→ 需要的是一层**薄持久化 + 补齐几个快照/归因/分类**，不是重写。

---

## 1. 已存在能力（可复用）
### 1.1 Run Manifest 雏形 — `run_baseline._meta()`（`research_engine/cn_a_short/run_baseline.py`）
已记录：`contract_id, contract_hash(sha256 of 合同 md), upstream_dataset_id, upstream_hash, derived_dataset_id, derived_dataset_hash(None), code_commit(git HEAD), generated_at_utc, seed, research/validation/oos_window`。
产物：`PHASE2A2_RESULTS.json`（18 键，proto-manifest）、`PHASE2A2_{DIAGNOSTICS,COST_SENSITIVITY,ACCOUNT_GRID}.json`。
**缺**：branch、python/dependency/OS 版本、model_name/model_version、cost_model_version、execution_simulator_version、universe_definition（结构化）、RUN_ID 方案、`runs/RUN_ID/` 目录。

### 1.2 Trade 生命周期字段 — `baseline.top_k_period`
逐笔已记：`symbol, status(FILL/FILL_CARRY_k/STUCK/entry-reason/NO_LOT), entered, gross, planned_exit, actual_exit, forced_hold_days, exit_block_reason, net, net_pct`；
期级已记：`n_pick/n_entry/n_entry_blocked/n_no_lot/n_round_trip_clean/n_exit_carry/n_stuck/forced_hold_days_total/invested/cash_out_incl_fees/mean_gross_topk/median/hit_rate/ret_net`。
执行原因来自 `capital_ref.exec_reason`：`DELISTED/SUSPENDED/MISSING_OPEN/ZERO_VOLUME/LIMIT_LOCK/FILL`。
**缺**：显式状态机（CANDIDATE→SELECTED→ORDER_PLANNED→ENTRY_ATTEMPT→ENTRY_FILLED/FAILED→HOLDING→EXIT_PLANNED→EXIT_FILLED/BLOCKED→CLOSED）、每步 timestamp/price/market_status 的逐步日志、涨停买不到/跌停卖不了/停牌/流动性不足的**单独计数与样本留存**。

### 1.3 数据质量守卫 — `baseline.panel_coverage` + `run_baseline` DATA_BLOCKED
已记：`n_dates/n_symbols/finite_close_rate_overall/…_when_listed/n_symbols_with_any_close/n_days_with_any_close/missing_{open,close,volume,amount,turn}_rate_listed/degenerate`。
**缺**：股票池构成（ST/主板/创业/科创/北交所计数）、质量分布（price/turnover/volatility 的 min/median/max/分位）、eligible vs excluded 明细。

### 1.4 评估指标 — `baseline.evaluate`
已记：`mean_gross_topk/mean_gross_ew/mean_excess_vs_ew/t_excess/hit_rate_gross/strategy_total_net/n_chain/mean_net_per_period/turnover_one_way_per_period`。
**缺**：attribution 拆解（β/sector/size/momentum/selection/cost）、best/worst 10 trades、benchmark 明确对齐。

### 1.5 仓库既有可复用基础设施（非 cn_a_short，但模式可借）
| 资产 | 位置 | 可复用为 |
|------|------|----------|
| `CONTRACT.json / REPRODUCTION.json / RESULTS.json / FDR.json / DECISION.json` | `data/market/research_engine/cn_a_share_ml_v25/` | Run Manifest / Reproduction / Metrics 约定 |
| `runs/CURRENT.json` 独占锁 + run 日志 | `master/api/app/service/paper_ops.py`（`RUNS/LOCK`） | `runs/RUN_ID/` 目录 + 并发锁模式 |
| `STATUS.json` | `ml1_live` `live/STATUS.json` | run 状态快照 |
| `SIGNAL_/SHORTLIST_/LEDGER_*` | `ml1_live/{shortlist,ledger}.py` | 逐日 signals / 账本落盘格式参考 |
| `report_tables.py` 确定性 JSON | `cn_a_short` | METRICS/artifact 确定性写盘 |

## 2. 缺失能力（本阶段目标）
| # | 能力 | 现状 |
|---|------|------|
| A | 统一 `results/runs/RUN_ID/` 布局 + RUN_ID 方案 | **缺** |
| B | 完整 RUN_MANIFEST（+branch/py/deps/OS/model/cost/exec 版本） | **部分**（_meta 有一半） |
| C | DATA_SNAPSHOT（股票池构成 + 质量分布） | **缺** |
| D | SIGNALS.json（逐日 rank + feature values + eligibility/reject reason） | **缺**（仅内存 names） |
| E | Trade lifecycle 状态机 + 逐步日志 + 阻塞样本 | **部分**（有终态字段，无过程状态机） |
| F | Performance attribution（β/size/momentum/selection/cost + best/worst 10） | **缺** |
| G | 错误分类系统（DATA/MODEL/EXECUTION/COST/ENV_ERROR） | **缺** |
| H | 自动 REPORT.md（11 节，含"为什么不赚钱"） | **缺** |
| I | 观测层测试（manifest 确定性/hash 失配/快照复现/生命周期完整/缺数据/未来泄漏/负现金） | **部分**（已有 33 业务测试，无观测层测试） |

## 3. 推荐最小实现方案（Phase 3，本轮不写）
> 目标：**薄持久化层**，把已有的内存 dict 落到 `runs/RUN_ID/`，并补 4 个新快照/归因/分类。不改 alpha/合同/universe/参数。

1. **新增 `cn_a_short/forensic/` 子模块**（不碰 baseline 逻辑）：
   - `run_manifest.py`：`new_run_id(exp)`、`build_manifest()`（扩展 `_meta` + branch/py/deps/OS/model/cost/exec 版本）、`write_run(run_dir, {...})`。
   - `snapshots.py`：`data_snapshot(pack, elig)`（复用 `panel_coverage` + 加 board/ST 计数 + price/turnover/vol 分位）、`signal_snapshot(pack, scores_t, elig_t, t, k)`（rank+feature+eligibility/reject reason）。
   - `lifecycle.py`：把 `top_k_period` 的 per-name 结果**映射**成状态机事件（不改 top_k_period；在其输出上派生 CANDIDATE→…→CLOSED）。
   - `attribution.py`：基础版（benchmark/excess/topk contribution/best-worst 10；size/momentum 暴露用已有字段近似）。
   - `errors.py`：错误分类枚举 + `classify(exc/context)`。
   - `report.py`：从 `runs/RUN_ID/*` 生成 `REPORT.md`（11 节）。
2. **`run_baseline` 只加一处调用**：run 开始建 RUN_ID + 目录 + manifest；run 中/后写 DATA_SNAPSHOT/SIGNALS/TRADES/LEDGER/METRICS/ERRORS/REPORT。**默认可开关**（`--no-forensic`），异常只记录不打断。
3. **落盘位置**：`data/market/research_engine/cn_a_short/runs/RUN_ID/`（gitignore 大件，只留小 manifest/report；见风险 §4）。
4. **测试**：新增 `tests/test_forensic.py`（manifest 确定性去除时间戳后一致、hash 失配检测、signal snapshot 复现、lifecycle 完整性、缺数据/未来泄漏/负现金断言）。

**估计改动面**：新增 `forensic/` 6 文件 + `run_baseline` 少量接线 + 1 个测试文件；**不改** `baseline.py` 计算逻辑、不改合同/参数/universe。

## 4. 风险点
1. **产物膨胀/入 git**：逐日 SIGNALS/TRADES 可能大。→ `runs/RUN_ID/` 大件走 gitignore，只提交小 manifest/REPORT（沿用 `DATA_STORAGE_POLICY.md`）。
2. **时间戳/commit churn**：manifest 带 `generated_at_utc`/`code_commit` → 复现测试须对"去时间戳后的规范化 manifest"做 hash（否则永远不 deterministic）。
3. **无数据仍 DATA_BLOCKED**：Cloud 无冻结面板 → 观测层只能在合成 pack + DATA_BLOCKED 路径上测；真实 SIGNALS/TRADES 快照需数据到位（不阻塞设计与合成测试）。
4. **不得偷改语义**：lifecycle/attribution 只能**在 `top_k_period` 输出上派生**，不得改撮合/成本/选股逻辑（否则违反 scope freeze）。
5. **attribution 归因近似**：无真实市值/行业数据接入 A-Short → size/sector 归因只能用现有字段近似并**显式标注**为近似，不得当精确归因。
6. **观测层不是 alpha**：forensic 只解释结果，**不改变**结果；严禁借观测层引入任何新特征/过滤/LLM。

## 5. 验收（Phase 完成后，任一 RUN_ID 可回答）
用什么代码（commit）/什么数据（dataset+hash）/股票池是什么（DATA_SNAPSHOT）/为什么买（SIGNALS：rank+feature+eligibility）/何时买（lifecycle timestamps）/为什么卖（exit_block_reason/actual_exit）/成本多少（METRICS/cost）/收益来自哪里（attribution）/失败原因（ERRORS + REPORT §Failure）/能否复现（REPRODUCTION command + normalized manifest hash）。

---
> 设计细节见同目录：`A_SHORT_OBSERVABILITY_DESIGN.md`、`A_SHORT_RUN_MANIFEST_SPEC.md`、`A_SHORT_TRADE_FORENSIC_SPEC.md`、`A_SHORT_FAILURE_DIAGNOSIS.md`、`A_SHORT_EXPERIMENT_REPORT_SPEC.md`。
> **本轮到此为止（Audit + Design）。Minimal Implementation（Phase 3）待确认后进行。**
