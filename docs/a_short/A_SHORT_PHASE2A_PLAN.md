# A_SHORT_PHASE2A_PLAN.md

> Phase 2A — Cost Feasibility + Account Feasibility + D1 Short-Horizon Research Contract Design.
> 核心问题：**在真实 A 股成本 / T+1 / 一手100股 / 停牌·涨跌停 / 不同账户规模下，T+1/T+2/T+3/T+5 短周期数字 alpha 是否值得继续投入研究，以及如何建立一个全新、独立、可审计的 A-Short D1 研究合同。**
> 本阶段允许**小规模** research code / calculation / tests（成本、账户可执行性、D1 baseline 数据验证、新合同前置验证），**不做** GUI / LLM / 新闻政策题材 / 完整策略。

---

## 0. 工作顺序（硬）
```
Audit → Cost → Account Feasibility → New Contract → D1 Baseline → Validation → OOS → Report
```
不走 `GUI → LLM → News → 漂亮推荐 → 最后发现没 alpha`。

## 1. 本阶段产物
| 类型 | 交付 |
|------|------|
| 代码（小） | `research_engine/cn_a_short/`（cost/account/feasibility/baseline/report/run + tests） |
| 文档 | 本文件 + COST_FEASIBILITY_V2 + ACCOUNT_FEASIBILITY + D1_RESEARCH_CONTRACT + D1_BASELINE_SPEC + PHASE2A_RESULTS |
| 数据产物 | `data/market/research_engine/cn_a_short/PHASE2A_TABLES.json`（确定性成本/账户表） |

## 2. 复用（不重造第二套数据系统，§17）
- 成本：`cn_a_share_alpha/cost.py`（canonical，不重发明）
- 撮合可执行性：`cn_a_share_strategy_v14_1/capital_ref.py::exec_reason`（停牌/涨跌停/T+1）
- 一手/最低佣金：`cn_a_share_ml_v25/top_n_book.py`（`LOT=100`、`MIN_FEE=5`、`_fee`、`board_mask`）
- 上游冻结价格：`tm-ashare-EQUITY-D1-20260830-000002`（**immutable upstream dependency**，只引用不改）

## 3. 严禁（§27/§33/§34）
不改 ML1/V25/V26/V33/V34/V38、不改冻结 dataset/旧合同/现有 paper ledger/真实交易路径；
不接 GUI/LLM/新闻政策题材；不采购付费数据；**结果不好不许改合同**（换 hold/改成本/删股票/改 universe/改 sign/改 OOS 全禁——要改只能开新版本合同）。

## 4. 关键立场（§2、§11、§36）
- **不预判某个 horizon 最好。** T+1/T+2/T+3/T+5 并行研究，分别给 gross/turnover/cost/min-account/breakeven。
- **成本先验 ≠ alpha 不可能。** 区分 `Cost Envelope`（本阶段可算）与 `Alpha Impossibility`（需数据才能判）。
- **高收益不删。** 若出现异常高结果，不是删掉，而是**加大审计**（leakage/幸存者/universe bias/执行/重复检验/regime）。

## 5. 数据可用性（本环境的硬事实，先说坏消息）
云端 VM **没有** A 股 D1 逐笔 OHLCV 面板（`pack_exists()=False`，`raw/daily_panel_v12_1` 缺失；`live/bars` 为空；只有 calendar/basics/universe/index 基准）。
→ **成本 / 账户 / 可行性表 = 已实算**（不需要面板）。
→ **经验 alpha（Q1–Q7）= DATA_BLOCKED**：`run_baseline.py` 返回 `DATA_BLOCKED` 并给出在 :9000 主机上物化 pack 的复现命令，**绝不编造结果**。详见 [A_SHORT_PHASE2A_RESULTS.md](A_SHORT_PHASE2A_RESULTS.md)。

## 6. 验收（§39）——本阶段达成项
| 项 | 状态 |
|----|------|
| Cost：不同账户×频率×滑点成本 | ✅ 实算（[COST_FEASIBILITY_V2](A_SHORT_COST_FEASIBILITY_V2.md)） |
| Execution：哪些账户可真实执行 | ✅ 实算（[ACCOUNT_FEASIBILITY](A_SHORT_ACCOUNT_FEASIBILITY.md)） |
| Research：新 A-Short D1 合同 | ✅ [D1_RESEARCH_CONTRACT](A_SHORT_D1_RESEARCH_CONTRACT.md) |
| Baseline：T+1/T+2/T+3/T+5 可计算 | ✅ 引擎+测试就绪；经验运行 DATA_BLOCKED（待 pack） |
| Evaluation：Top-K + net + turnover + cost | ✅ 引擎支持并测试 |
| Governance：新合同不碰旧冻结物 | ✅ 新 namespace，零改动冻结物 |

> 结论：Phase 2A 的**成本/账户/合同/引擎**部分完成；**经验 alpha 判定**在本环境数据受限，需在有面板的主机跑一条命令补齐后才能回答 §19 的 Q1–Q7。不进入 Phase 2B（新闻/政策/LLM）直到 baseline 数值结论清楚（§40）。
