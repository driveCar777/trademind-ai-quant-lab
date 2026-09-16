# A_SHORT_D1_BASELINE_SPEC.md

> A-Short D1 baseline 评估引擎规格（§17、§19–§27）。实现：`research_engine/cn_a_short/baseline.py`（+ tests）。
> 目标：回答 **仅靠可 PIT 数值数据，T+1/T+2/T+3/T+5 是否存在成本后、Top-K 明显优于全市场的可重复短周期 alpha。**

---

## 0. Specified ≠ Implemented（Phase 2A.1 澄清，§F）
| 组件 | 状态 |
|------|------|
| 评估引擎（forward label / T+1 fills / exit-recovery / Top-K vs EW / cost） | **IMPLEMENTED**（`baseline.py` + 32 tests） |
| 打分特征 | **仅 20 日动量 baseline 已实现**（`momentum_scores`）；[合同 §4](A_SHORT_D1_RESEARCH_CONTRACT.md) 的特征族仅 **specified**，未逐个编码 |
| News / Policy / Theme / 龙虎榜 / LLM | **未实现，也未 specified 为本阶段** |
> 本阶段**不声称** D1 特征引擎或任何信息层已完成。引擎就绪 ≠ 特征就绪 ≠ alpha 存在。

## 1. 两层分离（§21，硬）
```
PREDICTION LAYER              STRATEGY / CAPITAL LAYER
forward_label(open→open)      next-open fill + T+1 + limit/suspension
rank / prob                   ¥5 min-fee + stamp + slippage
= MEAN_FORWARD_RETURN         = STRATEGY_RETURN (chained non-overlap)
```
永不把 predictive return 叫 CAGR；net 用 STRATEGY_RETURN。函数：`forward_label` / `top_k_period`(net) / `ew_period`(bench) / `evaluate`(聚合)。

**Capital-path 执行（Phase 2A.1，§C=Option 2）**：entry(open t+1) 可执行即建仓；planned exit(open t+1+hold) 不可卖 → 向后 carry 到第一个可卖日（`EXIT_CARRY_MAX=10`），找不到 → `STUCK`（末收盘标记并 flag）。**entry 成交的仓位永不被 exit 失败抹成「未买入」**（区别于 `ROUND_TRIP_EXECUTABILITY`；`n_round_trip_clean` 另列两腿当日都成的子集）。affordability 为 fee-aware（买入现金含 ¥5 最低佣金 ≤ alloc）。详见 [EXECUTION_FORENSIC](A_SHORT_PHASE2A_EXECUTION_FORENSIC.md)。

## 2. 第一批核心问题（§19）
Q1 T+1 有无可重复短周期 alpha？ Q2 T+2？ Q3 T+3？ Q4 T+5？ Q5 成本后还有无？ Q6 是否独立（vs ML1<0.90、vs momentum baseline）？ Q7 Top-K 是否明显优于全市场？

## 3. 评估指标（§20，重 Top-K 不只 IC）
对每 horizon × Top-K ∈ {3,5,10,20,50}，对比 `Top-K vs Eligible-EW vs 指数基准(HS300/ZZ500) vs 简单动量 baseline`：
- mean / median return、excess vs EW、hit rate、tail return
- turnover、cost、**net return**、drawdown
- t 值 + FDR（BH q=0.05，m=20）

`evaluate()` 已输出：`mean_gross_topk / mean_gross_ew / mean_excess_vs_ew / t_excess / hit_rate_gross / strategy_total_net / mean_net_per_period / turnover_one_way_per_period`。

## 4. Signal density / NO TRADE（§22、§27）
- 测 Top3/5/10/20 及 **threshold-based** 选择；观察 opportunity density vs expected return。
- 允许 NO TRADE，但**不默认每天无交易**；必须输出 `Candidate Count / Signal Distribution / Threshold Distribution`，以区分「真没机会」vs「阈值太高」（对齐 [NOTIFICATION_SPEC](A_SHORT_NOTIFICATION_SPEC.md) 的 Opportunity Suppression Audit）。
- 持仓数**不提前固定**（不写死 N=10）；Top-K 是预注册比较组（§23），须处理多重性。

## 5. Opportunity Engine v1（§26）——只做透明排序
第一版**不做**大量手工权重，只 `transparent ranking`：`expected_return / confidence / cost_adjusted_expectancy`。Fusion（Market State + Signal + Stability + Cost Survival）留后续。

## 6. Baseline 审计动作（§36、§37）——高结果 = 加大审计而非删除
若某 horizon×Top-K 出现异常强结果，先跑：`Replication / Stress Cost / Alternative Universe / Alternative Benchmark / Placebo / Permutation / Subperiod / Regime Split / Capacity`，再决定；**不因收益高就删**。

## 7. 允许的结论形态（§38、§43）
`NO_ALPHA` 或 `T1 NO / T2 NO / T3 WEAK / T5 YES` 皆为有效结果；不预判 T+5 最好。

## 8. Track B 并行不阻塞（§30）
分钟数据只做 availability / depth / quality / storage / incremental，不进 Track A 启动路径、不做生产 alpha。

## 9. 运行
```bash
python -m research_engine.cn_a_short.run_baseline          # research 窗，动量 baseline（需 pack）
python -m research_engine.cn_a_short.run_baseline --scores SCORES.npy   # 外部 [T,N] 分数
python -m research_engine.cn_a_short.report_tables         # 成本/账户表（无需 pack）
python -m pytest research_engine/cn_a_short/tests/ -q      # 25 tests
```
本环境 `run_baseline` = `DATA_BLOCKED`（无 pack），引擎+测试已就绪；见 [PHASE2A_RESULTS](A_SHORT_PHASE2A_RESULTS.md)。
