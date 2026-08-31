# Strategy reconciliation V14

**Date:** 2026-08-31  

## Identity

`start + sum(trade net) = end`

| | H11 | H12 |
|--|-----|-----|
| Start | 1,000,000 | 1,000,000 |
| Sum net | −165,797.11 | −116,494.13 |
| End | 834,202.89 | 883,505.87 |
| Abs error | 1.5e-8 | 1.1e-7 |
| OK | yes | yes |

Local run 1 vs run 2: same terminal equity (`determinism=true`). Negative tests: wrong execution timing changes equity; suspended fills = 0. Future 2026 IPO does not change 2020-06-01 membership.

## Daily / trade / cash

Daily equity is close-to-close MTM between open entry and open exit. Official period PnL is open-to-open minus locked costs. Cash holds unfilled weights. Denied window is not used for new signals. A hold may *exit* after 2024-02-29; that is mechanical, not Final OOS research.

## Failure modes (traceable)

| Class | Result |
|-------|--------|
| DATA | Frozen pack hash matches |
| EXECUTION | Unfilled reasons logged; 0 suspended fills |
| COST | Model complete; UNKNOWN items listed |
| LIQUIDITY | Diagnostic only |
| PIT | 2020 membership stable under 2026 IPO mutation |
| CORPORATE_ACTION | Raw-only LIMITATION |

## Paper gap (not this mission)

Real-time raw price, PIT universe refresh, live suspension/limit, broker orders, lot size / min commission. `EXTERNAL_LIVE_DATA_REQUIRED` for this historical book = **NO**.
