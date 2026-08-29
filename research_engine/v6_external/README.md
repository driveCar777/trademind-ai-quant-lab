# V6 External Exchange Data

Mission: move TradeMind off the broker CFD information set.

```text
catalog → quote → acquire L0 daily/definition/statistics → TERM_STRUCTURE_V1
```

- Adapter: `research_engine/data_sources/databento.py`
- No key → `CREDENTIAL_REQUIRED`. No fake READY.
- First schemas: `ohlcv-1d`, `definition`, `statistics` on `GC.FUT` / `CL.FUT`.
- Forbidden first pass: MBO, trades, BBO.
- Ava GOLD/OIL is not a future.

Human: put `TRADEMIND_DATABENTO_API_KEY` in `.env`, then run
`scripts/research_engine_v6_acquire.py`.
