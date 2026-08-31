# Candidate decision V13.1

**Date:** 2026-08-31  
**Purchase:** $0  
**Final OOS:** DENIED  
**Strategy construction:** NOT STARTED  

```
H11 = CANDIDATE_SURVIVED
H12 = CANDIDATE_SURVIVED

LEVEL = 1
CANDIDATE = 2

NEXT = STRATEGY_CONSTRUCTION

STRATEGY = FALSE
PAPER = FALSE
LIVE = FALSE
FINAL_OOS = DENIED
```

Both Candidates **exist** under the locked overlapping Level 1 gate. They are **real and weak**. Validation cost-adjusted CAGR remains **0.55% / 1.30%**. Distance to a long-term 10% goal is still very large. Level 1 ≠ Level 2.

Do **not** retune lookback, hold, quantile, or sign. Do **not** combine H11+H12. Do **not** crown H12. Do **not** add H13.

## Twenty questions

1. H11 independent repro? **Yes.** Path A = original. Path B agrees. Deterministic.
2. H12 independent repro? **Yes.** Same.
3. Research still + after cost? **Yes** (official overlapping `mean_net_h`).
4. Validation still + after cost? **Yes** (official overlapping `mean_net_h`).
5. Cost-adjusted still +? **Yes** at 1.0x official cost. H11 fails 1.5x stress.
6. Rank IC kept? **Yes** (H11 val 0.117, H12 val 0.110).
7. FDR consistent? **Yes.** Historical BH discovery only. No new 12-test search.
8. Few stocks? **No.** ~900 filled names/day; top 1% of names ≈ 8% of winner PnL.
9. Few days? **Not a one-week artifact.** Top 10% of val days ≈ 41–42% of winner-day PnL. Net is thin; many days lose.
10. Single year? **No.** 2014–15 and 2021 help; 2011 and 2018 hurt. 2022–23 inside validation are flat/negative.
11. Capacity problem? **No mandate.** Unit-book ADV diagnostic only. Do not announce AUM.
12. Only beta / liquidity? **Possible.** Beta ≈ 0.66. Industry PIT blocked. Size field missing. Recorded as LIMITATION, not a new neutralized Candidate.
13. PIT clean? **Yes** for 2026 IPO vs 2020 membership and delist mutation.
14. Corporate action clean? **Limited.** Raw close ranking. qfq panel not frozen. Jump-day scan 0/100k. LIMITATION.
15. Suspension correct? **Yes.** 0 suspended fills among audited filled names.
16. Execution correct? **Yes.** Hold 20. Signal close(t), fill open(t+1). Limit-lock implemented; 0.002 buffer needs contract clarification only.
17. H11 `CANDIDATE_SURVIVED`? **Yes.**
18. H12 `CANDIDATE_SURVIVED`? **Yes.**
19. If survive, next = Strategy Construction? **Yes, as the next mission. Not this one.**
20. If failed, why? **Neither failed the official gate.** Fragility: cost stress, block-bootstrap, and the 20-day nonoverlap validation book (H11 negative, H12 ≈ 0).

## What this is not

- Not a 10% CAGR claim.
- Not permission to trade.
- Not permission to read Final OOS.
- Not permission to optimize until the nonoverlap book looks better.

This mission **STOPS**.
