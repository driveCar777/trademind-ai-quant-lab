# IMPLIED_VOL_V1 CONTRACT

search_space_hash: `f4bd4298a14eb0ac84cc7246319b4e3f323dc104583e5232902b8f289f5c3644`

Information: CBOE GVZ / OVX daily index. Not V0.9 realized vol. Not a z_cut search.

Parents:

- `tm-market-GOLD-D1-20260828-000001`
- `tm-market-OIL-D1-20260828-000001`
- `tm-alt-CBOE-GVZ-D1-20260828-000001`
- `tm-alt-CBOE-OVX-D1-20260828-000001`

Hypotheses (max 3):

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-IV-0001 | GOLD | GVZ z-cross > 2 | + |
| HYP-IV-0002 | OIL | OVX z-cross > 2 | + |
| HYP-IV-0003 | GOLD | GVZ−RV20 rich cross | + |

Frozen: hold=5, NEXT_BAR_OPEN, V0.6 cost, 70/15/15, FDR m=3 q=0.05, z_lookback=20, z_cut=2, rv=20, vrp_sd=100.

Knowledge: IV session date known at 21:00Z; trade uses NEXT_BAR_OPEN.

Final OOS: DENIED. Do not flip sign. Do not change z_cut.
