# CLOUD_CODE_MAP.md

> 代码地图（Cloud checkout 视角）。状态：**当前**=A-Short 已实现并在用；**可用**=通用/相邻可复用；**未接**=存在但未接入 A-Short；**缺失**=无代码。
> 详细逐文件索引见 `forensic/A_SHORT_CODE_INDEX.md`。

## A-Short 核心（本阶段成果）
| 模块 | 作用 | 状态 |
|------|------|------|
| `research_engine/cn_a_short` | A 股短周期研究引擎（离线） | **当前** |
| `cn_a_short/cost.py` | 成本模型（逐笔，min¥5） | 可用 |
| `cn_a_short/account.py` | 资金/可执行性约束（fee-aware，无负现金） | 可用 |
| `cn_a_short/baseline.py` | baseline 回测（T+1..T+5、Top-K、撮合、panel_coverage） | 可用 |
| `cn_a_short/feasibility.py` | 换手×滑点 成本包络 | 可用 |
| `cn_a_short/report_tables.py` | 成本/账户表（无需 pack） | 可用 |
| `cn_a_short/run_baseline.py` | empirical CLI（有 pack 才跑；否则 DATA_BLOCKED） | 可用（数据受限） |
| `cn_a_short/tests/` | 33 单测（合成 pack） | 可用（全绿） |

## 依赖的既有资产（复用，未改）
| 模块 | 作用 | 状态 |
|------|------|------|
| `research_engine/cn_a_share_alpha/pack.py` | 冻结 raw→npy pack | 可用（需字节，Cloud 缺） |
| `research_engine/cn_a_share_alpha/cost.py` | canonical 成本常量 | 可用（复用） |
| `research_engine/cn_a_share_strategy_v14_1/capital_ref.py` | `exec_reason`（停牌/涨跌停/T+1） | 可用（复用） |
| `research_engine/cn_a_share_ml_v25/top_n_book.py` | `LOT/MIN_FEE/_fee/board_mask` | 可用（复用） |
| `research_engine/cn_a_share/*` | V12 PIT 地基（日历/universe/D1 采集） | 可用（数据源，字节缺） |

## 目标需要但未接 / 缺失
| 模块 | 作用 | 状态 |
|------|------|------|
| 信息层包（margin/holders/financial/industry/index/preann/insider/pledge/div/macro） | 结构化信息层下载+编译 | **未接**（且 Cloud manifest-only） |
| `research_engine/ml1_live` / `ml7_live` | ML1/ML7 live 管线 | **未接**（cn_a_short 不 import） |
| `master/api`（:9000/:9001，paper_ops/paper_fusion/cursor_cloud） | 服务/纸面/LLM 传输 | **未接**（A-Short 无 :9002） |
| `ai-gateway`（:9100，Qwen/DeepSeek） | LLM 网关 | **未接** |
| `dashboard/*.html` | 4 个 HTML（ML1/hot） | **未接**（无 A-Short 页面） |
| LLM 融合（新闻/政策/红队/决策支持） | — | **未接** |
| GUI（PySide6/桌面） | — | **缺失**（文档级） |
| 通知（OS toast/winotify/scheduler/:9002） | — | **缺失**（文档级） |
| 龙虎榜 / 个股资金流 / 新闻政策文本 / 分钟数据 | — | **缺失**（全仓无代码） |
| 涨停/连板 / 热点 / 板块轮动 / 龙头 | — | **缺失**（V33 limit_up 独立冻结，不属 A-Short） |

## 一句话
A-Short 代码地图 = **一个成熟的离线短周期引擎（成本/账户/撮合/评估/测试）+ 20D 动量占位打分**，其余目标能力要么"存在但未接入"，要么"完全缺失"。
