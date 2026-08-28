# Regime Transition V0.9 — Data Requirements

Design only. 2026-08-26.  
Checklist for the implementer. Do not fetch new bars for V0.9.

---

## Executive Summary

V0.9 不需要新行情。只需要两份已冻 D1，加上 V0.5 状态定义。  
缺利率 / IV / 新闻 **不阻塞** 本实验。

---

## Current Evidence

| dataset_id | sha256 (from V0.8 audit) |
| --- | --- |
| `tm-market-GOLD-D1-20260825-000001` | `49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899` |
| `tm-market-OIL-D1-20260825-000001` | `a22e4213fbbf28e24e892fcce400522885e8208ba9f94bbf41ceed3177808d72` |

Do not overwrite. If hash differs at implement time: **stop**, `DATA_MISMATCH`.

---

## Required (must exist)

- [ ] Two parent CSVs readable under `data/market/immutable/`
- [ ] Manifests: UTC, 2000 rows, `tick_volume_only`, spread present
- [ ] `MARKET_STATE_V0.5` code already on disk (`research_engine/regime/`) — reuse, do not retune ADX/SMA
- [ ] `research_engine/statistics.py` (bootstrap / block / perm / BH)
- [ ] `final_oos_access()` still raises
- [ ] Four Xavier SSH (same hosts as V0.8) when execution is approved

## Explicitly not required

- EURUSD / USDJPY (not in V0.9 space)
- V0.8 align pack as a feature clock
- DXY, rates, IV, calendar, `real_volume`
- Longer M15/H1
- LLM

## Must create at implement time (not now)

| artifact | rule |
| --- | --- |
| `WINDOW.json` × GOLD, OIL | 70/15/15 on that series, before PnL |
| VOL percentile freeze | RESEARCH only |
| job manifests | 01=0001, 02=0002, 03=0003, 04=0001 check |
| ranking | after collect; m=3 |

## Must not create / touch

- New hypothesis JSON for XA or HYP-0001
- Files under `data/market/final_oos/` payload
- MT5 trade calls
- Overwrite of `*-20260825-000001`

---

## Occupancy risk (data, not a tune)

Transitions are sparse on ~6.4y D1.  
If RESEARCH trades < 8: label `INSUFFICIENT_OCCUPANCY`. That is a valid failure.  
Do not lower ADX 25 or change 33/67 to mint events.

---

## Decision

Data gate for V0.9 = **OPEN**.  
Blocked classes stay blocked; they are not V0.9’s problem.

---

## Next Automatic Action

`REGIME_TRANSITION_V0.9_TEST_FRAMEWORK.md` — 实现前必须写的测试清单（仍不写代码）。
