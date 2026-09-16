# HANDOFF_ENVIRONMENT.md

> 环境冻结报告（交接用）。当前 = **Cursor Cloud VM**，一次性容器。

---

## 身份（硬事实）
| 项 | 值 |
|----|----|
| 环境 | **Cursor Cloud VM**（Linux overlay 容器） |
| 本地盘（D:） | **不存在** |
| `:9000` Master | **不存在**（仅 `master/api` 源码在仓库） |
| AGX / Jetson | **不存在** |
| 本地数据库 | **不存在** |
| 外部数据假设 | **不假设任何外部数据存在** |

## 版本
| 项 | 值 |
|----|----|
| Python | **3.12.3**（`/usr/bin/python3`） |
| numpy | 2.4.4 |
| pytest | 9.1.1 |
| baostock | **未安装** |

## 体积
| 项 | 值 |
|----|----|
| overlay 总/用 | 252G / 15G |
| repo `/workspace` | 2.1G |
| `data/` | 558M（manifest/catalog/小参考表；bulk 数据 gitignored/缺失） |
| `research_engine/cn_a_short` | 244K |

## 可用工具
- `git`、`python3` + `numpy`（+ `pytest`，本会话装过）
- `cn_a_short` 全套：`pytest`、`report_tables`（确定性）、`run_baseline`（→ DATA_BLOCKED）
- 出网可达（BaoStock 域名可连）——但**不用于重建冻结数据**（会破坏 lineage，见 `DATA_HANDOFF_STATUS.md`）

## 不可用工具 / 资源
- 冻结 A 股 D1 面板字节（~124GB，在 owner 本地 D:，不在此机）
- baostock 包（未装）；本地 :9000/AGX/DB
- 任何 A-Short live 运行时（:9002/GUI/通知/scheduler = 文档级）

## 交接含义
- **一次性 VM**：未 `git push` 的内容随 VM 销毁丢失。所有成果已在 `cursor/a-short-architecture-forensic-3072`（PR #2）。
- 路径一律以 Cloud VM `/workspace` 为准；本地恢复见 `LOCAL_RESTORE_GUIDE.md`。
