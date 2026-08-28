# Candidate Acceptance Gate V1

Program: `ALPHA_PROGRAM_V1`. Phase 6.  
Write-once. Seeing a pretty equity curve does not amend this file.

This gate exists so Level 1 的「发现」和「年化 10%」不再被混成一句话。

---

## Executive Summary

用户举例里的 `CAGR > 10%`、`Sharpe > 1`、`MaxDD < 20%` **全部冻结**——但冻在 **Level 2 / 资本层**，不是 Level 1 发现层。

若把 CAGR>10% 写成 Level 1：

- 本样本 D1 只有 ~6.4 年，含 2020 原油极端与黄金牛市  
- 一个真实、可重复、成本后、FDR 过的 4% 边会被扔掉  
- 团队会被逼去调参制造 10%

那会远离赚钱，不是靠近。

Level 1 = **这是不是边**。  
Level 2 = **这是不是能当策略书**。  
≥10% = **这本书能不能支撑资本目标**（报告，可达不到）。

参数在看收益后不可改。改 = 新 `discovery_id`。

---

## LEVEL 1 — Discovery Candidate（本程序条件 A）

必须 **全部** 满足。缺一不可。

### 经济

- 预注册机制段落存在，且不是「指标 X 有时好」  
- `Not:` 至少写明不是 V0.6 短持有同构、不是 V0.8 次日代理

### 统计

- 预注册闭集；`m` = 假设数  
- RESEARCH permutation（或合同指定的）`adjusted_p` 进入 BH 发现，`q=0.05`  
- 不得降 q、不得事后丢掉失败假设再算 FDR

### 成本与重复

- RESEARCH 与 VALIDATION 成本后 `total_return` > 0  
- 实现符号与预注册 H1 一致  
- RESEARCH 笔数 ≥ 8，VALIDATION ≥ 4  
- 至少 **两个** 数据集或两个 target 过单假设门（与 V0.6/V0.8 精神一致）  
- 主证周期必须让年化可解释：**默认 D1**。M15/H1 不得单独把一个品种抬成 Level 1

### 风险（发现层，沿用已锁合同）

- RESEARCH max DD ≥ −25%  
- VALIDATION max DD ≥ −30%  
- `max_trade_share` ≤ 50%  
- 不得用同期相关代替滞后 delta

### 过程

- Final OOS 未读  
- 冻结实验未改  
- 哈希在跑前复现  
- 失败臂保留

```text
LEVEL_1 = economic + FDR + costed R/V + sign + ≥2 targets/datasets + DD/occupancy + no peek + no retune
```

**CAGR ≥ 10% 不是 Level 1 门。**  
必须报告 CAGR，并与同窗无条件同向基准比 delta。

---

## LEVEL 2 — Strategy Candidate

先有 Level 1，再问书。

在 **D1（或 Data V0.2 之后足够跨度）** 上冻结：

| 门 | 值 | 为何在这一层 |
| --- | --- | --- |
| 可解释 CAGR | 必须能算；M15 年化禁止 | 跨度 |
| Sharpe | **> 1.0** | 用户举例；过噪 |
| Max DD | **> −20%**（即回撤浅于 20%） | 比 Level 1 更严的书门 |
| 成本模型 | 不得比发现合同更便宜 | 防作弊 |
| 执行 | NEXT_BAR_OPEN；禁 close | 已锁 |
| 参数 | 与 Level 1 合同同一组 | 禁止为 Sharpe 改 hold |

Level 2 **仍不要求** CAGR>10%。一个 Sharpe>1、DD 浅、成本后重复的 6% D1 边是合法 Level 2。它 **不** 证明资本目标达标。

---

## CAPITAL MARK — 年化目标（不是发现）

| 标记 | 条件 | 用途 |
| --- | --- | --- |
| `CAPITAL_10_UNMET` | Level 2 存在但 D1 CAGR < 10% | 诚实：有边，不够 10% |
| `CAPITAL_10_PLAUSIBLE` | Level 2 且 RESEARCH+VALIDATION D1 CAGR ≥ 10%，且不是单窗极端日贡献 | 才许说「这本书在样本内碰到 10%」 |
| `CAPITAL_15_30` / `30_PLUS` | 另开高风险家族 + 另批 | 默认关 |

2020–2026 无条件多 GOLD 若看起来 ≥10%，记 `PATH_BENCHMARK`，**不得**写成 Candidate。

---

## 明确拒绝（任何一层）

- 看结果改假设 / 阈值 / hold / 成本 / 方向  
- 单品种过门  
- FDR 后再挑赢家讲故事  
- M15 上宣布年化 10% / 30%  
- 打开 Final OOS 来「确认」  
- MT5 / `order_send` / 真实资金

---

## 与已锁合同的兼容

V0.8 / V0.9 单假设门（收益>0、符号、笔数、DD −25/−30）= Level 1 的构件。  
本文件不回溯改 V0.8 结果。V0.8 已是 `NO_CANDIDATE`。  
V0.9 跑完用本文件贴标签，不另发明第三套门。

---

## Decision

条件 A = Level 1，不是 CAGR>10%。  
条件 B = 可做 UNKNOWN 被系统排除。  
两者都未到：继续设计 /（另批）执行 V0.9，不停成「等待」。

---

## Next Automatic Action

Phase 7：失败知识库、下一批数据需求、已有实验漏洞审计、STATUS_UPDATE。仍不写业务代码。
