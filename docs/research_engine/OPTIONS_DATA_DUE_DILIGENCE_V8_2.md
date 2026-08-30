# Options Data Due Diligence V8.2

**Mode:** QUOTE ONLY. Downloaded: **false**. Purchased: **false**. Credits spent this task: **$0**.

**Standing:** LEVEL=0. CANDIDATE=0. STRATEGY=0. PORTFOLIO=0. PAPER=0. LIVE=0.

**Failed-alpha gate:** GVZ/OVX (`IMPLIED_VOL_V1`) is killed. That index is **not** the GC/CL option surface. A real OG/LO surface would still be new information. It would still not be alpha.

Dataset: `GLBX.MDP3`. Historical license cut used for all quotes: **2026-08-29** (today 2026-08-30 is live and `get_cost` rejects it).

---

## 1. What was inspected

Allowed: `metadata.list_schemas` (GET), `metadata.list_fields` (GET), `metadata.list_unit_prices` (GET), `metadata.get_dataset_range` (GET), `symbology.resolve` (POST, free), `metadata.get_cost` (POST, quote).

Forbidden and not called: `timeseries.get_range`, `batch.submit_job`, any download, any purchase, Standard $199, ORATS, CME DataMine.

Machine:

- `data/market/research_engine/options/OPTION_COVERAGE_MATRIX_V8_2.json`
- `data/market/research_engine/options/OPTION_MVD_V8_2.json`
- `data/market/research_engine/options/OPTION_QUOTE_V8_2.json`
- raw probe: `OPTION_DD_RAW_V8_2.json`

---

## 2. Four things that are not the same

| Object | Where | What it is |
|--------|--------|------------|
| Option **definition** | `definition` | Identity: `raw_symbol`, `instrument_class` C/P, `strike_price`, `expiration`, `activation`, `underlying`, `security_type=OOF` |
| Option **price** | `ohlcv-1d` close | Electronic-session trade OHLC. **Not** official settlement. No bar if no trade |
| Option **settlement** | `statistics` `stat_type=3` | Venue official settle. Flags say preliminary/final, actual/theoretical |
| Option **implied vol** | **not on GLBX** | Databento `stat_type=14/15` exist as schema values, but the **GLBX.MDP3 dataset table does not publish 14 or 15**. ICE does. CME via this feed does **not** |

Therefore: **Databento does not hand us IV for OG/LO.** If we ever compute IV, it is **DERIVED**, not OBSERVED.

---

## 3. Answers that must be true before any dollar

### 1–3. Do GC/CL options exist? What are OG/LO?

| Parent | Exists on Databento? | Meaning |
|--------|----------------------|---------|
| `GC.OPT` | **NO** (HTTP 422) | Not a parent. Do not use |
| `CL.OPT` | **NO** (HTTP 422) | Not a parent. Do not use |
| `OG.OPT` | **YES** | COMEX **Options on Gold futures**. Underlying futures root is **GC** (sample `OGZ6 C5250` / `OGZ6 P5250` resolve) |
| `LO.OPT` | **YES** | NYMEX **Options on WTI crude futures**. Underlying futures root is **CL** (sample `LOU6 P7000` / `LOU6 C8000` resolve) |

`OG.OPT` is **not** “all gold options”. `LO.OPT` is **not** “all crude options”. See §6.

### 4–7. Strike, expiry, call/put, historical price

| Field | Present? | Evidence (no download) |
|-------|----------|------------------------|
| Strike | **YES** | `definition.strike_price` in `list_fields` (75 definition fields). Raw symbols contain strike tokens (`C5250`, `P7000`) |
| Expiry | **YES** | `definition.expiration` + month code in raw symbol |
| Call/Put | **YES** | `instrument_class` `C` / `P` (`T` = option spread) |
| Historical option price | **YES as a schema** | `ohlcv-1d` available on GLBX from 2010-06-06. Parent `get_cost` for OG/LO succeeds. **Occupancy of ATM / ±5% / ±10% is UNKNOWN until bytes exist** |

### 8–11. Volume, OI, settlement, bid/ask

| Field | In `ohlcv-1d`? | Elsewhere |
|-------|----------------|-----------|
| Volume | YES (electronic trades) | `statistics` `stat_type=6` cleared volume |
| Open interest | **NO** | `statistics` `stat_type=9` only |
| Official settlement | **NO** | `statistics` `stat_type=3` only |
| Bid/ask | **NO** | `bbo-1s` / `bbo-1m` / `tbbo` / `mbp-*`. Session high bid / low offer = statistics 8 / 7 |

### 12–14. Can definition + ohlcv-1d compute IV / skew / term?

**IV:** CONDITIONAL, **DERIVED**. Inputs: owned GC/CL futures settlement + strike + expiry + option price + risk-free proxy. Model: **Black-76**, not equity Black-Scholes. OG/LO are **American**; Black-76 is a European futures-option approximation. Residual: early exercise.

**ATM IV:** CONDITIONAL. Needs a daily price on the nearest-ATM listed strike. `ohlcv-1d` drops quiet strikes.

**Skew:** CONDITIONAL. Needs the same session, same expiry, at least ATM + one OTM put + one OTM call with prices. Pre-registered buckets: nearest ATM, ±5%, ±10%. Parent expansion **includes** many strikes. That is not proof those strikes **traded**.

**Term structure:** CONDITIONAL. `OG.OPT` / `LO.OPT` are monthly parents and expand **multiple expiries**. That is enough *in principle* for front vs second. A single-expiry world is not what these parents are. Occupancy of front **and** second on the same session is UNKNOWN until bytes exist.

This is **not CASE D**. The schemas can support the research question. They do **not** guarantee a usable surface.

### 15–16. Minimum useful pack and exact quotes

See `OPTIONS_MVD_V8_2.md` and `OPTION_QUOTE_V8_2.json`. Headline:

| Pack | Window | USD |
|------|--------|-----|
| OG MVD-A (definition+ohlcv-1d) | 1Y | **14.994811** |
| LO MVD-A | 1Y | **11.991718** |
| OG+LO MVD-A | 1Y | **26.986529** |
| LO MVD-B (+statistics) | 1Y | **24.088709** |
| OG MVD-A | 2Y | **24.886548** |
| LO MVD-A | 2Y | **23.126337** |
| OG+LO MVD-A | 2Y | **48.012885** |
| OG MVD-A | 3Y | **32.413535** (V8 revalidated) |
| LO MVD-A | 3Y | **34.224269** (V8 revalidated) |
| OG+LO MVD-A | 3Y | **66.637805** (V8 revalidated) |
| OG MVD-C (+bbo-1s) | 1Y | **62,759.69** |
| OG bbo-1s only | 1Y | **62,744.70** |

### 17–19. Worth spending? After buy? If not buy?

This task **does not spend**. Cheap CASE A packs exist. Cheap ≠ complete surface. Decision file: `OPTIONS_PURCHASE_DECISION_V8_2.md`.

If bought later: at most three **DESIGN** hypotheses (IV−RV, skew, term). Not a formal family until bytes exist and occupancy is measured.

If not bought: stay LEVEL=0. Do not reopen killed families. Other legal next information remains dated macro surprise. Do not rebuy Pack E.

---

## 4. Schema availability and research value

`metadata.list_schemas` for `GLBX.MDP3`:

`mbo`, `mbp-1`, `mbp-10`, `tbbo`, `trades`, `bbo-1s`, `bbo-1m`, `ohlcv-1s/1m/1h/1d`, `definition`, `statistics`, `status`.

There is **no** schema named `bbo`. Use `bbo-1s` / `bbo-1m`.

| Schema | Available | 1Y OG parent USD | Phase-1 value |
|--------|-----------|------------------|---------------|
| definition | YES | 11.63 | **Required** |
| ohlcv-1d | YES | 3.37 | Daily price + electronic volume. Maybe enough |
| statistics | YES | 40.79 (OG) / 12.10 (LO) | Official settle + OI. High value. OG is expensive |
| trades | YES | 1.79 | Same trades that build ohlcv; usually unnecessary |
| tbbo | YES | 2.98 | Bid/ask **only at trade times**. Not a quote surface |
| bbo-1s | YES | 62,745 | Continuous quotes. **Forbidden** at this credit balance |
| bbo-1m | YES | 3,494 | Still destroys the $60 floor |
| mbp-1 | YES | 15,242 | Not needed |
| mbo | YES | 30,598 | Not needed |
| status | YES | not quoted | Halts. Not needed for IV |

Unit prices ($/GB historical): definition 1.7, statistics 1.0, ohlcv-1d 190, trades/tbbo 28, bbo-1s 18, mbo/mbp-1 1.8. Daily bars are expensive **per byte**; options parents are expensive because **definition/statistics bytes** are huge.

---

## 5. CME root fragmentation (do not call one root a full chain)

10-day resolve `2026-08-19`–`2026-08-29`, `parent → instrument_id` (GLBX **rejects** `parent → raw_symbol`):

| Parent | Live? | Partial/UD mappings (10d) |
|--------|-------|---------------------------|
| OG.OPT | YES | 9246 |
| LO.OPT | YES | 3937 |
| OG1–OG4 | YES | 352 / 134 / 728 / 1548 |
| OG5 | NO this window | week-5 often absent |
| G2M G3M G1T G1W G2W G1R | YES | weekday gold weeklies |
| G1M | NO this window | |
| LO1–LO4 | YES | Friday crude weeklies |
| LO5 | NO this window | |
| ML2 NL1 WL1 XL1 | YES | Mon/Tue/Wed/Thu crude weeklies |
| ML1 | NO this window | |
| MCO.OPT | YES | Micro WTI options |
| OGW.OPT / LOW.OPT | NO | not parents |

`OG.OPT` parent also expands **user-defined spreads** (`UD:1Y:…` in `partial`). A parent purchase is **not** “outright chain only”. ATM-only cannot be bought on the first shot without a `raw_symbol` / `instrument_id` list, which itself needs definition.

Weeklies are **incremental**. Phase-1 design uses **monthly OG.OPT / LO.OPT only**. Adding Friday weeklies costs little extra on 1Y MVD-A (OG $16.93 vs $14.99; LO $13.40 vs $11.99) but mixes DTE regimes. Not default.

---

## 6. OPTION_INCREMENTAL_DATA_REQUIREMENT

Already owned, **do not rebuy**:

- Pack E billed **$31.816129**
- Slim curve `tm-fut-GLBX-CURVE-D1-20260829-000001` (8184 rows, 2010-06-04–2026-08-28)
- GC.FUT / CL.FUT: front/second settlement, open, expiry, OI, slope, steepening, knowledge times

Options need only **incremental** fields:

1. Definition (strike, expiry, C/P, underlying map)
2. Option price (electronic close and/or official settle)
3. Optional: option volume / OI as liquidity filters

Do not buy again: underlying futures, MBO/MBP, bbo-1s, GVZ/OVX, $199/month.

Realized vol for IV−RV comes from **owned** front futures settlements.

---

## 7. Knowledge time

Existing rule stays:

- Official settlement knowledge: session date **21:00Z**
- OI knowledge: **T+1 21:00Z**
- `ohlcv-1d` close is **not** official settlement. Do not treat it as T 21:00Z venue settle
- Definition `ts_event` is point-in-time; new strikes listed intraday are a lookahead risk if used same session

---

## 8. What “quote succeeded” does **not** prove

- That ATM and ±5/±10% OTM have a price every session
- That front and second expiries are jointly present
- That IV is observed
- That any hypothesis will pass FDR
- That option alpha exists

Data exists → mechanism → hypothesis → research → validation → FDR → Candidate.

V8 3Y dollar figures are **revalidated**. They still do not imply a completable IV/skew/term study until occupancy is measured on bytes.
