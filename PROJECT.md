# TradeMind — 本地 AI 量化研究平台

## 一句话

TradeMind 是一个运行在本地集群上的 AI 驱动量化研究与投资实验室。

## 愿景

构建一套**完全本地化**的量化研究基础设施，整合 A 股数据、MT5 外汇、AI 模型与 Jetson 计算集群。

## 核心目标

| 目标 | 说明 |
|------|------|
| A 股 | 本地 A 股数据接入与研究 |
| MT5 | MetaTrader 5 外汇/期货实盘与回测 |
| AI | 本地 LLM 驱动的研究 Agent |
| Docker | 所有服务容器化，一键部署 |
| Jetson Cluster | 4× Xavier NX 分布式计算 |
| Windows Master | 中央调度、数据汇总、Dashboard |

## 系统组成

```
Windows Master（调度中心）
    ├── Task Scheduler / REST API / Dashboard / Database / AI Gateway
    ↓ REST
Jetson Workers（计算节点）
    ├── indicator-worker  ✅ V1.0
    ├── factor-worker     🔜 V2.0
    └── backtest-worker   🔜 V2.1
```

## 设计原则

1. 简单优先 — REST 通信，不用消息队列
2. 模板复用 — 所有 Worker 复制同一模板
3. Master 调度 — Worker 只计算，Master 只调度
4. 本地优先 — 数据、模型、计算全部本地化
5. AI 协作 — 一人 + Cursor/ChatGPT 长期维护

## 硬件环境

| 设备 | 角色 |
|------|------|
| Windows PC | Master + MT5 + AI |
| Xavier NX ×4 | Worker 计算节点 |
| Arc A770M | LLM 推理（Master） |

## 当前状态

- V1.0 Worker Template — 已完成并冻结
- V1.1 Master — 下一步

## 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [TODO.md](TODO.md)
- [DECISIONS.md](DECISIONS.md)
