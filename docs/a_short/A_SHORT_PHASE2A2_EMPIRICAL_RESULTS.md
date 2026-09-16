# A_SHORT_PHASE2A2_EMPIRICAL_RESULTS.md

> Phase 2A.2 首轮 empirical D1 结果。**本阶段成功 = 得到未经人工筛选、严格 PIT、可复现、带真实成本与执行约束的 A-Short D1 证据；不是高收益。**
> 数据取证见 [DATA_FORENSIC](A_SHORT_PHASE2A2_DATA_FORENSIC.md)。

---

## Executive Status
```
DATA_BLOCKED
```
原因：注册的 frozen D1 价格面板（`tm-ashare-EQUITY-D1-20260830-000002`）在本 Cloud VM 无法物化——逐股票冻结原始 CSV 缺失；BaoStock 重建被 `AGENTS.md`/`pack.py` 禁止且会破坏 `upstream_hash` lineage。故**无任何 empirical alpha 数字可产出**。**未编造结果。**

> 唯一可产出的是**pack-independent 的成本/账户可行性算术**（Step 11/13 的一部分），已落 artifact；它们**不含 alpha**。

---

## Research（Step 4/6/7/15/16）
```
STATUS: DATA_BLOCKED  (需 frozen panel)
```
20 个预注册主比较（`4 horizons × 5 Top-K`，`m=20`，seed 20260916）**未运行**，因为无价格面板 → 无前向收益、无 Top-K 选择、无 EW/动量基准。
| horizon | Top3 | Top5 | Top10 | Top20 | Top50 |
|---|---|---|---|---|---|
| T+1 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| T+2 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| T+3 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| T+5 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

`MODEL_USED`（一旦物化）= **`20D_MOMENTUM_BASELINE`**（`baseline.py::momentum_scores`）——**不是** full D1 feature family（合同特征族仅 specified，见 [RESEARCH_CONTRACT §4](A_SHORT_D1_RESEARCH_CONTRACT.md)）。

## Validation
```
STATUS: DATA_BLOCKED
```

## OOS
```
LOCKED  (未 unlock；DATA_BLOCKED 下不解锁)
```

## FDR（Step 15）
```
STATUS: DATA_BLOCKED  (m=20 BH q=0.05 待有统计量后执行；无结果不做多重性)
```

## Cost（Step 11）— pack-independent 算术，NO alpha
滑点/侧敏感性（往返 RT%，实算，artifact `PHASE2A2_COST_SENSITIVITY.json`）：
| P=¥20,000 | 0.00% | 0.05% | 0.10% | 0.20% | 0.30% | 0.50% |
|---|---|---|---|---|---|---|
| RT% | 0.102% | 0.202% | 0.302% | 0.502% | 0.702% | 1.102% |

年化摩擦（friction envelope，**假设** 100% 单边换手、242 往返/年、P≥¥20k、0.1%/侧滑点**假设**）：T+1 73% / T+2 37% / T+3 24% / T+5 15%。
> **这是 cost envelope，不是策略实际盈亏；net alpha sign 需 gross（BLOCKED）。**「gross → fees → slippage → net」的 sign flip 分析待面板。

## Execution（Step 8/9/10）
```
entry_block_rate: DATA_BLOCKED
exit_block_rate:  DATA_BLOCKED
carry_rate:       DATA_BLOCKED   (LOW/MODERATE/HIGH 分层待真实数据)
stuck_rate:       DATA_BLOCKED
```
引擎已就绪（Phase 2A.1：fee-aware affordability + capital-path exit-recovery + STUCK flag），但 entry/exit/carry/stuck 诊断需真实面板才有数。

## Account（Step 13）— pack-independent 算术，NO alpha
可执行性（artifact `PHASE2A2_ACCOUNT_GRID.json`，price ¥20 参考）：
| 账户 | Top3 | Top10 |
|---|---|---|
| ¥2k | 不可行 | 不可行 |
| ¥5k | 不可行(2名) | 不可行 |
| ¥10k | 可行(闲置40%) | 不可行(4名) |
| ¥20k | 可行 | 不可行(9名) |
| ¥50k | 可行 | 可行(闲置20%) |
| ¥100k | 可行 | 可行 |
| ¥500k / ¥1m | 可行 | 可行 |
> net return 列 = **DATA_BLOCKED**（需 alpha）。账户规模只改可执行性，不改 alpha score。

---

## Q1–Q7（Step 18）
| Q | 问题 | Answer | Evidence | Status |
|---|------|--------|----------|--------|
| Q1 | Coverage / Opportunity Density | 无面板，无候选密度 | 无 OHLCV | **DATA_BLOCKED** |
| Q2 | Gross Forward Return | 未计算 | — | **DATA_BLOCKED** |
| Q3 | Excess vs EW | 未计算 | — | **DATA_BLOCKED** |
| Q4 | Excess vs Momentum | 未计算（且 baseline 本身=momentum，需另设独立打分才有意义） | — | **DATA_BLOCKED** |
| Q5 | Hit Rate / Dispersion | 未计算 | — | **DATA_BLOCKED** |
| Q6 | Execution Feasibility | 引擎就绪；账户可行性算术已出；真实 entry/exit 待面板 | `PHASE2A2_ACCOUNT_GRID.json` | **DATA_BLOCKED**(实证)/ 部分算术已出 |
| Q7 | Cost / Carry / Net Survival | 成本 envelope 已出；carry/net 待面板 | `PHASE2A2_COST_SENSITIVITY.json` | **DATA_BLOCKED**(net) |

## ML1 independence（Step 17）
```
NOT_COMPUTABLE  (无对齐面板与 ML1 分数环境；不编造 corr)
```

---

## BAD NEWS
1. **首轮 empirical D1 baseline 在本环境跑不了**——frozen 价格面板缺失，且不能用 BaoStock 旁路（会破坏 lineage）。这是环境/数据边界，**不是**执行模型缺陷。
2. **发现并修复一个静默陷阱**：缺失原始面板时 `pack_panel()` 会写出全 NaN pack 并"成功"；旧 runner 只查 `pack_exists()` 会在空数据上跑出假的 n_signal=0 结果。已加 `panel_coverage` 退化守卫 → 现在会明确报 `DEGENERATE_PANEL_NO_PRICES`。
3. **当前打分只有 20 日动量 baseline**；合同特征族（reversal/gap/vol accel/turnover/breadth/limit-up…）仅 specified 未实现。即便面板到位，首轮也只是**动量基准**，不是"独立 alpha"。
4. **滑点 = ASSUMPTION/UNKNOWN**；net sign 对其极敏感。
5. **capital-path 重叠会计仍是已知简化**（Phase 2A.1 遗留）：carry 频繁时 chained net 会低估重叠占用——必须在真实数据上先看 carry_rate 再定是否升级，**不能**在无数据时假装已解决。
6. 因此：**现在没有任何 alpha 证据，没有任何东西接近 Paper。**

## KNOWN LIMITATIONS
- 无 frozen 面板 → 无 empirical alpha（Q1–Q7 全 DATA_BLOCKED）。
- 动量 baseline ≠ 合同特征族；specified ≠ implemented。
- STUCK 按末收盘假设清算（保守，flag）；overlap 会计未实现；滑点未实测。
- 成本/账户 artifact 是**算术可行性**，**无 alpha**，不得当策略结果。

## 下一步（不改合同）
在 :9000 主机物化 frozen 面板后重跑 `run_baseline`；先读 §Execution 的 `carry_rate`/`stuck_rate` 与覆盖率，再看 20 主比较与 FDR。**结果好坏都原样报告**；若值得深挖只登记 `A_SHORT_D1_V2` 候选假设，**不在本阶段改 V1**。
