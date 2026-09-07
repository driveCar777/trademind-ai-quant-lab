# V20 Decision

**A_SHARE_INDEX_MEMBERSHIP_V1_NO_CANDIDATE**

NEXT = `INDEX_MEMBERSHIP_NO_CANDIDATE`. STOP = `STOP_B_FAMILY`.

```
LEVEL = 1
CANDIDATE = 2
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
```

Question: do CSI 300 / CSI 500 membership or 252-session add/delete sets contain a costed independent A-share CS edge?
Data: frozen price panel + BaoStock monthly index as-of.
PIT: effective_date <= signal. pit_test_ok=True.
FDR m=4 discoveries=[].
Candidate: L1=0 independent=0.
Next: INDEX_MEMBERSHIP_NO_CANDIDATE.

| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|
| X1_HS300_SET | INDEX_MEMBERSHIP | -1.26% | -56.49% | -32.50% | -14.22% | -0.0077 | False | False | None |
| X2_ZZ500_SET | INDEX_MEMBERSHIP | -1.00% | -38.68% | -23.88% | -10.10% | -0.0027 | False | False | None |
| X3_HS300_IN_252 | INDEX_RECONSTITUTION | -2.37% | -72.73% | -56.79% | -27.93% | -0.0217 | False | False | None |
| X4_HS300_OUT_252 | INDEX_RECONSTITUTION | -1.21% | -0.14% | -26.65% | -11.39% | -0.0189 | False | False | None |
