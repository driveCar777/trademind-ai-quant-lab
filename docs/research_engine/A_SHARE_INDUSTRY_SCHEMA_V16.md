# V16 Industry Schema

Monthly as-of from BaoStock `query_stock_industry(date=)`.

| Field | Meaning |
|---|---|
| symbol | code |
| industry | Then-current label |
| industry_classification | Vendor scheme (证监会行业分类 after ~2015) |
| effective_date | Query date (15th of month). Knowledge time |
| source_update_date | Vendor updateDate on that snapshot |
| pit_available | True on monthly grid |

Do not use the no-date call as history. Taxonomy changed ~2015. Use then-current labels.
No industry × momentum × low-vol factory.
