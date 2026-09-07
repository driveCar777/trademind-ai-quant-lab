# Post-V21 Purchase Value Case

**Date:** 2026-09-04  
**Decision recorded here:** `DO_NOT_BUY`  
This is not a request. Do not ask the human whether to buy.

---

## What would be bought

The only previously quoted increment that is still `PAYMENT_REQUIRED` and not already owned:

| Item | Price (quoted) | Surface |
|---|---|---|
| LO 1Y MVD-A (WTI options on futures, Databento) | **$11.99** | IV / skew / term on one energy name |
| OG 1Y MVD-A (Gold options, previously preferred in V8.4 CASE B) | **$14.99** | IV-RV on GOLD CFD sibling |
| Dual OG+LO 1Y MVD-A | **$26.99** | two names, still the same 4-name book |
| Databento Standard | **$199/mo** | already rejected |
| Tushare / Wind / Choice / CSMAR | not quoted this round | A-share fundamentals/events already tested on free PIT |

$93 Databento remainder remains `UNUSED_RESEARCH_RESERVE`. V8.4 sufficiency for a later human spend was **A** on LO 1Y MVD-A. Occupancy of ATM/OTM/front/second on a paid pull is still UNKNOWN until download.

---

## What new question it could answer

> After owning Pack E curves, do option-implied moments on LO (or OG) produce a **Level-1 Candidate on the MT5 4-name CFD book** that V9/V10 already failed?

That is a new *feature class* (IV/skew/term) on an **old universe**.

It does **not** answer:

- Why 42 A-share dual-book hyps have 0 positive validation capital.
- Whether a second *A-share* independent book exists.
- Whether the 20-day long-only CS construction should change (locked).

---

## Why this is not V9/V10 in a new wrapper — and why that still is not enough

V9/V10 used owned futures/CFD features on GOLD/OIL/EURUSD/USDJPY and returned `NO_CANDIDATE`. Options IV is not a rewrite of those features. Information increment vs owned columns: **high**.

P(new Level-1 Candidate) after $12: **low-to-medium**. The universe is four CFD names whose price-only, curve, and fusion families already died. A new column on the same four names is the definition of a paid hole, not a new market.

Even a lucky LO IV Candidate would be:

- on MT5 CFDs, not A-share,
- one name / one surface,
- still far from two independent *capital* books and from CAGR ≥ 10%,
- and would not repair H11/H12’s official −16% path.

---

## Default if nobody pays

`DO_NOT_BUY`.

Keep NEW_PURCHASE = FALSE. Keep `$0` this session.

Research judgment without payment:

1. A-share free PIT CS / announcement space is marginally exhausted (Post-V21).
2. Construction forensics: verdict **A** for missing second Alpha; sidecar **B** only for the overlap-vs-book crack already named in V14.1.
3. Paid options on the 4-name book are the remaining high-IV *external* hole. They stay on paper until a human spends. They are not the next automated unit.

Do not open `$199`. Do not tick. Do not buy MVD-B “for coverage.” Do not buy A-share vendor fundamentals to re-run V16.

## Addendum 2026-09-04 after W1–W4 (thickened, still DO_NOT_BUY)

**Default if nothing is bought:** project stays at LEVEL=1 / CANDIDATE=2 / NEW_INDEPENDENT=0 / PAPER=0. H11/H12 KEEP_LOW_PRIORITY. No trading. That is the correct default given the evidence; it is not a failure of discipline.

**Question any future purchase must answer *before* money moves:** "Which A-share (or other) *information object* does this buy add that is not a ratio, a membership, a filing window, or a price-derived state — and what is the pre-registered contract?"

Scored against that question:

| Purchase | Answers an A-share NEW_INDEPENDENT question? | Answers any NEW_INDEPENDENT question? | Verdict |
|---|---|---|---|
| LO 1Y MVD-A $11.99 | **No.** WTI options say nothing about A-share names. | Maybe: new feature class on a 4-name CFD book that already failed V9/V10. P(Level-1) low–medium. | Keep on paper. Not now. |
| OG 1Y MVD-A $14.99 | No | Same as above, GOLD | Keep on paper. |
| BaoStock login for `pbMRQ/peTTM` (free, $0, needs session) | It is a **ratio**. Same object class as V16. W2 lists it LOW_VALUE. | — | Not a purchase; still not a new object. Do not open as V22. |
| BaoStock `balance` API (free, $0) | Leverage **ratio**. V16 sibling. Locked. | — | No. |
| Tushare / Wind / Choice / CSMAR | Could add: holder changes, block trades, margin balances, analyst revisions, northbound flow — these are *not* ratios / memberships / filing windows. **This is the only class that could answer the A-share question.** Cost unquoted this round. | Yes, if PIT-able. | The one paid hole that maps to the real gap. Requires a human quote + spend. Not auto. Not asked. |

So: the *cheap* option (LO $11.99) does not touch the A-share gap. The option that touches the gap (vendor flow / holder / margin data) is unquoted and human-gated. Both stay in this file.

**Correction 2026-09-04 (later the same day):** the margin part of that class is **not** vendor-only. SSE/SZSE publish daily per-stock margin detail for free and the Eastmoney datacenter mirrors it back to 2010-03-31; both were probed reachable today (the V12-era "AkShare-class HTTP SSL 失败" no longer holds). It has been taken as **V23** at $0 — see `V23_MARGIN_CONTRACT.md`. Holder-count (quarterly, Eastmoney `RPT_HOLDERNUMLATEST`) and northbound holdings (HKEX, daily since 2017) are also free and reachable; they stay unqueued until V23 has a Decision (one family at a time).

**Databento $93 → spent $47.10 on the 30-root CME futures cross-section (V22).** `FUTURES_XS_V1_NO_CANDIDATE`. Reserve ≈ $46 stays unspent; nothing left on Databento maps to the A-share gap, and `statistics`/OI would only thicken a family whose body is flat. See `DATABENTO_93_PURCHASE_EVALUATION.md` and `V22_FUTURES_XS_DECISION.md`.

## Addendum 2026-09-04 after Q1

Q1: 29/42 validation `excess_vs_b0` negative. Mean −0.535%. Free A-share labels already lose to eligible EW. Buying LO 1Y MVD-A still does not answer that. Default remains **DO_NOT_BUY**. Not a question.
