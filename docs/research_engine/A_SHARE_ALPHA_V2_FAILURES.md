# A-share Alpha V2 Failures

n = 9 / 9. Reopen = new contract only. Do not flip sign. Do not retune lookback / hold / quantile.

## H21_RESID_REV_20_H20

- Family: CROSS_SECTIONAL_RESIDUAL
- Mechanism: Idiosyncratic overreaction after removing the day's EW market. Long lowest residual sum.
- Why failed: validation_mean_forward_net, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H22_RESID_REV_60_H20

- Family: CROSS_SECTIONAL_RESIDUAL
- Mechanism: Same residual reversal, 60-day residual sum.
- Why failed: validation_mean_forward_net, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H23_RESID_REV_20_H5

- Family: CROSS_SECTIONAL_RESIDUAL
- Mechanism: Same residual reversal, 5-day hold. Second registered hold, not a search.
- Why failed: research_mean_forward_net, validation_mean_forward_net, fdr, research_capital, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H24_DISP_HIGH_RESID_20_H20

- Family: MARKET_DISPERSION_STATE
- Mechanism: Trade residual-reversal 20 only when CS residual std >= trailing 60d median. Primary state = dispersion level.
- Why failed: validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H25_DISP_UP_RESID_20_H20

- Family: MARKET_DISPERSION_STATE
- Mechanism: Trade residual-reversal 20 only when residual std is higher than 20 days ago. Dispersion rising.
- Why failed: research_capital, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H26_DISP_HIGH_LOW_BREADTH_20_H20

- Family: MARKET_DISPERSION_STATE
- Mechanism: Primary HIGH dispersion AND auxiliary LOW breadth (pct-up <= 60d median), then residual-reversal 20.
- Why failed: validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H27_CAPITULATION_20_H20

- Family: PRICE_ACTIVITY_DISAGREEMENT
- Mechanism: Price down + activity up. Score = CS rank(-ret_sum_20) + CS rank(amount_sum_20). Long top quintile.
- Why failed: validation_mean_forward_net, validation_excess, research_rank_ic, validation_rank_ic, fdr, research_capital, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H28_CAPITULATION_60_H20

- Family: PRICE_ACTIVITY_DISAGREEMENT
- Mechanism: Same capitulation disagreement, 60-day window.
- Why failed: validation_mean_forward_net, validation_excess, validation_rank_ic, fdr, research_capital, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.

## H29_PX_AMT_CORR_20_H20

- Family: PRICE_ACTIVITY_DISAGREEMENT
- Mechanism: Long names with the most negative 20-day corr(daily ret, dlog amount). Disagreement, not level.
- Why failed: validation_mean_forward_net, validation_capital
- Reopen: New contract only. Do not flip sign. Do not retune lookback/hold/quantile.
