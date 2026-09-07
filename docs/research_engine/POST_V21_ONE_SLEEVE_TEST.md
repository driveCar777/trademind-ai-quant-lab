# Post-V21 One-Sleeve Test — Q4

**Date:** 2026-09-04  
**Read-only** year compounds from the same 42 RESULTS books vs V20 X1. Existing TRADES used only as already summarized in those years.  
**H24 offset grids:** **MISSING. Do not rerun.** No `*OFFSET*` files under `cn_a_share_alpha_v2/TRADES/`.

```
N_BOOKS              = 42
YEAR_CORR_VS_X1_N    = 41 (X1 excluded)
MEDIAN_CORR          = 0.54
N_CORR > 0.70        = 4
N_CORR > 0.50        = 28
H24_OFFSETS          = MISSING_DO_NOT_RERUN
```

---

## Answer

**42 experiments, one economic sleeve, different labels.**

The sleeve is: long a subset (or the whole eligible set) of A-share names for 20 sessions, cost model V1, no short, no industry residualization in the official book.

It is **not** 42 independent information engines. Crash years 2011 / 2018 / 2023 are unanimous or near-unanimous losers. 2015 is a near-unanimous winner for the CS books.

It is **not** identical to HS300. Median year-compound correlation vs X1 is only 0.54. Max is X3 (HS300 add-event) at 0.83 — a sibling of X1, not a new sleeve. 2015 and 2017 signs flip vs X1 (CS bubble vs large-cap leadership). D2 (stock-dividend announce) is the low outlier (corr −0.13): still a 20-day long-after-filing book, just a noisier event subset.

So: **one long-only A-share CS sleeve + one HS300-ish institutional subset + one event-window subset.** Three costumes. Same hold, same cost, same long-only. Labels change. The capital object does not.

H24 20-day offset grids that would quantify “official grid vs overlap” the way V14.1 did for H11 are **not on disk**. Q4 will not resimulate them.

---

## Decision

No second sleeve exists in the frozen archive. Q5 is strategy thinking on that fact, not a new family.
