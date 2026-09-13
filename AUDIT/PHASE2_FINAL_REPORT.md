# PHASE2_FINAL_REPORT

> 2026-09-13. Evidence = Phase 1 forensic reports + live Ava snapshot + unified GOLD baselines + EXP-001 Naive→Linear.  
> Honest. Does not prove 20%. `candidate=false`.

## Q1 — Is there one MT5 trading system that should be making money?

**No.** Phase 1 (`STRATEGY_FORENSIC_REPORT.md`): Grok demo desk, V9 RSI manual, D1/H1 research graves, and V4 follow are **different** logics. Research scores never enter the Grok prompt. There is no single robot.

## Q2 — What actually has a directional edge on Ava GOLD?

**Unlevered long gold.** RESEARCH (2019-02-26→2025-09-11) daily close **+173%**, CAGR **13.2%**, path MaxDD **−21.4%**.  
D1 Always-Long 20-day rolls: net **+161%**, CAGR **13.1%**.  
D1 Momentum / mean-reversion / breakout / vol-filter / random: weaker or negative.  
H1 Always-Long (24h rolls, same costs): net **−30%**. Hourly turnover eats the drift.  
V4 12-month TSMOM (Phase 1): validation +84%, research **−10%**, worse than buy-hold. Not independent alpha.

## Q3 — After costs, is there an economic edge above holding gold?

**No among pre-registered active rules.**  
D1 BUY_HOLD open→open net **+171%** (one round-trip). Linear EXP-001 **+64%**. Naive **+17%**.  
H1 active books all net negative except the single buy-hold path.  
Assumed slip = 2 bp/side (labeled). Live spread **34 points**. Long swap **−1.54**/night.

## Q4 — Is execution the same as the backtest?

**No for the old auto path.** Grok uses M15 + market bid/ask, no time stop. Research uses next D1/H1 open + hold. Phase 2 SignalContractV2 is the shared schema going forward; it is **not** yet wired to a live executor. `TRADEMIND_HOT_GROK_SEND` defaults **off**.

## Q5 — Are the old backtests trustworthy?

**Arithmetic yes, economic story often no.** H1 1752 fills audited 0 mismatch. Failures are always-in, overlapping labels, and using the 2024–26 bull as a gate. New Phase 2 books use a locked RESEARCH window and do **not** score FINAL OOS (`2025-09-12`→end).

## Q6 — Is there a complete paper/demo ledger?

**Writers exist; live chain is incomplete.** `research_engine/phase2_mt5/ledger.py` implements signal→order→deal→position→close. There are **no** new Phase 2 live fills. Phase 1 already found `MT5_JOURNAL.json` missing. Terminal **51 deals** are stored under `MT5_GROUND_TRUTH/DEALS.json` (tickets, not a SignalContract map).

## Q7 — Do we have broker ground truth?

**Yes, a live snapshot (2026-09-13T09:27Z).** Leverage **400**, USD, demo, GOLD contract **100**, tick 0.01 / $1, spread **34**, swap −1.54 / +0.64, volume 0.01–150. Login masked. Not README 100×.

## Q8 — Can 20% per month be supported?

**UNSUPPORTED (Case C).** 79 RESEARCH months: median **+1.11%**, best **+10.7%**, **0** months ≥20%. Reaching 20% from a 1.1% median needs ~**18×** economic exposure; the −21% gold path then ruins the account. 100×-to-hit-20% is **UNSAFE**. True supported monthly center ≈ **1%** (CAGR ≈ 13%).

## Q9 — Did EXP-001 find a stable low-frequency own-price edge?

**No.** Baselines: only buy-hold / always-long are strongly positive. Linear beat Naive on RESEARCH last-30% (**+26 pp TWR**) but **lost to buy-hold** (+64% vs +171%) and the increment sits in the gold bull. Next layer **denied**. See `EXP001_LADDER_DECISION.md`.

## Q10 — Did EXP-002 find an incremental hourly edge?

**Baselines only; no ML (ladder rule).** H1 Always-Long **−30%** net. Momentum/breakout/filters negative. Buy-hold path still ~+123% open→open because it does not pay 1,591 round-trips. Hourly own-price **FALSIFIED as a cost-aware book**. Contract frozen; ML not opened.

## Q11 — Did EXP-003 run?

**Registered, not run.** EXP-001 did not produce incremental value vs buy-hold, so cross-asset ML is blocked. DXY/US500 may be missing on this terminal.

## Q12 — Should anything auto-trade?

**No.** Candidate Gate V2: C5/C9/C12 fail (`DO_NOT_TRADE`). Grok is not a strategy. V4 follow is display-only. `:9000` frozen.

## Q13 — What is frozen, and what is the honest status?

LEGACY_FROZEN: D1 V1–V5, H1 V1–V9, V30, V32, V4 follow, RSI manual, Grok-as-strategy. Do not retune 252/hold/λ/k. FINAL OOS locked. Monte Carlo scaffolded, unused.

---

## CURRENT STATUS

```
Strategy Edge: FALSIFIED
Economic Edge: WEAK
Execution: INVALID
Backtest: PARTIAL
Paper: INCOMPLETE
MT5 Ground Truth: AVAILABLE
20% MONTHLY TARGET: UNSUPPORTED
Candidate: FALSE
```

Notes on the labels:

- **Strategy Edge FALSIFIED** — active own-price rules do not beat long gold on the locked window; Phase 1 trees/sessions already falsified.
- **Economic Edge WEAK** — gold drift is real (~13% CAGR) but it is **beta**, not a signal; costs flip H1 always-in negative.
- **Execution INVALID** — live auto path ≠ research book; Phase 2 contract not connected to `order_send` (and must not be until C0–C13).
- **Backtest PARTIAL** — new baselines are write-once and split-locked; old V4 “viable” used the bull as a gate.
- **Paper INCOMPLETE** — schema yes; no `signal_id`↔deal map for a Phase 2 strategy.
- **MT5 Ground Truth AVAILABLE** — live spec + 51 deals + empty positions.
- **20% UNSUPPORTED** — not seen; leverage-to-20% is unsafe.
- **Candidate FALSE** — Gate V2 not all pass.

## Hashes (this session)

| Item | Value |
|------|-------|
| data_hash (GOLD_D1 + META) | `0684aa0d4c3836a800f07dbb6214ca0ad28a357a41bf783c09fc81bf65eaa3f9` |
| code_hash (`phase2_mt5/*.py` at run) | `a28863e0bd5634006190b10840f4bc0869c84ebfefa80dca863a7a08561edd73` |
| D1 baselines result_hash | `2fba7ad081b8a5507649dda86a3f086c9c04ab62a57f237a71186c7b2c3a3b3d` |
| H1 baselines result_hash | `48d4ccf22fe9cd03b430236333fff5f26890f513921162daa8401e609f901c82` |
| EXP-001 ladder result_hash | `d43b6ba9b52c99407051f8665bd51e126e5ac0bf5a4f23ef9e491c9a99b8fad4` |
