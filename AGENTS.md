# TradeMind AI Quant Lab — AI 协作规则

> **最高法律。** Cursor / ChatGPT 每次打开本项目，必须先阅读本文件。

---

## 核心原则

> **一次只解决一个问题，一次只完成一个模块；没有通过冒烟测试，不开始下一模块；没有冻结，不重构整体。**

---

## 接力开发入口（必读顺序）

任何 AI 接手项目，**必须**按此顺序阅读：

1. **`docs/TRADEMIND_CONTEXT.md`**（最高优先级，防幻觉版上下文）
2. `AGENTS.md`（本文件，AI 协作规则）
3. `docs/TODO.md`（当前任务）
4. `docs/PROJECT_VISION.md`（项目愿景，仅供参考，不是事实）

**禁止依赖聊天上下文。** 所有决策以 `TRADEMIND_CONTEXT.md` 为准。

**冲突规则：** 任何与 `TRADEMIND_CONTEXT.md` 冲突的信息，以 `TRADEMIND_CONTEXT.md` 为准。

---

## 铁律：字段必须先查 SPEC

> **任何新增字段，必须先查 `SPEC.md`。未定义 → 先更新 SPEC → 再写代码。**

---

## 模块开发五阶段（铁律）

任何模块（Master、Worker、SDK、Dashboard……）**必须**经过以下五个阶段：

```
Phase 1  Design          设计
Phase 2  Implement       实现
Phase 3  Smoke Test      冒烟测试
Phase 4  Stability Test  稳定性测试
Phase 5  Freeze          冻结
```

**只有 Freeze 以后，才能开始下一个模块。**

进度追踪见 `TODO.md`，测试标准见 `TEST_PLAN.md`，项目状态见 `PROJECT_STATUS.md`。

---

## V1.1 Implement 八阶段（当前）

```
Phase 1  文档同步        ← PASS
Phase 2  Master 代码对齐
Phase 3  Worker 配置对齐
Phase 4  Smoke Test
Phase 5  Xavier 部署
Phase 6  端到端验证
Phase 7  稳定性测试
Phase 8  Freeze 文档更新
```

每完成一个 Phase，**必须**：
1. 输出 Phase 报告（状态 / 交付物 / 遗留问题）
2. 更新 `PROJECT_STATUS.md`
3. 停止，等待确认后再进入下一 Phase

---

## 项目定位

TradeMind 是**一人开发 + AI 长期协作**的本地 AI 量化研究平台。  
不是练手项目，而是可长期维护的软件产品。

---

## 开发规则（必须遵守）

### 1. Worker 规则

- 任何新 Worker **必须复制** `workers/indicator-worker` 模板
- **禁止**重新设计 Worker 目录结构
- **禁止**修改 Worker 公共接口（`/health`、`/ready`、`/version`、`/metrics`）
- Worker **永远负责计算**，不负责调度
- Worker **不知道 Master**（禁止 `master_host` / `master_port`）
- Worker 类型统一为 `indicator-worker`（非 `indicator`）

### 2. API 规则

- 计算类接口格式：`POST /api/v1/{service}/{action}`
- Master 业务接口统一响应格式：`{success, message, code, data}`（见 SPEC.md）
- 探针例外：`GET /health`、`GET /ready` 可保留轻量字段
- **禁止**引入 RabbitMQ、Kafka 等消息队列（见 DECISIONS.md）

### 3. 配置规则

- 所有环境变量统一前缀：`TRADEMIND_*`
- 配置文件放在 `config/` 目录（`master.yaml`、`worker.yaml`）
- **禁止**在代码中硬编码 IP、端口、密钥

### 4. 技术栈冻结（禁止升级）

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.8 | Xavier 兼容 |
| Docker | 当前版本 | 不升级 |
| JetPack | 当前版本 | 不升级 |
| FastAPI | 0.83.x | Worker 模板锁定 |

### 5. 目录规则

- **禁止**在根目录随意新建服务目录
- 新服务必须放在规定目录下（见 ARCHITECTURE.md）
- 每个目录必须有 `README.md`

### 6. Master 规则

- Master **永远运行在 Windows**
- Master **永远负责调度**，不负责计算
- LLM / AI 推理**只在 Master 运行**（Jetson 性能有限）
- V1.1 **只开发** `master/api/`，其它 Master 子目录保持空
- V1.1 唯一职责：`接收任务 → 找到 Worker → 调用 Worker → 保存结果`

### 7. 文档规则

- 重大架构决策写入 `DECISIONS.md`
- 每次完成功能更新 `CHANGELOG.md`
- 当前任务与五阶段进度写在 `TODO.md`
- 技术规范写在 `SPEC.md`
- 项目状态写在 `PROJECT_STATUS.md`
- 测试标准写在 `TEST_PLAN.md`
- 开发路线只写在 `ROADMAP.md`

### 8. 代码规则

- 优先编辑现有文件，不随意新建
- Worker Docker-only 部署；Master V1.1 可在 Windows 直接运行
- 冒烟测试放在 `tests/smoke/`（01_worker / 02_master / 03_master_worker）
- 模块单元测试放在各模块 `tests/`

### 9. AI 协作规则

- 开始任务前：读 `AGENTS.md` → `SPEC.md` → `PROJECT_STATUS.md` → `TODO.md`
- 完成任务后：更新 `PROJECT_STATUS.md`、`TODO.md`、`CHANGELOG.md`、`TEST_PLAN.md`
- **禁止**在未授权时开发 ROADMAP 中未到达的版本功能
- **禁止**同时推进多个模块
- **禁止**冒烟测试未通过就开始下一模块
- **禁止**新增架构设计或扩展 V1.2/V2 功能

### 10. 版本管理

- 研究代码与非敏感产物进入 **private GitHub**。禁止提交密码、token、`.env`。
- **禁止** `git reset --hard` / `git push --force` / 用 Git 回滚研究事实。
- 冻结合同与结果仍以文件 + `CHANGELOG.md` 为准，不得改写历史 evidence。

---

## V1.1 第一版禁止清单

以下在 V1.1 **全部禁止**：

| 类别 | 禁止 |
|------|------|
| 模块 | Scheduler、Dispatcher、Database 模块、Dashboard、SDK |
| 中间件 | RabbitMQ、Redis、消息队列 |
| 数据库 | SQLite、PostgreSQL、MySQL |
| 调度 | Cron、APScheduler、Timer、任务排队、线程池 |
| 前端 | Vue、React、Electron、Qt、WebSocket |
| 功能 | 自动重试、负载均衡、Worker 选择策略、超时恢复 |

V1.1 唯一目标：

```
POST /task → requests.post() → indicator-worker → RSI → 保存结果 → GET /task/{id}
```

存储：`storage/tasks/`（元数据）+ `storage/results/YYYY/MM/DD/`（结果分离）

---

## 当前阶段

**V1.0 — V11.0** ✅ 已冻结  
**Data Layer V0.1 / Qualification V0.1 / Readiness V0.2 / Research Protocol V0.3** ✅ 已冻结  
**Factor Discovery V0.1** ✅ 已冻结（`NO_USEFUL_FACTORS_FOUND`；不是策略；不是年化 10%）  
**Research Engine V0.5** ✅ 地基（`NO_USEFUL_STRATEGIES_FOUND`）  
**Profit Discovery V0.6** ✅ 已冻结（四 Xavier；`WEAK_EDGE_ONLY`；程序级 CANDIDATE=0；不是年化 10%）  
**Alpha Discovery V0.7** ✅ 仅设计（无代码；下一方向=跨品种 D1；不要再加简单策略）  
**Alpha OS V0.7.1** ✅ 仅设计（分类/矩阵/12 个月队列）  
**Cross Asset V0.8** ✅ 已冻结（四 Xavier；`NO_CANDIDATE`；3/3 FALSIFIED；FDR 0/3；不是年化 10%）  
**Alpha Map V1** ✅ 仅设计（覆盖/数据/排序/12M；Carry/IV/新闻 = BLOCKED）  
**Regime Transition V0.9** ✅ 已冻结（四 Xavier；`NO_CANDIDATE`；0001 FALSIFIED；不要第 4 条；不要调 ADX/hold/VOL）  
**ALPHA_PROGRAM_V1** ✅ Universe/分类器已落地（149 PASS；Level 1=0）  
**Residual V0.91** ✅ 已冻结（`NO_CANDIDATE`；不要调 SMA60）  
**Alpha Recovery V1.0** ✅ 失败分析 + 合同（当时未跑）  
**Alpha Mission V1.1** ✅ STOP B。IT WEAK_EDGE 已杀；TS/MS/RI/AMS FALSIFIED。Level=0 Candidate=0。  
**Alpha Research Mission V2.0** ✅ STOP B。IV/COT/EIA/UST10/CARRY_V1A **NO_CANDIDATE**。Level=0 Candidate=0。  
**Data Expansion Mission V3.0** ✅ WAIT_HUMAN 记录保留（SUPPLY_V1 NO_CANDIDATE）。  
**MT5 Max Mission V4.0** ✅ COMPLETE_NO_CANDIDATE。不要再调 gold-silver / DXY / EIA z_cut。  
**Market Universe V5.1** ✅ EXTERNAL_DATA_GATE。841 全是 CFD。BREADTH WEAK_EDGE。SIZE NO_CANDIDATE。不要改 V4 hash。不要覆盖 `20260825`/`20260828`。不要调 BREADTH/SIZE。  
**V6 External Exchange** ✅ Pack E 已拉（$31.82）。TERM_STRUCTURE NO_CANDIDATE。  
**V7 Information Fusion** ✅ STOP B+C。OI/Volume NO_CANDIDATE。DTE WEAK_EDGE。不要调 OI/volume/dte/斜率。  
**V8 Information Fusion** ✅ STOP C。TOP5 全失败。期权已报价（OG.OPT/LO.OPT）。未下载。Level=0 Candidate=0。不要调 gap/steepening/OI/wow/yield。不要 $199/月。不要 tick。  
V11：MT5 日线样本内外回测 + 风控证伪。`survived` 不是年化保证。
**V14 STRATEGY_WEAK_BUT_RESEARCHABLE。** 可执行但弱。  
**V14.1 METHODOLOGY_GAP_CONFIRMED。** Candidate overlapping statistic ≠ 资金账户。不要 Long Validation。不要改 lookback/hold/分位。不要第13个因子。不要组合当两个 alpha。不要为 10% 调参。财务/行业/事件 BLOCKED。无采购。Final OOS DENIED。
**V15 NO_NEW_CANDIDATE。** 9/9 验证资金账户为负。没有第二个独立 Alpha。不要重开 residual / dispersion / disagreement。不要优化 H11/H12。`PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`。不要买 $93。不要第10条。
**V16 STOP B。** 财务/行业 PIT READY。6+3 预注册全失败。NEW_CANDIDATE=0。`A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE`。信息可用但无边。不采购。不重开 price-only / H11/H12。未派 Xavier。
**Post-V16 STOP B。** V17 macro / V18 altinfo / V19 industry×macro 全无 Level-1。统一 FDR m=18 discoveries=1（IM6，非 Candidate）。`A_SHARE_INFORMATION_ALPHA_NO_CANDIDATE`。Event/News DATA_BLOCKED。Options PAYMENT_REQUIRED。不采购。
**Post-V19。** 下一刀不是更多 A 股 CS 因子。V20 指数成分/调仓 `A_SHARE_INDEX_MEMBERSHIP_V1_NO_CANDIDATE`。不要加 SZ50 / 504 日 / 翻号。V21=分红公告窗口 `A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE`。不要重开 V13–V21。`A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED`。不采购。
**Post-V21 法医。** VERDICT **A**（0.72）：42/42 验证资金负，38/42 验证 MEAN_FORWARD 负。没有第二 Alpha 的主因是新家族无验证信息。Sidecar B 只解释 H11/H24 类重叠统计。不要改 hold/成本。新类 NONE。不要买 LO $11.99 来假装推进 A 股。
**Post-V21 自驱 S1。** Q1 相对 EW NEGATIVE（29/42）。Q2 NONE。Q4 一条合格多头 CS 袖子。confidence **0.91**。停搜索。KEEP_LOW_PRIORITY。不采购。
**Post-V21 W1–W6。** 13 条打过 EW 的账本 NOT_ONE_SHADOW 但 13/13 验证资金负。os.walk AVAILABLE=0。H11 零成本反事实 CAGR +2.9%（诊断）；Paper=NO。任何新家族先查 `POST_V21_AUTODRIVE/FAILURE_ATLAS.json`。唯一对得上 A 股缺口的付费类 = vendor 资金流/股东/融资；未报价；不自动买。
**V22 / V23 / V24（2026-09-04 晚，用户授权花 Databento 余额）。** V22 期货截面 30 CME 品种 $47.10 → `FUTURES_XS_V1_NO_CANDIDATE`（扣费前就平）。V23 融资融券免费 → `A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE`（M1 研究 t 4.85 / 验证归零；不调、不移窗）。V24 股东户数免费 → `A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE`。北向 DATA_BLOCKED。余额 ≈$46 不再花。不重开 V22–V24。免费对象先查 `FAILURE_ATLAS.json`（71 行）。
**规则修正 V1（2026-09-04 深夜，用户授权改规则）。** `docs/research_engine/RESEARCH_RULES_AMENDMENT_V1.md`。保留：预注册、成本模型、非重叠 CAGR、FDR、无正独立账本不 Paper/Live、不改历史。修改：A1 每个新家族可**事前**登记 LO20 或 HN20（对冲）账本；A2 固定划分之外加 5 个滚动验证窗（≥4/5 正）；A3 每个信息层允许**一个**预注册模型，跑完冻结、不许搜特征/参数；A4 聚类/独立性用**超额-vs-EW 序列**（原始 MF 序列测的是大盘）。禁用窗仍锁。
**V25 / V25.1 / V26（2026-09-04 深夜，$0）。** V25 `A_SHARE_MULTILAYER_MODEL_V25`：14 个已有 PIT 特征 → 1 个 LightGBM（walk-forward，2021-08 冻结）+ 无拟合基线，m=2。**ML1 = 第一个 Level-1**：验证超额 +1.47%/20d（t 17.1）；LO20 研究 +276%（CAGR 14.5%，MaxDD −47%），验证 +30.9%（熊市；CAGR 11.1%，MaxDD −21%）；滚动 5/5；成本 2× 仍 +18%。正式标签 `WEAK_CANDIDATE_SAME_CLUSTER`（原始 MF 相关 0.94，是大盘）；超额序列 corr vs H11 **0.06**。V25.1 复现 7/7 + placebo 干净 → **`A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE`，NEW_INDEPENDENT=1**，STOP A。V26 策略规格已写（LO20 账本；小盘/低换手倾斜明示；≈¥5M 起）。**HN20-vs-HS300 不是策略**（β 0.92 到 EW−HS300，MaxDD −54%）。**禁止**：为改善 ML1 动特征/参数/hold/成本/对冲/refit（任何改动 = 新合同、计 m）；用验证期或禁用窗选东西；把 V25 当 10% 承诺。**待用户**：禁用窗单次预声明读取；Paper。
**V27（2026-09-04 夜，$0，冻结）。** `A_SHARE_FINANCIAL_DEEP_MODEL_V27`：东财季报 4 表免费（INCOME/CASHFLOW 的 NOTICE_DATE 晚 12 月 → 不用；CPD+BALANCE 原始公告日、同期取最早版、知识时间约束）→ 10 固定季报特征 → 2 预注册 LightGBM，LO20 闸门。**ML2F 仅季报层**：验证超额 +0.52%（t 5.6）、滚动 5/5、**超额 corr vs ML1 0.06（独立）**，但 LO20 验证资金 **−0.3%** → 不过 Level-1；HN20 验证 +12% 已看见，**禁止**事后换账本。**ML2 全栈**：Level-1 但 corr vs ML1 **0.96** 同簇，验证 1.42% vs ML1 1.47% → 无增量。结论 `LEVEL1_SAME_CLUSTER_AS_ML1`，**NEW_INDEPENDENT 仍 1，ML1 不变**。季报层 = 唯一与 ML1 正交且验证显著的信息层；卡在账本不在信息。**禁止**：调 ML2F/ML2；用 ML2 换 ML1；ML1+ML2F 当两袖；重开 INCOME/CASHFLOW；买季报数据。ATLAS 73 行。
**V28 ML1 Final OOS（2026-09-04 深夜，用户委托自决，已读已锁）。** 协议先写；原始数据延伸到 2026-08（特征到 2024-02-29 与冻结缓存逐位相同）；闸门 = V26 政策 REFIT_240。**`FINAL_OOS_PASS`**：超额 vs EW +1.00%/20d（t 9.3）、LO20 +71.4%（CAGR 24.3%，MaxDD −21.3%）、19/30 期打过 EW；冻结模型同向。合格 EW 自己 +1.17%/20d（小盘牛市），一半以上是 β。三段正账本 +276% / +30.9% / +71.4%，全程 CAGR ≈ 13.7%——不是承诺。**`FINAL_OOS_READ.json` 存在即拒绝再读；ML1 再无禁用窗；不改任何参数；不用禁用窗挑变体。** 下一门 = Paper 准备（五源每日增量管线 + 打分器只出名单 + 监控账本，按五阶段先 Design）；Paper 开始日/账户/行情源需用户。Portfolio 仍缺第二袖。
**V29 ML1 前向管线（2026-09-05 早，Smoke 5/5 PASS，Stability 进行中）。** `research_engine/ml1_live/daily.py` 每个交易日跑一次（≈35 分钟）：live 日历/basics/增量日线 → live pack（冻结块逐位相同）→ 融资/户数/成分增量 → 14 特征 → REFIT_240 模型缓存 → `live/signals/SIGNAL_{date}.json` 前 20% 名单 → `live/ledger/LEDGER.json` 影子账本（接 V28 链，第一信号 2026-08-28，结算 ≈09-29）。2026-07-30 重打分与 V28 分数 Δ0.0。**禁止**：往 `ml1_live` 里加任何改变名单的东西（特征/参数/hold/成本/对冲/refit 频率）；写冻结目录；`order_send`。影子账本 ≠ 资金 ≠ 承诺。有账户的 Paper 待用户。
**Amendment V2 + V30 MT5（2026-09-05 下午，用户授权解除 MT5 限制，$0）。** `RESEARCH_RULES_AMENDMENT_V2_MT5.md` 解除 ML 禁令（≥300 只截面）/ 股票 CFD 只清点 / 只多头账本；纪律全保留；**仍不重开** XA…SIZE / V10 / V11 / OI / DTE / TERM_STRUCTURE。终端无 XAUUSD / US500 / BTC。V30：492 只美股 CFD D1 冻结 → 7 价格特征 → 1 LightGBM → LS20 闸门 + 实测费率（多头融资 −11.09%/年、空头 −0.91%/年、点差 0.15%）→ **`MT5_US_XS_PRICE_V30_NO_CANDIDATE`**（验证毛价差 t 0.18；LS20 −71.5% t −4.0；LO−EW −1.03%/20d t −4.4；滚动 2/5）。**`MT5_STOCK_CFD_COST_CEILING`**：LS 一期成本 ≈1.9%/20d，任何信息层都过不了 → 不开 V31 on CFD；不调 hold/分位/账本；不在 MT5 上开 H1/tick；不为 MT5 采购。美股 alpha 需现金股票账户（用户决定）。MT5 对象已清点完。
**执行假设（2026-09-05 22:20 用户纠正，硬性）。** 用户 = 小资金、平安普通账户、无量化权限、短期开不了。**禁止**把 QMT/PTrade、999 只等权自动下单当 ML1 实盘路径；**禁止** computer-use / 非官方 API 下单。执行唯一形态 = 系统出短名单（`V26_1_ML1_TOP20_MANUAL`：前 20 只、等权、按手、最低佣金 ¥5、板块按用户权限），用户手工下单。V29 每日同时出 `SIGNAL`（999 只参考）与 `SHORTLIST`（20 只）；`LEDGER.json` / `LEDGER_TOP20.json` 两条影子账本。历史读取三种板块口径均 VIABLE（不读禁用窗）；板块由权限定、不由结果挑。MT5 美股 = CFD 已判死；期货账户未开，V31 研究先做。QMT 等资金权限到位再谈（新合同）。**用户事实 22:44：只能买主板；本金 ¥20,000；期望 ¥20 以内** → V26.2 `ML1_TOP10_20K_MAIN`（N=10 由资金÷一手推出，仅主板，收盘 ≤¥20，¥5 最低佣金）历史 VIABLE（验证 +32.7%，MaxDD −11%）；`daily.py` 默认 `--boards MAIN --manual-capital 20000 --n-names 10 --max-price 20`。不调 N / 价格上限 / 成本。¥20k 是练手不是财务自由。**23:20 诊断**：V26.2 在 2024-03→2026-08 已读窗 +31.5% 但超额 vs EW ≈0（t 0.01）= 纯 β；近 6 月 −12.6%。**禁止**用该窗挑 N/板块/价格。**V32 MT5 宏观池化 ML**（Amendment V2.1，63 只，黄金/原油仅 2018-12 起）→ `MT5_MACRO_POOLED_V32_NO_CANDIDATE`（毛价差 t 1.0；LS −60.5%；0/5）。MT5 宏观 D1 对象清点完（V1–V8 / V30 / V32）；不调、不按组切、不上 H1、不采购。
**用户声明 23:36（约束 + 人生目标，不是研究任务，硬性）。** 27 岁、目标 35 岁财务自由 = **期望不是闸门**；本金 ≤¥20k，后期月追加 2k–10k；一手 100 股、股价 ≤¥100（¥20 是算错）；不满仓、总仓事先定死；每只 1 手；N 随价格。**V26.2 作废**（文件留证）。V26.3 `ML1_ONELOT_70PCT_MAIN` **只算一次** → 验证 −10.8%、超额 t 0.87 → **NOT_VIABLE**（执行外壳问题）。**禁止**：为提高收益改 ML1 特征/参数/持有期/成本；试仓位比例/价格上限/手数；杠杆或加仓凑 CAGR；重开 MT5 黄金原油外汇/股票 CFD；把财务自由写成 Candidate/Paper 条件。复利算术见 `docs/OWNER_CONSTRAINTS_AND_GOAL.md`：缺口是本金不是边。短名单继续出、影子账本继续记、人暂不上实盘；研究资源全给 V31。
**V26.4（2026-09-06 00:15，用户 00:13 允许等金额多手）。** V26.3 拆解：一手制吃掉 1.8%/期，不是买卖点/模型。V26.4 `ML1_EQMONEY_70PCT_MAIN`（主板、70% 仓、每只 ¥2,000、N=floor(0.7×权益/2000)、出场遇跌停/停牌**顺延**最多 10 日再标 STUCK）**只算一次** → 验证 +13.4%（CAGR 5.1%，MaxDD −7.9%，超额 t 2.55）**VIABLE_HISTORICAL**；现金闲置 ≈49%。`daily.py` 默认 = V26.4。**禁止**调单位/仓位/N 公式/顺延天数；不读禁用窗。结论仍是本金决定数量级；人是否上 ¥20k 由用户定。
**V26.5（00:32，用户允许 80%）。** 仅 70%→80%，只算一次 → 验证 +12.1%（t 2.65）VIABLE；80% < 70% 是取整噪音，**不选**。"必要时 100%" 不采纳（无事前触发规则）。近期窗（V28 已消耗）**诊断**：全窗 +28.6% 但超额 t 0.16 = β；近 6 月 −7.7%。**近期窗不作门；不再对任何变体读它。** `daily.py` 默认 80%。
**用户 00:57 执行偏好 + MT5 清点（硬性）。** 执行偏好 = **MT5 下单**，期货账户后开。**A 股 V26.5 冻结**：只出名单和影子账本，**不再改外壳**。`MT5_D1_LEGAL_OBJECT_INVENTORY.md`：对照 ATLAS 76 行，MT5 D1 **可立即做的合法新对象 = 0**（FX/贵金属/能源/农产品/股指/债券/美股 CFD/ETF CFD（swap 同 −11.09%）全覆盖或成本死）；唯一未测层 `CN_INFO_TO_COMMODITY`（中国信息→铜/银/油，7.7 年样本功效低）排在 V31 之后。**下一刀 = V31 国内期货截面**；若过门，AU/AG/CU/SC 观点映射 GOLD/SILVER/COPPER/CrudeOIL 用 MT5 执行（实测：GOLD swap ≈0.13%/年，SILVER ≈1.1%，COPPER/油 −4.5% 双边），其余品种待期货户。禁止为提高收益改参数/成本/加杠杆。
**V31 中国期货截面（2026-09-06 10:10，冻结）。** 同合约展期调整 + LS 三分位只算一次 → `CN_FUTURES_XS_V31_NO_CANDIDATE`（G1/G4 资金正，G2 t 0.81，G3 3/5）。不调、不映射黄金原油。下一刀 V35 `CN_INFO_TO_COMMODITY`。
**V33（2026-09-06 09:20）。****V33 涨停事件模型**（用户要求的"事先预测谁会涨停"小资金版，只算一次，ATLAS 77）：前 10% 命中 12.4% vs 基础 4.4%（t 60.9）**能预测**；外壳账本验证 **−88%**、¥1M 大账本 −66% **不能赚钱** → `A_SHARE_LIMITUP_EVENT_V33_PREDICTIVE_BUT_NOT_TRADABLE_AT_20K`。彩票效应，不是资金规模问题。**禁止**调阈值/持有期/特征、日内变体、为 G1 找账本、把 ML3 塞进 ML1、重开短线/涨停/题材类。
**V34 出场规则诊断（2026-09-06 09:00）。** 13 条止盈/止损/移动止盈/保本规则事前写死，只读研究期：ML1 11/12 条比现状差（紧规则 → +144% 砍到 +12…25%），唯一略好 TP20 = 13 选 1 噪音**不选**；V33 无一翻正 → `EXIT_RULES_NO_IMPROVEMENT`。**禁止**把任何出场规则写进 `daily.py`/V26.5、用验证期/禁用窗重跑、以 TP20 细分点位。近期窗不再对任何变体读；一月/一季无统计意义，"最近"看 V29 影子账本。
**V26.6 补满仓位（2026-09-06 09:25，采纳）。** 事前算术：V26.5 现金闲置 42%（¥2,000 整手余数）。只加第二轮"同一批名字按分数每次加 1 手到 80% 预算"，只算一次 → 验证 **+33.9%（CAGR 12.3%，MaxDD −11.4%，t 2.56）** vs V26.5 +12.1%；研究 +318%（MaxDD −45%）。`daily.py` 默认 `ML1_EQMONEY_80PCT_TOPUP_MAIN`。不是 alpha 改进，是钱投出去了。**禁止** 试别的补仓/单位；因回撤加止损（V34）；改 ML1；读近期窗。
**V26.7 满仓 + 月定投 ¥2k（2026-09-06 09:35，用户 09:14 事前约束，采纳）。** 100%（预留 ¥200）+ 每月首个信号日存 ¥2,000，只算一次 → 验证 TWR +27.0%（CAGR 10.0%，MaxDD −13.2%，t 3.58，23/29）、资金 ¥74k→¥79k IRR 4.2%；研究 TWR +264%、¥236k→¥432k IRR 11.2%；2017/2018 各 −30%。`daily.py` 默认 `ML1_FULL_TOPUP_CONTRIB2K_MAIN`。**外壳冻结**：不试 90/95%、预留、定投额/日；不加止损；不改 ML1；不读禁用/近期窗。
**V26.8 单位随权益增长（2026-09-06 09:50，采纳）。** 佣金算术 + 排名单调 → `单位 = max(2000, 权益/N_target)`，{10,20,40} 研究期按夏普选 → N10（+551%，CAGR 21.3%）；验证 **TWR +39.0%（CAGR 14.0%），IRR 10.4%，¥74k→¥86.9k**。逐日 MaxDD 研究 −56%、验证 −24%；滚动 1 年 22% 为负、5 年 0%。`daily.py` 默认 `ML1_SCALED_UNIT_N10_FULL_CONTRIB2K_MAIN`。含定投的期末 MaxDD 低估已修正。**外壳到此冻结**：不试别的 N_target/单位下限、不做月份择时、不加止损、不改 ML1、不读禁用/近期窗。
HYP-0001 14:11 未改。不要 order_send。不要回头调 XA / RT / XR / IT / TS / MS / RI / AMS / IV / POS / INV / RATES / CARRY / SUP / CM / UM / BREADTH / SIZE。不要无 Candidate 写策略。

---

## 快速导航

| 文件 | 用途 |
|------|------|
| `SPEC.md` | V1.1 技术规范（最高技术法律） |
| `PROJECT_STATUS.md` | 项目状态快照（接力开发入口） |
| `PROJECT.md` | 项目介绍 |
| `TODO.md` | 当前任务与五阶段进度 |
| `TEST_PLAN.md` | 测试标准与 PASS 记录 |
| `ROADMAP.md` | 开发路线 |
| `ARCHITECTURE.md` | 系统架构 |
| `DECISIONS.md` | 架构决策 |
| `CHANGELOG.md` | 修改记录 |
