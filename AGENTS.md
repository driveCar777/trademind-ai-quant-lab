# TradeMind AI Quant Lab — AI 协作规则

> **最高法律。** Cursor / ChatGPT 每次打开本项目，必须先阅读本文件。

---

## 核心原则

> **一次只解决一个问题，一次只完成一个模块；没有通过冒烟测试，不开始下一模块；没有冻结，不重构整体。**

---

## 接力开发入口（必读顺序）

任何 AI 接手项目，**必须**按此顺序阅读：

1. **`docs/TRADEMIND_CONTEXT.md`**（最高优先级，防幻觉版上下文）
2. `AGENTS.md`（本文件，AI 协作规则）
3. `docs/TODO.md`（当前任务）
4. `docs/PROJECT_VISION.md`（项目愿景，仅供参考，不是事实）

**禁止依赖聊天上下文。** 所有决策以 `TRADEMIND_CONTEXT.md` 为准。

**冲突规则：** 任何与 `TRADEMIND_CONTEXT.md` 冲突的信息，以 `TRADEMIND_CONTEXT.md` 为准。

---

## 铁律：字段必须先查 SPEC

> **任何新增字段，必须先查 `SPEC.md`。未定义 → 先更新 SPEC → 再写代码。**

---

## 模块开发五阶段（铁律）

任何模块（Master、Worker、SDK、Dashboard……）**必须**经过以下五个阶段：

```
Phase 1  Design          设计
Phase 2  Implement       实现
Phase 3  Smoke Test      冒烟测试
Phase 4  Stability Test  稳定性测试
Phase 5  Freeze          冻结
```

**只有 Freeze 以后，才能开始下一个模块。**

进度追踪见 `TODO.md`，测试标准见 `TEST_PLAN.md`，项目状态见 `PROJECT_STATUS.md`。

---

## V1.1 Implement 八阶段（当前）

```
Phase 1  文档同步        ← PASS
Phase 2  Master 代码对齐
Phase 3  Worker 配置对齐
Phase 4  Smoke Test
Phase 5  Xavier 部署
Phase 6  端到端验证
Phase 7  稳定性测试
Phase 8  Freeze 文档更新
```

每完成一个 Phase，**必须**：
1. 输出 Phase 报告（状态 / 交付物 / 遗留问题）
2. 更新 `PROJECT_STATUS.md`
3. 停止，等待确认后再进入下一 Phase

---

## 项目定位

TradeMind 是**一人开发 + AI 长期协作**的本地 AI 量化研究平台。  
不是练手项目，而是可长期维护的软件产品。

---

## 开发规则（必须遵守）

### 1. Worker 规则

- 任何新 Worker **必须复制** `workers/indicator-worker` 模板
- **禁止**重新设计 Worker 目录结构
- **禁止**修改 Worker 公共接口（`/health`、`/ready`、`/version`、`/metrics`）
- Worker **永远负责计算**，不负责调度
- Worker **不知道 Master**（禁止 `master_host` / `master_port`）
- Worker 类型统一为 `indicator-worker`（非 `indicator`）

### 2. API 规则

- 计算类接口格式：`POST /api/v1/{service}/{action}`
- Master 业务接口统一响应格式：`{success, message, code, data}`（见 SPEC.md）
- 探针例外：`GET /health`、`GET /ready` 可保留轻量字段
- **禁止**引入 RabbitMQ、Kafka 等消息队列（见 DECISIONS.md）

### 3. 配置规则

- 所有环境变量统一前缀：`TRADEMIND_*`
- 配置文件放在 `config/` 目录（`master.yaml`、`worker.yaml`）
- **禁止**在代码中硬编码 IP、端口、密钥

### 4. 技术栈冻结（禁止升级）

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.8 | Xavier 兼容 |
| Docker | 当前版本 | 不升级 |
| JetPack | 当前版本 | 不升级 |
| FastAPI | 0.83.x | Worker 模板锁定 |

### 5. 目录规则

- **禁止**在根目录随意新建服务目录
- 新服务必须放在规定目录下（见 ARCHITECTURE.md）
- 每个目录必须有 `README.md`

### 6. Master 规则

- Master **永远运行在 Windows**
- Master **永远负责调度**，不负责计算
- LLM / AI 推理**只在 Master 运行**（Jetson 性能有限）
- V1.1 **只开发** `master/api/`，其它 Master 子目录保持空
- V1.1 唯一职责：`接收任务 → 找到 Worker → 调用 Worker → 保存结果`

### 7. 文档规则

- 重大架构决策写入 `DECISIONS.md`
- 每次完成功能更新 `CHANGELOG.md`
- 当前任务与五阶段进度写在 `TODO.md`
- 技术规范写在 `SPEC.md`
- 项目状态写在 `PROJECT_STATUS.md`
- 测试标准写在 `TEST_PLAN.md`
- 开发路线只写在 `ROADMAP.md`

### 8. 代码规则

- 优先编辑现有文件，不随意新建
- Worker Docker-only 部署；Master V1.1 可在 Windows 直接运行
- 冒烟测试放在 `tests/smoke/`（01_worker / 02_master / 03_master_worker）
- 模块单元测试放在各模块 `tests/`

### 9. AI 协作规则

- 开始任务前：读 `AGENTS.md` → `SPEC.md` → `PROJECT_STATUS.md` → `TODO.md`
- 完成任务后：更新 `PROJECT_STATUS.md`、`TODO.md`、`CHANGELOG.md`、`TEST_PLAN.md`
- **禁止**在未授权时开发 ROADMAP 中未到达的版本功能
- **禁止**同时推进多个模块
- **禁止**冒烟测试未通过就开始下一模块
- **禁止**新增架构设计或扩展 V1.2/V2 功能

### 10. 版本管理

- 研究代码与非敏感产物进入 **private GitHub**。禁止提交密码、token、`.env`。
- **禁止** `git reset --hard` / `git push --force` / 用 Git 回滚研究事实。
- 冻结合同与结果仍以文件 + `CHANGELOG.md` 为准，不得改写历史 evidence。

---

## V1.1 第一版禁止清单

以下在 V1.1 **全部禁止**：

| 类别 | 禁止 |
|------|------|
| 模块 | Scheduler、Dispatcher、Database 模块、Dashboard、SDK |
| 中间件 | RabbitMQ、Redis、消息队列 |
| 数据库 | SQLite、PostgreSQL、MySQL |
| 调度 | Cron、APScheduler、Timer、任务排队、线程池 |
| 前端 | Vue、React、Electron、Qt、WebSocket |
| 功能 | 自动重试、负载均衡、Worker 选择策略、超时恢复 |

V1.1 唯一目标：

```
POST /task → requests.post() → indicator-worker → RSI → 保存结果 → GET /task/{id}
```

存储：`storage/tasks/`（元数据）+ `storage/results/YYYY/MM/DD/`（结果分离）

---

## 当前阶段

**V1.0 — V11.0** ✅ 已冻结  
**Data Layer V0.1 / Qualification V0.1 / Readiness V0.2 / Research Protocol V0.3** ✅ 已冻结  
**Factor Discovery V0.1** ✅ 已冻结（`NO_USEFUL_FACTORS_FOUND`；不是策略；不是年化 10%）  
**Research Engine V0.5** ✅ 地基（`NO_USEFUL_STRATEGIES_FOUND`）  
**Profit Discovery V0.6** ✅ 已冻结（四 Xavier；`WEAK_EDGE_ONLY`；程序级 CANDIDATE=0；不是年化 10%）  
**Alpha Discovery V0.7** ✅ 仅设计（无代码；下一方向=跨品种 D1；不要再加简单策略）  
**Alpha OS V0.7.1** ✅ 仅设计（分类/矩阵/12 个月队列）  
**Cross Asset V0.8** ✅ 已冻结（四 Xavier；`NO_CANDIDATE`；3/3 FALSIFIED；FDR 0/3；不是年化 10%）  
**Alpha Map V1** ✅ 仅设计（覆盖/数据/排序/12M；Carry/IV/新闻 = BLOCKED）  
**Regime Transition V0.9** ✅ 已冻结（四 Xavier；`NO_CANDIDATE`；0001 FALSIFIED；不要第 4 条；不要调 ADX/hold/VOL）  
**ALPHA_PROGRAM_V1** ✅ Universe/分类器已落地（149 PASS；Level 1=0）  
**Residual V0.91** ✅ 已冻结（`NO_CANDIDATE`；不要调 SMA60）  
**Alpha Recovery V1.0** ✅ 失败分析 + 合同（当时未跑）  
**Alpha Mission V1.1** ✅ STOP B。IT WEAK_EDGE 已杀；TS/MS/RI/AMS FALSIFIED。Level=0 Candidate=0。  
**Alpha Research Mission V2.0** ✅ STOP B。IV/COT/EIA/UST10/CARRY_V1A **NO_CANDIDATE**。Level=0 Candidate=0。  
**Data Expansion Mission V3.0** ✅ WAIT_HUMAN 记录保留（SUPPLY_V1 NO_CANDIDATE）。  
**MT5 Max Mission V4.0** ✅ COMPLETE_NO_CANDIDATE。不要再调 gold-silver / DXY / EIA z_cut。  
**Market Universe V5.1** ✅ EXTERNAL_DATA_GATE。841 全是 CFD。BREADTH WEAK_EDGE。SIZE NO_CANDIDATE。不要改 V4 hash。不要覆盖 `20260825`/`20260828`。不要调 BREADTH/SIZE。  
**V6 External Exchange** ✅ Pack E 已拉（$31.82）。TERM_STRUCTURE NO_CANDIDATE。  
**V7 Information Fusion** ✅ STOP B+C。OI/Volume NO_CANDIDATE。DTE WEAK_EDGE。不要调 OI/volume/dte/斜率。  
**V8 Information Fusion** ✅ STOP C。TOP5 全失败。期权已报价（OG.OPT/LO.OPT）。未下载。Level=0 Candidate=0。不要调 gap/steepening/OI/wow/yield。不要 $199/月。不要 tick。  
V11：MT5 日线样本内外回测 + 风控证伪。`survived` 不是年化保证。
**V13 A-share CS alpha IN PROGRESS。** 只用冻结 `tm-ashare-EQUITY-D1-20260830-000002`。财务/行业/事件 BLOCKED。无采购。无 live API。Final OOS DENIED。不要重开 MT5 已杀死家族。
FINAL_OOS 仍未锁。HYP-0001 14:11 未改。不要 order_send。不要回头调 XA / RT / XR / IT / TS / MS / RI / AMS / IV / POS / INV / RATES / CARRY / SUP / CM / UM / BREADTH / SIZE。不要无 Candidate 写策略。

---

## 快速导航

| 文件 | 用途 |
|------|------|
| `SPEC.md` | V1.1 技术规范（最高技术法律） |
| `PROJECT_STATUS.md` | 项目状态快照（接力开发入口） |
| `PROJECT.md` | 项目介绍 |
| `TODO.md` | 当前任务与五阶段进度 |
| `TEST_PLAN.md` | 测试标准与 PASS 记录 |
| `ROADMAP.md` | 开发路线 |
| `ARCHITECTURE.md` | 系统架构 |
| `DECISIONS.md` | 架构决策 |
| `CHANGELOG.md` | 修改记录 |
