# Post-V21 Beat-EW Cluster — W1

**Date:** 2026-09-04  
**Read-only.** Pairwise Pearson on existing `capital_ret` (V15/V18/V19/V20 TRADES) and `ret` (V14 H11/H12 TRADES). No resim.  
**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/BEAT_EW_CLUSTER.json`  
**Script:** `research_engine/post_v21_w1_cluster.py`

Alignment: `exact` = same `signal_date`; `month` = mean capital_ret per YYYY-MM (grids differ by a few days across families, so exact alignment drops V18/V19 to n<8 → None). Validation = months ≥ 2021-08.

```
SHADOW_VERDICT          = NOT_ONE_SHADOW
vs H11 corr > 0.9       = 5 / 13   (H21, H22, H29, A1, A2)
vs H11 corr > 0.7       = 6 / 13
within-13 pair median   = 0.67   (min 0.20, max 1.00 — A1 ≡ A2)
clusters (month, >0.8)  = 6
```

---

## Answer to the three questions

**Are the 13 one residual / low-vol / quality shadow?**  
No. They split into at least four shapes:

| Cluster (month corr > 0.8) | Members | Reading |
|---|---|---|
| Low-vol core | H21, H22, H29, A1, A2, **H11, H12, X1** | Same sleeve as the Candidates. A1 and A2 are identical books (corr 1.0). X1 HS300 set sits inside this cluster too. |
| State-gated dispersion / calendar | H25, A5, A6 | Only trade in some months; fewer periods; different rhythm. |
| GVZ × industry | IM5, IM6 | Their own pair (0.64–0.67 vs H11). |
| Singletons | H23 (5-day hold), H24, H26 | Not linked to anything at 0.8. |

**Is the correlation with H11 > 0.9?**  
For 5 of 13 yes (0.90–0.97 full path). For the other 8 no: H23 0.63, H24 0.67, H25 0.67, H26 0.59, A5 0.46, A6 0.71, IM5 0.67, IM6 0.64. In validation-only months most drop further (H25 0.11, H26 0.18, A5 −0.35, A6 0.03, IM6 0.25).

**Is "beat EW" just another name for the frozen sleeve?**  
Partly. Five are the frozen low-vol sleeve wearing residual/age/amount labels. Eight are *not* strict H11 twins — and they still have negative validation capital and lost their own FDR/gate tests when they ran. Low correlation to H11 does not turn a losing book into a Candidate. It does mean the archive is not literally one time series; it is one long-only 20-day construction with several selection rhythms.

---

## What this does and does not change

- Does not create NEW_INDEPENDENT. Every one of the 13 has val capital < 0 (Q1). Independence from H11 is necessary, not sufficient.
- Does not reopen dispersion / age / GVZ. Those decisions stand.
- Refines Q4 wording: "one sleeve + labels" is exact for the low-vol core (8 books incl. Candidates and X1), approximate for the rest. The shared element for all 13 is construction (long-only, 20d, cost V1) and shared crash years, not a single return series.
- Records that X1 (HS300 membership) is inside the low-vol Candidate cluster at 0.79–0.87 vs H21/H22/A1/A2 and 0.8+ vs H29. Large-cap membership ≈ the same low-vol tilt.

Next: W2 disk walk.
