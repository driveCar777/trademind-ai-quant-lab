# A-Short 第一阶段：Architecture + Existing-Capability Forensic

> **状态：Phase 1 Design（仅审计 + 架构设计，无大规模实现）。**
> 原则：**Audit first, architecture second, implementation third.**
> 本目录只输出设计与审计文档，不动任何 frozen 研究合同、不改 ML1、不写 `order_send`。

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

## 三条必须先记住的硬结论（详见 §9 文档）

1. **成本天花板先于模型。** T+1..T+5 换手是 V26.8 的 ~21×，单次往返 ≈0.27% + 印花税 0.05% + ¥5 最低佣金；
   不先把「换手×成本」算清楚就建模，会重演 `MT5_STOCK_CFD_COST_CEILING`（V30 被这条判死）。
2. **LLM/新闻是 operational gate，不是 Candidate/alpha。** 新闻/政策在仓库里是 `DATA_BLOCKED` 研究特征，
   联网 LLM 输出「结构上不可回测」（前视 + 检索时点不可复现）。A-Short 的 LLM 只做**信息理解与红队**，
   不进 Candidate 统计闸门、不产生「年化承诺」。
3. **不动冻结物。** 不改 ML1 / V33 / 任何 frozen 合同；A-Short 复制 `ml1_live` 的做法**新开** `ashort_live` 包，
   新 dataset ID、新预注册窗口划分、不读 ML1 禁用窗、step-9 式单向 hook。

## 与 AGENTS.md / SPEC.md 的一致性与冲突

本设计**主动**标出了与现有治理文本的三处冲突（Decision 017 云 LLM 禁令、AGENTS.md V1.1 前端/调度禁令、
V33/题材 scope ban），并给出「需要一次新的 Decision/Amendment 才能推进」的结论，而不是默默绕过。详见
[A_SHORT_GAPS_AND_RISKS.md](A_SHORT_GAPS_AND_RISKS.md) §治理冲突。

**下一阶段（实现）在本 Forensic/Architecture PASS 之前不启动。**
