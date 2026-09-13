# HOT_MT5_GOLD_H1_V6_RIDGE 合同（跑前冻结）

> 2026-09-13。依据 `HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME.md`：V1/V5 真样本内 IC 0.52/0.48，折均训练 IC 0.62/0.58，折均测试 IC 0.038/0.022。过拟合。本份只换模型容量，不问新问题。
> 只用 `GOLD_H1.csv`。不覆盖 V1–V5 `READ.json`。`candidate=false`。

## 假设

同一十四列、同一 24 小时标签、同一 `sign(score)` 永远在场。把 LightGBM（200 棵 / 15 叶）换成 **标准化 + Ridge(α=1)**。若折外 IC 仍≈0 → 不是树太大，是线性组合也没有可迁移的 24h 边。若折外 IC 起来且验证账本过门 → 记 `VIABLE_HISTORICAL`，仍不是 Candidate。

## 模型（写死）

- 特征 = V1 十四列，不改、不挑。
- 每折：训练行均值/方差标准化（0 方差列改成 1），`sklearn.linear_model.Ridge(alpha=1.0)`。
- 标签仍 clip 到 [−5, 5]。
- Walk-forward 同 V1：首预测 2000、每 1000 重拟合、embargo=25。
- 外壳 / 成本 / 闸门同 §29.19。

## 必须报告

真样本内 IC/R²/命中；每折 train/test IC（写入 `FOLDS.json`）。不允许再出现「只报 walk-forward 账本、不报训练集」。

## 禁止

搜 α / 叶 / 持有 8/12/36；加美元；用 2024–26 金牛窗选参；覆盖旧 READ；写 Grok。
