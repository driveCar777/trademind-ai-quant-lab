# TradeMind Alpha Strategy Roadmap V2

Program: `ALPHA_PROGRAM_V1`. Phase 3.  
Ambition includes Paper in months 10–12. **Permission does not.**  
Each quarter has a **hard gate**. Missing the gate means that quarter becomes audit/data/stop, not the next label.

Capital ladder is ambition:

| 层 | 数字 | 现在 |
| --- | --- | --- |
| 基础 | ≥10% 成本后年化 | 无 Level 1，问不了 |
| 中 | 15–30% | 禁止无边叙事 |
| 高 | 30%+ | 禁止加杠杆制造 |

---

## Executive Summary

V2 按你指定的四季切：找 Candidate → 策略化 → 组合 → Paper。  
每一季前面加一把锁。没有 Level 1 就没有策略化；没有两条不全相关边就没有组合；没有 Level 2 就没有 Paper。

这不是拖延。这是「距离真实赚钱更近」：跳级 Paper 会制造假进度。

---

## Month 1–3 — 寻找 Level 1 Candidate

| 月 | 工作 | 门 |
| ---: | --- | --- |
| 1 | 本程序文档 + V0.9 合同已锁 | 不改 hash |
| 2 | **另批后** 实现 V0.9 + 四 Xavier | 恰好 3 条 |
| 3 | 冻结结论 | CANDIDATE / WEAK / NO |

允许：Δstate、失败保留、被动基准诊断。  
禁止：RSI、扩 XA、ML 主搜、读 OOS、MT5。

成功：Level 1 **或** 转换类被排除（条件 B 的一块）。

---

## Month 4–6 — Strategy construction

**硬门：** 至少一条 Level 1。否则本季改成 Data V0.2 或极窄日历或停。

若门开：

- 把该边写成策略合同：同一机制，锁定执行细节（已在 V0.9 的 hold/cost 上，不再扫）  
- Risk 4A 只挂在该袖套  
- 报告 Level 2 数字（CAGR/Sharpe/DD），**不**为了过门改参数

禁止：为 CAGR≥10% 改 hold。

---

## Month 7–9 — Portfolio

**硬门：** ≥2 个不全相关的 Level 1（或 1 个 Level 1 + 1 个独立 WEAK 且预注册为组合输入）。  
否则跳过组合，继续第二条未知（残差新家族 **或** 日历，一次一个）。

组合必须是信息分散，不是 V0.6 同品种三指标。  
跨品种用已有 1993 日时钟。

---

## Month 10–12 — Paper Trading

**硬门：** Level 2 Strategy Candidate 已冻，且另批。  
否则这 3 个月写年度 FAILED/UNKNOWN，或只补数据。

Paper 仍：人手确认路径，不自动 `order_send`，不碰真实资金。  
Final OOS 默认仍 DENIED。

---

## 与 V1 路线的关系

V1（`TRADEMIND_ALPHA_ROADMAP_12M.md`）把 Paper 放在「12 个月以后默认禁止」。  
V2 把 Paper **画进日历**，但用硬门锁死。两份不冲突：V2 是野心日历，门是法律。

---

## Decision

没有 Level 1 之前，本程序的「继续」= 设计、盘点、合同、（另批）V0.9 执行。  
不是开始写组合引擎或 Paper 接线。

---

## Next Automatic Action

Phase 4：V0.9 **深度机制设计**（最多 10 条，选出 Top 3）。不改已锁 hash，不写代码。
