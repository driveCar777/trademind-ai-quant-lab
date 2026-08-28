# Workers — Jetson 计算节点

所有 Worker 运行在 Jetson Xavier NX 集群，通过 REST 与 Master 通信。

## 当前 Worker

| Worker | 版本 | 状态 |
|--------|------|------|
| `indicator-worker/` | V1.0 | ✅ 已完成（母版） |
| `factor-worker/` | V2.0 | 骨架占位 |
| `backtest-worker/` | V2.1 | 骨架占位 |
| `monitor-agent/` | — | 骨架占位 |
| `task-agent/` | — | 骨架占位 |

## 新建 Worker 规则

1. **复制** `indicator-worker/` 整个目录
2. 修改业务逻辑（`app/core/`、`app/service/`）
3. 修改 API 路径（如 `/api/v1/factor/calculate`）
4. **禁止**修改公共接口（`/health`、`/ready`、`/version`、`/metrics`）
5. **禁止**重新设计目录结构

## 公共接口（所有 Worker 必须实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/ready` | 就绪探针 |
| GET | `/version` | 版本信息 |
| GET | `/metrics` | Prometheus |
| GET | `/docs` | OpenAPI Swagger |
| GET | `/redoc` | OpenAPI ReDoc |

## 相关

- [AGENTS.md](../AGENTS.md) — Worker 规则
- [DECISIONS.md](../DECISIONS.md) — Decision 006
