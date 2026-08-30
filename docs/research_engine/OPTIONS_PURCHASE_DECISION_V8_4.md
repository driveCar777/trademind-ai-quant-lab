# Options Purchase Decision V8.4

This mission: **purchase = FALSE**. No download. $0.

Credits remain ≈ **$93**. Floor **$60**.

---

## Case

- **LO:** CASE **A** — 251/251 ATM, 251/251 skew, 98% term, longest ATM streak = full year.
- **OG:** CASE **B** — ATM 98.4% but term 74.9% (gate A is 75%) and term streaks only 22 days.
- **Not CASE D.**

---

## One preferred package (if a human later spends)

```
BUY LO 1Y MVD-A
$11.99
```

**Why:** It is the only metal that meets the locked sufficiency **A** on the full-year census. Cheaper than OG. Futures-front ≈ option-front 86% of days (still use ACTIVE_OPTION_MONTH).

**Contains:** `LO.OPT` `definition` + `ohlcv-1d`, 2025-08-29–2026-08-29.

**Does not contain:** bid/ask, official option settlement, OI, venue IV, gold, weeklies, ticks.

**Can research (after a later purchase → freeze → qualify → derive IV):** crude DERIVED ATM IV, IV−RV vs owned CL, skew eligibility, term eligibility.

**Cannot research:** mid IV, exchange IV, OG surface, official option settle.

Next steps if bought later (not this mission):

```
purchase → freeze → qualify → derive IV
```

---

## Why not OG $14.99

OG ATM is excellent for IV−RV, but this census’s job was to promote CASE B → A or D. OG stayed **B**. Term is the hole. Do not buy OG just because V8.3 preferred gold.

## Why not dual / MVD-B

Dual is not required to get a grade A surface. MVD-B does not fix occupancy.

---

## 16 answers

1. OG ATM coverage: **98.41%** (247/251)  
2. LO ATM coverage: **100%**  
3. OG skew eligibility: **80.08%**  
4. LO skew eligibility: **100%**  
5. OG term eligibility: **74.90%**  
6. LO term eligibility: **98.01%**  
7. Longest usable streak: OG ATM **118**; LO ATM/skew **251**; OG term **22**; LO term **139**  
8. Longest gap: OG ATM **1**; LO ATM **0**; OG term **4**; LO term **2**  
9. Front futures expiry = option front? OG **never** (0%). LO **85.7%**  
10. Active option month stable? As a **rotating calendar**, yes. Not one code.  
11. MVD-A enough? **LO yes** for eligibility. OG for ATM/IV−RV only.  
12. MVD-B necessary? **No**  
13. Worth buying later: **LO 1Y MVD-A**  
14. **$11.99**  
15. Only grade A on locked gates  
16. First research question if bought: **LO IV − realized vol** (RV from owned CL)

---

```
PURCHASE = NO
REASON = This mission does not spend. LO is data-sufficiency A and OG is B. If a human later buys one pack: LO 1Y MVD-A $11.99.
```
