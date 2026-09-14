# MT5 PIT Data Acceptance Tests

**Date:** 2026-09-14  
**Use:** After the owner drops a candidate file for EXP-008 and/or EXP-009. Cursor runs these tests **before** any contract freeze or book.

Any **critical** fail ⇒ `DATA = BLOCKED`. Do not preregister-freeze. Do not run EXP-008 / EXP-009.

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
```

Critical tests: **1, 2 (008 only), 3, 4, 5, 10**.  
Important: **6, 7, 8, 9**.

---

## How to hand files to Cursor

1. Put the dump under  
   `data/market/research_engine/phase3/exp008/` or `.../exp009/`  
   (gitignored live bars stay ignored; a small frozen pack **may** be committed **without** keys).
2. Tell Cursor: “run `AUDIT/MT5_PIT_DATA_ACCEPTANCE_TEST.md` on `<path>`.”
3. Do **not** put API keys in chat. `.env` only.

---

## Test 1 — Historical release timestamp exists

**Critical.**

- Every in-scope row has `release_utc` parseable to seconds (or minute) in UTC.
- Not date-only. Not empty. Not `00:00:00` unless the vendor proves that was the clock (it is not 08:30 ET).
- Sample: CPI/NFP should cluster near **12:30Z or 13:30Z** (08:30 ET). FOMC should match **that meeting’s** statement clock, not a dummy noon.

**Fail:** `event_date` only; all timestamps midnight; clocks contradict BLS 08:30.

---

## Test 2 — Consensus is historical consensus (EXP-008 only)

**Critical for EXP-008. N/A for EXP-009.**

- `consensus` is non-null for CPI and NFP (FOMC: documented survey or **explicit** “no consensus, exclude FOMC from surprise rule”).
- `consensus_timestamp` or vendor PIT as-of **< `release_utc`**.
- Consensus does not equal today’s survey for that old month (spot-check vs a BLS archive month where street numbers are known from a second source if available; if no second source, at least: consensus ≠ revised actual, and consensus is frozen across two pulls on different days).

**Fail:** missing consensus; consensus dated after release; only `TEForecast` model (proprietary nowcast) passed off as street consensus without disclosure; current webpage scrape.

---

## Test 3 — First print ≠ revised print

**Critical.**

- First print stored separately from later vintage.
- For NFP, at least 3 of 10 sampled months show **CES first preliminary ≠ current FRED `PAYEMS`** (payrolls revise). If the vendor’s “Actual” **equals** today’s FRED for those months, it is **revised contamination**.
- CPI revisions are smaller; still require a vintage field.

**Fail:** single `actual` column that matches today’s FRED for heavily revised NFP months.

---

## Test 4 — `knowledge_time_utc` reconstructible

**Critical.**

- Field present; `knowledge_time_utc >= release_utc` (and >= consensus time).
- Join to GOLD: `knowledge_time_utc <= timestamp_utc(t+1)` for the intended bar; **zero** rows where knowledge is after fill.
- Manual: one CPI 08:30 ET is **not** joined to the GOLD bar **open** the same `00:00Z` date as if it were known at open.

**Fail:** `knowledge_time = observation_date`; `event_date = signal_date`.

---

## Test 5 — Historical vintage immutable

**Critical.**

- Re-pull (or vendor PIT as-of) of the **same** `asof` date returns the **same** first_print/consensus (hash of the as-of slice).
- Vendor documents that later revisions do not mutate that as-of.

**Fail:** second download of “2019-03 CPI asof 2019-03-13” changed; vendor says “we only keep current.”

---

## Test 6 — Random 10-event forensic (manual)

**Important.**

Pick 10 events (mix FOMC/CPI/NFP across 2019–2024, not all bull-gold years):

| Check | Source of truth |
|-------|-----------------|
| Release clock | BLS archive header / Fed statement page |
| First print | Archive PDF/TXT or ALFRED initial |
| Consensus | Only if vendor claims it — compare to a second calendar **if** one exists; else internal consistency |
| GOLD join | Next open after knowledge |

Write a 10-row table in the acquire note. **≥2 clock or first-print mismatches ⇒ BLOCKED.**

---

## Test 7 — Dataset hash

**Important.**

- sha256 of the frozen bytes in `MANIFEST.json`.
- Recompute on disk matches.
- `retrieval_timestamp` present.

**Fail:** no hash; file edited after hash.

---

## Test 8 — Duplicate events

**Important.**

- Unique `(event_type, release_utc, unit)` or vendor `event_id`.
- No double CPI the same month unless one is flagged revision.

**Fail:** silent duplicates that would double-count surprises.

---

## Test 9 — Timezone normalization

**Important.**

- Original TZ stored (`America/New_York`).
- UTC conversion uses the **historical** offset (EDT vs EST), not a fixed −4.
- DST around March/November sampled.

**Fail:** all 08:30 ET stored as 13:30Z in January.

---

## Test 10 — Revision contamination

**Critical.**

- No feature column is “current FRED as of pull day” for past months.
- EXP-009: `realtime_start` present; knowledge uses `max(H.15 16:15 ET, realtime_start)`.
- EXP-008: surprise never uses `revised_print`.

**Fail:** DFII10 downloaded in FRED-today mode without vintages and joined on `date`.

---

## Pass / fail

```text
ALL critical PASS → DATA = ACCEPTED_FOR_FREEZE
ANY critical FAIL → DATA = BLOCKED
```

Accepted means: **then** write the EXP contract hash and increment `MULTIPLE_TESTING.md`. It does **not** mean Candidate, trade, or 20%.
