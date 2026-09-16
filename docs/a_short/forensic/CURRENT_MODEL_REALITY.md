# CURRENT_MODEL_REALITY.md

> 当前模型现实（**只看代码，不看文档**）。审计对象：`cn_a_short/baseline.py`、`run_baseline.py`、`evaluate/top_k_period/momentum_scores`。

---

## 一句话
**当前真正实现的打分 = `20D_MOMENTUM_BASELINE`（`close(t)/close(t-20)-1`）。** 没有技术指标库、没有因子、没有 ML、没有 LLM、没有新闻/政策/资金流/财务进入打分。

---

## Specified（合同/文档登记，但未实现）
- 短线特征族：short reversal、overnight gap、intraday-vs-overnight、volume acceleration、amount acceleration、turnover anomaly、range position、volatility、market breadth、limit-up state、recent limit-up count（`A_SHORT_D1_RESEARCH_CONTRACT.md §4`，标注「specified ≠ implemented」）。
- 信息层（架构文档）：政策/宏观/资金流/龙虎榜/题材/龙头/新闻/财务融合、LLM 决策支持、GUI、通知、scheduler。

## Implemented（代码里真实存在）
| 组件 | 实现？ | 位置 |
|------|:---:|------|
| 打分：20 日动量 | ✅ | `baseline.momentum_scores(pack,t,lookback=20)` |
| Top-K 选择（score desc，tie→低索引） | ✅ | `baseline.top_k_period` |
| 前向标签 open(t+1)→open(t+1+hold)，T+1..T+5 | ✅ | `baseline.forward_label` / `top_k_period` |
| 撮合/执行：T+1、停牌、涨跌停、缺开盘、fee-aware 手数、capital-path exit-recovery、STUCK | ✅ | `top_k_period` + `capital_ref.exec_reason` |
| 成本模型（佣金 min¥5/过户/印花/滑点） | ✅ | `cn_a_short/cost.py`（canonical 复用） |
| EW / 动量基准对比、excess、t、hit rate、strategy net、turnover | ✅ | `baseline.evaluate` / `ew_period` |
| 面板覆盖率守卫（退化→DATA_BLOCKED） | ✅ | `baseline.panel_coverage` + `run_baseline` |
| 账户/可执行性/成本包络算术 | ✅ | `account.py` / `feasibility.py` / `report_tables.py` |
| 多重性登记（m=20, FDR 计划） | ✅（登记，未跑） | 合同 §8 |

## Missing（目标需要、代码里完全没有）
| 组件 | 状态 |
|------|:---:|
| 技术指标（MA/MACD/RSI/KDJ/BOLL…作为特征） | ❌ 无（注：另有独立 `indicator-worker` 计算 RSI，但**不进 A-Short**） |
| 因子挖掘 / 多因子 | ❌ 无 |
| ML 模型（LightGBM 等） | ❌ 无（ML1 有，但 A-Short 未接） |
| LLM 辅助（信息理解/红队/融合） | ❌ 无（fusion desk 有，A-Short 未接） |
| 新闻 / 政策 文本 | ❌ 无（仓库级 forbidden/DRAFT） |
| 资金流（主力/北向/龙虎榜） | ❌ 无（龙虎榜/资金流零代码；北向 gz 缓存存在但 2024-08 停发） |
| 财务 / 业绩预告 融合进打分 | ❌ 无（信息层包存在但 A-Short 未接，且 Cloud 无字节） |
| 板块轮动 / 热点 / 龙头 | ❌ 无 |
| 涨停/连板 事件建模 | ❌ 无（V33 有 limit_up_matrix，但独立冻结，不属 A-Short） |
| 分钟/intraday | ❌ 无（全仓库 `frequency="d"` only） |
| GUI / 通知 / scheduler / :9002 | ❌ 无（文档级） |

---

## 三行总表
```
Specified:   短线特征族 + 政策/宏观/资金/热点/龙头/涨停 + 财务融合 + LLM + GUI + 通知（文档登记）
Implemented: 仅 20D 动量打分 + T+1..T+5 撮合/成本/评估引擎 + 账户/成本算术（离线，需 frozen pack）
Missing:     除 20D 动量外的一切 alpha 来源、全部信息层接入、ML/LLM、GUI/通知/scheduler/:9002
```

## 重要澄清
- 引擎（撮合/成本/评估）**成熟且已测（33 tests）**；但**打分只有动量**——引擎 ≠ alpha。
- 20D 动量 **lookback=20** 是中周期信号，与「T+1~T+5 超短线」意图**方向不符**（持有期支持 T+1..T+5，但信号本身是 20 日动量）。
- 目前**无任何 empirical 结果**（Cloud 无 frozen pack，DATA_BLOCKED）。**不得宣称任何 alpha。**
