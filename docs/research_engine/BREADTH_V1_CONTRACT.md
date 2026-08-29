# BREADTH_V1 Contract

Locked family. Search-space hash `2ee70c767492a23101343885b653910b0b4e757cf7d50d0417a32d03a17ecf0a`.

## Mechanism

New MT5 information: seven agricultural CFDs (cotton, cocoa, coffee, corn, soybean, sugar, wheat), 7.7y D1, frozen as `*-20260829-000001`.

Feature is **participation**, not relative rank:

> share of the seven names whose 20-day return is positive.

Events (locked):

- `BREADTH_THRUST` — participation crosses above 0.80
- `BREADTH_CONTRACT` — participation crosses below 0.20

Hypotheses:

1. `HYP-BR-0001` contract → long GOLD
2. `HYP-BR-0002` thrust → short GOLD
3. `HYP-BR-0003` contract → short equal-weight ag book

This is a risk-regime read of a new commodity complex. It is not:

- 10-FX L3/S3 rank (`XS_REV_V1`)
- product−crude crack (`ENERGY_RV_V1`)
- GER40 one-name percentile (`IDX_ASYNC_V1`)
- buy US500

Hold = 5. Fill = NEXT_BAR_OPEN. Final OOS = DENIED. Leverage = 1x. Do not search lookback, thrust, or hold.
