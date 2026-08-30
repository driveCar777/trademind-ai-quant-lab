# Options Full-Year Occupancy Census V8.4

**Mode:** METADATA ONLY. Downloaded: **false**. Purchased: **false**. Credits this task: **$0**.

LEVEL=0. CANDIDATE=0. No options family. No IV series. No Xavier.

Window: **2025-08-29 – 2026-08-28**. Observation dates = Pack E GC/CL sessions with a front settlement. **n = 251** (not assumed 252). Same 251 dates for both metals.

ATM rule (unchanged): `min abs(K−F)/F`, F = owned front futures settlement.

`ACTIVE_OPTION_MONTH` (audit definition, not a contract change): among probed month codes

`{futures-front map, futures-second map, next CME month after second}`

take those with ATM call **or** put `ohlcv-1d` `get_record_count` > 0 that session; **front** = earliest `(year, month)`; **second** = next. Reproducible. Not picked from returns.

Exact option expiration timestamps: **UNKNOWN** (no definition download). DTE is not computed.

Parent daily outright C/P universe: **UNKNOWN**. Parent counts mix C/P/spreads/UD. This census prices only the locked ATM/OTM raw symbols.

---

## Phase M — Density (parent `ohlcv-1d` record_count)

Not one fat month and empty others.

| Month | OG | LO |
|-------|----|----|
| 2025-08 (3d) | 1,613 | 740 |
| 2025-09 | 33,073 | 21,111 |
| 2025-10 | 46,405 | 25,206 |
| 2025-11 | 25,114 | 18,644 |
| 2025-12 | 25,851 | 19,931 |
| 2026-01 | 35,855 | 30,882 |
| 2026-02 | 24,947 | 27,266 |
| 2026-03 | 29,109 | 58,636 |
| 2026-04 | 21,289 | 46,197 |
| 2026-05 | 19,024 | 38,012 |
| 2026-06 | 25,485 | 34,564 |
| 2026-07 | 22,522 | 35,027 |
| 2026-08 (to 28) | 29,313 | 26,823 |

339,600 / 383,039 1Y totals are **spread across the year**.

---

## Full-year eligibility (251 days)

| | OG | LO |
|--|----|----|
| ATM | **98.41%** (247/251) | **100%** (251/251) |
| Skew (ATM + OTM put + OTM call, active front) | **80.08%** | **100%** |
| Term (two active months both ATM) | **74.90%** | **98.01%** |
| Futures-front map = active option month | **0.00%** | **85.66%** |
| Days with no active ATM | **4** | **0** |

OTM on the **active** month only:

| Bucket | OG | LO |
|--------|----|----|
| −10% put | 55.4% | 96.4% |
| −5% put | 79.3% | 100% |
| +5% call | 79.7% | 100% |
| +10% call | 49.0% | 99.6% |

OG skew still reaches 80% because ±5% often fills when ±10% is missing.

---

## Consecutive coverage / missingness

| | OG ATM | OG skew | OG term | LO ATM | LO skew | LO term |
|--|--------|---------|---------|--------|---------|---------|
| Longest usable streak | **118** | 28 | 22 | **251** | **251** | 139 |
| Longest gap | **1** | 4 | 4 | **0** | **0** | 2 |
| Gap runs 1–2 / 3–5 / >5 | 4 / 0 / 0 | 36 / 2 / 0 | 41 / 4 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 0 / 0 |

OG ATM is almost continuous (max hole 1 day). OG term is choppy (max streak 22). LO ATM and skew never miss a session.

---

## Front futures vs option front

**Gold:** 0/251. The live option month is **never** the same-month map of the front future. Do not use futures-front expiry as the option front.

**Crude:** 85.7% same-month. Still use `ACTIVE_OPTION_MONTH`, not a blind futures map.

Active gold months rotate: OGV5 → … → OGU6 / OGV6. Four `NONE` days. Crude rotates LOV5 → LOV6 with no holes. Active month is **stable as a calendar**, not a single code all year.

---

## IV (not computed)

If a day has an option bar + owned F + strike + expiry + DGS10, **Black-76 DERIVED IV** is theoretically computable. Not venue IV. Not done this mission.
