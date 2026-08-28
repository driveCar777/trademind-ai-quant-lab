# DATA_EXPANSION_REPORT_V1

Mission V2.0. New dataset IDs only. Frozen `*-20260825-000001` bars were not rewritten.

## Acquired (immutable)

| dataset_id | rows | years | sha256 (bars.csv) | knowledge |
| --- | --- | --- | --- | --- |
| tm-alt-CBOE-GVZ-D1-20260828-000001 | 4259 | 16.939 | `7e77dab46fddb7898f73807e95faf6980e9de926fa77e21b257151d8d6918e3d` | session date + 21:00Z |
| tm-alt-CBOE-OVX-D1-20260828-000001 | 4259 | 16.939 | `f09417d3b8a8387c7f622edef2c3d1049b2cb0f110f326d64e6079aada9ba9c3` | session date + 21:00Z |
| tm-alt-CFTC-GOLD-COT-W1-20260828-000001 | — | — | Tuesday knowledge | **DO NOT CONTRACT** |
| tm-alt-CFTC-OIL-COT-W1-20260828-000001 | — | — | Tuesday knowledge | **DO NOT CONTRACT** |
| tm-alt-CFTC-GOLD-COT-W1-20260828-000002 | 451 | 8.624 | `f8d95e0313ace8c81441b5f98a64404870db7fb7b6d4a1c8caf6834e8269d85a` | Friday 21:00Z |
| tm-alt-CFTC-OIL-COT-W1-20260828-000002 | 451 | 8.624 | `d36158264be2db7ecde4542f63e94f861e0033b60784f998e10826a7149c5724` | Friday 21:00Z |
| tm-alt-EIA-USCRUDE-STXSPR-W1-20260828-000001 | 2291 | 44.0 | `479a3549770c99db892917942e7b825f4a34d7f885f1f04cd4056810a17fec57` | Wednesday 16:00Z |
| tm-alt-UST-DGS10-D1-20260828-000001 | 2164 | 8.649 | `a2598c564929c29409209ba2e26cd15a0690e76b78a66d82a37fa8fb4f4a593f` | date + 21:00Z |
| tm-alt-NYFED-EFFR-D1-20260828-000001 | 2174 | 8.649 | `9dd78d49c2f78f0f727f73c6ba11e3147f79b0d0cb2135a30682679cd495698b` | T+1 13:00Z |
| tm-alt-ECB-ESTR-D1-20260828-000001 | 1769 | 6.905 | `69f3daed016795685ad6508ec4cc705058f99696feabbf54c5bcd59000283e5d` | T+1 08:00Z |
| tm-alt-BOJ-CALL-D1-20260828-000001 | 1927 | 7.901 | `fe8db9db8040ad39adcdd0c7e6e961d346bfdb19e6ad9a5647cdd8e587d3047a` | T+1 01:00Z |

Price parents for V2 families: GOLD/OIL or EURUSD/USDJPY **D1 20260828**, never 20260825 overwrite.

CFTC raw zips stay in `tmp/cftc/` (gitignored). Git stores extracted GOLD/OIL series + metadata.

## Qualification notes

- CFTC Report_Date is Tuesday as-of. Using Tuesday 21:00Z leaks Wednesday–Thursday. Dataset 000002 is the leak-free Friday series.
- EIA week-ending Friday; WPSR release the following Wednesday.
- €STR starts 2019-10. FX D1 parents start 1971. CARRY_V1 split on full history is invalid. CARRY_V1A drops bars until first known carry.
- Macro consensus: not acquired.
- Option surface: not acquired.
- Gold ETF structured history: HTML only → not acquired.

## License / cost

All acquired series are official public downloads or public APIs with no key. No paid vendor was used.
