# MT5 Maximum Data & Alpha Expansion Mission V4.0

Date: 2026-08-28 / 2026-08-29  
START commit: `7169971dc7f9a7cb26015b54f3a1d6f94b0e69eb`  
V3 pointer: `f830a20784dcb37619b6090b8be06c8dd8977cfe`  
Money spent: **$0**  
Final OOS: not read  
`order_send`: not called

## What “2000 bars” meant

2000 bars is a **frozen sample length**, not the terminal ceiling. Live Ava `maxbars` = **100000**. New history went to **new** `*-20260828-000001` IDs. `*-20260825-000001` was never overwritten.

## Terminal facts

- Package 5.0.5735. Path `C:\Program Files\Ava Trade MT5 Terminal`.
- **841** live symbols. `#` equity CFDs = inventory only (survivorship; not the metals/energy object).
- GOLD ticks: **HIST_TICKS** ~648k in a 2-day window. Broker ticks, **not** an exchange order book.
- VIX D1 = 37 bars / 1.448y. **Not frozen.** UK100 D1 = 3.97y. **Not frozen.**

## What was frozen (new IDs)

About **59** new `MT5_MAX_V4` datasets. Highlights:

| Logical | D1 span | Also frozen |
| --- | --- | --- |
| SILVER | 7.715y | H1 7.715y, H4 7.715y, M15 3.37y |
| COPPER / PLATINUM / PALLADIUM | 7.715y | H1 7.715y |
| BRENT / NATGAS / HEATOIL / GASOLINE | 7.715y | H1; BRENT/NATGAS H4; BRENT M15 |
| GBPUSD and other majors | 32–55y D1 | H1 ~12.8y (80k-bar cap); some M15 ~3.2y |
| US500 | 15.6y | H1 15.6y |
| US30 / USTECH100 / GER40 / JPN225 / DXY | 7.715y | H1 |
| GOLD / OIL / EURUSD / USDJPY | existing D1 kept | new H4 + M15 `20260828` |

GOLD/OIL D1 remain **7.715y broker wall**. Do not advertise 10y. Do not treat new M15 ~3.3y as a 10% CAGR sample.

Capability: `data/market/research_engine/mt5_history/MT5_HISTORY_CAPABILITY_V1.json`.

## Families executed

### CROSS_METAL_V1 — KILLED

- Hash `ef6f3633e49de2b1f62657be638bb666ab7de1460021f6c0fc466a9bc2780df8`
- 252-day z of `log(GOLD/SILVER)`. Not SMA60 residual. Not OIL.
- local 2000 + four Xavier. 01=04 `26fcf886…593f53a`. **NO_CANDIDATE**.
- Do not flip. Do not change z_cut.

### USD_METAL_V1 — KILLED

- Hash `a39952f9dd4f3bcec04ce302ac9248b1dc5c2832cce762ee0ce16c0eec474f0b`
- 252-day z of DXY into GOLD/SILVER. Not V0.8 pair return. Not gold-silver ratio.
- local 2000 + four Xavier. 01=04 `2257aff4…0f218d34`. **NO_CANDIDATE**.
- Do not flip. Do not change z_cut.

VIX family was **not** opened (history too short). Another gold-silver / OIL-BRENT / DXY z_cut is forbidden.

## Databento decision

**Do not buy Databento to get more Ava OHLC.** That information is now on disk.

**Still HUMAN / PAYMENT if** the next mechanism is futures curve, option surface, or macro consensus. Those are not in this terminal.

Case A (price/CFD universe): MT5 priority extract is done.  
Case B (curve / surface / consensus): still blocked. Same pack: `HUMAN_DATA_PURCHASE_ACTION_PACK.md`.

## Official answers

1. LEVEL = **0**
2. Candidate = **0**
3. Live symbol count = **841** (inventory). New qualified V4 datasets ≈ **59**
4. Max history: terminal 100000 bars; GOLD/OIL/metals/energy CFD D1 **7.715y**; several FX D1 **33–55y**; VIX **1.45y**
5. New mechanisms executed: CROSS_METAL_V1, USD_METAL_V1
6. Failed this mission: both **NO_CANDIDATE**
7. Cash: **$0**. External data still needed for **curve / surface / consensus**, not for more Ava bars of the same names
8. Distance to 10%: still no Level 1. Do not claim 10% from 7.7y or 3.3y M15
