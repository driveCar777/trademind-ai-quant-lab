# CURRENT_IMPLEMENTATION_STATUS.md

> 当前实现状态（**只写代码里真实存在的**，不用未来规划代替）。坏消息优先。

---

## BAD NEWS FIRST
A-Short 真正落地的只有「**离线短周期引擎 + 20D 动量占位打分**」。目标里的短线信息能力（热点/龙头/涨停/龙虎榜/资金流/新闻/政策/宏观/LLM/GUI/通知/纸面 UI）**全部未实现**，且 empirical 被数据不可用硬阻塞。**未证明任何 alpha。**

---

## Implemented（代码真实存在，Cloud 可测）
| 项 | 证据 |
|----|------|
| cn_a_short baseline engine（T+1..T+5、Top-K、撮合、评估） | `research_engine/cn_a_short/baseline.py` |
| PIT framework（signal≤收盘T、fill=open t+1、`listed_cum` PIT、退化守卫） | `baseline.py::forward_label/top_k_period/panel_coverage` |
| cost engine（佣金 min¥5/过户/印花/滑点，逐笔） | `cn_a_short/cost.py`（复用 `cn_a_share_alpha/cost.py`） |
| account feasibility（fee-aware、最小资金、无负现金） | `cn_a_short/account.py` |
| paper execution skeleton（离线撮合：T+1/停牌/涨跌停/carry/STUCK/fee-aware 手数） | `baseline.top_k_period` + `capital_ref.exec_reason` |
| feasibility / report（成本×换手包络、成本/账户表，无需 pack） | `cn_a_short/feasibility.py`、`report_tables.py` |
| empirical CLI + lineage/artifacts + DATA_BLOCKED 守卫 | `cn_a_short/run_baseline.py` |
| tests（业务不变量，非"跑通"） | `cn_a_short/tests/`（**33 passed**） |

## Partial（存在但未接入 A-Short，或 Cloud 无字节）
| 项 | 状态 | 证据 |
|----|------|------|
| data pipeline（D1 采集/pack/PIT 地基） | 代码有，**冻结字节 Cloud 缺** | `cn_a_share/`、`cn_a_share_alpha/pack.py`（DATA_BLOCKED） |
| existing research infra（信息层：融资/户数/财务/行业/指数/预告/增减持/质押/分红/宏观） | 下载+编译代码有，**未接 A-Short**，Cloud manifest-only | `cn_a_share_*_v16..v38`、`cn_a_share_margin_v23` 等 |
| ML1/ML7 live 管线、paper_ops、paper_fusion+cursor_cloud（LLM 传输）、ai-gateway | 成熟，**A-Short 未复用/未接** | `ml1_live/`、`master/api/service/*`、`ai-gateway/` |
| 技术面 | 仅 20D 动量；`indicator-worker`（RSI 等）存在但不进 A-Short | `indicator-worker/` |

## Missing（目标需要，代码完全没有）
- 热点发现 · 龙头识别 · 涨停/连板分析 · 板块轮动
- 龙虎榜 · 个股资金流 · 新闻 · 政策 · 宏观（接入 A-Short）
- LLM fusion（A-Short）
- GUI · Windows notification · scheduler · paper portfolio UI · `:9002` 后端 · live 账户
- 短线数值特征族（reversal/gap/量能/换手/波动/breadth/涨停计数——仅 specified）
- 分钟/intraday 数据

---

## 一句话
**引擎成熟且已测，但只有 20D 动量一个占位信号；其余目标能力"未接入"或"完全缺失"，empirical 因数据不可用未跑。** 详见 `REQUIREMENT_GAP_MATRIX.md` / `CURRENT_MODEL_REALITY.md` / `DATA_HANDOFF_STATUS.md`。
