# EXP-001 ladder decision (write-once)

> 2026-09-13 after the frozen Naive→Linear run. Does not overwrite `READ.json`.  
> `candidate=false`. **Do not open Logistic / Ridge / LightGBM.**

## Pre-registered stop rule (contract)

Stop if Linear RESEARCH last-30% net TWR ≤ Naive **or** t increment ≤ 0.

## What the run said vs Naive

| | Naive | Linear |
|--|-------|--------|
| research TWR | +17.4% | +64.4% |
| research_70 TWR | −12.8% (t −0.31) | +2.1% (t 0.21) |
| research_30 TWR | +34.7% (t 1.56) | +61.1% (t 2.38) |
| Δ TWR research_30 | — | **+26.4 pp** |

Literal Naive-gate: increment **yes**.

## Why the next layer is still denied

The contract also required incremental value versus the **baseline set**, not a beauty contest against a weak 20-day sign.

On the same RESEARCH window (2019-02-26→2025-09-11):

| book | TWR | CAGR |
|------|-----|------|
| BUY_HOLD (open→open, one cost) | **+171%** | 13.1% |
| ALWAYS_LONG (20-day rolls) | **+161%** | 13.1% |
| Linear | +64% | 7.6% |
| Naive | +17% | 2.4% |
| MOMENTUM | +26% | 3.0% |

Linear lost to buy-hold and to always-long. The research_30 increment sits in the 2023–25 gold bull — the same slice that made V4 look like a Candidate in Phase 1. research_70 t = 0.21.

**Verdict:** `NO_INCREMENTAL_VS_BASELINE`. `next_layer=NONE`. Not a Candidate. FINAL OOS still locked.

## Forbidden

Read FINAL OOS to “check” Linear. Search a new threshold. Jump to Logistic because Δ vs Naive was +26 pp.
