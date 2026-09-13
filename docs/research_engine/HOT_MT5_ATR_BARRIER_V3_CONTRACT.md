# HOT_MT5_ATR_BARRIER_V3 合同（跑前冻结）

> 2026-09-13。长任务队列第 2 步。V2 法医已证明 2×META 成本相对 5/10 日波动太矮，空仓没发生。
> **不是**加大 V2 的 λ，**不是**法医 20bp。m 另计。只算一次。`candidate=false`。

## 数据 / 特征 / hold

与 V1/V2 同一批 D1+META、同一特征清单、同一持有期（GOLD 10，其余 5）。不重拉。美股不做。

## 标签（成交前写死）

`y` = t+1 开盘 → t+1+hold 开盘的价格变动。

`atr_frac[t] = ATR14[t] / close[t]`（只用 t 及以前的高低收）。

`hurdle[t] = 1.0 × atr_frac[t] × √hold`

1.0 是布朗运动一倍标准差，Lopez de Prado 三重障碍的默认宽度，不是从 V2 覆盖率反推的。

- `y > hurdle` → LONG
- `y < −hurdle` → SHORT
- 其余 → CASH

## 模型 / 策略 / 成本 / 闸门

与 V2 相同：一个 LGBM 三分类（无 class_weight），argmax，CASH 次日再看，多空下一开盘、非重叠。成本 = 点差 + 2×2bp + 实际隔夜。

验证成交 &lt; 8 或验证覆盖 &lt; 15% → `NO_CANDIDATE`。否则验证 TWR&gt;0 且 t&gt;1 → `VIABLE_HISTORICAL`，`candidate` 仍 false。

主报告 = 全样本。年切片只诊断。

## 禁止

改 k / hold / 特征；退回 2×成本或 20bp；美股；A 股对冲；写 Grok；覆盖 V1/V2 `READ.json`。
