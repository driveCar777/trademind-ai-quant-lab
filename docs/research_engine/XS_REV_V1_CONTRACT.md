# XS_REV_V1 Contract

Family: `FAM-XS-FX-0001`. Search-space hash:

`fe2a28755193a42c55469b8fe52390ced673581ef10239ebd5d9fcf145c9ede5`

## Mechanism

10-FX D1 book. Rank by 20-day return. Long 3 laggards, short 3 leaders. Rebalance every 5 bars. Hold 5. Fill `NEXT_BAR_OPEN`. Final OOS `DENIED`.

This is cross-sectional competition, not single-name momentum and not V0.8 pair→metal.

## Locked parameters

| Field | Value |
| --- | --- |
| lookback | 20 |
| k_leg | 3 |
| rebalance_every | 5 |
| hold_bars | 5 |
| disp_lookback | 252 |
| occupancy_max | 0.40 |
| seed | 20260829 |

Do not search lookback, k, hold, or flip to momentum.

## Hypotheses

| ID | Event | Side |
| --- | --- | --- |
| HYP-XS-0001 | XS_REBAL | REV long 3 / short 3 |
| HYP-XS-0002 | XS_REBAL | LAG_LONG only |
| HYP-XS-0003 | XS_REBAL_WIDE | REV when 20d CS std > 252d median |

CANDIDATE requires two book hyps plus FDR after cost. Not 10%.

## Parents

All `*-D1-20260828-000001`: EURUSD USDJPY GBPUSD AUDUSD USDCHF USDCAD NZDUSD EURJPY EURGBP GBPJPY.

Do not overwrite `*-20260825-000001`.
