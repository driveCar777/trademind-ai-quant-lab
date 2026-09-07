# V16 Decision

**A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE**

NEXT = `FINANCIAL_AND_INDUSTRY_NO_CANDIDATE`. STOP = `STOP_B`.

```
LEVEL = 1
CANDIDATE = 2
NEW_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0
```

H11/H12 KEEP_LOW_PRIORITY. Correlation ≈ 0.996. One cluster. Not two sleeves.
No purchase. Final OOS DENIED. Do not reopen price-only.

## Versus long-term CAGR >= 10%

10% is not an alpha gate. Do not retune toward it.
Existing strongest published strategy path (H11/H12 official 20-day book) is **negative full-path CAGR** (V14.1). Validation-fresh MTM was +0.12% / +0.74%. Gap to 10% is about 9–10 pp on that object.
V16 best Level-1 (if any): no Level-1; strongest scored (NOT a Candidate) F4_ROE_DELTA_ANN val CAGR -11.53%.

## Questions

1. Financial truly PIT? Knowledge-time on announcement_date: **True**. Values carry RESTATEMENT_RISK. Complete PIT: **NO**.
2. Financial coverage? symbols=5500 announcement_rate=1.0 coverage_2010=0.9364331959976456 coverage_ok=True
3. Restatement risk? **YES**. No historical revision table.
4. Industry PIT? **True** (status `INDUSTRY_PIT_OK`).
5. Industry classification changes? **YES** around 2015. n_2015_vs_2024_differ=638. Use then-current labels.
6. Financial alpha exists? **False** (Level-1 count in F* = 0).
7. Industry alpha exists? **False**.
8. New Candidate count? **0**.
9. Independent of H11/H12? independent=[] same_cluster=[]
10. Real capital CAGR? See CAPITAL report. Best Level-1: no Level-1; strongest scored (NOT a Candidate) F4_ROE_DELTA_ANN val CAGR -11.53%. H11/H12 full-path strategy CAGR remains negative (V14.1 FACT; not re-run).
11. MaxDD? See per-hypothesis capital. H11/H12 official book MaxDD ≈ −66% (V14.1, not re-run).
12. Sharpe? See per-hypothesis capital. Not a Candidate gate by itself.
13. FDR? unified BH q=0.05 m=9 discoveries=[]
14. IC / Rank IC? See FINANCIAL/INDUSTRY_RESULTS predictive.rank_ic. Predictive positive ≠ Candidate.
15. After cost? Capital books already use A_SHARE_STRATEGY_COST_MODEL_V1. Do not lower cost.
16. Profit concentration? See concentration / share_of_top on each book.
17. Year stability? See per-hypothesis year tables in the capital report.
18. Capacity? Validation unfilled_rate on each book. Eligible + limit/suspension contract unchanged.
19. Need new data? Only if both layers BLOCKED or the value review says information unavailable. Event still blocked.
20. Need purchase? **NO**.
21. Long Validation? **NO**.
22. Next unique legal route? `FINANCIAL_AND_INDUSTRY_NO_CANDIDATE`.

| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Val MaxDD | Val Sharpe | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1_YOY_NP_ANN | EARNINGS_GROWTH | -1.04% | -43.77% | -28.24% | -12.15% | -40.02% | -0.3739 | -0.0273 | False | False | None |
| F1_YOY_REV_ANN | EARNINGS_GROWTH | -1.38% | -55.26% | -35.78% | -15.87% | -45.89% | -0.5373 | -0.0377 | False | False | None |
| F2_ROE_ANN | PROFITABILITY | -1.63% | -67.47% | -40.87% | -18.54% | -48.18% | -0.7452 | -0.0446 | False | False | None |
| F2_GPM_ANN | PROFITABILITY | -0.96% | -52.64% | -27.61% | -11.85% | -37.79% | -0.3754 | -0.0192 | False | False | None |
| F3_NPM_ANN | QUALITY | -1.41% | -64.99% | -35.99% | -15.98% | -43.41% | -0.6666 | -0.0312 | False | False | None |
| F4_ROE_DELTA_ANN | FINANCIAL_CHANGE | -0.97% | -40.48% | -26.94% | -11.53% | -39.30% | -0.3574 | -0.0047 | False | False | None |
| I1_IND_RS_20 | INDUSTRY_RELATIVE_STRENGTH | -1.36% | -33.38% | -33.80% | -14.87% | -40.48% | -0.4835 | -0.0447 | False | False | None |
| I2_IND_RS_60 | INDUSTRY_RELATIVE_STRENGTH | -1.31% | -39.82% | -32.72% | -14.33% | -38.68% | -0.5237 | -0.0636 | False | False | None |
| I3_IND_BREADTH_20 | INDUSTRY_BREADTH | -1.27% | -25.46% | -28.86% | -12.45% | -37.19% | -0.3827 | -0.0361 | False | False | None |
