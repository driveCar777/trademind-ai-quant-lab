# Post-V21 Strategy Options — Q5

**Date:** 2026-09-04  
Locks unchanged. This is not a Candidate declaration and not a retune memo.

---

## 1. Why H11/H12 can be Candidates and still not a making-money Strategy

V14.1 numbers, official H11 book:

- Candidate object: overlapping 20-day filled open-to-open minus one round-trip, then `(1+mean)^(242/20)-1`. That mean stayed slightly positive.
- Strategy object: one non-overlapping 20-day capital account. Full path **−15.61%**, CAGR **−1.13%**, MaxDD **−66.46%** (2015-06-12 → 2018-10-18, no recovery).
- Official TRADES: arith mean **+0.115%**, geo mean **−0.105%**, compound **−16.58%**. Win rate ~52%. Left tail kills compounding (AM-GM).
- Validation fresh MTM +0.12% CAGR is not 10% and is not the official continuing book (−0.056% on the same equity path).
- H11/H12 capital correlation 0.996. One cluster.

They are Candidates because the *research statistic* passed gates. They are not a profitable Strategy because the *account* lost money. LEVEL=1 / STRATEGY=2 describes process completeness, not a funded edge.

---

## 2. Illegal “do strategy” while NEW_INDEPENDENT=0

These do not become legal because the goal is CAGR ≥ 10%:

- Blend H11+H12 and call it two Alphas / a portfolio
- Retune lookback / hold / quantile / sign toward 10%
- Paper or Live or `order_send` on a negative official book
- Leverage the −66% DD path
- Change cost model or Candidate gates
- Treat overlapping MEAN_FORWARD as CAGR
- Open Final OOS
- Promote H24/H25/H26 because overlap beat EW (Q1). Those families are frozen; their official books still lost.

---

## 3. Long-short / industry-neutral diagnostic (read-only)

Q1 relative EW is **NEGATIVE** (29/42). The construction fantasy that “the book hid a long-short edge vs the universe” is **closed for the main mass**.

The 13 IDs with val `excess_vs_b0` > 0 are already in RESULTS. That *is* the long-vs-EW diagnostic. They still have negative validation capital. Industry-neutral official books were not stored as a second TRADES file; V16 I1–I3 and V19 IM* *are* industry-tagged long-only books and they are in the 29 that lost to EW.

**This is a diagnostic, not a Candidate.** No hold change. No gate change. No new LS implementation. No declaration.

---

## 4. What evidence a second independent Strategy needs

All of these, not a subset:

1. A **new information object** (Q2 found NONE on disk).
2. Pre-registered contract, dual books, FDR.
3. Validation MEAN_FORWARD > 0 **and** validation **capital** > 0 (non-overlap).
4. Capital correlation vs H11/H12 ≤ 0.9 (not SAME_CLUSTER).
5. Reproduction contract written. Still no Final OOS until that gate is separately unlocked.

Missing any one = NEW_INDEPENDENT stays 0. Beating EW on an overlapping mean is not enough (the 13 already did that).

---

## 5. Only legal strategy posture with one weak cluster

**KEEP_LOW_PRIORITY.**

Do not optimize. Do not Long Validate. Do not portfolio. Do not paper. Keep H11/H12 as the documented weak cluster so history is not rewritten. The legal next *search* action is a new object or a human purchase. Both are closed this session (NONE; DO_NOT_BUY).

---

## After this file

Q6 = **S1**. Confidence after Q1–Q5 = **0.91**.
