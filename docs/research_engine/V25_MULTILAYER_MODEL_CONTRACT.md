# V25 Contract — A-share multi-layer combination model (pre-registered)

**Family:** `A_SHARE_MULTILAYER_MODEL_V25`  
**Authority for the rule changes used here:** `RESEARCH_RULES_AMENDMENT_V1.md` (A1 construction menu, A2 rolling validation, A3 one model per layer)  
**Machine copy:** `data/market/research_engine/cn_a_share_ml_v25/CONTRACT.json` (hash written at run start, before any result exists)

## Question

Every A-share signal we hold was tested alone, long-only, against an absolute-return gate through a −30% bear market. Two questions were never asked:

1. Do several weak, economically distinct signals *combined* carry enough information to beat costs when each alone does not?
2. Does the answer change when the book is hedged against the index (IF short), so the gate measures stock selection rather than "did you beat a bear market"?

## What is fixed before the run

| Item | Value |
|---|---|
| Features (14) | price: NEG_VOL_60, NEG_VOL_120, REV_20, MOM_250_20, NEG_TURN_20, NEG_LOG_AMT_20 · margin (V23, PIT lag 1): NEG_NET_INFLOW_20_OVER_CAP, NEG_BALANCE_OVER_CAP, NEG_BALANCE_CHG_60 · holders (V24, HOLD_NOTICE_DATE): NEG_QOQ_CHANGE, NEG_HOLDERS_PER_SHARE · finance (V16, announcement date): ROE_ANNUAL, YOY_NET_PROFIT_ANNUAL · index (V20 as-of): HS300_MEMBER |
| Transform | cross-sectional rank in [0,1] per session over eligible names; HS300_MEMBER raw 0/1 |
| Label | rank of open(t+1)→open(t+21) return, minus 0.5 |
| Model ML1 | LightGBM regressor: 31 leaves, lr 0.03, 400 trees, min_child 1000, colsample 0.8, subsample 0.7, λ₂ 1, seed 20260904 |
| Baseline ML0 | no-fit mean of a-priori-signed feature ranks (13 features; HS300_MEMBER excluded) |
| Walk-forward | first OOS prediction 2012-01-04; expanding window; refit every 120 sessions; training rows every 5th session; embargo 21 sessions (a row enters training only when its label is fully known at the refit date); **frozen at 2021-08-24**, validation scored by the frozen model |
| Universe / execution | eligible (listed, trading, non-ST, ≥40 sessions), signal at close(t), execute at open(t+1), top quintile, equal weight, 20-session hold, unfilled stays cash, `A_SHARE_STRATEGY_COST_MODEL_V1` unchanged |
| Primary book (gated) | **HN20**: stock fraction 0.85, short HS300 futures 1:1 on filled notional, futures cost = 3%/yr basis carry + 0.0046% fee + 0.02% slippage per round trip |
| Secondary book (reported) | LO20 legacy long-only |
| Predictive book | overlapping MEAN_FORWARD_RETURN excess vs eligible EW (unchanged; ≠ CAGR) |
| Fixed split | research 2010-01-04 → 2021-08-24; validation 2021-08-25 → 2024-02-29; denied 2024-03-01 → 2026-08-28 (never read) |
| Rolling blocks (A2) | 2014–15, 2016–17, 2018–19, 2020→2021-08-24, 2021-08-25→2024-02-29; excess-vs-EW must be positive in ≥4 of 5 |
| Level-1 gate | fixed-split gates (pred net>0 both, ≥2 of {excess, rank-IC} both, FDR q=0.05 over m=2, HN20 capital>0 research and validation) **and** rolling ≥4/5 |
| Cluster | corr vs H11/H12 (LO20 period returns and predictive series) > 0.9 → SAME_CLUSTER |
| FDR | m = 2 (ML1, ML0) |
| Diagnostics (not gated) | H11 NEG_VOL_60 and V23 M1 re-read on HN20, labelled DIAGNOSTIC |

## What is forbidden

- Second configuration of any kind (features, transform, label, params, schedule, hedge parameters) after seeing results.
- Refit after research end. Reading the denied window. Changing the stock cost model.
- Promoting a diagnostic. Treating MEAN_FORWARD_RETURN as CAGR.
- Reopening H11/H12 or V13–V24 as hypotheses (they enter only as features).

## Outcomes

- ML1 passes, ML0 fails → combination + nonlinearity carries information → `NEW_INDEPENDENT_CANDIDATE` if corr vs H11/H12 ≤ 0.9 → STOP A, reproduction.
- Both pass → information is in the combination, not the model; still one Candidate (m counted).
- Both fail → `A_SHARE_MULTILAYER_MODEL_V1_NO_CANDIDATE`; the "combine what we own" door is closed under the amended rules too.
