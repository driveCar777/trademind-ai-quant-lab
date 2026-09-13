# EXP-001 GOLD D1 own-price — write-once contract

> Frozen **2026-09-13 before any Phase 2 train/run**.  
> Experiment id: `EXP-001`. Market: Ava `GOLD` D1.  
> `candidate=false` until Candidate Gate V2 C0–C13 all pass. They do not.

## Question

Is there a **stable low-frequency directional edge** in Ava GOLD using only its own D1 OHLC, after spread + assumed slip + swap, with FLAT allowed?

This is **not** a retune of D1 V1–V5. Those families are `LEGACY_FROZEN` (baseline / negative control only). Do not change 252 / hold 10 / λ / k / 20-day V4 hold as a “fix”.

## Universe / data

- Symbol: broker `GOLD` (logical XAUUSD).
- Timeframe: D1 only.
- Source: existing `live/paper_hot/mt5_products/history/GOLD_D1.csv` + `GOLD_META.json` (read-only). Do not overwrite the frozen immutable pack `tm-mt5-MACRO-D1-20260905-000001`.
- Do not expand symbols.

## Locked split (do not evaluate FINAL OOS)

| Window | Dates | Use |
|--------|-------|-----|
| RESEARCH | first bar → **2025-09-11** inclusive | Official baseline + ladder evaluation |
| FINAL_OOS | **2025-09-12** → last available bar | **LOCKED. Do not score families on it. Do not pick thresholds on it.** |

Research-internal report split (not FINAL OOS): first 70% / last 30% of RESEARCH bars after warmup. Used only to report, not to search.

## Execution shell (unified)

- Signal at close[t] (PIT).
- Enter next D1 **open** (`t+1`).
- Time stop: **20** D1 bars; exit at open[t+1+20].
- Non-overlapping book. After a fill, next signal at `t_out`.
- FLAT is allowed and is the default when a rule does not fire.
- No forced always-in except the named Always-Long / Always-Short **controls**.
- Sizing for research books: **±1 or 0** (full unit). Not dollar leverage. Risk modes 0.25/0.50/1.00/2.00% are scenarios, not this book.
- Stops: baselines have **time stop only**. A Candidate (none yet) would also need a pre-registered risk stop. Do not add SL/TP after seeing numbers.

## Cost model (labeled)

From file META at contract time (must be replaced by live broker snapshot when collector succeeds):

- `point=0.01`, `digits=2`, `contract_size=100`, `volume_min=0.01`
- `spread_points_now=34` (file; **assumed current**, not each historical tick)
- `swap_mode=1`, `swap_long=-1.54`, `swap_short=0.64`, `swap_rollover3days=5`
- Slippage: **2 bp per side** (`0.0002`) — **ASSUMED**, same as frozen research books; validate later against deals
- Commission: **0** unless live deals show otherwise
- Bar spread: `max(bar_spread * point / px, 0.25 * now_spread_pct)` (same formula as V1 engine; **PARTIAL** use of today’s spread)
- Stress books: 1x / 2x / 3x on (spread+slip); Stress = 3x + extra 5 bp/side

Do not invent 100x leverage or a prettier spread.

## Pre-registered baselines (run before any new ML)

Hold=20, seed=25, lookbacks written here:

| id | rule |
|----|------|
| BUY_HOLD | One LONG from first research next-open to last research open; one round-trip cost |
| ALWAYS_LONG | Every decision LONG |
| ALWAYS_SHORT | Every decision SHORT |
| RANDOM | Uniform {LONG, SHORT, FLAT}, `random_state=25` |
| MOMENTUM | `sign(close[t]/close[t-20]−1)`; 0 → FLAT |
| MEAN_REVERSION | Opposite of MOMENTUM |
| BREAKOUT | Donchian 20: close > max(high[t-20:t]) LONG; close < min(low[t-20:t]) SHORT; else FLAT |
| VOL_FILTER | MOMENTUM only if ATR14/close > median(ATR14/close, last 60); else FLAT |
| TREND_FILTER | MOMENTUM only if close > SMA50; else FLAT |

## Model ladder (only after baselines frozen)

1. **Naive**: last 20-day return as score. Side: LONG if score > **+0.0020**, SHORT if score < **−0.0020**, else FLAT. Threshold = 20 bp, written **now**, not after seeing 0.63.
2. **Linear**: OLS walk-forward. Features (PIT, own-price only): `R20, VOL20, DIST_SMA50, RSI14, ATR14/close`. Label = next-20-day **open→open gross** (economic net is the book, not the fit target — disclosed). First pred bar 300, embargo 21, refit every 250. Same 20 bp FLAT threshold on predicted y.
3. Stop if Linear RESEARCH last-30% net TWR ≤ Naive or ≤ MOMENTUM, or t increment ≤ 0. **Do not** open Logistic / Ridge / LightGBM in this experiment if that happens.

## Gates

`VIABLE_HISTORICAL` is **not** Candidate. Candidate requires SPEC §30.5 C0–C13. Auto-trade only if all pass.

## Forbidden

Retune V4 252/20; reopen V1–V3 trees; use FINAL OOS; pick threshold after the run; LLM signals; `order_send`; write `:9000`; expand to H1/M15 inside this id (that is EXP-002).

## WHY / WHAT / EXPECTED / RISK

- **WHY**: Phase 1 showed own-price D1 ML falsified and V4 = gold beta, but there was no unified cost-aware baseline ladder on one schema.
- **WHAT**: Register then run the nine baselines; then Naive→Linear only.
- **EXPECTED EFFECT**: Honest monthly distribution and whether any rule beats buy-hold **net**. Likely: buy-hold dominates; active rules pay more cost.
- **RISK**: Treating V4-like 20-day hold as “new alpha”; leaking FINAL OOS; calling VIABLE_HISTORICAL a Candidate.
