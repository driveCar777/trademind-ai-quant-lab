# A_SHORT_PHASE2A_RESULTS.md

> Phase 2A 结果（§41–§43）。**先说坏消息。** 成本/账户/可行性 = 实算已完成；经验 alpha（Q1–Q7）在本环境 **DATA_BLOCKED**，未编造。
> 复现：`report_tables.py`（成本/账户）、`run_baseline.py`（alpha，需 pack）、`pytest`（25 tests）。产物：`data/market/research_engine/cn_a_short/PHASE2A_TABLES.json`。

---

## BAD NEWS（§41，必须主动告诉 owner）
1. **本环境没有 A 股 D1 逐笔价格面板** → 经验 alpha 无法在云端跑：`pack_exists()=False`、`raw/daily_panel_v12_1` 缺失、`live/bars` 为空。只有 calendar/basics/universe/index。**Q1–Q7 今天答不了**，需在 :9000 主机物化 pack 后跑一条命令。这是**能力受限**，我没有用漂亮推荐/LLM 掩盖（§40/§44）。
2. **T+1 成本最危险**：满换 + 0.1% 滑点 → 年化摩擦 73%（P≥¥20k）。小账户（¥2k 每名）往返 0.75%、年化 182%。T+1 需要 baseline 证明**极高且可低换手实现**的毛 alpha 才可能存活。
3. **最不现实的账户规模 = ¥2,000–¥20,000**：落在 ¥5 最低佣金主导的最差成本带（往返 0.4%–2.25%），且凑不满 Top10 等权（¥20k×Top10 只成 9 名、100% 闲置）。缺口是本金不是边。
4. **滑点 = UNKNOWN**（无逐笔成交数据）。所有 net 结论对滑点极敏感（每 0.05%/侧 = 往返 +0.1%）；实测前不得当定论。
5. **过拟合风险预警**：baseline 将并行比较 4 horizon × 5 Top-K = 20 个主假设；若出现异常高结果，默认怀疑 leakage/幸存者/universe bias/重复检验，先加审计再谈 Paper（§36/§37）。
6. **不能拿去 Paper 的东西**：目前**没有任何** A-Short alpha 结果存在，故**没有任何东西可进 Paper**。cost/account 表是可行性边界，不是策略。
7. **specified ≠ implemented（§F）**：已实现 = 评估引擎 + **仅 20 日动量 baseline** 打分；[合同 §4](A_SHORT_D1_RESEARCH_CONTRACT.md) 的完整特征族仅**登记未编码**；News/Policy/Theme/LLM **未实现**。不得把「特征族已列」读成「特征引擎已完成」。
8. **数字纪律（§E）**：文中「T+1 年化摩擦 73%」= **friction envelope**（假设 242 往返/年、100% 单边换手、P≥¥20k、滑点 0.1%/侧**假设**），**不是**策略实际「年化亏损 73%」。滑点 = **ASSUMPTION/UNKNOWN**，非观测事实。

---

## §42 主表（Horizon × Top-K × Account）
> Cost/Turnover/Feasible = **实算已知**；Gross/Net/MaxDD = **PENDING_DATA**（需 pack 跑 baseline）。price=¥20 参考，满换(turnover=100%/期)，含 0.1% 滑点假设。

| Horizon | Top-K | Account | Gross Alpha | Turnover | Cost(往返/年化) | Net Alpha | MaxDD | Feasible |
|---|---|---|---|---|---|---|---|---|
| T+1 | 3 | 20k | PENDING | 100%/期 | 0.419% / 101% | PENDING | PENDING | YES(3名,每名¥6k) |
| T+3 | 3 | 20k | PENDING | 100%/期 | 0.419% / 34% | PENDING | PENDING | YES |
| T+5 | 3 | 20k | PENDING | 100%/期 | 0.419% / 20% | PENDING | PENDING | YES |
| T+1 | 10 | 20k | — | — | — | — | — | **NO**(仅9名,100%闲置) |
| T+1 | 3 | 100k | PENDING | 100%/期 | 0.302% / 73% | PENDING | PENDING | YES(每名¥32k) |
| T+3 | 10 | 100k | PENDING | 100%/期 | 0.377% / 30% | PENDING | PENDING | YES(每名¥8k) |
| T+5 | 10 | 100k | PENDING | 100%/期 | 0.377% / 18% | PENDING | PENDING | YES |
| T+1 | 10 | 1m | PENDING | 100%/期 | 0.302% / 73% | PENDING | PENDING | YES(每名¥98k) |
| T+3 | 10 | 1m | PENDING | 100%/期 | 0.302% / 24% | PENDING | PENDING | YES |
| T+5 | 10 | 1m | PENDING | 100%/期 | 0.302% / 15% | PENDING | PENDING | YES |

（完整 4×5×8 网格见 `PHASE2A_TABLES.json`；低换手情形年化摩擦按比例下降，见 [COST_FEASIBILITY_V2](A_SHORT_COST_FEASIBILITY_V2.md) §4。）

---

## §43 A-SHORT D1 BASELINE STATUS
```
T+1:  PENDING_DATA — 引擎+测试就绪；成本最苛（满换年化73%+，小账户更高）
T+2:  PENDING_DATA — 引擎就绪
T+3:  PENDING_DATA — 引擎就绪；成本中（满换年化24%）
T+5:  PENDING_DATA — 引擎就绪；成本最轻（满换年化15%）——但不预判其最好（§2/§43）

Cost Survival:        已量化边界。每笔 breakeven(满换,+0.1%slip,P≥20k)=每期毛>0.302%；
                      小账户(¥2k)=>0.75%。是否被 alpha 覆盖 = 需数据。
Account Feasibility:  ¥2k–¥20k 最差带、凑不满 Top10；≈¥50万+ 才低成本跑 Top10 等权。已实算。
Top-K Stability:      PENDING_DATA（引擎支持 Top3/5/10/20/50 + threshold + FDR m=20）。
Independent Alpha:    PENDING_DATA（引擎将测 corr vs ML1<0.90、vs EW、vs momentum baseline）。
Next Research Step:   在 :9000 主机 `pack_panel()` 物化冻结面板 → `run_baseline`（research 窗）→
                      读 Q1–Q7 → 若有强项跑 §37 审计套件；若 NO_ALPHA 记 FAILURE 不接 LLM 救。
```

---

## 已完成 vs 待数据
| 维度 | 状态 | 证据 |
|------|------|------|
| Cost（账户×频率×滑点） | ✅ 实算 | `PHASE2A_TABLES.json`；[COST_FEASIBILITY_V2](A_SHORT_COST_FEASIBILITY_V2.md) |
| Account 可执行性 | ✅ 实算 | 同上；[ACCOUNT_FEASIBILITY](A_SHORT_ACCOUNT_FEASIBILITY.md) |
| 新 D1 研究合同 | ✅ | [D1_RESEARCH_CONTRACT](A_SHORT_D1_RESEARCH_CONTRACT.md) + `cn_a_short/__init__.py` |
| Baseline 引擎（T+1..T+5, Top-K, net, turnover, cost） | ✅ 代码+25 tests | `cn_a_short/baseline.py`；`pytest` 全绿 |
| 经验 alpha（Q1–Q7） | ⛔ DATA_BLOCKED | `run_baseline` 输出 `DATA_BLOCKED` + 复现步骤 |
| 执行模型正确性（Phase 2A.1） | ✅ 已复审+修正 | [EXECUTION_FORENSIC](A_SHORT_PHASE2A_EXECUTION_FORENSIC.md)：affordability fee-aware + entry/exit capital-path exit-recovery；32 tests |

## 复现命令 / hashes
```
upstream_dataset_id   = tm-ashare-EQUITY-D1-20260830-000002
upstream_dataset_hash = dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80
derived_dataset_id    = tm-ashort-D1BASE-V1  (derived_hash pending first materialization)
seed                  = 20260916
research window        = 2014-01-01 .. 2021-12-31   validation = 2022-01-01 .. 2023-12-31   OOS(locked) = 2024-01-01 ..

python -m research_engine.cn_a_short.report_tables      # 成本/账户表（已在本环境成功运行）
python -m pytest research_engine/cn_a_short/tests/ -q   # 25 passed
python -m research_engine.cn_a_short.run_baseline       # 本环境 => DATA_BLOCKED（含物化步骤）
```
