# Factor Discovery V0.1 Architecture

Not a strategy engine. Not HYP-0001 retune. Not MT5.

## Authority

```text
Windows locks FACTOR_SEARCH_SPACE_V0.1.json
        ↓
Windows writes job manifests (candidate_ids + hash + seed)
        ↓
Xavier node_eval.py reads job + space
        ↓
load dataset once → evaluate listed candidates in memory
        ↓
return lineage + stats
```

Worker cannot invent candidates. `catalog.py` is not used for this search.

HYP-0001 `node_runner.py` is untouched. Remote dir is `/tmp/tm-factor-discovery-v01`.

## Modules

| path | role |
| --- | --- |
| `research_engine/factors/space.py` | locked candidate universe |
| `research_engine/factors/compute.py` | causal features + evaluation targets |
| `research_engine/discovery/contract.py` | hash / job / Final OOS guards |
| `research_engine/discovery/evaluate.py` | research freeze + validation apply |
| `research_engine/discovery/nulls.py` | permute target / shuffle signal / random factor |
| `research_engine/discovery/rank.py` | BH-FDR + four ranks, no magic score |
| `research_engine/discovery/jobs.py` | dataset × node partition |
| `research_engine/discovery/node_eval.py` | Xavier worker |
| `scripts/research_engine_factor_run.py` | Windows dispatcher |

Reuse: `statistics.py`, `holdout.py`, `windows.py`, `bars.py`, `CausalView`, SSH pattern.

Cross-node compare uses `content_hash` (dataset + space + seed + candidates + nulls). `result_hash` includes `job_id` and therefore differs across nodes by design.

## Causal rule

`feature[t]` uses `CausalView` through `t`. Targets may read `t+horizon` only inside `window_guard` research/validation. Final OOS raises.

## Cost

`RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY`. Gross delta vs median(spread/close). Not a broker cost model. Not a backtester.

## Ranking

Four axes: statistical (FDR-pass count), effect (|d|), stability (same-sign datasets), economic (|delta|).

Statuses: REJECTED / INCONCLUSIVE / CANDIDATE / PROMISING.

`PROMISING != strategy != 10% annualized.`

`NO_USEFUL_FACTORS_FOUND` is valid.

## Strategy Mining V0.1 interface (not implemented)

```text
PROMISING factor
  → signal rule (threshold already frozen on research)
  → entry / exit / holding
  → cost / slippage
  → risk / position
  → strategy contract
  → later: portfolio → Final OOS → paper → MT5
```

Annualized return ≥ 10% is a **portfolio/OOS** target, not a Factor Discovery p-value cutoff.

## News / LLM (designed, not live)

```text
News → structured event factor → historical test → FDR → economic impact
```

No live news API. No “LLM says bullish → buy”.

## Cross-asset (designed, not computed)

Needs aligned timestamps across files. Family `FAM-FD-XASSET-0001` is DRAFT.

## Memory schema

Each tested factor keeps: search hash, candidate_id, datasets, raw_p, adjusted_p, effect, why rejected, status. Failed factors are not deleted.
