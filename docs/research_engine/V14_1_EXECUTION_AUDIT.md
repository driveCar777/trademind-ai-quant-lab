# V14.1 Execution Audit

| Check | H11 | H12 |
|---|---|---|
| Hold is 20 trading days | True | True |
| Signal gaps all 20 | {'max': 20, 'min': 20, 'n_not_20': 0} | {'max': 20, 'min': 20, 'n_not_20': 0} |
| Entry open(t+1) | True | True |
| Weight sum = 1 | True | True |
| Unfilled fees | 0.0 | 0.0 |
| Suspended fills | 0 | 0 |
| Limit-lock fills | 0 | 0 |
| Delist-during-hold fills | 0 | 0 |
| Last mechanical exit after denied start | ['2024-03-06'] | ['2024-03-06'] |

Unfilled H11 1.7470% (`{'DELISTED': 7, 'LIMIT_LOCK': 499, 'SUSPENDED': 1277}`). H12 1.8313% (`{'DELISTED': 11, 'LIMIT_LOCK': 511, 'SUSPENDED': 1308}`).

Breadth H11: elig median 2664.0, selected median 533.0, filled median 526.0, min selected 287. Collapse=False.
Breadth H12: elig median 2614.0, selected median 523.0, filled median 513.0, min selected 282. Collapse=False.

Liquidity (1e6 diagnostic book, not capacity): H11 P50/P90/P95 = 3.789888603600952e-05 / 0.00017425896805055362 / 0.0002651424239907953. H12 P50/P90/P95 = 3.6140346886487115e-05 / 0.00017300012973660327 / 0.0002633002487092021.

100 random fills (seed 20260831): `TRADE_FORENSICS.csv`. Full ledger stays on D: tmp.

Unfilled is 0 PnL, 0 cost, weight stays cash. No re-allocation. No phantom exposure. Limit-lock is not marked after the fact. tradestatus≠1 never fills. Delisting during the would-be hold is UNFILL — no last-price continuation.
