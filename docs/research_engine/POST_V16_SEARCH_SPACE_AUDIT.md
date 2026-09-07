# Post-V16 Search Space Audit

**Date:** 2026-09-02  
**Authority:** on-disk decisions and machine JSON. Not PROJECT_VISION. Not chat memory.  
**V16 reconcile:** `PROGRESS.json` stage was leftover `COMPILE`; now `COMPLETE` / `STOP_B`. Result files not modified.

```
LEVEL = 1
CANDIDATE = 2          # H11_VOL_60 / H12_VOL_120 only
NEW_CANDIDATE = 0
STRATEGY = 2           # WEAK_BUT_RESEARCHABLE; full-path capital negative
PORTFOLIO = 0
PAPER = 0
LIVE = 0
FINAL_OOS = DENIED
NEW_PURCHASE = FALSE
```

H11/H12 = one `LOW_VOL_CANDIDATE_CLUSTER` (corr ≈ 0.996). `KEEP_LOW_PRIORITY`. Not two sleeves.

---

## Status codes (only these)

| Code | Meaning |
|---|---|
| `EXHAUSTED` | Locked contract ran. No new legal hyp in-family without retune. |
| `FROZEN` | Immutable evidence. Do not reopen / retune / flip sign. |
| `AVAILABLE` | New legal question. Data on disk. PIT definable. Not yet run on this universe. |
| `DATA_BLOCKED` | Honest experiment impossible with current files. |
| `PAYMENT_REQUIRED` | Only paid vendor would unblock. Do not buy. |
| `NEW_RESEARCH_SPACE` | Available and not a re-expression of a killed family. |

---

## 1. RESEARCH_SPACE_MATRIX

### 1.1 MT5 / CFD / public-alt (V0.1–V11) — not A-share

| Family | Researched | Data | PIT | Hyp | Cand | FDR | Strategy | Status | Remaining legal space |
|---|---|---|---|---|---|---|---|---|---|
| HYP-0001 momentum | Y | MT5 OHLCV | bar | Y | 0 | not promoted | N | `FROZEN` `EXHAUSTED` | None. 14:11 hashes locked. |
| FD V0.1 | Y | 57-cand / 876 tests | bar | Y | 0 | 0/876 | N | `FROZEN` `EXHAUSTED` | No 58th RSI/MACD. |
| RE V0.5 sketches | Y | Market State + 15 | bar | Y | 0 | 0/203 | N | `FROZEN` `EXHAUSTED` | No ADX retune. |
| PD V0.6 | Y | TF/MR/MOM + cost | bar | Y | 0 | — | N | `FROZEN` `EXHAUSTED` | OIL MOM WEAK_EDGE only. |
| XA V0.8 | Y | USD proxy → GOLD/OIL | bar | Y | 0 | 0/3 | N | `FROZEN` `EXHAUSTED` | No XA-0004. |
| RT V0.9 | Y | Δstate | bar | Y | 0 | 0/3 | N | `FROZEN` `EXHAUSTED` | No RT-0004. |
| XR V0.91 | Y | GOLD/OIL residual | bar | Y | 0 | 0 | N | `FROZEN` `EXHAUSTED` | No SMA20. |
| IT / TS / MS / RI / AMS | Y | calendar / H1 | bar | Y | 0 | 0 | N | `FROZEN` `EXHAUSTED` | Do not retune. |
| IV / COT / EIA / UST10 / CARRY | Y | public alt + MT5 | lagged | Y | 0 | 0 | N | `FROZEN` `EXHAUSTED` | Killed on GOLD/OIL. CARRY_V1 INVALID_ALIGNMENT. |
| SUPPLY_V1 | Y | EIA prod/util | W1 | Y | 0 | — | N | `FROZEN` `EXHAUSTED` | Not inventory rewrap. |
| CM / UM / BREADTH / SIZE | Y | MT5 metals / 841 CFD | bar | Y | 0 | 0 | N | `FROZEN` `EXHAUSTED` | BREADTH WEAK_EDGE. |
| TERM_STRUCTURE / OI / VOL / DTE | Y | Pack E + derived | D1 | Y | 0 | 0 | N | `FROZEN` `EXHAUSTED` | Do not retune slope/OI. |
| V8 fusion TOP5 | Y | curve×OI×COT×EIA×yield | D1 | Y | 0 | 0/15 | N | `FROZEN` `EXHAUSTED` | STOP C. |
| V9 master replay | Y | 103 books | — | — | 0 | — | N | `FROZEN` `EXHAUSTED` | No Positive Reproducible. |
| V10 models | Y | 62 cells | — | Y | 0 | 0/62 | N | `FROZEN` `EXHAUSTED` | `MODEL_REPRESENTATION_EXHAUSTED`. |
| V11 allocation | Y (review) | none new | — | N | 0 | — | N | `FROZEN` | Next path was A-share. Done. |

**Do not reopen:** XA / RT / XR / IT / TS / MS / RI / AMS / IV / POS / INV / RATES / CARRY / SUP / CM / UM / BREADTH / SIZE.

### 1.2 A-share price / strategy (V12–V15)

| Family | Researched | Data | PIT | Hyp | Cand | FDR | Strategy | Status | Remaining |
|---|---|---|---|---|---|---|---|---|---|
| V12–V12.2 panel | Y (data) | 5549 / 18.4M raw | listing/ST/suspend | N | 0 | — | N | `FROZEN` | Do not re-download. |
| V13 CS price V1 | Y | frozen panel | Y | 12 | **2** | BH; 2 L1 | later | `FROZEN` | No 13th factor. |
| V13.1 reproduction | Y | same | Y | 2 | 2 survived | — | N | `FROZEN` | Do not retune. |
| V14 strategy | Y | official 20d book | Y | — | 2 | — | 2 weak | `FROZEN` | Full-path capital negative. |
| V14.1 forensics | Y | overlap vs capital | Y | — | 2 | — | gap | `FROZEN` | No Long Validation. |
| V15 residual / disp / disagreement | Y | same panel | Y | 9 | 0 new | 6/9 excess; 0/9 L1 | N | `FROZEN` `EXHAUSTED` | `PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`. No 10th. |

Price-only independent search on this panel = **EXHAUSTED**. Re-expressing close/amount/residual is not a new information source.

### 1.3 A-share information (V16)

| Family | Researched | Data | PIT | Hyp | Cand | FDR | Strategy | Status | Remaining |
|---|---|---|---|---|---|---|---|---|---|
| Financial annual Q4 | Y | 5500 sym / 64440 rows | announcement_date; RESTATEMENT_RISK | 6 | 0 | 0/9 unified | N | `FROZEN` `EXHAUSTED` | No 7th F*. No ROA/debt (unscanned). No quarterly unless new contract + new download. |
| Industry monthly as-of | Y | 171/171 | INDUSTRY_PIT_OK | 3 | 0 | 0/9 unified | N | `FROZEN` `EXHAUSTED` | No 4th I*. No industry×mom×low-vol. |
| Event announcements | N | empty `announcements/` | n/a | N | 0 | — | N | `DATA_BLOCKED` | No free PIT announcement store. |
| News / text | N | zero files | n/a | N | 0 | — | N | `DATA_BLOCKED` | Do not buy news API. |
| Options (CN or OG/LO) | N (quote only) | census JSON; no bars | n/a | N | 0 | — | N | `PAYMENT_REQUIRED` | V8.4 LO A / OG B. $93 unused. Do not buy. |

V16 machine: `data/market/research_engine/cn_a_share_information_v16/DECISION.json`  
`OVERALL=A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE` `STOP=STOP_B` `NEW_CANDIDATE=0`.

### 1.4 Not yet a contract on the A-share panel

| Family | Data on disk? | PIT feasible? | Independent of H11/H12? | Status | Why this is or is not new |
|---|---|---|---|---|---|
| **A-share × frozen macro CS** | YES. EURUSD 1971+, US500 2011+, GVZ 2009+. DXY/UST10/GOLD only 2018+ (too short for 2010 research cut). | YES. Strict `macro_calendar_date < ashare_signal_date`. | Designed to be. Cluster check required (low-beta ≈ low-vol). | `AVAILABLE` `NEW_RESEARCH_SPACE` | Macro was tested as GOLD/OIL predictor, never as A-share CS ranker. Not a price-only rewrite. |
| A-share IPO / listing age | YES. `tm-cn-a-BASIC-20260830-000001.csv` listing_date. | YES. Age at signal date from frozen basics. | Likely (not vol). | `AVAILABLE` `NEW_RESEARCH_SPACE` | New information (listing date), not a close formula. Second if macro dies. |
| A-share ST transition | YES. Daily `isST` in pack. | YES. Lagged ST flag. | Likely. | `AVAILABLE` | Thin CS after ST filter (V13 already excludes ST). Risk of reusing eligibility. |
| A-share calendar (month-end / CN holiday) | YES. Frozen CN calendar 13038 rows. | YES. | Partial. IT killed on MT5, not A-share CS. | `AVAILABLE` | Legal if CS interaction, not GOLD month-end clone. Third. |
| Dividend / CA full panel | Sample + adjust sidecar only | Incomplete | — | `DATA_BLOCKED` | Full dividend panel never frozen. Do not live-download. |
| Index membership (HS300/ZZ500 as-of) | Probe only; no freeze | Unknown | — | `DATA_BLOCKED` | Would need new BaoStock as-of download. Not authorized as silent extra download. |
| Balance-sheet ROA / debt | Probe only | — | — | `DATA_BLOCKED` | V16 did not scan balance. New download = new mission, not a silent V16 reopen. |
| Consensus / surprise | None | — | — | `PAYMENT_REQUIRED` | Trading Economics etc. |
| CN equity options | None | — | — | `PAYMENT_REQUIRED` | Forbidden in V16 source audit. |

---

## 2. Frozen datasets (do not replace)

| Layer | dataset_id | hash |
|---|---|---|
| Price | `tm-ashare-EQUITY-D1-20260830-000002` | `dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80` |
| Financial PIT | `tm-ashare-FINANCIAL-PIT-20260831-000001` | `bdd857d0c126c7d3b52188fc93da5063ba503c6d54a08235778baa9d71e332ee` |
| Industry PIT | `tm-ashare-INDUSTRY-PIT-20260831-000001` | `6ba883265c3a0d1be6599fe1832ef31354511a8451a7193e824cf2890971cc9c` |
| EURUSD D1 | `tm-market-EURUSD-D1-20260828-000001` | `4b1c1ae8b3d633bf4b133840ccdf39232a69277501c462ceb8413dd2eebd6ffb` |
| US500 D1 | `tm-market-US500-D1-20260828-000001` | `5d829d450904e512021301a8b6538e2b8ff8c69c07013d8edd3ff39c7575e8e4` |
| GVZ D1 | `tm-alt-CBOE-GVZ-D1-20260828-000001` | `7e77dab46fddb7898f73807e95faf6980e9de926fa77e21b257151d8d6918e3d` |

Split remains 70/15/15: Research 2010-01-04→2021-08-24 | Validation 2021-08-25→2024-02-29 | Denied 2024-03-01→2026-08-28.

---

## 3. Candidate gate (do not invent)

A-share Level-1 is the V15/V16 operational gate in `cn_a_share_information_v16/alpha.py` `_is_level1`, parented by `CANDIDATE_ACCEPTANCE_GATE_V1.md`:

- pre-registered
- research and validation `MEAN_FORWARD_RETURN` net > 0 (overlapping; **not CAGR**)
- BH-FDR q=0.05 on the closed family
- ≥2 evidence (excess vs EW and rank IC) on research **and** validation
- research **and** validation **capital account** total > 0
- PIT clean; no peek; no retune; sign as registered
- independence: `|corr|` vs H11/H12 ≤ 0.90 or tag `SAME_CLUSTER` (not a second sleeve)

CAGR ≥ 10% is not a gate. Cost model stays `A_SHARE_STRATEGY_COST_MODEL_V1`.

---

## 4. Selection

**Next family = A-share × frozen macro CS (`V17`).**

Rationale (IV / cost / data / PIT / independence):

1. Highest unused information among **free, frozen, PIT-able** sources.
2. Not a V0.8 clone (V0.8 predicted GOLD/OIL from USD; this ranks A-share names by lagged macro loading × shock).
3. Not a V15 residual rewrite (external series is the new field).
4. EURUSD and GVZ cover the locked 2010 research start. US500 starts 2011-01-17 (report coverage; do not invent a new split).
5. DXY / UST10 / GOLD 2018+ are **not** used as primary series — they would silently shrink Research to ~2.5y.
6. Event / News stay `DATA_BLOCKED`. Options stay `PAYMENT_REQUIRED` (spec later, do not stop the night on them).
7. If V17 `NEW_INDEPENDENT_CANDIDATE=0`, next legal family is A-share listing-age / ST / calendar (`AVAILABLE`), not price-only and not a purchase.

---

## 4b. Execution after this audit (2026-09-02)

| Family | Result | New status |
|---|---|---|
| V17 Macro CS | 0/6 L1, val capital 6/6 neg | `EXHAUSTED` |
| Event / News | no files | `DATA_BLOCKED` (unchanged) |
| V18 Altinfo | 0/6 L1; A2≡A1 rank | `EXHAUSTED` |
| V19 Industry×macro | 0/6 L1; IM6 excess FDR only | `EXHAUSTED` |
| Options | spec only | `PAYMENT_REQUIRED` (unchanged) |

Unified FDR m=18, discoveries=1 (IM6), Level-1=0. Global: `POST_V16_DECISION.md`.

## 5. Explicitly closed this audit

- Reopen H11/H12 / V13–V15 price-only / V16 F* I*.
- Live BaoStock re-download of financial/industry.
- Final OOS / Paper / Live / Portfolio.
- Buy Tushare / Wind / Choice / CSMAR / Databento / options.
- Xavier dispatch (V16 and this mission are Windows-local).
