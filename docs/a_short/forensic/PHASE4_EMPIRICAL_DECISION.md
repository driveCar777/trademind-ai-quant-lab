# PHASE4_EMPIRICAL_DECISION.md

> Phase 4 Decision Report。**empirical 运行未发生（DATA_BLOCKED）**——本报告如实记录无法评估的项，不编造结果、不寻找替代方案。
> 前置：`PHASE4_DATA_AUDIT.md`（DATA: BLOCKED）。

---

## 前置状态
- 冻结 D1 面板字节在 Cloud 不可用（`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`）。
- 因此 Step 2（materialization）/ Step 3（baseline run）/ Step 4（runs 结果）**均未执行**。
- 无 IC / RankIC / 胜率 / 收益分布 / attribution 的真实数字。

## REPORT 必答项（当前只能答 DATA_BLOCKED）
| 问题 | 回答 | 依据 |
|------|------|------|
| 1. 有无预测能力（IC/RankIC/胜率/收益分布） | **DATA_BLOCKED**（未计算） | 无价格面板 → 无前向收益 |
| 2. 收益来自哪里（beta/momentum/size/selection） | **DATA_BLOCKED / UNKNOWN**（size/selection 即便有数据也 UNKNOWN，无市值/因子模型） | attribution 只能 APPROX，且需数据 |
| 3. 亏损原因分类（ALPHA/DATA/EXECUTION/COST/STYLE） | **DATA_FAILURE**（唯一有证据的类：数据缺失，非模型/执行/成本；不是"模型不好"） | Step 1 审计 |
| 4. 垃圾股问题（小盘/低价/高波动/流动性） | **机制已知，实测 DATA_BLOCKED** | 见下 |

### 4. 垃圾股问题（机制分析，非修改）
当前 universe = 全 A 股（含 ST/微盘/低价/科创/创业/北交所）+ 20D 动量 + **无价格/成交额/换手/市值/财务过滤**（`CURRENT_UNIVERSE_REPORT.md` 代码核实）。机制上 Top-K 天然富集 **小盘 / 低价 / 高波动 / 流动性陷阱**。这是 `BASELINE_DESIGN_CHARACTERISTIC`，**不修改 universe**；一旦数据到位，forensic 的 DATA_SNAPSHOT（board/ST/价格·成交额分位）+ attribution（market_beta vs excess）将量化"收益里有多少是小盘 β"。当前无法给出实测占比 → DATA_BLOCKED。

## 决策
| # | 问题 | 结论 |
|---|------|------|
| 1 | 20D momentum baseline 有无历史有效性？ | **UNKNOWN（DATA_BLOCKED）**——从未在真实数据上运行；不得声称有效或无效 |
| 2 | 是否值得继续作为 baseline？ | **是（作为占位基准保留）**——它是可复现、可解释、已被 forensic 层观测的对照系，但**不是策略**；在有 empirical 之前不升级、不替换 |
| 3 | 主要风险 | 排序：**① 数据问题（当前总阻塞）② universe/β 错觉（结构性）③ 成本（小账户/高换手）④ alpha 不足（待验证）** |
| 4 | 是否允许进入 `A_SHORT_D1_V2`？ | **否（不要进入）**——在 20D 动量 baseline 拿到第一份 empirical 证据之前，开 V2 = 在未验证的地基上叠复杂度。仅**建议**：先解冻数据 → 跑 baseline → 读 forensic REPORT → 再议 V2 |

## 唯一前置（owner 决策）
解冻数据（保 `dataset_id`+`hash` 不变上传，或授权注册新数据集+合同修订）。见 `DATA_STORAGE_POLICY.md` / `A_SHORT_CLOUD_FINAL_AUDIT.md` G0。**本阶段不采购、不换源、不改 hash、不进 V2。**

## STOP
`DATA_BLOCKED` → STOP。不追求收益、不优化、不加聪明东西。等数据到位后，用现有 `run_baseline --forensic` 即产出第一份可信 empirical evidence（含 IC/attribution/垃圾股占比/亏损归类）。
