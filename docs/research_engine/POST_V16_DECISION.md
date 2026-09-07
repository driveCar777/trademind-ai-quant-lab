# Post-V16 Decision

**A_SHARE_INFORMATION_ALPHA_NO_CANDIDATE**

STOP = `STOP_B`  
Reason: every currently legal, free, PIT-able information family has been run or gated. No new independent Candidate.

```
LEVEL = 1
CANDIDATE = 2          # H11_VOL_60 / H12_VOL_120 only
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0
FINAL_OOS = DENIED
NEW_PURCHASE = FALSE
SPEND = $0
XAVIER = not used
```

H11/H12 remain `KEEP_LOW_PRIORITY`. One cluster. No portfolio.

---

## V16 — what it did, result, why it stopped

Financial + industry PIT both READY. 6+3 pre-registered dual-book alpha. Unified BH-FDR 0/9. Validation capital negative 9/9.

`A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE` / `STOP_B`  
Orchestrator exit_code=0 at 2026-09-01 21:29 UTC. Windows local.

Metadata leftover `PROGRESS.stage=COMPILE` was reconciled to `COMPLETE` without touching result JSON.

---

## After V16 — what was attempted

| Mission | Family | n | Family FDR | Val capital | L1 | Status |
|---|---|---|---|---|---|---|
| V17 | A-share × EURUSD/US500/GVZ stock beta | 6 | 0/6 | 6/6 negative | 0 | `EXHAUSTED` |
| Event | PIT announcements | 0 | — | — | 0 | `DATA_BLOCKED` |
| News | text / sentiment | 0 | — | — | 0 | `DATA_BLOCKED` |
| V18 | listing age / ST / resume / calendar | 6 | 2/6 (A1=A2 rank-identical) | 6/6 negative* | 0 | `EXHAUSTED` |
| V19 | industry PIT × same macros | 6 | 1/6 (IM6) | 6/6 negative | 0 | `EXHAUSTED` |
| Options | IV / skew / VRP | 0 | — | — | 0 | `PAYMENT_REQUIRED` |

\* A5 validation MEAN_FORWARD +0.12%; official capital −19.95%. MEAN_FORWARD ≠ CAGR.

Unified BH-FDR on the 18 executed tests: **m=18, discoveries=['IM6_GVZ_IND_DEF_120'], Level-1=0**.

Closest non-candidate remains diagnostic only: IM6 val CAGR −9.44%; V17 best val CAGR −7.75% (M4). Neither is a Candidate.

---

## Exhausted / blocked / payment

**EXHAUSTED (do not reopen / retune / flip sign)**  
Price-only V13–V15. Financial/industry V16. Macro CS V17. Altinfo V18. Industry×macro V19. All MT5 families listed in the search-space audit.

**DATA_BLOCKED**  
Event announcements. News. Full dividend panel. Quarterly / balance-sheet financials (not downloaded). HS300/ZZ500 as-of (not frozen). DXY/UST10/GOLD as primary macros (2018 start would change the locked 2010 research cut).

**PAYMENT_REQUIRED**  
Option surface (quoted: LO 1Y MVD-A $11.99 if a human later spends). Tushare/Wind/Choice/CSMAR. $93 unused.

**FROZEN keep**  
H11/H12 KEEP_LOW_PRIORITY. Final OOS DENIED.

---

## Answers required by the mission

| Question | Answer |
|---|---|
| V16 did what? | Financial+industry PIT + 9 hyps + unified FDR + capital books |
| V16 result? | NEW_CANDIDATE=0, STOP_B |
| Why stop V16? | Both READY layers had no edge after cost |
| After V16 tried what? | Macro CS, Event/News gate, Altinfo, Industry×macro, Options spec |
| Families exhausted? | V13–V19 listed above |
| Data blocked? | Event, news, dividend panel, extra BaoStock statements/index as-of |
| Payment required? | Options surface; vendor terminals |
| New Candidate? | **No** |
| Candidate count? | Still 2 (H11/H12) |
| FDR discoveries (unified 18)? | 1 (IM6), not Level-1 |
| Second independent Alpha? | **No** |
| Next legal stage? | Human gate: (1) stay stopped, (2) authorize a **new** free-data download contract (quarterly/balance/index as-of), or (3) later purchase decision for LO options. Not automatic. Not price reopen. Not Long Validation. |

---

## Versus CAGR ≥ 10%

10% is not a gate and was not used as one. The only published strategy path (H11/H12 official 20-day book) is still full-path negative (V14.1). No new book exists to compare.

---

## Authority

- Audit: `docs/research_engine/POST_V16_SEARCH_SPACE_AUDIT.md`
- V16: `docs/research_engine/V16_DECISION.md`
- V17: `docs/research_engine/V17_MACRO_DECISION.md`
- V18: `docs/research_engine/V18_ALTINFO_DECISION.md`
- V19: `docs/research_engine/V19_INDMACRO_DECISION.md`
- Event/News: `docs/research_engine/POST_V16_EVENT_NEWS_GATE.md`
- Options: `docs/research_engine/OPTIONS_DATA_REQUIREMENT_SPEC.md`
- Unified FDR: `docs/research_engine/POST_V16_UNIFIED_FDR.md`
