# Strategy cost audit V14

**Date:** 2026-08-31  
Model: `A_SHARE_STRATEGY_COST_MODEL_V1`  
Parent rates: commission 2.5bp, transfer 0.1bp, slip 10bp, stamp 10bp/5bp sell-only.

UNKNOWN (not assumed zero, also not added as new parameters): min commission 5 CNY, 100-share lot, SZ transfer applicability, observed bid/ask.

`EXECUTION_APPROXIMATION`: no bid/ask. Slippage is the locked 10bp.

## Full-path attribution (H11 diagnostic 1e6)

| Line | Amount |
|------|--------|
| Sum trade net | −165,797 |
| Fees (commission+transfer+stamp) | 215,501 |
| Slippage | 287,424 |
| Stamp (inside fees) | 140,770 |
| Start + net = end | yes, error 1e-8 |

H12 recon also holds (error 1e-7).

## Validation realized stress (31 trades, fresh 1e6)

| Stress | H11 | H12 |
|--------|-----|-----|
| 1.0x | +2.70% | +4.60% |
| 1.5x cost | +0.49% | +2.35% |
| 2.0x cost | **−1.67%** | +0.14% |
| 1.5x slip | **−0.42%** | +1.42% |
| 2.0x slip | −3.45% | −1.67% |

H11 does **not** stay positive at 1.5x slip or 2x cost. H12 is thin at 2x cost. Not a search for the cheapest model.

## Unfilled (full path)

| | H11 | H12 |
|--|-----|-----|
| Unfilled rate | 1.75% | 1.83% |
| Limit-lock | 0.49% (499) | 0.51% (511) |
| Suspended | 1277 | 1308 |
| Delisted (no invented price) | 7 | 11 |
| Suspended fills | 0 | 0 |

Turnover: daily 0.10, weekly 0.50, monthly 2.10, annual 24.2 (two-way if the book is replaced every 20 days). Average holding = 20.
