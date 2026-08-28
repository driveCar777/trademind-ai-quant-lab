# Alpha Coverage Map V1

Design / audit only. 2026-08-26.  
No code. No new experiment. No change to frozen contracts or immutable bars.

Parent facts: HYP-0001 14:11, FD V0.1, V0.5, V0.6, V0.8 freeze, Data Layer V0.1, Protocol V0.3.  
Does **not** replace those files. This map is the post-V0.8 coverage authority for *what return sources exist vs what TradeMind has actually tested*.

Long-run capital target remains: cost- and risk-adjusted annualized return ≥ 10%.  
This file does not claim a CANDIDATE, a book, or 10%.

---

## Executive Summary

TradeMind 的研究引擎（合同、不可变数据、四 Xavier、hash、null、FDR、bootstrap、permutation）已经到 **Level 0**。  
实验室还停在 **Level 0**：没有任何成本后、多数据集、FDR 通过的 Candidate。

已经杀死的不是“市场没有 alpha”，而是一类很窄的东西：

```text
同一品种、同一根 K 线自己的过去
  → 自己的未来方向
  → 短持有（1～8 根）
  → 再加 V0.6 成本
```

以及 V0.8 锁死的另一类：

```text
美元代理当日收益 → 下一对齐日 GOLD / OIL
  → 持有 1 根 D1
  → 同样成本
```

**还没研究、且现在磁盘上可能起步的主未知：Regime Transition（状态变化，不是状态水平）。**  
Carry / IV / 新闻 / 订单流 / 另类数据：**不是 TODO，是 DATA BLOCKED。** 写 TODO 会假装能做。

**2026-08-28 V3 appendix (does not rewrite the 2026-08-26 design):** V0.9 / residual / IT / public IV / COT / EIA stocks / UST / overnight / EIA supply are now **KILLED or INVALID**. Remaining coverage holes that can still change P(Level 1): **futures curve** and **option surface** (HUMAN). See `INFORMATION_GAP_MATRIX_V2.json`.

---

## Current Evidence

| 实验 | 结果 | 杀死了什么 |
| --- | --- | --- |
| HYP-0001 | WEAK_SUPPORT，不是书 | 单资产连续上涨 → 下一根 |
| FD V0.1 | `NO_USEFUL_FACTORS_FOUND`，PROMISING=0，CANDIDATE=0 | 57 个单序列因子农场 |
| V0.5 | `NO_USEFUL_STRATEGIES_FOUND` | 状态 **水平** + 下一根草图 |
| V0.6 | `WEAK_EDGE_ONLY`，程序 CANDIDATE=0 | 短持有突破 / 回归 / 动量；同品种三袖套组合 |
| V0.8 | `NO_CANDIDATE`，3/3 FALSIFIED，FDR 0/3 | 滞后美元代理 → GOLD/OIL，持有 1 日 |

禁止再测（除非新经济机制 + 新版本合同）：SMA / EMA / RSI / MACD / Donchian / 简单突破 / 简单动量 / 单品种短周期预测 / XA-0001/0002/0003 调参。

---

## 1. 状态码（只准用这些）

| 码 | 意思 |
| --- | --- |
| FAILED | 已按锁定合同寻找该边，无程序级 CANDIDATE |
| PARTIAL | 测过近邻，不是该问题本身 |
| UNKNOWN | 未测，现有数据够起步 |
| DATA BLOCKED | 诚实实验现在做不了 |
| FORBIDDEN_RETUNE | 机制已测败；改阈值/N/持有/方向 = 作弊，不是新覆盖 |
| SLEEVE BLOCKED | 理论可做，但没有已存活袖套当输入 |

覆盖 = 进过锁定搜索空间并出过冻结结论。  
「文档里写过、没跑」≠ 已覆盖。

---

## 2. Master coverage table

用户点名的行必须回答。状态按 **FACT**，不按愿望。

| Alpha 来源 | 已覆盖？ | 状态 | 覆盖到哪 | 未覆盖的真正对象 |
| --- | --- | --- | --- | --- |
| Directional | 是（短持有单品种） | **FAILED** | HYP-0001；FD 动量/符号；V0.5 LONG/SHORT；V0.6 MOM-DIR | 低换手、多日、**新机制**的方向（不是再扫 N） |
| Momentum | 是（短持有） | **FAILED** | HYP-0001 streak；FD；V0.6 MOM-DIR（OIL D1 仅 WEAK_EDGE，CAGR≈0.23%） | 趋势 **点火**（Δstate），不是“处于趋势就做” |
| Mean Reversion | 是（单序列短持有） | **FAILED** | FD reversal；V0.5 fade EXTENDED；V0.6 MR-Z20 | 跨品种残差回归（新家族；禁止用它救 V0.8） |
| Breakout | 是 | **FAILED** | FD DISTHIGH；V0.6 TF-BRK20 Donchian-20 | 相关品种确认后的突破（新机制才开） |
| Cross Asset | 是（锁定 3 条） | **FAILED** | V0.8 XA-0001/0002/0003 全灭 | 禁止扩成 10 条同构。其它 RV 要 **新机制 + 新版本** |
| Regime Transition | 否 | **UNKNOWN** | V0.5/V0.6 只用状态 **水平** | `ENTER` / `EXIT` / `VOL_SHOCK` 作信号本身 |
| Volatility Premium | 否（真 VRP） | **DATA BLOCKED** | FD 测过已实现波动→\|收益\|（聚集，非方向）；V0.6 DEF 空仓 0 收益 | IV−RV、卖权。磁盘无 IV |
| Carry | 否 | **DATA BLOCKED** | 无 | 利率 / 期限结构 / 远期曲线 |
| Intraday Seasonality | 否 | **DATA BLOCKED**（主证） | timestamp 在，M15 只有约 1 个月 | 时段效应需要更长 M15/H1 |
| Liquidity Premium | 部分 | **FAILED** as alpha | FD tick_volume / spread；`real_volume` 全 0 | 真成交量、深度、订单流 |
| Portfolio Effect | 部分（假组合） | **FAILED** / **SLEEVE BLOCKED** | V0.6 同品种 TF+MR+MOM 等权全负 | 多个不全相关的真袖套 |
| Event Driven | 否 | **DATA BLOCKED** | FD `FAM-FD-NEWS-0001` DRAFT，从未算 | 事件日历表 |
| Alternative Data | 否 | **DATA BLOCKED** | 无 | 任何非 OHLCV 外部表 |
| ML Nonlinear | 否 | **UNKNOWN**（能力有，合同无） | 本地 LLM 在；未进研究合同 | 锁特征名单之前禁止当主搜 |

---

## 3. 细拆：已测象限（不要再挖同构）

### 3.1 Directional / Momentum / MR / Breakout

同一信息源的四种皮肤。

```text
feature[t] from asset X's own history
target     = X's next 1～8 bars
fill       = next open (V0.6) or next-bar sketch (V0.5)
cost       = spread + 5bp + 10bp / side  (V0.6)
```

结果形态一致：成本后无程序级 CANDIDATE。  
OIL D1 动量残留不是路：单市场、Sharpe≈0.08、禁止调 hold 凑第二个命中。

**OS 判决：** 这一象限作为赚钱搜索 = FAILED。  
再加 SMA/RSI/MACD = 重复。

### 3.2 Cross Asset（V0.8 家族）

测过的 **只有** 这三句，持有 1 个对齐日：

| id | 机制 | 结果 |
| --- | --- | --- |
| HYP-XA-0001 | USDJPY Q3 → 次日 GOLD 空 | FALSIFIED |
| HYP-XA-0002 | EURUSD Q3 → 次日 GOLD 多 | FALSIFIED（符号也反） |
| HYP-XA-0003 | DOLLAR_UP → 次日 OIL 空 | FALSIFIED |

同期 gold/USD \|r\|≈0.41–0.43 **存在**，不是滞后可交易边。  
Decision 043：禁止改 lag / 67% / 方向 / 成本；禁止 HYP-XA-0004。

未测但 **本季不准用「再扫跨品种」冒充新覆盖** 的东西：GOLD−OIL 残差、多日 RV、同 bar 交易。  
那些若做，必须新版本、新机制、新 FDR 族，且排在 Regime Transition **之后**。

### 3.3 Regime 水平（已测）vs 转换（未测）

| 对象 | 状态 |
| --- | --- |
| 处于 TREND_STRONG 则突破 / 动量 | FAILED（V0.5 / V0.6） |
| 处于 RANGE 则回归 | FAILED |
| HIGH_VOL / WIDE 禁开当利润 | FAILED（0 收益） |
| 状态 **变化** 当天及随后固定 N 日 | **UNKNOWN** |

这是地图上唯一「数据够、机制不同、尚未证伪」的主格子。

### 3.4 波动

| 对象 | 状态 |
| --- | --- |
| 已实现高波动 → 更大 \|收益\| | PARTIAL（聚集，FDR 未过，~7–11bp） |
| 已实现高波动 → 可猜方向 | FAILED as directional |
| 空仓叠加当 alpha | FAILED |
| 真波动风险溢价（IV−RV） | DATA BLOCKED |

### 3.5 组合

V0.6 组合 = 同一 2000 根上三个弱技术袖套。负的加负。  
那不是 Portfolio Alpha。真组合要 ≥2 个不全相关的存活袖套。现在 **0 个**。

---

## 4. 未覆盖且可起步（磁盘已有）

按「现在能否诚实开合同」排序，不是按听起来多赚钱。

1. **Regime Transition** — D1，复用 `MARKET_STATE_V0.5` 轴，只对 Δstate 下注。  
2. **D1 日历结构（极窄）** — 星期 / 周末→周一条；D1 ~6.4 年勉强；必须预注册极少条。  
3. **已实现波动 *时机*（不是 VRP）** — 与 1 重叠；V0.9 已收进 `VOL_SHOCK`，不要另开农场。  
4. **低换手方向（新机制）** — 仅当机制不是「再一个均线/动量」。默认不排进下一刀。  
5. **Data Layer V0.2 加长** — 不是 alpha，是给时段 / 年化主证的基础设施。

---

## 5. 未覆盖且现在不能做

| 来源 | 缺什么 | 假装能做的代价 |
| --- | --- | --- |
| Carry | 利率、掉期、远期 | 用价格动量冒充 carry |
| 真 VRP | IV 曲面或 ATM IV | 用 ATR 冒充卖波动 |
| Event | 日历（CPI/NFP/库存） | 事后对着大阴线编故事 |
| 订单流 / 真流动性 | `real_volume` 全 0；无 DOM | 用 tick_volume 再扫一次（FD 已败） |
| 日内季节 | M15 ≈ 1 个月 | 在 20 个交易日上宣布时段 alpha |
| 另类数据 / 新闻 LLM | 无表 | 用聊天模型读行情当特征（泄漏） |
| 多策略组合 | 无袖套 | 再等权三个失败规则 |
| Paper / MT5 | 无 Candidate | 跳级 |

---

## 6. 一张图

```text
单品种短持有技术 ──────── FAILED（不要再挖）
跨品种次日美元代理 ────── FAILED（不要扩家族）
状态水平过滤 ──────────── FAILED
状态转换 Δstate ───────── UNKNOWN  ← 下一刀
D1 极窄日历 ───────────── UNKNOWN（次优先，极少条）
真组合 ────────────────── SLEEVE BLOCKED
时段 / 日内 ───────────── DATA BLOCKED（M15 太短）
Carry / IV / 事件 / 另类 ─ DATA BLOCKED
ML 主搜 ───────────────── 有算力，无合同；排后
```

---

## Decision

1. 覆盖地图以本文件为准。V0.7.1 的「Cross Asset = 下一刀」已被 V0.8 执行结果更新。  
2. 下一实现只允许 **一个** 新 alpha 类：Regime Transition。  
3. 用户表里标成 TODO 的 Carry / IV / 新闻 / 订单流，在本实验室记为 **DATA BLOCKED**，不是待办研究。  
4. 不把「再找更多指标」写成未知。

---

## Next Automatic Action

Phase B：`DATA_CAPABILITY_MATRIX_V1.md` — 用现有 16 份不可变行情，写清每类 alpha 的数据门。
