# V16 Capital Account Report

CAGR is taken only from the non-overlapping capital book. MEAN_FORWARD_RETURN is a different object.
Initial = 1,000,000. Cost model locked. Do not lower cost to pass a gate.

| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Val MaxDD | Val Sharpe | Rank IC val | FDR | L1 | Cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1_YOY_NP_ANN | EARNINGS_GROWTH | -1.04% | -43.77% | -28.24% | -12.15% | -40.02% | -0.3739 | -0.0273 | False | False | None |
| F1_YOY_REV_ANN | EARNINGS_GROWTH | -1.38% | -55.26% | -35.78% | -15.87% | -45.89% | -0.5373 | -0.0377 | False | False | None |
| F2_ROE_ANN | PROFITABILITY | -1.63% | -67.47% | -40.87% | -18.54% | -48.18% | -0.7452 | -0.0446 | False | False | None |
| F2_GPM_ANN | PROFITABILITY | -0.96% | -52.64% | -27.61% | -11.85% | -37.79% | -0.3754 | -0.0192 | False | False | None |
| F3_NPM_ANN | QUALITY | -1.41% | -64.99% | -35.99% | -15.98% | -43.41% | -0.6666 | -0.0312 | False | False | None |
| F4_ROE_DELTA_ANN | FINANCIAL_CHANGE | -0.97% | -40.48% | -26.94% | -11.53% | -39.30% | -0.3574 | -0.0047 | False | False | None |
| I1_IND_RS_20 | INDUSTRY_RELATIVE_STRENGTH | -1.36% | -33.38% | -33.80% | -14.87% | -40.48% | -0.4835 | -0.0447 | False | False | None |
| I2_IND_RS_60 | INDUSTRY_RELATIVE_STRENGTH | -1.31% | -39.82% | -32.72% | -14.33% | -38.68% | -0.5237 | -0.0636 | False | False | None |
| I3_IND_BREADTH_20 | INDUSTRY_BREADTH | -1.27% | -25.46% | -28.86% | -12.45% | -37.19% | -0.3827 | -0.0361 | False | False | None |

## F1_YOY_NP_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -43.77% / -4.79% / -68.35% / -0.0397
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -28.24% / -12.15% / -40.02% / -0.3739
- Validation years: 2021 compound 0.92%; 2022 compound -14.30%; 2023 compound -15.83%; 2024 compound -1.42%
- Unfilled validation: 0.005894422682335385
- Concentration: {'rebalance': {'n': 172, 'n_negative': 88, 'top_10_of_pos': 0.6070067769204673, 'top_1_of_pos': 0.12709757075528336, 'top_20_of_pos': 0.7966471174175953, 'top_5_of_pos': 0.41025411582010013}}

## F1_YOY_REV_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -55.26% / -6.62% / -71.44% / -0.1272
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -35.78% / -15.87% / -45.89% / -0.5373
- Validation years: 2021 compound 0.99%; 2022 compound -16.59%; 2023 compound -21.87%; 2024 compound -2.41%
- Unfilled validation: 0.0038644805462799683
- Concentration: {'rebalance': {'n': 172, 'n_negative': 89, 'top_10_of_pos': 0.635650854377478, 'top_1_of_pos': 0.11660137449622263, 'top_20_of_pos': 0.8291370610749592, 'top_5_of_pos': 0.42485202763354063}}

## F2_ROE_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -67.47% / -9.13% / -73.28% / -0.2665
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -40.87% / -18.54% / -48.18% / -0.7452
- Validation years: 2021 compound -2.13%; 2022 compound -19.47%; 2023 compound -24.88%; 2024 compound -0.15%
- Unfilled validation: 0.003069410533658877
- Concentration: {'rebalance': {'n': 172, 'n_negative': 92, 'top_10_of_pos': 0.663978991898833, 'top_1_of_pos': 0.1269835350100553, 'top_20_of_pos': 0.8511728541946078, 'top_5_of_pos': 0.441980693720935}}

## F2_GPM_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -52.64% / -6.17% / -71.85% / -0.1096
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -27.61% / -11.85% / -37.79% / -0.3754
- Validation years: 2021 compound -0.33%; 2022 compound -12.62%; 2023 compound -15.44%; 2024 compound -1.71%
- Unfilled validation: 0.00434689660086938
- Concentration: {'rebalance': {'n': 172, 'n_negative': 88, 'top_10_of_pos': 0.6165831907859237, 'top_1_of_pos': 0.11437918411518502, 'top_20_of_pos': 0.8214325637684622, 'top_5_of_pos': 0.40869827897961203}}

## F3_NPM_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -64.99% / -8.56% / -72.25% / -0.2180
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -35.99% / -15.98% / -43.41% / -0.6666
- Validation years: 2021 compound -2.04%; 2022 compound -17.58%; 2023 compound -20.14%; 2024 compound -0.72%
- Unfilled validation: 0.0030703743763302047
- Concentration: {'rebalance': {'n': 172, 'n_negative': 90, 'top_10_of_pos': 0.6688717424684433, 'top_1_of_pos': 0.1198930875461443, 'top_20_of_pos': 0.8584163299939475, 'top_5_of_pos': 0.4337690713953833}}

## F4_ROE_DELTA_ANN

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -40.48% / -4.32% / -67.60% / -0.0317
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -26.94% / -11.53% / -39.30% / -0.3574
- Validation years: 2021 compound 0.94%; 2022 compound -15.22%; 2023 compound -14.11%; 2024 compound -0.60%
- Unfilled validation: 0.005988472191032263
- Concentration: {'rebalance': {'n': 172, 'n_negative': 87, 'top_10_of_pos': 0.6045565220325938, 'top_1_of_pos': 0.12496557364569931, 'top_20_of_pos': 0.8002423725896426, 'top_5_of_pos': 0.4098518310843981}}

## I1_IND_RS_20

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -33.38% / -3.40% / -69.57% / 0.0074
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -33.80% / -14.87% / -40.48% / -0.4835
- Validation years: 2021 compound -1.92%; 2022 compound -17.81%; 2023 compound -10.96%; 2024 compound -7.75%
- Unfilled validation: 0.007137359177104471
- Concentration: {'rebalance': {'n': 172, 'n_negative': 87, 'top_10_of_pos': 0.5838846335192808, 'top_1_of_pos': 0.1117774941925191, 'top_20_of_pos': 0.7918394815527143, 'top_5_of_pos': 0.39081952497000266}}

## I2_IND_RS_60

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -39.82% / -4.23% / -72.06% / -0.0177
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -32.72% / -14.33% / -38.68% / -0.5237
- Validation years: 2021 compound -1.92%; 2022 compound -12.37%; 2023 compound -14.72%; 2024 compound -8.20%
- Unfilled validation: 0.007452242670212022
- Concentration: {'rebalance': {'n': 172, 'n_negative': 89, 'top_10_of_pos': 0.5966280147097369, 'top_1_of_pos': 0.12267418014240714, 'top_20_of_pos': 0.7991842784318325, 'top_5_of_pos': 0.40421994418630836}}

## I3_IND_BREADTH_20

- Research STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -25.46% / -2.47% / -68.84% / 0.0457
- Validation STRATEGY_PERIOD_RETURN / CAGR / MaxDD / Sharpe: -28.86% / -12.45% / -37.19% / -0.3827
- Validation years: 2021 compound 1.27%; 2022 compound -15.98%; 2023 compound -8.80%; 2024 compound -8.33%
- Unfilled validation: 0.0069974109579455605
- Concentration: {'rebalance': {'n': 172, 'n_negative': 85, 'top_10_of_pos': 0.5725163416505901, 'top_1_of_pos': 0.12285081698796317, 'top_20_of_pos': 0.7803014545508548, 'top_5_of_pos': 0.39926073890644603}}
