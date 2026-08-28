# CARRY_V1 / CARRY_V1A CONTRACT

## CARRY_V1 (invalid window)

search_space_hash: `0ccbac180f72da54bcdca046922b13a7637e811da3bc85caed3f479d9018a7cb`

This run is **INVALID_ALIGNMENT**. Do not treat occupancy 0 as a kill of overnight carry.

## CARRY_V1A (overlap bars only)

search_space_hash: `5974f11738baef21831a846991bd8d05dfa843e4c096e4f97ca636adcec03b46`

Same overnight legs and signs. Bars before the first known carry differential are dropped, then 70/15/15 is applied.

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-CARRYA-0001 | EURUSD | USD richer vs EUR z-cross > +2 | − |
| HYP-CARRYA-0002 | USDJPY | USD richer vs JPY z-cross > +2 | + |
| HYP-CARRYA-0003 | EURUSD | USD cheaper vs EUR z-cross < −2 | + |

Information: overnight funding differential, not FX price and not UST 10y on gold.

Knowledge:

- EFFR date T known T+1 13:00Z
- €STR date T known T+1 08:00Z
- BOJ call date T known T+1 01:00Z
- Feature then `NEXT_BAR_OPEN`

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-CARRY-0001 | EURUSD | USD richer vs EUR z-cross > +2 | − |
| HYP-CARRY-0002 | USDJPY | USD richer vs JPY z-cross > +2 | + |
| HYP-CARRY-0003 | EURUSD | USD cheaper vs EUR z-cross < −2 | + |

Signs are preregistered. Do not flip. Do not change z_cut. Final OOS DENIED.
