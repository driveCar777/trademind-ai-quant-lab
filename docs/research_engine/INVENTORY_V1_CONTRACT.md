# INVENTORY_V1 CONTRACT

search_space_hash: `944195090e6fb835aba35be30a7a13ffee437256b9ed3e5610b23fc7116b2c05`

Information: EIA weekly US crude stocks excluding SPR (WCESTUS1). Week-ending Friday, knowledge Wednesday 16:00Z.

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-INV-0001 | OIL | WoW z-cross < -2 (draw) | + |
| HYP-INV-0002 | OIL | WoW z-cross > +2 (build) | − |
| HYP-INV-0003 | GOLD | WoW z-cross < -2 (draw) | + |

HYP-INV-0002 sign is preregistered, not a post-hoc flip.

Do not change z_cut. Final OOS DENIED.
