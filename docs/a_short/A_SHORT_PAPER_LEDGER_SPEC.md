# A_SHORT_PAPER_LEDGER_SPEC.md

> 纸面账本设计（§11–19）。**PAPER ONLY · LONG ONLY · 禁 `order_send`。**
> 复用锚点：`master/api/app/service/paper_ops.py`（journal→账户派生、费用、原子写、锁）、`cn_a_share_alpha/cost.py`（成本）、
> `cn_a_share_strategy_v14_1/capital_ref.py`（撮合/`exec_reason`）、`ml_v25/top_n_book.py::_exit_fill`（阻塞出场）。

---

## 1. 账户模型（§13）

| 参数 | 语义 | 约束 |
|------|------|------|
| `initial_capital` | 起始本金（如 ¥20,000） | >0，用户设 |
| `max_capital` | 当前允许策略使用的资金上限 | ≥0；超出部分闲置 |
| `contribution` | 定投：`on/off` + `frequency`(monthly) + `amount`(如 ¥2,000) | 记 `CONTRIBUTION` 事件 |
| `withdrawal` | 取现（如 −¥5,000） | **任何情况下不得使 cash<0**（§13） |

现金/持仓**全部由事件派生，不落地存储**（复用 `paper_ops.derive_account`：BUY 扣 `amount+fee`、SELL 加 `amount−fee`、FIFO 持仓、`_last_close` 盯市、缺价标 `mark_missing` 不置 0）。

---

## 2. Ledger 不变量（§14）——违反即报错，禁止偷偷修正

```
cash >= 0
shares >= 0            # LONG ONLY: shares < 0 直接判 invariant violation
equity >= 0
position_value >= 0
```
- `shares < 0` / `cash < 0` → 抛 `LEDGER_INVARIANT_VIOLATION`，**停在失败态**（不 clamp、不续跑）。
- withdrawal 若会导致 `cash<0` → 拒绝该取现事件并提示，不部分执行。
- 每次写账本前后校验（沿用 `paper_ops` 的 `derive_account` 重算 + `recon_ok` 思路）。

---

## 3. 交易规则（§11、§12）

支持 `BUY / SELL / HOLD`；不支持 `SHORT / BORROW / MARGIN SHORT`。

**T+1（§12）严格模拟**：
```
T   BUY A          → T 当日 A 不可卖
T+1 可 SELL A       (最早)
```
- 每持仓记 `buy_date`；`sellable_today = (今日 > buy_date 的下一交易日及以后)`。复用 hot desk `_sellable(buy_date, fresh)` 而非 ML1 的「顺延note」。
- 撮合按真实规则：`next-open` 成交、`suspension/limit-up/limit-down/zero-volume/unavailable-open/execution-failure` 用 `exec_ok_matrix` + `exec_reason`（`DELISTED/SUSPENDED/MISSING_OPEN/ZERO_VOLUME/LIMIT_LOCK/FILL`）判定；卖不掉顺延（`_exit_fill`，`EXIT_CARRY_MAX=10`，最终 `STUCK` 按最后收盘标记）。
- `lot size = 100 股/手`；不足一手不可买。

---

## 4. 成本模型（§12）——复用 `cost.py`

| 项 | 值 | 出处 |
|----|----|------|
| 佣金 | `max(¥5, 额×0.00025)` +过户 0.00001 | `top_n_book._fee`（¥5 最低），`cost.py` |
| 印花税（卖） | 0.0005（2023-08-28 起，之前 0.0010） | `cost.py::stamp_duty_sell`（`STAMP_CUT`） |
| 滑点 | 0.0010（可 stress） | `cost.py::SLIPPAGE`,`stress_mult` |
| 往返 | buy+sell+印花 ≈ 0.27%+0.05% | `cost.py::round_trip_cost` |

> **成本天花板警示（写在最前）**：T+1..T+5 换手 ≈ V26.8 的 21×，每往返 ≈0.27%+印花+¥5 最低。
> **必须在建模前先算「换手×成本」**，否则重演 `MT5_STOCK_CFD_COST_CEILING`（V30 因此判死）。详见风险文档。

---

## 5. 资金规模 ⟂ Alpha（§15、§16）

- Alpha 推荐不看账户；`RECOMMENDATION_{date}.json` immutable。
- 账户/手数约束在 **Portfolio 层**决定「可执行」：
```
Alpha Recommendation → Account Constraint → Lot Constraint → Execution Feasibility
A = Alpha YES / Executable NO   (¥2000 买不起一手)
C = Alpha YES / Executable YES
```
- 资金变大 → 可执行组合变大（§16），但**基础 Alpha model 不变**。两层严格分文件/分快照。

---

## 6. 动态持仓数（§17）

不固定 10 只；允许 `0/3/5/8/12/20/30/...`，由 `Opportunity / expected_return / confidence / downside / correlation / liquidity / capital_feasibility` 决定。
`0` = NO TRADE 合法（§5）。持仓数是 Portfolio 层输出，不反向改 Alpha。

---

## 7. 自动纸面记账流程（§18、§19）

```
Recommendation → Portfolio Decision → Capital Feasibility → Lot Feasibility
→ T+1 Rule → Paper Execution → Ledger
```
**每笔纸面成交必须记录（§18）**：
```json
{
  "recommendation_id": "...", "paper_order_id": "...",
  "stock": "sh.600xxx", "side": "BUY|SELL",
  "intended_price": 0.0, "executed_paper_price": 0.0,
  "quantity": 0, "fees": 0.0, "slippage": 0.0,
  "reason": "FILL|LIMIT_LOCK|...", "execution_timestamp": "...",
  "strategy_version": "ashort_vX", "model_version": "REFIT_..."
}
```
- **禁止「推荐 5 只 = 假设全买」**（§18）。推荐 ≠ 一定买得到（§19）：保留 Recommendation 与 Paper Execution 两层。
- 推荐产生后可**自动**进入 Paper Ledger（§19），但仍经 Portfolio/Feasibility/T+1 三关。

---

## 8. Immutable 账本 + 快照（§43）

- `RECOMMENDATION_{date}.json` 生成即冻结，后续不可改（可完整回答「为什么当天推荐」，追溯到 Raw Evidence）。
- 成交日志（journal 事件）可增/改/删（人工纠错），但**账户永远由事件派生**，改一条不会双计（幂等，沿用 `paper_ops` §29.8）。
- 账本文件与 ML1 的 `LEDGER_TOP20.json` **分目录、永不混算**（沿用「两条链不混」原则）：A-Short 用 `live/ashort/JOURNAL.json`、`LEDGER_ASHORT.json`。
- 原子写（tmp+`os.replace`，沿用 `paper_ops._dump`）。

---

## 9. Contribution / Withdrawal 事件（§13）

- 定投：每月首个交易日记 `CONTRIBUTION`（金额可配）；未登记则 GUI 提示（沿用 `_contrib_logged` 警告式，不自动入金）。
- 取现：记 `WITHDRAWAL`（负额），先校验 `cash≥0` 才允许。
- equity 曲线含 deposit/withdrawal（用 TWR 剔除现金流影响，沿用 `scale_book::daily_curve`/`top_n_book.summarize` 的 TWR/IRR 口径）。

---

## 10. 结算与 Outcome（§44）

- 每推荐建 `T+1/T+3/T+5 outcome`，记 `prediction / actual / error`。
- 仅当实际开盘价在盘（`open_price(symbol, fill_date)` 存在）才结算，缺价挂起不臆造（沿用 fusion 结算幂等）。
- 用于 calibration / model evaluation / failure analysis；结果按 `FAILURE_ATLAS` 格式追加（`post_v21_atlas_append.py`）。

---

## 11. 不做的事（当前阶段）

不加个股止损/止盈/做 T/提前卖当**策略**（V34 `EXIT_RULES_NO_IMPROVEMENT`；出场规则 `_trigger` 仅作诊断，不写进主路径）；不 SHORT；不 margin；不 `order_send`；不为凑收益改 hold/成本/仓位。
