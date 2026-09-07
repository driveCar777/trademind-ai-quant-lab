# Post-V21 Failure Atlas — W3

**Date:** 2026-09-04  
**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/FAILURE_ATLAS.json`  
**Script:** `research_engine/post_v21_w3_atlas.py`

Span V8–V21. 60 rows. Validation capital negative: 42. Beat EW on overlap: 13. Level-1: 2 (H11/H12, one cluster). NEW_INDEPENDENT: 0.

| id | ver | mechanism | val MF | val cap | sign | beat EW | corr H11 | frozen | why not next |
|---|---|---|---|---|---|---|---|---|---|
| V8_FUSION_TOP5 | V8 | Existing-information fusion (OI / volume / DTE / gap / steepening / yi | — | — | NEG_OR_NONE | — | — | Y | All fusion cells failed FDR; options unpaid; do not retune gap/steepening/OI/wow/yield. |
| V9_MASTER_REPLAY | V9 | Replay all legal strategy mechanisms on owned data | — | — | NO_REPRODUCIBLE | — | — | Y | Research-positive but no Positive Reproducible Strategy; $31.82 Databento added 0 Candidates. |
| V10_MODEL_REPRESENTATION | V10 | Nonlinear models (FOREST etc.) on owned features | — | — | NEG_OR_NONE | — | — | Y | Model did not recover killed rules; OIL-heavy; cost stress flipped greens. |
| V11_ALLOCATION_REVIEW | V11 | Pick next universe | — | — | — | — | — | Y | Executed: V12-V21 followed. MT5 alpha frozen. |
| V12_PANEL | V12/V12.1/V12.2 | PIT daily panel freeze (BaoStock) | — | — | — | — | — | Y | Infrastructure, not alpha. |
| H11_H12_OFFICIAL_BOOK | V14/V14.1 | Long low realized vol (60/120d), quintile, 20d non-overlap capital | — | — | NEG (full −15.61%, val cont. −0.06%, val fresh +0.31%) | — | — | Y | MaxDD −66%; AM-GM; one cluster (corr 0.996); KEEP_LOW_PRIORITY; no retune. |
| H21_RESID_REV_20_H20 | V15 | CROSS_SECTIONAL_RESIDUAL | -0.14% | -1.36% | NEG | Y | 0.91 | Y | validation capital negative; beat EW on overlap only; still lost; corr vs H11 0.91 = same sleeve; FDR hit without capital = not Candidate |
| H22_RESID_REV_60_H20 | V15 | CROSS_SECTIONAL_RESIDUAL | -0.20% | -2.70% | NEG | Y | 0.92 | Y | validation capital negative; beat EW on overlap only; still lost; corr vs H11 0.92 = same sleeve; FDR hit without capital = not Candidate |
| H23_RESID_REV_20_H5 | V15 | CROSS_SECTIONAL_RESIDUAL | -0.35% | -43.82% | NEG | Y | 0.63 | Y | validation capital negative; beat EW on overlap only; still lost |
| H24_DISP_HIGH_RESID_20_H20 | V15 | MARKET_DISPERSION_STATE | 1.13% | -15.05% | NEG | Y | 0.67 | Y | validation capital negative; beat EW on overlap only; still lost; FDR hit without capital = not Candidate |
| H25_DISP_UP_RESID_20_H20 | V15 | MARKET_DISPERSION_STATE | 0.74% | -5.18% | NEG | Y | 0.67 | Y | validation capital negative; beat EW on overlap only; still lost; FDR hit without capital = not Candidate |
| H26_DISP_HIGH_LOW_BREADTH_20_H20 | V15 | MARKET_DISPERSION_STATE | 0.16% | -12.38% | NEG | Y | 0.59 | Y | validation capital negative; beat EW on overlap only; still lost; FDR hit without capital = not Candidate |
| H27_CAPITULATION_20_H20 | V15 | PRICE_ACTIVITY_DISAGREEMENT | -0.83% | -23.16% | NEG | N | — | Y | validation capital negative |
| H28_CAPITULATION_60_H20 | V15 | PRICE_ACTIVITY_DISAGREEMENT | -0.77% | -21.86% | NEG | N | — | Y | validation capital negative |
| H29_PX_AMT_CORR_20_H20 | V15 | PRICE_ACTIVITY_DISAGREEMENT | -0.24% | -1.54% | NEG | Y | 0.93 | Y | validation capital negative; beat EW on overlap only; still lost; corr vs H11 0.93 = same sleeve; FDR hit without capital = not Candidate |
| F1_YOY_NP_ANN | V16F | Latest visible annual net_profit vs prior visible annual. Long high Yo | -1.04% | -28.24% | NEG | N | — | Y | validation capital negative |
| F1_YOY_REV_ANN | V16F | Latest visible annual revenue vs prior visible annual. Long high YoY. | -1.38% | -35.78% | NEG | N | — | Y | validation capital negative |
| F2_ROE_ANN | V16F | Latest visible annual ROE. Long high ROE. | -1.63% | -40.87% | NEG | N | — | Y | validation capital negative |
| F2_GPM_ANN | V16F | Latest visible annual gross margin. Long high GPM. | -0.96% | -27.61% | NEG | N | — | Y | validation capital negative |
| F3_NPM_ANN | V16F | Latest visible annual net profit margin. Long high quality. | -1.41% | -35.99% | NEG | N | — | Y | validation capital negative |
| F4_ROE_DELTA_ANN | V16F | Change in annual ROE vs prior visible annual. Long improving ROE. | -0.97% | -26.94% | NEG | N | — | Y | validation capital negative |
| I1_IND_RS_20 | V16I | PIT industry 20-day EW close return. Long names in strong industries. | -1.36% | -33.80% | NEG | N | — | Y | validation capital negative |
| I2_IND_RS_60 | V16I | PIT industry 60-day EW close return. Long names in strong industries. | -1.31% | -32.72% | NEG | N | — | Y | validation capital negative |
| I3_IND_BREADTH_20 | V16I | PIT industry 20-day breadth (pct members with positive close return).  | -1.27% | -28.86% | NEG | N | — | Y | validation capital negative |
| M1_USD_DEF_60 | V17 | USD_STRENGTH_DEFENSIVE | -1.25% | -44.01% | NEG | N | — | Y | validation capital negative |
| M2_USD_DEF_120 | V17 | USD_STRENGTH_DEFENSIVE | -1.18% | -39.81% | NEG | N | — | Y | validation capital negative |
| M3_US_CONT_60 | V17 | GLOBAL_EQUITY_CONTINUATION | -1.04% | -23.30% | NEG | N | — | Y | validation capital negative |
| M4_US_CONT_120 | V17 | GLOBAL_EQUITY_CONTINUATION | -1.01% | -18.68% | NEG | N | — | Y | validation capital negative |
| M5_GVZ_DEF_60 | V17 | GOLD_VOL_DEFENSIVE | -1.06% | -40.13% | NEG | N | — | Y | validation capital negative |
| M6_GVZ_DEF_120 | V17 | GOLD_VOL_DEFENSIVE | -0.90% | -30.70% | NEG | N | — | Y | validation capital negative |
| A1_SEASONED_AGE | V18 | LISTING_AGE | -0.50% | -10.56% | NEG | Y | 0.97 | Y | validation capital negative; beat EW on overlap only; still lost; corr vs H11 0.97 = same sleeve; FDR hit without capital = not Candidate |
| A2_RELATIVE_AGE | V18 | LISTING_AGE | -0.50% | -10.56% | NEG | Y | 0.97 | Y | validation capital negative; beat EW on overlap only; still lost; corr vs H11 0.97 = same sleeve; FDR hit without capital = not Candidate |
| A3_CLEAN_STREAK | V18 | ST_HISTORY | -1.06% | -31.92% | NEG | N | — | Y | validation capital negative |
| A4_RECENT_RESUME | V18 | SUSPEND_RESUME | -1.30% | -34.42% | NEG | N | — | Y | validation capital negative |
| A5_MONTH_END_SEASONED | V18 | CALENDAR_WINDOW | 0.12% | -19.95% | NEG | Y | 0.46 | Y | validation capital negative; beat EW on overlap only; still lost |
| A6_QUARTER_END_SEASONED | V18 | CALENDAR_WINDOW | -2.61% | -34.98% | NEG | Y | 0.71 | Y | validation capital negative; beat EW on overlap only; still lost |
| IM1_USD_IND_DEF_60 | V19 | INDUSTRY_USD_DEFENSIVE | -0.96% | -43.51% | NEG | N | — | Y | validation capital negative |
| IM2_USD_IND_DEF_120 | V19 | INDUSTRY_USD_DEFENSIVE | -1.04% | -36.56% | NEG | N | — | Y | validation capital negative |
| IM3_US_IND_CONT_60 | V19 | INDUSTRY_US_CONTINUATION | -0.89% | -13.46% | NEG | N | — | Y | validation capital negative |
| IM4_US_IND_CONT_120 | V19 | INDUSTRY_US_CONTINUATION | -0.74% | -5.00% | NEG | N | — | Y | validation capital negative |
| IM5_GVZ_IND_DEF_60 | V19 | INDUSTRY_GVZ_DEFENSIVE | -0.59% | -34.09% | NEG | Y | 0.67 | Y | validation capital negative; beat EW on overlap only; still lost |
| IM6_GVZ_IND_DEF_120 | V19 | INDUSTRY_GVZ_DEFENSIVE | -0.39% | -22.43% | NEG | Y | 0.64 | Y | validation capital negative; beat EW on overlap only; still lost; FDR hit without capital = not Candidate |
| X1_HS300_SET | V20 | INDEX_MEMBERSHIP | -1.26% | -32.50% | NEG | N | — | Y | validation capital negative |
| X2_ZZ500_SET | V20 | INDEX_MEMBERSHIP | -1.00% | -23.88% | NEG | N | — | Y | validation capital negative |
| X3_HS300_IN_252 | V20 | INDEX_RECONSTITUTION | -2.37% | -56.79% | NEG | N | — | Y | validation capital negative |
| X4_HS300_OUT_252 | V20 | INDEX_RECONSTITUTION | -1.21% | -26.65% | NEG | N | — | Y | validation capital negative |
| D1_CASH_ANN_20 | V21 | DIVIDEND_CASH_EVENT | -4.24% | -41.06% | NEG | N | — | Y | validation capital negative |
| D2_STOCK_ANN_20 | V21 | DIVIDEND_STOCK_EVENT | -16.48% | -72.02% | NEG | N | — | Y | validation capital negative |
| H01_MOM_20 | V13 | CROSS_SECTIONAL_MOMENTUM | -2.29% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | frozen family; no val edge |
| H02_MOM_60 | V13 | CROSS_SECTIONAL_MOMENTUM | -2.37% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | frozen family; no val edge |
| H03_MOM_120 | V13 | CROSS_SECTIONAL_MOMENTUM | -2.37% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | frozen family; no val edge |
| H04_REV_20 | V13 | CROSS_SECTIONAL_REVERSAL | -0.14% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H05_REV_60 | V13 | CROSS_SECTIONAL_REVERSAL | -0.22% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H06_REV_120 | V13 | CROSS_SECTIONAL_REVERSAL | -0.21% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H07_ACT_20 | V13 | CROSS_SECTIONAL_ACTIVITY | -0.01% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H08_ACT_60 | V13 | CROSS_SECTIONAL_ACTIVITY | -0.12% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H09_ACT_120 | V13 | CROSS_SECTIONAL_ACTIVITY | -0.16% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H10_VOL_20 | V13 | CROSS_SECTIONAL_VOLATILITY | -0.07% | — | V13_OVERLAP_ONLY (mf<0) | — | — | Y | FDR hit without capital = not Candidate |
| H11_VOL_60 | V13 | CROSS_SECTIONAL_VOLATILITY | 0.05% | — | V13_OVERLAP_ONLY (mf>0) | — | — | Y | Level-1 but one low-vol cluster; official book negative |
| H12_VOL_120 | V13 | CROSS_SECTIONAL_VOLATILITY | 0.11% | — | V13_OVERLAP_ONLY (mf>0) | — | — | Y | Level-1 but one low-vol cluster; official book negative |

### Appended after S1 (V22-V27; V25 ML1 is the first Level-1 row — not a failure)

| id | ver | universe | val MF | val cap | beat EW | corr H11 (month) | FDR | why not next |
|---|---|---|---|---|---|---|---|---|
| FX1_XS_CARRY | V22 | CME futures 30 roots | — | 11.3% | — | -0.19 | N | Research 2010-2021 flat before cost (gross CAGR ~1%); no FDR discovery; validation tail not promoted. Do not retune / buy OI. |
| FX2_XS_MOM_12_1 | V22 | CME futures 30 roots | — | 9.2% | — | -0.07 | N | Research 2010-2021 flat before cost (gross CAGR ~1%); no FDR discovery; validation tail not promoted. Do not retune / buy OI. |
| FX3_TSMOM_12 | V22 | CME futures 30 roots | — | 4.3% | — | -0.12 | N | Research 2010-2021 flat before cost (gross CAGR ~1%); no FDR discovery; validation tail not promoted. Do not retune / buy OI. |
| M1_LOW_NET_MARGIN_INFLOW_20 | V23 | A-share marginable | -0.67% | -19.2% | Y | 0.78 | N | Research excess t=4.85 and capital +37%, but validation capital -19% and excess t=0.92; no FDR. Different failure shape (research-real, validation-flat). Do not retune or filter. |
| M2_LOW_MARGIN_BALANCE_RATIO | V23 | A-share marginable | -1.32% | -32.1% | N | 0.35 | N | Validation capital negative; validation excess <= 0. |
| M3_MARGIN_DELEVERAGED_60 | V23 | A-share marginable | -0.76% | -22.5% | N | 0.33 | N | Validation capital negative; validation excess <= 0. |
| HC1_CONCENTRATION_QOQ | V24 | A-share | -0.88% | -25.5% | N | 0.63 | N | See V24_HOLDERS_DECISION.md |
| HC2_CONCENTRATION_2Q | V24 | A-share | -0.89% | -26.4% | N | 0.64 | N | See V24_HOLDERS_DECISION.md |
| HC3_LOW_HOLDERS_PER_SHARE | V24 | A-share | -0.75% | -18.2% | N | 0.72 | N | See V24_HOLDERS_DECISION.md |
| ML1_LGBM_STACK | V25 | A-share eligible | 0.74% | 30.9% | Y | — | Y | LEVEL-1 PASS; 7/7 reproduction; excess-corr vs H11 0.06 -> INDEPENDENT under A4. Frozen. Next = strategy spec + human Final OOS decision. Not a failure row. |
| ML0_RANK_AVERAGE | V25 | A-share eligible | 0.00% | 3.7% | Y | — | Y | Beats EW (t 7.6 validation) but research HN20 capital negative; no-fit baseline; shows combination alone is not enough, fitted nonlinearity is. |
| ML2F_LGBM_FINDEEP_ONLY | V27 | A-share eligible | -0.21% | -0.3% | Y | — | Y | Quarterly-filings-only model: excess vs EW +0.65%/20d research, +0.52% validation (t 5.6), rolling 5/5, FDR Y, excess-corr vs ML1 0.06 (independent) -- but LO20 validation capital -0.3% (flat, bear market) -> NOT Level-1. Weak independent predictive edge with no positive book. HN20 val +12% already SEEN: no post-hoc HN20 contract for this signal. Frozen. |
| ML2_LGBM_FULL_STACK | V27 | A-share eligible | 0.69% | 28.0% | Y | — | Y | ML1 14 + 10 quarterly features: Level-1 but excess-corr vs ML1 0.96 = SAME_CLUSTER (pre-declared). Validation excess 1.42% vs ML1 1.47%, LO20 +28.0% vs +30.9%: quarterly layer adds nothing on top of ML1. ML1 unchanged. |

## Use

Before opening any new family, find its mechanism here. If it is a row (or a ratio / membership / filing-window sibling of a row), it is not the next unit. Next: W4 strategy bind.
