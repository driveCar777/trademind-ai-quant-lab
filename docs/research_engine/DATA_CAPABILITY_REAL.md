# DATA_CAPABILITY_REAL V1

Do not assume. On-disk packs and a read-only MT5 probe.

Recovery targets: **D1 > 10 years**, **H1 > 5 years**, **M15 > 2 years**.

Overall: **PROBE_H1_5Y_M15_2Y_OK_GOLD_OIL_D1_SHORT_OF_10Y**

Final OOS: **DENIED**. No `order_send`. No overwrite of `*-20260825-000001`.

## Targets vs probe

- **D1** target=10.0y meet=2 short=2 blocked=0 meet_assets=EURUSD,USDJPY short_assets=GOLD,OIL
- **H1** target=5.0y meet=4 short=0 blocked=0 meet_assets=GOLD,EURUSD,USDJPY,OIL short_assets=-
- **M15** target=2.0y meet=4 short=0 blocked=0 meet_assets=GOLD,EURUSD,USDJPY,OIL short_assets=-

## On-disk immutable (do not rewrite)

- EURUSD D1 years=6.39 n=2000 target=10.0 **SHORTFALL** `tm-market-EURUSD-D1-20260825-000001`
- EURUSD H1 years=0.32 n=2000 target=5.0 **SHORTFALL** `tm-market-EURUSD-H1-20260825-000001`
- EURUSD M15 years=0.08 n=2000 target=2.0 **SHORTFALL** `tm-market-EURUSD-M15-20260825-000001`
- GOLD D1 years=6.41 n=2000 target=10.0 **SHORTFALL** `tm-market-GOLD-D1-20260825-000001`
- GOLD H1 years=0.33 n=2000 target=5.0 **SHORTFALL** `tm-market-GOLD-H1-20260825-000001`
- GOLD M15 years=0.08 n=2000 target=2.0 **SHORTFALL** `tm-market-GOLD-M15-20260825-000001`
- GOLD M15 years=0.08 n=2000 target=2.0 **SHORTFALL** `tm-market-GOLD-M15-20260825-000002`
- OIL D1 years=6.41 n=2000 target=10.0 **SHORTFALL** `tm-market-OIL-D1-20260825-000001`
- OIL H1 years=0.33 n=2000 target=5.0 **SHORTFALL** `tm-market-OIL-H1-20260825-000001`
- OIL M15 years=0.08 n=2000 target=2.0 **SHORTFALL** `tm-market-OIL-M15-20260825-000001`
- USDJPY D1 years=6.39 n=2000 target=10.0 **SHORTFALL** `tm-market-USDJPY-D1-20260825-000001`
- USDJPY H1 years=0.32 n=2000 target=5.0 **SHORTFALL** `tm-market-USDJPY-H1-20260825-000001`
- USDJPY M15 years=0.08 n=2000 target=2.0 **SHORTFALL** `tm-market-USDJPY-M15-20260825-000001`

## Read-only MT5 probe

- GOLD D1 n=2398 span_years=7.707 first_unix=1544572800 **SHORTFALL**
- GOLD H1 n=29854 span_years=5.031 first_unix=1629064800 **MEETS_TARGET**
- GOLD M15 n=48192 span_years=2.037 first_unix=1723564800 **MEETS_TARGET**
- EURUSD D1 n=3134 span_years=10.029 first_unix=1471305600 **MEETS_TARGET**
- EURUSD H1 n=31371 span_years=5.031 first_unix=1629061200 **MEETS_TARGET**
- EURUSD M15 n=50606 span_years=2.037 first_unix=1723564800 **MEETS_TARGET**
- USDJPY D1 n=3134 span_years=10.029 first_unix=1471305600 **MEETS_TARGET**
- USDJPY H1 n=31405 span_years=5.031 first_unix=1629061200 **MEETS_TARGET**
- USDJPY M15 n=50741 span_years=2.037 first_unix=1723564800 **MEETS_TARGET**
- OIL D1 n=2395 span_years=7.707 first_unix=1544572800 **SHORTFALL**
- OIL H1 n=29824 span_years=5.031 first_unix=1629064800 **MEETS_TARGET**
- OIL M15 n=48266 span_years=2.037 first_unix=1723564800 **MEETS_TARGET**

## Phase 7 acquisition (honest)

Selected family INSTITUTIONAL_TIME_V1.0 uses frozen GOLD/OIL D1 dates. It does not wait on this list. The list is for blocked/unknown families.

### ACQ-H1-5Y - priority 1 - ACQUISITION_POSSIBLE

- need: Freeze H1 >= 5 years for GOLD/OIL/FX as new dataset_ids
- why: London/NY institutional open needs a session clock. Frozen H1 is months. Broker probe now spans ~5.03y when 5y is requested.
- cost: Read-only MT5 fetch + large CSV + new dataset_id. No cash cost. Do not overwrite 20260825-000001.
- action: New IDs only. Do not contract London/NY until the new H1 packs are frozen. Do not substitute weekday.

### ACQ-D1-COMMOD-10Y - priority 2 - ACQUISITION_POSSIBLE_BUT_STILL_SHORT_OF_10Y

- need: GOLD and OIL D1 >= 10 years
- why: A decade would raise month-end power and let a later family claim a longer TOM sample. Frozen packs are ~6.4y / 2000 bars.
- cost: Read-only MT5 fetch into a *new* dataset_id. Broker GOLD/OIL D1 currently starts ~2018 (~7.7y): still short of 10y.
- action: New IDs only. Never overwrite 20260825-000001. Do not claim 10y if first unix stays 2018.

### ACQ-D1-FX-10Y - priority 3 - ACQUISITION_POSSIBLE

- need: EURUSD/USDJPY D1 10y freeze as new IDs
- why: Probe already meets 10y. Useful only if a later FX-native family is contracted. Not required for INSTITUTIONAL_TIME_V1.0.
- cost: Read-only fetch + new dataset_id. No cash cost.
- action: Do not overwrite 20260825-000001. Do not reopen V0.8 with longer FX.

### ACQ-M15-2Y - priority 4 - ACQUISITION_POSSIBLE

- need: M15 >= 2 years freeze as new IDs
- why: Probe can meet 2y. Frozen M15 is ~1 month. Not required for the selected D1 calendar family.
- cost: Read-only fetch + new dataset_id. Large CSV.
- action: New IDs only. Do not put M15 into the calendar FDR family.

## Rules

1. New `dataset_id` only.
2. Never overwrite `20260825-000001`.
3. If first unix does not move, history does not exist. Record BLOCKED.
4. Do not invent IV / news / roll tape.
