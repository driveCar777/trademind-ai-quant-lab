# Regime Transition V0.9 — Test Framework (docs)

Design only. 2026-08-26.  
This is the test **contract**. Do not add tests or runner code in this documentation mission.

When implementation is approved, tests go under `tests/research_engine/` and must keep the existing suite green (currently 80 PASS).

---

## Executive Summary

V0.8 的教训：hash、1993、worker 不能加 ID、OOS raise、交叉节点 content_hash — 这些要原样搬到 V0.9。  
另外必须测一件 V0.8 没有的事：**信号是 Δstate，不是状态水平。**

---

## Current Evidence

Existing guards already in tree: `ContractMismatch`, `FinalOosAccessDenied`, V0.5 ADX14 lock, V0.6 cost/fill, V0.8 worker-cannot-add.

V0.9 must not weaken those.

---

## 1. Unit tests (implement later)

| id | assert |
| --- | --- |
| T1 | `canonical_search_space_hash() == 3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea` |
| T2 | space has exactly 3 IDs: RT-0001/0002/0003 |
| T3 | job with HYP-RT-0004 or HYP-XA-0001 raises |
| T4 | `final_oos` role or path raises; no target return read |
| T5 | VOL percentiles freeze on RESEARCH; changing VALIDATION bars does not change the freeze |
| T6 | future close mutation after t does not change `state[t]` or transition[t] |
| T7 | a bar that is HIGH vol but **not** a transition does **not** fire HYP-RT-0001 |
| T8 | a bar that is STRONG+UP but **not** an enter does **not** fire HYP-RT-0002 |
| T9 | hold_bars is 5; a 1-bar hold path does not exist in the worker |
| T10 | fill is next open, not close |
| T11 | overlapping signal while in hold is skipped, not stacked |
| T12 | same seed → same content_hash locally |
| T13 | window files exist and last 15% is not iterated for PnL |

Do not add a test that “finds a profitable hold”.

---

## 2. Local smoke (implement later)

Run all three hypotheses on GOLD/OIL D1 RESEARCH+VALIDATION only.  
Must print occupancy and n_trade.  
If n_trade is 0, still a legal smoke (then Xavier will confirm INSUFFICIENT).

Smoke ranking must not touch Final OOS.

---

## 3. Four Xavier (implement later, not this task)

Preflight: SSH, Python 3.6.x, disk.  
Collect: result, content_hash, runtime, node info.  
01 vs 04 hash match required.

---

## 4. Audit questions (same as V0.8)

After a real run the report must answer, without excitement:

1. Candidate?  
2. Three labels: SUPPORTED / WEAK_SUPPORT / INCONCLUSIVE / FALSIFIED  
3. Cross-target repeat?  
4. After cost?  
5. FDR?  
6. Distance to 10% vs path benchmark  

If no edge: freeze failure. Do not change hold / ADX / VOL cuts.

---

## Decision

测试框架已锁。本任务 **不** 把它们写成 `.py`。  
下一批准的实现任务才许动 `research_engine/`。

---

## Next Automatic Action

更新治理入口（CONTEXT / TODO / CHANGELOG / AGENTS / PROJECT_STATUS / DECISIONS），标明：地图与 V0.9 合同已锁、**未跑**。仍不改冻结实验结果，不跑 Xavier。
