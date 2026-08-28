# MICROSTRUCTURE_SURPRISE_V1 CONTRACT

Tag: `RESEARCH-2026-0003`

Not FD tick_volume **level**. Not weekday. Not session-open. Not month-end.

search_space_hash: `54ab70ff1cfc2f8cb4826bdde5075ca916c103d0a92fc7ea7b819298579892f1`

## Mechanism

tick_volume **surprise** versus the trailing 20 observations of the **same UTC hour**. Event if z > 2. Baseline excludes the current bar.

HYP-MS-0003 adds quiet-price divergence: surprise and |bar return| < 0.5 × same-hour mean absolute return.

## Parents

- `tm-market-GOLD-H1-20260828-000001`
- `tm-market-OIL-H1-20260828-000001`

## Hypotheses

| ID | Event | Target | Sign |
| --- | --- | --- | --- |
| HYP-MS-0001 | same-hour vol surprise | GOLD | + |
| HYP-MS-0002 | same-hour vol surprise | OIL | + |
| HYP-MS-0003 | surprise + quiet price | GOLD | + |

lookback=20. z_cut=2.0. hold=5 H1. NEXT_BAR_OPEN. V0.6 cost. 70/15/15. FDR m=3 q=0.05. Final OOS DENIED.

## Failure

Do not lower z_cut. Do not switch back to raw tick_volume level. Do not reopen FD V0.1.
