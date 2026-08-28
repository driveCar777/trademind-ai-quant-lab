# Alpha Discovery Operating System V0.7.1

Design only. No code. No experiment. No change to locked contracts.

Long-run capital target: **cost- and risk-adjusted annualized return ≥ 10%**.  
This file does not claim a CANDIDATE, a book, or 10%.  
It is the operating map: what kinds of alpha exist, what TradeMind already killed, what is still unknown, and the only next experiment that is allowed to start later.

Parent: `docs/research_engine/ALPHA_DISCOVERY_V0.7_PLAN.md`  
Do not collapse versions: V0.7 = audit. V0.7.1 = operating system. V0.8 = Cross Asset experiment (**FROZEN 2026-08-26**, `NO_CANDIDATE`).

Read-only: HYP-0001 14:11, FD V0.1, V0.5, V0.6, Data Layer V0.1, Protocol V0.3.

---

## 0. Operating verdict

```text
V0.6          NO PROGRAM CANDIDATE
V0.7 audit    search space exhausted on single-name short-hold direction
V0.7.1        taxonomy + coverage + 12-month queue + V0.8 contract (paper)
V0.8          NO_CANDIDATE (3/3 FALSIFIED; FDR 0/3; do not expand this family)
```

Largest unknowns that can still become money:

| unknown | can start on disk today? |
| --- | --- |
| Cross Asset | YES — after D1 alignment, no new bars required |
| Regime Transition | YES — D1 only |
| Risk Alpha | PARTIAL — sizing module yes; true VRP no |
| Portfolio Alpha | NO as a first experiment — needs a surviving sleeve |

**Planning superseded by `ALPHA_COVERAGE_MAP_V1.md` + `TRADEMIND_ALPHA_ROADMAP_12M.md`.**  
V0.8 has been executed and frozen (`NO_CANDIDATE`). Next contract (not executed): Regime Transition V0.9.

---

## 1. Alpha 地图 — Taxonomy V1

A class is a **source of return**, not a strategy folder.  
One class may later have many hypotheses. V0.8 may open only Relative Value, and only three claims.

### 1.1 Directional

**收益来源：** 同一品种、同一序列的过去，预测同一品种的未来方向或收益。

**需要数据：** 单品种 OHLCV + spread。现有 16 份 2000 根已够做否证。

**已有覆盖：**

- HYP-0001 streak=3 → 下一根（WEAK_SUPPORT，不是书）
- FD V0.1 动量 / 反转 / 突破 / 效率 / tick 量 / spread / 有限 MTF（`NO_USEFUL_FACTORS_FOUND`）
- V0.5 状态内下一根草图（`NO_USEFUL_STRATEGIES_FOUND`）
- V0.6 TF-BRK20 / MR-Z20 / MOM-DIR（程序级 CANDIDATE=0）

**未覆盖：** 几乎没有值得再挖的同构。未测的是“别的信息”，不是“另一个 N”。

**实验成本：** 低。管道齐。再开一次的成本是 **浪费多重检验与时间**。

**赚钱可能性：** **低。** 三种合同已杀。OIL D1 动量残留 CAGR +0.23%，不是路。

**OS 状态：** FAILED（作为赚钱搜索）

### 1.2 Relative Value

**收益来源：** 品种 A 在 t 的已实现信息，改变品种 B 在 t+1 的条件期望。  
包括美元代理→黄金/原油、两资产残差。不是四条曲线等权。

**需要数据：** ≥2 个品种、同一时钟、可对齐、滞后严格因果。现有四条 D1 重叠约 2020-04-01 → 2026-08-25。缺对齐索引。无 DXY。

**已有覆盖：** FD `FAM-FD-XASSET-0001` = DRAFT，从未计算。V0.6 组合是同品种三袖套，不是相对价值。

**未覆盖：** 全部可交易滞后。同期相关（不能交易）也未正式分开记录。

**实验成本：** 中。主要是对齐层 + 三条预注册假设。不必先加长 M15。

**赚钱可能性：** **当前最高（在可做集合里）。** 经济通道真实，样本已在盘上，从未测过。  
仍不保证 10%。只保证这是下一刀该砍的未知。

**OS 状态：** UNKNOWN（可起步）

### 1.3 Regime

**收益来源：** 市场状态的 **变化**（进入/离开趋势、波动切换），不是“处于 TREND_STRONG 就做突破”。

**需要数据：** 已有 SMA20/50、ADX14、ATR 状态轴够用。转换是稀疏事件，D1 ~6.4 年勉强，M15 一个月不够。

**已有覆盖：** 状态 **水平** 当过滤器（V0.5 / V0.6）。HIGH_VOL / WIDE 禁开。

**未覆盖：** `ENTER_TREND` / `EXIT_TREND` / `VOL_SHOCK` 作为信号本身。

**实验成本：** 中低。状态代码已有。难在稀疏样本与多重检验。

**赚钱可能性：** **中。** 换手低，成本不容易先杀死。排在 Cross Asset 之后，避免同时开两条。

**OS 状态：** UNKNOWN（可起步，D1）

### 1.4 Risk

**收益来源分两级，禁止混写：**

| 级 | 收益来源 | 状态 |
| --- | --- | --- |
| 4A 风险模块 | 不预测涨跌。用已实现波动缩放或禁开，让别的边活下来 | 可设计 |
| 4B 真风险溢价 | 收 IV−RV、卖波动、利率 carry | 无 IV / 无利率 |

**需要数据：** 4A = 现有 ATR/range。4B = 期权或利率序列。

**已有覆盖：** FD 波动→`future_abs_return` 五条 INCONCLUSIVE（聚集，不是方向）。V0.6 DEF 空仓 0 收益。0.5%/1% 风险、1× 杠杆、ATR 止损已是执行规则。

**未覆盖：** 目标波动缩放是否能保住一条真边（要先有边）。真 VRP。Carry。

**实验成本：** 4A 低（模块）。4B 无限（无数据）。

**赚钱可能性：** 4A **中（附属）**，单独 **低**。4B **未知且不可测**。  
禁止把“少做少亏”写成 Risk Alpha CANDIDATE。

**OS 状态：** 4A PARTIAL / FAILED as standalone；4B DATA BLOCKED

### 1.5 Portfolio

**收益来源：** 多个 **弱但不全相关** 的边合成一条权益曲线。分散的是信息，不是同一 K 线上的三个指标。

**需要数据：** 先有 ≥2 个可交易袖套，再有对齐时钟（若跨品种）。

**已有覆盖：** V0.6 同品种 TF+MR+MOM 等权，D1 研究收益全负（GOLD −4.1%，EURUSD −9.8%，USDJPY −5.1%，OIL −1.0%）。

**未覆盖：** 跨品种、跨家族、风险平价或波动目标合成。

**实验成本：** 在没有袖套时开组合 = 高浪费。

**赚钱可能性：** **现在低，将来中高。** 10% 几乎一定出在这一层，但 **现在没有输入**。先做 Relative Value，再谈书。

**OS 状态：** FAILED（同品种合成）；UNKNOWN（真跨品种书，被袖套挡住）

### 1.6 地图一览

```text
Directional ──────── FAILED（短持有单品种）
Relative Value ───── FAILED  ← V0.8 NO_CANDIDATE（3/3 FALSIFIED；禁止扩家族）
Regime ───────────── UNKNOWN  ← 下一刀 V0.9（若另批）
Risk 4A ──────────── 模块，不是第一边（无袖套则跳过）
Risk 4B ──────────── DATA BLOCKED
Portfolio ────────── 等袖套
Event / Carry / IV ─ DATA BLOCKED
Time / Session ───── DATA BLOCKED as 主证（M15 太短）
```

---

## 2. 当前缺口 — Coverage Matrix

状态只允许：

| 码 | 意思 |
| --- | --- |
| DONE | 能力在，可用，不是“有边” |
| FAILED | 已按锁定合同寻找该边，无程序级 CANDIDATE |
| UNKNOWN | 未测，数据够起步 |
| DATA BLOCKED | 诚实实验现在做不了 |

### 2.1 能力（基础设施）

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 不可变 OHLCV + spread | DONE | Data Layer V0.1，16×2000 |
| 资格 / 就绪 / 因果窗口 | DONE | Qual V0.1 / Ready V0.2 / Protocol V0.3 |
| 四 Xavier 执行 | DONE | FD / V0.6 / V0.8 实跑 |
| NEXT_BAR_OPEN + 5bp + 10bp + 1× | DONE | V0.6 引擎 |
| 假设 / FDR / 失败保留 | DONE | HYP-0001 / FD ledger |
| Final OOS | DONE as 拒绝 | `FINAL_OOS_LOCKED=false`，访问 raise |
| 跨品种对齐时钟 | DONE | V0.8 `tm-align-D1-XA-20260826-000001`，1993 日 |
| 更长 M15/H1 | DATA BLOCKED | 各约 1 个月 / 4 个月 |
| DXY / 利率 / IV / 事件日历 | DATA BLOCKED | 磁盘无 |
| `real_volume` | DATA BLOCKED | 全 0，只用 tick_volume |

### 2.2 Alpha 类

| 类 | 状态 | 依据 |
| --- | --- | --- |
| Directional 单品种短持有 | FAILED | HYP-0001 + FD + V0.5 + V0.6 |
| Directional 低换手多日（新合同） | UNKNOWN | 未开；不要用调 OIL hold 冒充 |
| Relative Value 可交易滞后 | FAILED | V0.8 三条 FALSIFIED；不要扩家族 |
| Regime 状态水平过滤 | FAILED | V0.5 / V0.6 无 CANDIDATE |
| Regime 状态转换 | UNKNOWN | 从未用 Δstate |
| Risk 空仓叠加当利润 | FAILED | DEF 0 收益 |
| Risk 目标波动缩放 | UNKNOWN | 无宿主边，未测 |
| Risk 真 VRP / carry | DATA BLOCKED | 无 IV / 利率 |
| Portfolio 同品种弱策略 | FAILED | V0.6 四条 D1 全负 |
| Portfolio 跨品种书 | UNKNOWN | 无袖套 + 无对齐 |
| Time 时段 | DATA BLOCKED | M15 ~2026-07-24/27 → 2026-08-25 |
| Time D1 星期（极少条） | UNKNOWN | 6.4 年 D1 可极窄预注册 |
| Event | DATA BLOCKED | 无日历 |
| AI 特征 | UNKNOWN | 有 LLM；未进合同；排最后 |

### 2.3 V0.7 点名的四大未知

| 未知 | 矩阵状态 | 缺什么 | 何时做 |
| --- | --- | --- | --- |
| Cross Asset | FAILED | V0.8 已跑；`NO_CANDIDATE` | 禁止扩成 10 条 |
| Regime Transition | UNKNOWN | 转换合同 | **下一实现（若另批）** |
| Risk Alpha | 4A UNKNOWN / 4B BLOCKED | 先有边，或先有 IV | 附属；禁止单独找 10% |
| Portfolio Alpha | FAILED / UNKNOWN | 先有 ≥2 袖套 | 有 CANDIDATE 之后 |

### 2.4 缺口一句话

治理、单品种短持有、以及 **本锁的三条跨品种滞后 RV** 已经结束。  
钱的缺口不在“再扫 XA”，在 **转换（未测）**、**真组合（无输入）**、**跨度与另类数据（挡住）**。

---

## 3. 未来 12 个月研究路线

排序键：收益潜力 × 现在能否做 / 实现难度 / 数据需求。  
一人 + AI。一次只开一个实现模块。没有冻结结论，不准开下一个 alpha 类。

### 3.1 队列（只这一张）

| 序 | 窗口 | 模块 | 潜力 | 难度 | 数据 | 为什么是这个顺序 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 本文件 | V0.7.1 OS | — | — | — | 锁地图与 V0.8 合同 |
| 1 | 月 1 | Data：四条 D1 UTC 对齐（能力，不是策略） | — | 低 | 现有 D1 | **DONE**（1993 日 pack） |
| 2 | 月 1–2 | **Cross Asset V0.8**（恰好 3 假设） | 高 | 中 | 现有 D1 | **DONE / FAILED**（`NO_CANDIDATE`） |
| 3 | 月 2 | 只读结论：CANDIDATE / WEAK / NO_EDGE | — | — | — | **DONE**：`NO_CANDIDATE`；禁止加假设 |
| 4 | 月 3 | **仅当 V0.8 有结论后**：Regime Transition V0.9（少量） | 中 | 中 | 现有 D1 | 第二条未知；不与 V0.8 并行 |
| 5 | 月 3–4 | Risk 4A 挂在 **已存活袖套** 上 | 中（附属） | 低 | 现有 | 无袖套则跳过 |
| 6 | 月 4–6 | Data Layer V0.2 加长（试抓，失败记 Max. bars） | 基础设施 | 中 | MT5 只读 | 给时段与年化主证；**不阻塞** 已完成的 V0.8 |
| 7 | 月 6–7 | Portfolio V1：只合成 **已过门** 袖套 | 中高（有输入时） | 中 | 对齐 D1 | 无袖套则不做 |
| 8 | 月 7–9 | Time Structure（仅当 V0.2 长 M15/H1 成功） | 中 | 中 | 新历史 | 现有 2000 M15 禁止当主证 |
| 9 | 月 9–10 | Event（仅当有日历文件） | 未知 | 中 | 新表 | 无日历则整季跳过 |
| 10 | 月 10–12 | 若仍无 CANDIDATE：停开新策略，只补数据或停 | — | — | — | 禁止为 10% 改规则 |
| 11 | 月 12 以后 | Final OOS / paper / MT5 | — | — | — | **本年内默认禁止** |

Carry / 真 VRP / DXY：有数据再插入队列，另开 versioned family。不预占月份。

### 3.2 月度杀停规则

- V0.8 三条全 NO_EDGE → 不扩成 10 条跨品种。进入 V0.9 或停。  
- V0.8 只有 OIL 一边过门 → WEAK_EDGE，与 V0.6 相同纪律，不调阈值。  
- V0.2 加长失败 → 时段主证取消，D1 路线继续。  
- 任何时候不准回头扫 RSI / MA / hold=5。

### 3.3 12 个月成功长什么样（诚实）

**好的一年：** 出现第一个程序级 CANDIDATE（多半来自相对价值或转换），组合只是锦上添花，10% 仍可能达不到。  
**合法的一年：** 全部 UNKNOWN 变成 FAILED，数据缺口写清。这也是进度。  
**失败的一年：** 为了报表改门槛、或在 1 个月 M15 上宣布年化 10%。

---

## 4. Cross Asset Alpha V0.8（只设计）

实现未开始。下列字段 **预注册意图**，批准实现时再写成 JSON。  
现在写 JSON 或跑数 = 违规。

家族血统：`FAM-FD-XASSET-0001`（FD DRAFT）。不要另起同义家族。  
新假设号：**HYP-XA-0001 / 0002 / 0003**。禁止碰 HYP-0001。

### 4.1 硬限制

- 恰好 **3** 条假设，不准第 4 条。  
- 只做 **D1**。M15/H1/H4 不作主证（跨度不够）。H4 最多事后诊断，且不算进 FDR 主族。  
- 只做 **t → t+1**。禁止扫领先 2/3/5 日。  
- 持有 **1 根 D1**，NEXT_BAR_OPEN 进、下一根开盘出（或持有期满的下一开盘）。禁止 close 成交。  
- 预测符号 **经济单向预注册**。失败就失败，禁止翻号。  
- 阈值只冻一次：预测变量在 **对齐后 RESEARCH 窗** 的分位，应用到 VALIDATION。  
- Windows 锁名单。Xavier 只评这三条。  
- Final OOS 仍 DENIED。

### 4.2 数据合同

**源（只读，不改）：**

| logical | dataset_id | start | end |
| --- | --- | --- | --- |
| GOLD | `tm-market-GOLD-D1-20260825-000001` | 2020-03-26 | 2026-08-25 |
| EURUSD | `tm-market-EURUSD-D1-20260825-000001` | 2020-04-01 | 2026-08-25 |
| USDJPY | `tm-market-USDJPY-D1-20260825-000001` | 2020-04-01 | 2026-08-25 |
| OIL | `tm-market-OIL-D1-20260825-000001` | 2020-03-24 | 2026-08-25 |

**对齐包（实现时新建，不覆盖上面四份）：**

- `dataset_id` 例：`tm-align-D1-XA-20260826-000001`  
- 键：UTC 日历日（D1 `timestamp_utc` 的日期）。  
- 方法：inner-join。某日缺任一 **本假设所需** 品种 → 丢该日，计入 `dropped_days`。禁止填 0。  
- 四品种全集重叠预期从 **2020-04-01** 起。  
- hash：对齐表 SHA256 + 四个 parent dataset hash。  
- `FINAL_OOS` 切片可在表上划出，**访问仍 raise**。

**共享窗口（必须共用对齐日历，禁止四文件各自 70/15/15）：**

```text
aligned dates sorted
  RESEARCH     = first 70%
  VALIDATION   = next 15%
  FINAL_OOS    = last 15%   ACCESS DENIED
```

窗口在看到收益 **之前** 冻结。

**OIL 极端日：** Qualification 要求人工看过极端收益。主检验 **不删** 极端日。允许一份 winsorize 1% 的 **诊断表**，诊断不得当通过条件。

**代理声明：** USDJPY、EURUSD 是不完美美元代理。合同禁止写“DXY”。

### 4.3 三条假设（锁死）

**HYP-XA-0001 — JPY proxy → next GOLD**

```text
If USDJPY D1 return[t] is in the top third of RESEARCH USDJPY returns,
then GOLD D1 open-to-open return[t+1] is negative after cost.
```

经济：USDJPY 升 ≈ 美元相对日元升，黄金承压。  
空：该条件期望 = 无条件下一根 GOLD（成本后 ≤ 0 或符号反）。  
不是：GOLD 自己的动量（V0.6 / HYP-0001）。

**HYP-XA-0002 — EUR proxy → next GOLD**

```text
If EURUSD D1 return[t] is in the top third of RESEARCH EURUSD returns,
then GOLD D1 open-to-open return[t+1] is positive after cost.
```

经济：EURUSD 升 ≈ 美元弱，黄金倾向涨。  
若 0001 过、0002 反号，记 **代理不一致**，不得只留下好看的一条当 CANDIDATE。

**HYP-XA-0003 — 双代理美元升 → next OIL**

```text
Dollar-up day := USDJPY return[t] > 0 AND EURUSD return[t] < 0
(both vs 0, not vs a scanned threshold).
Then OIL D1 open-to-open return[t+1] is negative after cost.
```

经济：两个代理同时说美元升，风险资产原油承压。  
用 0 而不是再扫分位，避免第 3 条变成参数。  
若 dollar-up 日太少（RESEARCH < 8 笔），该假设记 INSUFFICIENT_OCCUPANCY，不得改定义凑笔数。

### 4.4 执行、成本、风险

与 V0.6 **同一数字**，禁止为跨品种改便宜：

| 项 | 值 |
| --- | --- |
| 成交 | NEXT_BAR_OPEN |
| close 成交 | FORBIDDEN |
| 每边 | 半价差（已锁 broker points 规则）+ 5bp + 10bp |
| 风险 | 0.5% 权益 / 笔（主）；1% 只作并列报告，**不**另开假设号 |
| 杠杆 | ≤ 1× |
| 止损 | 1.5× 信号日 ATR，否则持有 1 日到下一开盘 |
| 宽点差 | FRICTION_WIDE 禁开（沿用 V0.6 规则） |
| 同时持仓 | 每条假设单独一本账，V0.8 不做三假设合成 |

1% 风险不是第 4、5、6 条假设。

### 4.5 指标（先锁，后看数）

每条假设、每个窗必须出：

| 类 | 字段 |
| --- | --- |
| 交易 | `trade_count` `win_count` `turnover` `occupancy` `dropped_days` |
| 收益 | `total_return` `cagr`（D1 才解释） |
| 风险 | `max_drawdown` `sharpe` `max_trade_share` |
| 成本 | `cost_paid` |
| 诊断 | 同期相关（t 对 t，**不算通过**） |

CAGR ≥ 10% **不是** 通过条件。

### 4.6 验证与分级

沿用 V0.6 门，改一处：dataset 改成 **target 品种的对齐 D1**。

单假设过门（全要）：

- RESEARCH 与 VALIDATION `total_return` > 0（成本后）  
- 符号与预注册方向一致  
- RESEARCH 笔数 ≥ 8，VALIDATION ≥ 4  
- RESEARCH DD ≥ −25%，VALIDATION ≥ −30%  
- `max_trade_share` ≤ 50%  
- 同期相关再强也不替代滞后收益

程序级（家族）CANDIDATE：

```text
至少 2 / 3 条假设过单假设门
```

仅 0001+0002 过而 0003 失败：两条都打 GOLD，算 **1 个被预测品种的双代理一致**，记 WEAK_EDGE，**不算** 程序级 CANDIDATE（与 V0.6“≥2 dataset”同一精神）。  
0001（或 0002）+ 0003 过：两个 target（GOLD 与 OIL）→ 可以升程序级 CANDIDATE。  
只有 OIL：WEAK_EDGE。禁止调 0003 定义。

FDR：主族 m=3（三条假设）。诊断、winsor、H4、1% 风险副本不进 m。  
`NO_EDGE` / `WEAK_EDGE_ONLY` 合法。

### 4.7 预注册清单（实现日必须落盘）

实现批准后、看收益前写入（本任务不写这些文件）：

1. 本文件哈希  
2. 三条假设 JSON  
3. 对齐包 manifest + hash  
4. 共享窗口 JSON  
5. 成本 / 风险 / 门（抄本节）  
6. `stopping_rule`: 一轮 research + 一轮 validation，不重调  
7. `FINAL_OOS_ACCESS: DENIED`

### 4.8 Xavier 草图（实现时）

| 节点 | 算 |
| --- | --- |
| Xavier-01 | HYP-XA-0001 |
| Xavier-02 | HYP-XA-0002 |
| Xavier-03 | HYP-XA-0003 |
| Xavier-04 | 重算 0001 做 content-hash 交叉 |

每节点拿到 **同一对齐包**，不是只拿 GOLD。Worker 不得增假设。远程目录建议：`/tmp/tm-cross-asset-v08`。

Windows：对齐、锁、派、收、排名。

### 4.9 明确失败模式（先写）

- 只有同期相关、滞后没有 → NO_EDGE  
- 只在 2020 OIL 极端段 → 通不过 `max_trade_share` 或 WEAK  
- 0001/0002 符号与预注册相反 → NO_EDGE，不准改故事  
- 对齐丢太多日 → 实验 FAIL（数据），不是 NO_EDGE

---

## 5. 数据路线 — Data Layer V0.2（只设计）

V0.1 仍冻结。V0.2 新 `dataset_id`，禁止覆盖 `*-20260825-000001`。仍只读 MT5，仍禁止 `order_send`。  
Max. bars：**UNKNOWN**，必须实抓后记。失败不是改合同去凑 10%。

### 5.1 为什么还要数据

| 目的 | 现有 2000 根 | V0.2 要什么 |
| --- | --- | --- |
| 跑 V0.8 | D1 够起步 | **对齐**（软件，可先做） |
| 谈年化 10% | D1 ~6.4 年勉强；M15/H1 无年化含义 | 更长、可解释的年数 |
| 时段 / 伦敦纽约 | M15 ~1 个月 | 多年 M15 或 H1 |
| 转换样本 | D1 转换可能偏少 | 更长 D1 |
| 真 VRP / carry / 事件 | 无字段 | 新源，不是加长 K 线 |

Tick、多 broker、Parquet、自动补洞：V0.1 已列为愿望。**不进 V0.8 关键路径。**

### 5.2 要哪些历史、为什么、多久

**A. 对齐（先做，可不加长）**

- 对象：现有四条 D1  
- 为什么：V0.8 没有它对不齐的 t / t+1  
- 多久：实现对齐能力的几天，不是几年行情

**B. 加长 D1（值得，不阻塞 V0.8）**

- 目标：每品种 **至少 10 年** 或终端能给的最长  
- 约 2500–3500 根（交易日）  
- 为什么：6.4 年只有一个 2020 原油体制；10% 至少要跨两个体制  
- 逻辑品种：仍是 GOLD / EURUSD / USDJPY / OIL  
- 可选：若 Ava 有 **DXY 或 USDX 类** 符号，另开 dataset，不冒充现有代理

**C. 加长 H1**

- 目标：**≥ 3 年**（约 1.5–2 万根量级，视周末缺口）  
- 为什么：V0.6 的 H1 只有约 2026-04 → 2026-08；转换与执行诊断需要多个季度  
- 不作 V0.8 主证

**D. 加长 M15**

- 目标：**≥ 2 年**（约 4–7 万根量级）  
- 为什么：时段结构；现有约 2026-07-24 → 2026-08-25  
- 2 年仍不够单独证 10%，但够否证“只有某一个星期有效”  
- 终端若 Max. bars < 目标：记 `history_shortfall`，不做假年化

**E. 加长 H4**

- 目标：能接到与 D1 重叠的更长段（现有已约 15 个月）  
- 优先级低于 D1/H1/M15

**F. 明确不要当 V0.2 必须项**

- Tick  
- 股票与公司行为  
- 自动 gap 修复  
- 把最新一段叫 Final OOS

**G. 另类表（不是 MT5 K 线，可并行设计）**

| 表 | 最低 | 挡住谁 |
| --- | --- | --- |
| 事件日历 UTC | FOMC / NFP / EIA | Event |
| 利率 | 美元短端即可起步 | Carry |
| IV | GOLD 或原油隐含波动 | 真 VRP |

无这些表就不开那一类。禁止 LLM 回忆新闻。

### 5.3 V0.2 阶段切法

```text
V0.2a  对齐现有 D1          ← V0.8 前置
V0.2b  试抓更长 D1/H1/M15   ← 与 V0.8 评价并行可，不改 V0.8 源
V0.2c  可选符号（DXY）      ← 另 dataset
V0.2d  另类表               ← 另合同
```

V0.8 主源必须仍是 `*-20260825-000001` 的对齐包，避免“一边抓数一边改样本”。

### 5.4 最短回答

要什么：对齐 +（若终端给）更长 D1/H1/M15。  
为什么：跨品种要齐时钟；10% 和时段要年，不要月。  
多久：对齐立刻；加长能抓多少算多少，目标 10 年 D1 / 3 年 H1 / 2 年 M15。

---

## 6. 年化 10% 路径

### 6.1 现在的距离（FACT）

最好锁定残留：OIL D1 动量，CAGR **+0.23%**，约差 **40×**。  
程序级 CANDIDATE：**0**。  
没有 CANDIDATE，10% 问题非法。

### 6.2 梯子（不得跳）

```text
OS 地图（本文件）
    → D1 对齐
    → V0.8 三条相对价值（成本后）
    → 有 ≥2 个 target 或停 / 转 V0.9
    → 风险模块只挂存活袖套
    → 组合只合成存活袖套
    → 更长历史后才谈年化是否像 10%
    → Final OOS（另批）
    → paper
    → MT5 demo
    → 真资金
```

1× 杠杆。禁止把风险从 1% 调到 10% 来“达到”10%。  
短持有 + 30bp+spread 已证明会先吃光边。V0.8 持有 1 日，仍必须付成本。

### 6.3 10% 仍可能失败的合法原因

- 相对价值只有同期相关  
- 6–10 年里边太小，成本后复利不够  
- 只有一个品种、一个体制  
- 永远没有 IV/利率，风险溢价整层缺失  

这些必须能写进 registry，而不是改门。

---

## 7. 禁止事项

1. 写 V0.8 / V0.2 业务代码（除非另一次明确批准）  
2. 跑新实验、写新 ranking 冒充完成  
3. 修改 HYP-0001、14:11、FD V0.1、V0.5、V0.6、不可变 bars  
4. 增加第 4 条跨品种假设，或扫领先期 / 持有期 / 分位  
5. 再开 RSI / MA / Donchian / z20 / 短持有动量  
6. 把 OIL D1 残留升 CANDIDATE  
7. 把空仓、缩放、少交易写成 Risk CANDIDATE  
8. 在没有袖套时做 Portfolio 挖参  
9. 用现有 2000 根 M15 宣称时段边或年化 10%  
10. 把 USDJPY/EURUSD 写成 DXY  
11. 用 LLM 生成新闻/事件序列  
12. 锁 Final OOS、paper、`order_send`、自动交易  
13. 为靠近 10% 改成本、杠杆、门槛  
14. 并行实现 Cross Asset + Regime + Portfolio  

---

## 8. 本任务交付

| 节 | 内容 |
| --- | --- |
| 1 | Alpha 地图（五类来源） |
| 2 | 覆盖矩阵（DONE / FAILED / UNKNOWN / DATA BLOCKED） |
| 3 | Cross Asset V0.8（3 假设 + 合同） |
| 4 | 数据路线 V0.2 |
| 5 | 10% 路径 |
| 6 | 禁止事项（第 7 节） |
| 12 个月队列 | 第 3 节 |

代码：无。实验：无。旧合同：未改。

**V0.7.1 状态：DESIGN ONLY。**  
下一实现许可应只写：`V0.2a 对齐 + V0.8 三条假设`。
