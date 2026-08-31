# Candidate robustness V13.1

**Date:** 2026-08-31  
**Do not use year or regime to pick a strategy.**  
**Final OOS was not read for gates.**

## Year-by-year (overlapping H-day mean_net, research+validation only)

CAGR-equivalent is `(1+mean_net)^(242/20)-1`. It is a diagnostic, not a selector.  
Do **not** use the overlapping-compounded MaxDD field in the machine year table as portfolio drawdown. That compounds overlapping 20-day returns every day and is not a book.

| Year | H11 mean_net | H11 CAGR-eq | H12 mean_net | H12 CAGR-eq | n |
|------|--------------|-------------|--------------|-------------|---|
| 2010 | −0.0062 | −7.3% | −0.0061 | −7.2% | 242 |
| 2011 | −0.0309 | −31.6% | −0.0286 | −29.6% | 244 |
| 2012 | −0.0028 | −3.3% | −0.0037 | −4.4% | 243 |
| 2013 | +0.0022 | +2.7% | +0.0033 | +4.1% | 238 |
| 2014 | +0.0393 | +59.4% | +0.0411 | +62.8% | 245 |
| 2015 | +0.0228 | +31.3% | +0.0219 | +30.0% | 244 |
| 2016 | +0.0039 | +4.9% | +0.0043 | +5.3% | 244 |
| 2017 | −0.0093 | −10.7% | −0.0085 | −9.9% | 244 |
| 2018 | −0.0294 | −30.3% | −0.0300 | −30.8% | 243 |
| 2019 | +0.0092 | +11.7% | +0.0104 | +13.4% | 244 |
| 2020 | +0.0060 | +7.5% | +0.0043 | +5.3% | 243 |
| 2021 | +0.0169 | +22.5% | +0.0156 | +20.6% | 243 |
| 2022 | −0.0015 | −1.9% | −0.0014 | −1.7% | 242 |
| 2023 | −0.0014 | −1.7% | −0.00005 | −0.1% | 242 |
| 2024* | −0.0172 | n/a | −0.0188 | n/a | 37 |

\*2024 is only validation through 2024-02-29. Not a full year. Denied window starts 2024-03-01 and was not used.

The overlapping mean is **not** a single-year story. 2014–2015 and 2021 are strong; 2011 and 2018 are large losses. 2022–2023 (inside validation) are flat to slightly negative.

## Pre-locked regime (validation overlapping)

Definition locked before this run: EW-market 60-day product sign, sideways if `|r60|<5%` and not stress, stress if EW equity DD ≤ −20%.

| Regime | H11 n | H11 mean_net | H12 n | H12 mean_net |
|--------|-------|--------------|-------|--------------|
| BEAR_STRESS | 359 | −0.00025 | 355 | +0.00016 |
| BULL_STRESS | 198 | −0.00493 | 210 | −0.00371 |
| BULL_NORMAL | 42 | +0.02773 | 40 | +0.03384 |
| SIDEWAYS_NORMAL | 8 | +0.02233 | 2 | +0.00839 |

Most validation days fall in **stress** labels. That is the locked definition, not a post-hoc cut. Do not redefine regime after seeing this.

## Nonoverlap 20-day book (diagnostic, not a new gate)

Official Level 1 uses overlapping `mean_net_h`. The contract rebalance is still `NON_OVERLAPPING_EVERY_HOLD`.

| Book | H11 n | H11 mean_net | H11 equity | H11 MaxDD | H12 mean_net | H12 equity | H12 MaxDD |
|------|-------|--------------|------------|-----------|--------------|------------|-----------|
| Research nonoverlap | 142 | +0.00129 | 0.791 | −69.1% | +0.00136 | 0.799 | −69.4% |
| Validation nonoverlap | 30 | **−0.00114** | 0.942 | −15.7% | **−0.00007** | 0.973 | −14.6% |

The tradable 20-day grid is weaker than the overlapping statistic. H11 validation nonoverlap is negative. H12 validation nonoverlap is about zero. This is a **limitation**, not a parameter change, and not a reason to retune lookback/hold.

## Bootstrap / permutation (reporting only)

Contract seed `20260831`. Not added as a new Candidate criterion.

| | H11 iid p(mean>0) | H11 block p(mean>0) | H12 perm p(≥obs) |
|--|-------------------|---------------------|------------------|
| Validation overlapping net | 0.581 | 0.429 | 0.0099 |

Permutation: 0/100 random quintiles beat the observed mean net, so the **ranking** is not a random-name effect.  
Block bootstrap: H11 validation mean is **not** reliably positive. The edge is weak.

H11 vs H12 validation net correlation = **0.993**. Diagnostic only. They were **not** combined.
