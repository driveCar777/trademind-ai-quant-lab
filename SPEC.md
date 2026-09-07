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

> 本地推理模型固定为 **Qwen2.5-14B-Instruct Q4_K_M**。禁止把 GPT 系列或其它闭源 API 写成已部署模型。

Master **不负责推理**。Master 只把 AI 请求转发到独立进程 AI Gateway (`port 9100`)。

### 14.1 配置

| 项 | 来源 | 默认 |
|----|------|------|
| `ai_gateway.url` | `config` / `TRADEMIND_AI_GATEWAY_URL` | `http://127.0.0.1:9100` |
| `ai_gateway.timeout_seconds` | `config` / `TRADEMIND_AI_GATEWAY_TIMEOUT_SECONDS` | `120` |

**禁止** 在代码中硬编码 Gateway IP/端口。

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
- `account`：`source`（`JOURNAL` 有事件 / `MODEL` 无事件）、`n_events`、`cash`、`market_value`、`equity`、`positions[]`（`symbol,name,lots,shares,avg_price,buy_date,mark_price,mark_date,cost_in,unrealized,status`）、`deposits_total`、`realized_pnl`、`month_contrib_logged`（本月是否已登记 ¥2,000 入金）。
- `history_model[]`（= `history[]`，兼容）：模型每期 `{period_no, signal_date, entry, exit, status, n_names, capital_ret, ew_ret, lo_minus_ew, net_yuan, equity, is_chain, names[]}`；非链上的强制名单以 `is_chain=false` 标注为「非操作日预览」。
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


