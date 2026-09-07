# V22 FUTURES_XS Contract — pre-registered before any run

**Date:** 2026-09-04  
**Dataset:** `tm-fut-GLBX-XS30-D1-20260904-000001` (Databento GLBX.MDP3 `ohlcv-1d`, 30 parents, all outright months, 2010-06-06 → 2026-08-29, $47.10)  
**Universe:** 30 CME roots: ES NQ YM RTY | ZN ZB ZF ZT | 6E 6J 6B 6A 6C 6S | GC SI HG PL | CL NG HO RB | ZC ZS ZW ZM ZL | LE HE GF  
**Why new:** first cross-section (30 names, 7 asset classes) and first term structure for all of them. Earlier futures work was 2–4 names (V6 GC/CL slope FALSIFIED; V7/V8 OI/DTE killed; CARRY_V1A FX overnight-rate). Those decisions are not reopened; this is a different object.

## Panel construction (fixed)

- Outright contracts only: symbol `^[A-Z0-9]{2,3}[FGHJKMNQUVXZ]\d{1,2}$`; spreads (`A-B`) dropped.
- Per root per session: **front** = outright with max volume; **next** = the outright with the nearest later expiry month than front that has volume > 0.
- Expiry month from symbol month code + year digit (decade resolved by session year).
- Daily return of the *held* contract: close_t / close_{t-1} − 1 on the same symbol. When front changes, the position rolls at close (turnover charged).
- Carry (annualised) = (front_close / next_close − 1) × 12 / months_between(front, next). For financials (index, FX, rates) this is the futures basis; interpreted on sign only, same as commodities. No per-class tweaks.
- Volatility for sizing: 60-session std of held-contract daily returns, ex-ante (computed to t−1).

## Hypotheses (exactly 3; no farm)

| ID | Signal at month-end t | Book | Mechanism |
|---|---|---|---|
| **FX1_XS_CARRY** | annualised carry | Long top-10 roots, short bottom-10, inverse-vol weights normalised to 1.0 gross each side | Backwardation earns roll yield; contango pays it. Koijen et al. |
| **FX2_XS_MOM_12_1** | return over months t−12 → t−1 | Same book | Cross-sectional momentum, Asness–Moskowitz–Pedersen. |
| **FX3_TSMOM_12** | sign of 12-month return, per root | Long/short each root by sign, inverse-vol weights, gross 1.0 | Time-series momentum, Moskowitz–Ooi–Pedersen. |

Rebalance monthly at the last session close. Hold one calendar month. No leverage beyond gross 1.0 per side (FX1/FX2) or gross 1.0 total (FX3). No parameter search. The 12-1, top/bottom-third, 60-session vol are literature defaults written here before running.

## Cost model `FUTURES_XS_COST_MODEL_V1` (fixed)

- 10 bps one-way on every notional traded (rebalance + roll). This is CFD-grade, several times exchange futures cost; deliberately conservative because execution would be via MT5 CFDs.
- Stress: ×2 (20 bps) reported.
- No financing / swap modelled for CFDs → recorded as a known hole; results are upper bounds for CFD execution.

## Windows (locked)

```
RESEARCH    2010-06-06 → 2021-09-30
VALIDATION  2021-10-01 → 2024-02-29
FINAL_OOS   2024-03-01 → 2026-08-29   DENIED. Not read. Not printed.
```

## Books and gates

Predictive book: monthly rank IC (signal vs next-month held return, across roots) and mean long-short spread (FX1/FX2). Capital book: monthly net portfolio return compounded from 1.0; CAGR, MaxDD, Sharpe (annualised √12).

Level-1 requires all of:
1. Research: one-sided t-test on monthly net returns, BH-FDR q = 0.05 over m = 3 → discovery.
2. Research net CAGR > 0 at ×2 cost.
3. Validation net capital > 0 and validation mean monthly net > 0.
4. Not a rename: month-level corr vs H11 official book (where months overlap) ≤ 0.9 — trivially expected across universes; reported anyway.

Fail any → NO_CANDIDATE for that ID. All three fail → `FUTURES_XS_V1_NO_CANDIDATE`, family frozen, no retune, no stats purchase.

10% CAGR is not a gate. Nothing in this file is adjusted after seeing results.
