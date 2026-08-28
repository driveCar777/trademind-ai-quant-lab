# INSTITUTIONAL_TIME_V1.0 Contract

Locked. Design only. **Not executed. Not a runner. Not V0.8 / V0.9 / V0.91.**

```text
search_space_hash =
1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457
```

Do not run until reviewed. Do not add a fourth ID. Do not widen the window after PnL.

## 0. Family

| field | value |
| --- | --- |
| family_id | `FAM-IT-CALENDAR-0001` |
| discovery_id | `INSTITUTIONAL_TIME_V1.0` |
| status | `LOCKED_NOT_RUN` |
| hypothesis_ids | `HYP-IT-0001` `HYP-IT-0002` `HYP-IT-0003` |
| timeframe | D1 |
| hold_bars | 5 |
| seed | 20260825 |

### Hypothesis

Month-end and month-start are **institutional** events (benchmark rebalance, commodity-book flattening, new-month allocation), not weekday dummies and not indicator crosses.

### Mechanism

Because allocated books and dealers flatten or refill at calendar turns,
when the last (or first) D1 bar of a calendar month is observed at t,
the next 5 D1 bars of GOLD or OIL, filled at next open, after V0.6 costs,
are predicted **positive**.

### Not

- weekday / weekend-gap fishing
- RSI / MACD / MA combination / breakout parameter search
- V0.8 next-day dollar proxy
- V0.9 delta-state / VOL_SHOCK retune
- V0.91 residual / SMA60
- widening T-2..T+2 after seeing PnL

## 1. Dataset

Parents (immutable, do not rewrite):

- `tm-market-GOLD-D1-20260825-000001`
- `tm-market-OIL-D1-20260825-000001`

Windows: 70/15/15 on **each target's own D1 dates**. Final OOS last 15% DENIED.

## 2. Signal / target

| ID | event | target | predicted_sign |
| --- | --- | --- | --- |
| HYP-IT-0001 | last D1 bar of calendar month | GOLD | +1 |
| HYP-IT-0002 | last D1 bar of calendar month | OIL | +1 |
| HYP-IT-0003 | first D1 bar of calendar month | GOLD | +1 |

Feature uses only information <= t. Fill `NEXT_BAR_OPEN`. Close fill FORBIDDEN.
Overlap skip if a new event fires inside an open 5-bar hold.

## 3. Cost / evaluation

Copy V0.6: half spread broker-points, commission 5 bp/side, slippage 10 bp/side,
risk 0.5% equity, leverage <=1x, stop 1.5xATR or hold end.
seed 20260825, bootstrap/perm 2000, block=5, FDR q=0.05 m=3.
Gates: RESEARCH n_trade>=8, validation n_trade>=4, occupancy<=0.40,
costed TR>0 and predicted sign on both RESEARCH and validation.
Program CANDIDATE needs FDR and **both targets** after cost.
CAGR>=10% is not a gate.

## 4. Failure condition

- INSUFFICIENT_OCCUPANCY / n_trade below gate → fail the ID. **Do not widen the window.**
- Sign flip after seeing PnL → new discovery_id, not an amendment.
- Adding weekday, RSI, or a fourth ID → contract breach.
- Reading Final OOS → denied.

## 5. Calendar counts used to justify the contract (dates only)

- GOLD n=2000 month_end=78 month_start=78 quarter_end=26 RESEARCH_ME~55
- OIL n=2000 month_end=78 month_start=78 quarter_end=26 RESEARCH_ME~55

## Canonical payload

See `research_engine/opportunity/contract_it.py` `CANONICAL_PAYLOAD`.
If any hashed field changes, it is not V1.0.

## Untouched

HYP-0001 14:11, FD, V0.5, V0.6, V0.8, V0.9, V0.91, immutable bars, Final OOS, MT5 orders.
