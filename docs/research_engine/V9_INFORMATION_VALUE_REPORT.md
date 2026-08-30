# V9 Information Value Report

IS-A = MT5 only. IS-B = MT5 + free public / extra owned CFDs. IS-C = + Pack E futures. IS-D = all owned fusion.

## Incremental (best-of-layer, reporting sort only)

```
{
  "B_minus_A": {
    "incremental_cagr": -0.032781455086627886,
    "incremental_dd": 0.01617071955621968,
    "incremental_return": -0.1952855070662205,
    "incremental_sharpe": -0.08443136373960897
  },
  "C_minus_B": {
    "incremental_cagr": 0.024981939591502522,
    "incremental_dd": -0.15668879849814532,
    "incremental_return": 0.35288634995740065,
    "incremental_sharpe": 0.03560975816841905
  },
  "D_minus_A": {
    "incremental_cagr": 0.016377165149387585,
    "incremental_dd": -0.2956245114435482,
    "incremental_return": 0.09900146457025039,
    "incremental_sharpe": -0.1649017408800615
  },
  "D_minus_C": {
    "incremental_cagr": 0.02417668064451295,
    "incremental_dd": -0.15510643250162254,
    "incremental_return": -0.05859937832092976,
    "incremental_sharpe": -0.11608013530887157
  }
}
```

## Databento $31.82

This is incremental **research value**, not a dollar P&L claim.
Best-of-layer comparisons can pick LEVEL_LEAK / FALSIFIED leftovers. Databento added 0 Candidates and 0 Positive Reproducible Strategies.

```
{
  "added_information": "GC/CL official settlement, OI, volume, DTE/roll, plus V8 fusion with public series",
  "added_positive_research": 14,
  "added_strategies": 30,
  "candidate": 0,
  "historical_spend_usd": 31.816129,
  "incremental_vs_mt5": {
    "incremental_cagr": 0.016377165149387585,
    "incremental_dd": -0.2956245114435482,
    "incremental_return": 0.09900146457025039,
    "incremental_sharpe": -0.1649017408800615
  },
  "incremental_vs_public": {
    "incremental_cagr": 0.024981939591502522,
    "incremental_dd": -0.15668879849814532,
    "incremental_return": 0.35288634995740065,
    "incremental_sharpe": 0.03560975816841905
  },
  "new_spend_usd": 0.0,
  "note": "incremental research value, not dollar P&L value of $31.82"
}
```

## Leave-one-source-out

{
  "applied": false,
  "reason": "ALL_OWNED did not produce a positive reproducible strategy. Leave-one-out is attribution of a gain that did not occur."
}
