# V14.1 Overlap Bridge

Series A/B/C are **diagnostics**. They are not a menu. Do not promote the prettier one.

| Series | Meaning | H11 | H12 |
|---|---|---|---|
| A | Overlapping mean net | 0.1163% (n=3438) | 0.1406% (n=3438) |
| B mean | Nonoverlap V13-style mean | 0.0868% | 0.1108% |
| B compound V13 | Product of those nets | -25.5026% | -22.2418% |
| B compound capital | Official book total | -16.5797% | -11.6494% |
| C | 20 offset grids, n negative | 20 / 20 (mean end 0.776) | 20 / 20 (mean end 0.802) |

HORIZON_TRANSLATION_RISK = True.

`CANDIDATE_TO_STRATEGY_BRIDGE.csv` / `OVERLAP_BRIDGE.csv`: each official rebalance date, Candidate overlapping net that day, V13-style net on the same fills, capital period return, difference, cause tag.

A same-date Candidate net equals the V13-style book net when pick/fill match. The remaining gap to capital is `COST_OR_CASH_FORMULA`. Sign flips on that date are tagged `SIGN_FLIP`.
