# MT5 PIT Data Vendor Matrix

**Date:** 2026-09-14  
**Scope:** EXP-008 (event surprise) and EXP-009 (TIPS real yield) only.  
**Price rule:** no invented list prices. Third-party figures are labeled **UNVERIFIED**. Official pages that do not show a number = **PRICE_UNKNOWN**. Institutional sales = **ENTERPRISE_ONLY**.

```
CANDIDATE: FALSE
PHASE 3: BLOCKED
```

Verdicts: **PASS** / **CONDITIONAL** / **FAIL** — not “looks professional.”

Classes: **A** true PIT/vintage · **B** history exists but revised/current DB · **C** history exists but knowledge time unprovable.

---

## 1. Matrix

| Vendor | Product | Object | Coverage | PIT | Vintage | First Release | Timestamp | API | Personal Purchase | Price | EXP008 | EXP009 | Verdict |
|--------|---------|--------|----------|-----|---------|---------------|-----------|-----|-------------------|-------|--------|--------|---------|
| St. Louis Fed | FRED / ALFRED API | DFII10, CPIAUCSL, PAYEMS, UNRATE, release dates | DFII10 from 2003; BLS series decades | A for official prints / yields | Yes (`realtime_*`, vintage dates) | `output_type=4` initial release | Date; **not** 08:30/16:15 clock — attach official clock | Yes, free key | Yes | **$0** | First print **only** | **Primary** | EXP-009 **PASS**. EXP-008 consensus **FAIL** |
| U.S. Treasury | Daily Par Real Yield XML / archive CSV | 10y TIPS par (R-CMT) | 2003+ | C if used alone | No vintage API | n/a (market yield) | Session date; quotes ~15:30 ET; not 00:00Z knowledge | XML GET | Yes | **$0** | No | Value cross-check | **CONDITIONAL** companion |
| Federal Reserve Board | H.15 HTML / DDP | DFII10 publication | Daily business days | Clock **A** | Current HTML is B | n/a | **16:15 ET** posted | DDP / HTML | Yes | **$0** | No | Clock oracle | **PASS** as clock |
| BLS | CPI + Employment Situation **archives** + CES vintages | First-print CPI / NFP | Archives to 1990s; CES vintages from 2003 method | A for the PDF/TXT of that month | CES vintage tables | Yes (that month’s release) | Header **08:30 ET**; historical **dates** on schedule pages | HTML/PDF; some APIs | Yes | **$0** | First print **PASS**; consensus **FAIL** | No | EXP-008 **CONDITIONAL** (prints only) |
| Federal Reserve | FOMC calendars / statements | Rate decision + statement time | Historical | A for the statement | Statements don’t “revise” like CPI | The statement is the print | Use **that meeting’s** posted time | HTML | Yes | **$0** | Print **PASS**; consensus **FAIL** | No | **CONDITIONAL** (no survey) |
| Trading Economics | Calendar API + documented PIT window | Consensus + actual + revised | Calendar claims long history (sample 2016+ in docs) | **Claimed A** | Date-range “as appeared”; must prove | `Actual` vs `Revised` fields in docs | `Date`, `LastUpdate` (example 13:30) | REST / Python | **Yes** (card / PayPal) | Official page: **PRICE_UNKNOWN** (quote / feature-based; prior host **403**). Third-party 2026 reviews **UNVERIFIED** ~$149–$299/mo Standard/Pro. Trial: not refundable; auto-charge if not cancelled; trial cap 100k points / 100 requests | **Primary paid candidate** | No | **CONDITIONAL** — trial + acceptance |
| Bloomberg | Terminal ECO / BDVD | Street consensus | Deep | A | Yes | Yes | Clock | Terminal / B-PIPE | No (firm) | **ENTERPRISE_ONLY** (typical terminal **PRICE_UNKNOWN**; not a personal API) | Overkill | Overkill | **CONDITIONAL** quality / **FAIL** as a purchase |
| LSEG / Refinitiv | Datastream / Workspace economics | Consensus + actuals | Deep | Usually A | Yes | Usually | Clock | Firm API | No | **ENTERPRISE_ONLY** | No | No | Do not buy |
| FactSet | Economics / estimates | Consensus | Deep | Usually A | Yes | Usually | Clock | Firm API | No | **ENTERPRISE_ONLY** | No | No | Do not buy |
| Macrobond | Analysis + data packages | Macro + consensus | Deep | Usually A | Yes | Usually | Clock | Web API for subscribers | Sales; not a casual card checkout | **ENTERPRISE_ONLY** / **PRICE_UNKNOWN** (UTS packages) | No | No | Do not buy |
| Investing.com / FXStreet / generic calendars | Public HTML | “Forecast / Actual” | Visible history | B / C | No immutable vintage | Unproven | Often date+time on page **today** | Scrape = FAIL | Free | $0 | No | No | **FAIL** |
| Grok / LLM / news search | Narrative | “What CPI did in 2019” | n/a | C | No | No | No | n/a | n/a | $0 | No | No | **FAIL** |
| Philadelphia Fed SPF | Quarterly survey | Not event consensus | Quarterly | Wrong object | Vintage exists | n/a | n/a | Free | Yes | $0 | No | No | **FAIL** (wrong frequency) |
| CME FedWatch (today) | Implied path | FOMC | Current | C / hindsight | No historical PIT store here | n/a | n/a | Web | Free | $0 | No | No | **FAIL** if pulled today as 2019 “consensus” |
| Databento | Market ticks / curves | Prices | Vendor catalog | n/a | n/a | n/a | n/a | Yes | Yes | Remaining lab credits are the **wrong object** | No | No | **FAIL** for 008/009 — do not spend |

---

## 2. FREE / LOW-COST vs PROFESSIONAL vs ENTERPRISE

### FREE / LOW-COST

| Use | Source | PIT? |
|-----|--------|------|
| EXP-009 entire series | FRED/ALFRED DFII10 + H.15 16:15 ET + Treasury XML check | **Free ≠ sloppy.** Vintage + clock required. |
| EXP-008 first prints + clocks | BLS archives + ALFRED initial release + Fed FOMC | **Free ≠ surprise.** No consensus. |

### PROFESSIONAL (individual can pay)

| Use | Source | Note |
|-----|--------|------|
| EXP-008 consensus | Trading Economics Calendar **trial → one month** if tests pass | Only paid packet allowed this phase. Not Markets, not Forecasts add-on, not annual unless tests already passed. |

### ENTERPRISE

Bloomberg / LSEG / FactSet / Macrobond — **do not solicit** for a one-person Ava research lab.

---

## 3. Price ceiling (do not buy above)

| Item | Rule |
|------|------|
| TE Calendar | If checkout **> $300 / month** or forces a year with no trial that can run Tests 1–10 → **do not buy** |
| Any ECO terminal | **do not buy** |
| News / tick / DOM / options | **do not buy** (not 008/009 inputs) |
| Databento leftover | **do not spend** on this |

Prior repo notes (`HUMAN_REQUIRED_ACTIONS.md`, 2026-08-28): TE ~$149–$199/mo, official pricing **403** from this host, TE Forecast ≠ Bloomberg street, vintage unproven ⇒ then `DATA_BLOCKED_FOR_LIVE_RESEARCH`. **Still true until a trial dump passes acceptance.**

---

## 4. Max packets this phase

1. EXP-008: **at most one** calendar dump (TE if tests pass).  
2. EXP-009: **at most one** DFII10 vintage file (**$0**).

Not a third packet.
