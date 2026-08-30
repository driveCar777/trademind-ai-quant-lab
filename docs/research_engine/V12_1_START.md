# V12.1 START — Full A-share equity daily panel freeze

**Date:** 2026-08-30  
**Purchase:** NO  
**Alpha:** NO  
**Backtest:** NO  
**Databento reserve:** unused  

## Mission

Upgrade the V12 PIT foundation into an immutable full-market equity daily panel that later price-alpha research can cite by `dataset_id` + content hash.

```
A_SHARE_DATA_STATUS = CONDITIONAL
NEW_PURCHASE = FALSE
ALPHA_RESEARCH = FALSE
dataset_id = tm-ashare-EQUITY-D1-20260830-000001
```

This task does **not** open financial alpha or industry PIT. Those stay BLOCKED.

## Hard rules

- One BaoStock session. No concurrent login.
- Empty `query_all_stock` is not a zero universe.
- `2015-04-30` stays INVALID until a live recount is trustworthy. Do not copy neighbors.
- Checkpoint every 20 symbols. Resume. Do not restart from zero.
- Raw prices are never overwritten by qfq/hfq.
- Large files stay on D: under `data/market/cn_a_share/raw/daily_panel_v12_1/`.
- Do not run RSI / momentum / value / ML / backtest.
