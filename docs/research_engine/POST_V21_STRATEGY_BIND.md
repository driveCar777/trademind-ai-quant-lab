# Post-V21 Strategy Bind — W4

**Date:** 2026-09-04  
**Read-only** on `cn_a_share_strategy_v14/H11|H12/TRADES.csv`. No retune. No new book.  
**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/STRATEGY_BIND.json`  
**Script:** `research_engine/post_v21_w4_bind.py`

This file binds the strategy layer to numbers so nobody has to re-argue it. The user's goal is money. The honest statement is: **the only strategy we own loses money after cost, and would make about 3%/yr before cost.** Nothing here can be tuned into 10%.

---

## 1. Why the existing Strategy cannot enter Paper (V14.1 numbers)

| Item | H11 | H12 |
|---|---|---|
| Official non-overlap book, 172 periods 2010-01 → 2024-02 | **−16.58%** total (grid) / −15.61% (daily MTM) | **−11.65%** |
| CAGR | −1.27% | −0.87% |
| MaxDD (daily MTM official) | **−66.46%** (2015-06-12 → 2018-10-18, no recovery) | ≈ −66% |
| Worst single period | −23.65% (signal 2015-06-15, −422,657 yuan) | — |
| Validation-only continuation (30 periods) | −5.75% total, CAGR −2.36%, MaxDD −15.6% | — |
| Validation fresh MTM (V14) | +0.31% total, CAGR +0.12% | +0.74% |

Cost decomposition H11, whole path (yuan on a 1,000,000 book):

```
gross            +337,128
fees+stamp       −215,501
slippage         −287,424
net              −165,797
cost / gross     = 1.49
```

Costs are 149% of gross. But the more important line is the **zero-cost counterfactual** (diagnostic, not a strategy): compound the gross returns with no fees or slippage at all → **+50.3% total, CAGR +2.91%, MaxDD −58.4%**. Even a free-trading H11 is a 3%/yr book with a −58% drawdown. The gap to 10% is not fees. It is information.

Paper is a step toward capital. Putting capital on a book whose official path is negative, whose best-case-free path is 3%, and whose drawdown is two-thirds of the account, is not a research step. It is a loss with extra steps. **Paper = NO.**

## 2. Admission checklist for a second Strategy

All required; none waivable:

1. New information object (W2: none on disk; two candidates that are not on disk are ratios and need a login that is locked).
2. Pre-registered contract, ≤ 3 hypotheses, dual books, BH-FDR.
3. Validation MEAN_FORWARD > 0 **and** validation non-overlap capital > 0 after `A_SHARE_STRATEGY_COST_MODEL_V1`.
4. Capital correlation vs H11/H12 ≤ 0.9 (W1: five "beat-EW" IDs failed this; the eight that passed it still failed item 3).
5. Reproduction contract written before any Final OOS discussion. Final OOS stays DENIED until separately unlocked.

## 3. Only legal action with NEW_INDEPENDENT = 0

**KEEP_LOW_PRIORITY** for H11/H12. No optimization. No Long Validation. No Portfolio. No Paper.

### If a second sleeve ever exists — the portfolio *contract* (text only, no backtest now)

```
PORTFOLIO_CONTRACT_V0 (draft, inactive)
  sleeves          : exactly two, each with its own non-overlap capital book
  admission        : each sleeve passes items 1-5 above independently
  independence     : capital corr(sleeve_A, sleeve_B) <= 0.9 on the shared validation window
  weights          : fixed 50/50 notional, pre-registered; no optimization on returns
  rebalance        : at each sleeve's own 20d grid; no cross-sleeve netting
  cost             : A_SHARE_STRATEGY_COST_MODEL_V1 per sleeve, unchanged
  leverage         : 1.0x; cash residual on unfilled
  gate             : portfolio val capital > 0 AND portfolio MaxDD reported; 10% not a gate
  forbidden        : H11+H12 as the two sleeves (corr 0.996); reweighting after seeing results
```

W4 diagnostic already shows why H11+H12 is not a portfolio: a 50/50 blend compounds to **−14.08%** (vs −16.58% for H11 alone), MaxDD −63.7%. Corr 0.996. Two labels, one sleeve.

## 4. Forbidden list (strategy layer)

- Retune lookback / hold / quantile / sign toward 10%
- Leverage the −66% path
- H11 + H12 as two sleeves
- Lower cost model or slippage assumptions
- Report overlapping MEAN_FORWARD as CAGR
- Paper / Live / `order_send` on a negative book
- Open Final OOS

## 5. The money question, answered plainly

Can this system make the user rich right now? **No.** It owns one weak, negative-after-cost book. The research system is working correctly by refusing to trade it. The path to money is a second independent, positive, post-cost book — and that requires information the free disk does not contain. That is a purchase question (W5), recorded in a file, not asked in chat.

Next: W5.
