# PHASE6_DECISION_REPORT.md

> Phase 6 决策报告。回答五问 + 八项验收。**只设计，不实现。**

---

## 五问
### 1. Cloud 和 Local 边界是否明确？
**是。** Cloud = 架构/代码/审计/文档/**报告分析**（无 124GB 数据、不大回测、不训练、不长跑）；Local = 冻结数据/大回测/ML 训练/长跑/产报告。GitHub = 只存 code/docs/tests/小 json/manifest/报告，**禁** raw/cache/weights/secrets。见 `CLOUD_LOCAL_ARCHITECTURE.md`。

### 2. 未来 ML/DL 在哪训练？
**Local Windows only**（有数据、可 GPU、可长跑）。Cloud 不训练（无数据/无 GPU）。训练产物（weights）**不入 GitHub**（禁），留本地；只推 report/metrics。ML/DL 启动须先过 Phase 5 roadmap 的 Gate B（数值因子扣成本后有边）。

### 3. LLM 在哪使用？
- **能力**：信息整理 / 报告分析 / 事件与矛盾理解 / 候选复核（Cloud 或 Local 皆可调）。
- **硬禁**：LLM 直接预测股票、当 alpha 生成器、拿真实交易权。LLM = **信息整理层**（Decision A-001 + phase5 `A_SHORT_MODEL_PIPELINE_V2.md`）。
- **时机**：Phase D，在数值因子证明有边之后；新闻/政策历史回测须先建 timestamped PIT 语料。

### 4. 实验失败如何避免重复？
`research_memory/`（hypothesis/experiments/accepted/rejected/failures/decisions）+ `FAILURE_ATLAS.json`。**新实验 REGISTER 前必须查 rejected/ + atlas**，命中 `do_not_retry` 即拒绝（除非新数据/新合同/新证据）。Cloud 分析每份报告后必须回写记忆。见 `RESEARCH_MEMORY_DESIGN.md` / `FAILURE_ATLAS_DESIGN.md`。

### 5. 如何保证 10 年后还能复现？
每个 experiment 绑定 `dataset_hash + derived_dataset_hash + code_commit + parameter_hash + model_version + manifest_hash + seed + windows`（`EXPERIMENT_PROTOCOL.md`）。给定这些即可精确重建“哪份代码/数据/参数/模型”；`manifest_hash`（排除 time/commit/env）作为“同语义输入→同结果”的判定键。前提：冻结数据集字节由 owner 长期保存（本地 SSD + 可选对象存储，保 id+hash 不变；**不换源/不改 hash**）。

---

## 八项验收速答
| # | 问题 | 答 |
|---|------|----|
| 1 | 代码在哪开发 | Cloud VM |
| 2 | 数据在哪保存 | Local Windows（SSD，system-of-record）；GitHub 只存小 json/报告 |
| 3 | 实验在哪运行 | Local Windows（大回测/ML）；Cloud 只跑测试/静态分析 |
| 4 | 结果如何回传 | runs/RUN_ID → experiment_reports/ 推 GitHub → Cloud 拉取分析 |
| 5 | 亏损原因如何判 | 五类归类（DATA/MODEL/EXECUTION/COST/SOFTWARE）+ forensic 证据链 |
| 6 | 如何避免重复踩坑 | research_memory + FAILURE_ATLAS，实验前先查 |
| 7 | 何时用 Cloud 模型 | 报告分析/信息整理/审计（非 alpha、非交易） |
| 8 | 何时用本地 Cursor | 需冻结数据/大回测/ML 训练/长跑时 |

---

## 现状与约束
- **数据仍 DATA_BLOCKED**（Cloud 无冻结字节，Phase 4）；本闭环的 Local 端待 owner 在本地物化 pack 后启用。
- 本阶段**未改** baseline/合同/universe/参数/数据源，**未跑** alpha，**未实现** LLM。
- 现有 forensic 层已产出所需 `runs/RUN_ID/` 产物；Phase 6 只在其上加**协议/记忆/图谱**（文档），代码接线（`parameter_hash`、拆分 environment/attribution 文件、research_memory 落盘）留待未来最小实现，**不在本阶段**。

## STATUS
Phase 6 = 文档交付（Audit + Design）。**STOP after documentation。**
