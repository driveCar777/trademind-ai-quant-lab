# V10 DECISION

**Stop:** STOP_B_MODEL_REPRESENTATION_EXHAUSTED
**Decision:** NO_CANDIDATE
**Purchase:** NO
**Databento remainder:** UNUSED_RESEARCH_RESERVE. Do not spend.
**Options:** do not buy.
**Final OOS:** DENIED

```
LEVEL = 0
CANDIDATE = 0
STRATEGY = 0
PORTFOLIO = 0
PAPER = 0
LIVE = 0
```

## Required answers

1. Existing information usable by nonlinear models: weak single-window advantages exist (21/62 beat M0 on validation logloss+Brier+AUC), but FDR discoveries = 0. Not a usable nonlinear edge.

2. Model vs simple rule: 21 converted cells beat the momentum-rule net on the primary book. That is not FDR-significant and not a Level 1 edge.

3. Most effective family by validation AUC / advantage count: FOREST.

4. Cross-asset stable: NO. Advantages are OIL-heavy (GOLD ALL-space adv=3, OIL ALL-space adv=13). Two keys had both-asset predictive advantage; neither passed FDR plus dual-asset costed-positive.

5. Cross-regime stable: NO candidate, so no regime claim. Yearly slices on converted books are diagnostic only and were not used to select.

6. Cost-adjusted profitable: NO program-level edge. 5 POSITIVE_REPRODUCIBLE cells still failed FDR q=0.05. Stress costx2/slipx2 flipped most weak validation greens.

7. Candidate: 0.

8. If none: locked families failed the joint gate (predictive + costed research/validation + FDR + >=2 assets). Shallow models did not recover a killed simple-rule edge.

9. Largest group increment on the locked M1/Z60/T1 slice: removing OI *raised* OIL val AUC (0.5647 -> 0.5945). Futures did not help. Cross-asset removal helped GOLD AUC toward 0.50 but stayed below a useful edge.

10. Futures lift: ALL val AUC 0.5167 vs ALL_MINUS_FUT 0.5221. Futures did not improve the locked slice.

11. COT/EIA/Rates lift: ALL val AUC 0.5167 vs ALL_MINUS_PUBLIC 0.5078. Public group is a small mixed increment, not a candidate driver.

12. MT5-only vs ALL: MT5_ONLY val AUC 0.5213 vs ALL 0.5167. Adding futures+public did not produce a better program model.

13. External live data required: NO. No candidate. A later ALL-data OIL cell would need futures/public live inputs; MT5-only would not.

14. Databento further spend: NO. $31.82 added 0 Candidates in V9 and 0 in V10. $93 remains UNUSED_RESEARCH_RESERVE.

15. Distance to long-run CAGR>=10%: still LEVEL=0. The gap is a reproducible predictive+economic edge after cost and multiple testing, not another simple CFD, not AutoML on the same set, and not an automatic options purchase.

## MODEL_REPRESENTATION_EXHAUSTED

All locked model families failed the Level 1 gate. Human may later choose options, macro surprise, news, or a new trading universe. This mission does not buy or redefine targets.

Do not reopen killed simple-rule families. Do not spend the $93 reserve on this result.
