# V11 MT5 Alpha Exhaustion

**Date:** 2026-08-30
**Purchase:** NO
**New experiment:** NO

MT5 alpha search has reached low marginal value. That is a capital fact, not a claim that markets have no alpha.

## What was actually tested

Frozen families on disk: **37**. Killed records: **37**. V9 mechanisms: **36**.

By class:
- Breadth: 1
- Breakout: 1
- COT: 2
- Calendar: 3
- Cross Asset: 6
- Cross Section: 2
- DTE: 1
- Directional: 2
- EIA: 3
- Futures: 4
- ML: 1
- Mean Reversion: 1
- Momentum: 2
- OI: 1
- Rates: 3
- Regime: 3
- Regime Transition: 1

V9: MT5-only / MT5+public / MT5+futures / ALL OWNED = no Positive Reproducible Strategy. Candidate=0.
V10: 62 locked model cells. 21 beat naive M0 on validation metrics. 5 research+validation costed-positive. FDR 0/62. Candidate=0.
Adding futures information did not produce a Candidate (ALL val AUC 0.5167 vs ALL minus futures 0.5221).

Databento ≈ $31.82 bought GC/CL settlement, OI, volume, expiry. Information value: YES. Certified trading value: 0 Candidate.

## What is still missing on MT5

1. Option surface (IV/skew/term) — quoted, bytes=0.
2. Macro *surprise* — owned series are actual-only.
3. Event timestamps + consensus — not owned.

Those holes do not automatically restore a 4-name CFD book. V9/V10 already showed extra structure on the same names failed the program gate.

Do not reopen killed families. Do not retune. Do not spend the $93 reserve on this file.
