# V14.1 Independent Capital Engine

Reference: `research_engine/cn_a_share_strategy_v14_1/capital_ref.py`.
It does **not** import `cn_a_share_strategy_v14.engine.simulate`. It does **not** read V14 `equity.csv`.

Path A = return-based `period_capital`. Path B = share-based `notional/open(t+1)`.
Same trade dates. Ending capital agrees to ~1e-7 or better.

Synthetic suite all_ok = **True**.

- All filled, zero raw → lose only locked RT.
- All unfilled → end = start, fees = 0.
- One of N filled → deploy 1/N, unfilled stay cash, unfilled fees = 0.
- Large loss recon holds.

| | H11 | H12 |
|---|---|---|
| Path A end | 834202.89 | 883505.87 |
| Path B end | 834202.89 | 883505.87 |
| Abs err | 4.505272954702377e-08 | 1.126900315284729e-07 |
| Same dates | True | True |
| Recon | True (abs 0.0) | True (abs 0.0) |
| Empty all-unfilled advances | 0 | 0 |
| No-pick advances | 0 | 0 |

Identity: starting capital + sum(trade net) = ending capital.
Daily MTM telescopes by construction. The economic recon is the trade ledger.

Benchmark is EW eligible open-to-open on the **same** 172 signal dates (not a purchased index). H11 bench end 0.7370. H12 bench end 0.7644. Same calendar as the strategy.

V14 published settled ends (834,202.89 / 883,505.87) match this independent engine. That is a check, not an input.
