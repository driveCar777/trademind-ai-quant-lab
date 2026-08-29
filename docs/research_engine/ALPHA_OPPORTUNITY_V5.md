# Alpha Opportunity V5

Machine: `data/market/research_engine/ALPHA_OPPORTUNITY_V5.json`.

## What is actually new

1. **Agricultural CFD OHLC** — seven names, 7.7y D1. Tested as `BREADTH_V1`. KILLED (WEAK_EDGE).
2. **US2000 17y D1** — tested as `SIZE_SPREAD_V1` vs US500 → GOLD. KILLED (NO_CANDIDATE).
3. **Bond CFDs** — EURO-BUND / JAPAN_BOND. Rates family already killed on UST10. Not reopened.
4. **638 stock + 67 ETF CFDs** — new *listings*, not a new *object*. Same broker equity OHLC class.

## What is not on this terminal

- Listed options (strike / expiry / call-put)
- Exchange futures with roll
- Order book
- Futures curve / open interest
- Option surface / IV skew as a field

## Do not run

RSI, MA, MACD, Donchian, single-asset momentum/reversal/breakout, USD→GOLD, calendar rescue, XS_REV lookback change, CORR_SHOCK pctl search, energy crack pctl, GER40 pctl, stock-CFD breadth clone, index-breadth clone.

## Next

`EXTERNAL_DATA_GATE`. See `DATA_PURCHASE_CASE.md` and `V5_NEXT_DECISION.md`.
