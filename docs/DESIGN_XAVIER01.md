# Phase 1 Design — Xavier-01 纳入四台启动

> **模块：** 运维补强（不是 V4）  
> **日期：** 2026-08-23  
> **状态：** Phase 3 Smoke 08 PASS（2026-08-23）。Phase 4/5 本轮不做。

## 0. 先回答：是不是少用一台？

**不是。** 集群始终是 4 台，当前阶段四台都参与计算。

| 板 | 角色 | 日常算不算 | 一键脚本以前为什么跳过 |
|----|------|------------|------------------------|
| Xavier-01 `192.168.1.200:8080` | 指标 (RSI/MACD) | **算。** 「现在就计算」默认就找它 | 部署是 **Docker**，当时已在线，怕误重启容器 |
| Xavier-02 `:8080` | A 股因子 | 算 | 无，`server.py` |
| Xavier-03 `:8002` | 回测 | 算 | 无，`server.py`（口是 8002） |
| Xavier-04 `:8080` | 监控 | 算 | 无，`server.py` |

跳过 01 是启动策略，不是「这台不属于本阶段」。

## 1. 本轮只解决一件事

桌面一键 / `start_xavier.bat` **四台同等对待**：

- 健康 → 跳过（不重启）
- 不健康 → 01 走 Docker 启动；02/03/04 走现有 `nohup python3 server.py`
- 网页「启动 / 重启」01 已走 `--id worker-01`，本轮把 Docker 选箱做稳

## 2. Xavier-01 启动规则

| 项 | 决定 |
|----|------|
| 探活 | 板上 `curl :8080/health`，再加 Windows 侧探活 |
| 已在线且非 `--restart` | 打印 `ALREADY_UP`，不碰容器 |
| 离线启动 | `docker start <固定名>`（容器在、只是停了） |
| `--restart` | `docker restart <固定名>` |
| 选箱 | **只认固定名单**，禁止「`docker ps` 第一行就重启」 |

固定名单（按顺序，命中第一个存在的）：

1. `indicator-worker-01`（仓库 compose 写名）
2. `trademind-indicator-worker`
3. `trademind-indicator`

若名单都不在、但有容器映射 **8080**，才用该箱。再没有 → 失败 `TM-1003`，不猜。

板上 compose 默认映射常是 `8000:8000`；**对外 FACT 以 Master `data/workers.json` 为准：`:8080`**。脚本只探 8080，不改板上 `server.py` / 不改 Worker 计算代码。

## 3. 不做

- 不停 01 做破坏性重启冒烟（会打断默认 RSI）
- 不网页一键重启全实验室
- 不重启通义千问
- 不开始 V4
- 不新增错误码、不新增 ops 字段

## 4. 五阶段

| Phase | 内容 | 本轮 |
|-------|------|------|
| 1 Design | 本文 + SPEC §15.4 + Decision 020 | 本文件 |
| 2 Implement | 去掉默认 SKIP 01；固定容器名；文案改「四台」 | 设计确认后 |
| 3 Smoke | 01 已在线则 `ALREADY_UP`；Windows 探活 `:8080` | 不停容器 |
| 4 Stability | 不在本轮（不停 01 连重启） | 不做 |
| 5 Freeze | 不在本轮 | 不做 |

## 5. 冒烟标准（Phase 3）

1. `GET http://192.168.1.200:8080/health` 能通，或明确记 OFFLINE。  
2. `POST /api/v1/ops/worker/worker-01/start`：已在线则提示不重复启动。  
3. `start_xavier_workers.py` 默认批次**不再打印** `SKIP Xavier-01`。
