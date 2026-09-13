# EXP-002 GOLD H1 + strict PIT — write-once contract

> Frozen **2026-09-13 before any Phase 2 H1 train**.  
> Experiment id: `EXP-002`. Market: Ava `GOLD` H1.  
> `candidate=false`. Own-price H1 V1–V9 are `LEGACY_FROZEN`. Do not retune hold=24 / SMA200-as-hours / ORB / Asia fade.

## Question

After unified costs and a three-state book, is there an **incremental hourly predictive edge** on GOLD H1 beyond the D1 buy-hold / EXP-001 baselines?

## Data

- Existing `GOLD_H1.csv` (read-only). Do not overwrite frozen D1 pack.
- H4/M15 may be pulled read-only into `data/market/research_engine/phase2/history/` if the terminal is up. **Not** a fishing expedition; no extra families.
- No MONTH/HOUR as **primary** regime. Clock features, if any later model uses them, must be disclosed as calendar memory risk (Phase 1 H1 overfit channel).

## Locked split

Same calendar lock as EXP-001: RESEARCH through **2025-09-11**; FINAL_OOS from **2025-09-12** — **do not evaluate families on FINAL OOS**.

## Shell

- Signal at H1 close[t]; enter next H1 open; time stop **24** bars; non-overlapping.
- FLAT allowed.
- Cost: same META swap (count **calendar midnights**, not 24 hourly swaps) + bar spread + **ASSUMED** 2 bp/side slip.
- Overlap: adjacent 24-bar labels share 23 bars. Training (if any) must purge/embargo. Official book is non-overlapping. See `OVERLAPPING_LABEL_AUDIT.md`.

## Baselines (same names as EXP-001, H1 scale)

Lookbacks: momentum/breakout **24**; vol median **72** hours; trend SMA **120** hours (5×24 — **not** “SMA200 days”). Seed 25. Hold 24.

ML (Naive→Linear→…) **only after** EXP-001 ladder rule is respected and this contract exists. If time is short, ship H1 baselines only.

## Forbidden

Restack 24h `sign` trees; copy H1 rules to M15; use last-month +18% as a gate; write Grok; `order_send`.

## WHY / WHAT / EXPECTED / RISK

- **WHY**: Phase 1 H1 trees overfit (train IC 0.52 / fold OOS 0.038) and net −35% to −67%. Need a clean baseline book, not another tree.
- **WHAT**: Unified H1 baselines on the locked research window.
- **EXPECTED EFFECT**: Active H1 rules lose to costs; buy-hold on H1 path still ≈ gold drift.
- **RISK**: Treating overlapping-label IC as evidence; calling session rules a new family.
