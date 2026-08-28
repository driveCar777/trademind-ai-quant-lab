# Research Engine V0.5 Plan — Strategy Discovery Foundation

Prompt for Market State examples was cut off at 「例如：」. State labels below are **locked for V0.5**, not optimized.

## Money route (not another factor farm)

```text
Locked market data
    → Market State (regime)
    → State-conditioned signal
    → Strategy contract (entry / exit / holding / cost / risk)
    → Cost-aware validation
    → later: portfolio → Final OOS → paper → MT5
```

Annualized ≥ 10% (stable 10–15, mid 15–30, high 30+) is a **capital outcome after cost and risk**. It is not a Factor Discovery p-value or a state-occupancy p-value.

V0.5 builds the **foundation**. It does not trade. It does not claim 10%.

## Why not another unconditional factor pass

FD V0.1 asked: “does feature X, unconditionally, shift next return?”  
Answer under FDR: no useful directional edge.

The next question is strategy-shaped:

> In which **Market State** is a simple, pre-declared rule allowed to act, and does the **held return after cost proxy** still move?

That is not “try 10000 indicators”.

## Market State V0.5 (locked)

Each bar `t` gets a causal state from `<= t` only.

| axis | values | definition (one locked recipe) |
| --- | --- | --- |
| TREND | UP / DOWN / FLAT | UP: close>SMA20 and SMA20>SMA50. DOWN: inverse. Else FLAT |
| TREND_STRENGTH | STRONG / WEAK | ADX14 ≥ 25 → STRONG, else WEAK. Period 14 only |
| VOL | HIGH / MID / LOW | TR/close vs research 67/33 percentiles, frozen |
| LOCATION | EXTENDED / NEUTRAL | \|z_dist 20\| ≥ 1 → EXTENDED |
| MOMENTUM | POS / NEG / FLAT | sign of RET_5 |
| ACTIVITY | HIGH / LOW | tick_volume z20 ≥ 0 → HIGH. `volume_type=tick_volume` |
| FRICTION | WIDE / TIGHT / MID | spread z20 ≥ 0.5 WIDE; ≤ −0.5 TIGHT; else MID |
| EVENT | UNAVAILABLE | no news API |

`state_id` example:

```text
T=UP|S=STRONG|V=MID|L=NEUTRAL|M=POS|A=HIGH|F=TIGHT|E=NA
```

V11.6 涨/跌/震 is **not** this contract. Do not reuse mine_longrun.

## Strategy contract (schema now)

A V0.5 strategy is not “a significant factor”. It is:

```text
strategy_id
state_filter          # which Market States may act
signal_rule           # pre-declared, causal
entry                 # next closed bar only (offset +1)
exit                  # fixed holding in V0.5 (horizon 1 or 3)
holding
cost_rule             # RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY
risk_rule             # SKIP if FRICTION=WIDE; no sizing yet
status
```

Statuses: DRAFT / REGISTERED / TESTED / REJECTED / INCONCLUSIVE / CANDIDATE / PROMISING / ARCHIVED.

`PROMISING !=` tradable book `!=` 10% annualized.

`NO_USEFUL_STRATEGIES_FOUND` is legal.

## First search space (small)

About 12–20 pre-declared strategy sketches, e.g.:

- Momentum only if TREND=UP and STRENGTH=STRONG and FRICTION≠WIDE
- Fade EXTENDED only if TREND=FLAT and VOL≠LOW
- Skip / flat if FRICTION=WIDE (risk rule, measured as “no trade”)
- Follow MOMENTUM=POS only inside TREND=UP

No RSI-14/15/16 farm. No ADX period search. No HYP-0001 streak retune.

## Evaluation (reuse engine)

Same as FD: research freeze, validation apply, BH q=0.05, nulls, Final OOS denied, worker cannot invent strategies.

Metrics: n, delta, effect, raw_p, adjusted_p, hit_rate, economic_magnitude **return + bps**, cost_sensitive, occupancy (bars in state).

No magic score. Four ranks + status.

## Xavier

Partition by dataset (same as FD). New remote dir `/tmp/tm-strategy-discovery-v05`. Do not reuse HYP-0001 or FD remote dirs as authority.

## Explicitly later

Portfolio, position sizing, Sharpe/DD/Calmar as **selection**, paper, MT5, news events, ML.

## Allowed risk bands (documentation only)

Record intended book style on a strategy: STABLE / MID / HIGH. V0.5 does **not** assign a strategy to 10% or 30% from a p-value.
