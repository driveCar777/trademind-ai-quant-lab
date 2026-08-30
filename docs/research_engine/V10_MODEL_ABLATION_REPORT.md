# V10 Model Ablation Report

Pre-registered slice: M1 + REP_Z60 + T1_DIR1. Leave-one-group-out. Not chosen after PnL.

- GOLD ALL val AUC=0.4687 logloss=0.6979 adv=False
- OIL ALL val AUC=0.5647 logloss=0.6837 adv=True
- GOLD ALL_MINUS_FUT val AUC=0.4720 logloss=0.6981 adv=False
- GOLD ALL_MINUS_OI val AUC=0.4727 logloss=0.6973 adv=False
- GOLD ALL_MINUS_PUBLIC val AUC=0.4661 logloss=0.6971 adv=False
- GOLD ALL_MINUS_XASSET val AUC=0.4959 logloss=0.6913 adv=False
- GOLD MT5_ONLY val AUC=0.4660 logloss=0.6966 adv=False
- OIL ALL_MINUS_FUT val AUC=0.5721 logloss=0.6843 adv=True
- OIL ALL_MINUS_OI val AUC=0.5945 logloss=0.6778 adv=True
- OIL ALL_MINUS_PUBLIC val AUC=0.5496 logloss=0.6867 adv=True
- OIL ALL_MINUS_XASSET val AUC=0.5630 logloss=0.6825 adv=True
- OIL MT5_ONLY val AUC=0.5765 logloss=0.6831 adv=True

Futures increment (ALL vs ALL_MINUS_FUT) mean val AUC: 0.5167 vs 0.5221
Public increment (ALL vs ALL_MINUS_PUBLIC) mean val AUC: 0.5167 vs 0.5078
MT5-only vs ALL mean val AUC: 0.5213 vs 0.5167
