# Post-V21 Decision

**A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED**

STOP = `STOP_B`  
Reason: every legal, free, PIT-able A-share information class that was worth one unit of resource has been run or classified `LOW_VALUE`. No new independent Candidate. The next executable object is not another A-share CS / announcement-window family.

```
LEVEL = 1
CANDIDATE = 2          # H11_VOL_60 / H12_VOL_120 only
NEW_CANDIDATE = 0
NEW_INDEPENDENT_CANDIDATE = 0
STRATEGY = 2
PORTFOLIO = 0
PAPER = 0
LIVE = 0
FINAL_OOS = DENIED
NEW_PURCHASE = FALSE
SPEND = $0
XAVIER = not used
```

H11/H12 remain `KEEP_LOW_PRIORITY`. One cluster. No portfolio. No Long Validation.

CAGR ≥ 10% is the long-run capital aim. It is not a gate and was not used as one. The only published strategy path (H11/H12 official 20-day book) remains full-path negative (V14.1). No new book exists to compare.

---

## V21 — what ran, result, why the class stops

Machine: `data/market/research_engine/cn_a_share_div_v21/DECISION.json`  
`OVERALL=A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE` `STOP=STOP_B_FAMILY`

PIT READY. 5549 files. 24803 event rows. 24029 cash. Knowledge = `announce_date < signal`. Operate/ex-date was not knowledge time. Moutai 2023-03-31 hidden on announce day, visible the next calendar day. Mutation OK.

Two pre-registered announcement-window sets. Dual books. Family FDR **0/2**. Validation capital **2/2 negative**.

| ID | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | L1 |
|---|---|---|---|---|---|---|
| D1_CASH_ANN_20 | −4.24% | −97.07% | −41.06% | −36.68% | −0.0223 | N |
| D2_STOCK_ANN_20 | −16.48% | −100.00% | −72.02% | −92.34% | −0.0234 | N |

This is not a near-miss. After cost, buying names in a 20-session window after a public dividend plan is **worse than the already-failed slow characteristics** (V16 ratios, V20 membership).

Do not: retune the 20-day window; flip to short; add yield quintile; download 5549 again; open forecast/express as a sibling 20-day announcement book. That last item would be coverage of the same economic object (`long the name after a filing`).

Dividend *yield level* was already `LOW_VALUE` after V16+V20. The announcement-window class is now `ALREADY_TESTED` / `EXHAUSTED`.

---

## Search space after V21

| Space | Status |
|---|---|
| A-share price CS (V13–V15) | `RESEARCH_SPACE_EXHAUSTED` |
| Annual / quarterly / balance ratios | `LOW_VALUE` |
| Industry RS; macro β; age/ST/calendar; industry×macro | `ALREADY_TESTED` |
| HS300/ZZ500 membership / reconstitution | `EXHAUSTED` |
| Dividend announce windows; dividend yield | `EXHAUSTED` / `LOW_VALUE` |
| Other A-share *filing windows* (forecast/express/unlock clones) | `LOW_VALUE` — same object as V21 |
| Event text / news / consensus surprise | `DATA_BLOCKED` ≠ no Alpha |
| LO/OG option surface | `PAYMENT_REQUIRED` ≠ no Alpha |
| MT5 GOLD/OIL/EURUSD/USDJPY owned features | `RESEARCH_SPACE_EXHAUSTED` |
| DXY/UST10/GOLD as A-share primary macros | `LOW_VALUE` without a new split |

A-share is **no longer the primary search universe**. It remains the only place with a Level-1 object (weak, one cluster, strategy books negative). That does not justify another free CS farm.

---

## Next unit of research resource

**Do not spend it on another A-share hypothesis.**

Expected information value of the remaining holes:

1. **Stay stopped** — highest *rational* use of the next unit. The free PIT surface that could change P(independent Candidate) is spent.
2. **LO option surface** — highest *theoretical* new class. Quoted. Do not auto-buy. P(Level-1) on the exhausted 4-name CFD book is still low-to-medium (V9/V10). Human purchase gate only.
3. **News / consensus / dated events** — high theoretical IV. `DATA_BLOCKED` or `PAYMENT_REQUIRED`. Not a silent BaoStock top-up.

Human gates (only these):

1. Stay stopped (default).
2. Later purchase decision for LO 1Y MVD-A (still not automatic).
3. Authorize a **new** information class that is not a re-expression of V13–V21 (not another ratio, membership, or filing window).

Not automatic: Final OOS, Paper, Live, Portfolio, Xavier, H11/H12 reopen, V22.

---

## Answers

| Question | Answer |
|---|---|
| V21 result? | NEW_CANDIDATE=0, STOP_B_FAMILY |
| Second independent Alpha? | **No** |
| Candidate count? | Still 2 (H11/H12) |
| A-share free information still worth farming? | **No** |
| Next executable family without purchase? | **None that is not LOW_VALUE** |
| Buy options / Tushare / Wind? | **NO** |
| Final OOS? | **DENIED** |

---

## Authority

- V21: `docs/research_engine/V21_DIVIDEND_DECISION.md`
- Machine: `data/market/research_engine/cn_a_share_div_v21/DECISION.json`
- Direction parent: `docs/research_engine/POST_V19_RESEARCH_DIRECTION_AUDIT.md`
- Prior global: `docs/research_engine/POST_V16_DECISION.md`
- Why NEW_INDEPENDENT=0: `docs/research_engine/POST_V21_CAPITAL_CONSTRUCTION_FORENSICS.md` (VERDICT A)
- Paid hole on paper: `docs/research_engine/POST_V21_PURCHASE_VALUE_CASE.md` (DO_NOT_BUY)
