# V14.1 Candidate → Strategy forensics

Audit only. Reconstructs the V13 overlapping candidate statistic and an
independent V14 capital account. Does not call `cn_a_share_strategy_v14.engine.simulate`.
Does not retune. Does not buy data. Final OOS remains DENIED.

```text
python -m research_engine.cn_a_share_strategy_v14_1.run
python -m research_engine.cn_a_share_strategy_v14_1.compile
```
