# CURRENT_MODEL_REALITY.md

> 当前模型现实（只看代码）。详版见 `forensic/CURRENT_MODEL_REALITY.md`；本文件是交接层速览。

---

## 当前真实模型
```
ONLY: 20D_MOMENTUM_BASELINE
```
`research_engine/cn_a_short/baseline.py::momentum_scores(pack, t, lookback=20)` = `close(t)/close(t-20) - 1`。**这是唯一进入打分/排序的信号。**

## 不是
- ❌ AI 模型
- ❌ LLM 模型
- ❌ 热点模型
- ❌ 龙头模型
- ❌ 多因子模型
- ❌ ML（LightGBM 等；ML1 有，A-Short 未接）

## Specified ≠ Implemented
- **Specified（合同 §4 登记，未实现）**：short reversal / overnight gap / intraday-vs-overnight / volume·amount acceleration / turnover anomaly / range position / volatility / market breadth / limit-up state / recent limit-up count。
- **Implemented**：仅 20D 动量打分 + 撮合/成本/账户/评估**引擎**。
- **引擎 ≠ alpha**：撮合/成本/评估成熟且已测（33 tests），但信号只有动量。

## 重要提醒
- 20D **lookback=20** 是中周期信号，与「T+1~T+5 超短线」意图方向不符（持有期短，信号中周期）。
- ALL universe + 无质量过滤 ⇒ 动量 Top-K 天然偏小盘/低价/高波动（`CURRENT_UNIVERSE_REPORT.md`）；任何未来收益先扣小盘 β。
- **未证明任何 alpha**；Cloud 无 empirical（DATA_BLOCKED）。**不得宣称策略/收益。**
