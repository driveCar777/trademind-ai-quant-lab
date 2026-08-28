# Contract Batch — Top 3 (re-evaluated)

Not a V0.9 rubber stamp. Pipeline clusters: Transition 1600 / Residual 576 / Calendar 540.

---

## 1. FAM-RT-DELTA-0001 — KEEP

File: `REGIME_TRANSITION_V0.9_CONTRACT.md`  
hash `3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`  
**Do not change.** Questions RB-0001/0002/0003/0047.

Status: LOCKED_NOT_RUN. Next = execution plan, then (later) jobs.

---

## 2. FAM-XR-RESIDUAL-0001 — NEW, DO NOT RUN YET

Full lock: `CROSS_RESIDUAL_V0.91_CONTRACT.md`  
hash `0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57`

Mechanism ≠ Δstate: a **slow relative price** between GOLD and OIL, faded after extremes.  
Not XA next-day dollar. Not “while in TREND”.

Three ids, m=3, hold=5, V0.6 cost, OOS denied.  
Run only after V0.9 has a freeze.

---

## 3. FAM-CAL-D1-0001 — PAPER ONLY

Not hashed as an executable space this week (would be a third parallel family).

Intended later, max 3:

- HYP-CAL-0001: Sunday/Monday vs other weekdays, GOLD 5D (RB-0005)  
- HYP-CAL-0002: first aligned row after a holiday-skip Friday, OIL (RB-0012)  
- HYP-CAL-0003: forbidden to add month-end unless 0001/0002 die and n is pre-counted  

If calendar is opened, freeze weekday definitions before PnL. No 20 dummies.

---

## Explicitly not contracted

Risk 4A, portfolio, ML, XA-style multi-asset, carry/VRP.

## Decision

V0.9 stays first. Residual is the independent second family (Phase 8). Calendar waits.

## Next automatic task

Engine gap requirements, then failure database, then V0.9 execution plan.
