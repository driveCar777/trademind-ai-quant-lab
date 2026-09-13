# HOT_MT5_ATR_BARRIER_V3 一次读取

> 2026-09-13。合同先冻。`candidate=false`。不覆盖 V1/V2。不改 k。

## 机制

`1×ATR/close×√hold` 事先是：黄金中位 378bp、原油 632bp、外汇 129–171bp。标签 CASH **79–88%**。模型学会了休息，验证期成交 0–8 笔，覆盖 1–12%，全部 `VALIDATION_COVERAGE`。

这是设计里写过的「一直空仓」否决：空仓成功，不是策略。

| 品种 | 标签 CASH | 中位门槛 | 全样本 TWR | 覆盖 | 验证笔数 | 判决 |
|------|-----------|----------|------------|------|----------|------|
| GOLD | 82.5% | 378bp | −12% | 12.4% | 8 | NO_CANDIDATE |
| CRUDE | 86.7% | 632bp | −36% | 4.3% | 2 | NO_CANDIDATE |
| EURUSD | 78.9% | 155bp | +10% | 5.7% | 0 | NO_CANDIDATE |
| USDJPY | 78.8% | 159bp | −6% | 7.6% | 0 | NO_CANDIDATE |
| GBPUSD | 87.1% | 156bp | −4% | 1.8% | 3 | NO_CANDIDATE |
| USDCAD | 88.0% | 129bp | −6% | 1.1% | 2 | NO_CANDIDATE |
| USDCHF | 79.2% | 171bp | +20% | 6.7% | 0 | NO_CANDIDATE |

欧美 / 美瑞全样本略正，验证 0 笔，**不升格**。不要把 k 改小去凑 15% 覆盖——那是看完再选。

`HOT_MT5_ATR_BARRIER_V3_NO_CANDIDATE`。下一刀按队列：V4 12 月 TSMOM（无 ML）。
