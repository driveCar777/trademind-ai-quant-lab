# Market datasets (Data Layer V0.1)

This tree is the only home for immutable OHLCV research data.

Do **not** mix with `data/mine/longrun/` (V11.7 falsify lab).

```text
data/market/
  immutable/     one directory per dataset_id (bars.csv + manifest + quality)
  manifests/     copy of each manifest.json for listing
  research/      reserved RESEARCH role pointers (V0.1 unused)
  final_oos/     LOCK.json only; FINAL_OOS_LOCKED = false
  raw/           reserved empty (no duplicate copies)
  validated/     reserved empty (no duplicate copies)
  logs/          DATA_FETCH_* event log
```

Storage policy: `single_immutable_copy`. See `STORAGE_POLICY.json`.
