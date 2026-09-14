# EXP-009 Pre-registration Audit

**Date:** 2026-09-14  
**Read-only first.** Then contract freeze only. **No train. No book. No `order_send`.**

```
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
EXP-008: BLOCKED
EXP-009: PREREGISTERED / READY_TO_RUN
```

Source commit for the frozen pack: `b068262f9211a9b91a8931c533d727396f9b74fa`.

---

## Audit (before any write)

Read: TIPS spec, acquire report, `EXP009_DATA_MANIFEST.json`, Phase 3 plan, `MULTIPLE_TESTING.md`, EXP-001 contract, SPEC §30.2–30.6, `research_engine/phase2_mt5/contract.py`, `git log -5`.

### CURRENT_MODEL_STATUS

**There is no EXP-009 model.** Nothing is trained. Phase 2 Linear/Naive are **own-price** graves (`NO_INCREMENTAL_ALPHA` vs BUY_HOLD). They are not this experiment.

A future EXP-009 “model” under the contract is a **pre-registered sign transform** of knowledge-aligned DFII10, outputting a **score** (not BUY/SELL).

### CURRENT_STRATEGY_STATUS

**There is no EXP-009 strategy book.** Infrastructure exists:

- SignalContractV2 `side ∈ {LONG, SHORT, FLAT}` (`SPEC.md` §30.2, `phase2_mt5/contract.py` `SIDES`)
- EXP-001 shell: signal at close[t], fill next open, hold **20**, non-overlap, FLAT allowed
- Phase 3 plan one-liner for EXP-009 (hold 20, FLAT, BUY_HOLD, m+1) — **incomplete** until this freeze

### CURRENT_POSITION_POLICY_STATUS

Research books: ±1 or 0 unit, time-stop 20. **No account risk engine.** Hot-desk `HOLD` is a **different enum** (keep Grok position). Not used here.

### Existing enums — do not invent a parallel set

| Surface | States | Use for EXP-009? |
|---------|--------|------------------|
| SignalContractV2 / Phase 2 baselines | `LONG` / `SHORT` / `FLAT` | **Yes** |
| `phase2_mt5` `HOLD = 20` | horizon bars, **not** a side | Cite as hold length only |
| Hot desk SPEC §29.12 | `BUY` / `SELL` / `FLAT` / `HOLD` | **No.** Desk observer. Do not merge |

**CONFLICT FOUND (documented, not overwritten):** hot-desk `HOLD` ≠ research `FLAT`. EXP-009 uses **only** `LONG|SHORT|FLAT`. `FLAT` = ABSTAIN / NO_POSITION. Exit is time-stop (or a later pre-registered risk stop), not desk `HOLD`.

### Layers (must stay separate)

| Layer | What it is here |
|-------|-----------------|
| **Model / signal** | Score = −Δ DFII10 (20 decision bars). Not BUY/SELL. |
| **Strategy** | Cost-aware map score → LONG/SHORT/FLAT |
| **Position policy** | When a position is on; fixed horizon 20; allowed transitions |
| **Risk** | Research size ±1/0; no 400×; live Candidate still needs a risk stop (C9 / P3-G12) |

---

## A–P answers

| | Question | Answer |
|--|----------|--------|
| A | Current model? | **None running.** Contract defines one sign transform. |
| B | Current strategy? | **None running.** Mapping is in `docs/research_engine/EXP009_PREREGISTRATION.md`. |
| C | Layered? | **Defined in contract.** Not implemented as a live stack. |
| D | LONG allowed? | **YES** |
| E | SHORT allowed? | **YES** |
| F | FLAT allowed? | **YES** (required) |
| G | FLAT meaning? | Expected tradable edge insufficient after costs / missing feature / zero change — not “must trade today” |
| H | Prevent forever-FLAT? | **Diagnostics + degenerate review.** No post-hoc min-trade% |
| I | Tune frequency after results? | **NO** |
| J | Benchmark? | **GOLD BUY-HOLD**, same window / 1× capital / Phase 2 costs |
| K | Primary success? | Incremental **net** TWR vs BUY_HOLD on RESEARCH 70 **and** 30 |
| L | 20%/month in optimizer? | **NO** (aspiration only) |
| M | PIT frozen? | **YES** `knowledge_time_utc <= decision_time_utc` |
| N | Dataset hash frozen? | **YES** `790b6d725a0d170b7e701f85880bbb57515a9033634ec02d0d9633fcf7fe7b1f` |
| O | Multiple testing first? | **YES** — this file’s registry update is **before** any run |
| P | Train/backtest this round? | **NO** |

---

## Allowed / forbidden one-liners

```
允许空仓 = YES
强制持续交易 = NO
允许无限期空仓而无需诊断 = NO
```

---

## What this audit does **not** do

No EXP-009 engine. No scores. No Xavier. No LightGBM/Ridge bake-off. No reopen of V9/V10/D1/H1/V4/RSI/Grok.
