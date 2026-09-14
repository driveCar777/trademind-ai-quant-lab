# EXP-009 TIPS / Real-Yield Data Specification

**Date:** 2026-09-14  
**Experiment:** EXP-009 `GOLD_TIPS_REAL_YIELD_PIT` (plan only; **DO NOT RUN**)

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
PHASE 3: BLOCKED
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
```

Procurement / knowledge-time only. No train, no book, no `order_send`.

---

## 1. Object (do not substitute)

**Wanted:** US **10-year constant-maturity TIPS real yield** (inflation-indexed).

**Canonical series:** FRED / ALFRED **`DFII10`**  
Title: *Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis, Inflation-Indexed.*  
Source: Board of Governors H.15; underlying construction: **U.S. Treasury** Daily Treasury **Par Real Yield Curve**, 10-year point.

**Same economic object (cross-check, not a second experiment):**

- Treasury XML `data=daily_treasury_real_yield_curve` → field **10 YR**
- Fed H.15 “Inflation indexed / 10-year”

**Forbidden substitutes (already killed or wrong object):**

| File / idea | Why FAIL |
|-------------|----------|
| `tm-alt-UST-DGS10-*` | **Nominal** 10y. RATES_V1 **NO_CANDIDATE** |
| NY Fed EFFR / €STR / BOJ call | Carry family **NO_CANDIDATE** |
| Ava `EURO-BUND` / `JAPAN_BOND` CFDs | Not TIPS real yield |
| DXY / dollar z | USD_METAL **KILLED** |
| `nominal_10y − trailing CPI` | Not a real-time TIPS yield unless a **new** id is pre-registered with a full knowledge-time proof. **Not EXP-009.** |

---

## 2. Semantics checklist

| Question | Answer for DFII10 / Treasury 10y real par |
|----------|-------------------------------------------|
| Real or nominal? | **Real** (inflation-indexed / TIPS par) |
| Constant maturity or a CUSIP? | **Constant maturity** interpolated from the TIPS curve (R-CMT). Not a single bond. |
| Revisions? | Market yields are **rarely revised** for economics. ALFRED still stores vintages (ingest lag, corrections, methodology notes). Use vintages; do not assume “never revised ⇒ observation_date = knowledge_time.” |
| Methodology changes? | FRED notes title/source-note changes (e.g. 2019-07-01, 2025-01-06). Freeze the series id; do not splice a homemade curve. |
| Backfill? | Treasury published the real par curve from **2003**; H.15 added TIPS yields **2004-01-05** with history from 2003-01-02. RESEARCH starts 2018-12 — coverage is enough. |
| Rewritten history? | Current FRED without `realtime_*` = **today’s** view. **Must** pull ALFRED vintages or store `realtime_start` per observation. |
| Fit as GOLD feature? | **Yes as opportunity-cost Z**, if knowledge time is **H.15 / Treasury publication**, not the Treasury *session* date at 00:00Z. |

---

## 3. Observation vs publication vs knowledge

Treasury (official):

- Inputs: NY Fed **indicative bids ~15:30 ET** on the session date.
- H.15 **posted 16:15 ET** business days (Fed: “The release is posted daily Monday through Friday at 4:15pm”).
- FRED `DFII10` “Updated” often ~15:16 **CDT** (= 16:16 ET) — ingest, not a second official clock.

**Do not set** `knowledge_time_utc = observation_dateT00:00:00Z`.

| Date | Meaning |
|------|---------|
| `observation_date` | Treasury **session** the quotes refer to (the “as of” yield day) |
| `publication_date` | Calendar day H.15 / Treasury posts that session’s 10y real yield |
| `knowledge_time_utc` | **Conservative:** `publication_date` at **16:15 America/New_York**, converted to UTC. If ALFRED `realtime_start` is **later**, use `max(16:15 ET that day, realtime_start 23:59:59Z)` |

ALFRED help: new points are added **typically within one business day** of source release. If `realtime_start` is T+1, **do not** use the yield on GOLD decision T. That is the whole point of vintage.

---

## 4. Minimum schema

| Field | Required | Example |
|-------|----------|---------|
| `date` | yes | observation_date `2019-03-20` |
| `timestamp_utc` | yes | Same as `knowledge_time_utc` or observation noon **labeled as not knowledge** — prefer knowledge |
| `series_id` | yes | `DFII10` |
| `value` | yes | percent, e.g. `2.32` |
| `unit` | yes | `percent_per_annum` |
| `source` | yes | `FRED/ALFRED` or `US_TREASURY` |
| `knowledge_time_utc` | yes | §3 |
| `vintage` | yes | ALFRED `realtime_start` or `vintage_date` |
| `retrieval_timestamp` | yes | pull time |
| `dataset_hash` | yes | sha256 |

Optional: `realtime_end`, `observation_date`, `publication_clock_et=16:15`.

---

## 5. GOLD join (same bar rule as EXP-008)

`GOLD_D1.csv` `timestamp_utc` = **bar OPEN** `T00:00:00Z`.

```text
decision_time_utc(t) = timestamp_utc(t+1)
usable iff knowledge_time_utc <= decision_time_utc(t)
```

H.15 16:15 ET = **20:15Z** (EDT) or **21:15Z** (EST).  
Next GOLD open at `t+1` 00:00Z is **after** that same calendar day’s 16:15 ET **if** we compare to the *next* UTC midnight. Example:

- Session Wednesday observation. H.15 Wednesday 16:15 ET → 20:15Z Wednesday.
- GOLD bar labeled Wednesday `00:00Z` closes before Thursday `00:00Z`.
- 20:15Z Wednesday **<** Thursday 00:00Z → yield is usable for the signal that fills **Thursday** open.

If someone joins `observation_date` to the GOLD bar with the **same date stamp**, they use Wednesday’s yield at Wednesday’s **open** — that is **lookahead / same-bar leak**. **FAIL.**

---

## 6. Official path is enough

| Source | Cost | PIT / vintage | Personal | Verdict |
|--------|------|---------------|----------|---------|
| FRED API + ALFRED `realtime_start` / `output_type=2|4` | **$0** (free API key, [fredaccount](https://fred.stlouisfed.org/docs/api/api_key.html)) | **A** — designed for “what was known when”; ingest lag must be respected | Yes | **PASS** for EXP-009 **if** knowledge_time uses vintage + 16:15 ET rule |
| Treasury XML `daily_treasury_real_yield_curve` | **$0** | **C** as a lone file (no vintage table). Use as **cross-check of values**, not as the only knowledge clock | Yes | **CONDITIONAL** companion |
| Fed H.15 HTML / DDP | **$0** | Official clock 16:15 ET; HTML is current | Yes | Clock oracle |
| Bloomberg TIPS / YCSW | **ENTERPRISE_ONLY** | A | No | Do **not** buy |

**Do not pay** for DFII10. Paying Bloomberg for the same H.15 number is waste.

---

## 7. What to hand Cursor (after a later acquire session)

```text
data/market/research_engine/phase3/exp009/tm-ust-DFII10-PIT-<date>-000001.csv
data/market/research_engine/phase3/exp009/MANIFEST.json
```

Pull recipe (do **not** run in this procurement session):

1. Register free FRED key → `.env` `TRADEMIND_FRED_API_KEY` (never git).
2. `fred/series/observations?series_id=DFII10&realtime_start=1776-07-04&realtime_end=9999-12-31` (or vintage-by-vintage).
3. Keep `realtime_start` / `realtime_end` columns.
4. Hash; run acceptance tests.
5. Cross-check a sample of 10y points vs Treasury XML.

Coverage needed: 2018-12-01 → 2025-09-11 at minimum (warmup before RESEARCH).

---

## 8. Status

**EXP-009 data = READY_FOR_FREE_ACQUIRE** (not a paid purchase).  
**EXP-009 experiment = still not run.** Pulling DFII10 is a later session. This file does not authorize a book.
