# A-share Alpha V2 Decision

**NO_NEW_CANDIDATE**

NEXT = `A_SHARE_PRICE_ALPHA_REVIEW_V2`

```
LEVEL = 1
EXISTING_CANDIDATE = 2
NEW_CANDIDATE = 0
CANDIDATE = 2
STRATEGY = 2
PORTFOLIO = 0
```

H11/H12 remain KEEP_LOW_PRIORITY. Do not reopen. Do not retune. Do not Long Validate.
Do not flip signs. Do not add a tenth hypothesis. Final OOS DENIED. Purchase = FALSE.

Cluster diagnostic (not a portfolio): {'H21_RESID_REV_20_H20': None, 'H22_RESID_REV_60_H20': None, 'H23_RESID_REV_20_H5': None, 'H24_DISP_HIGH_RESID_20_H20': None, 'H25_DISP_UP_RESID_20_H20': None, 'H26_DISP_HIGH_LOW_BREADTH_20_H20': None, 'H27_CAPITULATION_20_H20': None, 'H28_CAPITULATION_60_H20': None, 'H29_PX_AMT_CORR_20_H20': None}

## Questions

1. New Candidate? **NO**.
2. How many? **0**.
3. Independent of H11/H12? No new Candidate. Residual / disagreement-corr tracks LOW_VOL (predictive corr ≈ 0.90–0.94). Dispersion states thin the book; predictive corr still ≈ 0.91.
4. Research capital positive? Some (H21/H22/H24/H26/H29). Not a Candidate without validation capital.
5. Validation capital positive? **NO for all 9.**
6. Real CAGR? None official. Closest miss H24 research CAGR 6.39%; validation CAGR -7.05%.
7. MaxDD? H24 research -44.6% (2015-12-28 → 2018-10-24). Validation -26.2%.
8. Sharpe? H24 research 0.349; validation -0.178.
9. Rank IC? H24 research 0.0744; validation 0.1079.
10. FDR? 6/9 discoveries on excess-vs-EW. 0/9 Level 1.
11. Profit concentration? Typical top 10% of positive names ≈ 50–70% of positive stock PnL. Left tail remains.
12. Year stability? 2015 large; 2011/2017/2018 drawdowns. Validation 2023 often the killer year. Years are diagnostic, not a selector.
13. Cost sensitivity? Not run (no Level-1). 5-day hold H23 already dies at 1x — turnover, not a cheaper model.
14. Capacity? Unfilled 0.3–3%. No AUM announced. trade/ADV is not a gate.
15. PIT clean? **YES** — same frozen listed/ST/eligibility rules. No live API.
16. External data? **NO**. NEW_PURCHASE = FALSE. Databento ≈ $93 remains reserve. Options not bought.
17. Strategy construction? **NO**. No new Candidate. Do not build a portfolio from H11/H12 + failed V15 rows.
