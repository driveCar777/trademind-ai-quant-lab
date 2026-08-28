# HYP-0001 Execution Restoration

14:11 contracts were not rewritten. This is formal execution of the existing lock, not a new hypothesis.

## Locked identity (unchanged)

| field | value |
| --- | --- |
| parent | HYP-0001 |
| family | FAM-MOMENTUM-0001 |
| A hash | 485d56a8f5a8e6822231760be240500ce6deb194471cde78172c3b5e4630b6d8 |
| B hash | fbd14d199ba6390ac91f8700d48053ff75c99d7510183d58eeb1a101238cd3db |
| experiments | tm-exp-20260825-141158-001 … 032 |
| metric | continuation_mean vs 0 |

## Wrong run (quarantined)

22:59 catalog path. `QUARANTINED_CONTRACT_MISMATCH`.  
`data/market/research_engine/quarantine/CONTRACT_MISMATCH_20260826/`

Stopped only research PIDs. Sidecars 8002–8005 left running.

## Repair

Worker requires `--contracts-file`. Dispatcher uploads locked A/B + experiment JSON.  
Hard fail: `FAM-PERSISTENCE-0001`, `PENDING`, wrong hash, missing `continuation_mean`.

## Smoke — PASS

2026-08-25T16:35:05Z → 16:37:50Z. Xavier-01, GOLD M15, HYP-0001-A, `tm-exp-20260825-141158-001`, repeats=2.  
exit 0, blocked 0, DETERMINISTIC, continuation_mean present, Final OOS denied.

## Full dispatch — PASS

2026-08-25T16:40:21Z → 18:49:43Z. Repeats=10.

| | value |
| --- | --- |
| jobs collected | 48 |
| experiment_ids | 32 (all `tm-exp-20260825-141158-*`) |
| family | FAM-MOMENTUM-0001 only |
| prereg hashes | A and B lock hashes only |
| metric | continuation_mean |
| PENDING / None experiment_id | 0 |
| DETERMINISTIC | 48 / 48 |
| blocked | 0 |
| cross 01↔04 GOLD M15/H1, 02↔03 EURUSD M15, 02↔03 USDJPY M15 | PASS PASS PASS PASS |
| family_status (rollup) | WEAK_SUPPORT |
| FINAL_OOS | locked access denied |
| index | `data/market/research_engine/RESEARCH_ENGINE_INDEX_FORMAL.json` |

WEAK_SUPPORT is a statistical rollup across arms. It is **not** a trading strategy and **not** ≥10% annual return.

After collect: no `node_runner` on any Xavier. 8002–8005 still LISTEN (4 ports × 4 nodes).

## Q1–Q17

1. Yes — live jobs used 14:11 A/B + `tm-exp-20260825-141158-*`.  
2. Yes — FAM-MOMENTUM-0001 only in formal results.  
3. Yes — original A/B hashes.  
4. Yes — every formal row has experiment_id + experiment_hash + lineage.  
5. Formal path cannot guess: `--contracts-file` required. `catalog.py` remains draft/unit-test only.  
6. No PENDING/None experiment_id in 48 formal jobs.  
7. FAM-PERSISTENCE-0001 is not formal HYP-0001. Guard rejects it.  
8. Yes — continuation_mean vs 0 exported; baseline_mean 0 on continuation arm.  
9. Final OOS still denied.  
10. V11.7 not touched.  
11. 8002–8005 not stopped.  
12. No order_send.  
13. Yes — four Xaviers computed; Windows coordinated.  
14. Yes — 48/48 DETERMINISTIC.  
15. Yes — locked JSON + INDEX_FORMAL + formal result files.  
16. Engine now has a reusable contract→job→Xavier→lineage path for later factor mining. It is not yet a factor miner.  
17. This repair makes the research machine honest. It does not produce P&L. Next useful stage is factor/hypothesis discovery, not more profiling.

## CURRENT STATE

```
FORENSIC = PASS
ROOT_CAUSE = IDENTIFIED
14:11_CONTRACT = PRESERVED
CONTRACT_AUTHORITY = RESTORED
XAVIER_EXECUTION = PASS
LINEAGE = PASS
RESULT_SCHEMA = PASS
FINAL_OOS_GUARD = PASS
V11.7 = UNTOUCHED
SIDECARS = UNTOUCHED
ORDER_SEND = NONE
PROFITABILITY_ALIGNMENT_AUDIT = COMPLETE
HYP-0001_TRADING_CLAIM = NONE
ANNUALIZED_10PCT = NOT_PROVEN
```
