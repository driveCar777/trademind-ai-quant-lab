# cn_warehouse_v37

SHFE/INE registered warehouse receipts onto China futures XS (V37). Contract: `docs/research_engine/V37_WAREHOUSE_RECEIPT_CONTRACT.md`.

```
python -m research_engine.cn_warehouse_v37.pull
python -m research_engine.cn_warehouse_v37.run
```

Pull uses DIRECT (no Clash proxy). Refuses a second `RESULTS.json`.
