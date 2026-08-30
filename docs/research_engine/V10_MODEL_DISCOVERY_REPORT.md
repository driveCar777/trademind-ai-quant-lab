# V10 Model Discovery Report

**Date:** 2026-08-30
**Stop:** STOP_B_MODEL_REPRESENTATION_EXHAUSTED
**Purchase:** NO
**Final OOS:** DENIED

## Program

```
LEVEL = 0
CANDIDATE = 0
STRATEGY = 0
n_experiments = 62
n_predictive_advantage = 21
n_fdr_discoveries = 0
n_traded = 21
Xavier = NOT_USED_LOCAL_SKLEARN
```

Hypothesis tested: existing information may contain nonlinear / interaction structure not captured by simple rules. MODEL is not assumed to be alpha.

Owned model features: 29. Owned immutable datasets scanned: 110.
Contract hash: `8e361351298aabfa4d63bf0ade2e00ea033961430dd925b40a1e11dddbfe8229`.

## Families

- FOREST: advantage 9/16, mean val AUC 0.5285
- LOGISTIC: advantage 6/16, mean val AUC 0.5239
- TREE: advantage 1/16, mean val AUC 0.5229

Economic status counts: LOSS=37, NONE=14, POSITIVE_BUT_WEAK=6, POSITIVE_REPRODUCIBLE=5.
FDR Benjamini-Hochberg q=0.05 on 62 cells: 0 discoveries. Single-window AUC around 0.55 is not a program edge.
M1 Logistic on RAW hit the frozen max_iter=200 cap on some cells. That is recorded, not retuned.

## Predictive advantage cells

- V10-M3-REP_INTERACT-T1_DIR1-GOLD val AUC=0.5415 logloss=0.6850 FDR=False
- V10-M1-REP_RAW-T2_DIR5-GOLD val AUC=0.5570 logloss=0.6744 FDR=False
- V10-M3-REP_INTERACT-T2_DIR5-GOLD val AUC=0.5287 logloss=0.6752 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL val AUC=0.5647 logloss=0.6837 FDR=False
- V10-M1-REP_INTERACT-T1_DIR1-OIL val AUC=0.5633 logloss=0.6852 FDR=False
- V10-M1-REP_STATE-T1_DIR1-OIL val AUC=0.5698 logloss=0.6822 FDR=False
- V10-M2-REP_RAW-T1_DIR1-OIL val AUC=0.5560 logloss=0.6932 FDR=False
- V10-M3-REP_RAW-T1_DIR1-OIL val AUC=0.5228 logloss=0.6933 FDR=False
- V10-M3-REP_Z60-T1_DIR1-OIL val AUC=0.5556 logloss=0.6903 FDR=False
- V10-M3-REP_STATE-T1_DIR1-OIL val AUC=0.5750 logloss=0.6867 FDR=False
- V10-M1-REP_RAW-T2_DIR5-OIL val AUC=0.5356 logloss=0.6986 FDR=False
- V10-M1-REP_INTERACT-T2_DIR5-OIL val AUC=0.5620 logloss=0.6974 FDR=False
- V10-M3-REP_RAW-T2_DIR5-OIL val AUC=0.5134 logloss=0.6973 FDR=False
- V10-M3-REP_Z60-T2_DIR5-OIL val AUC=0.5311 logloss=0.6943 FDR=False
- V10-M3-REP_INTERACT-T2_DIR5-OIL val AUC=0.5261 logloss=0.6958 FDR=False
- V10-M3-REP_STATE-T2_DIR5-OIL val AUC=0.5206 logloss=0.6958 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_FUT val AUC=0.5721 logloss=0.6843 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_OI val AUC=0.5945 logloss=0.6778 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_PUBLIC val AUC=0.5496 logloss=0.6867 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_XASSET val AUC=0.5630 logloss=0.6825 FDR=False
- V10-M1-REP_Z60-T1_DIR1-OIL-MT5_ONLY val AUC=0.5765 logloss=0.6831 FDR=False

Do not retune depth / threshold / lookback / hold. That would be a new experiment.
