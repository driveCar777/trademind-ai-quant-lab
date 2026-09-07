# Post-V21 Capital Construction Forensics

**Date:** 2026-09-04  
**Read-only.** No backtest rerun. No BaoStock. No parameter change.  
**Machine:** `data/market/research_engine/POST_V21_FORENSICS.json`  
**Script:** `research_engine/post_v21_forensics.py`

```
VERDICT          = A
CONFIDENCE       = 0.72
SIDECAR          = B on 4 overlap-positive hyps + H11 official book
NEW_INFO_CLASS   = NONE
NEXT_UNIT        = NO_LEGAL_FREE_OBJECT_LEFT_DO_NOT_BUY
NEW_INDEPENDENT  = 0
```

A means: for the families that were supposed to produce a *second* Alpha, validation already had no predictive edge. Construction is not the reason those 38 books lost money.

B sidecar means: the official 20-day long-only book can still destroy a *positive overlapping mean* (V14.1, H24/H25/H26, A5). That is a real construction crack. It is **not** a license to retune hold or cost. Under current gates it also does **not** register a second Candidate.

---

## Question

Why did V13–V21 never produce a second independent post-cost capital account?

Two candidate bottlenecks:

1. Information: the new objects had no val edge.
2. Construction: one shared 20-day long-only CS book kills anything that is only weakly positive on the overlapping statistic.

---

## What was read

| Pack | File | Engine |
|---|---|---|
| V13 H01–H12 | `cn_a_share_alpha_v1/RESULTS.json` | overlap metrics only |
| V14 H11 official | `cn_a_share_strategy_v14/H11/SUMMARY.json` + `TRADES.csv` | non-overlap book |
| V15 H21–H29 | `cn_a_share_alpha_v2/RESULTS.json` + 3 TRADES CSVs | dual book |
| V16 F1–F6, I1–I3 | `FINANCIAL_RESULTS.json` / `INDUSTRY_RESULTS.json` | dual book |
| V17–V21 | each `RESULTS.json` | dual book |

42 dual-book hypotheses (V15–V21). V13 overlap rows kept as context, not mixed into the 42-count.

---

## Fact 1 — validation capital is uniformly negative

| | n |
|---|---|
| Dual-book hyps | 42 |
| Val capital > 0 | **0** |
| Val capital < 0 | **42** |
| Val MEAN_FORWARD > 0 | 4 |
| Val MEAN_FORWARD < 0 | 38 |

0/42 positive validation capital. That is not “a few near-misses.”

The 4 positive val MEAN_FORWARD IDs (B-pattern: overlap stat > 0, official book < 0):

| ID | Val MEAN_FORWARD | Val capital | Val CAGR |
|---|---|---|---|
| H24_DISP_HIGH_RESID_20_H20 | +1.13% | −15.05% | −7.05% |
| H25_DISP_UP_RESID_20_H20 | +0.74% | −5.18% | −2.36% |
| H26_DISP_HIGH_LOW_BREADTH_20_H20 | +0.16% | −12.38% | −5.97% |
| A5_MONTH_END_SEASONED | +0.12% | −19.95% | −10.62% |

H24–H26 are the V15 dispersion family already frozen (`do not reopen residual / dispersion`). A5 is a calendar/seasoned set, not a new object.

No ID has both val MEAN_FORWARD > 0 and val capital > 0.

---

## Fact 2 — V14.1 still describes H11

Official H11 non-overlap book (`SUMMARY.json`):

- Full path through validation: **−15.61%**, CAGR **−1.13%**, MaxDD **−66.46%** (2015-06-12 → 2018-10-18, no recovery).
- Validation continuation on the same book: **−0.056%**.
- Validation *fresh* MTM: **+0.31%** / CAGR **+0.12%**.
- Cost drag over start (full path): **0.503** of initial capital (fees + slip + stamp summed in recon: 215.5k + 287.4k + 140.8k).
- Unfilled rate **1.75%**. Reasons: SUSPENDED 1277, LIMIT_LOCK 499, DELISTED 7. Limit-lock rate **0.49%**.

Official H11 `TRADES.csv` (same grid, read-only):

| Window | n | Arith mean | Geo mean | AM−GM | Compound |
|---|---|---|---|---|---|
| Full | 172 | +0.115% | −0.105% | 0.221pp | **−16.58%** |
| Research | 142 | (AM>GM, compound loss) | | | |
| Validation | remainder | AM still cannot outrun left tail | | | |

Win rate on the official grid is ~52%. The mean period is slightly positive; compounding a fat left tail (worst period −23.7%, p05 −11.5%) makes the book lose. This is V14.1 Q4 verbatim. **Not a second Alpha.**

---

## Fact 3 — H24/H25 show the same crack, plus a grid mismatch

Existing V15 `TRADES` CSVs (not resimulated):

| Book | Val n | Grid arith | Grid geo | Grid compound | Overlap MEAN_FORWARD |
|---|---|---|---|---|---|
| H24 | 26 | **−0.21%** | −0.48% | −11.70% | **+1.13%** |
| H25 | 27 | +0.18% | −0.20% | −5.18% | +0.74% |
| H26 | 25 | −0.06% | −0.57% | −13.32% | +0.16% |

H25 is textbook AM-GM: grid arithmetic still slightly positive, geometric and compound negative.

H24 is stronger than AM-GM. The overlapping daily 20-day mean is +1.13% in validation, but the *official rebalance grid* already has a negative arithmetic mean. Those are different samples of the same hold length. The Candidate-style statistic is not the strategy book. V14.1 named this. H24 repeats it.

Worst official-grid periods on these three: −17% to −28%. One left-tail print wipes a year of +0.2% means.

---

## Fact 4 — losses cluster in the same calendar, not in one cap bucket

Share of the 42 dual-book *full-path* year compounds that are negative:

| Year | n | n compound < 0 |
|---|---|---|
| 2011 | 42 | **42** |
| 2015 | 42 | 4 |
| 2016 | 42 | 31 |
| 2017 | 42 | 41 |
| 2018 | 42 | **42** |
| 2021 | 42 | 11 |
| 2022 | 42 | 37 |
| 2023 | 42 | **41** |
| 2024 | 39 | 16 |

2015 is the long-CS boom (almost everyone compounds up). 2011 and 2018 are unanimous wipe years. 2023 is almost unanimous. This is **one long-only A-share sleeve in the same crash years**, not 42 independent information failures with 42 different calendars.

Cap-bucket concentration was not re-tabulated: V15–V21 RESULTS do not carry a frozen size-bucket PnL split. V14 H11 stock concentration exists (top 10 names = 58% of *positive* stock PnL; 2206/4202 names negative). That is H11, not a cross-family size map. Missing table = size attribution, not the A/B call.

---

## Fact 5 — unfilled / limit-lock is not the killer

Val unfilled on the 42 dual books: min **0%**, mean **0.53%**, max **1.39%**.

H11 official unfilled 1.75%, mostly suspends. V14.1 already ruled unfilled as 0 PnL / 0 fees / cash residual, not phantom fills.

A 0.5% unfilled rate cannot explain −15% to −72% validation books. Costs on H11 are large *in yuan over a decade* (drag 0.50 of start) but they tax a near-zero mean; they do not invert a large positive mean that is not there.

---

## Verdict

**A — signal has no information; construction is not the main reason there is no second Alpha. Confidence 0.72.**

38/42 new families already have negative validation MEAN_FORWARD. The 20-day book did not “eat a hidden edge.” It compounded a negative or near-zero forecast.

**Sidecar B, not a replacement verdict.** Four hyps plus H11 official show that when the overlapping statistic is slightly positive, the official book still loses (AM-GM and/or grid ≠ overlap). That is why H11 is a Candidate and not a capital edge. It is also why H24 cannot be promoted without changing the object that the gate measures. Changing hold/cost/quantile to manufacture 10% remains locked.

**C is rejected.** The required tables exist: RESULTS capital+predictive, V14 SUMMARY, existing TRADES CSVs. The only missing optional table is a cross-family size-bucket PnL.

---

## New information class inside the locks

**NONE.**

Rejected as same object: forecast/express/unlock 20-day announcement books; dividend yield quintile; SZ50 / 504-day twins; sign flips; quarterly leverage ratios; more industry×macro twins.

No free, PIT-able, economically distinct class is sitting in BaoStock unused that is not a sibling of V13–V21.

---

## Next unit of research resource

Not V22.

Not another A-share CS / filing window.

Construction contrast on existing trades is **done** (this file + `trade_amgm_existing_csvs` in the JSON). It explains NEW_INDEPENDENT=0. It does not raise that number under current gates.

Remaining high-IV hole is paid data. Written in `POST_V21_PURCHASE_VALUE_CASE.md`. Default: **do not buy.** That is a file decision, not a question.

Human gates that stay closed: payment, secrets, rewrite of historical evidence, Final OOS, `order_send`.
