# Post-V21 Disk Inventory — Q2

**Date:** 2026-09-04  
**No BaoStock login.** Listing from `data/market/cn_a_share/` plus `A_SHARE_SOURCE_MATRIX_V12.json` / catalogs / V13–V21 decisions.  
**Machine:** `POST_V21_AUTODRIVE/Q1_Q2.json` → `q2_full`

Canonical source: **BAOSTOCK**. Tushare = NOT_USED / paid. Scrape sources = NOT_TRUSTED.

Disk top-level: `A_SHARE_*.json`, `announcements/`, `corporate_actions/`, `dividend/`, `financial/`, `index/`, `industry/`, `manifests/`, `normalized/` (gitignored bars), `quality/`, `reference/`, `research/`.

| Object | Mechanism | PIT | V13–V21 wrapper? | Status |
|---|---|---|---|---|
| EQUITY_D1_PANEL | Daily bars | YES V12.2 | Every CS family | ALREADY_TESTED |
| UNIVERSE / BASIC / CALENDAR | Listing, ST, sessions | YES | V18 + eligibility | ALREADY_TESTED |
| FINANCIAL_ANNUAL | Annual after announce | YES V16 | F1–F6 | ALREADY_TESTED |
| INDUSTRY_MONTHLY | As-of membership | YES | I1–I3, IM1–IM6 | ALREADY_TESTED |
| INDEX HS300/ZZ500 | Monthly as-of / add-drop | YES V20 | X1–X4 | ALREADY_TESTED |
| DIVIDEND_EVENTS | Announce windows | YES V21 | D1/D2 | ALREADY_TESTED |
| FORECAST / EXPRESS | Filing then 20d long | would-be | Same as V21 | LOW_VALUE |
| CA SAMPLE | Representation, not signal | sample | DIVIDEND_EXCLUSION | LOW_VALUE |
| QUARTERLY / LEVERAGE | Slow accounting twin | possible | V16 sibling; locked | LOW_VALUE |
| DIVIDEND YIELD LEVEL | Quality/size neighborhood | YES | LOW_VALUE after V16+V20 | LOW_VALUE |
| FROZEN MACRO | EURUSD/US500/GVZ × CS | published | V17/V19 | ALREADY_TESTED |
| TUSHARE / WIND / CHOICE / CSMAR | Vendor | unknown | paid | PAYMENT_REQUIRED |
| LO/OG OPTIONS MVD | IV on 4 CFD names | vendor | paid; V9/V10 dead | PAYMENT_REQUIRED |

**AVAILABLE count = 0.**

**NONE** is issued *after* this table, not before.

Q3 is skipped. No legal new object. Queue → Q4.
