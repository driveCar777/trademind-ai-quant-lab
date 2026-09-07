# Options Data Requirement Spec

2026-09-02. **PAYMENT_REQUIRED**. No purchase in this mission. $93 unused.

## What would be needed (A-share or US metals)

| Item | Why | Granularity | History | PIT |
|---|---|---|---|---|
| Listed option identifiers + expiry | Universe | daily | ≥10y preferred; 1y is a probe | as-of membership |
| Settlement or reliable mid | IV / skew | EOD | same | knowledge ≤ signal date |
| Bid/ask or official settle | executable IV | EOD | same | no backfilled mid |
| Underlying close aligned | IV−RV | EOD | same | next-bar open for any book |
| OI / volume | positioning, not required for first ATM test | EOD | same | lagged 1 day |

A-share exchange options are **not** in the repo. V8.2–V8.4 only quoted Databento `OG.OPT` / `LO.OPT` (metals), `downloaded=false`.

## Expected information value

True IV / skew / VRP is still the largest **untested** non-price field in the 12M map. It is also the most expensive. V2 index IV (GVZ/OVX) on GOLD/OIL already `NO_CANDIDATE`. That does **not** test an option surface.

## Cost (already quoted, not spent)

- If a human later buys one metals pack: LO 1Y MVD-A **$11.99** (V8.4 CASE A). Not automatic.
- CN equity options vendors (Tushare/Wind/Choice) remain forbidden without a new purchase decision.

## Status

`PAYMENT_REQUIRED`

This mission does not buy, simulate IV, or invent surfaces. Continue free families.
