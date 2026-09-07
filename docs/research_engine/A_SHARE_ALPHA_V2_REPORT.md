# A-share Alpha V2 Report

Decision: **NO_NEW_CANDIDATE**. New Level-1 candidates: **0**.

Contract hash: `a40aece085206fc4472edbc0431513ec43d66fd5bad79800db6c9dd9ea131d5c`.
Dataset: `tm-ashare-EQUITY-D1-20260830-000002` / `dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80`.
H11/H12: KEEP_LOW_PRIORITY. No reopen. No H13. No tenth hypothesis. Final OOS DENIED. Purchase = FALSE.

## Dual books

Predictive column is overlapping H-day filled open-to-open minus one round-trip. Name: **MEAN_FORWARD_RETURN**. It is not CAGR.
Capital columns are non-overlapping 1/N books. Only those curves may be called CAGR.

| ID | Family | L | H | Val MEAN_FORWARD_RETURN | Res cap | Val cap | Val CAGR | FDR | L1 |
|---|---|---|---|---|---|---|---|---|---|
| H21_RESID_REV_20_H20 | RESIDUAL | 20 | 20 | -0.141% | 24.21% | -1.36% | -0.53% | Y | N |
| H22_RESID_REV_60_H20 | RESIDUAL | 60 | 20 | -0.201% | 6.49% | -2.70% | -1.06% | Y | N |
| H23_RESID_REV_20_H5 | RESIDUAL | 20 | 5 | -0.347% | -61.83% | -43.82% | -20.45% | N | N |
| H24_DISP_HIGH_RESID_20_H20 | DISPERSION_STATE | 20 | 20 | 1.131% | 88.69% | -15.05% | -7.05% | Y | N |
| H25_DISP_UP_RESID_20_H20 | DISPERSION_STATE | 20 | 20 | 0.738% | -11.45% | -5.18% | -2.36% | Y | N |
| H26_DISP_HIGH_LOW_BREADTH_20_H20 | DISPERSION_STATE | 20 | 20 | 0.165% | 10.84% | -12.38% | -5.97% | Y | N |
| H27_CAPITULATION_20_H20 | DISAGREEMENT | 20 | 20 | -0.834% | -43.82% | -23.16% | -9.77% | N | N |
| H28_CAPITULATION_60_H20 | DISAGREEMENT | 60 | 20 | -0.771% | -39.52% | -21.86% | -9.18% | N | N |
| H29_PX_AMT_CORR_20_H20 | DISAGREEMENT | 20 | 20 | -0.240% | 28.74% | -1.54% | -0.60% | Y | N |

## Benchmarks (MEAN_FORWARD_RETURN, not CAGR)

Hold 20 research: -0.065%. Hold 20 validation: -0.729%.
Hold 5 research: -0.290%. Hold 5 validation: -0.448%.

Validation EW was itself negative. Several hypotheses beat EW (FDR) and still lost money on the capital book. That is the V14.1 gap, not a hidden edge.

## Closest miss

H24 (dispersion-high residual-reversal): validation MEAN_FORWARD_RETURN 1.131%, research capital 88.69%, validation capital -15.05%, FDR pass, evidence 2/2. Failed only `validation_capital`. Predictive corr vs H11 = 0.913. Not independent. Not a Candidate.

H21 residual-reversal 20/20 predictive corr vs H11 = 0.906 (SAME_CLUSTER if it had passed).
