# Regime Transition Execution Plan

Prepare only. **Do not run Xavier in this step.**  
Contract hash must stay `3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`.

---

## Data

| item | source | check before any job |
| --- | --- | --- |
| GOLD D1 | `tm-market-GOLD-D1-20260825-000001` | sha256 `49291ffd…e899` |
| OIL D1 | `tm-market-OIL-D1-20260825-000001` | sha256 `a22e4213…8d72` |
| Windows | 70/15/15 on **that** series’ dates | write `WINDOW.json` before PnL |
| VOL freeze | RESEARCH 33/67 of TR/close | one freeze |
| Final OOS | last 15% | existence only; iterate → fail |
| EURUSD/USDJPY | not in space | do not load as features |

Do not use the 1993 four-asset pack as the V0.9 clock (it drops target days).

---

## Runner (Windows)

New package (when approved): `research_engine/regime_transition/`  
Copy the V0.8 pattern, do not fork V0.8 jobs as authority.

```text
space.py      reproduce hash or abort CONTRACT_MISMATCH
state_delta   ENTER_STRONG_UP / EXIT_STRONG / VOL_SHOCK only
evaluate.py   NEXT_BAR_OPEN, hold=5, V0.6 cost/size, overlap skip
jobs.py       01=0001 02=0002 03=0003 04=0001 CROSS_CHECK
rank.py       BH m=3; CANDIDATE needs GOLD and OIL and FDR
```

Remote dir (later): `/tmp/tm-regime-v09`  
Do not reuse `/tmp/tm-cross-asset-v08` as authority.

Script (later): `scripts/research_engine_regime_v09_run.py`  
`--mode smoke` local → `--mode full` four Xavier.

---

## Worker (Xavier)

Python 3.6 stdlib only.  
May compute the three listed ids.  
Must raise on unknown id, hash mismatch, Final OOS path, `order_send`.  
Must not add HYP-RT-0004.

---

## Result

Per job: lineage, n_trade, occupancy, TR, CAGR, DD, Sharpe, delta, d, CIs, raw_p, contemporaneous **level** diagnostic (not a gate), `content_hash`.  
Windows writes `REGIME_RANKING_V0.9.json`.  
Path benchmark: unconditional same-side and long-only GOLD/OIL.

If occupancy on 0002 looks like “half the days”: fail the job (definition leaked to level).

---

## Validation

Tests already specified in `REGIME_TRANSITION_V0.9_TEST_FRAMEWORK.md` (T1–T13).  
Write them in the implementation task, not now.  
Keep `tests/research_engine` green (now 85 with the pipeline suite).

Labels: same as V0.8 — FALSIFIED / INCONCLUSIVE / WEAK_SUPPORT / SUPPORTED.  
Program: CANDIDATE / WEAK_EDGE / NO_CANDIDATE.  
Level 1 gate: `CANDIDATE_ACCEPTANCE_GATE_V1.md` (not CAGR≥10%).

---

## Audit

After a future run: report + freeze file, hashes, 01=04 content_hash, no retune.  
If no edge: record. Do not change hold/ADX/percentiles.

---

## Decision

Preparation is complete enough to implement.  
This file is **not** permission to SSH. Residual family is not in this run.

## Next automatic task

Lock the second family on paper (`CROSS_RESIDUAL_V0.91_CONTRACT.md`).
