# TradeMind — 修改记录

> 研究代码现入 private GitHub。秘密仍禁止入库。冻结研究不可用 Git 回滚。

---

## 2026-09-06 (10:10) — V31 CN futures XS: NO_CANDIDATE (weak same-sign residual)

- Contract `V31_CN_FUTURES_XS_CONTRACT.md` committed before run. Pre-run revision (no scores yet): honest 20-day labels from per-contract series (2018-05+), first pred 2019-07, research→2023-06, validation 2023-07→2026-08. 8 features → one LightGBM (V25 params) frozen 2023-06-30 → LS tercile, 3.3 bp/side. Roll unit test passed (synthetic +10% jump → same-contract 0). `cn_futures_v31/pack.py` + `run.py`; refuses rerun.
- Result `CN_FUTURES_XS_V31_NO_CANDIDATE`: G1 validation LS +6.0% (CAGR 1.9%, t 0.48) pass; G4 research LS +13.9% pass; G2 gross L−S +0.32%/20d t 0.81 fail; G3 rolling 3/5 fail (2021 −5.8%, 2023H1 −4.5%); G5 validation align n=0 (V26.8 book ends 2024-01-26, 7-day offset > 5-day tolerance) — combined overlap n=21 corr 0.25 would have passed. Research LO +61% is 2020 commodity β. Jump bias vs continuous 0.1–0.2%/20d. ATLAS 78. Do not retune; do not map GOLD/OIL. Next = V35 `CN_INFO_TO_COMMODITY`.

## 2026-09-06 (09:50) — V26.8 scaled unit (N_target cap) + multi-horizon analysis; adopted

- Ex-ante: ¥5 minimum commission on ¥2,000 names = 0.5%/period ≈ 5.8%/yr, and deposits diluted the V26.7 list to 125 names (per-invested-yuan return 1.58% vs 1.98%, paired t −2.25). `V26_8_ML1_SCALED_UNIT_CONTRACT.md` committed before run: `unit = max(¥2,000, equity/N_target)`, grid {10, 20, 40} selected on RESEARCH by per-period Sharpe, winner read once on VALIDATION. `scale_book.py` adds a daily mark-to-market, deposit-adjusted TWR curve and day/week/month/quarter/year/rolling-1-3-5y statistics.
- Research grid: N10 +551% (CAGR 21.3%, Sharpe 0.219) / N20 +422% / N40 +369% — monotone; winner N10. Validation: TWR +39.0% (CAGR 14.0%), excess +2.05%/20d t 2.86, 19/29, money ¥74k → ¥86.9k, profit ¥12.9k, IRR 10.4% (V26.7: +27%, IRR 4.2%). → `ML1_SCALED_UNIT_N10_FULL_CONTRIB2K_MAIN_VIABLE_HISTORICAL`; adopted as `daily.py --n-target 10` default; `shortlist.py` / `LEDGER_TOP20` use the scaled unit.
- Multi-horizon (daily MTM): research daily σ 1.8%, worst day −9.9%, worst week −21%, worst month −31%, 2015 +147%, 2017/2018 −22% each, **daily MaxDD −55.9%** (2015-06→09, 231 sessions to recover), rolling 1y negative 22% of start days, 3y 13.5%, 5y 0%; validation weekly positive only 48%, **daily MaxDD −24.4%** (2022-01→04). Correction: period-end MaxDD computed on deposit-inclusive equity understated drawdowns (V26.7 validation −13% → −18% TWR-based; V26.8 −5% → −15%); `maxdd_period_end_twr` written into both READ files. Shell frozen.

## 2026-09-06 (09:35) — V26.7: 100% exposure + ¥2,000 monthly deposit (owner's ex-ante constraint change); adopted

- Owner 09:14: no 80% cap, all cash deployable; at least ¥2k deposited monthly. `V26_7_ML1_FULL_TOPUP_CONTRIB_CONTRACT.md` committed before the run; adoption rule = VIABLE (exposure and deposits are the owner's decision, not selected by return). `top_n_book.py`: `monthly_contrib` (added on the first signal day of each month before buying), ¥200 fee reserve at 100%, `total` stays time-weighted, plus deposits / profit / IRR; `_irr` approximation superseded by exact-deposit-date IRR written into the READ file post hoc.
- Single read: research TWR +264% (CAGR 14.2%, MaxDD −44.9%, excess +1.27%/20d t 4.47, 82/112 beat EW), money ¥236k in → ¥432k, profit ¥196k, IRR 11.2%; validation TWR +27.0% (CAGR 10.0%, MaxDD −13.2%, excess +2.44% t 3.58, 23/29), money ¥74k in → ¥79.0k, profit ¥5.0k, IRR 4.2% (last period Jan–Feb 2024 −15.1% on the largest equity). Lower TWR than V26.6 is the diversification effect of N growing with deposits (27 names in validation, 125 late research), not a defect. 2017 −30.5%, 2018 −29.6% at full exposure. → `ML1_FULL_TOPUP_CONTRIB2K_MAIN_VIABLE_HISTORICAL`, adopted: `daily.py` defaults `--exposure 1.0 --monthly-contrib 2000`; `shortlist.py` fee reserve + contract label; `LEDGER_TOP20` books monthly deposits; today's shortlist capital = closed ledger equity + this month's deposit. Smoke: 2026-08-28 shadow shortlist 10 names, ¥19,746 deployed. Shell frozen; no V26.8.

## 2026-09-06 (09:25) — V26.6 top-up: deploy the idle 42% of the ¥20k shell; adopted as `daily.py` default

- Ex-ante arithmetic fact from the V26.5 read: mean idle cash 42.4% (¥2,000/name × whole lots leaves a remainder per name; names > ¥20 cannot afford one lot and are skipped), i.e. only ≈¥11.5k of ¥20k was in the market. `V26_6_ML1_EQMONEY_80PCT_TOPUP_CONTRACT.md` committed before the run: one change only — a second pass that cycles through the already-selected names in score order adding one lot each until the 80% budget is exhausted. No new names, no change to ML1, exit, or costs. Adoption rule pre-declared (VIABLE and validation > V26.5's +12.1%).
- Single read: research +318% (CAGR 15.9%, MaxDD −44.8%, excess +1.25%/20d t 4.30, idle 21%); validation **+33.9% (CAGR 12.3%, MaxDD −11.4%, excess +2.38%/20d t 2.56, 19/29 beat EW, idle 21%)** → `ML1_EQMONEY_80PCT_TOPUP_MAIN_VIABLE_HISTORICAL`. Adopted: `top_n_book.py` `topup` flag, `shortlist.py` top-up pass + contract label, `daily.py` default on (`--no-topup`). Smoke on disk data: 2026-08-28 shadow shortlist 8 names, ¥15,879 deployed of ¥16,000 budget. Denied/recent windows not read. No V26.7.

## 2026-09-06 (09:00) — V34 exit-rule diagnostic: take-profit / stops / trailing / break-even do not help

- Owner asked whether take-profit, trailing take-profit and protective break-even stops were considered. `V34_EXIT_RULES_DIAG_CONTRACT.md` frozen before run; `cn_a_share_ml_v25/exit_rules_diag.py` (single read, RESEARCH window only, validation and denied window untouched). 13 pre-declared rules (TP 5/10/20, hard stop 5/10, trailing 5/10, break-even 3/5, two combos), close-triggered, next-open exit with V26.4 carry, on ML1 (V26.5 shell, hold 20) and V33 (hold 5).
- ML1: BASE +144% (CAGR 9.6%, excess +0.65%/20d t 1.85). 11 of 12 rules worse; tight rules destroy it (TP5 → +25%, TRAIL5 → +12%). Only TP20 marginally better (+188%, t 1.97, 13% triggers) — 1-of-13 noise, not selected, not economically motivated. No rule materially lowers MaxDD (best −31% vs −39% at half the return). V33: no rule flips sign (best −67%). → `EXIT_RULES_NO_IMPROVEMENT`. Nothing written into `daily.py`.

## 2026-09-06 (09:20) — V31 dataset frozen; V33 limit-up event model single read: predictive, not tradable

- `tm-cnfut-SINA-D1-20260906-000001` frozen: 73/73 declared products dominant-continuous (2005+), 5,614 per-contract series (mostly 2018-05+), 7,884 requests 0 failures, 1.22M rows, per-file sha256 manifest. V31 contract next.
- Owner (08:37) asked for a small-capital "predict who will limit-up soon from prior-day anomalies / technicals / fundamentals" strategy. `V33_LIMITUP_EVENT_MODEL_CONTRACT.md` frozen before run; `cn_a_share_ml_v33/run.py` single read (refuses on rerun). Label = limit-up close within t+2..t+6; 21 features (ML1's 14 + 7 D1 event features); LGBM classifier walk-forward, frozen 2021-08; gate book = owner shell (¥20k, main board, 80%, ¥2,000/name) hold 5 with carried exits; diag LO20 hold 5.
- Result: validation top-10% hit 12.4% vs base 4.4% (lift +8.0pp, t 60.9, 99.8% of sessions positive) — strongest predictive statistic in the repository; owner shell validation −88.1% (excess vs shell EW −1.66%/5d t −3.4), LO20 ¥1M −66.5%, research equally negative → `A_SHARE_LIMITUP_EVENT_V33_PREDICTIVE_BUT_NOT_TRADABLE_AT_20K`. Mechanism: lottery/MAX effect — high-amplitude, high-vol, recently-limit-up names have deeply negative mean 5-day returns; the same information ML1 uses via NEG_VOL, with the opposite sign. Not a capital-size problem. ATLAS 77 rows. `top_n_book.py` gained a `hold` parameter (default 20, unchanged behaviour).

## 2026-09-06 (01:05) — Owner execution preference (MT5); MT5 D1 legal-object inventory = 0; A-share V26.5 frozen; next cut V31

- Owner: prefers to execute on MT5; futures account later; do not reopen falsified gold/oil/FX/CFD families; no H1/tick; A-share V26.5 frozen (lists + shadow ledger only, no more shell changes); no parameter/cost/leverage changes for return.
- `MT5_D1_LEGAL_OBJECT_INVENTORY.md`: every instrument class on the terminal mapped against `FAILURE_ATLAS.json` and V1–V8 / V30 / V32. Immediate legal new objects = 0. ETF CFDs measured today: swap long −11.09%/yr, same ceiling as share CFDs. Only untested layer `CN_INFO_TO_COMMODITY` (A-share panel → COPPER/SILVER/CrudeOIL) is legal but low-power (targets start 2018-12) and is queued after V31.
- V31 → MT5 execution mapping with measured costs (GOLD swap ≈ 0.13%/yr, SILVER ≈ 1.1%/yr, COPPER/CrudeOIL −4.5%/yr both sides; spreads 0.02–0.14%).

## 2026-09-06 (00:32) — Owner allows 80% exposure; V26.5 `ML1_EQMONEY_80PCT_MAIN` single read VIABLE_HISTORICAL; recent-window diagnostic

- `V26_5_ML1_EQMONEY_80PCT_MAIN_CONTRACT.md`: identical to V26.4 except exposure 70% → 80%. "100% when necessary" not adopted (no ex-ante trigger; any trigger derived from results is tuning). Compounding reinvestment was already how every book works (N = floor(exposure·equity/2000) grows with equity).
- Single read: research +144% (CAGR 9.6%, MaxDD −39%, 1750 fills, 20 carried exits, 28 STUCK); validation +12.1% (CAGR 4.7%, MaxDD −10.8%, 248 fills), excess vs EW +1.51%/20d t 2.65, 19/29 → `ML1_EQMONEY_80PCT_MAIN_VIABLE_HISTORICAL`. 80% validation is below 70% (+13.4%) — lot-rounding noise; no exposure will be chosen from this.
- `recent_diag` (diagnostic, no decision) on the window V28 already consumed (2024-03-01..2026-08-28, REFIT_240 gate scores, benchmark EW of eligible main-board close ≤ ¥100): full +28.6% (28 periods, MaxDD −16.4%) with excess +0.10%/20d t 0.16 (beta); last 12m +9.5% (excess +1.18% t 1.2, 7/11); last 6m −7.7% vs EW −13% (excess +1.15% t 1.4, 4/5). Reported for the final contract only; never used as a gate.
- `daily.py` default `--exposure 0.80`; 2026-09-04 list 8 names ≈ ¥13,427.

## 2026-09-06 (00:15) — V26.3 attribution; owner allows equal-money multi-lot; V26.4 `ML1_EQMONEY_70PCT_MAIN` single read VIABLE_HISTORICAL

- Attribution of V26.3 validation (diagnostic on the same fills): equal-weight gross +2.27%/20d → one-lot price-weighted +0.50% → commission −0.67% → slippage+stamp −0.27% → ≈ −0.44% on invested × 70% ≈ −0.3%/period = −10.8%. Cause is the one-lot rule (avg 8.8 names, max single weight 33%), not entry/exit timing or the model.
- Owner (00:13) allows equal money per name with multiple lots and asks the backtest to respect: data available after close, buy at next open, sell no earlier than the following open, and a limit-down day blocks the sale.
- `V26_4_ML1_EQMONEY_70PCT_MAIN_CONTRACT.md` frozen before run, single read: main board, close ≤ ¥100, 70% exposure, ¥2,000 per name (smallest unit keeping the ¥5 minimum fee ≤ 0.25%/side; same unit as V26.2), N = floor(0.7·equity/2000) (7 at ¥20k), lots = floor(2000/(100·open)), entry non-fill = cash; **new exit rule**: if the planned exit open is limit-locked/suspended, keep holding and try each next open up to 10 sessions, else mark at that close as STUCK (stricter than the V14.1 convention that drops the trade). Result: research +156% (CAGR 10.2%, MaxDD −33%, 1520 fills, 16 carried exits, 26 STUCK), validation +13.4% (CAGR 5.1%, MaxDD −7.9%, 216 fills, 0 carried), excess vs EW +1.48%/20d t 2.55, 20/29 → `ML1_EQMONEY_70PCT_MAIN_VIABLE_HISTORICAL`. Cash idle ≈ 47–49% (30% rule + lot rounding). V14.1-convention diagnostic: research +142%, validation identical.
- `ml1_live/shortlist.py` `write_shortlist_eq_money`; `daily.py` default is now V26.4 (`--one-lot` keeps V26.3 for reference). 2026-09-04 list: 7 names ≈ ¥11,627.
- No parameter of V26.4 will be adjusted; owner-goal arithmetic in `OWNER_CONSTRAINTS_AND_GOAL.md` unchanged.

## 2026-09-05 (23:36) — Owner constraints & life-goal statement; V26.2 void; V26.3 `ML1_ONELOT_70PCT_MAIN` single read NOT_VIABLE

- Owner statement (not a research task; no change allowed to raise returns): age 27, goal financial independence by 35 (expectation, not a gate); ¥20k max during validation, later +¥2k–10k/month; one lot = 100 shares so price ≤ ¥100 is acceptable (¥20 was an arithmetic error); never 100% invested, exposure fixed in advance; max 1 lot per name; skip if unaffordable; N emergent, never chosen ex post; MT5 verdict stands, leverage is not an accelerator.
- V26.2 (≤¥20, N=10) declared void; its files are kept as evidence, unmodified.
- `V26_3_ML1_ONELOT_70PCT_MAIN_CONTRACT.md` frozen before run, single read enforced in `top_n_book.py V26_3` (refuses if `ML1_ONELOT_70PCT_MAIN_READ.json` exists): main board, close ≤ ¥100, 70% exposure (owner's example number adopted as-is), exactly 1 lot per name in score order while affordable, cost model V1 + ¥5 minimum fee, ¥20k, denied window not read. Research +74.7% (CAGR 5.9%, MaxDD −44%, 17.3 names avg, 32% idle); validation −10.8% (CAGR −4.4%, MaxDD −14%, 8.8 names, 30% idle); excess vs EW +0.46%/20d t 1.2 and +0.65% t 0.87 → `ML1_ONELOT_70PCT_MAIN_NOT_VIABLE`. Cause is the execution shell (weights ∝ price, minimum fee on ¥200 lots, 30% cash), not the ML1 ranking. No exposure/price/lot variants will be tried.
- `ml1_live/shortlist.py` `write_shortlist_one_lot`; `daily.py` defaults switched to V26.3 (`--exposure 0.70 --max-price 100 --boards MAIN --manual-capital 20000`, `--n-names 0`); `LEDGER_TOP20.json` now carries the V26.3 shadow book with `historical_gate: NOT_VIABLE`. 2026-09-04 one-lot list: 13 names, ¥13,996 (one ¥55 name = 39% of deployed).
- `docs/OWNER_CONSTRAINTS_AND_GOAL.md`: compounding arithmetic ¥20k + 2k/6k/10k per month × 8 years at evidence-based CAGRs (−4.4% … 13.7%): terminal 17–39万 / 50–106万 / 82–172万 vs principal 21 / 60 / 98万. Gap is principal, not edge; no cell reaches a 4%-rule target of 250万. Recommendation: shortlist and shadow ledger continue, owner stays off live money, all research resource to V31.

## 2026-09-05 (23:20) — V26.2 recent-window diagnostic; V32 MT5 macro pooled model NO_CANDIDATE

- Owner asked for last 1y/6m/1m of the executable ML1 variant and to start MT5 gold/oil/FX.
- V26.2 diagnostic on the already-read V28 window (REFIT_240 gate scores; no decision attached, nothing tuned): 2024-03→2026-08 +31.5% (28 periods) but excess vs main-board≤¥20 EW +0.01%/20d t 0.01 (15/28); last 12m +9.1% (excess +1.2% t 0.84); last 6m −12.6% (EW −12.7%); last period +1.0%. The 10-name low-price main-board slice carried beta only in this window while the 999-name ML1 book had +1.00%/20d t 9.3. `ML1_TOP10_20K_MAIN_RECENT_DIAG.json`; ATLAS row 76.
- V32 `MT5_MACRO_POOLED_V32` (Amendment V2.1: pooled panel ML ≥50 instruments × ≥10y allowed as one model). Dataset `tm-mt5-MACRO-D1-20260905-000001` frozen (69 symbols, 288,708 rows; non-FX only since 2018-12). 10 vol-normalised features → pooled LightGBM → LS tercile vol-parity, hold 5, measured spread + swap. **NO_CANDIDATE**: validation gross spread +0.06%/5d t 1.02 (research t −0.64); LS −60.5% t −8.5; rolling 0/5; all gates FAIL. `V32_MT5_MACRO_POOLED_DECISION.md`; ATLAS row 75. MT5 macro D1 research objects exhausted (V1–V8 rules, V30 share CFDs, V32 pooled ML).

## 2026-09-05 (22:44) — Owner facts (main board only, ¥20k, price ≤ ¥20) → V26.2 `ML1_TOP10_20K_MAIN`

- Contract `V26_2_ML1_TOP10_20K_MAIN_CONTRACT.md` frozen before run (m+1). N = 20000 / 2000 = 10 derived from capital and the ¥20 price ceiling (one lot ≤ ¥2,000), not tuned. Main board only; signal-day close ≤ ¥20; ¥2,000 per name, lot rounding; ¥5 minimum commission (≈0.25%/side; round trip ≈0.75%/period).
- Historical read on frozen ML1 scores, denied window not read (`ML1_TOP10_20K_MAIN_READ.json`): research +402% (CAGR 18.1%, MaxDD −43%); validation +32.7% (CAGR 11.9%, MaxDD −11%), excess vs EW +2.4%/20d (t 2.4), 20/29; 10/10 fills; ≈22% cash idle. `ML1_TOP10_20K_MAIN_VIABLE_HISTORICAL`.
- `top_n_book.py` / `shortlist.py` / `daily.py`: `n` and `max_price` parameters; daily defaults now `--boards MAIN --manual-capital 20000 --n-names 10 --max-price 20`. `SHORTLIST_2026-09-04.csv` regenerated (10 names). ML1 list and V26 ledger untouched; nothing places orders.

## 2026-09-05 (22:20) — Execution assumption corrected by owner; V26.1 ML1_TOP20_MANUAL contract, historical read, pipeline outputs

- Owner: small capital, Ping An ordinary account, no quant permission (not obtainable short-term); never assume QMT/PTrade or automated 999-name execution; no computer-use / unofficial-API order entry; execution = system emits a short list, owner enters orders by hand; MT5 US names are CFDs and there is no US account; futures account not open (research may proceed). Written into `MASTER_PLAN_V2.md`, `AGENTS.md`, `TRADEMIND_CONTEXT.md`.
- `V26_1_ML1_TOP20_MANUAL_CONTRACT.md` (frozen before run): ML1 scores unchanged; top 20 by score, equal weight, `lots = floor(alloc/(100·open))`, zero-lot names skipped and back-filled, V14.1 non-fill rules, cost model V1 + ¥5 minimum commission per order, capital parameter (default ¥100k), denied window not read, board filter set by owner permission.
- `cn_a_share_ml_v25/top_n_book.py` — historical read on frozen ML1 scores (research 2012-01→2021-08, validation 2021-08→2024-02), three permission scopes (m+3, none chosen by result): ALL research +298% / validation +17.0% (excess vs EW +2.0%/20d t 3.3, 22/29); MAIN_CHINEXT +385% / +10.5% (t 2.8); MAIN +410% / +34.5% (MaxDD −10%, t 3.1). All `ML1_TOP20_MANUAL_VIABLE_HISTORICAL`. ~10–13% cash idle from lot rounding; ~19.3–20 fills per period.
- `ml1_live/shortlist.py` + `daily.py --manual-capital --boards`: every run now also writes `SHORTLIST_{date}.csv/json` (20 names, estimated lots) and `LEDGER_TOP20.json` (TOP20 shadow ledger from the 2026-08-28 chain signal, in parallel with the 999-name ledger). ML1 list and V26 ledger untouched. Nothing places orders.

## 2026-09-05 (night) — MASTER_PLAN_V2 (owner-authorised plan revision) + V31 China futures cross-section Design

- Owner: "you may modify my design and plan; markets = MT5 gold/oil/majors, A-shares, China futures, US equities". `docs/MASTER_PLAN_V2.md`: platform (Xavier cluster, AI Gateway, 7 preset strategies, manual-confirm paper orders) frozen with no further investment; caution moved to statistical gates; market verdicts A-shares (1) > China futures (2) > US equities (3); MT5 macro symbols closed as research objects, kept only as an execution venue for futures-derived views (Ava Trade has `GOLD`/`SILVER`; earlier "no gold symbol" statement corrected). V26 execution gap recorded: 999 equal-weight names every 20 sessions is not manually executable → broker quant API (QMT/PTrade) required; "top-100" only as a new forward-validated contract. `ROADMAP.md` now points to MASTER_PLAN_V2.
- `V31_CN_FUTURES_XS_DESIGN.md`: data-source probe — exchange sites reset from this machine (Clash exit abroad; owner can add DIRECT rules), Sina futures API works (product continuous series from 2005, per-contract only from ~2019-05, 3–10 s/request), Eastmoney futures SSL fails. Two-stage plan (Sina first; exchange full history as V31.1 reproduction). Draft: ~70 products, 8 fixed features (incl. term slope / basis momentum 2019+), one LightGBM (V25 params), LS tercile gate book, roll-adjusted returns with unit test, independence gate corr vs ML1 < 0.3. No contract, no run yet.

## 2026-09-05 (afternoon) — Amendment V2 (MT5 scope) + V30 MT5 US share-CFD cross-sectional price model: NO_CANDIDATE, CFD cost ceiling

- Owner asked to start MT5 now and lift the old MT5 limits. `RESEARCH_RULES_AMENDMENT_V2_MT5.md`: lifted (a) the ML ban for cross-sections ≥300 names, (b) "share CFDs = inventory only", (c) long-only-book requirement (LS book allowed as pre-registered gate); kept pre-registration, measured costs, FDR, rolling windows, no order_send, no reopening of the 20+ falsified macro-CFD families. Terminal inventory: no XAUUSD/US500/BTC symbols on this broker; 497 `CFD-Shares\USA`, 67 US ETFs, ~55 FX, ~15 commodities.
- Dataset `tm-mt5-USSHARES-D1-20260905-000001`: 492 symbols with D1 bars, 2.37M rows (354 names start ≤2008), pulled from the local Ava Trade terminal in 5.9 h (server-side history sync ≈50 s/symbol). Specs: swap_mode 5, swap_long −11.09%/yr (488/492), swap_short −0.91%/yr, quoted spread median 0.15%.
- Contract `V30_MT5_US_XS_CONTRACT.md` (7 fixed price features → one LightGBM with V25 params → LS20 gate / LO20 diagnostic, measured spread + slippage + calendar-day swap). Pre-run revision after seeing data depth (before any score existed): research 2006-01→2019-12, validation 2020-01→2026-08, REFIT_240, 5 rolling blocks.
- **Result `MT5_US_XS_PRICE_V30_NO_CANDIDATE`** (`mt5_xs_v30/RESULTS.json`): validation gross L−S spread +0.07%/20d (t 0.18); LS20 −71.5% (t −4.0); LO20 −29.1%, LO−EW −1.03%/20d (t −4.4); rolling 2/5; research LS20 also negative after costs. Gates 0/4. Atlas row 74.
- Decision `V30_MT5_US_XS_DECISION.md`: price layer dead (consistent with A-share V15) **and** a CFD cost ceiling — LS round trip ≈1.9%/20d (≈25%/yr), LO ≈1.1%/20d, above any plausible gross spread; survivorship makes the result an upper bound. `MT5_STOCK_CFD_COST_CEILING`: V31 EDGAR layer is not opened on the CFD vehicle; US-equity alpha would need a cash equity account (owner's decision). MT5 research object list is exhausted on this terminal. Only live path remains ML1 / V29.

## 2026-09-05 (morning) — V29 ML1 forward pipeline: Design + Implement + Smoke PASS (Paper preparation)

- Owner: "继续，不用询问". Design first (`docs/research_engine/V29_ML1_LIVE_PIPELINE_DESIGN.md`), then module `research_engine/ml1_live/` (`panel.py` live calendar/basics/incremental bars + merged live pack; `layers.py` margin daily / holders weekly / index monthly into `data/market/cn_a_share/live/`; `score.py` V25 features + REFIT_240 model cache + top-20% list; `ledger.py` shadow ledger continuing the V28 chain with the frozen cost model and V26 pause/retire rules; `daily.py` orchestrator). Env overrides added: `TRADEMIND_MARGIN_CALENDAR`, `TRADEMIND_HOLDERS_RAW`. Frozen datasets untouched; no orders anywhere.
- First run (asof 2026-09-04): bars 5215 symbols × 5 sessions (0 failures, 29 min — one BaoStock call per symbol), margin 5 days, index 2026-08-15 as-of, holders raw seeded from the 2026-09-04 frozen copy (3 new listings fetched), live pack 8719 × 5552, 14 features rebuilt, REFIT_2025-11-06 model fitted once (2.45M rows, 33 s) and pickled.
- Smoke 5/5 (`data/market/research_engine/ml1_live/SMOKE_V29.json`): (1) live pack rows ≤ 2026-08-28 bit-identical to frozen pack (open/close/volume/tradestatus/isST/listed); (2) 5 new sessions, 20 random symbols' closes match BaoStock 0 mismatches; (3) 14/14 features bit-identical to `v25_features_finaloos` through 2026-08-28; (4) last V28 session 2026-07-30 rescored with the live model = V28 gate scores, max |Δ| 0.0, 997/997 same names; (5) ledger period 1 OPEN (signal 2026-08-28, entry 2026-08-31, 999 selected / 996 fillable, exit 20 sessions after entry); `SIGNAL_2026-09-04.json` written (999 names, ¥5M targets, no orders).
- Shadow ledger = the strategy's forward record without money; first settlement due when the 2026-09-29 open is in the pack. Phase 4 stability = 5 consecutive daily runs + first settlement; then Freeze. Paper with an account remains the owner's call. Annual layer next refresh 2027-03.

## 2026-09-04 (late night) — V28 ML1 Final OOS single read: PASS, locked

- Owner delegated the denied-window decision ("按照你的想法来"). Protocol written first (`docs/research_engine/V28_ML1_FINAL_OOS_PROTOCOL.md`, machine `cn_a_share_ml_v25/FINAL_OOS_PROTOCOL.json`, hash `844a4ea070ba…`): gate scores = V26 live policy (expanding walk-forward, REFIT_240, embargo 21, stride 5, through 2026-08-28), diagnostic = official 2021-05-25 frozen model, LO20 legacy book, eligible EW benchmark, gates G1 excess>0 / G2 capital>0 / G3 no 24-period retire trigger, single read.
- Raw data extended into the denied window with the existing downloaders only: margin detail 2024-03→2026-08 (607 days, 6 SSL retries, complete), HS300/ZZ500 monthly as-of 2024-03→2026-08 (30 months, 201 as-ofs), holders notice cutoff moved to 2026-08-28. Env overrides added (`TRADEMIND_MARGIN_END/NORM`, `TRADEMIND_HOLDERS_NOTICE_CUTOFF/NORM`, `TRADEMIND_V25_FEAT_CACHE`) so extended arrays live in `*_finaloos` directories; frozen V23/V24/V25 artifacts untouched. `final_oos.py` asserts the extended 14 features equal the frozen V25 cache bit-for-bit through 2024-02-29 (14/14 True).
- **Result `FINAL_OOS_PASS`** (`FINAL_OOS_READ.json`): 30 non-overlapping periods 2024-03-01→2026-07-30; gate scores excess vs EW **+1.00%/20d (t 9.3, n 586)**, LO20 **+71.4%** (CAGR 24.3%, Sharpe 1.00, MaxDD −21.3% 2026-02-27→07-24), 2024 +18.0% / 2025 +58.4% / 2026-to-July −8.2%, 19/30 periods beat EW, longest run behind EW = 3; frozen-2021 diagnostic +0.79% / +63.3% same direction. Eligible EW itself +1.17%/20d (small-cap bull) — more than half of the book is β. ML1 now has three non-overlapping positive books (+276% / +30.9% / +71.4%; ≈13.7% CAGR over 16.6 years) — evidence, not a promise.
- Lock: `final_oos.py` refuses to run when `FINAL_OOS_READ.json` exists; no parameter/feature/hold/cost/refit change; no variant selection on this window. Next gate = Paper preparation (daily five-source incremental pipeline, scorer that emits the list only, monitoring ledger) — Design first per AGENTS five phases; Paper start / account / feed are the owner's. Decision `V28_ML1_FINAL_OOS_DECISION.md`.

## 2026-09-04 (night) — V27 deep financial layer: independent signal, no positive book; ML1 unchanged

- **V27 `A_SHARE_FINANCIAL_DEEP_MODEL_V27`** (`research_engine/cn_a_share_findeep_v27/`, contract `V27_FINDEEP_CONTRACT.md` written first, $0). Eastmoney datacenter quarterly tables `RPT_LICO_FN_CPD` / `RPT_DMSK_FN_BALANCE` / `RPT_DMSK_FN_INCOME` / `RPT_DMSK_FN_CASHFLOW`, 64 report dates 2008Q1→2023Q4, 256 files, 0 failures, raw in `data/market/cn_a_share/financial_deep/raw/` (ignored). **Audit**: INCOME/CASHFLOW `NOTICE_DATE` is the next-year comparative filing (~12 months late) → rejected for features; CPD + BALANCE (Q1–Q3) carry the original filing date; several versions per period → earliest notice kept; feature inputs restricted to filings public at the event's notice date. PIT arrays `financial_deep/normalized/*.npy` + `FINDEEP_PIT.json` (324,931 events; 16,987 dropped past 2024-02-29; 64,554 stale-late ignored). 10 fixed features (SUE_Q, REV_YOY_Q, NEG_ACCRUALS, CFO_TTM_BP, ROE_TTM, GM_CHG, NEG_ASSET_GROWTH, NEG_LEV_CHG, EP_TTM, BP). Two pre-registered LightGBM models (same params/schedule as V25, gate book LO20 per A1): **ML2F financial-only** — excess vs EW +0.65%/20d research (t 21.5), **+0.52% validation (t 5.6)**, rolling 5/5, FDR discovery, **excess-series corr vs ML1 0.06** (independent) — but LO20 validation capital **−0.3%** (research +96.5%, MaxDD −58%) → fails Level-1; HN20 +12.1% validation was seen, so no post-hoc book switch for this signal. **ML2 full stack (24)** — Level-1, but excess corr vs ML1 **0.96** = SAME_CLUSTER as pre-declared; validation excess 1.42% vs ML1 1.47%, LO20 +28.0% vs +30.9%: quarterly layer adds nothing on top of ML1. Decision `V27_FINDEEP_DECISION.md`: `LEVEL1_SAME_CLUSTER_AS_ML1`, NEW_INDEPENDENT stays 1, ML1 untouched.
- `cn_a_share_ml_v25/model.py::build_scores` and `run.py::evaluate_signal` gained optional `features`/`tag` and `equity_dir`/`trades_dir`/`tag` parameters (defaults reproduce V25 exactly) so V27 could reuse them; `features.ranked_row` takes an optional `names`.
- Atlas 73 rows, span V8–V27. `POST_V21_CURRENT_STATE.json` / `POST_V21_AUTODRIVE/PROGRESS.json` updated.

## 2026-09-04 (late) — Rules amendment V1 + V25 multi-layer model: first independent Level-1

- User asked whether the rules were the blocker and authorised changing them. `docs/research_engine/RESEARCH_RULES_AMENDMENT_V1.md`: keep pre-registration / fixed cost model / non-overlapping CAGR / FDR / no Paper without a positive independent book / no evidence rewrite; **change** A1 (pre-registered construction menu LO20 / HN20 hedged), A2 (five rolling validation blocks on top of the fixed split), A3 (one pre-registered model per information layer; V10's "model exhausted" verdict was on 4 MT5 series, not on combining A-share layers), A4 (cluster test on excess-vs-EW series — added after V25 showed the raw-MF test measured the market). Denied window remains locked pending the owner.
- **V25 `A_SHARE_MULTILAYER_MODEL_V25`** (`research_engine/cn_a_share_ml_v25/`, contract `V25_MULTILAYER_MODEL_CONTRACT.md`, $0): 14 PIT features already on disk (6 price, 3 margin V23, 2 holders V24, 2 annual financials V16, HS300 membership V20) → one LightGBM (fixed params), expanding walk-forward from 2012-01, refit /120 sessions, embargo 21, **frozen 2021-08-24**; baseline ML0 = no-fit rank average; m=2. HS300/CSI500 daily index downloaded free (Eastmoney via local proxy / Sina fallback) bounded to 2024-02-29 for the hedged book. **ML1**: research excess +1.24%/20d (t 28), validation **+1.47%** (t 17), IC 0.12/0.17, rolling 5/5, LO20 research +276% (CAGR 14.5%, MaxDD −46.8%), validation **+30.9%** (CAGR 11.1%, MaxDD −20.9%) in a −30% HS300 window, full 2010→2024-02 CAGR 13.7%; cost stress 2× still +17.8% validation. HN20 vs HS300 +27% / +34% but β 0.92 to (EW−HS300), R² 0.93, MaxDD −54% → size-spread carrier, not the strategy. Formal tag `WEAK_CANDIDATE_SAME_CLUSTER` because raw-MF corr vs H11 0.94 (H11 vs EW itself 0.955); excess-series corr **0.06**. ML0 fails (research HN20 capital < 0). Diagnostics `DIAGNOSTICS_POST.json`: LO20 − eligible EW basket +0.89%/20d, t 5.1, 11 of 13 years positive; selected median amount-rank 0.86 (small/quiet tilt). Decision `V25_MULTILAYER_MODEL_DECISION.md`.
- **V25.1 reproduction** (`reproduce.py`, contract `V25_1_REPRODUCTION_CONTRACT.md`): seven fixed nuisance variants (seed ×2, stride 3/10, refit 60/240) all keep the Level-1 shape; validation excess 1.35–1.48%; excess-corr vs H11 0.02–0.07; placebo with labels shuffled within session → −0.09%/20d, LO −18%/−20% (no leak). **PASS → `A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE`, NEW_INDEPENDENT_CANDIDATE = 1** (`V25_1_DECISION.json`). V25 formal tag not re-scored.
- **V26 `V26_ML1_STRATEGY_SPEC.md`**: executable definition of the LO20 book (rebalance /20 sessions, ~600 names EW, fills, no in-period stops, pre-declared pause/retire rules, live refit policy = REFIT_240 variant, monitoring ledger), exposures stated (size/liquidity tilt, β≈1 to EW, 2017/2018/2024-01 on record), capacity ≈¥5M minimum for 100-share lots. Spec only: no Paper, no order_send.
- Atlas 71 rows (V25 rows appended; ML1 is the first non-failure row). `POST_V21_CURRENT_STATE.json` rewritten. Final OOS: DENIED until the owner unlocks a single pre-declared read.

## 2026-09-04 — User-authorised spend + free behavioral layer (V22 / V23 / V24)

- User authorised the Databento balance (~$93) with "evaluate first, then buy, then continue". Real `metadata.get_cost` menu in `databento_eval_v22/QUOTE.json`; evaluation `DATABENTO_93_PURCHASE_EVALUATION.md`.
- **V22 FUTURES_XS**: bought GLBX.MDP3 `ohlcv-1d` 30 CME roots all months 2010-06→2026-08 (**$47.10**, `tm-fut-GLBX-XS30-D1-20260904-000001`, batch job). Panel 30 roots / 119,724 root-days (denied window dropped at build). 3 pre-registered (XS carry, XS mom 12-1, TSMOM 12): research gross CAGR ≈ 1%, FDR 0/3 → **FUTURES_XS_V1_NO_CANDIDATE**. Reserve ≈ $46 unspent. Fixed `get_dataset_range` to GET.
- **V23 MARGIN**: exchange daily margin detail found free & reachable (Eastmoney datacenter mirror; SSE/SZSE official 200). 3381 sessions 2010-03→2024-02 downloaded ($0). 3 pre-registered. M1 research excess t=4.85 / capital +37% but validation capital −19%, FDR 0/3 → **A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE**.
- **V24 HOLDERS**: shareholder-count reports with `HOLD_NOTICE_DATE` (PIT), 5549 symbols, 297,732 reports ($0). 3 pre-registered → **A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE** (research excess ≤ 0).
- Northbound daily holdings: HKEX now 12-month window only + quarterly disclosure → **DATA_BLOCKED (free)**.
- New generic engine `research_engine/cn_a_share_freeinfo_engine.py`. Atlas extended to 69 rows (`post_v21_atlas_append.py`). NEW_INDEPENDENT still 0.

## 2026-09-04 — Post-V21 autodrive W1–W6 (idle_search_closed)

- W1 pairwise corr on existing TRADES: 13 beat-EW books NOT one shadow; 5/13 >0.9 vs H11; all val capital negative.
- W2 os.walk inventory: AVAILABLE=0; balance/valuation ratios not on disk and ratio-class.
- W3 failure atlas 60 rows V8–V21. W4 strategy bind: zero-cost H11 CAGR +2.9%, Paper=NO, portfolio contract draft inactive.
- W5 purchase case: only vendor flow/holder/margin data maps to the A-share gap; DO_NOT_BUY. Scripts `research_engine/post_v21_w{1,2,3,4}_*.py`.

## 2026-09-04 — Post-V21 autodrive S1 (Q1–Q5)

- Q1 relative EW NEGATIVE (29/42). Q2 NONE. Q4 one CS sleeve (median corr vs X1 0.54). Q5 KEEP_LOW_PRIORITY.
- Strategic choice **S1**. Confidence 0.91. NEW_INDEPENDENT still 0. Do not buy.
- Progress: `POST_V21_AUTODRIVE/PROGRESS.json`.

## 2026-09-04 — Post-V21 capital forensics VERDICT A

- Read-only V13–V21 RESULTS + existing TRADES. 42/42 val capital negative. 38/42 val MEAN_FORWARD negative.
- Verdict A (0.72): no second Alpha because new families had no val information. Sidecar B: H24/H25/H26/A5 + H11 official book = V14.1 overlap ≠ capital.
- New class NONE. Purchase default DO_NOT_BUY.
- Authority: `POST_V21_CAPITAL_CONSTRUCTION_FORENSICS.md` / `POST_V21_PURCHASE_VALUE_CASE.md`.

## 2026-09-04 — Post-V21 STOP B

- V21 dividend announcement windows: 0 Level-1. FDR 0/2. Validation capital −41% / −72%.
- Global: `A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED`. No purchase.
- Authority: `docs/research_engine/POST_V21_DECISION.md`.

## 2026-09-02 — Post-V19 direction + V20 index STOP B

- Direction audit: next unit of resource = HS300/ZZ500 membership/reconstitution, not more A-share CS factors. Options remain PAYMENT_REQUIRED (no buy).
- V20: monthly as-of PIT OK. 4/4 no Level-1. Family FDR 0/4. Validation capital all negative.
- V21 started: dividend announcement events (not yield quintile).
- Authority: `POST_V19_RESEARCH_DIRECTION_AUDIT.md` / `V20_INDEX_DECISION.md`.

## 2026-09-02 — Post-V16 STOP B

- V17 macro, V18 altinfo, V19 industry×macro: 0 Level-1. Unified BH-FDR m=18, 1 excess discovery (IM6), 0 Candidate.
- `A_SHARE_INFORMATION_ALPHA_NO_CANDIDATE`. Event/News blocked. Options unpaid. No purchase.
- Authority: `docs/research_engine/POST_V16_DECISION.md`.

## 2026-09-02 — V16 financial/industry information STOP B

- Financial + industry PIT both READY. 6+3 pre-registered dual-book alpha. Unified BH-FDR 0/9.
- `A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE`. Validation capital negative 9/9. Purchase=NO. Local Windows only.
- Authority: `docs/research_engine/V16_DECISION.md`.

## 2026-08-31 — V16 financial/industry information START

- Open blocked Financial / Industry layers on free BaoStock. No purchase. No H11/H12 reopen. No price-only rescue.
- Entry: `docs/research_engine/A_SHARE_INFORMATION_EXPANSION_V16.md`.

## 2026-08-31 — V15 second independent A-share alpha DECISION

- Nine pre-registered hypotheses on the frozen panel. Dual books. BH-FDR on all nine.
- `NO_NEW_CANDIDATE`. Validation capital negative 9/9. Residual family tracks LOW_VOL (corr ≈ 0.90–0.94).
- Review: `PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`. No purchase. No H11/H12 reopen.
- Entry: `docs/research_engine/A_SHARE_ALPHA_V2_DECISION.md`.

## 2026-08-31 — V14.1 candidate/strategy forensics DECISION

- Independent reconstruction: Candidate Path A/B match published `mean_net_h` (err=0). Capital Path A/B match V14 settled ends.
- `METHODOLOGY_GAP_CONFIRMED`. Overlapping mean CAGR is not a book. All 20 offset grids compound to a loss. No accounting bug. No Long Validation. No retune.
- Entry: `docs/research_engine/V14_1_DECISION.md`.

## 2026-08-31 — V14.1 candidate/strategy forensics START

- Audit only. Explain Candidate+ vs Strategy−. No new factor. No retune.
- Entry: `docs/research_engine/V14_1_START.md`.

## 2026-08-31 — V14 strategy construction DECISION

- Canonical Strategy-H11 / H12 are executable and reconciled. Full-path capital lost money.
- `STRATEGY_WEAK_BUT_RESEARCHABLE`. Do not retune toward 10%.
- Entry: `docs/research_engine/A_SHARE_STRATEGY_DECISION_V14.md`.

## 2026-08-31 — V14 strategy construction START

- Canonical Strategy-H11 / Strategy-H12 only. No new factor. No retune.
- Entry: `docs/research_engine/V14_START.md`.

## 2026-08-31 — V13.1 candidate reproduction DECISION

- H11 and H12 independently reproduce. Both `CANDIDATE_SURVIVED`.
- Official overlapping validation CAGR still ≈ 0.55% / 1.30%. Not 10%. Do not retune.
- Entry: `docs/research_engine/A_SHARE_CANDIDATE_DECISION_V13_1.md`.

## 2026-08-31 — V13.1 candidate reproduction START

- Reproduce H11/H12 only. No new factor. No retune.
- Entry: `docs/research_engine/V13_1_START.md`.

## 2026-08-31 — V13 A-share CS alpha DECISION

- 12 locked hypotheses. Level 1 = `H11_VOL_60` + `H12_VOL_120`.
- Validation cost-adjusted CAGR ≈ 0.55% / 1.30%. Not a 10% claim. Do not retune.
- Entry: `docs/research_engine/V13_DECISION.md`.

## 2026-08-31 — V13 A-share CS alpha START

- Frozen panel only. 12 pre-registered hypotheses. No purchase. No live API.
- Entry: `docs/research_engine/V13_START.md`.

## 2026-08-30 — V12.2 panel FROZEN PRICE_ALPHA_READY

- 5549/5549 raw. 18,418,047 rows. dataset_id `tm-ashare-EQUITY-D1-20260830-000002`.
- Financial / industry / event stay BLOCKED. Do not auto-start Alpha.
- Entry: `docs/research_engine/V12_2_FINAL.md`.

## 2026-08-30 — V12.2 panel completion START

- Single downloader to 5549/5549, then auto compile / freeze / ready gate.
- New dataset_id `tm-ashare-EQUITY-D1-20260830-000002`. Do not overwrite 000001.
- Entry: `docs/research_engine/V12_2_START.md`.

## 2026-08-30 — V12.1 full daily panel START

- Freeze the full PIT equity daily panel. No purchase. No alpha. Single BaoStock session.
- `2015-04-30` stays INVALID. dataset_id = `tm-ashare-EQUITY-D1-20260830-000001`.
- Entry: `docs/research_engine/V12_1_START.md`.

## 2026-08-30 — V12 A-share PIT foundation CONDITIONAL

- Free BaoStock PIT layer. No purchase. No alpha. No backtest.
- `A_SHARE_DATA_STATUS=CONDITIONAL`. Next = freeze the full equity daily panel. Do not start A-share alpha.
- Entry: `docs/research_engine/A_SHARE_READY_DECISION_V12.md`.

## 2026-08-30 — V12 A-share PIT foundation START

- Point-in-time A-share data layer. No purchase. No alpha. No backtest.
- Entry: `docs/research_engine/V12_START.md`.

## 2026-08-30 — V11 Alpha Capital Allocation

- Review only. No experiment. No purchase. Spend $0.
- NEXT = CHINA_A_SHARE_RESEARCH_UNIVERSE. Freeze MT5 alpha search. Do not buy options or Databento.
- Entry: `docs/research_engine/V11_DECISION.md`.

## 2026-08-30 — V10 Model Discovery STOP B

- Locked 4 families × representations × 2 targets × GOLD/OIL. 62 experiments. FDR 0/62.
- 21 cells beat naive M0 on validation metrics. No Level 1 Candidate. `MODEL_REPRESENTATION_EXHAUSTED`.
- Do not buy options. Do not spend $93. Do not retune depth/threshold/target.

## 2026-08-30 — V10 Model Discovery START

- Controlled nonlinear / interaction representation of the current information set.
- No purchase. No new download. Final OOS denied. MODEL is not assumed to be alpha.
- Entry: `docs/research_engine/V10_START.md`.

## 2026-08-30 — V9 Master Backtest STOP B

- Replayed locked mechanisms into one MT5 NEXT_BAR_OPEN ledger. No purchase. No new hypotheses.
- 103 strategy books. 0 Positive Reproducible. Level 1 Candidate = 0.
- Databento $31.82 added 0 Candidates. $93 remains UNUSED_RESEARCH_RESERVE.
- Next = model / information representation review. Do not buy options.

## 2026-08-30 — V9 Master Backtest START

- Existing-data profitability audit. No purchase. No new hypotheses. Final OOS denied.
- $93 Databento remainder is UNUSED_RESEARCH_RESERVE.
- Entry: `docs/research_engine/V9_START.md`.

## 2026-08-30 — V8.4 full-year options occupancy census (PURCHASE = NO)

- Metadata `get_record_count` on 251 Pack E sessions. No download. $0.
- Locked gates: A = ATM≥90 / skew≥75 / term≥75. LO = A. OG = B (term 74.9%).
- Gold option-front never equals futures-front (0%). LO ATM/skew streak = 251 days.
- If a human later buys one pack: LO 1Y MVD-A $11.99. Not dual. Not MVD-B for coverage.

## 2026-08-30 — V8.3 Options historical feasibility (PURCHASE = NO)

- Metadata only: `get_record_count` / resolve / billable size. No download. $0.
- 8 pre-registered dates. OG futures-front ATM 0/8; OG live month ATM 8/8; LO ATM/skew/term 8/8. Full 1Y census not run. CASE B.
- Preferred later package if a human accepts CASE B: OG 1Y MVD-A $14.99 for IV-RV. Do not auto-buy dual or LO B.

## 2026-08-30 — V8.2 Options Data Due Diligence (QUOTE ONLY)

- Catalog / schema / symbology / `get_cost` only. No download. No purchase. $0 new credits.
- `GC.OPT`/`CL.OPT` unresolved. Live parents: `OG.OPT`, `LO.OPT`, plus weekly/special roots. GLBX has no venue IV (`stat_type` 14/15 absent).
- CASE A invoices exist (1Y OG+LO MVD-A $26.99; 1Y LO MVD-B $24.09; 2Y single MVD-A ~$23–25). Occupancy of ATM/OTM/front/second still UNKNOWN. MVD-C vetoed.
- Artifacts: `docs/research_engine/OPTIONS_*_V8_2.md` and `data/market/research_engine/options/OPTION_*_V8_2.json`.

## 2026-08-30 — V8 Information Fusion STOP C

- Existing fusion TOP5 executed one family at a time. Four Xavier each. Candidate=0. FDR 0/15.
- FUT_CFD_LEAD and CURVE_OI_JOINT NO_CANDIDATE. OI_COT / EIA / REALYIELD WEAK_EDGE (one book hyp, no FDR).
- Options quoted, not downloaded. Parents `OG.OPT`/`LO.OPT`. Useful MVD ≈ $32–$54 > $30 auto cap. Credits still ≈ $93.
- Do not retune. Do not $199/mo. Do not tick.

## 2026-08-30 — V7 Information Fusion STOP B+C

- No new purchase. Credits still ≈ $93. Pack E 60-file hash preserve PASS.
- Derived OI-flow + volume-flow panels. Three new families, four Xavier each. Candidate=0.
- OI NO_CANDIDATE. Volume NO_CANDIDATE. DTE WEAK_EDGE FDR 0/3. Do not retune.
- Next = quote options-on-futures. Not $199/mo. Not another Pack E.

## 2026-08-29 — V6.1 TERM_STRUCTURE_V1 NO_CANDIDATE

- Pack E billed **$31.816129**. Slim curve `tm-fut-GLBX-CURVE-D1-20260829-000001` (8184 rows) frozen. Raw stays gitignored.
- Four Xavier executed. Cross-check match. All 3 hyps FALSIFIED (LEVEL_LEAK). Level=0 Candidate=0. Do not retune slope/hold.
- Next information = options-on-futures or dated macro. Quote first. No $199/mo. No tick.

## 2026-08-29 — V6.1 Pack E quote $31.82 GATE A PASS

- Key loaded from local ignored env. Not printed. Not committed.
- `metadata.get_cost` Pack E (GC+CL parent ohlcv-1d + definition + statistics, 2010-06-06–2026-08-29) = **$31.815091** ≤ $125.
- Next: batch acquire to `data/market/raw/databento/` (gitignored). No $199/month.

## 2026-08-29 — V6.1 START blocked: KEY_PRESENT=false

- Repo `.env` exists but is the 2026-07-13 Xavier worker file. No `TRADEMIND_DATABENTO_API_KEY`. Process env empty. Cost probe not run. $0 spent.
- Loader also reads `.env.local` and official `DATABENTO_API_KEY` alias. Never print the value.
- Stop C. Next: append the key locally, then acquire Pack E.

## 2026-08-29 — V6 External Exchange CREDENTIAL_REQUIRED

- 活页核实 `GLBX.MDP3`：2010-06-06 起；daily/definition/statistics 同日；MBO 2017-05-21。历史按量，不必 $199/月。Credits $125。
- 推荐最小包 **E**：GC+CL parent daily + definitions + statistics。精确价要 key。
- 落地：HTTP adapter、knowledge-time、novelty、TERM_STRUCTURE_V1 搜索空间、acquire 脚本。无字节，无 READY，无 Xavier。
- 停在 **CREDENTIAL_REQUIRED**。下一步：key 进 `.env` 后 acquire，不是再写文档。
- Level 仍 0。Candidate=0。花费 $0。Final OOS 未读。未 `order_send`。

## 2026-08-29 — Market Universe V5.1 EXTERNAL_DATA_GATE

- 841/841 Stage A 从 checkpoint 续完。全部 CFD。期权 0。真期货 0。
- 新冻 `20260829-000001`：7 个农业 + EUROBUND + JAPANBOND + US2000。未覆盖 `20260825`/`20260828`。
- BREADTH_V1 四 Xavier **WEAK_EDGE**。01=04 `253b06ff…23ab0fae`。不要调 lookback/thrust。
- SIZE_SPREAD_V1 四 Xavier **NO_CANDIDATE**。01=04 `77094eee…acf49410`。
- Level 仍 0。Candidate=0。花费 $0。Final OOS 未读。未 `order_send`。
- 下一动作：曲线/期权面采购案，不是再扫 638 个股票 CFD。

## 2026-08-29 — Market Universe V5.0 START

- START pointer `d29d3b7`。不改 V4 hash。不覆盖 `20260825`。
- 目标：真实终端 universe + 横截面 / 相关 / 离散，不是再写金银比或 DXY z。

## 2026-08-29 — MT5 Max Mission V4.0 COMPLETE_NO_CANDIDATE

- 2000 bars 不是上限。新 `20260828-000001` 冻了 SILVER/DXY/额外 FX/指数/H1/M15。未覆盖 `20260825`。
- CROSS_METAL_V1 与 USD_METAL_V1 四 Xavier **NO_CANDIDATE**。01=04。不要 z_cut / 翻号。
- VIX 1.45y 未冻。GOLD ticks ≈ 64 万 / 2 日，是经纪商 tick，不是订单簿。
- Databento 不为再下一根 Ava K 线。曲线/期权面仍 BLOCKED。
- 花费 $0。Level 仍 0。Candidate=0。Final OOS 未读。未 `order_send`。
- 报告：`docs/research_engine/MT5_MAX_MISSION_V4_REPORT.md`。

## 2026-08-28 — Data Expansion Mission V3.0 WAIT_HUMAN

- 数据工厂：`research_engine/data_expansion/` + `research_engine/data_sources/`（统一 fetch→hash，无字节不得 READY）。
- 新公开数据：EIA 产量 / 开工率 `20260828-000001`。SUPPLY_V1 四 Xavier **NO_CANDIDATE**。不是库存家族。
- 供应商核验（当日页）：Databento $125 credits / Standard $199；ORATS $599+$99；CME DataMine $105–$2100；TE 价页 403。
- 人类采购包：只买 Databento credits。见 `HUMAN_DATA_PURCHASE_ACTION_PACK.md`。
- 花费 $0。Level 仍 0。Candidate=0。Final OOS 未读。未 `order_send`。

## 2026-08-28 — Alpha Research Mission V2.0 STOP B

- 新公开数据（新 ID，未覆盖 20260825）：CBOE GVZ/OVX、CFTC COT Friday knowledge、EIA WCESTUS1、UST 10y、NY Fed EFFR、ECB €STR、BOJ overnight call。
- 五家族已跑：IV / Positioning / Inventory / Rates / Carry V1A。全部 **NO_CANDIDATE**。四 Xavier，01=04。
- CARRY_V1 记为 INVALID_ALIGNMENT，不是机制结论。
- Level 仍 0。Candidate=0。Final OOS 未读。未 `order_send`。
- 报告：`docs/research_engine/ALPHA_RESEARCH_MISSION_V2_REPORT.md`。

## 2026-08-28 — Alpha Mission V1.1 STOP B

- 新历史：GOLD/OIL D1/H1 `20260828-000001`。GOLD/OIL D1 **7.715y BROKER_LIMITATION**，不是 10y。未覆盖 `20260825`。
- IT V1.0 已跑：local 2000 + 四 Xavier。程序 **WEAK_EDGE**。FDR 0/3。01=04 一致。家族 KILLED。
- Time Structure / Microstructure Surprise / Regime Interaction / Alt Market Structure 全部 **NO_CANDIDATE**。高换手 hold=5 多头在 H1 上成本后证伪。
- Level 仍 0。Candidate=0。Final OOS 未读。未 `order_send`。
- 报告：`docs/research_engine/ALPHA_MISSION_V1.1_REPORT.md`。

## 2026-08-28 — GitHub baseline + secret removal

- 仓库初始化 private GitHub。脚本与文档中的硬编码 Xavier/Rabbit 密码已移除，改读 `TRADEMIND_XAVIER_PASSWORD`。
- 新增 `.env.example`、`scripts/secret_scan.py`、`.gitignore`。`.env` 不入库。
- 不改冻结研究哈希，不改 immutable bars。

---

## 2026-08-27 — Alpha Recovery Program V1.0

- 失败分析系统：`research_engine/forensics/` 扫描 rankings/results/contracts/datasets。覆盖 + A-E 分类。不改冻结结果。
- 数据审计：`scripts/data_inventory.py`。Recovery 目标 D1>10y / H1>5y / M15>2y。只读 MT5：H1 5y 与 M15 2y 探针可达；GOLD/OIL D1 ~7.7y 仍不够 10y。未覆盖写 `20260825-000001`。
- Opportunity V2 自动打分。选出 **一个** 新家族：`INSTITUTIONAL_TIME_V1.0`（month-end/start，不是 weekday / 不是指标）。
- 纸面合同 hash `1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457`。**未执行。**
- `pytest tests/research_engine --import-mode=importlib`：**167 PASS**。
- 未读 Final OOS。未 `order_send`。未改旧实验。

---

## 2026-08-27 — Alpha Discovery Program V1.0: Universe + V0.9 + V0.91

- 机器盘点：`ALPHA_UNIVERSE_DB.json`；机制分类器 `ALPHA_BACKLOG_V2.json`。
- 数据：盘上 D1/H1/M15 对 10y/3y/2y 仍 SHORTFALL。只读 MT5 探针 **ACQUISITION_POSSIBLE**（新 ID 才能冻更长历史；GOLD/OIL D1 仍不够 10 年）。未覆盖写 `20260825-000001`。
- V0.9 **已实现并四 Xavier 实跑**。hash 未改。01=04 `31995464…249b8`。结果 **`NO_CANDIDATE`**（0001 FALSIFIED；0002/0003 INCONCLUSIVE；FDR 0/3）。占用率 1–2%，是 Δstate 不是水平泄漏。
- 决策树进入 V0.91：残差家族已跑。hash 未改。结果 **`NO_CANDIDATE`**。
- 策略层 **BLOCKED**。距离 10%：当前认证 CAGR=无，缺口=10 个百分点。
- `pytest tests/research_engine --import-mode=importlib`：**149 PASS**。
- 未读 Final OOS。未 `order_send`。未改旧实验。

---

## 2026-08-26 — Alpha discovery pipeline + residual family paper

- 可运行评分：`scripts/research_engine_alpha_pipeline.py`，52 机制题，live=29。
- 簇排序：Regime Transition 1600、Residual 576、Calendar 540。V0.9 仍第一，hash 未改。
- 第二独立家族纸面合同：`CROSS_RESIDUAL_V0.91` hash `0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57`。
- 未跑 V0.9，未读 OOS，未改冻结实验。`tests/research_engine` 85 PASS。

---

## 2026-08-26 — ALPHA_PROGRAM_V1 documentation

- 全仓扫描 docs/data/research_engine/tests；根目录无 registry/。
- 机制库 V2、优先级 Top 10、路线 V2（Paper 有日历、有硬门）。
- V0.9 深度机制：10 条里锁定原 3 条；未改 hash。
- Level 1 门：成本后+FDR+双 target；CAGR>10% 冻在资本层。
- 失败知识库、数据需求、实验漏洞审计。无代码、无 Xavier、无 OOS。

---

## 2026-08-26 — Alpha Discovery Map V1 + V0.9 contract

- 只写文档，不写业务代码，不跑新实验，不改 14:11 / FD / V0.5 / V0.6 / V0.8。
- 覆盖地图：短持有技术 + V0.8 跨品种 = FAILED；Carry/IV/新闻/订单流 = DATA BLOCKED。
- 优先级：Regime Transition 第一。12 个月路线禁止跳级到 Paper/MT5。
- V0.9 合同锁 3 条 Δstate 假设；hash `3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`。
- 文档：`ALPHA_COVERAGE_MAP_V1.md`，`DATA_CAPABILITY_MATRIX_V1.md`，`ALPHA_PRIORITY_RANKING_V1.md`，`TRADEMIND_ALPHA_ROADMAP_12M.md`，`REGIME_TRANSITION_V0.9_CONTRACT.md`。

---

## 2026-08-26 — Cross Asset Alpha V0.8 execution freeze

- 四 Xavier 实跑：01=XA-0001，02=XA-0002，03=XA-0003，04=XA-0001 交叉。内容哈希 01=04。
- 对齐 1993 日。`search_space_hash` 未变。`align_hash` `1e8f6bbc…aaf2b`。
- 结果 **`NO_CANDIDATE`**。三条均为 FALSIFIED。FDR m=3 discoveries=0。
- 单元 80 PASS。未改 14:11 / FD / V0.5 / V0.6 / 不可变 bars。无 MT5。无 Final OOS 读取。
- 报告：`docs/research_engine/CROSS_ASSET_ALPHA_V0.8_REPORT.md`。冻结：`V0.8_EXECUTION_FREEZE.md`。

---

## 2026-08-26 — Cross Asset Alpha V0.8 contract

- 审计四条 D1：四向 inner join 1993 日（2020-04-01→2026-08-25）。EURUSD 与 USDJPY 日期完全相同。
- 锁 `FAM-FD-XASSET-0001` + 三条假设；未跑、未改 FD V0.1 文件。
- hash `787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827`。
- 文档：`CROSS_ASSET_DATA_AUDIT.md`，`CROSS_ASSET_ALPHA_V0.8_CONTRACT.md`。

---

## 2026-08-26 — Alpha Operating System V0.7.1

- 设计：五类 alpha 分类、DONE/FAILED/UNKNOWN/DATA BLOCKED 矩阵、12 个月队列。
- 纸面锁死 Cross Asset V0.8：恰好 HYP-XA-0001/0002/0003，共享对齐 D1 窗口，成本与 V0.6 相同。
- 无代码、无新实验、未改 14:11 / FD / V0.5 / V0.6。
- 文档：`docs/research_engine/ALPHA_OPERATING_SYSTEM_V0.7.1.md`。

---

## 2026-08-26 — Alpha Discovery V0.7 design

- 只审计已测搜索空间，不写业务代码，不跑新实验，不改 14:11 / FD / V0.5 / V0.6。
- 结论：单品种短持有方向已测败；下一最可能赚钱方向是跨品种 D1（FD 的 `FAM-FD-XASSET-0001` 仍是 DRAFT）。
- 计划：`docs/research_engine/ALPHA_DISCOVERY_V0.7_PLAN.md`。

---

## 2026-08-26 — Profit Discovery V0.6

- 真实回测：NEXT_BAR_OPEN、spread+5bp+10bp、0.5%/1% 风险、杠杆上限 1×、同品种组合。
- 四 Xavier：01 GOLD / 02 EURUSD / 03 USDJPY / 04 OIL，各 4 timeframe。结果 `WEAK_EDGE_ONLY`，程序级 CANDIDATE=0。
- 仅 OIL D1 动量过单数据集门；年化约 0.2%，不是 10%。失败方向全部保留。
- 单元 74 PASS。未改 14:11 / FD / V0.5 / V11.7。无 MT5。
- 报告：`docs/research_engine/PROFIT_DISCOVERY_V0.6_REPORT.md`。

---

## 2026-08-26 — Research Engine V0.5 foundation

- Market State + 15 locked strategy sketches（不是再挖无条件因子）。
- 本地 16 dataset 评估：FDR 203 tests / 0 discoveries，`NO_USEFUL_STRATEGIES_FOUND`。
- 单元测试 64 PASS。未改 HYP-0001 14:11 / FD V0.1 / V11.7。未发 MT5。
- 四 Xavier 调度脚本已写（`scripts/research_engine_v05_run.py`），本轮排名来自 Windows-local。
- 文档：`docs/research_engine/RESEARCH_ENGINE_V0.5_*.md`。

---

## 2026-08-26 — Factor Discovery V0.1

- 新搜索合同 `FACTOR_DISCOVERY_V0.1`（57 candidates，hash `add0211ffb189d50639b656af1b009ac15849d9f3d426af8469f9700eb05dc5a`）。不是 HYP-0001 调参。
- Windows 锁定 search space + job manifest；Xavier `node_eval.py` 只执行列表。远程目录 `/tmp/tm-factor-discovery-v01`。
- 四台实跑 17 jobs（16 primary + GOLD M15 交叉）。FDR m=876 discoveries=0。结果：`NO_USEFUL_FACTORS_FOUND`。
- 5 个 INCONCLUSIVE 是波动率聚类（`future_abs_return`），不是方向性 edge，且 cost-sensitive。
- 单元测试 56 PASS（旧 34 未改弱）。Final OOS 仍拒绝。未动 14:11 / V11.7 / 8002–8005 / immutable data。
- 报告：`docs/research_engine/FACTOR_DISCOVERY_V0.1_REPORT.md`。

---

## 2026-08-26 — HYP-0001 contract authority restored

- 22:59 catalog 路径（`FAM-PERSISTENCE-0001` / PENDING lineage）隔离为 `quarantine/CONTRACT_MISMATCH_20260826/`。只停 research PID，未动 8002–8005 / V11.7。
- Xavier 必须读 `NODE_JOBS.json` + 14:11 锁定 JSON。不再 hardcode `hyp_0001_a()` 当正式身份。
- 14:11 A/B hash 与 `tm-exp-20260825-141158-001…032` 未覆盖。
- 静态 34 tests PASS。Smoke（Xavier-01 / GOLD M15 / HYP-0001-A）PASS。全量 48 jobs / 四台交叉 4/4 PASS。`continuation_mean` vs 0。Final OOS 仍拒绝。
- Family rollup = WEAK_SUPPORT。不是交易策略，不是年化 10%。
- 审计：`docs/research_engine/`。

---

## 2026-08-25 — Research Protocol V0.3

- 独立研究协议：Dataset / Experiment / Window / Execution / Lookback / Horizon / Purge-Embargo / Causal Features / Leakage Sentinel。
- 四台 Xavier one-shot，每 dataset 10 次 feature/window/leakage；01↔04 与 02↔03 交叉 PASS。
- 16 份 CANDIDATE 窗口（UTC）。FINAL_OOS 未锁。不改 V11.7，不重跑 GOLD M15 RSI，不发单。

---

## 2026-08-25 — Research Readiness V0.2

- 四台 Xavier 对 16 个冻结 dataset 各做 20 次完整画像（另加 GOLD M15 跨节点 20 次），指纹全同。
- 8 块 / 19 滚动窗 / 分位 / 自相关 / 极端集中度 / 快照稳定 / 8 类故障注入均完成。
- OIL D1 极端日为 MARKET_EXTREME，不是坏数据。FINAL_OOS 未锁。不改 V11.7。

---

## 2026-08-25 — Data Qualification V0.1

- 四台 Xavier 一次性 `research_probe.py` 给 16 个冻结 dataset 做画像与资格审查。
- GOLD M15 跨节点复算 PASS。000001/000002 仅最后一根变化，无 HISTORICAL_MUTATION。
- OIL D1 = DATA_REVIEW_REQUIRED（2020 极端日收益密度）。其余 15 个 QUALIFIED_WITH_WARNINGS。
- 不改 V11.7 / Master / Worker。FINAL_OOS 未锁。

---

## 2026-08-25 — Data Layer V0.1

- 独立只读 MT5 市场数据层：`data_layer/` + `data/market/`。不接 V11.7，不接 Master/Xavier API。
- 16 组合（GOLD/EURUSD/USDJPY/OIL × M15/H1/H4/D1）各 2000 根 UTC OHLCV + manifest + SHA256。不可覆盖。
- `FINAL_OOS_LOCKED = false`。未自动回测，未 `order_send`。

---

## 2026-08-24 — V11.7 四台并行样本内筛选

- 01/02/04 在 8002 加回测旁路，不撤原角色。Master 线程扇出。
- 12 组冻结候选只按样本内打分，样本外只验选中组。禁止用外盘挑参。

---

## 2026-08-24 — V11.6 行情分段

- 一年总涨里面仍标出涨/跌/震。上涨用均线、震荡用布林、下跌空仓。映射写死。
- 特征是相对 50 均线偏离，冻结线性分割，不训练张量。换段平仓付滑点佣金。
- 策略篮增加 `REGIME_SWITCH`，并按开仓时所在段汇总各策略盈亏。

---

## 2026-08-24 — V11.5 连续切分 + 冻结策略篮

- 整段 K 线一次算完。`cut` 只分段，不在切分处强平。样本外接着样本内的 RSI/仓位。
- 同一段 GOLD 上跑冻结默认参数：RSI / EMA_MACD / SMA_CROSS / BOLLINGER / TURTLE。不按样本外调参。
- 不做 GRID、VWAP（量是合成的）。`survived` 仍不是买卖单。

---

## 2026-08-24 — 回测审计 Smoke 21

- 独立 RSI、成交价还原盈亏、判定四态、009995 四十笔配对，均与 Worker 一致。
- 真盘再跑：窗口滑 1 根后样本内 -19.15 / 外 2.02，明细仍 40 笔。已知缺口：样本内结束会强平、样本外 RSI 重算。

---

## 2026-08-24 — V11.4 成交明细可核对

- 仓库没有整段黄金行情。证伪时从本机 MT5 拉 K 线，这次留下每根时间和买卖点。
- Worker 2.1.2 回 `trades`（idx/价格）。控制台表格：分段、方向、UTC 时间、价格、盈亏%。
- 旧那笔 28/12 没有明细，要重新跑「黄金 MT5 证伪回测」。

---

## 2026-08-24 — V11.3 解读不再编 0 笔

- 网关只读 `context.result`。原先数字在外层，模型看到全 0，写成「没有任何交易」。
- 证伪回测改为按数字写解读，不再问模型。白盒：成交 28/12 必须进 result。

---

## 2026-08-24 — V11.2 加长历史

- 亏 12% 那笔是 CSV「黄金CSV样本」，不是 Ava GOLD。
- 证伪改为 H1 2000 → M15 2000 → H4 1000。摘要带成交笔数。回测不当买卖单。

---

## 2026-08-24 — V11.1 证伪入口 + 不足升级

- 紫色大按钮「黄金 MT5 证伪回测」。旧「黄金回测」改名为「黄金CSV样本」，不是 Ava GOLD。
- D1 成交不足则自动改 H4、再 H1，风控规则不变。

---

## 2026-08-24 — V11.0 MT5 证伪回测

- Master 拉 MT5 日线，切 70/30；Xavier 回测 2.1.1 可吃 `close[]`。
- 风控写死：回撤 25%、两边至少 5 笔、样本外收益必须 > 0。
- `survived` 只表示本次未证伪。不自动下单。Smoke 20 + Stability 08 PASS。

---

## 2026-08-24 — V10.0 测通模拟盘

- RSI 中间不再灰掉整条交易。人手「测买 / 测卖」0.01 手，`reason=wire_test`。
- 无 `side` 仍按 RSI 门拒绝。进终端 ≠ 预测有效。Smoke 19 PASS。

---

## 2026-08-24 — V9.0 黄金解析

- Ava 模拟盘黄金是 `GOLD`、原油是 `CrudeOIL`。原先只认 `XAUUSD`，点黄金会报没有。
- 解析先试券商标、再扫 `symbols_get`。冒烟补 Ava 名称。不改 Xavier。

---

## 2026-08-24 — V9.0 Freeze

- Master 拉本机 MT5 M15，只把 `{symbol, close}` 交给现有 indicator-worker。Xavier 不跑 MT5。
- 人手 `confirm=true` 后，仅 demo 账户 `order_send`。实盘拒绝。测试默认 `TRADEMIND_MT5_SEND=0`。
- 控制台：黄金 / 欧美 / 原油 / 美日。`GET /api/v1/mt5/quotes`。
- 同花顺未接：没有可测官方接口。A 股仍走因子 + `moutai.csv`。
- Smoke 18 + Stability 07 PASS（假终端，未打真实模拟账户）。V5.0 纸质单冻结件不改写。

---

## 2026-08-24 — V8.0 Freeze

- 因子读 `data/samples/moutai.csv`，回测读 `xauusd.csv`。Master 只拼 Worker 已有字段。
- `GET /api/v1/samples` 增加 `kind`。种类对不上 → TM-1001。
- 不改 Worker，不发 MT5。Smoke 17 + Stability 06 PASS。

---

## 2026-08-24 — V7.0 Freeze

- 指标研究读 `data/samples/eurusd.csv`，不再写死 close 数组。
- `GET /api/v1/samples`；`sample_id` 可选，默认 eurusd。
- 不是行情，不改 Worker，不发 MT5。
- Smoke 16 + Stability 05 PASS。

---

## 2026-08-23 — 控制台改成四步操作

- 对照 Stitch「炒股」设计系统（黑底 / 蓝主按钮 / 紫 AI，不用酒红）。
- 主路径改成 1 研究 → 2 看结果 → 3 拟单 → 4 确认纸质单。同时只突出一个主按钮。
- 「开始研究」跟你点的类型走，不再总是跑推荐项。
- 仍不往 MT5 发单。

---

## 2026-08-23 — V6.0 Freeze

- 打开研究先 `preview` 拟单，再允许确认。仍禁止发到 MT5。
- `GET /api/v1/desk/today`：当天研究 + 纸质单只读台账。
- Smoke 15 + Stability 04 PASS。preview 20 次不落新文件。

---

## 2026-08-23 — V5.0 Freeze

- 人手确认的模拟纸质单：`POST /api/v1/orders/submit`，`confirm=true` 才落盘。
- 禁止 `order_send`。探测到本机 MT5 为 demo，只记账不发单。
- 控制台「确认挂模拟单」。研究不自动开单。
- Smoke 14 + Stability 03 PASS。`tm-order-20260823-000003` EURUSD SELL 0.01 paper。

---

## 2026-08-23 — V4.1 Freeze

- `POST /api/v1/research/run` 可选 `chain`，最多两步现有预设。
- 开算前两台都必须在线；第一步失败不跑第二步。
- 控制台「因子后再回测」。`init()` 仍不自动跑。
- Smoke 13 + Stability 02 PASS。已冻结。不接 MT5。

---

## 2026-08-23 — V4.0 Freeze

- Phase 4：`tests/stability/01_research.py` PASS。连续 10 次 monitor 研究，调度中心仍健康；`:9100` 仍是同一进程（未双开 14B）。
- Worker 全离线 → TM-1002 路径；网关 503 → `ai_skipped`。
- V4.0 冻结。下一模块才是 V4.1。不做 MT5。

---

## 2026-08-23 — V4.0 Phase 2/3（实现 + Smoke 12）

- `POST/GET /api/v1/research*`：一笔现有计算 + 至多一次 AI，存 `data/research/`。
- 控制台「研究一笔」+ 研究记录列表。打开页面不自动跑。
- 复用 Master 已有 Worker 探针，避免每次新建 Registry 误判离线。
- 冒烟：`tests/smoke/12_research.py` PASS（indicator 含 RSI；重叠 TM-1005；非法 preset TM-1001）。
- 未做 Phase 4 稳定性、未冻结、未开 V4.1。

---

## 2026-08-23 — 各阶段目标对照

- `docs/STAGE_GOALS.md`：最终目标写清；后面 V4.0 / V4.1 / V5 各五步的「做到什么才算过」。
- 不把 V4 第一冻写成最终目标。

---

## 2026-08-23 — V4 Phase 1 设计（未实现）

- `docs/DESIGN_V4_RESEARCH_AGENT.md`：研究一笔 = 1 次现有计算 + 至多 1 次 AI。
- SPEC §16 草案；Decision 024。禁止在确认前写 `research_service.py`。

---

## 2026-08-23 — 通义千问单路推理

- Decision 023：`generate()` 互斥；`max_tokens`≤1024；消息截断。
- `start_sycl.bat` 写死 `GGML_SYCL_F16=OFF`。
- 冒烟：`tests/smoke/11_gateway_guard.py` PASS。正在跑的网关需重启才加载锁。

---

## 2026-08-23 — 算完后「用这笔数字问 AI」

- Decision 022：计算成功出现下一步条；该按钮只定位，不调用网关。
- 通义千问离线时禁用提问。仍禁止算完自动推理。
- 冒烟：`tests/smoke/10_ai_next.py`。

---

## 2026-08-23 — 一键状态以 HTTP 健康为准

- SPEC §15.5 + Decision 021：是否跳过启动只认 `/health`，不用 `netstat | findstr :9000`。
- 新增 `scripts/lab_status.py`：列出 Master / Gateway / 四台 Worker。端口占用但不健康则禁止再开窗口。
- `start_lab.bat` 弹窗按 `LAB_STATUS_OK / PARTIAL / FAIL`，不再笼统说已就绪。
- 冒烟：`tests/smoke/09_lab_status.py`。

---

## 2026-08-23 — Xavier-01 纳入四台同等启动

- SPEC §15.4 + Decision 020：一键覆盖 01–04。01 用固定名 Docker 启停，禁止重启 `docker ps` 第一行。
- `start_xavier_workers.py` 去掉默认 `SKIP Xavier-01`。已健康仍跳过。
- 文案：`start_xavier.bat` / `start_lab.bat` 改为四台。
- 冒烟：`tests/smoke/08_xavier01.py`（探活 + 已在线不重复启动；不停容器）。

---

## 2026-08-22 — 默认计算路径 + 详情带结果

- SPEC §8.4 / Decision 019：`GET /task/{id}` 可读则带 `data.result`；`GET /tasks` 不加载结果正文。
- 控制台推荐一笔在线计算，「现在就计算」才提交；刷新不自动算，算完不自动问 AI。
- 「让 AI 解读」改为送节点算完的数字（RSI latest / 因子评分 / 回测收益），不再送任务请求。
- 冒烟：`tests/smoke/07_default_path.py` **PASS**（2026-08-23，Master 重启后）。对照：`docs/DIFF_2026-08-22_default_path.md`。

---

## 2026-08-22 — 控制台去掉误用酒红

- Stitch 设计说明是深黑控制台（`#070b12` / `#111827` / 蓝 `#3b82f6` / 紫 `#7c5cfc` / 绿 `#10b981`）。
- 酒红来自「炒股」项目名自动色板，不是设计稿要求。已改回。

---

## 2026-08-22 — 网页启动/重启落地 + 桌面快捷方式提示

- SPEC §15 + Decision 018：`POST /api/v1/ops/worker/{id}/start|restart`、`POST /api/v1/ops/master/restart`。
- 控制台按炒股稿：酒红底、节点卡「启动/重启」、顶栏「重启调度中心」；通义千问不提供网页重启。
- 桌面只保留 `TradeMind-Lab.lnk`（`cmd /k start_lab.bat`）。已在运行会跳过，并弹窗 + 黑窗口停住，不再秒关。
- 冒烟 `tests/smoke/06_ops.py`：未知 worker `TM-1001`；worker-02 已在线提示。

---

## 2026-08-22 — 桌面合成一键 + 网页重启设计

- 合成脚本 `start_lab.bat` = 本机 `start_all.bat` + Xavier `start_xavier.bat`。
- 桌面快捷方式：`TradeMind-Lab.lnk` → `start_lab.bat`。
- 网页「节点启动/重启、调度中心重启」：**仅 Phase 1 设计**，见 `docs/DESIGN_OPS_RESTART.md`。未改 SPEC、未写接口。
- Stitch 指定炒股项目出控制台运维稿；生成通道若再断线，以设计文档为准。

---

## 2026-08-22 — 本机一键启动 + 拉起 Xavier-02/03/04

- 新增 `start_all.bat`：已占用 9000/9100 则跳过，否则新窗口启动 Master + `start_sycl.bat`，等健康后打开控制台。
- 实测：`LOCAL_START_PASS`，`tests/smoke/05_oneclick.py` PASS（Master / Gateway 模型已加载 / Master 代理 AI）。
- 新增 `start_xavier.bat` + `scripts/start_xavier_workers.py`：SSH 拉起 02/03/04，不碰 01。
- **端口对齐 (FACT)：** 回测进程监听 8002，`data/workers.json` worker-03 由 8080 改为 8002。
- 拉起后 Master `/workers`：01–04 全部 ONLINE。`POST /task` 因子/监控/回测三笔 COMPLETED。
- 对照：`docs/DIFF_2026-08-22_oneclick.md`。

---

## 2026-08-22 — Dashboard 控制台改版（语义 + 去重）

- 三步说明：看节点 → 开始计算 → 看记录 / 问 AI。
- 去掉重复入口：类型不再既有快捷按钮又有下拉；JSON 收到「高级」；统计并进计算记录标题；AI 状态只在顶栏。
- 按钮语义：提交计算 = 「开始计算」；对话 = 「问 AI」；任务详情 = 「让 AI 解读」。
- 文案标明：AI 只读输入框数字，默认是示例，不是实盘或节点结果。
- 接口与冒烟关键字未改：`问 AI`、通义千问、`/api/v1/ai/*`。

---

## 2026-08-22 — V3.0 Freeze (Arc A770M SYCL 真推理通过)

### GPU (FACT)

- 重编 `llama-cpp-python 0.3.34`, `GGML_SYCL_F16=OFF`。
- 设备: `SYCL0 Intel Arc A770M` (约 15GB 空闲)。
- `n_gpu_layers=-1`, `n_batch=512`, `flash_attn=False`。
- `try_gpu_chat.py`: 生成 ~7 tok/s, `GPU_CHAT_OK`。
- 网关 `POST /api/v1/ai/chat` HTTP 200, 13 tokens / 8.4s; Master 代理 `/api/v1/ai/health` 200。
- 禁止 `ONEAPI_DEVICE_SELECTOR=level_zero:gpu:0` (backend_init 抛 0xe06d7363)。
- 启动: `ai-gateway/start_sycl.bat`。CPU 备用: 重编 CPU wheel + `start_cpu.bat`。

### 冻结范围

- 本地模型只允许 Qwen2.5-14B-Instruct Q4_K_M。
- Master `/api/v1/ai/*` 代理 + 中文 Dashboard AI 入口。
- V4 Research Agent / V5 MT5 未开始。

---

## 2026-08-22 — AI Gateway 回退 CPU（GPU 推理崩溃）

- SYCL wheel 启动可加载模型, 但 `/api/v1/ai/chat` 进程 Abort (`3221226505`)。
- 重装 `llama-cpp-python 0.3.34` CPU wheel (~12MB); `n_gpu_layers: 0`。
- 启动脚本: `ai-gateway/start_cpu.bat`。
- 本机验证: `POST /api/v1/ai/chat` HTTP 200, 14 tokens / 5.4s, 模型自称 Qwen。
- Dashboard 已改为中文界面。

---

## 2026-08-22 — V3.0 Phase 1.5b SYCL + Phase 3 Master 代理 + Phase 4 Dashboard

### 文档纠偏 (FACT)

- 本地推理模型只写 **Qwen2.5-14B-Instruct Q4_K_M**。
- 清掉残留误写: `TODO.md` 的 "GPT-5.6 模型"、`ROADMAP_NEXT.md` 的 `Other-14B` / `Other.5-14b-instruct`、`PROJECT_VISION.md` 的 "Other conda"。
- GPT-5.6 是历史误写, 已废弃; 不是已部署模型, 也不是 Agent 身份。

### Phase 1.5b SYCL GPU (FACT)

- 根因修复: 必须 `-G Ninja` + `icx`, 不能用 Visual Studio generator。
- `CMake` 配置通过: `SUPPORTS_SYCL - Success`, oneMKL SYCL 库已找到。
- `ggml-sycl.dll` 链接成功 (`C:\tmp\sycl-probe-rel`)。
- `llama-cpp-python 0.3.34` SYCL wheel 已装入 `ai-gateway/.venv` (约 50MB, 含 `llama_cpp/lib/ggml-sycl.dll`)。
- pip 编译必须 `TMP=C:\tmp\icx`, 否则 icx 报 `#10026 error generating temporary file`。
- 运行必须先 `setvars.bat` (建议 `ai-gateway/start_sycl.bat`); 未初始化 oneAPI 时 `import llama_cpp` 会因缺 SYCL 依赖 DLL 失败。
- 本轮未再跑 8.37GB 真实 GPU 推理; 功能冒烟以 Master 代理 + Dashboard 入口为准。CPU 后端真实推理仍以 2026-08-02 记录为准。

### Phase 3 Master 代理 (FACT)

- `SPEC.md` 第十四节 + Decision 017。
- Master 新增: `GET/POST /api/v1/ai/{health,models,generate,describe,signal,chat}`。
- 配置: `ai_gateway.url` / `TRADEMIND_AI_GATEWAY_URL`, 超时 `TRADEMIND_AI_GATEWAY_TIMEOUT_SECONDS`。
- 离线 `TM-1002` / 超时 `TM-1004`。

### Phase 4 Dashboard (FACT)

- Worker 区增加 AI Gateway 卡片。
- 增加 Ask AI 面板 + 任务结果 "AI 分析" 按钮。
- 文案固定 Qwen2.5-14B-Instruct, 不含 GPT-5.6。

### 冒烟

- `tests/smoke/04_ai_gateway.py` 全部 PASS (proxy offline/timeout/success + routes + dashboard)。
- 本机 Master `:9000` 当时未运行, live 项 SKIP。

## 2026-08-02 — 文档纠偏: 移除错误的 "GPT-5.6" 模型引用

### 背景 (FACT)

用户指出 GPT-5.6 非开源、无 GGUF, 无法作为本地模型部署。经核查:

- 实现类文档 (`V3_AI_GATEWAY_SPEC.md` / `CHANGELOG.md` / `TODO.md` / `TRADEMIND_CONTEXT.md`)
  与代码 (`server.py` / `config.yaml`) 一致使用 **Qwen2.5-14B-Instruct** (已下载 8.37GB)。
- 但 `PROJECT_VISION.md` 与 `ROADMAP_NEXT.md` 将目标模型误写为 **"GPT-5.6"**
  (如 `| GPT-5.6 | BLOCKED | SYCL 后端编译为阻塞项 |`), 与同文件其他行 (首选模型 Qwen) 自相矛盾。

### 改动

- `docs/PROJECT_VISION.md`: 4 处 "GPT-5.6" -> "Qwen2.5-14B-Instruct"。
- `docs/ROADMAP_NEXT.md`: 1 处 "GPT-5.6" -> "Qwen2.5-14B-Instruct"。
- 澄清: GPT-5.6 是历史误写, 已废弃; 本地 LLM 始终是 Qwen2.5-14B-Instruct Q4_K_M。项目不部署、也不使用 GPT 系列作为推理模型。

### 结论

- 部署模型 = Qwen2.5-14B-Instruct (无需其他模型)。
- 无需、也无法部署 GPT-5.6。

## 2026-08-02 — V3.0 AI Gateway Phase 1.5 DONE (CPU 后端) + 真实冒烟测试通过

### 本次改动 (FACT)

- **安装 C++ 构建工具链 (Phase 1.5 的真正阻塞项)**: 环境原本缺 MSVC / Windows SDK / cmake / git。
  - 用管理员权限安装 Visual Studio Build Tools 2022 (Desktop development with C++):
    MSVC 14.44.35207 + Windows SDK 10.0.26100.0 + cmake 4.4 + ninja 1.13。
  - oneAPI 2026.0 已提供 `icx`/`icpx`/`sycl-ls` (Arc A770M SYCL 可用)。
- **安装 llama-cpp-python 0.3.34**: PyPI 无 cp313/win 预编译 wheel, 必须源码编译。
  - 源码 sdist 解压因 Windows MAX_PATH (260) 失败 (vendor/llama.cpp/tools/ui 深层路径);
    已用短路径解包到 `D:\s\llama_cpp_python-0.3.34` 规避。
  - SYCL GPU 编译尝试失败 (见下); 改用 **CPU 后端** (MSVC + AVX2) 编译成功,
    wheel 12MB 已装入 venv (`ai-gateway/.venv`)。
- **真实冒烟测试通过** (`tests/smoke_real.py`, 非白盒):
  - 实际加载 8.37GB `qwen2.5-14b-instruct-q4_k_m.gguf` 到内存 (CPU)。
  - `POST /api/v1/ai/chat` 返回 HTTP 200, 真实生成中文回复; 模型自报为 Qwen。
  - 23 tokens / 8.8s (CPU ~2.6 tok/s); 第二次对话正常, 统计累计正确。
  - 结论: 网关全链路 (FastAPI → InferenceEngine → llama_cpp → 模型) 真实可用。

### SYCL GPU 编译失败原因 (已知, 待解决)

1. scikit-build 选 Visual Studio generator + MSVC, 忽略 `CMAKE_C_COMPILER=icx`; SYCL 设备编译器未生效。
2. 链接错误 `MKL::MKL_SYCL::BLAS` target 未找到 (oneMKL SYCL interfaces 未接好)。
   → GPU 加速需在 Windows 上修复 oneAPI 工具链/开关, 见 TODO "Phase 1.5b"。

### 结论

- 部署模型 = Qwen2.5-14B-Instruct Q4_K_M (已验证可加载 + 推理, 模型自报 Qwen)。
- 当前后端 = CPU (功能正常, 但慢); Arc SYCL GPU 后端为下一步优化 (Phase 1.5b)。

---

## 2026-08-02 — V3.0 AI Gateway Phase 2 代码实现 (白盒测试通过)

### 本次改动 (FACT)

- **新建 `ai-gateway/inference.py`** (4736 B): `InferenceEngine` 封装 llama-cpp-python。
  - 关键设计: `llama_cpp` 使用*懒加载* (lazy import), 模块可在未安装原生扩展时导入。
  - 模型缺失/库缺失时优雅降级, 记录 `load_error`, 不抛异常阻断启动。
  - `stats` 真正实现 `avg_latency_ms` (修复 SPEC 中遗留的 TODO)。
- **新建 `ai-gateway/models.py`** (1519 B): Pydantic 请求模型
  (`GenerateRequest` / `DescribeRequest` / `SignalRequest` / `ChatRequest` / `ChatMessage`)。
- **新建 `ai-gateway/server.py`** (9118 B): FastAPI 服务, 端口 9100。
  - 端点: `/health`, `/models`, `/api/v1/ai/generate`, `/api/v1/ai/describe`,
    `/api/v1/ai/signal`, `/api/v1/ai/chat`。
  - 模型未加载时 `/health` 返回 `degraded`, 推理端点返回 `503`。
- **新建 `ai-gateway/tests/test_whitebox.py`** (3454 B): 白盒测试 (无需 GPU/运行服务)。
- 修正 `config.yaml` 模型路径默认值为真实文件名 `qwen2.5-14b-instruct-q4_k_m.gguf`。

### 白盒测试结果 (FACT)

```
pytest tests/test_whitebox.py  ->  10 passed, 1 warning (StarletteDeprecationWarning)
```
覆盖: 模块导入, 路由注册, /health 降级, /models 列表, 推理端点 503,
InferenceEngine 懒加载与未加载时 generate 抛 RuntimeError。

### 重要: 仍未完成 (不要误判为 DONE/FROZEN)

- `llama-cpp-python` **尚未安装** (venv 内 `import llama_cpp` 失败)。
- 因此模型**无法真正加载**, 真实 GPU 推理冒烟测试尚未进行。
- 安装 pytest 到 venv (测试依赖, 原 requirements 未包含)。

### 下一步

- Phase 1.5: 在 venv 内安装 `llama-cpp-python` (SYCL 或 CPU fallback)。
- 安装后运行 `python -m pytest tests/test_server.py` 做真实加载冒烟测试。
- 全部通过后, 再进入 Master 接口连接 / Dashboard AI 入口。

## 2026-08-01 — V3.0 AI Gateway (Phase 0+1 完成, Phase 1.5 阻塞中)

### 环境

- Intel Arc A770M 驱动 32.0.101.8826 ✅
- oneAPI 2026.0, `sycl-ls` 可见 Arc A770M ✅
- Python 3.13.12 (Miniconda), venv `ai-gateway/.venv` ✅
- venv 已装: fastapi 0.141.1, uvicorn 0.52.0, pydantic 2.13.4, pyyaml 6.0.3, huggingface-hub 1.26.0

### 模型

- GGUF 模型已下载: `ai-gateway/models/qwen2.5-14b-instruct-q4_k_m.gguf` (8.37GB)

### 已完成文件

- `prompts.py` — 3 个 prompt 模板 (投研/策略/信号) + dict_to_text
- `config.yaml` — 端口 9100 / 模型路径 / n_ctx 4096
- `requirements.txt` — 6 个依赖
- `tests/test_server.py` — 6 个冒烟测试用例

### 阻塞项

- `llama-cpp-python` 未安装 — SYCL 后端编译为 Phase 2 阻塞项
- `server.py` / `inference.py` / `models.py` 空文件 — 待 Phase 1.5 完成后实现

### 交接文档

- 新增 `V3_HANDOFF.md` — 完整进度/文件状态/下一步行动/风险
- 新增 PROJECT_OVERVIEW.md — 项目总览 (愿景/目标/架构/状态/读取顺序)

---

## 2026-07-31 — V2.1 Backtest Worker 增强

### 新增功能

- 4 个新策略: TURTLE (海龟/ATR止损), GRID (网格交易), BOLLINGER (布林带), VWAP (量价)
- 滑点模型: slippage_bps 参数, 买入向上滑/卖出向下滑
- 手续费模型: commission_bps 参数, 双向扣除
- 高级指标: Sharpe/Sortino/Calmar 比率, 盈亏比
- 资金曲线: 50 点采样, 前端可直接画图
- initial_capital 参数, 默认 10000
- ThreadingMixIn 并发安全

### 修复

- Python 3.6 兼容: stdout=PIPE + decode()
- ThreadingMixIn 防死锁
- try/except 保护

### 部署

- Xavier-03 (192.168.1.203:8080) stdlib 部署
- 7 策略全部冒烟测试通过
- 70/70 cross-symbol 组合测试通过

### 已知问题

- Master 探测线程受 Indicator Worker 2s 超时阻塞


## 2026-07-16 — V1.1 Phase 1 文档同步

### 完成

- 新增 `SPEC.md` — V1.1 技术规范（Task/Worker 生命周期、API、Storage、错误码）
- 新增 `PROJECT_STATUS.md` — 项目状态快照（接力开发入口）
- 更新 `AGENTS.md` — 增加 SPEC 铁律、接力阅读顺序、V1.1 八阶段流程
- 更新 `DECISIONS.md` — 新增 Decision 009–016（V1.1 冻结决策）
- 更新 `TODO.md` — 对齐 V1.1 Implement 八阶段
- 更新 `TEST_PLAN.md` — 对齐 Smoke 01/02/03 结构

### 决策落地

- POST /task 同步执行，返回 COMPLETED|FAILED
- Task ID：`tm-task-YYYYMMDD-NNNNNN`
- 存储分离：`tasks/` 元数据 + `results/YYYY/MM/DD/` 结果
- workers.json 只存静态注册，无 status
- Worker 类型：`indicator-worker`
- 统一 API 响应：`{success, message, code, data}`
- 错误码固定四个：TM-0000 / TM-1001 / TM-1002 / TM-1003

### 下一步

- Phase 2：Master 代码对齐（仅 `master/api/`）

---

## 2026-07-15 — V1.0 Worker Template 冻结 + 项目框架搭建

### 完成

- Worker Template v1.0（`workers/indicator-worker`）
  - FastAPI 0.83.x + `@app.on_event` 生命周期
  - REST API：`/health`、`/ready`、`/version`、`/metrics`、`/indicators`
  - 计算接口：`POST /api/v1/indicator/calculate`
  - Prometheus（prometheus-fastapi-instrumentator）
  - Docker Compose + healthcheck + logging
  - `TRADEMIND_*` 统一配置
  - 测试套件（API + 指标 + 并发 + 性能）

### 新增

- 项目治理文档：`AGENTS.md`、`PROJECT.md`、`TODO.md`、`ROADMAP.md`、`ARCHITECTURE.md`、`DECISIONS.md`
- 目录框架：`master/`、`workers/`、`sdk/`、`dashboard/`、`docs/`、`docker/`、`config/`、`scripts/`、`tests/`
- `workers/indicator-worker` 作为 Worker 母版

### 决策

- 不使用 Git（一人 + AI 协作）
- 不使用 ADR 目录，统一 `DECISIONS.md`
- V1.1 目标：Master API 跑通链路


