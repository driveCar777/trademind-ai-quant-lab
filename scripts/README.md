# TradeMind — 部署与运维脚本

| 脚本 | 说明 | 状态 |
|------|------|------|
| `../start_all.bat` | 本机一键：Master + 通义千问 | DONE 2026-08-22 |
| `../start_xavier.bat` | 拉起 Xavier-01/02/03/04（已在线跳过） | DONE 2026-08-23 |
| `wait_local.py` | 等 :9000 / :9100 健康 | DONE |
| `lab_status.py` | 六项状态；`--check-master` / `--check-gateway` | DONE 2026-08-23 |
| `start_xavier_workers.py` | SSH 探活并启动 Worker | DONE |
| `deploy-xavier.ps1` | Windows 部署到 Xavier | 待整理 |

## 规则

- 脚本只做部署/运维，不含业务逻辑
- 一键启动不重复占用已监听的端口
- 不改冻结 Worker 代码；端口以板上实际监听为准
