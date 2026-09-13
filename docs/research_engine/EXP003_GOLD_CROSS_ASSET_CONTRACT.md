# EXP-003 GOLD cross-asset incremental — write-once contract

> Frozen **2026-09-13 before any cross-asset train**.  
> Experiment id: `EXP-003`.  
> `candidate=false`. Do not reopen XA / RT / XR / V32 / TERM_STRUCTURE / OI / DTE.

## Question

Do **PIT** external series (DXY, rates, equity risk, oil) add **incremental** expected net return on GOLD beyond own-price baselines (EXP-001 / EXP-002)?

## Design (no run required to freeze)

| Layer | Intended series | PIT rule | Status this session |
|-------|-----------------|----------|---------------------|
| Own price | GOLD D1 OHLC | close[t] only | Required control |
| Dollar | DXY or USD index CFD if present on Ava | same-bar close only if that bar’s close is known | Run only if series exists without a hunt |
| Rates | US10Y / US02Y or broker bond CFD | same | Same |
| Risk | US500 / equity index CFD | same | Terminal historically **lacked US500**; do not invent |
| Oil | Ava `CrudeOIL` D1 already on disk | same | Allowed as one pre-registered add-on |

Incremental test (when run): compare Linear(own-price) vs Linear(own-price + layer) on RESEARCH window only. Add one layer at a time. FDR m = number of layers actually run.

## Locked split

Same as EXP-001: RESEARCH → 2025-09-11; FINAL_OOS from 2025-09-12 **unopened**.

## This session

Contract frozen. **No ML run** unless EXP-001 Linear showed OOS incremental value. If EXP-001 stops at Naive/baselines, EXP-003 stays `REGISTERED_NOT_RUN`.

## Forbidden

Shopping which FX pair “works”; using news timestamps without a PIT store; treating Grok macro narrative as this experiment; paying for new vendor data without a quote.

## WHY / WHAT / EXPECTED / RISK

- **WHY**: Phase 1 own-price well is exhausted; the honest next question is incremental information, not another RSI.
- **WHAT**: Pre-register the layer list and the incremental test.
- **EXPECTED EFFECT**: Dollar/rates may correlate with gold; correlation ≠ net edge after costs.
- **RISK**: Multiple-testing across series/TFs; look-ahead on slow macro prints.
