# V18 Decision

**A_SHARE_ALTINFO_V1_NO_CANDIDATE**

NEXT = `ALTINFO_NO_CANDIDATE`. STOP = `STOP_B_FAMILY`.

```
LEVEL = 1
CANDIDATE = 2
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
```

Question: do listing age / ST streak / resume / calendar windows contain a costed independent A-share CS edge?
Data: frozen basics + pack isST/tradestatus + CN calendar.
PIT: dates and flags through signal date.
FDR m=6 discoveries=[0, 1].
Candidate: L1=0 independent=0.
Next: ALTINFO_NO_CANDIDATE.

| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|
| A1_SEASONED_AGE | LISTING_AGE | -0.50% | -22.11% | -10.56% | -4.26% | 0.0399 | True | False | None |
| A2_RELATIVE_AGE | LISTING_AGE | -0.50% | -22.11% | -10.56% | -4.26% | 0.0399 | True | False | None |
| A3_CLEAN_STREAK | ST_HISTORY | -1.06% | -66.99% | -31.92% | -13.93% | -0.0144 | False | False | None |
| A4_RECENT_RESUME | SUSPEND_RESUME | -1.30% | -66.00% | -34.42% | -15.18% | -0.0443 | False | False | None |
| A5_MONTH_END_SEASONED | CALENDAR_WINDOW | 0.12% | -30.25% | -19.95% | -10.62% | 0.0441 | False | False | None |
| A6_QUARTER_END_SEASONED | CALENDAR_WINDOW | -2.61% | -26.77% | -34.98% | -40.60% | 0.0342 | False | False | None |
