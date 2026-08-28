# Research Opportunity Ranking V1

Produced by `scripts/research_engine_alpha_pipeline.py`  
`content_hash` = `1b2e65b3e9bdf9a03033bcd34f479ee9a7231037b6ee431b8fd49d08a9290bd6`  
V0.8 hash untouched. V0.9 hash untouched. Final OOS not read. Xavier not used.

Score = Economic plausibility × Data × Uniqueness × Cost survivability × Testability.  
Competition enters as crowding (5 = saturated → uniqueness 1).

---

## Re-evaluation (not “pick V0.9 by habit”)

Contract-eligible **clusters**:

| rank | cluster | best question | score | action |
| ---: | --- | --- | ---: | --- |
| 1 | REGIME_TRANSITION | RB-0047 | 1600 | **Keep V0.9.** Highest after a 52-question pass. |
| 2 | RESIDUAL | RB-0009 | 576 | Second family. Different mechanism. |
| 3 | CALENDAR | RB-0005 | 540 | Third. Thinner n. |
| — | RISK_4A / PORTFOLIO | RB-0030 / 0042 | 384 | No sleeve. Not a first contract. |
| — | Multi-asset XA-style | — | 0 | Killed as V0.8 isomorph. |

V0.9 remains #1. It is not automatically #1 because it already had a filename. It won because Δstate is untested, data-complete, sparse enough to survive cost, and has a two-target gate (RB-0047).

---

## TOP 20 questions (implementable list, raw)

1. RB-0047 1600 — both targets must speak if the story is a risk book  
2. RB-0001 1280 — vol-shock energy de-lever  
3. RB-0002 1280 — ignition delay  
4. RB-0003 1280 — strength death  
5. RB-0052 1250 — stop rule (meta, not a contract)  
6. RB-0048 800 — Sunday clock (meta)  
7. RB-0033 960 — vol-exit oil (SHELF, not 4th id)  
8. RB-0034 960 — down ignition (SHELF)  
9. RB-0043 — walk-forward diagnostic (meta)  
10. RB-0009 576 — gold/oil residual  
11. RB-0004 720 — haven on shock (SHELF)  
12. RB-0005 540 — weekend dump  
13. RB-0035 720 — FX ignition (outside V0.9 lock)  
14. RB-0010 324 — gold/FX residual  
15. RB-0040 324 — slow dollar residual  
16. RB-0012 384 — holiday-skip auction  
17. RB-0030 384 — 4A on a living sleeve  
18. RB-0039 384 — post-gap fade  
19. RB-0042 384 — two-sleeve book  
20. RB-0006 360 — Friday flatten  

(Exact order of mid-list is in `RANKING_V1.json` `top20_ids`.)

---

## Why the top money questions can exist / be missed / be tested

**RB-0047 / 0001–0003 (transition)**  
Why money: budgets and stops are discrete.  
Why missed here: V0.5 measured *level*, not *change*. Industry often does the same.  
Why testable now: D1 6.4y, locked state recipe, cost engine, two targets.

**RB-0009 (residual)**  
Why money: one factor, two prices; warehouses fade the leftover.  
Why missed: V0.8 tested a *different* leftover (next-day dollar). Same-bar gold/USD corr fooled the eye.  
Why testable now: two D1 series, inner join, no DXY required.

**RB-0005 (weekend)**  
Why money: humans close books before Saturday.  
Why missed: too “dumb”; or overfit with 20 weekday dummies.  
Why testable now: Sunday D1 bars are FACT. Must keep n tiny.

---

## Decision

Top three **contracts**: V0.9 (keep hash) + residual V0.91 (new) + calendar (paper, later).  
Do not run residual while V0.9 is unrun. One family at a time.

## Next automatic task

Write the three contract designs. Do not execute V0.9 jobs.
