# ml1_live — ML1 forward pipeline (V29, Paper preparation)

Design: `docs/research_engine/V29_ML1_LIVE_PIPELINE_DESIGN.md`. Strategy definition: `docs/research_engine/V26_ML1_STRATEGY_SPEC.md`.

| file | role |
|---|---|
| `panel.py` | live calendar / basics / incremental daily bars after 2026-08-28; merged live pack (frozen rows copied bit-for-bit) |
| `layers.py` | margin (daily), holders (weekly), index as-of (monthly) refresh into `data/market/cn_a_share/live/` |
| `score.py` | V25 features on the live pack, REFIT_240 model cache, top-20% list -> `live/signals/SIGNAL_{date}.json` |
| `ledger.py` | shadow ledger continuing the V28 chain (signal every 21 sessions), settled with the frozen cost model; V26 pause/retire rules |
| `daily.py` | orchestrator: `python -m research_engine.ml1_live.daily [--asof] [--capital] [--force-score] [--no-holders] [--skip-fetch] [--no-ml7]` |
| (hook) | step 9 calls `research_engine/ml7_live` (V38-S3 information-stack shadow, **output-only**: `SIGNAL_ML7_{date}.json`, `LEDGER_ML7.json`, `STATUS_ML7.json`) after every ML1 file is written; failures are recorded in `STATUS.json["ml7"]` and never affect ML1 outputs |

Outputs live under `data/market/cn_a_share/live/` (ignored by git except `STATUS.json`, `signals/`, `ledger/`).

Hard rules: no `order_send`; no writes into frozen datasets; no feature/param/hold/cost change (any such change breaks V26 and is a new contract).
