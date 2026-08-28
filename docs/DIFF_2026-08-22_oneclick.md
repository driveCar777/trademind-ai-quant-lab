# DIFF — 2026-08-22 一键启动 + 拉起 Xavier-02/03/04

> 本项目不使用 Git。此文件是本轮改动对照。

## 做了什么

1. 本机一键启动 Master(:9000) + 通义千问 SYCL 网关(:9100)，已占用端口不重复开。
2. 冒烟 `tests/smoke/05_oneclick.py`：Master / Gateway / Master 代理 AI 均 PASS。
3. SSH 拉起 Xavier-02/03/04 上已部署的 `server.py`。不动 Xavier-01。
4. 回测 Worker 实际监听 **8002**（冻结代码里写死），Master `data/workers.json` 从 8080 改成 8002。

## 实测 (FACT)

| 项 | 结果 |
|----|------|
| `start_all.bat` | `LOCAL_START_PASS` |
| `05_oneclick.py` | `SMOKE_05_PASS` |
| Xavier-02 `192.168.1.201:8080` | ONLINE，factor-worker 2.0.0 |
| Xavier-03 `192.168.1.202:8002` | ONLINE，backtest-worker 2.1.0 |
| Xavier-04 `192.168.1.203:8080` | ONLINE，monitor-worker 1.0.0 |
| `POST /task` factor / monitor / backtest | 三笔 COMPLETED（000003 / 000004 / 000005） |

## 文件对照

| 动作 | 路径 | 说明 |
|------|------|------|
| 新增 | `start_lab.bat` | 合成：本机 + Xavier-02/03/04 |
| 新增 | 桌面 `TradeMind-Lab.lnk` | 指向 `start_lab.bat` |
| 新增 | `docs/DESIGN_OPS_RESTART.md` | 网页启动/重启 Phase 1（未实现） |
| 新增 | `start_all.bat` | 本机一键启动入口 |
| 新增 | `start_xavier.bat` | 只拉 02/03/04 |
| 新增 | `scripts/wait_local.py` | 等 Master + 模型加载 |
| 新增 | `scripts/start_xavier_workers.py` | SSH 探活/拉起 |
| 新增 | `tests/smoke/05_oneclick.py` | 本机冒烟 |
| 新增 | `docs/DIFF_2026-08-22_oneclick.md` | 本对照 |
| 修改 | `data/workers.json` | worker-03 `port` 8080 → **8002** |
| 修改 | `scripts/README.md` | 运维入口说明 |
| 修改 | `docs/CHANGELOG.md` | 本轮记录 |
| 修改 | `docs/TODO.md` | 运维任务记录 |
| 修改 | `docs/TEST_PLAN.md` | Smoke 05 |
| 修改 | `docs/TRADEMIND_CONTEXT.md` | 运行事实 |
| 修改 | `PROJECT_STATUS.md` | 当前状态 |

## 未改（有意）

- 四个 Worker 的 `server.py`（已冻结）
- Master 调度逻辑
- V4 Research Agent（未开始）

## 以后怎么开

```
D:\AGXXAIVER-4-WINDOWS-1-STOCK\start_all.bat
D:\AGXXAIVER-4-WINDOWS-1-STOCK\start_xavier.bat
```

SSH 账号默认与现有部署脚本相同；可用环境变量覆盖：`TRADEMIND_XAVIER_USER`、`TRADEMIND_XAVIER_PASSWORD`。
