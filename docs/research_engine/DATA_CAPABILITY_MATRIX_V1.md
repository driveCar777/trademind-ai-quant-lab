# Data Capability Matrix V1

Design / audit only. 2026-08-26.  
No new bars. No MT5 fetch. No experiment.

Authority: Data Layer V0.1, Qualification V0.1, Cross Asset Data Audit, V0.8 align pack (read-only facts).

---

## Executive Summary

TradeMind **现在能研究的**，几乎只有四条品种上的 OHLCV + spread + tick_volume。  
时间够用来做主证的，几乎只有 **D1（约 6.4 年）**。  
M15 / H1 可以做工程冒烟，**不能**做年化 10% 的主证。

因此：趋势/状态转换/单资产方向 = 数据支持。  
跨资产 = 部分支持（有对齐时钟，无 DXY）。  
Carry / IV / 新闻 / 订单流 / 另类数据 = **不支持**。

---

## Current Evidence

### 宇宙（研究权威）

16 份不可变 dataset：GOLD / EURUSD / USDJPY / OIL × M15 / H1 / H4 / D1，`*-20260825-000001`。  
每份 **2000** 根。UTC。`tick_volume` only。`real_volume=0`。`spread` 在。  
额外 GOLD M15 `000002` **不在**研究宇宙。

Broker：Ava Trade。`logical OIL` = `CrudeOIL`。不要假设 `XAUUSD`。

### 跨度（FACT）

| 周期 | 约跨度 | 年化问题 |
| --- | --- | --- |
| M15 | ~1 个月（GOLD 2026-07-24→08-25） | 禁止当 10% 主证 |
| H1 | ~4 个月 | 禁止当 10% 主证 |
| H4 | ~15 个月 | CAGR 勉强可算，样本薄 |
| D1 | ~6.4 年（2020-03/04 → 2026-08-25） | 唯一可谈年化的窗 |

### 跨品种时钟

四向 D1 inner join：**1993** 日，`2020-04-01` → `2026-08-25`。  
`align_id` = `tm-align-D1-XA-20260826-000001`。禁止填日期。  
t+1 = 对齐序列下一行，不是日历 +1。Sunday D1 存在，Saturday 不存在。

EURUSD 与 USDJPY 日期集合相同。无 DXY、无利率、无 IV、无事件表、无 DOM。

### 窗口纪律

任意新合同必须 70/15/15。最后 15% Final OOS **DENIED**。  
V0.8 对齐窗已冻：RESEARCH 1395 / VALIDATION 299 / FINAL_OOS 299。  
单品种 D1 合同可按 **该品种自己的日期** 切 70/15/15，不得偷看收益后再切。

---

## 1. 字段能支持什么

| 字段 | 有？ | 能做什么 | 不能做什么 |
| --- | --- | --- | --- |
| `open high low close` | 是 | 收益、状态、突破、转换 | 不能当成交量 |
| `timestamp_utc` | 是 | D1 日历；对齐键 | M15 时段主证（跨度不够） |
| `spread` | 是 | 成本、FRICTION | 不能当流动性 alpha（FD 已败） |
| `tick_volume` | 是 | 活动轴（V0.5） | 不能冒充真实成交量 |
| `real_volume` | 全 0 | 无 | 流动性溢价、订单流 |
| IV / 期权 | 无 | — | VRP、卖波动 |
| 利率 / 掉期 / 远期 | 无 | — | Carry |
| 事件日历 | 无 | — | Event |
| 新闻 / 另类 | 无 | — | Alt / LLM macro 主证 |
| 盘口 / tick | 无 | — | 微观结构 |

---

## 2. Alpha × 数据门（必须回答）

| 方向 | 数据是否支持 | 周期 | 说明 |
| --- | --- | --- | --- |
| 趋势（状态水平） | **支持** | D1 主证 | 已测败。不是缺数据 |
| 动量 / 回归 / 突破 | **支持** | D1 主证；M15/H1 只可诊断 | 已测败 |
| 状态转换 | **支持** | **仅 D1** | 稀疏事件；M15 一个月不够 |
| 跨资产滞后 RV | **部分支持** | D1 对齐 1993 日 | 无 DXY；V0.8 三句已败；禁止同构扩族 |
| 跨资产残差 / 比价 | **部分支持** | D1 对齐 | 新机制才允许；本季不排第一 |
| 多资产配置（无预测） | **支持** | D1 | 这是基准，不是 alpha |
| Carry | **不支持** | — | 无利率 |
| IV / 真 VRP | **不支持** | — | 无期权 |
| 新闻 / 事件 | **不支持** | — | 无日历 |
| 订单流 | **不支持** | — | `real_volume=0` |
| 日内季节 | **不支持（主证）** | M15 太短 | 加长历史之前不要开 |
| 流动性溢价 | **不支持（真）** / 部分（spread） | — | spread/tick 已当因子败过 |
| 组合效应 | **不支持（现在）** | — | 无存活袖套 |
| ML 非线性 | **部分支持** | D1 特征 | 有 OHLC 和本地 LLM；无额外标签；过拟合风险高 |
| Paper / MT5 | **能力在，资格无** | — | 终端在；禁止无 Candidate 跳级 |

---

## 3. 周期能力（硬规则）

| 研究问题 | M15 | H1 | H4 | D1 |
| --- | --- | --- | --- | --- |
| 工程冒烟 / 泄漏哨兵 | 可 | 可 | 可 | 可 |
| 成本后方向证伪 | 可（已做过） | 可 | 可 | 可 |
| 稀疏事件（转换、星期） | 否 | 弱 | 弱 | **可** |
| 年化 10% 主证 | **否** | **否** | 弱 | **唯一候选窗** |
| 时段 / session | 否（跨度） | 否 | 否 | 不适用 |
| 跨品种对齐主证 | 否 | 否 | 诊断 | **是**（已有 pack） |

V0.6 已证明：把几周 M15 亏损年化会得到 −90% 垃圾 CAGR。再对 M15 谈 30% 年化 = 假问题。

---

## 4. 数据缺口清单（要补什么才能开哪一类）

| 缺口 | 打开哪一类 | 怎么补 | 不阻塞什么 |
| --- | --- | --- | --- |
| 更长 M15/H1（新 `dataset_id`，不覆盖 000001） | 时段、短周期年化 | Data Layer V0.2 只读再抓；失败记 Max. bars | V0.9 D1 转换 |
| 利率 / 掉期 | Carry | 新表 + 新家族 | 全部价格研究 |
| ATM IV 或期货曲线 | 真 VRP | 新表 | 已实现 vol 时机 |
| 事件日历 | Event | 新表；禁止事后贴 | V0.9 |
| `real_volume` 或 DOM | 流动性 / 订单流 | 换源或换品种 | V0.9 |
| 第二个存活袖套 | Portfolio | 先发现边 | — |

补数据必须新 `dataset_id`。禁止覆盖 immutable。禁止把「刚下载的最新段」叫 Final OOS。

---

## 5. 四 Xavier / 计算能力（不是行情）

| 能力 | 状态 |
| --- | --- |
| 四机 SSH 执行 stdlib 作业 | DONE（FD / V0.6 / V0.8） |
| Windows 锁合同 + 收集 + FDR | DONE |
| Xavier pip / numpy / pandas | **无**。新 runner 必须 stdlib |
| 本地 LLM（Arc A770M） | DONE 作为推理网关；**未**进研究合同 |
| MT5 `order_send` | 能力在模拟盘路径；研究阶段 **禁止** |

有算力 ≠ 有 alpha 数据。

---

## Decision

1. 下一份研究合同必须吃 **现有 D1**，不得以「先等 V0.2」为借口拖延 Regime Transition。  
2. 任何需要利率 / IV / 新闻 / 订单流的设计，标记 BLOCKED，不得开假合同。  
3. M15/H1 不得出现在 V0.9 的 FDR 主族。  
4. 被动做多 GOLD 2020–2026 会看起来很赚。那是样本路径，**不是** 条件边。合同必须对无条件同向基准做 delta。

---

## Next Automatic Action

Phase C：`ALPHA_PRIORITY_RANKING_V1.md` — 五维乘积打分，排出可实施 Top 5。
