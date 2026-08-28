# Regime Transition V0.9 Contract

Locked 2026-08-26. Design / contract only. **Not executed.**

This file is the write-once experiment contract. Implementation must copy these fields, not invent new ones.

Parents: `ALPHA_COVERAGE_MAP_V1.md`, `TRADEMIND_ALPHA_ROADMAP_12M.md`, `MARKET_STATE_V0.5` (V0.5 plan).  
Not a live book. Not MT5. Not Final OOS. Not HYP-0001. Not V0.6 retune. Not V0.8 expansion.

```text
search_space_hash =
3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea
```

Hash payload is the canonical JSON in §11. Implementation must reproduce the same hash before any job starts.

---

## 0. Family — FAM-RT-DELTA-0001

New family. Not a child of HYP-0001. Not `FAM-FD-XASSET-0001`.

| field | value |
| --- | --- |
| family_id | `FAM-RT-DELTA-0001` |
| discovery_id | `REGIME_TRANSITION_V0.9` |
| status | `LOCKED_NOT_RUN` |
| claim type | regime **transition** (Δstate), not state level |
| hypothesis_count | **3** |
| hypothesis_ids | `HYP-RT-0001`, `HYP-RT-0002`, `HYP-RT-0003` |
| parent_hypothesis_id | null |
| timeframe | D1 only |
| hold_bars | **5** aligned rows of the **target** series |
| seed | 20260825 |

### Mechanism

Because positioning and risk budgets adjust when a realized regime **changes**, the conditional expected return of the target over the next few days can differ from the unconditional same-side return.

The trade is taken **only on the transition bar** (and then held a fixed 5 D1 steps).  
It is not taken on every bar that merely *is* TREND_STRONG or HIGH vol.

### Not

- V0.5 / V0.6: “while TREND_STRONG, do breakout / MOM-DIR”
- V0.6: RANGE fade every EXTENDED bar
- V0.8: dollar-proxy return → next GOLD/OIL
- Scanning ADX period, SMA lengths, hold 3/8/10, or extra IDs
- Flipping predicted sign after seeing results

---

## 1. Dataset contract

### 1.1 Parents (immutable, do not copy-overwrite)

Primary targets only:

| logical | dataset_id | role |
| --- | --- | --- |
| OIL | `tm-market-OIL-D1-20260825-000001` | target of HYP-RT-0001 |
| GOLD | `tm-market-GOLD-D1-20260825-000001` | target of HYP-RT-0002 and HYP-RT-0003 |

EURUSD / USDJPY D1 are **not** in this search space. Do not add them to “get a second symbol”.

State features are computed on the **target’s own** D1 series. No cross-asset feature in V0.9.

### 1.2 Clock

```text
feature on row t  uses only bars with date <= t
entry             = NEXT_BAR_OPEN of target at t+1
exit              = open of row t+1+hold_bars, or 1.5×ATR stop
hold_bars         = 5
horizon is NOT calendar +5 if a date is missing
use the target series' own next 5 aligned rows
```

Sunday D1 bars are legal rows. Do not skip them to manufacture weekdays.

### 1.3 Windows (per target, frozen before PnL)

```text
sorted unique UTC dates of that parent D1
  RESEARCH     = first 70%
  VALIDATION   = next 15%
  FINAL_OOS    = last 15%   ACCESS DENIED
```

Write `WINDOW.json` per target at implementation, **before** any costed equity.  
Do not reuse V0.8’s 1993-day join as authority (that clock drops dates the target actually has).

Trade `(entry, exit)` must stay inside the same role. If hold would cross the role boundary, skip (do not peek OOS).

### 1.4 Warmup

SMA50 / ADX14 / ATR / VOL percentiles need history.  
Rows without a defined V0.5 state are not signal-eligible. Count them in `n_warmup_drop`.

---

## 2. State source (locked, do not retune)

Copy `MARKET_STATE_V0.5` axes used here. Periods are not parameters.

| axis | lock |
| --- | --- |
| TREND | UP: close>SMA20 and SMA20>SMA50. DOWN: inverse. Else FLAT |
| TREND_STRENGTH | ADX14 ≥ 25 → STRONG, else WEAK |
| VOL | TR/close vs RESEARCH 33/67 percentiles, **frozen once**, then applied to VALIDATION |

LOCATION / MOMENTUM / ACTIVITY / FRICTION: compute if needed for WIDE skip.  
They are **not** extra hypotheses.

VOL gate freeze: RESEARCH predictors only, same spirit as V0.8 Q3 freeze.

`FRICTION=WIDE` on the **signal** bar → skip new entry (V0.6 definition on target).

---

## 3. Three hypotheses (no fourth)

Feature = 1 if the named transition occurs on t, else 0.  
No scanned threshold beyond the locked V0.5 definitions.

### 3.1 HYP-RT-0001 — VOL_SHOCK → OIL short

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-RT-0001` |
| title | Vol enters HIGH → next 5D OIL down |
| hypothesis | After OIL D1 VOL switches into HIGH, the next 5-step costed OIL return is negative. |
| H0 | Conditional mean = unconditional same-side (always-short eligible days) mean. |
| H1 | Conditional mean is **negative** and economically non-zero after cost. |
| target | OIL |
| feature | `VOL[t-1] ≠ HIGH` AND `VOL[t] = HIGH` |
| predicted_sign | −1 |
| side | short |
| hold_bars | 5 |

Economic story: a realized vol shock is a risk-budget event; crude is the risk asset in this universe.

Not: “stay short whenever VOL is HIGH” (that is state level; V0.5/V0.6 already touched HIGH_VOL as a skip).

### 3.2 HYP-RT-0002 — ENTER_STRONG_UP → GOLD long

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-RT-0002` |
| title | Trend strength ignites UP → next 5D GOLD up |
| hypothesis | After GOLD D1 TREND_STRENGTH switches WEAK→STRONG while TREND=UP, next 5-step costed GOLD return is positive. |
| H0 | Conditional mean = unconditional same-side (always-long eligible days) mean. |
| H1 | Conditional mean is **positive** after cost. |
| target | GOLD |
| feature | `STRENGTH[t-1]=WEAK` AND `STRENGTH[t]=STRONG` AND `TREND[t]=UP` |
| predicted_sign | +1 |
| side | long |
| hold_bars | 5 |

Economic story: ignition (a constraint starting to bind) is a different object from “being in TREND_STRONG every day”.

Not: V0.6 MOM-DIR, which could fire on every bar inside the state.

### 3.3 HYP-RT-0003 — EXIT_STRONG → GOLD short

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-RT-0003` |
| title | Trend strength dies → next 5D GOLD down |
| hypothesis | After GOLD D1 TREND_STRENGTH switches STRONG→WEAK, next 5-step costed GOLD return is negative. |
| H0 | Conditional mean = unconditional same-side (always-short eligible days) mean. |
| H1 | Conditional mean is **negative** after cost. |
| target | GOLD |
| feature | `STRENGTH[t-1]=STRONG` AND `STRENGTH[t]=WEAK` |
| predicted_sign | −1 |
| side | short |
| hold_bars | 5 |

Economic story: de-risking / trend exhaustion is concentrated at the exit, not at every WEAK bar.

If 0002 and 0003 both pass: still **one target** (GOLD) → program WEAK_EDGE unless 0001 also passes.

---

## 4. Cost / risk

Copy V0.6 / V0.8 numbers. Do not cheapen because transitions are “rare”.

| item | lock |
| --- | --- |
| fill | NEXT_BAR_OPEN of target at t+1 |
| exit | open of aligned row t+1+5, or 1.5×ATR stop from signal-bar ATR |
| close fill | FORBIDDEN |
| spread | broker-points rule (`close>=10` → `spread*0.01`, else `spread*0.00001`) |
| commission | 5 bp / side |
| slippage | 10 bp / side |
| risk_frac | 0.5% of equity (primary) |
| 1% risk | report-only twin, **not** a hypothesis |
| leverage | ≤ 1× |
| start equity | 10000 |
| FRICTION_WIDE | skip new entry |
| overlapping holds | if a new signal arrives while a hold is open, **skip** (no stacking). Count `n_skip_overlap` |

Same-window pair: entry and scheduled exit in the same role.

---

## 5. Statistical evaluation

Reuse `research_engine/statistics.py`. No numpy on Xavier.

| knob | value |
| --- | --- |
| seed | 20260825 |
| bootstrap_iterations | 2000 |
| permutation_iterations | 2000 |
| block_length | 5 |
| fdr_q | 0.05 |
| m | **3** |
| alpha | 0.05 |

Baseline: unconditional costed 5-step return of the **same target**, same window, same fill/cost, same-side, every eligible day with a complete 5-step hold (no transition required).

```text
delta = mean(return | transition) - mean(return | all eligible same-side)
```

Cohen’s d as in FD/HYP-0001.  
Contemporaneous “state level still HIGH/STRONG on t+1” is diagnostic, not a gate.

Permutation p is two-sided on `delta`. Do not switch to one-sided after the fact.

BH-FDR: three RESEARCH raw p-values, m=3, q=0.05.  
VALIDATION is confirmation, not three more FDR tests.

Minimum completed test: RESEARCH `n_trade` ≥ 8, VALIDATION ≥ 4.  
Below: `INSUFFICIENT_OCCUPANCY`. Do not relax ADX 25 or VOL percentiles to mint trades.

---

## 6. Validation and labels

### 6.1 Single-hypothesis gates (all required)

- RESEARCH and VALIDATION costed `total_return` > 0  
- realized sign matches pre-registered H1  
- RESEARCH trades ≥ 8, VALIDATION ≥ 4  
- RESEARCH max DD ≥ −25%, VALIDATION ≥ −30%  
- `max_trade_share` ≤ 50%  
- occupancy is from transitions only (if occupancy looks like “half the days”, the Δstate definition is wrong — fail the job, do not reinterpret as state level)

Optional support (not sufficient): RESEARCH block-bootstrap CI on `delta` excludes 0 and `adjusted_p` ≤ 0.05.

### 6.2 Program CANDIDATE

```text
at least two hypotheses pass §6.1
AND they do not share a single target
AND FDR discovery includes those passers
```

So **0001 + 0002** or **0001 + 0003** can promote (OIL and GOLD).  
**0002 + 0003 only** (both GOLD) = `WEAK_EDGE` + `SINGLE_TARGET`.

Only OIL: `WEAK_EDGE`.  
Zero passes: `NO_CANDIDATE`.

CAGR ≥ 10% is not a gate.

### 6.3 Required diagnostic (not a hypothesis)

Unconditional long GOLD and unconditional long OIL, same windows, same cost, hold=5 rolling or buy-and-hold — report as **PATH_BENCHMARK**.  
If the benchmark looks like 10% and the transitions do not beat their same-side baseline, the answer is still no edge.

---

## 7. Four Xavier plan (do not run in this documentation task)

Windows owns space, windows, jobs, collect, FDR.  
Workers execute one hypothesis list. They cannot add IDs.

Suggested remote dir: `/tmp/tm-regime-v09`  
Do not reuse `/tmp/tm-cross-asset-v08` as authority.

| node | host | hypothesis_ids | role |
| --- | --- | --- | --- |
| Xavier-01 | 192.168.1.200 | `HYP-RT-0001` | PRIMARY |
| Xavier-02 | 192.168.1.201 | `HYP-RT-0002` | PRIMARY |
| Xavier-03 | 192.168.1.202 | `HYP-RT-0003` | PRIMARY |
| Xavier-04 | 192.168.1.203 | `HYP-RT-0001` | CROSS_CHECK |

Xavier-04 vs Xavier-01: compare `content_hash`.

`FINAL_OOS_ACCESS`: DENIED. Worker raises on Final OOS paths.

Python: stdlib only on Xavier (3.6).

---

## 8. What the next implementer does (and does not)

**Does:** reproduce hash → freeze windows on each target → freeze VOL percentiles on RESEARCH → dispatch four jobs → collect → BH m=3 → ranking → stop.

**Does not:** add hypotheses, change hold, change ADX 25, open M15, reopen V0.8, start MT5, lock Final OOS, start ML.

---

## 9. Distance to 10%

This contract can produce CANDIDATE / WEAK_EDGE / NO_CANDIDATE.  
It cannot certify annualized 10%.  
Even a pass must be compared to the GOLD/OIL path benchmark on 2020–2026.

Best prior leftover remains V0.6 OIL D1 +0.23% CAGR, unused here.

---

## 10. Untouched

HYP-0001 14:11 hashes, FD V0.1 search-space file, V0.5/V0.6/V0.8 spaces and results, immutable bars, `data/mine/longrun/`, `order_send`, Final OOS payload.

---

## 11. Canonical hash payload

SHA256 of this object, `json.dumps(..., sort_keys=True, separators=(',', ':'))`, UTF-8:

```json
{"adx_period":14,"close_fill":"FORBIDDEN","cost":{"commission_bp_per_side":5.0,"slippage_bp_per_side":10.0,"spread":"BROKER_POINTS_RULE"},"discovery_id":"REGIME_TRANSITION_V0.9","family_id":"FAM-RT-DELTA-0001","fill":"NEXT_BAR_OPEN","hold_bars":5,"horizon":"SIGNAL_PLUS_HOLD_ALIGNED_ROWS","hypothesis_count":3,"hypothesis_ids":["HYP-RT-0001","HYP-RT-0002","HYP-RT-0003"],"parent_datasets":["tm-market-GOLD-D1-20260825-000001","tm-market-OIL-D1-20260825-000001"],"risk":{"leverage_cap":1.0,"risk_frac":0.005,"stop_atr_mult":1.5},"seed":20260825,"sma_fast":20,"sma_slow":50,"state_source":"MARKET_STATE_V0.5","stats":{"block_length":5,"bootstrap":2000,"fdr_q":0.05,"m":3,"permutation":2000},"timeframe":"D1","vol_percentiles":[33,67],"windows":{"FINAL_OOS_ACCESS":"DENIED","split":"70/15/15_on_target_sorted_d1_dates"}}
```

`search_space_hash` = `3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`

If an implementation changes any field above, it is a **new** version, not V0.9.
