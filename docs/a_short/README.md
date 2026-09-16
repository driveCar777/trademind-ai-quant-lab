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

### Phase 2A 新增（Cost + Account Feasibility + D1 Research Contract + Baseline Engine）

| # | 文件 | 内容 | 回应 |
|---|------|------|------|
| 16 | [A_SHORT_PHASE2A_PLAN.md](A_SHORT_PHASE2A_PLAN.md) | 本阶段范围/顺序/复用/禁令/数据可用性 | §0–§5 |
| 17 | [A_SHORT_COST_FEASIBILITY_V2.md](A_SHORT_COST_FEASIBILITY_V2.md) | 逐笔成本 + 滑点敏感性 + Cost Envelope（区别于 Alpha Impossibility） | §3–§6, §10, §11, §14 |
| 18 | [A_SHORT_ACCOUNT_FEASIBILITY.md](A_SHORT_ACCOUNT_FEASIBILITY.md) | 最小可执行资金 + Account×Top-K Execution Feasibility Map | §7–§9, §24 |
| 19 | [A_SHORT_D1_RESEARCH_CONTRACT.md](A_SHORT_D1_RESEARCH_CONTRACT.md) | 全新独立合同 `A_SHORT_D1_V1`（血缘/窗/多重性/复现） | §12–§16, §18, §35 |
| 20 | [A_SHORT_D1_BASELINE_SPEC.md](A_SHORT_D1_BASELINE_SPEC.md) | 两层分离 + Top-K 评估 + NO TRADE 诊断 + 审计套件 | §17, §19–§27, §36–§38 |
| 21 | [A_SHORT_PHASE2A_RESULTS.md](A_SHORT_PHASE2A_RESULTS.md) | BAD NEWS + §42 主表 + §43 STATUS（alpha=DATA_BLOCKED，已实算成本/账户） | §41–§43 |
| 22 | [A_SHORT_PHASE2A_EXECUTION_FORENSIC.md](A_SHORT_PHASE2A_EXECUTION_FORENSIC.md) | Phase 2A.1 执行模型复审：affordability fee-aware + entry/exit capital-path exit-recovery + 新不变量 | 执行正确性 |

### Phase 2A.2 新增（First Empirical D1 Run — DATA_BLOCKED in cloud）

| # | 文件 | 内容 |
|---|------|------|
| 23 | [A_SHORT_PHASE2A2_DATA_FORENSIC.md](A_SHORT_PHASE2A2_DATA_FORENSIC.md) | 数据血缘取证：合同一致性✅、物化尝试失败(raw 面板缺失)、参考层齐全、退化守卫修复 |
| 24 | [A_SHORT_PHASE2A2_EMPIRICAL_RESULTS.md](A_SHORT_PHASE2A2_EMPIRICAL_RESULTS.md) | Executive `DATA_BLOCKED`；20 主比较/Q1–Q7 全 BLOCKED；成本/账户算术已出；BAD NEWS |
| 25 | [A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md](A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md) | Cloud 数据可用性 + Universe 取证：frozen 字节 `REGISTERED_BUT_BYTES_UNAVAILABLE`（never in git/LFS/release）；「垃圾股」= BASELINE_DESIGN_CHARACTERISTIC（ALL universe + 20D momentum，无质量过滤）；DATA_BLOCKED / REQUIRES_OWNER_DECISION |

> 代码：新增 `baseline.panel_coverage` 退化守卫 + `run_baseline` lineage 元数据/artifacts（`PHASE2A2_{RESULTS,DIAGNOSTICS,COST_SENSITIVITY,ACCOUNT_GRID}.json`）。empirical alpha 需在有冻结面板字节的机器上物化后才能跑。

### Cloud → Local 交接（handoff freeze）

| 文件 | 内容 |
|------|------|
| [ENVIRONMENT_REPORT.md](ENVIRONMENT_REPORT.md) | 环境身份（Cursor Cloud VM）+ git/python/deps/disk |
| [HANDOFF_CLOUD_TO_LOCAL.md](HANDOFF_CLOUD_TO_LOCAL.md) | 真实状态（Implemented/Not）+ 研究状态（`READY_FOR_DATA/NOT_ALPHA_PROVEN`） |
| [CLOUD_CODE_MAP.md](CLOUD_CODE_MAP.md) | 代码地图（当前/可用/未接/缺失） |
| [LOCAL_RESTORE_GUIDE.md](LOCAL_RESTORE_GUIDE.md) | 本地 clone 后安装/依赖/测试/运行 |
| [DATA_STORAGE_POLICY.md](DATA_STORAGE_POLICY.md) | GitHub 存储策略 + 大数据方案 A/B/C/D（不执行） |
| [A_SHORT_LOCAL_HANDOFF.md](A_SHORT_LOCAL_HANDOFF.md) | 本地恢复包（commit/branch/关键文件/命令/已知问题） |
| [A_SHORT_CLOUD_FINAL_AUDIT.md](A_SHORT_CLOUD_FINAL_AUDIT.md) | 需求差距（Implemented/Partial/Missing）+ 下一阶段顺序 G0→G7 |
| [HANDOFF_ENVIRONMENT.md](HANDOFF_ENVIRONMENT.md) | 环境冻结（Cloud VM / 版本 / 体积 / 可用·不可用工具） |
| [CURRENT_IMPLEMENTATION_STATUS.md](CURRENT_IMPLEMENTATION_STATUS.md) | Implemented / Partial / Missing（当前实现，非规划） |
| [CURRENT_MODEL_REALITY.md](CURRENT_MODEL_REALITY.md) | 当前模型 = ONLY 20D_MOMENTUM_BASELINE（Specified≠Implemented） |
| [REQUIREMENT_GAP_MATRIX.md](REQUIREMENT_GAP_MATRIX.md) | 20 项需求 × 状态 × 文件证据 |
| [DATA_HANDOFF_STATUS.md](DATA_HANDOFF_STATUS.md) | 数据血缘：REGISTERED BUT BYTES UNAVAILABLE |
| [A_SHORT_CLOUD_HANDOFF_FINAL.md](A_SHORT_CLOUD_HANDOFF_FINAL.md) | 交接最终报告（STATUS / Next Step / 待决策） |

> 代码：`research_engine/cn_a_short/`（cost/account/feasibility/baseline/report/run + 25 tests，全绿）。本环境经验 alpha `DATA_BLOCKED`（无价格面板），成本/账户已实算。

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
