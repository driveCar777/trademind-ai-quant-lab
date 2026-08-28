# POSITIONING_V1 CONTRACT

search_space_hash: `4a1240f6059172baf283576aac082b0c62e0a0f56e5dae108e082dd76496caec`

Information: CFTC disaggregated COT. Tuesday as-of, Friday 21:00Z knowledge. Not V0.8 price proxy.

Parents:

- `tm-market-GOLD-D1-20260828-000001`
- `tm-market-OIL-D1-20260828-000001`
- `tm-alt-CFTC-GOLD-COT-W1-20260828-000002`
- `tm-alt-CFTC-OIL-COT-W1-20260828-000002`

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-POS-0001 | GOLD | MM net/OI z-cross < -2 | + |
| HYP-POS-0002 | OIL | MM net/OI z-cross < -2 | + |
| HYP-POS-0003 | GOLD | Commercial net/OI z-cross > +2 | + |

Frozen: hold=5, NEXT_BAR_OPEN, z_lookback=52, z_cut=2, FDR m=3 q=0.05.

Do not use Tuesday as-of as knowledge. Do not flip sign. Do not change z_cut.
Final OOS: DENIED.
