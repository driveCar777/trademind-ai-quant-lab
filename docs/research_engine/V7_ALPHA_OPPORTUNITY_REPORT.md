# V7 Alpha Opportunity Report

Top 1 executed: **FUTURES_OI_FLOW_V1** / `FAM-FUTOI-0001`

Hash: `8ff94bd0dd6249b428497176d654e62944ed3ecf329440dd7539ec57dbcabbbc`

Four Xavier PASS. 01==04 `a97230b2…e4ecfe`. Outcome **NO_CANDIDATE**. Entered FAILED_ALPHA as RESEARCH-2026-0023.

| hyp | event | research occ | research TR | p | label |
|---|---|---|---|---|---|
| HYP-FUTOI-0001 | NEW_LONGS | 0.24 | +0.126 | 0.69 | WEAK_SUPPORT (validation fail) |
| HYP-FUTOI-0002 | SHORT_COVER | 0.40 | −0.293 | 0.86 | FALSIFIED LEVEL_LEAK |
| HYP-FUTOI-0003 | NEW_SHORTS | 0.20 | +0.033 | 0.43 | WEAK_SUPPORT (validation fail) |

FDR 0/3. Do not retune OI sign or hold.

Top 2 executed: **VOLUME_PRICE_FLOW_V1** / `FAM-FUTVOL-0001`

Hash: `e2e78ae9b815ac74c876fb969bf4b72aac095f37f919be71b7019e9cc04c70f0`

Four Xavier PASS. 01==04 `673721b7…5057c`. Outcome **NO_CANDIDATE**. RESEARCH-2026-0024.

Top 3 executed: **DTE_ROLL_WINDOW_V1** / `FAM-FUTDTE-0001`

Hash: `7b7451abdb1554a6b92b17b5afc6169bd9d283dbaf9f6a83ba6ff6cc53d4f365`

Four Xavier PASS. 01==04 `c51ea761…1c738`. Outcome **WEAK_EDGE** (only POST_ROLL book-pass, FDR 0/3). RESEARCH-2026-0025.

Remaining unused on purpose: curvature rescan, OI vs COT, CL+EIA. Those glue killed legs. Next dollar = options quote. Not RSI. Not slope.
