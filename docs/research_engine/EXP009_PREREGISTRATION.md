# EXP-009 Pre-registration Contract — GOLD × DFII10

> Write-once **2026-09-14**, after pack `b068262f`, **before any EXP-009 score**.  
> Experiment id: `EXP-009`. Family id: `EXP-009-F1` / `DFII10_D20_SIGN`.  
> `candidate=false`. `EXECUTION: NOT AUTHORIZED`. Do not run in the session that writes this file.

```
CANDIDATE = FALSE
EXECUTION = NOT AUTHORIZED
EXP-008 = BLOCKED
EXP-009 = PREREGISTERED / READY_TO_RUN
LIVE TRADING = FORBIDDEN
order_send = FORBIDDEN
```

This file **is** the decision / position / abstention freeze. A later session may run **this family only**. A different transform or a second model is a **new id** and a new `m`.

---

## 1. Research question

**Primary:** Does PIT-correct **DFII10** (10-year TIPS real yield) provide **incremental net** value for Ava `GOLD` **beyond GOLD BUY-HOLD**?

Not: GOLD strategy return > 0.  
Not: 20%/month.  
Not: Linear beat Naive.

\[
r_{\text{book}} = \beta \cdot r_{\text{gold}} + \alpha(Z_{\text{DFII10}}) - \text{costs} - \text{execution gap}
\]

H0: α = 0 (the book is gold beta plus noise and extra turnover).  
H1: the pre-registered three-state rule has incremental **net** TWR vs BUY_HOLD on **both** RESEARCH 70 and RESEARCH 30.

---

## 2. Economic rationale

TIPS 10y real yield is the real opportunity cost of holding a non-yielding metal. **Hypothesis (not a fact):** a **rise** in knowledge-aligned DFII10 lowers E[net gold]; a **fall** raises it. Prior RATES_V1 used **nominal DGS10** and is **NO_CANDIDATE**. That does **not** prove DFII10 works; it only says the object is different.

---

## 3–4. Frozen dataset + hash

| Field | Lock |
|-------|------|
| `dataset_id` | `EXP009_DFII10_PIT` |
| File | `data/market/research_engine/phase3/exp009/DFII10_raw.csv` |
| `sha256` | `790b6d725a0d170b7e701f85880bbb57515a9033634ec02d0d9633fcf7fe7b1f` |
| Coverage on disk | 2003-01-02 → 2026-09-10, 5927 numeric rows |
| GOLD D1 | existing `GOLD_D1.csv` (bar **OPEN** `T00:00:00Z`) + Phase 2 META costs |

**Forbidden as inputs:** live FRED, current FRED CSV, DGS10, DXY, Bund, CPI, Grok, 2003–2004 ALFRED backfill as a feature source (see §27).

If the hash changes, **EXPERIMENT INVALID**.

---

## 5–7. PIT, knowledge time, decision clock

```text
knowledge_time_utc <= decision_time_utc
```

**decision_time_utc(t)** = GOLD `timestamp_utc(t+1)` (next bar **open** = fill clock).  
Signal is formed at close of bar t; fill is open t+1.

**Forbidden (EXPERIMENT INVALID):**

- `observation_date == GOLD date`
- same-calendar-date join to GOLD **OPEN**
- same-day-open use of that day’s DFII10
- forward-fill a yield **before** its `knowledge_time_utc`

Worked constraint (from acquire report): print 2018-12-12 has `knowledge_time_utc=2018-12-13T23:59:59Z` (FRED T+1). It is **not** usable for GOLD open `2018-12-13T00:00:00Z`. First legal fill is a decision_time **≥** that knowledge time.

Knowledge rule on the frozen file (do not recompute from live FRED):

```text
max(H.15 16:15 America/New_York on observation_date,
    realtime_start 23:59:59Z)
```

except `alfred_pre_history=1` (H.15 only). Those rows are **outside** the primary window.

---

## 8. Feature rules

**One feature. No search.**

At GOLD decision bar t (after warmup):

1. `y_t` = latest frozen DFII10 `value` with `knowledge_time_utc <= decision_time_utc(t)` and `observation_date >= 2018-01-01` and `alfred_pre_history=0`.
2. `y_{t-20}` = the same construction 20 **GOLD decision bars** earlier (not 20 calendar days on the raw DFII10 file).
3. `z_t = y_t - y_{t-20}`  (percentage points, e.g. 1.08 − 0.90 = 0.18)
4. `score_t = -z_t`  (real yield **up** → gold score **down**)

Missing `y_t` or `y_{t-20}` → feature invalid → **FLAT**.

No RSI, SMA, ATR, GOLD OHLC features, DXY, or extra DFII10 lags. No IC-picked transforms.

---

## 9. Candidate model families

**This contract registers exactly one family.** Amendment A3 / Phase 3: one model per information layer.

| id | What | Selection |
|----|------|-----------|
| `EXP-009-F1` `DFII10_D20_SIGN` | `score_t = −Δ20` as above | **This is the family.** There is no bake-off. |

**Not in this contract:** Naive/Linear/Ridge/Logistic/LightGBM/XGBoost, extra lookbacks, extra thresholds.

A second family = new experiment id + `m += 1` **before** that run. **Do not** pick the prettier model after seeing numbers.

The “model” outputs a **score**, never `BUY`/`SELL`.

---

## 10–13. Strategy mapping, sides, entry, exit

```text
PIT DFII10 → Feature (z, score) → Decision layer → LONG|SHORT|FLAT
    → Position / time-stop → Net P&L vs BUY_HOLD
```

`Model ≠ Strategy ≠ Risk ≠ Benchmark`.

### LONG / SHORT / FLAT

Reuse SignalContractV2 only: `LONG` / `SHORT` / `FLAT`.  
`FLAT` = ABSTAIN / NO_POSITION.

```text
The strategy is allowed to abstain when expected edge is insufficient
after accounting for transaction costs and uncertainty.
```

**Case A** — direction and a non-zero score:  
`score_t > 0` → **LONG**; `score_t < 0` → **SHORT**.

**Case B** — direction unreliable: feature invalid → **FLAT**.

**Case C** — edge may not cover cost: this family has **no frozen gold-beta**, so it **cannot** apply EXP-001’s 20 bp gold-return hurdle without inventing an elasticity. Disclosed: cost-aware FLAT here is **invalid/zero change only**. **Round-trip costs still hit the book** (Phase 2). A tiny-z always-in book is expected to lose to BUY_HOLD after costs — that is the economic filter, not a tuned FLAT%.

`prediction accuracy ≠ tradability`. `score > 0` is not a live order.

### Entry

- Next GOLD D1 **open** after a valid signal (`t+1`).
- Sizing: **+1 / −1 / 0** research units. Not 400×. Not 0.1 lot as a risk model.
- Non-overlapping: after a fill, next signal at exit bar.

### Exit (frozen)

Fixed horizon, same as EXP-001 / Phase 3 plan:

| From → To | When allowed |
|-----------|----------------|
| LONG → FLAT | Time stop **20** D1, exit at `open[t+1+20]`, if next score is 0/invalid |
| SHORT → FLAT | Same |
| LONG → SHORT | Same clock, if next score < 0 |
| SHORT → LONG | Same clock, if next score > 0 |
| Any → same side | Roll: close and re-open (pay costs) if the new score keeps the side |

**No** mid-hold SL/TP/trail. **No** dynamic exit invented after seeing MAE/MFE.

Live Candidate would still fail C9 / P3-G12 until a **new** contract adds a risk stop. This research book is **time-stop only** and **cannot** be promoted to auto-trade on this document alone.

---

## 14. Cost model

**Phase 2 unified** (`EXP001_GOLD_D1_OWNPRICE_CONTRACT.md`):

- Spread formula as EXP-001 (PARTIAL today-floor labeled)
- Slip **ASSUMED_2BP_PER_SIDE** (`0.0002`)
- Swap from META (`swap_long=-1.54`, `swap_short=+0.64`, rollover 3-day=5)
- Commission 0 unless deals say otherwise
- Stress 1× / 2× / 3× on (spread+slip); Stress = 3× + 5 bp/side extra

Do not drop costs to make α look positive.

---

## 15. Risk limits (research book)

- Exposure: {−1, 0, +1} only
- Account leverage **400× is not strategy leverage**
- Risk modes 0.25/0.50/1.00/2.00% = **scenarios for a later paper**, not this run
- No leverage-to-20%
- MaxDD is **reported** vs BUY_HOLD path; “win only by missing 2022” = gate fail (P3-G9)

---

## 16–18. Benchmark and metrics

**BENCHMARK = GOLD BUY-HOLD** (Phase 2 definition: one LONG from first research next-open to last research open, one round-trip).

Same RESEARCH window, same 1× capital, same price basis, same cost convention.

**Primary metric:** incremental **net** TWR (strategy − BUY_HOLD) on RESEARCH **70 and 30** after warmup. Both must be **> 0**.

**Secondary (report, do not optimize):** strategy net TWR, BH TWR, incremental CAGR, MaxDD, vol, Sharpe, Sortino, Calmar, PF, expectancy, turnover, exposure, trade count, monthly distribution — **Phase 2 `metrics.py` definitions**. Do not invent a second Sharpe.

Also report, separately:

| Name | Meaning |
|------|---------|
| PREDICTIVE EDGE | Does `score` rank next-20d gold **gross** at all? |
| ECONOMIC EDGE | E[net \| signal] after costs |
| STRATEGY EDGE | Book net TWR |
| INCREMENTAL ALPHA | Book net − BUY_HOLD net |

`predictive = yes` and `economic = no` = **failure**.

---

## 19. Multiple testing

Charged **before this run** (see `AUDIT/MULTIPLE_TESTING.md`):

```text
m := ~75 + 1  →  ~76
family = EXP-009-F1 DFII10_D20_SIGN
```

No second lookback, no second dead-zone, no model shopping. White RC / SPA **not** run on graves.

---

## 20. OOS protocol (do not redraw)

| Window | Dates | Use |
|--------|-------|-----|
| PRIMARY RESEARCH | **2018-12 → 2025-09-11** (GOLD bars from 2018-12-12 through **2025-09-11**) | Official numbers |
| Warmup | first **20** GOLD decision bars with a valid `y` (all `observation_date >= 2018-01-01`) | No reported P&L |
| RESEARCH 70 / 30 | first 70% / last 30% of RESEARCH bars **after warmup** | Report both; **not** a search split |
| FINAL_OOS | **2025-09-12** → last bar | **LOCKED. Do not score. Do not pick.** |

`research_engine/phase2_mt5`: `RESEARCH_END=2025-09-11`, `FINAL_OOS_START=2025-09-12`. **Do not change.**

Do **not** use 2003–2004 / `alfred_pre_history=1` to “add sample.”

Embargo: if any statistic uses a future label, embargo **hold+1 = 21**. The official book is non-overlapping so labels do not stack in the ledger.

---

## 21. Activity / abstention diagnostics

**Abstention is allowed. Unbounded abstention without diagnosis is not acceptable.**

Every official result block **must** include:

```text
total_decision_bars
long_bars
short_bars
flat_bars
exposure_rate          # (long+short)/total
trade_rate             # position_changes / total
long_fraction
short_fraction
flat_fraction
number_of_position_changes
number_of_trades
```

These are **diagnostics**, not optimization targets.  
**No** min trades, min exposure, or max FLAT% may be set after seeing results.

---

## 21b. Degenerate strategy check (review, not a tuned gate)

Report as **DEGENERATE / INSUFFICIENT_COVERAGE** (not Candidate) if, on RESEARCH after warmup, **any** of:

- always LONG (flat_fraction = 0 and short_fraction = 0)
- always SHORT
- almost always FLAT: **flat_fraction ≥ 0.999** and **number_of_trades ≤ 3**
- extremely sparse: **number_of_trades ≤ 3** on the full RESEARCH book

The 0.999 / 3 cut is a **pre-registered degeneracy detector** (empty almost-never-trade lottery), **not** a target like “FLAT ≤ 40%.”  
Always-in sign-following is **also** reported (exposure_rate ≈ 1); it is not auto-Candidate. It still must beat BUY_HOLD **net** on both windows.

90% FLAT with a documented reason (feature often invalid, zero Δ) can be **honest and FAIL** the economic gate. It is not tuned away.

```text
ABSTENTION IS ALLOWED
BUT ABSTENTION MUST BE DIAGNOSTICALLY AUDITED
No minimum trade frequency may be tuned after seeing results.
```

---

## 22. Candidate gate

`VIABLE_HISTORICAL` is **not** Candidate.  
Use SPEC §30.5 C0–C13 **and** Phase 3 P3-G0–G12. Automatic **FALSE** if: beat cash only; bull-only; gross-only; validation-only; leverage-as-alpha; 20% as fit target; degenerate activity per §21b.

This contract’s research book **fails C9 / P3-G12** (no risk stop) until a **new** write-once addendum. So **even a pretty TWR cannot be Candidate / auto-trade** on EXP-009-F1 alone.

User list (all required for any future Candidate claim):

1. PIT correctness  
2. No future leak  
3. Reproducibility (frozen hash + this file)  
4. Explicit transaction cost  
5. OOS positive incremental **net**  
6. OOS > GOLD BUY-HOLD on the predefined dual-window rule  
7. Multiple-testing correction (m charged first)  
8. Robustness across 70/30 and not a single year  
9. Acceptable DD vs BH path  
10. Executable decision logic (SignalContractV2)  
11. Non-degenerate activity (diagnostics + §21b)  
12. Reproducible from frozen dataset  

---

## 23. Failure conditions

- Hash / PIT / date-join violation → **INVALID**  
- Substitute DGS10/DXY/Bund/CPI/2003 backfill → **INVALID**  
- Incremental net ≤ 0 on either RESEARCH 70 or 30 → **NO_INCREMENTAL_ALPHA**  
- Predictive edge without economic / incremental edge → **FAIL**  
- Degenerate per §21b → **DEGENERATE / INSUFFICIENT_COVERAGE**  
- Opening FINAL OOS or retuning 20/Δ/sign → **INVALID**  
- Reopening V9/V10/D1/H1/V4/RSI/Grok into this book → **INVALID**

---

## 24. Reproducibility

| Item | Value |
|------|--------|
| Contract | `docs/research_engine/EXP009_PREREGISTRATION.md` |
| Data hash | `790b6d725a0d170b7e701f85880bbb57515a9033634ec02d0d9633fcf7fe7b1f` |
| Pack commit | `b068262f9211a9b91a8931c533d727396f9b74fa` |
| Code (when written) | sha256 of the runner; must not change the rule |
| Result | write-once `READ.json`; no overwrite |

---

## 25. Prohibited actions

Train/search/grid; pick lookback 10/40; pick a yield dead-zone after seeing 0.63; LightGBM because “rules are too simple”; 20%/month as loss; leverage; `order_send`; live FRED; FINAL OOS peek; fuse V4/RSI/Grok; edit `cn_futures_v31/README.md` into this commit.

---

## 26. 20%/month

```text
TARGET_MONTHLY_RETURN = 20%+
```

**LONG-TERM INVESTMENT ASPIRATION only.**  
Not a training loss, HP objective, Candidate objective, threshold objective, or backtest objective.

---

## WHY / WHAT / EXPECTED / RISK

- **WHY:** Pack is frozen; Phase 3 one-liner is not a full decision policy.  
- **WHAT:** Freeze one sign family, three-state, BUY_HOLD increment, diagnostics, m+1.  
- **EXPECTED EFFECT:** Honest later run. Base rate: rates-like books already failed on the **wrong** object; this may also fail vs BUY_HOLD.  
- **RISK:** Treating sign-always-in as alpha; using 2003 backfill; calling PREREGISTERED a Candidate.

**STOP after this file. Do not run EXP-009 until a new explicit instruction.**
