# Data Acquisition Plan

Read-only check. Does not overwrite `*-20260825-000001`. Does not `order_send`.

## Status

- **ACQUISITION_POSSIBLE**
- action: `write_plan_then_human_freeze_new_ids_do_not_overwrite_20260825`
- MT5 probe: PROBED 

## Targets

- D1: 10 years
- H1: 3 years
- M15: 2 years

## On-disk (immutable, do not rewrite)

- EURUSD D1 tm-market-EURUSD-D1-20260825-000001 years=6.39 n=2000 target=10.0 **SHORTFALL**
- EURUSD H1 tm-market-EURUSD-H1-20260825-000001 years=0.32 n=2000 target=3.0 **SHORTFALL**
- EURUSD H4 tm-market-EURUSD-H4-20260825-000001 years=1.24 n=2000 target=None **UNKNOWN**
- EURUSD M15 tm-market-EURUSD-M15-20260825-000001 years=0.08 n=2000 target=2.0 **SHORTFALL**
- GOLD D1 tm-market-GOLD-D1-20260825-000001 years=6.41 n=2000 target=10.0 **SHORTFALL**
- GOLD H1 tm-market-GOLD-H1-20260825-000001 years=0.33 n=2000 target=3.0 **SHORTFALL**
- GOLD H4 tm-market-GOLD-H4-20260825-000001 years=1.24 n=2000 target=None **UNKNOWN**
- GOLD M15 tm-market-GOLD-M15-20260825-000001 years=0.08 n=2000 target=2.0 **SHORTFALL**
- GOLD M15 tm-market-GOLD-M15-20260825-000002 years=0.08 n=2000 target=2.0 **SHORTFALL**
- OIL D1 tm-market-OIL-D1-20260825-000001 years=6.41 n=2000 target=10.0 **SHORTFALL**
- OIL H1 tm-market-OIL-H1-20260825-000001 years=0.33 n=2000 target=3.0 **SHORTFALL**
- OIL H4 tm-market-OIL-H4-20260825-000001 years=1.24 n=2000 target=None **UNKNOWN**
- OIL M15 tm-market-OIL-M15-20260825-000001 years=0.08 n=2000 target=2.0 **SHORTFALL**
- USDJPY D1 tm-market-USDJPY-D1-20260825-000001 years=6.39 n=2000 target=10.0 **SHORTFALL**
- USDJPY H1 tm-market-USDJPY-H1-20260825-000001 years=0.32 n=2000 target=3.0 **SHORTFALL**
- USDJPY H4 tm-market-USDJPY-H4-20260825-000001 years=1.24 n=2000 target=None **UNKNOWN**
- USDJPY M15 tm-market-USDJPY-M15-20260825-000001 years=0.08 n=2000 target=2.0 **SHORTFALL**

## Rules if a later fetch is allowed

1. New `dataset_id` only. Never overwrite `20260825-000001`.
2. Read-only MT5 facade. `order_send` remains forbidden.
3. Do not touch Final OOS.
4. V0.9 / V0.8 / V0.6 hashes stay frozen on the old parents.

## Read-only MT5 probe (not frozen)

- GOLD D1 n=2398 first_unix=1544572800 last_unix=1787788800 **PROBE_OK**
- GOLD H1 n=17989 first_unix=1692028800 last_unix=1787842800 **PROBE_OK**
- GOLD M15 n=48192 first_unix=1723562100 last_unix=1787842800 **PROBE_OK**
- EURUSD D1 n=3134 first_unix=1471305600 last_unix=1787788800 **PROBE_OK**
- EURUSD H1 n=18876 first_unix=1692028800 last_unix=1787842800 **PROBE_OK**
- EURUSD M15 n=50606 first_unix=1723562100 last_unix=1787842800 **PROBE_OK**
- USDJPY D1 n=3134 first_unix=1471305600 last_unix=1787788800 **PROBE_OK**
- USDJPY H1 n=18910 first_unix=1692028800 last_unix=1787842800 **PROBE_OK**
- USDJPY M15 n=50741 first_unix=1723562100 last_unix=1787842800 **PROBE_OK**
- OIL D1 n=2395 first_unix=1544572800 last_unix=1787788800 **PROBE_OK**
- OIL H1 n=18021 first_unix=1692028800 last_unix=1787842800 **PROBE_OK**
- OIL M15 n=48266 first_unix=1723562100 last_unix=1787842800 **PROBE_OK**

On-disk files are still 2000-bar shortfalls. Extra bars require **new** dataset IDs.
GOLD/OIL D1 probe starts ~2018 (unix 1544572800): still short of a true 10-year D1. FX D1 is closer.
H1/M15 probe counts exceed the frozen 2000-bar packs. Do not overwrite `20260825-000001`.
V0.9 does not wait on this fetch.
