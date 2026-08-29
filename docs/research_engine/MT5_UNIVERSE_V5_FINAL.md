# MT5 Universe V5 Final

Source: live `symbols_get` + V4 specification merge. File: `data/market/research_engine/mt5_universe/MT5_UNIVERSE_V5.json`.

## Counts

| Field | N |
|---|---|
| total_symbols | 841 |
| instrument_type CFD | 841 |
| true options | 0 |
| true futures | 0 |
| READY | 81 |
| CONDITIONAL | 703 |
| SHORTFALL | 33 |
| BLOCKED | 21 |
| CLONE | 3 |

## Path roots

| Root | N | Class |
|---|---|---|
| CFD-SHARES | 638 | STOCK CFD |
| CFD-ETFS | 67 | ETF CFD |
| FOREX | 57 | FX CFD |
| CFD-INDICES | 38 | INDEX CFD |
| INTERNAL | 18 | mostly disabled exotic FX |
| CFD-METALS | 7 | METAL CFD |
| CFD-ENERGIES | 7 | ENERGY CFD |
| CFD-AGRICULTURAL | 7 | OTHER / new class |
| CFD-BONDS | 2 | BOND CFD |

## Research status rule

- `#` / `_` equity and ETF CFDs = CONDITIONAL (basket only, not single-name alpha).
- `GOLD_FUTURE`, `SI_FUTURE`, `CrudeTEST` = CLONE.
- INTERNAL + `trade_mode=0` = BLOCKED.
- Agricultural with D1 ≥ 5y after Stage B / freeze = new class, used in BREADTH_V1.

Equivalence: `SYMBOL_EQUIVALENCE_MAP_V1.json`.
