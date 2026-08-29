# V5.1 Mission Report — 841 Symbol Exhaustion

2026-08-29. Level = 0. Candidate = 0. Final OOS not read. `order_send` not used. Leverage 1x.

## What was finished

1. **Inventory** — 841 / 841 from checkpoint (not from 0). Stage A = specification. Remaining listings after ~190 did not get M1×500k.
2. **Taxonomy** — path-first. All 841 are **CFD**. True options = 0. True futures = 0. `GOLD_FUTURE` / `SI_FUTURE` are named CFDs.
3. **Dedup** — `SYMBOL_EQUIVALENCE_MAP_V1.json`. 825 economic underlyings; most uniqueness is equity ticker names, not new objects.
4. **Stage B** — 22 interesting names only. Agricultural D1 ≈ 7.71y. `US_2000` D1 = 17.12y. VIX still 1.45y.
5. **New datasets** — `*-20260829-000001` for 7 ag + EUROBUND + JAPANBOND + US2000. Did not overwrite `20260825` or `20260828`.
6. **Top 1 then next** — `BREADTH_V1` then `SIZE_SPREAD_V1`. Both four Xavier. 01 = 04.

## Official answers

| Question | Answer |
|---|---|
| MT5 symbols discovered | 841 |
| How many of 841 are usable listings | 782 trade_mode=4; 19 disabled; 40 close-only |
| Independent underlyings | 825 names; **information sets** are far fewer (FX/metal/energy already used; 638 stocks = one equity-CFD class) |
| Max history | FX D1 still ~55y on majors (first-190 deep probe). New ag 7.71y. US2000 17.12y. Terminal maxbars = 100000 |
| New asset class | Agricultural CFD (7). Bond CFD (2). Equity/ETF CFD already inventoried in V4 |
| New timeframe | None. Same M1–MN1. No option surface |
| New information | Ag OHLC; US2000 17y; bond CFDs. Not options, not exchange futures, not order book |
| New mechanisms executed | BREADTH_V1, SIZE_SPREAD_V1 (after V5 Top 5) |
| Experiments | 2 families × 3 hyps × (local + 4 Xavier) |
| Candidate | 0 |
| Level | 0 |
| Obstacle to 10% | Still no Level 1. 10% is not a discovery gate |

## Decisions

- Do not retune BREADTH or SIZE.
- Do not run stock-CFD or index-breadth clones.
- MT5 remaining mass is suffix / `#` / `_` equity CFDs. That is not a new object.
- Stop condition: **EXTERNAL_DATA_GATE** / `PAYMENT_REQUIRED` for curve or option surface.

Spent $0. C: stayed above 20 GB. TEMP on D:.
