# ALPHA_UNLOCK_MAP_EIA_SUPPLY

Dataset: `tm-alt-EIA-USCRUDE-PROD-W1-20260828-000001` + `tm-alt-EIA-USREFIN-UTIL-W1-20260828-000001`

Executed family: `SUPPLY_V1` hash `4f6548b39376eb773f772d739a06a8f0d436e52b02d5366b49aeacc61dbb16f1`

Outcome: **NO_CANDIDATE**. Do not retune.

## NEW INFORMATION

Weekly US **crude production** (WCRFPUS2) and **refinery utilization** (WPULEUS3).

Not WCESTUS1 stocks. Not GVZ. Not COT. Not UST10. Not overnight rates.

## NEW ECONOMIC MECHANISM

Supply shock and refining run-rate tightness.

Inventory draw/build is a stock. Production is a flow. Utilization is a capacity-use rate. Those are different objects.

## NEW HYPOTHESIS SPACE

| ID | Mechanism |
| --- | --- |
| HYP-SUP-0001 | Production WoW z-cross down → bid OIL |
| HYP-SUP-0002 | Utilization z-cross up → bid OIL |
| HYP-SUP-0003 | Production drop as energy impulse → bid GOLD |

Max 3. No z_cut search.

## OLD FAILURE SPACE DIFFERENCE

INVENTORY_V1 used stocks WoW z-cross on the same WPSR clock. That failure does not imply production/utilization failed in advance.

This run now shows the new space also has no Level 1 edge on Ava GOLD/OIL D1 7.715y after cost, FDR, and two-target gates. Occupancy of weekly z < −2 / z > +2 is ~0.4% / ~0.06%. That is a sparse-event failure, not a reason to lower z_cut.

Cushing / gasoline stocks would be inventory isomorphs. They are **not** the next family.

## Proof this is not a re-wrap

- Different `dataset_id`
- Different `family_id` / `search_space_hash`
- Different events: `PROD_DROP_CROSS` / `UTIL_UP_CROSS` vs `INV_DRAW_CROSS`
- Contract flag `not_inventory_stocks=true`
