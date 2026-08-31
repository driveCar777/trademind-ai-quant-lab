# Strategy economics V14

**Date:** 2026-08-31  
Diagnostic capital = 1,000,000. Results are ratios. Not a recommendation to invest that amount.

## Capital path (research through validation)

| | Strategy-H11 | Strategy-H12 |
|--|--------------|--------------|
| Start | 1,000,000 | 1,000,000 |
| End | 834,203 | 883,506 |
| Total return | **−15.6%** | **−10.5%** |
| CAGR | −1.13% | −0.74% |
| Ann. vol | 20.5% | 20.5% |
| MaxDD | **−66.5%** | **−66.2%** |
| Sharpe (rf=0) | 0.05 | 0.07 |
| Sortino | 0.06 | 0.08 |
| Calmar | −0.02 | −0.01 |
| Rebalances | 172 | 172 |
| Win rate | 53% (research book) | 51% |

The official 20-day book **lost money** from 2010 through validation. That is the strategy, not the overlapping Candidate statistic.

## Validation fresh start (1e6 at 2021-08-25)

| | H11 | H12 |
|--|-----|-----|
| MTM through 2024-02-29 | +0.31% / CAGR **+0.12%** | +1.94% / CAGR **+0.74%** |
| Realized 31-trade end (1.0x) | +2.70% | +4.60% |
| MaxDD | −24.4% | −23.7% |
| Sharpe | 0.09 | 0.13 |
| Sortino | 0.11 | 0.16 |

Still far from the **10%** long-term target. Gap ≈ **9.9 / 9.3 percentage points** on validation MTM CAGR. Do not fill the gap with leverage or new parameters.

## Research fresh start

H11 −16.2% (CAGR −1.43%), H12 −13.9% (CAGR −1.22%), MaxDD ≈ −66%.

## Benchmark

No purchased index. Proxy = equal-weight eligible names, same 20-day open-to-open (limit-lock ignored on the proxy).  
H11/H12 beta vs that proxy ≈ **0.75**. Up/down capture ≈ 0.76 / 0.76. Low-vol looks like a milder market sleeve, not a separate return engine.

## 10% target

Allowed to optimize toward 10%? **NO.**
