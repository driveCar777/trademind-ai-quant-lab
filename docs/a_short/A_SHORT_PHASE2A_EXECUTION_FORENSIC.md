# A_SHORT_PHASE2A_EXECUTION_FORENSIC.md — Phase 2A.1

> 执行模型正确性复审。流程：Audit → Reproduce → Prove bug → Minimal Fix → Tests → Re-audit → Report。
> 范围仅 `research_engine/cn_a_short/{account,baseline,cost}.py` + tests + `docs/a_short/`。**未改** ML1/V25/V26/V33/V34/V38、冻结 dataset、frozen contract、paper ledger、真实交易路径。

---

## 1. Audit scope
- `account.py`：affordability（`lots_for`/`feasible_portfolio`）是否含手续费；「无负现金」断言约束的是 notional 还是 true cash。
- `baseline.py`：`_fill_reason` / `top_k_period` / `evaluate` 的 entry/exit 对称性——entry 成交但 planned exit 失败时是否被错误当成「从未买入」。
- `cost.py`：canonical 成本常量（未改，仅被引用）。

## 2. Cash-affordability findings（Audit 1）
**BUG 确认。**
1. `lots_for()` 只按**份额成本**（含滑点，若传入），**不含 commission / transfer**。
2. `top_k_period` 旧逻辑 `lots = alloc // (LOT*o0*(1+slip))` 同样不含手续费。
3. `feasible_portfolio` 的 `assert invested <= equity` 约束的是**名义投资额（notional）**，**不是**扣费后 true cash。
4. ¥5 最低佣金 → 「名义可行但真实现金不可行」：每名超支 ≈¥5，多名累加超过 strategy capital。
   - 证据（repro）：`¥20k × Top10 @¥20`：`invested(notional)=¥20,000 ≤ equity`（断言通过），但 `true cash out = ¥20,050.20 > ¥20,000` → **真实现金为负 ¥50.20**。
5. 回答「断言约束谁」：**约束 invested（notional），不是 true cash after fees** → 断言无效。

## 3. Entry/exit findings（Audit 2）
**BUG 确认。** `_fill_reason(pack,t0,t1,j)`：entry(t0)=FILL 但 exit(t1)≠FILL 时返回 exit 的 reason；`top_k_period` 见非 FILL 即 `continue`（net 0、不建仓、不计成交）。
→ **「已买入但计划退出失败」被错误转成「从未买入」**（`n_fill=0, invested=0, pnl=0`），尽管 entry 可执行。这是 round-trip 双腿门，冒充了 capital path。

## 4. Synthetic reproduction cases
均可复现（脚本见提交历史/可重跑）：
| 用例 | 结果（fix 前） |
|------|---------------|
| 低价低账户 alloc¥2000 @¥20 | notional¥2000，actual_cash_out¥2005.02 **超支¥5.02** |
| 近 ¥5 最低佣金 alloc¥20000 @¥20 | actual¥20005.20 **超支¥5.20** |
| 高价股+小额 alloc¥10000 @¥100 | actual¥10005.10 **超支¥5.10** |
| 多名 ¥20k×Top10 | true cash **−¥50.20**（断言仍通过） |
| entry FILL + exit LIMIT_LOCK@t1 + FILL@t1+1 | status=LIMIT_LOCK, **n_fill=0, invested=0**（当作没买） |

## 5. Root cause
- **Affordability**：把「一手份额成本」当成「可支付性」，漏掉 `_fee`（commission floored ¥5 + transfer）；不变量写在 notional 上。
- **Entry/Exit**：把 round-trip 双腿可执行性当作建仓条件；缺少 **capital-path exit recovery**（entry 后强制持有到下一个可卖日）。

## 6. Minimal fix（§C 决策 = Option 2，最小可审计）
**Affordability（account.py）**
- 新增 `buy_cash_out(notional)=notional+_fee(notional)`；新增 `lots_affordable(alloc,price,slip)`（fee-aware，逐步递减到 true cash ≤ alloc）。
- `feasible_portfolio` 改用 `lots_affordable`，输出 `cash_out_incl_fees / cash_after_fees`，断言改为 **true cash**：`total_cash_out ≤ budget ≤ equity` 且 `cash_after_fees ≥ 0`。
- `lots_for` 保留但明确注释=notional-only，非可支付性判据。

**Entry/Exit（baseline.py，Option 2 = 最小 capital-path exit-recovery）**
- entry 非 FILL → 从不建仓（正确）。
- entry FILL → **一定建仓**；planned exit 不可卖 → `_find_exit` 向后找第一个可卖日（carry，`EXIT_CARRY_MAX=10`）；找不到 → `STUCK`（按最后收盘标记并 flag）。
- 逐名记录：`planned_exit / actual_exit / forced_hold_days / exit_block_reason / status(FILL|FILL_CARRY_k|STUCK)`；期级记录 `n_entry / n_round_trip_clean / n_exit_carry / n_stuck / forced_hold_days_total`。
- lot sizing 改为 fee-aware（cash out 含买费 ≤ alloc）。
- 保留 `exit`（=planned_exit）与 `n_fill`（=n_entry）别名，兼容原测试。

**§C 语义澄清（不静默修复）**
- `ROUND_TRIP_EXECUTABILITY`（两腿是否都可执行）与 `CAPITAL_PATH_EXECUTABILITY`（entry 后强制持有直到可退出）**已显式区分**。本引擎现为 **capital-path**（Option 2）；`n_round_trip_clean` 仍单列出「两腿当日都成」的子集，供审计。

### Exact changed files
```
research_engine/cn_a_short/account.py      # fee-aware affordability + true-cash invariant
research_engine/cn_a_short/baseline.py     # entry/exit asymmetry -> capital-path exit recovery
research_engine/cn_a_short/tests/test_account.py   # fee-aware affordability regressions（更新2条旧断言：其编码了 bug 行为）
research_engine/cn_a_short/tests/test_baseline.py  # 更新1条（原 test_limit_lock 编码 bug）+ 新增 5 条 entry/exit + true-cash
docs/a_short/A_SHORT_D1_RESEARCH_CONTRACT.md / A_SHORT_D1_BASELINE_SPEC.md / A_SHORT_PHASE2A_RESULTS.md  # specified≠implemented + 术语
docs/a_short/A_SHORT_PHASE2A_EXECUTION_FORENSIC.md  # 本文件（新增）
data/market/research_engine/cn_a_short/PHASE2A_TABLES.json  # 由 report_tables 重算（fee-aware，数值几乎不变）
```
> 更新（非删除）了 3 条原测试，因为它们**断言了 bug 行为**（¥2000 能买 ¥2000 一手；exit-limit-lock 当作未成交）。已在此逐条列明，其余原测试未改。

## 7. New invariants（现由测试强制）
```
I1  actual_cash_out(name) = buy_notional + buy_slippage + commission(floored ¥5) + transfer
I2  actual_cash_out(name) <= per-name alloc
I3  sum_name actual_cash_out <= strategy_capital(=exposure*equity) <= equity     # 无负现金（true cash）
I4  entry FILL  => 仓位一定被记账（n_entry++/invested>0），永不被 exit 失败抹成「未买入」
I5  entry !=FILL => 从不建仓（net 0）
I6  planned_exit 不可卖 => carry 到 actual_exit；超过 EXIT_CARRY_MAX => STUCK（仍是持仓，flag）
I7  PREDICTION(planned open-to-open gross) 与 STRATEGY(realized net on actual_exit) 分离
```

## 8. Test evidence
```
python -m pytest research_engine/cn_a_short/tests/ -q
=> 32 passed, 0 failed, 0 skipped
```
新增/更新覆盖（§D）：min-fee-aware affordability、multi-name true-cash 非负、one-lot 边界、entry FILL+exit LIMIT_LOCK（carry）、entry FILL+exit SUSPENDED（carry）、exit 永不恢复（STUCK）、period cash-out≤equity、entry-block 未建仓。
Re-audit repro（fix 后）：`¥20k×Top10@¥20 → feasible=False`（正确，原来是隐藏负现金）；`entry FILL + exit LIMIT_LOCK → status=FILL_CARRY_1, entered=True, forced_hold=1, block=LIMIT_LOCK`。

## 9. Remaining limitations（BAD NEWS，主动列出）
1. **经验 alpha 仍 DATA_BLOCKED**：本 VM 无 D1 价格面板；执行模型已修，但 Q1–Q7 仍需在 :9000 物化 pack 后才能跑。
2. **forced-hold 重叠**：carry 可能使持仓越过下一个 signal（当前 chained strategy 仍按 planned hold 非重叠步进）；完整重叠组合会计**未实现**，属已知简化，`evaluate` 的 chained net 在高 carry 情形会低估重叠成本/占用——需在真实数据上检视 carry 频率后再决定是否升级。
3. **STUCK 按最后收盘假设清算**：真实可能继续被锁；这是保守建模，已 flag，不当真实成交。
4. **滑点 = UNKNOWN**：0.1%/侧是假设；net 对其极敏感。
5. **feasible_portfolio fee-aware 保守**：等额 alloc 恰为整手倍数时可能少买 1 手（为覆盖 ¥5 费）；生产可用共享费用池优化，此处取保守可审计版。
6. **特征仅动量 baseline 已实现**；合同特征族/信息层未实现（§F）。

## 10. Explicit decision
```
ROUND_TRIP vs CAPITAL_PATH:   已显式区分；引擎=capital-path(Option 2)
Cash affordability:            已修（fee-aware, true-cash invariant, 8 项不变量测试）
Entry/exit asymmetry:          已修（entry-filled 永不被抹除；exit-recovery + STUCK）
Empirical baseline in cloud:   仍 DATA_BLOCKED（环境，无关正确性）

DECISION: READY_FOR_D1_DATA_RUN
```
执行模型已正确；唯一阻塞经验结果的是**数据物化**（环境限制），非模型缺陷。可在 :9000 主机物化 frozen D1 panel 后运行首次 empirical A-Short D1 baseline。
