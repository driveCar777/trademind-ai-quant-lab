# Regime Transition V0.9 Report

Executed 2026-08-27. Contract hash unchanged:

`3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea`

Not HYP-0001. Not V0.6. Not V0.8. Final OOS not read. No `order_send`.

## Decision

- Program: **NO_CANDIDATE**
- FDR m=3 discoveries: **0**
- GOLD pass: none
- OIL pass: none
- Xavier-01 vs Xavier-04 `content_hash`: **match** `3199546468e802bf…249b8`
- Next: Residual V0.91 (already executed after this decision). Do not retune ADX 25 / hold 5 / VOL 33/67.

## Real run

| node | host | job | seconds |
| --- | --- | --- | --- |
| Xavier-01 | 192.168.1.200 | HYP-RT-0001 PRIMARY | ~43 |
| Xavier-02 | 192.168.1.201 | HYP-RT-0002 PRIMARY | ~42 |
| Xavier-03 | 192.168.1.202 | HYP-RT-0003 PRIMARY | ~40 |
| Xavier-04 | 192.168.1.203 | HYP-RT-0001 CROSS_CHECK | ~40 |

Python 3.6.x on all four. Local 2000-iter book agrees on n_trade / occupancy / signs.

## Hypotheses

### HYP-RT-0001 VOL_SHOCK → OIL short

- label: **FALSIFIED**
- RESEARCH: n_trade=20 occupancy=1.85% TR=-2.95% CAGR=-0.54% delta=-0.0087 p=0.368
- VALIDATION: n_trade=5 TR=+0.32% mean_signal **positive** (H1 wanted negative)
- Occupancy is not a level leak (HIGH-vol *level* share ≈ 31%; transition share ≈ 2%).

### HYP-RT-0002 ENTER_STRONG_UP → GOLD long

- label: **INCONCLUSIVE**
- RESEARCH: n_trade=12 occupancy=0.89% TR=-2.19% mean_signal **negative**
- VALIDATION: n_trade=3 (<4)

### HYP-RT-0003 EXIT_STRONG → GOLD short

- label: **INCONCLUSIVE**
- RESEARCH: n_trade=24 occupancy=1.78% TR=-3.14% p=0.936
- VALIDATION: n_trade=3 (<4)

## Path benchmark (not a hypothesis)

Unconditional hold=5 after the same cost model, RESEARCH:

- GOLD long CAGR ≈ -6.3%
- OIL long CAGR ≈ -3.1%
- both shorts worse

Validation GOLD long path CAGR ≈ +9.8% is a **path**, not an alpha. Transitions did not beat their same-side baseline with a passing book.

## Distance to 10%

This family cannot certify 10%. Program CANDIDATE=0.

## Untouched

HYP-0001 14:11, FD V0.1, V0.5/V0.6/V0.8 spaces and results, immutable `*-20260825-000001`, Final OOS payload, MT5 trading.
