# A-share Alpha V2 / V15 Plan

Write-once. 2026-08-31. Locked before any V15 ranking result.

## Goal

Find a **second** cross-sectional mechanism on the frozen panel
`tm-ashare-EQUITY-D1-20260830-000002` that is not LOW_VOL.

H11/H12 stay `KEEP_LOW_PRIORITY`. Do not reopen. Do not retune. No H13.

## Excluded

Raw momentum, raw reversal, simple volatility, simple activity,
H11/H12 lookback/hold/quantile/sign variants, lookback 120/180/250,
ML, new data, Final OOS.

## Families (3) and hypotheses (9)

| ID | Family | Signal | L | Hold |
|---|---|---|---|---|
| H21 | RESIDUAL | −sum(ret − EW market) | 20 | 20 |
| H22 | RESIDUAL | same | 60 | 20 |
| H23 | RESIDUAL | same | 20 | 5 |
| H24 | DISPERSION | residual-rev 20 only if CS residual std ≥ 60d median | 20 | 20 |
| H25 | DISPERSION | residual-rev 20 only if residual std > 20d ago | 20 | 20 |
| H26 | DISPERSION | residual-rev 20 if HIGH disp **and** LOW breadth | 20 | 20 |
| H27 | DISAGREEMENT | rank(−ret20)+rank(amount20) capitulation | 20 | 20 |
| H28 | DISAGREEMENT | same, 60d | 60 | 20 |
| H29 | DISAGREEMENT | −corr(ret, dlog amount) over 20d | 20 | 20 |

No tenth. Completing these nine is the experiment, not a search extension.

## Two books (mandatory)

- **Predictive:** overlapping H-day filled open-to-open minus one RT. Name: `MEAN_FORWARD_RETURN`. **Not CAGR.**
- **Capital:** non-overlapping every hold, 1/N selected, unfilled stays cash. **Only this curve may be called CAGR.**

## Split

Existing 70/15/15: research 2010-01-04–2021-08-24, validation 2021-08-25–2024-02-29, denied 2024-03-01–2026-08-28.

## Gate

Both windows: MEAN_FORWARD_RETURN net > 0, excess vs EW > 0, rank IC > 0, **and** capital total > 0. BH-FDR q=0.05 on all nine. PIT clean.

Corr > 0.9 vs H11/H12 → `SAME_CLUSTER`, not independent.
