# Factor Discovery V0.1 Report

Locked 2026-08-26T00:29:38Z. Four Xavier full run 2026-08-26T00:31:55Z → ~00:38:46Z.

HYP-0001 14:11 was **not** modified. V11.7 / mine_longrun / order_send / Final OOS / immutable bars were **not** touched.

## A. Executive status

Implemented a runnable Factor Discovery pipeline: locked 57-candidate search space, Windows-owned jobs, Xavier `node_eval`, BH-FDR, three nulls, four-axis ranking.

Actual run: 17 jobs (16 primary datasets + GOLD M15 cross-check), 876 primary tests, seed `20260825`, screening bootstrap/perm 200.

**Finding:** `NO_USEFUL_FACTORS_FOUND`.

- PROMISING: 0
- CANDIDATE: 0
- INCONCLUSIVE: 5 (volatility clustering on `future_abs_return`, FDR fail, cost-sensitive)
- REJECTED: 52

This does **not** prove a profitable strategy, annualized ≥ 10%, paper trading, or live trading.

It also does **not** prove markets have no edge. It only says: this first pre-defined universe, under this contract, did not produce a factor that survived FDR + validation sign + multi-dataset + cost screen.

## B. Search contract

| field | value |
| --- | --- |
| discovery_id | `FACTOR_DISCOVERY_V0.1` |
| search_space_hash | `add0211ffb189d50639b656af1b009ac15849d9f3d426af8469f9700eb05dc5a` |
| candidates | 57 |
| families live | 9 (A–H + limited combo) |
| reserved DRAFT | cross-asset, news |
| FDR | BH q=0.05, m=876, discoveries=0 |
| Final OOS | DENIED |
| volume | `tick_volume` only |
| cost | `RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY` |

Worker cannot add candidates. Thresholds freeze on research 67/33 and apply to validation.

## C. Four Xavier

| node | jobs | candidates evaluated | compute s | wall s | status |
| --- | --- | --- | --- | --- | --- |
| Xavier-01 | 4 GOLD | 219 | 328.5 | 330.4 | ok |
| Xavier-02 | 4 EURUSD | 219 | 318.3 | 320.6 | ok |
| Xavier-03 | 4 USDJPY | 219 | 312.6 | 314.6 | ok |
| Xavier-04 | 4 OIL + GOLD M15 CROSS_CHECK | 276 | 408.9 | 411.5 | ok |

Load balance: 01–03 ~5.2–5.5 min. 04 has one extra cross-check job (~83 s), so ~6.9 min. Acceptable.

GOLD M15 Xavier-01 ↔ Xavier-04: **content hash PASS** (`399a3763c0aaf51c85e46e37be36df022d302e9a7c1d3ee06997d6a6d9094920`). `result_hash` differs because it includes `job_id` / node name; that is not a compute mismatch.

Nulls on GOLD M15 (same on both nodes): permute-target p=0.196, shuffle-signal p=0.922, random-factor p=0.627. Pipeline did not mint a significant null.

## D. The five INCONCLUSIVE rows

All are **volatility → future absolute return**, direction-stable across most of the 16 datasets, FDR fail, cost-sensitive:

| candidate | mean d | mean bps | same-sign datasets |
| --- | --- | --- | --- |
| TR_14_HIGH_ABS | +0.23 | +10.8 | 15 |
| RANGE_10_HIGH_ABS | +0.21 | +9.7 | 16 |
| RANGE_20_HIGH_ABS | +0.21 | +9.7 | 16 |
| RANGE_20_LOW_ABS | −0.17 | −7.1 | 14 |
| RANGE_10_LOW_ABS | −0.17 | −6.5 | 16 |

Interpretation: high recent range / TR tends to be followed by larger |return|; low range by smaller |return|. That is **volatility clustering**, not a directional betting edge.

They are not PROMISING. They are not a strategy. They are not 10% annualized.

Directional momentum / reversal / MTF / volume / spread families: rejected under FDR.

## E. Audit

| item | result |
| --- | --- |
| A locked dataset | PASS |
| B four Xavier distributed | PASS |
| C worker owns search space | PASS (does not) |
| D multiple testing / BH | PASS (m=876, 0 discoveries) |
| E null controls | PASS |
| F know how many factors tested | PASS (57 candidates, 876 tests) |
| G keep failed factors | PASS |
| H restore lineage | PASS |
| I Final OOS still accessible | PASS (DENIED / access raises) |

## F. Economic summary

No economically interesting **directional** candidate survived.

The only stable pattern is a small abs-return displacement after volatility state (~7–11 bps), which fails FDR at the full-search burden and is cost-sensitive under raw spread/close.

Distance to a tradable book with annualized ≥ 10%:

```text
Factor Discovery (this version) — no PROMISING edge
    ↓ still needed
broader / regime-conditioned factor search
    ↓
Strategy Mining (entry/exit/hold/cost/risk)
    ↓
Portfolio
    ↓
Final OOS
    ↓
Paper
    ↓
MT5
```

10% is a later capital outcome, not a p-value cutoff.

## G. Next stage (one)

**Continue Factor Discovery** (V0.2).

Do **not** start Strategy Mining V0.1: there is no PROMISING input.

Do **not** retune HYP-0001 streak.

Reasonable V0.2 directions (new versioned contract, not a silent expand):

- regime-conditioned directional tests (vol state × momentum/reversal)
- tighter, honest cost units (points vs price)
- still no RSI farms, no news API, no ML, no Final OOS

## H. Tests

- Old research-engine suite kept: 34 PASS
- New factor tests: 22 PASS
- Combined: **56 PASS**
- Smoke Xavier-01 GOLD M15: PASS (87 s wall)
- Full 17 jobs: PASS

## I. Untouched

HYP-0001 14:11 files, `FAM-MOMENTUM-0001`, V11.7, `data/mine/longrun`, 8002–8005, immutable datasets, quarantine evidence, `order_send`.
