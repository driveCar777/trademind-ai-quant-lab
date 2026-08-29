# SIZE_SPREAD_V1 Contract

Locked family. Search-space hash `7dce045b1207dedce7dfa2e6c9e453fea5ab1119849332b49dc583ce79aa7603`.

## Mechanism

New MT5 series: `US_2000` D1 17.12y frozen as `tm-market-US2000-D1-20260829-000001`.

Feature is the **size spread**, not participation and not a single-index percentile:

> 20-day return of US2000 minus 20-day return of US500.

Events (locked):

- `SIZE_LAG` — spread crosses from positive to negative (small lags large)
- `SIZE_LEAD` — spread crosses from negative to positive

Hypotheses:

1. `HYP-SZ-0001` lag → long GOLD
2. `HYP-SZ-0002` lead → short GOLD
3. `HYP-SZ-0003` lag → short US2000 / long US500

Not ag breadth. Not GER40 pctl. Not 10-FX rank. Not buy US500 alone.

Hold = 5. Fill = NEXT_BAR_OPEN. Final OOS = DENIED. Leverage = 1x.
