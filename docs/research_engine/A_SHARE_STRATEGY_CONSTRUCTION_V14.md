# Strategy construction V14

**Date:** 2026-08-31  
**Purchase:** $0  
**Final OOS:** DENIED  
**Paper:** NO  

```
CLUSTER = LOW_VOL_CANDIDATE_CLUSTER
Strategy-H11 ← H11_VOL_60
Strategy-H12 ← H12_VOL_120
```

They are **not** two independent alpha sleeves. Validation period-return correlation = **0.994**.

## Locked spec

| Field | Value |
|-------|--------|
| Parent contract | `b48b2657…f75e` |
| Dataset | `tm-ashare-EQUITY-D1-20260830-000002` |
| Signal | raw close(t) 60d / 120d realized vol, long lowest 20% |
| Execution | raw open(t+1) |
| Hold / rebalance | 20 trading days, non-overlapping |
| Weight | 1 / N_selected. Unfilled weight stays cash |
| Leverage | 1.0x long only |
| Capital | 1,000,000 diagnostic (also report as ratios) |
| Cost | `A_SHARE_STRATEGY_COST_MODEL_V1` (same locked rates as V13) |

No new lookback, hold, quantile, sign, or factor.

## Statistic → strategy

Level 1 Candidate used **overlapping** H-day `mean_net_h` (H11 val CAGR ≈ 0.55%, H12 ≈ 1.30%).  
Canonical V14 is the locked **non-overlapping capital account**. Those numbers are not required to match. This is `STATISTIC_TO_STRATEGY_TRANSLATION`.

## Execution rules

Unexecutable (no pretend fill): `LIMIT_LOCK`, `SUSPENDED`, `DELISTED`, `ZERO_VOLUME`, `MISSING_OPEN`.  
If entry or exit is unexecutable, the name is **UNFILLED**. The contract has **no mid-hold delist price** (`CONTRACT_GAP`). Canonical does not invent one.

Limit implementation: `abs(open/preclose-1) < limit-0.002`. The 0.002 buffer is an implementation clarification.

## What this is

Candidate: the low-vol ranking mechanism survived Level 1.  
Strategy: the same rule as a cash account with costs, fills, and a 20-day book.

This mission does not optimize toward 10%.
