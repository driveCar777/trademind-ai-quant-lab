# Candidate concentration V13.1

**Date:** 2026-08-31  
**Do not drop names after seeing stock PnL.**

Share-of-net ratios above 100% happen because **net is a small residual** of large winner and loser sums. Share-of-positive-PnL is the readable number.

## Stock contribution (nonoverlap names, research through validation)

| | H11 | H12 |
|--|-----|-----|
| Names that appeared | 4202 | 3861 |
| Names with + net / − net | 2138 / 2064 | 2040 / 1821 |
| Sum net (unit book, stacked holds) | +115.6 | +145.1 |
| Sum of winners / losers | +783.7 / −668.1 | +755.8 / −610.6 |
| Top 1% of names / **positive** PnL | 8.5% | 7.9% |
| Top 5% / positive PnL | 30.1% | 28.8% |
| Top 10% / positive PnL | 49.2% | 47.1% |
| Top 20% / positive PnL | 74.4% | 72.5% |
| Top 1% of names / **\|PnL\|** | 4.8% | 4.7% |

**H11/H12 do not depend on a handful of stocks.** Thousands of names appear. The top 1% of names is about 8% of winner PnL, not the whole book. There are almost as many negative contributors as positive ones. Do not delete losers.

## Time contribution (validation overlapping daily nets)

| | H11 | H12 |
|--|-----|-----|
| Days | 607 | 607 |
| Negative days | 314 | 301 |
| Top 5% days / positive PnL | 24.2% | 23.7% |
| Top 10% days / positive PnL | 42.1% | 41.0% |
| Top 20% days / positive PnL | 69.6% | 68.4% |

**A few days do not invent the entire edge**, but the overlapping net is thin: more than half of validation days are negative, so share-of-net for the best days is huge and misleading. Best 10% of days are about 40% of winner-day PnL — typical, not a one-week artifact.

## Breadth (validation overlapping)

| | H11 | H12 |
|--|-----|-----|
| Mean eligible | 4582 | 4490 |
| Min eligible | 4092 | 3968 |
| Mean selected / filled | 916 / 913 | 898 / 894 |
| Min selected / filled | 818 / 811 | 794 / 786 |
| Days with <20 selected | 0 | 0 |
| Days with <10 selected | 0 | 0 |

**Not a 5–10 name book.** Equal-weight effective N ≈ 900. Mean HHI ≈ 0.0011.

## Liquidity (unit-book diagnostic only)

Median execution-day `amount` ≈ 3.5e7 (H11) / 3.8e7 (H12).  
Unit weight / ADV ≈ 4e-11. That is a **one-unit book** ratio, not a capital mandate. Do not announce AUM capacity.

## H11 vs H12

Validation overlapping net correlation **0.993**. They are almost the same low-vol book. Recorded as two independent Candidates. **H12 1.30% is not a score.** No champion. No combination.
