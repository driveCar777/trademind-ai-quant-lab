# V10 START — Model Discovery & Information Representation

**Date:** 2026-08-30  
**Purchase:** NO  
**New download:** NO  
**Final OOS:** DENIED  
**A-share:** NOT IN SCOPE  

## Mission

Test whether the already-owned information set contains nonlinear / interaction / conditional structure that simple rules did not capture.

```
LEVEL = 0
LEVEL_1_CANDIDATE = 0
NEW_DATA_PURCHASE = FALSE
NEW_DATA_DOWNLOAD = FALSE
DATACOST = $0
UNUSED_RESEARCH_RESERVE ≈ $93
```

```
HYPOTHESIS:
Existing Information Set may contain
nonlinear / interaction-based predictive structure
not captured by previously tested simple mechanisms.
```

MODEL is not assumed to be alpha. 10% CAGR is the long-run capital target, not this mission's discovery gate.

## Phases

1. V10_START
2. FEATURE_INVENTORY
3. MODEL_CONTRACT
4. BASELINE
5. MODEL_RUN
6. ATTRIBUTION
7. ABLATION
8. TRADING_REPLAY
9. AUDIT
10. DECISION

## Hard rules

- Do not buy Databento / options / ORATS / CME DataMine / Trading Economics / any new source
- Do not reopen killed simple-rule hypotheses (OI, DTE, RSI, MA, COT, EIA, rates, carry, curve, fusion)
- Killed features may appear as model inputs; that is interaction testing, not a reopened rule
- Observed / derived only. No inferred LLM / news / live-internet features
- Time-order split only. Final OOS unused
- At most 4 model families, 6 feature groups, 2 targets, 10 interactions, 5 states, 3 thresholds
- No AutoML, no hyperparameter search, no target farm
- Xavier only if the local runtime is too large; Python 3.6 stdlib only on Xavier
- Intermediate files stay on `D:\AGXXAIVER-4-WINDOWS-1-STOCK\.tmp`

## Stop

- STOP A: formal Level 1 Candidate — freeze search, reproduce, do not retune
- STOP B: all locked model families `NO_CANDIDATE` → `MODEL_REPRESENTATION_EXHAUSTED`
- STOP C: payment / credential / license / destructive / Final OOS / real trading required
