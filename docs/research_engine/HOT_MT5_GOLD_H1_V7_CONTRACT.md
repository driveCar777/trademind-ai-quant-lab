# HOT_MT5_GOLD_H1_V7_SESSION_REMAIN 合同（跑前冻结）

> 2026-09-13。新问句：**伦敦–纽约场次剩余收益**。不是下一根 24 小时收盘符号，不是 V2 伦敦第一下突破跟随。
> 依据 `HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME.md`：24h 符号树过拟合（训练 IC 0.52 / 折外 0.04），Ridge 拟合不动（训练 IC 0.055）。V2–V4 场次规则已读完。
> 只用已有 `data/market/cn_a_share/live/paper_hot/mt5_products/history/GOLD_H1.csv`。不拉 M15。
> 不覆盖 V1–V6 `READ.json`。`candidate=false` 写死。

仓库里 §29.24 已是真样本内诊断、§29.25 已是 V6 Ridge。本族 SPEC 只追加一段（标成 §29.26），不改已有段落。兄弟族 V8 后来也占用了 §29.26；段落号交给父代理合并，正文不改对方。

## 假设

同一套 V5 小时钟 13 列，不问 24h 符号，改问「进场后到当日 ≥20:00 还剩多少收益」。空仓门槛 = 1 根小时 ATR（λ=1.0 写死，不是 20bp）。每日最多一笔。隔夜=0。

若真样本内能拟合而折外 IC≈0 → 同一病理、换了标签仍过拟合。
若真样本内也拟合不动 → 场次剩余收益在这 13 列上没有线性/树可抓的边。
若验证 TWR>0 且 t>1 且覆盖过门 → 只记 `VIABLE_HISTORICAL`，仍不是 Candidate，不晋升任一状态窗。

## 特征（写死，与 V5 native 相同，不按 IC 挑）

`R1, R6, R24, VOL24, VOL120, ATR14, DIST_SMA24, DIST_SMA120, RSI14, RANGE_ATR, HOUR_SIN, HOUR_COS, DOW`

`ATR14` 特征 = 原始 ATR14 / close。不加外生、不从法医表加列。

## 标签

`y[t] = open[t_exit] / open[t+1] - 1`

`t_exit` = 与信号根 **同一日历日**、**严格在 t+1 之后**、第一根 `hour >= 20` 的 bar。
若该根之后同日没有 hour≥20 → 该根不交易（空仓），`y[t] = NaN`。

只在 **07–15 UTC（含）** 发信（进场后还要留得到 20:00）。其它小时强制空仓，也不进训练集。

## 模型 / walk-forward

- LightGBM **回归**，超参 = `research_engine/hot_mt5_products/products.py` 的 `LGBM_PARAMS`（200 棵、15 叶、min_child 40）。不搜叶、不搜树、不搜持有。
- `FIRST_PRED = 2000`，`REFIT = 1000`。
- `hours-to-exit[t] = t_exit - (t+1)`（根数）。`embargo = max(20, max hours-to-exit) + 1`。本时钟理论上 max remaining ≤ 12，故 embargo 锁定为 **21**。训练行还要满足 `t_exit < fit_at`（标签已实现）。
- 标签拟合时 clip 到 [−5, 5]。

## 外壳

- 门槛：`|score| > λ × ATR14_raw[t] / close[t]`，`λ = 1.0` 写死。预测波幅小于 1 根小时 ATR → 空仓。不是永远在场。不是 20bp。不是 V2 ORB。
- `ATR14_raw/close` = V5 特征列 `ATR14`，不再除一次 close。
- 方向 = `sign(score)`（过门槛时）。
- 每日最多 1 笔：当日 07–15 第一根过门槛的信号。下一开盘进，当日 ≥20:00 开盘出。
- 隔夜 = 0。成本 = 点差 + 2×2bp（无 swap）。

## 闸门

- 合格日 = 当日至少有一根 07–15 且该根同日能出到 hour≥20。
- 验证 = 合格日的最后 30%（按日切，不按 bar 切）。
- `n >= 8`；覆盖 = 成交日 / 合格日 `>= 15%`；验证 TWR>0 且 t>1 → `VIABLE_HISTORICAL`。
- `candidate = false` 无论过不过门。
- 最近一个月只诊断。不按月 10% 当门。

## 必须报告（缺一即拒收）

1. **真样本内**：研究窗（合格日前 70%）同一批有限行，先拟合再预测这些行 → IC / R² / 符号命中 / 分数是否常数。
2. **折**：与 V1 `TRAIN_VAL_REGIME` 相同结构：每折训练集 IC vs 下一折样本外 IC（`FOLDS.json`）。
3. **状态表**（事前写死，不挑赢家）：COVID `2020-02-01`–`2020-06-30`，2022 全年，2023 全年，`2024-05-01`→样本末。每窗净 TWR vs 买持有（窗内第一根收到最后一根收）。禁止把任一窗写成策略。

## 禁止

搜持有 8/12/36；改 λ；fade-V2；拉 M15；覆盖 V1–V6 READ；写 Grok；`:9000`；`order_send`；用金牛窗 / 近一月选参；把财务自由或每月 10% 写成闸门。

## 产物

- 模块 `research_engine/hot_mt5_gold_h1_v7/`
- `live/paper_hot/mt5_products/gold_h1_v7/results/READ.json`
- `FOLDS.json` / `REMAIN_trades.json`
- 冒烟 `tests/smoke/37_hot_mt5_gold_h1_v7.py`（合成 0–20 时、植入场次漂移；不改 V1–V6 READ）
- 第二次训练若 `READ.json` 已在则拒绝，除非 `--force`
