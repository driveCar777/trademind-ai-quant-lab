# V7 Derived Feature Catalog

Parent: `tm-fut-GLBX-CURVE-D1-20260829-000001` (8184 rows, GC+CL).

| feature | status | n |
|---|---|---|
| front_contract / second_contract | DERIVED | 8184 |
| days_to_expiry | DERIVED | 8184 |
| OI_change | DERIVED, unused in V6.1 | 6728 |
| price_change × OI_change | DERIVED_NEW | 4282 |
| curve_slope / contango / backwardation / roll_yield | TESTED_KILLED TERM_STRUCTURE_V1 | — |
| third_contract / curvature | AVAILABLE_NEEDS_RESCAN | 0 |
| volume_change | RAW in Pack E statistics, not in slim curve | local $0 rescan |

OI knowledge = session T+1 21:00Z. Settlement knowledge = T 21:00Z. Joint OI×price only after OI is known.

MT5 cross-section catalog exists (`DERIVED_CROSS_SECTION_V1.json`). Do not re-research BREADTH / SIZE / XS_REV.

Do not auto-turn this catalog into a hypothesis farm.
