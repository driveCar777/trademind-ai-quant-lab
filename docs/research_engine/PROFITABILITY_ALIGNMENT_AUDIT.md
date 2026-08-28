# Profitability Alignment Audit — Research Engine V0.4

TradeMind end goal: a system that can make money. Long-run target: **annualized return ≥ 10%** after costs and risk, on real capital much later.

This document does **not** claim HYP-0001 is a trading strategy. A supported persistence test is not 10% annual return.

## A. What exists now

| capability | status | role vs profit |
| --- | --- | --- |
| Data Layer V0.1 (16 frozen datasets) | DONE | RESEARCH_INFRASTRUCTURE |
| Qualification V0.1 | DONE | RESEARCH_GOVERNANCE |
| Research Readiness V0.2 | DONE | RESEARCH_GOVERNANCE |
| Research Protocol V0.3 (causal window, no leakage) | DONE | RESEARCH_GOVERNANCE |
| HYP-0001 14:11 preregistration | LOCKED | DIRECTLY_PROFIT_RELEVANT (first predictive claim) |
| Experiment IDs `tm-exp-20260825-141158-*` | LOCKED | RESEARCH_GOVERNANCE |
| Research Engine dispatch / Xavier compute | IN REPAIR | RESEARCH_INFRASTRUCTURE |
| FDR / multiple-testing ledger | PARTIAL | RESEARCH_GOVERNANCE |
| Final OOS holdout | LOCKED, access denied | RESEARCH_GOVERNANCE |
| V11.7 RSI sample-in backtest | FROZEN history | INDIRECTLY_PROFIT_RELEVANT (old lab, not this contract) |
| MT5 order_send | exists, unused here | NOT_CURRENTLY_PROFIT_RELEVANT until paper/live |

HYP-0001 is the first **formal predictive** experiment. It tests whether a 3-bar sign streak has a next-bar continuation mean different from 0. If falsified, we stop that claim. If supported, it is still only a signal ingredient.

## B. What each layer does for money

- **Data + qualification**: you cannot estimate an edge on dirty bars. Infrastructure, not edge.
- **Protocol / windows**: stops leakage self-deception. Governance.
- **HYP-0001**: first attempt to find a *predictive* offset. Directly relevant, not a strategy.
- **Engine correctness**: if identity is wrong, every later factor mine will lie. Governance that protects profit search.
- **V11.7**: already showed sample-in RSI stories are easy to fake. History. Do not rerun.

Honest label: most of V0.1–V0.3 is **not** profit. It is the floor so the next stage can hunt edge without cheating.

## C. Missing (do not build in this task)

- factor mining loop (atomic features → combinations → FDR)
- strategy generation (entry/exit from a signal)
- cost-aware backtest on the *new* research path (V11.7 is frozen elsewhere)
- position sizing / portfolio
- regime detection
- cross-asset models
- news / LLM event signals
- economic significance (turnover, capacity, drawdown)
- paper trading
- live MT5

## D. What the four Xaviers should compute next

| stage | what | why | input | output | profit link |
| --- | --- | --- | --- | --- | --- |
| 1 | Research Engine correctness | no self-deception | locked HYP-0001 | lineage-complete results | makes later edges believable |
| 2 | Factor / hypothesis discovery | find more claims like HYP-0001 | frozen datasets + registry | new HYP-xxxx, not retuned 0001 | search for predictive offset |
| 3 | Predictive edge | keep only claims that survive validation + FDR | stage 2 survivors | ranked effects | raw edge, still not a book |
| 4 | Strategy mining | turn a signal into trades | survivors + cost model | strategy contracts | first P&L path |
| 5 | Robust OOS | one locked Final OOS, later | candidate strategies | pass/fail | kill overfit |
| 6 | Risk / portfolio | size and combine | survivors | book rules | path to ≥10% is here, not in p-values |
| 7 | Paper | execution friction | book rules | paper blotter | reality check |
| 8 | MT5 demo | venue | paper-pass only | fills | still not real money |
| 9 | Real capital | last | long paper + risk | live | years after stage 1 |

Stage 1 is the current task. After HYP-0001 formal execution finishes, **do not** add more data profiling. Next useful work is Stage 2 factor discovery — still with write-once hypotheses.

## E. Factor Mining V0.x (design only)

```
raw bars
  → atomic features (return, range, streak, vol, location)
  → optional combinations
  → condition + horizon target
  → effect vs pre-registered null
  → multiple-testing ledger + BH FDR
  → research / validation only
  → Final OOS still denied
```

Future families (new IDs, never overwrite HYP-0001):

- price / technical: momentum, reversal, ATR, breakout, MA distance
- structure: compression/expansion, pullback, regime
- cross-asset: GOLD↔USDJPY, GOLD↔EURUSD, OIL↔FX
- news later: LLM event → direction/strength → predictive test

Interface sketch (not implemented):

```
factor_id, feature_set, condition, target, horizon,
null, family_id, preregister_hash, experiment_id
```

Same authority rule as HYP-0001: Windows owns the contract; Xavier only computes.

## F. Distance to ≥10% annualized

HYP-0001, even if SUPPORTED, does **not** imply 10%. Missing: costs, turnover, sizing, portfolio, OOS, execution.

Current distance: **Stage 1 of 9**. The machine can now be made honest. It cannot yet produce a tradeable book.

## G. Next research priority (after this freeze)

1. Finish formal HYP-0001 (this repair).
2. Factor Discovery V0.x on the same 16 datasets.
3. Only then strategy mining with a cost model.

Not: more RSI, not V11.7, not `order_send`, not unlocking Final OOS.
