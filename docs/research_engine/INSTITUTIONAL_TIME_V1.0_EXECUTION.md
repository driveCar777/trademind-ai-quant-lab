# INSTITUTIONAL_TIME_V1.0 — executed and killed

Tag: `RESEARCH-2026-0001`

search_space_hash: `1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457`

Parents (unchanged):

- `tm-market-GOLD-D1-20260825-000001` sha256 `49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899`
- `tm-market-OIL-D1-20260825-000001` sha256 `a22e4213fbbf28e24e892fcce400522885e8208ba9f94bbf41ceed3177808d72`

## Program

**WEAK_EDGE**. Candidate = 0. Level remains 0.

FDR m=3 q=0.05 discoveries = 0.

Xavier-01 content_hash = Xavier-04 content_hash = `a7e646b53c722826790b60b8ac48ff2045c932ef89084c8b85837607fd7cb2d0`.

Final OOS: DENIED. No `order_send`. Hold stayed 5. Window was not widened.

## Hypotheses

| ID | Event | Target | Research TR | Validation TR | raw_p | label |
| --- | --- | --- | ---: | ---: | ---: | --- |
| HYP-IT-0001 | month-end D1 | GOLD | +6.61% | +2.61% | 0.0415 | WEAK_SUPPORT, FDR fail, single target |
| HYP-IT-0002 | month-end D1 | OIL | +21.92% | −1.23% | 0.0410 | validation sign fail |
| HYP-IT-0003 | month-start D1 | GOLD | −2.79% | +1.56% | 0.8196 | research sign fail |

Occupancy ≈ 3.9% on all three. Not a level leak.

0001 is **not** a Candidate: FDR failed, OIL did not confirm, block-bootstrap CI includes 0.

## Kill

Family `FAM-IT-CALENDAR-0001` is **KILLED**.

Forbidden reopen:

- month-end T−2 / T−3
- month-start T+2 / T+3
- add quarter-end to this family
- flip sign
- change hold
- change cost or risk to rescue PnL

Quarter-end is the same calendar-book mechanism. It is not the next family.

## Next

`TIME_STRUCTURE_V1` — London / NY session open on the new H1 packs. Not weekday. Not this contract.
