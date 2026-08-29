# CORR_SHOCK_V1 Contract

Family: `FAM-CS-CORR-0001`. Search-space hash:

`0d729861f138c5e974ec5b99cc308523e97ee4f12c04f17d51678a325ce1647d`

## Mechanism

60-day rolling correlation of GOLD and US500 daily returns. Event is a **regime cross**, not a level.

- `CORR_BREAK_CROSS`: corr falls through its trailing 252-day 20th percentile
- `CORR_SPIKE_CROSS`: corr rises through its trailing 252-day 80th percentile

Not DXY z. Not gold-silver ratio. Not ATR high/low. Not V0.8 pair return.

## Locked parameters

| Field | Value |
| --- | --- |
| corr_lookback | 60 |
| pct_lookback | 252 |
| break_pctl | 0.20 |
| spike_pctl | 0.80 |
| hold_bars | 5 |
| occupancy_max | 0.40 |
| seed | 20260829 |

Do not search lookbacks or percentiles. Do not flip signs.

## Hypotheses

| ID | Event | Book |
| --- | --- | --- |
| HYP-CS-0001 | CORR_BREAK_CROSS | long GOLD short US500 |
| HYP-CS-0002 | CORR_BREAK_CROSS | long GOLD only |
| HYP-CS-0003 | CORR_SPIKE_CROSS | short GOLD long US500 |

CANDIDATE needs two hyps plus FDR after cost. Not 10%.

## Parents

- `tm-market-GOLD-D1-20260828-000001`
- `tm-market-US500-D1-20260828-000001`
