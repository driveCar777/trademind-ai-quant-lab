# MT5 Alpha Data Availability

**Date:** 2026-09-14  
**Workspace:** `D:\AGXXAIVER-4-WINDOWS-1-STOCK`  
**Scope:** Ava GOLD Phase 3 entry review. Inventory of files **already on this machine**. No new bars pulled. No series invented.

```
STRATEGY EDGE: NOT PROVEN
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
ECONOMIC EDGE: WEAK
CURRENT AUTO-TRADING STRATEGY: NONE
BROKER LEVERAGE: 400x
TARGET MONTHLY RETURN: 20%+
TARGET STATUS: UNSUPPORTED
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
```

**Verdict in one sentence:** Phase 2 official books used GOLD D1/H1 + META + costs. Secondary symbols and public alt-packs exist, but most incremental-Z families that those files can support were already **NO_CANDIDATE**. There is **no** PIT US event calendar, **no** TIPS real-yield store, **no** gold option surface, **no** news farm, **no** tick/DOM farm. Do not treat “a CSV exists” as “usable for a new independent OOS Candidate.”

Status vocabulary:

| Label | Meaning |
|-------|---------|
| **AVAILABLE** | File exists; date range and knowledge time are usable in principle for a new pre-registered book |
| **AVAILABLE_BUT_DIRTY** | File exists, but leak / short sample / wrong object / cost-floor contamination / unmapped fills |
| **BLOCKED** | File exists (or existed) **and** the family that uses it is frozen NO_CANDIDATE, or the leak-free rule forbids the copy |
| **UNAVAILABLE** | No file on disk that is the claimed object |

Ten questions per series (abbreviated in tables): (1) in repo? (2) date range (3) granularity (4) source (5) lookahead? (6) historical timestamp? (7) reconstruct “known at t”? (8) survivorship? (9) revision/restatement? (10) usable for independent OOS?

---

## 0. What Phase 2 actually traded as data

Official Phase 2 RESEARCH books (`AUDIT/PHASE2_FINAL_REPORT.md`, write-once `data/market/research_engine/phase2/results/*/READ.json`):

| Object | Path | Bars | Span | Role |
|--------|------|------|------|------|
| GOLD D1 | `data/market/cn_a_share/live/paper_hot/mt5_products/history/GOLD_D1.csv` | **2411** | 2018-12-12 → 2026-09-11 | Official D1 |
| GOLD H1 | same folder `GOLD_H1.csv` | **45818** | 2018-12-12T08:00Z → 2026-09-11T20:00Z | Official H1 |
| GOLD META | `GOLD_META.json` | n/a | snapshot 2026-09-13 | point 0.01, spread **34 now**, swap −1.54 / +0.64 |
| Pull log | `PULL.json` | 7 products | pulled 2026-09-13 | live terminal copy |

`GOLD_D1.csv` header (verified on disk): `timestamp_utc,open,high,low,close,tick_volume,real_volume,spread`. First bar spread 40; last bar spread 29. `real_volume` is **0** on sampled GOLD rows.

RESEARCH lock: through **2025-09-11**. FINAL OOS **2025-09-12→end** locked, unused.

Ground truth: `MT5_GROUND_TRUTH/DEALS.json` **n=51**; `POSITIONS.json` n=0; `MT5_JOURNAL.json` **absent**. Login only as `****8889` in `AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json`.

If a reviewer only trusts Phase 2 official inputs, the usable set is **GOLD OHLC + bar spread + META + 51 unmapped deals**. Everything else below is either a frozen older pack, a live sidecar symbol, or a public series already charged to another family.

---

## A. Cross-asset

Live hot-product folder (`PULL.json`, 2026-09-13) — **present:** GOLD, CrudeOIL (`CRUDE_*`), EURUSD, USDJPY, GBPUSD, USDCAD, USDCHF.  
**Absent from live folder:** DXY / `DOLLAR_INDX`, US500 / `US_500`, SILVER, VIX, bonds. Phase 2 Q11 (“DXY/US500 may be missing on this terminal”) is **confirmed for the live history directory**. Those symbols **do** exist as frozen packs (below).

| Series | Status | 1 in repo | 2 range | 3 gran. | 4 source | 5 lookahead | 6 timestamp | 7 known-at-t | 8 surv. | 9 revision | 10 indep. OOS |
|--------|--------|-----------|---------|---------|----------|-------------|-------------|--------------|---------|------------|----------------|
| GOLD own price | **AVAILABLE** | Yes, live + frozen macro | 2018-12-12 → 2026-09-11 (live D1 2411) | D1, H1 | Ava MT5 `copy_rates` | Signal at close[t], fill open[t+1] is PIT | `timestamp_utc` | Yes for OHLC at bar close | Single listed CFD | Broker restates bars; no vintage store | Yes as **price**; **not** as new alpha Z (own-price well exhausted) |
| CrudeOIL / CRUDE | **AVAILABLE** | Yes, **live** `CRUDE_D1.csv` 2408 bars; frozen `CrudeOIL.csv` 2402 to 2026-09-04 | 2018-12-12 → 2026-09-11 live | D1, H1 | Ava `CrudeOIL` | Same-bar close only if that close is known | UTC | Yes at bar close | Current listing | No vintage | Price-CFD **already used** (V32, XA/XR, EXP-003 oil layer registered). New z-cut **forbidden** |
| DXY / DOLLAR_INDX | **AVAILABLE** frozen; **UNAVAILABLE** live | Frozen `tm-market-DXY-D1-20260828-000001` (1999, 2018-12-12→2026-08-28); macro `DOLLAR_INDX.csv` 2004 to 2026-09-04; H1 41468 | D1, H1 | Ava `DOLLAR_INDX` | Same-bar | UTC | Yes at close | Current listing | No vintage | **BLOCKED as a new DXY-z family** (`USD_METAL_V1` KILLED, `MT5_MAX_MISSION_V4_REPORT.md`). File exists; family is dead |
| US_500 / US500 | **AVAILABLE** frozen; **UNAVAILABLE** live | Frozen D1 4850 (2011-01-17→2026-08-28); macro 4856 to 2026-09-04; H1 39746 | D1, H1 | Ava `US_500` | Same-bar | UTC | Yes at close | Current listing | No vintage | Frozen pack exists. Terminal historically lacked live US500 (`EXP003_GOLD_CROSS_ASSET_CONTRACT.md`). V32 pooled equity CFDs **NO_CANDIDATE** |
| SILVER | **AVAILABLE** frozen; **UNAVAILABLE** live | `tm-market-SILVER-D1-20260828-000001` 2397 (2018-12-12→2026-08-28); macro 2403 to 2026-09-04; also H1/H4/M15 packs | D1+ | Ava `SILVER` | Same-bar | UTC | Yes | Current listing | No vintage | Gold-silver / CROSS_METAL **forbidden reopen** (V4 mission) |
| FX majors (EURUSD, USDJPY, GBPUSD, USDCAD, USDCHF) | **AVAILABLE** live | `*_D1.csv` / `*_H1.csv` in live history; D1 spans decades (EURUSD from 1971) to 2026-09-11 | D1, H1 | Ava FX | Same-bar | UTC | Yes | Current listing | No vintage | Dollar **proxy**. Using them as “new DXY” is the same killed USD_METAL family. CARRY on EFFR−€STR already **NO_CANDIDATE** |
| Other macro CFDs (US_TECH100, US_30, EURO-BUND, JAPAN_BOND, COPPER, …) | **AVAILABLE** frozen pack | `tm-mt5-MACRO-D1-20260905-000001` 69 symbols, sha256 `7289ff01…0e59db49`, 288708 rows, retrieved 2026-09-05 | D1 | Ava CFD listing | Same-bar | UTC | Yes at close | **Current listing only** (manifest) | No vintage | V32 `MT5_MACRO_POOLED_V32_NO_CANDIDATE`. Survivorship: pack is today’s book, not a point-in-time listing |
| GOLD_FUTURE (macro pack) | **AVAILABLE_BUT_DIRTY** | `GOLD_FUTURE.csv` **73** bars | 2026-06-12 → 2026-09-04 | D1 | Ava | n/a | UTC | Too short | n/a | n/a | **Unusable** for OOS |
| WTICrude (macro pack) | **AVAILABLE_BUT_DIRTY** | **102** bars | 2022-12-23 → 2023-05-26 | D1 | Ava | n/a | UTC | Stale / short | n/a | n/a | **Unusable**; use live `CRUDE_*` instead |
| GLBX GC/CL curve panel | **BLOCKED** | `tm-fut-GLBX-CURVE-D1-20260829-000001` 8184 rows | Databento curve | D1 | Databento | Must use knowledge time of settle | UTC | Only if panel is as-of | Contract panel | Vendor revisions | TERM_STRUCTURE / CURVE families **NO_CANDIDATE**. Do not reopen |
| CN futures AU/AG/CU/SC | **BLOCKED** | `tm-cnfut-SINA-D1-20260906-000001` | D1 | Sina | PIT rules in V31/V35 | — | — | — | — | V31/V35–V37 **NO_CANDIDATE**; not a gold fix |

**Class A summary:** Secondary **price** series exist. Live incremental Z that is not a forbidden reopen = **CrudeOIL + FX majors** only. DXY and US500 are **on disk as frozen files**, not in the 2026-09-13 live pull. Price-CFD cross-asset as a gold family has already been charged (USD_METAL, V32, XA/XR). EXP-003 remains **REGISTERED_NOT_RUN** — do not silently rerun it.

---

## B. Macro events

| Series | Status | Notes (1–10) |
|--------|--------|----------------|
| US FOMC / CPI / NFP / OPEC **release time + consensus + first print** | **UNAVAILABLE** | No event store under `data/`. Coverage notes already say this (`data/market/research_engine/V11_ALPHA_COVERAGE.json`: “cannot be studied without release time + consensus”). Cannot reconstruct surprise or “known at t.” Not usable for OOS. |
| A-share trading calendar | **BLOCKED** (wrong object) | `data/market/cn_a_share/reference/tm-cn-a-CALENDAR-20260830-000001.csv` — BaoStock **China** session calendar, 8714 trading days, TZ Asia/Shanghai. Not FOMC. Do not use as US macro events. |
| EIA weekly crude stocks (WCESTUS1) | **BLOCKED** | `tm-alt-EIA-USCRUDE-STXSPR-W1-20260828-000001` 2291 wks, 1982-08-20 → 2026-08-21; knowledge `week_ending_Friday + following Wednesday 16:00Z`. INVENTORY_V1 **NO_CANDIDATE**. EIA z_cut **forbidden reopen**. |
| EIA prod / refinery util | **BLOCKED** | Sister packs `tm-alt-EIA-USCRUDE-PROD-W1-*`, `tm-alt-EIA-USREFIN-UTIL-W1-*`. Same mission, do not reopen. |
| UST DGS10 nominal 10y | **BLOCKED** | `tm-alt-UST-DGS10-D1-20260828-000001` 2164, 2018-01-02 → 2026-08-27; knowledge `UST_session_date + 21:00Z`. RATES_V1 **NO_CANDIDATE**. Not TIPS. |
| NY Fed EFFR | **BLOCKED** | `tm-alt-NYFED-EFFR-D1-20260828-000001` 2174, 2018-01-02 → 2026-08-27; knowledge `EFFR_T_plus_1_13:00Z`. CARRY_V1A **NO_CANDIDATE**. |
| ECB €STR / BOJ call | **BLOCKED** | `tm-alt-ECB-ESTR-D1-*`, `tm-alt-BOJ-CALL-D1-*`. Same carry family. |
| TIPS / 10y **real** yield | **UNAVAILABLE** | No TIPS / DFII / real-yield file found. Bond CFDs (`EURO-BUND.csv` 1979, 2018-12-12 → 2026-09-04) are **not** real yield. |
| Scheduled geopolitical calendar (pre-listed) | **UNAVAILABLE** | No PIT store. Grok web text is not a calendar. |

**Class B summary:** The event-surprise object that could be independent of gold beta **is not on disk**. Existing public macro files are **rates / inventory / carry** and are **already killed**.

---

## C. Market state (volatility / regime)

| Series | Status | Notes |
|--------|--------|-------|
| GOLD realized vol / ATR / range from D1/H1 OHLC | **AVAILABLE** (derived) | Computed from official GOLD CSV. PIT if only past returns at close[t]. Historical timestamp = bar time. Reconstruct known-at-t: yes. Survivorship: n/a. Revision: broker bars. **Usable as a feature**; **not** a new information layer. V5 inverse-vol, Phase 2 VOL_FILTER (−30% RESEARCH), A-share O2 overlay REJECT already charged similar ideas. |
| GOLD H1 clock / session boxes | **BLOCKED** | Same H1 file. H1 V2 ORB / V3 barriers / V4 Asia fade / V5 clock **LEGACY_FROZEN**, nets deep negative. Do not rerun ORB/MACD/RSI. |
| VIX CFD | **AVAILABLE_BUT_DIRTY** | Macro `VIX.csv` **37** bars, 2024-09-30 → 2026-03-13. Sample-unusable for a gold RESEARCH OOS book (`AUDIT/MT5_STRATEGY_CASE_FILE.md` §5.2). Not in live pull. |
| CBOE GVZ (gold vol index) | **BLOCKED** | `tm-alt-CBOE-GVZ-D1-20260828-000001` 4259, 2009-09-18 → 2026-08-27; knowledge `DATE + 21:00Z`. IMPLIED_VOL_V1 **NO_CANDIDATE**. Index IV ≠ option surface. |
| CBOE OVX (oil vol index) | **BLOCKED** | Same dates/count as GVZ. Same killed family. |
| Broker VIX / GVZ live | **UNAVAILABLE** | Not in 2026-09-13 live history. |

**Class C summary:** Realized-vol state can be rebuilt from GOLD bars. Index IV and VIX CFD are either killed or too short.

---

## D. Positioning

| Series | Status | Notes |
|--------|--------|-------|
| CFTC GOLD COT Tuesday as-of (`…000001`) | **BLOCKED** | 451 wks, 2018-01-02 → 2026-08-18. `DATA_EXPANSION_REPORT_V1.md`: Tuesday knowledge **leaks** Wed–Thu. **DO NOT CONTRACT**. |
| CFTC GOLD COT Friday 21:00Z (`…000002`) | **BLOCKED** | 451 wks, 2018-01-05 → 2026-08-21; knowledge `CFTC_report_date_plus_21:00Z_Friday_release`. POSITIONING_V1 **NO_CANDIDATE** (sparse after leak-free Friday; do not lower z_cut). File is PIT-capable; family is dead. |
| CFTC OIL COT 000002 | **BLOCKED** | Same mission. |
| Exchange OI / volume by expiry (COMEX) | **UNAVAILABLE** | Quoted, not purchased (`DATA_PURCHASE_CASE.md`). CFD `tick_volume` ≠ exchange OI. |
| Managed-money / other vendor positioning | **UNAVAILABLE** | No second store. |
| 51 Ava deals as “positioning” | **AVAILABLE_BUT_DIRTY** | `MT5_GROUND_TRUTH/DEALS.json`. Symbols seen: GOLD, EURUSD, USDJPY, GBPUSD, CrudeOIL + one blank-symbol balance-style row. **Not** mapped to `signal_id`. n=51 is not a research panel. |

**Class D summary:** The leak-free COT pack **exists** and was **already tested**. Do not reopen. No other positioning panel.

---

## E. News / sentiment

| Series | Status | Notes |
|--------|--------|-------|
| Broker or vendor news tape (PIT, timestamped) | **UNAVAILABLE** | Post-V16 Event/News **DATA_BLOCKED**. No store under `data/` for US gold news. |
| Grok web / geopolitics narrative | **UNAVAILABLE** as research Z | `paper_hot_mt5` prompt may fetch web text. No historical reconstruction, no knowledge-time, no OOS book. SPEC §29.12: Grok is not a strategy. |
| Social / sentiment scores | **UNAVAILABLE** | None found. |
| A-share “韭菜指数” / northbound | **BLOCKED** | Other market. O3 REJECT; O5 NOT_DEPLOYABLE (HKEX stopped daily northbound). |

**Class E summary:** **UNAVAILABLE.** Do not fabricate headlines as features.

---

## F. Microstructure / session

| Series | Status | Notes |
|--------|--------|-------|
| GOLD D1/H1 **bar spread** (points) | **AVAILABLE** | Column `spread` on official CSVs. First D1 40, last 29. Known at that bar’s close. Reconstruct known-at-t: **yes if only that bar’s spread is used**. Survivorship n/a. Revision: broker-reported, not a regulatory vintage. Independent OOS: **partial** — Phase 2 costs also floor with `0.25 × META_now` (34 pts) → **PARTIAL** today-leak if that floor is used as a **feature**. Feature rule: historical `spread` only. |
| GOLD META `spread_points_now=34` | **AVAILABLE_BUT_DIRTY** | Snapshot 2026-09-13. Using it as a historical sit-out threshold **leaks today’s fee**. Cost model may keep the labeled floor; **features must not**. |
| `tick_volume` | **AVAILABLE_BUT_DIRTY** | Present. `real_volume=0` on GOLD. Broker tick count ≠ exchange volume. Not a true size series. |
| GOLD H4 frozen | **AVAILABLE** (not Phase 2 official) | `tm-market-GOLD-H4-20260828-000001` 12348, 2018-12-12 → 2026-08-28, sha256 `a3e473a8…e94c9da2`. No official book. Own-price TF fishing **not recommended**. |
| GOLD M15 frozen | **AVAILABLE** (not Phase 2 official) | `tm-market-GOLD-M15-20260828-000001` 80000, 2023-04-13 → 2026-08-28. Grok uses **live** 20 M15 closes, not this pack. Short span vs RESEARCH lock. |
| Tick farm / M1 / DOM / order flow | **UNAVAILABLE** | Not pulled. Broker ticks ≠ book. |
| Session clock of the **hot desk** | **AVAILABLE_BUT_DIRTY** | `datetime.now()` local 08:30/20:30 vs UTC bars (`FAILURE_ANALYSIS.md`). Execution mismatch, not a PIT feature store. |

**Class F summary:** The only unused-as-signal microstructure field on the official GOLD file is **historical bar spread** (plus derived realized vol). Session **entry** rules are already dead.

---

## Cross-check requested by Phase 3 brief

| Symbol class | Live `mt5_products/history/` 2026-09-13 | Frozen immutable | Phase 2 official? |
|--------------|------------------------------------------|------------------|-------------------|
| GOLD | YES | YES (several generations; do not overwrite) | YES |
| Oil / CrudeOIL | YES (`CRUDE_*`) | YES | No (sidecar) |
| Silver | **NO** | YES | No |
| DXY / DOLLAR_INDX | **NO** | YES | No |
| US500 / US_500 | **NO** | YES | No |
| Rates (DGS10, EFFR, Bund CFD) | **NO** live DGS10 | YES public + CFD | No |
| VIX | **NO** | YES, **37** bars | No |
| COT | n/a | YES, Friday pack | No (already tested) |
| US event calendar | **NO** | **NO** | No |
| TIPS | **NO** | **NO** | No |
| Option surface | **NO** | **NO** (GVZ is an index) | No |

---

## Honest bottom line

1. **Not** “only GOLD OHLC+META+51 deals exist.” Live folder also has **oil + five FX majors**. Frozen packs add DXY, US500, silver, 69-symbol macro D1, H4/M15 GOLD, COT, GVZ/OVX, EIA, UST10, EFFR, GLBX curve.
2. **Almost every incremental-Z object that is already on disk has been charged** (own-price D1/H1, USD_METAL/DXY, V32 pool, POSITIONING, IMPLIED_VOL, RATES, INVENTORY, CARRY, TERM_STRUCTURE).
3. **True gaps** (UNAVAILABLE): US macro **surprise** calendar, **TIPS** real yield, **option surface**, news tape, tick/DOM.
4. **Usable unused-as-signal Z on official GOLD:** historical `spread` + derived realized vol — still own-price state, not a new information layer.

Do not pull new bars to “complete” this table. Do not invent DXY/COT/VIX if a reviewer only has the live folder — they are frozen, not live, and VIX is unusable length.
