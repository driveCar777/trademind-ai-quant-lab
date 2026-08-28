# Alpha Recovery Report V1.0

Not a strategy. Not a 10% CAGR claim. Level is still **0**. Candidate = **0**.

Frozen families were **read**, not rewritten: HYP-0001, FD V0.1, V0.5, V0.6, V0.8, V0.9, V0.91.

Final OOS: **DENIED**.

## 1. Covered probability space

- direction: covered 83% (5/6 slots)
- relative_value: covered 40% (2/5 slots)
- state_transition: covered 50% (3/6 slots)
- risk_premium: covered 0% (0/4 slots)
- event: covered 0% (0/3 slots)
- microstructure: covered 60% (3/5 slots)
- time_institutional: covered 0% (0/7 slots)
- volatility_realized: covered 40% (2/5 slots)

Direction and state-level price rules were exhausted. Relative-value was tested twice (V0.8 wrong object, V0.91 residual). Risk premium, scheduled events, and institutional time were not contracted. Microstructure was tested only as next-return *level* (FD tickvol_z), not as surprise/divergence.

## 2. Information-gap codes (A-E)

| family | codes | outcome | why |
| --- | --- | --- | --- |
| HYP-0001 | A,E | WEAK_SUPPORT_NOT_A_BOOK | Family rollup was not a costed book. Short-horizon persistence is not Level 1. |
| FACTOR_DISCOVERY_V0.1 | A | NO_USEFUL_FACTORS_FOUND | FDR farm: PROMISING=0 CANDIDATE=0. No next-return displacement survived. |
| RESEARCH_ENGINE_V0.5 | A,E | NO_USEFUL_STRATEGIES_FOUND | State-level sketches / 1-3 bar rules. The label recipe survived; the sketches did not. |
| PROFIT_DISCOVERY_V0.6 | B,C | WEAK_EDGE_ONLY | Program CANDIDATE=0 after cost. One OIL D1 leftover ~0.2% CAGR. M15/H1 2000 bars cannot certify years. |
| CROSS_ASSET_ALPHA_V0.8 | A,E | NO_CANDIDATE | 3/3 FALSIFIED. Next-day dollar proxy is the wrong relative-value object. |
| REGIME_TRANSITION_V0.9 | A,C | NO_CANDIDATE | Delta fired (occupancy 1-2%, not level). RESEARCH books lost money. 0002/0003 validation n<4.; mean_occupancy=0.0151 |
| CROSS_RESIDUAL_V0.91 | B,A | NO_CANDIDATE | 0001 perm p=0.072 and a positive delta, but costed two-leg TR is deeply negative.; 0002/0003: no usable residual edge (A). 0001: fragment eaten by cost (B).; mean RESEARCH TR=-1.832 |

Code key: **A** no usable predictive information; **B** fragment eaten by cost; **C** wrong timescale; **D** missing data; **E** wrong expression of a nearby idea.

Dominant code: **A**.

## 3. Why the existing search space produced no alpha

Direction and state-level price rules were exhausted. The two new families (delta-state, residual) also failed after cost. Untested slots that still have on-disk data are institutional time and realized-vol term structure / volume-return divergence. IV, carry, news remain D.

## 4. Remaining unknown space that still has data

- Institutional month-end / month-start on frozen D1 (never contracted).
- Realized-vol term structure and volume-return divergence (OHLC + tick_volume on disk).
- London/NY open: economically real. Frozen H1 is months; broker probe meets ~5.03y as **new IDs only**.
- IV / carry / news: still **D / BLOCKED**.

## 5. Calendar occupancy on frozen D1 (dates only)

- GOLD n=2000 month_end=78 month_start=78 quarter_end=26 RESEARCH_ME~55 VAL_ME~12
- OIL n=2000 month_end=78 month_start=78 quarter_end=26 RESEARCH_ME~55 VAL_ME~12

hold=5 does not collide with monthly events. RESEARCH month-end count is above the n_trade>=8 gate if the event fires.

## 6. Selected family (one)

- **OPP-IT-ME** - Month-end institutional rebalance window on D1
- why not tested before: Queued behind V0.9/V0.91. Backlog mentioned calendar; no contract was written. Not a weekday dummy.
- score: 20000

Contract: `INSTITUTIONAL_TIME_V1.0`. **Not executed.**
