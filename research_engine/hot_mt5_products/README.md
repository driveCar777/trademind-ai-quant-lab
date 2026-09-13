# hot_mt5_products

`:9001` 分品种 MT5 研究。美股 CFD 不做。不写 `:9000`。不是 Candidate。

每个产品：自己的 D1 历史 → 自己的特征 → 自己的 LightGBM → 自己的持有期外壳 → 全样本回测。

```
C:\ProgramData\miniconda3\python.exe research_engine/hot_mt5_products/run.py
```

`READ.json` 已存在则不要再跑同一合同。产物在 `data/market/cn_a_share/live/paper_hot/mt5_products/`。判决 `docs/research_engine/HOT_MT5_PER_PRODUCT_DECISION.md`。
