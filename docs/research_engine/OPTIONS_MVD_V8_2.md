# Options Minimum Viable Dataset V8.2

**QUOTE ONLY.** No download. No purchase. No formal options research family.

Pre-registered scope (locked **before** interpreting quotes; do not change after seeing prices):

- Strikes: nearest ATM, ±5%, ±10%
- Expiries: front, second; third only if front+second are jointly missing
- Roots phase 1: `OG.OPT`, `LO.OPT` monthly only
- Weeklies: not default
- History compared: 1Y / 2Y / 3Y ending **2026-08-29**
- AI must not change strike, expiry, hold, or sign after this quote

---

## OPTION_INCREMENTAL_DATA_REQUIREMENT

Owned GC/CL futures already give underlying price, realized vol, expiry, futures OI/volume/settlement.

Options MVD must add only:

| Need | Schema |
|------|--------|
| Identity (strike, expiry, C/P, underlying) | `definition` |
| Daily option price | `ohlcv-1d` close and/or `statistics` settle |
| Liquidity filter (optional) | `ohlcv-1d.volume` and/or `statistics` OI / cleared volume |

IV is **not** in the feed. If computed: **DERIVED Black-76**.

---

## Tiers

### MVD-A — definition + ohlcv-1d

**Must** for any options work.

| Question | Answer |
|----------|--------|
| Compute IV? | **CONDITIONAL DERIVED**. Needs a price bar + owned futures + r. No venue IV |
| ATM IV? | **CONDITIONAL**. Nearest listed strike must have an `ohlcv-1d` bar |
| Skew? | **CONDITIONAL**. ATM + OTM put + OTM call same expiry same session |
| Term? | **CONDITIONAL**. Front and second must both have a priced ATM that session |

Missing vs research-complete: official settlement, OI, bid/ask, venue IV.

Blocker: Databento prints **no ohlcv-1d row when there is no electronic trade**. Quiet OTM can vanish.

### MVD-B — MVD-A + statistics

Adds official settlement (`stat_type=3`), cleared volume (6), OI (9), session low offer / high bid (7/8). Still **no** GLBX IV (14) or delta (15).

Research-value increment: **high** for surface construction (theoretical settles on listed strikes that did not trade) and for an OI liquidity filter.

Cost increment is **asymmetric**:

| | 1Y statistics | 3Y statistics |
|--|---------------|---------------|
| OG.OPT | $40.79 | $70.77 |
| LO.OPT | $12.10 | $30.74 |

LO MVD-B 1Y = **$24.09** (still CASE A). OG MVD-B 1Y = **$55.79** (CASE B).

### MVD-C — definition + ohlcv-1d + bbo-1s

Only if A/B cannot answer the question. **Default buy = false.**

OG 1Y MVD-C = **$62,759**. One schema (`bbo-1s`) is already **$62,745**. This is not a research pack at a $93 balance.

`tbbo` (BBO at trade time) is cheap (OG 1Y $2.98, LO 1Y $6.66) but is **not** a bid/ask surface for untraded strikes. Do not treat tbbo as MVD-C.

---

## Exact quotes (parent, `stype_in=parent`)

End = `2026-08-29`. Full grid: `OPTION_QUOTE_V8_2.json`.

### MVD-A

| Symbols | 1Y | 2Y | 3Y |
|---------|----|----|----|
| OG.OPT | 14.994811 | 24.886548 | 32.413535 |
| LO.OPT | 11.991718 | 23.126337 | 34.224269 |
| OG+LO | 26.986529 | 48.012885 | 66.637805 |
| OG+OG1–5 | 16.933721 | — | — |
| LO+LO1–5 | 13.398051 | — | — |

`GC.OPT` / `CL.OPT` 1Y MVD-A: **fail** (unresolved).

### MVD-B

| Symbols | 1Y | 2Y | 3Y |
|---------|----|----|----|
| OG.OPT | 55.789747 | 83.612058 | 103.181225 |
| LO.OPT | 24.088709 | 43.605794 | 64.968166 |
| OG+LO | 79.878456 | 127.217852 | 168.149391 |

### Components (useful for two-step thinking)

| | OG 1Y | LO 1Y | OG 3Y | LO 3Y |
|--|-------|-------|-------|-------|
| definition | 11.629622 | 8.196081 | 22.880409 | 23.530837 |
| ohlcv-1d | 3.365189 | 3.795638 | 9.533126 | 10.693433 |
| statistics | 40.794936 | 12.096991 | 70.767690 | 30.743897 |
| trades | 1.789738 | 3.997858 | — | — |

Definition-first then filter to `instrument_class` C/P outrights, then price only those `instrument_id`s, is a **possible later** cost cut. It is a second quote after a definition purchase. This task does not buy the first step.

---

## History: 1Y vs 2Y vs 3Y

| Horizon | Can attempt IV/skew/term? | TradeMind validation risk |
|---------|---------------------------|---------------------------|
| 1Y | Yes, if occupancy holds | Thin. Occupancy and n-windows may fail the existing protocol |
| 2Y | Same schemas, more sessions | Still one-shot IS/OOS pressure; better than 1Y |
| 3Y | Same | Closest to prior research windows; **single-name MVD-A exceeds $30** |

Minimum **dollar** pack that can *attempt* both metals: **1Y OG+LO MVD-A $26.99**.

Minimum pack that adds **official settle + OI** under $30: **1Y LO MVD-B $24.09** (crude only).

Minimum 2Y one-commodity MVD-A: LO **$23.13** or OG **$24.89**.

Do not start at 16 years.

---

## Black-76 record (if IV is ever derived)

| Input | Source | Status |
|-------|--------|--------|
| Underlying futures | Owned GC/CL `front_settle` | Do not rebuy |
| Strike | `definition.strike_price` | Buy definition |
| Expiry | `definition.expiration` | Buy definition |
| Option price | `ohlcv-1d.close` or `statistics` settle | Buy price schema |
| Risk-free | Owned UST DGS10 | Proxy, not a matching curve |

Assumptions: American OG/LO ≈ European Black-76; no early-exercise premium; ohlcv close ≠ official settle; r is a proxy.

---

## DESIGN only — at most three hypotheses

Not a family. No search-space hash. No code. Do not open after seeing quotes.

Hold = next session after knowledge time. Sign locked. Strike/expiry locked to the pre-registered scope above.

1. **IV−RV.** Feature: front-month nearest-ATM Black-76 IV minus 20-session realized vol of owned front futures. Signal: feature above trailing median → next-session front future log return after cost is **negative**.
2. **Skew.** Feature: ±10% OTM put IV minus ±10% OTM call IV, same monthly expiry. Signal: feature above trailing median → next-session front future log return after cost is **negative**.
3. **Term.** Feature: second-expiry ATM IV minus front ATM IV. Signal: feature **below** zero (inversion) → next-session front future log return after cost is **negative**.

These are mechanisms, not edges. GVZ/OVX failure does not answer them. Buying data does not answer them either.
