# Alpha Discovery V0.7 Plan — Audit and Next Money Map

Design only. No code. No new experiment. No Final OOS. No MT5. No `order_send`.

10% annualized after cost and risk is the **long-run capital target**.  
This document does **not** claim a CANDIDATE, a book, or 10%.  
It answers: **why the current search found no edge, what was never tested, and which untested channel is most likely to be worth the next experiment.**

Locked prior work is read-only: HYP-0001 14:11, FD V0.1, V0.5, V0.6, Data Layer V0.1, Research Protocol V0.3.

Version map (do not collapse these):

| user label | on-disk name | result |
| --- | --- | --- |
| V0.4 研究协议 | Research Protocol V0.3 + Engine V0.4 | 合同 / 窗口 / 泄漏哨兵可信 |
| V0.5 Market State + Strategy 基础 | `STRATEGY_DISCOVERY_V0.5` | `NO_USEFUL_STRATEGIES_FOUND` |
| V0.6 Strategy Discovery | `PROFIT_DISCOVERY_V0.6` | `WEAK_EDGE_ONLY`，程序级 CANDIDATE=0 |

---

## 0. Verdict first

V0.6 没有 CANDIDATE，**不是因为“市场没有 alpha”**。  
是因为本实验室到现在只测了一种很窄的东西：

```text
单品种 + 单序列技术状态 + 短持有（1～8 根）+ 方向性下注
+ 成本（spread + 5bp + 10bp）
```

这条路已经用三种合同测完：无条件因子、下一根 bar 草图、成本后真实回测。  
三种都没有给出可继续当书的策略。

**下一阶段不要再增加简单策略。**  
下一阶段要换 **信息来源**，不是换 RSI / MA / N / 持有期。

在现有磁盘数据上，**最可能赚钱、也最先能诚实开实验的方向**是：

**方向 2 — Cross Asset Relationship（先对齐四条 D1，用美元通道看 GOLD / OIL）。**

它在 FD V0.1 里已经写成 `FAM-FD-XASSET-0001` DRAFT，从未计算。  
四条 D1 已有约 2020-04-01 → 2026-08-25 的重叠，**不必先等更长的 M15** 才能开始设计合同。

实现仍未开始。本文件只锁设计。

---

## 1. 为什么 V0.6 失败

### 1.1 失败是什么（FACT）

`PROFIT_DISCOVERY_V0.6`，hash `0fba52a98d861046cd61db51861bf96bebfaa2d51b42001d37463776bb7891d7`。

```text
outcome           = WEAK_EDGE_ONLY
program CANDIDATE = 0
WEAK_EDGE         = 2   (MOM-DIR 0.5% / 1%，只过 OIL D1)
NO_EDGE           = 5
```

最好的锁定残留：OIL D1 动量 1% 风险，研究总收益 +1.82%，**D1 CAGR +0.23%**，Sharpe ≈ 0.08。  
程序规则要求 **≥ 2 个 dataset** 过门。失败。  
同品种 TF+MR+MOM 等权组合：GOLD / EURUSD / USDJPY / OIL 的 D1 研究收益全负。

这不是“差一点点到 10%”。这是 **没有可升级的策略对象**。

### 1.2 失败不是什么

| 不要读成 | 事实 |
| --- | --- |
| 数据不可信 | Data Layer / Qualification / Readiness / Protocol 已冻结 |
| 实验不可信 | 合同、窗口、FDR、四 Xavier 执行已证明 |
| 成本模型写错所以没边 | 成本是真实摩擦。去掉成本去找 10% 是作弊 |
| 市场没有机会 | 只证明：**这个搜索空间**不够 |
| OIL D1 是候选 | 单市场过门 = WEAK_EDGE，禁止调参凑第二个命中 |

### 1.3 五层原因（按约束力）

**A. 信息来源太窄（主因）**

测过的全是 **同一根 K 线自己的过去 → 自己的未来**：

- HYP-0001：3 根同号连续 → 下一根
- FD V0.1：57 个单序列动量 / 反转 / 突破 / 波动 / 效率 / tick 量 / spread
- V0.5：状态过滤后的下一根方向草图
- V0.6：状态内突破 / 回归 / 动量，持有 5～8 根

从未测：

- 状态 **变化**（进入 / 离开 TREND，而不是“处于 TREND”）
- 品种 A 的过去 → 品种 B 的未来
- 对齐后的多资产残差 / 领先滞后
- 交易时段 / 星期结构
- 事件日历
- 利率 / 隐含波动 / 期限结构这类风险溢价

FD 自己把 cross-asset 和 news 标成 DRAFT。V0.6 没有打开它们。

**B. 持有太短，成本先吃光（机制）**

V0.6 锁定：NEXT_BAR_OPEN，半价差 + 5bp + 10bp / 边，来回约 **spread + 30bp**。  
持有 5～8 根。M15/H1 上这是高频摩擦，不是投资。

结果形态：M15/H1 研究收益大面积为负；年化数字到 −90% 是 **把几周亏损年化**，不是一个交易年。  
DEF-SKIP 0 笔 0 收益：空仓叠加不是利润引擎。

结论（约束，不是新策略）：  
以后任何方向，若仍用 5～8 根持有 + 30bp+spread，会再次印出 NO_EDGE。  
**低换手是所有新方向的硬约束，不是一个可扫描的参数。**

**C. 样本跨度不够回答年化 10%（数据）**

每份 dataset **2000 根**（manifest FACT）：

| dataset | start UTC | end UTC | 大约跨度 |
| --- | --- | --- | --- |
| GOLD M15 | 2026-07-24 | 2026-08-25 | ~1 个月 |
| EURUSD / USDJPY M15 | 2026-07-27 | 2026-08-25 | ~1 个月 |
| 四品种 H1 | 2026-04-24/30 | 2026-08-25 | ~4 个月 |
| 四品种 H4 | 2025-05-27/29 | 2026-08-25 | ~15 个月 |
| GOLD D1 | 2020-03-26 | 2026-08-25 | ~6.4 年 |
| EURUSD / USDJPY D1 | 2020-04-01 | 2026-08-25 | ~6.4 年 |
| OIL D1 | 2020-03-24 | 2026-08-25 | ~6.4 年 |

只有 D1 的 CAGR 有年化含义。最好残留仍是 +0.23%。  
M15/H1 上谈 10% 年化，在这批快照上是假问题。

**D. 组合没有新信息（组合）**

V0.6 组合 = 同一品种、同一 2000 根上的三个弱袖套等权。  
三个袖套相关、同成本、同状态过滤。负的加负还是负。  
这不是跨资产组合，也不是风险平价。

**E. 评价对象错位（历史，V0.5 已部分修正）**

更早的合同只输出 p 值 / 下一根位移。  
V0.6 第一次输出总收益、CAGR、DD、Sharpe、笔数、换手、成本后权益。  
评价已经对齐赚钱问题。**搜索空间没有对齐。**  
所以 V0.7 禁止再堆简单策略，禁止把 OIL 动量调成第二个命中。

### 1.4 已经用尽的失败方向（禁止再测）

| 方向 | 合同 | 结果 |
| --- | --- | --- |
| 3 根同号连续 | HYP-0001 | WEAK_SUPPORT，不是书 |
| 无条件单因子农场 | FD V0.1 57 | `NO_USEFUL_FACTORS_FOUND` |
| 状态内下一根多空 | V0.5 15 sketches | `NO_USEFUL_STRATEGIES_FOUND` |
| Donchian-20 趋势突破 | V0.6 TF-BRK20 | NO_EDGE |
| RANGE_LOWVOL z20 回归 | V0.6 MR-Z20 | NO_EDGE |
| 趋势+RET_5 动量短持有 | V0.6 MOM-DIR | 仅 OIL D1 WEAK_EDGE |
| HIGH_VOL / WIDE 空仓 | V0.6 DEF | 0 收益 |
| 同品种三袖套等权 | V0.6 portfolio | D1 全负 |

禁止：RSI 优化、MA 扫描、改 N=20、改 hold=5、改 5bp/10bp 去凑 10%。

---

## 2. 当前 Alpha 覆盖范围

### 2.1 覆盖矩阵

图例：

- **TESTED_FAIL** — 已用锁定合同测过，无 CANDIDATE
- **PARTIAL** — 测过近邻，不是该问题本身
- **DRAFT_NEVER_RUN** — 合同里写过，没算
- **NOT_TESTED** — 从未进搜索空间
- **BLOCKED_NO_DATA** — 现在磁盘上没有所需字段

| alpha 族 | 覆盖 | 证据 | 值不值得再挖同构 |
| --- | --- | --- | --- |
| 方向预测（下一根符号 / 连续） | TESTED_FAIL | HYP-0001；FD momentum；V0.5 LONG/SHORT/MOM | 否 |
| 趋势跟随（处于趋势则做） | TESTED_FAIL | V0.5 UP/DOWN；V0.6 MOM-DIR | 否 |
| 均值回归 / 反转 | TESTED_FAIL | FD reversal；V0.5 FADE_EXT*；V0.6 MR-Z20 | 否 |
| 突破 | TESTED_FAIL | FD DISTHIGH/NEARHIGH；V0.6 TF-BRK20 | 否 |
| 波动（预测 \|收益\|） | PARTIAL | FD 5 条 INCONCLUSIVE：波动聚集，FDR 失败，~7–11 bps | 不要当方向性边；见方向 3 |
| 波动（空仓叠加） | TESTED_FAIL | V0.5 SKIP_WIDE；V0.6 DEF | 否，不是利润引擎 |
| tick 量 / spread 摩擦 | TESTED_FAIL | FD VOLUME/SPREAD；宽点差诊断 | 只作过滤，不作 alpha |
| 有限 MTF | TESTED_FAIL | FD MTF，仅 M15 上 4 根 HTF 代理 | 否 |
| **状态转换** | **NOT_TESTED** | 有 `state_id`，从未用 Δstate 作信号 | **是** |
| **多资产关系 / 跨品种** | **DRAFT_NEVER_RUN** | `FAM-FD-XASSET-0001` | **是（优先）** |
| **时间结构** | **NOT_TESTED** | 有 `timestamp_utc`，未做时段/星期 | 要更长 M15/H1；D1 星期须极窄预注册 |
| **事件驱动** | **BLOCKED_NO_DATA** | `FAM-FD-NEWS-0001` DRAFT；无日历 | 先有事件表再谈 |
| **风险溢价（利率/隐含波动/期限）** | **BLOCKED_NO_DATA** | 无利率、无 IV、无期货曲线 | 有数据前不要假装能收溢价 |
| 跨品种组合曲线 | NOT_TESTED | V0.6 只做同品种袖套 | 有跨品种信号后再做 |
| AI 生成特征 | NOT_TESTED | 本地 LLM 存在，未进研究合同 | 最后，且必须锁名单 |

### 2.2 已覆盖的五类（用户点名）分别测到哪

**1. 方向预测** — 测透。从“下一根是否同号”到“状态内是否该做多/空”。没有经济上站得住的位移。

**2. 趋势** — 测透“处于趋势”。没测“刚进入趋势 / 刚离开趋势”。

**3. 反转** — 测透价格偏离均值后的短持有回归。没测跨品种偏离（GOLD 相对 USD 的残差）。

**4. 突破** — 测透单序列 20 根高低点。没测相关品种确认后的突破。

**5. 波动** — 测到一件真事：高波动后面更可能是大 \|收益\|（聚集）。没测到一件假事：高波动后面更容易猜对方向。  
V0.6 用高波动禁开仓，组合仍亏。所以波动目前是 **风险信息**，不是方向 alpha。

### 2.3 一张图：钱不在已测象限

```text
                单品种技术状态
                       │
     已测完且失败 ─────┼───── 未测：状态转换
                       │
     已测完且失败 ─────┼───── 未测：跨品种 / 对齐 D1
                       │
     部分：波动聚集 ───┼───── 挡住：事件 / IV / 利率
                       │
                       └── 未测：时间结构（缺跨度）
```

---

## 3. 下一代 Alpha 方向（只设计，不实现）

五条都要写清：**经济假设、不是什么、现有数据能否起步、成功长什么样、失败长什么样。**  
成功仍不是 10%。成功是：出现 **可升级的 Strategy Candidate 输入**（成本后、多窗口、不是单次贡献）。

共同硬约束（从 V0.6 继承，不重开讨论）：

- NEXT_BAR_OPEN，禁止 close 成交
- 成本必须计
- 杠杆上限 1×
- 持有按 **日或更长** 设计，不回到 5～8 根扫描
- Windows 锁空间，Xavier 只执行
- 不改旧实验，不锁 Final OOS，不发 MT5

### 方向 1 — Market Regime Transition

**假设：** 预测力在 **状态变化**，不在状态水平。  
例如：SMA20/50 关系翻转、ADX14 从弱变强、VOL 从低切高。变化本身可能改变下一步的条件期望。

**不是：** 再当 TREND_STRONG 就做 Donchian。那是 V0.6。

**信号草稿（预注册时再锁死，这里只定性）：**

- `ENTER_TREND`：RANGE_* → TREND_* 
- `EXIT_TREND`：TREND_* → RANGE_*
- `VOL_SHOCK`：LOW/MID → HIGH_VOL
- 只在转换 bar 及随后 **固定少数日** 评估，不允许事后加长窗口

**现有数据：** D1 可起步（~6.4 年，转换次数有限）。M15 一个月转换样本不够。

**需要的新能力：** 在已有 `state_id` 上做因果差分；转换计数；稀疏事件的多重检验（转换很少，FDR 负担不同）。

**成功：** 至少 2 个 D1 品种上，转换后的成本后收益同号，且不是一两根极端日贡献。  
**失败：** 转换后收益 ≈ 无条件，或只在 OIL 极端日出现。保留失败。

**赚钱理由：** 换手低，成本不再先杀死实验。经济故事是“制度切换”，不是“再找一个均线”。

### 方向 2 — Cross Asset Relationship（本阶段最优先）

**假设：** 美元通道与风险资产不是同步噪声。  
USDJPY / EURUSD 的已实现变化，对 **下一根** GOLD / OIL 的条件期望可能非零。  
这是宏观相关，不是再挖 GOLD 自己的 RSI。

**不是：** 四条曲线简单等权（V0.6 同品种组合已失败）。  
**不是：** 宣称有 DXY。磁盘上 **没有** DXY。USDJPY、EURUSD 只是不完美的美元代理。必须在合同里写代理，禁止写成“美元指数”。

**可起步的具体问题（将来锁 1～3 条，不准扫）：**

1. USDJPY D1 收益 → 下一根 GOLD D1  
2. EURUSD D1 收益 → 下一根 GOLD D1  
3. USDJPY / EURUSD 同步走强 → 下一根 OIL D1  
4. GOLD 与 OIL 残差（回归残差的均值回复或动量）— 仍是跨品种，不是单序列 z20

**现有数据：** 四条 D1 重叠约 **2020-04-01 → 2026-08-25**。H4 重叠约 15 个月，可作稳健性，不能当主年化窗口。M15/H1 重叠只有几周到几个月，**不能**作本方向主证。

**缺的不是新 K 线，是对齐层：** 按 UTC 日（或 bar 开盘）做 inner-join，滞后严格因果（t 的 A 只能预测 t+1 的 B）。Data Layer V0.1 写明未做跨品种对齐。这是 V0.7 框架的第一块数据工作，仍不是策略。

**成功：** 成本后、NEXT_BAR_OPEN、持有 ≥ 1 个 D1，至少两个被预测品种或两个代理定义同号，最大单笔不主导。  
**失败：** 相关只在同期（不能交易）或只在 2020 原油极端段。OIL D1 资格里已有极端日，必须预注册如何处理，禁止 silently drop。

**赚钱理由：** 这是当前矩阵里 **唯一既有经济通道、又有现成重叠样本、又从未计算** 的方向。  
FD 已预留 `FAM-FD-XASSET-0001`。不要重开一个同义家族而不写血统。

### 方向 3 — Volatility Risk Premium（诚实版）

**假设（能做的）：** 不预测涨跌。预测 **已实现波动是否异常**，用来 **缩放仓位 / 禁止交易**，让别的边在成本后活下来。

**假设（不能假装）：** 收取隐含波动溢价。磁盘无期权、无 IV、无方差互换。  
FD 已证明：高 range / TR 后面 \|收益\| 更大（聚集），**不是**方向。  
V0.6 已证明：只跳过 HIGH_VOL **不会**单独产生正收益。

**因此本方向拆成两级：**

| 级 | 内容 | 现在 |
| --- | --- | --- |
| 3A 风险模块 | 用已实现 VOL 做目标波动或硬跳过 | 可设计进框架的 Risk Evaluation；不是 CANDIDATE 来源 |
| 3B 真 VRP | 卖波动 / 收 IV−RV | **BLOCKED_NO_DATA** |

**成功（3A）：** 同一跨品种或转换信号，在 vol-targeted 下验证收益仍在、DD 下降。  
**失败：** 一加缩放边就消失——说明原来是波动赔付，不是可交易边。  
**禁止：** 把 3A 写成“找到了波动率风险溢价”。

### 方向 4 — Time Structure

**假设：** 条件期望随时钟变。FX / 黄金有伦敦、纽约、亚洲时段；D1 有星期效应。

**现有数据：** `timestamp_utc` 已在。不需要新列就能做 **特征**。  
**不够的是跨度：**

- M15 ~1 个月：独立交易日太少，时段研究会过拟合当周新闻
- H1 ~4 个月：只够探索，不够年化
- D1 ~6.4 年：可以预注册 **极少** 条星期假设（例如“周一不做 / 只做”），不准做 5×12 日历农场

**成功：** 预注册的时段或星期规则，在 ≥2 品种同号，成本后仍在，且换手低于 V0.6。  
**失败：** 只在某一个月的 M15 上好看。

**顺序：** 排在方向 2 之后。若要做时段主证，先要 Data Layer V0.2 的长 M15/H1。

### 方向 5 — AI Feature Discovery

**假设：** 人想不全的 **有经济解释的特征** 可以由本地模型提议，再进入与 FD 相同的锁空间纪律。

**不是：** 模型直接下单。不是无限特征农场。不是把 Qwen 的散文当因子。

**允许：** Windows 上的已有 LLM（Qwen2.5-14B）根据 **本文件的缺口表** 提出 ≤10 条候选，每条必须有：经济故事、输入字段、因果窗口、预测对象、为什么不是 V0.5/V0.6 重写。  
人审 → 写入 versioned Feature Library → Xavier 只评列表。

**禁止：** Worker 调模型；看见结果后再让模型“再想 20 个”；用模型改门槛去靠近 10%。

**顺序：** 最后。先有方向 2（以及可选方向 1）的合同和评价管道，AI 才有可挂载的库，否则会重新变成指标农场。

### 方向 6（保留，不排进 V0.7 实现）— Carry / 利率风险溢价

EURUSD、USDJPY 有利差。无利率序列则不能测。列入 BLOCKED。有数据后再开新 versioned family。不要用价格动量冒充 carry。

---

## 4. 数据需求 — Minimum Data Requirement

### 4.1 当前库存（不得夸大）

- 16 个合格 dataset：GOLD / EURUSD / USDJPY / OIL × M15 / H1 / H4 / D1  
- 每份 2000 根；`tick_volume` only；`real_volume=0`；有 `spread`  
- 无事件、无利率、无 IV、无 DXY、无跨品种对齐索引  
- 终端 Max. bars 限制：Data Layer 已记录。**V0.2 能否拉到更长历史 = UNKNOWN，必须实抓后才能说**

### 4.2 每个方向最低要求

| 方向 | 最低现在就能开实验？ | 最低数据 | 没有它会怎样 |
| --- | --- | --- | --- |
| 1 Transition | **能（仅 D1）** | 现有 4×D1 2000；更好是 ≥10 年 D1 | M15 上做转换 = 样本谎言 |
| 2 Cross-asset | **能（仅 D1，先做对齐）** | 现有 4×D1 + UTC 对齐表；更好加 DXY、≥10 年 | 不对齐就做相关 = 泄漏或同期相关 |
| 3A Vol sizing | 能（模块） | 现有 ATR/range 即可 | 不能叫 VRP |
| 3B True VRP | **不能** | 隐含波动或期权 | 禁止开实验 |
| 4 Time structure（时段） | **不能作为主证** | M15 ≥ 2 年（约 4–7 万根量级，视交易时段）或 H1 ≥ 3 年 | 用现有 2000 M15 会过拟合 |
| 4 Time structure（星期） | 勉强能 | 现有 D1；最多 1～2 条预注册 | 日历农场禁止 |
| 5 AI features | 取决于特征 | 与所提特征相同 | 无新字段就不要提事件/IV 特征 |
| 事件 | **不能** | 日期+类型+时区的日历（FOMC / NFP / EIA 最低） | 禁止用 LLM“回忆新闻”当事件 |
| 年化 10% 主证 | **现有 M15/H1 不能** | 可解释的多年样本 + 低换手书 | 见第 6 节 |

### 4.3 Data Layer V0.2（记录需求，本任务不实现）

已写在 `docs/DATA_LAYER_V0.1.md` 的 V0.2 清单里。V0.7 把它从“愿望”收成 **alpha 前置**：

1. **跨品种对齐索引**（可先对现有 2000 根 D1 做，不必须先加长）  
2. **更长历史**（若终端允许）：M15 / H1 优先；D1 能加长则加长  
3. 仍只读 MT5，仍禁止 `order_send`  
4. 新 `dataset_id`，不覆盖 `*-20260825-000001`  
5. 不把新抓的最近一段叫 Final OOS

对齐与加长是两件独立的事。  
**先对齐 D1，不必等加长成功。**  
加长失败（Max. bars）时，方向 2 / 1 仍可在 6.4 年 D1 上做；方向 4 时段主证暂停。

### 4.4 对“2000 根不足什么”的直接回答

| 问题 | 2000 根够不够 |
| --- | --- |
| 证明数据干净、合同能跑 | 够（已够） |
| 单品种短持有方向边 | 够测，且已测败 |
| 跨品种日度领先滞后 | D1 勉强够起步，不够宣称 10% |
| 状态转换 | D1 勉强；转换次数可能只有几十到一两百 |
| 时段结构 | 不够 |
| 事件研究 | 缺字段，不是根数问题 |
| 成本后年化 10% | 不够（M15/H1 无年化含义；D1 最好残留 0.23%） |

---

## 5. TradeMind V0.7 架构 — Alpha Research Framework

不要写代码。不要新建空目录充数。  
实现时必须 **复用** 已冻结管道：CausalView、windows、FDR、Windows 锁空间、Xavier `node_eval`、V0.6 成本/风险引擎。  
`ENGINE_VERSION` 的假设引擎保持 0.4。V0.7 是新合同，不是改旧结果。

```text
Hypothesis Generation
        ↓  (write-once HYP-xxxx, not HYP-0001)
Feature Library
        ↓  (versioned, causal, worker cannot add)
Model Evaluation
        ↓  (research / validation; cost; not p-value only)
Risk Evaluation
        ↓  (size / skip / DD; not a profit story by itself)
Experiment Registry
        ↓
  CANDIDATE or NO_EDGE / WEAK_EDGE
        ↓
  Final OOS = still DENIED
  MT5 = still unused
```

### 5.1 Hypothesis Generation

职责：把“想法”变成 **一条不可改写的预测主张**。

必须有：

- `hypothesis_id`（新号，禁止复用 HYP-0001）
- 经济故事（一句话）
- 输入字段与因果窗口
- 预测对象（哪一品种、哪一持有、什么目标）
- 明确 **不是** 哪条已失败方向
- 预注册哈希后才许计算

来源允许：人、或方向 5 的 AI 提议。  
来源不允许：看见 OIL D1 后再写一条“OIL 动量 hold=12”。

一次只激活一个新 family 的少量假设。禁止同时开五条方向的实现。

### 5.2 Feature Library

职责：可审计、可复算的特征定义，不是 notebook。

两层：

| 层 | 内容 | 状态 |
| --- | --- | --- |
| Frozen legacy | FD V0.1 / V0.5 state / V0.6 信号 | 只读，禁止重跑冒充新发现 |
| ALPHA_V07 | 转换指示、对齐后的跨品种滞后、时钟桶、（将来）事件标记 | 未实现 |

每条特征：`feature_id`、公式、因果边界、所需 dataset、缺失时 FAIL 而不是填 0。

跨品种特征必须声明对齐键。对齐失败 = 实验失败，不准 inner-join  silently 丢日期还叫稳健。

### 5.3 Model Evaluation

职责：回答“这个假设在成本后有没有可重复位移”，不是训练黑箱。

复用：

- research / validation 切分（Protocol 窗口）
- NEXT_BAR_OPEN + V0.6 成本（或同一成本的新 versioned 副本，禁止悄悄改 bp）
- 总收益、CAGR、DD、Sharpe、笔数、换手、最大单笔占比
- BH-FDR + 失败保留

新增评价对象（设计）：

- 转换事件研究（稀疏）
- 跨品种滞后回归 / 条件均值（先简单，不准一上来深度学习）
- 明确记录 **同期相关 vs 可交易滞后**（同期再高也是 NO_EDGE）

模型在 V0.7 的意思是 **预注册的映射**（线性、条件均值、状态机），不是可训练的大模型。  
若以后要训练，必须另开版本，且训练只在 research 窗。

程序级 CANDIDATE 门继续：成本后双窗为正、笔数门槛、DD、非单笔主导、**≥ 2 dataset**。  
CAGR ≥ 10% 仍不是通过条件。

### 5.4 Risk Evaluation

职责：把边变成可存活的仓位规则。独立计分，避免把“少做亏得少”写成 alpha。

复用：0.5% / 1% 风险、1.5×ATR 止损思路、杠杆 1×。

设计增加：

- 目标波动缩放（方向 3A）
- 宽点差禁开（已有，保持过滤身份）
- 将来：事件窗口禁开（无日历则不做）

输出必须能拆开：

```text
raw_signal_pnl
  vs
risk_adjusted_pnl
```

若 raw 不存在、只有 risk 之后变正，要标记 **PATH_DEPENDENT / SIZING_ONLY**，不得升 CANDIDATE。

### 5.5 Experiment Registry

职责：回答“我们测过什么、为什么失败、下一条为什么不是重复”。

复用 FD / V0.6 的 ranking + ledger 形态。新 registry 名：`ALPHA_DISCOVERY_V0.7`（实现时再建，本任务不建文件冒充已跑）。

每条记录：hypothesis、feature hash、data hash、eval hash、dataset 列表、状态、why、禁止事项引用。

查询问题必须能答：

1. 这个想法是不是 V0.6 同构？  
2. 用了哪些品种的 t 信息预测哪个品种的 t+1？  
3. 失败是成本、跨度、还是假设本身？

### 5.6 权威与集群

```text
Windows：生成/锁假设、锁特征名单、对齐索引、调度、回收、排名
Xavier：只读 job + 已锁定义，算，回传 lineage
LLM：只在 Windows，只在 Hypothesis Generation，不在 Worker
```

远程目录（实现时）：`/tmp/tm-alpha-discovery-v07`。  
不改 HYP-0001 `node_runner.py`。不改 8002–8005 sidecar。

### 5.7 明确不建的东西

- 新的简单策略族（TF/MR/MOM 再来一版）
- 空的 `research_engine/alpha/` 目录充数（实现第一个方向时再长出来）
- Final OOS 数据
- MT5 交易路径
- 为了 10% 改 V0.6 门槛

---

## 6. AI 如何参与

本地能力是 FACT：Windows Arc A770M + Qwen2.5-14B，V3.0 已冻结。Xavier 不做 LLM。

| 阶段 | AI 可以 | AI 不可以 |
| --- | --- | --- |
| 本文件（V0.7 设计） | 整理缺口、提出方向、写清楚失败模式 | 编造未跑的实验结果 |
| Hypothesis Generation | 按缺口表提议 ≤10 条特征/假设 | 自己写入 registry；自己改 hash |
| Feature Library | 提议公式草稿 | 在 Worker 上算“模型分”当特征 |
| Model / Risk Evaluation | 事后用数字写人话解读（已有网关模式） | 看见结果后改门槛、再生成一堆特征 |
| 交易 | 无 | 下单、改仓、锁 OOS |

纪律：

1. AI 输出必须落到一条可拒绝的假设，否则丢掉。  
2. 多重检验按 **人锁进库的条数** 计，不按模型内心想过的条数。  
3. 禁止用模型“解释”OIL D1 残留然后把它升格。  
4. 方向 5 未到实现顺序前，日常研究默认 **不用** 模型生成特征。

AI 的正确位置： **缩小搜索空间，不是扩大。**

---

## 7. 距离 10% 的路径

### 7.1 现在在哪

```text
治理地板          DONE
单品种短持有方向  EXHAUSTED / FAIL
成本后真实回测    DONE（V0.6），CANDIDATE=0
最好残留 CAGR     +0.23%  （约差 40×）
跨品种 / 转换     NOT STARTED
长历史 / 对齐     对齐未做；加长 UNKNOWN
Final OOS         DENIED
Paper / MT5       禁止
```

0.23% → 10% 不是“再扫一组参数”。  
即使方向 2 是真的，也 **不保证** 能到 10%。它只是当前最可能产生 **第一个 CANDIDATE** 的通道。  
没有 CANDIDATE，10% 问题非法。

### 7.2 必须按这个梯子走

```text
1. 本设计（V0.7）                              ← 现在
2. D1 跨品种对齐（Data 能力，不是策略）
3. 只开方向 2 的 versioned 假设（少量，预注册）
4. 用 V0.6 成本/风险评价（持有按日）
5. 若 NO_EDGE：保留失败，不要加策略
6. 若 WEAK_EDGE：只允许加方向 1（转换）或 3A（缩放），仍不准调参
7. 若出现程序级 CANDIDATE：再问组合与跨度是否撑得起年化
8. 同时推进 Data V0.2 加长 M15/H1（给方向 4 和将来 10% 主证）
9. Final OOS / paper / MT5 = 更后面，本阶段禁止
```

### 7.3 到 10% 还缺的三块，一块都不能用叙事代替

| 块 | 现在 | 没有它 |
| --- | --- | --- |
| 可重复边（CANDIDATE） | 0 | 没有 10% 可谈 |
| 足够年化的样本 | 仅 D1 ~6.4 年勉强 | M15 上的 10% 是假的 |
| 成本后仍活的换手 | V0.6 短持有已死 | 高频边会被 30bp+spread 杀死 |

杠杆不加。1× 下要从 0.23% 走到 10%，必须是 **边变大或边变稳**，不是把风险分数从 1% 调到 10%。

### 7.4 下一阶段唯一推荐

**不要同时实现五个方向。**

下一最小实现（需另一次明确批准，本任务不做）：

1. 只读四条 D1，做 UTC 对齐索引（新 Data 能力或 V0.7 框架的第一刀）  
2. 预注册 2～3 条跨品种滞后假设（方向 2）  
3. 用已有成本/风险引擎评价  
4. 无论输赢都写入新 registry  

并行但独立：尝试 Data Layer V0.2 加长；失败就记录 Max. bars，不阻塞方向 2。

不要：再写一套 Trend/MR/Momentum。不要：MT5。不要：Final OOS。不要：为 10% 改规则。

---

## 8. 本任务交付清单

| 项 | 状态 |
| --- | --- |
| 为什么 V0.6 失败 | 第 1 节 |
| Alpha Coverage Matrix | 第 2.1 节 |
| 未来赚钱方向 | 第 3 节（5 + 1 保留） |
| 数据需求 | 第 4 节 |
| AI 如何参与 | 第 6 节 |
| 距离 10% 路径 | 第 7 节 |
| 框架设计 | 第 5 节 |
| 代码 / 新实验 / 旧实验改写 | **未做（禁止）** |

**V0.7 状态：DESIGN ONLY。**  
未实现。未跑 Xavier。未产生新 ranking。  
旧实验哈希与 14:11 文件必须保持不动。
