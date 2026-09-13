# HOT_MT5_GOLD_H1_V5_NATIVE 合同（跑前冻结）

> 2026-09-13。只测「日线特征名拧在小时上」这一条。不是突破/反向第 5 刀。不是从 IC 表挑列。
> 只用 `GOLD_H1.csv`。不覆盖 V1–V4 `READ.json`。`candidate=false`。

## 假设

V1 十四列是日线配方。本份换成小时钟价内特征，标签 / 外壳 / 成本 / 闸门与 V1 的 `H1_ML` 相同。若仍无边 → 不是列名问题，是「自己的 K 线猜未来 24 小时符号」没信息。

## 特征（写死）

`R1, R6, R24, VOL24, VOL120, ATR14, DIST_SMA24, DIST_SMA120, RSI14, RANGE_ATR, HOUR_SIN, HOUR_COS, DOW`

- R6 / SMA24 / SMA120 = 约半个伦敦上午、1 日、1 周，不是 SMA200。
- `HOUR_SIN = sin(2π·hour/24)`，`HOUR_COS = cos(...)`。不用 0–23 线性小时。
- 不加外生、不从法医 IC 加 `DIST_SMA200`。

## 模型 / 账本 / 闸门

与 V1 `H1_ML`：LightGBM 回归同一超参；标签 = 下一开盘起 24 根；`sign(score)` 永远在场；首预测 2000、每 1000 重拟合、embargo=25；成本 = 点差 + 2×2bp + 跨过的自然日 swap。验证后 30%、成交≥8、覆盖≥15%、TWR>0 且 t>1 → `VIABLE_HISTORICAL`。最近一个月只诊断。

## 禁止

搜持有 6/8/12；加 ATR 空仓；加美元/利率；用 8 月 +18% 改列；覆盖旧 READ；写 Grok。
