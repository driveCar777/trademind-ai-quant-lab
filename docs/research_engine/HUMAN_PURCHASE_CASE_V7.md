# HUMAN_PURCHASE_CASE_V7

```text
GATE = EXTERNAL_DATA_GATE
AUTO_SPEND = false
REMAINING_CREDITS_USD ≈ 93.18
DO_NOT_OPEN_STANDARD_199 = true
```

## Research question

Does the **options-on-futures surface** (implied vol, skew, term of IV) on GC/CL contain a tradable edge that official futures **settlement / OI / cleared volume / days-to-expiry** do not?

## Required data

Databento (or equivalent) **options-on-futures** definitions + a daily or settlement IV/statistics schema for GC/CL. Not GVZ. Not OVX. Not MT5 CFD.

## Why current data cannot answer

Already owned and tested on the same GC/CL Pack E bytes:

| family | outcome |
|---|---|
| TERM_STRUCTURE_V1 | NO_CANDIDATE / LEVEL_LEAK |
| FUTURES_OI_FLOW_V1 | NO_CANDIDATE |
| VOLUME_PRICE_FLOW_V1 | NO_CANDIDATE |
| DTE_ROLL_WINDOW_V1 | WEAK_EDGE, FDR 0/3 |

Public GVZ/OVX already killed as z-cross. There is **no strike-level or implied-vol term structure** in the current information set.

## Expected research value

This is the next unused **economic mechanism** (volatility risk premium / skew / IV term), not another slope/OI/volume cut.

## Cost

**Unknown until quote.** Rule: quote first, then decide. Do not download. Do not consume the remaining ~$93 because a quote was not obtained in this mission. Do not open $199/month Standard to rescue.

## Human decision

WAIT. Quote options-on-futures coverage + USD. Then HUMAN PURCHASE GATE.

Secondary unused $0 fusions (OI vs COT, CL+EIA) are optional later. They combine already-killed legs. They are not the next dollar.
