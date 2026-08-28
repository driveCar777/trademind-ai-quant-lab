# NEXT_ALPHA_DECISION

One family. Paper contract only. **Do not run.**

## Decision

- selected: **OPP-IT-ME**
- family: `INSTITUTIONAL_TIME_V1.0` / `FAM-IT-CALENDAR-0001`
- search_space_hash: `1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457`
- executed: **false**

## Why this one

- previously **UNKNOWN** (no calendar contract exists).
- data **available**: frozen GOLD/OIL D1 timestamps.
- economic mechanism: month-end / month-start institutional rebalance, not an indicator.
- not RSI / MACD / MA / breakout.
- not V0.8 isomorph. not V0.9 retune. not V0.91 SMA60.

## Why not the others

- London/NY open: frozen H1 is months. Broker probe meets ~5.03y as new IDs. Not selected: data is not on the immutable packs.
- RV term structure / vol-of-vol: adjacent to V0.9 VOL_SHOCK (isomorph risk).
- volume surprise/divergence: FD already killed tickvol as next-return *level*; still UNKNOWN but lower cost-survival score.
- USD proxy / basket residual: FAILED isomorphs.
- IV / carry: DATA_BLOCKED.
- weekday: FORBIDDEN.

## Why not tested before

Queued behind V0.9/V0.91. Backlog mentioned calendar; no contract was written. Not a weekday dummy.

## TOP 10 (Opportunity V2)

| rank | id | score | status | why not tested |
| --- | --- | --- | --- | --- |
| 1 | OPP-IT-ME | 20000 | UNKNOWN | Queued behind V0.9/V0.91. Backlog mentioned calendar; no contract was written. Not a weekday dummy. |
| 2 | OPP-IT-QE | 5120 | UNKNOWN | Same reason as month-end. Fewer events on the frozen D1 packs (~26 quarters). |
| 3 | OPP-RV-TERM | 3840 | UNKNOWN | IV is blocked so this was never opened. ATR *level* was used in V0.5/V0.9; slope of RV was not. |
| 4 | OPP-VDIV | 2880 | UNKNOWN | Not in the FD search space as a joint event. tick_volume is still on disk. Do not delete it. |
| 5 | OPP-IT-LON | 1920 | UNKNOWN | Never contracted. Frozen H1 is months. Broker probe meets ~5.03y H1 only as a new dataset_id. Not on-disk yet. |
| 6 | OPP-VOVOL | 1620 | UNKNOWN | Adjacent to V0.9 VOL_SHOCK. Left untested to avoid a fourth RT ID. |
| 7 | OPP-VSURP | 1620 | UNKNOWN | FD tested tickvol_z as next-return *level* and rejected it. Surprise was not the hypothesis. |
| 8 | OPP-IT-NY | 960 | UNKNOWN | Same as London: 5y H1 is acquirable, not frozen. Do not contract yet. |
| 9 | OPP-RISK-LABEL | 540 | UNKNOWN | V0.8 used FX to forecast next GOLD/OIL. A label without a new target is not a family. |

## Calendar counts (frozen D1 dates)

- GOLD month_end=78 month_start=78 quarter_end=26
- OIL month_end=78 month_start=78 quarter_end=26

## Contract (locked, not run)

- hypotheses: HYP-IT-0001 GOLD month-end +; HYP-IT-0002 OIL month-end +; HYP-IT-0003 GOLD month-start +
- hold=5, NEXT_BAR_OPEN, V0.6 cost, seed 20260825, FDR m=3, 70/15/15, Final OOS DENIED
- failure: do not widen the event window after seeing PnL; INSUFFICIENT_OCCUPANCY fails the ID
- Level 1 still requires FDR + both targets after cost. This contract does not grant it.

## Data gate

- selected family: **does not wait** on acquisition.
- Recovery H1 5y overall: **PROBE_H1_5Y_M15_2Y_OK_GOLD_OIL_D1_SHORT_OF_10Y**

Stop here. Wait for review.
