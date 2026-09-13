# LEVERAGE_AND_RISK

> 2026-09-13. Phase 2. Not a sizing recipe. Not a Candidate.  
> Live snapshot: `AUDIT/BROKER_GOLD_SPEC_20260913T092709Z.json`.

## Four different numbers

| Word | What it is | What it is not |
|------|------------|----------------|
| **Leverage** | Broker margin multiplier. Ava demo `ACCOUNT_LEVERAGE=400`. | Alpha. Expected return. A reason the model is good. |
| **Risk** | How much equity you can lose (path, gap, stop-out). | The leverage field. |
| **Size** | Lots × contract. 0.01 GOLD = 1 oz notionally (`CONTRACT_SIZE=100` × 0.01). | “The strategy wants 20%/month.” |
| **Expected return** | E(net) of a **signal**. Gold drift is not a signal. | Leverage × wish. |

Leverage does not create edge. It multiplies **whatever** the next path is, including the −21% close-to-close drawdown already on the RESEARCH gold path (2022-10-20).

## Live GOLD facts (not README)

| Field | Live 2026-09-13T09:27Z |
|-------|-------------------------|
| ACCOUNT_LEVERAGE | **400** (not 100) |
| ACCOUNT_MARGIN_MODE | 2 (retail hedging) |
| ACCOUNT_CURRENCY | USD |
| ACCOUNT_TRADE_MODE | 0 demo |
| CONTRACT_SIZE | 100 |
| TICK_SIZE / TICK_VALUE | 0.01 / 1.0 USD per 1.0 lot |
| VOLUME_MIN / STEP / MAX | 0.01 / 0.01 / 150 |
| BID / ASK / SPREAD | 4348.75 / 4349.09 / **34 points** |
| SWAP_LONG / SHORT / MODE | −1.54 / +0.64 / 1 |
| DIGITS / POINT | 2 / 0.01 |
| MARGIN_INITIAL (symbol field) | 0.0 (broker uses leverage formula, not a stored initial) |
| MARGIN_HEDGED | 100 |
| Balance / equity / margin | 11784.53 / 11784.53 / 0 (flat) |

**Notional 1.00 lot** ≈ 4349 × 100 = **$434,900**.  
**Margin at 400×** ≈ $434,900 / 400 ≈ **$1,087 / lot**.  
**0.01 lot** ≈ $4,349 notional, ≈ **$11 margin**.

`TICK_VALUE=1` means 1.00 lot moves $1 per 0.01 price. 0.01 lot moves $0.01 per 0.01 price = **$1 per $1 gold move**.

## Why 400× is not a 20% machine

Account return ≈ (notional / equity) × price return − costs.

At $11,785 equity, **one 0.01 lot** is ~0.37× equity (notional $4,349). A +1.1% gold month (RESEARCH median) ≈ **+0.4% account** before swap/spread. To turn that median month into +20% account you need ~50× that unit (~0.5 lot) — about **18× economic exposure to gold**. See `TARGET_20PCT_MONTH.md` and `LEVERAGE_STRESS_TEST.md`.

## Risk that leverage actually hits

- **MaxDD:** gold RESEARCH daily path **−21.4%**. At 18× economic exposure that is account death, not a “deep drawdown.”
- **Margin utilization:** 0.5 lot ≈ $543 margin on $11.8k = 4.6% used while flat-risk is tiny; the kill is **price**, not the margin % looking safe.
- **Margin call / stop-out:** demo hedging mode still liquidates when equity vs margin fails. Gaps through gold weekends skip your stop.
- **Stop slippage:** Phase 1 Grok path had **no SL**. A stop in a 34-point spread market is a cost, not a guarantee.
- **Swap:** long **pays** (−1.54/night, mode 1). Holding leveraged gold overnight is a yield drag, not free beta.
- **Tail / gap:** 2022-10-20 path low is one example. One 8% gap at 18× is −144% theoretical; the account stops out earlier.

## Risk modes (research scenarios, not defaults)

0.25% / 0.50% / 1.00% / 2.00% of equity are **labels for later Candidate sizing**. They are not live defaults. No Candidate exists, so no mode is authorized to send.

## Bottom line

Leverage is a **converter** from price return to account return. Ava offering 400× does not change E(net|signal). Phase 2 baselines say the only positive D1 book is **being long gold**. That is beta, not a 20% monthly strategy.
