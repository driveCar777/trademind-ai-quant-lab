# V9 Master Backtest Report

Replay of existing locked mechanisms. No new hypotheses. No data purchase. Final OOS DENIED.

## Counts

- strategies_replayed: 103
- strategies_profitable (research net>0): 31
- strategies_loss: 76
- strategies_non_tradeable: 3
- POSITIVE_REPRODUCIBLE books: 0
- LEVEL_1_CANDIDATE: 0

## Best reporting row (pre-fixed sort: net return, then max DD, then Sharpe)

```
{
  "cagr": 0.02854458120463632,
  "economic_status": "POSITIVE_BUT_WEAK",
  "family": "TERM_STRUCTURE_V1",
  "information_set": "IS-C",
  "max_dd": -0.16777598379382924,
  "net_return": 0.37679167076779163,
  "sharpe": 0.48570376521008,
  "sortino": 0.15430376631381507,
  "strategy_id": "HYP-TSFUT-0001",
  "target": "next-session front contract log return after settlement knowledge_time"
}
```

## Layers

```
{
  "IS-A": {
    "best": {
      "cagr": 0.036344096699761685,
      "economic_status": "POSITIVE_BUT_WEAK",
      "family": "INSTITUTIONAL_TIME_V1.0",
      "max_dd": -0.027257904851903596,
      "net_return": 0.21919082787661148,
      "sharpe": 0.5345253707812699,
      "strategy_id": "HYP-IT-0002",
      "target": "OIL"
    },
    "information_set": "IS-A",
    "n_positive_research": 6,
    "n_research_books": 136
  },
  "IS-B": {
    "best": {
      "cagr": 0.003562641613133799,
      "economic_status": "POSITIVE_BUT_WEAK",
      "family": "ENERGY_RV_V1",
      "max_dd": -0.011087185295683916,
      "net_return": 0.023905320810390984,
      "sharpe": 0.45009400704166097,
      "strategy_id": "HYP-ER-0003",
      "target": "OIL"
    },
    "information_set": "IS-B",
    "n_positive_research": 12,
    "n_research_books": 45
  },
  "IS-C": {
    "best": {
      "cagr": 0.02854458120463632,
      "economic_status": "POSITIVE_BUT_WEAK",
      "family": "TERM_STRUCTURE_V1",
      "max_dd": -0.16777598379382924,
      "net_return": 0.37679167076779163,
      "sharpe": 0.48570376521008,
      "strategy_id": "HYP-TSFUT-0001",
      "target": "next-session front contract log return after settlement knowledge_time"
    },
    "information_set": "IS-C",
    "n_positive_research": 8,
    "n_research_books": 12
  },
  "IS-D": {
    "best": {
      "cagr": 0.05272126184914927,
      "economic_status": "POSITIVE_BUT_WEAK",
      "family": "FUT_CFD_LEAD_V1",
      "max_dd": -0.3228824162954518,
      "net_return": 0.31819229244686187,
      "sharpe": 0.36962362990120845,
      "strategy_id": "HYP-FUTCFD-0001",
      "target": "next-session broker CFD open-to-open after settlement knowledge_time"
    },
    "information_set": "IS-D",
    "n_positive_research": 6,
    "n_research_books": 18
  }
}
```

## Execution

TRADING VENUE = MT5. Fill = NEXT_BAR_OPEN. Bars are OHLC + spread points: EXECUTION_APPROXIMATION.
HYP-0001 and Factor Discovery and V0.5 are not strategy CAGRs.
