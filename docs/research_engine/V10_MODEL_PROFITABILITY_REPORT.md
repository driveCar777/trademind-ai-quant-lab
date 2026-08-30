# V10 Model Profitability Report

Trading conversion required validation logloss and Brier better than M0 and AUC>0.5. Otherwise MODEL_ONLY.
Thresholds 0.55/0.60/0.65 and risk 0.5%/1.0% were all pre-registered. Primary report: 0.55 / 1%.
Execution: NEXT_BAR_OPEN + V0.6 spread + 5bp commission + 10bp slip.

Converted cells: 21. Strategy metric rows: 252.
### V10-M3-REP_INTERACT-T1_DIR1-GOLD
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.0930 CAGR=-0.0102 MaxDD=-0.1236 Sharpe=-0.3631 trades=322 cost=6004.1123
- validation net=-0.0716 CAGR=-0.0078 MaxDD=-0.0739 Sharpe=-0.6233 trades=48 cost=781.8945
- validation_stress_costx2_slipx2 net=-0.1321 CAGR=-0.0148 MaxDD=-0.1337 Sharpe=-1.1000 trades=49 cost=1492.2233
### V10-M1-REP_RAW-T2_DIR5-GOLD
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.0048 CAGR=-0.0005 MaxDD=-0.1847 Sharpe=0.0154 trades=257 cost=4601.3813
- validation net=0.0626 CAGR=0.0064 MaxDD=-0.0481 Sharpe=0.2724 trades=51 cost=802.8096
- validation_stress_costx2_slipx2 net=-0.0613 CAGR=-0.0066 MaxDD=-0.0869 Sharpe=-0.2445 trades=52 cost=1479.9120
### V10-M3-REP_INTERACT-T2_DIR5-GOLD
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.2340 CAGR=0.0223 MaxDD=-0.1579 Sharpe=0.4672 trades=248 cost=4699.2761
- validation net=0.0293 CAGR=0.0030 MaxDD=-0.0558 Sharpe=0.1354 trades=57 cost=837.8133
- validation_stress_costx2_slipx2 net=-0.0797 CAGR=-0.0087 MaxDD=-0.0989 Sharpe=-0.3157 trades=59 cost=1596.0376
### V10-M1-REP_Z60-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2416 CAGR=-0.0287 MaxDD=-0.2522 Sharpe=-0.8239 trades=526 cost=3633.5900
- validation net=-0.0413 CAGR=-0.0044 MaxDD=-0.0933 Sharpe=-0.2467 trades=118 cost=1076.5469
- validation_stress_costx2_slipx2 net=-0.1316 CAGR=-0.0147 MaxDD=-0.1700 Sharpe=-0.8352 trades=118 cost=1940.6829
### V10-M1-REP_INTERACT-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.1864 CAGR=-0.0215 MaxDD=-0.2184 Sharpe=-0.6049 trades=558 cost=3986.5346
- validation net=-0.1073 CAGR=-0.0119 MaxDD=-0.1332 Sharpe=-0.6473 trades=123 cost=1068.3628
- validation_stress_costx2_slipx2 net=-0.1912 CAGR=-0.0221 MaxDD=-0.2096 Sharpe=-1.1973 trades=123 cost=1926.7088
### V10-M1-REP_STATE-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2537 CAGR=-0.0303 MaxDD=-0.2702 Sharpe=-0.8589 trades=545 cost=3863.8919
- validation net=-0.0814 CAGR=-0.0089 MaxDD=-0.1143 Sharpe=-0.4932 trades=124 cost=1096.8766
- validation_stress_costx2_slipx2 net=-0.1709 CAGR=-0.0195 MaxDD=-0.1944 Sharpe=-1.0791 trades=124 cost=1974.5276
### V10-M2-REP_RAW-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.0160 CAGR=-0.0017 MaxDD=-0.0651 Sharpe=-0.0773 trades=168 cost=1909.8129
- validation net=-0.0673 CAGR=-0.0073 MaxDD=-0.0711 Sharpe=-0.5747 trades=64 cost=748.0930
- validation_stress_costx2_slipx2 net=-0.1266 CAGR=-0.0141 MaxDD=-0.1284 Sharpe=-1.0949 trades=64 cost=1368.3990
### V10-M3-REP_RAW-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.1203 CAGR=0.0120 MaxDD=-0.0389 Sharpe=0.5973 trades=230 cost=1714.9797
- validation net=-0.0829 CAGR=-0.0091 MaxDD=-0.1013 Sharpe=-0.8033 trades=39 cost=296.1682
- validation_stress_costx2_slipx2 net=-0.1069 CAGR=-0.0118 MaxDD=-0.1228 Sharpe=-1.0211 trades=39 cost=552.4151
### V10-M3-REP_Z60-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.2748 CAGR=0.0259 MaxDD=-0.0211 Sharpe=1.2835 trades=231 cost=2145.9055
- validation net=-0.0368 CAGR=-0.0039 MaxDD=-0.0422 Sharpe=-0.3632 trades=34 cost=329.1876
- validation_stress_costx2_slipx2 net=-0.0644 CAGR=-0.0070 MaxDD=-0.0673 Sharpe=-0.6371 trades=34 cost=613.8285
### V10-M3-REP_STATE-T1_DIR1-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.3435 CAGR=0.0316 MaxDD=-0.0283 Sharpe=1.2448 trades=255 cost=2600.5427
- validation net=0.0178 CAGR=0.0019 MaxDD=-0.0311 Sharpe=0.1566 trades=43 cost=411.0408
- validation_stress_costx2_slipx2 net=-0.0187 CAGR=-0.0020 MaxDD=-0.0476 Sharpe=-0.1544 trades=43 cost=764.5175
### V10-M1-REP_RAW-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.0161 CAGR=0.0017 MaxDD=-0.1655 Sharpe=0.0592 trades=236 cost=1770.3374
- validation net=-0.0373 CAGR=-0.0040 MaxDD=-0.0851 Sharpe=-0.1684 trades=52 cost=412.9205
- validation_stress_costx2_slipx2 net=-0.0642 CAGR=-0.0070 MaxDD=-0.1036 Sharpe=-0.2852 trades=52 cost=787.8265
### V10-M1-REP_INTERACT-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.3348 CAGR=0.0309 MaxDD=-0.0838 Sharpe=0.5940 trades=278 cost=2446.4338
- validation net=0.0048 CAGR=0.0005 MaxDD=-0.0826 Sharpe=0.0321 trades=64 cost=525.0903
- validation_stress_costx2_slipx2 net=-0.0318 CAGR=-0.0034 MaxDD=-0.0905 Sharpe=-0.1138 trades=64 cost=978.2253
### V10-M3-REP_RAW-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.4588 CAGR=0.0405 MaxDD=-0.1152 Sharpe=0.8235 trades=273 cost=2341.0032
- validation net=0.0925 CAGR=0.0094 MaxDD=-0.0554 Sharpe=0.4009 trades=49 cost=454.3615
- validation_stress_costx2_slipx2 net=0.0394 CAGR=0.0041 MaxDD=-0.0731 Sharpe=0.1814 trades=50 cost=846.3898
### V10-M3-REP_Z60-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.4484 CAGR=0.0397 MaxDD=-0.0722 Sharpe=0.8609 trades=226 cost=2270.3222
- validation net=0.0437 CAGR=0.0045 MaxDD=-0.0724 Sharpe=0.2151 trades=42 cost=386.2929
- validation_stress_costx2_slipx2 net=0.0055 CAGR=0.0006 MaxDD=-0.0787 Sharpe=0.0370 trades=43 cost=725.9275
### V10-M3-REP_INTERACT-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.4673 CAGR=0.0412 MaxDD=-0.0649 Sharpe=0.8362 trades=257 cost=2446.4536
- validation net=-0.0432 CAGR=-0.0046 MaxDD=-0.0625 Sharpe=-0.2248 trades=41 cost=351.7562
- validation_stress_costx2_slipx2 net=-0.0698 CAGR=-0.0076 MaxDD=-0.0717 Sharpe=-0.3739 trades=41 cost=658.1662
### V10-M3-REP_STATE-T2_DIR5-OIL
model_vs_rule: MODEL_ADDS_VALUE
- research net=0.5113 CAGR=0.0444 MaxDD=-0.1010 Sharpe=0.9243 trades=233 cost=2356.1814
- validation net=-0.0387 CAGR=-0.0041 MaxDD=-0.0766 Sharpe=-0.1862 trades=36 cost=309.2923
- validation_stress_costx2_slipx2 net=-0.0631 CAGR=-0.0068 MaxDD=-0.0961 Sharpe=-0.3083 trades=36 cost=582.3684
### V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_FUT
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2790 CAGR=-0.0338 MaxDD=-0.2858 Sharpe=-1.0130 trades=496 cost=3462.5661
- validation net=-0.0480 CAGR=-0.0052 MaxDD=-0.0608 Sharpe=-0.3584 trades=109 cost=983.6908
- validation_stress_costx2_slipx2 net=-0.1304 CAGR=-0.0146 MaxDD=-0.1334 Sharpe=-1.0139 trades=109 cost=1778.9786
### V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_OI
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.1684 CAGR=-0.0192 MaxDD=-0.1908 Sharpe=-0.5623 trades=485 cost=3519.4291
- validation net=-0.0178 CAGR=-0.0019 MaxDD=-0.0654 Sharpe=-0.1109 trades=106 cost=969.9778
- validation_stress_costx2_slipx2 net=-0.1010 CAGR=-0.0111 MaxDD=-0.1307 Sharpe=-0.6902 trades=106 cost=1754.2379
### V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_PUBLIC
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2766 CAGR=-0.0335 MaxDD=-0.2789 Sharpe=-1.0354 trades=513 cost=3534.5483
- validation net=-0.1045 CAGR=-0.0115 MaxDD=-0.1434 Sharpe=-0.6810 trades=108 cost=941.7664
- validation_stress_costx2_slipx2 net=-0.1799 CAGR=-0.0207 MaxDD=-0.2071 Sharpe=-1.2022 trades=108 cost=1708.4904
### V10-M1-REP_Z60-T1_DIR1-OIL-ALL_MINUS_XASSET
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2252 CAGR=-0.0265 MaxDD=-0.2442 Sharpe=-0.7598 trades=504 cost=3552.7086
- validation net=-0.0223 CAGR=-0.0024 MaxDD=-0.0849 Sharpe=-0.1130 trades=120 cost=1080.4418
- validation_stress_costx2_slipx2 net=-0.1143 CAGR=-0.0127 MaxDD=-0.1629 Sharpe=-0.6455 trades=120 cost=1948.1682
### V10-M1-REP_Z60-T1_DIR1-OIL-MT5_ONLY
model_vs_rule: MODEL_ADDS_VALUE
- research net=-0.2327 CAGR=-0.0275 MaxDD=-0.2369 Sharpe=-0.9835 trades=391 cost=2787.6348
- validation net=-0.0630 CAGR=-0.0068 MaxDD=-0.0724 Sharpe=-0.5562 trades=83 cost=726.8293
- validation_stress_costx2_slipx2 net=-0.1232 CAGR=-0.0137 MaxDD=-0.1257 Sharpe=-1.1035 trades=83 cost=1330.3769

Cost×2 / slip×2 are stress tests, not selection.
