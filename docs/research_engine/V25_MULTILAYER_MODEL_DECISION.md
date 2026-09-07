# V25 Decision — A-share multi-layer combination model

**Date:** 2026-09-04 (evening)  
**Family:** `A_SHARE_MULTILAYER_MODEL_V25` · contract `V25_MULTILAYER_MODEL_CONTRACT.md` (hash in `CONTRACT.json`, written before the run)  
**Formal outcome (as pre-registered):** `WEAK_CANDIDATE_SAME_CLUSTER` · `STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE` · **Level-1 = 1** (first since H11/H12) · NEW_INDEPENDENT_CANDIDATE by contract test = 0  
**After V25.1 reproduction (§5, amendment A4):** `A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE` · **NEW_INDEPENDENT_CANDIDATE = 1** · STOP A  
**Machine files:** `data/market/research_engine/cn_a_share_ml_v25/{CONTRACT,MODEL,RESULTS,FDR,FAILURES,CANDIDATES,DECISION,DIAGNOSTICS_POST,REPRODUCTION}.json`, `EQUITY/`, `TRADES/`, `SCORES_*.npy`  
**Cost:** $0. No purchase. Denied window untouched (index dailies were downloaded only to 2024-02-29; hedged book drops any exit past it).

## 1. What was run

Fourteen PIT features already on disk (6 price, 3 margin, 2 holders, 2 annual financials, 1 index membership), cross-sectionally ranked, fed to one LightGBM regressor predicting the rank of the 20-session forward open→open return. Expanding walk-forward, first OOS prediction 2012-01-04, refit every 120 sessions, embargo 21 sessions, **frozen at 2021-08-24**; validation 2021-08-25 → 2024-02-29 scored by the frozen model. No second configuration was tried. Baseline ML0 = the same features rank-averaged with no fitting.

## 2. Results (all out-of-sample, stock cost model unchanged)

| | ML1 LightGBM | ML0 rank-average |
|---|---|---|
| Research excess vs EW (per 20d, overlapping) | **+1.24%**, t = 28.3, IC 0.120 | +0.37%, t = 8.3, IC 0.087 |
| Validation excess vs EW | **+1.47%**, t = 17.1, IC 0.167 | +0.73%, t = 7.6, IC 0.111 |
| FDR (m=2, q=0.05) | discovery, adj-p ≈ 1e-65 | discovery, adj-p ≈ 1e-14 |
| Rolling blocks positive (A2) | **5 / 5** (2014-15 +2.35%, 2016-17 +1.29%, 2018-19 +0.86%, 2020-21 +0.40%, valid +1.47%) | 5 / 5 (weaker) |
| LO20 capital research 2010→2021-08 | **+276%**, CAGR 14.5%, MaxDD −46.8% (2016-11 → 2018-11), Sharpe 0.60 | +58%, CAGR 4.8%, MaxDD −56% |
| LO20 capital validation 2021-08→2024-02 (HS300 ≈ −30%) | **+30.9%**, CAGR 11.1%, MaxDD −20.9% | +3.7% |
| HN20 (hedged vs HS300) research | +27.3%, CAGR 2.5%, MaxDD −54% | −42.7% |
| HN20 validation | **+33.8%**, CAGR 12.5%, MaxDD −20% | +18.5% |
| Level-1 (fixed gates + rolling) | **PASS** | FAIL (research HN20 capital < 0) |
| Cluster test as pre-registered (raw MF corr vs H11) | 0.94 → **SAME_CLUSTER** | 0.99 |
| Full 2010→2024-02 LO20 | +381%, CAGR 13.7%, MaxDD −46.8% | |
| Cost stress LO20 validation 1× / 1.5× / 2× | +30.9% / +24.2% / +17.8% (research +276% / +208% / +153%) | |

Feature gain share at the last refit: NEG_LOG_AMT_20 (size/liquidity) 28%, NEG_TURN_20 17%, REV_20 14%, MOM_250_20 6%, ROE 5%, holders 5%+3%, margin 3%+3%+1%, vol 4%+4%, HS300_MEMBER 0.3%.

## 3. What the diagnostics say (read-only; never gates)

**3a. The pre-registered cluster test measured the market, not the signal.** Raw MEAN_FORWARD_RETURN of *any* long quintile co-moves with the market: H11 vs EW 0.955, ML1 vs EW 0.973, hence ML1 vs H11 0.94. On **excess-vs-EW series** the correlation ML1 vs H11 is **0.06** (n = 2950). Stock selection is not the low-vol sleeve. The contract test was mis-specified for long books; the formal tag stands, and the correction is made for the future in `RESEARCH_RULES_AMENDMENT_V1` (A4 below), not by re-scoring V25.

**3b. The HS300 hedge does not neutralise this book.** HN20 period returns regress on (eligible-EW − HS300) with β = 0.92, R² = 0.93. The model buys the small-amount / low-turnover / short-term-loser quintile (median amount-rank of selected names 0.86 where 1 = smallest; ~627 names per period). Hedging with the large-cap index leaves the whole small-vs-large spread in the book: that is why HN20 lost 34% in 2017 and 19% in 2020 (large-cap years) and 22% in Jan–Feb 2024 (small-cap crash), while LO20 did not.

**3c. The stock-selection alpha net of the basket is real and steady.** LO20 minus the eligible equal-weight basket over the same 147 non-overlapping windows: **+0.89% per 20 sessions, t = 5.1, 71% of periods positive**, positive in 11 of 13 years (2017 −2.7%, 2020 −7.2% the exceptions). This is the part that is neither market beta nor size beta relative to the average eligible stock — what an equal-weight-benchmarked A-share long book is actually paid for.

**3d. Diagnostics on frozen singles (A1):** H11 on HN20: research −58%, validation +21%. M1 on HN20: −48% / −11%. The hedge did not rescue single signals; the combination is doing the work.

## 4. Reading

1. **NEW_INDEPENDENT stays formally 0 by the pre-registered test, but for the wrong reason.** By the informative test (excess-series corr 0.06) ML1 is a different sleeve from H11/H12. Reproduction (§5) treats the excess-series test as the independence criterion, pre-registered in `V25_1_REPRODUCTION_CONTRACT.md`.
2. **The book to trade is not HN20 as specified.** Against HS300 it is a size-spread carrier with a −54% drawdown. The honest constructions are (i) LO20 with explicit size exposure and −47% MaxDD, or (ii) a hedge against a small/mid-cap instrument (CSI1000 futures IM exist since 2022-07; before that no tradable hedge) — which cannot be backtested over 2010–2021 with a real instrument. A2/A1 already allow pre-registering such a book for a *new* family; for V25 it is a diagnostic, not a re-score.
3. **This is the first Level-1 in 12 versions, and it comes from combining what was already on disk.** The information that V13–V24 declared individually dead is, jointly, worth about +0.9% per 20 sessions over the average stock after costs, robust to doubled costs and a 2.5-year bear validation.
4. **Not a 10% promise.** CAGR figures above are from a ¥1M non-overlapping capital account with the locked cost model; capacity at scale, small-cap fill quality beyond the 10bp slippage approximation, and the 2017/2020/2024-01 regimes are all real risks; the denied window has never been read.

## 5. Reproduction battery (V25.1) — PASS

Contract `V25_1_REPRODUCTION_CONTRACT.md`, machine `REPRODUCTION.json`, `V25_1_DECISION.json`. Seven fixed nuisance variants, nothing selected, primary unchanged.

| variant | excess R | excess V | LO20 R / V | HN20 R / V | rolling | excess-corr vs H11 | shape |
|---|---|---|---|---|---|---|---|
| PRIMARY | +1.24% | +1.47% | +276% / +31% | +27% / +34% | 5/5 | 0.063 | ✔ |
| SEED_1 | +1.24% | +1.48% | +281% / +31% | +29% / +34% | 5/5 | 0.070 | ✔ |
| SEED_2 | +1.26% | +1.46% | +289% / +32% | +31% / +35% | 5/5 | 0.070 | ✔ |
| STRIDE_3 | +1.26% | +1.47% | +287% / +30% | +30% / +33% | 5/5 | 0.054 | ✔ |
| STRIDE_10 | +1.26% | +1.45% | +274% / +29% | +26% / +32% | 5/5 | 0.074 | ✔ |
| REFIT_60 | +1.25% | +1.35% | +287% / +22% | +30% / +27% | 5/5 | 0.022 | ✔ |
| REFIT_240 | +1.24% | +1.44% | +265% / +27% | +24% / +30% | 5/5 | 0.024 | ✔ |
| **PLACEBO** (labels shuffled within session) | −0.09% (t −5.5) | −0.07% | −18% / −20% | — | 1/5 | — | leak check: clean |

All three pre-declared criteria met (7/7 shape; min validation excess +1.35% ≥ +0.5%; max excess-corr 0.074 ≤ 0.9). The placebo shows a random selection paying round-trip costs, so the pipeline does not leak through masks, eligibility or feature alignment.

**Under amendment A4: `NEW_INDEPENDENT_CANDIDATE = 1`.** `A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE`, STOP A. The V25 formal tag is left as written.

## 6. Next unit of work (research judgment)

- **Frozen:** features, params, hold, cost, hedge parameters, FDR family. Any "improvement" to ML1 is a new contract, m counted.
- **The Strategy is the LO20 book** (long top-quintile, 20-session hold, ~600 names, equal weight, size/turnover tilt explicit, MaxDD −47% on record). HN20-vs-HS300 is a size-spread carrier with a worse drawdown and is *not* the strategy; a small/mid-cap hedge (IM, since 2022-07) is a future pre-registered construction, not a re-score.
- **Strategy spec next** (`V26_ML1_STRATEGY_SPEC.md`): capital, rebalancing calendar, fill rules, risk stops, monitoring, what would falsify it live. Portfolio still needs two positive sleeves; H11/H12 stay KEEP_LOW_PRIORITY and do not qualify.
- **Final OOS (2024-03 → 2026-08): DENIED until human unlock.** ML1 now meets the condition set in `RESEARCH_RULES_AMENDMENT_V1` for the single pre-declared read. Whether to spend the last unread 2.5 years on it is the owner's call; the read, if made, is one shot on the frozen scores with the LO20 book and is never used to change anything.
- No Paper, no order_send.
