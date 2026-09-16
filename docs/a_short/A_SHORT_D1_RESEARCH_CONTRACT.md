# A_SHORT_D1_RESEARCH_CONTRACT.md — `A_SHORT_D1_V1`

> 全新、独立、可审计的 A-Short D1 短周期研究合同（§12–§16、§18、§35）。**不改** ML1/V25/V26/V33/V34/V38 或任何冻结物；引用上游冻结价格为 **immutable upstream dependency**，只读不改。
> 机器可读镜像：`research_engine/cn_a_short/__init__.py`。预注册：本文件跑任何经验结果**之前**冻结。

---

## 1. 身份 / 血缘（§13）
| 字段 | 值 |
|------|----|
| contract_id | `A_SHORT_D1_V1` |
| namespace | `research_engine/cn_a_short/`（新，独立于 ML1/V33） |
| upstream_dataset_id | `tm-ashare-EQUITY-D1-20260830-000002`（**只引用**） |
| upstream_hash | `dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80` |
| derived_dataset_id | `tm-ashort-D1BASE-V1` |
| derived_dataset_hash | 首次物化 pack 时由 `run_baseline` 盖章（当前 `null`，数据受限） |

## 2. Universe / Calendar / Boards
- universe：A 股普通股（复用 `A_SHARE_UNIVERSE_HISTORY_V12_2`，PIT 上市/退市已知日）。
- calendar：`tm-cn-a-CALENDAR-20260830-000001`（交易日历，T+1 以此判定，非自然日）。
- boards：`ALL / MAIN / MAIN_CHINEXT`（`board_mask` 复用）。默认 `ALL` 研究，账户层按权限选板（§4 分离）。

## 3. PIT / 决策与执行时点
- **PIT rule**：signal 只用 ≤ 收盘(T) 的信息；特征在 T 收盘后计算。
- **decision time**：T 收盘后（研究）/ 生产对齐 ~08:58 freeze（[执行时序](A_SHORT_PAPER_EXECUTION_TIMELINE.md)）。
- **execution time**：**开盘(T+1)** 成交，不用不存在的同日价；退出 = 开盘(T+1+hold)。
- 结构性无前视：entry index = t+1，earliest exit = t+2（hold≥1）。单元测试 `test_pit_no_same_day_fill` 覆盖。

## 4. Hold / Label（§17 第一批仅数值）
- horizons：**T+1 / T+2 / T+3 / T+5**（hold ∈ {1,2,3,5}），四者并行，不预判优劣。
- label：`open(t+1+hold)/open(t+1) − 1`（open-to-open forward return）= **MEAN_FORWARD_RETURN 空间**，非 CAGR（§21）。
- 第一批特征族**已登记（specified）**，只用可 PIT 数值：short momentum / short reversal / overnight gap / intraday-vs-overnight（若数据允许）/ volume·amount acceleration / turnover anomaly / range position / volatility / market breadth / limit-up state / recent limit-up count。**不含** LLM/News/Policy/Theme/龙虎榜/付费 L2（§17、§29）。
- **specified ≠ implemented（Phase 2A.1 澄清）**：当前**已实现代码 = 仅 20 日动量 baseline**（`baseline.py::momentum_scores`），用于打通评估引擎与做占位基准。**上面这份特征族尚未逐个实现**，Phase 2A **不声称** D1 特征引擎已完成，更**不声称** News/Policy/Theme/LLM 已完成。逐个特征的实现属于后续（须仍在本合同窗口/多重性内）。

## 5. Cost model（§14，新合同独立成本）
- 逐笔按 notional：commission(min ¥5)/transfer/stamp(sell)/slippage(**假设**分档 0–0.5%/侧)。
- 引用 [COST_FEASIBILITY_V2](A_SHORT_COST_FEASIBILITY_V2.md)；代码 `cn_a_short/cost.py`（canonical 常量）。

## 6. Liquidity / Exclusion / Board / ST / Suspension / Limit（执行规则）
- eligibility：listed & tradestatus==1 & 有限 close>0 & 上市≥N 日；可选排除 ST。
- exclusion / fill：`exec_reason` → DELISTED/SUSPENDED/MISSING_OPEN/ZERO_VOLUME/**LIMIT_LOCK**（一字，`|open/preclose−1|≥limit−0.002`）。
- limit 档：主板 10%、创业板/科创 20%（创业板 2020-08-24 起）、北交所 30%、ST 5%（`_limit` 复用）。
- 未成交不建仓、不计成本、现金不变。测试覆盖 limit/suspension。

## 7. 研究窗（§15，先解释依据，不结果倒推；不沿用 ML1 窗）
> ML1 用 RESEARCH 2010–2021-08 / VALIDATION 2021-08–2024-02 / DENIED 2024-03–2026-08。A-Short **另立**，依据 = regime + 制度变化：
| 窗 | 区间 | 依据 |
|----|------|------|
| **Research** | 2014-01-01 … 2021-12-31 | 2014-15 牛/股灾、2016 熔断、2017 蓝筹、2018 熊、2019-20 COVID+科创板、2021 结构市；含 10% 与 2020-08 后 20% 涨跌幅两种制度 |
| **Validation** | 2022-01-01 … 2023-12-31 | 2022 熊 + 2023 弱势 + 2023-04 主板注册制 |
| **OOS（锁）** | 2024-01-01 … 最新 | 2024 微盘股崩 + 国家队时代；**单向解锁**，owner 批准前不读（§16） |
| **Embargo** | 5 交易日 | ≥ 最大 hold，防止跨窗前视泄漏 |

- **禁止** 用 OOS/最后一段做 research（§16）；`run_baseline --unlock-oos` 需显式且一次性。
- seed = `20260916`。

## 8. Multiple-testing policy（§23、§35）
- **预注册比较数** = horizons(4) × Top-K(5: {3,5,10,20,50}) = **20 个主比较**（`N_PLANNED_PRIMARY_COMPARISONS`）。
- Top-K 是**预注册的一组比较**，不是看结果后挑最好看的一个。
- 报告用 **FDR（BH，q=0.05）** 控制多重性；账户规模 × Top-K 组合是 **Execution Feasibility Map**，不计入 alpha 多重性但需登记。
- 任意额外比较（新特征/新窗/新 sign）**须新版本合同并重新计 m**。

## 9. Reproduction policy（§14、§45）
- 一切经验结果由 `python -m research_engine.cn_a_short.run_baseline` 复现；确定性 seed；成本表由 `report_tables.py` 复现。
- 结果落 `data/market/research_engine/cn_a_short/`，带 window/seed/upstream_hash。
- **结果不好不许改本合同**（§34）：只能开 `A_SHORT_D1_V2`。

## 10. 与 V33 的区别（§18，硬）
V33 = 涨停事件 hold5，已 `PREDICTIVE_BUT_NOT_TRADABLE_AT_20K`。本合同 = **新假设族 + 新 feature 定义 + 新 label(open-to-open T+1..T+5) + 新窗 + 新 OOS + 新成本**；可复用**工程骨架**（cost/exec/lot），**不得**宣称「V33 结果就是 A-Short」，且**不重开/不改 V33**（Decision A-003）。新研究须**独立证明增量 alpha**（vs EW、vs momentum baseline、corr vs ML1 < 0.90）。
