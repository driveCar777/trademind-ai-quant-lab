# mt5_xs_v30 ¡ª MT5 US share-CFD cross-sectional price model (V30)

Contract: docs/research_engine/V30_MT5_US_XS_CONTRACT.md. Decision: V30_MT5_US_XS_DECISION.md (NO_CANDIDATE, MT5_STOCK_CFD_COST_CEILING).

- pull.py  freeze D1 + specs from the local terminal into data/market/immutable/tm-mt5-USSHARES-D1-20260905-000001 (never overwrites)
- run.py   panel, 7 fixed features, walk-forward LightGBM (V25 params), LS20/LO20 books with measured CFD costs, gates

Frozen. Do not re-run with different features/params/hold/books.
