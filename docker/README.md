# Docker — 容器编排

TradeMind 全局 Docker 配置与编排模板。

## 结构

```
docker/
├── README.md           # 本文件
├── docker-compose.master.yml   # Master 编排（V1.1）
└── docker-compose.workers.yml  # Workers 编排模板
```

## 规则

- Worker 各自维护 `workers/{name}/docker-compose.yml`
- 全局编排放在本目录
- **禁止升级 Docker 版本**（见 DECISIONS.md Decision 008）

## 相关

- [workers/indicator-worker/](../workers/indicator-worker/) — Worker 母版
