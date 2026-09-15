# A_SHORT_GAPS_AND_RISKS.md

> **主动找坏消息**（§9、§58.9、§61）。先写最危险、最可能让 A-Short 设计失败的地方，再给缓解。
> 每个数据缺口按 §61 回答：缺什么 / 为什么缺 / 历史还是实时 / 是否必须 / 能否免费 / 是否需新 provider / 是否可先 shadow。

---

## A. 会直接判死项目的三大风险（先说）

### R1（最高）— 成本天花板：短周期换手 × A 股成本
- **坏消息**：T+1..T+5 换手 ≈ V26.8（21 日）的 **21×**。每往返 ≈ 佣金 0.025%×2 + 过户 + 滑点 0.1%×2 + 卖印花 0.05% ≈ **0.27%**，再叠 ¥5 最低佣金（小资金致命）。5 日一换 ≈ 每月 5–6% 摩擦。
- **同型先例**：`MT5_STOCK_CFD_COST_CEILING` 一条把 V30 判死（LS 一期成本 ≈1.9%/20d，任何信息层过不了）。V33 涨停模型 predictive t=60.9 但外壳 −88%、¥1M −66% → `NOT_TRADABLE_AT_20K`。
- **Phase 1.1 已交付**：[A_SHORT_COST_FEASIBILITY.md](A_SHORT_COST_FEASIBILITY.md) 用 `cost.py`/`_fee` 逐笔算出真实往返成本（¥2k/名 0.55–0.75% → ≥¥20k/名 0.10–0.30%）、账户 2k/5k/20k/100k/1m 分带、T+1/T+3/T+5 年化换手成本、以及「需多少 gross alpha 才净正」的答案。**结论：T+1 小账户判死、大账户几乎不可行；优先 T+5，其次 T+3。过不了 breakeven 就不建模。**
- 缓解：优先 T+5/T+3、限制换手、只在高机会日交易（Opportunity-driven，NO TRADE 合法）、避开 ¥5 最低佣金主导的过小单。

### R2 — 治理冲突：三处（Phase 1.1 已裁决，见 A_SHORT_GOVERNANCE_DECISIONS.md）
1. **云 LLM 禁令（Decision 017）** → **已解决**：Decision A-001 允许云 LLM 作 Research/Information Intelligence/Shadow/Paper Recommendation Support，硬禁 `LLM→real order`、交易权、silent autonomy。
2. **前端/调度禁令（AGENTS.md V1.1）** → **已解决**：Decision A-002 条件批准 PySide6 桌面 GUI（独立进程/只读/不发单/关闭不停后台）；调度沿用 SPEC §29.11a 已认可的「任务计划+curl 幂等端点」，不加调度库。
3. **题材/涨停 scope ban（V33）** → **已解决**：Decision A-003——V33 负结果是 prior evidence，不封杀独立假设；A-Short 研究涨停/龙头/主题**须新合同**（新 dataset ID/预注册/窗口/OOS/成本/hold/执行假设），禁重开 V33，须独立证明增量 alpha。
- **结论**：三条均为 PROPOSED，本 PR 合并即 RATIFIED；Phase 2 在三条 RATIFIED + R1 成本闸通过后启动。

### R3 — LLM 输出结构上不可回测 → A-Short 无法按仓库自身闸门产出 Candidate
- **坏消息**：仓库明确「联网 = 前视 + 检索时点不可复现 + 权重内前视」，新闻/政策 = `DATA_BLOCKED` 研究特征。因此 A-Short 的「LLM 理解/主题/新闻」**不能**进 FDR/Level-1/OOS 统计闸，也**不能**声称回测年化。
- **含义**：A-Short 的 LLM 层只能是 **operational gate / 信息展示 / 红队**，Candidate 资格必须由**可 PIT 的 Quant 层**独立支撑。若某天 Quant 层（价量+可 PIT 信息层）自己出不了独立正账本，A-Short 就没有可交易 alpha——这与 ML1 之外「无第二袖」的现状一致（`PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`）。**这是产品级的根本风险：短周期是否真有可 PIT 的边，未知。**

---

## B. 数据缺口（按 §61 逐项）

| 缺口 | 为什么缺 | 历史/实时 | 是否必须 | 能否免费 | 需新 provider | 可先 shadow |
|------|----------|-----------|----------|----------|---------------|-------------|
| **分钟/日内 K 线** | 所有 BaoStock 调用 `frequency=d`，无分钟代码/数据；`SESSION` 仅声明 | 两者（历史浅≈1月 + 实时） | 短周期**强相关**（开盘/封板/日内龙头），但非 D1 路径的必须 | BaoStock 5/15/30/60min 免费但**历史深度未实测**（文档≈1月）；tick/L2 付费 | 否（先试 BaoStock 分钟）；深度不够再评估付费 | **可**（先只落分钟、不进策略，攒历史） |
| **龙虎榜/席位** | 无代码无数据 | 实时（收盘后） | 「游资/主力行为」核心，但可延后 | 部分免费(东财)/部分付费 | 可能 | **可**（先采集攒库） |
| **主力/大单资金流** | 无 | 实时 | 短周期资金面重要 | 多付费 | 是（付费评估） | 可 |
| **题材/概念板块成分** | 无（`概念板块=0`） | 事件 | 「识别主题/下一热点」核心 | 部分付费(同花顺/东财) | 可能 | 可 |
| **新闻正文/RSS** | `announcements/` 仅 `.gitkeep`；无 NLP | 实时 | LLM 理解需要，但**非可回测特征**（R3） | 免费源多但质量/PIT 差 | 否（先用 LLM 联网）| **必须先 shadow**（只理解不回测） |
| **政策（五年规划/部委）** | 无（`部委/发改委=0`） | 实时+结构 | LLM 理解用；`DATA_BLOCKED` | 免费但无结构化 PIT 库 | 否 | 必须 shadow |
| **公告正文** | 只有 `announcement_date` 数值门 | 实时 | 事件驱动用 | 免费(交易所)但需解析 | 否 | 可 shadow |
| **北向日频** | HKEX 2024-08-19 停发 | — | 曾有效(O5)，现**死** | — | **无**（禁代理） | 否（DEAD） |
| **每股每日涨停价/封单** | 面板只有百分比启发式；封单需 L2 | 历史+实时 | 涨停策略必须 | 涨停价可派生(免费)；封单 L2 付费 | L2 付费 | 涨停价可直接 EXTEND |

---

## C. 工程/运行风险

| 风险 | 说明 | 缓解 |
|------|------|------|
| **云 Agent 跑不了实盘增量** | bulk 数据在 owner `D:` 盘且 gitignore；BaoStock/东财/MT5 需本地网络/终端；当前云检出无 `alpha_cache/live/bars/...` | A-Short 实盘只在 owner Windows 跑；云端仅开发 + 离线回测（需先在本机重下或同步子集） |
| **无测试覆盖 V25+** | `tests/` 无 ml_v25/v33/ml1_live 测试 | A-Short 新代码必须带测试（复用 `_now()` 可测模式、holdout/multiple-testing 既有测试扩展） |
| **无桌面 GUI/通知/服务/任务注册** | 全 NEW（`QSystemTrayIcon/win10toast/NSSM/服务`=0；任务手建） | 起步用 PySide6 托盘 toast + 任务计划 `ONSTART` + `register_ashort_tasks.ps1`；服务化(NSSM)作二期 |
| **`TRADEMIND_PAPER_READONLY` 只在文档、代码未读** | 审计发现「更新按钮拒绝」是文档不是代码 | A-Short 的 `TRADEMIND_ASHORT_READONLY`/`_SEND=0` 必须**真的**在代码里 enforce |
| **短周期 PIT 更紧** | 1 日滞后在 20 日 hold 无害，在 3 日 hold 是大比例；margin(D+1) 是唯一够快的信息层，户数/质押/季报在此 horizon 已结构性过期 | 只把够快的层进短周期特征；慢层降级为 context |
| **`.bat` 硬编码 `D:\...` 路径** | 违反 AGENTS.md「禁硬编码路径」 | A-Short 脚本从 `config/ashort.yaml` 读路径 |
| **LLM 无 token/$ 账本** | 只有调用次数上限；Cloud Agents 不返回 usage | NEW token/$ 账本 + 预算闸 |
| **`run_id` 缺失 / STATUS 仅末尾写** | A 股路径靠 pid+日志名+asof；崩溃无 STATUS | 加 `run_id` + 增量写 STATUS + 滚动文件日志 |

---

## D. 现有基础设施是否足以支撑 A-Short？（§61 最终判断）

**分层回答，不泛泛说「不足」：**

- **足够（可直接搭骨架）**：D1 数据获取/冻结+增量/PIT/pack/特征缓存/walk-forward 建模/成本-撮合-账本/后台运行器(锁·孤儿·账户派生·freshness)/LLM 分析台(角色·schema·截断·priced_in·三时钟·证据)/会话调度(任务计划+curl 幂等)/统一响应壳。→ **A-Short 的「日线 + 纸面 + LLM 信息门 + 后台运行」骨架可用现有件拼出。**
- **不足（必须补，按优先级）**：
  1. **可 PIT 的短周期 alpha 本身**（R3/R1）——是否存在可交易的短周期边，未证，是产品成败根本。
  2. 分钟数据（可先 shadow 攒历史）。
  3. 题材/龙头/龙虎榜/资金流数据（部分付费，先 shadow）。
  4. 桌面 GUI + Windows 通知 + 开机自恢复服务（全 NEW，但技术直接）。
  5. 新闻/政策/公告文本（仅作 LLM operational gate，不进回测）。
- **必须先裁决（治理）**：R2 三条冲突。

**一句话结论**：
> **基础设施足以支撑 A-Short 的运行外壳与信息展示；不确定的是「短周期是否真有可 PIT 的可交易 alpha」，以及三处治理冲突是否获批。**
> 因此第一阶段正确姿势 = 先把外壳（数据/PIT/成本可行性/纸面/调度/GUI/LLM 门）按本设计搭好并**先 shadow**，用 Quant 层在**新预注册窗口**上诚实检验短周期边；**在成本可行性 + 独立正账本 + 治理批准三关通过前，不 Paper 承诺、不谈年化、不 order_send。**

---

## E. 建议的实现顺序（供二期，不在本阶段执行）

1. 成本可行性算术（R1）+ 新预注册窗口划分（不读 ML1 禁用窗）。
2. `ashort_live` 包（复制 `ml1_live`，复用 `panel/layers`，短 hold 特征与标签）+ 测试。
3. 短周期 Quant 候选 + 机会分 + NO_TRADE 闸 → 先出 shadow 名单/影子账本（幂等会话调度）。
4. `:9002` 后台服务 + 状态机 + Data Health + Scheduler + 09:00 通知（先 GUI 内，不 owner 承诺）。
5. PySide6 桌面 GUI（复用现有壳）+ 托盘 toast。
6. LLM 层（复用 fusion 台）作 operational gate + 红队代码化 + 证据库。
7. 分钟/题材/龙虎榜先 shadow 采集攒库；付费源单独报价等批。
8. 满 §59 全部 21 项验收 + R1–R3 三关，才进 Paper。
