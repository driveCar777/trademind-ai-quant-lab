# HYP-0001 CONTRACT MISMATCH — Root Cause

Date: 2026-08-26  
Forensic snapshot: `data/market/research_engine/reports/HYP-0001_LIVE_FORENSIC.md`  
Quarantine: `data/market/research_engine/quarantine/CONTRACT_MISMATCH_20260826/`

## Phenomenon

Windows scheduler (22:59 local, PID 25012/36392) reused the 14:11 locked HYP-0001 files and 32 experiment IDs. Four Xaviers ran `node_runner.py` at ~99% CPU and wrote JSON. Those outputs were **not** formal HYP-0001 evidence.

Identity on Xavier:

- `family_id` from `catalog.py` = `FAM-PERSISTENCE-0001` (draft)
- `experiment_id` / `preregister_hash` written as `PENDING`
- exported continuation field named `conditional_mean`
- locked JSON never uploaded

## Why Windows looked correct

Call chain:

```
scripts/research_engine_run.py main()
  → preregister()          # saw existing A/B files → RE_PREREG_REUSE
  → make_experiments()     # saw tm-exp-20260825-141158-* → RE_EXPERIMENT_REUSE
  → ThreadPoolExecutor
       → run_node()
```

`preregister()` / `make_experiments()` did load the 14:11 lock. File mtimes stayed `2026-08-25 22:11:58`. That is why Windows looked like it was running the locked contract.

## Why Xavier was not

`run_node()` uploaded only:

- `research_engine/*.py`
- `research_protocol/*.py`
- dataset `bars.csv` / `manifest.json` / `DATA_QUALITY.json`

It did **not** upload:

- `preregistration/HYP-0001-A.json` / `HYP-0001-B.json`
- `experiments/tm-exp-20260825-141158-*.json`
- `jobs/ALL_JOBS.json`

`node_runner.py` then hardcoded:

```python
variants = [hyp_0001_a(), hyp_0001_b()]
```

and wrote lineage placeholders:

```python
"experiment_id": "PENDING"
"preregister_hash": "PENDING"
```

Comment in the old runner said Windows would rewrite lineage later. That is an authority split: worker invents identity, collector patches it. Formal results must be born with the locked IDs.

## Exact root cause

One sentence:

> Contract existed on Windows and was never serialized into the Xavier job; the worker ignored manifests and reconstructed a draft hypothesis from `catalog.py`.

Anti-patterns confirmed:

| pattern | where |
| --- | --- |
| Hardcoded hypothesis | `node_runner.py` `hyp_0001_a()` / `hyp_0001_b()` |
| Hardcoded draft family | `catalog.py` `FAM-PERSISTENCE-0001` |
| PENDING experiment_id | `node_runner.py` lineage |
| Hash stays on Windows only | `ALL_JOBS.json` never sent |
| Result serializer drops metric name | `compact_arm()` omitted `continuation_mean` |

## Exact fix

1. Quarantine 22:59 outputs as `QUARANTINED_CONTRACT_MISMATCH`. Do not mix into formal results.
2. Stop only `research_engine_run.py` and `node_runner.py`. Leave 8002–8005.
3. Worker requires `--contracts-file`. No catalog fallback for formal jobs.
4. Dispatcher uploads locked hypothesis / prereg / experiment JSON + `NODE_JOBS.json`.
5. `contract_guard.py` hard-fails `FAM-PERSISTENCE-0001`, `PENDING`, wrong prereg hash, missing `continuation_mean`.
6. Results write `continuation_mean`, `family_id=FAM-MOMENTUM-0001`, real `experiment_id`.
7. Formal collect lands in `results/formal/`. Wrong contract → `results/blocked/`.

`catalog.py` remains as historical draft / unit-test builder. It is not the formal HYP-0001 path.

## Prevention

- Formal worker cannot start without `NODE_JOBS.json` (`formal: true`).
- Tests 1–10 in `tests/research_engine/test_contract_authority.py`.
- Collector calls `assert_formal_result` before writing formal evidence.
