# V25.1 Reproduction Contract (pre-registered)

**Object:** `ML1_LGBM_STACK` from V25, the only Level-1 since H11/H12.  
**Purpose:** decide whether the Level-1 shape is a property of the information or of one arbitrary schedule, and apply the independence test that is actually informative for long books.  
**Not:** tuning. Nothing in this battery is selected; the V25 primary configuration is unchanged whatever the numbers say.

## Fixed variant list (`research_engine/cn_a_share_ml_v25/reproduce.py`)

| id | change | everything else |
|---|---|---|
| PRIMARY_AS_CONTRACT | none (re-read of saved scores) | contract |
| SEED_1, SEED_2 | LightGBM seed 1 / 2 | contract |
| STRIDE_3, STRIDE_10 | training rows every 3rd / 10th session | contract |
| REFIT_60, REFIT_240 | refit every 60 / 240 sessions | contract |

## Recorded per variant

research / validation excess vs EW (mean, t); LO20 and HN20 capital totals research and validation; rolling blocks positive (of 5); **excess-series corr vs H11** (corr of excess-vs-EW series, n ≈ 2950); `level1_shape` = all six of {excess R, excess V, LO20 R, LO20 V, HN20 R, HN20 V} > 0.

## Pass criteria (decided before results)

- `level1_shape` true in **7 of 7** variants, and
- validation excess ≥ +0.5% per 20 sessions in every variant, and
- excess-series corr vs H11 ≤ 0.9 in every variant.

If met: `NEW_INDEPENDENT_CANDIDATE = 1` under amendment A4 (excess-series cluster test), ML1 enters the Strategy layer as the second sleeve subject to `POST_V21_STRATEGY_BIND.md`. If any variant fails: the result is schedule-fragile; record and stop at Level-1 without independence.

## Still forbidden

Any change to features, label, hold, cost, hedge parameters, or FDR family. Reading the denied window. Paper / Live.
