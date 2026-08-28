# ALPHA MISSION V1.1 REPORT

Stop: **STOP B**. Level **0**. Candidate **0**.

START COMMIT: `134bfe565a6972991cec5d75da22d80e5d62bae3`  
END COMMIT: `8ca1d3a79af8626b4ad5d6ffff383cbf2d237528`  
Remote: `https://github.com/driveCar777/trademind-ai-quant-lab` (private, `main`)  
Final OOS: **DENIED**. `order_send`: **FORBIDDEN**. Frozen `*-20260825-000001` hashes unchanged.

## 1. What Level is TradeMind?

**Level 0.** No Level 1 Candidate. No strategy layer. No paper. No MT5 live.

## 2. Is there a Candidate?

**No.**

HYP-IT-0001 (GOLD month-end +) is the only single-target costed book that passed research and validation gates. It is **not** a Candidate: FDR 0/3, OIL failed validation, block-bootstrap CI includes 0. Do not promote it. Do not retune it.

## 3. If none: which Alpha mechanisms remain?

Researchable on **current** broker data: **none that are still UNKNOWN and legal**.

Killed this mission (new evidence):

| Family | Result | Hash |
| --- | --- | --- |
| INSTITUTIONAL_TIME_V1.0 | WEAK_EDGE → KILLED | `1d3c4a1f…24457` |
| TIME_STRUCTURE_V1 | NO_CANDIDATE 3/3 FALSIFIED | `51bb3eed…93d2` |
| MICROSTRUCTURE_SURPRISE_V1 | NO_CANDIDATE 3/3 FALSIFIED | `54ab70ff…92f1` |
| REGIME_INTERACTION_V1 | NO_CANDIDATE 3/3 FALSIFIED | `c060a77e…d321` |
| ALT_MARKET_STRUCTURE_V1 | NO_CANDIDATE 3/3 FALSIFIED | `8e12e3b1…0aad6` |

Still unknown **only** because data does not exist here:

- IV / options — DATA_BLOCKED
- Carry / funding — DATA_BLOCKED
- News / text — DATA_BLOCKED
- GOLD/OIL D1 10y — BROKER_LIMITATION (max **7.715y**, first bar 2018-12-12). Do not write 10y.

Quarter-end, Tokyo open, sign flips, hold changes, ADX/SMA60/z_cut rescue: **FORBIDDEN reopens**, not remaining UNKNOWN.

AI-assisted generation was **not** opened. Every legal clock/volume/gap/relative-vol family on this tape is already KILLED. An LLM proposing another z-cut or a short of a failed long would be result-based mutation.

## 4. What is worth the next research dollar?

**New data**, not another contract on Ava D1/H1 GOLD/OIL:

1. A venue that actually has GOLD/OIL D1 before 2018, **or**
2. Options IV / carry / funding series, **or**
3. A non-broker alternative (inventory, positioning, news) with a new hash and a new family.

Do not spend another week on London open, month-end T−2, or tickvol z_cut=1.5.

## 5. What is the real obstacle to long-run 10%?

Not leverage. Not a missing Sharpe number.

The obstacle is **Level 1 does not exist**. There is no pre-registered, costed, two-target, FDR-passing edge. Without that, CAGR 10% is a capital wish, not a statistic we are allowed to optimize toward.

Pattern across TS / MS / RI / AMS: long + hold 5 + V0.6 cost on frequent H1 events **loses money** in both research and validation. The tape does not pay for that book. IT month-end is rarer and only half-works on GOLD.

## 6. If there were a Candidate, why Strategy Construction?

There is not one. Strategy Construction stays **blocked**.

## Data (honest)

New IDs only. `20260825` parents untouched (GOLD D1 sha `49291ffd…e899`, OIL D1 sha `a22e4213…8d72`).

| Pack | Span | Status |
| --- | --- | --- |
| GOLD/OIL D1 20260828 | 7.715y from 2018-12-12 | BROKER_LIMITATION |
| GOLD/OIL H1 20260828 | 7.715y, ~45k bars | ACQUIRED |
| EURUSD/USDJPY D1 20260828 | broker 1971; EUR pre-1999 is backfill | ACQUIRED with caution |
| FX H1 20260828 | ~8.10y from 2018-07-22 | ACQUIRED |

IT used frozen 2000-bar D1 parents, as contracted. Longer history was **not** used to reopen IT.

## Execution

- IT: local 2000 + four Xavier, 01=04 `a7e646b5…b2d0`
- TS: local 2000 + four Xavier, cross_check True
- MS: local 2000 + four Xavier, cross_check True
- RI / AMS: local 2000 authority (same failure shape; no param search)

## Why not MT5

Level 0. No Candidate. No Level 2 strategy. Final OOS denied. `order_send` remains forbidden.

Tags: `RESEARCH-2026-0001` … `0005`. Ledger: `docs/research_engine/RESEARCH_LEDGER_V1.json`.
