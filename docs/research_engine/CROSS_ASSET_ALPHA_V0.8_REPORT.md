# Cross Asset Alpha V0.8 Report

Four Xavier full run collected `2026-08-26T14:55:26Z`.  
HYP-0001 / FD V0.1 / V0.5 / V0.6 / 14:11 files were not modified. Immutable bars were not overwritten. Final OOS exists and was not read. No MT5. No `order_send`. No fourth hypothesis. No post-hoc retune.

Contract: `docs/research_engine/CROSS_ASSET_ALPHA_V0.8_CONTRACT.md`  
Audit: `docs/research_engine/CROSS_ASSET_DATA_AUDIT.md`  
Freeze: `docs/research_engine/V0.8_EXECUTION_FREEZE.md`  
Ranking: `data/market/research_engine/cross_asset/CROSS_ASSET_RANKING_V0.8.json`

```text
search_space_hash = 787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827
align_hash        = 1e8f6bbc82c542dbe9aa6751ea56af1a3a364c5ef0406ba2b4c89ef5a83aaf2b
ranking_hash      = 243772583cee81e298147cbe29c152bd92a6104db8e45218a71349361674ab81
```

## 1. Executive

This version asked whether a **locked, three-hypothesis, lagged cross-asset relative-value** space has repeatable predictive power after V0.6 costs.

```text
program outcome     = NO_CANDIDATE
CANDIDATE           = 0
WEAK_EDGE           = 0
gold_pass           = []
oil_pass            = []
FDR m=3 q=0.05      = 0 discoveries
hypothesis labels   = FALSIFIED / FALSIFIED / FALSIFIED
```

**No candidate.**  
GOLD and OIL did not both pass. Neither passed alone. FDR did not promote any test.

Correct reading: **this locked 3-hypothesis lagged RV space has no after-cost, validation-confirmed, FDR-surviving edge.**  
Not: gold and FX are unrelated. Same-bar gold/USD correlation is real and is **not** a CANDIDATE.

Do **not** flip signs, change 67%, change lag, cheapen cost, or add HYP-XA-0004.

## 2. What was already tested (do not repeat)

| prior | result | do not repeat as |
| --- | --- | --- |
| HYP-0001 streak=3 | WEAK_SUPPORT, not a book | streak 2/3/4/5 retune |
| FD V0.1 57 factors | NO_USEFUL_FACTORS_FOUND | RSI / MA / factor farms |
| V0.5 15 next-bar sketches | NO_USEFUL_STRATEGIES_FOUND | always-long-in-UP, fade-EXTENDED |
| V0.6 costed books | WEAK_EDGE_ONLY, CANDIDATE=0 | OIL momentum N/hold/cost retune |
| FD `FAM-FD-XASSET-0001` | DRAFT, never computed | do not edit that FD file |

## 3. What V0.8 tested (new)

Lagged, next-aligned-row, NEXT_BAR_OPEN, same V0.6 cost/risk. Horizon is **not** calendar +1.

| id | feature (t) | target (t+1) | side |
| --- | --- | --- | --- |
| HYP-XA-0001 | USDJPY Q3 (67th pct, RESEARCH freeze) | GOLD | short |
| HYP-XA-0002 | EURUSD Q3 (67th pct, RESEARCH freeze) | GOLD | long |
| HYP-XA-0003 | DOLLAR_UP (`USDJPY_RET>0` AND `EURUSD_RET<0`) | OIL | short |

Frozen gates used:  
0001 `0.001631222812953359` (`n_freeze=1394`)  
0002 `0.0012857708031122073` (`n_freeze=1394`)  
0003 DOLLAR_UP vs 0.

Alignment: four-way D1 inner join, **1993** UTC dates, `2020-04-01` → `2026-08-25`.  
Windows 70/15/15 on that series: RESEARCH 1395 / VALIDATION 299 / FINAL_OOS 299 (exists only).

## 4. Four Xavier

Preflight `2026-08-26T14:55:08Z`: SSH_OK on all four. Python 3.6.9 / 3.6.8 / 3.6.8 / 3.6.9. Disk OK.

Collected `2026-08-26T14:55:26Z`. Remote dir `/tmp/tm-cross-asset-v08`.

| node | host | job | role | wall s | status | content_hash |
| --- | --- | --- | --- | --- | --- | --- |
| Xavier-01 | 192.168.1.200 | HYP-XA-0001 | PRIMARY | 17.0 | ok | `1140432a…b20` |
| Xavier-02 | 192.168.1.201 | HYP-XA-0002 | PRIMARY | 16.8 | ok | `b0509ae5…626a` |
| Xavier-03 | 192.168.1.202 | HYP-XA-0003 | PRIMARY | 16.6 | ok | `da15b0da…422b` |
| Xavier-04 | 192.168.1.203 | HYP-XA-0001 | CROSS_CHECK | 16.7 | ok | `1140432a…b20` |

Xavier-01 and Xavier-04 **content_hash identical**.  
Local smoke p-values matched Xavier primaries (0001 `p=0.31634182908545727` exact).

Workers executed only contract IDs. Windows computed BH `m=3`.

## 5. Required answers

### 5.1 Is there a candidate?

**No.** Program outcome `NO_CANDIDATE`. `gold_pass=[]`, `oil_pass=[]`.

### 5.2 Three hypothesis labels

| id | label | dataset | why (locked gates) |
| --- | --- | --- | --- |
| HYP-XA-0001 | **FALSIFIED** | NO_EDGE | RESEARCH_NOT_PROFITABLE, VALIDATION_NOT_PROFITABLE, RESEARCH_DD |
| HYP-XA-0002 | **FALSIFIED** | NO_EDGE | same + RESEARCH_SIGN, VALIDATION_SIGN |
| HYP-XA-0003 | **FALSIFIED** | NO_EDGE | RESEARCH_NOT_PROFITABLE, VALIDATION_NOT_PROFITABLE, RESEARCH_DD |

None of SUPPORTED / WEAK_SUPPORT / INCONCLUSIVE.

### 5.3 Does it repeat across targets?

**No.** GOLD failed (0001 and 0002). OIL failed (0003). There is no two-target promotion path.

### 5.4 Does it exist after cost?

**No.** All three RESEARCH books lost money after half-spread + 5bp + 10bp / side, 0.5% risk, leverage ≤ 1×. Validation books also lost.

### 5.5 Did it pass FDR?

**No.** BH-FDR `m=3`, `q=0.05`, discoveries=0. All `adjusted_p=0.9155422288855574`.

### 5.6 Distance to 10% annualized

See §9. Short answer: **there is no surviving sleeve to measure 10% against.** Best prior leftover remains V0.6 OIL D1 ≈ +0.23% CAGR (~40× below). V0.8 RESEARCH CAGRs are all negative.

## 6. Statistical results (do not upgrade)

Seed `20260825`. IID bootstrap 2000. Moving-block `block_length=5`, 2000. Permutation 2000. BH `m=3`.

### HYP-XA-0001 — USDJPY Q3 → GOLD short

| window | n_trade | TR | CAGR | max DD | Sharpe | delta | Cohen d | raw_p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RESEARCH | 459 | −39.5% | −8.70% | −39.5% | −3.76 | −4.50 bp | −0.054 | 0.316 |
| VALIDATION | 110 | −12.2% | −10.5% | −12.5% | −4.69 | −0.51 bp | −0.005 | — |

Contemporaneous `corr(USDJPY, GOLD)` RESEARCH ≈ **−0.43**. Same-bar relationship exists. Lagged short after Q3 lost after cost. Block CI on RESEARCH delta includes 0 (`−16.8 bp` … `+8.2 bp`).

### HYP-XA-0002 — EURUSD Q3 → GOLD long

| window | n_trade | TR | CAGR | max DD | Sharpe | delta | Cohen d | raw_p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RESEARCH | 459 | −30.0% | −6.24% | −30.1% | −3.11 | −0.92 bp | −0.012 | 0.821 |
| VALIDATION | 90 | −5.7% | −4.86% | −6.0% | −2.39 | −6.03 bp | −0.064 | — |

Contemporaneous `corr(EURUSD, GOLD)` RESEARCH ≈ **+0.41**. Same-bar relationship exists. Pre-registered long after Q3 produced **negative** mean signal in both windows (`RESEARCH_SIGN` / `VALIDATION_SIGN` fail). Do not flip the story.

### HYP-XA-0003 — DOLLAR_UP → OIL short

| window | n_trade | TR | CAGR | max DD | Sharpe | delta | Cohen d | raw_p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RESEARCH | 482 | −27.9% | −5.74% | −31.1% | −0.89 | +1.40 bp | +0.005 | 0.916 |
| VALIDATION | 98 | −1.3% | −1.10% | −4.1% | −0.48 | +22.0 bp | +0.116 | — |

Delta vs same-side unconditional baseline is slightly positive (signal lost **less** than always-short). Books are still negative after cost. Occupancy ~35%. Not a gate pass. Contemporaneous dollar/OIL corr on RESEARCH ≈ 0.02 (noise).

## 7. Honest mechanism note (not a rescue)

Same-day gold vs dollar-proxy correlation is visible in this sample. The **tradable** object was next-aligned-row, after spread/commission/slippage, with Q3 / DOLLAR_UP occupancy near one-third of days.

High turnover + ~30 bp + spread per round trip on a one-row hold bled RESEARCH equity 28–40%. That is cost + lag, not a hidden +10% book.

Contemporaneous correlation is diagnostic. Contract: it is **not** evidence.

## 8. Failed directions (keep)

This version, retained under `data/market/research_engine/cross_asset/`:

- Lagged USDJPY Q3 → next GOLD short: **FALSIFIED**
- Lagged EURUSD Q3 → next GOLD long: **FALSIFIED**
- Lagged DOLLAR_UP → next OIL short: **FALSIFIED**
- Program CANDIDATE requiring GOLD **and** OIL **and** FDR: **NO_CANDIDATE**

Do **not**:

- add HYP-XA-0004
- invert 0001 / 0002 because contemporaneous corr is strong
- change 67% / lag / hold / cost
- treat validation “less bad” on 0003 as a candidate
- expand this family to 10 cross-asset tests

V0.7.1 kill rule applies: three NO_EDGE → do not grow the XA family.

## 9. Distance to 10% annualized

10% is the long-run capital target. **This version cannot certify it and produced no CANDIDATE that could later be asked that question.**

| fact | meaning |
| --- | --- |
| Program CANDIDATE = 0 | no sleeve reaches the 10% question |
| V0.8 RESEARCH CAGRs | −8.7% / −6.2% / −5.7% (wrong side of zero) |
| Best prior leftover | V0.6 OIL D1 MOM ≈ **+0.23%** CAGR (~**40×** below 10%) |
| Same-bar gold/USD \|r\| ≈ 0.41–0.43 | not a lagged after-cost edge |
| Occupancy ~33%, daily hold | costs dominate this horizon |
| D1 aligned span ~6.4 years | enough to reject these three; not enough to claim 10% on a survivor that does not exist |

The gap is **not** “0.23% vs 10% and we are close.” The gap is: **no locked lagged RV hypothesis survived cost, validation, two-target, and FDR.**

Raising any of these books by changing threshold, lag, sign, or cost would be a **new contract**, not a discovery.

## 10. Tests and invariants

`tests/research_engine` **80 PASS** (prior 74 + 6 V0.8).  
Contract hash equals lock. Align n=1993. Worker cannot add IDs. `final_oos` / `FINAL_OOS` raise. Gates freeze on RESEARCH predictors only.

Not touched: V11.7, `master/api/`, Xavier 8002–8005 sidecars, `data/mine/longrun/`, `data/market/immutable/`, HYP-0001 14:11 hashes, FD V0.1 search-space file, V0.5/V0.6 spaces.

## 11. Next stage (one)

**Do not start MT5. Do not lock Final OOS. Do not retune XA-0001/0002/0003. Do not expand this family.**

V0.7.1 queue item 4 is now legal: **Regime Transition V0.9** as a **new versioned contract** with a few pre-registered Δstate hypotheses — **or stop**.  
Risk overlay and Portfolio stay skipped (no surviving sleeve).  
Data Layer V0.2 longer history remains infrastructure, not a rescue of V0.8.

Status: `NO_CANDIDATE`. Failures retained.
