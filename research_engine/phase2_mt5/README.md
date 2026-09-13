# phase2_mt5

Ava GOLD Phase 2 foundation. **Not a Candidate. No `order_send`.**

Follows existing `research_engine/` package style. Does not create a new root service. Does not write `:9000`, `daily.py`, ML1, or frozen `READ.json`.

## What this package is

| Module | Role |
|--------|------|
| `collector.py` | Read-only MT5 snapshot → `AUDIT/BROKER_GOLD_SPEC_*.json` + `MT5_GROUND_TRUTH/` |
| `contract.py` | SignalContractV2 (SPEC §30.2) |
| `ledger.py` | signal → order → deal → position → close |
| `costs.py` | Unified spread/slip/swap; assumptions labeled |
| `baselines.py` | Nine pre-registered baselines on RESEARCH window |
| `ladder.py` | EXP-001 Naive → Linear only |
| `gates.py` | Candidate Gate V2 C0–C13 |
| `overlap.py` | H1 hold=24 overlap numbers |
| `monte_carlo.py` | Scaffold; refuses to run without a Candidate |
| `metrics.py` / `labels.py` | Unified metrics + economic label V2 |

## Experiments

Only `EXP-001` / `EXP-002` / `EXP-003`. Contracts in `docs/research_engine/EXP00*_*.md` were frozen **before** runs.

- RESEARCH official window: through `2025-09-11`
- FINAL OOS from `2025-09-12`: locked, not used for selection

## Run

```
C:\ProgramData\miniconda3\python.exe -m research_engine.phase2_mt5.collector
C:\ProgramData\miniconda3\python.exe -m research_engine.phase2_mt5.baselines
C:\ProgramData\miniconda3\python.exe -m research_engine.phase2_mt5.ladder
```

Write-once: existing `READ.json` is refused unless `TRADEMIND_PHASE2_FORCE=1`.

## Grok

Grok is not a strategy. `:9001` send requires `TRADEMIND_HOT_GROK_SEND=1` (default 0).
