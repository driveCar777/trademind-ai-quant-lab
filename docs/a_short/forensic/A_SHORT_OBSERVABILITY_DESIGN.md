# A_SHORT_OBSERVABILITY_DESIGN.md

> `A_SHORT_FORENSIC_OBSERVABILITY_LAYER` 总设计。目的：任何未来实验结果异常，都能定位到 数据/泄漏/universe/模型/因子/成本/执行/撮合/代码/环境 十类之一。**观测层只解释结果，不改变结果。**
> 阶段：Design（docs only）。实现见 `CURRENT_OBSERVABILITY_AUDIT.md §3`（Phase 3，待确认）。

---

## 1. 原则
- **不改 alpha/合同/参数/universe/数据源**；观测层是**旁路持久化 + 派生分析**，挂在 `top_k_period`/`evaluate` 输出之上。
- **薄层**：最大化复用已有字段（`_meta`、per-name lifecycle、`panel_coverage`、`evaluate` 指标）。
- **可复现优先**：每个 RUN_ID 自包含（代码/数据/配置/结果）。
- **坏消息可见**：REPORT 必须回答"为什么不赚钱"，不能只 FAIL。
- **默认可关 / 失败不打断**：`--no-forensic`；观测异常只记录进 ERRORS，不影响主结果。

## 2. 组件与产物
```
results/runs/<RUN_ID>/
  RUN_MANIFEST.json    ← 代码/数据/模型/成本/执行 版本 + seed（见 RUN_MANIFEST_SPEC）
  CONFIG.json          ← 本次运行入参（window/equity/boards/topk/horizons/model）
  DATA_LINEAGE.json    ← upstream/derived id+hash + pack meta + coverage
  DATA_SNAPSHOT.json   ← 股票池构成 + 质量分布（见 §3）
  SIGNALS.json         ← 逐日 rank + feature + eligibility/reject（见 TRADE_FORENSIC_SPEC §1）
  TRADES.json          ← 逐笔生命周期（见 TRADE_FORENSIC_SPEC §2）
  LEDGER.json          ← 账本/资金流（cash_out_incl_fees、净额、无负现金校验）
  METRICS.json         ← evaluate 指标 + attribution（见 EXPERIMENT_REPORT_SPEC §Attribution）
  ERRORS.json          ← 错误分类（见 FAILURE_DIAGNOSIS）
  REPORT.md            ← 自动 11 节报告（见 EXPERIMENT_REPORT_SPEC）
```
> 大件（逐日 SIGNALS/TRADES）走 gitignore，只提交小 manifest/REPORT（`DATA_STORAGE_POLICY.md`）。

## 3. 四个新增快照/分析（其余为已有字段落盘）
1. **DATA_SNAPSHOT**：total/eligible/excluded symbols；board 计数（主板/创业/科创/北交所）+ ST 计数；price/turnover/volatility 的 min/median/max + 关键分位。目的：**证伪"只是买垃圾小票"**。
2. **SIGNALS**：每日 top_rank 列表（symbol/score/rank/features/eligibility_reason/reject_reason）。目的：回答"为什么买这只"。
3. **Trade lifecycle**：CANDIDATE→…→CLOSED 状态机（派生自 per-name 结果）。目的：回答"何时买/为什么没买到/为什么卖不掉"。
4. **Attribution**：Total = Beta + Sector + Size + Momentum + Selection − Cost（基础版：benchmark/excess/topk contribution/best-worst 10；size/momentum 用现有字段近似并标注）。目的：回答"收益来自哪里"，防 β 错觉。

## 4. 与现有代码的接线（最小）
| 现有 | 接线动作 |
|------|----------|
| `run_baseline.run()` | 开头建 RUN_ID+目录+RUN_MANIFEST/CONFIG/DATA_LINEAGE；结尾写 SNAPSHOT/SIGNALS/TRADES/LEDGER/METRICS/ERRORS/REPORT |
| `baseline.top_k_period` 输出 | `lifecycle.py` 在其**输出上**派生状态机（不改函数） |
| `baseline.panel_coverage` | `snapshots.data_snapshot` 复用 + 扩展 board/ST/质量分布 |
| `baseline.evaluate` 指标 | `attribution.py` + `METRICS.json` |
| `_meta()` | 扩展为完整 RUN_MANIFEST |

## 5. 不做（scope freeze）
不新增因子/不调 hold/不改 universe/不接 LLM/新闻/GUI/交易/不改冻结 lineage。观测层若"发现"某过滤/因子值得研究 → 只在报告里登记为 `A_SHORT_D1_V2 HYPOTHESIS`，不实现。

## 6. 分期
- **Phase 1（本轮）**：Audit + 本组设计文档。
- **Phase 3（待确认）**：`cn_a_short/forensic/` 6 文件 + `run_baseline` 接线 + `tests/test_forensic.py`。合成 pack + DATA_BLOCKED 路径可测；真实快照待数据。
