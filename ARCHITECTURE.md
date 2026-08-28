# TradeMind — 系统架构

---

## 总体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Windows Master                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Scheduler │ │   API    │ │Dashboard │ │AI Gateway│ │
│  └────┬─────┘ └────┬─────┘ └──────────┘ └──────────┘ │
│       │            │                                     │
│  ┌────▼─────┐ ┌────▼─────┐ ┌──────────┐ ┌──────────┐  │
│  │Dispatcher│ │ Database │ │ Collector│ │  Result  │  │
│  └────┬─────┘ └──────────┘ └──────────┘ │  Center  │  │
│       │                                  └──────────┘  │
└───────┼─────────────────────────────────────────────────┘
        │ REST
        ▼
┌─────────────────────────────────────────────────────────┐
│              Jetson Xavier Cluster (×4)                  │
│  ┌────────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │indicator-worker│ │factor-worker │ │backtest-worker│ │
│  │     ✅ V1.0    │ │   🔜 V2.0   │ │   🔜 V2.1   │  │
│  └────────────────┘ └──────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 数据流

```
Task Scheduler
    ↓
REST POST /task
    ↓
Indicator Worker (Xavier)
    ↓
JSON POST /result
    ↓
Master → Database → Dashboard
```

---

## 目录结构

```
TradeMind/
├── AGENTS.md              # AI 协作规则（最高法律）
├── PROJECT.md             # 项目介绍
├── TODO.md                # 当前任务
├── ROADMAP.md             # 开发路线
├── ARCHITECTURE.md        # 本文件
├── CHANGELOG.md           # 修改记录
├── DECISIONS.md           # 架构决策
├── README.md              # 项目入口
│
├── master/                # Windows 调度中心
│   ├── api/               # REST API
│   ├── scheduler/         # 任务调度
│   ├── dispatcher/        # 任务分发
│   ├── collector/         # 结果采集
│   ├── database/          # 数据持久化
│   ├── result-center/     # 结果汇总
│   └── ai-gateway/        # AI 推理网关
│
├── workers/               # Jetson 计算节点
│   ├── indicator-worker/  # ✅ V1.0 模板
│   ├── factor-worker/     # 🔜 V2.0
│   └── backtest-worker/   # 🔜 V2.1
│
├── sdk/                   # Python 客户端
│   └── trademind_client/
│
├── dashboard/             # Web 可视化
├── docs/                  # 补充文档
├── docker/                # Docker 编排
├── config/                # 统一配置
├── scripts/               # 部署脚本
└── tests/                 # 集成测试
```

---

## 通信协议

| 方向 | 协议 | 说明 |
|------|------|------|
| Master → Worker | REST | `POST /api/v1/{service}/{action}` |
| Worker → Master | REST | `POST /result` |
| 监控 | Prometheus | `/metrics` |
| 健康检查 | REST | `/health`、`/ready` |

**不使用消息队列（RabbitMQ / Kafka）。**

---

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| Worker | Python + FastAPI | 3.8 / 0.83.x |
| Master | Python + FastAPI | 3.8+ |
| 容器 | Docker + Compose | 当前版本 |
| 计算节点 | Jetson Xavier NX | JetPack 当前版本 |
| AI | Arc A770M LLM | Master 端 |
| 交易 | MetaTrader 5 | Windows |

---

## 设计原则

1. **Master 调度，Worker 计算** — 职责严格分离
2. **REST 通信** — 简单、可调试、无中间件
3. **模板复用** — 新 Worker 复制 indicator-worker
4. **配置统一** — 全部 `TRADEMIND_*` 前缀
5. **本地优先** — 数据、模型、计算全部本地化
