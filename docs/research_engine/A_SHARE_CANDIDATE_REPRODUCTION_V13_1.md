# Candidate reproduction V13.1

**Date:** 2026-08-31  
**Purchase:** NO  
**Optimize:** NO  
**Final OOS:** DENIED  
**Strategy construction:** NOT STARTED  

Contract authority: `data/market/research_engine/cn_a_share_alpha_v1/CONTRACT.json`  
`contract_hash = b48b2657c4991041fb4e8f9fafa33c53c40be29222a1b39f87d24a82f596f75e`  
`dataset_id = tm-ashare-EQUITY-D1-20260830-000002`  
`dataset_hash = dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80`

H11/H12 parameters were **not** changed: lookback 60/120, hold 20, quantile 20%, long low realized vol, raw close(t) signal, raw open(t+1) execution, `A_SHARE_TRANSACTION_COST_MODEL_V1`, seed 20260831.

## Independent paths

| Check | H11_VOL_60 | H12_VOL_120 |
|-------|------------|-------------|
| Path A vs original `mean_net_h` | exact match | exact match |
| Path A run 1 vs run 2 hash | identical | identical |
| Path B vs Path A `mean_net_h` | exact match (tol 1e-8) | exact match |
| Score max abs diff A vs B | 3.8e-13 | 5.7e-14 |
| Eligible mask A vs B | equal | equal |
| Nonoverlap trade count A vs B | 172 = 172 | 172 = 172 |
| Status | **CANDIDATE_SURVIVED** | **CANDIDATE_SURVIVED** |

Path A = frozen V13 `feature_matrix` + `overlapping_series`.  
Path B = window-sum vol + `lexsort` pick + inline fees. Same contract, different code. Numerical tolerance = `1e-8` on mean net.

## Official overlapping gate (reproduced)

| Window | H11 mean_net | H12 mean_net | H11 Rank IC | H12 Rank IC |
|--------|--------------|--------------|-------------|-------------|
| Research | +0.001314 | +0.001478 | +0.0618 | +0.0538 |
| Validation | +0.000457 | +0.001067 | +0.1169 | +0.1102 |

Validation cost-adjusted CAGR from the locked overlapping formula remains **+0.55% / +1.30%**. That is **not** 10%.

Historical FDR discovery flags were **not** re-searched. Both remain `true` from the original 12-test BH q=0.05.

## Answers

1. H11 independently reproduces: **yes**.  
2. H12 independently reproduces: **yes**.  
3. Research stays positive after cost: **yes** (overlapping official book).  
4. Validation stays positive after cost: **yes** (overlapping official book).  
6. Rank IC stays positive: **yes**.  
7. FDR conclusion unchanged: **yes** (historical confirmation only).
