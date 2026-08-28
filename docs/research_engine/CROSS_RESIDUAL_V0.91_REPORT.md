# Cross Residual V0.91 Report

Executed 2026-08-27 after V0.9 `NO_CANDIDATE`. Hash unchanged:

`0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57`

Not V0.8 dollar-proxy. Not V0.9 Δstate. Final OOS not read.

## Decision

- Program: **NO_CANDIDATE**
- FDR discoveries: **0**
- Align n = 1998 GOLD∩OIL D1 dates
- Residual AR(1) Δstat beta ≈ -0.030 (weak pull to the SMA60; not a trade)

## Hypotheses

| id | kind | RESEARCH n | delta | p | label |
| --- | --- | ---: | ---: | ---: | --- |
| HYP-XR-0001 | RICH fade | 437 | +0.0030 | 0.072 | FALSIFIED (costed TR < 0 both windows) |
| HYP-XR-0002 | CHEAP fade | 442 | -0.0009 | 0.556 | no edge / sign fail |
| HYP-XR-0003 | joint risk-off | 218 | +0.0006 | 0.790 | no edge |

0001’s iid bootstrap on *delta* is not a CANDIDATE. The costed two-leg book loses money. Do not flip signs.

## Not a strategy

Strategy layer remains blocked. Do not retune SMA60 or 33/67.
