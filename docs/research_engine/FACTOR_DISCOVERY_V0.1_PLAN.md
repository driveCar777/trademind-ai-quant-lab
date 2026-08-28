# Factor Discovery V0.1 Plan

HYP-0001 stays locked. This is a **new** search contract, not a retune of streak=3.

## Profitability Gap Map

### Now have

| capability | class |
| --- | --- |
| 16 immutable qualified datasets | INFRASTRUCTURE |
| dataset qualification / readiness | GOVERNANCE |
| experiment contract + preregistration (HYP-0001) | GOVERNANCE |
| distributed Xavier execution | INFRASTRUCTURE |
| determinism + result immutability | GOVERNANCE |
| bootstrap / block bootstrap / permutation | GOVERNANCE |
| BH-FDR + multiple-testing ledger | GOVERNANCE |
| validation window + Final OOS denied | GOVERNANCE |
| HYP-0001 WEAK_SUPPORT (predictive datapoint) | DIRECT_PROFIT_RELEVANT |

### Missing before this task

| capability | class | this version |
| --- | --- | --- |
| factor registry + metadata | DIRECT_PROFIT_RELEVANT | implement |
| factor definitions with economic rationale | DIRECT_PROFIT_RELEVANT | implement |
| target definitions (return / abs / dir / vol) | DIRECT_PROFIT_RELEVANT | implement, limited |
| candidate generation from families | DIRECT_PROFIT_RELEVANT | pre-defined, not random farm |
| factor combinations | DIRECT_PROFIT_RELEVANT | 5 explicit combos only |
| regime conditioning | INDIRECTLY_RELEVANT | interface / later |
| cross-asset factors | INDIRECTLY_RELEVANT | DRAFT, not computed |
| economic magnitude in return + bps | DIRECT_PROFIT_RELEVANT | implement |
| cost-aware scoring | DIRECT_PROFIT_RELEVANT | raw spread/close screen only |
| strategy translation | INDIRECTLY_RELEVANT | interface only |
| news / LLM events | NOT_CURRENTLY_PRIORITY | designed, no API |
| ML models | NOT_CURRENTLY_PRIORITY | not this version |
| annualized 10% / Sharpe / DD | NOT_CURRENTLY_PRIORITY | strategy/portfolio later |

Do not label infrastructure as “directly makes money”.

Closest to money now: **a locked, causal, FDR-controlled factor screen with cost sensitivity**.

## Search contract (FACTOR_DISCOVERY_V0.1)

- Seed `20260825`
- Screening bootstrap/permutation **200** (not HYP-0001’s 5000)
- FDR q=0.05 over all primary (candidate × dataset) tests
- Targets: `future_return` h=1 primary; some vol → `future_abs_return`; a few h=3
- Condition: research 67th/33rd percentile frozen, applied to validation
- Volume = `tick_volume` only (`real_volume` is 0)
- Final OOS: access denied
- Worker cannot add candidates
- Candidate count: 57 (9 live families, including limited combos)

## Families

| family | live | notes |
| --- | --- | --- |
| A Momentum | yes | continuous RET / sign consistency / accel — not HYP-0001 streak |
| B Reversal | yes | distance from mean, range position, z, close location |
| C Volatility | yes | range, TR-like, short/long ratio → return and abs-return |
| D Breakout | yes | distance to recent high/low |
| E Efficiency | yes | net move / path |
| F Volume | yes | tick_volume only |
| G Spread | yes | spread regime + one ret×low-spread combo |
| H MTF | yes | M15 only; closed 4-bar HTF proxy |
| I Cross-asset | DRAFT | needs aligned multi-file timestamps |
| News | DRAFT | no live API |

## Partition

By dataset so each node loads bars once:

- Xavier-01 GOLD ×4
- Xavier-02 EURUSD ×4
- Xavier-03 USDJPY ×4
- Xavier-04 OIL ×4 + GOLD M15 CROSS_CHECK (not double-counted in FDR)

## Allowed honest outcomes

`NO_USEFUL_FACTORS_FOUND` is valid.

`PROMISING !=` trading strategy `!=` annualized ≥ 10%.
