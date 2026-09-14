# EXP-009 Data Acquisition Report

**Date:** 2026-09-14  
**Retrieval:** `2026-09-14T05:04:23Z`  
**Session:** acquire + PIT acceptance only. No train, no book, no EXP-007/008, no `order_send`.

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
EXP-008: BLOCKED
EXP-009: READY_FOR_PREREGISTRATION
```

This is **not** a tradable strategy. PASS here means the **data pack** may be hashed into a later pre-registration contract. It does **not** mean incremental alpha vs GOLD BUY-HOLD.

---

## 1. Where did the data come from?

| Source | Role | Used |
|--------|------|------|
| FRED / ALFRED API `series_id=DFII10` | Values + `realtime_start` / `realtime_end` | **Yes** (key in local `.env` only) |
| FRED current view | Frozen **value** (latest) | Yes, 6181 API rows; 5927 numeric |
| ALFRED vintage windows | First-available timing | Yes, 11 chunks from **2005-10-12** (5089 vintage dates). Full-history one-shot rejected: FRED max **2000** vintages/request |
| U.S. Treasury XML `daily_treasury_real_yield_curve` / `TC_10YEAR` | Cross-check, not a substitute | Yes |
| DGS10 / DXY / Bund / CPI | Forbidden substitutes | **Not used** |

Pack: `data/market/research_engine/phase3/exp009/`

---

## 2. Free?

**Yes.** FRED API key is free. No Bloomberg. Key was **not** written into any pack file or git.

---

## 3. Coverage

| | |
|--|--|
| Observation start | **2003-01-02** |
| Observation end | **2026-09-10** |
| Frozen numeric rows | **5927** |
| FRED `.` / empty (holidays etc.) | **254** (excluded from freeze) |
| Duplicates | **0** |
| ALFRED archive start | **2005-10-12** (694 pre-history rows flagged `alfred_pre_history=1`) |

RESEARCH lock (2018-12 → 2025-09-11) is inside this span.

---

## 4. What DFII10 actually is

FRED title:

> Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis, Inflation-Indexed

Units: **percent**, daily, not seasonally adjusted.  
Source notes: H.15 + Treasury yield-curve methodology.  
This is **10-year TIPS / inflation-indexed constant maturity (R-CMT)**, not nominal DGS10.

---

## 5. Knowledge time

**Not** `observation_date`.

Rule applied:

```text
h15 = 16:15 America/New_York on observation_date  (DST-correct UTC)
if ALFRED first realtime_start is the 2005-10-12 archive backfill
    and observation_date < 2005-10-12:
        knowledge_time = h15          # flag alfred_pre_history=1
else:
        knowledge_time = max(h15, realtime_start 23:59:59Z)
```

Examples in the frozen CSV:

| observation_date | value | knowledge_time_utc | meaning |
|------------------|-------|--------------------|---------|
| 2003-01-02 | 2.43 | `2003-01-02T21:15:00Z` | January EST; ALFRED did not exist yet |
| 2018-12-12 | 1.08 | `2018-12-13T23:59:59Z` | FRED ingest **T+1** |
| 2026-09-10 | 2.55 | `2026-09-11T23:59:59Z` | FRED `last_updated` 2026-09-11 15:16 CDT |

**5231 / 5233** post-archive rows have `realtime_start` **after** `observation_date`. Conservative knowledge is usually **next UTC day 23:59:59Z**, not the H.15 print clock alone.

GOLD D1 `timestamp_utc` is bar **OPEN** `T00:00:00Z`.  
`decision_time = next bar open`.  
**date == date at the OPEN is lookahead** (1937/1937 overlapping bars). The frozen file does **not** encode that join.

---

## 6. H.15 clock

**VERIFIED** on live `https://www.federalreserve.gov/RELEASES/h15/` (this lab, 2026-09-14):

> The release is posted daily Monday through Friday at 4:15pm.

Timezone letters `ET` are **not** on that sentence. Treated as **America/New_York** (Board in Washington).  
DST check: 2003-01-02 H.15 → **21:15Z**; 2003-07-01 → **20:15Z**.

FRED `last_updated` for this pull: **2026-09-11 15:16:26-05** (ingest, not the official clock).

---

## 7. Is ALFRED vintage meaningful?

**LIMITED — not INVALID, not CPI-like.**

| Fact | Number |
|------|--------|
| Vintage dates | 5089 (2005-10-12 → 2026-09-11) |
| ALFRED rows across windows | 40078 |
| Observation dates with multiple realtime windows | 5738 |
| Observation dates whose **value** changed across vintages | **0** |
| As-of 2015-12-31 / 2018-12-31 / 2020-12-31 / 2022-12-30 vs current | **0** value diffs |

So vintage is **availability / ingest timing**, not a restatement history like PAYEMS.  
It is still required: `realtime_start` is usually **T+1**, and that delays `knowledge_time_utc`.  
Do **not** write “DFII10 has no revisions so observation_date = knowledge_time.”

Pre-2005-10-12: ALFRED backfilled the whole history on archive start. Those 694 rows use H.15-only knowledge and are flagged.

---

## 8. Treasury cross-check

**PASS** as a value check. Not a second series.

| | |
|--|--|
| Treasury rows parsed | 5678 (`TC_10YEAR`) |
| Overlap | **5677** |
| \|DFII10 − Treasury\| > 0.5 bp | **0** |
| Only FRED | 250 (mostly **2017** — Treasury XML year fetch `URLError`; DATA_GAP, not a rewrite) |
| Only Treasury | 1 (`2026-09-11`, after FRED observation_end 2026-09-10) |

Values were **not** edited to force a match.

---

## 9. Future leak

**NOT FOUND in the frozen feature columns.**  
`knowledge_time_utc` is never midnight of `observation_date`.  
**FOUND if a later book joins on calendar date to GOLD open** — 1937/1937 overlap bars would leak. Any EXP-009 contract must use `knowledge_time_utc <= decision_time`.

---

## 10. Acceptance tests

| ID | Topic | Result |
|----|--------|--------|
| TEST-01 | fields complete | **PASS** |
| TEST-02 | continuity (no gap > 5d) | **PASS** |
| TEST-03 | duplicates | **PASS** (0) |
| TEST-04 | missing | **PASS** (254 FRED `.` dropped) |
| TEST-05 | timezone DST | **PASS** |
| TEST-06 | knowledge ≠ observation midnight | **PASS** |
| TEST-07 | vintage semantics | **PASS** (label LIMITED) |
| TEST-08 | Treasury | **PASS** (0 mismatches; 2017 XML gap noted) |
| TEST-09 | hash repeat | **PASS** |
| TEST-10 | future-info rule | **PASS** (same-date OPEN join documented as leak; file does not use it) |

No critical fail. Data were not edited to pass.

---

## 11. Dataset SHA256

**`790b6d725a0d170b7e701f85880bbb57515a9033634ec02d0d9633fcf7fe7b1f`**  
File: `DFII10_raw.csv`

---

## 12. Current status

**READY_FOR_PREREGISTRATION**

Not Candidate. Not authorized to trade. Do **not** train, search lookbacks, or run EXP-009 books in this session.

Next allowed step (later): write `docs/research_engine/EXP009_*` contract with this `hash_sha256`, increment `AUDIT/MULTIPLE_TESTING.md` **before** any engine, success = incremental net vs GOLD BUY-HOLD.

---

## Files

```
data/market/research_engine/phase3/exp009/DFII10_raw.csv
data/market/research_engine/phase3/exp009/DFII10_metadata.json
data/market/research_engine/phase3/exp009/DFII10_vintage_audit.json
data/market/research_engine/phase3/exp009/DFII10_treasury_crosscheck.csv
data/market/research_engine/phase3/exp009/DFII10_treasury_crosscheck.json
data/market/research_engine/phase3/exp009/EXP009_DATA_MANIFEST.json
data/market/research_engine/phase3/exp009/EXP009_ACQUIRE_STATUS.json
data/market/research_engine/phase3/exp009/acquire_dfii10.py
```

`git check-ignore .env` remains ignored. No key in the pack.
