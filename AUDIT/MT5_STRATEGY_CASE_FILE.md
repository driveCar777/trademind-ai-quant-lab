STRATEGY EDGE: NOT PROVEN
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
ECONOMIC EDGE: WEAK
CURRENT AUTO-TRADING STRATEGY: NONE
BROKER LEVERAGE: 400x
TARGET MONTHLY RETURN: 20%+
TARGET STATUS: UNSUPPORTED
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED

# MT5 Strategy Case File

**Audience:** independent senior quant (external).  
**Date compiled:** 2026-09-14.  
**Workspace:** `D:\AGXXAIVER-4-WINDOWS-1-STOCK`  
**Repo:** https://github.com/driveCar777/trademind-ai-quant-lab  
**Branch:** `main`  
**Source-of-truth research commit:** `559204773a767a61bff6b6fd20dfd2709b904d2d`  
**This file:** forensic compilation only. No new trains, no retunes, no FINAL OOS, no `order_send`.

TradeMind is a local research lab plus a few disconnected execution surfaces. It is **not** one Ava GOLD robot. Phase 2 (2026-09-13) added broker ground truth, SignalContractV2, unified cost-aware baselines, and a write-once Naive→Linear ladder. The ladder did **not** produce incremental value versus gold buy-hold. Candidate remains **FALSE**.

**Three words used throughout (do not collapse them):**

| Word | Meaning here | Not |
|------|----------------|-----|
| **Beta** | Being long gold. RESEARCH daily close path **+173%**, CAGR **13.2%**, path MaxDD **−21.4%**. | A signal. A reason to auto-trade. |
| **Alpha** | Incremental expected **net** return versus the named benchmark (primary: BUY_HOLD). | In-sample IC. Linear beating Naive. A bull-window TWR. |
| **Leverage** | Broker margin multiplier. Live Ava demo `ACCOUNT_LEVERAGE=400`. | Alpha. A 20%/month machine. Strategy risk. |

**Explicit answers (evidence already in the repo):**

- **NO PROVEN ALPHA** on Ava GOLD.
- **NO_INCREMENTAL_ALPHA** versus BUY_HOLD. EXP-001 Linear RESEARCH TWR **+64%** versus BUY_HOLD **+171%**.
- **TARGET UNSUPPORTED** (Case C). 20%/month was not observed and is not a safe leverage multiple of gold beta.

If a number is not in `AUDIT/PHASE2_FINAL_REPORT.md`, the live broker JSON, a write-once `READ.json`, or a cited Phase 1 decision, it is marked **UNKNOWN** or **DATA BLOCKED**. Nothing below was recomputed for this file.

---

## 1. Executive Summary

There is **no single MT5 trading system** that should be making money.

Four layers share a UI and a demo account. They do **not** share a signal, a fill model, or a ledger:

| Layer | What it actually is | Sends orders? |
|-------|---------------------|---------------|
| A. Grok demo desk (`:9001`) | LLM narrative, 20 M15 closes, bid/ask. No pre-register, no OOS book. | Only if `TRADEMIND_HOT_GROK_SEND=1` **and** demo gates. **Default off.** |
| B. V9 RSI manual | Regex-extract RSI ≥70 short / ≤30 long. Human `confirm=true`. | Demo only, human confirm. Not a Candidate. |
| C. Research graveyard | D1 V1–V5, H1 V1–V9, V30, V32, Phase 2 EXP-001/002 baselines. | **Never.** |
| D. V4 follow display | `sign(close/close_252−1)`, D1, hold 20. Display-only. | **No.** Never appended to Grok. |

A fifth path exists and must not be conflated: **A-share ML1** on `:9000` (frozen paper shortlist, different market, no MT5). See §3 and §20.

Phase 2 added: live Ava snapshot, SignalContractV2 schema, a true-ledger **schema** (empty of fills), nine D1 + nine H1 baselines on a locked RESEARCH window, EXP-001 Naive→Linear, and a stop rule. EXP-001 Linear beat Naive on the last 30% of RESEARCH (**+26.4 pp TWR**) and **lost to buy-hold**. Next model layer **denied**. EXP-002 shipped H1 baselines only (Always-Long **−30%** net). EXP-003 registered, **not run**.

**Candidate Gate V2 fails at least C5 / C9 / C12.** Auto-trade is **DO_NOT_TRADE**.

The only economically large positive book on this GOLD sample is **unlevered long gold**. That is beta. Active own-price rules pay more cost or short the bull. High TWR on a 2024–26 validation slice is not a Candidate.

---

## 2. Broker Ground Truth

Live snapshot: `AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json`  
Also: `MT5_GROUND_TRUTH/ACCOUNT_SNAPSHOT.json`, `SYMBOL_GOLD.json`  
Timestamp UTC: **20260913T092709Z**. `assumed=false`. `order_send=false`. `candidate=false`.

Login is stored **masked only**: `****8889`. Full account numbers are not repeated here.

| Field | Live value | Source |
|-------|------------|--------|
| Company | Ava Trade Markets Ltd. | account |
| Server | Ava-Demo 1-MT5 | account |
| Account mode | `ACCOUNT_TRADE_MODE=0` **demo** | account |
| Currency | USD | account |
| **ACCOUNT_LEVERAGE** | **400** | account |
| Margin mode | 2 (retail hedging) | account |
| Balance / equity / margin | 11784.53 / 11784.53 / 0 (flat) | account |
| Broker symbol | **GOLD** (logical XAUUSD; terminal is not `XAUUSD`) | GOLD |
| CONTRACT_SIZE | **100** | GOLD |
| TICK_SIZE / TICK_VALUE | **0.01 / $1.00** per 1.00 lot | GOLD |
| VOLUME_MIN / STEP / MAX | 0.01 / 0.01 / 150 | GOLD |
| BID / ASK / SPREAD | 4348.75 / 4349.09 / **34 points** | GOLD |
| SWAP_LONG / SWAP_SHORT | **−1.54 / +0.64** | GOLD |
| SWAP_MODE | 1 | GOLD |
| DIGITS / POINT | 2 / 0.01 | GOLD |
| swap_rollover3days | **5** | GOLD |
| MARGIN_INITIAL (symbol field) | 0.0 (broker uses leverage formula) | GOLD |
| MARGIN_HEDGED | 100 | GOLD |
| TRADE_MODE | 4 | GOLD |

**400× is account margin, not strategy leverage.** It does not change E(net|signal). Using 400× to manufacture 20%/month is choosing a ruinous economic-exposure multiple, not “using the broker’s product.”

Notional 1.00 lot ≈ 4349 × 100 ≈ **$434,900**. Margin at 400× ≈ $434,900 / 400 ≈ **$1,087 / lot**. 0.01 lot ≈ $4,349 notional ≈ **$11 margin**. Cited from `docs/research_engine/LEVERAGE_AND_RISK.md` (computed from this snapshot).

Older README text that said 100× is **obsolete**. Ground truth is this JSON.

---

## 3. Current Strategy Inventory

Status vocabulary: **LEGACY_FROZEN** = do not retune; **display-only**; **not a Candidate**; **registered-not-run**.

### 3.1 Ava GOLD / MT5 families (this Case File)

| Family | Mechanism (code, not folder name) | Official result | Status |
|--------|-----------------------------------|-----------------|--------|
| D1 V1 per-product LGBM | Own-price OHLC → regress hold return → `sign(score)` always-in. GOLD hold=10. | GOLD full-sample net **−18%**. 7/7 products NO_CANDIDATE. IC≈0. | LEGACY_FROZEN |
| D1 V2 cost 3-class | Long/short only if \|y\| > 2× META expected cost. | Hurdle 10–33 bp ≪ vol. CASH labels 4–20%. Coverage 82–91%. 0/7 viable. | LEGACY_FROZEN |
| D1 V3 ATR barrier 3-class | Hurdle `k×ATR√hold`, k=1 written. | CASH labels 79–88%. Coverage 1–12%. 7/7 coverage fail. | LEGACY_FROZEN |
| D1 V4 TSMOM12 | `sign(close/close_252−1)`, hold 20, no tree. | GOLD `VIABLE_HISTORICAL`: val **+84.4%** t **2.18**; research **−10%**; full TWR **+51.9%** CAGR **6.2%** MaxDD **−47%**; 81 long / 21 short. Weaker than buy-hold (~**+250%** full sample to 2026-09-11). **Not independent alpha.** | LEGACY_FROZEN, `candidate=false`, `deploy=false` |
| D1 V5 inverse-vol | Same V4 sign; `w=min(1, 0.10/σ20d_ann)`, no extra leverage. | GOLD still historical-gate (val +73% t 2.83, MaxDD −40%). Same edge. 6/7 NO_CANDIDATE. | LEGACY_FROZEN |
| H1 V1 LGBM + 120h mom | 24h `sign`, always-in. | ML net **−35%**; 120h mom **−61%**. Gross +80%/+13%. Train IC **0.52** / 44-fold OOS IC **0.038**. | LEGACY_FROZEN |
| H1 V2 session | London 1h ORB / Donchian24, exit ≥20:00 UTC. | ORB 99% of days. Net deep negative (ORB net **−74%** in CHANGELOG). | LEGACY_FROZEN |
| H1 V3 barriers | Prev-day HL / ORB±0.5 ATR. | ATR 95% trigger. Prev-day HL val +25% t 1.34 = historical-only; full **−23%**, research **−39%**. | LEGACY_FROZEN |
| H1 V4 Asia fade | Fade 00–06 UTC box, exit 20:00. | Net **−80%**, val t −3.62, every year negative. 92% days fire. | LEGACY_FROZEN |
| H1 V5 clock features | SMA24/120 + hour sin/cos; still 24h `sign`. | Gross −10%, net **−67%**, val t −0.14. | LEGACY_FROZEN |
| H1 V6 Ridge | Same columns, fold z-score, α=1. | Train IC **0.055**, fold OOS **0.007**, net **−52%**, val t 0.20. | LEGACY_FROZEN |
| H1 V7 session remainder | Fit remainder-of-session; λ=1 ATR filter; 1 trade/day. | Train IC 0.54 / fold OOS **−0.001**; net **−37%**; val +1.2% t 0.16. | LEGACY_FROZEN |
| H1 V8 triple barrier | First-touch ±1 ATR in 24 bars. | Train acc 65% / fold IC 0.007; val **−72%** t −4.3; CASH 2.4%. | LEGACY_FROZEN |
| H1 V9 sparse 5-col | R24 VOL24 DIST_SMA24 HOUR_SIN/COS. | Train IC 0.283 / fold OOS **−0.001**; net **−52%**; val t −0.03. | LEGACY_FROZEN |
| V4 path exits (BE/TRAIL/SL/TP) | Read-only on 102 closed GOLD trades. | BE3 cuts full +52% → +14%. 41/47 losers never reached +3% MFE. `DIAGNOSTIC_NOT_A_BOOK`. | LEGACY_FROZEN diagnostic |
| V4 gold follow | Same V4 rule, `STATUS.json` for humans. | Display. Last documented bar 2026-09-11: LONG, open leg 2026-08-25 @ 4679.82, mtm ≈ **−7.1%**. | display-only, `feeds_grok=false` |
| V9 RSI manual | RSI≥70 SELL / ≤30 BUY from research summary regex. | Never a research Candidate. | not a Candidate |
| Grok hot table | LLM BUY/SELL/FLAT/HOLD. Confidence unused. | No OOS, no contract. SPEC §29.12: not a strategy. | not a Candidate; send default off |
| Phase 2 D1 9 baselines | Pre-registered, RESEARCH → 2025-09-11. | Only BUY_HOLD / ALWAYS_LONG strongly positive. See §12. | write-once; not a Candidate |
| Phase 2 H1 9 baselines | Same names, hold=24. | Always-Long **−30%**. Active books negative. Buy-hold path still ~**+123%**. | write-once; ML not opened |
| EXP-001 Naive→Linear | 20 bp FLAT; OLS WF 5 own-price cols. | Linear +64% vs Naive +17% vs BUY_HOLD +171%. `NO_INCREMENTAL_VS_BASELINE`. | write-once; next layer denied |
| EXP-002 H1 PIT | Baselines only (ladder rule). | Hourly own-price **falsified as a cost-aware book**. | contract frozen; ML not opened |
| EXP-003 cross-asset | DXY / rates / equity risk / oil, one layer at a time. | **REGISTERED_NOT_RUN.** Blocked because EXP-001 had no increment vs buy-hold. | registered-not-run |
| V30 US share CFD | 492 names, 7 price features, LS20, measured swap −11.09%/yr long. | `MT5_US_XS_PRICE_V30_NO_CANDIDATE`. Val LS **−71.5%** t −3.99; LO−EW **−1.03%/20d** t −4.4; rolling **2/5**. Cost ceiling ≈ **1.9%/20d**. | LEGACY_FROZEN |
| V32 macro pooled | 63 macro CFDs, one LightGBM. | `MT5_MACRO_POOLED_V32_NO_CANDIDATE`. Val LS **−60.5%**; gross t **1.02**; rolling **0/5**. | LEGACY_FROZEN |

Older MT5 graves (V1–V8 / V11 / XA / term structure / OI / DTE / COT / IV / carry on the MT5 universe) are in `FAILURE_ATLAS` and `docs/TRADEMIND_CONTEXT.md`. They are **not** Candidates and must not be reopened to “help gold.”

### 3.2 A-share ML1 (different market — not this trade path)

ML1 (`A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE`) is a **China A-share** cross-section LightGBM with a frozen V26.8 execution shell. Paper desk `:9000`. **No MT5 `order_send`.** Final OOS already consumed (`FINAL_OOS_READ.json` exists ⇒ refuse another read). This Case File does **not** promote, retune, or combine ML1 with Ava GOLD. Mentioned only so a reviewer does not think TradeMind has “no research at all,” and so the two books are not mixed.

---

## 4. Strategy-to-Execution Map

**Which code can call `order_send`?**

| Path | Module | Gate | Default | Same as research book? |
|------|--------|------|---------|------------------------|
| Grok demo | `master/api/app/service/paper_hot_mt5.py` → `mt5_service.send_demo_order` | `demo_send` **and** `TRADEMIND_MT5_SEND≠0` **and** `TRADEMIND_HOT_GROK_SEND=1` **and** not smoke **and** `account_mode=demo`. Live account refused. | **`TRADEMIND_HOT_GROK_SEND` defaults `"0"`** (`grok_send_allowed`, lines 111–113). | **No.** Research scores are not in the prompt. V4 follow comment: never appended. |
| V9 human | `order_service.py` `proposal_from_research` + confirm | `TRADEMIND_MT5_SEND` (historical default `"1"`) + human confirm + demo | Manual | **No.** RSI regex, not V4/H1/EXP-001. |
| Phase 2 research | `research_engine/phase2_mt5/` | Collector/baselines/ladder **forbid** send | n/a | Research-only |
| D1/H1 V1–V9 engines | `research_engine/hot_mt5_*` | Never wired to send | n/a | Self-contained books |
| V4 follow | `hot_mt5_gold_follow/stance.py` | `order_send=false` | n/a | Display of frozen D1 state |
| A-share paper | `paper_ops.py` / `daily.py` | `orders_sent` always false | n/a | Other market |

`TRADEMIND_MT5_SEND` still defaults to allow **V9** demo sends (`mt5_service.send_allowed`: env default `"1"`). That is **not** a Grok strategy switch. Phase 2 closed the LLM→BUY→MT5 path unless the owner sets `TRADEMIND_HOT_GROK_SEND=1` knowing it is not a Candidate (SPEC §29.12, §30.1).

**Fill model mismatch (old auto path vs research):**

| | Research book | Grok / V9 live |
|--|---------------|----------------|
| Price | Next D1/H1 **open** | Concurrent **ask/bid** |
| Clock | Bar UTC | Session clock `datetime.now()` local 08:30/20:30 |
| TF | D1 or H1 | 20× **M15** closes in the prompt |
| Exit | Time stop (5/10/20 D1 or 24 H1) | **No SL, no TP, no time stop** |
| Slip | Labeled 2 bp/side | `deviation=30` points, no model |
| Journal | Phase 2 `LEDGER.json` schema; **events=[]** | Phase 1: `MT5_JOURNAL.json` **missing** |

Magic numbers: requests historically used `mt5_service.MAGIC=240824`; hot-desk constant `260912` was not written on the wire (Phase 1 forensic). Close volume was the **planned** lot, not `position.volume` — partial closes possible.

**Paper/demo ledger:** Phase 2 `data/market/research_engine/phase2/ledger/LEDGER.json` is schema-ready and **empty**. Terminal **51 deals** sit in `MT5_GROUND_TRUTH/DEALS.json` (tickets, not `signal_id`). Positions snapshot **n=0**. There is **no** complete paper chain for a Phase 2 strategy.

---

## 5. Data Inventory

**Do not pull new bars.** This section lists what already exists.

### 5.1 Phase 2 official GOLD (write-once books)

| Series | Path used at run | Bars | Span (from READ) |
|--------|------------------|------|------------------|
| GOLD D1 + META | `data/market/cn_a_share/live/paper_hot/mt5_products/history/GOLD_D1.csv` + `GOLD_META.json` (live, gitignored; files present on the compile machine 2026-09-14) | **2411** D1 | 2018-12-12 → 2026-09-11 |
| GOLD H1 | same folder `GOLD_H1.csv` | **45818** | 2018-12-12 → 2026-09-11 |
| RESEARCH lock | first research bar → **2025-09-11** | D1 2038 bars from 2019-02-26; H1 39758 from 2018-12-19 | Official evaluation |
| FINAL OOS | **2025-09-12** → last bar | **Locked, not scored** | |

`data_hash` (GOLD_D1 + META): `0684aa0d4c3836a800f07dbb6214ca0ad28a357a41bf783c09fc81bf65eaa3f9`  
H1 baselines `data_hash`: `68d326c10867f817be490301d678cc1faecb395ad12b67880aa2772d7c2952da`  
`code_hash` (`phase2_mt5/*.py` at run): `a28863e0bd5634006190b10840f4bc0869c84ebfefa80dca863a7a08561edd73`

Phase 2 `data/market/research_engine/phase2/history/` has **no** extra H4/M15 pull (Wave E: no fishing).

### 5.2 Frozen immutable packs (older generations; do not overwrite)

| Dataset | Role | Notes |
|---------|------|-------|
| `data/market/immutable/tm-mt5-MACRO-D1-20260905-000001` | Frozen macro D1, 69 symbols, sha256 `7289ff01…0e59db49` | Includes GOLD, CrudeOIL, `DOLLAR_INDX`, `US_500`, `VIX.csv`. Phase 2 D1 merge key is timestamp, not “future.” |
| `tm-market-GOLD-D1-20260825/28` | Older GOLD D1 | Do not overwrite. |
| `tm-market-GOLD-H1-20260825/28` | Older GOLD H1 | |
| `tm-market-GOLD-H4-20260828-000001` | **H4 exists** | 12348 bars, 2018-12-12 → 2026-08-28, sha256 `a3e473a8…e94c9da2`. **No Phase 2 official book.** |
| `tm-market-GOLD-M15-20260828-000001` | **M15 exists** | 80000 bars, 2023-04-13 → 2026-08-28, sha256 `a282ffca…329ec564`. Grok uses **live** 20 M15 closes, not this pack. **No Phase 2 official book.** |
| `tm-market-DXY-D1-20260828-000001` | DXY D1 frozen | Prior USD_METAL / DXY families already NO_CANDIDATE. |

VIX in the 20260905 macro pack starts **2024-09-30** (short; inventory: 37–102 bars on some VIX/future symbols). Treat as **sample-unusable** for a gold OOS book.

### 5.3 Ground-truth deals

`MT5_GROUND_TRUTH/DEALS.json`: **n=51**. Symbols observed: GOLD, EURUSD, USDJPY, GBPUSD, CrudeOIL, plus one blank-symbol balance-style row (profit 10000, not a GOLD fill). **Not** mapped to SignalContractV2.  
`POSITIONS.json`: **n=0**.  
`MT5_JOURNAL.json`: **absent** (Phase 1 and this compile). Account equity curve from open-to-today = **UNKNOWN**.

### 5.4 Other

No tick-farm / order-book store. Hot desk injects 20 M15 closes from the terminal when a session runs. H1 research ≠ M15 execution.

---

## 6. Missing Data

Status is **from repo evidence only**. “AVAILABLE” means a file or frozen pack exists — not that it is a proven edge.

| Series | Status | Evidence |
|--------|--------|----------|
| GOLD D1 / H1 own price | AVAILABLE | Live CSV + Phase 2 READ |
| GOLD H4 / M15 | AVAILABLE as **frozen packs**; **not** Phase 2 official | `tm-market-GOLD-H4/M15-20260828-*` |
| CrudeOIL D1 | AVAILABLE (live + frozen macro) | EXP-003 contract; V32 pack |
| Dollar index | AVAILABLE as CFD/frozen (`DOLLAR_INDX`, `tm-market-DXY-D1`) | Already used in V4 USD_METAL / DXY families → NO_CANDIDATE |
| Equity index CFDs (US_500, etc.) | AVAILABLE in frozen macro pack | Live terminal **historically lacked US500** (Amendment V2 / EXP-003). Do not invent a live symbol. |
| VIX CFD | AVAILABLE but **short sample** | `VIX.csv` from 2024-09-30; inventory: unusable length |
| Bond CFDs / UST10-style | AVAILABLE as CFD; **tested** | RATES / CARRY_V1A / V2.0 **NO_CANDIDATE** |
| CFTC COT / positioning | **DATA BLOCKED** for a new PIT gold book | Prior POSITIONING / OI_COT **NO_CANDIDATE**; no Phase 2 COT store |
| Options IV / vol surface | **DATA BLOCKED** / **PAYMENT_REQUIRED** | Index IV ≠ option surface. `OG.OPT`/`LO.OPT` quoted, not downloaded. GLBX no venue IV. |
| Futures term structure / curve | **DATA BLOCKED** on MT5 CFD | CFD ≠ curve. TERM_STRUCTURE **NO_CANDIDATE** (V6). |
| Real yields (TIPS, not bond CFD) | **DATA BLOCKED** as a clean PIT store | REALYIELD / UST10 already weak or dead on prior books |
| Oil curve (term, not spot CFD) | **DATA BLOCKED** | Same as term structure |
| Order flow / DOM | **DATA BLOCKED** | Broker ticks ≠ book. GOLD ticks ~2 days in an old note; not a farm. |
| Economic calendar / surprises | **DATA BLOCKED** | No PIT event store in Phase 2 |
| News / geopolitics | **DATA BLOCKED** | Grok web text is not a PIT feature. Event/News flagged DATA_BLOCKED post-V16. |
| Tick / M1 research farm | **DATA BLOCKED** | Not pulled; forbidden as a fishing TF |

Do not fabricate COT/IV/DXY-as-new-alpha/rates/VIX/news.

---

## 7. Label Review

Canonical research label (D1 V1 / H1 V1 / Phase 2 Linear fit):

```text
y[t] = open[t + 1 + hold] / open[t + 1] − 1
```

| Item | Fact |
|------|------|
| Horizon | D1 GOLD V1 hold=10; V4/Phase 2 baselines hold=**20**; H1 hold=**24** |
| Overlap | Every t can have a label. Adjacent H1 labels share **23/24 = 95.8%** of hours. Independent labels ≈ floor(45818/24) ≈ **1908**. Official Phase 2 **book** is non-overlapping (EXP-002 booked **1591** Always-Long trades). Source: `OVERLAPPING_LABEL_AUDIT.md`. |
| Costs in y? | **No** for V1/V4/H1/EXP-001 Linear fit. Costs hit the **book**. V2/V3 put a hurdle on the class label, not a full net-return target. |
| Economic vs code | Arithmetic of next-open hold return is **correct** (H1 1752 fills, **0** mismatch). Economic object is “gross open-to-open sign,” not “account money after spread+swap.” |
| Neutral | V1 `sign`: score=0 is **short**. No cash state. Phase 2 baselines allow FLAT except Always-Long/Short. |
| Grok | **No label.** It does not optimize y. |

**Model objective ≠ trading objective.** Fitting gross hold-return while trading always-in (or almost always-in) after costs is why H1 can print gross +80% and net **−35%**.

---

## 8. Feature Review

| Book | Features | Mechanism? |
|------|----------|------------|
| D1 V1 | R1 R5 R20 VOL20 VOL60 ATR14 DIST_SMA50 DIST_SMA200 RSI14 GAP RANGE_ATR DOW MONTH | Own-price TA stack. No volume truth, no news, no cross-asset. |
| H1 V1 | Same + HOUR | **`DIST_SMA200` on H1 = 200 hours ≈ 8.3 days**, not a 200-day trend. Wrong scale, not a future leak. |
| H1 V5 | R1/R6/R24 VOL24/120 ATR14 DIST_SMA24/120 RSI14 RANGE_ATR HOUR_SIN/COS DOW | Relabeled clock. Still failed. |
| H1 V9 | R24 VOL24 DIST_SMA24 HOUR_SIN HOUR_COS | Sparse prior. Fold OOS IC still ~0. |
| V4/V5 | One number: 252-day return sign | Textbook trend. On this sample = gold bull beta. |
| EXP-001 Linear | R20, VOL20, DIST_SMA50, RSI14, ATR14/close | Same well, shallower model. Lost to BUY_HOLD. |
| Grok | 20 M15 closes + lore + optional web | Not PIT features. |

**Incremental-information failure:** adding columns, fixing the SMA name, dropping to five priors, or switching Ridge did **not** produce fold-OOS IC or a cost-aware book that beats buy-hold. Collinearity (R1/R5/R20, dual vol, dual SMA distance) is expected. Trees can memorize overlapping labels; linear train IC 0.055 already said the linear signal was tiny.

No future-close-in-X leak was found on the research path (signal at close[t], fill open[t+1]). **PARTIAL** cost leakage: spread floor uses a fraction of **today’s** META spread (`max(bar_spread, 0.25×now)`). That bends historical “should we trade” toward today’s fee. It is not a price look-ahead.

---

## 9. Model Review

**Do we need ML on this GOLD own-price well?** **No.**

| Evidence | Number | Source |
|----------|--------|--------|
| H1 tree true in-sample IC | **0.52** (R² 0.187, hit 62%) | `HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME` / CHANGELOG |
| H1 44-fold mean train / test IC | **0.619 / 0.038** | same |
| H1 Ridge train / fold IC | **0.055 / 0.007** | H1 V6 |
| D1 V1 IC | ≈ 0 | per-product forensics |
| EXP-001 Linear vs Naive RESEARCH | +64% vs +17% | ladder READ |
| EXP-001 Linear vs BUY_HOLD | **+64% vs +171%** | ladder decision |
| Linear research_70 t | **0.21** | ladder READ |
| Linear Sharpe (research) | **0.58** | ladder READ |

Walk-forward scores are OOS **per row** (embargo = hold+1). That does not make the **family** an economic discovery after ~75 GOLD-relevant trials (see §10).

**Forbidden sentence:** “Linear beat Naive ⇒ ML works.”  
**Required sentence:** Linear beat a weak 20-day-sign Naive on a bull slice and **lost to buy-hold**. Verdict `NO_INCREMENTAL_VS_BASELINE`. Logistic / Ridge / LightGBM on this ladder = **denied**.

Architectures used: shallow LightGBM (15 leaves, 200 trees, seed 25) or Ridge α=1. No DL, no RL. Research models are **not** loaded on the hot desk. A-share `REFIT_240` is a different market.

---

## 10. Validation Review

```text
Ava CSV
  → X[t] from close[t] and past
  → y[t] future open return (overlapping if every t)
  → walk-forward fit rows < t − embargo
  → non-overlap book
  → research_70 / validation_30  = last 30% of RESEARCH bars (or Phase 1 full-sample last 30%)
  → no independent TEST
  → FINAL OOS 2025-09-12→end  LOCKED, unused
  → paper/demo is a different program
```

| Issue | Verdict |
|-------|---------|
| WF row scores OOS? | **Yes**, with embargo. |
| Is `research_70` in-sample? | **No** (once corrected). H1 true train IC was the in-sample number. |
| Was `validation_30` a **family gate**? | **Yes (selection leakage, not hot-labeling).** Phase 1 gate: val TWR>0 and t>1 → `VIABLE_HISTORICAL`. V4 GOLD entered the follow narrative because the last 30% **is the 2024–26 gold bull**. Parameters 252/20 were written first; **which book to show humans** was chosen after seeing validation. |
| A-share banned window 2024-03→2026-08 | **Does not apply** to MT5 hot research. MT5 val window **is** the bull. |
| FINAL OOS | Locked. `final_oos_evaluated=false` on all Phase 2 READ files. Do not open to “find a survivor.” |
| Hyperparameter search in code | **No** grid. V1→V9 is a **researcher sequence** (each “once”) that still counts as m. |
| Last-month H1 +18% | **Diagnostic only.** Not a gate. |

**Multiple testing** (`AUDIT/MULTIPLE_TESTING.md`):

| Family | m (approx) |
|--------|------------|
| D1 V1–V5 × 7 products | 35 |
| H1 V1–V9 GOLD | 9 |
| V30 / V32 | 2 |
| Grok / RSI / V4 follow | 3 |
| V4 path-exit diagnostics | 6 |
| Phase 2 D1 9 baselines | 9 |
| Phase 2 H1 9 baselines | 9 |
| EXP-001 Naive + Linear | 2 |
| **Charged** | **~75** |

Plus implicit Phase 1 choices of threshold, hold, TF, and product. Phase 2 did **not** add a grid. FDR as a **count**: discoveries versus buy-hold among pre-registered Phase 2 families = **0**. White Reality Check / SPA **not run** (no Candidate; running RC on 75 graves is theater). Deflated Sharpe: Linear 0.58 after many GOLD trials is not a discovery; Always-Long Sharpe ~1.0 is gold beta.

---

## 11. Cost Review

Live spread **34 points** × POINT 0.01 = **0.34 price**.  
TICK_VALUE $1 per 0.01 per **1.00 lot** ⇒ 34 ticks = **$34 / 1.00 lot** = **$3.4 / 0.10 lot** = **$0.34 / 0.01 lot**.

| Cost | Treatment | Note |
|------|-----------|------|
| Spread | `max(bar_spread, 0.25×META_now)` | PARTIAL use of today’s 34-pt snapshot |
| Slip | **2 bp/side** (`0.0002`), round-trip 4 bp | **ASSUMED**, labeled `ASSUMED_2BP_PER_SIDE` |
| Commission | 0 in research books | Sampled `DEALS.json` rows show `commission=0.0`; not a full fee study |
| Swap | META mode 1; long **−1.54**/night, short **+0.64**; rollover **5** | H1 books charge **calendar midnights**, not 24 hourly swaps |
| Stress | 1× / 2× / 3× on (spread+slip); Stress = 3× + extra 5 bp/side | Already in D1/H1 READ `stress` blocks |

**Frequency versus any putative edge**

- D1 BUY_HOLD: **one** round-trip. E_cost on that single trade ≈ **3.2%** of notional over the whole RESEARCH hold (`economic.E_cost` 0.032 on the one-trade book). Net still **+171%**.
- D1 ALWAYS_LONG: 98 trades, E_cost ≈ **8.0 bp/trade**. Still +161% because it stays long gold.
- D1 Linear: 86 trades, E_cost ≈ **7.4 bp/trade**. Loses to BUY_HOLD because it is **not always long** in the bull.
- H1 ALWAYS_LONG: **1591** trades, E_gross ≈ +6.8 bp, E_cost ≈ **8.6 bp**, E_net **negative**. Hourly turnover **eats the drift**. Stress 3× TWR **−89%**.

V30 (other market on same terminal): long swap **−11.09%/year**, LS one-period cost ≈ **1.9%/20d** — a **cost ceiling**, not a gold result.

**Base vs stress (D1 ALWAYS_LONG RESEARCH):** base TWR +161%; 2× +147%; 3× +133%; stress +122% (`d1_baselines/READ.json`). Buy-hold barely moves under stress because it trades once. Active H1 books collapse.

Long swap **−1.54 / night / 1.00 lot** is a yield drag on leveraged overnight gold, not free beta.

---

## 12. Benchmark Review

**Hierarchy (must be read in this order):**

1. **Cash** (0).
2. **BUY_HOLD** gold (one long, one cost) — the economic question.
3. **Always Long** with the strategy’s own hold/roll cost — “am I just paying more to stay long?”
4. Low-frequency trend (V4 12-month; Phase 2 MOMENTUM/TREND_FILTER).
5. The candidate rule.

**Incremental versus BUY_HOLD is the question.** Linear beating Naive is not.

Phase 2 D1 RESEARCH (2019-02-26→2025-09-11), net TWR / CAGR from write-once READ + ladder:

| Book | TWR | CAGR | Notes |
|------|-----|------|-------|
| Daily close path (sidecar) | **+173%** | **13.2%** | MaxDD **−21.4%** (2022-10-20). `BUY_HOLD_PATH.json` |
| BUY_HOLD open→open | **+171%** | **13.1%** | One round-trip |
| ALWAYS_LONG 20d rolls | **+161%** | **13.1%** | Sharpe ≈ 1.00 |
| TREND_FILTER | +45% | 6.0% | Still ≪ BH |
| EXP-001 Linear | **+64%** | **7.6%** | Lost to BH |
| MOMENTUM | +26% | 3.0% | |
| EXP-001 Naive | +17% | 2.4% | |
| VOL_FILTER | −30% | | |
| BREAKOUT | −34% | | |
| MEAN_REVERSION | −40% | | |
| RANDOM | −45% | | |
| ALWAYS_SHORT | −71% | | |

Phase 2 H1 RESEARCH:

| Book | TWR | Notes |
|------|-----|-------|
| BUY_HOLD open→open | **+123%** | Same drift; one cost. Gross open→open +190%; E_cost 0.67 on the single long because the implementation still marks a large cost field — **net still +123%**. Do not treat H1 BH as a 1591-trade book. |
| ALWAYS_LONG 24h | **−30%** | 1591 fills. Cost dominated. |
| MOMENTUM / MR / BRK / VOL / TREND / RAND / SHORT | all net negative | |

Phase 1 full sample to 2026-09-11 (already published, not Phase 2 official): buy-hold about **+250%**, CAGR about **17.5%**, still **0** months ≥20%.

**NO_INCREMENTAL_ALPHA.** The increment Linear showed versus Naive sits in `research_30` (2023–25 bull): Naive +34.7% (t 1.56) vs Linear +61.1% (t 2.38). `research_70` Linear +2.1% (t 0.21). Same slice that made V4 look like a Candidate.

---

## 13. Risk Review

There is **no account-level risk engine**.

What exists:

- Permission gates: live account refuse; SHARES never send; one position per logical product; Grok ≤2 calls/day.
- Research books: **time stop only**. Candidate Gate C9 requires time stop **and** risk stop. C9 **fails**.
- Hot settings volume **0.1** (10× the 0.01 comment in older docs) is a **lot size**, not R%.
- V5 weight is a **display cap**, not a live sizer.
- Risk modes 0.25 / 0.50 / 1.00 / 2.00% of equity are **research labels**, not authorized defaults.

Missing (none of these are implemented as a GOLD auto-trader):

- Per-trade R% of equity  
- Daily / weekly loss limits  
- Account MaxDD halt  
- Margin utilization cap  
- Kill switch  
- Stale-data / disconnect abort  
- Abnormal spread / slip circuit breaker  
- News / event flatten  
- Overnight / weekend policy  
- Session force-flat  

**No stop ⇒ more conservative in the sense that no Candidate is authorized — not “no risk.”** The Grok path historically sent **market** orders with **no SL**. A 34-point market plus weekend gaps is operational risk. Phase 1 V4 path diagnostic: tight stops on a trend book **cut winners**; adding a stop after seeing numbers is a new contract.

0.1 lot GOLD at ~$4350 is ≈ $43,500 notional ≈ **3.7×** a $11.8k demo (before the owner changes size). That is not a risk model.

---

## 14. Leverage Review

| Number | What it is |
|--------|------------|
| **400×** | Ava **account** leverage. Margin ≈ notional/400. |
| **k = 1** | Unlevered gold (own cash ≈ notional). RESEARCH median month **+1.11%**. |
| **k ≈ 18** | Multiple that turns that median month into **+20%** account. |
| **0.1 lot** | Desk setting. Not “the strategy’s leverage.” |

**False arithmetic:** “13% CAGR × 400× ⇒ huge monthly.”  
Leverage multiplies **the next path**, including the already-observed **−21.4%** close-to-close drawdown (2022-10-20), spread, slip, and **−1.54** long swap. It scales **noise, cost, and DD**, not expected alpha (there is no proven alpha).

From `LEVERAGE_STRESS_TEST.md` (upper bound: costs ignored):

| k | Median month | Worst month | Path MaxDD | +20% month? | On −21.4% path |
|---|--------------|-------------|------------|-------------|----------------|
| 1 | +1.1% | −7.3% | −21% | No | Survives |
| 4 | +4.4% | −29% | −86% | No | Ruin risk |
| 8 | +8.9% | −59% | ruin | Rare | Ruin on 2022 |
| **18** | +20% by construction on median | **−132%** | ruin | Median only | **Ruin** |
| 100 | +111% | ruin | ruin | Quiet months still miss if gold is flat | **UNSAFE** |

Broker 400× is a **ceiling**, not a target. 100×-to-hit-20% is **UNSAFE**. Ground truth is **400×**, not a verified “100× strategy.”

At $11,785 equity, one 0.01 lot is ~0.37× equity. A +1.1% gold month ≈ **+0.4% account** before swap/spread. Hitting +20% from that median needs ~**0.5 lot** ≈ 18× economic exposure (`LEVERAGE_AND_RISK.md`).

---

## 15. 20% Monthly Target Analysis

20%/month is a **performance objective**, not an optimizer, not a gate, and not a reason to retune 252 / hold / λ / k / ATR / RSI / SMA / TF / SLIP / windows.

**Compounded meaning:**  
(1.20)^12 − 1 ≈ **7.912 ≈ 791% annualized**.  
Gold RESEARCH CAGR is **13.2%**. You do not get 791% from 13% without ruinous k.

**From `TARGET_20PCT_MONTH.md` + `BUY_HOLD_PATH.json` (RESEARCH, 79 months):**

| Stat | Value |
|------|-------|
| Median month | **+1.11%** |
| Mean month | +1.38% |
| Worst month | **−7.33%** |
| Best month | **+10.7%** |
| Months ≥ +10% | **1 / 79** (1.3%) |
| Months ≥ +20% | **0 / 79** |
| Required multiple vs 1.11% median | 20 / 1.11 ≈ **18×** economic exposure |
| Interaction with −21.4% gold path at 18× | Account death (stress table: −132% theoretical on worst-month scaling; path DD kills earlier) |

Supported monthly center from this distribution: **~1% median, ~13% CAGR**. 3% happens; 5–8% is the right tail; 12% was not a habit; **20% was not observed**.

| Case | Meaning | This project |
|------|---------|--------------|
| A SUPPORTED | Repeatable net edge that carries 20%/month at safe k | **No** |
| B POSSIBLE_BUT_UNPROVEN | Real edge exists; 20% needs aggressive but non-ruinous size | **No** — no edge above gold beta |
| **C UNSUPPORTED** | 20% needs leverage that dies on the observed path, or there is no edge | **Yes** |

**Do not reverse-engineer a model to hit 20%.** That would be fitting the objective. C13 of Gate V2 exists specifically to forbid it.

H1 always-in is **net negative**: more trading cannot manufacture 20%. Linear CAGR 7.6% still needs ~15×+ and still loses to BH.

---

## 16. Failed Experiments

Not a bare “FAILED” list. **Why** each died:

| ID | Why |
|----|-----|
| D1 V1 (7 products) | **No signal** (IC≈0) + **always-in costs**. GOLD −18%. FX raw+ / net− (~4%/yr cost). |
| D1 V2 | **Cost hurdle too low** vs vol → still always-in. 0/7. |
| D1 V3 | **Opposite**: hurdle too high → no coverage. |
| D1 V4 GOLD | **Benchmark dominated / regime.** Val bull; research −10%; shorts −27%; ≪ buy-hold. **Beta masquerading as TSMOM.** |
| D1 V4 other 6 | No historical gate. |
| D1 V5 | Same beta, milder DD. Not new alpha. |
| H1 V1 ML / 120h mom | **Overfit** (IC 0.52→0.038) + **cost dominated** + shorts the bull. |
| H1 V2–V4 session/break/fade | **No filter** (99%/95%/92% days) or **fading a bull**. Cost + execution mismatch vs “band” story. |
| H1 V5–V9 | **Overfit** persists after clock rename, Ridge, new label, triple barrier, sparse cols. |
| V4 path BE/TRAIL | **Diagnostic.** Tight rules cut TWR. Not a book. |
| Phase 2 D1 active baselines | **Benchmark dominated.** Only BH / always-long work. |
| Phase 2 H1 active + always-long | **Cost dominated.** 1591 round-trips. |
| EXP-001 Linear | Incremental vs Naive **yes**; vs BUY_HOLD **no**. Bull-slice. |
| EXP-002 ML | **Not run** (ladder). Baselines already falsify hourly own-price. |
| EXP-003 | **Not run** (process block). Not a result. |
| Grok desk | **No experiment.** **Execution mismatch** vs every measured book. |
| RSI V9 | **Not a contract.** Mean-reversion heuristic. |
| V30 | **Cost ceiling** (−11.09%/yr) + val spread t 0.18. Carrier dead. |
| V32 | **No signal** (t~1) + cost. 0/5. |
| V1–V8 / XA / OI / DTE / TERM / COT / IV / CARRY (older MT5) | Prior program: **NO_CANDIDATE** or DATA_BLOCKED. Do not reopen. |
| V31 / V35–V37 CN futures | Frozen **NO_CANDIDATE** (other objects). Not a gold fix. |
| V4 follow “viable” narrative | **Selection leakage** on validation_30 + **execution never wired**. |

**Multiple-testing** sits under all of the above: ~75 charged GOLD-relevant looks. One pretty TWR is not a discovery.

---

## 17. Surviving Hypotheses

These are **hypotheses still worth considering**, not facts, not Candidates, not permission to run.

Already **falsified on this Ava GOLD own-price sample** (do not relist as live):

- Own-price D1 trees / 3-class / ATR sit-out  
- Own-price H1 trees, Ridge, sparse, session ORB, Asia fade, triple barrier  
- “12-month TSMOM is independent alpha” (it tracked the bull)  
- “Hourly always-in captures drift after costs”  
- Linear own-price incremental vs BUY_HOLD  

**Still open only if new information exists, or as beta (not research):**

| Hypothesis | Status |
|------------|--------|
| Gold **trend persistence** as **beta** | Observed as BUY_HOLD. Not alpha. No new family. |
| Vol-regime **overlay** that cuts DD without killing BH Sharpe | Not demonstrated on GOLD. A-share O1/O2 overlays REJECT. Would be a **new** pre-registered overlay, not a retune of V5. |
| Breakout / MR on **new** TFs (H4/M15) using only OHLC | **Not recommended.** Frozen H4/M15 exist; Phase 2 refused a fishing pull. Own-price well is exhausted at D1/H1. |
| Macro / USD / real rates as **incremental vs BUY_HOLD** | Price-CFD versions already failed (USD_METAL, DXY z, V32, RATES). A **new PIT series** (TIPS, not bond CFD) would be a new contract — data mostly DATA BLOCKED. |
| Risk-off / event windows (FOMC, CPI, geopolitics) | **Not PIT-tested** on Phase 2 GOLD. Needs a calendar store. |
| Session / liquidity / overnight gap as a **three-state** book | H1 session rules failed; a different labeled overnight book was **not** Phase 2-official. High multiple-testing risk. |
| Options IV-RV, true futures curve, COT | Need data that is **not** in a usable PIT form here. See §18. |

Do not treat gold drift, buy-hold, validation bull, in-sample IC, or a recent month as surviving alpha hypotheses.

---

## 18. Blocked Hypotheses

| Hypothesis | Block |
|------------|-------|
| CFTC COT / managed-money positioning as a new gold family | DATA BLOCKED (no Phase 2 PIT store); prior POSITIONING / OI_COT NO_CANDIDATE |
| COMEX / OG.OPT IV surface, IV-RV | DATA BLOCKED / PAYMENT_REQUIRED; index IV ≠ options; not downloaded |
| Futures curve / warehouse / OI as CFD features | DATA BLOCKED on MT5; TERM_STRUCTURE / OI / DTE / V37 already dead or other-market |
| DXY z-cut / gold-silver / EIA z | Already forbidden reopen; NO_CANDIDATE |
| True TIPS real yield | DATA BLOCKED as a clean PIT store |
| VIX as a long gold factor | Short CFD sample; not a Phase 2 book |
| News / Grok web geopolitics | DATA BLOCKED as research features; Grok is not a strategy |
| Order flow / DOM / tick-farm alpha | DATA BLOCKED |
| Economic calendar surprises | DATA BLOCKED (no store) |
| “Open Logistic because Linear > Naive” | Process + evidence block |
| FINAL OOS peek | Locked |
| H1 OHLC-only ML rerun / M15 copy of H1 rules | Explicit stop `STOP_GOLD_H1_OWN_PRICE_ML_AND_RULES` |
| 100× or 400× as alpha | Category error |

---

## 19. New Research Proposal

**PRE-REGISTER TEXT ONLY. DO NOT RUN.**  
At most three. No RSI/MACD/SMA fishing. No H1 OHLC-only ML rerun. EXP-001/002/003 stay frozen as written. EXP-003 remains **REGISTERED_NOT_RUN** and is **not** reopened because Linear beat Naive.

Own-price incremental vs BUY_HOLD is already answered **no**. Cross-asset **price CFDs already on disk** (DXY, US_500, CrudeOIL, VIX-short) were consumed by V4 / V32 / older families. The honest next work is **new PIT information** or **quotes**, not another TA stack.

### EXP-004 — `GOLD_EVENT_CALENDAR_PIT_QUOTE`

| Field | Pre-register |
|-------|----------------|
| **ID** | EXP-004 |
| **Hypothesis** | Scheduled US macro prints (FOMC, CPI, NFP) and a pre-listed geopolitical calendar change E(net) of a **three-state** GOLD D1 book versus BUY_HOLD in a short window. |
| **Mechanism** | Positioning / risk-premium reset around known timestamps — not OHLC patterns. |
| **Data** | **Not in repo as a PIT store.** Action = **vendor quotes only** (calendar + surprise). Do not scrape. Do not use Grok text. |
| **Timeframe** | D1 decision, event window written **before** purchase (e.g. t−1 close → t+1 open). |
| **Label** | Open→open **net** (spread + assumed 2 bp slip + swap). |
| **Entry / exit** | Next D1 open after event classification; time stop ≤ 5 D1; FLAT default. |
| **Cost** | Live snapshot model (34-pt now rule labeled). |
| **Risk** | Pre-registered stop (price or 1×ATR) + time stop. R% scenario 0.50% — not live. |
| **Benchmark** | BUY_HOLD on the **same** event-adjacent days **and** full-sample BUY_HOLD. |
| **OOS** | RESEARCH through 2025-09-11 only. FINAL OOS locked. |
| **Acceptance** | RESEARCH last-30% **and** first-70% net TWR both **> BUY_HOLD** on the same days; t increment > 0; FDR m incremented **before** run; C0–C13 otherwise. |
| **Rejection** | Lose to BUY_HOLD, or data not PIT, or quote not purchased. **Default expected: do not buy without a written quote.** |
| **Status** | PRE-REGISTER. **DO NOT RUN.** |

### EXP-005 — `GOLD_OPTIONS_IV_QUOTE`

| Field | Pre-register |
|-------|----------------|
| **ID** | EXP-005 |
| **Hypothesis** | A **PIT** gold implied-vol or IV−RV residual has incremental E(net) versus BUY_HOLD (vol-risk premium / crush), not another price SMA. |
| **Mechanism** | Option-implied vol is not in the CFD close. |
| **Data** | **DATA BLOCKED** in-repo. Prior quote path: `OG.OPT` / `LO.OPT`; GLBX no venue IV. Action = **quote only**. Do not auto-buy. Do not use GVZ/index IV as a substitute (already used; not a surface). |
| **Timeframe** | D1, hold 20, non-overlap — only if a PIT store is purchased and frozen **before** fit. |
| **Label / entry / exit / cost / risk / benchmark / OOS** | Same discipline as EXP-001 shell vs **BUY_HOLD**, not vs Naive. |
| **Acceptance** | Incremental net vs BUY_HOLD on RESEARCH 70 and 30; m counted first. |
| **Rejection** | No purchase; or IV series not PIT; or lose to BH. |
| **Status** | PRE-REGISTER / QUOTE. **DO NOT RUN.** |

### EXP-006 — `GOLD_REAL_YIELD_PIT_QUOTE`

| Field | Pre-register |
|-------|----------------|
| **ID** | EXP-006 |
| **Hypothesis** | A **TIPS / real-yield** series (not Ava bond CFD, not UST10 z-cut already run) adds incremental E(net) versus BUY_HOLD via the opportunity-cost channel. |
| **Mechanism** | Real rates vs gold — textbook macro. Prior **CFD/rates** families are **not** this series. |
| **Data** | **DATA BLOCKED** as a clean PIT store. Action = **quote** a dated, knowledge-time-stamped series. Do not reuse `EURO-BUND` / `JAPAN_BOND` CFDs as “real yield.” |
| **Timeframe** | D1, hold 20, FLAT allowed. |
| **Label / entry / exit / cost / risk** | Unified Phase 2 costs; time stop + pre-registered risk stop if it ever becomes a Candidate. |
| **Benchmark** | BUY_HOLD. Increment vs Linear-own-price is secondary. |
| **OOS** | RESEARCH lock; FINAL OOS locked. |
| **Acceptance** | Same dual-window beat of BUY_HOLD; m+1 **before** run. |
| **Rejection** | Quote unused; or series not PIT; or lose to BH (prior rates books failed — base rate is high). |
| **Status** | PRE-REGISTER / QUOTE. **DO NOT RUN.** |

**Not proposed:** EXP-00x H1/M15 OHLC ML; Logistic on EXP-001; leverage overlay to hit 20%; mapping V31 (already NO_CANDIDATE) into GOLD.

---

## 20. Final Recommendation

**DO NOT TRADE**

One label, as required:

- Ava GOLD **auto** path: **DO NOT TRADE**  
- A-share ML1: **separate frozen paper path** (`:9000`). Do not conflate. Do not treat ML1 as permission to send GOLD.  
- Human discretionary long gold is **beta**, not a TradeMind Candidate. This file does not authorize it, size it, or call it alpha.

Not TRADE. Not PAPER ONLY for a new GOLD strategy (paper schema exists; **no** mapped strategy). **RESEARCH ONLY** is the lab’s job; the **authorization** for money on Ava GOLD auto is **DO NOT TRADE**.

### What would qualify TradeMind to try to make money (C0–C13)

Auto-trade **only if every gate passes**. High TWR alone cannot pass. Source: SPEC §30.5, `phase2_mt5/gates.py` `default_phase2_context()`.

| Gate | Meaning | Ava GOLD today |
|------|---------|----------------|
| C0 | Pre-registered write-once contract | Pass for EXP-001/002/003 **as research**. No live strategy contract. |
| C1 | PIT; no future-close fills | Pass on research path |
| C2 | Economic labels (net, cost, MFE/MAE) | Partial/pass on Phase 2 books; fit target still gross |
| C3 | Non-overlap book; overlap disclosed | Pass on Phase 2 books |
| C4 | Unified costs; assumptions labeled | Pass (slip assumed) |
| **C5** | Baselines run; **incremental OOS vs baseline / BUY_HOLD** | **FAIL** — Linear < BUY_HOLD |
| C6 | Research and val same sign; no val search | **FAIL** for V4-style stories (research −10% / val +84%) |
| C7 | FINAL OOS locked, unused | Pass (locked) |
| C8 | Multiple-testing counted | Count exists (~75); not a discovery |
| **C9** | Time stop **and** risk stop | **FAIL** — time stop only |
| C10 | LONG/SHORT/FLAT; not always-in | Phase 2 baselines allow FLAT; V1/Grok do not qualify |
| C11 | Execution = SignalContractV2 | **FAIL** for any live path |
| **C12** | Paper `signal_id` ↔ MT5 deal | **FAIL** — empty ledger; 51 unmapped deals |
| C13 | 20%/month not an optimizer; leverage ≠ alpha | Pass as **policy**; target still UNSUPPORTED |

`gates.py` default context already sets `incremental_oos=False`, `risk_stop=False`, `deal_mapped=False`, `candidate=False`, `do_not_trade=True`.

Additional practical checklist (same spirit): data PIT; no leak; pre-reg; costs; OOS+; **OOS beats BUY_HOLD**; multiple-test; WF; regime; DD; execution identity; paper shadow; sizing. **Candidate cannot pass on high TWR alone.**

---

### Why the system cannot stably profit

Separate causes. Do not merge them into “need a better RSI.”

#### Alpha

No pre-registered active rule has shown incremental expected **net** return versus gold buy-hold on the locked RESEARCH window. Own-price ML fold-OOS IC collapsed. EXP-001 Linear CAGR 7.6% < BH 13.1%. **NO PROVEN ALPHA. NO_INCREMENTAL_ALPHA.**

#### Beta-masquerading

Long gold is real (**+173%** close path, ~13% CAGR). V4 “VIABLE_HISTORICAL” and Linear `research_30` **look like skill** because 2024–26 was a gold bull. Research window V4 **−10%**. Shorts lose. Always-short **−71%**. Directory names like TREND_LS are not evidence.

#### Cost

H1 always-long **−30%** after 1591 round-trips while buy-hold stays positive. Spread 34 pts, 2 bp slip/side, long swap −1.54/night. V30 shows a different carrier can be dead from fees alone. Frequency is not free.

#### Overfit

H1 train IC 0.52 vs fold 0.038; overlapping labels (23/24 hours); trees; calendar columns. Ridge train IC 0.055 proves it is not “missing one feature.” Validation-as-gate selected the bull book.

#### Execution mismatch

The only path that **can** send (Grok, if the owner flips `TRADEMIND_HOT_GROK_SEND`) is **not** the path that was measured. Research never sends. V4 never enters the Grok prompt. Even a working D1 book would be the wrong fill if someone scalp-traded M15. Journal missing ⇒ cannot attribute the 51 terminal deals.

#### No risk engine

No R%, no DD halt, no stale/spread kill switch, no required SL on a Candidate. 0.1 lot is not a model. 400× is margin.

#### Multiple testing

~75 charged looks. Discoveries vs buy-hold = 0. Opening FINAL OOS or Logistic to hunt one survivor is forbidden.

---

### 20% monthly — meaning (existing numbers only)

| Lens | Number |
|------|--------|
| Monthly objective | +20% |
| Compounded annual | ≈ **791%** |
| Gold median month | **+1.11%** (79 RESEARCH months) |
| Gold best month | **+10.7%** |
| Months that hit 20% | **0 / 79** |
| Exposure to turn 1.11% into 20% | **~18×** |
| Gold path DD | **−21.4%** |
| 18× × that path | Ruin (`LEVERAGE_STRESS_TEST.md`) |
| Leverage on P&L **and** DD | Both scale; swap and 34-pt spread scale with size and nights |
| Required true edge | An **alpha** that is not in this repo, **or** beta at unsafe k |
| Cost vs frequency | H1 always-in already net negative at 1×; more frequency worsens the 20% problem |

**TARGET STATUS: UNSUPPORTED.** Do not retune.

---

## Appendix A — Write-once hashes (Phase 2)

| Item | Value |
|------|-------|
| Source commit | `559204773a767a61bff6b6fd20dfd2709b904d2d` |
| data_hash GOLD_D1+META | `0684aa0d4c3836a800f07dbb6214ca0ad28a357a41bf783c09fc81bf65eaa3f9` |
| code_hash `phase2_mt5/*.py` | `a28863e0bd5634006190b10840f4bc0869c84ebfefa80dca863a7a08561edd73` |
| D1 baselines result_hash | `2fba7ad081b8a5507649dda86a3f086c9c04ab62a57f237a71186c7b2c3a3b3d` |
| H1 baselines result_hash | `48d4ccf22fe9cd03b430236333fff5f26890f513921162daa8401e609f901c82` |
| EXP-001 ladder result_hash | `d43b6ba9b52c99407051f8665bd51e126e5ac0bf5a4f23ef9e491c9a99b8fad4` |
| Frozen macro pack sha256 | `7289ff019b7bbbcd9a4364598358c2617082dea9ed512ea37e5145660e59db49` |

## Appendix B — Primary sources

- `docs/TRADEMIND_CONTEXT.md`, `AGENTS.md`, `SPEC.md` §29–§30  
- `AUDIT/PHASE2_FINAL_REPORT.md`, `PHASE2_STATUS.md`, `MULTIPLE_TESTING.md`  
- `AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json`  
- `docs/research_engine/FAILURE_ANALYSIS.md`, `STRATEGY_FORENSIC_REPORT.md`  
- `docs/research_engine/EXP001_*`, `EXP002_*`, `EXP003_*`  
- `docs/research_engine/TARGET_20PCT_MONTH.md`, `LEVERAGE_AND_RISK.md`, `LEVERAGE_STRESS_TEST.md`, `OVERLAPPING_LABEL_AUDIT.md`  
- `docs/research_engine/HOT_MT5_OWN_PRICE_D1_INVENTORY.md`, `HOT_MT5_GOLD_H1_INVENTORY.md`, `HOT_MT5_GOLD_FOLLOW_V4_SPEC.md`  
- `docs/research_engine/V30_MT5_US_XS_DECISION.md`, `V32_MT5_MACRO_POOLED_DECISION.md`  
- `data/market/research_engine/phase2/results/{d1_baselines,h1_baselines,exp001_ladder}/READ.json`  
- `data/market/research_engine/phase2/results/d1_baselines/BUY_HOLD_PATH.json`  
- `research_engine/phase2_mt5/` (read, not rerun)  
- `master/api/app/service/paper_hot_mt5.py`  
- `MT5_GROUND_TRUTH/`  

## Appendix C — UNKNOWN / not sourced

| Item | Why |
|------|-----|
| Ava demo equity curve and P&L attribution from account open | `MT5_JOURNAL.json` missing; 51 deals not mapped |
| Which of the 51 deals were Grok vs human vs other | UNKNOWN |
| Full commission/swap study on those 51 deals | Not computed this session; sampled commission 0.0 |
| Live terminal symbol list **today** (US500/DXY present?) | UNKNOWN; historically US500 missing; frozen pack has `US_500.csv` |
| Phase 2 H4/M15 baseline TWRs | **Not run** (deliberate). Packs exist. |
| Current V4 follow mtm after 2026-09-11 | Last documented STATUS in the follow spec; not re-read as a new mark |
| Monte Carlo / bootstrap p-values | Scaffold only; unused without a Candidate |

**End of Case File. Candidate = FALSE. Execution = NOT AUTHORIZED. DO NOT TRADE.**
