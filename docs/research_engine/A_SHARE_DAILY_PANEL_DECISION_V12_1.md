# A-share daily panel decision V12.1

```
PRICE_ALPHA_STATUS = PRICE_ALPHA_CONDITIONAL
FINANCIAL_ALPHA_READY = FALSE
INDUSTRY_ALPHA_READY = FALSE
EVENT_ALPHA_READY = FALSE
dataset_id = tm-ashare-EQUITY-D1-20260830-000001
content_hash = 125a73a3555c1f4bcb79a7aaa3a00a06ea84fbfd0038cdd1df599d35c1c8594b
NEW_PURCHASE = FALSE
ALPHA_RESEARCH = FALSE
```

If PRICE_ALPHA_READY, next is CHINA_A_SHARE_ALPHA_DISCOVERY. This mission does not run it.

## Twenty-seven answers

1 symbols in master. 5549
2 trading days. 8714
3 rows (done symbols). 128817
4 history start. 1990-12-19
5 history end. 2026-08-28
6 listed now (2026-08-28 PIT). 5212
7 delisted vendor. 337
8 symbols with bars. 20
9 symbols without bars. 0
10 mean daily listed. 2114.1
11 min/max daily listed. 8 / 5212
12 why 2015-04-30 = 2000. Session truncation (and 2000 looks like a page). PIT listing-window is 2695. Snapshot ends at sz.002273.
13 repaired?. No. Status remains INVALID. Not interpolated.
14 PIT. Listing-window yes. Vendor snapshot for that day no.
15 survivorship. 335/337 had bars in V12 census. Empty names kept.
16 adjustment. sample raw≠qfq = 20
17 suspension. tradestatus=0 is NO_TRADE
18 corporate action. adjust_factor stored per symbol when vendor returns it
19 price integrity. 0
20 determinism. vendor CSV rewrite uses .part then rename; hash stable
21 resume. checkpoint skips done symbols whose raw.csv exists
22 dataset_id. tm-ashare-EQUITY-D1-20260830-000001
23 content hash. 125a73a3555c1f4bcb79a7aaa3a00a06ea84fbfd0038cdd1df599d35c1c8594b
24 DATA_STATUS. CONDITIONAL
25 PRICE_ALPHA. PRICE_ALPHA_CONDITIONAL
26 FINANCIAL_ALPHA. BLOCKED
27 INDUSTRY_ALPHA. BLOCKED
