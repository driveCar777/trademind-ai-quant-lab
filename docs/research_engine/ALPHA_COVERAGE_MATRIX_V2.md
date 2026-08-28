# Alpha Coverage Matrix V2

Does not rewrite `ALPHA_COVERAGE_MAP_V1.md`. V4 live facts only.

## New MT5 assets frozen this mission (D1 unless noted)

Metals: SILVER 7.715y, COPPER 7.715y, PLATINUM 7.715y, PALLADIUM 7.715y. SILVER H4 7.715y.

Energy: BRENT 7.715y + H4, NATGAS 7.715y + H4, HEATOIL 7.715y, GASOLINE 7.715y.

FX extras: GBPUSD 33.3y, AUDUSD 33.3y, USDCHF 55.6y, USDCAD 33.3y, NZDUSD 32.6y, EURJPY 33.3y, EURGBP 33.3y. More in flight.

H1/M15: first-pass `copy_rates_from_pos(100000)` returned empty; second-pass 80k progressive froze H1 (~7.7y metals, ~12.8y FX) and M15 (~3.2–3.6y). VIX still too short.

Do not treat `#` equity CFDs as the research object.

## Families this mission

| Family | Result | Do not reopen |
| --- | --- | --- |
| CROSS_METAL_V1 | NO_CANDIDATE, four Xavier, 01=04 | gold-silver z_cut / sign flip / SMA60 residual |
| USD_METAL_V1 | NO_CANDIDATE, four Xavier, 01=04 | DXY z_cut / sign flip / V0.8 pair return |

## Still not a Candidate

Level = 0. External curve / option surface / consensus still blocked. Databento is not required to get more Ava OHLC of the same four names.
