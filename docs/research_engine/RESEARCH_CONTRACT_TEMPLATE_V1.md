# Research Contract Template V1

Design only. 2026-08-26.  
Use this to write a **new versioned** contract. Do not edit a frozen contract with this template.

A contract is write-once. Seeing results and changing a field is a **new** discovery_id, not an amendment.

---

## Executive Summary

每一份新实验必须先回答机制，再锁字段，再实现。  
禁止：先扫 100 个指标，再编故事。

最小合同 = 下面清单全部非空。缺一项 = 不准派 Xavier。

---

## 1. Identity

| field | rule |
| --- | --- |
| `discovery_id` | 新版本字符串。不得复用 V0.8 / V0.6 / HYP-0001 |
| `family_id` | 新机制新家族。禁止把失败家族改名重开 |
| `hypothesis_ids` | 预注册闭集。默认最多 **3**。禁止 worker 自增 |
| `parent_hypothesis_id` | 若衍生则写；否则 null。不得挂到 HYP-0001 当孩子来改 streak |

---

## 2. Mechanism (required prose)

Must fit one paragraph:

```text
Because [market constraint / risk transfer],
when [observable at t, causal],
the next [horizon] return of [target]
is [sign] after the locked cost model.
```

Reject if the paragraph is “indicator X is sometimes good”.

Also write **Not:** 至少三条（不是 V0.6 动量、不是 V0.8 次日代理、不是无条件因子农场）。

---

## 3. Data

| field | rule |
| --- | --- |
| `parent_datasets` | 只读 immutable id 列表 |
| `timeframe` | 主证默认 D1。M15/H1 不得进 FDR 主族，除非 Data V0.2 加长后另开 |
| `align` | 跨品种必须写 align_id / inner join / 禁止填充 |
| `windows` | 70/15/15，看收益前冻结 |
| `FINAL_OOS_ACCESS` | `DENIED` 直到另批 |

---

## 4. Feature / target / hold

| field | rule |
| --- | --- |
| feature | 只用 ≤ t |
| target | 未来窗，不得与 feature 同 bar 成交 |
| fill | `NEXT_BAR_OPEN`。`close` 成交 FORBIDDEN |
| hold | 锁一个整数。禁止事后扫 3/5/8/10 |
| predicted_sign | 经济单向。失败不得翻号 |

---

## 5. Cost / risk (default = V0.6)

| item | default |
| --- | --- |
| half spread | broker-points rule |
| commission | 5 bp / side |
| slippage | 10 bp / side |
| risk_frac | 0.5% equity |
| leverage | ≤ 1× |
| stop | 1.5× ATR or hold end |
| FRICTION_WIDE | skip |

Cheapening cost to find 10% is cheating.

---

## 6. Statistics

| knob | default |
| --- | --- |
| seed | 20260825 |
| bootstrap / permutation | 2000 |
| block_length | 5 on D1 |
| BH m | = hypothesis_count |
| q | 0.05 |

Report: n_aligned, n_signal, n_trade, occupancy, total_return, cagr, max_dd, sharpe, delta vs same-side unconditional, Cohen d, CIs, raw_p, adjusted_p.

CAGR ≥ 10% is **not** a pass gate.

---

## 7. Labels / program gate

Single hypothesis pass (all required):

- RESEARCH and VALIDATION costed `total_return` > 0  
- realized sign matches H1  
- RESEARCH trades ≥ 8, VALIDATION ≥ 4  
- RESEARCH DD ≥ −25%, VALIDATION ≥ −30%  
- `max_trade_share` ≤ 50%  

Program CANDIDATE: ≥2 passing hypotheses that do **not** collapse to one target, **and** FDR discovery on the passers.

Legal outcomes: `NO_CANDIDATE`, `WEAK_EDGE`, `CANDIDATE`.

---

## 8. Rejection (write before run)

至少写清：

- INSUFFICIENT_OCCUPANCY → 不改定义凑笔数  
- 符号反 → FALSIFIED，不翻号  
- 只一个品种过 → WEAK_EDGE，不调参凑第二  
- FDR 0 → 不得降 q  
- 无边 → 冻失败，开新版本，不优化本空间  

---

## 9. Untouched

HYP-0001 14:11, FD V0.1 space file, V0.5/V0.6/V0.8 results, immutable bars, `data/mine/longrun/`, `order_send`, Final OOS payload.

---

## 10. Canonical hash

`json.dumps(payload, sort_keys=True, separators=(',', ':'))` UTF-8 SHA256.  
Implementation must reproduce before any job.

---

## Next Automatic Action

Apply this template to Regime Transition: `REGIME_TRANSITION_V0.9_CONTRACT.md`.
