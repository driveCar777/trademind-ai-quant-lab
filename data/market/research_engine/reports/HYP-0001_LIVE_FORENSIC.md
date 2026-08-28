# HYP-0001 LIVE FORENSIC

Snapshot: `2026-08-25T16:15:48Z` (local 2026-08-26 00:15:48 CST).  
Observe only. No kill, no re-dispatch, no overwrite.

## A. Existing Preregistration

14:11 lock is on disk. File LastWriteTime `2026-08-25 22:11:58` (= `2026-08-25T14:11:58Z`). Not rewritten by the 22:59 scheduler.

| field | parent HYP-0001 | HYP-0001-A | HYP-0001-B |
| --- | --- | --- | --- |
| path | `data/market/research_engine/hypothesis/HYP-0001.json` | `hypothesis/HYP-0001-A.json` + `preregistration/HYP-0001-A.json` + `.md` | `hypothesis/HYP-0001-B.json` + `preregistration/HYP-0001-B.json` + `.md` |
| hypothesis_id | HYP-0001 | HYP-0001-A | HYP-0001-B |
| family_id | FAM-MOMENTUM-0001 | FAM-MOMENTUM-0001 | FAM-MOMENTUM-0001 |
| created_at | 2026-08-25T14:11:58Z | 2026-08-25T14:11:58Z | 2026-08-25T14:11:58Z |
| preregister_hash | **no parent prereg file** | `485d56a8f5a8e6822231760be240500ce6deb194471cde78172c3b5e4630b6d8` | `fbd14d199ba6390ac91f8700d48053ff75c99d7510183d58eeb1a101238cd3db` |
| status | LOCKED | LOCKED (hypothesis) | LOCKED (hypothesis) |
| metric | `continuation_mean = mean(streak_sign * horizon_return)` | same | same |
| benchmark | 0 (two-sided) | 0 | 0 |
| horizon | primary 1 / confirm 5 | 1 | 5 |
| streak | 3 | 3 | 3 |
| seed | (family default 20260825) | 20260825 | 20260825 |
| research window | protocol_70_15_15_candidate_research | same | same |
| validation window | protocol_70_15_15_candidate_validation | same | same |

Family file: `data/market/research_engine/registry/FAM-MOMENTUM-0001.json` (mtime 22:11:58). Variants: HYP-0001-A, HYP-0001-B.

There is **no** `preregistration/HYP-0001.json` for the parent. A/B prereg exist. That is the 14:11 layout.

## B. Scheduler

| field | value |
| --- | --- |
| PID (parent python) | **25012** |
| PID (child python) | **36392** (PPID 25012) |
| shell / terminal | PID **34524** / Cursor terminal 352088 |
| command | `"D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\.venv\Scripts\python.exe" scripts/research_engine_run.py` |
| cwd | `D:\AGXXAIVER-4-WINDOWS-1-STOCK` |
| start time | **2026-08-25 22:59:22** local |
| CPU / WS | 25012: CPU 0, WS ~4 MB (waiting). 36392: CPU ~9.6 s, WS ~45 MB |
| status | **RUNNING** — blocked on `paramiko.exec_command` waiting for four remote `node_runner.py` |
| stdout | terminal 352088 body empty (no flush while SSH waits) |

Call chain in `scripts/research_engine_run.py`:

```
main()
  → preregister()          # if hyp+prereg files exist → RE_PREREG_REUSE; no write
  → make_experiments()     # if experiments/*.json exist → RE_EXPERIMENT_REUSE; no write
  → ThreadPoolExecutor(4)
       → run_node(node)
            → SSH connect
            → rm -rf /tmp/tm-research-engine-v04 && mkdir
            → SCP research_engine/*.py + research_protocol/*.py
            → SCP each assigned dataset (bars.csv, manifest.json, DATA_QUALITY.json)
            → SSH: python3 research_engine/node_runner.py --node … --repeats 10 --datasets …
            → (after remote exit) SCP /tmp/.../out → data/market/research_engine/results/<node>
```

Evidence the 22:59 run **reused** 14:11 files: hypothesis / prereg / experiment / ALL_JOBS mtimes still `22:11:58`. The 14:57 run died on `write_once(HYP-0001.json)` and did not overwrite.

Xavier does **not** load those JSON contracts. `node_runner.py` `run_dataset()` hardcodes `variants = [hyp_0001_a(), hyp_0001_b()]` from `research_engine/catalog.py`. Lineage writes `experiment_id="PENDING"`, `preregister_hash="PENDING"`.

14:11 scheduler (terminal 352085, shell 36320) already exited `15:17:25Z`, all four `exit_1` (`jobs/datasets/manifest.json` missing). Not running now.

Master API: **no** `master/api` python process. Not part of this compute path.

Communication: **SSH** (paramiko), not HTTP to 8002–8005.

## C. Experiment

32 experiment files, all `tm-exp-20260825-141158-001` … `-032`.

| field | value |
| --- | --- |
| experiment_id range | `tm-exp-20260825-141158-001` … `032` |
| example | `tm-exp-20260825-141158-001` GOLD M15 / HYP-0001-A |
| status (on disk) | LOCKED |
| created_at | 2026-08-25T14:11:58Z |
| family_id | FAM-MOMENTUM-0001 |
| metric in 14:11 files | continuation_mean vs 0 |
| preregister_hash | A=`485d56a8…630b6d8` / B=`fbd14d19…238cd3db` |
| code_hash / protocol_hash | `9222ab65c752c33aaac31b2b561e76c3984896045adc449c7dac58a800b5d10c` |
| seed | 20260825 |
| dataset_count | 16 (each × A/B = 32 experiments) |
| job_count (manifest) | 48 |
| result_count (Windows `results/`) | **0** — collect happens only after remote SSH returns |

Live code mtime `22:58:15`–`22:58:57` is **newer** than the frozen `code_hash` `9222ab65…`. Warning, not a new experiment id.

## D. Job Summary

Windows `jobs/ALL_JOBS.json` (14:11, status field is contract lock, not runtime):

| | count |
| --- | --- |
| total manifests | 48 |
| per node | 12 |
| status on disk | all LOCKED |
| Windows queued/running/completed/failed | **not updated** |

Live runtime inferred from remote `/tmp/tm-research-engine-v04/out` at 16:15:48Z (each node 6 datasets × 2 variants = 12):

| | count |
| --- | --- |
| completed variant JSON | 21 |
| running (CPU ~99%, no new file this variant yet) | 4 (one per node) |
| queued remaining | 23 |
| failed this run | 0 observed |
| Windows collected results | 0 |

14:11 INDEX `job_count: 0` / all dispatch `exit_1` is the **first** run, not this one.

## E. Xavier Status

SSH 22: 200–203 `TcpTestSucceeded=True`. Hostname on all four is `xavier`; identity is `--node` + IP.

| node | ip | ssh | process | cpu | memory | temp | job_count | active_job |
| ---- | -- | --- | ------- | --- | ------ | ---- | --------- | ---------- |
| Xavier-01 | 192.168.1.200 | OK | research PID **20142** PPID 20129 etime 52:28 | 99.6% / load 2.05 | 0.0% RSS (ps) | CPU-therm **38.5C** / freq 2265600 | assigned 12; done 4 | GOLD H4 (after H1 B @ 00:08:13) |
| Xavier-02 | 192.168.1.201 | OK | research PID **27283** PPID 27232 etime 01:15:32 | 99.5% / load 2.00 | 0.0% | CPU-therm **39.5C** / 2265600 | assigned 12; done 7 | EURUSD D1 B (D1 A @ 00:13:04) |
| Xavier-03 | 192.168.1.202 | OK | research PID **32247** PPID 32208 etime 54:56 | 99.7% / load 2.35 | 0.0% | CPU-therm **39.0C** / 2265600 | assigned 12; done 5 | USDJPY H4 B (H4 A @ 00:11:07) |
| Xavier-04 | 192.168.1.203 | OK | research PID **18789** PPID 18746 etime 54:59 | 99.7% / load 2.22 | 0.0% | CPU-therm **40.0C** / 2265600 | assigned 12; done 5 | OIL H4 B (H4 A @ 00:11:13) |

tegrastats: `Unknown command: --count` on these images. Used `/sys` thermal + `scaling_cur_freq`. Freq locked 2265600=min=max. No nvpmodel change.

Xavier-01 started later (~23 min behind 02). Consistent with `run_node` attempt retry (`rm -rf` then re-upload). Still computing. **Not idle.**

Sidecar (observe only; still listening 8002–8005):

| node | 8002 | 8003 | 8004 | 8005 |
| --- | --- | --- | --- | --- |
| 01 | 21551 | 14757 | 14953 | 15115 |
| 02 | 25084 | 7453 | 7608 | 7756 |
| 03 | 3106 | 11489 | 11596 | 11728 |
| 04 | 23544 | 17243 | 17351 | 17484 |

## F. Contract Consistency

**14:11 locked files (Windows): consistent with each other.**

All 48 ALL_JOBS rows: `family_id=FAM-MOMENTUM-0001`, `parent_hypothesis_id=HYP-0001`, seed `20260825`, protocol/code hash `9222ab65…`. Two prereg hashes only (A vs B). Same `experiment_id` on two nodes is the written `node_assignment` cross-check (GOLD on 01+04, EURUSD M15 on 02+03, etc.).

**Live Xavier compute: not executing those JSON contracts.**

| item | 14:11 lock | live `catalog.py` / node output |
| --- | --- | --- |
| family_id | FAM-MOMENTUM-0001 | catalog `FAM-PERSISTENCE-0001`; result JSON `FAM None` |
| experiment_id | tm-exp-20260825-141158-* | `EXP None` / lineage `PENDING` |
| preregister_hash | 485d56a8… / fbd14d19… | lineage `PENDING` |
| null / metric text | continuation_mean vs **0** | catalog: “conditional mean equals **unconditional mean**” |
| continuation arm in `persistence.py` | vs 0 | `_zeros` + `continuation_mean=mean(signed)` present on remote |
| exported result keys | should name continuation_mean | compact_arm has `conditional_mean`, **no** `continuation_mean` key |
| extra arms | not the locked primary | positive/negative vs baseline still computed |

Remote peek (continuation arm): `conditional_mean == delta` → baseline is 0 for that arm. So the **numeric** continuation test is vs 0. Identity (family / experiment_id / prereg hash / catalog H0 text / exported field name) does **not** match the 14:11 lock.

**CONTRACT_MISMATCH** on identity and catalog text. Continuation-arm math is vs 0.

## G. Duplicate Dispatch

16 extra ALL_JOBS rows share `(experiment_id, dataset_id)` across two nodes. That matches `node_assignment` in the 14:11 experiment files. Not the same job twice on one node.

Live: one `node_runner.py` per Xavier. No second research process per host.

No `DUPLICATE_JOB` (accidental same-node resend). Cross-check pairs are designed.

## H. Multiple Scheduler Check

| run | when | state now |
| --- | --- | --- |
| 14:11 `research_engine_run.py` | 14:11:57Z–15:17:25Z | **dead** (exit 1) |
| 14:57 `research_engine_run.py` | 14:57:25Z | **dead** (write_once) |
| 22:59 `research_engine_run.py` | 22:59:22 local | **one tree**: 34524 → 25012 → 36392 |

25012+36392 are parent/child of the same command, not two schedulers.

**Not MULTIPLE_SCHEDULERS.**

## I. Ports

Windows listen on 9000, 9100, 8002–8005: **empty** this snapshot. No Master API listener. Research Engine has no dedicated Windows port. Path is SSH 22.

Xavier 8002–8005: LISTEN on all four. Sidecar + research coexist. Research does not bind those ports.

## J. Logs

Windows:

- `logs/` directory: missing
- `data/market/research_engine/results/`: empty
- Cursor terminal 352088: **empty stdout**
- **NO_PERSISTED_LOG_FOUND** on Windows

Xavier: no growing `*.log` for this engine. Evidence is JSON under `/tmp/tm-research-engine-v04/out/` writing about every 10 minutes. Last writes at snapshot: 01 00:08:13, 02 00:13:04, 03 00:11:07, 04 00:11:13 (local). Combined with ~99% CPU → files still advancing, not frozen.

Raw SSH dump (observe): `tmp/hyp0001_xavier_forensic.txt`.

## K. Final Assessment

CONTRACT_MISMATCH

Liveness (not the K token): four Xaviers are computing; Windows scheduler 25012/36392 is waiting on SSH; not STALLED; not NOT_RUNNING; not DISPATCH_FAILURE for the 22:59 run. 14:11 compute itself failed earlier.

Why not RUNNING_CORRECTLY: Xavier runs later `catalog.py` (FAM-PERSISTENCE-0001, unconditional-mean H0), does not load 14:11 experiment/prereg JSON, result identity fields are PENDING/None, exported metric key is `conditional_mean`.

This report did not overwrite 14:11 files, did not create a second HYP-0001, did not change FAM-MOMENTUM-0001, V11.7, Master, Xavier workers, or start mine_longrun / order_send.
