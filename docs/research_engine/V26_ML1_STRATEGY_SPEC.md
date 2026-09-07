# V26 — Strategy specification for ML1 (`A_SHARE_MULTILAYER_MODEL_V25 / ML1_LGBM_STACK`)

**Status:** SPEC ONLY. No Paper, no Live, no order_send. Written because a Candidate that passed Level-1 and reproduction must have an executable definition before anyone talks about money; the definition is what the Final-OOS read (if the owner unlocks it) and any future Paper would test.

## 1. What the strategy is, in one paragraph

Every 20 trading sessions, at the close, score every eligible A-share (listed, trading, non-ST, ≥40 sessions of history) with the frozen V25 LightGBM model on 14 ranked PIT features; buy the top 20% (≈600 names) equal-weight at the next open; hold 20 sessions; sell at the open; repeat. Names that cannot be filled at the open (limit-up/down, suspension) stay in cash for that period. Stock costs per `A_SHARE_STRATEGY_COST_MODEL_V1` (commission 2.5bp + transfer 0.1bp + slippage 10bp per side; stamp 10bp→5bp from 2023-08-28 on sells). No leverage, no hedge (see §4).

## 2. Record it is judged on (non-overlapping ¥1M capital account, costs included)

| window | total | CAGR | MaxDD | Sharpe | periods |
|---|---|---|---|---|---|
| research 2010→2021-08 (OOS from 2012-01) | +276% | 14.5% | −46.8% (2016-11→2018-11) | 0.60 | 118 |
| validation 2021-08→2024-02 (HS300 ≈ −30%) | +30.9% | 11.1% | −20.9% | 0.53 | 31 |
| full 2010→2024-02 | +381% | 13.7% | −46.8% | 0.59 | 148 |

Stock-selection component (LO20 minus the eligible equal-weight basket, same windows): +0.89% per 20 sessions, t 5.1, positive in 11 of 13 years (2017 −2.7%, 2020 −7.2%). Cost stress: validation +31% → +24% at 1.5× → +18% at 2× costs. Reproduction 7/7; placebo clean. Excess-series correlation to H11/H12: 0.06.

**None of this is a 10% promise.** The two −20%…−47% drawdowns are on the record; the Jan–Feb 2024 small-cap crash (−3.7% for LO20 in 2024 YTD, −22% for the HS300-hedged variant) is on the record; the denied window 2024-03→2026-08 is unread.

## 3. What it is exposed to (say it plainly)

- **Size / liquidity tilt.** Median amount-rank of selected names 0.86 (1 = smallest). This is where most of the gain-share sits (NEG_LOG_AMT_20 28%, NEG_TURN_20 17%, REV_20 14%). The strategy is long the small, quiet, recently-down end of the A-share market. That premium has been real for 14 years and it has also produced 2017, 2018 and Jan-2024.
- **Beta ≈ 1 to the equal-weight market.** It is a long-only book. In a bear market it loses less than the average stock (validation), not nothing.
- **Regulatory / microstructure.** Delisting reform, registration system, T+1, limit rules and the 2024 quant-trading rules all change the small-cap end first.
- **Capacity.** Equal-weight into ≈600 small names with 100-share lots: at ¥1M the per-name ticket is ≈¥1,700, below one lot for any stock above ¥17. Realistic minimum for the book *as specified* is ≈¥5M; below that, the backtest's equal weights cannot be held. Above ≈¥100–200M, 10bp slippage on the smallest quintile is no longer a fair approximation. Fewer names or a different weighting is a **new contract**, not an adjustment.

## 4. Why the hedged variant is not the strategy

HN20 (short HS300 futures 1:1) has β 0.92 to the (EW − HS300) spread, R² 0.93, MaxDD −54%, CAGR 2.5% in research. Hedging small-cap longs with a large-cap index converts market risk into size-spread risk and made the drawdown worse. A hedge against a small/mid-cap instrument (IM CSI1000 futures, listed 2022-07; or 中证2000 when available) is the economically right neutraliser and cannot be backtested over 2010–2021 with a real contract. If wanted later: pre-register as a new construction under A1, run on the frozen ML1 scores, count in FDR. Not now.

## 5. Operating rules (what "the same strategy" means going forward)

1. **Model:** the V25 frozen LightGBM (contract params). Re-fit policy for live use, declared now: re-fit once per 240 sessions on data up to t−21 with the identical configuration (this is the REFIT_240 variant, reproduced above). Any other change = new version, new contract.
2. **Features:** the same 14, from the same free sources (BaoStock price/finance/index snapshots, Eastmoney margin daily and holder-count reports), with the same PIT lags (margin D+1, holders after HOLD_NOTICE_DATE, financials after announcement date, index as-of). If a source dies, the feature goes NaN for all names (LightGBM handles it) and the event is logged; the strategy is not re-fit to compensate.
3. **Calendar:** rebalance every 20 trading sessions from the first session of the live period; signal at close, orders at next open, market-on-open or limit at open ±0.5%.
4. **Fills:** a name that opens at the limit or is suspended is skipped; the weight stays in cash until the next rebalance. No chasing.
5. **Risk stops (pre-declared, not tuned):** none inside a period. Between periods: if the live 12-period rolling return of the book minus the eligible EW basket is below −8% (roughly 2× the worst research-period stretch), trading pauses and the case is reviewed; the review may only conclude "resume unchanged" or "retire the version".
6. **Monitoring ledger:** per period record n_selected, n_filled, LO return, EW-basket return, HS300 return, cost paid, and the model's realised rank-IC. These are compared to the research distribution monthly.
7. **Falsification (live):** 24 consecutive periods (≈2 years) with LO20 − EW basket ≤ 0 would put the live record outside 99% of the research distribution; that retires the version.

## 6. Gates still ahead

| gate | status |
|---|---|
| Candidate (Level-1, reproduced, independent) | **PASS** (V25 / V25.1) |
| Strategy spec | this file |
| Final OOS single read | **DENIED until owner unlocks**; one shot, frozen scores, LO20 book, nothing changed afterwards |
| Portfolio | needs a second positive independent sleeve; H11/H12 are negative post-cost and do not qualify → 1 sleeve only |
| Paper (≥ 6 months) | requires owner decision, a broker data feed, and a live feature pipeline for the five sources |
| Small real capital | after Paper matches research within tolerance |

Written 2026-09-04. Author: agent, under `RESEARCH_RULES_AMENDMENT_V1`. Nothing here was tuned on the validation window or the denied window.
