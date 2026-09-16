# A_SHORT_CODE_INDEX.md

> 代码索引（只读审计）。列「路径 | 功能 | 输入 | 输出 | 依赖 | 是否进入 A-Short 运行链路」。
> 「A-Short 链路」= 是否在**目标的每日短线推荐运行时**（09:00 通知→推荐→纸面）中；`partial` = 被 `cn_a_short` 研究复用或文档指定复制的模式；`no` = 仅 ML1/hot/通用基础设施。

---

## 1. A-Short 研究包 `research_engine/cn_a_short/`（REAL，离线研究，非 live）
| 路径 | 功能 | 输入 | 输出 | 依赖 | A-Short 链路 |
|------|------|------|------|------|:---:|
| `__init__.py` | 合同常量（`A_SHORT_D1_V1`、horizons、窗口、TopK） | — | 常量 | — | partial |
| `cost.py` | 逐笔往返成本（含 ¥5 最低佣金） | notional | 成本% | `cn_a_share_alpha.cost`, `top_n_book` | partial |
| `account.py` | 可执行性/最小资金/现金 | K/价/资金 | 可行性 dict | `cost.py` | partial |
| `feasibility.py` | horizon×turnover×slippage 成本包络 | 网格 | envelope | `cost.py` | partial |
| `baseline.py` | D1 baseline 引擎 T+1..T+5 + Top-K + 撮合 + `panel_coverage` | 合规 `pack` | 评估指标 | `capital_ref.exec_reason` | partial |
| `report_tables.py` | 成本/账户表（无需 pack） | 常量 | `PHASE2A_TABLES.json` | account/feasibility | partial |
| `run_baseline.py` | empirical CLI（有 pack 才跑，否则 DATA_BLOCKED） | frozen pack | `PHASE2A2_*.json` | `cn_a_share_alpha.pack` | partial |
| `tests/*` | 合成 pack 单测（33） | 合成 | pytest | 上述 | partial |
> **关键**：`cn_a_short` **不 import** `ml1_live` / `paper_ops` / master api。唯一打分 = `baseline.momentum_scores(lookback=20)`。

## 2. 价格/数据地基 `research_engine/cn_a_share/`（REAL，V12 PIT 地基）
| 路径 | 功能 | 输入 | 输出 | A-Short 链路 |
|------|------|------|------|:---:|
| `calendar.py` | 交易日历（BaoStock） | BaoStock | calendar.csv | partial（复用） |
| `universe.py`/`universe_daily.py` | PIT 上市/退市、universe 历史 | basics | universe 历史 | partial |
| `session.py` | 单 BaoStock 会话，**只 `frequency="d"`** | — | k线 | partial |
| `bars.py`/`acquire.py`/`normalize_panel.py` | D1 抓取→`raw/daily_panel_v12_1/symbols/` | BaoStock | 逐股票 raw.csv | partial（数据源） |
| `factory.py`/`compile_v12_2.py` | 冻结参考集/编译面板+PIT 回归 | raw | 冻结数据集+manifest | partial |
| `pit.py`/`quality*.py`/`decision*.py` | 知识时间/质量/READY 门 | 面板 | 质量判定 | partial |
> **无 intraday、无信息层适配器**（都在兄弟包）。`schema.SESSION`：intraday「仅定义，稍后」。

## 3. 冻结 pack `research_engine/cn_a_share_alpha/`
| 路径 | 功能 | 输入 | 输出 | A-Short 链路 |
|------|------|------|------|:---:|
| `pack.py` | 冻结 raw CSV → (T×N) npy（**"Never call BaoStock"**） | raw.csv | `alpha_cache/*.npy`+meta | partial（cn_a_short 依赖） |
| `cost.py` | canonical 成本常量 | — | COMMISSION/SLIPPAGE/STAMP | partial |
| `paths.py` | cache 路径 | — | CACHE | partial |

## 4. 现有 live 管线 `research_engine/ml1_live/` `ml7_live/`（REAL，ML1，非 A-Short）
| 路径 | 功能 | 输出 | A-Short 链路 |
|------|------|------|:---:|
| `ml1_live/daily.py` | 9 步编排（日历/bars→pack→融资/户数/指数→14特征→打分→影子账本→SHORTLIST→ML7→STATUS） | signals/ledger/STATUS | **partial（模式复制，非接入）** |
| `ml1_live/panel.py` | 增量 D1 + 合并 live pack（冻结块逐位相同） | live/bars, live/pack | partial（数据层复用） |
| `ml1_live/layers.py` | 融资/户数/指数增量 | 特征输入 | no |
| `ml1_live/score.py`/`ledger.py`/`shortlist.py` | REFIT_240 打分/影子账本/V26.8 短名单 | LEDGER/SIGNAL/SHORTLIST | no（ML1 专有） |
| `ml7_live/*` | 32 特征信息栈影子（output-only，`affects_shortlist:False`） | LEDGER_ML7 等 | no |
> `cn_a_short` **未复用**其中任何模块（只共享 pack schema / cost / exec 规则）。

## 5. Master API `master/api/`（REAL：:9000 ML1 / :9001 hot）
| 路径 | 功能 | A-Short 链路 |
|------|------|:---:|
| `app/main.py` (:9000) / `hot_main.py` (:9001) | 两个 FastAPI app | no |
| `app/api/routes.py` | :9000 路由（/paper/ops、/paper/update→spawn daily.py、journal 等） | **partial（模式）** |
| `service/paper_ops.py`（1294 行，REAL） | Paper Ops V2：锁/进度/日历修复/21日计划/journal→账户；`start_update()` spawn `ml1_live.daily` | **partial（最强复用骨架）** |
| `service/paper_service.py` | 读 ML1 live 产物、V26.8 手数预览 | partial |
| `service/paper_fusion.py`（1214 行，REAL） | Hot Desk V3：ML1 池 + Grok Layer A/B + `enforce()` 硬规则 + `prompt_hash()` | partial（LLM 叠加模式） |
| `service/paper_fusion_fill.py` | 次开自动成交 + 会话调度 + Grok 预算（`MAX_GROK_CALLS_PER_DAY=3`） | partial（幂等/预算模式） |
| `service/cursor_cloud.py`（338 行，REAL） | Cursor Cloud **Agents** API 客户端（Grok 等） | partial（计划 LLM 层） |
| `service/ai_gateway_proxy.py` | :9000→:9100 代理 | no |
| `service/{task,worker,research,order,mt5}*` | V1.1 worker/MT5/研究 | no |
> **缺失（文档级）**：`app/ashort_main.py`、`:9002`、任何 `/api/v1/ashort/*`。

## 6. AI Gateway `ai-gateway/`（REAL，:9100，未接 A-Short）
| 路径 | 功能 | A-Short 链路 |
|------|------|:---:|
| `server.py` | FastAPI 网关（generate_report/interpret_signal/chat） | no（ML1/cn_a_short 不调用） |
| `inference.py` | 本地 Qwen2.5-14B（llama.cpp） | no |
| `providers.py` | 目录：local Qwen / DeepSeek（可用）/ Cursor（`available:false`） | partial |
| `prompts.py` | 静态模板 v3.0（**无版本字段**） | partial |
> Grok 不走网关，走 `:9001` 的 `cursor_cloud.py`。无中心化证据库、无美元预算账本。

## 7. GUI / Dashboard（REAL：仅 4 个 HTML，纯 JS）
| 路径 | 功能 | A-Short 链路 |
|------|------|:---:|
| `dashboard/paper.html` | ML1 Paper Ops V2 UI（读 /paper/ops），**网页内 toast** | partial（UX 模式） |
| `dashboard/paper_v1.html` / `paper_hot.html` / `index.html` | 旧版/hot/研究桌面 | no |
> **零** PySide6 / PyQt / `ashare-desktop` / `.tsx/.vue`；A-Short GUI 全是文档。

## 8. 通知 / Scheduler（REAL 仅 hot 的 curl+任务计划；A-Short 全文档）
| 路径 | 功能 | A-Short 链路 |
|------|------|:---:|
| `scripts/hot_fusion_session.bat` / `hot_fusion_daily.bat` | curl → :9001 fusion（Windows 任务计划手工设） | partial（模式） |
| `scripts/hot_mt5_session.bat` / `start_hot_desk.bat` | MT5/启动 | no |
> **零**：winotify/win11toast/BurntToast/QSystemTrayIcon/nssm/schtasks(代码)/`register_ashort_tasks.ps1`/`live/ashort/`/`NOTIFICATIONS.json`。

---

## 现在实际运行的链路（A-Short 不在其中）
```
dashboard/paper.html --POST /paper/update--> paper_ops.py --subprocess--> ml1_live/daily.py
   --> live/signals(SIGNAL/SHORTLIST) + live/ledger(LEDGER*) + STATUS.json  --> paper_ops ops/plan 读回
   --> (step9) ml7_live/daily.py (output-only)
cn_a_short + 计划中的 :9002/GUI/通知/scheduler = 不在此链路。
```
