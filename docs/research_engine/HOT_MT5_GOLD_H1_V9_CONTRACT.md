# HOT_MT5_GOLD_H1_V9_SPARSE 合同（跑前冻结）

> 2026-09-13。主人判断：过拟合 = 找错了特征；树记住大量无效列，没存下关键列。
> 科学校正（必须诚实）：Ridge 在完整十四列上真样本内 IC 只有 **0.055**（拟合不动）。若垃圾堆里藏着一条强**线性**关键列，Ridge 会留下它。树把训练 IC 抠到 0.52、折外 0.04，是在组合噪声。所以「再加列直到它想起关键列」是错的。
> 本份是**不搜 IC**、且对得上主人假设的那一刀：**事前登记一小撮先验列，一棵树，只跑一次。**
> 折外 IC 升 → 主人对「垃圾列害树」说对了。训练 IC 像 Ridge 一样塌、或折外仍≈0 → 没有能猜 24h 符号的关键自价列。
> 只用已有 `GOLD_H1.csv`。不覆盖 V1–V8 `READ.json`。`candidate=false`。

## 禁止（写死）

- **禁止**按 V1/V5 单列 IC 排名再留赢家（例如 DIST_SMA200 验证 IC −0.066）。那是特征搜索。本份五列在看任何数字之前锁死。
- 禁止加列、禁止看完数字再 `--force` 重训、禁止搜持有、禁止加 DXY、禁止写 Grok、禁止 `order_send`。
- 不改 `hot_mt5_gold_h1_v7/**`、`hot_mt5_gold_h1_v8/**`，不改冒烟 37/38，不改 SPEC §29.24/§29.25。

## 数据

仅 `data/market/cn_a_share/live/paper_hot/mt5_products/history/GOLD_H1.csv`（+ 同目录 `GOLD_META.json` 供成本）。

## 特征（五列，事前钟 + 尺度，不是法医 IC 表里最好的五列）

| 列 | 先验理由 |
|----|----------|
| `R24` | 一天的小时收益 |
| `VOL24` | 一天已实现波动 |
| `DIST_SMA24` | 相对一日均线的位置（不是 SMA200 当 8 个交易日） |
| `HOUR_SIN` | `sin(2π·hour/24)` |
| `HOUR_COS` | `cos(2π·hour/24)` |

**为什么是这五列、不是「IC 最好的五列」：** 拿掉 SMA200-当-8-日、`MONTH`、线性 `HOUR`、以及 R1/R5 这种垃圾 tick。钟用正余弦，尺度对齐 24 小时。不是从 V1/V5 `feature_ic` 表里挑赢家。

## 问句 / 模型 / 外壳（与 V1 同一问）

- `y[t] = open[t+1+24] / open[t+1] − 1`
- LightGBM **回归**，超参 = `research_engine/hot_mt5_products/products.py` 的 `LGBM_PARAMS`（不改叶/树/正则）
- 决策 = `sign(score)`，永远在场（分数有限才下单）
- Walk-forward：`FIRST_PRED=2000`，`REFIT=1000`，`embargo=25`（`HOLD+1`）
- 成交下一开盘，非重叠，持有 24 根
- 成本 = 点差 + 2×2bp + 跨午夜 swap（复用 V1 `_fill_cost` / `_nights`）

## 闸门

验证 = 后 30%。`n≥8` 且覆盖≥15% 且 TWR>0 且 t>1 → `VIABLE_HISTORICAL`。`candidate` 仍 **false**。不晋升。

## 必须报告（主人拒收没有训练集测试的作业）

与 `docs/research_engine/HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME.md` 同一协议：

1. 真样本内 IC / R² / 符号命中（研究窗同一批行：先拟合，再预测这些行）
2. 约 44 折：每折训练集 IC vs 下一折测试 IC
3. 状态窗（事前写死，不挑赢家）对买持有：COVID `2020-02-01`–`2020-06-30`；2022 全年；2023 全年；`2024-05-01`→样本末

对照锚：V1 真样本内 IC **0.52** / 折均测试 IC **0.038**。Ridge 十四列真样本内 IC **0.055**。

## 产物

`live/paper_hot/mt5_products/gold_h1_v9/results/`：`READ.json`、`FOLDS.json`、成交表。模块 `research_engine/hot_mt5_gold_h1_v9/`。冒烟 `tests/smoke/39_hot_mt5_gold_h1_v9.py`。
