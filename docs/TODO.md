# TradeMind TODO — 版本任务清单

> **当前活跃模块:** Market Universe V5.1 **EXTERNAL_DATA_GATE**。Level 仍是 0。Candidate=0。
> **最后更新:** 2026-08-29（841 盘完；BREADTH+SIZE 已跑；不改 V4）
> **阶段终点:** 人类采购曲线/期权面，或 Level 1。禁止调参救 BREADTH/SIZE/Top5。禁止 RSI。禁止覆盖 `20260825`/`20260828`。

---

## 版本完成记录

| 版本 | 里程碑 | 状态 | 冻结日期 |
|------|--------|------|----------|
| V1.0 | Worker Template (indicator-worker) | ✅ FROZEN | 2026-07-25 |
| V1.1 | Master API + 4 Worker 端到端 | ✅ FROZEN | 2026-07-25 |
| V1.2 | Master 增强 (重试/超时/探测/任务列表) | ✅ FROZEN | 2026-07-31 |
| V1.3 | Dashboard 前端 (单文件深色主题 Web 面板) | ✅ FROZEN | 2026-07-31 |
| **V2.0** | **Factor Worker 增强 (15 因子/50 只股票/评分引擎)** | **✅ FROZEN** | 2026-07-31 |
| V2.1 | Backtest Worker 增强 (4 新策略/滑点手续费/高级指标) | ✅ FROZEN | 2026-07-31 |
| V3.0 | AI Gateway (Arc A770M LLM 推理) | ✅ FROZEN | 2026-08-22 |
| V4.0 | Research Agent (AI 驱动量化研究) | ✅ FROZEN | 2026-08-23 |
| V4.1 | 两步研究（factor→backtest） | ✅ FROZEN | 2026-08-23 |
| V5.0 | 模拟纸质单（人手确认，不发单） | ✅ FROZEN | 2026-08-23 |
| V6.0 | 今日台账（先看拟单，不发 MT5） | ✅ FROZEN | 2026-08-23 |
| V7.0 | 本机样本 CSV（指标研究读文件） | ✅ FROZEN | 2026-08-24 |
| V8.0 | 因子/回测也读本机样本 | ✅ FROZEN | 2026-08-24 |
| V9.0 | MT5 模拟盘（人手确认后进终端） | ✅ FROZEN | 2026-08-24 |
| V10.0 | 人手选方向测通模拟盘 | ✅ FROZEN | 2026-08-24 |
| V11.0 | MT5 历史回测 + 风控证伪 | ✅ FROZEN | 2026-08-24 |
| V11.3 | 证伪解读不再编 0 笔 | ✅ FROZEN | 2026-08-24 |
| V11.4 | 成交明细（时间+价格） | ✅ FROZEN | 2026-08-24 |
| V11.5 | 连续切分 + 冻结策略篮 | ✅ FROZEN | 2026-08-24 |
| V11.6 | 行情分段（涨/跌/震） | ✅ FROZEN | 2026-08-24 |
| V11.7 | 四台并行样本内筛选 | ✅ FROZEN | 2026-08-24 |
| RP V0.3 | Causal Research Sandbox + Leakage Sentinel | ✅ FROZEN | 2026-08-25 |
| FD V0.1 | Factor Discovery（57 candidates / FDR / 四 Xavier） | ✅ FROZEN | 2026-08-26 |
| RE V0.5 | Strategy Discovery Foundation（Market State + 15 sketches） | ✅ FOUNDATION | 2026-08-26 |
| PD V0.6 | Profit Discovery（成本后回测 / 四 Xavier） | ✅ FROZEN | 2026-08-26 |
| AD V0.7 | Alpha Discovery Audit（仅设计） | ✅ DESIGN | 2026-08-26 |
| OS V0.7.1 | Alpha Operating System（分类/矩阵/V0.8合同） | ✅ DESIGN | 2026-08-26 |
| XA V0.8 | Cross Asset 执行（3 假设 / 四 Xavier） | ✅ FROZEN | 2026-08-26 |
| MAP V1 | Alpha 覆盖 / 数据 / 排序 / 12M | ✅ DESIGN | 2026-08-26 |
| RT V0.9 | Regime Transition 执行（3 假设 / 四 Xavier） | ✅ FROZEN | 2026-08-27 |
| XR V0.91 | GOLD/OIL residual（3 假设 / 本地 2000） | ✅ FROZEN | 2026-08-27 |
| PROG V1 | Alpha Program 盘点/库/门/路线 | ✅ DESIGN | 2026-08-26 |
| REC V1 | Alpha Recovery（forensics + 一个纸面合同） | ✅ DESIGN | 2026-08-27 |
| MISSION V1.1 | IT → TS → MS → RI → AMS | ✅ STOP B | 2026-08-28 |
| MISSION V2.0 | IV → COT → EIA → UST10 → FX overnight carry | ✅ STOP B | 2026-08-28 |
| MISSION V3.0 | Data factory + EIA supply + vendor/purchase pack | ⏸ WAIT_HUMAN 记录 | 2026-08-28 |
| MISSION V4.0 | MT5 max history + CROSS_METAL + USD_METAL | ✅ NO_CANDIDATE | 2026-08-29 |
| MISSION V5.0 | Market universe + cross-section / corr / dispersion | ✅ Top5 NO_CANDIDATE | 2026-08-29 |
| MISSION V5.1 | 841 inventory + BREADTH + SIZE | ⏸ EXTERNAL_DATA_GATE | 2026-08-29 |

## MT5 Max Mission V4.0 — COMPLETE_NO_CANDIDATE 2026-08-29

2000 bars 不是上限。新 ID，未覆盖 `20260825`。

- 能力图：`data/market/research_engine/mt5_history/MT5_HISTORY_CAPABILITY_V1.json`
- CROSS_METAL_V1 四 Xavier **NO_CANDIDATE**。不要 gold-silver z_cut。
- USD_METAL_V1 四 Xavier **NO_CANDIDATE**。不要 DXY z_cut。
- VIX 1.45y，未开族。
- 报告：`MT5_MAX_MISSION_V4_REPORT.md`。
- Databento：只为曲线/期权面。不要为了再下一根 Ava K 线付钱。

## Data Expansion Mission V3.0 — WAIT_HUMAN 2026-08-28

目标不是策略。目标是新 Information Set。

- 工厂：`research_engine/data_expansion/` + `research_engine/data_sources/`
- 免费新源：EIA 产量 + 开工率。SUPPLY_V1 四 Xavier **NO_CANDIDATE**。KILLED。不要 z_cut。
- 仍 BLOCKED：futures curve、option surface、macro consensus、GLD file、structured news。
- 人类唯一下一步：Databento 注册拿 $125 credits，key 写入 `.env` 的 `TRADEMIND_DATABENTO_API_KEY`。
- 报告：`DATA_EXPANSION_MISSION_V3_REPORT.md`。采购包：`HUMAN_DATA_PURCHASE_ACTION_PACK.md`。

key 进 `.env` 之后 Cursor 从 ACQUIRE 继续，不要再写一份排序然后停。

## Alpha Research Mission V2.0 — STOP B 2026-08-28

从 Level 0 推向 Level 1 再次失败。新信息公开源已测完。Candidate=0。Level 仍 0。

- IMPLIED_VOL / POSITIONING / INVENTORY / RATES / CARRY_V1A：local 2000 + 四 Xavier。全部 **NO_CANDIDATE**。KILLED。
- CARRY_V1：INVALID_ALIGNMENT（1971 FX 研究窗早于 €STR）。不是机制失败。
- 仍 BLOCKED：option smile、macro consensus、futures curve、gold ETF file、news schema。
- 报告：`ALPHA_RESEARCH_MISSION_V2_REPORT.md`。Ledger：`RESEARCH_LEDGER_V2.json`。Memory：`RESEARCH_MEMORY_V2.json`。

下一最小任务：**付费或人工账户数据**。不要再开 GVZ/COT/EIA/UST10/overnight z_cut。不要读 Final OOS。

## Alpha Mission V1.1 — STOP B 2026-08-28

从 Level 0 推进到 Level 1 失败。五家族已执行。Candidate=0。Level 仍 0。

- IT V1.0：local 2000 + 四 Xavier。WEAK_EDGE。FDR 0/3。KILLED。
- TS / MS：local 2000 + 四 Xavier。3/3 FALSIFIED。KILLED。
- RI / AMS：local 2000 权威。3/3 FALSIFIED。KILLED。
- GOLD/OIL D1 最大 **7.715y BROKER_LIMITATION**（2018-12-12）。不要写成 10y。
- 报告：`ALPHA_MISSION_V1.1_REPORT.md`。记忆：`RESEARCH_MEMORY_INDEX.json`。失败库：`FAILED_ALPHA_DATABASE_V2.json`。

下一最小任务：**新数据**（2018 前商品、IV、carry、新闻）。不要再开 Ava GOLD/OIL hold=5 多头合同。不要 AI feature farming。不要读 Final OOS。

## Alpha Recovery V1.0 — DESIGN 2026-08-27

失败分析 + 数据审计 + Opportunity V2 + **一个** 新合同。未跑 Xavier。未读 Final OOS。

- 选出：`OPP-IT-ME` / `INSTITUTIONAL_TIME_V1.0` / hash `1d3c4a1f…24457`
- 文档：`ALPHA_RECOVERY_REPORT.md`，`DATA_CAPABILITY_REAL.md`，`NEXT_ALPHA_DECISION.md`，`INSTITUTIONAL_TIME_V1.0_CONTRACT.md`
- 探针：H1 5y / M15 2y **可达**（新 ID）；GOLD/OIL D1 仍 <10y
- 下一最小任务：**审查合同**。不要实现 runner。不要冻新 H1 除非另批。

## ALPHA_PROGRAM_V1 — DESIGN 2026-08-26

全仓盘点、机制库 V2、Top 10、路线 V2、V0.9 机制深挖、引擎缺口、Level 1/2 门、失败知识库。  
未跑实验。Level 1 Candidate = 0。CAGR≥10% 不是发现门。  
索引：`docs/research_engine/ALPHA_PROGRAM_V1.md`。日志：`STATUS_UPDATE.md`。

下一最小任务：不要重开 V0.9/V0.91。不要写策略。日历族仍是 UNKNOWN，需新合同才许动。

---

## Regime Transition V0.9 — FROZEN 2026-08-27

四 Xavier 已跑。hash 未改。程序 **`NO_CANDIDATE`**。0001 FALSIFIED；0002/0003 INCONCLUSIVE；FDR 0/3。  
01=04 content_hash `31995464…249b8`。  
文档：`REGIME_TRANSITION_V0.9_REPORT.md`，`V0.9_EXECUTION_FREEZE.md`。

不要第 4 条，不要改 hold=5 / ADX14 / VOL 33/67。

## Cross Residual V0.91 — FROZEN 2026-08-27

本地 2000-iter。hash 未改。程序 **`NO_CANDIDATE`**。不要调 SMA60。  
文档：`CROSS_RESIDUAL_V0.91_REPORT.md`。

---

## Cross Asset V0.8 — FROZEN 2026-08-26

四 Xavier 已跑。四向 D1 join = 1993 日。HYP-XA-0001/0002/0003 均为 **FALSIFIED**。  
程序结果 **`NO_CANDIDATE`**。FDR m=3 discoveries=0。  
文档：`docs/research_engine/CROSS_ASSET_ALPHA_V0.8_REPORT.md`，`V0.8_EXECUTION_FREEZE.md`。

下一最小任务（需另批）：Regime Transition V0.9 **新合同**，或停。不要第 4 条，不要改领先期/阈值/方向/成本。

---

## Alpha OS V0.7.1 — DESIGN 2026-08-26

分类、覆盖矩阵、12 个月队列、Cross Asset V0.8 三条假设（纸面合同）。无代码、无新实验。  
文档：`docs/research_engine/ALPHA_OPERATING_SYSTEM_V0.7.1.md`。

下一最小任务（需另批）：D1 UTC 对齐 + 只跑 HYP-XA-0001/0002/0003。不要第 4 条，不要并行开 Regime/Portfolio。

---

## Alpha Discovery V0.7 — DESIGN 2026-08-26

只写计划，不写代码，不跑新实验。单品种短持有已测败。  
下一最可能赚钱方向：跨品种 D1 对齐 + 少量预注册滞后假设。  
文档：`docs/research_engine/ALPHA_DISCOVERY_V0.7_PLAN.md`。

下一最小任务（需另批）：D1 对齐索引，只开方向 2。不要同时实现转换/时段/AI/VRP。不要 MT5。

---

## Profit Discovery V0.6 — FROZEN 2026-08-26

四 Xavier 16 jobs。NEXT_BAR_OPEN + 成本 + 风险。结果：`WEAK_EDGE_ONLY`，无程序级 CANDIDATE。  
OIL D1 动量是单市场残留，D1 CAGR≈0.2%，不是年化 10%。  
文档：`docs/research_engine/PROFIT_DISCOVERY_V0.6_REPORT.md`。

下一最小任务：更长历史 或 低换手家族。不要 MT5，不要调参制造第二个命中。

---

## Research Engine V0.5 — FOUNDATION 2026-08-26

Market State + 15 locked strategy sketches。Windows-local 16 dataset，FDR 203 / 0，`NO_USEFUL_STRATEGIES_FOUND`。  
不是 MT5，不是年化 10%。四 Xavier 调度已写、本轮未实跑。  
文档：`docs/research_engine/RESEARCH_ENGINE_V0.5_REPORT.md`。

---

## Factor Discovery V0.1 — FROZEN 2026-08-26

Windows 锁定 search space；四台 Xavier 执行 17 jobs。FDR 876 tests / 0 discoveries。  
结果：`NO_USEFUL_FACTORS_FOUND`。5 个 INCONCLUSIVE 是波动率聚类，不是方向性策略。  
不是回测，不是 HYP-0001 调参，不是年化 10%。`FINAL_OOS` 仍拒绝。  
文档：`docs/research_engine/FACTOR_DISCOVERY_V0.1_REPORT.md`。结果：`data/market/research_engine/factor_discovery/`。

下一最小任务：继续 Factor Discovery（新 versioned contract）。不要 Strategy Mining，不要锁 Final OOS。

---

## Research Protocol V0.3 — FROZEN 2026-08-25

四台 Xavier 对 16 个冻结 dataset 做因果特征、候选窗口、泄漏/纯度/边界、10 次重复与交叉复算。  
不是回测，不是选参，不是 GOLD M15 RSI 再验证。`FINAL_OOS_LOCKED=false`。  
文档：`docs/RESEARCH_PROTOCOL_V0.3.md`。结果：`data/market/research_protocol/`。

下一最小任务：Hypothesis Registry（新假设的第一份正式 Experiment Contract）。不要锁 Final OOS。

---

## 运维 — 一键启动 / 拉起节点 (2026-08-22)

| 项 | 状态 | 说明 |
|----|------|------|
| 本机 `start_all.bat` | ✅ 实测 PASS | Master 已在则跳过；网关 SYCL 新窗口；`LOCAL_START_PASS` |
| Smoke 05 | ✅ PASS | Master / Gateway model_loaded / 代理 AI |
| 拉起 02/03/04 | ✅ PASS | 01 未动。03 端口对齐 8002 |
| 三笔任务 | ✅ COMPLETED | factor 000003 / monitor 000004 / backtest 000005 |

对照：`docs/DIFF_2026-08-22_oneclick.md`。不是 V4，不改 Worker 计算代码。

网页启动/重启已落地（SPEC §15）。桌面只用 `TradeMind-Lab`，已运行会弹窗说明。

---

## 控制台 — 默认计算路径 (2026-08-22)

| 项 | 状态 | 说明 |
|----|------|------|
| SPEC §8.4 `data.result` | ✅ | 仅 `GET /task/{id}` 读结果；`GET /tasks` 不读 |
| Decision 019 | ✅ | 不自动提交、不自动问 AI |
| 控制台「现在就计算」 | ✅ | 推荐当前在线类型；离线类型灰掉 |
| AI 填算完的数字 | ✅ | 不再把任务请求当结果 |
| Smoke 07 | ✅ PASS | 列表无正文；详情有 result；新 RSI `latest=76.10` |

不是 V4。对照：`docs/DIFF_2026-08-22_default_path.md`。

---

## 运维 — Xavier-01 纳入四台启动 (2026-08-23)

| 项 | 状态 | 说明 |
|----|------|------|
| Phase 1 Design | ✅ | `docs/DESIGN_XAVIER01.md` + SPEC §15.4 + Decision 020 |
| Phase 2 Implement | ✅ | 默认批次不再 SKIP 01；Docker 只认固定箱名 |
| Phase 3 Smoke 08 | ✅ PASS | 探活 200；已在线不重复启动；脚本不再 SKIP 01 |
| Phase 4 / 5 | 不做 | 不连重启 01、不冻结本模块为新版本 |

四台都是当前阶段计算节点。01 只是 Docker，不是「本阶段不用」。

---

## 运维 — 一键状态更准 (2026-08-23)

| 项 | 状态 | 说明 |
|----|------|------|
| Phase 1 Design | ✅ | `docs/DESIGN_LAB_STATUS.md` + SPEC §15.5 + Decision 021 |
| Phase 2 Implement | ✅ | `scripts/lab_status.py`；`start_all.bat` 不再 netstat |
| Phase 3 Smoke 09 | ✅ PASS | 健康则 skip；报告含 Master / worker-01 |
| Phase 4 / 5 | 不做 | — |

---

## 控制台 — 算完下一步问 AI (2026-08-23)

| 项 | 状态 | 说明 |
|----|------|------|
| Phase 1 Design | ✅ | `docs/DESIGN_AI_NEXT.md` + Decision 022 |
| Phase 2 Implement | ✅ | 下一步条；离线禁用提问 |
| Phase 3 Smoke 10 | ✅ PASS | 有下一步按钮；填框不发推理；离线守卫 |

---

## 网关防护 — 单路推理 (2026-08-23)

| 项 | 状态 | 说明 |
|----|------|------|
| Phase 1–3 | ✅ Smoke 11 PASS | 锁 + token 上限 + F16=OFF。正在跑的网关要重启才吃到锁 |
| Phase 4 / 5 | 不做 | — |

---

## V11.0 MT5 证伪回测

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V11_WALKFORWARD.md` + SPEC §24 + Decision 032 |
| 2 Implement | ✅ Worker `close[]` + 70/30 + 风控判定 |
| 3 Smoke | ✅ `tests/smoke/20_walkforward.py` PASS |
| 4 Stability | ✅ `tests/stability/08_walkforward.py` PASS |
| 5 Freeze | ✅ 2026-08-24 |

---

## V10.0 测通模拟盘

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V10_WIRE_TEST.md` + SPEC §23 + Decision 031 |
| 2 Implement | ✅ `side=BUY/SELL` + 「测买 / 测卖」 |
| 3 Smoke | ✅ `tests/smoke/19_wire_test.py` PASS |
| 4 Stability | ✅ 沿用 03/14：无 confirm / 非法 side / 重复 |
| 5 Freeze | ✅ 2026-08-24 |

---

## V9.0 MT5 模拟盘

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V9_MT5_DEMO.md` + SPEC §22 + Decision 030 |
| 2 Implement | ✅ `mt5_service.py` + `source=mt5` + 黄金/欧美/原油/美日 |
| 3 Smoke | ✅ `tests/smoke/18_mt5_demo.py` PASS（假终端） |
| 4 Stability | ✅ `tests/stability/07_mt5_demo.py` PASS |
| 5 Freeze | ✅ 2026-08-24 |

同花顺：本环境没有可测官方接口，未做。A 股仍走因子 + `moutai.csv`。

---

## V8.0 因子 / 回测本机样本

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V8_SAMPLE_PRESETS.md` + SPEC §21 + Decision 029 |
| 2 Implement | ✅ `moutai.csv` / `xauusd.csv` + `kind` |
| 3 Smoke | ✅ `tests/smoke/17_sample_presets.py` PASS |
| 4 Stability | ✅ `tests/stability/06_sample_presets.py` PASS |
| 5 Freeze | ✅ 2026-08-24 |

---

## V7.0 本机样本 CSV

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V7_SAMPLE_DATA.md` + SPEC §20 + Decision 028 |
| 2 Implement | ✅ `data/samples/eurusd.csv` + `sample_service.py` + `GET /api/v1/samples` |
| 3 Smoke | ✅ `tests/smoke/16_sample_data.py` PASS |
| 4 Stability | ✅ `tests/stability/05_sample_data.py` PASS |
| 5 Freeze | ✅ 2026-08-24 |

---

## V6.0 今日台账

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V6_PAPER_DESK.md` + SPEC §19 + Decision 027 |
| 2 Implement | ✅ preview 先行 + `/api/v1/desk/today` |
| 3 Smoke | ✅ `tests/smoke/15_paper_desk.py` PASS |
| 4 Stability | ✅ `tests/stability/04_paper_desk.py` PASS |
| 5 Freeze | ✅ 2026-08-23 |

---

## V5.0 模拟纸质单

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V5_MT5_BRIDGE.md` + SPEC §18 + Decision 026 |
| 2 Implement | ✅ `order_service.py` + `/api/v1/orders*` + 「确认挂模拟单」 |
| 3 Smoke | ✅ `tests/smoke/14_paper_order.py` PASS |
| 4 Stability | ✅ `tests/stability/03_paper_order.py` PASS |
| 5 Freeze | ✅ 2026-08-23 |

---

## V4.1 两步研究

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V4_1_RESEARCH_CHAIN.md` + SPEC §17 + Decision 025 |
| 2 Implement | ✅ `chain` 最多 2 步 + 「因子后再回测」 |
| 3 Smoke | ✅ `tests/smoke/13_research_chain.py` PASS |
| 4 Stability | ✅ `tests/stability/02_research_chain.py` PASS |
| 5 Freeze | ✅ 2026-08-23 |

---

## V4.0 Research Agent

| Phase | 状态 |
|-------|------|
| 1 Design | ✅ `docs/DESIGN_V4_RESEARCH_AGENT.md` + SPEC §16 生效 + Decision 024 |
| 2 Implement | ✅ 三条 research 路由 + `data/research/` + 「研究一笔」 |
| 3 Smoke | ✅ `tests/smoke/12_research.py` PASS |
| 4 Stability | ✅ `tests/stability/01_research.py` PASS |
| 5 Freeze | ✅ 2026-08-23 |

---

## V3.0 AI Gateway — Phase 进度 (FROZEN 2026-08-22)

| Phase | 内容 | 状态 | 说明 |
|-------|------|------|------|
| Phase 0 | 环境/目录搭建 | ✅ DONE | Arc 驱动, oneAPI, venv |
| Phase 1 | 模型下载 + prompts/config/requirements | ✅ DONE | 模型 8.37GB 已就位 |
| Phase 1.5 | 安装 llama-cpp-python (CPU 后端) | ✅ DONE | 2026-08-02 CPU/AVX2 真实推理通过 |
| Phase 1.5b | SYCL GPU 后端 (Arc A770M) | ✅ DONE | F16=OFF; 全层卸载; 真推理 ~7 tok/s |
| Phase 2 | 核心代码 + 真实冒烟测试 | ✅ DONE | 白盒 10/10 + 全 6 端点真实推理通过 (CPU, 2026-08-02) |
| Phase 3 | Master 接口连接 | ✅ DONE | `/api/v1/ai/*` 代理; 离线 TM-1002 / 超时 TM-1004 |
| Phase 4 | Dashboard AI 入口 | ✅ DONE | AI Gateway 卡片 + Ask AI + 任务 AI 分析 |

> 说明: Phase 2 代码已实现并通过白盒测试 (`tests/test_whitebox.py`) 与 **全端点真实冒烟测试** (6/6 通过: health/models/chat/generate/describe/signal)。
> `llama-cpp-python 0.3.34` 已装入 venv (CPU/AVX2 后端); 真实加载 8.37GB Qwen2.5-14B-Instruct 模型, 6 个端点全部返回 HTTP 200。
> CPU 性能: 模型加载 10.2s, 推理 ~3.2 tok/s, chat(64 tokens) ~5.9s, generate(128 tokens) ~46s, 内存 ~10GB。
> 2026-08-22 Freeze: GPU 真推理通过 (`try_gpu_chat.py` + `POST /api/v1/ai/chat` HTTP 200, SYCL0=Arc A770M, ~7 tok/s)。启动用 `start_sycl.bat`。CPU 备用 `start_cpu.bat`。

---

## V3.0 AI Gateway — Phase 1.5 实际记录 (2026-08-02)

> 本段是 Phase 1.5 的真实操作日志 (FACT), 用于复现与后续 SYCL GPU 编译参考。

### 1. 阻塞根因 (比预期更深)

最初以为只需 `pip install llama-cpp-python`, 但逐步暴露三层阻塞:

1. **无预编译 wheel**: PyPI 无 `cp313-win_amd64` wheel, `pip` 退回 sdist 源码编译。
2. **Windows MAX_PATH (260)**: sdist 解压失败, 深层路径
   `vendor\llama.cpp\tools\ui\...\ChatAttachmentsListItemMcpPrompt.svelte` 超长。
   规避: 用 Python 把 sdist 解包到短路径 `D:\s\llama_cpp_python-0.3.34` (最深路径 ≈178 字符)。
3. **缺 C++ 构建工具链**: 环境原本无 MSVC (`cl`/`link`)、无 Windows SDK、无 cmake、无 git。
   oneAPI 2026.0 只提供 `icx`/`icpx`/`sycl-ls`, 但 DPC++ 在 Windows 上链接 C++ 仍需 MSVC + Windows SDK。
   → 用管理员权限安装 **Visual Studio Build Tools 2022** (Desktop C++ 工作负载):
   MSVC 14.44.35207 + Windows SDK 10.0.26100.0 + cmake 4.4 + ninja 1.13。

### 2. 构建命令 (已验证可用 — CPU 后端)

```bat
:: 需先初始化 MSVC 环境 (cmake/ninja/cl 才在 PATH)
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set TMP=C:\tmp & set TEMP=C:\tmp
cd /d D:\s\llama_cpp_python-0.3.34
"ai-gateway\.venv\Scripts\python.exe" -m pip install . --no-build-isolation
```

- venv 内已预装 `scikit-build-core 1.0.3` + `cmake 4.4.0` + `ninja 1.13.0` (PyPI 可达)。
- 结果: wheel `llama_cpp_python-0.3.34-py3-none-win_amd64.whl` (12MB) 编译并安装成功。
- 后端: CPU / AVX2 (CMake 检测到 `HAS_AVX2_1 - Success`); `n_gpu_layers=0` 时纯 CPU 推理。

### 3. SYCL GPU 编译失败 (Phase 1.5b 待解决)

尝试命令 (在 vcvars + setvars 环境下):

```bat
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
set CMAKE_ARGS=-DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_F16=ON
"ai-gateway\.venv\Scripts\python.exe" -m pip install . --no-build-isolation
```

CMake 配置阶段失败, 两处根因:

1. **编译器被覆盖**: scikit-build 选 `Visual Studio 17 2022` generator + MSVC,
   忽略 `-DCMAKE_C_COMPILER=icx`; SYCL 设备编译器 (DPC++) 未真正启用。
   → 需用 `-G Ninja` + 强制 Intel toolset, 而非 VS generator。
2. **MKL SYCL target 缺失**: 链接报错
   `Target "ggml-sycl" links to: MKL::MKL_SYCL::BLAS but the target was not found`。
   oneMKL 的 SYCL BLAS 导入目标未接好 (需 oneMKL SYCL Interfaces 或对应开关)。
   → 可能需要在 Windows 上调整 oneMKL 配置, 或显式关闭 SYCL 的 MKL BLAS。

配置日志关键行 (备查):
```
-- The C compiler identification is MSVC 19.44.35228.0        # icx 未生效
-- GGML_SYCL_TARGET=INTEL
-- Performing Test SUPPORTS_SYCL - Failed
-- Including SYCL backend
CMake Error: MKL::MKL_SYCL::BLAS target not found
```

### 4. 真实冒烟测试 (已通过)

`tests/smoke_real.py` — 实际加载模型并推理 (非 mock):

```bat
"ai-gateway\.venv\Scripts\python.exe" ai-gateway\tests\smoke_real.py
```

结果 (FACT):
- `/health` → 200; 网关启动即加载模型 (lifespan 内 `engine.load()`)。
- `POST /api/v1/ai/chat` → 200, 生成 23 tokens / 8.8s (CPU ~2.6 tok/s)。
- 模型自报身份为 **Qwen** (验证部署模型确为 Qwen2.5-14B-Instruct)。
- 第二次对话正常, `engine.stats` 累计正确 (`total_requests=2, total_tokens=55`)。

### 5. 下一步 (Phase 1.5b) — 2026-08-22 已完成编译

- [x] 修复 SYCL 编译: `-G Ninja` + `icx`; CMake `SUPPORTS_SYCL - Success`; `ggml-sycl.dll` 链接成功。
- [x] `llama-cpp-python 0.3.34` SYCL wheel 装入 venv (需 `TMP=C:\tmp\icx`)。
- [x] `config.yaml` 已是 `n_gpu_layers: -1`。
- [ ] 用 `start_sycl.bat` 重跑 `tests/smoke_real.py` 做 GPU 真实推理确认 (冻结前建议)。

复现命令:

```bat
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
set TMP=C:\tmp\icx & set TEMP=C:\tmp\icx
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_F16=ON -DGGML_SYCL_TARGET=INTEL
cd /d D:\s\llama_cpp_python-0.3.34
"D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway\.venv\Scripts\python.exe" -m pip install . --no-build-isolation --force-reinstall --no-deps
```

---

## V2.0 Factor Worker 增强

### 目标

将 Factor Worker 从 "15 只股票 + 3 维评分" 升级为 "50 只股票 + 15 因子 + 五维百分制评分 + 行业对比 + 分位数排名"。

### 当前 V1.0 对比

| 维度 | V1.0 | V2.0 |
|------|------|------|
| 股票池 | 15 只 (硬编码) | 50 只 (分行业) |
| 因子数量 | ~8 个 (ROE/PE/PB/MC/趋势/波动/流动性/评分) | 15 个 (完整多因子体系) |
| 评分维度 | 3 维 (价值+质量+规模) | 5 维 (价值+质量+动量+波动+流动性) |
| 评分范围 | 0-100 但分布不均 | 0-100 百分制，行业分位数对齐 |
| 行业对比 | 无 | 有 (行业内排名) |
| 分位数 | 无 | 有 (全市场 + 行业内) |
| 响应数据 | 简单 dict | 结构化多层 JSON |

---

### Phase 1: Design — 因子体系与评分模型

#### 1.1 完整因子清单 (15 个)

| # | 因子名 | 类型 | 计算公式 / 说明 | 权重 |
|---|--------|------|----------------|------|
| 1 | `roe` | 质量 | 净利润 / 净资产 × 100 | — |
| 2 | `roa` | 质量 | 净利润 / 总资产 × 100 | — |
| 3 | `pe` | 价值 | 股价 / 每股收益 | — |
| 4 | `pb` | 价值 | 股价 / 每股净资产 | — |
| 5 | `ps` | 价值 | 总市值 / 营业收入 | — |
| 6 | `dividend_yield` | 价值 | 每股股息 / 股价 × 100 | — |
| 7 | `market_cap_bn` | 规模 | 总市值 (亿元) | — |
| 8 | `revenue_growth` | 动量 | 营收同比增长率 (%) | — |
| 9 | `profit_growth` | 动量 | 净利润同比增长率 (%) | — |
| 10 | `roe_3y_avg` | 质量 | 近 3 年 ROE 均值 | — |
| 11 | `debt_ratio` | 风险 | 总负债 / 总资产 × 100 | — |
| 12 | `current_ratio` | 风险 | 流动资产 / 流动负债 | — |
| 13 | `momentum_60d` | 动量 | 近 60 日涨跌幅 (%) | — |
| 14 | `volatility_60d` | 风险 | 近 60 日收益率标准差 × √252 (年化) | — |
| 15 | `volume_ratio` | 流动性 | 近 5 日均量 / 近 20 日均量 | — |

#### 1.2 五维评分模型 (百分制)

```
总分 = 价值分(25) + 质量分(25) + 动量分(20) + 风险分(15) + 流动性分(15)
```

| 维度 | 权重(分) | 因子组合 | 评分逻辑 |
|------|----------|----------|----------|
| **价值** | 25 | PE + PB + PS + 股息率 | 行业分位数: PE 低→高分, PB 低→高分, 股息率高→高分 |
| **质量** | 25 | ROE + ROA + 3年ROE均值 + 营收增速 | ROE>15→满分, ROA>8→高分, 3年均值稳定加分 |
| **动量** | 20 | 利润增速 + 60日动量 | 增速>20%→满分, 60日正动量加分 |
| **风险** | 15 | 负债率 + 流动比率 + 60日波动率 | 负债率<50→高分, 流动比>1.5→高分, 波动率低→高分 |
| **流动性** | 15 | 量比 + 市值 | 量比 0.8-1.5→适中高分, 大市值流动性好加分 |

#### 1.3 行业分类

```python
SECTORS = {
    "白酒":   ["600519", "000858", "000568", "002304", "603369"],
    "银行":   ["600036", "000001", "601166", "601398", "601288"],
    "保险":   ["601318", "601628", "601601", "601336"],
    "医药":   ["600276", "603259", "000538", "300015", "300760"],
    "电子":   ["002475", "002371", "603986", "600183", "300661"],
    "新能源": ["300750", "002594", "601012", "600438", "002459"],
    "家电":   ["000333", "000651", "002032", "600690"],
    "消费":   ["603288", "002714", "600436", "603517", "300146"],
    "矿业":   ["601899", "600362", "601225", "000630"],
    "电力":   ["600900", "600886", "003816", "600905"],
    "科技":   ["002230", "688981", "603501", "688036"],
    "其他":   ["000002", "600048", "601668", "601319", "002027"],
}
```

#### 1.4 响应数据结构 (V2.0)

```json
{
  "success": true,
  "stock": "600519",
  "date": "20260731",
  "version": "2.0.0",
  "score": {
    "total": 82,
    "value": 18.5,
    "quality": 23.1,
    "momentum": 16.8,
    "risk": 12.0,
    "liquidity": 11.6,
    "grade": "A",
    "rank_market": 5,
    "rank_sector": 1,
    "total_stocks": 50,
    "sector_stocks": 5
  },
  "factors": {
    "roe": 30.12,
    "roa": 12.45,
    "pe": 28.5,
    "pb": 10.2,
    "ps": 9.1,
    "dividend_yield": 1.2,
    "market_cap_bn": 22000,
    "sector": "白酒",
    "name": "贵州茅台",
    "revenue_growth": 16.8,
    "profit_growth": 18.2,
    "roe_3y_avg": 29.5,
    "debt_ratio": 22.1,
    "current_ratio": 3.8,
    "momentum_60d": 5.3,
    "volatility_60d": 18.2,
    "volume_ratio": 1.1
  },
  "percentiles": {
    "market": {"roe": 95, "pe": 85, "pb": 92, "score": 90},
    "sector": {"roe": 80, "pe": 60, "pb": 75, "score": 85}
  },
  "calculation_time_ms": 1.2,
  "timestamp": "2026-07-31T12:00:00"
}
```

#### 1.5 评分等级

| 总分区间 | 等级 | 含义 |
|----------|------|------|
| 85-100 | S | 极度低估 / 强烈推荐 |
| 70-84 | A | 低估 / 推荐 |
| 55-69 | B | 合理 / 中性 |
| 40-54 | C | 偏高 / 谨慎 |
| 0-39 | D | 高估 / 回避 |

---

### Phase 2: Implement — 实现步骤

| # | 步骤 | 说明 | 预估 |
|---|------|------|------|
| 2.1 | 扩充 `STOCK_DB` | 从 15 只扩充到 50 只，按 12 个行业分类，每个因子数据补齐 | 1h |
| 2.2 | 新增因子计算函数 | 15 个因子各自的计算函数，全部基于确定性 hash 模拟 | 1.5h |
| 2.3 | 五维评分引擎 | `compute_score_v2()` 五维加权评分，输入因子 dict，输出总分+分项+等级 | 1h |
| 2.4 | 行业对比 | `compute_sector_rank()` 计算行业内排名百分比 | 0.5h |
| 2.5 | 分位数计算 | `compute_percentile()` 全市场 + 行业内双维度分位数 | 0.5h |
| 2.6 | 路由改造 | `/factor` POST 返回 V2.0 结构，`/factors` 返回完整 15 因子列表 | 0.5h |
| 2.7 | 兼容性 | 支持 `?v=1` 参数返回 V1.0 格式（向后兼容） | 0.5h |
| 2.8 | ThreadingMixIn | 同 Monitor Worker 修复，防止并发死锁 | 0.5h |

---

### Phase 3: Smoke Test — 冒烟测试

| # | 测试 | 方法 | 预期 |
|---|------|------|------|
| 3.1 | 健康检查 | `GET /health` | version=2.0.0, status=healthy |
| 3.2 | 因子列表 | `GET /factors` | 返回 15 个因子名 |
| 3.3 | 已注册股票-茅台 | `POST /factor {"stock":"600519","date":"20260731"}` | score.total>0, 5维分项之和=总分, grade∈{S,A,B,C,D} |
| 3.4 | 已注册股票-招行 | `POST /factor {"stock":"600036","date":"20260731"}` | sector="银行", 银行业内 rank_sector>0 |
| 3.5 | 未注册股票 | `POST /factor {"stock":"999999","date":"20260731"}` | 自动生成模拟数据, score>0 |
| 3.6 | 参数缺失 | `POST /factor {"stock":"600519"}` | 返回 400 错误 |
| 3.7 | 无效股票码 | `POST /factor {"stock":"abc","date":"20260731"}` | 返回 400 错误 |
| 3.8 | 分位数验证 | 已注册股票 | percentiles.market.score 为 0-100 整数 |
| 3.9 | V1.0 兼容 | `POST /factor {"stock":"600519","date":"20260731","v":"1"}` | 返回 V1.0 格式 |
| 3.10 | 响应时间 | `POST /factor` 50 次 | 平均 <20ms (含全量排名) |

---

### Phase 4: Stability Test — 稳定性测试

| # | 测试 | 方法 | 预期 |
|---|------|------|------|
| 4.1 | 连续 100 次查询 | 循环 100 次 `/factor` 不同股票 | 全部成功, 无崩溃 |
| 4.2 | 并发 10 路 | 同时 POST 10 个不同股票 | 全部返回, 无死锁 (ThreadingMixIn) |
| 4.3 | 大市值 + 小市值交替 | 快速切换极端股票 | 评分不越界, 全部 0-100 |
| 4.4 | 进程稳定性 | 运行 1 小时持续查询 | 无内存泄漏, 无异常日志 |
| 4.5 | 崩溃恢复 | kill 进程后重启 | 新进程正常响应 |

---

### Phase 5: Deploy — 部署

#### 部署清单

```bash
# 1. 杀旧进程
ssh("fuser -k 8080/tcp 2>/dev/null")

# 2. SFTP 上传新 server.py
sftp.put('factor-worker-v1/server.py', '/home/dji/factor-worker/server.py')

# 3. 启动
ssh("setsid python3 /home/dji/factor-worker/server.py > /tmp/factor.log 2>&1 &")

# 4. 健康检查
ssh("curl -s http://127.0.0.1:8080/health")

# 5. 冒烟测试
ssh("curl -s -X POST http://127.0.0.1:8080/factor -d '{\"stock\":\"600519\",\"date\":\"20260731\"}' -H 'Content-Type: application/json'")

# 6. Master 端到端
curl -X POST http://localhost:9000/task -H 'Content-Type: application/json' -d '{"worker_type":"stock-factor-worker","indicator":"factor","data":{"stock":"600519","date":"20260731"},"params":{}}'
```

#### 验证清单

- [ ] `GET /health` 返回 version=2.0.0
- [ ] `GET /factors` 返回 15 个因子
- [ ] `POST /factor` 50 只股票全部返回 score.total > 0
- [ ] 五维分项之和 == 总分
- [ ] grade 等级 S/A/B/C/D 正确映射
- [ ] 行业排名 rank_sector > 0
- [ ] 全市场排名 rank_market > 0
- [ ] percentiles 数值 0-100
- [ ] V1.0 兼容模式可用
- [ ] Master 端到端 POST /task COMPLETED
- [ ] Dashboard 提交 Factor 任务正常显示

---

## V2.1 Backtest Worker 增强

### 目标

在 V1.0 三个策略基础上新增 4 个策略，增加滑点/手续费模拟，增加夏普比率/Calmar 比率等高级指标。

### 新增策略

| # | 策略 | 类型 | 说明 |
|---|------|------|------|
| 1 | `TURTLE` | 趋势跟踪 | 海龟交易法: 20 日突破入场, 10 日突破出场, ATR 止损 |
| 2 | `GRID` | 震荡 | 网格交易: 固定价格间距买卖, 适合横盘 |
| 3 | `BOLLINGER` | 均值回归 | 布林带策略: 下轨买入, 上轨卖出, 带宽收缩后突破加仓 |
| 4 | `VWAP` | 量价 | VWAP 策略: 价格低于 VWAP 买入, 高于卖出, 量能确认 |

### 滑点 / 手续费模型

```python
# 请求 params 可选
{
  "slippage_bps": 5,       # 滑点 (基点, 1bps = 0.01%)
  "commission_bps": 10,    # 手续费 (基点)
  "initial_capital": 10000  # 初始资金
}

# 每笔交易成本 = 价格 × (slippage_bps + commission_bps) / 10000
```

### 新增高级指标

| 指标 | 说明 |
|------|------|
| `sharpe_ratio` | 夏普比率 (年化, rf=2%) |
| `calmar_ratio` | Calmar 比率 (收益 / 最大回撤) |
| `sortino_ratio` | Sortino 比率 (仅下行波动) |
| `profit_factor` | 盈亏比 (总盈利 / 总亏损) |
| `avg_trade_duration` | 平均持仓天数 |
| `equity_curve` | 资金曲线 (采样 50 点) |

### 验证

- [ ] 7 个策略全部通过冒烟测试
- [ ] 滑点/手续费正确扣减
- [ ] 高级指标计算正确
- [ ] equity_curve 返回 50 个采样点
- [ ] Master 端到端 COMPLETED
- [ ] Dashboard Backtest 预设正常

---

## V3.0 AI Gateway — 详细设计

> 详细设计文档: `V3_AI_GATEWAY_SPEC.md`

### 目标

在 Windows Master 上部署 Arc A770M 本地 LLM，提供投研报告/策略描述/信号解读能力。

### 推理框架

**llama-cpp-python + Intel Arc SYCL 后端** (GGUF 量化模型)

| 组件 | 选型 | 说明 |
|------|------|------|
| 推理框架 | llama-cpp-python | SYCL 后端支持 Intel Arc |
| 模型格式 | GGUF Q4_K_M | ~9GB VRAM |
| API 框架 | FastAPI (port 9100) | 与 Master API 一致 |
| 首选模型 | Qwen2.5-14B-Instruct Q4_K_M | 中文投研最佳 |

### 架构

```
Dashboard / Master API (port 9000)
    ↓ REST proxy
AI Gateway (port 9100, FastAPI)
    ↓ llama-cpp-python
Arc A770M (16GB VRAM, SYCL)
    ↓
投研报告 / 策略描述 / 信号解读 / 通用对话
```

### 目录结构

```
ai-gateway/
├── server.py          # FastAPI 入口 (单文件)
├── inference.py       # LLM 推理引擎封装
├── prompts.py         # Prompt 模板
├── config.yaml        # 配置
├── models/            # GGUF 模型文件
├── requirements.txt   # 依赖
└── tests/             # 测试
```

### API 端点

| 端点 | 说明 | 输入 | 输出 |
|------|------|------|------|
| `GET /health` | 健康检查 + GPU 状态 | 无 | GPU 信息/模型状态 |
| `GET /models` | 已加载模型列表 | 无 | 模型名称/状态 |
| `POST /api/v1/ai/generate` | 投研报告 | 因子+市场数据 | Markdown 报告 |
| `POST /api/v1/ai/describe` | 策略描述 | 回测结果 | 策略评估文本 |
| `POST /api/v1/ai/signal` | 信号解读 | 技术指标 | 信号分析 |
| `POST /api/v1/ai/chat` | 通用对话 | messages | 回复文本 |

### Phase 计划

| Phase | 名称 | 预估 | 说明 | 前置 | 状态 |
|-------|------|------|------|------|------|
| 0 | 环境准备 | 1天 | Arc 驱动 + oneAPI + Python 3.13 + venv 创建 | 无 | ✅ DONE |
| 1 | 模型下载 | 0.5天 | Qwen2.5-14B-Instruct GGUF (8.37GB) 下载到 models/ | P0 | ✅ DONE |
| 1.5 | 推理库安装 | 0.5天 | llama-cpp-python CPU 后端已装 + 真实推理通过 | P1 | ✅ DONE (CPU) |
| 1.5b | SYCL GPU 后端 | 0.5天 | Arc A770M GPU 加速 (oneAPI 工具链修复) | P1.5 | ✅ DONE |
| 2 | 核心实现 | 2天 | inference.py + server.py + 真实冒烟测试 | P1.5 | ✅ DONE |
| 3 | API 对接 | 0.5天 | Master proxy + Dashboard 集成 | P2 | ✅ DONE |
| 4 | 冒烟测试 | 0.5天 | 4 类端点逐个验证 | P3 | ✅ DONE |
| 5 | 性能调优 | 1天 | 延迟优化 + 缓存 | P4 | 待定 |
| 6 | 冻结 | 0.5天 | 文档 + CHANGELOG | P5 | 待定 |

**总预估: 6 天**

> **Phase 0 完成 (2026-07-31):**
> - Intel Arc A770M 驱动 32.0.101.8826 ✅
> - oneAPI 2026.0 已安装, `sycl-ls` 可见 Arc A770M ✅
> - Python 3.13.12 (Miniconda) + qwen-ai conda 环境 ✅

> **Phase 1 完成 (2026-08-01):**
> - GGUF 模型: `ai-gateway/models/qwen2.5-14b-instruct-q4_k_m.gguf` (8.37GB) ✅
> - venv 已建, fastapi/uvicorn/pydantic/pyyaml/huggingface-hub 已装 ✅
> - prompts.py / config.yaml / requirements.txt / tests/test_server.py 已完成 ✅
> - llama-cpp-python **已安装 (0.3.34, CPU/AVX2 后端)** ✅ (SYCL GPU 后端见 Phase 1.5b)
> - server.py / inference.py / models.py **已实现 + 白盒/真实测试通过** ✅

### 关键风险

| 风险 | 缓解 |
|------|------|
| SYCL 编译失败 | 备选 OpenVINO 或 CPU fallback |
| VRAM OOM | 更小量化 Q3_K_M 或换 7B 模型 |
| 延迟过高 (>5s) | 换 7B 模型 + 缓存 |

### 前置条件

- [ ] V2.1 Freeze ✅
- [ ] Arc A770M 驱动安装
- [ ] oneAPI Runtime 安装
- [ ] Python 3.11+ 环境
- [ ] Qwen2.5-14B GGUF 模型下载

---

## V4.0 Research Agent (概要)

### 目标

AI 自动扫描市场数据，发现异常模式，生成交易策略假设，回测验证，输出可执行建议。

### 工作流

```
1. 定时扫描 (每小时)
   → Indicator Worker: 技术指标异动检测
   → Factor Worker: 因子评分突变检测

2. 异常发现
   → RSI 超卖 + 因子评分 A 级 = 买入信号候选

3. 策略生成
   → AI Gateway: 基于异常生成策略参数

4. 回测验证
   → Backtest Worker: 自动回测新策略

5. 输出报告
   → Dashboard 展示 + 可选推送通知
```

### 前置条件

- V3.0 Freeze
- 至少 30 天历史数据积累
- AI Gateway 稳定运行

---

## V5.0 MT5 Bridge (概要)

### 目标

将 Research Agent 产出的交易信号通过 MetaTrader 5 API 执行实盘交易。

### 架构

```
Research Agent 信号
    ↓ REST POST /api/v1/bridge/signal
MT5 Bridge (Windows, port 9200)
    ↓ MetaTrader 5 Python API
MT5 终端 → 交易所执行
    ↓
持仓管理 / 止损止盈 / 资金管理
```

### 核心功能

| 功能 | 说明 |
|------|------|
| 信号接收 | REST API 接收买卖信号 |
| 风控检查 | 仓位限制 / 单笔金额限制 / 日亏损限制 |
| 订单执行 | MT5 API 下单 (市价/限价/止损) |
| 持仓管理 | 查询持仓 / 平仓 / 修改止损止盈 |
| 资金曲线 | 实时资金曲线推送 Dashboard |

### 前置条件

- V4.0 Freeze
- MT5 终端安装 + 账户配置
- MT5 Python API (`MetaTrader5` 包, 仅 Windows)
- 至少 3 个月模拟盘验证

---

## 稳定性测试报告 (2026-07-31 完成)

| # | 测试 | 结果 | 详情 |
|---|------|------|------|
| 1 | 连续 100 次 RSI 调度 | **PASS** | 100/100 COMPLETED, 平均 61.3ms/task, 任务ID连续 |
| 2 | 4 Worker 并发提交 | **PASS** | Indicator/Factor/Backtest/Monitor 同时提交全部 COMPLETED, 无死锁 |
| 3 | Worker 崩溃恢复 | **PASS** | kill→1s内检测OFFLINE→TM-1002→重启→1s内恢复ONLINE→COMPLETED |
| 4 | 长时间运行 24h | **待运行** | 脚本 test-longrun.py 已就绪, 需手动启动 |
| 5 | 网络中断恢复 | **未测试** | 需 iptables 操作, 暂跳过 |

### 测试详情

**1.1 连续 100 次 RSI**
- 全部 COMPLETED, 0 FAILED
- 总耗时 6128ms, 平均 61.3ms/task
- 任务 ID: tm-task-20260731-000121 ~ 000220 (连续)

**1.2 四 Worker 并发**
- Indicator-RSI: COMPLETED (3138ms)
- Factor-600519: COMPLETED (77ms)
- Backtest-EMA: COMPLETED (2120ms)
- Monitor: COMPLETED (8430ms)
- Wall time: 8432ms (受 Monitor 最慢限制)

**1.3 崩溃恢复 (Xavier-02 Factor Worker)**
- Kill: fuser -k 8080/tcp → PID 31140 killed
- 检测 OFFLINE: 1 秒
- 提交任务: TM-1002 "Worker for type 'stock-factor-worker' is offline"
- 重启: setsid python3 server.py → 健康检查通过
- 恢复 ONLINE: 1 秒
- 恢复后任务: COMPLETED (tm-task-20260731-000230)

---

## 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-31 | V1.0-V1.3 | 全部冻结, V2.0 设计完成 |
