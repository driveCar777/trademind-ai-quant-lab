# LEVERAGE_STRESS_TEST

> 2026-09-13. Economic exposure 1×–100× on **real** Ava GOLD path.  
> Live leverage field = **400**. Contract size = **100**. Not a Candidate.

## Method

Apply a constant economic-exposure multiple `k` to the RESEARCH daily gold close path (2019-02-26→2025-09-11, +173% price, MaxDD **−21.4%**, monthly median **+1.11%**, worst month **−7.33%**, **0 / 79** months ≥ +20%).

Account approximation: `r_acct ≈ k × r_price` until ruin (`equity ≤ 0`). Costs ignored here so the table is an **upper bound**. Real 34-point spread + long swap make leveraged paths worse.

`k=1` = unlevered gold (own money ≈ notional).  
`k=18` ≈ the multiple that turns the **median** month into +20%.  
`k=100` = “only 100× will print 20% in a quiet month.”

## Stress table

| k | Name | Median month | Worst month | Path MaxDD | Hit +20% month? | Account after −21.4% path DD |
|---|------|--------------|-------------|------------|-----------------|------------------------------|
| 1 | unlevered | +1.1% | −7.3% | −21% | No | Survives |
| 2 | modest | +2.2% | −15% | −43% | No | Survives |
| 4 | aggressive | +4.4% | −29% | −86% | No | Barely / ruin risk |
| 8 | very aggressive | +8.9% | −59% | **ruin** | Rare | Ruin on 2022 path |
| 18 | “median→20%” | +20% | **−132%** | ruin | By construction on median only | **Ruin** |
| 50 | wish | +56% | ruin | ruin | Some months | Ruin |
| 100 | 100× | +111% | ruin | ruin | Quiet months still <20% if gold is flat | **UNSAFE** |

A 0.5% gold month at 100× is +50% — and a −2% two-day dump is −200% theoretical. The 2022 RESEARCH drawdown at 5× already exceeds −100%.

## Classification

| k | Class |
|---|--------|
| 1–2 | **SAFE** relative to gold’s own −21% DD (you still eat gold beta) |
| 4 | **AGGRESSIVE** |
| 8+ | **UNSAFE** (path DD kills) |
| 18 needed for median-month 20% | **UNSAFE** |
| 100× only to hit 20% in a quiet month | **UNSAFE** |

Broker **400×** is a ceiling, not a target. Using it to manufacture 20%/month is the same as choosing k≫8.

## Case

This is **Case C** in `TARGET_20PCT_MONTH.md`: 20% monthly is **UNSUPPORTED**. The stress does not create a Candidate.
