# Engine V1 Requirements

Checked against code on disk. Do not implement the missing book-layer in this pass.

---

## 1. Multi-strategy comparison

**Have:** FD rank, V0.5 evaluate, V0.6 rank, V0.8 rank — each inside one discovery_id.  
**Missing:** a single compare table across families with shared windows and shared cost.  
**Need for Level 1:** no. Intra-family FDR is enough.  
**Need for Level 2+:** yes, later.

## 2. Position sizing

**Have:** `profit/risk/sizing.py` — 0.5% equity / ATR stop, 1× cap.  
**Missing:** portfolio risk budget, vol targeting (RB-0030).  
**Need for V0.9:** copy the existing function. Do not invent a new sizer.

## 3. Portfolio accounting

**Have:** `profit/portfolio/combine.py` — equal-weight three **same-dataset** V0.6 sleeves.  
**Missing:** aligned multi-asset ledger, cash, margin, strategy tags.  
**Need now:** no. Candidate=0.

## 4. Correlation

**Have:** V0.8 contemporaneous corr as a **diagnostic** (explicitly not a gate).  
**Missing:** rolling corr as a feature family; pairwise sleeve corr.  
**Need now:** residual family will need a residual series, not a corr trade.  
**Do not** promote same-bar corr to a signal (V0.8 lesson).

## 5. Walk forward

**Have:** 70/15/15 roles; V11 walk-forward is a **different** stack (`data/mine/longrun/`, closed).  
**Missing:** rolling refit of a locked research family.  
**Need now:** no. RB-0043 is a post-Level-1 diagnostic. Refit ≠ search.

## 6. Regime labeling

**Have:** `regime/state.py` + `adx.py` — V0.5 axes, causal.  
**Missing:** Δstate helper (enter/exit/shock).  
**Need for V0.9:** yes — smallest new code. Must fail if occupancy looks like level.

## 7. Feature lineage

**Have:** `lineage.py` keys (dataset, preregister, code fingerprint, …). FD/V0.6/V0.8 jobs carry lineage.  
**Missing:** a feature-id graph from raw column → state → Δstate → residual.  
**Need for V0.9:** job must name `state_source=MARKET_STATE_V0.5` and freeze VOL percentiles.

## 8. Experiment genealogy

**Have:** `family.py`, parent_hypothesis_id, multiple_testing ledgers, `graph.py` relations.  
**Missing:** one root registry directory (repo has no `/registry`).  
**Need now:** no new registry service. Point genealogy at existing JSON. Do not edit FD DRAFT flags.

---

## V0.9 minimum increment (when execution is approved)

```text
+ delta(state[t], state[t-1])
+ overlap skip
+ path benchmark report
+ worker cannot add HYP-RT-0004
+ OOS still raises
```

Do **not** add portfolio, walk-forward search, or corr trading to get Level 1.

## Decision

Engine is sufficient to *discover* if we add Δstate. It is not sufficient to *run a fund*. That is correct.

## Next automatic task

`FAILED_ALPHA_DATABASE_V1.md`
