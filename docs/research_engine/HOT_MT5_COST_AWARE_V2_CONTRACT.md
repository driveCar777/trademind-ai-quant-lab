# HOT_MT5_COST_AWARE_V2 合同（跑前冻结）

> 2026-09-13。用户授权跑设计稿 `HOT_MT5_SITOUT_AND_HURDLE_DESIGN.md`。
> m 另计。只算一次。不是 Candidate。不写 `:9000`。不与 A 股对冲。
> **禁止**用 V1 法医里的 20bp 当门槛。

## 数据

- 只读 V1 已拉的 D1 + META：`live/paper_hot/mt5_products/history/{ID}_D1.csv`、`{ID}_META.json`。
- 不改特征清单，不改 hold，不重拉、不写冻结盘。美股不做。

## 七个假设（m=7）

与 V1 相同品种 / 特征 / 持有期。外壳改名 `COST_AWARE_3WAY`。

## 标签（成交前写死）

`y` = t+1 开盘 → t+1+hold 开盘的价格变动（未乘方向）。

预期往返成本只用来自该品种 META 的数，不用 bar 里事后点差、不用 20bp：

```
nights_exp = hold + 2 * (hold / 5)          # 每 5 个交易日一个三重日
spread     = spread_points_now * point / bid
slip       = 2 * 0.0002
swap_frac  = mode1: swap * point / bid * nights_exp
             mode5: swap/100 * nights_exp/365
cost(side) = max(0, spread + slip − swap_frac(side))
hurdle(side) = 2 * cost(side)
```

- `y > hurdle(+1)` → LONG
- `y < −hurdle(−1)` → SHORT
- 其余 → CASH

λ=2 来自 triple-barrier / 成本乘数惯例，不是 V1 切片。

## 模型

一个 LightGBM **三分类**（cash=0, long=1, short=2）。叶子/树/min_child 与 V1 回归器同档，事先写死。不要 `class_weight`。某一折只有 1 个类 → 该折不拟合，预测当 CASH。

Walk-forward：首预测 300 根，每 250 根重拟合，embargo = hold+1。

## 策略

argmax。CASH = 空仓，次日再看。LONG/SHORT = 下一根开盘进，hold 根后平，0.01 手，只 demo。成本仍用 V1 公式（bar 点差 + 2×2bp + 实际隔夜）。

## 报告与闸门

主报告 = 全样本账户 TWR（空仓日收益 0，CAGR 用日历年）。验证 = 后 30%，只报告。

**直接否：** 验证成交 &lt; 8，或验证在场时间（成交数×hold / 窗口交易日）&lt; 15%。  
**过门：** 验证未直接否，且验证 TWR&gt;0 且 t&gt;1.0 → `VIABLE_HISTORICAL`。`candidate` 仍 false。

## 禁止

改 λ / hold / 特征 / 加 class_weight 去凑覆盖率；用 20bp；美股；A 股对冲；写进 Grok 提示词。
