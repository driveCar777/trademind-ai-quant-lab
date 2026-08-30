# A-share ready decision V12.2

```
PRICE_ALPHA_STATUS = PRICE_ALPHA_READY
FINANCIAL_ALPHA_READY = FALSE
INDUSTRY_ALPHA_READY = FALSE
EVENT_ALPHA_READY = FALSE
FULL_PANEL_FROZEN = True
NEXT_PRIMARY_ACTION = CHINA_A_SHARE_ALPHA_DISCOVERY
NEW_PURCHASE = FALSE
ALPHA_RESEARCH = FALSE
```

If PRICE_ALPHA_READY, next is CHINA_A_SHARE_ALPHA_DISCOVERY. This mission does not run it.

## Twenty-three answers

1 5549 processed. 5549 / 5549
2 with bars. 5549
3 empty. 0
4 total rows. 18418047
5 trading days. 8714
6 history. 1990-12-19 / 2026-08-28
7 2015-04-30. INVALID vendor 2000; PIT window 2695
8 PIT. True
9 survivorship. vendor table + 0 empty DATA_GAP
10 suspension. tradestatus=0 NO_TRADE
11 adjustment. raw panel first; qfq later; V12 sample still valid
12 raw integrity. neg=0 ohlc=1
13 duplicates. 0
14 future leakage. True
15 determinism. raw.csv rewrite uses .part; skip if exists
16 resume. VERIFY_EXISTING raw.csv skip
17 dataset_id. tm-ashare-EQUITY-D1-20260830-000002
18 hash. dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80
19 PRICE_ALPHA. PRICE_ALPHA_READY
20 FINANCIAL_ALPHA. BLOCKED
21 INDUSTRY_ALPHA. BLOCKED
22 EVENT_ALPHA. BLOCKED
23 NEXT. CHINA_A_SHARE_ALPHA_DISCOVERY
