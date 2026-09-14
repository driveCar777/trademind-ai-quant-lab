# MT5 Return-Target Reality Check

**Date:** 2026-09-14  
**Object:** 20% **per month** as an **investment objective**, never as an optimizer target.  
**Evidence:** already published — `docs/research_engine/TARGET_20PCT_MONTH.md`, `LEVERAGE_AND_RISK.md`, `LEVERAGE_STRESS_TEST.md`, `data/market/research_engine/phase2/results/d1_baselines/BUY_HOLD_PATH.json`. No new path computed this session.

```
TARGET MONTHLY RETURN: 20%+
TARGET STATUS: UNSUPPORTED
BROKER LEVERAGE: 400x
CANDIDATE: FALSE
```

---

## 1. 20% monthly is not a normal target

Compounded:

\[
(1.20)^{12} - 1 \approx 7.916 \approx \mathbf{791.6\%\ annualized}.
\]

That is hedge-fund-advertising arithmetic, not the center of a liquid gold CFD. Gold RESEARCH (2019-02-26 → 2025-09-11, daily close path):

| Stat | Value | Source |
|------|-------|--------|
| Path TWR | **+173%** | `BUY_HOLD_PATH.json` |
| CAGR | **13.2%** | same |
| Path MaxDD | **−21.4%** (2022-10-20) | same |
| Months | **79** | `TARGET_20PCT_MONTH.md` |
| Median month | **+1.11%** | same |
| Mean month | +1.38% | same |
| Worst month | **−7.33%** | same |
| Best month | **+10.7%** | same |
| Months ≥ +10% | **1 / 79** (1.3%) | same |
| Months ≥ +20% | **0 / 79** | same |

Phase 1 full sample to 2026-09-11 (already published, not Phase 2 official): buy-hold about **+250%**, CAGR about **17.5%**, still **0** months ≥20%.

**Supported monthly center from this distribution:** about **1%** median, about **13%** CAGR. 3% happens; 5–8% is the right tail; 12% was not a habit; **20% was not observed**.

| Case | Meaning | This project |
|------|---------|--------------|
| A SUPPORTED | Repeatable net edge that carries 20%/month at safe economic exposure | **No** |
| B POSSIBLE_BUT_UNPROVEN | Real edge above gold beta; 20% needs aggressive but non-ruinous size | **No** — no proven incremental alpha |
| **C UNSUPPORTED** | 20% needs leverage that dies on the observed path, or there is no edge | **Yes** |

---

## 2. Leverage cannot manufacture the target

**Account leverage ≠ strategy risk budget.** Ava demo `ACCOUNT_LEVERAGE=400` (`AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json`) is the **margin multiplier**. It does not change E(net | signal). It does not turn 13% gold CAGR into 791% without scaling the **same path**, including the **−21.4%** drawdown, 34-point spread, 2 bp/side assumed slip, and long swap **−1.54 / night / 1.00 lot**.

False arithmetic: “13% × 400 ≈ huge monthly.”  
True arithmetic: account ≈ (notional / equity) × gold return − costs.

From `LEVERAGE_AND_RISK.md` (snapshot prices ~4349):

- 1.00 lot notional ≈ **$434,900**; margin at 400× ≈ **$1,087**
- 0.01 lot ≈ **$4,349** notional ≈ **$11** margin
- At **$11,785** equity, one 0.01 lot ≈ **0.37×** economic exposure; a +1.11% gold month ≈ **+0.4%** account before swap/spread
- Turning the **median** gold month into +20% account needs about **18×** economic exposure (~0.5 lot on that equity)

`LEVERAGE_STRESS_TEST.md` applies constant k to the **real** RESEARCH path (costs ignored ⇒ **upper bound**):

| k | Median month | Worst month | Path MaxDD | +20% month? | On −21.4% path |
|---|--------------|-------------|------------|-------------|----------------|
| 1 | +1.1% | −7.3% | −21% | No | Survives |
| 4 | +4.4% | −29% | −86% | No | Ruin risk |
| 8 | +8.9% | −59% | ruin | Rare | Ruin on 2022 |
| **18** | +20% by construction on the median | **−132%** | ruin | Median only | **Ruin** |
| 100 | +111% | ruin | ruin | Quiet months still miss if gold is flat | **UNSAFE** |

**Do not over-leverage to hit 20%.** Broker 400× is a **ceiling**, not a target. 100×-to-hit-20% is **UNSAFE**. This file does not recommend any k>1.

Phase 2 C13 exists so that 20%/month **cannot** be an optimizer or a retune excuse (252 / hold / λ / k / ATR / RSI / SMA / TF / slip).

---

## 3. What genuine alpha would be required

Let \(r_g\) be gold’s month and \(r_a\) incremental **net** alpha (after spread, slip, swap, not leverage).

Account month ≈ \(k \times (r_g + r_a)\) until ruin.

To print **+20%** in a **typical** month without k≈18:

- If you only have gold beta (\(r_a \approx 0\)): you need **k≈18** → ruin on the observed −21.4% path.
- If you want k=1 (unlevered): you need a **typical month ≈ +20%** in the **account**, i.e. an alpha engine whose monthly center is ~20%, not 1.11%. That object **does not exist** in this repo.
- If you want k=2 (still aggressive vs a −21% gold DD): you still need a typical **(gold+alpha)** month ≈ +10%. Gold’s **best** RESEARCH month was **+10.7%**, and that happened **once**. Alpha would have to be a **new**, persistent distribution, not a bull-window TWR.

Active books already measured:

| Book | RESEARCH net | Implication for 20% |
|------|----------------|---------------------|
| BUY_HOLD | +171% TWR, CAGR **13.1%** | Beta. Still 0/79 months ≥20%. |
| ALWAYS_LONG 20d | +161% | Same beta, more cost. |
| EXP-001 Linear | +64%, CAGR **7.6%** | **Worse** than beta; still needs ~15×+ and still loses to BUY_HOLD. |
| H1 ALWAYS_LONG | **−30%** | More trading **destroys** the 20% story. |
| V4 TSMOM | Research **−10%**, val +84% on the bull | Not a 20% engine. |

**Genuine alpha** here means: a pre-registered net book whose OOS increment versus BUY_HOLD is positive and not a single-period artifact. That increment has **not** been shown. Without it, 20%/month is a wish applied to gold beta.

---

## 4. Maximum reasonable drawdown (descriptive, not a recipe)

Gold already delivered **−21.4%** unlevered on the official RESEARCH path. That is the **minimum** historical DD any long-gold book must accept unless it has a **proven** sit-out that still beats BUY_HOLD (none does).

| Economic exposure k | Implied path DD on −21.4% | Class (`LEVERAGE_STRESS_TEST.md`) |
|---------------------|---------------------------|-----------------------------------|
| 1 | ≈ −21% | Relatively survivable vs gold’s own history |
| 2 | ≈ −43% | Still gold beta, painful |
| 4 | ≈ −86% | AGGRESSIVE |
| ≥8 | ruin on 2022 | UNSAFE |

A “max reasonable DD” for a **research Candidate** is not a number this lab is authorized to pick for live size. What can be said: **if the edge is only gold beta, DD of order −20% is already in the data; levering it to chase 20% months is how the account dies.** Tight stops on the V4 path **cut** TWR (BE3: +52% → +14%); they are not a 20% machine.

---

## 5. If the edge is weak, 20% monthly is unrealistic

Phase 2 lock:

- **STRATEGY EDGE: NOT PROVEN**
- **INCREMENTAL ALPHA VS GOLD BUY-HOLD: NOT PROVEN** (`NO_INCREMENTAL_ALPHA`: Linear +64% vs BUY_HOLD +171%)
- **ECONOMIC EDGE: WEAK** (drift is real; it is beta)

Therefore:

- You **cannot** get 791% annualized from a 13% beta without ruinous k.
- You **cannot** get it from Linear 7.6% CAGR.
- You **cannot** get it from H1 always-in (net negative).
- You **cannot** get it by retuning RSI/SMA/ORB or opening Logistic because Linear beat Naive on a bull slice.

**TARGET STATUS: UNSUPPORTED.** Do not prove 20%. Do not optimize for 20%. Do not advise 400× as a plan.

---

## 6. Beta vs alpha vs “high return” books

A high TWR on this sample is **usually**:

\[
\text{book} \approx \underbrace{\text{long gold}}_{\beta} + \underbrace{\text{2024–26 bull window}}_{\text{regime}} + \underbrace{k}_{\text{leverage}} - \text{costs} - \text{shorts}.
\]

That is **not** alpha. V4 validation +84% and Linear `research_30` +61% sit in the same bull. Research-window V4 **−10%**. Always-short **−71%**.

See `AUDIT/MT5_PHASE3_ALPHA_DISCOVERY_PLAN.md` §5.

---

## Pointers

- Plan: `AUDIT/MT5_PHASE3_ALPHA_DISCOVERY_PLAN.md`
- Case File §14–§15: `AUDIT/MT5_STRATEGY_CASE_FILE.md`
- Phase 2 Q8: `AUDIT/PHASE2_FINAL_REPORT.md`
