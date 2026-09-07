# A-share Alpha V2 Contract

Write-once before ranking. See `research_engine/cn_a_share_alpha_v2/contract.py`.

- Contract hash: `a40aece085206fc4472edbc0431513ec43d66fd5bad79800db6c9dd9ea131d5c`
- Dataset: `tm-ashare-EQUITY-D1-20260830-000002`
- Hash: `dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80`
- 9 pre-registered hypotheses. No tenth. No H11/H12 reopen. No H13.
- Signal close(t), execute open(t+1). Raw prices. `DIVIDEND_EXCLUSION`.
- Cost: `A_SHARE_STRATEGY_COST_MODEL_V1` (not optimized).
- Predictive metric: `MEAN_FORWARD_RETURN` (overlapping, not CAGR).
- Official CAGR: non-overlapping capital account only.
- Split: 70/15/15 as V13/V14 (research / validation / denied). Final OOS DENIED.
- FDR: BH q=0.05 on all nine.
- Lesson from V14.1: predictive mean ≠ capital CAGR.
