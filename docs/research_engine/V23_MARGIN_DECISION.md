# V23 Margin Positioning Decision

**A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE** — STOP_B_FAMILY

**Date:** 2026-09-04  
**Cost:** $0 (exchange-published margin detail via Eastmoney datacenter mirror; SSE/SZSE official endpoints probed reachable).  
**Contract:** `V23_MARGIN_CONTRACT.md`, hash in `cn_a_share_margin_v23/CONTRACT.json` (written before download finished).  
**Machine:** `data/market/research_engine/cn_a_share_margin_v23/{RESULTS,FDR,FAILURES,CANDIDATES,DECISION,MARGIN_DATASET}.json`, `EQUITY/`, `TRADES/`  
**Raw:** 3381 session files 2010-03-31 → 2024-02-29, 0 failures, 4.02 M mapped rows. Denied window not downloaded.

```
LEVEL = 1   CANDIDATE = 2   NEW_CANDIDATE = 0   NEW_INDEPENDENT = 0
FDR m=3 q=0.05 discoveries = []
```

## Coverage

Marginable names (median per year): 2010 89 · 2012 278 · 2013 495 · 2015 894 · 2017–2019 ≈ 950 · 2020 1697 · 2021 2026 · 2022 2345 · 2023 3197. Cross-section ≥ 100 from late 2012, so the capital books effectively start 2012–2013 (M1 118 research periods).

## Results (long-only top quintile, 20 sessions, cost V1)

| ID | Research MF / excess vs EW (t) / IC | Research capital | Validation MF / excess (t) / IC | Validation capital | FDR | Gate fails |
|---|---|---|---|---|---|---|
| M1_LOW_NET_MARGIN_INFLOW_20 | **+0.57% / +0.25% (t 4.85) / 0.041** | **+37.2%**, CAGR 3.3%, MaxDD −55%, Sharpe 0.26 | −0.67% / +0.06% (t 0.92) / 0.059 | **−19.2%** | no (adj p 0.54) | fdr, val capital, val MF |
| M2_LOW_MARGIN_BALANCE_RATIO | +0.40% / +0.14% (t 1.40) / 0.029 | +8.4%, MaxDD −49% | −1.32% / −0.59% (t −4.38) / −0.006 | −32.1% | no | fdr, val capital, val excess, val MF, val IC |
| M3_MARGIN_DELEVERAGED_60 | +0.28% / +0.07% (t 1.17) / 0.020 | −11.1%, MaxDD −58% | −0.76% / −0.03% / 0.061 | −22.5% | no | fdr, res capital, val capital, val excess, val MF |

Month-aligned capital correlation vs H11: M1 0.78, M2 0.35, M3 0.33. M2/M3 are genuinely different books from the low-vol cluster — and negative. M1 leans low-vol (low margin inflow ≈ quiet names).

Yearly M1 (compound): 2013 −21%, 2014 +28%, **2015 +68%**, 2016 −11%, 2017 −15%, 2018 −26%, 2019 +24%, 2020 +3%, 2021 +20%, 2022 −15%, 2023 −25%.

## Reading

This is the strongest research-window result any A-share family has produced since V13: M1's research excess over EW has t = 4.85 across 2343 overlapping windows, and its research capital account is +37%. That part is real information — leveraged retail inflow did predict lower 20-day returns in 2013–2021, and avoiding it beat the eligible EW book after cost.

It did not survive validation. 2021-08 → 2024-02 was a grinding bear market in which every long-only book lost; M1 lost 19% versus EW-excess of only +0.06% per window (t 0.92). The pre-registered gates require validation capital > 0 and an FDR discovery on validation excess. Neither happened. Under the rules, M1 is `NO_CANDIDATE`, and the family is frozen.

What this does *not* license: retuning the 20-session window, changing the quintile, adding a market-state filter, flipping to short the high-inflow quintile (A-shares cannot be shorted at scale), or "extending research through 2023". Any of those would be selecting on the validation slice.

What it does record, for the atlas: `MARGIN_FLOW` is the first A-share information class with a **strongly positive research-period edge** and a **near-zero (not negative) validation excess vs EW**. That is a different failure shape from V15–V21 (which were mostly negative in both). If a future contract on a *different* free object shows the same shape, the honest question becomes whether the 2021-08 → 2024-02 validation slice is representative — a question to be answered with the denied window only after an explicit human unlock, never by moving windows now.

## Next

Family frozen. Queue: HOLDER_COUNT (quarterly, Eastmoney), NORTHBOUND_HOLDINGS (HKEX / Eastmoney, daily since 2017). One at a time, ≤ 3 hypotheses each, same gates, $0. FAILURE_ATLAS to be extended with M1–M3.
