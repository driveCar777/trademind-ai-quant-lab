# HYP-0001 LIVE FORENSIC — 2026-08-26 correction

Does not overwrite `HYP-0001_LIVE_FORENSIC.md`.

## Before stop (16:34:20Z)

Windows research PIDs 25012, 36392 (`scripts/research_engine_run.py`, started 2026-08-25 22:59:22).  
Xavier node_runner PIDs: 01=20142, 02=27283, 03=32247, 04=18789.

Those outputs were copied to:

`data/market/research_engine/quarantine/CONTRACT_MISMATCH_20260826/`

Status: `QUARANTINED_CONTRACT_MISMATCH`.

## After stop (16:34:38Z)

Windows research PIDs terminated.  
Xavier `node_runner.py` TERM: 20142 / 27283 / 32247 / 18789.

Sidecar `server.py` still up. 8002–8005 LISTEN on all four nodes.

Not stopped: factor-worker on 02, monitor-worker on 04, uvicorn on 01:8000.

## 14:11 lock after quarantine

Unchanged:

- A `485d56a8f5a8e6822231760be240500ce6deb194471cde78172c3b5e4630b6d8`
- B `fbd14d199ba6390ac91f8700d48053ff75c99d7510183d58eeb1a101238cd3db`
- experiments `tm-exp-20260825-141158-001` … `-032`
- family `FAM-MOMENTUM-0001`

## Assessment of the 22:59 run

Still `CONTRACT_MISMATCH`. Isolated. Not formal evidence.
