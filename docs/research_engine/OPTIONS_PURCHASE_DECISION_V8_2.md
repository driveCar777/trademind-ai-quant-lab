# Options Purchase Decision V8.2

**This task: NO PURCHASE.** Even CASE A is quote-only.

Credits remaining ≈ **$93**. Floor **$60**. Auto-purchase max **$30**. Auto-purchase this mission: **false**.

Downloaded: **false**. This-mission USD: **0**.

---

## Case bucket (MVD-A / MVD-B only)

MVD-C is not a case. It is a veto ($35k–$211k).

### CASE A — MVD ≤ $30 (exists)

| Pack | USD | What it can attempt | What it does not prove |
|------|-----|---------------------|------------------------|
| 1Y LO MVD-A | 11.99 | Derived IV / skew / term on crude monthly if bars exist | Occupancy; official settle; OI |
| 1Y OG MVD-A | 14.99 | Same on gold monthly | Same |
| 1Y LO+weeklies MVD-A | 13.40 | Adds Friday weeklies | Mixes DTE; not pre-registered default |
| 1Y OG+weeklies MVD-A | 16.93 | Same | Same |
| 1Y LO MVD-B | 24.09 | Derived IV **plus official settle + OI** on crude 1Y | Gold; 1Y thin |
| 2Y LO MVD-A | 23.13 | Two years crude prices, no official settle | OI/settle |
| 2Y OG MVD-A | 24.89 | Two years gold prices, no official settle | OI/settle |
| 1Y OG+LO MVD-A | 26.99 | Both metals, one year, prices only | Official settle; OI; 1Y validation |

**Cheap is not sufficient.** CASE A means the invoice fits. It does **not** mean the surface is complete. `ohlcv-1d` silent strikes, parent UD spreads, and 1Y occupancy are still open.

Do **not** auto-buy 1Y OG+LO just because $26.99 ≤ $30.

### CASE B — $30–60

| Pack | USD |
|------|-----|
| OG 3Y MVD-A | 32.41 |
| LO 3Y MVD-A | 34.22 |
| LO 2Y MVD-B | 43.61 |
| OG+LO 2Y MVD-A | 48.01 |
| OG 1Y MVD-B | 55.79 |
| LO 3Y definition+statistics (no ohlcv) | 54.27 |

**Do not buy in this task.** If a human later wants 3Y one-commodity MVD-A, that is `HUMAN_PURCHASE_REQUIRED`.

### CASE C — > $60

| Pack | USD |
|------|-----|
| OG+LO 3Y MVD-A | 66.64 |
| LO 3Y MVD-B | 64.97 |
| OG 2Y MVD-B | 83.61 |
| OG+LO 1Y MVD-B | 79.88 |
| anything + bbo-1s | ≥ 35,000 |

Do not buy. Shrink horizon or drop statistics on gold before shrinking strikes/expiries. Do not destroy the research question to hit $30.

### CASE D — cannot complete the research

**Not this.** Definition + daily prices **can** support derived IV / skew / term **if** occupancy holds. GLBX simply does not ship venue IV. That is a model step, not a missing schema.

---

## Decision (this mission)

```
PURCHASE = FALSE
AUTO_PURCHASE = FALSE
STOP = HUMAN_PURCHASE_REQUIRED
CASE = A_EXISTS_BUT_CONDITIONAL
```

Reasons:

1. Task forbids spend.
2. Several CASE A invoices exist; none have occupancy proof.
3. 3Y useful single-name MVD-A is CASE B ($32–$34), same as V8.
4. MVD-C / MBO / MBP / $199 Standard are forbidden.
5. Do not rebuy GC/CL futures.

If a human later spends **one** CASE A row, prefer a pack that still matches the locked scope:

1. **2Y LO MVD-A $23.13** or **2Y OG MVD-A $24.89** — longer than 1Y, still ≤ $30, one commodity.
2. **1Y LO MVD-B $24.09** — only pack ≤ $30 with official settle + OI.
3. **1Y OG+LO MVD-A $26.99** — only dual-metal pack ≤ $30; thinnest history.

Do not buy weeklies first. Do not buy OG statistics in the same ticket as gold prices unless the human accepts CASE B.

---

## If bought later — what can be researched

Only the three DESIGN mechanisms in `OPTIONS_MVD_V8_2.md`:

1. IV − realized vol (realized from **owned** futures)
2. Skew (ATM / ±5 / ±10, monthly front)
3. Term (front vs second ATM IV)

Then: occupancy audit → contract → local 2000 → four Xavier → FDR. Still LEVEL=0 until Candidate.

Do not modify old contracts. Do not claim option alpha from a successful download.

---

## If not bought — next legal direction

- Stay LEVEL=0, CANDIDATE=0
- Do not reopen killed families (including GVZ/OVX, V8 TOP5, Pack E term structure)
- Do not retune gap / steepening / OI / wow / yield / z_cut
- Other remaining **new information** named in V6: dated macro surprise — still not authorized here
- Wait for a human to pick exactly one quote row

---

## HUMAN_PURCHASE_REQUIRED

A human may approve **one** row from `OPTION_QUOTE_V8_2.json` with `mvd` in `{MVD-A, MVD-B}` and `ok=true`.

Not approved: MVD-C, bbo-1s, mbo, mbp, trades-as-default, $199/month, Pack E again, `GC.OPT`/`CL.OPT`.
