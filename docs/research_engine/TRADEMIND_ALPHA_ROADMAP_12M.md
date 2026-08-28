# TradeMind Alpha Roadmap — 12 Months

Design only. 2026-08-26.  
Parents: Coverage Map V1, Data Capability V1, Priority Ranking V1.  
Does not unlock Final OOS. Does not authorize MT5. Does not modify frozen experiments.

Capital ladder (ambition, not this quarter's gate):

| 层 | 目标 | 现在 |
| --- | --- | --- |
| 基础 | 年化 ≥10% 成本后 | 无 Candidate，问不了 |
| 中风险 | 15%–30% | 禁止用无边策略假装 |
| 高风险 | 30%+ | 仅当有边且另开高风险家族 |

成功不按「写了几个 V0.x」计。按 Coverage Map 的 Level 0–5。

---

## Executive Summary

未来 12 个月只做一件事的序列，不是并行实验室。

```text
第一阶段（月 1–3）  低成本、高可检验：V0.9 转换 → 只读结论
第二阶段（月 4–8）  中风险：加长数据 或 极窄日历；禁止无边就上 ML
第三阶段（月 9–12） 高风险探索仅当数据门打开；默认仍禁止 Paper/MT5
```

若第一阶段再得到 `NO_CANDIDATE`，合法进度是 **把 UNKNOWN 标成 FAILED**，然后补数据或停。  
非法进度是改门槛、扩假设、或在 1 个月 M15 上宣布 30%。

---

## Current Evidence

| Level | 定义 | 状态 |
| --- | --- | --- |
| 0 | Research Engine 稳定 | **DONE** |
| 1 | Candidate（成本后 + 多数据集 + FDR） | **未到** |
| 2 | Strategy Candidate（CAGR/DD/Sharpe 可解释） | 未到 |
| 3 | Portfolio（多个不全相关边） | 未到 |
| 4 | Paper | 禁止跳级 |
| 5 | MT5 | 禁止跳级 |

V0.7.1 队列的 Cross Asset 段已执行并失败。本路线从「转换」重排，不重跑 V0.8。

---

## 阶段一 — 低成本、高概率（月 1–3）

「高概率」= 实验能 **诚实结束**，不是「高概率赚钱」。

| 序 | 模块 | 产出 | 杀停 |
| --- | --- | --- | --- |
| 1.0 | 本 V1 地图 / 打分 / 路线 / 合同模板 | 本目录一组 md | — |
| 1.1 | **Regime Transition V0.9 合同** | 恰好 3 条；hash 锁死 | 禁止第 4 条 |
| 1.2 | V0.9 实现 + 四 Xavier（需另批跑数） | ranking + freeze | 见结果改门 = 违规 |
| 1.3 | 只读结论 | CANDIDATE / WEAK / NO_CANDIDATE | 失败必须保留 |

并行禁止：ML、组合、再开跨品种、M15 主证、MT5。

**被动 D1 基准（诊断，不是假设）：** 同窗、同成本、无条件做多 GOLD / OIL。只回答路径收益。禁止升级为 Candidate。

阶段一成功：出现 Level 1 **或** 转换类被干净证伪。两种都是进度。

---

## 阶段二 — 中风险探索（月 4–8）

只在 1.3 有结论之后打开 **其中一个**（一次一个）：

| 若 V0.9 是… | 下一刀 | 不要做 |
| --- | --- | --- |
| CANDIDATE | Risk 4A 挂在该袖套上；再谈第二个低相关边 | 立刻组合四条品种 |
| WEAK_EDGE | 记录；不调参凑第二命中；转 Data V0.2 或极窄日历 | 扩 hold/ADX |
| NO_CANDIDATE | **Data V0.2 加长** 或 **D1 日历极少条** 或停 | 扩 RT 到 10 条；回头调 XA |

中风险研究（仍要合同）：

- 已实现波动时机 — 仅当 V0.9 **没有** 把 `VOL_SHOCK` 测完；否则算重复  
- ML state model — 仅当特征名单预注册、m 很小、且最好已有一个非 ML 袖套。禁止「让模型自己找 100 个指标」  
- 跨品种残差新家族 — 机制必须 ≠ V0.8 次日美元代理

中风险 **不是** 15%–30% 的许可。那是资本层，不是搜索层。

---

## 阶段三 — 高风险高收益（月 9–12）

默认 **多数月份跳过**。打开条件 = 数据门从 BLOCKED 变成 DONE。

| 方向 | 开门条件 | 仍禁止 |
| --- | --- | --- |
| Alternative data / LLM macro | 外部表只读入库 + 时间戳 ≤ 决策时 | 用 LLM 读未来新闻 |
| Event | 日历文件 + 预注册事件集合 | 对着大阴线事后贴标签 |
| Carry | 利率/掉期序列 | 用价格动量冒充 |
| 真 VRP | IV | 用 ATR 冒充卖权 |
| 30%+ 家族 | 至少一条 Level 1 边已冻 | 无边加杠杆 |

高风险探索可以设计，**不可以**在无数据时执行。

月 12 之后：Final OOS / Paper / MT5 仍默认禁止，直到 Level 2 存在且另批。

---

## 12 个月日历（一人 + AI）

| 月 | 只准做 | 明确不做 |
| ---: | --- | --- |
| 1 | V0.9 合同 + 模板 + 机制库 + 数据需求（本任务） | 跑数（除非另批） |
| 2 | V0.9 实现与四 Xavier | 第 4 条假设 |
| 3 | 冻结结论 | 改门 |
| 4–5 | 按 1.3 二选一：4A 或 Data V0.2 或日历 | 并行 ML+RV |
| 6–7 | 若有袖套：第二个低相关未知；若无：只补数据或停 | 为 10% 改规则 |
| 8 | 中期审计：Level 几？BLOCKED 清单 | 宣布年化 |
| 9–10 | 仅当新数据落地：一个高风险家族 | 无数据的高风险 |
| 11 | 若仍无 Candidate：停开策略 | 再挖 RSI |
| 12 | 写年度 FAILED/UNKNOWN 清单 | Paper/MT5 |

---

## 与资本目标的距离（路线层）

| 事实 | 对 12 个月的约束 |
| --- | --- |
| 无 Level 1 | 今年任何 10%/15%/30% 数字都是幻觉 |
| 最好残留 +0.23% CAGR | 不是起点，是已冻失败残留 |
| D1 ~6.4 年含 2020 原油极端 | 即使出现 Candidate，10% 仍可能达不到 |
| 黄金牛市路径 | 被动多头会好看；那不是研究胜利 |

好的一年：第一个 CANDIDATE，或全部可做 UNKNOWN 变 FAILED 且缺口写清。  
失败的一年：改门槛、扩假设、跳级交易。

---

## Decision

1. 本路线取代 V0.7.1 队列里「下一刀 = Cross Asset」的规划角色。V0.8 事实文件不改。  
2. 第一阶段唯一研究合同 = Regime Transition V0.9。  
3. 禁止跳级到 Level 4/5。  
4. 月度只开一个实现模块。

---

## Next Automatic Action

Phase E：写出 `RESEARCH_CONTRACT_TEMPLATE_V1.md`、`CANDIDATE_MECHANISM_LIBRARY_V1.md`、`REGIME_TRANSITION_V0.9_CONTRACT.md` 及数据/测试框架。仍不写代码、不跑实验。
