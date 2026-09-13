# TradeMind — V1.1 技术规范

> **最高技术法律。** 任何新增字段、接口、状态值，必须先写入本文件，再写代码。  
> 未定义 → 禁止实现。

> **冲突解决原则：** 最新冻结决策 > SPEC > 旧代码。Decision / Freeze 更新后，必须先修改本文件，再写代码。

---

## 一、V1.1 唯一职责

```
接收任务 → 找到 Worker → 调用 Worker → 保存结果
```

**V1.1 禁止：**

- 自动重试、负载均衡、Worker 选择策略
- 超时恢复、任务排队、定时任务
- AI 推理、MT5 调用、A 股数据
- 数据库（SQLite / PostgreSQL / MySQL）
- 消息队列（RabbitMQ / Kafka / Redis Pub/Sub）
- Dashboard、SDK、Scheduler、Dispatcher

---

## 二、Task 生命周期

```
CREATED → RUNNING → COMPLETED
                  ↘ FAILED
```

| 状态 | 说明 |
|------|------|
| `CREATED` | 任务已创建，尚未调用 Worker |
| `RUNNING` | 正在调用 Worker |
| `COMPLETED` | Worker 返回成功 |
| `FAILED` | Worker 不存在、离线、调用失败或计算失败 |

**禁止混用：** `done` / `success` / `finish` / `finished` / `ok` / `completed`（小写或非规范值）

**POST /task 行为：** 同步执行。请求内完成 Worker 调用后返回，不返回 `submitted`。

**POST /task 响应（统一包装）：**

```json
{
  "success": true,
  "message": "Task completed.",
  "code": "TM-0000",
  "data": {
    "task_id": "tm-task-20260716-000001",
    "status": "COMPLETED",
    "worker_id": "worker-01"
  }
}
```

`status` 允许 `CREATED` / `RUNNING` / `COMPLETED` / `FAILED`（大写）。

---

## 三、Task ID 格式

```
tm-task-YYYYMMDD-NNNNNN
```

| 部分 | 说明 |
|------|------|
| `tm-` | 固定前缀 |
| `task` | 固定标识 |
| `YYYYMMDD` | UTC 日期 |
| `NNNNNN` | 当日递增序号，6 位，从 `000001` 起 |

**示例：** `tm-task-20260716-000001`

**禁止：** UUID、`task-00001` 等非规范格式。

---

## 四、Worker 生命周期（V1.1）

```
OFFLINE ↔ ONLINE
```

| 状态 | 说明 |
|------|------|
| `ONLINE` | `GET /health` 返回 200 |
| `OFFLINE` | 健康检查失败或超时 |

**V2 预留（V1.1 不实现）：** `BUSY`、`MAINTENANCE`

**通信方向：** 单向 `Master → Worker`。Worker 不知道 Master，不回调 Master。

**Worker Base URL：** `http://{host}:8080`

---

## 五、Worker 类型

| 字段值 | 说明 |
|--------|------|
| `indicator-worker` | 指标计算 Worker |

**禁止：** `indicator`（无 `-worker` 后缀）

---

## 六、统一 API 响应格式

Master 对外**业务接口**统一此格式：

```json
{
  "success": true,
  "message": "",
  "code": "TM-0000",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否成功 |
| `message` | string | 人类可读说明，成功时可为空 |
| `code` | string | 错误码，见第七节 |
| `data` | object | 业务数据 |

**探针例外：** `GET /health`、`GET /ready` 可保留轻量字段（不强制包装），但不得与业务接口混用格式。

---

## 七、错误码（V1.1 固定四个）

| 代码 | 含义 |
|------|------|
| `TM-0000` | Success |
| `TM-1001` | Worker 不存在 |
| `TM-1002` | Worker 离线 |
| `TM-1003` | Task 执行失败 |

**禁止新增错误码**，除非写入新 Decision 并更新本文件。

---

## 八、Master API（V1.1）

### 8.1 GET /health

探针，返回 Master 健康状态（不强制统一包装）。

### 8.2 GET /workers

返回已注册 Worker 及运行时状态（`ONLINE` / `OFFLINE` + `latency_ms`）。

```json
{
  "success": true,
  "message": "",
  "code": "TM-0000",
  "data": {
    "workers": [
      {
        "id": "worker-01",
        "name": "Xavier Worker 01",
        "worker_type": "indicator-worker",
        "host": "192.168.1.200",
        "port": 8080,
        "description": "Jetson Xavier NX #1",
        "status": "ONLINE",
        "latency_ms": 18.0
      }
    ],
    "count": 1
  }
}
```

### 8.3 POST /task

同步提交并执行任务。

**请求：**

```json
{
  "worker_type": "indicator-worker",
  "indicator": "RSI",
  "data": {
    "symbol": "EURUSD",
    "timeframe": "M15",
    "close": [44.34, 44.09, 44.15]
  },
  "params": {"period": 14}
}
```

**响应：**

```json
{
  "success": true,
  "message": "Task completed.",
  "code": "TM-0000",
  "data": {
    "task_id": "tm-task-20260716-000001",
    "status": "COMPLETED",
    "worker_id": "worker-01"
  }
}
```

### 8.4 GET /task/{task_id}

查询任务元数据。若结果文件存在，**额外**带上 `result` 正文（给控制台展示 / 交给 AI）。磁盘仍以 `data/results/` 为准。

```json
{
  "success": true,
  "message": "",
  "code": "TM-0000",
  "data": {
    "task_id": "tm-task-20260716-000001",
    "status": "COMPLETED",
    "worker_type": "indicator-worker",
    "worker_id": "worker-01",
    "request": {},
    "result_path": "results/2026/07/16/tm-task-20260716-000001.json",
    "result_exists": true,
    "result": {"success": true, "indicator": "RSI", "symbol": "EURUSD"},
    "error": null,
    "created_at": "2026-07-16T10:00:00Z",
    "completed_at": "2026-07-16T10:00:01Z"
  }
}
```

| 字段 | GET /task/{id} | GET /tasks 列表项 |
|------|----------------|-------------------|
| `result` | 文件可读则为 JSON，否则 `null` | **始终 `null`**（不读结果文件） |
| `result_path` / `result_exists` | 有 | 有 |

`GET /tasks` **禁止**批量加载结果正文（回测曲线会放大响应）。结果文件损坏时：`result=null`，接口仍 200，不新增错误码。

---

## 九、Worker API（V1.1 不变）

沿用 V1.0 Worker Template：

| 接口 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /ready` | 就绪探针 |
| `GET /version` | 版本信息 |
| `GET /indicators` | 支持的指标列表 |
| `POST /api/v1/indicator/calculate` | 指标计算 |

Worker **禁止** 配置 `master_host` / `master_port`。

---

## 十、存储结构

```
data/
├── workers.json
├── tasks/
│   └── tm-task-20260716-000001.json
└── results/
    └── 2026/07/16/
        └── tm-task-20260716-000001.json
```

> **说明：** `data/` 为业务持久化目录。不再使用 `storage/` 作为业务数据目录。

### 10.1 workers.json

```json
[
  {
    "id": "worker-01",
    "name": "Xavier Worker 01",
    "worker_type": "indicator-worker",
    "host": "192.168.1.200",
    "port": 8080,
    "description": "Jetson Xavier NX #1"
  }
]
```

- 只存静态注册信息
- **禁止** 在文件中写 `status`、`online`、`latency`、`heartbeat`
- Master 运行时对每个 Worker 执行 `GET /health` → 判定 `ONLINE` / `OFFLINE` + `latency_ms`
- **禁止** 将运行时状态写回 JSON

**淘汰字段：** `worker_id`、`type`、`status`

### 10.2 tasks/{task_id}.json

任务元数据，**不含** `result` 正文：

```json
{
  "task_id": "tm-task-20260716-000001",
  "status": "COMPLETED",
  "worker_type": "indicator-worker",
  "worker_id": "worker-01",
  "request": {},
  "result_path": "results/2026/07/16/tm-task-20260716-000001.json",
  "error": null,
  "created_at": "2026-07-16T10:00:00Z",
  "completed_at": "2026-07-16T10:00:01Z"
}
```

### 10.3 results/{YYYY}/{MM}/{DD}/{task_id}.json

Worker 返回的完整计算结果。

---

## 十一、配置

```
config/
├── master.yaml
├── worker.yaml
└── logging.yaml
```

```
logs/
├── master/
├── worker/
└── system/
```

- 环境变量统一 `TRADEMIND_*` 前缀
- **禁止** 硬编码 IP、端口、密钥

---

## 十二、部署（V1.1）

| 组件 | 运行环境 | IP / 端口 |
|------|----------|-----------|
| Master | Windows PC | 192.168.1.101:9000 |
| indicator-worker #1 | Jetson Xavier NX | 192.168.1.200:8080 |
| indicator-worker #2 | Jetson Xavier NX | 192.168.1.201:8080 |
| indicator-worker #3 | Jetson Xavier NX | 192.168.1.202:8080 |
| indicator-worker #4 | Jetson Xavier NX | 192.168.1.203:8080 |

**V1.1 部署顺序：** 先 Xavier 验证 Dockerfile + docker compose，Buildx 统一构建后置。

---

## 十三、V1.1 Definition of Done

1. **功能：** Windows Master → POST /task → Xavier indicator-worker → RSI → GET /task/{id} → PASS
2. **测试：** Smoke 01/02/03 全部 PASS + 连续 100 次 RSI PASS
3. **文档：** SPEC / CHANGELOG / TODO / TEST_PLAN / PROJECT_STATUS 全部更新

三层全部 PASS → V1.1 Freeze。

---

## 十四、V3.0 AI Gateway 代理（Master）

> 本机推理仍是 **Qwen2.5-14B-Instruct Q4_K_M**。另外允许 **目录里列出的** 远程模型：DeepSeek 官方 API、Cursor `GET /v1/models` 返回的 id。页面只准下拉选择，禁止手输模型名。没有对应 key 的项 `available=false`，选了不能发。

Master **不负责推理**。Master 只把 AI 请求转发到独立进程 AI Gateway (`port 9100`)。

### 14.1 配置

| 项 | 来源 | 默认 |
|----|------|------|
| `ai_gateway.url` | `config` / `TRADEMIND_AI_GATEWAY_URL` | `http://127.0.0.1:9100` |
| `ai_gateway.timeout_seconds` | `config` / `TRADEMIND_AI_GATEWAY_TIMEOUT_SECONDS` | `120` |
| DeepSeek key | `.env` `TRADEMIND_DEEPSEEK_API_KEY` | 空 = 目录仍列出官方两只，但 `available=false` |
| Cursor key | `.env` `TRADEMIND_CURSOR_API_KEY` | 空 = 目录用冻结兜底 id，`available=false` |

**禁止** 在代码中硬编码 Gateway IP/端口。密钥只进本机 `.env`，禁止入库。

`GET /models` 的每条：`id`（`local:…` / `deepseek:…` / `cursor:…`）、`provider`、`label`、`available`、`name`（兼容旧字段=label）。DeepSeek 有 key 时拉 `https://api.deepseek.com/models`；Cursor 有 key 时拉 `https://api.cursor.com/v1/models`。页面只渲染这些 id。

请求体可带 `model`（必须是目录里的 `id`）。缺省 = 本机 Qwen。未知 id → `TM-1001`。Cursor id 目前不能当聊天补全（官方是 Agent API）；选了返回 503，提示改用本机或 DeepSeek。

### 14.2 Master 代理路由

| Master 路由 | 转发到 Gateway |
|-------------|----------------|
| `GET /api/v1/ai/health` | `GET /health` |
| `GET /api/v1/ai/models` | `GET /models` |
| `POST /api/v1/ai/generate` | `POST /api/v1/ai/generate` |
| `POST /api/v1/ai/describe` | `POST /api/v1/ai/describe` |
| `POST /api/v1/ai/signal` | `POST /api/v1/ai/signal` |
| `POST /api/v1/ai/chat` | `POST /api/v1/ai/chat` |

成功时原样返回 Gateway JSON（已是 `{success, data}`）。

| 情况 | HTTP | code | message |
|------|------|------|---------|
| Gateway 不可达 | 503 | `TM-1002` | AI Gateway offline |
| Gateway 超时 | 504 | `TM-1004` | AI Gateway timeout |
| Gateway 返回非 JSON | 502 | `TM-1003` | AI Gateway invalid response |

**禁止** Master 本地加载模型、禁止新增错误码。

---

## 十五、V3 运维：启动 / 重启（Master）

> 控制台运维。不负责计算。不重启通义千问（必须独立 SYCL 窗口）。

### 15.1 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `POST` | `/api/v1/ops/worker/{worker_id}/start` | 拉起该 Xavier 上的 Worker |
| `POST` | `/api/v1/ops/worker/{worker_id}/restart` | 停掉再拉起该 Worker |
| `POST` | `/api/v1/ops/master/restart` | 脱离进程重启本机调度中心 |

`worker_id` 只允许 `worker-01` … `worker-04`。

### 15.2 成功 `data`

| 字段 | 类型 | 说明 |
|------|------|------|
| `worker_id` | string / null | 调度中心重启时为 null |
| `action` | string | `START` / `RESTART` |
| `accepted` | bool | 已接手 |
| `hint` | string | 给人看的下一句 |

`action` 只允许大写 `START` / `RESTART`。

### 15.3 错误（复用已有码，不新增）

| 情况 | HTTP | code |
|------|------|------|
| 未知 `worker_id` | 200 | `TM-1001` |
| SSH / 板子不可达 | 200 | `TM-1002` |
| 拉起失败 | 200 | `TM-1003` |

调度中心重启：立即 `accepted=true`，由脱离脚本结束 :9000 再执行 `start_master.bat`。页面约 10 秒后刷新。

### 15.4 四台 Xavier 启动方式

当前阶段 **4 台都参与计算**。一键脚本对四台同等：已健康则跳过，不健康才拉起。

| worker_id | 主机:端口 (FACT) | 拉起方式 |
|-----------|------------------|----------|
| worker-01 | `192.168.1.200:8080` | Docker：`docker start` / `docker restart`，只认固定容器名 |
| worker-02 | `192.168.1.201:8080` | `nohup python3 server.py` |
| worker-03 | `192.168.1.202:8002` | 同上（板上口写死 8002） |
| worker-04 | `192.168.1.203:8080` | 同上 |

worker-01 容器名只按名单匹配，禁止重启「`docker ps` 第一行」。名单：`indicator-worker-01`、`trademind-indicator-worker`、`trademind-indicator`；再否则仅当 Ports 含 `8080`。

网页 `POST .../worker/worker-01/start|restart` 走同一脚本。不新增字段、不新增错误码。

### 15.5 本机一键状态（脚本，无新路由）

`scripts/lab_status.py` 只读现有健康接口，不新增 Master 字段。

| 来源 | 用途 |
|------|------|
| `GET {TRADEMIND_MASTER_URL}/health` 默认 `http://127.0.0.1:9000` | 调度中心 |
| `GET {TRADEMIND_AI_GATEWAY_URL}/health` 默认 `http://127.0.0.1:9100` | 通义千问是否 `model_loaded` |
| `GET {Master}/workers` | 四台 Xavier 在线/离线 |

禁止用 `netstat | findstr :9000` 作为「已经在跑」的唯一依据。端口占用但 health 失败时，禁止再开第二个 Master / Gateway 窗口。

---

## 十六、V4.0 Research Agent（冻结 2026-08-23）

人点一次「研究一笔」：1 次现有计算 + 至多 1 次 AI。指标收盘价来自 `data/samples/`（§20），因子/回测/监控仍是预设/内置库。不是实时行情。

### 16.1 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `POST` | `/api/v1/research/run` | 同步：一笔预设计算 + 至多一次 AI |
| `GET` | `/api/v1/research/{research_id}` | 读研究记录 |
| `GET` | `/api/v1/research` | 列表，`limit` 默认 20 |

`POST` 请求：`{"preset": "indicator"}`，`preset` 可省略。允许：`indicator` / `factor` / `backtest` / `monitor`。

成功 `data`：`research_id`、`task_id`、`preset`、`summary`、`ai_text`、`ai_skipped`、`created_at`。

### 16.2 约束

- 一次研究最多 1 次任务、最多 1 次 AI。  
- `preset` 空则按在线节点推荐（指标→因子→回测→监控）。非法 preset → `TM-1001`。  
- 已有研究在跑 → `TM-1005`。 Worker 离线 → `TM-1002`。任务失败 → `TM-1003`。超时 → `TM-1004`。  
- 网关离线/忙碌：研究仍成功，`ai_skipped=true`。  
- AI 只接收结果摘要。不引入队列 / 数据库。不新增错误码。

存储：`data/research/{research_id}.json`。

---

## 十七、V4.1 两步研究（冻结 2026-08-23）

在 V4.0 同一条 `POST /api/v1/research/run` 上增加可选两步。仍不是 MT5，仍禁止队列/库。

### 17.1 请求

| 字段 | 必填 | 说明 |
|------|------|------|
| `preset` | 否 | 与 §16 相同，单步 |
| `chain` | 否 | 1～2 个预设名。超过 2 个或含未知名 → `TM-1001` |

`chain` 与 `preset` 同时出现时，必须 `chain == [preset]`，否则 `TM-1001`。都空则仍按在线推荐单步。

### 17.2 行为

- 开算前：链上每台 Worker 都必须 ONLINE，否则 `TM-1002`，一步都不跑。
- 第一步失败：不跑第二步。
- 仍只一把研究锁；进行中再请求 → `TM-1005`。
- 至多 1 次 AI，只解读**最后一步**摘要。监控仍可 `ai_skipped`。
- 成功 `data` 在 §16 字段外增加 `steps`：`[{preset, task_id, summary}, ...]`。`task_id` / `preset` / `summary` 等于最后一步。

---

## 十八、V5.0 模拟纸质单（冻结 2026-08-23）

研究结论可以变成**一张可核对的模拟单**。不是实盘，不是自动下单。

### 18.1 拍板

| 项 | 决定 |
|----|------|
| 盘 | 只模拟纸质单。V5.0 **禁止** `order_send` |
| 确认 | 必须人手 `confirm=true`。研究跑完不自动开单 |
| 谁跑 | 只在 Windows Master。Xavier 不碰 MT5 |
| 源 | 只读已有 `data/research/`。不发明新行情 |

### 18.2 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/mt5/status` | 探测本机终端：是否装了包、能否连上、demo/live |
| `POST` | `/api/v1/orders/preview` | 根据 `research_id` 生成拟单，不落盘 |
| `POST` | `/api/v1/orders/submit` | `confirm=true` 才落盘一张模拟单 |
| `GET` | `/api/v1/orders` | 列表，`limit` 默认 20 |
| `GET` | `/api/v1/orders/{order_id}` | 读一张单 |

`preview` / `submit` 请求：`research_id` 必填。`submit` 另需 `confirm`（必须 `true`）。

成功 `data`：`order_id`（preview 可为空）、`research_id`、`symbol`、`side`（`BUY`/`SELL`/`HOLD`）、`volume`、`status`（`PREVIEW`/`ACCEPTED`/`REFUSED`）、`mode`（恒为 `paper`）、`reason`、`mt5_connected`、`account_mode`、`created_at`。

### 18.3 规则

- 缺 `confirm=true` → `TM-1001`。研究不存在 → `TM-1003`。已有该研究的 `ACCEPTED` 单再提交 → `TM-1005`。
- 仅 `preset=indicator` 且能从摘要读出 RSI：`>=70` → `SELL`，`<=30` → `BUY`，否则 `HOLD`/`REFUSED`。
- 其它预设 → `REFUSED`，`reason=not_orderable_preset`。
- 探测到 live 账户只记账，仍不发单。
- 存储：`data/orders/{order_id}.json`。不引入队列/库。不新增错误码。

---

## 十九、V6.0 今日台账（冻结 2026-08-23）

仍禁止向 MT5 发单。人先看拟单，再确认纸质单。

### 19.1 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/desk/today` | 当天（UTC 日期）研究记录 + 纸质单，只读 |

成功 `data`：`date`（`YYYYMMDD`）、`research`（`ResearchData` 列表）、`orders`（`OrderData` 列表）、`research_count`、`order_count`。

### 19.2 控制台

- 打开研究时必须先 `POST /api/v1/orders/preview`，把拟单写在弹窗里，再允许点确认。
- 研究成功后可出现「先看拟单」条；该条只 preview，不 submit。
- `init()` 禁止 `POST /orders/submit`。
- 仍须 `confirm=true` 才落盘。`mode` 恒为 `paper`。

---

## 二十、V7.0 本机样本 CSV（2026-08-24）

指标研究的收盘价来自本机文件，不是实时行情。不改 Worker。禁止 `order_send`。

### 20.1 存储

`data/samples/{sample_id}.csv`（utf-8）。内置 `eurusd.csv`。

`sample_id` 只允许 `^[a-z0-9][a-z0-9_-]{0,31}$`。表头必须有 `close`；可选 `symbol`。15～500 行有效收盘价。

### 20.2 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/samples` | 列出本机样本 |

成功 `data`：`items`（`sample_id`、`filename`、`rows`、`symbol`）、`count`。

### 20.3 研究

`POST /api/v1/research/run` 增加可选 `sample_id`。

- `preset=indicator` 且 `sample_id` 空 → 用 `eurusd`。  
- 非法 id、种类和预设对不上、监控带了 `sample_id` → `TM-1001`。  
- 文件缺失 / 读失败 / 行数不合 → `TM-1003`。  
- 成功记录可带 `sample_id`。旧记录没有该字段仍合法。  
- 因子 / 回测默认文件见 §21。监控 payload 不变。

---

## 二十一、V8.0 因子 / 回测本机样本（2026-08-24）

Master 从本机 csv 读出 Worker **已经认识**的字段。不改 Worker。不是行情。禁止 `order_send`。

### 21.1 文件

| sample_id | kind | 表头 | 默认预设 |
|-----------|------|------|----------|
| `eurusd` | indicator | `symbol,close` | indicator |
| `moutai` | factor | `stock,date` | factor |
| `xauusd` | backtest | `strategy,symbol,start` | backtest |

### 21.2 研究

- `preset=factor` 且 `sample_id` 空 → `moutai`。  
- `preset=backtest` 且 `sample_id` 空 → `xauusd`。  
- `GET /api/v1/samples` 的 `items` 增加 `kind`。  
- 两步 `chain` 不带 `sample_id` 时，每步用上表默认。

---

## 二十二、V9.0 MT5 模拟盘（2026-08-24）

人手确认后，**模拟盘**可以发到本机 MT5 终端。实盘账户必须拒绝。Xavier 不算终端、不 `order_send`，只算 Master 给它的 `{symbol, close}`。

V5.0 纸质单冻结件不改写。本版是新路径。

### 22.1 拍板

| 项 | 决定 |
|----|------|
| 盘 | 仅 `account_mode=demo` 才 `order_send`。`live` → 拒绝 |
| 确认 | 仍须人手 `confirm=true`。研究结束不自动开单 |
| 谁跑 | Windows Master 连终端。Xavier 只算数 |
| 品种 | 黄金 / 欧美 / 原油 / 美日。按终端真实代码解析（Ava 黄金是 `GOLD`、原油是 `CrudeOIL`，不是死写 `XAUUSD`） |
| 测试 | 冒烟必须 `TRADEMIND_MT5_SEND=0`，禁止打到真实模拟账户 |
| 同花顺 | 本环境没有可测的官方行情/下单接口。A 股仍走因子 Worker + `moutai.csv`。不假装已接通 |

### 22.2 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/mt5/status` | 探测 demo/live，附带四品种是否有报价 |
| `GET` | `/api/v1/mt5/quotes` | 四品种最新价 |
| `POST` | `/api/v1/research/run` | 可选 `source=mt5`、`symbol`。只允许单步 `indicator` |
| `POST` | `/api/v1/orders/submit` | demo 且已连接才发终端；否则纸质记账；live 拒绝 |

`source=mt5` 且预设不是单步 indicator → `TM-1001`。拉不到足够 M15 → `TM-1003`。

成功研究记录增加 `source`、`symbol`。成功订单可带 `mt5_ticket`、`mode=demo`。旧记录缺这些字段仍合法。

### 22.3 规则

- 默认手数 `0.01`，magic `240824`。
- `TRADEMIND_MT5_SEND=0` 时 `order_send` 不执行，订单以 `paper` 记账。
- 不改 Xavier Worker。不引入队列/库。不新增错误码。
- 不接同花顺下单。

---

## 二十三、V10.0 测通模拟盘（2026-08-24）

V9 的 RSI 门不变：`>=70` 拟卖，`<=30` 拟买，中间 `HOLD` / `rsi_neutral`。  
中间不是没有终端，是没有信号。要测通路，人手带 `side`。

### 23.1 拍板

| 项 | 决定 |
|----|------|
| 测通 | `POST /orders/submit` 可选 `side=BUY` 或 `SELL` |
| 谁能测 | 仅 `preset=indicator` 且研究里有品种 |
| 确认 | 仍须 `confirm=true` |
| 盘 | 仍仅 demo 发单，live 拒绝 |
| 含义 | `reason=wire_test`。不是预测有效 |

### 23.2 规则

- 非法 `side` → `TM-1001`。
- 无 `side` 时行为与 §22 / §18 相同（中性仍拒绝）。
- 成功订单可带 `reason` 含 `wire_test`。不新增错误码。不改 Xavier。

---

## 二十四、V11.0 MT5 历史回测 + 风控证伪（2026-08-24）

用本机 MT5 日线收盘价做样本内 / 样本外回测。目标是证伪，不是承诺收益。

### 24.1 拍板

| 项 | 决定 |
|----|------|
| 数据 | Master 拉 MT5 `close`。先 H1 2000 根，成交不足再 M15 2000、再 H4 1000。两边各至少 5 笔成交 |
| 谁算 | Xavier `backtest-worker`。可选 `close[]`；没有则仍走旧合成路径 |
| 切分 | 前 70% 样本内，后 30% 样本外。两边各跑一次 |
| 策略 | 现成 `RSI`。滑点 10bp，佣金 5bp |
| 风控 | 回撤 > 25% → `risk_fail`；任一边成交 < 5 → `insufficient`；样本外收益 ≤ 0 → `falsified`；否则 `survived` |
| `survived` | 本次未被证伪。不是有效、不是年化保证 |
| 下单 | 本版不自动 `order_send` |

### 24.2 研究

`POST /api/v1/research/run`：`source=mt5` 且 `preset=backtest`。  
成功记录可带 `verdict`、`bars`、`timeframe`。旧记录缺这些字段仍合法。

`source=mt5` 只允许单步 `indicator` 或单步 `backtest`。

### 24.3 V11.3 解读接线（2026-08-24）

网关 `strategy_description` 只读 `context.result`。回测数字必须放在 `result` 里，样本内/外放 `benchmark`。  
有 `verdict` 时不调用模型，按数字写 `ai_text`，`ai_skipped=true`。不能把摘要里的成交笔数写成 0。

### 24.4 V11.4 成交明细（2026-08-24）

本机仓库**不存**整段黄金行情。K 线在跑证伪时从本机 MT5 拉。Master 必须留下每根 `time`（unix 秒）和收盘价；Xavier 仍只收 `{symbol, close}`。

回测 Worker ≥ 2.1.2 在结果里回 `trades[]`：`type`、`idx`、`price`，平仓带 `pnl_pct`。Master 用该段 `time[idx]` 写成可读时间。

成功研究记录可带：

| 字段 | 说明 |
|------|------|
| `window_from` / `window_to` | 整段 K 线起止（UTC 显示） |
| `trades` | `{split, side, idx, time, price, pnl_pct}`，样本内在前 |

旧记录没有这些字段仍合法。没有明细就不许假装有买卖点。成交明细不是买卖单。

### 24.5 V11.5 连续切分 + 冻结策略篮（2026-08-24）

样本内 / 样本外是**同一条持仓**的前后两段，不是两段各算一遍。

| 项 | 决定 |
|----|------|
| 计算 | Worker ≥ 2.1.3 吃整段 `close[]` + `cut`。切分处不强制平仓 |
| 样本内盈亏 | 切分前一根基差到切分点（含未实现） |
| 样本外盈亏 | 切分点净值到期末 |
| 跨段单 | 切分前买、切分后卖：买记样本内，卖记样本外 |
| 策略篮 | 冻结默认参数：`RSI` `EMA_MACD` `SMA_CROSS` `BOLLINGER` `TURTLE`。禁止按样本外调参 |
| 不做 | 网格搜参、VWAP（量是合成的）、GRID |

成功记录可带 `cut`、`carry=true`、`basket[]`。主摘要仍是 RSI。`survived` 仍不是买卖单。

### 24.6 V11.6 行情分段（2026-08-24）

一年整体上涨，里面仍有下跌和震荡。不允许全年只用一套多头。

| 项 | 决定 |
|----|------|
| 特征 | 每根两个数：相对 50 均线偏离、近 20 根收益波动。冻结线性分割，不训练、不用神经网络 |
| 分段 | `up` / `down` / `range`。偏离 > 0.4% 上涨，< -0.4% 下跌，否则震荡 |
| 映射 | 上涨 → `SMA_CROSS`；震荡 → `BOLLINGER`；下跌 → 空仓。映射写死，不看样本外 |
| 代价 | 换段平仓走原滑点+佣金 |
| 策略 | Worker `REGIME_SWITCH` 进策略篮。另给各策略按「开仓时所在段」汇总盈亏 |
| 不做 | 用样本外改映射、张量拟合、隐马尔可夫搜参 |

成功记录可带 `regime_counts`、`regime_table`。下跌空仓也是策略。不是买卖单。

### 24.7 V11.7 四台并行、样本内筛选（2026-08-24）

四台 Xavier 都是 ARM64 计算节点。回测仍是标准库，可在 01/02/03/04 的 8002 上并行跑。原角色（指标/因子/回测/监控）不撤。

| 项 | 决定 |
|----|------|
| 并发 | Master 把候选打到所有在线 `backtest-worker`，线程扇出。单台也能并发 |
| 筛选 | 只看样本内：成交≥5、回撤≤25%，得分=`is_profit - 0.3*is_dd`。禁止用样本外挑参 |
| 验证 | 选中组的样本外只公布一次，用来判定 |
| 候选 | 冻结的一小盘：几组 RSI/均线/布林 + 海龟 + 分段切换。不是海量网格 |
| 不做 | 用样本外回写参数、改 nvpmodel、上 GPU 张量 |

成功记录可带 `mine[]`、`picked`、`mine_workers`。`survived` 仍不是买卖单。

---

## 二十五、Data Layer V0.1（本地 Windows，不接 V11.7）

独立市场历史数据层。不是 Master 路由，不是 Xavier API，不改 §24 回测字段。

### 25.1 目录

| 路径 | 用途 |
|------|------|
| `data/market/immutable/{dataset_id}/` | 唯一 bars 副本 + `manifest.json` + `DATA_QUALITY.json` |
| `data/market/manifests/{dataset_id}.json` | 清单索引 |
| `data/market/final_oos/LOCK.json` | `FINAL_OOS_LOCKED`，V0.1 为 `false` |
| `data/mine/longrun/` | V11.7 证伪实验（禁止混入） |

存储策略：`single_immutable_copy`。`raw/` 与 `validated/` 留空，避免重复拷贝。

### 25.2 Bar 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp_utc` | string | 存储时区只能是 UTC，`YYYY-MM-DDTHH:MM:SSZ` |
| `timestamp_unix` | int | MT5 bar `time`（UTC epoch） |
| `open` / `high` / `low` / `close` | float | 必须 finite 且 > 0 |
| `tick_volume` | int or null | 不得写成来源不明的 `volume` |
| `real_volume` | int or null | 全 0 合法；不得用 tick 冒充 |
| `spread` | int or null | 缺失写 null，禁止偷填 0 |

格式：CSV（当前环境无 pandas/pyarrow）。文件 SHA256 写入 manifest。

### 25.3 Manifest 字段

`dataset_id`、`logical_symbol`、`mt5_symbol`、`timeframe`、`timeframe_minutes`、`source`、`source_type`、`broker`、`terminal`、`terminal_version`、`python_package_version`、`retrieved_at_utc`、`data_start_utc`、`data_end_utc`、`row_count`、`columns`、`timezone`、`volume_policy`、`history_request`、`sha256`、`validation_status`、`schema_version`、`tick_volume_present`、`real_volume_present`、`spread_present`、`parent_dataset_id`、`history_shortfall`、`requested_*` / `actual_*`、`FINAL_OOS_LOCKED`、`role`。

`dataset_id` 形如 `tm-market-GOLD-M15-20260825-000001`。再次抓取必须新 id，禁止覆盖。

### 25.4 校验

重复 / 乱序 timestamp → FAIL。OHLC 违反、NaN、inf、零价、负价 → FAIL，不自动修。D1 与周末 gap ≠ 错误（WARN）。`real_volume` 全 0 → `volume_policy=tick_volume_only`，不得因此 FAIL。请求根数 > 实得 → WARN + `history_shortfall`。

### 25.5 只读 MT5

允许：`initialize` / `shutdown` / `terminal_info` / `version` / `symbols_get` / `symbol_info` / `symbol_select` / `copy_rates_*` / `last_error`。

任何交易 API（含 `order_send`）→ `RuntimeError("DATA_LAYER_READ_ONLY")`。

逻辑品种 `GOLD` / `EURUSD` / `USDJPY` / `OIL` 经现场 `symbols_get` 解析 `mt5_symbol`，禁止写死 XAUUSD 一定存在。

---

## 二十六、Data Qualification V0.1（四台 Xavier 一次性画像）

不是 Worker，不占 8002–8005，不注册 Master。脚本：`research_profile/research_probe.py`。

每个冻结 dataset 产出 `dataset_profile.json`。资格四档：`QUALIFIED` / `QUALIFIED_WITH_WARNINGS` / `DATA_REVIEW_REQUIRED` / `DATA_INVALID`。只表示研究就绪，不表示可交易。

`FINAL_OOS_LOCKED` 保持 `false`。70/15/15 只允许写 `CANDIDATE_WINDOW`。

跨节点：同一 `dataset_id` 在两台 Xavier 上 comparable 字段必须一致。

快照：关闭 bar 的 OHLC 变化记 `HISTORICAL_MUTATION`，禁止覆盖任一侧。

---

## 二十七、Research Readiness V0.2

四台 Xavier 一次性 `research_readiness/node_runner.py`。每 dataset 至少 20 次重复。`profile_hash` 必须全同。

分块 8×250。滚动 200/100。故障只打 `/tmp` 副本。`FINAL_OOS_LOCKED` 保持 false。

资格结构档：`READY_FOR_RESEARCH` / `READY_WITH_REVIEW` / `HOLD_FOR_REVIEW` / `INVALID`。不是交易评分。

---

## 二十八、Research Protocol V0.3

独立因果研究沙箱。不是回测引擎，不改 §24 / §25。包：`research_protocol/`。调度：`scripts/research_protocol_run.py`。Xavier：`node_runner.py` one-shot。

### 28.1 合同

实验前 `verify_hash()` 必须通过，否则 `EXPERIMENT_BLOCKED`。  
Experiment id：`tm-exp-YYYYMMDD-HHMMSS-NNN`。合同 write-once。改 dataset / 参数 / 窗口 / 执行 / 成本 / 策略 → 新 id。  
状态：CREATED → VALIDATED → RUNNING → COMPLETED | FAILED → FROZEN。禁止改 COMPLETED 合同。

窗口记录 `start_timestamp_utc` / `end_timestamp_utc`。默认候选切分 70/15/15（可配置，创建后冻结）。`FINAL_OOS_LOCKED` 保持 false。

Lookback：第一信号 = research_start + lookback。  
Purge / embargo：研究标签不得穿入 Validation；Validation 与 Holdout 之间同样隔离。  
执行：`NEXT_BAR_OPEN` 为 `close(t)` 信号、`open(t+1)` 成交。禁止用 `close[t]` 在 `open[t]` 执行。

### 28.2 因果与泄漏

`CausalView` 只允许 `0..t`。未来 index → `FUTURE_DATA_ACCESS`。  
Feature Registry：sma / ema / rsi / atr / macd / bollinger / vwap。VWAP 仅 `tick_volume`。缺量 → `FEATURE_UNAVAILABLE`。  
纯度：只改未来 close / volume / high / low / timestamp，过去 feature 必须不变。

### 28.3 节点

Windows 只编排。Xavier 只计算。四台各至少 10 次 feature / window / leakage。交叉至少 Xavier-01↔04、Xavier-02↔03。stdlib only。结果不得写回 `data/market/immutable/`。

---

## 二十九、V29 A 股纸面台（Master 只读 + 预览）

给人看 ML1 / V26.8 短名单和影子账本。不发单。不改 ML1 特征 / 持有期 / 成本 / refit。

### 29.1 路由

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/paper` | 纸面台 HTML |
| `GET` | `/api/v1/paper/desk` | 状态 + 本期持仓 + 日期窗 + 资金曲线 + TOP20 账本 |
| `POST` | `/api/v1/paper/preview` | 按新资金重算手数，并按同一套 V26.8 规则重跑研究/验证账本（预览，不写冻结 READ、不改官方仓） |
| `PUT` | `/api/v1/paper/settings` | 写下一次预览默认资金（`live/PAPER_SETTINGS.json`） |

### 29.2 `GET /api/v1/paper/desk` 的 `data`

`asof_session`、`contract`、`status`、`settings`、`shortlist`、`holdings[]`（本期 OPEN：`symbol,name,buy_date,buy_price,mark_date,mark_price,lots,shares,cost_in,buy_fee,unrealized,recipe`）、`holdings_august[]`（本月已平仓：买入/卖出日价、净利、`recipe`）、`books`（`live`/`august`/`validation`/`research` 各带 `kind`+`rows`，切页用）、`window`、`curves`、`preset_replay`、`ledger`、`august`、`orders_sent`（恒 `false`）。切曲线页必须换表和票据。

`window` 另含首页动作态：`today_action` ∈ `HOLD | SELL | BUY | UNKNOWN`（按 `asof_session` 与 `exit_date` 在交易日历上的位置算出）、`sessions_held`（买入开盘后已过交易日数）、`sessions_left`、`sessions_total`（=20，`held + left == total`）。只描述状态，不发单。

禁用窗日期只展示为已消耗，不得用来选变体。

### 29.3 `POST /api/v1/paper/preview` 请求

| 字段 | 类型 | 说明 |
|------|------|------|
| `capital` | number | 必填，> 0。账户资金（元） |
| `monthly_contrib` | number | 可选，默认设置值。只展示，不改官方账本 |
| `max_price` | number | 可选，默认 100。信号日收盘上限 |
| `n_target` | int | 可选，默认 10。改 N = 预览，不是新合同采纳 |
| `boards` | string | 可选，`MAIN` / `MAIN_CHINEXT` / `ALL` |

`data`：`contract`、`capital`、`unit_yuan`、`n_target`、`n_names`、`est_invested_yuan`、`cash_yuan`、`preview`（恒 `true`）、`names[]`（`rank,symbol,score,last_close,lots_100_est,est_yuan`）、`replay`（可空：`research` / `validation` / `live`（本期/本周） / `august`（本月）曲线与持仓；`official_capital` 恒 20000）。

手数公式与 V26.8 相同：`unit=max(2000, capital/n_target)`，`lots=floor(unit/(100*close))`，再按分数补手到仓位。名字来自最近 SIGNAL 的前 20% 分数，不再拟合。

`replay` 用冻结 ML1 分数在研究窗 + 验证窗各跑一次账本。不读禁用窗。不覆盖 `ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json`。本期影子仓仍是官方 ¥20,000。

### 29.4 规则

- 不写冻结研究目录。不 `order_send`。
- 改 `n_target` / `exposure` / 持有期不得当成官方外壳；官方默认仍是 V26.8。
- 资金可调：预览立刻变手数，并按该资金重跑研究/验证曲线；`PUT settings` 只记默认资金，不改已开仓影子账本。官方合同仍是 V26.8 / ¥20,000。
- 缺文件 → `TM-1003`。

### 29.5 操作台 V2 路由（2026-09-07，设计见 `docs/research_engine/PAPER_OPS_DESK_V2_DESIGN.md`）

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/paper/ops` | 今天的操作计划 + 数据新鲜度 + 运行状态 + 成交日志派生账户 + 历史每一期 |
| `POST` | `/api/v1/paper/update` | 后台启动 `daily.py --asof <最近已收盘交易日>`。休市自动回跳上一开盘日。已是最新且日线无缺口则 `skipped` 不启动。有锁则返回当前运行。 |
| `POST` | `/api/v1/paper/update/stop` | 结束正在跑的更新（`taskkill /T`）。已下好的日线保留，下次从缺口续。没有在跑则返回 `stopped=false`。 |
| `GET` | `/api/v1/paper/update/status` | 运行锁 / 进度阶段 / 日志尾 / 上次运行结果 / `asof_target` |
| `GET` | `/api/v1/paper/journal` | 成交日志（事件 + 派生持仓/现金） |
| `POST` | `/api/v1/paper/journal` | 追加一条事件 `{type: BUY|SELL|DEPOSIT|WITHDRAW|NOTE, date, symbol?, lots?, price?, fee?, note?}` |
| `DELETE` | `/api/v1/paper/journal/{event_id}` | 删除一条事件（用于改错） |

### 29.6 `GET /api/v1/paper/ops` 的 `data`

- `freshness`：`today`、`today_is_trading_day`、`last_completed_session`（今天 18:00 前 = 上一个交易日；休市回跳上一开盘日，不用未来）、`asof_session`、`stale_sessions`、`needs_update`、`bars_gap`（`n_missing`/`n_ok`，页面加载时清点）、`update_window`。
- `run`：`running`、`pid`、`started_at`、`elapsed_s`、`stage`（从日志识别的阶段文字）、`log_tail[]`、`last_run`（`STATUS.json` 摘要：`asof_session,started_at,elapsed_s,errors[]`）、`last_failed`。
- `plan`：`phase` ∈ `UPDATE_FIRST | SELL_TODAY | LIST_READY_BUY_TOMORROW | SIGNAL_TONIGHT | BUY_TODAY | HOLD | NO_POSITION`；`headline`、`sub`、`steps[]`（每步 `{when, text}`）、`sell_list[]`、`buy_list[]`（按实际现金重算：`rank,symbol,name,last_close,lots_100_est,est_yuan,score`）、`cash_check`（`cash_available, reserve, budget, planned_yuan, ok, shortfall, source ∈ JOURNAL|MODEL`）、`warnings[]`、`key_dates`（`signal_date, entry, exit_date, next_signal, next_entry`）、`sessions_held/left/total`。
- `plans`：`{actual, model}` 两份独立 `plan`（V2.1）。`actual` = `mode=JOURNAL`，只按成交日志：空仓则 `NO_POSITION/today_action=WAIT`（"等下一买入日"，不建议中途进场），部分买入则卖出清单只含实际持有的几只并带 `partial` 提示，现金 0 时提示先入金；`model` = `mode=MODEL`，¥20,000 影子账本假设全买。两者永不混用；顶层 `plan` = `plans.actual`（兼容）。
- `account`：`source`（`JOURNAL` 有事件 / `MODEL` 无事件）、`n_events`、`cash`、`market_value`、`equity`、`positions[]`（`symbol,name,lots,shares,avg_price,buy_date,mark_price,mark_date,cost_in,unrealized,status`）、`deposits_total`、`realized_pnl`、`month_contrib_logged`（本月是否已登记 ¥2,000 入金）。持仓 `mark_price` 每次 `ops()` 从 `live/bars/{symbol}.csv` 最后一行收盘读取，不依赖 `daily.py`。
- `model_positions[]` / `model_summary`：与 `account.positions` **同一套** `_last_close` 重估。`LEDGER_TOP20.json` 的 `mark_close` 只是上次 `daily.py` 快照，页面不得直接当最新价。缺价按成本暂记（`mark_missing`），不得当 ¥0。`model_summary` 的 `positions_mv` / `mtm_equity` / `unrealized` / `open_mark_date` 按这次重估价重算；`cash` 仍用账本现金（未平仓）。
- `history_model[]`（= `history[]`，兼容）：模型每期 `{period_no, signal_date, entry, exit, status, n_names, capital_ret, ew_ret, lo_minus_ew, net_yuan, equity, is_chain, names[]}`；未平仓期的 `names[].last_close` / `pnl` 同样用最新收盘重估。非链上的强制名单以 `is_chain=false` 标注为「非操作日预览」。
- `history_actual[]`（V2.1）：用户自己的每期，从成交日志按链上周期归组（买入 ∈ [entry, next_entry)，卖出 ∈ (entry, next_entry]）：`{period_no, signal_date, entry, exit, status ∈ OPEN|CLOSED|NOT_TRADED|PENDING_ENTRY, n_names, invested, proceeds, open_value, pnl, capital_ret, names[{symbol,name,lots,sold_lots,open_lots,avg_price,proceeds,mark_price,pnl,status}]}`。
- `journal_events[]`：最近 50 条。
- `orders_sent`：恒 `false`。

### 29.7 `POST /api/v1/paper/update`

`body` 可选 `{force: bool}`（默认 `false`；`true` 只在已有运行时返回 `TM-1005` 冲突而不是复用）。返回 `run` 结构，含 `asof_target`（最近已收盘交易日）、`skipped`、`note`、`bars_gap`。

- **截止日期**：`last_completed_session`。今天休市 → 上一开盘日（周六 9/6 → 周五 9/4）。今天开市但 18:00 前 → 仍是上一交易日。今天开市且 18:00 后 → 今天。不会用未来日期。
- **已是最新**：`STATUS.asof_session >= asof_target` 且日线文件最后一行已覆盖该日 → `skipped=true`，不 spawn。
- **补漏**：日历已齐但有票缺该日 K 线 → 启动，只拉缺口；`note` 写明补漏只数。
- **截断日历 / 2007 标签**：`STATUS.asof_session` 早于冻结日 `2026-08-28` 是被写坏的标签（killed write / 短日历），不是行情回到 2007。`freshness.asof_bogus=true`，页面不得把它当成已是最新。`daily.py` 拒绝写出早于冻结日的 STATUS。点击更新在东财不可用时走 `--skip-fetch` 用本地日线重算。
- **单实例**：同一时刻只允许一个 `ml1_live.daily`。锁文件用独占创建；pid 仍在但 cmdline 读不到时不得拆锁。发现无锁的 daily.py 视为仍在跑。东财返回「黑名单」则立刻停拉取、不再登录。
- 正在跑时页面按钮为「停止更新」（`POST /api/v1/paper/update/stop`）。日线单票超过约 40 秒无响应记 `BAR_HANG` 并跳过。
- `daily.py` 以仓库默认参数运行（V26.8 官方外壳），页面**不能**传特征/参数/持有期/资金。

### 29.8 成交日志规则

- 事件可追加、就地修改（`PUT /api/v1/paper/journal/{event_id}`）或删除；持仓与现金全部由事件推导（FIFO 按票）。填错改手数/价格/日期即可，不必删了重登。
- 本期推荐名单在部分登记后仍返回：`buy_list` = 尚未持有的名字，`logged_list` = 已登记的，`continue_register=true`。页面不得在登记第一只后把名单收掉。
- 手续费空则按 `max(5, 成交额×0.0003)` 估（买）/ `max(5, 成交额×0.0003)+成交额×0.0005 印花税`（卖）；用户填了以填的为准。
- 日志不进冻结目录，不影响 `LEDGER_TOP20.json`；只改页面的「实际账户」视图和买入手数。

### 29.9 高风险热点实验台 V1（`:9001/paper`，2026-09-10）

> **冻结：** §29.5–29.8 的 V2.1 操作台只跑在 `:9000/paper`。本小节是**另一进程**，不得改 `paper_ops.py` / `paper.html` / `JOURNAL.json` / `LEDGER_TOP20.json` / `daily.py`。不是 Candidate，不是 V26.8，未经回测。V33/V34 的证伪仍然成立；本台是用户授权的高风险试验，禁止把结果写回主线合同。

独立进程：`TRADEMIND_PORT=9001`，入口 `GET /paper` → `dashboard/paper_hot.html`。健康检查 `GET /health`（`service=trademind-hot-desk`）。**禁止**占用 9000，禁止在 `start_all.bat` 里替换主线 Master。

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/paper` | 高风险实验台页面 |
| `GET` | `/api/v1/hot/desk` | 账户 + 简报 + 参考名单 + Cursor 目录 |
| `GET` | `/api/v1/hot/symbol/{symbol}/curve` | 该股 `live/bars` 收盘；若热台持仓则附投入/浮动。不是新家族。见 §29.13 |
| `GET` | `/api/v1/hot/models` | Cursor `GET https://api.cursor.com/v1/models`（下拉，禁止手输） |
| `POST` | `/api/v1/hot/brief` | 后台启动无仓库 Cloud Agent（`repos`/`env` 都不传） |
| `GET` | `/api/v1/hot/brief/status` | 简报任务进度 |
| `POST` | `/api/v1/hot/brief/stop` | 取消当前 run |
| `GET/POST/PUT/DELETE` | `/api/v1/hot/journal` | 本台成交日志，路径 `live/paper_hot/JOURNAL.json` |

密钥：只读本机 `TRADEMIND_CURSOR_API_KEY_FILE`（默认 `D:\Cursor\APIKey.txt`）或 `TRADEMIND_CURSOR_API_KEY`。禁止入库、禁止写进日志。

`GET /api/v1/hot/desk` 的 `data`：

| 字段 | 说明 |
|------|------|
| `profile` | 恒 `HOT_V1` |
| `frozen_url` | `http://127.0.0.1:9000/paper` |
| `risk` | 恒 `HIGH` |
| `t_plus` | 普通账户股票 **T+1**（当天买的不能当天卖；所谓做T = 底仓/隔日） |
| `freshness` | 只读主线 `STATUS` / 日历（数据仍由 `:9000` 更新） |
| `account` | 只从 `paper_hot/JOURNAL.json` 推导；`positions[].sellable_today`；`util_pct`=市值/权益×100 |
| `equity_curve` | 可选。热台纸面账户点 `[{date, equity, cash, market_value, realized, unrealized, pnl, util_pct}]`。由 JOURNAL + `live/bars` 已有收盘按日盯市推导，不是新研究家族。空仓给种子点。首笔成交日前一个交易日补一粒种子快照（权益=初始、现金=初始），方便画线。`realized`=已卖出相对成本的落袋；`pnl`=权益 − 初始 − 净入金；`util_pct`=市值/权益×100（权益≤0 则为 0）。见 §29.13 |
| `brief` | 最近一次简报（可空） |
| `brief_run` | `{running, agent_id, run_id, stage, error}` |
| `cursor` | `{key_present, models[{id,label,api_id,params[]}], selected}`。`id` 是下拉值，可带变体查询串（如 `grok-4.6?effort=xhigh&fast=true` = Extra High + Fast）。API 的模型名仍是 `grok-4.6`，Extra High / Fast 是 `model.params`，不是另一个模型名。 |
| `ml1_ref` | 最近 SHORTLIST 前 10 只，**仅参考**，不是本期必须买的名单 |
| `plan` | `{headline, sub, exposure_pct, themes[], recs[], warnings[]}`，来自简报，**没有 20 日固定持有** |
| `orders_sent` | 恒 `false` |

简报 JSON（Agent `result` 必须能解析出）：`asof, exposure_pct (0–100), regime, themes[{tag,note}], names[{symbol,name,action ∈ BUY\|SELL\|HOLD\|T_BUY\|T_SELL, horizon ∈ 1-3d\|swing\|intraday, tag, reason, lots_hint}], avoid[], disclaimer`。

规则：

- 不 `order_send`。不写冻结研究目录。不改主线成交日志。
- 买卖日不由 21 日链决定；用户随时登记。T+1 由页面禁用「今天买的票今天卖」。
- Cloud Agent **禁止**带本仓库 `repos`（无仓库问答）。失败 → `TM-1002`。
- 未知模型 id → `TM-1001`。页面只准下拉。
- 简报与推荐不是历史闸门、不是 Level-1、不是承诺。

### 29.10 三本对照账 V2（`:9001/paper`，2026-09-10）

> §29.9 是 V1（联网荐股、无回测）。本小节替换页面语义，不改 `:9000` / `paper_ops.py` / `daily.py`。三本不是 Candidate。禁止用账本2 成绩改 ML1。

| 账本 | 引擎 | Grok | 调仓 | 每天记一笔 | 产物 |
|------|------|------|------|------------|------|
| 1 | 冻结 ML1 分数 + V26.8 `top_n_book` | 无 | 21 个交易日 | 收盘盯市 | `live/paper_hot/B1_LEDGER.json` |
| 2 | 账本1 候选 → 匿名 OHLC → `keep[]` | 只看价格，禁止搜网、禁止代码 | 同 V26.8 | 收盘盯市 | `B2_LEDGER.json` + `B2_ANON_LOG.json` |
| 3 | 最新 ML1 SHORTLIST 为池 | 允许联网、允许代码 | 下一开盘（纸面） | 成交日志 | `JOURNAL.json` |

`GET /api/v1/hot/desk` 增加 `profile=HOT_V2`、`books.{b1,b2,b3}`、`book1_run`、`book2_run`。`POST /api/v1/hot/brief` 只服务账本3。`POST /api/v1/hot/book2/run` 跑账本2（`limit` 从前 N 期；`tail` 从最近 N 期）；`POST /api/v1/hot/book2/stop` 停止。`POST /api/v1/hot/book1/run` 重放账本1。非前缀 resume 自动重来，避免 1 期冒烟污染全窗权益。

账本2 匿名协议：近 60 根 OHLC、首根收盘归一 100、id=`U01…`、相对日 `d=0…`。payload 禁止 `sh.`/`sz.`/`bj.`、6 位代码、中文、`YYYY-MM-DD`。Grok 只回 `{"keep":["Uxx",…]}`。验证窗 = V26.8 `VALIDATION`（2021-08-25→2024-02-29）。不读禁用窗。账本1 验证 TWR 必须与 `ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json` 同号同量级（|Δ|<0.005）。

规则：不 `order_send`。三本永不混算。账本2 即使正收益也不是 Level-1。

### 29.11 融合台 V3（`:9001/paper` 默认视图，2026-09-11）

> §29.10 三本保留为「对照账」审计账本（页面二级开关），不删、不混算。本小节是同一进程上的**一条管线**。不改 `:9000` / `paper_ops.py` / `daily.py` / ML1 / V26.8。**不是 Candidate。联网层不可回测。** 设计见 `docs/research_engine/PAPER_HOT_DESK_V3_FUSION.md`。

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/hot/fusion` | `profile=HOT_V3_FUSION`；`plan`（最近计划，含 `stale`）、`run`、`account`（融合台账，`live/bars` 收盘盯市）、`book2`（门）、`honesty[]` |
| `POST` | `/api/v1/hot/fusion/run` `{model?}` | 后台线程：组池 → Layer A → Layer B → 硬规则 → 写计划。状态 `FUSION_RUN.json`（死线程校正同 §29.9 brief） |
| `POST` | `/api/v1/hot/fusion/stop` | 取消当前 Cloud Agent run |

`GET /api/v1/hot/desk` 的 `profile` 改为 `HOT_V3`，其余字段不变（`books.b2` 增加 `n_timeout / total_expected / complete`）。

管线字段（`FUSION_PLAN_{asof}.json` = `FUSION_LAST.json`）：

| 字段 | 说明 |
|------|------|
| `profile` / `candidate` / `level1` / `promise` / `orders_sent` | 恒 `HOT_V3_FUSION` / `false` / `false` / `false` / `false` |
| `asof` / `fill_date` | 数据截至日 / 成交假设日（下一交易日开盘） |
| `pool` | `{signal_date, shortlist_file, n_shortlist, n_extended(≤30), n_pool}`；池只来自 ML1 `SHORTLIST_*.json` ∪ `SIGNAL_*.json` 前 30（主板、≤¥100） |
| `layer_a` | `{n_in, n_keep, keep_ids[], status ∈ OK\|GROK_TIMEOUT\|EMPTY_POOL\|SMOKE_STUB, leak_hits[] (必须空), skipped_no_bars[], lookback=60}`；payload 记 `FUSION_ANON_LOG.json` |
| `layer_b` | `{status ∈ OK\|GROK_TIMEOUT\|PARSE_ERROR\|…, raw_exposure_pct, confidence, n_names_raw, agent_id, run_id, duration_ms}` |
| `exposure_pct` | 硬规则后 0–100；Layer B 失败 → 0 |
| `actions[]` | `{symbol, name, action ∈ BUY\|HOLD\|SELL, lots, price_ref, est_yuan, est_fee, reason, tag, source, held, in_pool, blocked?}` |
| `dropped[]` | 被截掉的每一条 + `why ∈ BUY_OUT_OF_POOL\|NOT_MAIN_BOARD\|PRICE_OUT_OF_RANGE\|SELL_NOT_HELD\|MAX_8_NAMES\|EXPOSURE_CAP_OR_CASH\|BAD_ACTION\|DUP_OR_EMPTY\|HOLD_NOT_HELD_NOT_POOL` |
| `budget` | `{equity, cash, cap_notional=exposure×equity, held_notional, buy_budget=min(cash−200, cap−held), planned_buy_notional, est_fees, fee_pct_of_equity, post_plan_notional}` |
| `book2` | `{n_periods, total_expected=29, n_timeout, complete, note}`；`complete=false` 时页面固定显示「账本2 未读完，匿名过滤增量未知」 |
| `warnings[]` / `disclaimer` | 含「不是 Candidate」「联网层不可回测」「激进 = 换手高、费用高」 |

硬规则（`paper_fusion.enforce`，确定性）：T+1（`buy_date ≥ fill_date` 的持仓不能 SELL → HOLD + `blocked`）；BUY 只能 keep 内 + 主板 + ≤¥100；SELL 只能持仓；BUY/HOLD ≤ 8；总名义 ≤ `exposure_pct × equity`；新买 ≤ 现金 − ¥200；Grok 未提及的持仓默认 HOLD。

Layer A 匿名协议同 §29.10（60 根、首收盘 100、`U01…`、无 `sh.`/`sz.`/6 位码/日期/中文），**v1.1 起** payload = `{"protocol":"v1.1","cols":["o","h","l","c"],"series":[{"id":"U01","bars":[[o,h,l,c],…]}]}`（2 位小数、索引隐含；账本2 同用，`B2_LEDGER.anon_protocol` 记录）；价格尾部 = 冻结包（只读）+ `live/bars` 增量，**不做任何历史评估**。

对照账第四本 `books.n5`（`B_N5_LEDGER.json`，`book_n5.py`）：账本1 引擎只改 `n_target=5`，预注册、只读 VALIDATION 一次、`read_once=true` 后拒绝再跑；字段 `label ∈ HOT_N5_CONCENTRATION_{VIABLE_HISTORICAL|NOT_VIABLE}`（VIABLE iff TWR>0 且 ≥ 账本1 TWR）、`daily_maxdd`、`periods_beaten_b1/periods_compared`、`mean_excess_vs_b1`、`t_excess_vs_b1`。2026-09-11 读数 = NOT_VIABLE。不是 Candidate；主线 `n_target=10` 不变。Layer B 提示词要求每条 `reason` 写来源类型与时效，写不出来源不得 BUY。

**§29.11a 自动纸面登记（2026-09-12，用户要求"每天的建议都纸面登记模拟买卖"）。** 模块 `master/api/app/service/paper_fusion_fill.py`（仅 :9001）。
- `settle_pending()`：对每个未结算的 `FUSION_PLAN_{asof}.json`，若其 `fill_date` 在 `live/bars/{symbol}.csv` 已有开盘价，则按**该日开盘价**把 BUY/SELL 写进热台 `JOURNAL.json`（`hot.add_event(body, extra={auto, plan_id, reason, session, snapshot})`，`fee` = `paper_ops._est_fee` 同一估算器，`note = "FUSION auto {asof}"`）。`reason` 抄计划原文；`snapshot` = 当时现金/权益/持仓/asof/`fill_price`（`price_source=live_bars_open`）。先 SELL 后 BUY；T+1（当日买入手数不可卖 → `T_PLUS_ONE_LOCKED`）；现金地板（买入 ≤ 派生现金 − ¥200，手数向下取整 → 不够 `CASH_FLOOR`）；未持有 SELL → `SELL_NOT_HELD`；无该日 K 线 → `NO_BAR_AT_FILL_DATE`。计划写 `settled_at` / `fills`；审计 `FUSION_FILLS.json`（`plan_id`、`requested`、`filled`、`skipped`）。**幂等**：`settled_at` 与 `FUSION_FILLS` 双重守卫，重跑不重复登记。开关 `FUSION_SETTINGS.json.auto_fill`（默认 true；关 = 计划照出、不登记）。手工 `add_event` 同样钉 `snapshot`。
- 每日驱动 `POST /api/v1/hot/fusion/daily`（后台线程，状态 `FUSION_DAILY_RUN.json`）：(a) `settle_pending()`；(b) `paper_ops.freshness`（只读）显示 `asof_session` = 最近完成交易日且不需更新 → 跑融合管线；否则 `pipeline = SKIPPED_STALE_DATA`（不调 Grok）；该 asof 已有计划 → `SKIPPED_ALREADY_PLANNED`；融合台正在跑 → `SKIPPED_RUN_IN_PROGRESS`。`POST /api/v1/hot/fusion/settle` 只结算；`GET/POST /api/v1/hot/fusion/settings {auto_fill}`。`GET /api/v1/hot/fusion` 增 `auto_fill = {enabled, last_daily, last_settle, n_auto_events, today{n_filled,n_skipped,skipped}, skipped, pending_plans}`。
- 调度不加库：`scripts/hot_fusion_daily.bat`（curl POST，日志 `FUSION_DAILY_CRON.log`）+ Windows 任务计划 `TradeMind_HotFusionDaily` 19:30 周一至周五（用户级）。**:9000 的行情更新仍是用户的按钮，此脚本永不触发 :9000**；行情没更新就 SKIPPED_STALE_DATA。
- **自动纸面成交 = 模拟**：按下一开盘价、估算费用；没有真实下单、没有 `order_send`；不是 Candidate、不是收益承诺。

**§29.11c 实时诊股场次（2026-09-12 10:51，用户决定；2 个月观察，只 :9001）。** `POST /api/v1/hot/fusion/session {session: open|lunch|close|daily|settle, model?}` → `{success, data: 驱动状态}`；`/fusion/daily` = `session=daily`。`paper_fusion.run_pipeline(..., session=)`：`session ∈ {open,lunch,close}` 时 **不调 Layer A**（`layer_a.status=SKIPPED_LIVE_SESSION`，池不缩），一次 Grok 联网调用，snapshot 增 `session / universe / pending_plans`，计划写 `FUSION_PLAN_{date}_{session}.json` + `FUSION_LAST.json`，字段增 `session / session_label / session_date`，`actions[].kind ∈ {BUY,SELL,HOLD,ADD,REDUCE,REPLACE_OUT,REPLACE_IN}`（可带 `replace_with` / `replaces`），`counts.kinds`，`budget.sell_proceeds_net`。`enforce`：宇宙 = kept（ML1 池）∪ 持仓，其它 `OUT_OF_UNIVERSE`；ADD 须已持有（`ADD_NOT_HELD`）；REDUCE 部分卖 `lots_hint` 手（缺省一半；≥持仓即 SELL）；REPLACE 展开为 SELL 旧 + BUY 新（新买仍受池/主板/≤¥100/名义上限）；买入预算 = 现金 + 计划 SELL 净额 − ¥200。`paper_fusion_fill.run_session`：先结算；`settle` 永不调 Grok；非交易日 `SKIPPED_NOT_TRADING_DAY`；同日同场次已有计划 `SKIPPED_ALREADY_PLANNED`；`MAX_GROK_CALLS_PER_DAY=3` → `SKIPPED_CALL_BUDGET`；close/daily 行情陈旧 `SKIPPED_STALE_DATA`；既无 T+1 可卖、现金 − ¥200 又不够 1 手（`BUY_MIN_YUAN=200`）→ `SKIPPED_NO_CAPACITY`（不诊，不是策略）；open/lunch/close 允许 T-1 日线。`st.capacity = {can_act, can_sell, can_buy, cash, budget, n_sellable}`。结算：同一 `fill_date` 多份未结算计划，后出的覆盖先出的（先出的 `fills.status=SUPERSEDED`、`superseded_by`）。`FUSION_SESSIONS.json {days:{date:{session:{job_id,pipeline,note,plan,settle}}}}`（RAN 记录不被跳过覆盖）；`GET /api/v1/hot/fusion.auto_fill.sessions = {date, sessions, n_calls_today, max_calls_per_day, next, schedule, token_note}`。任务计划 `TradeMind_HotFusionOpen 09:35 / Lunch 11:30 / Close 15:05 / Daily 19:30`（一–五）调 `scripts/hot_fusion_session.bat <session>`。读取：≥24 已结算融合期或 2026-11-12 取晚者，只读一次；不是 Candidate。

**§29.11b 热台纸面账户种子（2026-09-12，用户：初始资金 ¥20,000）。** `FUSION_SETTINGS.json.initial_capital`（默认 20000，`POST /api/v1/hot/fusion/settings {initial_capital}` 可改）。`paper_hot.derive_account(journal, days)` = 种子 + 日志流水（内部只读调用 `paper_ops.derive_account`，`base_cash=种子`）；事件带 `seed: true` 的 DEPOSIT 是种子本身的证据，不再计入 `deposits_total`（2026-09-10 的 ¥20,000 DEPOSIT 已标记）。账户增 `initial_capital`、`seed_events`、`overspent`（现金为负时的超额）、`pnl_vs_initial`。所有 :9001 调用方（desk / brief / fusion / settle / journal 路由）统一走它；:9000 的 `paper_ops.derive_account` 不变。现金为负只如实显示（买入预算 0），不生成反向交易。纸面，不是 Candidate。

账本2 超时协议：`grok_keep.ask_keep` 2 次 × 420 s；失败抛 `GrokTimeout`；`book2` 记 `status=GROK_TIMEOUT, keep=None`，**不计入 TWR**，`n_timeout` 单独计数，run `stopped_reason=GROK_TIMEOUT`；续跑弹出尾部超时期重试。禁止把超时当 keep-all / keep-none。

**§29.11d 时钟分裂（2026-09-12，主人只在工作日晚上更新 :9000）。** 三套时钟必须分开：`clocks.local_asof` = 本地日线/盯市/ML1 名单（通常 T-1）；Grok 网上 = 今天的新闻/报价（不是成交价）；`fill_date` = 下一交易日开盘（`resolve_fill_date`：优先 `freshness.next_trading_day`，日历被截断则工作日往后走）。盘中/收盘诊股**不再**因为本地没有今收而 `SKIPPED_STALE_DATA`；15:05 与 09:35/11:30 一样用 T-1 + 联网。19:30 场次规则以 §29.11e 为准。提示词写明 `last_close` 不是今收。不是 Candidate。

**§29.11e 晚间必看 + 池内补仓（2026-09-13）。** 覆盖 §29.11c 里「不能买卖整日不诊 / 19:30 只结算」：
- **场次：** `open/lunch/close` 仅当 `can_act`（有 T+1 可卖 **或** 现金−¥200 够买约 1 手）才调 Grok，否则 `SKIPPED_NO_CAPACITY`。`daily`（19:30）若当日 `n_calls_today==0` **必须**看一次（`must_evening`），即使 stale / 无现金 / 全 T+1 锁死；写成当天 `close` 计划。白天已诊过且行情陈旧 → `SKIPPED_STALE_DATA`。仍 `MAX_GROK_CALLS_PER_DAY=3`。不是问句：计划按下一开盘自动记 `JOURNAL`。
- **池：** `stamp_pool` 对比上一份 `FUSION_LAST`：`pool_age ∈ {CURRENT,NEW,OLD}`，`n_new`/`n_old`/`previous_signal_date`/`pool_rotated`/`refill_rule`。`actions[]` 带 `name_source ∈ {SHORTLIST,SIGNAL_TOP30,HELD,UNKNOWN}`、`pool_age`（持仓不在池 = `HELD_OUT_OF_POOL`）。自动成交 extra 抄 `name_source`/`pool_age`/`pool_signal_date`。
- **补仓（已被 §29.11f 覆盖）：** 合适买当前池；不合适刷新 :9001 池。
- 提示词写死补仓规则。`prompt_hash` 随提示词变（新序列戳）。不是 Candidate。

**§29.11f :9001 自有池（2026-09-13，周一 asof≥2026-09-14 启用）。** `:9000` 与 `:9001` 池分开。
- 文件：`live/paper_hot/POOL.json`（`owner=hot_9001`，`writes_9000=false`）。永不写 `live/signals/SIGNAL_*.json` / `SHORTLIST_*.json`。
- 井：只读最新 ML1 `SIGNAL`（主板、≤¥100）。第一份热台池 = 当前 SHORTLIST ∪ 信号前 30 的副本，持仓不因换池被卖掉。
- 启用：`hot_pool_owned` iff `asof_session >= 2026-09-14`。此前 `status=WAIT_MONDAY`，诊股仍读共享 ML1，不刷新。
- 刷新：`cash_policy ∈ {HOLD_CASH, SELL_TO_CASH}` 且已启用且 `write=true` → `refresh_hot_pool` 取井里下一页未用过的 `HOT_POOL_PAGE=40` 只写入 POOL.json。本场不因刷新再调 Grok。每天最多 `MAX_POOL_REFRESH_PER_DAY=2`。井用尽 → `WELL_EXHAUSTED`，等 :9000 新 SIGNAL（只读）。
- 字段：`pool.owner/status/generation`，`plan.pool_refresh`，`actions[].name_source` 可取 `HOT_POOL`。
- 不是 Candidate。A 股与 MT5 仍禁止对冲、禁止拿两边数字改提示词。

**§29.12 热台 MT5 分品种 demo（2026-09-12，只 :9001，Ava Trade）。** 模块 `paper_hot_mt5.py`。报价走本机 MT5 终端（与 A 股晚上更新无关）。品种账：黄金 / 原油 / 欧美 / 美日 / 美英 / 美加 / 美瑞 各一本逻辑；美股 CFD 一个篮子**只建议不发单**（V30 成本天花板）。场次工作日 08:30 / 20:30 各 1 次 Grok（`MAX_GROK_CALLS_PER_DAY=2`），每品种每场最多 1 笔，手数默认 0.01。动作 BUY/SELL/FLAT/HOLD；`priced_in` 开仓丢弃；未知品种丢弃。`demo_send` 默认开，但 `account_mode=live` 拒绝、`TRADEMIND_MT5_SEND=0` / 冒烟不发单。日志 `live/paper_hot/MT5_JOURNAL.json`（每笔：`type, product, volume, price, bid, ask, ts, reason, session, ticket, paper, snapshot{account_mode, products[], positions[], sent}`），不写 `live/paper/JOURNAL.json`。路由 `GET /api/v1/hot/mt5`、`POST /api/v1/hot/mt5/session {session:asia|ny|settle}`、`GET/POST /api/v1/hot/mt5/settings`。任务 `TradeMind_HotMt5Asia` / `HotMt5Ny`。**不是 Candidate**；不重开 V1–V8 / V30 / V32；不下载 H1/tick 农场；不看完再训。冒烟 `tests/smoke/26_hot_mt5.py`。

`TRADEMIND_HOT_SMOKE=1` 时两层 Grok 都走本地 stub（$0）。冒烟 `tests/smoke/25_hot_fusion.py`。

**§29.31 MT5 取证审计（2026-09-13，只读）。** 不改核心代码、不重训、不调参。产物 `docs/research_engine/STRATEGY_FORENSIC_REPORT.md`、`FAILURE_ANALYSIS.md`。结论：能 `order_send` 的是 `:9001` Grok 观察台（无止损、研究分数不进提示词）；研究 D1/H1/V30/V32 不发单；V4 跟盘只展示。不是 Candidate。

**§29.30 热台黄金 V4 路径/出场诊断（2026-09-13，只读）。** `research_engine/hot_mt5_tsmom/path_exits.py`。不覆盖 `tsmom12_v4/results/READ.json`，不改 252/20，不写 `gold_follow` 规则。对象 = 已平 102 笔 `GOLD_trades.json` + 当前未平腿。路径字段：D1 高低在 `[entry, exit)`，`mfe/mae/close_mfe/giveback/mfe_day`。诊断规则事前写死（收盘判定、下一开盘出）：`BE3/BE5/TRAIL5/TRAIL10/SL10/TP10`。`candidate=false`，`not_a_book=true`，`do_not_write_into_follow=true`。产物 `GOLD_PATH_EXITS.json`、`GOLD_PATH_TRADES.json`。读法：研究窗连续 72 笔 TWR 须与 `GOLD.json` research_70 一致；不得用全样本或后 30 笔去选最好的出场。说明 `HOT_MT5_GOLD_V4_PATH_EXITS.md`。冒烟 `tests/smoke/41_hot_mt5_gold_v4_path.py`。

**§29.29 热台黄金 V4 手工跟盘（2026-09-13，只 :9001）。** 模块 `research_engine/hot_mt5_gold_follow/`。不是 Candidate，不是 live，不 `order_send`，不写 `:9000` / `daily.py` / `paper_ops.py` / `live/paper/JOURNAL.json`，**不把本状态写入 Grok 提示词**。只读冻结 V4/V5 `GOLD.json` + `GOLD_trades.json` + 最新 `history/GOLD_D1.csv`（可选只读 `h1_month_diag/GOLD_LAST_MONTH.json`），写出 `live/paper_hot/mt5_products/gold_follow/STATUS.json`。规则仍是 V4：`sign(close/close_252−1)`，下一开盘、持有 20 根 D1；V5 仓位 `min(1, 0.10/σ20d_ann)` 只作手数上限，不加杠杆。Ava 成交符号以 `GOLD_META.json` 的 `broker=GOLD` 为准（逻辑名 XAUUSD，终端常见 `GOLD`）。`candidate=false`，`deploy=false`，`feeds_grok=false`。路由 `GET /api/v1/hot/mt5/gold_follow`（刷新并返回 STATUS）；`GET /api/v1/hot/mt5` 的 `gold_follow` 只读已写 STATUS，不进 `_prompt`。禁止再训 24h sign / 把 H1 规则抄到 M15。冒烟 `tests/smoke/40_hot_mt5_gold_follow.py`。规格 `HOT_MT5_GOLD_FOLLOW_V4_SPEC.md`。
STATUS 字段：`profile, candidate, deploy, writes_9000, feeds_grok, order_send, broker_symbol, logical, stance, last_bar_sign, since_signal, since_entry, open_leg, last_bar, last_close, close_252, mom_252, entry_open, mtm_to_last_open, mtm_to_last_close, v5_weight, v5_weight_last, v5_target_ann, lookback, hold, bars_held, bars_left, planned_exit_est, h1_dump{window,mtm,maxdd,worst_ts,worst_px}, book_v4{verdict,val_twr,val_t,maxdd,research_twr,n_long,n_short}, book_v5{verdict,val_twr,val_t,maxdd}, disclaimer`。
页面（`:9001/paper` MT5 页）只展示：`stance, since_entry, last_close, v5_weight, mtm_to_last_close, disclaimer`。

**§29.28 热台黄金 H1 稀疏五列（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v9/`。同一 24h 符号问句，不是新标签。特征事前锁死五列：`R24/VOL24/DIST_SMA24/HOUR_SIN/HOUR_COS`（一天尺度 + 小时钟正余弦）。不是从 V1/V5 单列 IC 表挑赢家。拿掉 SMA200-当-8-日、`MONTH`、线性 `HOUR`、R1/R5。LightGBM 回归，超参同 `products.LGBM_PARAMS`，`sign(score)` 永远在场。Walk-forward / 成本 / 闸门同 §29.19 的 H1_ML。必须写真样本内 IC/R²/命中与约 44 折 train/test IC（协议同 §29.24）。状态窗同 §29.24，不晋升。产物 `live/paper_hot/mt5_products/gold_h1_v9/results/`。不覆盖 V1–V8 READ。`candidate=false`。冒烟 `tests/smoke/39_hot_mt5_gold_h1_v9.py`。合同 `HOT_MT5_GOLD_H1_V9_CONTRACT.md`。

**§29.27 热台黄金 H1 三障碍（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v8/`。新问句：未来 24 根谁先碰到 ±1.0×ATR14，不是 24h 收盘符号，不是 V2 ORB，不是 D1 V3。特征 = §29.23 小时钟 13 列。k=1.0 写死。LightGBM 三分类，argmax，CASH 坐一期。Walk-forward 首预测 2000 / 每 1000 重拟合 / embargo=25。成交下一开盘，障碍触达后下一开盘出或 `t+1+24` 开盘时间止。成本同 §29.19（点差+2×2bp+跨午夜 swap）。覆盖率 = Σ持有小时 / 窗口小时。闸门：验证 30%、n≥8、覆盖≥15%、TWR>0 且 t>1 → `VIABLE_HISTORICAL`，`candidate=false`。每折必须报训练集三类准确率与 `P(long)−P(short)` 对已实现符号的 IC。产物 `live/paper_hot/mt5_products/gold_h1_v8/results/`。不覆盖 V1–V7 READ。冒烟 `tests/smoke/38_hot_mt5_gold_h1_v8.py`。合同 `HOT_MT5_GOLD_H1_V8_CONTRACT.md`。

**§29.26 热台黄金 H1 场次剩余收益（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v7/`。新问句：伦敦–纽约场次剩余收益，不是 24h 符号，不是 V2 第一下突破。特征同 §29.23 小时钟 13 列，不挑 IC。标签 `y[t]=open[t_exit]/open[t+1]−1`，`t_exit`=同日第一根 `hour≥20` 且严格在 `t+1` 之后；出不了则该根空仓。只在 07–15 UTC 发信。LightGBM 回归，超参同 `products.LGBM_PARAMS`。Walk-forward：`FIRST_PRED=2000`、`REFIT=1000`、`embargo=max(20,出场根数)+1`。外壳：`|score|>1.0×ATR14/close` 才 `sign(score)`，λ=1 写死；每日最多 1 笔（第一根过门槛），下一开盘进、当日 ≥20:00 开盘出，隔夜=0，成本=点差+2×2bp。闸门：验证=合格日最后 30%，n≥8，覆盖=成交日/合格日≥15%，TWR>0 且 t>1 → `VIABLE_HISTORICAL`，`candidate=false`。必须写真样本内 IC/R²/命中与每折 train/test IC。状态窗同 §29.24，不晋升。不覆盖 V1–V6 READ。冒烟 `tests/smoke/37_hot_mt5_gold_h1_v7.py`。合同 `HOT_MT5_GOLD_H1_V7_CONTRACT.md`。

**§29.25 热台黄金 H1 Ridge 正则（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v6/`。依据 §29.24：V1/V5 真样本内 IC≈0.50、折均训练 IC≈0.60、折均测试 IC≈0.03，过拟合。本份换更简单模型，不问新问题。特征/标签/walk-forward/`sign(score)`/成本/闸门同 §29.19 的 H1_ML。模型写死：每折对训练行做均值方差标准化，再 `Ridge(alpha=1.0)`。不搜 α。产物 `live/paper_hot/mt5_products/gold_h1_v6/results/READ.json`，另写 `FOLDS.json`（每折 train/test IC）。不覆盖 V1–V5 READ。`candidate=false`。冒烟 `tests/smoke/38_hot_mt5_gold_h1_v6.py`。合同 `HOT_MT5_GOLD_H1_V6_CONTRACT.md`。

**§29.24 热台黄金 H1 真样本内 / 折外 / 状态诊断（2026-09-13，只 :9001，只读）。** `research_engine/hot_mt5_gold_h1/train_val_regime.py`。不覆盖 V1–V5 `READ.json`。回答的是「树有没有在自己的训练集上拟合过」，不是再训一版 24h `sign`。产物 `live/paper_hot/mt5_products/gold_h1_v1/results/TRAIN_VAL_REGIME.json`（V5 段可附在同一文件 `v5` 键）。字段：`true_in_sample{n, ic, r2, hit, mean_abs_score, score_min, score_max, score_std, n_unique, stuck_constant}`；`folds[]` 每折 `{fold, fit_at_i, n_train, n_test, train_ic, test_ic, train_r2, test_r2, train_hit, test_hit, score_min, score_max, score_std, n_unique, stuck_constant}`；`regimes[]` / `years[]` `{id, start, end, n_trades, twr, hit, t, buy_hold, vs_buy_hold}`；`feature_ic` 每列对 24h 标签在研究窗与各状态的 Pearson。`ic` = Pearson(pred, y)。`stuck_constant` = `score_std < 1e-12` 或 `n_unique <= 2`。状态窗事前写死：COVID `2020-02-01`–`2020-06-30`，HIKING_2022 全年，CHOP_2023 全年，GOLD_BULL `2024-05-01`–样本末。不是 Candidate。冒烟 `tests/smoke/37_hot_mt5_gold_h1_train_val.py`。

**§29.23 热台黄金 H1 小时钟特征（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v5/`。只测日线列名是否拧错。特征写死 `R1/R6/R24/VOL24/VOL120/ATR14/DIST_SMA24/DIST_SMA120/RSI14/RANGE_ATR/HOUR_SIN/HOUR_COS/DOW`。标签、`sign(score)`、成本、闸门同 §29.19 的 H1_ML。不覆盖 V1–V4 READ。冒烟 `tests/smoke/36_hot_mt5_gold_h1_v5.py`。合同 `HOT_MT5_GOLD_H1_V5_CONTRACT.md`。

**§29.22 热台黄金 H1 亚洲反向（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v4/`。新族：00–06 UTC 箱体，伦敦第一次打穿则反向，当日 ≥20:00 出。不是 V2 伦敦 ORB 反手。m=1 无树。成本/闸门同 §29.20。不覆盖 V1–V3 READ。冒烟 `tests/smoke/35_hot_mt5_gold_h1_v4.py`。合同 `HOT_MT5_GOLD_H1_V4_CONTRACT.md`。

**§29.21 热台黄金 H1 真实障碍（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v3/`。V2 伦敦 1 小时区间 99% 日触发，不是过滤。本份换更大障碍，不是反向第一下，不是改 07/20。m=2 无树当日平：`PREV_DAY_HL`（打穿上一日高低）；`LONDON_ORB_ATR05`（07:00 高低各外扩 `0.5×ATR14`）。进出同时段、成本同 §29.20。不覆盖 V1/V2 READ。冒烟 `tests/smoke/34_hot_mt5_gold_h1_v3.py`。合同 `HOT_MT5_GOLD_H1_V3_CONTRACT.md`。

**§29.20 热台黄金 H1 当日场次（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1_v2/`。V1 法医：24h 收盘方向无边、路径里有波动、永远在场在做空趋势。本份不是再训 24h 符号，不是搜 8/12/36 小时。m=2 无树：`LONDON_ORB`（07:00 UTC 那根高低为区间，当日第一次收盘突破后下一开盘进，≥20:00 开盘出）；`DONCHIAN24_SESSION`（当日 07–19 时第一次收盘突破此前 24 根高低，同样当日 ≥20:00 出）。无 07:00 或当日出不了就空仓。成本 = 点差 + 2×2bp，隔夜=0。覆盖率 = 成交日 / 有 07:00 的日。闸门同 §29.19。不覆盖 V1 `READ.json`。不拉 15/30。冒烟 `tests/smoke/33_hot_mt5_gold_h1_v2.py`。合同 `HOT_MT5_GOLD_H1_V2_CONTRACT.md`。

**§29.19 热台黄金 H1（2026-09-13，只 :9001）。** `research_engine/hot_mt5_gold_h1/`。用户执行口径 = 小时/15/30 分钟；本份只做已有 `GOLD_H1.csv`。m=2：H1 LightGBM + `sign(score)` 持有 24 根；H1 120 小时动量持有 24 根。隔夜只按跨过的自然日计。不搜 15/30。不覆盖 D1 READ。冒烟 `tests/smoke/32_hot_mt5_gold_h1.py`。合同 `HOT_MT5_GOLD_H1_V1_CONTRACT.md`。

**§29.18 热台 MT5 波动倒数仓位（2026-09-13，只 :9001）。** `research_engine/hot_mt5_voltarget/`。V4 同一 12 月符号、持有 20；仓位 = min(1, 10%/20 日年化波动)，不加杠杆。不是 V4 补丁，不是 SMA200。产物 `live/paper_hot/mt5_products/voltarget_v5/`。冒烟 `tests/smoke/31_hot_mt5_voltarget.py`。合同 `HOT_MT5_VOLTARGET_V5_CONTRACT.md`。

**§29.17 热台 MT5 十二个月 TSMOM（2026-09-13，只 :9001）。** `research_engine/hot_mt5_tsmom/`。无树。信号 = sign(收盘/252 日前收盘−1)，下一开盘、持有 20 根、同一成本。不是 SMA200，不是 CME 截面 FX3。产物 `live/paper_hot/mt5_products/tsmom12_v4/`。冒烟 `tests/smoke/30_hot_mt5_tsmom.py`。合同 `HOT_MT5_TSMOM12_V4_CONTRACT.md`。

**§29.16 热台 MT5 ATR 波动门槛三分类（2026-09-13，只 :9001）。** `research_engine/hot_mt5_atr_barrier/`。同一批 D1/特征/hold。标签门槛 = `1.0 × ATR14/close × √hold`（不是 V2 的 2×META 成本，不是法医 20bp）。其余闸门同 §29.15。产物 `live/paper_hot/mt5_products/atr_barrier_v3/`。冒烟 `tests/smoke/29_hot_mt5_atr_barrier.py`。合同 `HOT_MT5_ATR_BARRIER_V3_CONTRACT.md`。

**§29.15 热台 MT5 成本门槛三分类（2026-09-13，只 :9001）。** `research_engine/hot_mt5_cost_aware/`。同一批 V1 D1/META，不改特征/hold。标签 = 三分类：未来 hold 日收益大于 `2×META 预期往返成本` 为多，小于相反门槛为空，其余空仓。λ=2 写死，**不是** V1 法医 20bp。模型 = LightGBM 分类器，argmax；CASH 次日再看。覆盖率 = 成交数×hold/窗口交易日。验证成交&lt;8 或验证覆盖&lt;15% → 直接 `NO_CANDIDATE`；否则验证 TWR&gt;0 且 t&gt;1 → `VIABLE_HISTORICAL`，`candidate` 仍 false。产物 `live/paper_hot/mt5_products/cost_aware_v2/`，不覆盖 V1 `READ.json`。冒烟 `tests/smoke/28_hot_mt5_cost_aware.py`。合同 `HOT_MT5_COST_AWARE_V2_CONTRACT.md`。

**§29.14 热台 MT5 分品种模型（2026-09-13，只 :9001）。** `research_engine/hot_mt5_products/`。品种 = GOLD / CRUDE / EURUSD / USDJPY / GBPUSD / USDCAD / USDCHF（**不做美股**）。本机 Ava `copy_rates` 写入 `live/paper_hot/mt5_products/history/{ID}_{D1|H1}.csv` + `{ID}_META.json`。训练只用 D1；H1 只存档。每品种一份预注册 LightGBM + 持有期外壳（黄金 10 日，其余 5 日），特征只用该品种 OHLC。成交 = 下一根开盘，非重叠。成本 = 点差 + 2×2bp + swap（mode 1/5）。主报告 = 全样本 TWR；前 70% / 后 30% / 按年 / COVID_2020 / HIKING_2022 / RECENT_2024_ON 为报告或诊断，不用于选参。闸门：验证 TWR>0 且 t>1 且期数≥8 → `VIABLE_HISTORICAL`，`candidate` 仍 false。不写 `:9000`，不与 A 股对冲，不把结果写进 Grok 提示词。冒烟 `tests/smoke/27_hot_mt5_products.py`。合同 `HOT_MT5_PER_PRODUCT_CONTRACT.md`。

**§29.13 热台多页操作台（2026-09-12，只 :9001 UI）。** `dashboard/paper_hot.html` 横向多页，**只留顶栏**（今日 / 持仓 / 日程 / MT5 / 设置），不重复底栏 dock。今日页按主人标注：左上缩小账户卡 + 左侧色例；中间一张多色资金曲线；右「今天要不要动手」；下最多 4 张建议卡（理由只留一两句，点击放大看全文和该股曲线）。默认页不展示对照账、账本1/2/N5、「跑融合台」、Layer A/B、三套时钟堆砌、诚实墙。`GET /api/v1/hot/symbol/{symbol}/curve` 返回 `{symbol,name,held,series:[{date,close,invested?,pnl?}]}`，收盘来自已有 `live/bars`。设置页可调 `auto_fill`、`initial_capital`、MT5 `demo_send` / `volume`（0.01–0.10）；不改 ML1 / V26.8。`auto_fill.sessions.recent` / `sessions.recent` 为近几日场次摘要。不改 `:9000` / `daily.py` / `paper_ops.py` / ML1 / V26.8。


