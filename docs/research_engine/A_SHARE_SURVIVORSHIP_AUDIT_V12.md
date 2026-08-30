# A-share survivorship audit V12

**Date:** 2026-08-30

- Vendor equity delisted rows: **337**
- Census done: **True**
- With bars: **335**
- Empty: **2**
- Empty rate: **0.005934718100890208**

Live membership: `sh.600005` present 2016-12-30, absent 2017-03-01 (`outDate=2017-02-14`).
`sz.000003` has 2698 bars 1991-07-03 → 2002-06-14. Empty if queried only 2010–2018.

A 12-name sample all had bars. That is not a substitute for the 337 census.

Empty names (no vendor bars from ipoDate to outDate): sz.000033 (1994-01-03→2017-07-07), sz.000038 (1994-08-08→2023-07-12)

If empty rate is high: `SURVIVORSHIP_BIAS_RISK` and `A_SHARE_UNIVERSE_NOT_READY`.
Vendor table is not an exchange official delist tape. Residual risk remains.
