# V9 START — Existing Data Master Backtest

**Date:** 2026-08-30  
**Purchase:** NO  
**New hypotheses:** NO  
**Final OOS:** DENIED  

## Mission

Convert already-owned data and already-defined mechanisms into one costed MT5 trade ledger.

```
LEVEL = 0
LEVEL_1_CANDIDATE = 0
NEW_DATA_PURCHASE = FALSE
DATACOST = $0
UNUSED_RESEARCH_RESERVE ≈ $93
```

10% CAGR is a capital target, not this mission's discovery gate.

## Phases

1. V9_START
2. DATA_CENSUS
3. BACKTEST_ENGINE
4. REPLAY
5. ATTRIBUTION
6. MASTER_EQUITY
7. AUDIT
8. DECISION

## Hard rules

- Do not buy Databento / options / any paid series
- Do not modify HYP-0001 / FD / V0.5 / V0.6 / V0.8 / V0.9 / V0.91 / V6 / V7 / V8 originals
- NEXT_BAR_OPEN only. No CLOSE[t] → OPEN[t]
- OHLC + spread = EXECUTION_APPROXIMATION
- Replay only. No combinatorial search
- Xavier only if volume requires it; local must reproduce

## Stop

- STOP A: formal Level 1 Candidate
- STOP B: all legal strategy mechanisms replayed and no Positive Reproducible Strategy
- STOP C: technical blocker
