# Options MVD Purchase Ranking V8.3

This task does **not** buy. Ranking is for a later human ticket.

ATM / OTM / term evidence is the **8-date sample** in `OPTIONS_FEASIBILITY_V8_3.md`.

---

## Rank 1 — OG 1Y MVD-A — $14.99

`OG.OPT` definition + ohlcv-1d, 2025-08-29–2026-08-29.

**Why first:** The first research question is gold IV−RV. Sample ATM on the **live** gold option month (futures second) is 8/8. Owned GC futures already give RV. Do not auto-buy OG+LO just because $26.99 ≤ $30.

**Unlocks:** DERIVED ATM IV on that live month; IV−RV; likely skew (6/8).

**Still impossible:** venue IV; mid IV; official option settle; OG term under futures front+second (0/8); 252-day census.

---

## Rank 2 — LO 1Y MVD-A — $11.99

Stronger sample: ATM/skew/term all 8/8 on front and second.

**Not rank 1** because the priority rule is: if OG 1Y A can attempt IV−RV, prefer OG. It can.

---

## Rank 3 — LO 1Y MVD-B — $24.09

Adds official settlement + OI. Not auto-preferred. Settlement/OI are not the missing piece for IV−RV; occupancy of a **price** is.

---

## Rank 4 — OG+LO 1Y MVD-A — $26.99

Do not buy dual by default.

---

## Not ranked

MVD-C / bbo-1s / MBO / MBP / $199 Standard / Pack E again / weeklies as phase-1.
