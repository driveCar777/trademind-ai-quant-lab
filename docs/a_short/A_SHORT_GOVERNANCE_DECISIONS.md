# A_SHORT_GOVERNANCE_DECISIONS.md

> Phase 1.1 治理裁决。把 Phase 1 发现的三处冲突正式化为 Decision/Amendment。
> 状态：**PROPOSED（本 PR 合并即视为 owner 批准 = RATIFIED）**。本文档只裁决边界，不写业务代码。
> 本轮仍：Audit → Architecture → Implementation，禁大规模实现 / order_send / SHORT / margin / 改 ML1 / 改 V33 / 改 frozen 合同 / 采购付费数据。

---

## Decision A-001 — 云端 LLM 用于 A-Short（修订 `DECISIONS.md` Decision 017）

**背景**：Decision 017 规定「不使用 OpenAI/GPT/任何云端大模型 API 作为**已部署推理引擎**」。但 SPEC §14、`master/api/app/service/paper_fusion.py`、`cursor_cloud.py` 实际已在用 Cursor Cloud Agents / DeepSeek。A-Short 明确需要云 LLM。

**裁决**：在 017 之上增补——**允许**云端 LLM 用于 A-Short 的 `Research / Information Intelligence / Shadow / Paper Recommendation Support`。

**允许角色（permitted）**：新闻/政策/公告/主题/事件的信息理解、矛盾分析、候选解释、红队/逆否审查、融合的**决策支持**。
**硬禁角色（prohibited）**：
```
LLM → real order          （禁）
LLM → order_send / broker （禁）
LLM = Trading Authority    （禁：LLM 无真实交易权）
LLM = silent autonomy      （禁：无人工可见的自动决策链）
```
最终 Paper 决策由 **Local Decision / Portfolio Engine** 控制，LLM 只作输入。

**强制要求（新 Decision 必须含）**：
| 项 | 要求 |
|----|------|
| permitted_roles | 见上（信息智能 + 决策支持） |
| prohibited_roles | LLM→real order / trading authority / silent autonomy |
| logging | 每次调用存 request/response/model/prompt_version/timestamp/latency/run_id/role |
| evidence_persistence | 联网证据存 url/title/source/published_time/captured_time/knowledge_time/content_hash |
| budget | token/$ 账本 + 每日调用上限（现 `MAX_GROK_CALLS_PER_DAY`） |
| model_version | 固定 model + prompt_hash；变更即新序列 |
| no_real_order | `TRADEMIND_ASHORT_SEND=0` 代码层 enforce |

**结论**：**017 冲突已解决**（作为增补，非推翻——本地 Qwen 仍是默认推理，云 LLM 仅限上述角色且无交易权）。

---

## Decision A-002 — 批准 PySide6 桌面 GUI（修订 `AGENTS.md` V1.1「禁 Qt 前端」）

**背景**：AGENTS.md V1.1 禁令列有「前端禁 Vue/React/Electron/Qt/WebSocket」（写于 V1.1 极简期）。Owner 已明确要求 **Windows Desktop GUI（PySide6）**。项目实际早已超越 V1.1（`:9001` hot desk、fusion desk 已入 SPEC §29）。

**裁决**：**批准** A-Short 使用 PySide6 桌面 GUI，条件如下（全部为硬条件）：
```
independent process        独立进程（不与后台同生命周期）
read/control console only   只读 + 控制台（触发按钮），无业务逻辑
no order_send               不发单
no strategy logic           不含策略/alpha 逻辑
no data layer               不含数据采集/存储
backend = localhost :9002   只通过本地 HTTP 与后台通信
GUI close ≠ backend stop     关 GUI 不停后台
```

**结论**：**Qt GUI 冲突已解决**（限定条件下批准）。注意其与 §Decision A-004（通知解耦）配套：GUI **不是**通知发送方。

---

## Decision A-003 — V33 scope：新研究合同而非重开 V33

**背景**：`cn_a_share_ml_v33` 判决 `A_SHARE_LIMITUP_EVENT_V33_PREDICTIVE_BUT_NOT_TRADABLE_AT_20K`（predictive t=60.9，但外壳 −88%）。AGENTS.md/`V38_EVOLUTION_MISSION_DESIGN.md` 禁「重开 V33 / 题材 / 涨停短线」并禁调 V33 参数。

**裁决**：
1. **V33 的负结果是 prior evidence，不是对所有未来独立假设的自动封杀。** 明确写入本裁决：*V33 negative result is prior evidence, not automatic prohibition of all future independent hypotheses.*
2. A-Short 若研究 `limit-up / leader / theme / next-theme / event-driven short-horizon`，**必须创建全新研究合同**，且**不得**修改/重开/重跑 V33 本体。新合同至少含：
```
new dataset ID              （新 tm-ashare-… 命名空间）
new hypothesis registry     （独立预注册，逐条计 m）
new pre-registration        （跑前冻结，跑完不许搜参数）
new research window          （不读 ML1/V33 禁用窗）
new validation window
new OOS rule
new cost model              （见 A_SHORT_COST_FEASIBILITY.md，逐笔真实成本）
new hold definition         （T+1/T+2/T+3/T+5 明确）
new execution assumptions   （T 日开盘/定义成交时点，非 09:00 价）
```
3. 新合同**必须独立证明增量 alpha**（相对 ML1/EW 的 corr < 0.90 且验证正账本），否则按 `FAILURE_ATLAS` 记一行并停。

**结论**：**V33 scope 冲突已解决**（禁重开 V33，但允许独立新合同，须独立证明）。

---

## 三问速答（§28 Governance）

| 冲突 | 解决？ | 依据 |
|------|--------|------|
| Decision 017（云 LLM） | **是** | A-001：允许云 LLM 作信息智能+决策支持，硬禁 real order/交易权 |
| Qt GUI | **是** | A-002：条件批准 PySide6（独立进程/只读/不发单/关 GUI 不停后台） |
| V33 scope | **是** | A-003：禁重开 V33，允许全新独立合同，须独立证明增量 alpha |

> 三条均为 **PROPOSED**，本 PR 合并即 RATIFIED。实现阶段（Phase 2）在三条 RATIFIED + 成本可行性（[A_SHORT_COST_FEASIBILITY.md](A_SHORT_COST_FEASIBILITY.md)）通过后才启动。

---

## Decision A-004 — 通知与 GUI 解耦（新增，回应 §5）

**背景**：Phase 1 把 09:00 通知放在 `QSystemTrayIcon.showMessage()`，而它需要 Qt 事件循环（GUI 必须开着）→ 与「GUI 可关、后台续发通知」冲突。

**裁决**：通知发送归属**后台 Notification Service**，不依赖 GUI：
```
Scheduler / Backend → Notification Service → Windows Toast (无需 GUI)
GUI 只读通知历史（NOTIFICATIONS.json），不是发送方
```
具体无 GUI 发送方案见 [A_SHORT_NOTIFICATION_SPEC.md](A_SHORT_NOTIFICATION_SPEC.md)。

**结论**：GUI 关闭时 Windows 通知**仍能工作**（后台直发）。
