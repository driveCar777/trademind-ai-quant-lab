# FUTURES_ALPHA_REPORT

Date: 2026-08-29  
Family: `TERM_STRUCTURE_V1` / `FAM-TSFUT-0001`  
Hash: `5ce2c888aa5530113d769dda8af3602fc45dd96b2db273a73e764f3bf15bb4d0`  
Parent: `tm-fut-GLBX-CURVE-D1-20260829-000001`  
sha256: `f9eecdc2be28d98dca045d8e115868c73334efd067fb7769daceec2bf898702e`

## Official answer

| Item | Value |
|---|---|
| LEVEL | 0 |
| CANDIDATE | 0 |
| Program | **NO_CANDIDATE** |
| Four Xavier | PASS (01–03 PRIMARY, 04 CROSS_CHECK match) |
| Final OOS | DENIED, not touched |

## Hypotheses (Xavier / 2000)

| ID | Event | Research occ | Research n | Research TR | p | Validation TR | Label |
|---|---|---|---|---|---|---|---|
| HYP-TSFUT-0001 | BACKWARDATION | 0.549 | 184 | +0.377 | 0.181 | −0.099 | FALSIFIED |
| HYP-TSFUT-0002 | STEEPENING | 0.681 | 437 | −0.243 | 0.891 | −0.205 | FALSIFIED |
| HYP-TSFUT-0003 | POSITIVE_ROLL | 0.549 | 184 | +0.377 | 0.181 | −0.099 | FALSIFIED |

0001 and 0003 are the same days: slope < 0 iff roll yield > 0. Occupancy ≥ 0.40 is **LEVEL_LEAK**. Contract forbids retuning slope or hold.

FDR discoveries: 0. Book pass: 0.

## Do not

- Retune slope / hold / occupancy cut
- Replace F2 with Ava CFD
- Read Final OOS
- Write a strategy from this family
