# Research Engine V0.5 — Phase 1 Field Audit

Date: 2026-08-26. Inspect only. No guesses.

Labels: **FACT** (on disk / in code) · **DONE** (finished and evidenced) · **UNKNOWN** (not verified here) · **TODO** (not built).

## 1. Experiment assets

| item | label | evidence |
| --- | --- | --- |
| HYP-0001 parent + A/B JSON | **FACT / DONE** | `data/market/research_engine/hypothesis/HYP-0001.json`, `-A.json`, `-B.json` |
| 14:11 preregistration A/B | **FACT / DONE** | `preregistration/HYP-0001-A.json` hash `485d56a8f5a8e682…b6d8`; B `fbd14d199ba6390a…cd3db` |
| Family `FAM-MOMENTUM-0001` | **FACT / DONE** | `registry/FAM-MOMENTUM-0001.json` |
| 32 experiment contracts | **FACT / DONE** | `experiments/tm-exp-20260825-141158-001` … `-032` |
| Formal 48-job index | **FACT / DONE** | `RESEARCH_ENGINE_INDEX_FORMAL.json`: 32 experiments, 4 nodes ok, `family_status=WEAK_SUPPORT`, FDR m=96 discoveries=0 |
| Formal Xavier results | **FACT / DONE** | `results/formal/HYP-0001-A|B/<dataset>/` |
| HYP-0001 jobs / windows | **FACT / DONE** | `jobs/ALL_JOBS.json`, 16 `*_window.json`, 4 `dispatch_Xavier-0X.json` |
| Draft catalog family `FAM-PERSISTENCE-0001` | **FACT** | `research_engine/catalog.py` only. Not formal identity |
| Directory named `contracts/` | **FACT** | **Does not exist** under `data/market/research_engine/`. Contracts are the JSON files above + FD search-space file |
| `research_engine/__init__.py` version | **FACT** | `ENGINE_VERSION = "0.4"` |
| V0.5 / strategy / regime package | **FACT** | **Absent** (`research_engine/strategy/`, `research_engine/regime/` not present) |

HYP-0001 is a **predictive hypothesis**, not a strategy. Formal rollup **WEAK_SUPPORT** ≠ annualized 10%.

## 2. Factor results

| item | label | evidence |
| --- | --- | --- |
| Locked search space | **FACT / DONE** | `factor_discovery/FACTOR_SEARCH_SPACE_V0.1.json` hash `add0211ffb189d50639b656af1b009ac15849d9f3d426af8469f9700eb05dc5a`, 57 candidates |
| Factor registry file | **FACT / DONE** | `factor_discovery/registry/FACTOR_REGISTRY_V0.1.json` (statuses still `REGISTERED`; ranking is the post-test source) |
| Ranking | **FACT / DONE** | `FACTOR_RANKING_V0.1.json`: `NO_USEFUL_FACTORS_FOUND`; PROMISING 0; CANDIDATE 0; INCONCLUSIVE 5; REJECTED 52 |
| Multiple-testing ledger | **FACT / DONE** | `factor_discovery/ledgers/multiple_testing.json`: tested_count 876, fdr_discoveries 0, keep_failed true |
| Four-Xavier FD results | **FACT / DONE** | `factor_discovery/results/Xavier-01…04/` (17 jobs: 16 primary + GOLD M15 cross-check) |
| Cross-node GOLD M15 | **FACT / DONE** | content-hash PASS |
| Unconditional directional edge | **DONE** (negative result) | 0 FDR discoveries. Correct reading: **this search space did not produce a trading advantage**. Not “markets have no opportunity”. |
| 5 INCONCLUSIVE | **FACT** | Vol → `future_abs_return` clustering; FDR fail; cost-sensitive |

## 3. Failure / memory records

| item | label | evidence |
| --- | --- | --- |
| HYP-0001 `rejected/` | **FACT / DONE** | 22 JSON files under `data/market/research_engine/rejected/` |
| FD failed factors kept | **FACT / DONE** | All 57 remain in ranking with `why` |
| Contract-mismatch quarantine | **FACT / DONE** | `quarantine/CONTRACT_MISMATCH_20260826/` (do not delete) |
| Registry status write-back after FD | **FACT** | Ranking has REJECTED/INCONCLUSIVE; registry rows still say REGISTERED |
| Query UI “what did we falsify?” | **TODO** | Schema exists in ranking/ledger; no NL query UI (by prior design) |

## 4. Data capability

| item | label | evidence |
| --- | --- | --- |
| Immutable datasets | **FACT / DONE** | 16 qualified ids GOLD/EURUSD/USDJPY/OIL × M15/H1/H4/D1 (`tm-market-*-20260825-000001`). Extra GOLD M15 `000002` exists; **not** in FD/HYP universe |
| Bars | **FACT** | 2000 rows; columns include `tick_volume`, `real_volume`, `spread`. `real_volume` policy: tick_volume only |
| Protocol windows + leakage | **FACT / DONE** | `research_protocol/windows.py`, `causal.py`. `FINAL_OOS_LOCKED=false`, access denied |
| Causal features in protocol | **FACT / DONE** | SMA/EMA/RSI/ATR/MACD/Bollinger/VWAP in `research_protocol/features.py` (protocol lab, not FD space) |
| FD compute kinds | **FACT** | ret, sign_cons, accel, dist_mean, range/z/close_loc, vol, efficiency, tickvol, spread, limited MTF/combos. **No ADX in `research_engine/`** |
| Xavier SSH pattern | **FACT / DONE** | `scripts/research_engine_run.py`, `research_engine_factor_run.py`. IPs 192.168.1.200–203 |
| Cost model | **FACT** | Screen only: raw `spread/close`. Not a broker cost model. Not a backtester |
| News / events | **FACT** | DRAFT only. No live news API |
| Cross-asset aligned series | **FACT** | DRAFT. Four symbols exist as **separate** files |
| Strategy layer (entry/exit/hold/risk/PnL) | **TODO** | Architecture interface only in FD V0.1 doc |
| Market regime layer | **TODO** | V11.6 had frozen 涨/跌/震 in the **old mine path**. Not a research-engine Market State contract |
| Annualized 10% / Sharpe / DD on research path | **TODO** | Not computed for HYP-0001 or FD |
| MT5 `order_send` / paper / Final OOS rank | **TODO** and **forbidden now** | Must stay unused for V0.5 |
| Whether 8002–8005 sidecars are up right now | **UNKNOWN** | Not probed this audit |
| Whether Xavier disks still hold `/tmp/tm-factor-discovery-v01` | **UNKNOWN** | Windows has collected results |

## 5. What this means for V0.5

**DONE and reusable:** locked data, protocol windows, stats (bootstrap/perm/BH), Xavier dispatch, HYP-0001 datapoint, FD V0.1 negative result + lineage.

**Missing for a profitability research system:** Market State, strategy contract, cost-aware trade translation, risk/portfolio, OOS-as-capital-test.

**Do not do:** retune HYP-0001; rerun FD V0.1; more bar profiles; start MT5.
