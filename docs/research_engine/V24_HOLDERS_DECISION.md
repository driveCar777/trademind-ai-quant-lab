# V24 Shareholder-Count Concentration Decision

**A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE** — STOP_B_FAMILY

**Date:** 2026-09-04  
**Cost:** $0. 5549 symbols fetched, 0 failures, 297,732 announced reports with `HOLD_NOTICE_DATE` used; notice dates after 2024-02-29 dropped at compile.  
**Contract:** `V24_HOLDERS_CONTRACT.md` (pre-registered).  
**Machine:** `data/market/research_engine/cn_a_share_holders_v24/{RESULTS,FDR,FAILURES,CANDIDATES,DECISION,HOLDERS_DATASET,CORR_MONTH}.json`, `EQUITY/`, `TRADES/`

```
LEVEL = 1   CANDIDATE = 2   NEW_CANDIDATE = 0   NEW_INDEPENDENT = 0
FDR m=3 q=0.05 discoveries = []
```

Coverage (median names with a visible score): 2013 2159 → 2017 3357 → 2021 4594 → 2023 5060. Effective books start 2013.

## Results

| ID | Research MF / excess vs EW (t) / IC | Research capital | Validation MF / excess (t) / IC | Validation capital | corr H11 (month) |
|---|---|---|---|---|---|
| HC1_CONCENTRATION_QOQ | +0.27% / **−0.08% (t −2.65)** / 0.016 | −16.0%, MaxDD −71% | −0.88% / −0.15% (t −3.90) / 0.017 | −25.5% | 0.63 |
| HC2_CONCENTRATION_2Q | +0.41% / −0.01% (t −0.33) / 0.027 | +1.2%, MaxDD −70% | −0.89% / −0.17% (t −4.43) / 0.023 | −26.4% | 0.64 |
| HC3_LOW_HOLDERS_PER_SHARE | +0.34% / −0.02% (t −0.34) / 0.024 | +0.2%, MaxDD −62% | −0.75% / −0.02% (t −0.18) / 0.017 | −18.2% | 0.72 |

All three fail on research excess (≤ 0), validation excess (< 0), validation capital (< 0), FDR.

## Reading

"筹码集中" does not beat the eligible equal-weight book after cost in either window. Rank IC is a small positive (0.016–0.027) in both windows — i.e. the ordering carries a whisper of information — but the top quintile does not outperform EW and the long-only book loses money the same way every A-share sleeve has. The three books correlate 0.63–0.72 with H11 at month level: concentrated-ownership names overlap with quiet, low-vol names.

Contrast with V23 M1: margin inflow had a research-real edge (t +4.85) that vanished in validation; holder concentration has no research edge to lose. It is the more ordinary failure.

Frozen. No retune of report horizon or quintile. No sign flip. No monthly-disclosure subset.

## Queue

One free, PIT-able, non-tested object remains reachable: **northbound (陆股通) daily per-stock holdings** (HKEX CCASS, 2017-03 → ; Eastmoney mirror). Coverage is short (research 2017-03 → 2021-08 ≈ 4.5 years) and that limitation must be written into its contract before running. After that, the free A-share behavioral layer (margin, holders, northbound) is either exhausted or has produced a Candidate.
