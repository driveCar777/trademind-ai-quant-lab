# Master — Windows 调度中心

TradeMind 中央调度节点，运行在 Windows PC。

## 模块

| 模块 | 职责 | 状态 |
|------|------|------|
| `api/` | REST API 入口 | 骨架 |
| `scheduler/` | 任务调度 | 骨架 |
| `dispatcher/` | 任务分发到 Worker | 骨架 |
| `collector/` | 结果采集 | 骨架 |
| `database/` | 数据持久化 | 骨架 |
| `result-center/` | 结果汇总 | 骨架 |
| `ai-gateway/` | AI 推理网关 | 骨架 |

## 设计原则

- Master **只调度，不计算**
- LLM 推理只在 Master 运行
- 通过 REST 与 Worker 通信

## 相关

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [ROADMAP.md](../ROADMAP.md) — V1.1
