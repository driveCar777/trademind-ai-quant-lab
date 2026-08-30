# A-share source stability V12.1

**Date:** 2026-08-30  
**Purchase:** NO  

V12 lost 138 as-of snapshots to empty `query_all_stock` while two BaoStock logins ran at once. One as-of stuck at `n_all=2000`.

## Rules now

- One `BaoSession` at a time. No second login.
- Transient errors: reset session, backoff, max 3 tries.
- Empty as-of is `DATA_ERROR` / `SOURCE_LIMIT`, never a zero universe.
- `2015-04-30` vendor snapshot stays **INVALID**. PIT listing-window count that day is **2695** (neighbors 2665 / 2736). Do not copy neighbors.
- Listing-window hashes match healthy V12 `query_all_stock` hashes on 2015-03-31, 2016-12-30, 2024-01-02, 2026-08-28.

Canonical source remains BaoStock. AkShare-class HTTP is still cross-check only.
