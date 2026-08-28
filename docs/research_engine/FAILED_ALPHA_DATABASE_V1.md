# Failed Alpha Database V1

Machine-adjacent to the backlog (killed rows score 0).  
Do not edit frozen result JSON to “fix” a row.

```text
FAIL(mechanism, universe, cost, horizon)
  ≠ FAIL(all alpha)
```

Repeating a killed row with a new indicator name is forbidden.

---

## HYP-0001 — FAM-MOMENTUM-0001

**What was claimed:** After three same-sign closed bars, the next return is displaced.  
**Why it failed as money:** WEAK_SUPPORT is a family rollup, not a costed book, not two-dataset CANDIDATE, not 10%.  
**What actually died:** short-horizon persistence as a *trade*.  
**Do not repeat:** streak 2/4/5, RSI as a streak, a second HYP-0001.  
**14:11 hashes:** immutable.

## FD V0.1 — 57 factors

**What was claimed:** Unconditional technical features shift next return.  
**Why it failed:** FDR m=876, discoveries=0, PROMISING=0, CANDIDATE=0.  
**What actually died:** single-series factor farm (momentum/reversal/breakout/vol-as-direction/tick/spread/toy MTF).  
**What did not die:** vol *clustering* as magnitude (PARTIAL, not a direction).  
**Do not repeat:** add RSI/MACD to the 57. Do not edit `FACTOR_SEARCH_SPACE` to “update” XASSET DRAFT (V0.8 already ran that idea elsewhere).

## V0.5 — state + 15 sketches

**What was claimed:** Inside a Market State, a tiny rule has next-bar edge.  
**Why it failed:** `NO_USEFUL_STRATEGIES_FOUND`.  
**What actually died:** **level** conditioning + 1–3 bar sketches.  
**What did not die:** the state *recipe* (still the V0.9 measuring stick).  
**Do not repeat:** ADX period search, “always long in UP”.

## V0.6 — costed sleeves

**What was claimed:** TF / MR / MOM after spread+5bp+10bp+0.5% risk is a strategy candidate.  
**Why it failed:** program CANDIDATE=0. Same-symbol three-sleeve book negative on all four D1.  
**What actually died:** 5–8 bar holds with high occupancy; overlay-as-profit; fake diversification.  
**Near-miss:** OIL D1 MOM CAGR ≈ +0.13–0.23%, Sharpe ≈ 0.08, one dataset.  
**Do not repeat:** retune OIL hold/N/cost to mint a second hit. Do not annualize M15 weeks.

## V0.8 — lagged dollar proxy

**What was claimed:** Big USDJPY/EURUSD day changes next GOLD/OIL after cost.  
**Why it failed:** 3/3 FALSIFIED, FDR 0/3, both windows lost money, high occupancy (~1/3 of days).  
**What actually died:** *next-aligned-row* dollar-proxy + 1-day hold + V0.6 costs.  
**What did not die:** same-bar gold/USD correlation (diagnostic only).  
**Do not repeat:** XA-0004, flip signs, change 67%, cheapen cost, trade the correlation on the same bar.

## V0.9 — Regime Transition

**What was claimed:** Δstate (VOL_SHOCK / ENTER_STRONG_UP / EXIT_STRONG) has a 5-day costed edge.  
**Why it failed:** Program `NO_CANDIDATE`. 0001 FALSIFIED (research TR<0, validation sign flip). 0002/0003 INCONCLUSIVE (validation n<4, RESEARCH not profitable). FDR 0/3. Occupancy 0.9–2% so the definition was actually a transition.  
**What actually died:** pre-registered 5-day Δstate on GOLD/OIL D1 after V0.6 costs.  
**What did not die:** V0.5 state *labels* as a measuring stick.  
**Do not repeat:** HYP-RT-0004, ADX 20/30, hold 3/8, VOL 20/80, “stay short while HIGH”.

## V0.91 — GOLD/OIL residual

**What was claimed:** log(GOLD/OIL)−SMA60 extremes fade over 5 aligned days.  
**Why it failed:** `NO_CANDIDATE`. Costed two-leg TR<0. 0001 perm p=0.072, BH not a discovery.  
**What actually died:** residual-percentile fade as a *book*.  
**What did not die:** a slow common factor might still exist; it did not pay after cost.  
**Do not repeat:** flip rich/cheap, drop SMA to 20, drop a leg to “make TR>0”.

---

## Process failures (refuse, do not “test”)

| id | attempt | response |
| --- | --- | --- |
| RB-0049 | cheapen cost after seeing red | reject job |
| RB-0050 | scan hold 3/5/8/10 after Δstate fail | new version only |
| — | read Final OOS to confirm | raise |
| — | MT5 / order_send | refuse |

---

## Decision

This database is the memory of the pipeline.  
A new family must cite at least one row in `Not:`.

## Next automatic task

Do not reopen V0.9 / V0.91. Calendar remains UNKNOWN. Do not write a strategy.
