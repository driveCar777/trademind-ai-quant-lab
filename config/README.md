# TradeMind — 统一配置

所有服务的环境变量与配置文件。

## 环境变量前缀

全部使用 `TRADEMIND_*`（见 DECISIONS.md Decision 007）。

## 配置文件

| 文件 | 说明 |
|------|------|
| `default.yaml` | 全局默认配置 |
| `master.yaml` | Master 专用配置 |
| `workers.yaml` | Worker 集群配置 |
| `data_sources.yaml` | Data Layer V0.1（只读 MT5 行情；不接 V11.7） |

## 规则

- **禁止**在代码中硬编码 IP、端口、密钥
- 敏感信息放在 `.env`（不提交到文档）
