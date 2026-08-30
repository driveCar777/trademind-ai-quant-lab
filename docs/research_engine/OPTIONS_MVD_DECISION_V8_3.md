# Options MVD Decision V8.3

**This mission did not purchase.** `timeseries.get_range` and `batch.submit_job` were not called.

Credits remaining ≈ **$93**. Floor **$60**.

---

## Case

```
CASE B
MVD likely researchable but occupancy unknown at 1Y census resolution
```

Not CASE A: 8 pre-registered dates ≠ 252 sessions. OG futures-front ATM rate is 0/8. OG term rate is 0/8.

Not CASE C: parent ohlcv-1d has 339,600 (OG) and 383,039 (LO) records in 1Y; LO sample ATM/skew/term are 8/8; OG live-month ATM is 8/8.

---

## Is MVD-A enough?

| Question | OG 1Y A $14.99 | LO 1Y A $11.99 |
|----------|----------------|----------------|
| DERIVED IV | YES on **live** option month (sample 8/8) | YES (8/8) |
| Skew | LIKELY (6/8 on live month) | YES (8/8) |
| Term | **NO** under locked futures front+second | YES (8/8) |

MVD-A is enough to **attempt IV−RV**. It is not enough to claim a complete OG surface or mid-market IV.

## Is MVD-B necessary?

**No** for attempting DERIVED IV. It adds official settle + OI. It does not add venue IV. It is not the reason to pick LO over OG.

---

## One preferred package (if a human later spends)

**OG 1Y MVD-A — $14.994811**

- Cost: $14.99, leaves the $60 floor intact
- Why: first question is gold IV−RV; sample says the live gold option month has ATM trades
- Research question: DESIGN IV−RV (not a family)
- Unlocks: derived ATM IV + IV−RV vs owned GC RV; likely skew
- Remains impossible: exchange IV, bid/ask mid, official option settle, proven OG term, 1Y daily census

Do not buy OG+LO $26.99 by default. Do not buy LO B $24.09 by default.

---

## 20 questions

1. OG exists? **YES** (`OG.OPT`)
2. LO exists? **YES** (`LO.OPT`)
3. Monthly vs weekly? Monthly = `OG.OPT` / `LO.OPT`. Weeklies = `OG1–4`, `LO1–4`, weekday roots. Phase-1 = monthly outright C/P only
4. Definition has strike? **YES**
5. Expiry? **YES** as a field; exact timestamp UNKNOWN until bytes
6. C/P? **YES**
7. Historical OHLCV usable? **YES in aggregate** (339k / 383k 1Y bars). Per contract: see sample
8. ATM occupancy proved? **Sample YES** on OG live month and all LO. **Sample NO** on OG futures-front. Full year: not censused
9. OTM occupancy? LO sample strong; OG live month 0.50–0.75
10. Front/second same day? LO **8/8**. OG **0/8**
11. Skew constructable? LO YES (sample). OG live month 6/8
12. Term constructable? LO YES (sample). OG **NO** under locked mapping
13. IV derived? **YES if a bar exists**
14. Model? **Black-76**
15. Model risk? American, last-trade, settle mismatch, DGS10 proxy — see limitations file
16. MVD-A enough? For IV−RV: **likely**. For OG term: **no**
17. MVD-B necessary? **No**
18. Most worth buying later? **OG 1Y MVD-A**
19. Price? **$14.99**
20. Buy now? **NO**

---

## DESIGN_ONLY (not a family)

1. IV−RV  
2. Skew  
3. Term (LO sample-feasible; OG not)

---

```
PURCHASE = NO
REASON = CASE B: 8-date sample is not a 1Y census; OG futures-front ATM is 0/8; OG term is 0/8; MVD-A has no bid/ask and no official settle. This mission does not spend. If a human later accepts CASE B, the single package is OG 1Y MVD-A $14.99 for IV-RV on the live option month.
```
