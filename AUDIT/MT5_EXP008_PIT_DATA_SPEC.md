# EXP-008 PIT Data Specification — GOLD Event Surprise

**Date:** 2026-09-14  
**Experiment:** EXP-008 `GOLD_EVENT_SURPRISE_PIT` (plan only; **DO NOT RUN**)  
**Audience:** owner + later acquire session.

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
PHASE 3: BLOCKED
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
```

This file is a **procurement / knowledge-time contract**. It does not buy data, scrape the web, train, or backtest.

---

## 1. What Point-in-Time means here

At GOLD **decision time** `t`, TradeMind may use a field `X` if and only if a stored `knowledge_time_utc(X) ≤ decision_time_utc(t)`.

For every historical event the pack must answer:

| Question | Fail if unanswered |
|----------|--------------------|
| Which **consensus** was on the tape *before* the print? | Consensus is today’s webpage or a later backfill |
| Which **first print** hit the tape? | Only the current revised actual exists |
| **When** (UTC, clock) was each of those known? | Date-only `event_date` |
| Did a **revision** arrive later? | Revision overwrote the first print |
| Does today’s vendor query return the **vintage** or the **latest**? | Vendor cannot explain vintage |

**Direct FAIL (do not freeze, do not run EXP-008):**

1. Only the current database “final actual.”
2. No consensus timestamp / no proof consensus was pre-release.
3. Consensus is a post-hoc reconstruction.
4. Revision replaced first release in the same field.
5. Release time not verifiable to clock precision.
6. Vendor cannot document vintage.
7. “Historical” values are today’s HTML for old dates.
8. Grok / LLM / news search as the event store.

Official **first prints** without economist consensus are **not** the registered EXP-008 object. They may become a *different* pre-registered family later. They must not be silently labeled EXP-008.

---

## 2. Official event list (do not expand the run)

**In-scope (frozen list):**

| event_type | Official print | Typical clock (America/New_York) |
|------------|----------------|-----------------------------------|
| `FOMC` | Target range / statement | Statement time on Fed calendar (often 14:00 ET; **use the historical clock, not “2pm always”**) |
| `CPI` | CPI-U all-items SA m/m and/or y/y as stored in the pack | BLS **08:30 ET** |
| `NFP` | CES total nonfarm payroll change (first preliminary) | BLS Employment Situation **08:30 ET** |

**Optional (document only; not in the first EXP-008 freeze):** PCE, Retail Sales, ISM, GDP, OPEC, other G10 CB. Adding any of these is a **new experiment id**.

Research window to cover: **2018-12-12 → 2025-09-11** (Phase 2 RESEARCH lock). FINAL OOS dates may be stored but **must not be scored**.

---

## 3. Minimum schema

Every row:

| Field | Required | Meaning |
|-------|----------|---------|
| `event_id` | yes | Stable unique id (vendor id or `TYPE-YYYYMMDD`) |
| `event_type` | yes | `FOMC` / `CPI` / `NFP` only in v1 |
| `release_utc` | yes | Clock time the official print was scheduled/released |
| `knowledge_time_utc` | yes | Time TradeMind treats the **usable surprise inputs** as known (see §4) |
| `first_print` | yes | Number on the **first** release, not today’s revised series |
| `consensus` | yes for EXP-008 | Pre-release economist survey / vendor “Forecast” **as of before** `release_utc` |
| `revision_flag` | yes | `0` first vintage; `1` later revision row (separate row or separate columns) |
| `source` | yes | e.g. `BLS`, `FRB`, `TE` |
| `source_vintage` | yes | Vendor vintage date or `asof=` |
| `unit` | yes | `%`, `k_jobs`, `bp`, … |
| `frequency` | yes | `meeting` / `monthly` |
| `country` | yes | `US` |
| `timezone_original` | yes | Usually `America/New_York` |
| `retrieval_timestamp` | yes | When *we* pulled the file |
| `dataset_hash` | yes | sha256 of the frozen file |

If the vendor provides, also store: `previous_print`, `revised_print`, `surprise`, `consensus_range`, `consensus_timestamp`, `first_available_timestamp`.

`surprise` used by the (future) contract must be computed as:

```text
surprise = first_print - consensus
```

using the **same unit**. Do not use `revised_print - consensus`. Do not use `first_print - previous_print` under this experiment id.

---

## 4. Knowledge-time contract (GOLD)

Ava official GOLD D1 (`GOLD_D1.csv`) labels bars at **`timestamp_utc` = bar OPEN**, always `T00:00:00Z` in the live file. That column is **not** the decision clock.

Phase 2 book: signal at **close of bar t**, fill **open of bar t+1**.

**Conservative decision time for bar t:**

```text
decision_time_utc(t) = timestamp_utc(t+1)   # next bar open; known once bar t has closed
```

An event is usable for the signal that fills at `open(t+1)` iff:

```text
knowledge_time_utc <= decision_time_utc(t)
```

**Forbidden:** `event_date == signal_date` (calendar-day join).

### Worked clocks

| Event | Clock | UTC (EDT, UTC−4) | UTC (EST, UTC−5) | Same GOLD D1 bar? |
|-------|-------|------------------|------------------|-------------------|
| CPI / NFP | 08:30 ET | 12:30Z | 13:30Z | Yes: known long before `open(t+1)` of the *next* UTC day |
| FOMC 14:00 ET | 14:00 ET | 18:00Z | 19:00Z | Yes vs next 00:00Z open |
| H.15 (EXP-009, not this file) | 16:15 ET | 20:15Z | 21:15Z | See EXP-009 spec |

If an event’s `knowledge_time_utc` is **after** `decision_time_utc(t)`, it goes to the **next** decision bucket. No same-bar sneak.

`knowledge_time_utc` for EXP-008 =

```text
max(release_utc, consensus_timestamp_utc, first_available_timestamp_utc)
```

If consensus timestamp is missing → **FAIL** (event unused; if too many unused → pack FAIL).

---

## 5. Official sources vs consensus

| Object | Official free source | Enough for EXP-008? |
|--------|----------------------|---------------------|
| CPI first print + archive PDF/TXT | BLS CPI news-release archive + ALFRED `CPIAUCSL` / related first vintage (`output_type=4`) | First print **yes**. Consensus **no**. |
| NFP first print | BLS Employment Situation archive + CES vintage tables + ALFRED `PAYEMS` first vintage | First print **yes**. Consensus **no**. |
| Release **dates** | BLS schedules; ALFRED `fred/release/dates` | Date **yes**. Confirm clock was 08:30 ET from the archived release header. |
| FOMC statement time + rate | Federal Reserve historical calendar / statements | Print **yes**. Economist consensus **no**. Fed funds futures “implied” pulled today is **FAIL**. |
| Economist consensus | **Not published** by BLS / Fed / Treasury | **UNAVAILABLE** on official sources |

**Conclusion:** Official sources **cannot** close EXP-008 as registered (surprise vs consensus). They **must** still be used as the **acceptance oracle** for first prints and clocks if a paid calendar is bought.

---

## 6. Vendor classes (detail in the matrix)

| Class | Who | Personal buy? | PIT claim | Verdict for EXP-008 |
|-------|-----|---------------|-----------|---------------------|
| A claimed PIT calendar | Trading Economics Calendar API | Yes (card). Official $ often quote / third-party ~$149–$299/mo **unverified** | Docs show `Forecast`, `Actual`, `Revised`, `LastUpdate`, date-range “as appeared” | **CONDITIONAL** — trial + acceptance tests |
| B revised current DB | Investing.com / FXStreet / generic scrapes | Free web | No vintage contract | **FAIL** |
| C knowledge time unprovable | LLM news, today’s “what happened in 2019” pages | Free | No | **FAIL** |
| Enterprise ECO | Bloomberg `ECO`, LSEG, FactSet, Macrobond | **ENTERPRISE_ONLY** | Usually yes | **CONDITIONAL** economically; **do not buy** at this lab’s scale |

Do not buy news farms, ticks, DOM, or option surfaces for EXP-008.

---

## 7. What the owner should hand Cursor

One frozen file, e.g.:

```text
data/market/research_engine/phase3/exp008/tm-us-EVENT-SURPRISE-PIT-<date>-000001.csv
```

plus `MANIFEST.json` (`dataset_hash`, vendor, retrieval_timestamp, license note).

No `.env` in git. API keys stay in `.env` as `TRADEMIND_TE_API_KEY` (if TE) and are **never** committed.

---

## 8. Status

**EXP-008 = BLOCKED** until a pack passes `AUDIT/MT5_PIT_DATA_ACCEPTANCE_TEST.md` Tests 1–4 and 10.

A TE **trial** is the only low-cost path that might produce that pack. Official-only first prints ≠ EXP-008.
