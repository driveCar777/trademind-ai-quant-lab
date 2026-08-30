# A-share source audit V12

**Date:** 2026-08-30  
**Purchase:** NO  
**Key:** none  

Live calls were made. Documentation was not trusted alone.

## BaoStock (canonical candidate)

- Package `baostock==0.9.3`. Login `error_code=0`. No credential.
- `query_all_stock()` without `day=` returns **0** on a Sunday. Must pass a trading `day=`.
- `query_all_stock(day=2015-06-15)` n=3318; `2020-01-02` n=4306; `2024-01-02` n=5638.
- `query_stock_basic()` n=8928. Fields: `code, code_name, ipoDate, outDate, type, status`.
- Type 1 equity: 5212 listed + **337 delisted**.
- Type 5 on-exchange fund/ETF: 1651 listed. Index type 2 present.
- Daily kline `adjustflag` 3=raw, 2=qfq, 1=hfq. Fields include `turn`, `tradestatus`, `isST`, volume, amount.
- `query_adjust_factor` and `query_dividend_data` return operate dates and cash/stock fields.
- Financials (`query_profit_data` …) return **`pubDate` + `statDate`**. 茅台 2023Q4 `pubDate=2024-04-03`.
- Industry `query_stock_industry()` n=5545, **`updateDate=2026-08-24` only**. Not point-in-time.
- HS300 **is PIT** if `date=` is passed: 2026-08-24 vs 2018-06-25, symmetric_diff=258.

## AkShare-class HTTP (cross-check only)

- AkShare was **not installed** (large scrape stack).
- East Money public kline HTTP: **SSL record layer failure**. Fragility recorded.
- Not canonical. Not a store.

## Paid sources

- Tushare Pro / Wind / Choice / CSMAR: **not used**. Not purchased.

## Verdict

- CANONICAL = BaoStock
- SECONDARY = AkShare-class HTTP
- NOT TRUSTED = scrape-as-store
- Cost = **$0**
