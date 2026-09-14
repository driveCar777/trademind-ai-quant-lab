# MT5 Phase 3 — Alpha Discovery Plan

**Date:** 2026-09-14  
**Audience:** independent senior quant (external).  
**Repo:** https://github.com/driveCar777/trademind-ai-quant-lab  
**Branch:** `main`  
**This file:** planning only. **DO NOT RUN** the experiments below. No `order_send`, no demo auto-send, no retrain, no grid, no FINAL OOS.

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

Phase 2 remains locked. Linear RESEARCH **+64%** vs Gold Buy-Hold **+171%** is **NO_INCREMENTAL_ALPHA**, not “Linear failed so try another OHLC tree.” 20%/month is an investment objective, never an optimizer target.

---

## 1. Phase 2 locked conclusions

Sources: `AUDIT/PHASE2_FINAL_REPORT.md`, `AUDIT/MT5_STRATEGY_CASE_FILE.md`, `docs/research_engine/EXP001_LADDER_DECISION.md`.

| Claim | Lock |
|-------|------|
| There is no single Ava GOLD robot | Four layers (Grok desk, V9 RSI, research graves, V4 follow) do not share a signal |
| Directional edge on the sample | **Unlevered long gold** (close path +173%, CAGR 13.2%, MaxDD −21.4%) |
| Incremental net vs BUY_HOLD | **NOT PROVEN.** EXP-001 Linear +64% vs BUY_HOLD +171% vs Naive +17% |
| H1 own-price after costs | **FALSIFIED** as a book (Always-Long **−30%**, 1591 fills) |
| EXP-002 ML / EXP-003 | ML not opened; EXP-003 **REGISTERED_NOT_RUN** |
| 20%/month | **UNSUPPORTED** (0/79 months; ~18× exposure ruins the −21% path) |
| Candidate Gate V2 | C5 / C9 / C12 fail. `DO_NOT_TRADE` |
| Auto-trading strategy | **NONE** |
| FINAL OOS 2025-09-12→end | **Locked, unused** |
| Charged GOLD-relevant looks | **~75** (`AUDIT/MULTIPLE_TESTING.md`); discoveries vs BUY_HOLD = **0** |

Do not change production SPEC C0–C13 so that old families pass. This plan **documents** a research gate for *new* families only.

---

## 2. The real question

Not: “Which OHLC model has the highest CAGR?”  
Not: “Linear beat Naive, so open LightGBM.”

**H0:** After costs, any candidate book’s expected net return on locked RESEARCH equals Gold Buy-Hold (or is worse). The book is gold **beta** (plus noise, plus turnover).

**H1:** There exists a **pre-registered**, PIT, cost-aware, three-state (or overlay) book whose expected **net** return exceeds Buy-Hold on comparable capital because of incremental information **Z** that is not a function of gold’s own lagged OHLC in the already-exhausted well.

\[
r_{\text{book},t} = \underbrace{\beta \cdot r_{\text{gold},t}}_{\text{H0}} + \underbrace{\alpha(Z_t)}_{\text{H1}} - \text{costs}_t - \text{execution gap}.
\]

Phase 2 answered H1 for **Z = own-price TA / Linear**: **no**. Phase 3 only proceeds if **Z** is new or a single unused own-price *state* overlay (spread/RV), not another tree.

---

## 3. Data gaps

Full inventory: `AUDIT/MT5_ALPHA_DATA_AVAILABILITY.md`.

**Verified on disk 2026-09-14 (no new pull):**

- Live `mt5_products/history/`: GOLD, CRUDE, EURUSD, USDJPY, GBPUSD, USDCAD, USDCHF — **not** DXY, US500, SILVER, VIX.
- Frozen: DXY, US_500, SILVER, 69-symbol macro D1, GOLD H4/M15, CFTC COT, GVZ/OVX, EIA, UST DGS10, EFFR, GLBX curve.
- VIX CFD: **37** bars (2024-09-30 → 2026-03-13) — unusable.
- 51 unmapped deals; no journal.

**Largest blockage for true incremental Z:** no PIT US **event calendar + surprise**; no **TIPS** real yield; no **option surface** (GVZ is a killed index). On-disk cross-asset **prices** were already charged (USD_METAL, V32, XA/XR, POSITIONING, RATES, IMPLIED_VOL).

Owner must **supply** named PIT series before EXP-008 / EXP-009. This plan does **not** purchase data.

---

## 4. Alpha Family Map (summary)

See `AUDIT/MT5_ALPHA_CANDIDATE_MAP.md`.

| # | Family | Status | Next |
|---|--------|--------|------|
| 1 | Cross-asset divergence (CFD prices) | On disk; **families killed**; EXP-003 frozen | Do not rerun |
| 2 | Macro event surprise | **UNAVAILABLE** | **EXP-008** after acquire |
| 3 | Volatility regime | RV from GOLD; overlays historically weak | **EXP-007** (one rule) |
| 4 | Momentum + confirmation | V4 = beta | Do not run |
| 5 | Conditional mean reversion | Needs events | Fold into EXP-008 |
| 6 | Positioning extremes | COT exists; **POSITIONING_V1 killed** | STOP |
| 7 | News / sentiment | **UNAVAILABLE** | Do not run |
| 8 | Microstructure / spread | Bar `spread` unused as signal | **EXP-007** |

Plus **TIPS real yield** (not UST10, not Bund CFD): **UNAVAILABLE** → **EXP-009**.

---

## 5. Beta vs alpha framework

\[
\text{strategy P\&L} = \text{beta (long gold)} + \text{alpha}(Z) - \text{costs} - \text{execution mismatch}.
\]

| Component | What it is on this sample | Not |
|-----------|---------------------------|-----|
| **Beta** | Being long gold. RESEARCH close +173%, CAGR 13.2% | A signal |
| **Alpha** | Incremental **net** vs BUY_HOLD | In-sample IC; Linear vs Naive; val-window TWR |
| **Costs** | 34-pt live spread; ASSUMED 2 bp/side slip; long swap −1.54/night | Free |
| **Execution** | Research = next D1/H1 open + time stop. Grok = M15 market, no SL | The same book |
| **Leverage** | Account field 400× | Alpha; a 20% machine |

**Is any “high return” book just long gold + bull + leverage?**  
**Yes, for every large positive GOLD book already measured.** BUY_HOLD / ALWAYS_LONG are explicit beta. V4 “VIABLE_HISTORICAL” and Linear `research_30` are the **2023–26 bull**. Always-short **−71%**. H1 always-in is beta **minus** 1591 round-trips (**−30%**). Levering k≈18 to hit 20% months is beta × ruin (`AUDIT/MT5_RETURN_TARGET_REALITY_CHECK.md`).

A book that beats **cash** but not **BUY_HOLD** is still **FALSE** as a Candidate.

---

## 6. New Candidate Gate (document only)

**Does not modify** SPEC §30.5 C0–C13 or `research_engine/phase2_mt5/gates.py`. Production gates stay as written so **old** families cannot be laundered through a weaker hurdle.

Phase 3 research gate (P3-G). A family is **CANDIDATE=TRUE** only if **all** hold. Otherwise **FALSE**.

| ID | Requirement | Fail if |
|----|-------------|---------|
| P3-G0 | Written contract **before** any score; write-once | Peek then register |
| P3-G1 | Frozen data; hashes recorded; no new pull after freeze | Live hunt for a symbol that “works” |
| P3-G2 | No lookahead; knowledge time reconstructable | Tuesday COT; revised CPI; META_now as a **feature** |
| P3-G3 | No selection leakage; val/FINAL OOS not used to pick | V4-style val gate |
| P3-G4 | Explicit costs: spread + slip + swap + commission; stress 2×/3× | Gross-only |
| P3-G5 | Official book **OOS+** on RESEARCH (embargoed WF if any fit) | Train IC |
| P3-G6 | **OOS net TWR > Gold BUY_HOLD** on **comparable 1× capital**, **both** RESEARCH 70 and 30 | Beat cash only; beat Naive only; one window |
| P3-G7 | Incremental alpha statistically credible; **m** incremented **before** run | Silent extra look |
| P3-G8 | Regime + subperiod robustness; not a single bull | research_30-only |
| P3-G9 | DD acceptable vs BUY_HOLD path (must not “win” only by missing 2022 and dying later) | 2022 sit-out artifact |
| P3-G10 | No single-period dependency; no data-source artifact (CFD listing, short VIX, index IV as “surface”) | VIX n=37; GVZ-as-OG.OPT |
| P3-G11 | Executable later on Ava GOLD (CFD, 0.01 lot, documented swap/spread) | Paper option that cannot be hedged here |
| P3-G12 | Time stop **and** a pre-registered risk stop if it ever goes live | Time stop only (today’s C9 fail) |

**Automatic FALSE:** beat cash but not BUY_HOLD; bull-only; gross-only; validation-only; leverage-as-alpha; 20% as fit target.

---

## 7. Next experiments (at most 3) — DO NOT RUN

Selection discipline: no RSI/MACD/SMA/ORB reruns; no Logistic/LGBM on GOLD-only OHLC; prefer on-disk unused Z, then cross-asset if new, else DATA-BLOCKED acquire-first. EXP-003 is **not** rerun. Case File EXP-004/005/006 remain unused text; IDs below are **EXP-007/008/009** so they are not confused with a silent 003/004 restart.

Chosen for **highest chance of true incremental alpha given actual data**, not highest chance of a pretty backtest:

1. **EXP-007** — only unused-as-signal Z on official GOLD (spread + RV overlay). Low prior. On disk.
2. **EXP-008** — event surprise. Highest remaining economic prior. **Data missing.**
3. **EXP-009** — TIPS real yield (not DGS10/EFFR/Bund). Textbook channel; prior rates tests used the **wrong object**. **Data missing.**

Cross-asset **CFD** residual is **not** a fourth experiment: USD_METAL / V32 / XA already answered “price CFDs ≠ net edge,” and EXP-003 stays **REGISTERED_NOT_RUN** because EXP-001 had no increment vs BUY_HOLD — still blocked for that process reason **and** because a DXY/oil z-cut would be a forbidden reopen even with frozen files on disk.

---

### EXP-007 — `GOLD_LIQVOL_SITOUT_OVERLAY`

| Field | Pre-register (DO NOT RUN) |
|-------|---------------------------|
| **EXPERIMENT_ID** | EXP-007 |
| **HYPOTHESIS** | Pre-registered high realized-vol **or** high historical bar-spread states have sufficiently negative conditional E(net) that sitting **FLAT** there produces **higher RESEARCH net TWR than BUY_HOLD** on both 70/30 windows. |
| **DATA_REQUIREMENTS** | Official `GOLD_D1.csv` only (OHLC + `spread`). Do **not** use `GOLD_META.spread_points_now` as a feature. No DXY/VIX/GVZ. |
| **LABEL** | \(y = \) open[t+1+20]/open[t+1]−1 **gross** for any fit (none expected); **official book is net** (Phase 2 cost formula, slip ASSUMED_2BP_PER_SIDE, swap from META). |
| **FEATURES** | (1) RV20 = stdev of 20 D1 close-to-close returns, percentile vs trailing 252. (2) spread_pct = `spread * 0.01 / close`, percentile vs trailing 252. Both PIT at close[t]. |
| **ENTRY** | Next D1 open. **LONG** iff both percentiles ≤ **0.90**; else **FLAT**. Threshold written **now**. No search 80/85/95. |
| **EXIT** | Time stop 20 D1 at next open. FLAT = no position (exit if previously long). No SL/TP picked after the run. |
| **COST_MODEL** | Phase 2 unified; stress 1×/2×/3×. Extra round-trips **must** be charged (this overlay trades more than BUY_HOLD). |
| **BENCHMARK** | **BUY_HOLD** (primary). ALWAYS_LONG secondary. |
| **OOS_SPLIT** | RESEARCH → 2025-09-11. Report first 70% / last 30% of RESEARCH after warmup. FINAL OOS locked. |
| **EMBARGO** | hold+1 = 21 if any statistic uses future labels; book is non-overlapping. |
| **MULTIPLE_TESTING_PLAN** | m := charged(~75) **+ 1**. Increment **before** any number. No second threshold. |
| **SUCCESS_CRITERIA** | RESEARCH 70 **and** 30 **net TWR > BUY_HOLD**; increment t > 0 on the official non-overlap book; not solely a 2022 sit-out (P3-G8/G9). Incremental alpha vs BUY_HOLD, **not** CAGR max. |
| **FAILURE_CRITERIA** | Either window ≤ BUY_HOLD; or wins only by missing 2022; or uses META_now / a searched percentile. **Expected: FAIL** (V5, VOL_FILTER −30%, A-share O2). Failure does **not** authorize ML. |

---

### EXP-008 — `GOLD_EVENT_SURPRISE_PIT`

| Field | Pre-register (DO NOT RUN) |
|-------|---------------------------|
| **EXPERIMENT_ID** | EXP-008 |
| **HYPOTHESIS** | Signed **surprises** on a **frozen** US calendar (FOMC, CPI, NFP; optional pre-listed geopolitics) change E(net) of a **FLAT-default** GOLD D1 book enough to beat BUY_HOLD on event-adjacent days **and** on full RESEARCH. |
| **DATA_REQUIREMENTS** | **DATA MUST BE ACQUIRED FIRST.** Owner provides a frozen pack with: event_id, type, `release_utc`, first_print, consensus, `knowledge_time_utc` ≤ signal. **Not** Grok text. **Not** A-share `tm-cn-a-CALENDAR-*`. No scrape in-session. Quote before any paid vendor; default = do not buy. |
| **LABEL** | Open→open **net**; time stop ≤ **5** D1 (written now). |
| **FEATURES** | Surprise = first_print − consensus; sign / one pre-registered bucket. No extra TA. |
| **ENTRY** | Next D1 open after knowledge time. FLAT default. Side = pre-registered function of surprise sign only. |
| **EXIT** | Time stop ≤ 5 D1. Pre-registered risk stop required before any live talk (P3-G12) — research may stay time-stop-only and then **cannot** pass a live Candidate. |
| **COST_MODEL** | Phase 2 GOLD costs. |
| **BENCHMARK** | BUY_HOLD on **same** event-adjacent days **and** full-sample BUY_HOLD. |
| **OOS_SPLIT** | RESEARCH → 2025-09-11 only. FINAL OOS locked. |
| **EMBARGO** | No event whose knowledge time is after close[t]. |
| **MULTIPLE_TESTING_PLAN** | m+1 **before** run; one calendar, one rule. No shopping CPI vs NFP after seeing scores. |
| **SUCCESS_CRITERIA** | Dual-window net TWR > BUY_HOLD (full book **and** event-day matched); increment credible; PIT audit passes. |
| **FAILURE_CRITERIA** | Data not PIT; lose to BUY_HOLD; one-year dependence; using revised prints. **Do not run until the pack exists.** |

Supersedes Case File EXP-004 (same idea, stricter BUY_HOLD gate, new ID so 003/004 are not “quietly restarted”).

---

### EXP-009 — `GOLD_TIPS_REAL_YIELD_PIT`

| Field | Pre-register (DO NOT RUN) |
|-------|---------------------------|
| **EXPERIMENT_ID** | EXP-009 |
| **HYPOTHESIS** | A **TIPS / 10y real-yield** series (opportunity-cost channel) has incremental E(net) versus BUY_HOLD when used as a **single** pre-registered three-state or overlay rule. |
| **DATA_REQUIREMENTS** | **DATA MUST BE ACQUIRED FIRST.** Dated real-yield (e.g. TIPS 10y / DFII-like) with `knowledge_time_utc`. **Forbidden substitutes:** `tm-alt-UST-DGS10-*` (RATES_V1 **killed**), EFFR/€STR (CARRY **killed**), `EURO-BUND` / `JAPAN_BOND` CFDs, DXY z. |
| **LABEL** | D1 open→open **net**, hold=20, FLAT allowed. |
| **FEATURES** | One pre-registered transform (e.g. real-yield **change** over 20 D1, sign → sit-out or side). Written after the series is frozen and **before** scores. No feature search. |
| **ENTRY** | Next D1 open. FLAT when the frozen rule says no edge. |
| **EXIT** | Time stop 20. |
| **COST_MODEL** | Phase 2 unified. |
| **BENCHMARK** | BUY_HOLD. Linear own-price secondary only. |
| **OOS_SPLIT** | RESEARCH lock; FINAL OOS locked. |
| **EMBARGO** | 21 bars if any fit; prefer a **rule**, not a new ML layer. |
| **MULTIPLE_TESTING_PLAN** | m+1 before run. One model for this information layer (Amendment A3 spirit). |
| **SUCCESS_CRITERIA** | Dual-window net TWR > BUY_HOLD; increment credible; series is actually TIPS, not nominal 10y. |
| **FAILURE_CRITERIA** | Substitute killed series; lose to BUY_HOLD; post-hoc transform. **Do not run until TIPS exists.** Prior: RATES on **nominal** 10y already failed — base rate for “rates-like” books is high. |

Supersedes Case File EXP-006. EXP-005 (option surface) stays on the **acquire list** (§12) but is **not** one of the three: GVZ already killed index-IV; a surface is PAYMENT_REQUIRED (`OPTIONS_DATA_REQUIREMENT_SPEC.md`).

---

## 8. Preregistration requirements

Before **any** Phase 3 number:

1. Contract file under `docs/research_engine/` with the table fields above, dated **before** the run.
2. Data hash + knowledge-time rule + RESEARCH lock + “FINAL OOS unused.”
3. Add **1** to `AUDIT/MULTIPLE_TESTING.md` **before** the engine starts.
4. Cost assumptions labeled (`ASSUMED_2BP_PER_SIDE` until deals validate).
5. Success = incremental vs **BUY_HOLD**, not vs Naive.
6. Write-once `READ.json`; no overwrite; no `TRADEMIND_PHASE2_FORCE` fishing.
7. No `order_send`; no Grok send; no `:9000` / `daily.py` / `paper_ops.py` / `paper_hot_mt5` send-path edits.
8. Do not open Logistic/LGBM because an overlay “looked close.”

---

## 9. 20% reality check

Pointer: `AUDIT/MT5_RETURN_TARGET_REALITY_CHECK.md`.

Median month **+1.11%**, **0/79** months ≥20%, ~**18×** exposure to turn the median into 20%, **−21.4%** gold path → ruin. **TARGET UNSUPPORTED.** Do not prove 20%. Do not use 20% as a fit target (C13 / P3-G).

---

## 10. STOP directions

- OHLC-only ML (D1/H1 trees, Ridge, sparse, Logistic-because-Linear>Naive)
- H1 always-in / 24h sign restacks
- Frozen V1–V9, V30, V32, V4 follow, RSI V9, Grok-as-strategy
- Grok → `order_send` (`TRADEMIND_HOT_GROK_SEND` stays default off)
- Leverage-to-20% / 400× as alpha
- TA fishing (RSI/MACD/SMA/ORB/M15 copies of H1)
- Reopen XA / XR / USD_METAL / DXY z / gold-silver / EIA z / COT z / GVZ / UST10 / OI / DTE / TERM_STRUCTURE
- Silent EXP-003 rerun
- FINAL OOS peek
- Changing SPEC C0–C13 so graves pass

---

## 11. CONTINUE directions

- Keep Phase 2 locks and Candidate **FALSE**
- Forensic mapping of 51 deals → journal (optional, not alpha)
- **Acquire quotes only** for EXP-008 calendar and EXP-009 TIPS (owner decision; no auto-buy)
- After a **written** EXP-007 contract, a later session **may** run that **one** overlay — expected FAIL; not a research season
- V29 / `:9000` A-share ML1 remains a **different** market (frozen paper). Do not mix with Ava GOLD

---

## 12. Data that must be obtained first

Owner must provide (or explicitly decline). This plan does not buy.

| Series | For | PIT rule | Not a substitute |
|--------|-----|----------|------------------|
| US FOMC/CPI/NFP (+ optional pre-listed geopolitics): release UTC, first print, consensus | EXP-008 | knowledge_time ≤ signal | A-share calendar; Grok news |
| TIPS / 10y real yield, dated | EXP-009 | published knowledge time | DGS10, EFFR, EURO-BUND, DXY |
| (Optional, not in the 3) Gold **option** surface IV/settle | future quote | EOD knowledge ≤ signal | GVZ/OVX, VIX n=37 |

Until EXP-008/009 data exist, the research program that could **honestly** change CANDIDATE is **blocked**. EXP-007 is not a consolation scan.

---

## Status of this plan

| Item | Value |
|------|-------|
| CANDIDATE | **FALSE** |
| EXECUTION | **NOT AUTHORIZED** |
| EXP-003 | REGISTERED_NOT_RUN (still) |
| EXP-007/008/009 | PRE-REGISTER text only |
| Honest program status | **BLOCKED** on named PIT series (events, TIPS) |

**End of Phase 3 plan. Do not trade. Do not prove 20%.**
