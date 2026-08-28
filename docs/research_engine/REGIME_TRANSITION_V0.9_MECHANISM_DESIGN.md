# Regime Transition V0.9 — Mechanism Design

Program: `ALPHA_PROGRAM_V1`. Phase 4.  
Does **not** rewrite `REGIME_TRANSITION_V0.9_CONTRACT.md` §11.  
Hash stays `3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`.

This file answers: why a *state change* could pay, lists ≤10 claims, picks the same Top 3 already locked.

---

## 4.1 经济机制（不是 ADX 变化）

ADX / SMA / VOL 分位只是 **测量器**。赚钱故事必须是人的约束。

当已实现波动从中低跳到高，或趋势强度从弱跳到强：

1. **风险预算重置。** 基金/柜台按波动或回撤砍名义本金。砍仓不是瞬时完成，会在随后数个交易日继续。  
2. **止损与强平成群。** 转换日是 cascade 的起点，不是终点。条件期望在 t+1…t+5 仍可能偏离。  
3. **做市商库存。** 制度切换后买卖不平衡，库存消化需要时间。  
4. **「处于状态」已被本室证伪。** 每天在 TREND_STRONG 里做突破，等于买一个高占用过滤器。转换是稀疏事件，占用应远低于 30%。V0.8 次日高占用把成本先吃光；转换类赌的是相反的成本结构。

因此 H1 不是「ADX 变大」。H1 是：**风险补偿的价格在制度切换后的短窗口被错误或延迟定价。**

若转换后收益 ≈ 无条件同向，机制假。记 FALSIFIED。不准改成「那就多拿几天」。

---

## 4.2 假设生成（最多 10，全部预注册意图）

共同锁（若未另开版本）：D1；NEXT_BAR_OPEN；hold=5；V0.6 成本；0.5% 风险；1×；FRICTION_WIDE 禁开；70/15/15；OOS DENIED。

| id | Hypothesis | Economic mechanism | Asset | Feature | Target | Holding | Risk | Failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RT-A | Vol 进入 HIGH 后原油承压 | 风险资产去杠杆，能源先被砍 | OIL | VOL≠HIGH → HIGH | 其后 5 步 OIL 收益 < 0 | 5 D1 | 0.5% / 1.5×ATR | 成本后不赚、符号反、n<8、只极端日 |
| RT-B | 趋势强度点火且方向 UP 后黄金续涨 | 约束开始绑定，趋势跟随资金延迟入场 | GOLD | WEAK→STRONG 且 TREND=UP | 其后 5 步 GOLD > 0 | 5 | 同 | 与「每天在 STRONG 里做多」无异（占用过高）或亏损 |
| RT-C | 趋势强度死亡后黄金回吐 | 去杠杆/趋势资金撤退集中在退出点 | GOLD | STRONG→WEAK | 其后 5 步 GOLD < 0 | 5 | 同 | 符号反；或只是无条件空头 |
| RT-D | Vol 进入 HIGH 后黄金上涨 | 避险买盘 | GOLD | 同 RT-A 但标的 GOLD | GOLD > 0 | 5 | 同 | 与 RT-A 对冲故事冲突；作第 4 条会涨 m |
| RT-E | 进入 DOWN+STRONG 后黄金下跌 | 对称点火 | GOLD | WEAK→STRONG 且 DOWN | GOLD < 0 | 5 | 同 | 与 RT-B 成对扫描；本季不进 m=3 |
| RT-F | Vol **离开** HIGH 后原油反弹 | 风险预算恢复 | OIL | HIGH → 非 HIGH | OIL > 0 | 5 | 同 | 稀疏更甚；SHELF |
| RT-G | FX TREND 点火 | 美元代理制度变了 | EURUSD | 同 RT-B | EURUSD 5 步 | 5 | 同 | 扩大宇宙；V0.9 合同只锁 GOLD/OIL |
| RT-H | 相关跳升后残差可交易 | 压力相关→1 | GOLD vs OIL | 滚动 corr 进入高档 | 残差回复 | 5 | 同 | 新家族，不是 V0.9 |
| RT-I | 连续两日同向转换 | 「确认」减少假转换 | OIL | 两根 VOL_SHOCK | OIL < 0 | 5 | 同 | 改定义凑笔；禁止 |
| RT-J | hold=10 的同一转换 | 预算调整更慢 | 同 A/B | 同 A/B | 同 | **10** | 同 | **参数扫描**。禁止。应用新版本 |

---

## 4.3 排序 — Top 3 = 已锁合同

选择规则（看收益前）：

1. 必须覆盖 **两个标的**（GOLD 与 OIL），否则永远只能 WEAK_EDGE。  
2. 三个故事必须不同（shock / ignition / death），不是同一句换符号。  
3. 不得把 hold、ADX、分位变成第四维。  
4. 不得为了「黄金避险更好听」把 RT-D 换进主族（那是看见黄金牛市后的诱惑）。

**入选：**

| 合同 id | 设计 id | 理由 |
| --- | --- | --- |
| HYP-RT-0001 | RT-A | 唯一 OIL 腿；风险资产去杠杆 |
| HYP-RT-0002 | RT-B | GOLD 点火；与 V0.6「处于趋势」不同 |
| HYP-RT-0003 | RT-C | GOLD 退出；与 0002 成对但不共享 OIL |

RT-D…J：**SHELF / 禁止**。不写入 runner。不增加 m。

若实现时发现占用像「一半交易日都在交易」：定义被写错，job 失败，不准改成状态水平。

---

## Decision

深度设计确认：可执行集合已经锁对。  
完善合同 = 本文件 + 验收门 + 引擎缺口清单，**不是**改 hash。

---

## Next Automatic Action

Phase 5：`RESEARCH_ENGINE_MISSING_COMPONENTS_V1.md`。
