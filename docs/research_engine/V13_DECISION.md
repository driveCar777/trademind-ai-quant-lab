# V13 DECISION — first-wave A-share CS alpha

**Date:** 2026-08-31  
**Purchase:** NO  
**Live API:** NO  
**Final OOS:** DENIED  

```
DECISION = LEVEL_1_CANDIDATE
LEVEL = 1
CANDIDATE = 2
STRATEGY = 0
PAPER = 0
LIVE = 0
NEXT = CANDIDATE_REPRODUCTION
```

Candidates (frozen, do not retune):

- `H11_VOL_60` — long low 60-day realized vol, hold 20, quintile
- `H12_VOL_120` — long low 120-day realized vol, hold 20, quintile

dataset_id = `tm-ashare-EQUITY-D1-20260830-000002`  
contract_hash = `b48b2657c4991041fb4e8f9fafa33c53c40be29222a1b39f87d24a82f596f75e`

Validation cost-adjusted CAGR is about **0.55% / 1.30%**. This is **not** a 10% path and not a trading license.

Momentum (locked long-winners) failed. Do not flip its sign.  
Reversal / low-turnover beat the market on validation but **lost money after cost** — not Candidate.

This mission **stops**. Do not test a 13th factor. Do not optimize lookback/hold/quantile.
