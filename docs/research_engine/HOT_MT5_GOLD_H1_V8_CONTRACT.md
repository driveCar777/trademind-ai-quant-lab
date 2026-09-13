# HOT_MT5_GOLD_H1_V8_TRIPLE_BARRIER 合同（跑前冻结）

> 2026-09-13。新问句：**未来 24 根 H1，谁先碰到 ±1.0×ATR14**。不是 24h 收盘符号（V1/V5/V6 已穷尽），不是 V2 伦敦 ORB 跟随，不是 D1 V3（日线 10 日 ATR√hold 三分类、空仓过多）。
> 只用已有 `GOLD_H1.csv`。不拉 M15。不覆盖 V1–V7 `READ.json`。`candidate=false`。
> 依据 `HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME.md`：树能拟合 24h 符号（训练 IC 0.52）但折外 IC≈0；Ridge 训练 IC 0.055。本份换标签，不换「再堆一棵 24h 树」。

## 假设（m=1）

在信号根 t，用 V5 小时钟 13 列，训一个三分类：LONG / SHORT / CASH = 先碰上障碍 / 先碰下障碍 / 24 根内都没碰到（时间止）。预测 LONG 或 SHORT 才开仓，CASH 坐一期再看。

## 数据

- 仅 `live/paper_hot/mt5_products/history/GOLD_H1.csv` + `GOLD_META.json`。
- 禁止拉 15/30。禁止第二品种。

## 特征（写死，不搜 IC）

与 §29.23 V5 同一清单，一字不改：

`R1, R6, R24, VOL24, VOL120, ATR14, DIST_SMA24, DIST_SMA120, RSI14, RANGE_ATR, HOUR_SIN, HOUR_COS, DOW`

特征列 `ATR14` 仍是 V5 的 **ATR/close**。障碍用的是价格单位的 ATR14 原值，不是这一列。

## 标签（写死）

- 先验：允许 **全部小时**（0–23）。只要前面还有 24 根可扫、后面还能在 `t+1+24` 开盘出完。
- **LOCK：扫 24 根 H1，允许隔夜。** 不按「次日 hour≥20」截断。
- `k = 1.0`（Lopez 默认）。不是 V1 MFE。不是 D1 V3 的 k 搜索。
- `up = close[t] + 1.0 * ATR14_price[t]`
- `dn = close[t] - 1.0 * ATR14_price[t]`
- 扫 `t+1 … t+24`（含）。第一根 `high >= up` → LONG；第一根 `low <= dn` → SHORT；都没有 → CASH。
- **同一根** `high>=up` 且 `low<=dn` → CASH（H1 无法排序路径）。
- 没有有限 ATR / 没有 `t+25` 开盘 → 该行无标签。
- 已实现符号：LONG=+1，SHORT=−1，CASH=0。用于训练集 IC。

## 模型（写死）

- LightGBM **三分类**，参数抄 `hot_mt5_cost_aware.LGBM_CLF`：`objective=multiclass`，`num_leaves=15`，`n_estimators=200`，`min_child_samples=40`，其余同表。
- Walk-forward：`FIRST_PRED=2000`，`REFIT=1000`，`embargo=25`。
- 决策 = argmax。CASH 是一类，坐一期（`t += 1`），不是丢掉。
- 不搜叶 / 树 / k / 持有。

## 真样本内（不做就拒收）

每折拟合后，必须在 **训练行** 上再预测一次：

- 三类准确率 `acc = mean(argmax == y)`
- `IC = Pearson(P(long) − P(short), 已实现符号)`

折内训练 vs 折外测试都写进 `FOLDS.json`。另报研究窗一次全拟合的同一对数字。禁止只报 walk-forward 账本。

## 账本

- 预测 LONG/SHORT：`t+1` 开盘进。
- 出：先碰到任一障碍的 **下一根开盘**；否则 `t+1+24` 开盘时间止。
- 非重叠：成交后下一信号从出仓根起。
- 成本 = 点差 + 2×2bp + 跨过的午夜 swap。复用 V1 `_fill_cost` / `_nights`（不是每根 H1 收一夜）。
- 不写 `order_send`。不写 `:9000`。

## 覆盖率（写死，闸门用这个）

```
coverage = Σ(t_out − t_in) / 窗口根数
         = (成交笔数 × 平均持有小时) / 窗口小时
```

窗口根数 = 该窗可发信号的 H1 根数。**不用** `笔数 × 24 / 根数`（持有是变长的）。

## 闸门

验证 = 后 30%。验证笔数 ≥ 8 且 coverage ≥ 15% 且 TWR > 0 且 t > 1 → `VIABLE_HISTORICAL`。`candidate` 仍为 false。覆盖不足 → `NO_CANDIDATE` / `VALIDATION_COVERAGE`。

## 状态（事前写死，不挑赢家）

COVID `2020-02-01`–`2020-06-30`；2022 全年；2023 全年；`2024-05-01`→样本末。各窗净 TWR 对买持有（窗内第一根收到最后一根收）。**禁止**把任一状态窗写成策略。

## 禁止

搜 k / 8/12/36 小时 / 叶 / 树；用 V1 MFE 定 k；用金牛窗或近一月选参；拉 M15；覆盖 V1–V7 READ；写 Grok；`order_send`；10%/月闸门；第二趟训练（`READ.json` 在则拒绝）。
