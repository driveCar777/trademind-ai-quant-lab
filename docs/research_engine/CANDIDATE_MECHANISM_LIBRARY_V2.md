# Candidate Mechanism Library V2

Program: `ALPHA_PROGRAM_V1`. Phase 1.  
Not an indicator library. A mechanism is a **risk-transfer or constraint story**, then a testable claim.

V1 shelf (`CANDIDATE_MECHANISM_LIBRARY_V1.md`) remains. This file is the expanded taxonomy.

Status codes: `KILLED` / `UNKNOWN` / `DATA_BLOCKED` / `SHELF` / `NEXT`.  
Do not use `SUPPORTED` for any Tradable edge — **none exist**.  
HYP-0001 `WEAK_SUPPORT` is statistical, not `SUPPORTED` as money.

---

## Executive Summary

Price Formation 三个经典皮肤（趋势持续、回归、突破）在本实验室的短持有合同下 **KILLED**。  
还活着的是结构层：转换、相关变化、残差；以及被数据挡住的溢价层。

可执行下一步仍然只有：**Regime Transition（NEXT）**。

---

## 1. Price Formation

| id | 机制 | 不是什么 | 状态 |
| --- | --- | --- | --- |
| PF-TREND | 价格沿已实现方向继续，因为仓位/止损单向堆积 | SMA 交叉、ADX 水平过滤 | **KILLED**（短持有）。低换手新机制 = SHELF |
| PF-REV | 偏离被库存/做市商拉回 | RSI 超买超卖 | **KILLED**（单序列短持有） |
| PF-BRK | 区间结束时止损 cascade | Donchian-20 每天扫 | **KILLED** |
| PF-PERSIST | 短连续同号有条件位移 | 交易书 | **KILLED as book**；HYP-0001 仅 WEAK_SUPPORT |

别人可能没「发现」这些：发现得太多了。本实验室用 FDR + 成本证明 **这一宇宙 + 这一成本** 下它们不是 Candidate。

---

## 2. Market Structure

| id | 机制 | 为什么可能赚钱 | 状态 |
| --- | --- | --- | --- |
| MS-RT | 状态 **变化** 时风险预算重置，条件期望在随后数日偏移 | 转换稀疏，成本可能不先杀死；V0.5 只测了水平 | **UNKNOWN / NEXT** |
| MS-VOLC | 波动聚集：大 \|r\| 后仍大 \|r\| | FD 见过聚集痕迹，FDR 未过；**不是方向** | UNKNOWN as magnitude；KILLED as direction |
| MS-LIQ | 摩擦高时收益被点差吃掉或出现流动性溢价 | spread/tick 已当因子败；无 real_volume | PARTIAL killed / **DATA_BLOCKED**（真溢价） |
| MS-CORR | 品种间相关在压力期上升，残差可交易 | V0.8 测的是滞后代理，不是相关制度切换 | **UNKNOWN**（新机制才合法） |
| MS-CAL | 周末/星期信息集中释放 | D1 有 Sunday bar；从未预注册 | **UNKNOWN** SHELF |

---

## 3. Relative Value

| id | 机制 | 状态 |
| --- | --- | --- |
| RV-XA08 | 美元代理当日收益 → 次日 GOLD/OIL | **KILLED** |
| RV-RES | GOLD 对 OIL（或 FX）慢速关系的残差回归 | **UNKNOWN** SHELF（≠ XA 改 lag） |
| RV-SPREAD | 两资产比价均值回复 | 同 RV-RES；要对齐 D1 | **UNKNOWN** SHELF |
| RV-PROXY | 用 EURUSD/USDJPY 合成伪 DXY 再扫分位 | 与 V0.8 同构 | **KILLED** |

---

## 4. Risk Premium

| id | 机制 | 状态 |
| --- | --- | --- |
| RP-CARRY | 利率差异补偿 | **DATA_BLOCKED** |
| RP-VRP | IV − RV | **DATA_BLOCKED** |
| RP-DEF | 高波动空仓「少亏」当利润 | **KILLED**（0 收益） |
| RP-4A | 已实现 vol 缩放 **已存活** 袖套 | **SHELF**（无袖套） |
| RP-PATH | 无条件持有风险资产收溢价 | 可测基准；**不是** alpha。2020–2026 黄金路径会骗人 |

---

## 5. 明确没有 SUPPORTED 的交易边

```text
SUPPORTED (tradable)     = 0
WEAK_SUPPORT (predictive)= HYP-0001 only, not a book
KILLED families          = PF-* short-hold, RV-XA08, RP-DEF
UNKNOWN implementable    = MS-RT (V0.9)
UNKNOWN shelf            = MS-CAL, MS-CORR, RV-RES
DATA_BLOCKED             = RP-CARRY, RP-VRP, event, alt, order flow
```

---

## Decision

机制库 V2 冻结分类。禁止把 KILLED 行改名重开。  
Phase 2 只对 UNKNOWN / SHELF / infra 打分。

---

## Next Automatic Action

`ALPHA_RESEARCH_PRIORITY_V2.md` — Top 10，每条写清「为何可能赚 / 为何别人可能没做 / 为何现有数据能验」。
