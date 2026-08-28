# TradeMind — 本地 AI 量化研究平台

> 一人开发 + AI（Cursor/ChatGPT）长期协作的本地量化研究实验室。

## 快速导航

| 文件 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | **AI 协作规则（最高法律，Cursor 必读）** |
| [PROJECT.md](PROJECT.md) | 项目介绍与愿景 |
| [TODO.md](TODO.md) | **当前任务（每天从这里开始）** |
| [ROADMAP.md](ROADMAP.md) | 开发路线 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构 |
| [DECISIONS.md](DECISIONS.md) | 架构决策记录 |
| [CHANGELOG.md](CHANGELOG.md) | 修改记录 |

## 目录结构

```
TradeMind/
├── master/          # Windows 调度中心（V1.1）
├── workers/         # Jetson 计算节点
│   └── indicator-worker/  ✅ V1.0 母版
├── sdk/             # Python 客户端
├── dashboard/       # Web 可视化
├── config/          # 统一配置
├── docker/          # Docker 编排
├── docs/            # 补充文档
├── scripts/         # 部署脚本
└── tests/           # 集成测试
```

## 当前状态

- **V1.0 Worker Template** — 已完成并冻结
- **V1.1 Master 骨架** — 进行中

## 快速开始

```bash
cd workers/indicator-worker
docker compose up --build -d
curl http://localhost:8000/health
```

## 硬件环境

| 设备 | 角色 |
|------|------|
| Windows PC | Master + MT5 + AI |
| Xavier NX ×4 | Worker 计算节点 |
| Arc A770M | LLM 推理 |

## Xavier SSH

Never put the password in the repo. Copy `.env.example` to `.env` (gitignored) or set:

```text
TRADEMIND_XAVIER_USER=dji
TRADEMIND_XAVIER_PASSWORD=...
```

Research dispatchers read only those environment variables.

## 版本管理

研究代码与非敏感产物进入 **private GitHub**。冻结合同与结果不得用 Git 改写。秘密只放环境变量。版本说明仍写在 `CHANGELOG.md`。
