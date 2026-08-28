# Profit Discovery V0.6 Report

Four Xavier full run started `2026-08-26T14:18:10Z`, collected `2026-08-26T14:23:07Z`.  
HYP-0001 / FD V0.1 / V0.5 / 14:11 files were not modified. Final OOS denied. No MT5. No `order_send`.

Plan: `docs/research_engine/PROFIT_DISCOVERY_V0.6_PLAN.md`  
Ranking: `data/market/research_engine/profit_discovery/PROFIT_RANKING_V0.6.json`  
Search hash: `0fba52a98d861046cd61db51861bf96bebfaa2d51b42001d37463776bb7891d7`

## 1. Executive

This version asked whether a **cost- and risk-adjusted Strategy Candidate** exists in a locked, small family set.

```text
outcome              = WEAK_EDGE_ONLY
program CANDIDATE    = 0
WEAK_EDGE            = 2   (MOM-DIR 0.5% and 1%, OIL D1 only)
NO_EDGE              = 5
```

**No strategy may continue as a CANDIDATE.**  
OIL D1 momentum passed the *dataset* gate once. That is not two-dataset support. It is not 10% annualized.

Correct reading: **this search space is insufficient for a tradeable candidate after spread + 5bp + 10bp + 0.5%/1% risk.**  
Not: markets have no opportunity.

## 2. What was already tested (do not repeat)

| prior | result | do not repeat as |
| --- | --- | --- |
| HYP-0001 streak=3 | WEAK_SUPPORT, not a book | streak 2/3/4/5 retune |
| FD V0.1 57 factors | NO_USEFUL_FACTORS_FOUND | RSI / MA / factor farms |
| V0.5 15 next-bar sketches | NO_USEFUL_STRATEGIES_FOUND | always-long-in-UP, fade-EXTENDED, p-value only |

## 3. What V0.6 tested (new)

| family | mechanism | not the same as |
| --- | --- | --- |
| TF-BRK20 | TREND_STRONG + 20-bar breakout, next open, hold 5, ATR stop | V0.5 always-long-in-UP |
| MR-Z20 | RANGE_LOWVOL fade \|z\|≥1, next open, hold 5 | V0.5 next-bar fade p-value |
| MOM-DIR | trend + RET_5 agreement, hold 8 | HYP-0001 streak=3 |
| DEF | skip HIGH_VOL / WIDE | overlay, not a PnL engine |

Fill: **NEXT_BAR_OPEN**. Close fills forbidden. Leverage cap 1×. Cost: half spread + 5bp + 10bp per side.

## 4. Four Xavier

| node | symbol | jobs | wall s | status |
| --- | --- | --- | --- | --- |
| Xavier-01 | GOLD ×4 | 4 | 296.6 | ok |
| Xavier-02 | EURUSD ×4 | 4 | 286.3 | ok |
| Xavier-03 | USDJPY ×4 | 4 | 273.7 | ok |
| Xavier-04 | OIL ×4 | 4 | 275.2 | ok |

Windows locked space + collected. Workers did not invent ids.

## 5. Candidate ranking

Program CANDIDATE list: **empty**.

Ranked by program status, then dataset-gate hits, then mean research total return (16 datasets). Mean return is **not** a trading score; it is mostly cost bleed.

| rank | strategy_id | program | cand. datasets | mean research TR | why |
| --- | --- | --- | --- | --- | --- |
| 1 | `PD-V06-MOM-DIR-H8-R005` | WEAK_EDGE | 1 (OIL D1) | −21.6% | PARTIAL_SUPPORT |
| 2 | `PD-V06-MOM-DIR-H8-R010` | WEAK_EDGE | 1 (OIL D1) | −24.0% | PARTIAL_SUPPORT |
| 3 | `PD-V06-TF-BRK20-H5-R005` | NO_EDGE | 0 | −3.9% | SEARCH_SPACE_INSUFFICIENT_OR_NULL |
| 4 | `PD-V06-TF-BRK20-H5-R010` | NO_EDGE | 0 | −4.9% | SEARCH_SPACE_INSUFFICIENT_OR_NULL |
| 5 | `PD-V06-DEF-SKIP-HIVOL` | NO_EDGE | 0 | 0.0% | overlay; 0 trades by design |
| 6 | `PD-V06-MR-Z20-H5-R005` | NO_EDGE | 0 | −10.5% | SEARCH_SPACE_INSUFFICIENT_OR_NULL |
| 7 | `PD-V06-MR-Z20-H5-R010` | NO_EDGE | 0 | −11.9% | SEARCH_SPACE_INSUFFICIENT_OR_NULL |

Do **not** treat rank 1–2 as a book.

## 6. Weak leftover (not a candidate)

`PD-V06-MOM-DIR-H8-R005` / `R010` on **OIL D1 only**:

| size | research TR | research CAGR | research trades | research DD | val TR | val trades |
| --- | --- | --- | --- | --- | --- | --- |
| 0.5% | +1.04% | +0.13% | 85 | −6.0% | +2.22% | 18 |
| 1.0% | +1.82% | +0.23% | 85 | −11.7% | +4.39% | 18 |

Sharpe on that leftover ≈ 0.08. OIL H1 validation was slightly positive, research lost. All GOLD / EURUSD / USDJPY lost after cost.

Program rule requires the dataset CANDIDATE gate on **≥ 2 datasets**. Failed.

Do **not** retune hold=8 or risk on OIL to manufacture a second hit.

USDJPY D1 TF-BRK20 had a small after-cost research profit (+1.1% / +1.7%) but **validation trades < 4**. Dataset WEAK_EDGE only. Family remains NO_EDGE.

## 7. All failed directions (keep)

Prior (already frozen; not re-run):

- Unconditional factor farm (FD V0.1)
- Next-bar state sketches / p-value only (V0.5)
- HYP-0001 streak continuation as a trading book

This version (failures retained under `data/market/research_engine/profit_discovery/`):

- Trend-following Donchian-20 in TREND_STRONG: **NO_EDGE** (both risk fractions)
- Range fade z20 in RANGE_LOWVOL: **NO_EDGE**
- Defensive cash overlay: **NO_EDGE** by design (0 trades, 0 return)
- Momentum-with-trend on GOLD / EURUSD / USDJPY, all four timeframes: **NO_EDGE**
- Equal-weight TF+MR+MOM 0.5% portfolio on all four **D1** books: **negative** research total return

High turnover + 30bp+spread per round trip is lethal on M15/H1. Annualizing a few weeks of losses produces garbage CAGRs near −90% to −99%. That is a **span problem**, not a −99% trading year.

## 8. Same-dataset D1 portfolios (R005 sleeves)

Equal-weight TF + MR + MOM, defensive overlay on each. Not a cross-asset book.

| symbol | research TR | research CAGR | research DD | skip rate |
| --- | --- | --- | --- | --- |
| GOLD | −4.08% | −0.52% | −4.3% | 44.2% |
| EURUSD | −9.80% | −1.29% | −9.8% | 36.8% |
| USDJPY | −5.12% | −0.66% | −7.0% | 38.1% |
| OIL | −1.04% | −0.13% | −3.9% | 37.3% |

Combining three weak sleeves did not produce a candidate curve.

## 9. Distance to 10% annualized

| fact | meaning |
| --- | --- |
| Best locked D1 CAGR ≈ **+0.23%** (OIL MOM 1%) | ~**44×** below 10% even on the one leftover |
| Leftover Sharpe ≈ 0.08 | compatible with noise |
| 16 datasets × 2000 bars | M15/H1/H4 spans are too short to estimate 10% |
| D1 2000 bars ≈ years | the only usable CAGR window, and it still missed 10% by an order of magnitude |
| Costs 5+10 bp/side + spread | dominate 5–8 bar holds |
| Portfolio D1 all negative | diversification inside one symbol did not close the gap |

10% is the long-run capital target. **This version cannot certify it and did not reach a CANDIDATE that could later be asked that question.**

To even *study* 10% honestly you need longer M15/H1 history **or** much lower turnover. Raising the leftover by retuning N/hold/cost would be a rule change, not a discovery.

## 10. Data insufficiency (must say)

`actual_count=2000` on every file.

- M15 2000 bars ≈ weeks. CAGR is not interpretable.
- H1 2000 bars ≈ a few months.
- H4 2000 bars < 2 years of 24h bars.
- D1 2000 bars is the only span where CAGR is a real number — and the best leftover is +0.23%.

Any future 10% claim on M15 from this snapshot would be a lie.

`tick_volume` only. `real_volume=0`. Event state is NA. Cross-asset aligned portfolio was not claimed.

## 11. Tests and invariants

`tests/research_engine` **74 PASS** (prior suite kept). V0.6: open fill ≠ close, leverage cap, OOS denied, worker cannot add ids, gates locked.

Not touched: V11.7, `master/api/`, Xavier 8002–8005 sidecars, `data/mine/longrun/`, `data/market/immutable/`, HYP-0001 14:11 hashes.

## 12. Next stage (one)

**Do not start MT5. Do not lock Final OOS. Do not retune OIL momentum.**

Recommended next: **longer immutable history (new Data Layer version).**  
Until M15/H1 span can support an annualized question, more indicator families on 2000 bars will reprint NO_EDGE.

If a strategy contract is opened later, it must be a **new versioned family** with much lower turnover (multi-day hold), not N=20 / hold=5 / RSI-MA scan.

Status: `NO_STRATEGY_CANDIDATE`. Failures retained.
