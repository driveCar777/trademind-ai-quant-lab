# A_SHORT_DATA_SOURCE_MATRIX.md

> 逐项数据源审计（§二、§31）。列：source / provider / data_type / coverage / historical_depth / frequency / PIT / latency / reliability / fallback / cost / current_implementation / 结论。
> 「结论」= REUSE / EXTEND / NEW / BLOCKED / DEAD。**优先复用现有；付费源单独提出，不默认购买（§30）。**

---

## 1. 核心数据（失败即 `NO RECOMMENDATION`，§27）

| source | provider | 类型 | 覆盖/深度 | 频率 | PIT | latency | 可靠性 | fallback | cost | 现有实现 | 结论 |
|--------|----------|------|-----------|------|-----|---------|--------|----------|------|----------|------|
| Price D1 | BaoStock | OHLCV+turn+amount | 1990-12-19→今, 5549+ | 日 | 是（冻结+live_hash） | 收盘后当日 | 高（canonical） | AkShare（仅 cross-check，SSL 常挂） | 免费 | `cn_a_share/acquire.py`,`ml1_live/panel.py` | **REUSE** |
| Calendar | BaoStock | 交易日 | 1990→2027-01 | — | 是 | — | 高 | 冻结 reference csv | 免费 | `cn_a_share/calendar.py` | **REUSE** |
| Universe/Basic | BaoStock | 代码/名称/上市退市/ST | 8928 行 | 月/事件 | 是（`listed_on`） | — | 高 | 冻结 BASIC csv | 免费 | `cn_a_share/universe.py` | **REUSE** |
| 涨跌停/停牌撮合 | 面板派生 | exec 可行性 | 全历史 | 日 | 是 | — | 高 | — | 免费 | `strategy_v14_1/scores.py::exec_ok_matrix` | **REUSE** |

## 2. 短周期关键增量（A-Short 主战场）

| source | provider | 类型 | 覆盖/深度 | 频率 | PIT | latency | 可靠性 | fallback | cost | 现有实现 | 结论 |
|--------|----------|------|-----------|------|-----|---------|--------|----------|------|----------|------|
| **分钟 K 线** | BaoStock（同 API，`frequency=5/15/30/60`） | 日内价量 | **文档称 ≈1 月**（未实测） | 1/5/15/30/60min | 需新建 | 收盘后 | UNKNOWN | 无 | 免费 | **不存在** | **NEW**（`BaoSession` 加分钟查询 + `tm-ashare-…-M5-…` + 新 pack） |
| 市场广度 breadth | 面板派生 | 涨跌家数/涨停数/换手 | 全历史 | 日 | 是 | 收盘后 | 高 | — | 免费 | `alpha_v2/signals.py::cs_breadth`、`v38_overlay/sentiment.py`（ad hoc，未持久化） | **EXTEND**（落成每日 breadth 序列） |
| 涨停统计/连板/近高 | 面板派生 | 事件特征 | 全历史 | 日 | 是 | 收盘后 | 高 | — | 免费 | `ml_v33::limit_up_matrix`、`EVT_*` | **EXTEND**（派生；封单/排队=L2 缺） |
| 融资融券（每股每日） | 东财 `RPTA_WEB_RZRQ_GGMX` | 资金杠杆代理 | 2010-03→ | 日（滞后1） | 是（lag=1） | D+1 盘前 | 中 | 无 | 免费 | `cn_a_share_margin_v23` | **REUSE**（唯一真·日频资金代理） |
| 龙虎榜（龙虎/席位） | 东财/vendor | 游资/机构成交 | — | 日 | 需建 | 收盘后 | — | 无 | 部分付费 | **不存在** | **NEW+付费评估** |
| 主力/大单资金流 | 东财/vendor | 分档资金 | — | 日/分钟 | 需建 | — | — | 无 | 多为付费 | **不存在** | **NEW+付费评估** |
| 题材/概念板块成分 | 东财/同花顺 | 概念映射 | — | 事件 | 需建 | — | — | 无 | 部分付费 | **不存在** | **NEW+付费评估** |

## 3. 中低频信息层（短周期增量价值有限，但 PIT 齐全）

| source | provider | 覆盖 | 频率 | PIT | 现有实现 | 结论 |
|--------|----------|------|------|-----|----------|------|
| 股东户数 | 东财 `RPT_HOLDERNUM_DET` | 全历史/票 | 季 | 是（`HOLD_NOTICE_DATE`） | `holders_v24` | REUSE（慢，短周期弱） |
| 质押 | 中登 `RPT_CSDC_LIST` | 2014→,1.43M 行 | 周（lag=3） | 是 | `pledge_v38` | REUSE（慢） |
| 增减持 | 东财 `RPT_SHARE_HOLDER_INCREASE` | 2007→,268k | 事件（lag=1/3） | 是 | `insider_v38` | REUSE（事件短窗有一定价值） |
| 业绩预告/快报 | 东财 `RPT_PUBLIC_OP_NEWPREDICT` | 2008→,100k | 事件 | 是 | `preann_v38`（**唯一事件窗特征**） | REUSE/EXTEND |
| 季报深度 | 东财 CPD+BALANCE | 2008→ | 季 | 是（INCOME/CASHFLOW 晚12月已弃） | `findeep_v27` | REUSE（慢） |
| 指数成分 | BaoStock HS300/ZZ500 | 2009→2026-08 月 | 月 as-of | 是 | `index_v20` | REUSE |
| 分红 | BaoStock | 24.8k | 事件 | 是（公告日） | `div_v21` | REUSE |
| 行业分类 | BaoStock 月 as-of | 2009→2024-02 | 月 | 是（V16 网格） | `information_v16` | REUSE（`SNAPSHOT_ONLY`） |

## 4. 宏观 / 海外 / 情绪

| source | provider | 覆盖 | 频率 | 现有实现 | 结论 |
|--------|----------|------|------|----------|------|
| 全球指数 | Yahoo `^IXIC/^DJI/^N225/^HSI` | 2000→今 | 日 | `v38_overlay/global_north.py::yahoo_closes`（缓存，活） | **REUSE**（O4 曾 REJECT，作 context 可用） |
| 北向资金（日频） | 东财 `RPT_MUTUAL_DEAL_HISTORY` | 2014-11→**2024-08-19 止** | 日 | `global_north.py::northbound_daily` | **DEAD**（HKEX 停发；**禁代理**） |
| 散户开户/情绪 | 中登 `RPT_STOCK_OPEN_DATA` | 月（lag15） | 月 | `v38_overlay/sentiment.py` | REUSE（O3 曾 REJECT，作 context） |
| 美债收益率/FRED | Treasury/FRED | 长 | 日 | `scripts/data_acquire_ust_yields.py`,`acquire_dfii10.py` | REUSE（context） |
| 冻结宏观 EURUSD/US500/GVZ | 本地冻结 | — | 日 | `cn_a_share_macro_v17/macro.py`（`_assert_hash`） | REUSE |

## 5. 文本类（全部 NEW；且是治理红线，见风险文档）

| source | 现状 | 结论 |
|--------|------|------|
| 新闻正文/RSS | **不存在**（`feedparser/bs4/jieba`=0；`announcements/`仅`.gitkeep`） | **NEW**；且新闻=`DATA_BLOCKED`研究特征 → 只能作 operational gate |
| 政策（五年规划/部委） | **不存在**（`五年规划/部委/发改委`=0） | **NEW**；同上红线 |
| 公告正文 | **不存在**（只有 `announcement_date` 数值门） | **NEW**（正文）；PIT门 REUSE `pit.py` |
| LLM 联网理解（Grok web） | `paper_fusion.py` 已有 | REUSE 作**理解/红队**，**不作可回测特征** |

## 6. LLM / API 源

| source | provider | 现有实现 | cost 控制 | 结论 |
|--------|----------|----------|-----------|------|
| Cursor Cloud Agents | api.cursor.com | `cursor_cloud.py`（`grok-4.6 xhigh`，5×重试，防重复计费） | 仅 `MAX_GROK_CALLS_PER_DAY=3` | REUSE（token/$ 账本 NEW） |
| DeepSeek / 本地 Qwen | ai-gateway :9100 | `ai-gateway/*` | token 统计有 | REUSE |

## 7. 付费源（单列，不默认买，§30.7）

`research_engine/data_sources/DATA_SOURCE_REGISTRY_V1.json` 已记的付费/受阻源（作模板）：Databento(`CREDENTIAL_REQUIRED`,余额≈$46 冻结)、ORATS/CME/FirstRate/TradingEconomics(`PAYMENT_REQUIRED`)、GLD-ETF(`DATA_BLOCKED`)。
**A-Short 若要龙虎榜/主力资金/题材/L2，须在此表新增一行并单独报价，等 owner 批准后才买。**

---

## 8. 注册表统一化建议

现有三套注册表（`data_sources/registry.py` + `DATA_SOURCE_REGISTRY_V1.json`、`A_SHARE_SOURCE_MATRIX_V12.json`、`config/data_sources.yaml`）**缺 `latency/fallback/freshness SLA`**。
A-Short 应 **EXTEND** `data_sources/registry.py` 加 `latency / fallback_sources / freshness / status∈{OK,STALE,PARTIAL,FAILED,UNKNOWN} / last_success / last_attempt / retry_count / coverage`（§26/§31），并把 news/policy/LLM/分钟源都登进去，**不造第四套**。
