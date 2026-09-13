# PHASE2_FOUNDATION

> 2026-09-13. Index for the Ava GOLD Phase 2 mission. Not a Candidate.

## Why

Phase 1 showed there is no single MT5 money machine. This phase builds **broker truth**, a **shared signal/ledger schema**, **unified cost-aware baselines**, and **three write-once experiments** — then stops where the evidence stops.

## Layout

| Path | Role |
|------|------|
| `SPEC.md` §30 | SignalContractV2, ledger, ground truth, Gate V2, EXP ids |
| `research_engine/phase2_mt5/` | Code (collector, contract, ledger, baselines, ladder) |
| `AUDIT/` | Broker spec, status, final report, multiple-testing |
| `MT5_GROUND_TRUTH/` | Masked account + GOLD + orders/deals/positions |
| `docs/research_engine/EXP001_*` | D1 contract + ladder decision |
| `docs/research_engine/EXP002_*` | H1 contract (baselines run; no ML) |
| `docs/research_engine/EXP003_*` | Cross-asset contract (not run) |
| `data/market/research_engine/phase2/results/` | Write-once READ |

## Status

See `AUDIT/PHASE2_STATUS.md` and `AUDIT/PHASE2_FINAL_REPORT.md`.
