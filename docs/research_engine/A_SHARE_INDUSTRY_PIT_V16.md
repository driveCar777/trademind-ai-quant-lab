# V16 Industry PIT Report

Status: **INDUSTRY_PIT_OK**. Label: `MONTHLY_ASOF`.

`query_stock_industry(date=)` is historical as-of. The no-date call is CURRENT_ONLY and is not the freeze.
Do not backfill 2026 industry onto 2010 names. Taxonomy changed ~2015 (Chinese names → CSRC codes). Then-current labels only.

- download_complete: **True** (171 / 171 snapshots)
- PIT test: **True**
- n 2010/2015/2020/2024: 1926 / 2842 / 3854 / 5319
- 300750 absent 2010/2015: **True** / **True**
- Moutai labels: `{'2010': '制造业-饮料制造业-食品、饮料-酒精及饮料酒制造业', '2015': 'C15酒、饮料和精制茶制造业', '2020': 'C15酒、饮料和精制茶制造业', '2024': 'C15酒、饮料和精制茶制造业'}`
- 2015 vs 2024 label differ (common symbols): 638
- Future snapshot mutation: **True**
- INDUSTRY_ALPHA_READY: **True**

Incomplete monthly grid → DOWNLOAD_INCOMPLETE. No current-only fake PIT.
