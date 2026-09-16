# ENVIRONMENT_REPORT.md

> Cloud→Local 交接前的环境身份确认。**当前环境 = Cursor Cloud VM**（一次性容器），不是 owner 本地机。

---

## 1. 环境身份（硬事实）
| 项 | 值 |
|----|----|
| 环境 | **Cursor Cloud VM**（Linux overlay 容器） |
| 是否本地 Windows | **否** |
| `:9000` master | **不存在**（未运行；仅 `master/api` 代码在仓库里） |
| AGX / Jetson worker | **不存在** |
| 本地 D: 数据盘 | **不存在**（冻结行情库在 owner 本地 D:，不在此机） |
| 路径基准 | 一律以 Cloud VM `/workspace` 为准 |

## 2. Git
```
repo   : github.com/driveCar777/trademind-ai-quant-lab
branch : cursor/a-short-architecture-forensic-3072
HEAD   : 9b85f065c19a859bdccfa09f9745e9861bd788ac
```
（远程 URL 含临时访问 token，本文件不记录 token；本地 clone 用你自己的凭据。）

## 3. Python / 依赖
| 项 | 值 |
|----|----|
| Python | **3.12.3**（`/usr/bin/python3`） |
| numpy | 2.4.4 |
| pytest | 9.1.1 |
| baostock | **未安装**（数据采集用；A-Short 测试/报表不需要） |
| cn_a_short 运行依赖 | 仅 `numpy`（+ `pytest` 跑测试）；无 `requirements.txt`（极简） |

> 注意：仓库其它模块（master/api、ai-gateway、worker）有各自较重的依赖；A-Short（`cn_a_short`）**只依赖 numpy**。

## 4. 磁盘
| 项 | 值 |
|----|----|
| overlay 总/用 | 252G / 15G（6%） |
| repo `/workspace` | 2.1G |
| `data/` | 558M（多为 manifest/catalog/小参考表；bulk 数据 gitignored/缺失） |
| `research_engine/cn_a_short` | 244K |

## 5. 关键环境结论
- **冻结 A 股 D1 面板字节不在本机**（Phase 2A.3：`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`）→ 无法在 Cloud 跑 empirical alpha。
- A-Short 代码在 Cloud **可测、可生成成本/账户报表**（`pytest` 33 通过；`report_tables` 确定性），但 **empirical baseline = DATA_BLOCKED**。
- 本 VM 是一次性的：**所有成果须通过 git 交接**；未提交内容随 VM 销毁丢失（见 `A_SHORT_LOCAL_HANDOFF.md`）。
