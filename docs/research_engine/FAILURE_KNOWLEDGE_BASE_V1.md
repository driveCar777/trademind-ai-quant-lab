# Failure Knowledge Base V1

Program: `ALPHA_PROGRAM_V1`. Phase 7.  
Purpose: so the next agent does not rediscover a killed family under a new filename.

Do not edit frozen result JSON to “fix” these rows.

---

## Rule

```text
KILLED + same mechanism + different N/hold/indicator
  = cheating, not research
```

新合同必须写出 **新约束故事**，并在 `Not:` 里点名下表至少一行。

---

## Killed rows

| 失败 | 机制（人话） | 合同 | 典型诱惑 | 正确反应 |
| --- | --- | --- | --- | --- |
| 连续上涨 | 短持续 | HYP-0001 | 改 streak 2/4/5 | 禁止 |
| 因子农场 | 无条件技术 | FD 57 / FDR 876 | 再加 RSI | 禁止 |
| 状态内下一根 | 水平过滤 | V0.5 | 换 ADX 周期 | 禁止 |
| 趋势里突破 | Donchian 在 STRONG | V0.6 TF | 改 20→30 | 禁止 |
| 震荡里回归 | z20 | V0.6 MR | 改 z | 禁止 |
| 趋势+RET_5 | 短动量 | V0.6 MOM | 只留 OIL、改 hold | 禁止。残留 ≠ Candidate |
| 空仓 overlay | 少做少亏 | V0.6 DEF | 叫 Risk Alpha | 禁止当利润 |
| 同品种等权 | 相关噪声相加 | V0.6 book | 「先做组合」 | 无袖套禁止 |
| 次日美元代理 | 滞后 RV 1 日高占用 | V0.8 | 改 67%、翻号、同 bar | 禁止 |
| spread/tick 方向 | 摩擦当信号 | FD | 叫流动性溢价 | 真量 BLOCKED |

---

## Near-miss that must not be promoted

| 项 | 数字 | 不是 |
| --- | --- | --- |
| HYP-0001 WEAK_SUPPORT | 预测假设弱支持 | 书、10% |
| OIL D1 MOM | CAGR ≈ +0.13–0.23%，Sharpe≈0.08 | Level 1 |
| gold/USD 同期 \|r\|≈0.43 | 同 bar | 可交易边 |
| 2020–2026 黄金牛 | 路径 | Candidate |

---

## Still unknown (do not mark killed)

- Δstate（V0.9 未跑）  
- D1 日历极少条  
- 残差新家族  
- 真组合（无输入）

---

## Decision

本表是负面清单。扩行只许新增 **已冻失败**，不许把 UNKNOWN 提前写成 KILLED。
