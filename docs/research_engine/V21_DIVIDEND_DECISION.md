# V21 Decision

**A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE**

NEXT = `DIVIDEND_EVENT_NO_CANDIDATE`. STOP = `STOP_B_FAMILY`.

```
LEVEL = 1
CANDIDATE = 2
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
```

Question: do cash or stock dividend *announcement windows* contain a costed independent A-share CS edge?
Not a high-yield quintile. Not V16 ROE.
PIT: announce_date < signal. pit_test_ok=True.
FDR m=2 discoveries=[].
Candidate: L1=0 independent=0.

| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|
| D1_CASH_ANN_20 | DIVIDEND_CASH_EVENT | -4.24% | -97.07% | -41.06% | -36.68% | -0.0223 | False | False | None |
| D2_STOCK_ANN_20 | DIVIDEND_STOCK_EVENT | -16.48% | -100.00% | -72.02% | -92.34% | -0.0234 | False | False | None |
