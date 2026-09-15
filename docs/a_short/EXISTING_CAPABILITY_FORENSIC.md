# EXISTING_CAPABILITY_FORENSIC.md

> **问题：现有 TradeMind 有哪些能力可被 A-Short 直接复用？逐模块给结论。**
> 结论取值：`REUSE`（直接用）/ `EXTEND`（在其上扩展/复制不改原件）/ `NEW`（必须新增）/ `DEPRECATE`（不用）/ `UNKNOWN`（需进一步确认）。
> 所有结论均带文件引用。审计方法：4 个只读子代理逐包扫描 `research_engine/`、`master/api/`、`data/`、`dashboard/`、`ai-gateway/`、`docs/`。

---

## 0. 一句话总览

现有仓库是一套**成熟、PIT 纪律严格、但只有日线（D1）** 的 A 股研究+纸面运行栈。
A-Short 需要的「数据获取 / 冻结+增量 / PIT / 特征缓存 / walk-forward 建模 / 成本-撮合-账本 / 后台运行 / LLM 分析台 / 会话调度 / 纸面记账」**绝大部分已经存在**。
A-Short 主要是 **EXTEND（复制 `ml1_live`/`paper_fusion` 模式新开包）**，而非从零。
真正 `NEW` 的是：**分钟级数据、题材/龙头/龙虎榜/涨停可交易数据、新闻/政策/公告文本、桌面 GUI、Windows 通知、开机自恢复的后台服务、短周期特征与短周期基准**。

---

## 1. 数据获取 / 存储 / PIT

| 能力 | 现状文件 | 频率/覆盖 | PIT | 结论 |
|------|----------|-----------|-----|------|
| A 股日线 OHLCV 获取 | `research_engine/cn_a_share/acquire.py`, `session.py`（`BaoSession`：单登录、超时、退避、错误分类 `TRANSIENT/PERMANENT/SOURCE_LIMIT/EMPTY_HISTORY/DATA_GAP` + 黑名单检测） | D1，1990-12-19→2026-08-28，5549 股 | 是 | **REUSE** |
| 冻结数据集 + 哈希 | `research_engine/cn_a_share_alpha/__init__.py`（`DATASET_ID/DATASET_HASH`）、`pack.py`（`load_pack` 不匹配即 `PACK_DATASET_MISMATCH`）、`data/market/cn_a_share/manifests/*.json` | T×N float32 pack | 是 | **REUSE**（A-Short 另铸新 `tm-ashare-…` ID，**禁止**改 `…20260830-000002`） |
| 增量「live pack」（逐位等于冻结块） | `research_engine/ml1_live/panel.py::build_live_pack`（`live_hash` over `symbol|date|close|volume`）、`update_bars`（增量、tail-date、`BAR_HANG`） | D1 增量 | 是 | **REUSE** |
| 交易日历 | `research_engine/cn_a_share/calendar.py`、`data/.../reference/tm-cn-a-CALENDAR-*.csv`、`panel.refresh_calendar`（截断写防护、`CALENDAR_ASOF_BEFORE_FROZEN`） | 1990→2027-01 | 是 | **REUSE** |
| Universe / ST / 板块 / 退市 | `cn_a_share/universe.py`（`listed_on` PIT 成员）、`universe_daily.py`、`cn_a_share_ml_v25/top_n_book.py::BOARD_SETS`、面板内 `isST/tradestatus` | 全历史 | 是 | **REUSE**；每票每日涨停价序列 = **EXTEND**（现为按板块百分比启发式，新股首日无限制未建模） |
| 撮合可行性 / 涨跌停 | `cn_a_share_strategy_v14_1/scores.py::exec_ok_matrix`（涨跌停带内不成交）、`capital_ref.py::exec_reason`（`DELISTED/SUSPENDED/MISSING_OPEN/ZERO_VOLUME/LIMIT_LOCK/FILL`） | D1 | 是 | **REUSE** |
| 免费信息层（融资/户数/质押/增减持/预告/季报/指数成分/分红/行业） | `cn_a_share_margin_v23`、`holders_v24`、`pledge_v38`、`insider_v38`、`preann_v38`、`findeep_v27`、`index_v20`、`div_v21`、`information_v16`（各 `download.py→compile.py→features.py` + `*_PIT.json`） | D1(margin,滞后1)/周(pledge)/季/月 | 是 | **REUSE**（层本身），短周期增量价值有限 = **EXTEND** |
| PIT 强制代码 | `cn_a_share/pit.py`（`knowledge_ok/visible_financials/future_*_mutation_stable`）、各层 `compile.py` 的 `NOTICE_DATE`/lag/cutoff env | — | 是 | **REUSE**（短周期下 1 日滞后占比变大，需重估每层可用性） |
| 分钟 / 日内 / tick（A 股） | **不存在**。所有 BaoStock k 线 `frequency="d"`，所有东财 `klt=101`；`schema.py::SESSION` 仅「Defined only」 | — | — | **NEW**（需给 `BaoSession` 加分钟 k 线查询 + 新 `tm-ashare-…-M5-…` 命名空间 + 新 pack 形状） |
| 每股每日涨停价 / 连板 / 封单 | 仅面板派生的百分比 + `limit_pct_for`；无 vendor 涨停/连板/封单表（封单需 L2=缺） | — | 部分 | **EXTEND**（可从面板派生涨停计数/近高）/ 封单 = **NEW+付费** |

**关键提醒**：仓库大宗数据（raw bars、`alpha_cache/*.npy`、`live/bars|features|models`、各层 `raw/`）**均 gitignore、当前云检出里不存在**——它们在 owner 的 Windows `D:` 盘。云端做 A-Short 需在 owner 机器上跑或重新下载。

---

## 2. 研究引擎 / 特征 / 模型 / 回测

| 能力 | 现状文件 | 结论 |
|------|----------|------|
| pack 数据对象（T×N，全特征/标签/账本的唯一形状） | `cn_a_share_alpha/pack.py::load_pack` | **REUSE**（最可复用资产） |
| 前向收益标签（`hold` 为参数，1..5 直接可用） | `cn_a_share_ml_v25/model.py::forward_open_matrix`、`_label_row`（截面 rank−0.5） | **REUSE** |
| walk-forward LGBM 训练（expanding、purge/embargo、refit、研究末冻结、no-fit baseline） | `cn_a_share_ml_v25/model.py::build_scores`（`REFIT_AFTER_RESEARCH_NOT_ALLOWED_BY_CONTRACT`） | **REUSE**（`HOLD_DAYS→EMBARGO`、`TRAIN_STRIDE` 需按 hold 1–5 重新推导） |
| 活的 REFIT + 模型缓存 | `ml1_live/score.py::model_for`（`REFIT_240`，pickle 到 `live/models`） | **REUSE**（复制到 `ashort_live`） |
| 成本模型（佣金/过户/滑点/印花税 2023-08-28 切换） | `cn_a_share_alpha/cost.py`、`top_n_book.py::_fee`（¥5 最低） | **REUSE** |
| 非重叠资金账本 + 逐日盯市 + MaxDD + 现实阻塞出场 | `cn_a_share_alpha_v2/books.py::capital_book`、`capital_ref.py::simulate_capital`、`top_n_book.py::_exit_fill`（`EXIT_CARRY_MAX=10`、STUCK） | **REUSE** |
| 零售外壳（整手、按金额、补仓、月定投、TWR/CAGR/MaxDD/超额-vs-EW/t） | `cn_a_share_ml_v25/top_n_book.py`、`scale_book.py::daily_curve` | **REUSE**（选择分位 `pick_lexsort` 从模块常量读，不同分位=新 picker = 小 EXTEND） |
| 短周期事件模型骨架（hold=5、t+2..t+6 标签、EMBARGO=7、7 个事件特征、LGBMClassifier、lift） | `cn_a_share_ml_v33/run.py`（**唯一**短窗特征代码） | **EXTEND**（骨架直接抄；但 V33 判决 `NOT_TRADABLE_AT_20K`、AGENTS.md 禁止再调 V33 本体 → A-Short 必须是**新合同**） |
| 出场规则库（12 条止盈/止损/移动，`_trigger` 扫收盘） | `cn_a_share_ml_v25/exit_rules_diag.py`（V34 `EXIT_RULES_NO_IMPROVEMENT`） | **REUSE**（`_trigger` 通用；仅收盘触发，日内触碰未建模） |
| 市场状态/regime（trend/ADX/vol/location，因果视图） | `research_engine/regime/state.py`、`profit/market_state/labels.py`、`v8_fusion/states.py`（每状态须带经济句） | **REUSE 概念**（当前多为 MT5 bar-list 世界，pack-native 需小 EXTEND） |
| 暴露/择时 overlay（SMA200/vol/情绪/全球/北向）+ `apply_overlay/metrics/_roll_z` | `research_engine/v38_overlay/*` | **REUSE 工具**（O1–O5 均已读一次并 REJECT；S2 已关；A-Short overlay=新合同） |
| 方法论护栏（预注册/FDR-BH/非重叠 CAGR/禁用窗锁/holdout 拒绝/独立性 corr-vs-EW） | `research_engine/preregistration.py`、`statistics.py`、`holdout.py`、`cn_a_share_alpha/evaluate.py`、各 `contract.py` | **REUSE**（A-Short 需**新的**预声明窗口划分，且**不读** ML1 禁用窗 2024-03→2026-08） |
| 失败图谱（开新家族前必查） | `data/market/research_engine/POST_V21_AUTODRIVE/FAILURE_ATLAS.json`（90+ 行）、`post_v21_atlas_append.py`（幂等按 id） | **REUSE**（A-Short 结果按同格式追加一行） |
| 机会打分 / 候选选择 | `research_engine/opportunity/score_v2.py`（`score=mechanism×economic_reason×data_available×time_scale×cost_survival×novelty`）、`select.py`（`FORBIDDEN_TOKENS`、硬闸） | **REUSE 轴与闸** |
| 单元测试覆盖 V25+ | **无**（`tests/research_engine` 无 ml_v25/v33/ml1_live 测试） | **NEW**（A-Short 新代码必须补测试） |
| 短周期特征（1–5 日反转/跳空/隔夜-日内拆分/量额换手异动/5 日区间位置/涨停邻近/连板） | 仅 V33 的 7 个事件特征存在 | **NEW**（写进同一 T×N float32 缓存即可复用 `ranked_row` 与全部账本） |
| 短周期基准序列（1–5 日 EW/指数） | 仅 `ew_overlapping`，且 hold 与策略同 | **NEW** |
| 主题/概念/龙头/板块轮动检测 | **不存在**（`概念板块/龙虎榜/lhb/题材` 代码 = 0） | **NEW** |

---

## 3. 运行 / 服务 / 调度 / 纸面 / 配置 / GUI

| 能力 | 现状文件 | 结论 |
|------|----------|------|
| FastAPI Master（统一响应 `{success,message,code,data}`、异常处理、app 工厂 + uvicorn:9000） | `master/api/app/main.py`、`model/schemas.py`（`ApiResponse`/`ErrorCode`）、`api/routes.py` | **REUSE**（A-Short 另开 `app.ashort_main:app` 独立端口，仿 `hot_main.py`，**禁占 9000**） |
| 后台运行器（spawn `daily.py`、独占锁 `CURRENT.json`、孤儿恢复、日志 tail→阶段文案、`derive_account`、freshness 时钟） | `master/api/app/service/paper_ops.py`（1294 行） | **REUSE**（A-Short 最强现成骨架） |
| 纸面账户（journal 事件派生 cash/FIFO 持仓、费用估算、T+1、月定投提示、原子写） | `paper_ops.py::derive_account/_est_fee`、SPEC §29.5–29.8 | **REUSE 形状**；21 日链/`HOLD=20` 状态机 = **EXTEND**（短周期需按日/日内的 plan 生成器 + 真 T+1 sellable 闸，如 hot desk `_sellable`） |
| 「无调度库的调度」 | `scripts/hot_fusion_session.bat`（`open|lunch|close|daily|settle`）+ Windows 任务计划 `TradeMind_HotFusion*` → `curl POST` 幂等端点；SPEC §29.11a | **REUSE 模式**（A-Short 加 `scripts/ashort_session.bat` + 09:00 任务 → `POST /api/v1/ashort/session`；契合 AGENTS.md「不加调度库」） |
| 幂等/恢复（独占创建锁、`_find_daily_pids` 孤儿、`skipped/reused`、`_repair_live_calendar`、`asof_bogus` 拒退、每日会话账本 `FUSION_SESSIONS.json` 带 typed skip、`_now()` 可测） | `paper_ops.py`、`paper_fusion_fill.py` | **REUSE**（最强现成资产；A-Short 做 `ASHORT_SESSIONS.json`） |
| 现有 GUI | `dashboard/*.html`（web，polling，双账本切换、hero「今天做什么」状态机、toast、stage+log 面板） | **REUSE 概念**；桌面 GUI/托盘/可关窗后台/09:00 通知 = **NEW** |
| 配置（`TRADEMIND_*` 前缀、YAML+env 合并、`@lru_cache`、默认关的 kill switch） | `master/api/app/config/settings.py`、`config/*.yaml` | **REUSE 约定**；`config/ashort.yaml`（时间/通知/账本路径）= **NEW** |
| 日志/审计（`RUN_{ts}.log` + `HISTORY.json` + stage markers + `STATUS.json`） | `paper_ops.py`、`live/STATUS.json` | **REUSE**；`run_id` + 增量写 STATUS + 滚动文件日志（常驻服务）= **EXTEND/NEW** |
| worker 模板（health/ready/version/metrics） | `workers/indicator-worker/*` | **REUSE probe 面**（A-Short 常驻进程也应暴露 alive/ready） |
| Windows 服务 / 开机自启 / 任务计划注册代码 | **无**（`scripts/services/*.service` 空；仅 Xavier 有 systemd；现有任务计划是手建） | **NEW** |

---

## 4. LLM / 新闻 / 政策 / 通知

| 能力 | 现状文件 | 结论 |
|------|----------|------|
| 云 LLM 传输层（Cursor Cloud Agents，5 次重试、SSL EOF 硬化、`_adopt_created` 防重复计费） | `master/api/app/service/cursor_cloud.py`（`grok-4.6?effort=xhigh`） | **REUSE** |
| 本地/DeepSeek 网关（Qwen2.5-14B + DeepSeek chat-completions，token 统计） | `ai-gateway/*`（:9100，`providers.py`/`inference.py`/`prompts.py`） | **REUSE** |
| **已有的 LLM 分析台**（两层 Grok：匿名价格过滤 + 联网新闻/政策/板块 overlay；硬规则截断 `enforce`；`priced_in` 门；三时钟；prompt 哈希；审计块；会话调度；自动纸面记账） | `master/api/app/service/paper_fusion.py`（1214 行）、`paper_fusion_fill.py`、`paper_hot.py`；SPEC §29.9–29.12 | **EXTEND**（A-Short 的 LLM 层 ≈ 复用此台的角色/schema/截断/证据） |
| Prompt 版本 / 证据 / 计费 | `prompt_hash()`、`FUSION_ANON_LOG.json`、`FUSION_PLAN_*.json`、`agent_id/run_id`；`MAX_GROK_CALLS_PER_DAY=3` | **REUSE**（token/$ 账本、逐分析师 prompt/response 落盘 > 60 环形 = **NEW/EXTEND**） |
| 新闻采集（RSS/正文/中文 NLP） | **不存在**（`announcements/` 仅 `.gitkeep`；`feedparser/bs4/jieba/舆情/快讯` = 0） | **NEW**（且新闻在仓库是 `DATA_BLOCKED` 研究特征——见风险文档） |
| 政策（五年规划/部委/发改委/证监会） | **不存在**（`五年规划/部委/国务院/发改委` = 0；`政策` 仅出现在 `.md`） | **NEW** |
| 公告**正文**解析 | **不存在**（只有 `announcement_date` 作为数值表 PIT 门） | **NEW**（正文 = NEW；PIT 门 = REUSE `pit.py`） |
| 宏观/海外/商品/FX（可给 A 股用） | `v38_overlay/global_north.py::yahoo_closes`（`^IXIC/^DJI/^N225/^HSI`，活）；北向 `RPT_MUTUAL_DEAL_HISTORY`（**2024-08-19 后停发**）；FRED/UST 脚本 | **REUSE**（Yahoo/FRED/UST）；北向 = **DEPRECATE**（死，禁代理） |
| 主题/龙头/龙虎榜/涨停数据 | **不存在**；仅 V33 涨停模型（`NOT_TRADABLE_AT_20K`，−88%，禁调） | **NEW+付费**；触碰须正面回应 V33 判决与 scope ban |
| 通知基础设施（toast/托盘/邮件/webhook） | **完全不存在**（`win10toast/plyer/pywin32/QSystemTrayIcon/smtplib/webhook/BurntToast` 全 0） | **NEW**（好消息：GUI 用 PySide6 → `QSystemTrayIcon.showMessage()` 原生 toast 零新依赖） |
| 统一数据源注册表 | `research_engine/data_sources/registry.py` + `DATA_SOURCE_REGISTRY_V1.json`（含 `status` 枚举、`knowledge_timestamp_utc`、`BlockedAdapter`）；A 股侧 `A_SHARE_SOURCE_MATRIX_V12.json` | **EXTEND**（缺 `latency/fallback/freshness SLA`；把 A-Short 的 news/policy/LLM 源登进此表，别造第四套） |
| 机会分/市场态/候选/融合/红队 | 机会分 `opportunity/`、市场态 `regime/`+`profit/market_state/`、融合 `paper_fusion.py`+`v8_fusion/`、红队=**仅文档仪式**（`red.?team/contrarian` 代码 = 0） | 前四 **REUSE/EXTEND**；红队作为**代码** = **NEW** |

---

## 5. 汇总结论

- **REUSE（直接用，不改原件）**：pack、cost、eligibility/`exec_ok_matrix`、`forward_open_matrix`/`_label_row`、`cs_rank_row/ranked_row`、`capital_book`/`simulate_capital`/`_exit_fill`、`top_n_book` 外壳、全部信息层 `download/compile/features`、`pit.py`、FDR-BH、`holdout.py`、`v38_overlay::apply_overlay/metrics/_roll_z`、`scale_book::daily_curve`、`post_v21_atlas_append.py`、`paper_ops.py`（锁/孤儿/账户派生/freshness/原子写）、`paper_fusion.py`（角色/schema/`enforce`/`priced_in`/三时钟/prompt 哈希）、`cursor_cloud.py`、`ai-gateway`、任务计划+curl 调度模式、统一响应壳、`opportunity/score_v2.py`、`regime/state.py`。
- **EXTEND（复制 `ml1_live`/`ml7_live`/`paper_fusion` 模式新开包，原件冻结）**：`ashort_live` 每日管线（复用 `panel.py`/`layers.py`）、短 hold 的 `build_scores`、V33 事件骨架、`exit_rules_diag::_trigger`、step-9 单向 hook、`paper_ops` 的短周期 plan/T+1 闸、数据源注册表加字段、LLM 台的 A-Short 角色。
- **NEW（必须新增）**：分钟/日内数据与 pack、短周期价量特征、短周期基准、主题/龙头检测、新闻/政策/公告正文、桌面 GUI、Windows 通知、开机自恢复后台服务、`run_id`/滚动日志、红队代码、LLM token/$ 账本、A-Short 测试。
- **DEPRECATE（不用）**：北向日频（2024-08-19 死，且禁代理）；任何重开 V33/题材/涨停短线当 Candidate 的路径。
- **UNKNOWN（需确认）**：owner 机器上 `D:` 盘 bulk 数据的实际可用性与磁盘余量；BaoStock 分钟 k 线的真实历史深度与稳定性（文档称「≈1 个月」但未实测）；Cursor Cloud Agents 用于「每日 09:00 前定时分析」的延迟与配额是否够 08:20–08:58 窗口。

> 结论：**现有数据/研究/运行/LLM 基础设施足以支撑 A-Short 的"日线 + 纸面 + LLM 信息门 + 后台运行"骨架**；
> 不足集中在**分钟数据、题材/龙头/龙虎榜、新闻/政策文本、桌面通知层、开机自恢复**五处（详见数据源矩阵与风险文档）。
