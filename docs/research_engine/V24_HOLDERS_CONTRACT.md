# V24 A-share Shareholder-Count Concentration — Contract (pre-registered)

**Date:** 2026-09-04, written while the download runs; no result seen.  
**Machine contract:** `data/market/research_engine/cn_a_share_holders_v24/CONTRACT.json`  
**Code:** `research_engine/cn_a_share_holders_v24/`, engine `research_engine/cn_a_share_freeinfo_engine.py`

## Object

Per stock, per report period (quarterly, some monthly voluntary disclosures): 股东户数 `HOLDER_NUM`, previous `PRE_HOLDER_NUM`, `TOTAL_A_SHARES`, report `END_DATE`, and **`HOLD_NOTICE_DATE`** — the announcement date. Source: Eastmoney datacenter `RPT_HOLDERNUM_DET`, one request per symbol, all history (≈60 reports per long-listed name). Cost $0.

Mechanism class: **ownership dispersion / concentration** — how many hands hold the float. Not price, not a ratio, not membership, not a margin/leverage figure (V23). A-share retail lore and several published studies treat falling holder count ("筹码集中") as informed accumulation and rising count as distribution.

## PIT

A report's value is visible from the **first session strictly after `HOLD_NOTICE_DATE`** and stays visible until the next report's notice date. Rows with notice date after 2024-02-29 are dropped at compile so no denied-window information exists in memory. Execution `RAW_OPEN_T1`.

## Hypotheses (exactly 3; sign fixed a priori: concentration → long)

| ID | Score (higher = long) |
|---|---|
| HC1_CONCENTRATION_QOQ | −(HOLDER_NUM / PRE_HOLDER_NUM − 1) |
| HC2_CONCENTRATION_2Q | −(HOLDER_NUM_t / HOLDER_NUM_{t−2 reports} − 1) |
| HC3_LOW_HOLDERS_PER_SHARE | −(HOLDER_NUM / TOTAL_A_SHARES) |

HC1/HC2 are horizon variants of one idea and may cluster; HC3 is a level measure and is expected to lean large-cap. All accepted as-is; FDR m = 3.

## Inherited unchanged

Frozen price pack, eligibility, long-only top-quintile 20-session non-overlapping book, `A_SHARE_STRATEGY_COST_MODEL_V1`, research 2010-01-04 → 2021-08-24, validation 2021-08-25 → 2024-02-29, denied 2024-03-01 →, dual books, BH-FDR q = 0.05, `_is_level1`, 0.9 cluster test vs H11/H12.

All three fail → `A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE`, frozen. No retune, no sign flip, no second contract on this object.
