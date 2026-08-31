# Candidate cost audit V13.1

**Date:** 2026-08-31  
**Cost model:** `A_SHARE_TRANSACTION_COST_MODEL_V1` (locked).  
**Zero-cost is diagnostic only. Not an official result.**  
**Do not search for a cheaper cost.**

## Validation overlapping split (1.0x official)

Round-trip ≈ 34.0 bp: commission 5.0 bp + transfer 0.2 bp + stamp ~8.8 bp + slippage 20.0 bp.

| | H11 | H12 |
|--|-----|-----|
| Mean gross | +0.003860 | +0.004470 |
| Mean cost | 0.003403 | 0.003403 |
| Mean net | +0.000457 | +0.001067 |
| Cost drag / gross | 88% | 76% |

The official book **survives cost**, but most of the gross is eaten. Slippage is the largest line. H11 net is a thin leftover.

## Fixed stress (validation overlapping mean_net)

| Stress | H11 | H12 |
|--------|-----|-----|
| 1.0x cost + 1.0x slip | +0.000457 | +0.001067 |
| 1.5x cost | **−0.000245** | +0.000366 |
| 2.0x cost | −0.000947 | **−0.000336** |
| 1.5x slip | **−0.000543** | +0.000067 |
| 2.0x slip | −0.001543 | −0.000933 |
| Zero cost (not official) | +0.003860 | +0.004470 |

H11 flips at 1.5x cost and 1.5x slip. H12 still positive at 1.5x, flips at 2.0x.  
This is **fragility**, not a new cost parameter. Do not pick 1.0x because it is the only passing stress.

## Turnover (contract)

`NON_OVERLAPPING_EVERY_HOLD`, hold = 20.  
Daily two-way equivalent = 2/20 = **0.10**. Weekly 0.50. Monthly 2.10.  
All audited nonoverlap trades have `hold_days=20`. No execution-horizon anomaly.

## Execution / CA / suspension / limit

- Signal date → entry open(t+1) → exit open(t+1+20). Sample: `TRADE_AUDIT.csv` (120 random fills per name, seed 20260831).
- Suspended fills: **0**. Unlisted fills: **0**. Non-exec-mask fills: **0**.
- Contract lists `LIMIT_LOCK`. Implementation uses `abs(open/preclose-1) < limit-0.002`. The 0.002 buffer is an **implementation clarification**, not a new contract parameter.
- Close vs preclose >12% on filled signal days: **0 / ~100k** names checked. Ranking still uses **raw** close. Full qfq panel was not frozen. Corporate-action leakage remains a **LIMITATION**.
- 2026 IPO mutation does not change 2020-06-01 membership (3853 listed). Delist mutation stable. PIT clean for this check.

## Beta / size / industry

- H11 validation beta vs EW market overlapping net ≈ **0.66**. Down-market mean net still **negative** (−2.9%). Low-vol looks like a milder risk profile, not a down-market money machine.
- No reliable market-cap field. Amount/price only. **Size LIMITATION.**
- Industry PIT **BLOCKED**. Low-vol may be sector-confounded. **Not** an industry-neutral Candidate. Do not load today's industry file.
