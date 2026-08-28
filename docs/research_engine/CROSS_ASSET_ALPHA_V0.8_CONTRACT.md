# Cross Asset Alpha V0.8 Contract

Locked 2026-08-26. Executed 2026-08-26. Outcome: **`NO_CANDIDATE`** (3/3 FALSIFIED).

This file is the write-once experiment contract. Locked fields below were not retuned after the run.  
Report: `CROSS_ASSET_ALPHA_V0.8_REPORT.md`. Freeze: `V0.8_EXECUTION_FREEZE.md`.

Audit: `docs/research_engine/CROSS_ASSET_DATA_AUDIT.md`  
OS parent: `docs/research_engine/ALPHA_OPERATING_SYSTEM_V0.7.1.md`

Not a live book. Not MT5. Not Final OOS. Not HYP-0001. Not FD V0.1 retune. Not V0.6 strategy scan.

```text
search_space_hash =
787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827
```

Hash payload is the canonical JSON in §11. Implementation must reproduce the same hash before any job starts.

---

## 0. Family — FAM-FD-XASSET-0001

This ID already exists as **DRAFT** in `FACTOR_SEARCH_SPACE_V0.1.json` (`reserved_not_computed`).  
V0.8 **activates** the family. It does **not** edit that FD file.

| field | value |
| --- | --- |
| family_id | `FAM-FD-XASSET-0001` |
| discovery_id | `CROSS_ASSET_ALPHA_V0.8` |
| status | `EXECUTED_NO_CANDIDATE` (was `LOCKED_NOT_RUN` before the run) |
| claim type | relative-value / lagged cross-asset |
| hypothesis_count | **3** |
| hypothesis_ids | `HYP-XA-0001`, `HYP-XA-0002`, `HYP-XA-0003` |
| parent_hypothesis_id | null (not children of HYP-0001) |
| timeframe | D1 only |
| seed | 20260825 |

Economic story: a dollar-proxy move observed on day t changes the **next aligned row** of GOLD or OIL.  
Not: same-bar correlation. Not: DXY (no DXY on disk).

---

## 1. Dataset contract

### 1.1 Parents (immutable, do not copy-overwrite)

| logical | dataset_id |
| --- | --- |
| GOLD | `tm-market-GOLD-D1-20260825-000001` |
| EURUSD | `tm-market-EURUSD-D1-20260825-000001` |
| USDJPY | `tm-market-USDJPY-D1-20260825-000001` |
| OIL | `tm-market-OIL-D1-20260825-000001` |

Timezone: UTC. See audit for hashes and missing dates.

### 1.2 Alignment pack (to be written at implementation, not now)

| field | lock |
| --- | --- |
| proposed id | `tm-align-D1-XA-20260826-000001` |
| key | UTC date of `timestamp_utc` |
| method | inner join of all four |
| n | 1993 |
| range | 2020-04-01 → 2026-08-25 |
| fill | FORBIDDEN |
| pair-only 1995-day joins | diagnostic only |

Pack must store: parent hashes, `dropped_days` list, SHA256 of the aligned table.

### 1.3 Time alignment

```text
feature on row t  uses only bars with date <= t
target on row t+1 is the next row in the aligned series
horizon is NOT calendar +1 day
```

Sunday D1 bars exist. Friday → Sunday is a legal next row.

### 1.4 Windows (shared; frozen)

| role | dates inclusive | n | access |
| --- | --- | --- | --- |
| RESEARCH | 2020-04-01 → 2024-09-26 | 1395 | allowed |
| VALIDATION | 2024-09-27 → 2025-09-10 | 299 | allowed |
| FINAL_OOS | 2025-09-11 → 2026-08-25 | 299 | **DENIED** |

Trade `(t, t+1)` requires both dates in the same role. Last date of a window: no trade.

Reading FINAL_OOS bars for features or targets must raise.

---

## 2. Three hypotheses (no fourth)

Feature freeze is written **before** target outcomes are used.  
Thresholds for 0001/0002: 67th percentile of the **predictor** on RESEARCH aligned rows only, then applied to VALIDATION. One freeze. No re-estimate.

Return of an input asset on t:

```text
ret_input[t] = close[t] / close[t-1] - 1
```

using that asset’s own previous aligned close (t−1 must exist). First aligned row: no feature.

Target evaluation return (costed, see §4): GOLD or OIL **open[t+1] → open[t+2]** is **not** used.  
Entry at **open of t+1**, exit at **open of the row after t+1** or stop. Holding = one aligned step.

### 2.1 HYP-XA-0001

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-XA-0001` |
| title | JPY-proxy high → next GOLD down |
| hypothesis | After a large USDJPY D1 rise, next aligned GOLD open-to-open return is negative after cost. |
| H0 | Mean costed GOLD next-step return \| Q3(USDJPY ret) = mean costed GOLD next-step return (unconditional). Sign is not systematically negative. |
| H1 | Conditional mean is **negative** and economically non-zero after cost. |
| input asset | USDJPY |
| target asset | GOLD |
| time alignment | four-way inner join; t → next aligned row |
| feature freeze | `USDJPY_RET` ; gate = RESEARCH 67th percentile of `USDJPY_RET` ; side = ret ≥ gate |
| prediction horizon | 1 aligned row |
| predicted sign | GOLD next return **< 0** |
| cost model | §4 |
| validation | §5–§6 |

Not: GOLD momentum. Not: two-sided “whatever sign appears”.

### 2.2 HYP-XA-0002

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-XA-0002` |
| title | EUR-proxy high → next GOLD up |
| hypothesis | After a large EURUSD D1 rise, next aligned GOLD open-to-open return is positive after cost. |
| H0 | Conditional mean = unconditional; sign not systematically positive. |
| H1 | Conditional mean is **positive** after cost. |
| input asset | EURUSD |
| target asset | GOLD |
| time alignment | same four-way join |
| feature freeze | `EURUSD_RET` ; gate = RESEARCH 67th percentile of `EURUSD_RET` ; side = ret ≥ gate |
| prediction horizon | 1 aligned row |
| predicted sign | GOLD next return **> 0** |
| cost model | §4 |
| validation | §5–§6 |

If 0001 passes and 0002’s realized sign flips vs H1: record `PROXY_INCONSISTENT`. Do not keep only 0001 as program CANDIDATE.

### 2.3 HYP-XA-0003

| field | lock |
| --- | --- |
| hypothesis_id | `HYP-XA-0003` |
| title | Dual-proxy dollar-up → next OIL down |
| hypothesis | On a dollar-up day, next aligned OIL open-to-open return is negative after cost. |
| H0 | Conditional mean = unconditional; sign not systematically negative. |
| H1 | Conditional mean is **negative** after cost. |
| input asset | USDJPY **and** EURUSD |
| target asset | OIL |
| time alignment | same four-way join |
| feature freeze | `DOLLAR_UP := (USDJPY_RET > 0) AND (EURUSD_RET < 0)` — comparison to **0**, not a percentile |
| prediction horizon | 1 aligned row |
| predicted sign | OIL next return **< 0** |
| cost model | §4 |
| validation | §5–§6 |

If RESEARCH occupancy < 8: `INSUFFICIENT_OCCUPANCY`. Do not relax `DOLLAR_UP`.

### 2.4 What these are not

They are **predictive contracts** evaluated with a locked cost translation.  
They are not an order book, not a portfolio, not permission to `order_send`.

---

## 3. Prohibitions (part of the contract)

These are invalid operations. A result produced after any of them is void.

1. **Do not change the lead.** Horizon stays 1 aligned row. No t+2, t+3, t+5 scan.  
2. **Do not change thresholds.** 67th percentile (0001/0002) and the 0-cut (0003) stay. No 60/70/80. No re-freeze on validation.  
3. **Do not add a fourth hypothesis.** No GOLD–OIL residual, no H4 twin, no 1% risk as a new ID.  
4. **Do not flip predicted signs after seeing results.** Failed H1 is NO_EDGE.  
5. **Do not use Final OOS.** Access denied. Dates 2025-09-11 → 2026-08-25 are not inputs.  
6. Do not edit HYP-0001, FD V0.1 space, V0.5, V0.6, or the four parent manifests/bars.  
7. Do not write USDJPY/EURUSD as DXY.  
8. Do not fill missing dates.  
9. Do not evaluate close-to-close as the fill. Close fill FORBIDDEN.  
10. Do not change cost bp, leverage cap, or CANDIDATE gates to chase 10%.  
11. Do not drop OIL extreme days in the primary test.  
12. Do not promote “only GOLD, both proxies” to program CANDIDATE.  
13. Worker must not add IDs, change gates, or open FINAL_OOS.  
14. Do not run MT5 trading APIs.

---

## 4. Cost, fill, risk

Copy V0.6 numbers. Do not cheapen for cross-asset.

| item | lock |
| --- | --- |
| fill | NEXT_BAR_OPEN of target at t+1 |
| exit | open of next aligned row after entry, or 1.5×ATR stop from signal-bar ATR |
| close fill | FORBIDDEN |
| spread | existing broker-points rule (`close>=10` → `spread*0.01`, else `spread*0.00001`) |
| commission | 5 bp / side |
| slippage | 10 bp / side |
| risk_frac | 0.5% of equity (primary) |
| 1% risk | report-only twin, **not** a hypothesis |
| leverage | ≤ 1× |
| start equity | 10000 |
| FRICTION_WIDE | skip new entry (same V0.6 definition on the **target** bar) |

Side: 0001 short GOLD; 0002 long GOLD; 0003 short OIL.  
Opposite of predicted sign is not a second test.

---

## 5. Statistical evaluation

Reuse `research_engine/statistics.py` (LCG, bootstrap, moving-block, permutation, BH).  
Do not add numpy.

### 5.1 Locked knobs

| knob | value | why |
| --- | --- | --- |
| seed | 20260825 | same lab seed |
| bootstrap_iterations | 2000 | formal, small m |
| permutation_iterations | 2000 | same |
| block_length | 5 | D1 ≈ one week; not the M15 `20` |
| fdr_q | 0.05 | BH |
| m | **3** | only these three primary tests |
| alpha | 0.05 | CI |

1% risk twin, winsor 1% diagnostic, contemporaneous correlation: **not** in m.

### 5.2 Sample size

Per hypothesis per window:

- `n_aligned` — dates in window  
- `n_feature` — rows with t−1 so ret exists  
- `n_signal` — occupancy  
- `n_trade` — same-window `(t,t+1)` actually costed  
- `dropped_days` on the pack (global)

Minimum for a completed test: RESEARCH `n_trade` ≥ 8, VALIDATION ≥ 4.  
Below that: `INSUFFICIENT_OCCUPANCY`, not a silent pass.

### 5.3 Baseline

Primary baseline: **unconditional** costed next-step return of the **same target**, same window, same fill/cost, every eligible aligned day (no Q3 / no DOLLAR_UP).

```text
delta = mean(return | signal) - mean(return | all eligible)
```

A second baseline (diagnostic): always-flat 0.  
Contemporaneous `corr(input_ret[t], target_ret[t])` is diagnostic. **It is not evidence.**

### 5.4 Effect size

Cohen’s d on the two samples (signal vs complement or vs all), same formula as FD/HYP-0001 (`difference_of_means` / pooled sd).  
Also report mean bps after cost.  
d is not a pass gate by itself.

### 5.5 Bootstrap

IID bootstrap CI on `delta` and on mean costed signal return. 2000 iterations, seed 20260825, 95%.

### 5.6 Block bootstrap

Moving-block bootstrap, `block_length=5`, 2000 iterations, same seed family as `statistics.py`.  
Report CI on `delta`. Prefer block CI for “excludes 0” language when it disagrees with IID.

### 5.7 Permutation

Two-sided permutation p on `delta` (`permutation_delta_p`). 2000 iterations.  
H1 is one-sided for **classification**, but the p-value stays two-sided (harder).  
A one-sided story that fails two-sided p is not rescued by switching to one-sided after the fact.

### 5.8 BH-FDR

```text
raw_p = permutation p of each of the 3 hypotheses (RESEARCH primary)
m = 3
q = 0.05
benjamini_hochberg
```

VALIDATION does not add three more FDR tests. Validation is **confirmation** (sign, costed return, gates).  
FDR discovery without validation confirmation ≠ CANDIDATE.

---

## 6. Validation and labels

### 6.1 Single-hypothesis gates (all required)

- RESEARCH and VALIDATION costed `total_return` > 0  
- realized sign matches pre-registered H1  
- RESEARCH trades ≥ 8, VALIDATION ≥ 4  
- RESEARCH max DD ≥ −25%, VALIDATION ≥ −30%  
- `max_trade_share` ≤ 50%  
- contemporaneous correlation does not substitute for lagged `delta`

Optional support (not sufficient alone): RESEARCH block-bootstrap CI on `delta` excludes 0 and `adjusted_p` ≤ 0.05.

### 6.2 Program (family) CANDIDATE

```text
at least two hypotheses pass §6.1
AND the two passed hypotheses do not share a single target
```

So **0001 + 0003** or **0002 + 0003** can promote.  
**0001 + 0002 only** (both GOLD) = `WEAK_EDGE` + `SINGLE_TARGET`.

Only OIL: `WEAK_EDGE`.  
Zero passes: `NO_EDGE`.  
`NO_EDGE` / `WEAK_EDGE_ONLY` are legal program outcomes.

CAGR is reported. **CAGR ≥ 10% is not a gate.**

---

## 7. Four Xavier plan (executed 2026-08-26)

Windows owns space, alignment, jobs, collect, FDR.  
Workers execute one hypothesis list. They cannot add IDs.

Remote directory (when implemented): `/tmp/tm-cross-asset-v08`  
Do not reuse `/tmp/tm-factor-discovery-v01` or profit/strategy temps as authority.

### 7.1 Job manifest

One job per node. Every job carries the **same** alignment pack (all four parents).

```json
{
  "job_id": "XA-V08-Xavier-01-HYP-XA-0001",
  "discovery_id": "CROSS_ASSET_ALPHA_V0.8",
  "family_id": "FAM-FD-XASSET-0001",
  "search_space_hash": "787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827",
  "node": "Xavier-01",
  "host": "192.168.1.200",
  "role": "PRIMARY",
  "hypothesis_ids": ["HYP-XA-0001"],
  "hypothesis_count": 1,
  "align_id": "tm-align-D1-XA-20260826-000001",
  "parent_dataset_ids": [
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-EURUSD-D1-20260825-000001",
    "tm-market-USDJPY-D1-20260825-000001",
    "tm-market-OIL-D1-20260825-000001"
  ],
  "timeframe": "D1",
  "seed": 20260825,
  "bootstrap_iterations": 2000,
  "permutation_iterations": 2000,
  "block_length": 5,
  "fdr_q": 0.05,
  "FINAL_OOS_ACCESS": "DENIED",
  "note": "Worker executes this list only. Not HYP-0001. Not V0.6."
}
```

| node | host | hypothesis_ids | role |
| --- | --- | --- | --- |
| Xavier-01 | 192.168.1.200 | `HYP-XA-0001` | PRIMARY |
| Xavier-02 | 192.168.1.201 | `HYP-XA-0002` | PRIMARY |
| Xavier-03 | 192.168.1.202 | `HYP-XA-0003` | PRIMARY |
| Xavier-04 | 192.168.1.203 | `HYP-XA-0001` | CROSS_CHECK |

Xavier-04 vs Xavier-01: compare `content_hash` (align + hyp + seed + stats + research/validation numbers). `job_id` / node name may differ; that is not a mismatch.

Windows writes `jobs/ALL_JOBS.json` and `jobs/dispatch_Xavier-0X.json` at run time. **Not in this task.**

### 7.2 Worker contract

Worker may:

- read job, space hash, alignment pack, four parent CSVs  
- compute listed hypothesis only  
- return lineage + metrics for RESEARCH and VALIDATION  

Worker must reject / raise when:

- `hypothesis_ids` contains an unknown id or more than the job lists  
- `search_space_hash` mismatches  
- any path under FINAL_OOS or role `FINAL_OOS`  
- asked to change horizon, gate, or sign  
- `order_send` or any trade API  

Worker does not:

- invent alignment  
- compute FDR (Windows does m=3 after collect)  
- write parent bars  
- call the LLM  

Python: stdlib only on Xavier (3.6). Reuse existing bootstrap/permutation code.

### 7.3 Result format (per job)

```json
{
  "job_id": "XA-V08-Xavier-01-HYP-XA-0001",
  "discovery_id": "CROSS_ASSET_ALPHA_V0.8",
  "node": "Xavier-01",
  "role": "PRIMARY",
  "search_space_hash": "787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827",
  "align_hash": "<sha256 of aligned pack>",
  "content_hash": "<sha256 of numbers without job_id/node>",
  "FINAL_OOS_TOUCHED": false,
  "hypothesis": {
    "hypothesis_id": "HYP-XA-0001",
    "n_aligned_research": 1395,
    "n_aligned_validation": 299,
    "feature_gate": "<frozen float or DOLLAR_UP>",
    "research": {
      "n_trade": 0,
      "occupancy": 0.0,
      "total_return": 0.0,
      "cagr": 0.0,
      "max_drawdown": 0.0,
      "sharpe": null,
      "turnover": 0.0,
      "cost_paid": 0.0,
      "max_trade_share": null,
      "mean_signal": 0.0,
      "mean_baseline": 0.0,
      "delta": 0.0,
      "effect_size": 0.0,
      "raw_p": 1.0,
      "bootstrap_ci": {"low": 0.0, "high": 0.0, "method": "iid_bootstrap_delta"},
      "block_bootstrap_ci": {"low": 0.0, "high": 0.0, "method": "moving_block_bootstrap_delta_conservative"},
      "contemporaneous_corr": 0.0
    },
    "validation": {},
    "dataset_status": "NO_EDGE",
    "dataset_why": []
  }
}
```

Windows ranking file: `data/market/research_engine/cross_asset/CROSS_ASSET_RANKING_V0.8.json` (`m=3`, `outcome=NO_CANDIDATE`).

---

## 8. What the next implementer does (and does not)

**Did (2026-08-26):** alignment pack → freeze gates on RESEARCH predictors only → four jobs → collect → BH m=3 → ranking → freeze. Outcome `NO_CANDIDATE`.

**Does not:** add hypotheses, retune XA, open M15, start MT5, lock Final OOS. Regime V0.9 only as a **new** versioned contract if separately approved.

---

## 9. Distance to 10%

This contract can produce CANDIDATE / WEAK_EDGE / NO_EDGE.  
It cannot certify annualized 10%. D1 span is ~6.4 years with a 2020 oil regime.  
Best prior leftover remains V0.6 OIL D1 +0.23% CAGR, unused here.

---

## 10. Untouched

HYP-0001 14:11 hashes, FD V0.1 search-space file, V0.5/V0.6 spaces, immutable bars, `data/mine/longrun/`, `order_send`, Final OOS payload.

---

## 11. Canonical hash payload

SHA256 of this object, `json.dumps(..., sort_keys=True, separators=(',', ':'))`, UTF-8:

```json
{"align_key":"UTC_DATE","align_method":"INNER_JOIN_ALL_FOUR","aligned_end":"2026-08-25","aligned_n_dates":1993,"aligned_start":"2020-04-01","close_fill":"FORBIDDEN","cost":{"commission_bp_per_side":5.0,"slippage_bp_per_side":10.0,"spread":"BROKER_POINTS_RULE"},"discovery_id":"CROSS_ASSET_ALPHA_V0.8","family_id":"FAM-FD-XASSET-0001","fill":"NEXT_BAR_OPEN","horizon":"NEXT_ALIGNED_ROW","hypothesis_count":3,"hypothesis_ids":["HYP-XA-0001","HYP-XA-0002","HYP-XA-0003"],"parent_datasets":["tm-market-GOLD-D1-20260825-000001","tm-market-EURUSD-D1-20260825-000001","tm-market-USDJPY-D1-20260825-000001","tm-market-OIL-D1-20260825-000001"],"risk":{"leverage_cap":1.0,"risk_frac":0.005,"stop_atr_mult":1.5},"same_window_pair":true,"seed":20260825,"stats":{"block_length":5,"bootstrap":2000,"fdr_q":0.05,"m":3,"permutation":2000},"timeframe":"D1","windows":{"FINAL_OOS_ACCESS":"DENIED","final_oos":["2025-09-11","2026-08-25"],"research":["2020-04-01","2024-09-26"],"split":"70/15/15_on_sorted_aligned_dates","validation":["2024-09-27","2025-09-10"]}}
```

`search_space_hash` = `787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827`

If an implementation changes any field above, it is a **new** version, not V0.8.
