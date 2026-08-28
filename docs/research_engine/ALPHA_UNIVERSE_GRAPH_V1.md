# Alpha Universe Graph V1

Rebuilt 2026-08-26 from `docs/`, `data/`, `research_engine/`, `tests/`.  
Not a table of wishes. A chain: source → data → capability → evidence → next action.

Machine ranking of 52 mechanisms: `data/market/research_engine/alpha_program/RANKING_V1.json`  
hash `1b2e65b3e9bdf9a03033bcd34f479ee9a7231037b6ee431b8fd49d08a9290bd6`.

---

```text
                    ┌─────────────────────────┐
                    │   Level 0 engine (DONE) │
                    │ contract Xavier stats   │
                    │ immutable OOS-deny      │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ Candidate count = 0     │
                    │ so Portfolio / Paper /  │
                    │ MT5 stay closed         │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   KILLED sources          UNKNOWN sources         BLOCKED sources
```

---

## Price formation (short-hold)

```text
Alpha Source
    same-bar-history → same-asset next 1–8 bars
Required Data
    any of 16 OHLCV files (HAVE)
Current Capability
    FD / V0.5 / V0.6 runners exist
Historical Evidence
    HYP-0001 WEAK_SUPPORT ≠ book
    FD 57 PROMISING=0
    V0.5 NO_USEFUL_STRATEGIES
    V0.6 WEAK_EDGE_ONLY, OIL leftover +0.23% CAGR
Next Action
    STOP. Failure DB. Do not reopen RSI/MA/Donchian/streak.
```

## Regime level (in-state filter)

```text
Alpha Source
    “while TREND_STRONG / HIGH_VOL …”
Required Data
    V0.5 state axes (HAVE)
Current Capability
    regime/state.py, ADX14 locked
Historical Evidence
    V0.5 sketches + V0.6 sleeves failed
    DEF overlay = 0 return
Next Action
    STOP as alpha. Reuse axes only as Δstate inputs.
```

## Regime transition (Δstate)

```text
Alpha Source
    risk-budget / stop clustering at a STATE CHANGE
Required Data
    GOLD D1 + OIL D1 + SMA20/50 + ADX14 + VOL freeze (HAVE)
Current Capability
    state labels YES; Δstate runner NO
Historical Evidence
    never computed as a signal
    contract LOCKED_NOT_RUN hash 3ccb614d…6cea
Next Action
    KEEP as #1. Execute later per REGIME_TRANSITION_EXECUTION_PLAN.md
```

## Cross asset next-day dollar proxy

```text
Alpha Source
    USDJPY/EURUSD day-t → GOLD/OIL day-t+1
Required Data
    1993-day align pack (HAVE)
Current Capability
    research_engine/cross_asset/ ran on four Xavier
Historical Evidence
    NO_CANDIDATE, 3/3 FALSIFIED, FDR 0/3
    same-bar |r|≈0.43 is not a trade
Next Action
    STOP family. Do not add XA-0004. Do not flip signs.
```

## Residual / relative value (new)

```text
Alpha Source
    slow GOLD/OIL (or gold/dollar-basket) residual mean-reverts
Required Data
    GOLD+OIL D1 join (HAVE; do not need DXY)
Current Capability
    align code exists; residual family does not
Historical Evidence
    not tested. V0.8 tested a different object (1-day proxy)
Next Action
    #2 cluster (score 576). Paper contract CROSS_RESIDUAL_V0.91
    Do not run in parallel with V0.9.
```

## Calendar / weekend clock

```text
Alpha Source
    weekly human calendar concentrates information and inventory
Required Data
    D1 timestamps; Sunday bars FACT (HAVE)
Current Capability
    timestamps only; no calendar family
Historical Evidence
    untested. Month-end n is thin (~77)
Next Action
    #3 cluster (score 540). Design only after residual or if V0.9 dies.
```

## Risk overlay / portfolio

```text
Alpha Source
    vol-target a living sleeve; combine uncorrelated sleeves
Required Data
    ≥1 Level 1 curve (MISSING)
Current Capability
    sizing.py YES; combine.py is same-symbol fake book
Historical Evidence
    V0.6 equal-weight TF+MR+MOM all D1 negative
Next Action
    SLEEVE BLOCKED. Do not build a book engine now.
```

## Carry / VRP / event / order flow / session

```text
Alpha Source
    rate transfer / IV-RV / scheduled news / DOM / London-NY hours
Required Data
    rates, IV, event table, real_volume, long M15 (MISSING)
Current Capability
    none honest
Historical Evidence
    FD NEWS/XASSET drafts; never computed
Next Action
    DATA BLOCKED. Fetch later as new dataset_id. Not V0.9.
```

---

## What can still produce information

```text
unrun V0.9 contract ──► first new evidence
residual contract    ──► second family (different mechanism)
calendar contract    ──► third, thinner
failure database     ──► negative information (already)
longer history V0.2  ──► unlocks session, not this week
```

---

## Decision

Universe is not “more indicators”.  
It is three living arrows (transition, residual, calendar) and a wall of killed/blocked.

## Next automatic task

`RESEARCH_BACKLOG_V1.md` — 52 mechanisms, scored by the running pipeline.
