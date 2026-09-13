# hot_mt5_cost_aware

V2：三分类 long / cash / short。门槛 = 2× META 预期往返成本，不是 V1 法医的 20bp。不覆盖 V1 `READ.json`。

```
C:\ProgramData\miniconda3\python.exe research_engine/hot_mt5_cost_aware/run.py
```

`cost_aware_v2/results/READ.json` 已存在则不要再跑。
