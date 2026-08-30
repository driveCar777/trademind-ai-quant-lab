# Options Historical Feasibility V8.3

**Mode:** METADATA ONLY. Downloaded: **false**. Purchased: **false**. Credits this task: **$0**.

LEVEL=0. CANDIDATE=0. No research family. No Xavier. No FINAL OOS.

This document answers: if we paid for OG/LO `definition + ohlcv-1d`, would the **bytes** contain enough option **prices** to study IV / skew / term?

It does **not** answer whether that study would produce Candidate.

---

## Method (no download)

Free endpoints only: `symbology.resolve`, `metadata.get_record_count`, `metadata.get_billable_size`, `metadata.get_dataset_condition`.

`get_record_count` for `ohlcv-1d` on one raw symbol and one UTC day is **0 or ≥1**. Databento emits no daily bar if there was no electronic trade. So `count ≥ 1` means a **traded** price that day, not a definition-only listing.

ATM rule was locked **before** counts:

```
ATM = strike minimizing abs(K - F) / F
F   = owned Pack E front futures settlement (do not rebuy GC/CL)
OG  = $10 (then $25 only if $10 not listed)
LO  = $0.50, encoded as price × 100
OTM = −10%, −5%, +5%, +10% of F, same rounding
```

Eight dates were pre-registered (not chosen after seeing bars):

`2025-08-29`, `2025-10-31`, `2025-12-31`, `2026-02-27`, `2026-04-30`, `2026-06-30`, `2026-08-14`, `2026-08-28`

If a target was not a session, the last curve session `≤` target was used.

Option month mapping (also locked): futures `GCQ6` → `OGQ6`, `CLU6` → `LOU6`. Front = curve front, second = curve second.

Definition availability ≠ price availability. Parent schema availability ≠ that contract has a bar.

Full 1Y daily census: **NOT RUN**. Rates below are **sample rates** on those 8 dates.

---

## Phase A — Universe

| Parent | Class | Phase-1 study? |
|--------|--------|----------------|
| `OG.OPT` | monthly gold outright + UD junk | YES (filter to C/P outright after definition) |
| `LO.OPT` | monthly crude outright + UD junk | YES |
| `OG1–4.OPT`, `G2W.OPT` | gold weeklies | NO |
| `LO1–4.OPT`, `ML2.OPT` | crude weeklies | NO |
| `OG5.OPT`, `LO5.OPT` | week-5 | often absent |
| `MCO.OPT` | micro WTI | NO |
| `UD:1Y:…` | user-defined / custom | NO |

`GC.OPT` / `CL.OPT` still do not exist.

---

## Phase B — Definition coverage

`OPTION_DEFINITION_COVERAGE_V8_3.json` has **186** constructed outrights that **resolved**.

Each row: root, underlying futures code, expiry month code, strike, C/P, `instrument_class`.

`listing` / exact `expiration`: **UNKNOWN** without a paid definition download. Month code is not the timestamp.

Parent `definition` **does** have strike / expiry / C/P / underlying fields (V8.2 `list_fields`).

---

## Phase C — Historical price feasibility (aggregate)

| Query | Record count |
|-------|----------------|
| OG.OPT ohlcv-1d 1Y | **339,600** |
| LO.OPT ohlcv-1d 1Y | **383,039** |
| OG.OPT ohlcv-1d 2026-08-14 | **1,020** |
| LO.OPT ohlcv-1d 2026-08-14 | **1,272** |
| OG.OPT definition 1Y | 14,125,805 |
| LO.OPT definition 1Y | 9,955,288 |

So: historical OHLCV **exists in bulk**. Most definition rows never become a daily bar. That is exactly why occupancy had to be tested per strike.

---

## Phase D–G — Sample occupancy

### Gold (OG), futures-front mapping

| Bucket | ATM_OBSERVATION_RATE (8 dates) |
|--------|--------------------------------|
| ATM | **0.00** |
| ±5 / ±10 | **0.00** |

Those contracts are often **listed** (`resolve` ok, count=0). Definition exists; **price does not**. Gold options die before the same-month future. On 2026-08-14, `OGQ6` ATM was **not even listed** while `GCQ6` was still the front future.

### Gold (OG), futures-second mapping (= live option month in this sample)

| Bucket | Rate |
|--------|------|
| ATM | **1.00** (8/8) |
| −5% put | 0.625 |
| +5% call | 0.75 |
| −10% put | 0.50 |
| +10% call | 0.75 |
| Skew (ATM+OTM put+OTM call) | **0.75** (6/8) |
| Term (front **and** second ATM) | **0.00** |

### Crude (LO)

| | Front | Second |
|--|-------|--------|
| ATM | **1.00** | **1.00** |
| −5% / +5% | 1.00 / 1.00 | 1.00 / 0.875 |
| −10% / +10% | 0.875 / 1.00 | 1.00 / 0.875 |
| Skew | **1.00** | **1.00** |
| Term both ATM | **1.00** (8/8) |

---

## What this proves / does not prove

Proved (sample, metadata):

- Buying parent ohlcv-1d is not buying an empty schema.
- LO ATM / skew / term were jointly present on all 8 pre-registered dates.
- OG ATM prices exist on the **live** option month (here: futures second), not on the futures front.
- `count ≥ 1` ⇒ a trade that day ⇒ not a zero-volume ghost bar.

Not proved:

- 252-session ATM_OBSERVATION_RATE. Mark: **sample only**, not UNKNOWN and not a census.
- OG term structure under the locked front+second futures mapping.
- Bid/ask, official settlement, venue IV.
- Any alpha.

---

## Phase H — IV

IV = **DERIVED**, never exchange IV (GLBX has no `stat_type` 14/15).

Black-76 inputs: option trade price + owned GC/CL settle + strike + expiry + UST DGS10. OG/LO are American. See `OPTIONS_IV_MODEL_LIMITATIONS_V8_3.md`.

---

## Phase I — Dirty observations

Design (cannot execute without bytes):

- Do not invert a bar with `volume = 0` (ohlcv-1d should not emit these).
- Do not invert if OHLC is a one-tick print used as a stale stand-in.
- Do not invert if resolve listed the strike but `get_record_count` is 0.
- Official settlement ≠ ohlcv close. MVD-A has only the latter.

---

## Phase K–L — Reuse

Do not rebuy GC/CL. Realized vol = 20-session stdev of owned front settlement log returns, knowledge T 21:00Z.

---

## Phase M — DESIGN_ONLY (max 3, no family)

1. **IV−RV.** Live-month ATM Black-76 IV minus owned 20-session RV. Above trailing median → next-session front future log return after cost is negative.
2. **Skew.** −10% put IV minus +10% call IV, same live expiry. Above trailing median → next-session return negative.
3. **Term.** Second-expiry ATM IV minus front ATM IV. Below zero → next-session return negative. **OG: not sample-feasible under the locked mapping. LO: sample-feasible.**

Hold and sign locked. Do not retune after a future purchase.
