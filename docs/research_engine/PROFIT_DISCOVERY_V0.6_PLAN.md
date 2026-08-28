# Profit Discovery V0.6 Plan

Executed 2026-08-26. Result: `WEAK_EDGE_ONLY`, program CANDIDATE=0. See `PROFIT_DISCOVERY_V0.6_REPORT.md`. Gates below were locked **before** the run and were not changed after OIL D1.

10% annualized is the **long-run capital target**, not a gate for this version.
This version asks: **is there a Strategy Candidate after cost and risk, or is this search space insufficient?**

Do not retune HYP-0001, FD V0.1, or V0.5 sketches. Do not touch Final OOS / MT5 / `order_send`.

## Phase 1 — already tested (do not repeat)

| search | result | do not repeat as |
| --- | --- | --- |
| HYP-0001 streak=3 continuation | WEAK_SUPPORT, not a book | streak 2/3/4/5 retune |
| FD V0.1 57 unconditional factors | NO_USEFUL_FACTORS_FOUND | RSI/MA/factor farms |
| V0.5 15 next-bar state sketches | NO_USEFUL_STRATEGIES_FOUND | always-long-in-UP, fade-EXTENDED next bar, p-value only |

Worth continuing: **state-conditioned trades with next-bar OPEN, holding, spread+fee+slip, sized risk, equity path**. That was not tested.

## Data limit (must say)

Each dataset has **2000 bars**.

- M15 ≈ weeks, not years. CAGR on M15/H1 is noisy.
- D1 2000 bars ≈ 8 years — the only span where CAGR is interpretable.
- CANDIDATE is **not** awarded from M15 CAGR.

## Money stack

```text
Market State → Strategy family → NEXT_BAR_OPEN execution
    → spread + 5bp + 10bp → 0.5%/1% risk, leverage cap 1x
    → research/validation equity → same-dataset portfolio
```

## Locked Market State (not a farm)

Axes reuse V0.5 recipes (SMA20/50, ADX14, ATR14/close, RET_5, tick_volume, spread). Event = NA.

Compact `state_id` examples:

```text
TREND_STRONG_LOWVOL
TREND_STRONG_HIGHVOL
TREND_WEAK_MIDVOL
RANGE_LOWVOL
RANGE_HIGHVOL
FRIC_WIDE
```

Direction UP/DOWN is stored separately for side. HIGH_VOL and FRIC_WIDE **block new entries** on all families (defensive overlay).

VOL cuts freeze on research 67/33, then apply to validation.

## Locked families (no parameter search)

| id | state | rule | hold | risk |
| --- | --- | --- | --- | --- |
| TF-BRK20 | TREND_STRONG, not HIGH_VOL/WIDE | close breaks prior 20-bar high/low with trend | 5 | 0.5% and 1% |
| MR-Z20 | RANGE_LOWVOL, not WIDE | fade \|z20\|≥1 | 5 | 0.5% and 1% |
| MOM-DIR | TREND_* and momentum agrees | hold with trend | 8 | 0.5% and 1% |
| DEF | overlay | skip HIGH_VOL and FRIC_WIDE | — | — |

Entry: **NEXT_BAR_OPEN**. Exit: open after holding, or 1.5×ATR stop. One position at a time. Stop distance from **signal bar** ATR (causal).

Notional capped at 100% equity. No infinite leverage.

## Cost (locked)

Per side: half spread (broker points rule locked in code) + 5 bp commission + 10 bp slippage.
Round-trip ≈ spread + 30 bp + path.

**Close fills are forbidden.**

## CANDIDATE (locked before seeing results)

All required:

- research total_return > 0 after cost
- validation total_return > 0 after cost
- research trades ≥ 8, validation trades ≥ 4
- research max DD ≤ 25%, validation max DD ≤ 30%
- largest \|trade pnl\| ≤ 50% of sum \|trade pnl\|
- same-sign total_return on ≥ 2 datasets

CAGR is reported. **CAGR ≥ 10% is not a pass rule.**

WEAK_EDGE: after-cost profit in one window or two datasets but fails a CANDIDATE clause.
NO_EDGE: otherwise.

`NO_EDGE` / empty candidate list is a legal program result.

## Xavier

- 01 GOLD ×4, 02 EURUSD ×4, 03 USDJPY ×4, 04 OIL ×4
- Windows: lock + dispatch + collect
- Worker: execute job list only
- Remote: `/tmp/tm-profit-discovery-v06`

## Portfolio

Per dataset: three 0.5%-risk sleeves (TF, MR, MOM), equal starting cash, defensive overlay on each. Combined equity is the book for that symbol. Cross-asset aligned book is **not** claimed (timestamps are not joined).
