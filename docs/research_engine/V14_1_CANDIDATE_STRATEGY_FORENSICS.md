# V14.1 Candidate vs Strategy Forensics

AUDIT ONLY. No retune. No H13. No purchase. Final OOS DENIED.

## Primary question

Why is the Candidate statistic positive while the canonical Strategy full-path capital account is negative?

## First-class answer

The Candidate number is **not a capital account**.

It is the arithmetic mean of **overlapping** 20-trading-day filled open-to-open returns, minus one locked round-trip, then annualized as `(1+mean_net_h)^(242/20)-1`. The `years` argument is unused. That formula can stay positive while every non-overlapping 20-day **compounded** book loses money.

Independent reconstruction:

- Path A Candidate = original `overlapping_series`. Matches published V13 `mean_net_h` with abs err **0**.
- Path B Candidate = fresh pick + inline fees. Agrees with Path A at abs err **0**.
- Capital Path A (return-based) and Path B (share-based) end at the same money (H11 err `4.51e-08`, H12 err `1.13e-07`).
- H11 settled end **834202.89**. H12 settled end **883505.87**. Same trade set as V14. Not read from V14 `equity.csv`.

Accounting is clean. This is **METHODOLOGY_GAP_CONFIRMED**, not a hidden implementation bug.

## Definitions

| Object | What it is | What it is not |
|---|---|---|
| Candidate statistic | Daily overlapping H-day EW mean of fills, minus one RT. CAGR = `(1+mean)^(12.1)-1` | A compounded book |
| Canonical Strategy | One long-only EW book, rebalance every 20 trading days, unfilled stays cash, compound `(1+period_return)` | An overlapping mean |

## Reconstructed Candidate

| Window | H11 mean_net | H11 CAGR_from_h | H12 mean_net | H12 CAGR_from_h |
|---|---|---|---|---|
| Research | 0.00131437 | 1.6020% | 0.00147823 | 1.8034% |
| Validation | 0.00045652 | 0.5538% | 0.00106703 | 1.2988% |
| Both | 0.00116291 | 1.4162% | 0.00140563 | 1.7141% |

Published V13 match: H11 True, H12 True. Path A vs Path B: H11 err=0.0, H12 err=0.0.

## Independent capital

| | H11 | H12 |
|---|---|---|
| Start | 1,000,000 | 1,000,000 |
| End | 834202.89 | 883505.87 |
| Full total | -16.5797% | -11.6494% |
| Recon start+net=end | True | True |
| N trades | 172 | 172 |
| Unfilled | 1.7470% | 1.8313% |

## Why they disagree (ordered)

1. **Object mismatch.** Candidate CAGR annualizes an overlapping mean. Strategy compounds one 20-day book.
2. **AM-GM / left tail.** H11 nonoverlap V13-style **mean** is still +0.087%, but the **product** is −25.5%. H12 mean +0.111%, product −22.2%. A slightly positive average 20-day return is not a profitable capital path when 2011 and 2018 exist.
3. **Overlap sampling.** 3,438 overlapping observations share crashes. The mean is smoother than any single 20-day grid.
4. **All 20 offset grids lose money** when compounded (H11 ends 0.69–0.90, H12 0.75–0.93). The official grid is not an unlucky calendar.
5. **Cost formula is not the flip.** Capital mean is *higher* than V13-style mean (H11 formula gap +2.9bp). Unfilled is cash, not a phantom book. No double charge.

Decision: **METHODOLOGY_GAP_CONFIRMED**. NEXT = `KEEP_CANDIDATE_STRATEGY_WEAK_NO_LONG_VALIDATION`.

## Locks

New data = NO. Retune = NO. Make H12 into 10% = NO. Paper = 0. Portfolio = 0. Final OOS = DENIED.
