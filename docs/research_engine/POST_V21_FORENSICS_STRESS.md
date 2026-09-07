# Post-V21 Forensics Stress — Q1 vs EW / HS300

**Date:** 2026-09-04  
**Read-only.** `excess_vs_b0` is already in RESULTS: selected overlapping mean minus eligible-universe EW, same hold. No resim. No BaoStock.  
**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/Q1_Q2.json`

```
Q1_RELATIVE_EW     = NEGATIVE
VAL_EXCESS_POS     = 13 / 42
VAL_EXCESS_NEG     = 29 / 42
MEAN_VAL_EXCESS    = −0.535%
X1_VAL_EXCESS      = −0.531%
X1_VAL_CAPITAL     = −32.50%
CONFIDENCE_AFTER_Q1_Q2 = 0.86  (raised to 0.91 after Q4+Q5)
NEXT               = Q2 done NONE → Q4
```

B0 = equal-weight all eligible executable names, same H-day open-to-open. Not a purchased index.

---

## Answer

The 42 validation losses are **not** “stock-picking lost while the market was fine.”

They are also **not** “everyone just cloned HS300.”

They are: **a long-only eligible A-share sleeve that lost money in the same crash years, and on the overlapping book most labels lost to EW as well.**

- 29/42 validation `excess_vs_b0` < 0. Mean −0.535%. Selection was typically *worse* than doing nothing but EW the eligible universe.
- 13/42 beat EW on the overlapping statistic and **still** have negative validation capital. Those IDs are the frozen V15 residual/dispersion set, four V18 age/calendar sets, and IM5/IM6. Not a new object. Not a Candidate.
- X1 HS300 membership itself: val MEAN_FORWARD −1.26%, excess vs B0 **−0.53%**, val capital **−32.50%**. The large-cap set is not a safe harbor.

Verdict A is harder, not softer. Relative EW is not a hidden second Alpha.

---

## Crash-year signs vs X1 (HS300 set book)

X1 full-path year compounds: 2011 **−32.75%**, 2015 **−6.41%**, 2018 **−32.88%**, 2023 **−19.93%**.

| Year | 42 books compound < 0 | Same sign as X1 | Note |
|---|---|---|---|
| 2011 | 42/42 | 42/42 | Shared crash |
| 2015 | 4/42 | 4/42 | CS sleeve *up*; HS300 set *down* |
| 2017 | 41/42 | 1/42 | CS sleeve *down*; HS300 set *+3.3%* |
| 2018 | 42/42 | 42/42 | Shared crash |
| 2023 | 41/42 | 41/42 | Shared crash |

2015/2017 prove the 42 books are **not** the HS300 portfolio. They are the scored/eligible long-only CS sleeve. In crash years that sleeve and HS300 print the same sign. In the 2015 bubble and 2017 leadership year they diverge.

---

## Decision (no question)

Q1 = NEGATIVE → do not open a construction-only hunt for a relative-EW Candidate.  
Q2 inventory is mandatory and already run: **NONE**.  
Next = Q4 one-sleeve test (already computed year-corr vs X1 in the same JSON), then Q5.
