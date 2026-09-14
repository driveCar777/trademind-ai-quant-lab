# MT5 Alpha Candidate Map

**Date:** 2026-09-14  
**Market:** Ava `GOLD` (logical XAUUSD).  
**Question:** which **information families** could, in principle, produce **incremental net return versus Gold Buy-Hold** — not which TA rule might print a high TWR.

```
CANDIDATE: FALSE
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
```

At most **eight** families. Not 50 strategies. Labels are research objects, not permission to run. Data status cites `AUDIT/MT5_ALPHA_DATA_AVAILABILITY.md`. Past experiments cite Phase 1/2 write-once books and V2.0 / V4 / V32 / V30 decisions.

**How incremental alpha is proved (all families):** pre-register → freeze data → non-overlapping net book (spread + labeled slip + swap) → RESEARCH through 2025-09-11 only → **both** first-70% and last-30% of RESEARCH **net TWR > BUY_HOLD on comparable 1× capital** → increment statistically credible after adding **m** → regime/subperiod not a single bull slice → executable later on Ava GOLD. Beat cash but lose to BUY_HOLD → **FALSE**. Gross-only → **FALSE**. Validation-only → **FALSE**.

---

## 1. Cross-Asset Divergence

| Field | Statement |
|-------|-----------|
| **Economic logic** | Gold is priced in USD and co-moves with real rates, the dollar, and sometimes oil/risk assets. A **residual** (gold move not explained by a named external close) could be a risk-premium shock rather than gold drift. |
| **Why it could be independent of Gold Buy-Hold** | BUY_HOLD is always long gold. A divergence rule is **three-state**: long / flat / (rarely) short when the residual is large. If the residual has E(net) after costs, the book can beat a always-long path by sitting out dollar-driven gold declines. |
| **Required data** | PIT external D1 closes aligned to GOLD: dollar index **or** TIPS; optionally oil / equity. Same-bar close only if that close is known before the gold decision. |
| **Data status** | DXY **AVAILABLE** frozen, **UNAVAILABLE** live. US_500 frozen only. CrudeOIL **AVAILABLE** live. TIPS **UNAVAILABLE**. FX majors live (dollar proxy). |
| **Lookahead risk** | Using a slow macro print on the same UTC date; merging live GOLD (to 2026-09-11) with frozen DXY (to 2026-08-28) without an as-of rule; treating FX as “new DXY.” |
| **Why past experiments did not test *this*** | They tested **other** objects: `USD_METAL_V1` = 252-day **DXY z into GOLD/SILVER** (KILLED). V32 = one LightGBM on 63 CFDs (NO_CANDIDATE). XA/XR gold-oil books in the master-backtest graveyard. EXP-003 was the incremental Linear(own-price+layer) test and is **REGISTERED_NOT_RUN** (process block after EXP-001 lost to BUY_HOLD). Nobody ran “residual vs BUY_HOLD” as Phase 2 official. |
| **Label** | Next D1 open→open **net** hold=20, non-overlap. |
| **Signal** | One pre-registered residual or layer — **not** a z_cut search, **not** gold-silver ratio. |
| **Benchmark** | BUY_HOLD first; ALWAYS_LONG second. Linear own-price is a control, not the economic hurdle. |
| **How to prove incremental alpha** | Dual-window net TWR > BUY_HOLD; increment t>0; m counted **before** run. |
| **Phase 3 action** | **Do not reopen** DXY z / gold-silver / V32 / XA. EXP-003 stays frozen. A *new* ID would still be **blocked** unless the Z is a **new** series (see TIPS / events), not another CFD close. |

---

## 2. Macro Event Surprise

| Field | Statement |
|-------|-----------|
| **Economic logic** | Scheduled US prints (FOMC, CPI, NFP) reset real-rate and dollar expectations. Gold’s **event-window** return can differ from its unconditional drift (risk-premium jump, then mean reversion or trend continuation). |
| **Why it could be independent of Gold Buy-Hold** | BUY_HOLD holds through every print. A three-state book that is **FLAT except around classified surprises** (or that flips only on surprise sign) is not “long gold in a bull.” Incremental alpha = event-adjacent net minus BUY_HOLD on the **same days** and vs full-sample BUY_HOLD. |
| **Required data** | Release **timestamp UTC**, event type, **first print**, **consensus** (so surprise = first − consensus), knowledge time ≤ signal time. Optional: pre-listed geopolitical dates with the same discipline. |
| **Data status** | **UNAVAILABLE.** A-share calendar is the wrong object. Grok text is not PIT. |
| **Lookahead risk** | Revised prints; consensus backfilled; using “what we know now” about wars; timestamp in local TZ vs UTC bars. |
| **Why past experiments did not test it** | No store. V11 coverage already marked FOMC/CPI/NFP unstudyable without consensus. Phase 2 did not invent a calendar. |
| **Label** | Open→open **net** on a **pre-registered** window (e.g. t−1 close decision → ≤5 D1 time stop). |
| **Signal** | Surprise sign / bucket written **before** purchase. FLAT default. |
| **Benchmark** | BUY_HOLD on event-adjacent days **and** full RESEARCH BUY_HOLD. |
| **How to prove incremental alpha** | Both RESEARCH 70/30 net > BUY_HOLD; not one CPI year. |
| **Phase 3 action** | Family with the highest remaining economic chance. Experiment = **acquire PIT calendar first** (`EXP-008`). No scrape. No purchase without a written quote. |

---

## 3. Volatility Regime

| Field | Statement |
|-------|-----------|
| **Economic logic** | Gold’s drift may not compensate for variance in high-vol states; a sit-out can raise E(net) per unit risk. That is **beta timing**, not a new price pattern. |
| **Why it could be independent of Gold Buy-Hold** | Only if sitting out high-vol (or wide-spread) states has **higher net TWR** than staying long — not merely a prettier Sharpe while missing the bull. Independence fails if the rule is “miss 2022, keep 2024–25.” |
| **Required data** | GOLD D1 OHLC (RV/ATR) and/or historical bar `spread`. Optional: a **long** VIX/GVZ series. |
| **Data status** | RV/spread **AVAILABLE** on official GOLD. VIX CFD **37 bars** dirty. GVZ **BLOCKED** (IMPLIED_VOL_V1 killed). |
| **Lookahead risk** | Using today’s META 34-pt spread as a historical feature; picking vol percentile after seeing 2022. |
| **Why past experiments did not test *this exact* overlay** | V5 = inverse-vol **on V4 sign** (same beta). Phase 2 VOL_FILTER = momentum **only if** ATR high → RESEARCH **−30%**. A-share O2 vol overlay **REJECT**. Nobody ran a **BUY_HOLD sit-out** with a frozen 90th-percentile rule vs BUY_HOLD as the hurdle. |
| **Label** | Same Phase 2 D1 net hold=20. |
| **Signal** | Pre-registered: FLAT if RV20 **or** spread percentile > 0.90 of trailing 252; else LONG. No grid. |
| **Benchmark** | BUY_HOLD. |
| **How to prove incremental alpha** | Dual-window net TWR > BUY_HOLD (hard). MaxDD improvement **alone** is not enough. |
| **Phase 3 action** | Only on-disk family that is not a killed reopen (`EXP-007`). Prior says **likely FAIL**. Not OHLC ML. |

---

## 4. Momentum + Cross-Asset Confirmation

| Field | Statement |
|-------|-----------|
| **Economic logic** | 12-month gold momentum is textbook trend. Confirmation from dollar/risk would claim “trend only when macro agrees.” |
| **Why it could be independent of Gold Buy-Hold** | Only if confirmation **removes** bull-beta trades that lose after costs and **keeps** those that beat BUY_HOLD. On this sample, raw TSMOM **lost** to BUY_HOLD (V4 research **−10%**; full-sample TWR weaker than buy-hold ~**+250%** to 2026-09-11). Confirmation usually **reduces** exposure further → even harder to beat BUY_HOLD TWR. |
| **Required data** | GOLD + DXY or TIPS (PIT). |
| **Data status** | GOLD AVAILABLE. DXY frozen. TIPS UNAVAILABLE. |
| **Lookahead risk** | Choosing the confirm series after seeing V4 validation +84%. |
| **Why past experiments did not test it** | V4/V5 and Phase 2 MOMENTUM/TREND_FILTER were **own-price**. EXP-003 (add a layer to Linear) did not run. |
| **Label / signal / benchmark** | Same D1 net 20; momentum sign **and** one frozen confirm; BUY_HOLD. |
| **How to prove incremental alpha** | Dual-window > BUY_HOLD — historically implausible given V4. |
| **Phase 3 action** | **Do not run.** Confirmation of a beta book is not a new family. |

---

## 5. Mean Reversion under a specific regime

| Field | Statement |
|-------|-----------|
| **Economic logic** | After a classified shock (event, liquidity spike), gold may overshoot and revert. Unconditional MR is just fading the bull. |
| **Why it could be independent of Gold Buy-Hold** | A **short-horizon, FLAT-default** book around a **named** regime is not always-long. Unconditional MR is the opposite of BUY_HOLD and already lost (Phase 2 MEAN_REVERSION **−40%**; H1 Asia fade **−80%**). |
| **Required data** | The **regime series** (events or PIT liquidity). GOLD OHLC alone is not a new regime. |
| **Data status** | Regime Z **UNAVAILABLE** (events) or **dirty/killed** (GVZ, COT). |
| **Lookahead risk** | Defining “shock” after seeing losers; ORB/RSI reruns. |
| **Why past experiments did not test a *conditional* MR** | They tested **unconditional** MR and session fades. No event store. |
| **Label / signal / benchmark** | Short time stop; FLAT default; BUY_HOLD + event-day BUY_HOLD. |
| **How to prove incremental alpha** | Same dual-window vs BUY_HOLD; m+1. |
| **Phase 3 action** | Fold into **event surprise** if a calendar is acquired. Do not reopen RSI/Asia fade. |

---

## 6. Positioning Extremes

| Field | Statement |
|-------|-----------|
| **Economic logic** | Crowded managed-money shorts (or commercial extremes) can mark a risk-premium washout in gold futures. |
| **Why it could be independent of Gold Buy-Hold** | Signals are weekly and sparse; the book is **often flat**. That is not 2019–25 gold drift. |
| **Required data** | CFTC disagg COT with **Friday 21:00Z** knowledge (not Tuesday as-of). |
| **Data status** | Friday pack **exists** (`tm-alt-CFTC-GOLD-COT-W1-20260828-000002`, 451 weeks). Tuesday pack is a **leak**. |
| **Lookahead risk** | Tuesday as-of; lowering z_cut after sparse occupancy. |
| **Why past experiments *did* test it** | POSITIONING_V1 **NO_CANDIDATE** (Xavier 4, 01=04). Validation n too small after leak-free Friday. |
| **Label / signal / benchmark** | Frozen contract: hold=5, z_lookback=52, z_cut=2 — **do not retune**. |
| **How to prove incremental alpha** | Already failed research+validation+FDR. A new proof would need a **new** positioning object, not a new z_cut. |
| **Phase 3 action** | **STOP** this family on existing COT. |

---

## 7. News Shock / Sentiment Change

| Field | Statement |
|-------|-----------|
| **Economic logic** | Unscheduled geopolitical or policy headlines can reprice gold faster than D1 OHLC features. |
| **Why it could be independent of Gold Buy-Hold** | Event-driven, often flat, not a 12-month long. |
| **Required data** | Timestamped headline store with knowledge time, a **pre-registered** relevance rule, and no peeking at future text. |
| **Data status** | **UNAVAILABLE.** Grok web is not reconstructable. |
| **Lookahead risk** | Survival of “important” news; LLM summaries written after the move. |
| **Why past experiments did not test it** | DATA_BLOCKED since post-V16. Phase 2 forbade news timestamps without a PIT store. |
| **Label / signal / benchmark** | Short window net; BUY_HOLD. |
| **How to prove incremental alpha** | Same gate; plus text-PIT audit. |
| **Phase 3 action** | **Do not run.** Do not use Grok as this family. Prefer **scheduled** events (family 2) if anything is acquired. |

---

## 8. Microstructure / Session effects

| Field | Statement |
|-------|-----------|
| **Economic logic** | Spread and session liquidity change the **cost** of being long and, sometimes, the conditional return (inventory / dealer risk). Overnight gaps are a different object from London ORB. |
| **Why it could be independent of Gold Buy-Hold** | BUY_HOLD pays **one** round-trip. A liquidity overlay that **exits and re-enters** pays more; it beats BUY_HOLD only if wide-spread days have **negative** E(net) large enough to cover extra costs. Session **scalps** are the opposite of BUY_HOLD and already lost after 34-pt spread + 2 bp slip + swap. |
| **Required data** | Official GOLD `spread` + OHLC. Tick/DOM would be better and **UNAVAILABLE**. |
| **Data status** | Bar spread **AVAILABLE**. Tick farm **UNAVAILABLE**. H4/M15 packs exist; **not** Phase 2 official. |
| **Lookahead risk** | META_now spread as a feature; copying H1 ORB to M15. |
| **Why past experiments did not test *spread-as-signal*** | Spread was a **cost** (and a PARTIAL today-floor), not a sit-out feature. Session **entries** (H1 V2–V4) were always-on-ish and net negative. |
| **Label / signal / benchmark** | Combined with family 3 in `EXP-007` (spread **or** RV percentile). BUY_HOLD. |
| **How to prove incremental alpha** | Dual-window net > BUY_HOLD after **extra** round-trips. |
| **Phase 3 action** | Allow **one** write-once overlay. **STOP** ORB / Asia fade / M15 copies. |

---

## Map → Phase 3 experiments

| Family | Worth a **new** contract? | Experiment |
|--------|---------------------------|------------|
| 1 Cross-asset CFD | No (killed / EXP-003 frozen) | None. Do not reuse EXP-003. |
| 2 Event surprise | Yes, if data is acquired | **EXP-008** |
| 3 Vol regime | One overlay only | **EXP-007** (with family 8) |
| 4 Mom + confirm | No | None |
| 5 Conditional MR | Only with events | Covered by EXP-008 |
| 6 Positioning | No on existing COT | None |
| 7 News | No store | None |
| 8 Microstructure | Spread as feature only | **EXP-007** |
| TIPS real yield (macro, not a CFD) | Yes, if data is acquired | **EXP-009** (see plan; not a DXY reopen) |

Case File §19 EXP-004/005/006 were pre-register text only. This map **does not run** them. Official next IDs are **EXP-007 / EXP-008 / EXP-009** in `AUDIT/MT5_PHASE3_ALPHA_DISCOVERY_PLAN.md`.
