# A-Short 设计基线：Phase 1 Forensic/Architecture + Phase 1.1 Governance/Runtime v2

> **状态：Phase 1 + Phase 1.1 Design（仅审计 + 架构设计 + 治理裁决，无大规模实现）。**
> 原则：**Audit first, architecture second, implementation third.**
> 本目录只输出设计与审计文档，不动任何 frozen 研究合同、不改 ML1/V33、不写 `order_send`。
> **Phase 1.1 交付**：三处治理冲突（云 LLM / Qt GUI / V33 scope）已裁决；Prediction/Recommendation/Execution 三层边界、通知与 GUI 解耦、执行时序、逐笔真实成本可行性已落文档。`*_V2` 文档在被修订处**取代** v1 对应章节。

本目录是对用户「A-Short 运行架构 / 数据复用 / GUI / Scheduler / Paper Trading / 数据流补充需求」的
第一阶段交付。所有结论来自对现有仓库的**逐文件审计**（见每份文档的文件引用），不依赖聊天上下文。

## 定位（一句话）

A-Short = TradeMind 的**短周期（T+1/T+2/T+3/T+5）机会发现与纸面推荐系统**，
与 ML1（20 日慢速横截面 alpha）**并列、独立、互不污染**；当前阶段 **PAPER ONLY / LONG ONLY / 禁止 order_send**。

## 文档清单（对应需求 §58）

| # | 文件 | 内容 | 验收项 |
|---|------|------|--------|
| 1 | [EXISTING_CAPABILITY_FORENSIC.md](EXISTING_CAPABILITY_FORENSIC.md) | 逐模块 REUSE/EXTEND/NEW/DEPRECATE/UNKNOWN | §59.1–3, §61 |
| 2 | [A_SHORT_RUNTIME_ARCHITECTURE.md](A_SHORT_RUNTIME_ARCHITECTURE.md) | GUI/Research/Paper/Scheduler/Notif/Data/LLM + 进程边界 | §59.4–6, §8–10 |
| 3 | [A_SHORT_DATA_SOURCE_MATRIX.md](A_SHORT_DATA_SOURCE_MATRIX.md) | source×(coverage/depth/freq/PIT/latency/reliability/fallback/cost/impl) | §59.20, §31 |
| 4 | [A_SHORT_DATA_FLOW.md](A_SHORT_DATA_FLOW.md) | External→Raw→PIT→Features→Candidates→LLM→Fusion→Rec→Paper→Outcome | §41, §59.17–18 |
| 5 | [A_SHORT_GUI_SPEC.md](A_SHORT_GUI_SPEC.md) | 页面/图表/动画/通知/设置/账户/推荐详情 | §45–52 |
| 6 | [A_SHORT_PAPER_LEDGER_SPEC.md](A_SHORT_PAPER_LEDGER_SPEC.md) | cash/shares/T+1/fees/contribution/withdrawal/invariants/immutable | §11–19, §59.7–8,13–15 |
| 7 | [A_SHORT_SCHEDULER_SPEC.md](A_SHORT_SCHEDULER_SPEC.md) | 后台进程/开机/重启/重试/手动/09:00 通知/幂等/恢复 | §20–27, §59.9–12,19 |
| 8 | [A_SHORT_LLM_PIPELINE_SPEC.md](A_SHORT_LLM_PIPELINE_SPEC.md) | LLM 角色/输入输出 schema/prompt 版本/证据存储/日志/降级/成本 | §34–38, §59.16 |
| 9 | [A_SHORT_GAPS_AND_RISKS.md](A_SHORT_GAPS_AND_RISKS.md) | 缺口 + 风险（先写坏消息） | §9, §59.21, §61 |

### Phase 1.1 新增/修订（Governance Resolution + Runtime v2）

| # | 文件 | 内容 | 回应 |
|---|------|------|------|
| 10 | [A_SHORT_GOVERNANCE_DECISIONS.md](A_SHORT_GOVERNANCE_DECISIONS.md) | Decision A-001 云 LLM / A-002 Qt GUI / A-003 V33 scope / A-004 通知解耦 | §11–13, §28.Governance |
| 11 | [A_SHORT_RUNTIME_ARCHITECTURE_V2.md](A_SHORT_RUNTIME_ARCHITECTURE_V2.md) | Prediction/Recommendation/Execution 三层 + GUI 生命周期 + 通知解耦 + 时间线 | §2–8, §28.Architecture |
| 12 | [A_SHORT_DATA_FLOW_V2.md](A_SHORT_DATA_FLOW_V2.md) | 三层落点 + Candidate=资源预算 + Track A/B 分离 + LLM 回测边界 | §15–16, §9–10 |
| 13 | [A_SHORT_COST_FEASIBILITY.md](A_SHORT_COST_FEASIBILITY.md) | 逐笔真实成本 + 2k/5k/20k/100k/1m + 换手×成本 + gross-alpha 下限 | §14, §28.Cost |
| 14 | [A_SHORT_NOTIFICATION_SPEC.md](A_SHORT_NOTIFICATION_SPEC.md) | 后台通知服务 / 无 GUI Windows toast / 语义 / 错过重放 | §5, §18, §28.Notification |
| 15 | [A_SHORT_PAPER_EXECUTION_TIMELINE.md](A_SHORT_PAPER_EXECUTION_TIMELINE.md) | 08:58 freeze / 09:00 notify / 09:25 pre-open / 09:30 exec | §1, §8, §28.Runtime |

> 同时修订：LLM_PIPELINE / SCHEDULER / PAPER_LEDGER / GUI / GAPS（治理与通知/成本/三层边界已更新）。

## 三条必须先记住的硬结论（详见 §9 文档）

1. **成本天花板先于模型。** 逐笔真实往返成本 ¥2k/名 0.55–0.75%、≥¥20k/名 0.10–0.30%（见 COST_FEASIBILITY）；
   T+1 小账户判死、大账户几乎不可行，优先 T+5/T+3。不先算清「换手×成本」就建模，会重演 `MT5_STOCK_CFD_COST_CEILING`。
2. **LLM = Information Intelligence + Decision Support（不是 Alpha、不是交易权）。** 无历史 PIT 语料前，LLM 输出
   「结构上不可回测」不得当历史回测特征；但**可**参与实时 shadow/paper 的信息理解与融合决策支持（Decision A-001），
   最终 Paper 由 Local/Portfolio Engine 控制，LLM 无 `order_send`。
3. **不动冻结物。** 不改 ML1 / V33 / 任何 frozen 合同；A-Short 复制 `ml1_live` 的做法**新开** `ashort_live` 包，
   新 dataset ID、新预注册窗口划分、不读 ML1 禁用窗、step-9 式单向 hook。

## 与 AGENTS.md / SPEC.md 的一致性与冲突

三处冲突（Decision 017 云 LLM、AGENTS.md V1.1 前端/调度、V33/题材 scope ban）在 **Phase 1.1 已裁决**：
见 [A_SHORT_GOVERNANCE_DECISIONS.md](A_SHORT_GOVERNANCE_DECISIONS.md)（Decision A-001/A-002/A-003/A-004，PROPOSED → 本 PR 合并即 RATIFIED）。

**下一阶段（Phase 2 实现）在治理三条 RATIFIED + 成本可行性闸通过之前不启动。**
