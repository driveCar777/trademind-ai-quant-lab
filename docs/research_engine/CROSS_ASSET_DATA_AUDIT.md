# Cross Asset Data Audit — V0.8

Inspect only. No new bars. No alignment file written. No experiment.

Purpose: state what the four locked D1 datasets can and cannot support for `FAM-FD-XASSET-0001`.

Parents are read-only:

| logical | dataset_id | sha256 |
| --- | --- | --- |
| GOLD | `tm-market-GOLD-D1-20260825-000001` | `49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899` |
| EURUSD | `tm-market-EURUSD-D1-20260825-000001` | `5c46942d797330185ce919e79cd1b94ac6ca11f25f4442c3a05963c174786ed3` |
| USDJPY | `tm-market-USDJPY-D1-20260825-000001` | `c00389ce1cbeeed3e1ceb9a09e549fa8335556cf2fd8c644db8f8a44f7ce3ad7` |
| OIL | `tm-market-OIL-D1-20260825-000001` | `a22e4213fbbf28e24e892fcce400522885e8208ba9f94bbf41ceed3177808d72` |

`DATA_QUALITY.json` `gap_count=0` means no overlapping / out-of-order bars. It does **not** mean every weekday exists.

---

## 1. Per-dataset facts

Common to all four: timezone **UTC**, every bar `timestamp_utc` ends `T00:00:00Z`, `row_count=2000`, unique dates=2000, duplicate dates=0, `real_volume` all 0, `volume_policy=tick_volume_only`, `validation_status=WARN`, broker Ava Trade, `FINAL_OOS_LOCKED=false`.

Requested range in manifests starts `2010-03-22` with `requested_count=2000`. Actual count is 2000, `history_shortfall=0`. That is “got 2000 bars”, not “got history back to 2010”. Actual starts are 2020.

| field | GOLD | EURUSD | USDJPY | OIL |
| --- | --- | --- | --- | --- |
| mt5_symbol | GOLD | EURUSD | USDJPY | CrudeOIL |
| first bar UTC | 2020-03-26 | 2020-04-01 | 2020-04-01 | 2020-03-24 |
| last bar UTC | 2026-08-25 | 2026-08-25 | 2026-08-25 | 2026-08-25 |
| Saturday bars | 0 | 0 | 0 | 0 |
| Sunday bars | 331 | 332 | 332 | 330 |
| Mon–Thu | 335/335/334/335 | 334×4 | 334×4 | 335/336/335/335 |
| Friday | 330 | 332 | 332 | 329 |
| gaps ≠ 1 calendar day | 335 | 334 | 334 | 335 |
| max calendar gap | 3 days | 3 | 3 | 3 |
| weekday-skipping holidays | 5 | 2 | 2 | 6 |
| spread_zero_count | 2 | 2 | 0 | 0 |

EURUSD and USDJPY have **identical date sets**.

Weekday-skipping holidays (a Friday missing between two present dates):

| symbol | skipped Fridays (examples) |
| --- | --- |
| GOLD | 2020-04-10, 2020-12-25, 2021-01-01, 2021-12-24, 2022-04-15 |
| EURUSD / USDJPY | 2020-12-25, 2021-01-01 |
| OIL | GOLD’s five plus 2023-04-07 |

Sunday bars are normal for this broker’s D1 (weekend session). Saturday never appears. Inner join must use **UTC date of the bar**, not “next weekday”.

---

## 2. Dates present in one file and not another

**GOLD not in EURUSD/USDJPY (5):** 2020-03-26, 2020-03-27, 2020-03-29, 2020-03-30, 2020-03-31  
(before FX series starts)

**EURUSD/USDJPY not in GOLD (5):** 2020-04-10, 2021-12-24, 2022-04-15, 2022-12-25, 2023-01-01

**GOLD not in OIL (2):** 2021-07-11, 2023-04-07

**OIL not in GOLD (2):** 2020-03-24, 2020-03-25

**OIL not in EURUSD (7):** 2020-03-24 … 2020-03-31 (OIL starts earlier; no 2020-03-28 Saturday)

**EURUSD not in OIL (7):** 2020-04-10, 2021-07-11, 2021-12-24, 2022-04-15, 2022-12-25, 2023-01-01, 2023-04-07

Do not impute these days. Do not shift a bar to the next calendar date.

---

## 3. Inner-join rules (locked for V0.8)

### 3.1 Key

```text
align_key = UTC calendar date of timestamp_utc
          = timestamp_utc[0:10]
```

All current D1 bars are midnight UTC, so key == bar timestamp date.

### 3.2 Method

**Official pack:** inner join of **all four** date sets.

```text
aligned = GOLD ∩ EURUSD ∩ USDJPY ∩ OIL
n       = 1993
min     = 2020-04-01
max     = 2026-08-25
Saturday in aligned = 0
Sunday in aligned   = 329
```

Pair-only joins (diagnostic, not official):

| pair | n |
| --- | --- |
| GOLD ∩ USDJPY | 1995 |
| GOLD ∩ EURUSD | 1995 |
| OIL ∩ USDJPY ∩ EURUSD | 1993 |

The two extra GOLD∩USDJPY dates not in the four-way join: **2021-07-11**, **2023-04-07** (OIL missing).  
V0.8 **drops** them so all three hypotheses share one clock. Recovering them after seeing results is forbidden.

### 3.3 Drop, do not fill

| event | action |
| --- | --- |
| date missing on any of the four | drop; increment `dropped_days` |
| fill 0 / ffill / nearest | FORBIDDEN |
| use t on GOLD and t−1 on USDJPY as if same t | FORBIDDEN |
| join on unix time if dates differ | FORBIDDEN (they match today; still join on date) |

Dates dropped from GOLD to reach all4 (7):  
2020-03-26, 2020-03-27, 2020-03-29, 2020-03-30, 2020-03-31, 2021-07-11, 2023-04-07

### 3.4 Next bar ≠ next calendar day

On the 1993 aligned dates there are **1992** successive pairs.  
Only **1658** of those pairs are calendar distance 1. The rest skip a weekend or holiday.

**Horizon lock:** `t+1` = next **row** in the sorted aligned series, not `date + 1 day`.

Example from the official series: `2020-04-03` → `2020-04-05` (Sunday bar exists; Saturday does not).  
`2020-04-09` → `2020-04-12` (Good Friday / weekend).

A signal on Friday may be evaluated on Sunday’s open, if Sunday is the next aligned row.

### 3.5 Shared windows (70 / 15 / 15 on sorted aligned dates)

Computed on the 1993 dates. Frozen here. Last slice is drawn and **denied**.

| role | inclusive UTC dates | n dates |
| --- | --- | --- |
| RESEARCH | 2020-04-01 → 2024-09-26 | 1395 |
| VALIDATION | 2024-09-27 → 2025-09-10 | 299 |
| FINAL_OOS | 2025-09-11 → 2026-08-25 | 299 |

A trade `(t, t+1)` counts only if **both** dates sit in the same role. The last date of each window has no trade.

Approximate pair budgets (before occupancy): RESEARCH 1394, VALIDATION 298.  
FINAL_OOS pairs exist on disk and must not be read by the evaluator.

---

## 4. What this data cannot do

- No DXY. USDJPY / EURUSD are proxies only.  
- No rates, IV, events.  
- No `real_volume`.  
- Cannot claim 10% from M15 (not in this audit’s join).  
- 6.4 years, one 2020 oil regime included. Extreme OIL days stay in the primary test (see contract).  
- Alignment pack is **not** written yet. This audit only specifies how to write it.

---

## 5. Enough to run V0.8?

**Yes**, for three D1 lagged hypotheses on this four-way clock.  
Not yes for session alpha, true VRP, or annualized 10% certification.
