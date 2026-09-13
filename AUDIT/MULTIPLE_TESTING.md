# Multiple-testing note (Phase 2)

> 2026-09-13. Count researcher degrees of freedom. Applicability, not a fake SPA p-value.

## Count (GOLD-relevant, already run)

| Family | m (approx) | Status |
|--------|------------|--------|
| D1 V1–V5 × 7 products | 35 | LEGACY_FROZEN, 0 Candidate |
| H1 V1–V9 (GOLD) | 9 | LEGACY_FROZEN, 0 Candidate |
| V30 US CFD / V32 macro pool | 2 | LEGACY_FROZEN |
| Grok hot table / RSI manual / V4 follow | 3 | Not research Candidates |
| V4 path-exit diagnostics (BE/TRAIL/…) | 6 | DIAGNOSTIC_NOT_A_BOOK |
| Phase 2 D1 9 baselines | 9 | pre-registered, RESEARCH only |
| Phase 2 H1 9 baselines | 9 | pre-registered, RESEARCH only |
| EXP-001 Naive + Linear | 2 | Linear increment vs Naive only; lost to BH |
| **Total charged** | **~75** | |

Thresholds, holds, TFs, and “which product to look at” were additional implicit trials in Phase 1. Phase 2 **did not** add a grid.

## Methods — applicability

| Method | Applicable now? | Why |
|--------|-----------------|-----|
| **FDR (BH)** | Yes, as a **count**. Discoveries = 0 among pre-registered Phase 2 families vs buy-hold. | Family-level; we are not calling Linear a discovery. |
| **White Reality Check** | Applicable **in principle** to a Candidate’s equity vs a universe of rules. | **Not run.** No Candidate. Running RC on 75 already-seen graves is theater. |
| **SPA (Hansen)** | Same as RC. | Not run. Needs a pre-registered universe before looking. |
| **Deflated Sharpe (Bailey)** | Useful **judgment**: Linear research Sharpe 0.58 after many prior GOLD trials is not a discovery. Always-Long Sharpe ~1.0 is gold beta, not a selected rule. | Not used to promote. |

## Rule

New work must add to `m` **before** the run (EXP-001/002/003). Do not open FINAL OOS to “find” one survivor among 75.
