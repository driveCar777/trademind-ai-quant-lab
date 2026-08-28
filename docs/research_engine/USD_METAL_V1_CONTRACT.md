# USD_METAL_V1 CONTRACT

search_space_hash: `a39952f9dd4f3bcec04ce302ac9248b1dc5c2832cce762ee0ce16c0eec474f0b`

Information: 252-day z of Ava `DOLLAR_INDX` (logical DXY) close.

Parents:

- `tm-market-GOLD-D1-20260828-000001`
- `tm-market-SILVER-D1-20260828-000001`
- `tm-market-DXY-D1-20260828-000001`

Not V0.8 EURUSD/USDJPY daily return. Not CROSS_METAL gold/silver ratio.

Knowledge: same-or-prior DXY date, then NEXT_BAR_OPEN.

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-UM-0001 | GOLD | DXY_UP_CROSS (z > +2) | − |
| HYP-UM-0002 | GOLD | DXY_DOWN_CROSS (z < −2) | + |
| HYP-UM-0003 | SILVER | DXY_UP_CROSS (z > +2) | − |

Do not flip. Do not change z_cut. Do not reopen V0.8 or gold-silver ratio. Final OOS DENIED.
