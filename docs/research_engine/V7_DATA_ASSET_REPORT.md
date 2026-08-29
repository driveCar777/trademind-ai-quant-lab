# V7 Data Asset Report

```text
NO_NEW_PURCHASE = true
CREDITS_REMAINING_USD ≈ 93.18
BILLED_PACK_E_USD = 31.816129
PACK_E_PRESERVED = true
```

Inventoried frozen datasets: **110**.

| class | n | note |
|---|---|---|
| FREE | 107 | MT5 Ava CFD + public COT/EIA/rates/GVZ/OVX |
| PAID | 1 | `tm-fut-GLBX-CURVE-D1-20260829-000001` (Pack E slim curve) |
| DERIVED | 2 | OI-flow + volume-flow panels |
| FROZEN | all of the above | do not overwrite `20260825` / `20260828` / curve `000001` |

Pack E raw (`ohlcv-1d` / `definition` / `statistics`) remains on D:, gitignored. 60 files hash-checked. Re-purchase forbidden.

License: Databento historical bytes are internal research only. Research / Paper / Live / redistribution are not the same right.

Machine file: `data/market/research_engine/information_layer/DATA_ASSET_INVENTORY_V7.json`
