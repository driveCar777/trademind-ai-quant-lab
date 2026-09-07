# Databento remaining-credit evaluation — what the ~$93 should buy

**Date:** 2026-09-04  
**Authorization:** user 2026-09-04 — "买之前评估是否真的需要，买完继续干，不用问". Scope = Databento credit balance only (est. **$93.18** = $125 − $31.82 spent in V6).  
**Quotes:** real `metadata.get_cost`, `data/market/research_engine/databento_eval_v22/QUOTE.json`. Nothing downloaded at quote time.  
**Script:** `scripts/research_engine_v22_databento_eval_quote.py`

## The gap this money can and cannot touch

Databento sells US exchange data (CME, Nasdaq, US consolidated). It has **no A-share data**. So the $93 cannot close the A-share `NEW_INDEPENDENT=0` gap. Buying anything here is only justified if it opens a **different universe with a different information object**, not another proxy for a dead family.

## Real quotes

| Option | Dataset / schema | Window | Cost | Verdict |
|---|---|---|---|---|
| **A. 30 CME futures roots, all contract months, daily bars** | GLBX.MDP3 `ohlcv-1d`, parent, ES NQ YM RTY ZN ZB ZF ZT 6E 6J 6B 6A 6C 6S GC SI HG PL CL NG HO RB ZC ZS ZW ZM ZL LE HE GF | 2010-06-06 → 2026-08-29 | **$47.10** | **BUY** |
| A2. same + official stats (settle / OI / volume) | `statistics` | 2010 → | +$42.85 (total $89.95) | Not now — leaves $3; OI not needed for the first contract |
| A3. same, stats from 2015 | `statistics` | 2015 → | +$34.59 | Deferred; buy only if a contract needs OI |
| A4. definitions | `definition` | 2010 → | $82.35 | No — expiry month is in the symbol; front = max volume |
| B. Nasdaq-listed US equities daily, all names | XNAS.ITCH `ohlcv-1d` | 2018-05 → | $29.90 | No now. Price-only CS on 8 years, one exchange. A-share taught us price-only CS ≈ dead; US is more crowded. |
| C. All US equities consolidated daily | EQUS.SUMMARY `ohlcv-1d` | 2024-07 → | $10.02 | No. 2 years is not research. |
| D. DBEQ.BASIC all names | `ohlcv-1d` | 2023-03 → | $73.04 | No. 3 years, most of the money. |
| E. LO 1Y MVD-A (V8.4 pick) | LO.OPT `definition`+`ohlcv-1d` | 2025-08 → | $11.99 | No. Single-name IV on the 4-name CFD book that V7–V10 killed. |
| F. OG 1Y MVD-A | OG.OPT | 2025-08 → | $14.99 | No. Same reason, worse coverage (V8.4 CASE B). |
| G. US equities stats all names | EQUS.SUMMARY `statistics` | | $34,893 | Out of scope. |

## Why A, and why it is not a re-run of a killed family

What the repo has tested on futures/CFDs:

- V5.1: 841 MT5 CFDs, price-only breadth/size → WEAK_EDGE / NO_CANDIDATE. CFDs have **no term structure**.
- V6: GC + CL only (Pack E). TERM_STRUCTURE slope on **two names, time-series** → 3/3 FALSIFIED.
- V7/V8: OI / volume / DTE / fusion on those same two names → killed.
- V2.0 CARRY_V1A: FX overnight-rate carry, 4 CFD names → NO_CANDIDATE.

What option A adds that none of those had:

1. **A cross-section of ~30 instruments across 7 asset classes** (equity index, rates, FX, metals, energy, grains, livestock). Every earlier futures test was 2–4 names → no cross-section possible. Rank-based, dollar-neutral long-short across 30 roots is a different statistical object from a time-series rule on GC/CL.
2. **Term structure for all 30**, from actual contract months (front/next spread from prices, front = highest-volume contract). Carry / backwardation ranked across commodities and financials is the most replicated non-equity premium in the literature (Koijen–Moskowitz–Pedersen–Vrugt; Moskowitz–Ooi–Pedersen for TSMOM). That is a claim about the literature, not a forecast.
3. 16 years, exchange data, hashable and reproducible. Reusable by the existing dual-book / FDR Research OS with a new cost model.

Construction note: this universe's natural book is **long-short, monthly rebalance, notional-weighted**. That is not the A-share long-only 20-day sleeve. It is a *new universe with its own contract*, so the H11/H12 "do not change hold/cost" lock does not apply to it; those locks stay on the A-share books.

Execution note: the user trades MT5 CFDs. A futures-signal → CFD-execution mapping hole exists (V11 flagged it). The research contract will price a CFD-grade cost (wider than exchange futures) so any surviving book is already conservative. If the book survives only at futures costs and dies at CFD costs, that is recorded as such — not tuned.

## Budget rule

- Spend now: **$47.10** (option A). Reserve: ≈ $46.
- Stats ($34.59 from 2015) only if the first contract's Decision explicitly needs OI. Not automatic.
- No $199/month Standard. No ticks. No options.
- Max 3 pre-registered hypotheses in the first contract. All NO_CANDIDATE → stop; do not buy B/E to "keep going".

```
PURCHASE = A
COST_USD = 47.10
RESERVE_USD ≈ 46
NEXT = freeze → qualify → FUTURES_XS_V22 contract (≤3) → dual book → FDR → Decision
```
