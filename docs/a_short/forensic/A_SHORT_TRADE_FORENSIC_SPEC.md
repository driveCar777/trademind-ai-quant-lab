# A_SHORT_TRADE_FORENSIC_SPEC.md

> 信号快照 + 交易生命周期取证规范。目的：回答"为什么买这只 / 何时买 / 为什么没买到 / 为什么卖不掉"。

---

## 1. SIGNALS.json（逐日）
```json
{
  "date": "2025-01-02",
  "n_eligible": 3120,
  "top_rank": [
    {"symbol": "sz.000001", "score": 0.32, "rank": 1,
     "features": {"momentum20": 0.32},
     "eligibility_reason": "ELIGIBLE",
     "reject_reason": null}
  ],
  "excluded_sample": [
    {"symbol": "sh.600xxx", "reject_reason": "NOT_LISTED_MIN_HIST"},
    {"symbol": "sz.30xxxx", "reject_reason": "SUSPENDED"}
  ]
}
```
必存：`symbol / score / rank / feature values / eligibility_reason / reject_reason`。
- `eligibility_reason`：ELIGIBLE 或未入选原因（NOT_LISTED / NOT_TRADING / NO_CLOSE / BELOW_MIN_HIST / BOARD_FILTERED）。
- `reject_reason`：进入排序后未进 Top-K 的原因（BELOW_TOPK / NO_LOT / BUDGET_CUT）。
- 现状：这些在 `top_k_period` 内是**内存变量**（picks/names/status）——落盘即可，无需改逻辑。
- feature values 当前只有 `momentum20`；未来因子加入时同结构扩展（新合同）。

## 2. TRADES.json（逐笔生命周期）
状态机（**派生自 `top_k_period` 输出，不改撮合**）：
```
CANDIDATE → SELECTED → ORDER_PLANNED → ENTRY_ATTEMPT
   → ENTRY_FILLED | ENTRY_FAILED
   → HOLDING → EXIT_PLANNED → EXIT_ATTEMPT
   → EXIT_FILLED | EXIT_BLOCKED(→carry) → CLOSED | STUCK
```
每步记录：`state, timestamp(交易日), symbol, price(若有), reason, market_status(tradestatus), limit_status(LIMIT_LOCK?), suspension_status(SUSPENDED?)`。

映射自现有字段：
| 现有字段（top_k_period per-name） | 生命周期含义 |
|-----------------------------------|--------------|
| `entered=False, status=entry_reason` | ENTRY_FAILED（reason=LIMIT_LOCK/SUSPENDED/MISSING_OPEN/…）→ 未 CLOSED |
| `status="NO_LOT"` | SELECTED→ORDER_PLANNED→ENTRY_FAILED(NO_LOT/资金不足) |
| `entered=True, status="FILL"` | ENTRY_FILLED→HOLDING→EXIT_PLANNED→EXIT_FILLED(planned)→CLOSED |
| `status="FILL_CARRY_k"` | EXIT_PLANNED→EXIT_BLOCKED(`exit_block_reason`)→carry k 日→EXIT_FILLED(actual_exit)→CLOSED |
| `status="STUCK"` | EXIT_BLOCKED 到底→STUCK（末收盘标记，flag，**非成功成交**） |
| `planned_exit / actual_exit / forced_hold_days` | 计划 vs 实际退出、强制持有天数 |

## 3. 特别计数与样本（必须单独留）
| 情形 | 计数字段（已有） | 需补 |
|------|------------------|------|
| 涨停买不到 | entry `LIMIT_LOCK` | 单独 `n_entry_limit_lock` + 样本 |
| 跌停卖不了 | exit `LIMIT_LOCK`（→carry/STUCK） | `n_exit_limit_lock` + 样本 |
| 停牌 | `SUSPENDED`（entry/exit） | 分 entry/exit 计数 + 样本 |
| 流动性不足 | `ZERO_VOLUME` / `NO_LOT` | 计数 + 样本；**注：当前无 ADV/成交额门**，流动性陷阱风险须在报告显式提示 |
| 缺开盘 | `MISSING_OPEN` | 计数 + 样本 |

## 4. LEDGER.json
`cash_out_incl_fees`、per-name net、invested、cash_after_fees（若适用）；**校验** `cash_out_incl_fees ≤ strategy_capital ≤ equity`（负现金 → ERRORS 记 EXECUTION/COST_ERROR）。

## 5. 复现要求
SIGNALS/TRADES 在 same code+data+config+seed 下逐位可复现（除 timestamp 元数据）。测试对"去时间戳后的 SIGNALS/TRADES"做等值断言。
