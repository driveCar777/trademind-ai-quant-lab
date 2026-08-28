# Research Engine V0.5 Report — Strategy Discovery Foundation

2026-08-26. HYP-0001 14:11 and FD V0.1 files were not modified.

## What was built

Market State (causal) + 15 locked strategy sketches + evaluator + contract guards + Windows dispatcher (Xavier path exists, not executed this session).

Local evidence: all 16 qualified datasets, 200/200 bootstrap/perm, seed `20260825`.

```text
outcome = NO_USEFUL_STRATEGIES_FOUND
PROMISING 0 / CANDIDATE 0 / INCONCLUSIVE 2 / REJECTED 13
FDR m=203 discoveries=0
```

This is **not** a trading book and **not** annualized ≥ 10%.

Four Xavier dispatch (`scripts/research_engine_v05_run.py`, remote `/tmp/tm-strategy-discovery-v05`) is implemented. This session’s ranking is **Windows-local** because the SSH dispatcher embeds cluster credentials and was not auto-launched.

## Search contract

| field | value |
| --- | --- |
| discovery_id | `STRATEGY_DISCOVERY_V0.5` |
| search_space_hash | `a582b945a4f4d42cde6ceba36ad1f1f98de92accc9466cbdc6f4c77529b0bbdd` |
| strategies | 15 |
| Market State | TREND / ADX14 strength / VOL / LOCATION / MOMENTUM / tick ACTIVITY / FRICTION / EVENT=NA |
| runner | Windows-local-stdlib, 113.9s wall |

## INCONCLUSIVE (not PROMISING)

| id | mean d | bps | same-sign datasets |
| --- | --- | --- | --- |
| LONG_UP_TIGHT | +0.15 | +4.4 | 5 / 16 |
| SKIP_WIDE_ONLY | +0.14 | +1.8 | 13 / 16 |

Both fail FDR. Magnitude is a few bps before a real cost model. `SKIP_WIDE_ONLY` measures trading **inside** wide spread; it is a diagnostic, not a license to trade wide markets.

Trend-following and fade-extended sketches: REJECTED.

## Tests

64 `tests/research_engine` PASS (old 56 kept; +8 regime/strategy). Final OOS still denied. Worker cannot add strategy ids.

## Next

Do **not** start MT5. Do **not** retune HYP-0001.

Optional: run the existing four-Xavier dispatcher after explicit SSH approval.

Research next (new versioned contract): tighter friction units, or one more state-conditioned family — only if occupancy is large enough. Still no 10% claim.
