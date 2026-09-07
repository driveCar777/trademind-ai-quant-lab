# Research Rules Amendment V1 — which locks protect the money, which ones only protect old habits

**Date:** 2026-09-04  
**Trigger:** owner asked whether the rule set is what is stopping a second Alpha, and authorised changing rules.

## Honest diagnosis first

The rules are not why NEW_INDEPENDENT is 0. In 24 versions the pattern is the same: signals that carry a little information in the research window (V13 low-vol, V23 margin inflow t=4.85) do not survive the 2021-08 → 2024-02 validation slice, and most families carry none at all. No rule stopped a real edge from showing; the gates only stopped us from *pretending* one had.

But three rules are doing damage of a different kind — they make the test **harder than the market itself**, and one of them has been quietly applied far beyond its original intent.

## Keep — these are the ones that stand between you and losing money

| Rule | Why it stays |
|---|---|
| Pre-register before running; no retune / sign flip after seeing results | This is the whole difference between research and curve-fitting. Every "competition winner" who lacked this blew up later. |
| Cost model fixed (`A_SHARE_STRATEGY_COST_MODEL_V1`) | Costs are the one thing we know for certain. Lowering them is lying to yourself. |
| CAGR only from a non-overlapping capital account | Overlapping statistics overstated V13 by 10×. Learned the hard way in V14.1. |
| FDR over the whole family | 3 tries at 5% each ≈ 14% chance of a fake hit. |
| No Paper / Live without an independent positive validated book | Trading H11 today would have lost 66% at the worst point. |
| No historical evidence rewritten | Otherwise every past "NO_CANDIDATE" is negotiable and nothing is ever known. |

## Change — three rules I am amending now, because they were mis-scoped

### A1. The "one construction" lock → pre-registered construction menu

**Old, as applied:** every A-share family had to be judged as a *long-only, top-quintile, 20-session, equal-weight, absolute-return* book. The original rule was narrower: "do not change hold/cost of a Candidate *after* seeing results to manufacture 10%". It was correct for H11/H12. It was never meant to forbid other constructions for *new* families, yet since V15 no family has been allowed a different book.

**Why it hurts:** the validation slice 2021-08 → 2024-02 is a −30% bear market. A long-only absolute-return gate in that slice fails *every* long-only book regardless of stock-selection skill. V23 M1 beat equal-weight in research at t=4.85 and still "failed" mainly because the market fell. We have been testing "did you beat a bear market" not "do you have information".

**New rule:** a new family's contract may pre-register **one** of these capital books (chosen before the run, never after):
- LO20: the existing long-only 20-session book (unchanged, default for comparability), or
- **HN20: hedged-neutral** — same long quintile, hedged 1:1 with an HS300 (IF) or CSI500 (IC) index-futures short, futures cost and basis charged; capital gate then applies to the hedged book, and
- for both: the *research* gate is still excess-vs-EW with FDR; the *capital* gate is on the pre-registered book only.

The A-share short leg is real: IF/IC futures and 300ETF/500ETF 融券 exist for retail with a futures account. This is not a theoretical hedge.

This does **not** reopen V13–V24 for re-scoring. Re-running M1 hedged today would be selecting on the validation slice. It is recorded once as a *diagnostic* (like the zero-cost counterfactual), labelled as such, and never promoted from it.

### A2. One fixed research/validation split → rolling multi-window validation

**Old:** research 2010–2021-08, validation 2021-08 → 2024-02, one shot.

**Why it hurts:** with one validation slice, the verdict on 14 years of information is decided by 2.5 years of one regime. That is not stricter; it is noisier.

**New rule:** in addition to the fixed split (kept for comparability), every new family reports **five rolling validation windows** (walk-forward: research on all data before each 2-year block starting 2014, 2016, 2018, 2020, 2022-08). Level-1 requires the fixed-split gates **and** positive excess-vs-EW in ≥ 4 of 5 rolling windows. This is *harder* to pass by luck and *fairer* to a real edge that had one bad regime. The denied window is still not touched.

### A3. ML ban → one pre-registered combination model per data layer

**Old:** `ML = False` since V18, after V10 found nothing on the 4-name MT5 book.

**Why it hurts:** V10 tested model representation on **four price series**. It said nothing about combining *different information classes* across 3,000 names. We now hold, on disk and PIT-aligned: price/volume, annual ratios, industry, index membership, dividends, margin positioning, holder concentration. No contract has ever been allowed to combine them.

**New rule:** one pre-registered gradient-boosted (or ridge) cross-sectional model per information layer, purged/embargoed walk-forward CV only, features and target fixed in the contract, **no feature search after the first run**, judged by the same capital gates as any hypothesis and counted as m=1 in FDR. Not "throw everything at XGBoost until it works" — one shot, then frozen.

### A4. Cluster / independence test → on excess-vs-EW series, not raw forward returns (added after V25 exposed the flaw)

**Old:** SAME_CLUSTER if corr > 0.9 between raw MEAN_FORWARD_RETURN (or raw capital) series of the new hypothesis and H11/H12.

**Why it hurts:** any two long quintiles share the market. In V25, H11 vs EW correlated 0.955 and the model vs EW 0.973, so model vs H11 came out 0.94 and was tagged SAME_CLUSTER while the two selections were unrelated (excess-series corr 0.06). The test could never declare a long book independent.

**New rule:** independence is judged on the **excess-vs-eligible-EW** series (predictive) and on hedged/basket-relative period returns (capital). Threshold stays 0.9. V25's formal tag is not re-scored; the corrected test is applied from V25.1 onward, pre-registered in `V25_1_REPRODUCTION_CONTRACT.md`.

## Not changing without you — one real decision

**The denied window 2024-03-01 → 2026-08-28.** It is the last 2.5 years nobody has looked at. It exists exactly for a situation like V23 M1: research-real, validation-zero, and we want to know whether the validation slice was the anomaly. Opening it answers that question once. It cannot be re-locked. If it gets used to *choose* among families, it is gone as evidence. My recommendation: do not open it for M1 alone. Open it only when a family passes A1+A2 gates on the first 14 years and needs one final, single, pre-declared read.

## On "US trading-competition techniques"

Three things are true at once:

1. Championship records (World Cup Trading Championships etc.) are 100–1000%+ in one year on small accounts using futures/options with extreme leverage and concentration. They are selected from thousands of entrants; the median entrant loses. Their edge is not published and their results are not repeatable at scale. Nothing in them is a data source we can test.
2. The *methodology* winners of the quant world actually use — Numerai, WorldQuant BRAIN, Kaggle-style — is: many weak orthogonal features, cross-sectional models, purged CV, ensembles, strict live-vs-backtest tracking. That is exactly what A3 opens and what our engine can already host. It is not magic; it is a way to combine several weak signals we already own (V23 M1, low-vol, dispersion) into one book that might beat costs where each alone did not.
3. The part of "competition style" that is genuinely useful for a one-person shop is **rapid iteration under a fixed cost model with a locked out-of-sample** — which we already do, and which is why we have not lost money.

## What happens next under the amended rules

V25 = first A3 model on the A-share layer: features = the PIT scores already computed (H11 vol, M1 margin inflow, M2 balance ratio, HC1 concentration, V16 ROE/YoY, index membership flag), target = 20-session forward return rank, walk-forward CV per A2, capital book per A1 (both LO20 and HN20 pre-registered, HN20 primary), FDR m=1. Contract before run, as always.
