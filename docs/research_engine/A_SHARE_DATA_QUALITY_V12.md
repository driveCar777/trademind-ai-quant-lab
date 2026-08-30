# A-share data quality V12

**Date:** 2026-08-30

Download is not READY.

## Scores

- SECURITY_BASIC: **CONDITIONAL**
- TRADING_CALENDAR: **PASS**
- UNIVERSE_HISTORY: **PASS**
- DAILY_SAMPLE: **CONDITIONAL**
- CORPORATE_ACTION_SAMPLE: **PASS**
- FINANCIAL_SAMPLE: **CONDITIONAL**
- INDUSTRY: **CONDITIONAL**
- DELIST_CENSUS: **CONDITIONAL**

## Calendar

- 2024-01-01 trading: False (must be false)
- 2024-01-02 trading: True (must be true)
- Timezone: Asia/Shanghai. UTC label stored. Not UTC+1.

## Price sample

- 600519 raw bars: 30
- Sample integrity ok: True
- Full panel frozen: NO

## Adjustment

- raw ≠ qfq on 2023-06 window: True
- overlap: 30
- n raw≠qfq: 30

## ST / suspension

- `tradestatus=0` = suspension. Do not treat as zero return.
- `isST` is daily metadata. Not an alpha.
- Universe history cannot count ST from `query_all_stock` (field absent).

## Universe anomalies

- Concurrent BaoStock sessions can return empty `query_all_stock`. Factory now rejects n_all=0.
- 2015-04-30 still has `n_all=2000` from a dying first session (neighbors 2015-03-31=3217, 2015-05-29=3291). Do not use that month as a size fact.
- 202 as-of dates otherwise repaired; zeros=0 after re-fetch.
