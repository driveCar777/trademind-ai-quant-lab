# V23 A-share Margin Positioning — Contract (pre-registered)

**Date:** 2026-09-04, written while the raw download is still running; no result has been seen.  
**Machine contract:** `data/market/research_engine/cn_a_share_margin_v23/CONTRACT.json` (hash written at run start)  
**Code:** `research_engine/cn_a_share_margin_v23/`

## Why this is allowed under S1

S1 closed the search over *free A-share objects on disk* (W2: AVAILABLE=0). W2 also said: "有真·新对象（免费、PIT、机制不是公告窗/比率/成分）→ 先实现到 Decision（≤3 条）". W5 named the class that maps to the gap — flow / holder / margin — and assumed it was vendor-paid. A fresh probe today shows the exchange-published daily **margin detail (融资融券明细)** is free and reachable (SZSE and SSE official endpoints 200; Eastmoney datacenter mirror 200 with per-date full cross-section back to 2010-03-31). That is the W2 branch, not a V22 factor farm.

## Information object

Per stock per session: 融资余额 `RZYE`, 融资净买入 `RZJME`, 融资买入 `RZMRE`, 融券余量 `RQYL`, 流通市值 `SZ`. Source: Eastmoney `RPTA_WEB_RZRQ_GGMX` (mirror of SSE/SZSE daily publication). Window downloaded: 2010-03-31 → 2024-02-29 only. **The denied window is not downloaded.**

Mechanism class: **leveraged-investor positioning**. Not a price transform, not a financial ratio, not membership, not an announcement. It is other people's borrowed money.

## PIT

Exchanges publish session D's margin detail on D+1 before the open. Rule: the score at close of session t may use rows with `DATE ≤ t−1`. Implemented as a one-session shift at compile time; no downstream code can see same-day rows. Execution is `RAW_OPEN_T1`.

## Universe

Frozen V12.2 eligible names that have a margin row on t−1 (the marginable set: ~90 names in 2010, ~290 in 2012, ~900 in 2015, ~3500 by 2024). Days with < 100 eligible marginable names are skipped by the engine (same `MIN_CROSS_SECTION` as V13–V21), so the effective sample starts in 2012–2013.

## Hypotheses (exactly 3; signs from literature; no flips)

| ID | Score (higher = long) | Mechanism |
|---|---|---|
| M1_LOW_NET_MARGIN_INFLOW_20 | −Σ₂₀ RZJME / SZ | Leveraged retail inflow predicts lower returns; long the least-crowded quintile. |
| M2_LOW_MARGIN_BALANCE_RATIO | −RZYE / SZ | Leverage overhang; long the least-levered quintile. |
| M3_MARGIN_DELEVERAGED_60 | −(RZYE_t / RZYE_{t−60} − 1) | Names that already shed leveraged holders; long the largest 60-session decline. |

## Everything else is inherited unchanged

Same frozen price pack, same eligibility, same long-only top-quintile 20-session non-overlap book, same `A_SHARE_STRATEGY_COST_MODEL_V1`, same research 2010-01-04 → 2021-08-24 / validation 2021-08-25 → 2024-02-29 / denied 2024-03-01 →, same dual books (MEAN_FORWARD_RETURN is not CAGR), same BH-FDR q=0.05 with m=3, same Level-1 gate (`_is_level1`: research & validation MEAN_FORWARD > 0, FDR discovery, ≥2 of excess/IC per window, research & validation capital > 0), same 0.9 cluster test vs H11/H12.

All three fail → `A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE`, frozen. No retune of 20 / 60 / quintile. No sign flip. No second margin contract.

Cost: $0.
