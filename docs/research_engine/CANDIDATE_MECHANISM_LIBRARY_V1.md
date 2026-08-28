# Candidate Mechanism Library V1

Design only. 2026-08-26.  
This is a **shelf**. Listing a mechanism is not permission to run it.  
Only `REGIME_TRANSITION_V0.9_CONTRACT.md` is the next executable contract.

Do not implement items marked SHELF / BLOCKED / KILLED.

---

## Executive Summary

库的用途：防止下一任 AI 把「没写过的名词」误当成「没想过所以该扫」。  
每条都有：机制一句、不是什么、数据门、状态。

---

## KILLED（禁止再开同构）

| id | 机制 | 被谁杀死 |
| --- | --- | --- |
| K1 | 连续同号 → 下一根 | HYP-0001 |
| K2 | 无条件技术因子农场 | FD V0.1 |
| K3 | 处于某状态则做下一根 | V0.5 |
| K4 | 处于趋势则 Donchian / MOM 短持有 | V0.6 |
| K5 | 处于 RANGE 则 z 回归短持有 | V0.6 |
| K6 | 空仓叠加当利润 | V0.6 DEF |
| K7 | 同品种三袖套等权 | V0.6 book |
| K8 | 美元代理当日收益 → 次日 GOLD/OIL | V0.8 |

---

## NEXT（唯一即将进合同）

| id | 机制 | 状态 |
| --- | --- | --- |
| N1 | 状态 **变化** 后固定持有：风险补偿/仓位调整发生在转换附近，而不是状态水平里 | V0.9 合同 |

---

## SHELF（有机制，本季不跑）

| id | 机制一句 | 不是什么 | 数据 | 何时 |
| --- | --- | --- | --- | --- |
| S1 | 周末信息在 Sunday/Monday D1 被定价 | 不是扫 20 个星期虚拟变量 | D1 支持 | V0.9 结论后，极少条 |
| S2 | GOLD 相对 OIL 的残差回到慢速关系 | 不是 XA 改 lag | 对齐 D1 | 新家族；043 之后 |
| S3 | 无条件配置：波动或等权持有四条 D1 | 不是预测边 | D1 支持 | 永远只当基准 |
| S4 | 已实现 vol 缩放已存活袖套（4A） | 不是 VRP | 要先有袖套 | Candidate 之后 |
| S5 | 预注册非线性状态机（极少特征） | 不是 LLM 扫指标 | D1 + 算力 | 中风险阶段 |
| S6 | 相关品种确认后的突破 | 不是再扫 Donchian N | 对齐 D1 | 新机制合同 |

---

## BLOCKED（缺数据）

| id | 机制一句 | 缺 |
| --- | --- | --- |
| B1 | 利率差异补偿（carry） | 利率 / 掉期 |
| B2 | 卖出偏贵的隐含波动 | IV |
| B3 | 事件溢价（CPI/NFP/库存） | 日历 |
| B4 | 真实供给流动性补偿 | `real_volume` / DOM |
| B5 | 时段拥挤 / 开盘效应 | 更长 M15/H1 |
| B6 | 另类 / 新闻 LLM | 带时间戳的外部表 |

---

## Decision

库可以变长。**可执行集合不能变长**，除非新版本合同。  
V0.9 只取 N1 的三个实例，不取 S* / B*。

---

## Next Automatic Action

写出 V0.9 合同、数据需求、测试框架。
