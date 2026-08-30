# V12.2 START — Full panel completion and auto-advance

**Date:** 2026-08-30  
**Purchase:** NO  
**Alpha:** NO  

Keep the single raw-first BaoStock downloader running until **5549/5549**. Then automatically compile, audit, freeze, and run the ready gate.

- Do not start a second full downloader.
- `2015-04-30` vendor `n_all=2000` stays INVALID. Use PIT listing-window **2695**.
- New dataset_id: `tm-ashare-EQUITY-D1-20260830-000002` (does not overwrite 000001).
- Qfq is a later pass. Financial / industry stay BLOCKED.
- Supervisor: `scripts/research_engine_v12_2_run.py supervise`
- 2026-08-30 20:08: recorded `MULTIPLE_DOWNLOADER` (PIDs 8076 + 8692). Stopped orphan 8076 and three hung `2015-04-30` `query_all_stock` sessions. Kept 8692. Did not touch Xavier 8002–8005.
- C: free was ~13 GB (`C_DISK_LOW`). Large writes stay on D:. D: ~125 GB.
