# OVERLAPPING_LABEL_AUDIT

> 2026-09-13. H1 hold=24 design. Computed, not guessed.

## Design

Phase 1 H1 V1 and EXP-002 baselines use:

```text
y[t] = open[t+1+24] / open[t+1] − 1
```

Every bar `t` can have a label. Adjacent labels share **23** of 24 return hours.

## Numbers (GOLD H1, 45,818 bars)

From `research_engine.phase2_mt5.overlap.audit_hold(45818, 24)`:

| Item | Value |
|------|-------|
| hold | 24 |
| overlapping labels (if every t) | ≈ 45,793 |
| shared bars (adjacent) | **23** |
| overlap fraction | **23/24 = 95.8%** |
| approx independent labels | floor(n / 24) ≈ **1,908** |
| purge gap | 24 |
| embargo | 25 |
| official Phase 2 book | **non-overlapping** |

EXP-002 RESEARCH window (to 2025-09-11) booked **1,591** non-overlap Always-Long trades. That is the honest sample size, not 39k overlapping rows.

## Why Phase 1 H1 trees looked smart

Train IC **0.52** vs 44-fold OOS IC **0.038** is the overlap + tree memory of shared hours. Ridge (V6) train IC 0.055 already showed the linear signal was tiny. Sparse V9 did not save fold-OOS IC.

## Rule for Phase 2

- Report and gate on the **non-overlap** book.
- If a model is fit on every `t`, it **must** purge `hold` bars and embargo `hold+1`.
- Do not quote overlapping IC as evidence of an hourly edge.
- FINAL OOS remains locked; this audit is not a new train.
