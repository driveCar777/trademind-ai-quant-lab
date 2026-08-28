# CROSS_METAL_V1 CONTRACT

search_space_hash: `ef6f3633e49de2b1f62657be638bb666ab7de1460021f6c0fc466a9bc2780df8`

Information: 252-day z of `log(GOLD_close / SILVER_close)` on overlapping D1 dates.

Parents:

- `tm-market-GOLD-D1-20260828-000001`
- `tm-market-SILVER-D1-20260828-000001`

Not V0.91 SMA60 residual. Not OIL. Not a z_cut search.

Knowledge: same-day closes, then NEXT_BAR_OPEN.

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-CM-0001 | SILVER | RATIO_RICH_CROSS (z > +2) | + |
| HYP-CM-0002 | GOLD | RATIO_CHEAP_CROSS (z < −2) | + |
| HYP-CM-0003 | GOLD | RATIO_RICH_CROSS (z > +2) | − |

Do not flip. Do not change z_cut. Do not reopen residual. Final OOS DENIED.
