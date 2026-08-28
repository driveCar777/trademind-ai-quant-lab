# SUPPLY_V1 CONTRACT

search_space_hash: `4f6548b39376eb773f772d739a06a8f0d436e52b02d5366b49aeacc61dbb16f1`

Information: EIA weekly **production** (WCRFPUS2) and **refinery utilization** (WPULEUS3). Not WCESTUS1 stocks. Not INVENTORY_V1.

Knowledge: week-ending Friday; WPSR Wednesday 16:00Z; then NEXT_BAR_OPEN.

| ID | Target | Event | Sign |
| --- | --- | --- | --- |
| HYP-SUP-0001 | OIL | production WoW z-cross < −2 | + |
| HYP-SUP-0002 | OIL | utilization z-cross > +2 | + |
| HYP-SUP-0003 | GOLD | production WoW z-cross < −2 | + |

Do not flip. Do not change z_cut. Do not reopen INV z-cut. Final OOS DENIED.
