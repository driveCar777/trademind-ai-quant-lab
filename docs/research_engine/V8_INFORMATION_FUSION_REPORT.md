# V8 Information Fusion Report

Mission: prove whether already-owned MT5 + futures + COT + EIA + rates data had unused **joint** mechanisms. Then quote options. No new purchase by default.

## Census

110 frozen datasets (107 FREE / 1 PAID / 2 DERIVED). Pack E not re-bought. Credits still ≈ $93.18.

## Provenance

Official settlement / OI / volume / expiry = OBSERVED. Curve slope, OI shock, CFD gap, weekly positioning change = DERIVED. LLM text = INFERRED. 16 named states (cap 20).

## TOP 5 executed one family at a time

| Rank | Family | Hash | Outcome | 01=04 | FDR |
|------|--------|------|---------|-------|-----|
| 1 | FUT_CFD_LEAD_V1 | `f271a988…d2c0013` | NO_CANDIDATE | `cf2820e8…ddb2b7` | 0/3 |
| 2 | CURVE_OI_JOINT_V1 | `65ba0698…c58c69` | NO_CANDIDATE | `dc00f4cc…0018a6c` | 0/3 |
| 3 | OI_COT_BUILD_V1 | `b8aa91d8…220f23` | WEAK_EDGE (0003 only) | `29ee472b…ba5c7bb` | 0/3 |
| 4 | CURVE_EIA_REPRICE_V1 | `61c3b93d…0ea176f6` | WEAK_EDGE (0002 only) | `741dd840…5469fe38` | 0/3 |
| 5 | CURVE_REALYIELD_V1 | `8ce8bac1…397ef9cb` | WEAK_EDGE (0003 only) | `1ac4369d…4596f7f` | 0/3 |

Candidate gate needs two book hyps + FDR. None reached it. Do not retune gap / steepening / OI / wow / yield / hold.

## Options quote

`OG.OPT` and `LO.OPT` resolve. `GC.OPT` / `CL.OPT` do not.

| Window | Schema | Symbols | USD |
|--------|--------|---------|-----|
| 3y | ohlcv-1d | OG.OPT | 9.53 |
| 3y | ohlcv-1d | LO.OPT | 10.69 |
| 3y | definition | OG.OPT | 22.88 |
| 3y | definition | LO.OPT | 23.53 |
| 3y | statistics | LO.OPT | 30.74 |
| 3y | statistics | OG.OPT | 70.77 |
| 3y | definition+ohlcv | OG+LO | ≈ 66.64 |
| 3y | definition+statistics | LO | 54.27 |

Downloaded: false. Auto-purchase: false. Stop C.

## Distance to 10%

Level 0. CAGR is not a legal metric yet. 1x only.
