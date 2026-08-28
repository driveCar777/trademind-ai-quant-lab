# Dataset Qualification V0.1

Research readiness of frozen Data Layer V0.1 datasets.

Not a strategy ranking. Not a trading recommendation. FINAL_OOS_LOCKED = false.

## Dataset Matrix

16 datasets from `data/market/immutable/`. Each 2000 bars. Hash verified on Xavier.

GOLD M15 `000002` is not in the 16-cell matrix. It is only used for snapshot diff.

## Node Allocation

| Node | Host | Datasets |
|------|------|----------|
| Xavier-01 | 192.168.1.200 | GOLD M15 / H1 / H4 / D1 |
| Xavier-02 | 192.168.1.201 | EURUSD M15 / H1 / H4 / D1 |
| Xavier-03 | 192.168.1.202 | USDJPY M15 / H1 / H4 / D1 |
| Xavier-04 | 192.168.1.203 | OIL M15 / H1 / H4 / D1 |

Cross-check: GOLD M15 000001 also run on Xavier-04. Deterministic fields PASS.

## Data Quality

All 16: `hash_ok=true`, `anomaly_count=0`, no OHLC invalid, no duplicate, no out-of-order.

Data Layer validation_status remains WARN (real_volume all zero; intra-day session gaps).

OIL D1 is `DATA_REVIEW_REQUIRED` because 10+ bars have |simple_return| >= 10% (2020 oil crash window). That is an EXTREME_MOVE cluster, not a schema failure, and not a signal to trade or avoid oil.

## Return Profile

Bar simple returns. Not trade P/L. Not win rate.

| dataset | mean_return | std_return | +bars | -bars | first-to-last close % |
|---------|-------------|------------|------:|------:|----------------------:|
| GOLD M15 | 6.87e-05 | 0.00141 | 1040 | 955 | +14.50 |
| GOLD H1 | -4.63e-06 | 0.00301 | 969 | 1030 | -1.82 |
| GOLD H4 | 1.92e-04 | 0.00641 | 1043 | 951 | +40.79 |
| GOLD D1 | 5.79e-04 | 0.01037 | 1064 | 933 | +185.58 |
| EURUSD M15 | 1.28e-05 | 0.00031 | 988 | 961 | +2.58 |
| EURUSD H1 | 5.16e-07 | 0.00066 | 963 | 1012 | +0.06 |
| EURUSD H4 | 1.41e-05 | 0.00153 | 997 | 989 | +2.61 |
| EURUSD D1 | 4.04e-05 | 0.00419 | 986 | 1005 | +6.52 |
| USDJPY M15 | -1.29e-05 | 0.00069 | 1046 | 921 | -2.60 |
| USDJPY H1 | -3.62e-06 | 0.00101 | 1095 | 893 | -0.82 |
| USDJPY H4 | 5.20e-05 | 0.00200 | 1070 | 926 | +10.51 |
| USDJPY D1 | 2.11e-04 | 0.00520 | 1127 | 872 | +48.46 |
| OIL M15 | -3.63e-05 | 0.00385 | 980 | 975 | -8.40 |
| OIL H1 | -5.42e-05 | 0.00753 | 985 | 985 | -15.24 |
| OIL H4 | 2.40e-04 | 0.01361 | 1033 | 939 | +34.19 |
| OIL D1 | 1.05e-03 | 0.02974 | 1036 | 953 | +233.63 |

Price-change percent is a path description, not a quality score.

## Volatility Profile

Population stdev of trailing simple returns. Windows 20 and 50 are available on all 16 (2000 bars).

Examples (mean_volatility_20): GOLD M15 0.00127; EURUSD M15 0.00026; USDJPY M15 0.00044; OIL M15 0.00297; OIL D1 0.02275.

## ATR Profile

Simple 14-bar mean of True Range (not Wilder). Data description, not a signal.

Examples (mean_ATR14): GOLD M15 8.39; EURUSD M15 0.00046; USDJPY M15 0.099; OIL M15 0.352; GOLD D1 37.41.

## Gap Profile

D1: gap_count=0 under the V0.1 D1 rule (weekend/session not FAIL).

Intra-day gap_count: GOLD 22/87/73; EURUSD 4/17/69; USDJPY 4/17/68; OIL 22/88/73 for M15/H1/H4. overlap_count=0 on all 16.

## Volume Profile

`volume_policy=tick_volume_only`. real_volume is 2000/2000 zeros on every dataset. tick_volume is not real volume.

## Spread Profile

Spread present on all 16. Means (points): GOLD ~32–43; EURUSD ~7–9; USDJPY ~11–14; OIL ~2–3. EURUSD D1 and GOLD D1 have 2 zero-spread bars each. Not converted to USD cost.

## Extreme Move Audit

Top absolute bar returns are labeled EXTREME_MOVE. Large moves are not automatically bad data.

Largest listed |return|: OIL D1 +34.20% (2020-04-19) and -34.20% (2020-04-21). GOLD D1 largest listed about -10.03%. Intra-day FX tops are well below 3%.

## Trend Efficiency

`abs(last-first)/sum(|delta close|)`. Path directional efficiency only. Not a trend-strategy score.

Range in this batch: EURUSD H1 0.00069 to GOLD D1 0.078.

## Qualification

| dataset | qualification | reasons |
|---------|---------------|---------|
| GOLD M15/H1/H4/D1 | QUALIFIED_WITH_WARNINGS | real_volume_all_zero; session gaps (except D1); extreme moves listed |
| EURUSD M15/H1/H4/D1 | QUALIFIED_WITH_WARNINGS | same family |
| USDJPY M15/H1/H4/D1 | QUALIFIED_WITH_WARNINGS | same family |
| OIL M15/H1/H4 | QUALIFIED_WITH_WARNINGS | same family |
| OIL D1 | DATA_REVIEW_REQUIRED | dense_extreme_moves (>=10 bars with \|ret\|>=10%, 2020 crash window) |

No DATA_INVALID. Qualification is research-readiness, not “this market is good”.

## Cross Node Verification

GOLD M15 000001 on Xavier-01 and Xavier-04. Python 3.6.9 both. Deterministic fields identical. **PASS**. See `CROSS_NODE_VERIFY.md`.

## GOLD M15 Snapshot Diff

000001 vs 000002: 1999 identical rows. 1 changed row = last bar 2026-08-25T12:45:00Z (close and tick_volume). **HISTORICAL_MUTATION = false**. See `SNAPSHOT_DIFF_GOLD_M15.md`.

## Candidate windows

70 / 15 / 15 by bar index is recorded on each profile as `CANDIDATE_WINDOW`. Not locked. Not Final OOS.

## Node runtime

Wall clock ~29s for 16 parallel jobs plus cross-check.

| Node | datasets | bars | elapsed_s | errors | peak_rss_kb |
|------|----------|------|-----------|--------|-------------|
| Xavier-01 | 4 | 8000 | 19.45 | 0 | 16180 |
| Xavier-02 | 4 | 8000 | 19.22 | 0 | 15796 |
| Xavier-03 | 4 | 8000 | 18.99 | 0 | 15896 |
| Xavier-04 | 4 | 8000 | 19.43 | 0 | 16148 |

## Cleanup

`research_probe.py` is not resident. `/tmp/tm-data-qual-v01` removed. pgrep only matched the cleanup shell line.

8002–8005 sidecars still listening on all four hosts. Left untouched.

## Known Limitations

- ATR14 is simple mean of TR, not Wilder.
- Volatility is population stdev of simple returns.
- real_volume is unused (all zero).
- OIL D1 review flag is a density rule, not proof of corruption.
- Candidate windows are suggestions.

## Next Stage Requirements

Do not implement here:

- OHLCV research dataset contract for a future engine
- timestamp-aware research / validation / holdout lock
- dataset provenance in that engine
- Final OOS lock

FINAL OOS remains UNLOCKED.
