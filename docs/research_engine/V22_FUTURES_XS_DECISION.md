# V22 FUTURES_XS Decision

**FUTURES_XS_V1_NO_CANDIDATE**

**Date:** 2026-09-04  
**Spent:** $47.10 Databento (`tm-fut-GLBX-XS30-D1-20260904-000001`). Reserve ≈ $46.  
**Contract:** `V22_FUTURES_XS_CONTRACT.md` (written before the run; nothing changed after).  
**Machine:** `data/market/research_engine/futures_xs_v22/RESULTS.json`, `PANEL_QUALITY.json`, `EQUITY/*.csv`  
**Denied window** 2024-03-01 → : dropped at panel build; never loaded.

```
LEVEL = 1            (unchanged: H11/H12 A-share low-vol cluster)
CANDIDATE = 2        (unchanged)
NEW_CANDIDATE = 0
NEW_INDEPENDENT = 0
FDR m=3 q=0.05 discoveries = []
```

## Data (qualified)

30 roots, 119,724 root-days, 2010-06-06 → 2024-02-29. Front = max-volume outright; next = nearest later month with volume. Held-contract returns: ES +414%, NQ +837%, NG −98%, CL −55%, HE −61% over the panel — consistent with known index gains and contango bleed, so the roll logic is right. Median annualised carry: NG −14.9%, HE −19.8%, RB +6.9%, ZB +3.0% — signs as expected. 7 daily |ret| > 20%, all real (CL April 2020, HO March 2022). `next` missing 8% (thin back months on GF/PL/6S), handled by dropping from carry rank that day.

## Results (10 bps one-way, monthly rebalance, gross 1.0 per side)

| ID | Research 2010-06→2021-09 (n=124–135 months) | Validation 2021-10→2024-02 (n=28) | FDR | ×2 cost | Val cap > 0 | Level-1 |
|---|---|---|---|---|---|---|
| FX1_XS_CARRY | total −4.4%, CAGR −0.40%, Sharpe 0.01, MaxDD −28%, p=0.49 | total +11.3%, CAGR +4.7%, Sharpe 0.61 | no | −2.1% | yes | **no** |
| FX2_XS_MOM_12_1 | total −11.4%, CAGR −1.16%, Sharpe −0.03, MaxDD −44%, p=0.53 | total +9.2%, CAGR +3.9%, Sharpe 0.34 | no | −2.7% | yes | **no** |
| FX3_TSMOM_12 | total +5.0%, CAGR +0.47%, Sharpe 0.17, MaxDD −7%, p=0.30 | total +4.3%, CAGR +1.8%, Sharpe 0.40 | no | +0.1% | yes | **no** |

Gross (zero-cost) research CAGR: 1.3% / 0.4% / 0.8%. The failure is not cost. On 11+ years of research data the three textbook futures premia were flat before fees in this universe and window. Correlation with the H11 A-share book on overlapping months: −0.19 / −0.07 / −0.12 (n≈150) — truly independent, and truly nothing.

Validation is positive for all three (2022 commodity/rates trend year). Pre-registered gates say research FDR first; a 28-month positive tail after a flat 11-year body is what a coin does. It is recorded, not promoted.

## What this closes and what it does not

- Closes: "the futures cross-section is the untested object". It was, and it is now tested with 3 literature-default hypotheses. Frozen. No retune of lookback / top-third / vol window / cost. No sign flip.
- Does not close: this is the 2010–2021 window, the well-known lean decade for trend and carry. That is context, not a reason to move the window or read the denied slice.
- Does not justify buying `statistics` ($34.59 for OI). OI would add positioning to a family whose price/carry body is flat. Reserve stays.

## Honest summary for the owner

We spent $47 of the $93 on the one thing the balance could buy that was genuinely new. It works as data. It does not work as alpha under the rules that protect your money. The remaining $46 buys nothing on Databento that changes the A-share question, and nothing here that changes this one.

Next: freeze; update authority docs; `research_engine/futures_xs_v22` stays as a reusable panel builder.
