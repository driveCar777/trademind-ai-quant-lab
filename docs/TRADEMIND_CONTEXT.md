# TradeMind AI Quant Lab — AI Agent Context Document

> **版本:** V1.0  
> **更新时间:** 2026-09-04 深夜 (用户授权改规则 → `RESEARCH_RULES_AMENDMENT_V1`；**V25 ML1 = 第一个独立 Level-1 Candidate**，V25.1 复现 7/7 + placebo 干净；**NEW_INDEPENDENT=1**；V26 策略规格已写；**V27 季报层冻结：ML2F 与 ML1 正交(0.06)但验证资金 −0.3% 不过，ML2 同簇 0.96 无增量 → ML1 不变**；**V28 Final OOS 单次读取 PASS（超额 +1.00%/20d t 9.3，LO20 +71.4%，已锁）→ V29 ML1 前向管线 Smoke 5/5 PASS（每日名单 + 影子账本，Stability 进行中；有账户的 Paper 待用户）**；V22–V24 NO_CANDIDATE；余额 ≈$46 不花)  
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
- **V9 Master Backtest FACT 2026-08-30 STOP B：** 现有锁定机制已统一 NEXT_BAR_OPEN 重播。Level=0。Candidate=0。无 Positive Reproducible Strategy。HYP-0001 = PREDICTIVE_ONLY。Databento $31.82 未产生 Candidate。不买数据。$93 = UNUSED_RESEARCH_RESERVE。下一方向 = model / information representation review。见 `V9_DECISION.md`。
- **V10 Model Discovery FACT 2026-08-30 START：** 不是采购任务。不是重开 RSI/MA/OI/DTE。假设：已有 information set 可能含简单规则未捕获的非线性 / 交互结构。MODEL ≠ ALPHA。NEW_DATA_PURCHASE=FALSE。Final OOS DENIED。见 `V10_START.md`。
- **V10 Model Discovery FACT 2026-08-30 STOP B：** 62 个锁定实验。21 个 validation 相对 M0 有预测优势。FDR 0/62。Level=0。Candidate=0。`MODEL_REPRESENTATION_EXHAUSTED`。不买 Options。不花 $93。不要改 target 后重跑。见 `V10_DECISION.md`。
- **V11 Capital Allocation FACT 2026-08-30：** 不是新实验、不是采购。MT5 alpha 边际价值低。`NEXT_PRIMARY_RESEARCH_PATH = CHINA_A_SHARE_RESEARCH_UNIVERSE`。先做免费 BaoStock 数据层。不买 Options / Databento / Tushare。$93 = reserve。见 `V11_DECISION.md`。
- **V12 A-share PIT FACT 2026-08-30 START：** 不是因子、不是回测、不是采购。目标 = point-in-time A 股研究宇宙。见 `V12_START.md`。
- **V12 A-share PIT FACT 2026-08-30 CONDITIONAL：** BaoStock = CANONICAL（无 key）。AkShare-class HTTP SSL 失败，仅 cross-check。337 只退市股普查 335 有 K 线，空 2（`sz.000033` / `sz.000038`）。202 个 as-of 宇宙已修。财务样本有 `pubDate`，完整财务盘未冻。行业不是 PIT。全日线盘未冻。`A_SHARE_DATA_STATUS=CONDITIONAL`。`NEXT_PRIMARY_ACTION=FREEZE_FULL_EQUITY_DAILY_PANEL`。不要跑 Alpha。见 `A_SHARE_READY_DECISION_V12.md`。
- **V12.1 Daily Panel FACT 2026-08-30 START：** 全日线盘冻结。无采购。无 Alpha。单 session。`2015-04-30` 保持 INVALID。dataset_id=`tm-ashare-EQUITY-D1-20260830-000001`。见 `V12_1_START.md`。
- **V12.2 Panel Completion FACT 2026-08-30 START：** 单 downloader 收到 5549/5549 后自动 compile/freeze。dataset_id=`tm-ashare-EQUITY-D1-20260830-000002`。不覆盖 000001。见 `V12_2_START.md`。
- **V12.2 Panel Completion FACT 2026-08-30 FINAL：** 5549/5549 raw。18,418,047 行。`PRICE_ALPHA_READY`。`FULL_PANEL_FROZEN`。`sz.000033`/`sz.000038` 现有 K 线，不再是 empty DATA_GAP。2015-04-30 仍 INVALID。不要自动开 Alpha。见 `V12_2_FINAL.md`。
- **V13 CS Alpha FACT 2026-08-31 START：** 只用 `tm-ashare-EQUITY-D1-20260830-000002`。4 族 12 假设。hold=20。无财务/行业/事件。无 ML。无采购。Final OOS DENIED。见 `V13_START.md`。
- **V13 CS Alpha FACT 2026-08-31 DECISION：** Level 1 = 2（`H11_VOL_60` / `H12_VOL_120`）。验证期成本后 CAGR ≈ 0.55% / 1.30%。不是 10%。动量失败。不要翻号。下一动作 = Candidate Reproduction。见 `V13_DECISION.md`。
- **V13.1 Reproduction FACT 2026-08-31 START：** 只复现 H11/H12。不改 lookback/hold/分位/符号。不买数据。见 `V13_1_START.md`。
- **V13.1 Reproduction FACT 2026-08-31 DECISION：** H11 与 H12 均为 `CANDIDATE_SURVIVED`。Path A/B 复现原 overlapping `mean_net_h`。验证期成本后 CAGR 仍约 0.55% / 1.30%。不是 10%。20 日非重叠验证簿更弱（H11 负、H12 近 0）。不要调参。不要组合。见 `A_SHARE_CANDIDATE_DECISION_V13_1.md`。
- **V14 Strategy FACT 2026-08-31 START：** 只把 H11/H12 做成 Canonical Strategy。LOW_VOL_CANDIDATE_CLUSTER。不买数据。见 `V14_START.md`。
- **V14 Strategy FACT 2026-08-31 DECISION：** `STRATEGY_WEAK_BUT_RESEARCHABLE`。20 日资金账户 2010–validation 为负（约 −16% / −11%，MaxDD −66%）。验证期新开 CAGR 约 0.12% / 0.74%。不是 10%。H11/H12 相关 0.994，一个 cluster。不要调参。不要 Paper。见 `A_SHARE_STRATEGY_DECISION_V14.md`。
- **V14.1 Forensics FACT 2026-08-31 DECISION：** `METHODOLOGY_GAP_CONFIRMED`。Candidate overlapping `mean_net_h` 复现（Path A/B err=0）。独立资金引擎复现 V14 终点（H11 834,202.89 / H12 883,505.87）。会计正确。正的 Candidate 不是资金曲线：重叠均值年化 vs 非重叠复利 + 左尾 AM-GM。20 个 offset grid 全部亏。无 double charge。无 unfilled/limit bug。不要 Long Validation。不要调参。见 `V14_1_DECISION.md`。
- **V15 Alpha V2 FACT 2026-08-31 DECISION：** `NO_NEW_CANDIDATE`。同一冻结盘 9 条预注册（残差 / 分化状态 / 价量分歧）。双账本。BH-FDR 6/9 相对 EW 发现，**0/9 Level 1**。全部验证资金账户为负。残差与 H11/H12 预测相关 ≈ 0.90–0.94，不是独立 Alpha。H11/H12 KEEP_LOW_PRIORITY。Review：`PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`。不要买 $93。不要第10条。不要翻号。见 `A_SHARE_ALPHA_V2_DECISION.md`。
- **V16 Information FACT 2026-08-31 START：** 打开财务/行业信息层。无采购。不重开 H11/H12。不挖价格因子。Final OOS DENIED。见 `A_SHARE_INFORMATION_EXPANSION_V16.md`。
- **V16 Information FACT 2026-09-02 STOP B：** 财务年报 PIT READY（5500 symbols，announcement_rate=1，coverage_2010≈0.936，RESTATEMENT_RISK）。行业月度 as-of PIT READY（171/171）。预注册 6+3，双账本，统一 BH-FDR 0/9。验证资金账户 9/9 为负。NEW_CANDIDATE=0。`A_SHARE_INFORMATION_ALPHA_V1_NO_CANDIDATE`。信息可用但无边。全流程 Windows 本地，未派 Xavier。不采购。不重开 price-only。H11/H12 KEEP_LOW_PRIORITY。见 `V16_DECISION.md`。
- **V17 Macro FACT 2026-09-02 STOP B family：** A 股 × 冻结 EURUSD/US500/GVZ。6/6 验证资金负。FDR 0/6。`A_SHARE_MACRO_INFORMATION_V1_NO_CANDIDATE`。见 `V17_MACRO_DECISION.md`。
- **V18 AltInfo FACT 2026-09-02 STOP B family：** listing/ST/resume/calendar。0 Level-1。A2 与 A1 秩相同。见 `V18_ALTINFO_DECISION.md`。
- **V19 Industry×Macro FACT 2026-09-02 STOP B family：** 行业 PIT × 同一宏观。0 Level-1。见 `V19_INDMACRO_DECISION.md`。
- **Post-V16 FACT 2026-09-02 STOP B：** 统一 BH-FDR m=18 discoveries=1（IM6，非 Candidate）。NEW_INDEPENDENT=0。Event/News=`DATA_BLOCKED`。Options=`PAYMENT_REQUIRED`。见 `POST_V16_DECISION.md`。
- **Post-V19 Direction FACT 2026-09-02：** 最高可执行 IV = 指数成分/调仓，不是再挖 CS 因子。见 `POST_V19_RESEARCH_DIRECTION_AUDIT.md`。
- **V20 Index FACT 2026-09-02 STOP B family：** HS300/ZZ500 月度 as-of PIT OK（171/171；2018 vs 2024 diff=258）。4/4 无 Level-1。FDR 0/4。验证资金全负。调仓 X3 最差（val CAGR −27.93%）。`A_SHARE_INDEX_MEMBERSHIP_V1_NO_CANDIDATE`。见 `V20_INDEX_DECISION.md`。
- **V21 Dividend FACT 2026-09-04 STOP B family：** 分红 PIT READY（5549 files，24803 rows，announce_date < signal）。2/2 无 Level-1。FDR 0/2。验证资金 D1 −41% / D2 −72%。`A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE`。不要重下。不要改 20 日窗口。不要股息率分位。见 `V21_DIVIDEND_DECISION.md`。
- **Post-V21 FACT 2026-09-04 STOP B：** `A_SHARE_FREE_INFORMATION_MARGINALLY_EXHAUSTED`。不要再开 A 股 CS / 公告窗口。见 `POST_V21_DECISION.md`。
- **Post-V21 Forensics FACT 2026-09-04：** 只读 42 条双账本。验证资金 42/42 负。验证 MEAN_FORWARD 38/42 负。**VERDICT=A**。Sidecar B：H24/H25/H26/A5 + H11 官方账本。见 `POST_V21_CAPITAL_CONSTRUCTION_FORENSICS.md`。
- **Post-V21 Autodrive FACT 2026-09-04 S1：** Q1 相对 EW **NEGATIVE**（29/42 val excess_vs_b0<0，均值 −0.535%）。Q2 磁盘清单后新类仍 **NONE**。Q3 跳过。Q4：一条合格多头 CS 袖子（对 X1 年相关中位 0.54；2011/2018/2023 同号，2015/2017 与 HS300 反号）。Q5：唯一合法策略姿态 = H11/H12 **KEEP_LOW_PRIORITY**。**S1**：免费层+构造都不是下一刀。停搜索。不采购。confidence **0.91**。NEW_INDEPENDENT=0。见 `POST_V21_FORENSICS_STRESS.md` / `POST_V21_DISK_INVENTORY.md` / `POST_V21_ONE_SLEEVE_TEST.md` / `POST_V21_STRATEGY_OPTIONS.md` / `POST_V21_AUTODRIVE/PROGRESS.json`。
- **V22 / V23 / V24 FACT 2026-09-04 晚 STOP B×3：** 用户明确授权用 Databento 余额（先评估再买，买完自己干）。真实报价见 `databento_eval_v22/QUOTE.json`；Databento 无 A 股。**V22 FUTURES_XS**：买 30 个 CME 品种全合约 `ohlcv-1d` 2010-06→2026-08，**$47.10**（`tm-fut-GLBX-XS30-D1-20260904-000001`）；面板 30 品种 / 119,724 品种日（禁用窗在建面板时丢弃）；预注册 3 条（截面 carry / 截面动量 12-1 / 时序动量 12）：研究期 2010–2021 **扣费前** CAGR ≈ 1%，FDR 0/3，验证期正尾不提升 → `FUTURES_XS_V1_NO_CANDIDATE`。与 H11 月相关 −0.19/−0.07/−0.12。余额 ≈ **$46 不再花**：不买 statistics/OI，不买 LO/OG，不买美股日线。**V23 MARGIN**：交易所每日融资融券明细**免费可达**（东财数据中心镜像；SSE/SZSE 官方 200；V12 时代的 SSL 失败已不成立），3381 交易日 2010-03→2024-02，禁用窗不下载。PIT = D+1 早公布 → 信号用 t−1。预注册 3 条（低 20 日融资净流入 / 低融资余额占比 / 60 日去杠杆最大）。**M1 研究期 excess t=4.85、资金 +37%（CAGR 3.3%）；验证 MF −0.67%、excess +0.06%（t 0.92）、资金 −19%**；FDR 0/3 → `A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE`。M2/M3 与 H11 月相关仅 0.35/0.33 但为负。失败形状不同于 V15–V21（研究期真实、验证期归零而非为负），记入 atlas，不许移窗。**V24 HOLDERS**：股东户数含 `HOLD_NOTICE_DATE`（PIT），5549 只 297,732 份报告，$0。预注册 3 条（季度环比集中 / 两季集中 / 每股户数低）：研究期 excess 全 ≤0，验证资金 −18%~−26%，FDR 0/3 → `A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE`；与 H11 月相关 0.63–0.72。**北向持股**：HKEX 只留 12 个月且改季度披露 → 免费 **DATA_BLOCKED**。免费 A 股行为层（融资/户数/北向）= 已测或已阻断。Atlas 69→71 行。通用引擎 `cn_a_share_freeinfo_engine.py`。不要重开 V22/V23/V24；不要调 20/60/分位；不要翻号；不要用验证期选窗。
- **规则修正 V1 FACT 2026-09-04 深夜（用户授权改规则）：** `docs/research_engine/RESEARCH_RULES_AMENDMENT_V1.md`。诊断：规则不是 NEW_INDEPENDENT=0 的主因，但三条被用过头——(a)「只能长多 20 日绝对收益」原本只针对 H11 看完结果调 hold，却被套到所有新家族；验证期是 −30% 熊市，任何长多绝对收益门在那段必死；(b) 单一固定划分让 2.5 年一个行情决定 14 年信息的生死；(c) ML 禁令来自 V10 在 4 条 MT5 价格上的结论，与 3000 只股票 × 7 类信息合成无关。**保留**：预注册、`A_SHARE_STRATEGY_COST_MODEL_V1`、非重叠 CAGR、FDR、无正独立账本不 Paper/Live、不改历史。**修改**：A1 新家族可事前登记 LO20 或 HN20（对冲 IF/IC，计基差+手续费）账本；A2 固定划分之外 5 个滚动验证窗（2014-15/16-17/18-19/20-21.08/验证）≥4/5 正；A3 每个信息层一个预注册模型，跑完冻结，不许搜特征/参数；A4（V25 后加）聚类/独立性判在**超额-vs-EW 序列**上，原始 MF 序列任何长多分位都与大盘 0.95+ 相关，永远判不出独立。禁用窗 2024-03→2026-08 仍锁：只在某家族先过 A1+A2 门后做**一次**预声明读取，需用户点头。美国交易大赛：冠军纪录是小账户+极端杠杆+幸存者选择，无可测数据；能用的是 Numerai/WorldQuant 式方法论（多弱信号、截面模型、purged CV、严格样本外）= A3。
- **V25 MULTILAYER MODEL FACT 2026-09-04 深夜 LEVEL-1（$0）：** `A_SHARE_MULTILAYER_MODEL_V25`，合同 `V25_MULTILAYER_MODEL_CONTRACT.md`（hash 先写）。14 个已有 PIT 特征（价格 6：NEG_VOL_60/120、REV_20、MOM_250_20、NEG_TURN_20、NEG_LOG_AMT_20；融资 3（V23，lag 1）；户数 2（V24，notice date）；年报 2（V16，公告日）：ROE、净利 YoY；HS300 成分（V20 as-of））→ 截面排名 → 1 个 LightGBM（31 叶/lr 0.03/400 树/min_child 1000，seed 20260904）预测 20 日 open→open 收益排名；expanding walk-forward 首预测 2012-01-04，每 120 交易日 refit，embargo 21，训练行每 5 日，**2021-08-24 冻结**，验证期用冻结模型；基线 ML0 = 无拟合排名均值；m=2。HS300/CSI500 日线免费下载（东财走本机代理 / Sina 回退）只到 2024-02-29。**ML1**：研究超额 +1.24%/20d（t 28.3，IC 0.120）、验证 **+1.47%**（t 17.1，IC 0.167）；FDR 发现；滚动 5/5（+2.35/+1.29/+0.86/+0.40/+1.47%）；LO20 研究 **+276%**（CAGR 14.5%，MaxDD −46.8% 2016-11→2018-11，Sharpe 0.60），验证 **+30.9%**（HS300 ≈ −30%；CAGR 11.1%，MaxDD −20.9%），全程 2010→2024-02 CAGR 13.7%；成本 1×/1.5×/2× 验证 +31/+24/+18%。HN20（对冲 HS300）研究 +27% / 验证 +34%，但对 (EW−HS300) β 0.92、R² 0.93、MaxDD −54%（2017 −34%、2020 −19%、2024 年初 −22%）→ **小盘价差载体，不是策略**。特征增益：NEG_LOG_AMT_20 28%、NEG_TURN_20 17%、REV_20 14%、MOM 6%、ROE 5%、户数 8%、融资 7%、波动 8%、成分 0.3%；选中名字 amount 排名中位 0.86（小/静/近期下跌端），每期 ≈627 只。**正式标签 `WEAK_CANDIDATE_SAME_CLUSTER`**：预注册聚类用原始 MF 相关 = 0.94，但 H11 与 EW 本身 0.955、ML1 与 EW 0.973——测的是大盘；**超额序列 corr ML1 vs H11 = 0.06**（n 2950）。LO20 − 合格 EW 篮子 = **+0.89%/20d，t 5.1，71% 期正，13 年 11 年正**（2017 −2.7%，2020 −7.2%）。ML0：验证超额 +0.73% t 7.6 但研究 HN20 资金 −43% → 不过 Level-1。诊断（不门控）：H11 on HN20 −58%/+21%；M1 on HN20 −48%/−11%。见 `V25_MULTILAYER_MODEL_DECISION.md`、`cn_a_share_ml_v25/{RESULTS,DIAGNOSTICS_POST,MODEL}.json`。
- **V25.1 REPRODUCTION FACT 2026-09-04 深夜 PASS → NEW_INDEPENDENT=1：** 合同 `V25_1_REPRODUCTION_CONTRACT.md`（通过标准先写：7/7 形状、验证超额 ≥ +0.5%、超额 corr vs H11 ≤ 0.9）。7 个固定扰动（seed 1/2、stride 3/10、refit 60/240）全部保持 Level-1 形状；验证超额 [1.35%, 1.48%]；LO20 研究 [+265%, +289%]、验证 [+22%, +32%]；超额 corr vs H11 [0.022, 0.074]。**Placebo（标签在每日内打乱）→ 研究超额 −0.09%（t −5.5）、LO −18%/−20%、滚动 1/5**：管线无泄漏。结论 `A_SHARE_MULTILAYER_MODEL_V1_INDEPENDENT_CANDIDATE`，**NEW_INDEPENDENT_CANDIDATE=1**，STOP A（`V25_1_DECISION.json`）。V25 正式标签不改写。**不是 10% 承诺**：−47% 与 −21% 回撤在记录上；2024 年 1–2 月小盘崩盘在记录上；禁用窗未读；容量 ≈¥5M 起（100 股一手）。
- **V26 ML1 STRATEGY SPEC FACT 2026-09-04 深夜（仅规格）：** `V26_ML1_STRATEGY_SPEC.md`。策略 = LO20 账本（每 20 交易日收盘打分、次日开盘买前 20%≈600 只等权、持 20 日、开盘卖；涨跌停/停牌跳过留现金）。暴露明示：小盘/低换手/近期下跌倾斜、对 EW β≈1、监管与微观结构。操作规则：live refit 政策 = REFIT_240 变体；特征源死则该列 NaN 不补拟合；期内无止损；期间 12 期滚动 (LO−EW) < −8% 暂停复核（只能「原样恢复」或「退役」）；24 期连续 LO−EW ≤ 0 退役。门：Candidate ✅ → 规格 ✅ → **Final OOS 单次读取待用户** → Portfolio 需第二条正袖（H11/H12 不算）→ Paper 需用户 + 行情源 + 五源实时管线 → 小资金。无 Paper、无 order_send。
- **V27 FINDEEP FACT 2026-09-04 夜（$0，冻结）：** `A_SHARE_FINANCIAL_DEEP_MODEL_V27`，合同 `V27_FINDEEP_CONTRACT.md`（先写）。东财数据中心 4 张季报表 × 64 报告期（2008Q1→2023Q4）免费，256 文件 0 失败。**审计**：`RPT_DMSK_FN_INCOME/CASHFLOW` 的 NOTICE_DATE 是次年可比公告（晚 12 月）→ 不用；`RPT_LICO_FN_CPD` 业绩表 + `RPT_DMSK_FN_BALANCE`（Q1–Q3）是原始公告日；同期多版本取最早；计算特征只用公告日 ≤ 本份的其他报告。10 个固定特征（SUE_Q、单季营收 yoy、−应计、CFO/BPS、ROE_ttm、毛利变化、−资产增速、−杠杆变化、EP、BP）。m=2，闸门账本 **LO20**（A1 事前登记）。**ML2F 仅季报层**：超额 vs EW 研究 +0.65%（t 21.5）、验证 **+0.52%（t 5.6）**，滚动 5/5，FDR Y，**超额序列 corr vs ML1 = 0.06**（第二个与 ML1 正交的正信号），但 **LO20 验证资金 −0.3%**（熊市打平；研究 +96.5%，MaxDD −58%）→ **不过 Level-1**，不是候选。HN20 验证 +12.1% 已被看见 → 禁止事后给它换账本。**ML2 全栈 24 特征**：Level-1 但 corr vs ML1 **0.96** = SAME_CLUSTER（事前预期）；验证超额 1.42% vs ML1 1.47%、LO20 +28.0% vs +30.9% → 季报层加在 ML1 上**无增量**。结论 `LEVEL1_SAME_CLUSTER_AS_ML1`，**NEW_INDEPENDENT 仍 = 1**，ML1 不变。季报层 = 目前唯一与 ML1 正交且验证显著的信息层，问题在账本不在信息（与法医结论 B 同形）。ATLAS 73 行（V8–V27）。**禁止**：调 ML2F/ML2 任何东西；用 ML2 换 ML1；ML1+ML2F 当两袖；重开 INCOME/CASHFLOW；买季报数据。
- **V28 ML1 FINAL OOS FACT 2026-09-04 深夜（单次读取，已锁，$0）：** 用户 21:07 委托流程自决 → 协议先写（`V28_ML1_FINAL_OOS_PROTOCOL.md`，G1 超额>0 / G2 LO20 资金>0 / G3 无 24 期退役触发）→ 原始数据延伸到 2026-08-28（融资 607 天、HS300/ZZ500 as-of 30 月、户数截止改）→ 特征写单独缓存，**到 2024-02-29 与 V25 冻结缓存逐位相同 14/14**。闸门分数 = V26 政策 REFIT_240 walk-forward（15 次 refit，最后 2025-11-06）；诊断 = 2021 冻结模型。窗口 2024-03-01→2026-07-30 信号，30 期。**结果 `FINAL_OOS_PASS`**：超额 vs EW **+1.00%/20d（t 9.3）**，LO20 **+71.4%**（CAGR 24.3%，Sharpe 1.00，MaxDD −21.3% 2026-02→07），2024 +18.0% / 2025 +58.4% / 2026 至 7 月 −8.2%，19/30 期打过 EW，最长连续落后 3 期；冻结模型同向（+0.79%，+63.3%）。**合格 EW 自己 +1.17%/20d = 小盘牛市**，LO20 一半以上是 β。ML1 三段互不重叠正账本：+276% / +30.9% / +71.4%，全程 ≈16.6 年 8.4×，CAGR ≈ 13.7%。**锁**：`FINAL_OOS_READ.json` 存在即拒绝再读；ML1 永远没有下一个禁用窗；不改任何参数；不用禁用窗挑变体。**下一门 = Paper 准备**（每日五源增量管线 + 打分器只出名单 + 监控账本；开始日/账户/行情源由用户定）。Portfolio 仍缺第二袖。
- **V29 ML1 前向管线 FACT 2026-09-05 早（Design+Implement+Smoke PASS，$0）：** 用户「继续，不用询问」→ 先写 `V29_ML1_LIVE_PIPELINE_DESIGN.md`，再建 `research_engine/ml1_live/`。live 数据全部在 `data/market/cn_a_share/live/`，冻结数据集一字不改。`panel.py`：BaoStock 刷日历/basics（新上市 3 只追加在后），逐只增量拉 2026-08-29 之后的日线（5215 只 × 5 日，0 失败，29 分钟），live pack = 冻结面板逐位复制 + 新日期。`layers.py`：融资按日文件增量（lag 1）、户数按文件龄 7 天重拉、成分月中 as-of；年报层下次有新信息是 2027-03。`score.py`：V25 14 特征在 live pack 重建、REFIT_240 序列取 ≤ t 最近一次（2025-11-06，2.45M 行，33 秒，pickle 缓存只拟合一次）、前 20% 等权名单写 `SIGNAL_{date}.json`（含 ¥ 目标金额/手数、特征覆盖率、live_hash），不发单。`ledger.py`：影子账本接 V28 链（2026-07-30 后每 21 日 → 第一信号 2026-08-28，入场 2026-08-31，999 选 / 996 可成交），用同一 `capital_book` 成本模型结算，自动判 V26 暂停/退役。**冒烟 5/5**（`ml1_live/SMOKE_V29.json`）：冻结块 open/close/volume/tradestatus/isST/listed 逐位相同；20 只随机股 5 日收盘对 BaoStock 0 错；14/14 特征到 2026-08-28 与 `v25_features_finaloos` 逐位相同；**2026-07-30 用 live 模型重打分 = V28 闸门分数，max|Δ| 0.0，997/997 同名**；`SIGNAL_2026-09-04.json` 999 只。Stability = 连续 5 个交易日日更 + 第一期在 ≈2026-09-29 结算 → Freeze。有账户的 Paper 仍待用户。影子账本不是资金、不是承诺。
- **Amendment V2 + V30 MT5 FACT 2026-09-05 下午（用户授权解除 MT5 限制，$0）：** 用户「可以打破之前对于 MT5 的规则限制……你来开始吧」→ `RESEARCH_RULES_AMENDMENT_V2_MT5.md`：解除 ML 禁令（限 ≥300 只截面）、股票 CFD 只清点、只多头账本；保留预注册/实测成本/FDR/滚动窗/不 order_send/不重开已证伪宏观家族。终端清点：**无 XAUUSD / US500 / BTC 符号**；497 `CFD-Shares\USA`、67 US ETF、~55 FX、~15 商品。冻结 `tm-mt5-USSHARES-D1-20260905-000001`（492 只有 bar、2.37M 行、354 只 ≤2008 起；拉取 5.9 小时，服务器逐符号同步 ≈50 秒）。实测费率：`swap_mode 5`，**多头 −11.09%/年（488/492）、空头 −0.91%/年**，点差中位 0.15%。合同 `V30_MT5_US_XS_CONTRACT.md`：7 固定价格特征 → 1 LightGBM（V25 参数）→ LS20 闸门 / LO20 诊断，成本 = 半点差 + 0.05% 滑点/边 + 日历天 swap；跑前（分数生成前）按数据深度改成长划分：研究 2006-01→2019-12 / 验证 2020-01→2026-08 / REFIT_240 / 5 滚动块。**结果 `MT5_US_XS_PRICE_V30_NO_CANDIDATE`**：验证多空毛价差 +0.07%/20d（t 0.18）；LS20 −71.5%（t −4.0）；LO20 −29.1%，LO−EW −1.03%/20d（t −4.4）；滚动 2/5；研究期 LS 成本后也为负（毛 +1.31% t 2.76 < 成本 ≈1.9%）。四门 0/4。ATLAS 74 行。**结论 `MT5_STOCK_CFD_COST_CEILING`**：LS 一期往返 ≈1.9%/20d（≈25%/年）、LO ≈1.1%，高于任何可信的毛价差；幸存者偏差使结果为上界。**不开 V31（EDGAR）on CFD**；不调 hold/分位/账本。MT5 这台终端上的研究对象已清点完（宏观 CFD 无信号、股票 CFD 费率不可行）。美股 alpha 需现金股票账户 → 用户决定。唯一有效路径仍是 ML1 / V29。
- **V31 数据冻结 + V33 涨停事件模型 FACT 2026-09-06 09:20：** (a) `tm-cnfut-SINA-D1-20260906-000001` 冻结：73/73 预声明品种主力连续（铜/铝/橡胶/豆粕/玉米/棉花 2005 起；金 2008、银 2012、原油 2018、股指/国债 2017、工业硅/碳酸锂 2022–23）+ 逐合约 5,614 张（多数 **2018-05** 起，早于设计估计的 2019-05）、7,884 次请求 0 失败、121.9 万行、逐文件 sha256。V31 合同待写。(b) 用户 08:37："博涨停 = 根据前几日异动/技术/基本面事先判断，不是盘中、不是追板；你自己设计小资金版本"。→ 合同 `V33_LIMITUP_EVENT_MODEL_CONTRACT.md` 跑前冻结、只算一次（m+1，ATLAS 77 行）：目标 = t+2…t+6 出现收盘涨停；特征 = ML1 14 个 + 7 个日线事件特征（5 日异常收益、量比、近 10 日涨停次数、距 250 日高点、振幅等；消息/政策 DATA_BLOCKED 不入）；LGBM 二分类 walk-forward 2021-08 冻结；闸门账本 = 用户外壳（¥20k、主板、80%、¥2,000/只）持有 5 日。**结果**：验证期前 10% 命中率 **12.4% vs 基础 4.4%（提升 +8.0pp，t 60.9，99.8% 交易日为正）**= 仓库最强预测统计量；但外壳账本验证 **−88.1%**（超额 vs EW −1.66%/5d t −3.4），¥1M LO20 诊断 −66.5%，研究期同样深负 → **`A_SHARE_LIMITUP_EVENT_V33_PREDICTIVE_BUT_NOT_TRADABLE_AT_20K`**。机制 = 彩票效应：涨停概率高的股票（高振幅、高波动、近期已涨停）平均 5 日收益深负，与 ML1 的 NEG_VOL 同一枚硬币。**不是资金规模问题**（大账本同样负）。**禁止**：调阈值/持有期/特征；日内变体；为 G1 找账本；把 ML3 反向塞进 ML1。研究资源回 V31。
- **V31 中国期货截面 FACT 2026-09-06 10:10：** 合同 `V31_CN_FUTURES_XS_CONTRACT.md` 先提交后跑。跑前修订（未见分数）：诚实 20 日收益只能来自逐合约，首预测改 2019-07，研究→2023-06，验证 2023-07→2026-08，2023-06-30 冻结。8 特征 → 1 LightGBM → LS 三分位，3.3 bp/边，同合约开盘→开盘；展期单测通过（人造换月 +10% → 同合约 0）。**结果 `CN_FUTURES_XS_V31_NO_CANDIDATE`**：G1 验证 LS +6.0%（过）、G4 研究 +13.9%（过）、G2 毛价差 t 0.81（不过）、G3 滚动 3/5（不过；2021 −5.8%、2023H1 −4.5%）、G5 验证对齐 n=0（V26.8 账本止于 2024-01 且错开 7 日；全样本 n=21 corr 0.25 本会过）。LO 研究 +61% 是 2020 牛市 β，验证 t 0.45。平均 45–54 只合格。连续 vs 同合约偏差 0.1–0.2%/20d。**禁止**调参/剔金融期货/用 LO 替 LS/为 +6% 映射黄金原油。价格/持仓/期限结构层已清点。下一刀 = `CN_INFO_TO_COMMODITY`（V35）。ATLAS 78。
- **V26.8 单位随权益增长 FACT 2026-09-06 09:50（用户 09:27 授权"按你的来"）：** 事前理由 = 最低佣金算术（¥2,000/只 → 0.5%/期 ≈ 5.8%/年）+ 排名单调（V26.7 定投把名单稀释到 125 只，每块钱收益 1.58% vs 1.98%，配对 t −2.25）。合同 `V26_8_ML1_SCALED_UNIT_CONTRACT.md` 先提交后跑：`单位 = max(¥2,000, 权益/N_target)`，网格 {10,20,40} **在研究期按单期夏普选**，胜者单次读验证。研究期三条：N10 +551%（CAGR 21.3%，夏普 0.219）/ N20 +422% / N40 +369%，单调 → **N10 胜**。验证：**TWR +39.0%（CAGR 14.0%），超额 +2.05% t 2.86，19/29，资金 ¥74k → ¥86.9k 净利 ¥12.9k IRR 10.4%**（V26.7：+27% / IRR 4.2%）→ VIABLE，**采纳** `daily.py --n-target 10`。**多维度（逐日 MTM、剔除定投现金流）**：研究期 日 σ 1.8% 最差 −9.9%；周最差 −21%；月最差 −31%；年 2015 +147% / 2017 −22% / 2018 −22%；**逐日 MaxDD −55.9%**（2015-06→09，231 日回本）；滚动 1 年 22% 起点为负、3 年 13.5%、5 年 0%。验证期 周为正仅 48%，**逐日 MaxDD −24.4%**（2022-01→04）。**修正**：含定投权益算的期末 MaxDD 低估（V26.7 验证 −13% → TWR 口径 −18%；V26.8 −5% → −15%），已写回。**外壳冻结**：不试别的 N_target/单位下限、不做月份择时、不加止损、不改 ML1。
- **V26.7 满仓 + 每月定投 FACT 2026-09-06 09:35（用户 09:14 事前约束变更）：** "钱全部出去，不预设 80%；每月至少再充 2k"。合同 `V26_7_ML1_FULL_TOPUP_CONTRIB_CONTRACT.md` 先提交后跑，只算一次：100% 仓位（预留 ¥200 手续费）+ 每月首个信号日存入 ¥2,000；其余同 V26.6；采纳规则 = VIABLE 即采纳（仓位/定投是用户决定，不由收益反选）。**结果**：研究 TWR +264%（CAGR 14.2%，MaxDD −44.9%，超额 t 4.47，82/112）、资金 ¥236k → ¥432k 净利 ¥196k IRR 11.2%；验证 TWR **+27.0%（CAGR 10.0%，MaxDD −13.2%，超额 +2.44% t 3.58，23/29）**、资金 ¥74k → ¥79.0k 净利 ¥5.0k **IRR 4.2%**（末期 2024-01/02 −15.1% 砸在最大权益上）。TWR 低于 V26.6 因定投使 N 变大（验证 27 只、研究后期 125 只）→ 分散换稳定，不调。年度：2017 −30.5%、2018 −29.6% 满仓无止损。→ `VIABLE_HISTORICAL`，**采纳为 `daily.py` 默认**（`--exposure 1.0 --monthly-contrib 2000`）；`LEDGER_TOP20` 按月记入定投；今日名单本金 = 已结权益 + 当月定投；2026-08-28 影子名单 10 只投出 ¥19,746。**外壳冻结**：不试 90/95%、预留、定投额/日；不加止损；不改 ML1；不读禁用/近期窗。
- **V26.6 补满仓位 FACT 2026-09-06 09:25：** 用户 09:06 "根据你的来，继续优化"。事前算术事实：V26.5 验证期平均现金闲置 **42.4%**（¥2,000/只 + 整手 → 每只剩一截、>¥20 的股票买不起被跳过），¥20k 只有 ≈¥11.5k 在市场。合同 `V26_6_ML1_EQMONEY_80PCT_TOPUP_CONTRACT.md` 先提交后跑：只加第二轮"把 80% 预算剩余按分数顺序在同一批名字上每次加 1 手"，不加名字/不改选股/出场/成本；采纳规则事前写死（VIABLE 且验证 > V26.5 的 +12.1%）。**结果**：研究 +318%（CAGR 15.9%，MaxDD −44.8%，超额 +1.25%/20d t 4.30，闲置 21%）；验证 **+33.9%（CAGR 12.3%，MaxDD −11.4%，超额 +2.38% t 2.56，19/29 打过 EW，闲置 21%）** → `VIABLE_HISTORICAL`，**采纳为 `daily.py` 默认**（`--no-topup` 关）。`SHORTLIST`/`LEDGER_TOP20` 口径 = `ML1_EQMONEY_80PCT_TOPUP_MAIN`；2026-08-28 影子名单 8 只投出 ¥15,879。不是 alpha 改进（ML1 一字未动），是同一批股票买够了；MaxDD 同步放大。**禁止**：V26.7 试别的补仓/单位/仓位；因 −45% 回头加止损；改 ML1；读近期窗。
- **V34 出场规则诊断 FACT 2026-09-06 09:00：** 用户 08:50 问止盈/移动止盈/保本止损。合同 `V34_EXIT_RULES_DIAG_CONTRACT.md` 跑前冻结：13 条规则（止盈 5/10/20、硬止损 5/10、移动止盈 5/10、保本 3/5、两组合）事前写死，**只读研究期**，收盘判定次日开盘卖（顺延同 V26.4），对象 = ML1 V26.5 外壳（20 日）与 V33（5 日）。**ML1**：BASE +144%（CAGR 9.6%，超额 +0.65%/20d t 1.85）；12 条里 **11 条更差**（5% 止盈 → +25%，5% 移动止盈 → +12%；紧规则在噪声里卖掉会均值回归的低波动股）；唯一略好 = 止盈 20%（+188%，超额 +0.79% t 1.97，触发 13%）= 13 选 1 的随机预期，**不选**。回撤无一条实质压低（最好 −31% vs −39%，收益减半）。**V33**：13 条无一翻正（最好 −67%）。结论 `EXIT_RULES_NO_IMPROVEMENT`。近期窗（2024-03+）不再对任何变体读；一月/一季 = 1–3 个持有期无统计意义；"最近"由 V29 前向影子账本回答。**禁止**：把任何出场规则写进 `daily.py`/V26.5；用验证期/禁用窗重跑网格；以 TP20 再细分点位。
- **执行偏好 + MT5 D1 合法对象清点 FACT 2026-09-06 01:05（用户 00:57）：** 用户执行偏好 = MT5 下单；期货账户后开；研究不重开黄金/原油/外汇/CFD、不上 H1/tick；**A 股 V26.5 冻结（只出名单 + 影子账本，不改外壳）**；禁止为收益改参数/成本/杠杆。`docs/research_engine/MT5_D1_LEGAL_OBJECT_INVENTORY.md`：终端 69 宏观 + 492 美股 CFD + 68 ETF CFD 逐类对照 ATLAS —— FX（FX1–3/COT/RATES/CARRY/V32）、贵金属与能源（V1–V8/IV/COT/EIA/TERM/OI/DTE/V32）、农产品（SUPPLY/V32；天气 USDA 需采购）、股指 17 只与债券 2 只（不成截面）、美股 CFD（V30 成本天花板）、ETF CFD（**今日实测 swap 同 −11.09%/年**，68 只）→ **可立即做的合法新对象 = 0**。唯一未测层 `CN_INFO_TO_COMMODITY`（A 股面板→COPPER/SILVER/CrudeOIL；目标序列仅 2018-12 起 7.7 年 ≈90 期，功效低）合法但排在 V31 之后。**下一刀 = V31**。执行映射：AU→GOLD（swap −$1.54/手/日 ≈0.13%/年，点差 0.02%）、AG→SILVER（≈1.1%/年，0.11%）、CU/BC→COPPER（−4.5%/年双边，0.14%）、SC→CrudeOIL/BRENT（−4.5%，0.04%）；其余需期货户。
- **V26.5 FACT 2026-09-06 00:32（用户 00:30：资金利用率允许 80%，必要时 100%，复利再投入；要求看最近一年）：** 合同 `V26_5_ML1_EQMONEY_80PCT_MAIN_CONTRACT.md` = V26.4 唯一改动 70%→**80%**（"必要时 100%" **不采纳**：无事前触发规则即调参；复利再投入本来就是所有账本的做法）。**只算一次**（`ML1_EQMONEY_80PCT_MAIN_READ.json`）：研究 +144%（CAGR 9.6%，MaxDD −39%）；验证 **+12.1%**（CAGR 4.7%，MaxDD −10.8%），超额 vs EW +1.51%/20d t 2.65，19/29 → `VIABLE_HISTORICAL`；闲置 ≈40–42%。注意 80% 验证 (+12.1%) < 70% (+13.4%)：按手取整噪音，说明仓位比例上的差别是噪音，**不据此选**。**近期诊断（无决策，`ML1_EQMONEY_80PCT_MAIN_RECENT_DIAG.json`，V28 已消耗窗 2024-03→2026-08，REFIT_240 分数，同口径主板≤¥100 EW）**：全窗 +28.6%（28 期，MaxDD −16.4%）但超额 **+0.10%/20d t 0.16 = β**；近 12 月 +9.5%（超额 +1.18% t 1.2，7/11）；近 6 月 **−7.7%**（EW −13%，超额 +1.15% t 1.4，4/5）。为什么"最近一年"不作门：该窗是 V28 唯一一次真 OOS，已用掉；再对变体读它 = 用它挑变体；本次只对最终合同报一次数字。`daily.py` 默认 `--exposure 0.80`；09-04 名单 8 只 ≈ ¥13,427。**禁止**：70/80/90/100 对比；用近期窗做门；调任何参数。
- **V26.3 拆解 + V26.4 FACT 2026-09-06 00:15（用户 00:13 改约束：允许每只等金额多手；要求回测尊重 t 收盘后出数据、t+1 开盘买、卖出遇跌停卖不出）：** V26.3 验证期拆解（诊断，同一批成交）：等权毛 +2.27%/20d → 一手制（权重 ∝ 股价）+0.50% → 佣金 −0.67% → 滑点印花 −0.27% → 投入净 ≈ −0.44% × 70% ≈ −0.3%/期 = −10.8%。**不是买卖点、不是模型，是"每只 1 手"规则**（验证期均 8.8 只、单只最大权重 33%）。→ 合同 `V26_4_ML1_EQMONEY_70PCT_MAIN_CONTRACT.md`（跑前冻结、只算一次）：主板、≤¥100、总仓 70%、**每只 ¥2,000**（最低佣金 ≤0.25%/边的最小单位，沿用 V26.2）、N=floor(0.7×权益/2000)=7 起、`lots=floor(2000/(100×开盘))`、**出场新规**：t+21 开盘跌停/停牌 → 继续持有逐日试卖最多 10 日、仍不能卖按第 10 日收盘标 `STUCK`（比 V14.1 "整笔当没发生" 严）。结果 `ML1_EQMONEY_70PCT_MAIN_READ.json`：研究 +156%（CAGR 10.2%，MaxDD −33%，1520 笔，顺延 16、STUCK 26）；验证 **+13.4%**（CAGR 5.1%，MaxDD −7.9%，216 笔，顺延 0），超额 vs EW +1.48%/20d t 2.55，20/29 → **`VIABLE_HISTORICAL`**。现金闲置 ≈ 47–49%（30% 规则现金 + 按手取整）。V14.1 出场规则诊断：研究 +142% / 验证相同。`daily.py` 默认改为 V26.4（`--n-names 0`，不加 `--one-lot`）；09-04 名单 7 只 ≈ ¥11,627。**禁止**：调 ¥2,000 单位 / 70% / N 公式 / 顺延天数；读禁用窗；用 V14.1 诊断数替代门。`OWNER_CONSTRAINTS_AND_GOAL.md` 结论不变（本金决定数量级）。
- **用户约束与人生目标声明 + V26.3 FACT 2026-09-05 23:36（用户声明：不是研究任务；禁止为提高收益率做任何改动）：** 用户 27 岁，目标 35 岁前财务自由（**期望，不是闸门**）；验证阶段本金最多 ¥20k，后期每月可追加 ¥2k–10k；一手 100 股、可接受股价 ≤ ¥100（¥20 是算错）；不要 100% 股票，总仓事先定死；每只最多 1 手；买不起跳过；N 随价格变化不回头选；MT5 维持原判决、杠杆不是加速器。→ **V26.2 作废**（文件保留为 evidence）。新合同 `V26_3_ML1_ONELOT_70PCT_MAIN_CONTRACT.md`（主板、收盘 ≤ ¥100、总仓 **70%**（用户示例数字直接采用）、每只 1 手、¥5 最低佣金、¥20k、不读禁用窗），**只算一次**（`ML1_ONELOT_70PCT_MAIN_READ.json`，再跑拒绝）：研究 +74.7%（CAGR 5.9%，MaxDD −44%，均 17.3 只，闲置 32%）；验证 **−10.8%**（CAGR −4.4%，MaxDD −14%，均 8.8 只，闲置 30%）；超额 vs EW +0.46% t 1.2 / +0.65% t 0.87 → **`ML1_ONELOT_70PCT_MAIN_NOT_VIABLE`**。原因 = 执行外壳（权重 ∝ 股价：2026-09-04 名单里一只 ¥55 股占可投现金 39%；¥200 一手被 ¥5 佣金吃 2.5%/边；30% 现金），不是 ML1 排序。**禁止**试 60/80% 仓位、其他价格上限、手数规则来过门。`daily.py` 默认改为 V26.3 一手制（`--exposure 0.70 --max-price 100 --boards MAIN --manual-capital 20000`，`--n-names 0`）；`SHORTLIST` 输出一手名单（09-04：13 只，¥13,996），`LEDGER_TOP20.json` 记 V26.3 影子账本。复利算术（`docs/OWNER_CONSTRAINTS_AND_GOAL.md`）：¥20k + 每月 2k/6k/10k × 8 年，在 0–13.7% 年化下终值 21–39 万 / 60–106 万 / 98–172 万；本金合计 21 / 60 / 98 万——**缺口是本金不是边**；4% 提取率下年支出 10 万需 250 万，无一格达到。结论：**2 万实盘不改变 8 年后数量级；短名单继续出、影子账本继续记、人暂不上实盘（历史门未过也不建议手工 Paper）；研究资源全部优先 V31。** 不为安慰挖"更高收益"变体。
- **V26.2 近期窗诊断 + V32 MT5 宏观池化 FACT 2026-09-05 23:20（用户 22:53 要求近 1 年/半年/1 月 + MT5 黄金原油货币对同步开始）：** (a) V26.2 在 V28 已读窗（2024-03→2026-08，REFIT_240 分数）上的**诊断**（`ML1_TOP10_20K_MAIN_RECENT_DIAG.json`，无决策、不调参）：全窗 +31.5%（28 期）但 **超额 vs 主板≤¥20 EW +0.01%/20d t 0.01（15/28）= 纯 β**；近 12 月 +9.1%（超额 +1.2% t 0.84）；近 6 月 **−12.6%**（EW −12.7%）；近 1 期 +1.0%。同窗 999 只 ML1 超额 +1.00%/20d t 9.3 → **10 只低价主板切片在近期把 alpha 丢了**。**禁止**用该窗挑 N/板块/价格上限；前向影子账本说话。(b) V32 `MT5_MACRO_POOLED_V32`：Amendment V2.1（池化面板 ML ≥50 只×≥10 年允许一个模型）；数据 `tm-mt5-MACRO-D1-20260905-000001`（69 只，黄金/原油/股指/农产品/债券**只有 2018-12 起 7.7 年**，外汇 2001 起）；10 个自归一价格特征 → 池化 LightGBM → LS 三分位波动平价、hold 5、实测点差+swap（非外汇 −4.5%/年两边付）→ **`NO_CANDIDATE`**：验证毛价差 +0.06%/5d t 1.0（研究 t −0.6）；LS −60.5% t −8.5；滚动 0/5；四门全 FAIL。ATLAS 75–76 行。**MT5 宏观 D1 研究对象清点完**：单品种规则 V1–V8 证伪、池化 ML V32 证伪、股票 CFD V30 成本死。不调、不按组切、不上 H1/tick、不采购。MT5 只剩执行终端用途。期货 V31 未开始（用户说可缓）。
- **V26.2 `ML1_TOP10_20K_MAIN` FACT 2026-09-05 22:44（用户事实：只能买主板；本金 ¥20,000；期望 ¥20 以内的股）：** 合同 `V26_2_ML1_TOP10_20K_MAIN_CONTRACT.md` 跑前冻结，m+1。N 由算术推出（¥20,000 ÷ 一手 ¥20 股最大成本 ¥2,000 = **10**），不是搜参；仅主板；信号日收盘 ≤ ¥20；每只 ¥2,000 按手取整；最低佣金 ¥5/笔（≈0.25%/边，一期往返 ≈0.75%）；其余同 V26.1。历史读取（不读禁用窗，`ML1_TOP10_20K_MAIN_READ.json`）：研究 +402%（CAGR 18.1%，MaxDD −43%）；**验证 +32.7%（CAGR 11.9%，MaxDD −11%），超额 vs EW +2.4%/20d（t 2.4），20/29 期打过 EW**；每期成交 10/10；现金闲置 ≈22%（按手取整）→ `ML1_TOP10_20K_MAIN_VIABLE_HISTORICAL`。V29 `daily.py` 默认改为 `--boards MAIN --manual-capital 20000 --n-names 10 --max-price 20`；每日 `SHORTLIST_{date}.csv` 10 只（2026-09-04 已生成）；`LEDGER_TOP20.json` 记 n=10 影子账本，2026-08-28 起。**禁止**调 N / 价格上限 / 手数 / 成本；资金或权限变化 = 新合同。¥20k 年化 10% = ¥2,000/年，是练手账本，不是财务自由。
- **执行假设纠正 + V26.1 FACT 2026-09-05 22:20（用户纠正，硬性）：** 用户：小资金、平安普通账户、考试过了但无量化权限、短期开不了；不要把 QMT/PTrade / 999 只等权自动下单当 ML1 实盘路径；不做 computer-use / 非官方 API 下单；执行 = 系统出短名单，用户手工下单；MT5 美股是 CFD、无美股账户；期货账户未开、研究先做。→ 合同 `V26_1_ML1_TOP20_MANUAL_CONTRACT.md`（跑前冻结）：ML1 分数不动，取前 **20** 只、等权、`lots=floor(alloc/(100×开盘))`、0 手跳过顺延、V14.1 不成交规则、成本模型 V1 + **最低佣金 ¥5/笔**、资金参数默认 ¥100k、不读禁用窗。历史读取（`TOP20_MANUAL_READ*.json`，m+3）：**全板** 研究 +298%（CAGR 15.3%，MaxDD −53%）/ 验证 +17.0%（CAGR 6.5%，MaxDD −18%，超额 vs EW +2.0%/20d t 3.3，22/29）；**主板+创业板** 研究 +385% / 验证 +10.5%（超额 +1.7% t 2.8）；**仅主板** 研究 +410% / 验证 +34.5%（CAGR 12.5%，MaxDD −10%，超额 +2.4% t 3.1）。三口径均 `VIABLE_HISTORICAL`；**板块由用户账户权限决定，不由结果挑**（默认 MAIN_CHINEXT 待用户确认）。约 10–13% 现金因按手取整闲置。V29 `daily.py` 新增 `--manual-capital` / `--boards`，每日输出 `SHORTLIST_{date}.csv`（20 只、估算手数）与 `LEDGER_TOP20.json`；2026-08-28 起 TOP20 影子账本与 999 只账本并行。`MASTER_PLAN_V2` 执行节已改写；QMT 等以后资金权限到位再谈。
- **MASTER_PLAN_V2 + V31 Design FACT 2026-09-05 夜（用户授权修改规划）：** 用户「你可以修改我的设计和规划……市场是 MT 黄金/原油/直盘、A 股、中国大陆期货、美股」→ `docs/MASTER_PLAN_V2.md`。审查：原设计 80% 精力在平台（Xavier 集群、本地 LLM、7 个教科书策略、人手确认纸质单），有证据的价值 100% 来自研究纪律 + ML1；平台冻结不再投入；谨慎放在统计门而非人手点击。市场判决：**A 股优先级 1**（唯一有证据；V26 执行坑 = 999 只等权人手不可执行 → 需券商 QMT/PTrade 接口，备用「前 100 只」只能作新合同前向验证）；**中国期货优先级 2**（~70 品种有截面、无融资费、20 日往返 ≈0.05–0.15%、交易所数据免费；黄金/白银/铜/原油观点可经 Ava Trade GOLD/SILVER/COPPER/CrudeOIL 执行口）；**MT5 宏观品种作为研究对象关闭**（20+ 家族 + V10 62 实验 + V30；Ava Trade 有 `GOLD`/`SILVER` 符号，下午「无黄金符号」为口误）；**美股优先级 3**（需现金账户 + 无幸存者价格史不免费）。财务自由算术：13.7% CAGR 翻倍 5.5 年，不加杠杆，改变结果的只有第二/第三条独立袖子。V31 `CN_FUTURES_XS_V31` Design 已写：数据源实测——四家交易所官网本机直连被重置（Clash 出口境外，需用户加 DIRECT），新浪 `getDailyKLine` 可用（主力连续 2005→，逐合约仅 2019-05→，3–10 秒/请求），东财 SSL 失败；两阶段方案（新浪先跑，交易所全史作 V31.1 复现）；拟 8 特征、一个 LightGBM、LS 三分位闸门、展期调整必须写清并单测、独立性门 corr vs ML1 < 0.3。未写合同、未跑。
- **Post-V21 Autodrive W1–W6 FACT 2026-09-04：** W1 `BEAT_EW_CLUSTER.json`：13 条打过 EW 的账本**不是一个影子**（月对齐 vs H11 >0.9 只有 5/13：H21/H22/H29/A1/A2；A1≡A2；H24/H25/H26/A5/A6/IM5/IM6 与 H11 0.46–0.71；>0.8 联通得 6 簇），但 13/13 验证资金仍负。X1 在低波簇内。W2 `DISK_WALK.json`：os.walk 11605+6974 文件，AVAILABLE=0；`announcements/` 空；`financial/raw/balance` 空；日线 raw 无 pe/pb；两者都是比率类且需登录。W3 `FAILURE_ATLAS.json`：V8–V21 60 行，42 验证资金负，13 打过 EW。W4 `STRATEGY_BIND.json`：H11 成本/毛利 1.49；**零成本反事实 CAGR +2.91%、MaxDD −58%**（诊断，不是策略）；H11+H12 50/50 −14.08%、corr 0.996；Paper=**NO**。W5：唯一能对上 A 股缺口的付费类是 vendor 资金流/股东/融资数据（未报价、人类闸门）；LO $11.99 对不上。默认 **DO_NOT_BUY**。S1 关闭的是搜索不是项目。下一入口 = 人类报价后先对照 FAILURE_ATLAS 再写合同；否则 idle KEEP_LOW_PRIORITY。

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
| P61 | V9 Existing Data Master Backtest | DONE STOP B（已重播；无 Positive Reproducible；PURCHASE=NO；Level 0；Candidate=0） |
| P62 | V10 Model Discovery | DONE STOP B（`MODEL_REPRESENTATION_EXHAUSTED`；FDR 0/62；PURCHASE=NO；Level 0；Candidate=0） |
| P63 | V11 Alpha Capital Allocation | DONE（NEXT=A股研究宇宙；PURCHASE=NO；未跑新实验） |
| P64 | V12 A-share PIT foundation | CONDITIONAL（无采购；无 Alpha；未 RESEARCH_READY） |
| P65 | V12.1 Full equity daily panel | IN PROGRESS（无采购；无 Alpha） |
| P66 | V12.2 Panel completion + freeze | DONE FROZEN（PRICE_ALPHA_READY；不要自动开 Alpha） |
| P67 | V13 A-share CS alpha V1 | DONE LEVEL_1_CANDIDATE=2（不要第13个因子） |
| P68 | V13.1 H11/H12 candidate reproduction | DONE CANDIDATE_SURVIVED×2（弱；Final OOS DENIED） |
| P69 | V14 H11/H12 strategy construction | DONE WEAK_BUT_RESEARCHABLE（不优化；Final OOS DENIED） |
| P80 | V22 FUTURES_XS (Databento $47.10, 30 CME roots) | DONE NO_CANDIDATE（FDR 0/3；扣费前平；余额 ≈$46 不花） |
| P81 | V23 A-share MARGIN positioning ($0) | DONE NO_CANDIDATE（M1 研究 t 4.85 / 验证归零；不调不移窗） |
| P82 | V24 A-share HOLDER concentration ($0) | DONE NO_CANDIDATE（研究 excess ≤0） |
| P83 | Northbound daily holdings | DATA_BLOCKED（HKEX 12 个月 + 季度） |
| P84 | RESEARCH_RULES_AMENDMENT_V1（A1–A4） | DONE（用户授权；禁用窗仍锁） |
| P85 | V25 multilayer model（14 已有 PIT 特征 → 1 LightGBM，$0） | DONE **LEVEL-1**（验证超额 +1.47% t 17；LO20 验证 +30.9%；滚动 5/5） |
| P86 | V25.1 reproduction + placebo | DONE PASS（7/7；placebo −0.09%）→ **NEW_INDEPENDENT=1** |
| P87 | V26 ML1 strategy spec | DONE（规格；无 Paper） |
| P88 | Final OOS single read on ML1 | DONE **FINAL_OOS_PASS**（用户委托；超额 +1.00%/20d t 9.3；LO20 +71.4%，MaxDD −21%；已锁，不再读） |
| P90 | V29 ML1 前向管线（live pack + 三层增量 + 特征 + REFIT_240 + 名单 + 影子账本） | Design+Implement+Smoke **5/5 PASS**（2026-09-05）；Stability 待连续 5 日 + 第一期结算 ≈2026-09-29 |
| P91 | ML1 Paper（有账户） | 待用户：开始日 / 账户 / 行情源 |
| P93 | MASTER_PLAN_V2（用户授权改规划）+ V31 中国期货截面 Design | DONE（规划）/ Design 完成；V31 数据 = 新浪（连续 2005→、逐合约 2019-05→）；交易所官网需用户 Clash DIRECT |
| P92 | Amendment V2 (MT5) + V30 美股 CFD 截面价格模型 | DONE **NO_CANDIDATE**（验证毛价差 t 0.18；LS20 −71.5%；`MT5_STOCK_CFD_COST_CEILING`；不开 V31 on CFD） |
| P89 | V27 financial deep layer（季报/资产负债/现金流 → 2 模型，$0） | DONE **LEVEL1_SAME_CLUSTER_AS_ML1**（ML2F 独立 corr 0.06 但验证资金 −0.3% 不过；ML2 corr 0.96 无增量；ML1 不变） |
| P70 | V14.1 Candidate→Strategy forensics | DONE METHODOLOGY_GAP_CONFIRMED（不优化；不要 LV；Final OOS DENIED） |
| P71 | V15 second independent A-share CS alpha | DONE NO_NEW_CANDIDATE（9/9 验证资金负；不采购；Final OOS DENIED） |
| P72 | V16 financial/industry PIT + controlled alpha | DONE STOP B（READY 两边；0 新 Candidate；不采购） |
| P73 | V17 A-share × frozen macro CS | DONE STOP B family（0 新 Candidate） |
| P74 | V18 A-share altinfo | DONE STOP B family（0 新 Candidate） |
| P75 | V19 industry PIT × macro | DONE STOP B family（0 新 Candidate） |
| P76 | Post-V16 global decision | DONE STOP B（当时合法免费空间耗尽） |
| P77 | Post-V19 direction audit | DONE（下一刀=指数成分，不是更多 CS 因子） |
| P78 | V20 HS300/ZZ500 membership | DONE STOP B family（0 新 Candidate） |
| P79 | V21 dividend announcement events | DONE STOP B family（0 新 Candidate） |
| P80 | Post-V21 global freeze | DONE STOP B（免费信息边际耗尽） |
| P81 | Post-V21 capital forensics | DONE VERDICT A；新类 NONE；不采购 |
| P82 | Post-V21 autodrive Q1–Q5 | DONE **S1** confidence 0.91 |
| P83 | Post-V21 autodrive W1–W6 | DONE（机器文件 4 份；NOT_ONE_SHADOW；AVAILABLE=0；Paper=NO；idle） |

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

