# GOLD M15 Snapshot Diff

- dataset_a: tm-market-GOLD-M15-20260825-000001
- dataset_b: tm-market-GOLD-M15-20260825-000002
- overlap: 2026-07-24T19:00:00Z -> 2026-08-25T12:45:00Z
- same_rows: 1999
- changed_rows: 1
- added_rows: 0
- removed_rows: 0
- changed_columns: close=1, tick_volume=1
- first_changed_timestamp: 2026-08-25T12:45:00Z
- last_changed_timestamp: 2026-08-25T12:45:00Z
- HISTORICAL_MUTATION: false
- historical_mutation_count: 0

The only difference is the last bar `2026-08-25T12:45:00Z` (forming / latest bar):

- 000001 close 4639.79 tick_volume 2934
- 000002 close 4640.23 tick_volume 2984

Open / high / low / spread unchanged. No closed-history OHLC mutation. Neither snapshot was overwritten.
