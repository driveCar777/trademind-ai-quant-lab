# REGIME_INTERACTION_V1 CONTRACT

Tag: `RESEARCH-2026-0004`

Not V0.8. Not V0.9 ADX/VOL tercile. Not V0.91 SMA60. Not weekday.

search_space_hash: `c060a77e5c08e7c226f63878f6b105e9255b7dedebd5074aa5782dbc9b1fd321`

## Mechanism

Relative realized-vol regime between GOLD and OIL (20-bar RV ratio crossing 1). Joint vol shock is both RVs above own 100-bar mean+1sd.

## Parents

GOLD/OIL H1 `20260828-000001`.

## Hypotheses

| ID | Event | Target | Sign |
| --- | --- | --- | --- |
| HYP-RI-0001 | GOLD RV/OIL RV crosses below 1 | GOLD | + |
| HYP-RI-0002 | GOLD RV/OIL RV crosses above 1 | OIL | + |
| HYP-RI-0003 | joint vol shock | GOLD | + |

hold=5 H1. NEXT_BAR_OPEN. V0.6 cost. 70/15/15. FDR m=3 q=0.05. Final OOS DENIED.
