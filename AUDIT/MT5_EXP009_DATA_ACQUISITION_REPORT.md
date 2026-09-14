# EXP-009 Data Acquisition Report

**Date:** 2026-09-14  
**Session:** acquire + PIT acceptance only. No train, no book, no EXP-007/008, no `order_send`.

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
EXP-008: BLOCKED
EXP-009: BLOCKED
```

---

## Verdict

**EXP-009 = BLOCKED**

Cause: **`TRADEMIND_FRED_API_KEY` is not in the process environment and not in `.env`.**  
No key was created, guessed, or written. No DFII10 observations were stored.  
This is **not** a strategy failure and **not** a reason to substitute DGS10 / DXY / Bund / CPI.

H.15 posting language was checked on the **live official HTML** this session (no FRED key required). That does **not** unlock a frozen DFII10 pack.

---

## 1. Where would the data come from?

| Intended source | Used this session? |
|-----------------|--------------------|
| FRED / ALFRED API `series_id=DFII10` with `realtime_start` / `realtime_end` | **No** — API without a key returned HTTP **400** (`https://api.stlouisfed.org/fred/series?series_id=DFII10`) |
| FRED public CSV (today’s revised view) | **Not used** — would fail vintage / Test 10 |
| Treasury real par XML | **Not pulled** — no DFII10 series to cross-check |
| Substitutes (DGS10, DXY, Bund, CPI) | **Not used** |

On-disk search: **zero** `DFII10` files under `data/`.

---

## 2. Is it free?

Yes. A FRED API key is **free** after registration.  
https://fred.stlouisfed.org/docs/api/api_key.html  

Do not pay Bloomberg for DFII10.

---

## 3. Coverage

**Unknown / not acquired.** Spec target remains 2003 → present (RESEARCH lock uses 2018-12 → 2025-09-11).

---

## 4. What DFII10 is

FRED series page title (HTML retrieved 2026-09-14, HTTP 200):

> Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis, Inflation-Indexed (DFII10)

That is the **10-year TIPS / inflation-indexed constant-maturity** yield (H.15), **not** nominal DGS10.

---

## 5. Knowledge time (contract — not applied to rows)

Until a vintage pack exists, knowledge time is a **rule**, not a computed column.

Per `AUDIT/MT5_EXP009_TIPS_DATA_SPEC.md`:

```text
observation_date  = Treasury session the yield refers to
publication_clock = H.15 post time on the publication calendar day
knowledge_time_utc = max(publication_day 16:15 America/New_York in UTC,
                         ALFRED realtime_start end-of-day UTC)
```

**Never** `observation_date == knowledge_time`.  
GOLD D1 `timestamp_utc` is bar **OPEN** `T00:00:00Z`. Decision clock = `timestamp_utc(t+1)`.  
Same-date join of DFII10 to that open is a **future leak** (spec §5). Not implemented this session because there is no series.

---

## 6. H.15 clock — live check

Retrieved `https://www.federalreserve.gov/RELEASES/h15/` on 2026-09-14 (HTTP 200).

Official note on that page:

> The release is posted daily Monday through Friday at 4:15pm.  
> The release is not posted on holidays or in the event that the Board is closed.  
> Release date: September 11, 2026

The same page lists **Inflation indexed / 10-year** (values visible in the HTML).

**DATA_GAP:** that note says **4:15pm** and does **not** print the letters `ET` / `Eastern` on the clock sentence. The Board is in Washington; this lab treats 16:15 as **America/New_York** unless a later official line says otherwise. Marked **VERIFIED** for “posted 4:15pm business days,” not for a timezone token on that sentence.

---

## 7. ALFRED vintage

**Not tested.** No API key ⇒ no vintage dates, no `realtime_start` table.  
Do **not** write “DFII10 has no revisions.” Vintage meaning is **UNKNOWN** until a keyed pull.

---

## 8. Treasury cross-check

**Not run.** No DFII10 values on disk.

---

## 9. Future leak

**No package ⇒ no join ⇒ no leak found in a feature file.**  
Also **not certified clean**. The leak test only applies after rows exist.

---

## 10. Acceptance tests (this session)

Mapped to the user’s TEST-01…10 and to `AUDIT/MT5_PIT_DATA_ACCEPTANCE_TEST.md`.

| ID | Topic | Result |
|----|--------|--------|
| TEST-01 fields | schema / FRED observations | **FAIL** — no file |
| TEST-02 continuity | business-day gaps | **NOT RUN** |
| TEST-03 duplicates | unique observation dates | **NOT RUN** |
| TEST-04 missing | `.` / null yields | **NOT RUN** |
| TEST-05 timezone | EST/EDT 16:15 → UTC | **NOT RUN** on rows; H.15 clock text checked |
| TEST-06 knowledge time | ≠ observation_date | **NOT RUN** |
| TEST-07 vintage | ALFRED 2015/2018/2020/2022 | **NOT RUN** |
| TEST-08 Treasury | value mismatch table | **NOT RUN** |
| TEST-09 hash | sha256 of frozen bytes | **N/A** — no frozen series |
| TEST-10 future info | date==date join | **NOT RUN** |

Critical failures (no observations) ⇒ **DATA = BLOCKED**. Data were **not** edited to force a pass.

---

## 11. Dataset SHA256

**None.** No `DFII10_raw` file.

Marker only: `data/market/research_engine/phase3/exp009/EXP009_ACQUIRE_STATUS.json`  
(`acceptance_status=BLOCKED`, `block_reason=TRADEMIND_FRED_API_KEY_MISSING`).

---

## 12. Git / secrets

| Check | Result |
|-------|--------|
| `.gitignore` | `.env` and `.env.*` ignored; `!.env.example` kept |
| `git check-ignore .env` | ignored |
| `.env` keys | **no** `TRADEMIND_FRED_API_KEY` |
| `.env.example` | commented `# TRADEMIND_FRED_API_KEY=` added (empty, not a secret) |
| Real key in git | **no** |

---

## 13. Current status

**BLOCKED** — waiting for the owner to set a free FRED key.  
After a keyed pull and tests, the only upgrade allowed is **READY_FOR_PREREGISTRATION**.  
Not Candidate. Not tradable. Do not start EXP-009 research books.

---

## USER ACTION REQUIRED

1. Open https://fred.stlouisfed.org/docs/api/api_key.html and request a **free** FRED API key.  
2. Edit local `D:\AGXXAIVER-4-WINDOWS-1-STOCK\.env` (not git, not chat):

```text
TRADEMIND_FRED_API_KEY=<paste key here>
```

3. Reply in this project: “FRED key is in `.env`, continue EXP-009 acquire.”  
4. Do **not** paste the key into GitHub, Slack, or the chat.
