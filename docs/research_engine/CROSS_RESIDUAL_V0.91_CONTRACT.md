# Cross Residual V0.91 Contract

Locked 2026-08-26. Design only. **Not executed. Not V0.9. Not V0.8.**

Independent family: a **slow relative price**, not a state change, not a next-day dollar proxy.

```text
search_space_hash =
0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57
```

Do not run while V0.9 is still LOCKED_NOT_RUN. One family at a time.

---

## 0. Family

| field | value |
| --- | --- |
| family_id | `FAM-XR-RESIDUAL-0001` |
| discovery_id | `CROSS_RESIDUAL_V0.91` |
| status | `LOCKED_NOT_RUN` |
| hypothesis_ids | `HYP-XR-0001` `HYP-XR-0002` `HYP-XR-0003` |
| timeframe | D1 |
| hold_bars | 5 |
| seed | 20260825 |

### Mechanism

Gold and oil share a slow inflation/risk factor.  
`resid[t] = log(GOLD_close[t]/OIL_close[t]) − SMA60(that log ratio)`  
When the residual is extreme, inventory and relative-value desks fade it over several days.

### Not

- V0.8 HYP-XA-0001/0002/0003 (next-day dollar Q3 / DOLLAR_UP)  
- V0.9 Δstate  
- V0.6 same-symbol MR-Z20  
- Trading same-bar gold/USD correlation  
- Flipping signs after seeing results  

---

## 1. Data

Parents (immutable):

- `tm-market-GOLD-D1-20260825-000001`  
- `tm-market-OIL-D1-20260825-000001`  

Align: inner join on UTC date (two-way). Do not fill.  
Windows: 70/15/15 on **aligned GOLD∩OIL dates**, frozen before PnL.  
Final OOS last 15% DENIED.

SMA60 and residual z-gates freeze on RESEARCH residuals only.

---

## 2. Three hypotheses

Book is a **spread**: +1 means long GOLD / short OIL in residual space (dollar-neutral-ish via 0.5% risk per leg cap 1× each — implementation must document notional).  
If two-leg accounting is too heavy at implement time, evaluate the residual’s next 5-step **change** as the target (predict `resid[t+5]−resid[t]`), still costed on both legs’ opens. Do not switch after seeing PnL.

### HYP-XR-0001

Residual rich: `resid[t] ≥ RESEARCH 67th percentile` → next 5 aligned steps the residual **falls** (fade rich gold vs oil).

### HYP-XR-0002

Residual cheap: `resid[t] ≤ RESEARCH 33rd percentile` → next 5 steps the residual **rises**.

### HYP-XR-0003

Joint risk-off leftover: both GOLD and OIL next-day? No — **same-day** both returns < 0 **and** `|resid|` in the outer third → fade residual (RB-0021).  
This is still residual, not “short oil because vol jumped” (that is V0.9).

m=3. No fourth. 0001+0002 are two tails of one story; program CANDIDATE still needs FDR and validation on more than a single tail plus a crash year.

---

## 3. Cost / stats

Copy V0.6 numbers. seed 20260825, boot/perm 2000, block=5, q=0.05.  
Baseline: unconditional same-side residual (or both-leg) 5-step return.  
Gates: same costed TR>0, sign, n, DD as V0.9 §6.  
CAGR≥10% is not a gate.

---

## 4. Canonical payload

```json
{"align_method":"INNER_JOIN_GOLD_OIL","close_fill":"FORBIDDEN","cost":{"commission_bp_per_side":5.0,"slippage_bp_per_side":10.0,"spread":"BROKER_POINTS_RULE"},"discovery_id":"CROSS_RESIDUAL_V0.91","family_id":"FAM-XR-RESIDUAL-0001","fill":"NEXT_BAR_OPEN","hold_bars":5,"horizon":"SIGNAL_PLUS_HOLD_ALIGNED_ROWS","hypothesis_count":3,"hypothesis_ids":["HYP-XR-0001","HYP-XR-0002","HYP-XR-0003"],"parent_datasets":["tm-market-GOLD-D1-20260825-000001","tm-market-OIL-D1-20260825-000001"],"residual":"LOG_GOLD_OVER_OIL_MINUS_SMA60","risk":{"leverage_cap":1.0,"risk_frac":0.005,"stop_atr_mult":1.5},"seed":20260825,"stats":{"block_length":5,"bootstrap":2000,"fdr_q":0.05,"m":3,"permutation":2000},"timeframe":"D1","windows":{"FINAL_OOS_ACCESS":"DENIED","split":"70/15/15_on_aligned_gold_oil_dates"}}
```

If any field changes, it is not V0.91.

---

## Untouched

HYP-0001 14:11, FD space file, V0.5/V0.6/V0.8 results, V0.9 hash, immutable bars, Final OOS, MT5.
