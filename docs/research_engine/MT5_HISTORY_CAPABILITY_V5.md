# MT5 History Capability V5

Machine file: `data/market/research_engine/mt5_universe/MT5_HISTORY_V5.json`.

## Probe policy

- Stage A: metadata for all 841. Deep TFs only on the first ~190 walk (FX/metal/energy/index already in cache).
- Stage B: 22 interesting names. D1 2k→80k; H1/H4/M15/W1 only if D1 ≥ 5y.
- Not 841 × M1 500k.

## New frozen D1 (`20260829-000001`)

| Logical | MT5 | Bars | Years | SHA256 prefix |
|---|---|---|---|---|
| COTTON | COTTON#2 | 1930 | 7.715 | 365985b4 |
| COCOA | COCOA | 1958 | 7.715 | 20975d20 |
| COFFEE | COFFEE_C | 1959 | 7.715 | 34aebd01 |
| CORN | CORN | 1928 | 7.715 | dbd618ea |
| SOYBEAN | SOYBEAN | 1892 | 7.715 | 488cfcda |
| SUGAR | SUGAR#11 | 1938 | 7.715 | 4cf92aa1 |
| WHEAT | WHEAT | 1928 | 7.715 | 5a4d5292 |
| EUROBUND | EURO-BUND | 1974 | 7.715 | e2ea58d8 |
| JAPANBOND | JAPAN_BOND | 2387 | 7.715 | b744e398 |
| US2000 | US_2000 | 4799 | 17.123 | 4aff77cc |

V4 `20260825` / `20260828` IDs were not rewritten.

## Still short

- VIX D1 ≈ 1.45y — not frozen.
- ITALY_40 D1 ≈ 3.97y.
- ALUMINIUM_SPOT / NICKEL_SPOT ≈ 2.67y.
- Broker ticks: GOLD HIST_TICKS ~592k / 2 days. Not an order book.

Terminal `maxbars` = 100000. 2000 bars is not the cap.
