# `data/market/cn_a_share`

China A-share research factory. Large files stay on D:. Git holds catalogs, manifests, and small reference tables.

```text
raw/                 immutable vendor pulls (gitignored)
normalized/          versioned, never overwrite an old dataset_id
reference/           calendar, basic, universe counts
corporate_actions/
financial/           sample only in V12; not RESEARCH_READY
announcements/
manifests/
quality/
research/
```

Machine catalogs:

- `A_SHARE_DATA_CATALOG_V12.json`
- `A_SHARE_UNIVERSE_HISTORY_V12.json`
- `A_SHARE_DATASETS_V12.json`
- `A_SHARE_PIT_TEST_V12.json`
- `A_SHARE_SOURCE_MATRIX_V12.json`

Do not commit credentials. There are none for BaoStock.
