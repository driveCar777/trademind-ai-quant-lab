# Data Sources

Unified adapter:

```text
source → fetch → normalize → timestamp → validate → hash → immutable dataset
```

Normalized observation fields:

- `timestamp_utc`
- `knowledge_timestamp_utc`
- `source`
- `asset`
- `field`
- `value`
- `revision`

Options add `expiry`, `strike`, `option_type`, `implied_volatility`, `delta`.
Futures add `contract`, `expiry`, `settlement`, `open_interest`, `volume`.

Do not jam every vendor into one semantic-free table. Use `record_type`.
Without a real file or credential, status is `DATA_BLOCKED` / `CREDENTIAL_REQUIRED`, never `READY_FOR_RESEARCH`.

V6 Databento: `databento.py` quotes `metadata.get_cost` then pulls L0 `ohlcv-1d` / `definition` / `statistics` only. No MBO/trades first. Ava CFD is not a future.
