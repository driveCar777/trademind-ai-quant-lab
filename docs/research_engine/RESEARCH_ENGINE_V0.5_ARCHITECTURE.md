# Research Engine V0.5 Architecture

Foundation only. Not MT5. Not Final OOS. Does not overwrite V0.4 / HYP-0001 / FD V0.1.

## Authority (same lesson as HYP-0001)

```text
Windows locks MARKET_STATE_V0.5.json + STRATEGY_SEARCH_SPACE_V0.5.json
    → job manifest (strategy_ids + hashes + seed)
    → Xavier reads job, executes, returns lineage
```

Worker does not invent states or strategies.

`ENGINE_VERSION` stays `0.4` for the hypothesis engine. V0.5 lives in `research_engine/regime/` and `research_engine/strategy/`.

## Modules

| path | role |
| --- | --- |
| `research_engine/regime/state.py` | causal Market State |
| `research_engine/regime/adx.py` | locked ADX14 |
| `research_engine/strategy/schema.py` | strategy contract fields |
| `research_engine/strategy/space.py` | locked small strategy list |
| `research_engine/strategy/evaluate.py` | occupancy + cost-aware hold return |
| `research_engine/strategy/contract.py` | hash / OOS / worker guard |
| `scripts/research_engine_v05_run.py` | Windows dispatcher |

Reuse: `CausalView`, `windows.py`, `statistics.py`, `holdout.py`, `factors/compute.py` (ret, z_dist, spread_z, tickvol_z, efficiency), protocol `sma_at` / `atr_at`.

## Causal

`state[t]` and `signal[t]` use `<= t`. Target `t+horizon` is evaluation only. Future mutation of close must not change `state[t]`.

## Cost / risk V0.5

- Gross hold return vs raw spread/close
- Hard skip when FRICTION=WIDE if the strategy says so
- No position size, no portfolio

## After V0.5

Strategy Mining expands entry/exit/hold **only** from PROMISING V0.5 sketches, as a new versioned contract.
