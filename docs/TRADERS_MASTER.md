# TradeMind — 项目总纲

> **版本:** V2.1 冻结 + V3.0 设计先行
> **最后更新:** 2026-08-01
> **维护模式:** 一人 + AI 长期协作

---

## 一、项目愿景

构建一套**完全本地化**的 AI 量化研究与投研实验平台，整合 A 股数据、MT5 外汇、AI 模型与 Jetson 分布式计算集群。不依赖任何云服务，所有数据、计算、推理全部在本地完成。

**核心原则：**
- 全本地化（零云依赖）
- 一人 + AI 维护（零团队成本）
- REST 通信（零特殊协议）
- stdlib 优先（零外部依赖，Xavier 节点）
- 文档驱动（每个版本冻结前更新文档）


---

## 二、最终目标（V5.0 架构）

`
Windows Master 主机 (localhost:9000, FastAPI)
    |
    +-- REST 调度
    +-- AI Gateway (port 9100) --- Arc A770M LLM推理
    |   +-- 投研报告生成 / 策略描述 / 信号解读 / Research Agent
    |
    +-- MT5 Bridge (port 9200) --- MetaTrader 5 实盘
    |   +-- 信号执行 / 风控管理 / 持仓管理
    |
    +-- Dashboard (port 9000/dashboard) --- Web面板
    |
    +-- REST (requests.post, 同步)
    |
    Jetson Xavier 集群 (4节点, 全部 8080 端口)
    +-- Xavier-01 (192.168.1.200) -- Indicator Worker (Docker, FastAPI)
    +-- Xavier-02 (192.168.1.201) -- Factor Worker (stdlib server.py)
    +-- Xavier-03 (192.168.1.202) -- Backtest Worker (stdlib server.py)
    +-- Xavier-04 (192.168.1.203) -- Monitor Worker (stdlib server.py)
`

### 六大核心能力

| # | 能力 | 说明 | 当前状态 |
|---|------|------|----------|
| 1 | A 股研究 | 本地 A 股数据接入、50只股票、15因子、五维评分 | DONE (V2.0) |
| 2 | MT5 外汇 | MetaTrader 5 外汇/期货实盘与回测 (7策略) | DONE (V2.1) |
| 3 | AI 推理 | Arc A770M 本地 LLM，投研报告/策略描述/信号解读 | NEXT (V3.0) |
| 4 | 分布式计算 | 4x Xavier NX 并行，REST 调度 | DONE (4节点在线) |
| 5 | 实时监控 | GPU/系统状态，集群健康度 | DONE (V1.0) |
| 6 | Web Dashboard | 任务管理、结果可视化 | DONE (V1.3) |

---

## 三、硬件环境

### 3.1 Windows Master 主机

| 组件 | 规格 |
|------|------|
| GPU | **Intel Arc A770M** 16GB VRAM |
| GPU 驱动 | 32.0.101.8826 (OpenCL 3.0 NEO) |
| CPU | 12th Gen Intel Core i7-12700H |
| 集显 | Intel Iris Xe Graphics (驱动 31.0.101.3430) |
| OS | Windows 11 (10.0.26200) |
| Python | 3.13.12 (Miniconda) |
| 项目目录 | D:\AGXXAIVER-4-WINDOWS-1-STOCK |
| Master API | localhost:9000 (FastAPI + Uvicorn) |
| AI Gateway | localhost:9100 (设计中) |
| MT5 Bridge | localhost:9200 (设计中) |

### 3.2 Intel oneAPI 环境

| 组件 | 状态 | 路径 |
|------|------|------|
| oneAPI SDK 2026.0 | 已安装 | C:\Program Files (x86)\Intel\oneAPI\2026.0 |
| SYCL 编译器 | 可用 | compiler\latest\bin\ |
| sycl-ls | 可见 Arc A770M | 需通过完整路径或 setvars.bat 调用 |
| MKL | 已安装 | oneAPI 2026.0 内含 |
| TBB | 已安装 | oneAPI 2026.0 内含 |
| VTune | 已安装 | oneAPI 2026.0 内含 |
| DNNL | 已安装 | oneAPI 2026.0 内含 |
| ONEAPI_ROOT | 未设置 | 需手动 setvars.bat 或添加到 PATH |

**sycl-ls 设备列表：**
`
[opencl:gpu][opencl:0] Intel Arc A770M Graphics OpenCL 3.0 NEO [32.0.101.8826]
[opencl:gpu][opencl:1] Intel Iris Xe Graphics OpenCL 3.0 NEO [31.0.101.3430]
[opencl:cpu][opencl:2] Intel Core i7-12700H OpenCL 3.0
`

### 3.3 Conda 环境

| 环境 | Python | 用途 |
|------|--------|------|
| base | 3.13.12 | Miniconda 默认 |
| (待核对本机 conda env list) | 3.10.20 | 通用环境 |
| stock-review | - | 股票分析 |
| qwen-ai | - | 量化工具 |

### 3.4 Jetson Xavier 集群

| 节点 | IP | 用户名 | Python | 部署方式 |
|------|-----|--------|--------|----------|
| Xavier-01 | 192.168.1.200 | dji (<TRADEMIND_XAVIER_PASSWORD>) | 3.6.9 | Docker (8080->8000) |
| Xavier-02 | 192.168.1.201 | dji (<TRADEMIND_XAVIER_PASSWORD>) | 3.6.9 | stdlib server.py |
| Xavier-03 | 192.168.1.202 | dji (<TRADEMIND_XAVIER_PASSWORD>) | 3.6.9 | stdlib server.py |
| Xavier-04 | 192.168.1.203 | dji (<TRADEMIND_XAVIER_PASSWORD>) | 3.6.9 | stdlib server.py |

**Xavier 关键约束：** Python 3.6.9, 无 Docker Hub, 无 pip/apt, 无 nvidia-smi, 仅 stdlib 可用。


---

## 四、版本历史

| 版本 | 里程碑 | 冻结日期 | 核心内容 |
|------|--------|----------|----------|
| V1.0 | Worker Template | 2026-07-25 | indicator-worker 模板 + Docker 部署 |
| V1.1 | Master API + 端到端 | 2026-07-25 | REST 调度 + 4 Worker 通信 |
| V1.2 | Master 增强 | 2026-07-31 | 自动重试/超时/健康探测/任务列表 |
| V1.3 | Dashboard 前端 | 2026-07-31 | 单文件深色主题 Web 面板 |
| V2.0 | Factor Worker 增强 | 2026-07-31 | 50只/15因子/五维评分/行业对比/分位数 |
| V2.1 | Backtest Worker 增强 | 2026-07-31 | 7策略/滑点手续费/高级指标/ThreadingMixIn |
| V3.0 | AI Gateway | 设计中 | Arc A770M 本地 LLM 推理 |
| V4.0 | Research Agent | TODO | AI 自动发现异常/生成策略/回测验证 |
| V5.0 | MT5 Bridge | TODO | 实盘交易/风控/仓位管理 |

---

## 五、Worker 能力详情

### 5.1 Indicator Worker (Xavier-01)

| 项目 | 详情 |
|------|------|
| 节点 | Xavier-01 (192.168.1.200:8080) |
| 部署 | Docker (trademind-indicator:1.0.0) |
| 技术栈 | FastAPI (Python 3.6.9 容器内) |
| 指标 | SMA, EMA, RSI, MACD |
| 端点 | GET /health, POST /indicator |

### 5.2 Factor Worker (Xavier-02)

| 项目 | 详情 |
|------|------|
| 节点 | Xavier-02 (192.168.1.201:8080) |
| 部署 | stdlib server.py (单文件, ~25KB) |
| 技术栈 | Python 3.6.9 stdlib + ThreadingMixIn |
| 股票池 | 50 只 A 股, 12 个行业 |
| 因子 | 15 个 (ROE/ROA/PE/PB/PS/股息率/市值/营收增速/利润增速/ROE_3年均值/负债率/流动比率/60日动量/60日波动率/量比) |
| 评分 | 五维百分制 (价值25+质量25+动量20+风险15+流动性15) |
| 等级 | S(85-100) / A(70-84) / B(55-69) / C(40-54) / D(0-39) |
| 端点 | GET /health, GET /factors, POST /factor |

### 5.3 Backtest Worker (Xavier-03) -- V2.1

| 项目 | 详情 |
|------|------|
| 节点 | Xavier-03 (192.168.1.202:8080) |
| 部署 | stdlib server.py (单文件, ~416行) |
| 技术栈 | Python 3.6.9 stdlib + ThreadingMixIn |
| 策略 (7个) | EMA_MACD, RSI, SMA_CROSS, TURTLE, GRID, BOLLINGER, VWAP |
| 滑点 | slippage_bps 参数 (基点, 买入向上滑/卖出向下滑) |
| 手续费 | commission_bps 参数 (双向扣除) |
| 高级指标 | Sharpe/Sortino/Calmar 比率, 盈亏比, 资金曲线(50点) |
| 初始资金 | initial_capital 参数 (默认 10000) |
| 端点 | GET /health, GET /strategies, GET /version, POST /backtest |

### 5.4 Monitor Worker (Xavier-04)

| 项目 | 详情 |
|------|------|
| 节点 | Xavier-04 (192.168.1.203:8080) |
| 部署 | stdlib server.py (单文件, ~12KB) |
| 技术栈 | Python 3.6.9 stdlib + ThreadingMixIn |
| 指标 | CPU/RAM/Disk/GPU/Network/Load/进程数 |
| 端点 | GET /health, GET /metrics, GET /services, GET /cluster, POST /monitor |

---

## 六、Master API 参考

### 6.1 服务信息

- **版本:** 1.2.0
- **端口:** 9000
- **技术栈:** FastAPI + Uvicorn

### 6.2 路由表

| 端点 | 方法 | 说明 |
|------|------|------|
| /health | GET | Master 健康检查 |
| /workers | GET | Worker 列表 (4/4 ONLINE) |
| /tasks | GET | 最近任务列表 |
| /task | POST | 提交任务 (同步执行) |
| /task/{id} | GET | 查询任务详情 |
| /dashboard | GET | Dashboard 页面 |

### 6.3 错误码

| Code | HTTP | 说明 |
|------|------|------|
| TM-0000 | 200 | 成功 |
| TM-1001 | 400 | 请求参数错误 |
| TM-1002 | 200 | Worker 离线 |
| TM-1003 | 200 | 任务失败 |
| TM-1004 | 504 | 超时 |
| TM-1005 | 429 | Worker 忙 |

---

## 七、V3.0 AI Gateway -- 当前重点

### 7.1 目标

在 Windows Master 上部署 Arc A770M 本地 LLM 推理服务，提供投研报告/策略描述/信号解读能力。

### 7.2 推理框架选型

| 组件 | 选型 | 原因 |
|------|------|------|
| 推理框架 | llama-cpp-python | SYCL 后端原生支持 Intel Arc |
| 模型格式 | GGUF Q4_K_M | ~9GB VRAM, 无需 PyTorch |
| API 框架 | FastAPI (port 9100) | 与 Master API 一致 |
| 首选模型 | Qwen2.5-14B-Instruct | 中文投研场景最佳 |

### 7.3 架构

```
Dashboard / Master API (port 9000)
    | REST proxy
AI Gateway (port 9100, FastAPI)
    | llama-cpp-python (SYCL)
Arc A770M (16GB VRAM)
    |
投研报告 / 策略描述 / 信号解读 / 通用对话
```

### 7.4 API 端点

| 端点 | 说明 |
|------|------|
| GET /health | 健康检查 + GPU 状态 |
| GET /models | 已加载模型列表 |
| POST /api/v1/ai/generate | 投研报告 (因子+市场数据 -> Markdown) |
| POST /api/v1/ai/describe | 策略描述 (回测结果 -> 评估文本) |
| POST /api/v1/ai/signal | 信号解读 (技术指标 -> 分析) |
| POST /api/v1/ai/chat | 通用对话 |

### 7.5 目录结构

```
ai-gateway/
  server.py          # FastAPI 入口
  inference.py       # LLM 推理引擎封装
  prompts.py         # Prompt 模板
  config.yaml        # 配置
  models/            # GGUF 模型文件 (~9GB)
  requirements.txt   # 依赖
  tests/             # 冒烟测试
```

### 7.6 Phase 计划

| Phase | 名称 | 预估 | 状态 |
|-------|------|------|------|
| 0 | 环境准备 | 1天 | DONE |
| 1 | 模型下载 | 0.5天 | NEXT |
| 2 | 核心实现 | 2天 | 待定 |
| 3 | API 对接 | 0.5天 | 待定 |
| 4 | 冒烟测试 | 0.5天 | 待定 |
| 5 | 性能调优 | 1天 | 待定 |
| 6 | 冻结 | 0.5天 | 待定 |

**总预估: 6 天**

### 7.7 环境检查结果 (2026-08-01)

| 检查项 | 结果 | 详情 |
|--------|------|------|
| Arc A770M 驱动 | PASS | 32.0.101.8826 |
| oneAPI SDK 2026.0 | PASS | 已安装 |
| SYCL 编译器 | PASS | sycl-ls 可见 Arc A770M |
| Python 3.13.12 | PASS | Miniconda |
| ONEAPI_ROOT | FAIL | 未设置 |
| llama-cpp-python | PASS | 0.3.34 CPU/AVX2 (SYCL GPU 未通) |
| Qwen2.5-14B GGUF | PASS | qwen2.5-14b-instruct-q4_k_m.gguf (8.37GB) |

---

## 八、V4.0 Research Agent -- 中期规划

### 目标

AI 自动扫描市场数据，发现异常模式，生成策略假设，回测验证，输出建议。

### 工作流

```
1. 定时扫描 -> Indicator RSI + Factor 评分突变
2. 异常发现 -> RSI超卖 + A级 = 买入候选
3. 策略生成 -> AI Gateway 生成参数
4. 回测验证 -> Backtest Worker, 仅Sharpe>0
5. 输出报告 -> Dashboard
```

**前置条件:** V3.0 Freeze + 30天数据积累

---

## 九、V5.0 MT5 Bridge -- 远期规划

### 目标

Research Agent 信号通过 MT5 API 执行实盘交易。

### 核心功能

信号接收 / 风控检查 / 订单执行 / 持仓管理 / 资金曲线

**前置条件:** V4.0 Freeze + MT5 账户 + 3个月模拟盘

---

## 十、稳定性测试报告 (2026-07-31)

| # | 测试 | 结果 |
|---|------|------|
| 1 | 连续100次RSI调度 | PASS (100/100, 61.3ms avg) |
| 2 | 4 Worker并发提交 | PASS (无死锁) |
| 3 | Worker崩溃恢复 | PASS (1s检测, 1s恢复) |
| 4 | 长时间运行24h | 待运行 |
| 5 | 网络中断恢复 | 未测试 |

---

## 十一、已知问题

1. PowerShell吞输出 -> 用 python -c 内联模式
2. Xavier Python 3.6.9 -> 无pip/apt, 仅stdlib
3. 单线程HTTPServer死锁 -> 全部改用ThreadingMixIn
4. Xavier间HTTP互访不通 -> Master链路正常
5. Master探测线程阻塞 -> 修复方向: ThreadPoolExecutor

---

## 十二、文件索引

| 文件 | 说明 |
|------|------|
| TRADERS_MASTER.md | 项目总纲 (本文件) |
| CONTEXT.md | 完整会话上下文 |
| TODO.md | 版本任务清单 |
| ROADMAP_NEXT.md | 版本路线图 |
| V3_AI_GATEWAY_SPEC.md | V3.0 设计文档 |
| CHANGELOG.md | 变更记录 |
| DECISIONS.md | 决策记录 |
| AGENTS.md | AI 协作规则 |

---

## 十三、AI 接手指南

新开对话时，AI 按以下顺序读取文件即可接手：

1. **TRADERS_MASTER.md** -- 全局概览 + 硬件 + 状态
2. **CONTEXT.md** -- 网络/SSH/API/部署/问题
3. **TODO.md** -- Phase 计划/验证清单
4. **ROADMAP_NEXT.md** -- 路线 + 行动
5. **AGENTS.md** -- 协作规则
6. 按需: V3_AI_GATEWAY_SPEC.md / DECISIONS.md / CHANGELOG.md
7. 代码: master/api/app/service/task_service.py
