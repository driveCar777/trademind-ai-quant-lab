# V9 Decision

STOP B: all legal strategy mechanisms replayed; no Positive Reproducible Strategy. Do not buy data. Next = model / information representation review.

Reporting 'best' rows use a pre-fixed sort (net return, then max DD, then Sharpe). They include historically FALSIFIED / LEVEL_LEAK leftovers. They are not Candidates and not a reason to retune.

## A-J

### A. MT5-only

RESEARCH_POSITIVE_NOT_CANDIDATE

### B. MT5 + public

RESEARCH_POSITIVE_NOT_CANDIDATE

### C. MT5 + futures

RESEARCH_POSITIVE_NOT_CANDIDATE

### D. ALL OWNED

RESEARCH_POSITIVE_NOT_CANDIDATE

### E. Databento incremental research value

{
  "historical_spend_usd": 31.816129,
  "new_spend_usd": 0.0,
  "added_information": "GC/CL official settlement, OI, volume, DTE/roll, plus V8 fusion with public series",
  "added_strategies": 30,
  "added_positive_research": 14,
  "incremental_vs_public": {
    "incremental_return": 0.35288634995740065,
    "incremental_cagr": 0.024981939591502522,
    "incremental_sharpe": 0.03560975816841905,
    "incremental_dd": -0.15668879849814532
  },
  "incremental_vs_mt5": {
    "incremental_return": 0.09900146457025039,
    "incremental_cagr": 0.016377165149387585,
    "incremental_sharpe": -0.1649017408800615,
    "incremental_dd": -0.2956245114435482
  },
  "candidate": 0,
  "note": "incremental research value, not dollar P&L value of $31.82"
}

### F. Best legal reporting strategy

{
  "strategy_id": "HYP-TSFUT-0001",
  "family": "TERM_STRUCTURE_V1",
  "information_set": "IS-C",
  "target": "next-session front contract log return after settlement knowledge_time",
  "net_return": 0.37679167076779163,
  "cagr": 0.02854458120463632,
  "max_dd": -0.16777598379382924,
  "sharpe": 0.48570376521008,
  "sortino": 0.15430376631381507,
  "economic_status": "POSITIVE_BUT_WEAK"
}

### G. Level 1 Candidate?

0

### H. If none, what is missing?

Existing locked mechanisms do not produce a Positive Reproducible Strategy after MT5 costs. The gap is not another simple price rule.

### I. Buy options now?

NO_PURCHASE

### J. If a human later buys

Only if a human later accepts a new family that needs OG/LO occupancy. V8.4 preferred pack remains LO 1Y MVD-A $11.99. Live book would need EXTERNAL_LIVE_DATA=YES.

## Hard stops

- NEW_DATA_PURCHASE = FALSE
- $93 credits = UNUSED_RESEARCH_RESERVE
- Do not retune killed families
- Do not read Final OOS
