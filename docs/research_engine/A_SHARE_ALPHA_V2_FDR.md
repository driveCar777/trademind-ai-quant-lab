# A-share Alpha V2 FDR

BH q = 0.05. All 9 onesided validation **excess vs EW** p-values entered the ledger. No silent extra tests.

| ID | onesided p | BH adj p | discovery |
|---|---|---|---|
| H21_RESID_REV_20_H20 | 5.773711129423109e-10 | 2.5981700082403992e-09 | True |
| H22_RESID_REV_60_H20 | 2.032708727589285e-07 | 3.658875709660713e-07 | True |
| H23_RESID_REV_20_H5 | 0.05039858273836192 | 0.06479817780646532 | False |
| H24_DISP_HIGH_RESID_20_H20 | 2.3992797385339536e-09 | 5.398379411701395e-09 | True |
| H25_DISP_UP_RESID_20_H20 | 9.976418571680325e-10 | 2.9929255715040975e-09 | True |
| H26_DISP_HIGH_LOW_BREADTH_20_H20 | 3.7341978932142236e-06 | 5.601296839821335e-06 | True |
| H27_CAPITULATION_20_H20 | 1.0 | 1.0 | False |
| H28_CAPITULATION_60_H20 | 1.0 | 1.0 | False |
| H29_PX_AMT_CORR_20_H20 | 2.908247724243841e-16 | 2.6174229518194573e-15 | True |

Discoveries (0-based indices): [8, 0, 4, 3, 1, 5].

FDR here tests excess vs a losing EW book. A discovery is not a Candidate and is not CAGR.
H23 / H27 / H28 did not discover. H21 / H22 / H24 / H25 / H26 / H29 did — and still failed capital gates.

Bootstrap / cost-stress / permutation: not run. Those fire only on Level-1 positives. Count = 0.
