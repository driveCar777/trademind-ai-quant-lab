# A-share alpha V1 decision

```
DECISION = LEVEL_1_CANDIDATE
LEVEL = 1
CANDIDATE = 2
NEW_PURCHASE = FALSE
FINAL_OOS = DENIED
NEXT = CANDIDATE_REPRODUCTION
```

1. 12 hypotheses: H01_MOM_20, H02_MOM_60, H03_MOM_120, H04_REV_20, H05_REV_60, H06_REV_120, H07_ACT_20, H08_ACT_60, H09_ACT_120, H10_VOL_20, H11_VOL_60, H12_VOL_120
2. positive (window flag): ['H04_REV_20', 'H05_REV_60', 'H06_REV_120', 'H07_ACT_20', 'H08_ACT_60', 'H09_ACT_120', 'H10_VOL_20', 'H11_VOL_60', 'H12_VOL_120']
3. negative both windows: ['H01_MOM_20', 'H02_MOM_60', 'H03_MOM_120']
4. inconclusive: those with mixed windows
5. FDR discoveries: [11, 3, 10, 9, 5, 6, 4, 7, 8]
6-8. see report IC / rank IC / spread
9-13. see validation metrics
14. capacity = median ADV diagnostic only
15. most stable: see by_year
16. year coverage 2010-2026 in by_year
17. survivorship: PIT listing/delist + delisted names kept in panel
18. PIT: membership from ipo/outDate; no 2026 backfill
19. Level 1 Candidate: ['H11_VOL_60', 'H12_VOL_120']
20. why: gates passed
21. next: new contract only if exhausted; not a 13th lookback
