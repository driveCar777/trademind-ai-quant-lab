# cn_a_short — A-Short D1 short-horizon research package (Phase 2A)

New, independent, auditable package for the A-Short short-horizon (T+1/T+2/T+3/T+5) research
contract `A_SHORT_D1_V1`. **Does not modify** ML1 / V25 / V26 / V33 / V34 / V38 or any frozen
dataset. Reuses the canonical cost model, execution-feasibility rule, and lot/min-fee constants.

## Modules
| file | purpose | needs price pack? |
|------|---------|-------------------|
| `__init__.py` | contract id, dataset lineage, pre-registered comparison grid, windows | no |
| `cost.py` | per-notional round-trip cost (fee-only vs +slippage), ¥5 min-fee aware | no |
| `account.py` | account/executability feasibility, min executable capital, cash drag | no |
| `feasibility.py` | horizon × turnover × slippage → cost envelope + gross-alpha requirement | no |
| `baseline.py` | D1 baseline engine: forward labels, T+1 fills, limit/suspension, Top-K vs EW | yes (real run) |
| `report_tables.py` | generates cost/account/feasibility tables → `PHASE2A_TABLES.json` | no |
| `run_baseline.py` | runs the empirical baseline IF the frozen pack is present, else DATA_BLOCKED | yes |

## Reuse (single source of truth, not reinvented)
- `research_engine/cn_a_share_alpha/cost.py` — COMMISSION / TRANSFER / SLIPPAGE / stamp
- `research_engine/cn_a_share_ml_v25/top_n_book.py` — `MIN_FEE=5.0`, `LOT=100`, `_fee`, `board_mask`
- `research_engine/cn_a_share_strategy_v14_1/capital_ref.py` — `exec_reason` (limit-lock / suspension / T+1)

## Run
```bash
# runnable now (no price data needed):
python -m research_engine.cn_a_short.report_tables
# empirical baseline (needs frozen price pack on the :9000 master box):
python -m research_engine.cn_a_short.run_baseline
# tests:
python -m pytest research_engine/cn_a_short/tests/ -q
```

## Status in this environment
The frozen price pack (`tm-ashare-EQUITY-D1-...`) is **not materialized** in the cloud VM, so
`run_baseline` returns `DATA_BLOCKED` with reproduction steps. Cost / account / feasibility results
are fully computed. See `docs/a_short/A_SHORT_PHASE2A_RESULTS.md`.
