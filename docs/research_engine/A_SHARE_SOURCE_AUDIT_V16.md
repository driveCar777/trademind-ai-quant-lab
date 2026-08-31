# V16 Source Audit

2026-08-31. Free sources only. NEW_PURCHASE = FALSE.

## Financial (BaoStock)

- `query_profit_data` live. Fields include `pubDate`, `statDate`, `netProfit`, `MBRevenue`, `roeAvg`, `gpMargin`, `npMargin`, `epsTTM`.
- 茅台 2023 annual `pubDate=2024-04-03`. On 2024-01-01 it is hidden. 2022 annual is visible.
- No revision table. **RESTATEMENT_RISK**.
- `epsTTM` is vendor TTM, not period EPS. ROA unavailable on profit. `liabilityToAsset` exists on balance.
- ~0.32s per profit call. Annual Q4 panel is the freeze (quarterly exists, not swept).

## Industry (BaoStock)

- `query_stock_industry()` without date is today's snapshot (`updateDate=2026-08-31`). That alone is CURRENT_ONLY.
- **`query_stock_industry(date=)` works.** 2010-06-15 n=1926; 2015-06-15 n=2842; 2020-01-02 n=3869; 2024-01-02 n=5330.
- 300750 absent in 2010/2015. Taxonomy changed ~2015. Then-current labels are used. Monthly as-of grid is the PIT freeze.

## Not used

AkShare not installed. East Money HTTP cross-check only. Tushare/Wind/Choice/CSMAR/Databento/options untouched.
