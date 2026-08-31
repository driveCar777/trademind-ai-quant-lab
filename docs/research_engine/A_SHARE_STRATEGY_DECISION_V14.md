# Strategy decision V14

**Date:** 2026-08-31  
**Purchase:** $0  
**Final OOS:** DENIED  
**Paper:** NO  

```
H11 = STRATEGY_WEAK_BUT_RESEARCHABLE
H12 = STRATEGY_WEAK_BUT_RESEARCHABLE

OVERALL = STRATEGY_WEAK_BUT_RESEARCHABLE

LEVEL = 1
CANDIDATE = 2
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0

CLUSTER = LOW_VOL_CANDIDATE_CLUSTER
NEXT = LOW_PRIORITY

FINAL_OOS = DENIED
optimize_toward_10pct = NO
```

Level 2 **process** gate (survived, executable, cost complete, PIT clean, no hidden opt, economics disclosed, stress available): **PASS**.  
10% CAGR is **not** a Level 2 gate.

They are **not** `STRATEGY_READY_FOR_LONG_VALIDATION` because the official 20-day capital book lost money from 2010 through validation (H11 −15.6%, H12 −10.5%, MaxDD −66%) and validation-fresh CAGR is 0.12% / 0.74%. The Candidate overlapping +0.55% / +1.30% is a different statistic.

Candidate mechanism remains. Do not delete H11/H12. Do not retune. Do not add H13. Do not blend them as two alphas.

## Twenty-five questions

1. H11 executable? **Yes.**  
2. H12 executable? **Yes.**  
3. True strategy CAGR? Full path **−1.13% / −0.74%**. Val fresh MTM **+0.12% / +0.74%**.  
4. MaxDD? Full **−66%**. Val fresh **−24%**.  
5. Sharpe? Full 0.05 / 0.07. Val 0.09 / 0.13.  
6. Sortino? Full 0.06 / 0.08. Val 0.11 / 0.16.  
7. Turnover? Daily 0.10; annual two-way 24.2. Hold 20.  
8. Cost drag? Full-path fees+slip are large vs the thin edge.  
9. Unfilled rate? **1.75% / 1.83%**.  
10. Limit-lock rate? **0.49% / 0.51%**.  
11. Liquidity? 1e6 book P95 pos/ADV ≈ 2e-4. No AUM claim.  
12. CA sensitivity? Raw-only. 0 jump-days >12% in fills. `REPRESENTATION_RISK`. No qfq switch.  
13. Few stocks? **No.**  
14. Few years? **No**, but 2011/2018 dominate losses.  
15. Few days? Top 10% of rebalances ≈ half of winner-period PnL. Typical, not one week.  
16. 1.5x cost still + on val realized? **Yes, barely.**  
17. 2x cost? H11 **no**. H12 barely +.  
18. Still highly correlated? **Yes, 0.994.**  
19. One `LOW_VOL_ALPHA_CLUSTER`? **Yes.**  
20. Level 2 process gate? **Yes.** Economic strength for long validation? **No.**  
21. Worth LONG_VALIDATION now? **No. LOW_PRIORITY.**  
22. External live data now? **No.**  
23. Future paper needs: live raw price, PIT universe, halt/limit, orders.  
24. Gap to 10%: about **9.9 / 9.3 pp** on val MTM CAGR; full-path CAGR is negative.  
25. Optimize for 10%? **NO.**

This mission **STOPS**.
