# Options Research Sufficiency V8.4

**Not an alpha gate.** This is DATA SUFFICIENCY only. LEVEL stays 0.

Gates were locked **before** the census was read:

| Grade | ATM | Skew | Term |
|-------|-----|------|------|
| **A** | ≥ 90% | ≥ 75% | ≥ 75% |
| **B** | ≥ 75% | ≥ 60% | ≥ 60% |
| **C** | ATM ≥ 40% but not A/B | | |
| **D** | ATM < 40% | | |

---

## Scores (251 Pack E sessions)

| Metal | ATM | Skew | Term | Grade |
|-------|-----|------|------|-------|
| OG | 98.41% | 80.08% | **74.90%** | **B** |
| LO | 100% | 100% | 98.01% | **A** |

OG misses **A** only on term (74.90% vs 75.00%). That is 188/251 vs 189/251 — one day. Consecutive term is still only 22 days, so it is not “almost A” in a stability sense.

LO meets A with no ATM/skew holes and term holes of at most 2 days.

---

## What MVD-A is enough for

**LO 1Y MVD-A:** enough to **attempt** a daily ATM IV series, a daily skew eligibility series, and a near-daily term eligibility series. Still last-trade IV, not mid, not official settle, not venue IV.

**OG 1Y MVD-A:** enough to **attempt** ATM IV−RV (98.4% ATM, max gap 1 day). Skew usable most days. Term **not** grade A and is bursty.

**MVD-B** is **not** required for this coverage result. It would add official settle + OI, not occupancy.

---

## Limitations (even if grade A)

- no bid/ask  
- no official option settlement  
- no OI  
- DERIVED Black-76, American residual  
- parent bytes include spreads/UD  
- exact option expiry UNKNOWN until definition is bought  

---

## Ranking (do not buy this mission)

1. **LO 1Y MVD-A $11.99** — only grade A  
2. OG 1Y MVD-A $14.99 — grade B; ATM/IV−RV strong; term short  
3. LO 1Y MVD-B $24.09 — not needed for coverage  
4. OG+LO 1Y MVD-A $26.99 — do not auto-buy dual  
