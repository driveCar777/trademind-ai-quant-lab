# Alpha Priority Ranking V1

Design only. 2026-08-26.  
Scoring is declared **before** any new PnL. Not a feeling. Not a code change.

Parents: `ALPHA_COVERAGE_MAP_V1.md`, `DATA_CAPABILITY_MATRIX_V1.md`.

---

## Executive Summary

在「现有磁盘 + 禁止偷看 + 禁止跳级」约束下，下一刀不是 ML，不是另类数据，不是再扫跨品种。

**Top 1 可实施：Regime Transition（Δstate，D1，恰好 3 条假设）。**

Top 5 里没有 Carry / IV / 新闻。那些分数被数据门打成 0。

---

## Current Evidence

已失败方向的 Expected Edge 不再给高分：同构重复的边际信息 ≈ 0。  
V0.8 证明「听起来很宏观」也可以成本后全灭。机制强度 ≠ 已验证边。

成本教训（V0.6 / V0.8）：占用率高 + 持有 1 根 + 30bp+spread ≈ 先死。  
转换事件稀疏，反而可能活过成本。这是 **Cost Survivability** 给转换加分的唯一理由。

---

## 1. 评分模型（锁死）

每个来源五维，整数 **1–5**。

| 维 | 符号 | 5 | 1 |
| --- | --- | --- | --- |
| Expected Edge Potential | E | 若机制为真，有机会贡献长期 ≥10% 的一层 | 即使为真也只是噪声级 bps |
| Data Availability | D | 磁盘已有且跨度够主证 | 缺关键字段或跨度假问题 |
| Statistical Testability | T | 可预注册、可计 n、可 FDR、可拒绝 | 特征无限、稀疏到无法检验、或必泄漏 |
| Cost Survivability | C | 低换手 / 多日持有，成本不先杀死 | 次日或日内高占用 |
| Market Mechanism Strength | M | 有风险转移 / 约束 / 补偿故事 | 纯技术同构 |

```text
raw = E × D × T × C × M          # max 3125
if D <= 1: rank_score = 0        # hard gate: DATA BLOCKED
if class is FAILED_isomorph: E := min(E, 2), M := min(M, 2)
if Decision 043 forbids expansion this quarter: implementable = NO
```

**Implementable** = 本季允许写成合同并（另批后）执行。  
`rank_score = 0` 或 `implementable = NO` 的项不进 Top 5。

禁止：看完分数再改某一维把宠儿抬上去。本表一次写死。

---

## 2. 打分表

| 来源 | E | D | T | C | M | raw | score | implementable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Regime Transition（Δstate） | 4 | 5 | 4 | 4 | 4 | 1280 | **1280** | YES — 下一合同 |
| D1 极窄日历（星期/周末间隙） | 2 | 5 | 3 | 4 | 2 | 240 | **240** | YES — 第二，极少条 |
| 被动多资产基准（非 alpha） | 2 | 5 | 5 | 5 | 2 | 500 | 500* | YES as **baseline only** |
| 已实现 vol 时机（独立农场） | 3 | 5 | 3 | 3 | 3 | 405 | 405† | NO this quarter（并入 V0.9 VOL_SHOCK） |
| 跨品种残差（新家族） | 3 | 4 | 3 | 3 | 3 | 324 | 324 | NO this quarter（043：先不扩 RV） |
| 低换手方向（新机制） | 3 | 5 | 3 | 3 | 2 | 270 | 270 | 仅当机制≠均线/动量 |
| Data V0.2 加长 | — | — | — | — | — | infra | infra | YES as **infra**，不是 alpha |
| ML / LLM 宏观信号 | 3 | 3 | 2 | 2 | 2 | 72 | 72 | 后置 |
| Portfolio 真组合 | 4 | 2 | 3 | 4 | 3 | 288 | 288 | SLEEVE BLOCKED |
| 同构动量/回归/突破 | 2 | 5 | 4 | 2 | 1 | 80 | 80 | NO（FAILED） |
| V0.8 同构跨品种 | 2 | 4 | 4 | 1 | 2 | 64 | 64 | NO（FAILED + 043） |
| Intraday seasonality | 3 | 1 | 2 | 1 | 3 | 18 | **0** | NO |
| Liquidity premium（真） | 3 | 1 | 2 | 3 | 3 | 54 | **0** | NO |
| Carry | 4 | 1 | 4 | 5 | 5 | 400 | **0** | NO |
| 真 VRP | 4 | 1 | 3 | 4 | 5 | 240 | **0** | NO |
| Event driven | 3 | 1 | 3 | 3 | 4 | 108 | **0** | NO |
| Alternative data | 3 | 1 | 2 | 3 | 3 | 54 | **0** | NO |

\* 被动基准分数高是因为它 **可测、低成本、数据够**。它不是预测边。只用来回答「无条件持有四条 D1 离 10% 多远」。禁止把 2020–2026 黄金牛市写成 Candidate。

† Vol 时机若再开独立农场，会与 V0.9 的 `VOL_SHOCK` 双重检验。本季并入，不另开。

---

## 3. Top 5 下一研究方向（可实施）

| 序 | 方向 | score | 为什么是这个序 | 不是什么 |
| ---: | --- | ---: | --- | --- |
| 1 | **Regime Transition V0.9** | 1280 | 唯一「未测 + 数据够 + 机制与已败方向不同 + 换手可能更低」 | 不是再当 TREND_STRONG 做突破 |
| 2 | **D1 日历结构（极少条）** | 240 | 数据够；机制弱；必须极窄预注册 | 不是扫 20 个星期组合 |
| 3 | **Data Layer V0.2** | infra | 打开时段与更诚实的年化；不阻塞 1 | 不是策略 |
| 4 | **跨品种残差（新家族，V0.9 之后）** | 324 | 与 V0.8 不同机制才合法；本季不并行 | 不是 XA-0001 改 lag |
| 5 | **ML state model（有袖套或 V0.9 结论后）** | 72 | 算力在；检验最差；排后是纪律 | 不是让 LLM 扫指标 |

若 V0.9 得出 `NO_CANDIDATE`：按杀停进入 2 或 3，或停。  
**不要**自动去 4。不要为了报表去 5。

---

## 4. 明确降级 / 拒绝

| 项 | 决定 |
| --- | --- |
| 再扫 RSI/MA/Donchian | 拒绝 |
| 扩 HYP-XA-0004… | 拒绝 |
| 先做 LLM 宏观 | 拒绝（T=2，无标签） |
| 先做组合 / 风险平价当第一边 | 拒绝（无袖套） |
| 先做 Carry/VRP/新闻 | 拒绝（D=0） |
| 先做 M15 时段 | 拒绝（假跨度） |
| 把 OIL D1 动量调到第二个品种 | 拒绝 |

---

## Decision

评分一次锁定。Top 1 = Regime Transition。  
Phase D 的 12 个月路线必须服从这张序，不得把高风险项提前到第一阶段。

---

## Next Automatic Action

Phase D：`TRADEMIND_ALPHA_ROADMAP_12M.md` — 低成本 / 中风险 / 高风险三阶段，且不跳级。
