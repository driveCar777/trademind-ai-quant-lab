# A_SHORT_FAILURE_DIAGNOSIS.md

> 失败诊断 / 错误分类系统（= §六 ERROR_CLASSIFICATION）。目的：结果异常时定位到具体一类，而不是只说 FAIL。

---

## 1. 十问 → 五类映射
用户的十个诊断问题归并为五个错误类 + 一个"正常无边"结论：
| # | 问题 | 类 |
|---|------|----|
| 1 数据问题 | → DATA_ERROR |
| 2 数据泄漏 | → DATA_ERROR (FUTURE_LEAK) |
| 3 universe 问题 | → DATA_ERROR (UNIVERSE) / 或 BASELINE_DESIGN |
| 4 模型问题 / 5 因子问题 | → MODEL_ERROR |
| 6 成本问题 | → COST_ERROR |
| 7 执行问题 / 8 撮合问题 | → EXECUTION_ERROR |
| 9 代码 bug | → 任一类的 `code_bug=true` 标注 |
| 10 环境差异 | → ENV_ERROR |
| （真的没边） | → `TRUE_NO_EDGE`（非错误，是结论） |

## 2. 分类枚举
### DATA_ERROR
`MISSING_BAR`（缺 K 线）、`WRONG_TIMESTAMP`（时间错位）、`FUTURE_LEAK`（未来数据进特征/归一化/universe）、`INCOMPLETE_UNIVERSE`（合格数不足/覆盖率低）、`DEGENERATE_PANEL`（全 NaN，已由 `panel_coverage` 捕获）、`DATA_BLOCKED`（无冻结字节）。

### MODEL_ERROR
`NO_PREDICTIVE_POWER`（gross 无显著超额）、`OVERFIT`（研究好/验证/OOS 崩）、`STYLE_EXPOSURE_ONLY`（收益=size/momentum β，非 selection alpha）、`UNSTABLE`（子期/regime 不稳）。

### EXECUTION_ERROR
`UNREALISTIC_FILL`（无视涨跌停/停牌成交）、`IGNORED_LIMIT_LOCK`、`IGNORED_SUSPENSION`、`T_PLUS_1_VIOLATION`（早于 T+1 卖）、`OVERLAP_OCCUPANCY_UNDERCOUNT`（carry 频繁但 chained net 未计重叠占用——**已知简化**）、`STUCK_MISPRICED`（STUCK 末收盘假设清算被当真实成交）。

### COST_ERROR
`TURNOVER_TOO_HIGH`（换手×成本吞噬）、`MIN_FEE_DOMINATED`（小单被 ¥5 最低佣金主导）、`SLIPPAGE_ASSUMPTION_UNVERIFIED`（滑点假设未实测，net 结论脆弱）。

### ENV_ERROR
`DEPENDENCY_MISMATCH`（numpy/py 版本差异致数值不一致）、`MISSING_DATA`（pack 未物化）、`NON_DETERMINISTIC`（复现失败）。

## 3. 判定信号（从观测层字段自动推断）
| 结论 | 触发信号（来自 SNAPSHOT/SIGNALS/TRADES/METRICS） |
|------|--------------------------------------------------|
| STYLE_EXPOSURE_ONLY | excess_vs_EW ≈ 0（t 不显著）但绝对收益正；DATA_SNAPSHOT 显示 Top-K 集中低价/小盘/高波动 |
| EXECUTION_ERROR | `n_entry_limit_lock` / `n_exit_limit_lock` / `n_stuck` 高；unfilled 高 |
| COST_ERROR | turnover 高 且 net≪gross；`min_fee_binding` 频繁 |
| DATA_ERROR | `degenerate` / 覆盖率低 / 合格数<MIN_ELIGIBLE / DATA_BLOCKED |
| OVERFIT | research 正、validation/OOS 反 |
| TRUE_NO_EDGE | gross、excess、net 全不显著，且执行/成本/数据均正常 |

## 4. ERRORS.json 结构
```json
{"run_id":"...","errors":[
  {"class":"COST_ERROR","code":"MIN_FEE_DOMINATED","evidence":{"min_fee_binding_rate":0.7},"code_bug":false,"severity":"HIGH"}
],"primary_conclusion":"STYLE_EXPOSURE_ONLY|TRUE_NO_EDGE|..."}
```

## 5. 纪律
- 分类只**诊断**，不触发任何自动"修复"（不改参数/universe/成本/合同）。
- 发现值得研究的方向 → 登记 `A_SHORT_D1_V2 HYPOTHESIS`，不实现。
- **不得**用"环境/数据"当借口掩盖 MODEL 无边；也**不得**把 MODEL 无边误判为数据问题——五类需各自证据。
