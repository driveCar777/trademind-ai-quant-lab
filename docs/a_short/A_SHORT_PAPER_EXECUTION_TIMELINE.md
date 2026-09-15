# A_SHORT_PAPER_EXECUTION_TIMELINE.md

> 推荐时点 ≠ 纸面成交时点（§1、§8）。**不得用不存在的 09:00 成交价。**
> 复用锚点：`paper_ops.py::freshness/plan`（三时钟/`fill_date`）、`capital_ref.py::exec_reason`（撮合）、`ml_v25/top_n_book::_exit_fill`。

---

## 1. 两个时间戳（硬区分）

```
Recommendation Timestamp   ≠   Paper Execution Timestamp
     ~08:58 (freeze)                09:30 (T 日开盘成交)
```
- **Recommendation Timestamp**：推荐冻结时刻（≈08:58），写入 `RECOMMENDATION_{date}.json`（immutable）。
- **Paper Execution Timestamp**：纸面成交时刻，模拟 **T 日 09:30 开盘价**（或定义好的实际成交时点），绝不用 09:00 的价（09:00 无成交）。

---

## 2. 每日执行时序（正常交易日）

```
~08:58  RECOMMENDATION_FREEZE   → RECOMMENDATION_{date}.json (immutable)
 09:00  WINDOWS_NOTIFICATION     → 后台直发 toast（有推荐才发）
 09:15  集合竞价开始（参考，不成交我们的单）
 09:25  PRE_OPEN_STATUS          → 读集合竞价/停牌/涨跌停，刷新可执行性
 09:30  PAPER_EXECUTION          → 按 09:30 开盘价撮合 BUY（T 日）
 ...    盘中不加仓/不做 T（当前阶段）
```
- 09:00 通知 → 09:30 成交之间的 30 分钟是**执行准备窗**：09:25 读 pre-open（停牌/一字涨停/竞价缺口）→ 决定哪些推荐**可执行**（Executable YES/NO）。
- 具体时刻可按数据源/市场规则优化，但顺序固定：**freeze < notify < pre-open < execution**。

---

## 3. 成交价规则（不臆造）

| 动作 | 成交价 | 规则 |
|------|--------|------|
| BUY（T 日建仓） | T 日 09:30 开盘价 | 一字涨停/停牌 → `LIMIT_LOCK`/`SUSPENDED` 不成交（`exec_ok_matrix`/`exec_reason`） |
| SELL（≥T+1） | 卖出日 09:30 开盘价 | 跌停/停牌卖不掉 → 顺延（`_exit_fill`，最多 10 日，`STUCK` 按最后收盘标） |
| 缺开盘价 | 不成交 | `MISSING_OPEN`，挂起不臆造 |

- **T+1 用交易日历判定**（§22），不是自然日 +1：`sellable = 成交日 ≥ buy_date 的下一交易日`。

---

## 4. Prediction → Recommendation → Paper Execution（§2）

```
Prediction:      P(T+1 > +5%) = 0.61        （模型概率/期望，数学事实）
   ↓
Recommendation:  A-grade                     （分级，Alpha 层，不看钱，immutable）
   ↓
Paper Execution: BUY 100 shares @ 09:30 open （Portfolio 层，看钱/手数/T+1/可执行）
```
三层不混算（详见 [A_SHORT_RUNTIME_ARCHITECTURE_V2.md](A_SHORT_RUNTIME_ARCHITECTURE_V2.md)）。

---

## 5. Outcome 结算时点（§24）

- 每条 Recommendation 记 `predicted` 与 `paper executable outcome` **两套**：
  - `predicted`：模型对 T+1/T+2/T+3/T+5 的预测 vs 实际（不管买没买到）。
  - `paper`：实际纸面成交后的 T+1/T+2/T+3/T+5 盈亏（受可执行性/T+1/成本影响）。
- 仅当实际开盘价在盘才结算（幂等），缺价挂起。

---

## 6. 与 Scheduler 对齐

各时刻由 Windows 任务计划触发（见 [A_SHORT_SCHEDULER_SPEC.md](A_SHORT_SCHEDULER_SPEC.md)）：
`...FreezeTask 08:58 → NotifyTask 09:00 → PreOpenTask 09:25 → ExecTask 09:30`。
每个是幂等端点；`run_id` 贯穿 freeze→notify→exec→ledger→outcome。
