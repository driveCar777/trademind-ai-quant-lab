# Research Engine V0.4

冻结日期：2026-08-25。

RESEARCH_ENGINE_V0.4 = FROZEN  
RESEARCH_PROTOCOL_V0.3 = 仍 FROZEN  
RESEARCH_READINESS_V0.2 = 仍 FROZEN  
DATA_QUALIFICATION_V0.1 = 仍 FROZEN  
Data Layer V0.1 = 仍 FROZEN  
V11.7 = 仍 FROZEN  
HYP-0001 = FROZEN（不是交易许可）  
FINAL_OOS_LOCKED = false  
FINAL_OOS_STATE = CANDIDATE_LOCKED_ACCESS_DENIED

## Purpose

把「我想研究一个策略」变成必须先登记、预注册、锁定，再由四台 Xavier 按同一份不可改合同跑 Research 与 Validation。

失败也要留下。改参数必须新 hypothesis / experiment。不能偷看 Final OOS。不能把显著性写成「可以买」。

## Hypothesis Registry

`research_engine/hypothesis.py` + `data/market/research_engine/hypothesis/`。

必须有 H0 / H1。禁止「策略可能赚钱」这类不可证伪陈述。

正式锁定 family 是 `FAM-MOMENTUM-0001`（14:11 preregistration）。`FAM-PERSISTENCE-0001` 只是 `catalog.py` 里的历史草稿名，不是 HYP-0001 身份。HYP-0001-A horizon=1，HYP-0001-B horizon=5。统计合同以锁定 JSON 为准：`continuation_mean vs 0`。

## Pre-registration

每个 hypothesis：`preregistration.json` + `.md`。`preregister_hash` write-once。改任何字段必须新 id。

预注册阈值：`min_condition_n=30`，`min_abs_delta=0.00005`，`max_adjusted_p=0.05`，方向一致，block-bootstrap CI 不跨 0。q=0.05 事先写死。

## Experiment Contract

`tm-exp-YYYYMMDD-HHMMSS-NNN` 绑定 hypothesis / family / dataset sha256 / preregister_hash / window_hash / seed=20260825。运行前后 `experiment_hash` 必须相同。

## Research / Validation / Final OOS

Research 可探索，但每次探索是独立 experiment。  
Validation 只跑已锁定合同，不能调参。  
Final OOS 有候选窗，但 `HoldoutGuard.final_oos_access()` 一律 `FINAL_OOS_ACCESS_DENIED`。这不是把 `FINAL_OOS_LOCKED` 设为 true。

本任务不创建解锁事件。

## Multiple Testing / Degrees of Freedom

`ledgers/multiple_testing.json` 记录 family 下所有 hypothesis / experiment 计数。  
`ledgers/rdf.json`：改 parameter / window / feature / cost / execution / sample / instrument / timeframe / universe 只能新实验，禁止覆盖。

## Statistics

stdlib：mean / median / variance / std / SE / 均值差 / 比例差 / Cohen's d / IID bootstrap 5000 / moving block bootstrap（block=20）5000 / permutation 5000 / Benjamini-Hochberg FDR q=0.05。

Seed 固定 20260825。显著性 ≠ 赚钱。必须同时报 effect size 与 n。

## Null controls

A 随机方向；B 无预测（effect=0）；C 朴素动量 streak=1（不优化）。

## HYP-0001

预测假设，不是交易策略。不用 RSI / MACD / Bollinger / MA / VWAP，不衍生 V11.7 参数。

条件：最近 3 根已关闭 bar 收益同号。目标：horizon 后那根已关闭 bar 的简单收益。分别统计 positive_streak 与 negative_streak。

Universe：16 个 immutable dataset。仅 `DATA_INVALID` 可自动排除。当前无 INVALID，16 份全跑。

## Four-Xavier

| Node | Home | Cross |
|------|------|-------|
| Xavier-01 | GOLD ×4 | EURUSD M15, USDJPY H1 |
| Xavier-02 | EURUSD ×4 | USDJPY M15, USDJPY H4 |
| Xavier-03 | USDJPY ×4 | EURUSD M15, EURUSD H4 |
| Xavier-04 | OIL ×4 | GOLD M15, GOLD H1 |

每 dataset 每 variant 10 次完整 Research+Validation+bootstrap+permutation+block bootstrap。

## Lineage / Failure / Graph

Result → Experiment → Hypothesis → Preregistration → Dataset hash → protocol / feature / code fingerprint。缺一项 `RESULT_INVALID`。

证伪写入 `rejected/`，不可删。

JSON 知识图：USES_DATASET / USES_FEATURE / BELONGS_TO_FAMILY / VALIDATED_BY / FALSIFIED_BY / DERIVED_FROM / REJECTED_BY。

## Known Limitations

- HYP-0001 不是交易系统；SUPPORTED 也不能进模拟盘
- 70/15/15 窗口继承 V0.3 候选协议，不是按收益选的
- Xavier-02/03 为 Python 3.6.8，01/04 为 3.6.9
- IID bootstrap 对收益偏乐观，故同时报 block bootstrap
- 未锁 Final OOS

## Next stage

最小任务：第二份与 HYP-0001 无关的预注册假设（仍不锁 Final OOS，仍不进交易）。

索引：`data/market/research_engine/RESEARCH_ENGINE_INDEX.json`  
完成报告：`data/market/research_engine/RESEARCH_ENGINE_V0.4_COMPLETION.md`
