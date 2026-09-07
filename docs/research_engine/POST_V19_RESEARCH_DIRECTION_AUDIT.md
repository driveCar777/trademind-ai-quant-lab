# Post-V19 Research Direction Audit

**Date:** 2026-09-02  
**Authority:** on-disk decisions and machine JSON. Not PROJECT_VISION. Not chat memory.  
**Question:** given current evidence, data, Research OS, and the no-purchase lock, where should the next unit of research resource go if the aim is an independent, reproducible, post-cost Alpha?

```
LEVEL = 1
CANDIDATE = 2          # H11_VOL_60 / H12_VOL_120 only
NEW_INDEPENDENT = 0
STRATEGY = 2           # WEAK_BUT_RESEARCHABLE; official 20-day books full-path negative
PORTFOLIO = 0
PAPER = 0
LIVE = 0
FINAL_OOS = DENIED
NEW_PURCHASE = FALSE
```

CAGR ≥ 10% remains the long-run capital aim. It is not a discovery gate and is not used to retune.

Status codes used below: `AVAILABLE` `LOW_VALUE` `ALREADY_TESTED` `DEPENDENT_ON_EXISTING_ALPHA` `DATA_BLOCKED` `PAYMENT_REQUIRED` `RESEARCH_SPACE_EXHAUSTED`.

`DATA_BLOCKED` ≠ “no Alpha exists.”  
`PAYMENT_REQUIRED` ≠ “no Alpha exists.”

---

## 1. What was actually researched

### 1.1 MT5 / CFD / public-alt (V0.1–V11)

Locked families on GOLD / OIL / EURUSD / USDJPY and the 841-CFD inventory. Representative kills:

| Object | Result | What it closed |
|---|---|---|
| HYP-0001 / FD / V0.5 / V0.6 | no Candidate; OIL D1 MOM WEAK_EDGE only | single-name short-hold price rules |
| XA / RT / XR | 3/3 + residual FALSIFIED | USD→GOLD/OIL; Δstate; GOLD/OIL residual |
| IT / TS / MS / RI / AMS | NO_CANDIDATE | calendar / microstructure / alt structure on those names |
| IV / COT / EIA / UST10 / CARRY / SUPPLY | NO_CANDIDATE | public actuals, not surprise |
| CM / UM / BREADTH / SIZE | NO_CANDIDATE; BREADTH WEAK_EDGE | metals cross; CFD breadth/size |
| TERM / OI / DTE / V8 fusion | FDR 0/15 | Pack E curve×OI×COT×EIA×yield |
| V9 103 books | 0 Positive Reproducible | unified replay |
| V10 62 models | FDR 0/62 | nonlinear / interaction on owned features |
| V11 allocation | review only | next path was A-share universe |

V11 FACT: MT5 alpha search is at low marginal value. Remaining MT5 holes are option surface, consensus surprise, and dated events — not another RSI/MA/OI/slope on the same four names.

### 1.2 A-share price and the only surviving cluster (V12–V15)

| Object | Result |
|---|---|
| V13 12 CS price hyps | Level-1 = H11_VOL_60 / H12_VOL_120. Val overlapping CAGR ≈ 0.55% / 1.30%. Momentum failed. |
| V13.1 / V14 / V14.1 | Survived as one `LOW_VOL_CANDIDATE_CLUSTER` (corr ≈ 0.996). Official 20-day capital 2010–validation negative (≈ −16% / −11%, MaxDD ≈ −66%). Overlapping `mean_net_h` ≠ CAGR. |
| V15 9 residual / dispersion / disagreement | 0 new Level-1. Val capital 9/9 negative. Residual corr vs H11/H12 ≈ 0.90–0.94. `PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`. |

### 1.3 A-share information (V16–V19)

| Object | n | What was actually tested | Result |
|---|---|---|---|
| V16 financial | 6 | Annual Q4 YoY NP/Rev, ROE, GPM, NPM, ROE Δ. Not ROA, not debt, not quarterly. | FDR 0/9 unified. Val capital 9/9 neg. Best non-candidate F4 val CAGR −11.53%. Rank IC val all negative. |
| V16 industry | 3 | Industry RS 20/60, industry breadth 20. Not industry×low-vol. | Same unified 0/9. |
| V17 macro CS | 6 | Stock-level β × EURUSD/US500/GVZ shock. | FDR 0/6. Val capital 6/6 neg. |
| V18 altinfo | 6 | Listing age, ST streak, resume, month/quarter-end. A2 rank-identical to A1. | 0 Level-1. A5 MEAN_FORWARD +0.12%, capital −19.95%. |
| V19 industry×macro | 6 | Industry EW β × same macros. | 0 Level-1. IM6 excess FDR only; val CAGR −9.44%. |
| Post-V16 unified | 18 | V17+V18+V19 | discoveries=1 (IM6), Level-1=0 |

These families are frozen. Do not retune, flip sign, or reopen H11/H12.

---

## 2. Whole category vs a few proxies

| Category | Coverage | Verdict |
|---|---|---|
| A-share price CS (close/amount/vol/residual) | Broad (V13+V15). Independent search exhausted. | `RESEARCH_SPACE_EXHAUSTED` |
| Annual profit-sheet *ratios* | Six proxies, not the catalog. All val Rank IC < 0 and all capital < 0. | Category `LOW_VALUE`. More ROA/debt/quarterly is the same slow accounting object, not a new mechanism. Stop the class. |
| Industry labels as RS/breadth | Three proxies. | `LOW_VALUE` for more RS lookbacks. Labels remain usable as a *join key* (V19 already used that). |
| Macro *as A-share CS ranker* | EURUSD / US500 / GVZ at stock and industry β. DXY/UST10/GOLD unused as primary (2018 start would shrink the locked 2010 Research cut). | Tested mechanism `ALREADY_TESTED`. Short-history macros `LOW_VALUE` unless a new split is authorized. |
| Listing age / ST / calendar on A-share | Six hyps; one contract defect (A1≡A2). | `ALREADY_TESTED` |
| Index membership / reconstitution | Probe only (HS300 `date=` works; 2018 vs 2026 symmetric_diff=258). Never a contract. | `AVAILABLE` |
| Dividend / payout event | 600519 sample + `query_dividend_data` probe. No panel. V14.1: current books are price return, not total return. | `AVAILABLE` after free download; dependence risk vs low-vol/value. |
| Event filings / news | Empty `announcements/`; zero news files. | `DATA_BLOCKED` |
| Option surface | V8.4 occupancy only. Bytes=0. | `PAYMENT_REQUIRED` |
| Macro *surprise* / consensus | Owned series are actuals. V2 RATES/EIA already failed on actuals. | `PAYMENT_REQUIRED` |
| MT5 4-name book | 37 killed families + 103 books + 62 models. | `RESEARCH_SPACE_EXHAUSTED` on owned features |

---

## 3. Families close to H11/H12 (low marginal value)

H11/H12 = long low realized vol, hold 20, top quintile. One cluster.

| Family | Why close | Action |
|---|---|---|
| V15 residual | pred corr 0.90–0.94 | Do not reopen |
| More vol lookbacks / quantiles | same object | Forbidden retune |
| Static large-cap / low-turnover / “quality” price sorts | economically adjacent to low-vol | `DEPENDENT_ON_EXISTING_ALPHA` unless independence is measured and fails the 0.90 gate |
| HS300 *static* membership | likely size/liquidity/quality; may cluster with H11 | Runnable only as a measurement, not as a hoped-for second sleeve |
| Another A-share close-formula CS factor | V15 review | `LOW_VALUE` |

Reconstitution (add/delete), dividends, and option surfaces are **not** close-formula rewrites of H11/H12. They can still fail independence after the fact.

---

## 4–6. Blocked / free / paid

### DATA_BLOCKED (honest experiment impossible now)

- PIT announcement / earnings-surprise store (`announcements/` = `.gitkeep`)
- News / text
- Full dividend panel (not frozen; API exists)
- Quarterly + balance-sheet sweep (API exists; V16 did not download)
- HS300/ZZ500 as-of panel (API exists; probe only)
- ETF flow / IOPV / northbound / margin detail

The last four are blocked **as frozen files**, not as vendor products. BaoStock can supply index as-of, dividend, quarterly, and balance without purchase.

### PAYMENT_REQUIRED

| Item | Quote / note | Information-value assessment |
|---|---|---|
| LO 1Y MVD-A | $11.99 if a human later spends. V8.4 sufficiency **A**. | New information class (IV/skew/term) on a **4-name CFD book that already failed V9/V10 even after Pack E**. Information increment: high vs owned features. P(Level-1 Candidate): low-to-medium. Not auto-buy. $93 unused. |
| OG options | Sufficiency **B**; futures month ≠ option month 0%. | Weaker than LO. |
| Tushare / Wind / Choice / CSMAR / news API | not quoted this mission | Would unblock event/consensus/northbound. Do not buy. |
| Databento extra / $199 Standard | already rejected | Do not reopen. |

### Free and immediately usable after a BaoStock as-of sweep

1. **HS300 / ZZ500 membership history** — one call per date, not per symbol. V12 FACT: `query_hs300_stocks(date=)` is PIT. ~171 monthly snapshots × 2 indices.
2. **Dividend operate/cash panel** — per symbol-year; same scale as V16 financial. Mechanism is payout/ex-date, not ROE.
3. Quarterly/balance — free, but `LOW_VALUE` given V16 annual Rank IC sign.

---

## 7. Should A-share stay the primary universe?

**Yes, for the next unit of resource — not because more price CS factors are worth it.**

V11 moved here because MT5 residual IV was spent and A-share had untested information diversity. V13–V19 spent the *easy free* layers (price, annual ratios, industry RS, macro β, age/ST/calendar). That does **not** restore MT5 as the primary search universe.

A-share remains primary only while a **new mechanism** is still free and PIT-able. If index membership and (if needed) dividends also die, the free A-share information argument collapses and the honest next write-up is `A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED`, not another CS factor farm.

---

## 8. GOLD / OIL / EURUSD / USDJPY leftover space

Mechanisms tested on those names are **not** the same as A-share low-vol CS, so correlation with H11/H12 would likely be low. That is irrelevant: those mechanisms were **FALSIFIED on their own book**.

Untested leftovers on that universe:

| Leftover | Status | Why not NEXT |
|---|---|---|
| Option surface | `PAYMENT_REQUIRED` | See §6. Human gate. |
| Consensus surprise | `PAYMENT_REQUIRED` | Actuals already failed (V2). |
| Dated events | `DATA_BLOCKED` | No timestamp+consensus store. |
| A-share market EW → GOLD | never a contract | Economically a risk-on clone of XA / US500 paths. `LOW_VALUE`. |
| Another D1 timing rule | `ALREADY_TESTED` | V9/V10 closed owned-feature search. |

Do not reopen XA / RT / XR / IT / TS / MS / RI / AMS / IV / POS / INV / RATES / CARRY / SUP / CM / UM / BREADTH / SIZE.

---

## 9. Structures not truly tested

| Structure | Status | Note |
|---|---|---|
| A-share index reconstitution / membership | `AVAILABLE` | Highest free EIV. This audit’s choice. |
| A-share dividend / payout change | `AVAILABLE` | #2 if membership dies. Dependence risk. |
| A-share event text / surprise | `DATA_BLOCKED` | High theoretical IV; no files. |
| Cross-market term structure | `ALREADY_TESTED` | V6–V8. |
| Funding / positioning (COT) | `ALREADY_TESTED` | V2. |
| Public macro *state* on A-share names | `ALREADY_TESTED` | V17/V19. |
| Option IV/skew/VRP | `PAYMENT_REQUIRED` | Highest paid EIV; 4-name mapping hole remains. |

---

## 10. Is there a direction worth more than dozens more A-share CS factors?

**Yes. Do not run dozens more A-share CS factors.**

Expected information value, *conditional on current locks*:

| Rank | Direction | EIV | Why |
|---|---|---|---|
| 1 | **A-share HS300/ZZ500 membership + reconstitution** | Highest *executable* | New institutional-demand object. PIT already demonstrated. Cheap as-of download. Not a close formula. Independence vs H11/H12 is measurable. |
| 2 | A-share dividend / payout event panel | Medium | New payout object. Free. Likely closer to value/low-vol than reconstitution. Larger download. |
| 3 | LO option surface | Highest *theoretical new class* | New IV information. Payment required. Low P(Candidate) on the exhausted 4-name CFD book. Do not buy in this mission. |

Quarterly/balance, more annual ratios, more macro β lookbacks, more age/ST, and another price CS factor are **below** these three. They are coverage completion of killed classes.

---

## Selection (executed by this mission)

**Next family = V20 A-share index membership / reconstitution.**

Not another financial ratio. Not a price-only factor. Not a purchase.

Pre-registered question (one question, four hyps):

> After cost, on the frozen A-share panel and the locked 70/15/15 split, do CSI 300 / CSI 500 membership or 252-session add/delete sets contain a Level-1 independent edge?

If the answer is no, stop the *membership* class. Do not add SZ50, do not add 504-day twins, do not flip signs. Then the next free class is dividends — only if it still has independent economic content.

If the answer is a new independent Candidate, stop searching and freeze reproduction. Do not farm neighbors.

### V20 result (2026-09-02)

PIT: 171/171 monthly as-of. Moutai in HS300 2010 and 2024. 300750 absent 2010. 2018 vs 2024 symmetric_diff=258. Mutation OK.

| ID | Val MEAN_FORWARD | Val capital | Val CAGR | Rank IC val | FDR | L1 |
|---|---|---|---|---|---|---|
| X1_HS300_SET | −1.26% | −32.50% | −14.22% | −0.0077 | N | N |
| X2_ZZ500_SET | −1.00% | −23.88% | −10.10% | −0.0027 | N | N |
| X3_HS300_IN_252 | −2.37% | −56.79% | −27.93% | −0.0217 | N | N |
| X4_HS300_OUT_252 | −1.21% | −26.65% | −11.39% | −0.0189 | N | N |

`A_SHARE_INDEX_MEMBERSHIP_V1_NO_CANDIDATE` / `STOP_B_FAMILY`. FDR 0/4.

Stop the membership class. Do not add SZ50, 504-day twins, or flip signs.

Updated ranking after V20: static membership and reconstitution are `ALREADY_TESTED` / `LOW_VALUE`. Dividend *yield level* is now `LOW_VALUE` (same size/quality neighborhood as failed V16+V20). Remaining free distinct object = dividend **announcement windows** (V21). Not operate/ex-date as knowledge time.

### V21 result (2026-09-04)

PIT: 5549 files, 24803 rows, 24029 cash. announce_date < signal. Operate date not knowledge time.

| ID | Val MEAN_FORWARD | Val capital | Val CAGR | Rank IC val | FDR | L1 |
|---|---|---|---|---|---|---|
| D1_CASH_ANN_20 | −4.24% | −41.06% | −36.68% | −0.0223 | N | N |
| D2_STOCK_ANN_20 | −16.48% | −72.02% | −92.34% | −0.0234 | N | N |

`A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE` / `STOP_B_FAMILY`. FDR 0/2.

Stop announcement-window class. Do not retune 20d. Do not flip short. Do not open forecast/express as a sibling filing window.

Global after V21: `A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED`. See `POST_V21_DECISION.md`. Next unit = stay stopped.

---

## Explicitly closed by this audit

- Reopen H11/H12 / V13–V19.
- More annual/quarterly/balance *ratio* hyps (`LOW_VALUE`).
- DXY/UST10/GOLD as primary macros without a new split.
- Auto-buy LO/OG/Tushare/Wind.
- Final OOS / Paper / Live / Portfolio / `order_send`.
- Xavier dispatch (Windows-local, same as V16–V19).
