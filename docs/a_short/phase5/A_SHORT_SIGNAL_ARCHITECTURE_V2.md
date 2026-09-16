# A_SHORT_SIGNAL_ARCHITECTURE_V2.md

> 未来信号管线设计（V2）。**只设计，不实现。** 5 层 + Prediction/Recommendation/Execution/Ledger/Outcome 边界（沿用 Phase 1.1 三层纪律）。

---

## 分层总览
```
Layer 0  Market Regime        市场状态（决定"今天该不该出手 / 出手强度"）
Layer 1  Theme Intelligence   题材/信息智能（政策/行业周期/资金集中/公告/新闻）
Layer 2  Stock Selection      选股（动量/相对强度/量能/换手/涨停行为/突破/龙头分）
Layer 3  Risk Filtering       风险过滤（ST/流动性/异常波动/财务风险/估值）
Layer 4  Execution Simulation 执行模拟（T+1/涨跌停/停牌/成本/撮合/账本）
```
- 每层输出**结构化 + 可解释 + 带 PIT 时点**；每层可独立开关（消融），forensic 记录逐层贡献。
- **Layer 0/1 决定 Recommendation 强度，Layer 4 决定 Executability**；资金规模只改 Layer 4，不改 Layer 0–2 的分数（Phase 1.1 §4）。

## Layer 0 — Market Regime
输入：CSI300 趋势、指数波动率、市场流动性（成交额/换手）、RMB 汇率、美股、商品。
输出：`regime_state`（RISK_ON/RISK_OFF/NEUTRAL）+ `exposure_scalar`（0–1，允许 NO-TRADE 日但不默认无交易）。
用途：机会抑制审计（TRUE_NO_EDGE vs SYSTEM_TOO_STRICT）；regime split 评估（避免小盘牛冒充 alpha）。
数据现状：指数日线可用；汇率/海外/商品 immutable 有但未接；**先用可得的指数+汇率做最小 regime**。

## Layer 1 — Theme Intelligence
输入：政策方向、行业周期、新闻频率、公告、资金集中度（北向行业/资金流/龙虎榜）。
输出：`theme_scores`（板块热度/轮动）+ `theme_evidence`（带来源时点）。
**关键纪律**：新闻/政策为**信息层**，历史回测须先建 timestamped PIT 语料；否则只进实时 shadow（Layer 1 的 LLM 部分 = Phase D）。
数据现状：龙虎榜/资金流/新闻政策**无代码**（需新采集，禁采购）；行业 PIT 有代码未接。

## Layer 2 — Stock Selection
输入：D1（+ 可选分钟）价格/量。
候选因子族（**仅登记，见 FEATURE_REGISTRY**）：动量、相对强度、量能扩张、换手异常、涨停/连板行为、突破、龙头分（板块内相对强度）。
输出：`selection_scores`（截面）+ rank。
现状：唯一实现 = 20D 动量（baseline/CONTROL）。

## Layer 3 — Risk Filtering
输入：ST 标记、流动性（ADV/成交额）、异常波动、财务风险、估值。
输出：`eligibility_mask` + `risk_flags`（**作为报告叠加/可执行子宇宙，不是偷改 baseline universe**）。
现状：当前 baseline 仅 listed/tradestatus/finite-close/min_hist；ADV/价格/市值/财务门**故意未加**（垃圾股效应靠 forensic 暴露，见 README Q4）。V2 可预注册"可执行子宇宙"为新合同。

## Layer 4 — Execution Simulation（已实现）
`baseline.top_k_period`：T+1、涨跌停(LIMIT_LOCK)、停牌(SUSPENDED)、缺开盘、fee-aware 手数、capital-path exit-recovery（carry/STUCK）、canonical cost。**这一层已成熟且测试覆盖**（33+9 tests）。

---

## Prediction / Recommendation / Execution / Ledger / Outcome（边界）
```
PREDICTION    每票前向收益/概率/rank（数学事实；Layer 2 输出；不看钱、不分级）
   ↓
RECOMMENDATION 分级（A/B/S）= Layer0×Layer1×Layer2 融合 + 双可信度；immutable 快照；不看账户
   ↓
PAPER EXECUTION Layer 4：看 capital/lot/T+1/涨跌停/流动性/可执行性 → 纸面成交（09:30 开盘）
   ↓
LEDGER        cash_out_incl_fees / 持仓 / 无负现金；forensic LEDGER.json
   ↓
OUTCOME       T+1/T+2/T+3/T+5 predicted vs paper-executable；forensic 归因/失败分类
```
- Recommendation Timestamp（≈08:58 freeze）≠ Execution Timestamp（09:30 开盘）；不用不存在的 09:00 价（Phase 1.1）。
- 每次实验产出 `runs/RUN_ID/`（Phase 3 forensic 已实现）；失败归类 DATA/MODEL/EXECUTION/COST/ENV。

## 消融与独立性
- 逐层开关做消融，测每层增量；Layer 2 因子须打过 EW-eligible + size-bucket EW + 20D 动量三基准（README Q5）。
- corr vs ML1 < 0.90 才算独立（沿用治理）。

## 现状 vs 目标（一句话）
Layer 4 完成、Layer 2 只有动量占位、Layer 0/1/3 = 设计；且被 D1 数据阻塞。V2 按 ROADMAP 分阶段逐层落地，每层新合同、不改冻结物。
