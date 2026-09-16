# A-Short Phase 6 — Research Operation System Design

> **Audit + Design only. No code, no baseline/contract/universe/param/data-source change, no alpha run, no LLM.**
> 目标：建立 Cloud ↔ Local 研究运行闭环（Cloud=代码/审计/分析；Local=冻结数据/回测/训练）。

## 文档
| 文件 | 内容 |
|------|------|
| [CLOUD_LOCAL_ARCHITECTURE.md](CLOUD_LOCAL_ARCHITECTURE.md) | Cloud/Local 职责边界 + 闭环 + 存储 allow/deny + 失败框架 + 八问速答 |
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | experiment_id 绑定 dataset/code/contract/param/model/result/failure_class |
| [FAILURE_ATLAS_DESIGN.md](FAILURE_ATLAS_DESIGN.md) | 失败知识库（五类 + 证据 + do_not_retry） |
| [RESEARCH_MEMORY_DESIGN.md](RESEARCH_MEMORY_DESIGN.md) | research_memory/（accepted/rejected/experiments/hypothesis/failures/decisions），防重复 |
| [LOCAL_RUNTIME_PROTOCOL.md](LOCAL_RUNTIME_PROTOCOL.md) | 本地 数据→experiment→runs/RUN_ID→report→GitHub→Cloud；大数据策略 |
| [PHASE6_DECISION_REPORT.md](PHASE6_DECISION_REPORT.md) | 五问 + 八项验收 + STATUS |

## 与现有实现的关系
- 复用 Phase 3 forensic 层（`research_engine/cn_a_short/forensic/`）已产出的 `runs/RUN_ID/` bundle；Phase 6 只加**协议/记忆/图谱**文档。
- 取代 `docs/a_short/DATA_STORAGE_POLICY.md` 的存储段（本 Phase 的 LOCAL_RUNTIME_PROTOCOL §大数据）。
- 失败五类与 `forensic/errors.py` 对齐；`SOFTWARE_ERROR` 映射代码的 `ENV_ERROR + code_bug`（命名待未来 reconcile，本阶段不改代码）。

## STATUS
PASS（design delivered）。empirical 仍 DATA_BLOCKED（Phase 4）；闭环 Local 端待 owner 本地物化数据后启用。STOP after documentation。
