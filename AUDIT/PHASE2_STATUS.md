# PHASE2_STATUS

> Living status. 2026-09-13 end of first Phase 2 session.

**Experiment ids:** EXP-001 / EXP-002 / EXP-003 only. `candidate=false`.

## Done

- [x] Wave A: SPEC §30; Grok send default off; EXP contracts; LEGACY_FROZEN marks
- [x] Wave B: collector + SignalContractV2 + ledger + smokes 42/43
- [x] Wave B: **live** Ava snapshot `AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json` (leverage 400, GOLD contract 100, spread 34)
- [x] Wave C: GOLD D1 + H1 unified baselines (write-once READ)
- [x] Wave D: EXP-001 Naive→Linear; increment vs Naive only; **lost to buy-hold**; next layer denied
- [x] Wave E: TARGET / leverage / overlap / multiple-testing / FINAL_REPORT
- [x] Wave F: `55920477` pushed to `origin/main`
- [x] Case File: `AUDIT/MT5_STRATEGY_CASE_FILE.md` (2026-09-14, independent review; no new runs)

## Blocked

- EXP-002/003 ML: blocked (EXP-001 no increment vs buy-hold)
- FINAL OOS from 2025-09-12: locked
- Candidate / Monte Carlo evidence: none
- H4/M15 baselines: not pulled (no fishing expedition)
- Paper `signal_id`↔deal: no Phase 2 live fills

## Next (later session)

1. Do **not** open Logistic or FINAL OOS.
2. Optional: map existing 51 terminal deals to a journal (forensic only).
3. EXP-003 only if a new **pre-registered** incremental test is justified — not because Linear beat Naive on a bull slice.
4. Keep `:9000` frozen. Keep Grok send off unless the owner sets `TRADEMIND_HOT_GROK_SEND=1` knowing it is not a Candidate.
