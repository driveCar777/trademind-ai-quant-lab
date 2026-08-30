# TradeMind AI Quant Lab — AI Agent Context Document

> **版本:** V1.0  
> **更新时间:** 2026-08-30 (V9 Master Backtest IN PROGRESS：现有数据统一回测；PURCHASE=NO；$0；Level=0；Candidate=0)  
> **用途:** AI Agent 最高优先级上下文文件。  
> **读取顺序:** TRADEMIND_CONTEXT.md → AGENTS.md → TODO.md → PROJECT_VISION.md → 代码

---

## 核心规则

**AI Agent 必须严格区分：**

| 标记 | 含义 | 说明 |
|------|------|------|
| **FACT** | 已确认事实 | 硬件配置、网络结构、软件版本等客观事实 |
| **DONE** | 已完成功能 | 已实现、已测试、已部署的功能 |
| **IN PROGRESS** | 当前开发 | 正在进行的工作 |
| **TODO** | 未来规划 | 计划中但尚未开始的工作 |
| **UNKNOWN** | 未验证假设 | 不确定或未验证的信息 |

**禁止：**
1. 不允许把 TODO 描述为已经完成
2. 不允许创造不存在的硬件
3. 不允许修改真实网络结构
4. 不允许假设测试通过
5. 不允许补充不存在的代码
6. 不允许把「愿景文档」当「运行状态文档」

---

## 1. 项目简介

TradeMind AI Quant Lab 是一个个人本地化 AI 量化研究平台。

**目标：** 利用已有硬件构建 A 股研究、MT5 外汇研究、策略回测、本地 AI 分析系统。

**最终目标：** 数据 → 指标计算 → 因子分析 → 策略回测 → AI 分析 → 交易辅助

**注意：** TradeMind 当前不是商业交易系统，当前定位是个人研究实验平台。

---

## 2. 硬件真实信息 (FACT)

### 2.1 Master 主机

| 项目 | 详情 |
|------|------|
| 设备 | Windows 蝰蛇峡谷 |
| CPU | Intel Core i7-12H |
| GPU | Intel Arc A770M |
| 显存 | 16GB |
| 内存 | 32GB DDR4 |
| 用途 | Master API, Dashboard, AI Gateway, 本地 LLM 推理 |
| 状态 | ONLINE |

### 2.2 Jetson AGX Xavier 集群

**共有 4 台。不是 Xavier NX。统一名称：Jetson AGX Xavier Cluster。**

| 项目 | 详情 |
|------|------|
| 架构 | ARM64 |
| Python | 3.6.9 |
| 限制 | 无法方便联网, 无法 pip 安装大量依赖, 无法 apt 安装, Docker Hub 不可直接使用 |

**Worker 设计原则：** Python 标准库优先, 单文件 server.py, SCP 部署。

### 2.2.1 Xavier-01

| 项目 | 详情 |
|------|------|
| IP | 192.168.1.200 |
| 角色 | Indicator Worker |
| 功能 | 技术指标计算 (SMA/EMA/RSI/MACD) |
| 状态 | DONE |

### 2.2.2 Xavier-02

| 项目 | 详情 |
|------|------|
| IP | 192.168.1.201 |
| 角色 | Factor Worker |
| 功能 | A 股因子计算 (50 只股票, 15 因子, 五维评分) |
| 状态 | DONE |

### 2.2.3 Xavier-03

| 项目 | 详情 |
|------|------|
| IP | 192.168.1.202 |
| 角色 | Backtest Worker |
| 功能 | 策略回测 (7 策略, 滑点手续费, 高级指标) |
| 状态 | DONE |

### 2.2.4 Xavier-04

| 项目 | 详情 |
|------|------|
| IP | 192.168.1.203 |
| 角色 | Monitor Worker |
| 功能 | 集群监控 |
| 状态 | DONE |

---

## 3. 当前网络结构 (FACT)

```
Windows Master (192.168.1.101)
    |
    | REST API (port 9000)
    | AI Gateway (port 9100)
    |
Jetson AGX Xavier Cluster
    |
    +-- Xavier-01 (192.168.1.200) -- Indicator Worker
    +-- Xavier-02 (192.168.1.201) -- Factor Worker
    +-- Xavier-03 (192.168.1.202) -- Backtest Worker
    +-- Xavier-04 (192.168.1.203) -- Monitor Worker
```

---

## 4. 软件架构 (FACT)

```
Dashboard
    |
Master API (port 9000)
    |
REST Task Dispatch
    |
    +-- Xavier-01 Indicator
    +-- Xavier-02 Factor
    +-- Xavier-03 Backtest
    +-- Xavier-04 Monitor

AI Gateway (port 9100)
    |
Local LLM (Arc A770M)
```

---

## 5. 已完成版本 (DONE)

### V1.0 Worker Template
- Worker 规范, FastAPI 模板, API 生命周期, 健康检查
- 状态: DONE

### V1.1 Master 通信
- Master 注册 Worker, 调度任务, 获取结果
- 状态: DONE

### V1.2 Master 增强
- Worker 健康检测, 超时, 自动重试
- 状态: DONE

### V1.3 Dashboard
- Worker 状态, 任务查看
- 状态: DONE

### V2.0 Factor Worker
- 50 只股票, 15 因子, 五维评分 (价值/质量/动量/风险/流动性)
- 状态: DONE

### V2.1 Backtest Worker
- 7 策略: EMA_MACD, RSI, SMA_CROSS, TURTLE, GRID, BOLLINGER, VWAP
- 支持: 滑点, 手续费, Sharpe, Sortino, Calmar, Equity Curve
- 状态: DONE

---

## 6. 当前开发 (IN PROGRESS)

### V3.0 AI Gateway

**状态:** DONE / FROZEN (2026-08-22)

**目标:** 在 Windows Master 运行本地 LLM。

**硬件:** Intel Arc A770M

**模型:** Qwen2.5-14B-Instruct, GGUF Q4_K_M, 约 8.37GB

**已完成 (DONE):**
- [x] Arc 驱动安装
- [x] oneAPI 安装
- [x] sycl-ls 识别 GPU
- [x] Python 环境
- [x] GGUF 模型下载
- [x] prompts.py
- [x] config.yaml
- [x] requirements.txt

**已完成 (本轮 DONE — 2026-08-02):**
- [x] inference.py — LLM 推理引擎封装 (lazy import, 优雅降级, 统计)
- [x] models.py — Pydantic 请求/响应模型
- [x] server.py — FastAPI 服务 (6 端点, /health 降级可用)
- [x] tests/test_whitebox.py — 白盒测试 (10/10 passed, 无需 GPU)
- [x] llama-cpp-python 0.3.34 装入 venv (**CPU/AVX2 后端**; 需先装 VS Build Tools 2022 提供 MSVC/WinSDK)
- [x] tests/smoke_real.py — **真实冒烟测试通过**: 实际加载 8.37GB Qwen 模型, `/api/v1/ai/chat` 返回 HTTP 200 并生成真实中文回复, 模型自报 Qwen

**已完成 (2026-08-22):**
- [x] Phase 1.5b: SYCL GPU 后端编译 — Ninja + icx, `ggml-sycl.dll` 已链, SYCL wheel 已装入 venv
- [x] Master 接口连接 — `/api/v1/ai/*` 代理
- [x] Dashboard AI 入口 — 卡片 + Ask AI + 任务 AI 分析

**已完成 (2026-08-22 晚 — GPU 真推理 + Freeze):**
- [x] SYCL 推理通过: 设备 `SYCL0 Intel Arc A770M`, `n_gpu_layers=-1`, `GGML_SYCL_F16=OFF`
- [x] 独立脚本 `try_gpu_chat.py` + 网关 `POST /api/v1/ai/chat` 均 HTTP 200, 生成约 7 tok/s
- [x] V3.0 Freeze

**已完成 (2026-08-23 — V4.0 Phase 2/3):**
- [x] `POST/GET /api/v1/research*` + `data/research/` + 控制台「研究一笔」
- [x] Smoke 12 PASS（`tm-research-20260823-000001`，EURUSD RSI 76.1，已问通义千问）

**已完成 (2026-08-23 — V4.0 Freeze):**
- [x] Phase 4 Stability：`tests/stability/01_research.py` PASS（10 次、不双开 14B、503/`ai_skipped`）
- [x] Phase 5 Freeze

**已完成 (2026-08-23 — V4.1 Freeze):**
- [x] 可选 `chain` 最多两步；「因子后再回测」
- [x] Smoke 13 + Stability 02 PASS

**已完成 (2026-08-23 — V5.0 Freeze):**
- [x] 人手确认模拟纸质单；本机 MT5 探测为 demo 仍不发单
- [x] Smoke 14 + Stability 03 PASS（`tm-order-20260823-000003` EURUSD SELL）

**已完成 (2026-08-23 — V6.0 Freeze):**
- [x] 先 preview 再确认；`GET /api/v1/desk/today`
- [x] Smoke 15 + Stability 04 PASS

**已完成 (2026-08-24 — V7.0 Freeze):**
- [x] 指标研究读 `data/samples/eurusd.csv`；`GET /api/v1/samples`
- [x] Smoke 16 + Stability 05 PASS

**已完成 (2026-08-24 — V8.0 Freeze):**
- [x] 因子 `moutai.csv`、回测 `xauusd.csv`；`GET /samples` 带 kind
- [x] Smoke 17 + Stability 06 PASS

**未完成:**
- [ ] 向 MT5 发单（你已否决，保持纸质单）
- [ ] 把 K 线/因子表也从本机文件喂给 Worker（板上仍用内置库）

---

## 7. V3.0 目录 (FACT)

```
ai-gateway/
├── server.py          # DONE (白盒测试通过)
├── inference.py       # DONE (白盒测试通过)
├── prompts.py         # DONE
├── config.yaml        # DONE
├── requirements.txt   # DONE
├── models/            # DONE (模型已下载)
└── tests/             # DONE (测试用例已写)
```

---

## 8. 当前阻塞问题 (FACT)

**无运行阻塞。** 当前交付后端 = Arc A770M SYCL (`start_sycl.bat`)。CPU 为备用 (`start_cpu.bat` + 重编 CPU wheel)。

本机一键：`start_all.bat`（2026-08-22 实测 `LOCAL_START_PASS`）。  
Xavier 四台一键：`start_xavier.bat`（01 Docker，02/03/04 `server.py`；已健康则跳过）。

Worker 对外端口 (FACT, Master `data/workers.json`):
- Xavier-01 Indicator `192.168.1.200:8080`
- Xavier-02 Factor `192.168.1.201:8080`
- Xavier-03 Backtest `192.168.1.202:8002`（板上代码写死 8002，不是 8080）
- Xavier-04 Monitor `192.168.1.203:8080`

已知事实:
- `GGML_SYCL_F16=ON` 时 uvicorn 推理曾 Abort (`3221226505`)。
- `F16=OFF` + `n_gpu_layers=-1` + `n_batch=512` + `flash_attn=False` 已验证可对话。
- 启动必须 `setvars.bat`。不要设 `ONEAPI_DEVICE_SELECTOR=level_zero:gpu:0` (会在 `llama_backend_init` 抛 0xe06d7363)。

---

## 9. 未来规划 (TODO)

### V4.0 Research Agent
- **FROZEN 2026-08-23**：一次研究 = 1 次计算 + 至多 1 次 AI；人手点「研究一笔」
- 实现：`master/api/app/service/research_service.py` + 控制台按钮；SPEC §16 已冻结

### V4.1 研究加力
- **FROZEN 2026-08-23**：可选 `chain` 最多 2 步；人手点「因子后再回测」

### V5.0 模拟纸质单
- **FROZEN 2026-08-23**：人手 `confirm=true` → `data/orders/`。禁止 `order_send`。

### V6.0 今日台账
- **FROZEN 2026-08-23**：先看拟单；`GET /api/v1/desk/today`。仍不发 MT5。

### V7.0 本机样本
- **FROZEN 2026-08-24**：指标研究读 `data/samples/`。不是行情。

### V8.0 因子 / 回测样本
- **FROZEN 2026-08-24**：`moutai.csv` / `xauusd.csv`。不改 Worker。

### V9.0 MT5 模拟盘
- **FROZEN 2026-08-24**：Master 拉本机 MT5 M15，Xavier 只算 `{symbol, close}`。人手确认后 demo 才 `order_send`。实盘拒绝。
- 冒烟用假终端 + `TRADEMIND_MT5_SEND=0`。同花顺：UNKNOWN，没有可测官方接口。

### V10.0 测通模拟盘
- **FROZEN 2026-08-24**：RSI 中性可人手 `side=BUY/SELL` 测 0.01 手。不是预测有效。

### V11.0 MT5 证伪回测
- **FROZEN 2026-08-24**：MT5 日线 70/30 + 风控。`survived` ≠ 年化保证。Xavier 回测 2.1.1 吃 `close[]`。
- V11.1：紫色按钮「黄金 MT5 证伪回测」。旧「黄金回测」改名「黄金CSV样本」。D1 不足则改 H4/H1。
- V11.3：网关只读 `context.result`。证伪有 verdict 不再问模型，按数字写解读。D/0 笔是接线，不是策略没成交。
- V11.4：仓库没有整段 GOLD 行情。MT5 拉 K 线时留 `time`；Worker 2.1.2 回买卖点；控制台出成交表。旧 28/12 那笔没有明细。
- V11.5：连续切分（切分不强平）。冻结参数策略篮对照，不按样本外调参。Worker 2.1.3。
- V11.6：涨/跌/震分段。上涨均线、震荡布林、下跌空仓。不用张量训练。Worker 2.1.4。
- V11.7：四台 8002 并行回测。12 组候选只按样本内打分，样本外只验选中组。
- **证伪实验室已收口（2026-08-25）：** 见 `docs/PHASE_FALSIFY_LAB.md` 与 `data/mine/longrun/V11_7_FREEZE_CLOSEOUT.md`。不要再开 `mine_longrun` / `mine_is_only`。
- **Data Layer V0.1 FROZEN 2026-08-25：** 独立只读行情层，见 `docs/DATA_LAYER_V0.1.md`。数据在 `data/market/`，不进 V11.7。Xavier 不参与采集。`FINAL_OOS_LOCKED=false`。
- **Data Qualification V0.1 FROZEN 2026-08-25：** 四台 Xavier 一次性画像 16 个 dataset。见 `docs/DATA_QUALIFICATION_V0.1.md`。GOLD M15 跨节点 PASS。OIL D1 需人工看极端日收益。不锁 Final OOS。
- **Research Readiness V0.2 FROZEN 2026-08-25：** 每份 20 次重复 + 分块/滚动/故障注入。340 次 full profile 全同。GOLD M15 跨节点 PASS。快照仅最后一根变化。见 `docs/RESEARCH_READINESS_V0.2.md`。
- **Research Protocol V0.3 FROZEN 2026-08-25：** 因果沙箱 + 泄漏哨兵 + 实验治理。16 份 CANDIDATE 窗口（UTC）。四台各 10 次 feature/window/leakage，交叉 4 组 PASS。未锁 Final OOS。未重跑 V11.7 / GOLD M15 RSI。见 `docs/RESEARCH_PROTOCOL_V0.3.md`。
- **HYP-0001 FACT 2026-08-26：** 14:11 锁定 `FAM-MOMENTUM-0001` / A+B hash 未改。合同权威已修复。48 formal jobs 四台跑完，交叉 4/4 PASS。Family rollup=WEAK_SUPPORT，不是交易许可，不是年化 10%。见 `docs/research_engine/HYP-0001_EXECUTION_RESTORATION.md`。
- **Factor Discovery V0.1 FACT 2026-08-26：** 新搜索合同，不是 HYP-0001 调参。57 candidates / 17 Xavier jobs / FDR 876 tests / 0 discoveries。结果 `NO_USEFUL_FACTORS_FOUND`。见 `docs/research_engine/FACTOR_DISCOVERY_V0.1_REPORT.md`。
- **Research Engine V0.5 FACT 2026-08-26：** Market State + 15 sketches，`NO_USEFUL_STRATEGIES_FOUND`。见 `docs/research_engine/RESEARCH_ENGINE_V0.5_REPORT.md`。
- **Profit Discovery V0.6 FACT 2026-08-26：** 四 Xavier 16 jobs，NEXT_BAR_OPEN + 5bp/10bp + 风险。`WEAK_EDGE_ONLY`，程序级 CANDIDATE=0。OIL D1 动量单市场过门，D1 CAGR≈0.2%，不是 10%。M15/H1 2000 根不够估年化。见 `docs/research_engine/PROFIT_DISCOVERY_V0.6_REPORT.md`。不要 MT5，不要调参。
- **Alpha Discovery V0.7 DESIGN 2026-08-26：** 只审计、只设计，无代码、无新实验。单品种短持有已测败。下一最可能赚钱方向：跨品种 D1（`FAM-FD-XASSET-0001` 仍是 DRAFT）。见 `docs/research_engine/ALPHA_DISCOVERY_V0.7_PLAN.md`。不要实现五条方向，不要 MT5。
- **Alpha OS V0.7.1 DESIGN 2026-08-26：** 分类 + 覆盖矩阵 + 12 个月队列。见 `docs/research_engine/ALPHA_OPERATING_SYSTEM_V0.7.1.md`。
- **Cross Asset V0.8 FROZEN 2026-08-26：** 四 Xavier 已跑。结果 **`NO_CANDIDATE`**，3/3 **FALSIFIED**，FDR 0/3。不要第 4 条，不要回头调 XA。见 `CROSS_ASSET_ALPHA_V0.8_REPORT.md`。
- **Alpha Map V1 DESIGN 2026-08-26：** 覆盖/数据/排序/12 个月路线已写。Carry/IV/新闻/订单流 = DATA BLOCKED，不是 TODO。下一刀 = Regime Transition。见 `ALPHA_COVERAGE_MAP_V1.md` 与 `TRADEMIND_ALPHA_ROADMAP_12M.md`。
- **Regime Transition V0.9 FROZEN 2026-08-27：** 已实现 + 四 Xavier。hash 未改。结果 **`NO_CANDIDATE`**（0001 FALSIFIED；0002/0003 INCONCLUSIVE；FDR 0/3）。01=04 hash `31995464…249b8`。不要调 ADX/hold/VOL。见 `REGIME_TRANSITION_V0.9_REPORT.md`。
- **Cross Residual V0.91 FROZEN 2026-08-27：** 已跑。hash 未改。结果 **`NO_CANDIDATE`**。不要调 SMA60。见 `CROSS_RESIDUAL_V0.91_REPORT.md`。
- **Alpha Program V1.0 2026-08-27：** 机器 Universe + 机制分类器 + 数据探针。策略层 BLOCKED。认证 CAGR=无。单元 **149 PASS**。
- **ALPHA_PROGRAM_V1 DESIGN 2026-08-26：** 全仓盘点、机制库 V2、优先级 V2、路线 V2、验收门、失败知识库。Level 1=0。CAGR≥10% 不是 Level 1 门。
- **Alpha Pipeline 2026-08-26：** 52 机制题打分（live=29）。簇：RT 1600 / Residual 576 / Calendar 540。两簇现已跑败。
- **Alpha Recovery V1.0 FACT 2026-08-27：** 失败分析系统已落地。覆盖：direction 83% / RV 40% / transition 50% / risk premium 0% / event 0% / institutional time 0%。主因 **A**（无可用预测信息）。选出 **一个** 新家族：`INSTITUTIONAL_TIME_V1.0`（month-end/start，不是 weekday）。hash `1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457`。当时未执行。
- **Alpha Mission V1.1 FACT 2026-08-28 STOP B：** IT 已跑（WEAK_EDGE，FDR 0/3，四 Xavier 01=04）。随后 Time Structure / Microstructure Surprise / Regime Interaction / Alt Market Structure 全部 **NO_CANDIDATE / FALSIFIED**。Level 仍 0。Candidate=0。GOLD/OIL D1 最大 **7.715y**（BROKER_LIMITATION，2018-12-12）。新 H1 约 7.7y 已冻成 `20260828-000001`。不要调参救 IT/TS/MS/RI/AMS。不要读 Final OOS。见 `ALPHA_MISSION_V1.1_REPORT.md`。
- **Alpha Research Mission V2.0 FACT 2026-08-28 STOP B：** 信息集已扩大并测完当时无密钥公开源。IMPLIED_VOL / POSITIONING / INVENTORY / RATES / CARRY_V1A 全部 **NO_CANDIDATE**，四 Xavier，01=04。CARRY_V1 是 INVALID_ALIGNMENT（1971 FX 窗口早于 €STR），不是机制结论。Level 仍 0。Candidate=0。不要调 IV/COT/EIA stocks/UST10/overnight z_cut。不要读 Final OOS。见 `ALPHA_RESEARCH_MISSION_V2_REPORT.md`。
- **Data Expansion Mission V3.0 FACT 2026-08-28 WAIT_HUMAN：** 数据工厂已落地。EIA 产量+开工率已冻成新 ID 并跑 SUPPLY_V1（hash `4f6548b3…b16f1`）四 Xavier **NO_CANDIDATE**。不是库存重包装。指数 IV ≠ option surface。CFD ≠ futures curve。花费 $0。见 `DATA_EXPANSION_MISSION_V3_REPORT.md`。
- **MT5 Max Mission V4.0 FACT 2026-08-29 COMPLETE_NO_CANDIDATE：** 2000 bars 不是上限。`maxbars=100000`。新 ID 冻了 SILVER/DXY/额外 FX/指数/H1/M15（约 59 个 `MT5_MAX_V4` 集）。未覆盖 `20260825`。CROSS_METAL_V1 hash `ef6f3633…780df8` 与 USD_METAL_V1 hash `a39952f9…474f0b` 四 Xavier **NO_CANDIDATE**，01=04。VIX 1.45y 未冻。不要再调 gold-silver / DXY / EIA z_cut。见 `MT5_MAX_MISSION_V4_REPORT.md`。
- **Market Universe V5.1 FACT 2026-08-29 EXTERNAL_DATA_GATE：** 841/841 全是 CFD。期权 0。真期货 0。新冻农业/US2000 `20260829-000001`。BREADTH_V1 **WEAK_EDGE**；SIZE_SPREAD_V1 **NO_CANDIDATE**；四 Xavier 01=04。不要调参。不要再做股票 CFD breadth 克隆。曲线/期权面才是下一信息。不覆盖 `20260825`/`20260828`。
- **Market Universe V5.0 FACT 2026-08-29：** START pointer `d29d3b7388b7d09f4951f8901d7745371be30ab6`。Top 5（XS/CS/ER/VT/IA）已跑完，全部 NO_CANDIDATE。不改 V4 合同。
- **V8 Information Fusion FACT 2026-08-30 STOP C：** 已有 110 集融合 TOP5 已跑（FUT_CFD_LEAD / CURVE_OI_JOINT / OI_COT_BUILD / CURVE_EIA_REPRICE / CURVE_REALYIELD）。四 Xavier，01=04。Candidate=0。FDR 0/15。不要调 gap/steepening/OI/wow/yield。见 `V8_DECISION.md`。
- **V8.2 Options Due Diligence FACT 2026-08-30 QUOTE ONLY：** `GC.OPT`/`CL.OPT` 不存在。真实父符号是 `OG.OPT` / `LO.OPT`。GLBX 无 venue IV。见 `OPTIONS_PURCHASE_DECISION_V8_2.md`。
- **V8.3 Options Feasibility FACT 2026-08-30：** 8 日样本。见 `OPTIONS_MVD_DECISION_V8_3.md`。
- **V8.4 Full-Year Occupancy FACT 2026-08-30 PURCHASE=NO：** 251 个 Pack E 交易日。只 `get_record_count`。门槛事先锁死 A= ATM≥90/skew≥75/term≥75。**LO = A**（ATM/skew 100%，term 98.0%，ATM 连续 251 日）。**OG = B**（ATM 98.4%，skew 80.1%，term 74.9%；期货近月=期权近月 **0%**）。父级月度 ohlcv 全年都有量，不是单月堆出来的。MVD-B 对 coverage 不必需。本任务不买。若以后买一包：**LO 1Y MVD-A $11.99**。Credits ≈ $93。见 `OPTIONS_PURCHASE_DECISION_V8_4.md`。
- **V9 Master Backtest IN PROGRESS 2026-08-30：** 现有数据 / 现有机制统一 MT5 成本后回测。不买数据。不新假设。HYP-0001 = PREDICTIVE_ONLY。$93 = UNUSED_RESEARCH_RESERVE。见 `V9_START.md`。

---

## 10. AI Agent 行为规则

### 事实优先
如果文档没有说明, 回答: "当前没有确认"。不要猜。

### 状态标记规则
- **DONE:** 已经完成并验证
- **IN PROGRESS:** 正在开发
- **TODO:** 计划
- **UNKNOWN:** 未知

### 禁止幻觉
禁止输出: 不存在的代码, 不存在的 API, 不存在的测试结果, 不存在的硬件, 虚假的完成状态。

### 修改代码前必须确认
1. 当前文件是否存在
2. 当前版本是什么
3. 是否影响已有 Worker
4. 是否符合 Python 版本限制

---

## 11. 当前下一步任务

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | Phase 1.5b: SYCL GPU 后端 (Arc A770M) | DONE (编译+安装; GPU 真实推理待重跑) |
| P1 | 完成 AI Gateway 基础 API (含真实测试) | DONE |
| P2 | 连接 Master | DONE |
| P3 | Dashboard 增加 AI 入口 | DONE |
| P4 | GPU 真推理 (Arc A770M SYCL, F16=OFF) | DONE |
| P5 | V3.0 Freeze | DONE |
| P6 | 本机一键启动 + 拉起 Xavier-02/03/04 | DONE (2026-08-22) |
| P7 | 控制台运维按钮 + 桌面一键提示 | DONE (2026-08-22；色板按设计说明，不用酒红) |
| P8 | 默认计算路径 + 详情带结果给 AI | DONE (2026-08-23；Smoke 07 PASS) |
| P9 | Xavier-01 纳入四台同等启动 | DONE (2026-08-23；Smoke 08 PASS) |
| P10 | 一键状态以 HTTP 健康为准 | DONE (2026-08-23；Smoke 09 PASS) |
| P11 | 算完后明确「用这笔数字问 AI」 | DONE (2026-08-23；Smoke 10 PASS) |
| P12 | 通义千问单路推理 / 长度上限 | DONE (2026-08-23；Smoke 11 PASS；网关需再启才加载锁) |
| P13 | V4.0 Phase 1 Design | DONE (2026-08-23) |
| P14 | V4.0 Phase 2/3 实现 + Smoke 12 | DONE (2026-08-23) |
| P15 | V4.0 Phase 4/5 稳定 + 冻结 | DONE (2026-08-23) |
| P16 | V4.1 两步研究五阶段 | DONE (2026-08-23 Freeze) |
| P17 | V5.0 模拟纸质单五阶段 | DONE (2026-08-23 Freeze) |
| P18 | V6.0 今日台账五阶段 | DONE (2026-08-23 Freeze) |
| P19 | V7.0 本机样本 CSV | DONE (2026-08-24 Freeze) |
| P20 | V8.0 因子/回测本机样本 | DONE (2026-08-24 Freeze) |
| P21 | V9.0 MT5 模拟盘（人手确认后进终端） | DONE (2026-08-24 Freeze；假终端冒烟) |
| P22 | V10.0 人手选方向测通 | DONE (2026-08-24 Freeze；Smoke 19) |
| P23 | V11.0 MT5 证伪回测 | DONE (2026-08-24 Freeze；Smoke 20) |
| P24 | V11.3 证伪解读接线 | DONE (2026-08-24；Smoke 20 白盒) |
| P25 | V11.4 成交明细 | DONE (2026-08-24；Xavier 2.1.2；Smoke 20) |
| P26 | V11.5 连续切分 + 策略篮 | DONE (2026-08-24；Xavier 2.1.3；Smoke 21) |
| P27 | V11.6 行情分段 | DONE (2026-08-24；Xavier 2.1.4；Smoke 21) |
| P28 | V11.7 四台并行样本内筛选 | DONE (2026-08-24；四台 8002；Smoke 21) |
| P29 | Data Layer V0.1 不可变行情层 | DONE (2026-08-25；16 组合只读抓取；不接 V11.7) |
| P30 | Data Qualification V0.1 四节点画像 | DONE (2026-08-25；16 profile + 跨节点 PASS；不锁 OOS) |
| P31 | Research Readiness V0.2 深度稳定性 | DONE (2026-08-25；340 repeats PASS；不锁 OOS) |
| P32 | Research Protocol V0.3 因果研究协议 | DONE (2026-08-25；四台 10-repeat + 交叉 PASS；不锁 OOS) |
| P33 | HYP-0001 正式实验（14:11 锁定） | DONE (2026-08-26；WEAK_SUPPORT；不是交易许可) |
| P34 | Factor Discovery V0.1 | DONE (2026-08-26；`NO_USEFUL_FACTORS_FOUND`) |
| P35 | Research Engine V0.5 Strategy Discovery | DONE (2026-08-26；`NO_USEFUL_STRATEGIES_FOUND`) |
| P36 | Profit Discovery V0.6 | DONE (2026-08-26；四 Xavier；`WEAK_EDGE_ONLY`；CANDIDATE=0) |
| P37 | 更长不可变历史，或新合同低换手族 | SUPERSEDED（被 P38 设计收口：先跨品种 D1 对齐） |
| P38 | Alpha Discovery V0.7 审计与方向设计 | DONE（仅文档；无代码；无新实验） |
| P39 | D1 跨品种对齐 + 方向 2 预注册（少量） | DONE（V0.8 对齐包 + 三条假设已执行） |
| P40 | Alpha Operating System V0.7.1 | DONE（仅文档；无代码；无新实验） |
| P41 | Cross Asset V0.8 合同定稿 | DONE（hash 已锁） |
| P42 | Cross Asset V0.8 执行（对齐 + 四 Xavier） | DONE（`NO_CANDIDATE`；3/3 FALSIFIED；已冻结） |
| P43 | Alpha Coverage / Data / Priority / 12M 路线 V1 | DONE（仅文档；未跑新实验） |
| P44 | Regime Transition V0.9 合同定稿 | DONE（仅文档；hash 已锁；未跑） |
| P45 | ALPHA_PROGRAM_V1 文档（盘点→门→知识库） | DONE（仅文档；条件 A/B 未到） |
| P46 | Alpha pipeline 评分 + 残差家族纸面合同 | DONE（52 题；未跑 V0.9） |
| P47 | Regime Transition V0.9 执行（实现 + 四 Xavier） | DONE（`NO_CANDIDATE`；已冻结；不要调参） |
| P48 | Cross Residual V0.91 执行 | DONE（`NO_CANDIDATE`；已冻结；不要调参） |
| P49 | Alpha Recovery Program V1.0 | DONE（forensics + 纸面合同；当时未跑） |
| P50 | Alpha Mission V1.1 | DONE（STOP B；IT/TS/MS/RI/AMS 已跑；Level 0；Candidate=0） |
| P51 | Alpha Research Mission V2.0 | DONE（STOP B；IV/COT/EIA/UST10/CARRY_V1A 已跑；Level 0；Candidate=0） |
| P52 | Data Expansion Mission V3.0 | WAIT_HUMAN 记录保留（工厂+SUPPLY_V1 已跑；曲线/面仍 BLOCKED） |
| P53 | MT5 Max Mission V4.0 | DONE（新历史已冻；CM+UM NO_CANDIDATE；Level 0；Candidate=0） |
| P54 | Market Universe V5.0 / V5.1 | DONE（841 CFD；BREADTH WEAK_EDGE；SIZE NO_CANDIDATE；EXTERNAL_DATA_GATE） |
| P55 | V6 External Exchange Data | DONE NO_CANDIDATE（Pack E 已拉；TERM_STRUCTURE 三条 FALSIFIED；不要调斜率） |
| P56 | V7 Information Fusion | DONE STOP B+C（OI/Volume NO_CANDIDATE；DTE WEAK_EDGE；不要调；下一美元先报价期权） |
| P57 | V8 Information Fusion | DONE STOP C（TOP5 用尽；OG.OPT/LO.OPT 已报价；未下载；Level 0；Candidate=0） |
| P58 | V8.2 Options Data Due Diligence | DONE QUOTE ONLY（catalog/MVD/quote；CASE A 发票存在但不买；Level 0；Candidate=0） |
| P59 | V8.3 Options Historical Feasibility | DONE PURCHASE=NO（8日 record_count 样本；CASE B；未下载；Level 0；Candidate=0） |
| P60 | V8.4 Full-Year Options Occupancy Census | DONE PURCHASE=NO（251日；LO A / OG B；未下载；Level 0；Candidate=0） |
| P61 | V9 Existing Data Master Backtest | IN PROGRESS（统一回测；PURCHASE=NO；$0；Level 0；Candidate=0） |

---

## 12. 文档读取顺序

**AI Agent 启动时必须首先读取:**

1. `docs/TRADEMIND_CONTEXT.md` — 本文件 (事实 + 状态)
2. `AGENTS.md` — AI 协作规则
3. `TODO.md` — 当前任务
4. `docs/STAGE_GOALS.md` — 各阶段目标（最终链 / V1–V5）
5. `docs/PROJECT_VISION.md` — 项目愿景（不是运行状态）

**任何与 TRADEMIND_CONTEXT 冲突的信息, 以 TRADEMIND_CONTEXT 为准。**

---

END

