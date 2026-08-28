# Alpha Research Priority V2

Program: `ALPHA_PROGRAM_V1`. Phase 2.  
Score declared before any new PnL.

```text
score = E × D × I × C × P
if D <= 1: score = 0
KILLED isomorph: not in Top 10 implementable
```

| 维 | 含义 | 5 | 1 |
| --- | --- | --- | --- |
| E Expected Edge | 若为真，对长期资本有没有量级 | 能成为 10% 的一层 | 几个 bps |
| D Data Availability | 磁盘 + 跨度 | D1 够主证 | 缺字段 |
| I Statistical Identifiability | 能预注册、能拒绝、n 够 | 稀疏可数、m 小 | 无限特征 |
| C Cost Survivability | 换手是否先杀死 | 多日、稀疏 | 次日高占用 |
| P Economic Plausibility | 有约束/补偿故事 | 风险转移 | 指标神话 |

---

## Executive Summary

Top 1 仍是 **Regime Transition**。  
Top 10 里没有 RSI，没有 XA-0004，没有无数据的 Carry。  
第 10 名是「停或只补数据」——这是合法研究方向。

---

## Top 10

### 1. Regime Transition Δstate（V0.9）— score 1280

E4 D5 I4 C4 P4

**为何可能赚钱：** 风险预算和止损在制度切换时重置，随后数日的条件期望可以偏离无条件。稀疏事件，30bp 成本不一定先吃光。  
**为何别人可能没发现（在本室）：** 业界测过「在趋势里做趋势」。本室 V0.5/V0.6 也只测了 **水平**。转换本身没进过 FDR 族。  
**为何数据能验：** GOLD/OIL D1 ~6.4 年；`MARKET_STATE_V0.5` 已有；成本模型已有。M15 不够，所以只锁 D1。

### 2. Data Layer V0.2 加长 — infra（不是 alpha，排第 2 因为挡住时段）

E— D 待试 I5 C— P5 as infra

**为何可能赚钱：** 本身不赚钱。它打开时段与诚实年化。  
**为何别人没当研究：** 被当成运维。本室 Max. bars=2000 是硬墙。  
**为何能验：** MT5 只读再抓；失败就记短板。不覆盖 `000001`。

### 3. D1 日历 / 周末间隙 — 240

E2 D5 I3 C4 P2

**为何可能赚钱：** 周末信息在 Sunday/Monday D1 集中进入价格。占用低。  
**为何别人可能没当主搜：** 太土；或被 20 个星期 dummy 多重检验毁掉。我们只许极少条。  
**为何能验：** 每根 D1 有 UTC 日期；Sunday bar 是 FACT。

### 4. 无条件路径基准（GOLD/OIL 被动）— 诊断 500*

**为何可能赚钱：** 风险溢价路径，不是预测。2020–2026 黄金会好看。  
**为何必须做：** 否则会把牛市当成 Candidate。  
**为何能验：** 同窗同成本即可。禁止升级为 Level 1。

### 5. 跨品种残差（新家族）— 324，本季不并行

E3 D4 I3 C3 P3

**为何可能赚钱：** 黄金与原油有宏观慢关系；残差回复是库存/风险偏好，不是次日美元代理。  
**为何别人可能没做干净：** 容易和 V0.8 混成「再扫跨品种」。  
**为何能验：** 1993 日对齐包已在。**等 V0.9 结论**，新 `discovery_id`。

### 6. 相关制度切换（压力期 corr 上升）— 288

E3 D4 I3 C3 P3

**为何可能赚钱：** 危机时相关→1，分散失效；切换前后条件期望可测。  
**为何别人常做错：** 用同 bar 相关当可交易信号（V0.8 已见 gold/USD \|r\|≈0.43 不可交易）。  
**为何能验：** 四条 D1。必须滞后、成本后。SHELF。

### 7. Risk 4A 挂在存活袖套 — 288，SLEEVE BLOCKED

E3 D5 I4 C4 P3

**为何可能赚钱：** 不预测方向，让已有边少死在高波动。  
**为何现在不做：** 没有宿主边。单独做 = V0.6 DEF 重演。  
**为何以后能验：** `sizing.py` + ATR 已在。

### 8. 预注册 ML 状态机（极少特征）— 72

E3 D3 I2 C2 P2

**为何可能赚钱：** 非线性交互可能是真的。  
**为何别人「发现」很多假的：** 特征无穷，FDR 必炸。  
**为何部分能验：** 只有锁 3–5 个因果特征才算可识别。排后。

### 9. 相关品种确认后的突破 — 160

E2 D4 I3 C2 P2

**为何可能赚钱：** 单品种假突破多；第二品种确认减少噪声。  
**为何像重复：** 非常接近 PF-BRK。必须是 **确认** 机制，不是再扫 N。  
**为何能验：** 对齐 D1。SHELF，且优先级低于残差。

### 10. 停开策略 / 只写 FAILED 清单 — n/a

**为何这是第 10 名研究：** 若 V0.9 再灭，继续挖同构是负 EV。  
**为何别人不停：** 版本号焦虑。  
**为何「能验」：** 条件 B：可做 UNKNOWN 被系统排除。

---

## 明确未进 Top 10

RSI/MACD/MA/Donchian/HYP-0001 调参 / XA-0004 / Carry / VRP / 新闻 / 订单流 / M15 时段主证 / 无袖套组合 / Paper。

---

## Decision

执行序：1 →（另批跑 V0.9）→ 按结果选 2 或 3 或 10。不并行 5–9。

---

## Next Automatic Action

`TRADEMIND_ALPHA_STRATEGY_ROADMAP_V2.md`。
