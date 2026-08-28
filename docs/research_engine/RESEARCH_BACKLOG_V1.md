# Research Backlog V1

52 economic questions. Not 52 indicators.  
Authoritative scored copy: `data/market/research_engine/alpha_program/RESEARCH_BACKLOG_V1.json`  
Source: `research_engine/alpha_program/backlog_data.py`  
Score = E × D × (6−crowding) × C × T. Blocked or killed isomorph → 0.

Priority here is the **pre-registered integer score**, not a feeling after this sentence.

---

## How to read a row

- **Mechanism** — the transfer or constraint.  
- **Why exists** — who is forced to trade.  
- **Required data** — HAVE or BLOCKED.  
- **Expected failure** — how this dies honestly.  
- **Priority** — pipeline score (0 = do not implement).

---

## RB-0001 — Vol-shock de-lever of energy

**Mechanism:** Risk books cut energy after a realized vol jump; selling continues several days.  
**Why exists:** VaR/vol targets are discrete.  
**Required data:** OIL D1 + V0.5 VOL freeze. HAVE.  
**Expected failure:** 2020-only, or = always-short oil.  
**Priority:** 1280. In V0.9 as HYP-RT-0001.

## RB-0002 — Delayed trend capital on ignition

**Mechanism:** CTA/risk-on capital enters after strength *ignites*, not every in-trend bar.  
**Why exists:** Committees and confirmation lags.  
**Required data:** GOLD D1 + SMA20/50 + ADX14. HAVE.  
**Expected failure:** Occupancy looks like TREND_STRONG (V0.6).  
**Priority:** 1280. V0.9 HYP-RT-0002.

## RB-0003 — Clustered de-risk on strength death

**Mechanism:** Levered longs exit when strength dies.  
**Why exists:** Stops fire at the change.  
**Required data:** GOLD D1 + ADX14. HAVE.  
**Expected failure:** Unconditional gold short.  
**Priority:** 1280. V0.9 HYP-RT-0003.

## RB-0004 — Haven bid on the same shock

**Mechanism:** Gold bought as insurance while oil is dumped.  
**Why exists:** Different books, same clock.  
**Required data:** GOLD D1. HAVE.  
**Expected failure:** Conflicts with 0001 in one m; gold bull path.  
**Priority:** 720. SHELF. Not a 4th V0.9 id.

## RB-0005 — Weekend information dump

**Mechanism:** Weekend news and inventory square is priced on Sunday/Monday D1.  
**Why exists:** Human week.  
**Required data:** D1 timestamps; Sunday bars exist. HAVE.  
**Expected failure:** Thin events; path.  
**Priority:** 540. Calendar family seed.

## RB-0006 — Friday flatten

**Mechanism:** Dealers refuse weekend inventory on Friday.  
**Why exists:** Balance-sheet weekend.  
**Required data:** D1 weekday. HAVE.  
**Expected failure:** Twin of 0005 (multiple testing).  
**Priority:** 360.

## RB-0007 — Month-end rebalance

**Mechanism:** Benchmark matching moves gold/FX at month-end.  
**Why exists:** Public calendar constraint.  
**Required data:** D1. HAVE.  
**Expected failure:** ~77 events, weak power.  
**Priority:** 240.

## RB-0008 — Quarter-end dressing

**Mechanism:** Reporting dates bind harder than month-end.  
**Why exists:** Official close.  
**Required data:** D1. HAVE.  
**Expected failure:** ~25 events.  
**Priority:** 240.

## RB-0009 — Gold/oil slow residual fade

**Mechanism:** log(GOLD/OIL) minus a slow center mean-reverts after extremes.  
**Why exists:** One macro factor, two real assets; inventory pulls the spread.  
**Required data:** GOLD+OIL D1 join. HAVE.  
**Expected failure:** Inflation-tape only; or V0.8 in costume.  
**Priority:** 576. **#2 contract cluster.**

## RB-0010 — Gold vs frozen FX-basket residual

**Mechanism:** Slow dollar gap in gold, not next-day Q3.  
**Why exists:** Gold is a dollar price.  
**Required data:** Align pack. HAVE.  
**Expected failure:** Decision 043 lookalike.  
**Priority:** 324.

## RB-0011 — Residual after a correlation spike

**Mechanism:** In stress, betas → 1; the leftover is what desks still hold.  
**Why exists:** Forced common-factor hedging.  
**Required data:** Align pack. HAVE.  
**Expected failure:** Trading same-bar corr (V0.8 trap).  
**Priority:** 324.

## RB-0012 — Holiday-Friday skip catch-up

**Mechanism:** Missing Friday is an information hole; next aligned row is an auction.  
**Why exists:** Broker holiday calendar (FACT in XA audit).  
**Required data:** Skip lists. HAVE.  
**Expected failure:** n tiny.  
**Priority:** 384.

## RB-0013 — Wide spread as rationing

**Mechanism:** Dealers widen to refuse risk, not to predict direction.  
**Required data:** spread. HAVE.  
**Expected failure / Priority:** Already killed as direction (FD) and as profit (DEF). **0.**

## RB-0014 — Tick drought then a gap

**Mechanism:** Thin tape jumps when the next informed order arrives.  
**Required data:** tick_volume only.  
**Priority:** 0 (FD + no real_volume).

## RB-0015 — Interest-rate carry

**Mechanism:** Rate differential is a transfer to the holder.  
**Required data:** rates/swap. **BLOCKED.**  
**Priority:** 0.

## RB-0016 — Variance risk premium

**Mechanism:** Insurance demand keeps IV above later RV.  
**Required data:** IV. **BLOCKED.**  
**Priority:** 0.

## RB-0017 — CPI/NFP clock premium

**Mechanism:** Uncertainty is sold until a scheduled print.  
**Required data:** event file. **BLOCKED.**  
**Priority:** 0.

## RB-0018 — EIA inventory lag

**Mechanism:** Physical quantity updates paper with a delay.  
**Required data:** EIA table. **BLOCKED.**  
**Priority:** 0.

## RB-0019 — London/NY session transfer

**Mechanism:** Human hours still clear inventory.  
**Required data:** long M15. **BLOCKED** as primary.  
**Priority:** 0.

## RB-0020 — True order-flow imbalance

**Mechanism:** Someone must take the other side of size.  
**Required data:** DOM / real_volume. **BLOCKED.**  
**Priority:** 0.

## RB-0021 — Residual after a joint crash day

**Mechanism:** Common shock plus an idiosyncratic leftover.  
**Required data:** GOLD+OIL join. HAVE.  
**Expected failure:** Two-leg costs.  
**Priority:** 288.

## RB-0022 — Disagreeing dollar proxies as a skip filter

**Mechanism:** Do not trade gold on a noisy-dollar day.  
**Priority:** 0 (becomes XA-0004).

## RB-0023 — Second-asset confirmed breakout

**Mechanism:** Stops cluster on one chart, not two.  
**Priority:** 0 (Donchian with extra steps).

## RB-0024 — Short streak continuation

**Mechanism:** Tiny under-reaction.  
**Priority:** 0 (HYP-0001).

## RB-0025 — Fade a short-window extreme

**Mechanism:** Dealers lean against inventory they just took.  
**Priority:** 0 (V0.6 MR / FD).

## RB-0026 — Stop cascade after a range high

**Mechanism:** Stops sit above the range.  
**Priority:** 0 (V0.6 TF-BRK20).

## RB-0027 — Permission while in TREND_STRONG

**Mechanism:** State as a hall pass.  
**Priority:** 0 (level filter).

## RB-0028 — Skipping HIGH_VOL is the return

**Mechanism:** Insurance by not playing.  
**Priority:** 0 (DEF 0 return).

## RB-0029 — Equal-weight three weak same-symbol sleeves

**Mechanism:** Independent errors cancel.  
**Priority:** 0 (they were the same error).

## RB-0030 — Vol-target a living sleeve

**Mechanism:** PMs allocate risk units.  
**Required data:** a Level 1 curve. MISSING.  
**Priority:** 384. Blocked by sleeve, not by prices.

## RB-0031 / RB-0032 — Buy-and-hold gold / oil

**Mechanism:** Scarcity / consumption premium.  
**Priority:** scored but **meta**. PATH_BENCHMARK only. Not Candidate.

## RB-0033 — Vol leaving HIGH, oil risk-on

**Mechanism:** Inverse of 0001: budgets reopen.  
**Priority:** 960. SHELF. Not 4th V0.9 id.

## RB-0034 — Down-trend ignition

**Mechanism:** Symmetric to 0002.  
**Priority:** 960. SHELF.

## RB-0035 — FX trend ignition

**Mechanism:** Same delay on G10.  
**Priority:** 720. Outside locked V0.9 universe.

## RB-0036 — Tiny locked nonlinear state machine

**Mechanism:** Interactions can be real.  
**Priority:** 144. After linear Δstate.

## RB-0037 — Dated LLM macro text

**Mechanism:** Language carries a constraint.  
**Priority:** 0 (no dated corpus).

## RB-0038 — Oil curve roll premium

**Mechanism:** Hedgers pay along the curve.  
**Priority:** 0 (no curve).

## RB-0039 — Post-closure overshoot fade

**Mechanism:** First auction after a 3-day gap is noisy.  
**Required data:** gap list (max gap 3 — FACT).  
**Priority:** 384.

## RB-0040 — Slow agreed-dollar residual in gold

**Mechanism:** Multi-day dollar factor, not Q3 next day.  
**Priority:** 324. Residual family, not XA retune.

## RB-0041 — London-fix then NY trend (intraday)

**Priority:** 0 (M15 too short).

## RB-0042 — Two uncorrelated Level 1 sleeves

**Mechanism:** Independent premia add.  
**Priority:** 384. No inputs yet.

## RB-0043 — Walk-forward as decay test

**Mechanism:** Markets adapt.  
**Priority:** meta diagnostic after Level 1.

## RB-0044 — Funding stress → commodity de-lever

**Priority:** 0 (no TED/OIS).

## RB-0045 — Tight-spread one-way gold then fade

**Priority:** 0 (FD spread-low).

## RB-0046 — Oil crash bounce as inventory dump

**Mechanism:** Physical prints once, paper overshoots.  
**Expected failure:** one crash.  
**Priority:** 120. Weak. Do not promote.

## RB-0047 — Cross-target test of the risk-budget story

**Mechanism:** Risk desks cut *books*, not one ticker. GOLD and OIL must both speak.  
**Why exists:** This is the V0.9 program gate, as a question.  
**Required data:** GOLD+OIL D1. HAVE.  
**Expected failure:** gold-only = WEAK_EDGE.  
**Priority:** 1600. Highest implementable question.

## RB-0048 — Sunday D1 is its own session

**Mechanism:** Weekend news must not be shifted to Monday.  
**Priority:** meta clock rule, not an alpha id.

## RB-0049 / RB-0050 — Cheapen cost / scan hold after a fail

**Mechanism:** None. These are cheat patterns.  
**Priority:** 0. Refuse the job.

## RB-0051 — Residual ∩ vol-transition

**Mechanism:** Shock plus a mis-relative price.  
**Priority:** 288. Only after both parents exist.

## RB-0052 — Stop if all implementable UNKNOWNs die

**Mechanism:** Negative knowledge.  
**Priority:** meta. Legal Condition B.

---

## Decision

52 questions exist and were scored by a running program.  
Killed/blocked are in the file so they cannot be “forgotten” into a new RSI.

## Next automatic task

Rank live questions and pick three contract clusters.
