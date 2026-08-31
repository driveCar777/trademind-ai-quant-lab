# V14.1 Decision

**METHODOLOGY_GAP_CONFIRMED**

NEXT = `KEEP_CANDIDATE_STRATEGY_WEAK_NO_LONG_VALIDATION`

```
LEVEL = 1
CANDIDATE = 2
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0
```

H11/H12 remain Candidates. Strategy remains WEAK. Not two sleeves. Capital correlation 0.9959656057073649. Overlap correlation 0.9956077026823058.

## 22 questions

1. Why Candidate positive: The Level 1 number is the mean of overlapping 20-day filled open-to-open returns minus one round-trip, then (1+mean)^(242/20)-1. That mean stayed slightly positive.
2. Why V14 full path negative: The official object is one non-overlapping 20-day capital account that compounds (1+period_return). Compounding, the 20-day grid sample, cash residual on unfilled, and multiplicative costs are a different economic object and lost money on the full path.
3. Overlap core? Yes for the published Candidate CAGR. That number is an overlapping mean, then (1+mean)^(242/20)-1. It is not a book.
4. Non-overlap core? Partial. All 20 offset grids compound to a loss, so the official grid is not a bad draw. The nonoverlap arithmetic mean is still slightly positive. The capital killer is compounding a fat left tail (AM-GM), not a negative mean.
5. Entry timing consistent? **YES** — close(t) signal, open(t+1) fill.
6. Exit timing consistent? **YES** — open(t+1+20), 20 trading days.
7. Unfilled error? **NO** — 0 PnL, 0 fees, cash residual.
8. Limit-lock error? **NO** — never filled, no phantom later return.
9. Cost double count? **NO**.
10. Corporate action? REPRESENTATION_RISK_RAW_CLOSE
11. Dividend omitted? **YES** — DIVIDEND_EXCLUSION, price return only.
12. −66% DD: 2015-06 peak to 2018-10 trough, no recovery
13. One mechanism? **YES** — LOW_VOL_CANDIDATE_CLUSTER. Do not blend.
14. H11 still researchable? **YES** as a Candidate. **NO** as a capital edge.
15. H12 still researchable? **YES** as a Candidate. **NO** as a capital edge.
16. Executable? **YES** — process complete, fills defined.
17. Level 2 process gate? **YES**. Economic gate? **NO**.
18. Long Validation? **NO**.
19. Why not: Full-path capital is negative and far from 10%. Methodology gap, not a hidden edge.
20. New data? **NO**.
21. Retune? **NO**.
22. Make H12 into 10%? **NO**.

## Next

Keep H11/H12 Candidate status. Strategy stays WEAK. Do not Long Validate. Do not combine H11+H12. Do not optimize lookback / hold / quantile. Do not buy data. Final OOS remains DENIED.
