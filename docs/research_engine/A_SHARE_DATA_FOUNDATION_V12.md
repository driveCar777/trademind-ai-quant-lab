# A-share data foundation V12

**Date:** 2026-08-30
**Purchase:** NO
**Alpha:** NO
**Backtest:** NO

```
LEVEL = 0
CANDIDATE = 0
A_SHARE_DATA_STATUS = CONDITIONAL
NEXT_PRIMARY_ACTION = FREEZE_FULL_EQUITY_DAILY_PANEL
```

This is a data layer, not a strategy.

## Tree

`data/market/cn_a_share/{raw,normalized,reference,corporate_actions,financial,announcements,manifests,quality,research}`

## Canonical

BaoStock. No key. AkShare-class HTTP is cross-check only.

## What exists

- Security basic with listing/delisting fields
- China trading calendar (Asia/Shanghai)
- As-of universe snapshots: **202** dates
- Daily sample + corporate-action sample (600519)
- Financial sample with `pubDate`
- Delist bar census: done=True n=337 empty=2

## What does not exist

- Full equity daily panel (too large for Git; not frozen this run as RESEARCH)
- Point-in-time industry
- RESEARCH_READY financial panel
- Official exchange delist tape

## Sixteen answers

1 Free A-share data enough? Enough to start a PIT foundation. Not enough to mark RESEARCH_READY. Full daily panel is not frozen.
2 BaoStock canonical? Yes, as the only free programmatic source that actually returned listing, delist, bars, CA, calendar, and pubDate.
3 AkShare cross-check only? Yes. Not installed. EM HTTP SSL failed. Fragile. Not a store.
4 Historical delisted stocks? Vendor table has 337 type-1 delisted names. Bars exist for sampled names including 1991-era 000003. Full 337 census: done=True empty=2
5 Listing dates? Yes. `ipoDate` on `query_stock_basic`. Blank is UNKNOWN, not invented.
6 Suspensions? Yes on daily kline `tradestatus`. Do not treat as zero return.
7 ST? Yes on daily kline `isST`. Metadata only. Not alpha.
8 Adjustment? Yes. raw / qfq / hfq via adjustflag 3/2/1. Convention recorded.
9 Corporate action verifiable? Yes on sample: 600519 cash dividend operate 2023-06-30; raw≠qfq; adjust_factor present.
10 Trading calendar complete? BaoStock `query_trade_dates` 1990-12-19→2026-08-29. n_days=13038 n_trading=8714. 2024-01-01 holiday.
11 Financial announcement date? Yes (`pubDate`). Sample only. Full financial dataset is not RESEARCH_READY.
12 Survivorship bias? Reduced vs listed-only vendors. Residual vendor-table risk. Census empty_rate=0.005934718100890208
13 Point-in-time pass? Membership + knowledge-time + mutation tests on samples: see A_SHARE_PIT_TEST_V12.json. Industry PIT fails.
14 RESEARCH_READY? No. Status=CONDITIONAL. Label=A_SHARE_RESEARCH_CONDITIONAL.
15 Blockers / gaps blocking=[] limitations=['AKSHARE_CLASS_HTTP_FRAGILE', 'FINANCIAL_DATASET_NOT_RESEARCH_READY', 'FULL_DAILY_PANEL_NOT_FROZEN', 'INDUSTRY_NOT_POINT_IN_TIME', 'VENDOR_DELIST_TABLE_NOT_EXCHANGE_OFFICIAL']
16 Data cost $0
