# V17 Decision

**A_SHARE_MACRO_INFORMATION_V1_NO_CANDIDATE**

NEXT = `MACRO_NO_CANDIDATE`. STOP = `STOP_B_FAMILY`.

```
LEVEL = 1
CANDIDATE = 2
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0
```

H11/H12 KEEP_LOW_PRIORITY. No purchase. Final OOS DENIED.

## Versus long-term CAGR >= 10%

10% is not a gate. Do not retune toward it.

## Answers

- Question: does frozen public macro contain a costed, FDR-valid, H11-independent A-share CS edge?
- Hypothesis: 6 pre-registered beta×shock mappings.
- Data: frozen price 000002 + EURUSD + US500 + GVZ.
- PIT: macro_date < signal_date.
- Sample: 70/15/15 locked. Denied unused.
- Costs: A_SHARE_STRATEGY_COST_MODEL_V1.
- Multiple testing: BH q=0.05 m=6.
- FDR discoveries: [].
- Capital validation: see table. CAGR only from non-overlapping book.
- Candidate status: L1=0 independent=0.
- Decision: A_SHARE_MACRO_INFORMATION_V1_NO_CANDIDATE / STOP_B_FAMILY.
- Next action: MACRO_NO_CANDIDATE.

| ID | Family | L | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_USD_DEF_60 | USD_STRENGTH_DEFENSIVE | 60 | -1.25% | -55.89% | -44.01% | -20.26% | -0.0068 | False | False | None |
| M2_USD_DEF_120 | USD_STRENGTH_DEFENSIVE | 120 | -1.18% | -55.36% | -39.81% | -17.98% | -0.0039 | False | False | None |
| M3_US_CONT_60 | GLOBAL_EQUITY_CONTINUATION | 60 | -1.04% | -45.96% | -23.30% | -9.83% | -0.0001 | False | False | None |
| M4_US_CONT_120 | GLOBAL_EQUITY_CONTINUATION | 120 | -1.01% | -36.59% | -18.68% | -7.75% | -0.0037 | False | False | None |
| M5_GVZ_DEF_60 | GOLD_VOL_DEFENSIVE | 60 | -1.06% | -54.07% | -40.13% | -18.15% | 0.0046 | False | False | None |
| M6_GVZ_DEF_120 | GOLD_VOL_DEFENSIVE | 120 | -0.90% | -54.99% | -30.70% | -13.34% | 0.0023 | False | False | None |
