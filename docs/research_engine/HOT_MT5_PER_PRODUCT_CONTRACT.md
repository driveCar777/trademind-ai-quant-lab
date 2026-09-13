# HOT_MT5_PER_PRODUCT_V1 合同（跑前冻结）

> 2026-09-13。用户：黄金/原油/欧美/美日/美英/美加/美瑞各自拉历史、各自训、各自策略；美股暂不做；回测用长期全样本，特殊时段只诊断。
> 只算一次。不是 Candidate。不写 `:9000`。不与 A 股对冲、不拿两边数字改提示词。

## 数据

- 本机 Ava demo `copy_rates_from_pos`，D1 与 H1 各最多 100000 根，写入 `live/paper_hot/mt5_products/history/`。
- 训练只用 **D1**。H1 只存档，不在本合同搜参。
- 不加其他品种当特征（美加不加原油，黄金不加白银/美元）。

## 七个假设（m=7，各一份模型）

| id | 外壳 | 持有 | 特征 |
|----|------|------|------|
| GOLD | TREND_LS | 10 | CORE + MONTH |
| CRUDE | SHORT_HOLD_LS | 5 | CORE + REV5 + VOL_EXPAND |
| EURUSD / USDJPY / GBPUSD / USDCAD / USDCHF | FX_LS | 5 | CORE + R60 |

CORE = R1 R5 R20 VOL20 VOL60 ATR14 DIST_SMA50 DIST_SMA200 RSI14 GAP RANGE_ATR DOW。

LightGBM 参数写死在 `products.LGBM_PARAMS`（单序列事先缩小叶子/min_child，不是搜出来的）。

## 成交与成本

- 信号日 t 收盘打分；t+1 开盘进，t+1+hold 开盘出。非重叠。
- 分数 >0 多，≤0 空。
- 成本 = 点差（bar spread 与当前点差取稳健值）+ 2×2bp 滑点 − 隔夜 swap（mode 1 / 5 与 V32 同一公式，用现场 `symbol_info`）。

## 报告窗（不拿来选模型）

- **主报告 = 全样本**（首个可预测 bar → 最后一根）。
- 研究 = 前 70%，验证 = 后 30%，只报告。
- 按年切片、COVID_2020、HIKING_2022、RECENT_2024_ON = **诊断**，禁止据此改特征/持有期。

## 闸门（历史可行，不是 Candidate）

验证期期数 ≥8 且验证 TWR>0 且 t>1.0 → `VIABLE_HISTORICAL`。否则 `NO_CANDIDATE`。`candidate` 一律 false。

## 禁止

改 hold / 特征 / 阈值去凑正；美股；A 股组合；把 demo 数字写进 Grok 提示词。

## 一次读取

`data/market/cn_a_share/live/paper_hot/mt5_products/results/READ.json` 已存在 → **拒绝再训同一合同**（改特征/持有期 = 新合同、另计 m）。判决 `HOT_MT5_PER_PRODUCT_DECISION.md`：7/7 `NO_CANDIDATE`。
