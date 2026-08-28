# TradeMind — 架构决策记录

> 一人项目，不用 ADR 目录。所有重大决策记录在此。

---

## Decision 001 — Worker 通信使用 REST

**决定：** Worker 之间、Master 与 Worker 之间，统一使用 REST HTTP。

**不使用：** RabbitMQ、Kafka、Redis Pub/Sub 等消息队列。

**原因：**
- 简单，可调试（curl 即可测试）
- 一人项目，不需要分布式消息中间件
- FastAPI 原生支持，零额外依赖

---

## Decision 002 — Master 运行在 Windows

**决定：** Master（调度中心）永远运行在 Windows PC。

**原因：**
- MT5 只支持 Windows
- Arc A770M LLM 在 Windows 上运行
- Dashboard 本地访问

---

## Decision 003 — Worker 运行在 Jetson

**决定：** 所有计算 Worker 运行在 Jetson Xavier NX 集群。

**原因：**
- 分布式计算，4 节点并行
- Docker 容器隔离
- 与 Master 物理分离，REST 通信

---

## Decision 004 — LLM 只在 Master 运行

**决定：** 所有 AI / LLM 推理只在 Windows Master 执行。

**不在 Jetson 上运行 LLM。**

**原因：**
- Jetson 性能有限，适合数值计算
- Arc A770M 在 Windows 上，算力更强
- 避免在 Worker 节点引入 AI 依赖

---

## Decision 005 — 不使用 Git

**决定：** 一人 + AI 协作项目，不使用 Git 版本管理。

**版本记录方式：**
- `CHANGELOG.md` — 修改历史
- `ROADMAP.md` — 版本路线
- `DECISIONS.md` — 架构决策
- `PROJECT_STATUS.md` — 项目状态快照

**原因：**
- Git 增加管理成本
- 文件即版本，CHANGELOG 更清晰
- Cursor 直接读写文件，无需分支管理

---

## Decision 006 — Worker 必须复制 Template

**决定：** 任何新 Worker 必须从 `workers/indicator-worker` 复制。

**禁止重新设计 Worker 目录结构。**

**原因：**
- 统一接口、配置、部署方式
- 降低维护成本
- AI 协作时不会越写越偏

---

## Decision 007 — 配置统一 TRADEMIND_* 前缀

**决定：** 所有环境变量使用 `TRADEMIND_` 前缀。

**原因：**
- 避免与其他服务冲突
- 统一配置管理
- Docker Compose 环境变量清晰

---

## Decision 008 — 技术栈冻结

**决定：** 以下版本禁止升级，除非写入新 Decision。

| 组件 | 版本 |
|------|------|
| Python | 3.8 |
| FastAPI | 0.83.x |
| Docker | 当前版本 |
| JetPack | 当前版本 |

**原因：** Xavier 兼容性，避免升级引发连锁问题。

---

## Decision 009 — V1.1 POST /task 同步执行

**决定：** `POST /task` 同步执行，请求内完成 Worker 调用后返回。

**响应格式：** `{task_id, status: COMPLETED|FAILED, worker_id}`

**禁止：** 返回 `submitted`、异步任务队列。

**原因：**
- V1.1 唯一职责是跑通链路，不需要异步调度
- 简化调试与冒烟测试

---

## Decision 010 — Task ID 格式 tm-task-YYYYMMDD-NNNNNN

**决定：** Task ID 使用 `tm-task-YYYYMMDD-NNNNNN` 格式。

**禁止：** UUID、`task-00001` 等非规范格式。

**原因：**
- 人类可读，按日期分层存储
- 与 results/ 目录结构一致

---

## Decision 011 — 存储分离 tasks/ 与 results/

**决定：**
- `storage/tasks/` — 任务元数据，不含 result 正文
- `storage/results/YYYY/MM/DD/` — 计算结果，按日期分层

**原因：**
- 元数据与结果分离，便于查询与归档
- 结果文件可按日期清理

---

## Decision 012 — workers.json 只存静态注册

**决定：** `storage/workers.json` 只存静态注册信息（worker_id、host、port、type），**不写 status**。

**运行时状态：** Master 启动后对每个 Worker 执行 `GET /health` → 判定 `ONLINE` / `OFFLINE` + `latency_ms`。

**原因：**
- 静态配置与运行时状态分离
- 避免手动维护 status 字段

---

## Decision 013 — Worker 不知道 Master

**决定：** 通信方向单向 `Master → Worker`。

**禁止：** Worker 配置 `master_host` / `master_port`，Worker 不回调 Master。

**原因：**
- 职责分离：Master 调度，Worker 计算
- 简化 Worker 部署与配置

---

## Decision 014 — Worker 类型统一 indicator-worker

**决定：** Worker 类型字段值为 `indicator-worker`（非 `indicator`）。

**原因：**
- 与目录名、服务名一致
- 避免歧义

---

## Decision 015 — 统一 API 响应格式

**决定：** Master 与 Worker 对外业务接口统一响应格式：

```json
{
  "success": true,
  "message": "",
  "code": "TM-0000",
  "data": {}
}
```

**探针例外：** `GET /health`、`GET /ready` 可保留轻量字段。

**原因：**
- 统一错误处理与客户端解析
- 便于 SDK 封装（V1.2+）

---

## Decision 016 — V1.1 错误码固定四个

**决定：** V1.1 只允许以下错误码：

| 代码 | 含义 |
|------|------|
| `TM-0000` | Success |
| `TM-1001` | Worker Offline |
| `TM-1002` | Task Failed |
| `TM-1003` | Invalid Request |

**禁止新增错误码**，除非写入新 Decision 并更新 SPEC.md。

**原因：**
- V1.1 范围最小化
- 避免过度设计错误处理

---

## Decision 017 — V3.0 Master 只代理 AI Gateway，本地模型固定 Qwen

**决定：**
- 本地 LLM 只部署 **Qwen2.5-14B-Instruct Q4_K_M**。
- Master 通过 REST 代理 AI Gateway，不在 Master 进程内加载模型。
- Gateway URL / 超时只来自配置与 `TRADEMIND_*` 环境变量。
- Gateway 离线复用 `TM-1002`，超时复用 `TM-1004`，不新增错误码。
- SYCL GPU 加速为性能优化，不是功能交付前提；编译失败则以 CPU 后端为交付基线。

**不使用：** OpenAI / GPT 系列 / 任何云端大模型 API 作为已部署推理引擎。

---

## Decision 018 — 控制台可启动/重启 Worker 与调度中心，不重启通义千问

**决定：**
- Master 提供 `POST /api/v1/ops/worker/{id}/start|restart` 与 `POST /api/v1/ops/master/restart`。
- 错误码复用 `TM-1001` / `TM-1002` / `TM-1003`，不新增。
- 网页不重启 AI Gateway。通义千问只走桌面/`start_sycl.bat`。
- 调度中心重启必须脱离当前 HTTP 进程，禁止在请求内自杀等待。

**不使用：** 网页一键重启「全实验室」、关机、改密码。

---

## Decision 019 — 详情带结果正文；控制台默认算一笔，不自动问 AI

**决定：**
- `GET /task/{id}` 在结果文件可读时返回 `data.result`。`GET /tasks` 不读结果文件，`result` 恒为 `null`。
- 控制台打开后推荐**一笔**当前在线节点的预设计算。用户点「现在就计算」才提交。禁止每次刷新自动 `POST /task`。
- 「让 AI 解读」只送节点算完的数字（或用户改过的框），不送任务请求里的原始行情数组冒充结果。
- 不自动调用通义千问。节点离线则禁用对应类型，不提交。

**不使用：** V4 Research Agent、自动选股、自动连跑四类任务、网页重启模型。

---

## Decision 020 — 一键启动覆盖全部 4 台 Xavier；01 只动固定 Docker 箱

**决定：**
- 四台都是当前阶段计算节点。不再默认跳过 Xavier-01。
- 01 用 Docker 启停；02/03/04 仍用 `server.py`。已健康则跳过。
- 选箱只认固定名单（或 Ports 含 8080）。禁止重启第一个容器。
- 冒烟不主动停 01。不新增 API 字段与错误码。

**不使用：** 把 01 排除出本阶段、网页重启全实验室、改 Worker 计算代码。

---

## Decision 021 — 一键「已在跑」只认 HTTP 健康，不认 netstat 字符串

**决定：**
- 调度中心 / 通义千问是否跳过启动，以 `/health`（及 TCP 能否连上）为准。
- Xavier 状态只读 Master `GET /workers`，新脚本不写死板子 IP。
- 收尾必须列出 Master / Gateway / 四台 Worker，禁止只用一个「已就绪」。
- 不新增 API、不新增错误码。

**不使用：** `findstr :9000` 当唯一判据、端口不健康仍再开窗口、V4。

---

## Decision 022 — 算完只展示「用这笔数字问 AI」，离线禁止推理

**决定：**
- 计算成功后必须出现下一步条：摘要 +「用这笔数字问 AI」。该按钮只滚动定位，不调用网关。
- 通义千问离线时禁用提问按钮。
- 不新增 API / 字段 / 错误码。

**不使用：** 算完自动 `POST` AI、V4、网页重启模型。

---

## Decision 023 — 通义千问同时只跑一路，限制生成长度

**决定：**
- `generate()` 互斥。第二路立即 503 busy，不排队。
- `max_tokens` ≤ 1024；消息最多 4 条、每条最多 4000 字。
- `start_sycl.bat` 固定 `GGML_SYCL_F16=OFF`，禁止 `ONEAPI_DEVICE_SELECTOR`。
- 不新增 Master 错误码。

**不使用：** 双开 14B、F16=ON、本轮改 `n_ctx`。

---

## Decision 024 — V4 第一版只编排「一笔计算 + 一次解读」

**决定（已冻结 2026-08-23）：**
- V4.0 第一冻：人点「研究一笔」→ 现有 `POST /task` → 现有 AI 代理 → `data/research/`。
- 一次只 1 个 Worker 预设，AI 不发明任务 JSON。
- 同时只 1 份研究。网关忙碌则保存数字并 `ai_skipped`。
- 不做 MT5、队列、数据库、自动定时、自动连跑回测。

**不使用：** 把愿景里的「自动发现异常 / 生成策略」写成 V4.0 已交付。

---

## Decision 025 — V4.1 最多两步现有计算

**决定：**
- 同一 `POST /api/v1/research/run` 增加可选 `chain`，长度 1～2。
- 开算前链上 Worker 都必须在线；第一步失败不跑第二步。
- 仍只 1 次 AI、1 把研究锁。不接 MT5。

**状态：** 已冻结 2026-08-23。

---

## Decision 026 — V5.0 只做人手确认的模拟纸质单

**决定：**
- 只模拟。V5.0 禁止调用 MT5 `order_send`。
- 必须人手 `confirm=true`。研究结束不自动开单。
- 只读已有研究。Xavier 不跑 MT5。
- 实盘发单留给以后的版本，需另写设计。

**状态：** 已冻结 2026-08-23。探测到本机账户为 demo，仍不发单。

---

## Decision 027 — V6 先看拟单，仍不发单

**决定：**
- 控制台打开研究必须先 preview。
- 增加只读 `GET /api/v1/desk/today`。
- 继续禁止 `order_send`。

**状态：** 已冻结 2026-08-23。

---

## Decision 028 — V7 指标研究读本机 CSV

**决定：**
- 指标研究的收盘价来自 `data/samples/{id}.csv`，默认 `eurusd`。
- 不是实时行情。不拉 MT5 历史。不改 Worker。
- 因子 / 回测 / 监控本版不动。
- 继续禁止 `order_send`。不新增错误码。

**状态：** 已冻结 2026-08-24。

---

## Decision 029 — V8 因子 / 回测也读本机 CSV

**决定：**
- 因子默认 `moutai.csv`（stock/date），回测默认 `xauusd.csv`（strategy/symbol/start）。
- Master 只拼 Worker 已有字段。不改 Xavier。
- 种类和预设对不上 → `TM-1001`。
- 继续禁止 `order_send`。不新增错误码。

**状态：** 已冻结 2026-08-24。

---

## Decision 030 — V9.0 人手确认后可发 MT5 模拟盘

**决定：**
- V5.0 纸质单冻结件不改写。V9 是新路径：Master 连本机 MT5。
- 仅 `account_mode=demo` 才 `order_send`。实盘必须拒绝。
- Xavier 不装、不跑 MT5。Master 拉 M15 close，交给现有 indicator-worker。
- 人手 `confirm=true` 才发。研究结束不自动开单。
- 自动化测试必须 `TRADEMIND_MT5_SEND=0`。
- 同花顺本环境没有可测官方接口，不假装已接通。A 股继续因子 + `moutai.csv`。

**状态：** 已冻结 2026-08-24。Smoke 18 + Stability 07 PASS（假终端，未打真实模拟账户）。

---

## Decision 031 — V10 人手选方向只为测通，不是预测

**决定：**
- RSI 中性不再假装是「终端坏了」。无 `side` 仍拒绝。
- 可选 `side=BUY|SELL` + `confirm=true` 才发 0.01 手测通。
- `reason=wire_test`。不把测通写成策略有效。
- 不新增因子、不改 Xavier、不接同花顺。

**状态：** 已冻结 2026-08-24。Smoke 19 PASS（SEND=0，未打真实模拟账户）。

---

## Decision 032 — V11 用真 K 线证伪，不承诺年化

**决定：**
- Xavier 回测可吃 `close[]`。没有则仍合成，避免假装 MT5。
- Master 切 70/30，风控写死：回撤 25%、两边至少 5 笔、样本外收益必须 > 0。
- `survived` 只表示本次未证伪。禁止写成年化 100% 或策略已验证。
- 本版不自动下单。

**状态：** 已冻结 2026-08-24。Smoke 20 + Stability 08 PASS。Xavier-03 已升 2.1.1。

---

## Decision 033 — V11.4 留下成交时间和价格

**决定：**
- 本机 `data/samples/` 只有演示 CSV，不是 2000 根 GOLD H1。
- 真行情在本机 MT5。Master 拉 K 线时必须留 `time`，不能只留 close。
- Xavier 仍只算 `{symbol, close}`，回 `idx`。Master 用 `time[idx]` 写成可读时间。
- 控制台必须能看到窗口起止和每笔买卖点。没有明细就不能假装可核对。

**状态：** 2026-08-24。需要 Xavier-03 升 2.1.2。

---

## Decision 034 — V11.5 连续切分，冻结参数对照

**决定：**
- 样本内外是一条持仓的两段。禁止切分强平。
- 多策略只用 Worker 里已冻结的默认参数，同一段 K 线对照。这是稳健性检查，不是寻优。
- 禁止用样本外数字去改阈值。GRID / VWAP 不进篮。

**状态：** 2026-08-24。Xavier-03 需 2.1.3。

---

## Decision 035 — V11.6 分段用冻结线性规则，不用张量拟合

**决定：**
- 大趋势不等于每一段都能做多。下跌允许空仓。
- 特征二维：相对均线偏离。阈值写死。禁止用样本外改映射。
- 不上神经网络 / 张量训练。线代只用到阈值分割。换段付代价。

**状态：** 2026-08-24。Xavier-03 2.1.4。

---

## Decision 036 — V11.7 并行挖参只看样本内

**决定：**
- 四台 ARM 都可跑标准库回测（01/02/04 为 8002 旁路）。
- 候选盘写死。得分只用样本内。样本外只公布选中组。
- 不改 nvpmodel，不上 GPU 张量。单台在线时仍扇出到该台。

**状态：** 2026-08-24。

---

## Decision 037 — Factor Discovery 搜索空间由 Windows 锁定

**决定：**
- Factor Discovery 的 candidate 列表写在 versioned search-space JSON，由 Windows 锁定。
- Xavier worker 只读 job manifest + space hash，不得自己决定“今天研究哪些因子”。
- HYP-0001 `node_runner.py` / 14:11 合同保持不动。
- `NO_USEFUL_FACTORS_FOUND` 是合法结果，禁止为了交差制造 top factor。
- PROMISING ≠ 可交易策略 ≠ 年化 10%。没有 PROMISING 时不进入 Strategy Mining。

**状态：** 2026-08-26。Factor Discovery V0.1 已按此实跑。

---

## Decision 038 — V0.5 先做 Market State，不再做无条件因子农场

**决定：**
- 盈利研究下一层是状态条件策略草图，不是再扫一遍无条件因子。
- Market State 轴与 ADX 周期写死。禁止 ADX/RSI 周期搜索。
- 年化 ≥10% 是成本与风险之后的资金结果，不是 V0.5 的 p 值门槛。
- `NO_USEFUL_STRATEGIES_FOUND` 合法。

**状态：** 2026-08-26。地基已本地跑通。

---

## Decision 039 — Profit Discovery 必须成本后、风险后，且不得事后改门槛

**决定：**
- 盈利路径是 Market State → 有限策略族 → NEXT_BAR_OPEN → spread+5bp+10bp → 固定风险仓位 → 同品种组合。
- 禁止 close 成交。禁止无限杠杆（名义上限 1× 权益）。
- 程序级 CANDIDATE 必须在 **≥ 2 个 dataset** 上过锁死门。单市场过门只能是 WEAK_EDGE。
- CAGR ≥ 10% **不是** V0.6 通过条件；它是长期资金目标。
- `WEAK_EDGE_ONLY` / 空候选列表合法。禁止看见 OIL D1 动量残留后改 N、持有期、成本或门槛。
- 不改 HYP-0001 / FD V0.1 / V0.5 / 14:11。不锁 Final OOS。不发 MT5。

**状态：** 2026-08-26。V0.6 四 Xavier 已按此实跑，结果 `WEAK_EDGE_ONLY`。

---

## Decision 040 — V0.7 先审计 alpha 缺口，不再堆简单策略

**决定：**
- V0.6 无 CANDIDATE 之后，禁止再增加同构的趋势/回归/短持有动量策略。
- V0.7 第一刀是设计：覆盖矩阵、数据需求、框架，不写代码、不改旧实验。
- 下一最可能赚钱的实现方向是 **跨品种 D1 关系**（对齐后滞后，不是同期相关）。`FAM-FD-XASSET-0001` 保持血统，不要另起同义家族冒充新发现。
- 状态转换可作第二刀。时段主证要更长 M15/H1。真 VRP / 事件 / 利率在有数据前禁止开实验。
- AI 只在 Windows 提假设，必须锁进名单再算。禁止用模型改门槛或扩大农场。
- 10% 仍是长期资金目标，不是本设计的通过条件。

**状态：** 2026-08-26。计划已写，实现未开始。

---

## Decision 041 — V0.7.1 先锁操作系统，V0.8 最多三条跨品种假设

**决定：**
- V0.7.1 是运营地图，不是新实验。不写代码，不改旧合同。
- 下一实现只许：现有四条 D1 的 UTC 对齐 + `HYP-XA-0001/0002/0003`。禁止第 4 条，禁止扫领先期/持有期。
- 程序级 CANDIDATE 需要两个 **被预测品种**（GOLD 与 OIL），仅双代理打 GOLD 只能是 WEAK_EDGE。
- 真 VRP / 事件 / 利率在有数据前禁止开实验。Portfolio 必须等存活袖套。
- Data V0.2 加长不覆盖 `*-20260825-000001`。V0.8 主源必须是旧 D1 的对齐包。

**状态：** 2026-08-26。OS 已写。V0.8 已执行并冻结（`NO_CANDIDATE`）。

---

## Decision 042 — V0.8 跨品种合同先锁再跑，且不得改门

**决定：**
- `FAM-FD-XASSET-0001` 用三条假设激活：HYP-XA-0001/0002/0003。禁止第四条。
- 时钟 = 四条 D1 四向 inner join（1993 日）。禁止填日期。t+1 = 对齐序列下一行，不是日历 +1。
- 窗口 70/15/15 已按该序列冻死。最后 15% Final OOS 拒绝访问。
- 领先期、67% 分位 / 0 切割、预注册方向、V0.6 成本，看见结果后一律不准改。
- 程序级 CANDIDATE 需要两个 **target**（GOLD 与 OIL）。仅双代理打 GOLD = WEAK_EDGE。
- 统计：seed 20260825，bootstrap/perm 2000，block_length=5，BH m=3，q=0.05。
- 不改 FD V0.1 的 `FACTOR_SEARCH_SPACE` 文件。

**状态：** 2026-08-26。合同已写。实验已跑：`NO_CANDIDATE`，见 Decision 043。

---

## Decision 043 — V0.8 负结果冻结，禁止回头调 XA

**决定：**
- Cross Asset V0.8 已按合同跑完。程序结果 **`NO_CANDIDATE`**。HYP-XA-0001/0002/0003 均为 **FALSIFIED**。FDR m=3 discoveries=0。
- 禁止改领先期、67% 分位、DOLLAR_UP、预注册方向、V0.6 成本、持有规则来「救」这三条。
- 禁止新增 HYP-XA-0004，禁止把本家族扩成 10 条跨品种假设（V0.7.1 杀停）。
- 同期 gold/USD 相关不是 CANDIDATE，不准改成同 bar 交易故事而不另开合同。
- 下一合法模块（若另批）：Regime Transition V0.9 **新版本合同**，或停。不要 MT5，不要 Final OOS。

**状态：** 2026-08-26。已冻结。

---

## Decision 044 — V1 地图后下一刀只开 Regime Transition

**决定：**
- 规划权威改为 `ALPHA_COVERAGE_MAP_V1.md` + `TRADEMIND_ALPHA_ROADMAP_12M.md`。V0.7.1 不再当「下一刀 = Cross Asset」。
- Carry / 真 VRP / 事件 / 订单流 / 日内季节 = **DATA BLOCKED**，禁止写成可执行 TODO。
- 下一份可执行合同只能是 `REGIME_TRANSITION_V0.9`（HYP-RT-0001/0002/0003；hold=5；ADX14；VOL 33/67）。禁止第 4 条。
- 看见结果后不准改 hold / ADX / 分位 / 方向。
- 不实现、不跑数，直到另批。不跳级 Paper/MT5。

**状态：** 2026-08-26。合同已写，实验未跑。

---

## Decision 045 — Level 1 不是年化 10%；文档边际已尽

**决定：**
- `CANDIDATE_ACCEPTANCE_GATE_V1.md`：Level 1 = 成本后重复 + FDR + ≥2 target + 预注册机制。CAGR≥10% / Sharpe>1 / DD<20% 属于 Level 2 或资本标记。
- ALPHA_PROGRAM_V1 只设计。V0.9 hash 不准改。
- 再写同构文档不接近赚钱。下一刀是另批后的 V0.9 实现，或停。
- 月 10–12 Paper 仅当 Level 2 存在。

**状态：** 2026-08-26。

---

## Decision 046 — 52 题重评后仍先 V0.9；残差是第二家族且不并行

**决定：**
- 评分程序锁定：V0.9 簇最高（1600）。不是因为文件已在。
- 第二独立机制 = GOLD/OIL 慢速残差（`FAM-XR-RESIDUAL-0001`）。禁止与 V0.9 同时跑。
- 日历第三。4A/组合无袖套。
- 本步可以跑评分管线，不可以 SSH V0.9。

**状态：** 2026-08-26。

---

## Decision 047 — V0.9 / V0.91 负结果冻结

**决定：**
- V0.9 已按合同实跑。程序 **`NO_CANDIDATE`**。禁止改 hold / ADX / VOL 分位 / 方向。禁止 HYP-RT-0004。
- V0.91 已按合同实跑。程序 **`NO_CANDIDATE`**。禁止改 SMA60 / 33/67 / 翻面。
- 无 Candidate 禁止写策略层。
- 认证 CAGR 仍是「无」。V0.6 OIL +0.2% 不是 Level 1。
- 更长历史若另冻，必须新 `dataset_id`，不准覆盖 `20260825-000001`。

**状态：** 2026-08-27。已冻结。

---

## Decision 048 — Recovery 只开一个未知家族，且先锁再跑

**决定：**
- 冻结家族只做失败分析，禁止调参重开。
- Opportunity V2 自动打分后只许选 **一个** 新家族。
- 选中：`INSTITUTIONAL_TIME_V1.0`（month-end / month-start）。不是 weekday，不是指标农场。
- 合同先锁。**未经审查不得实现 runner，不得派 Xavier。**
- London/NY 需要先冻新的 5y H1 ID，不能用冻结的 2000 根 H1 冒充。
- GOLD/OIL D1 10y 在本经纪商上仍不存在（~2018 起）。不准编 10 年。

**状态：** 2026-08-27。合同已写。实验未跑。



