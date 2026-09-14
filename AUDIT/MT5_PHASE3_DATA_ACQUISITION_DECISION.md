# Phase 3 Data Acquisition Decision

**Date:** 2026-09-14  
**Inputs:** EXP-008/009 specs, vendor matrix, acceptance tests.  
**Not done:** buy, FRED pull, TE trial, train, backtest, `order_send`.

```
STRATEGY EDGE: NOT PROVEN
INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN
ECONOMIC EDGE: WEAK
CURRENT AUTO-TRADING STRATEGY: NONE
BROKER LEVERAGE: 400x
TARGET MONTHLY RETURN: 20%+
TARGET STATUS: UNSUPPORTED
CANDIDATE: FALSE
EXECUTION: NOT AUTHORIZED
PHASE 3: BLOCKED
```

20%/month is **not** a reason to buy a more expensive calendar.

---

## 1. EXP-008 recommended source

**Primary paid candidate (consensus):** Trading Economics **Calendar** API, **trial first**.

**Why:** Official US sources do **not** publish historical economist consensus. TE is the only **personally purchasable** product that *documents* a calendar PIT window (`Forecast` / `Actual` / `Revised` / `LastUpdate`). Bloomberg/LSEG/FactSet/Macrobond are better known in shops and are **ENTERPRISE_ONLY**.

**Required companion (free, not a second purchase):** BLS CPI + Employment Situation archives + ALFRED first vintages + Fed FOMC statement clocks — **acceptance oracle**, not the surprise itself.

**Risks:**

- Official TE price page has been **PRICE_UNKNOWN** / **403** from this lab before. Third-party $149–$299/mo is **UNVERIFIED**.
- `Forecast` may not be Bloomberg street. `TEForecast` is a **model** — must not be used as consensus unless the contract says so (default: **do not**).
- Trial auto-charges if not cancelled; trial caps 100k points / 100 requests.
- Vintage may fail Tests 2, 3, 5, 10. Then **do not** convert the trial to a month.

---

## 2. EXP-009 recommended source

**Primary: FRED / ALFRED `DFII10` + H.15 16:15 ET knowledge rule + Treasury real-par XML cross-check.**

**Why:** This **is** the 10-year TIPS constant-maturity real yield. It is **$0**, has vintages, and does not require Bloomberg. DGS10 / Bund / DXY are **wrong objects**.

**Risks:** FRED ingest lag (ALFRED: typically within one business day). Using `observation_date` as knowledge_time **FAIL**. Paying a terminal for the same H.15 print is waste.

---

## 3. Free alternatives

| Experiment | Free path | Enough? |
|------------|-----------|---------|
| EXP-009 | FRED+ALFRED+Treasury+H.15 | **Yes** for the registered object |
| EXP-008 | BLS+ALFRED+Fed clocks | **No** — missing consensus. A “first print vs last month” book would be a **new id**, not EXP-008 |

---

## 4. Paid path

| Packet | Action | Cap |
|--------|--------|-----|
| EXP-008 | TE **trial** → dump US FOMC/CPI/NFP 2018–2025 → acceptance. If PASS, **one month** only to freeze a hash | Do not pay **> $300/mo**. No annual until tests PASS |
| EXP-009 | **$0** | Do not pay |

---

## 5. Do not buy

- Bloomberg / LSEG / FactSet / Macrobond  
- News / sentiment / tick / DOM / option surface  
- Databento credits (wrong object)  
- Investing.com / FXStreet scrapes  
- DGS10, GVZ, COT, EIA “again”  
- TE Markets / extra countries / extra indicators beyond FOMC/CPI/NFP  

---

## 6. Price above which it is not worth it

- TE Calendar **> $300/month** or multi-thousand enterprise ECO: **skip**. Incremental gold alpha vs BUY_HOLD is **unproven**; a $2k terminal cannot be justified by a 20% wish.  
- Any vendor that cannot pass Tests 2–3: **$0 is already too much**.

---

## 7. After files arrive — acceptance

Run `AUDIT/MT5_PIT_DATA_ACCEPTANCE_TEST.md`. Critical fail ⇒ `DATA = BLOCKED`.

---

## 8. Freeze only after acceptance

Order:

1. Acceptance PASS  
2. Write `docs/research_engine/EXP008_*` / `EXP009_*` contract with **data_hash**  
3. `m += 1` in `AUDIT/MULTIPLE_TESTING.md` **before** any engine  
4. Then a later session may run **one** pre-registered book  

This decision file does **not** start step 4.

---

## 9. Why still BLOCKED

- EXP-008 pack **does not exist**. Official sources cannot supply consensus. TE is untested.  
- EXP-009 can be downloaded for free **later**; it has not been pulled in this session.  
- Phase 2 banner unchanged. No Candidate. No execution.  
- EXP-007 is unrelated and still “expected fail,” not a consolation scan.

---

## 10. What you should do next (human)

**Do not start the experiments.**

**EXP-009 (no money):**

1. Create a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html  
2. Put it in `.env` as `TRADEMIND_FRED_API_KEY` (never git, never chat).  
3. Tell Cursor (later session): “Acquire DFII10 per `AUDIT/MT5_EXP009_TIPS_DATA_SPEC.md` and run acceptance tests.”

**EXP-008 (maybe money):**

1. Open https://tradingeconomics.com/api/pricing.aspx and **read the live checkout** (this lab has seen 403 / PRICE_UNKNOWN).  
2. If a **trial** exists: start it, **calendar only**, dump FOMC/CPI/NFP, then **cancel if you do not want the auto-charge**.  
3. Drop CSV/JSON in `data/market/research_engine/phase3/exp008/`.  
4. Tell Cursor: “Run `AUDIT/MT5_PIT_DATA_ACCEPTANCE_TEST.md` on this dump.”  
5. If FAIL: **do not pay**. EXP-008 stays BLOCKED.  
6. If PASS and monthly price **≤ $300**: one month to freeze the hash, then cancel.  

**Buy now?** **No automatic buy.**  
**Suggested:** acquire EXP-009 for **$0** when you want; TE **trial only** for EXP-008.  
**Not suggested:** Bloomberg, annual TE, or any data outside these two packets.
