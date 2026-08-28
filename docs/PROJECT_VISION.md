# TradeMind AI Quant Lab — 项目总览

> **最后更新:** 2026-08-01
> **当前版本:** V1.2.0 (Master) / V2.1.0 (Backtest) / V3.0 (AI Gateway, Phase 0+1 完成)
> **项目状态:** V1.0-V2.1 全线冻结, V3.0 进行中

---

## 一、项目愿景

### 一句话目标

构建一套**完全本地化**的 AI 量化研究与投研实验平台，整合 A 股数据、MT5 外汇、AI 模型与 Jetson 分布式计算集群。一人 + AI 长期协作维护。

### 最终目标 (V5.0)

```
Windows Master (调度 + AI + MT5 + Dashboard)
    |
    | REST API
Jetson Xavier Cluster (分布式计算, 4 节点)
    |
    +-- Indicator Worker: 外汇/股票技术指标实时计算 (RSI/MACD/EMA/SMA)
    +-- Factor Worker: A股基本面因子评分 (50只/15因子/五维评分)
    +-- Backtest Worker: 策略回测与优化 (7策略/滑点手续费/高级指标)
    +-- Monitor Worker: 集群 GPU/系统监控
    +-- AI Gateway: 本地 LLM 推理 (Arc A770M, 投研报告/策略描述/信号解读)
    +-- Research Agent: AI 驱动量化研究 (自动发现异常/生成策略/回测验证)
        |
        v
MT5 实盘交易 <-- 信号输出
```

### 六大核心能力

| # | 能力 | 说明 | 当前状态 |
|---|------|------|----------|
| 1 | **A 股研究** | 本地 A 股数据接入、50只股票、15因子、五维评分 | DONE (V2.0) |
| 2 | **MT5 外汇** | MetaTrader 5 外汇/期货实盘与回测 | DONE (V2.1, 7策略) |
| 3 | **AI 推理** | Arc A770M 本地 LLM, 投研报告/策略描述/信号解读 | IN PROGRESS (V3.0) |
| 4 | **分布式计算** | 4x Xavier NX 并行, REST 调度, 自动重试/超时/健康探测 | DONE (4节点在线) |
| 5 | **实时监控** | GPU/系统状态, 集群健康度, Dashboard 可视化 | DONE (V1.0) |
| 6 | **Web Dashboard** | 任务管理、结果可视化、一键提交 | DONE (V1.3) |

---

## 二、版本路线图

| 版本 | 里程碑 | 状态 | 冻结日期 | 核心内容 |
|------|--------|------|----------|----------|
| V1.0 | Worker Template | FROZEN | 2026-07-25 | indicator-worker 模板 + Docker 部署 |
| V1.1 | Master API + 端到端 | FROZEN | 2026-07-25 | REST 调度 + 4 Worker 通信 |
| V1.2 | Master 增强 | FROZEN | 2026-07-31 | 自动重试/超时/健康探测/任务列表 |
| V1.3 | Dashboard | FROZEN | 2026-07-31 | Web 面板 (Worker状态/任务列表/一键提交) |
| V2.0 | Factor Worker 增强 | FROZEN | 2026-07-31 | 50只/15因子/五维评分/行业对比/分位数 |
| V2.1 | Backtest Worker 增强 | FROZEN | 2026-07-31 | 7策略/滑点手续费/高级指标/资金曲线 |
| **V3.0** | **AI Gateway** | **IN PROGRESS** | — | **Arc A770M LLM 推理/投研报告/策略描述** |
| V4.0 | Research Agent | TODO | — | AI 自动发现异常/生成策略/回测验证 |
| V5.0 | MT5 Bridge | TODO | — | 实盘交易/风控/仓位管理 |

---

## 三、系统架构

### 3.1 网络拓扑

```
Windows Master (localhost:192.168.1.101)
    |
    | REST API (FastAPI + Uvicorn, port 9000)
    | AI Gateway (port 9100, 进行中)
    |
Jetson Xavier Cluster (局域网, 0-1ms 延迟)
    |
    +-- Xavier-01 (192.168.1.200:8080) -- Indicator Worker (Docker, FastAPI)
    +-- Xavier-02 (192.168.1.201:8080) -- Stock Factor Worker (stdlib server.py)
    +-- Xavier-03 (192.168.1.202:8080) -- Backtest Worker (stdlib server.py)
    +-- Xavier-04 (192.168.1.203:8080) -- Monitor Worker (stdlib server.py)
```

### 3.2 组件清单

| 组件 | 版本 | 状态 | 节点 | 端口 | 部署方式 | 文件 |
|------|------|------|------|------|----------|------|
| Master API | v1.2.0 | FROZEN | localhost | 9000 | FastAPI + Uvicorn | `master/api/app/` |
| Dashboard | v1.3 | FROZEN | localhost | 9000/dashboard | 单文件 HTML | `dashboard/index.html` |
| AI Gateway | v3.0 | IN PROGRESS | localhost | 9100 | FastAPI + llama-cpp-python | `ai-gateway/` |
| Indicator Worker | v1.0 | FROZEN | Xavier-01 | 8080 | Docker (8080->8000) | `indicator-worker/` |
| Factor Worker | v2.0 | FROZEN | Xavier-02 | 8080 | stdlib server.py | `factor-worker-v1/server.py` |
| Backtest Worker | v2.1 | FROZEN | Xavier-03 | 8080 | stdlib server.py | `backtest-worker-v1/server.py` |
| Monitor Worker | v1.0 | FROZEN | Xavier-04 | 8080 | stdlib server.py | `monitor-worker-v1/server.py` |

### 3.3 Master API 路由表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | Master 健康检查 |
| `/workers` | GET | Worker 列表 (4/4 ONLINE, 含延迟) |
| `/tasks` | GET | 最近任务列表 (?limit=N) |
| `/task` | POST | 提交任务 (同步执行) |
| `/task/{id}` | GET | 查询任务详情 |
| `/dashboard` | GET | Dashboard 静态文件 |

---

## 四、网络与 SSH

| 节点 | IP | 用户名 | 密码 | sudo 密码 |
|------|-----|--------|------|-----------|
| Master | localhost (192.168.1.101) | Phoenix | -- | -- |
| Xavier-01 | 192.168.1.200 | dji | <TRADEMIND_XAVIER_PASSWORD> | <TRADEMIND_XAVIER_PASSWORD> |
| Xavier-02 | 192.168.1.201 | dji | <TRADEMIND_XAVIER_PASSWORD> | <TRADEMIND_XAVIER_PASSWORD> |
| Xavier-03 | 192.168.1.202 | dji | <TRADEMIND_XAVIER_PASSWORD> | <TRADEMIND_XAVIER_PASSWORD> |
| Xavier-04 | 192.168.1.203 | dji | <TRADEMIND_XAVIER_PASSWORD> | <TRADEMIND_XAVIER_PASSWORD> |

- SSH 端口: 22, 协议: OpenSSH
- Xavier 架构: aarch64 (ARM64)
- Python 版本: 3.6.9 (Xavier 系统自带)
- 网络延迟: 0-1ms (局域网)

---

## 五、Worker 详情

### 5.1 Indicator Worker (Xavier-01, Docker)

- **端点:** GET /health, GET /version, POST /indicator
- **支持指标:** SMA, EMA, RSI, MACD
- **部署:** Docker (trademind-indicator:1.0.0)
- **状态:** FROZEN

### 5.2 Stock Factor Worker (Xavier-02, stdlib)

- **端点:** GET /health, GET /version, GET /factors, POST /factor
- **股票池:** 50 只 A 股 (12 行业)
- **因子数:** 15 个 (ROE/PE/PB/PS/股息率/市值/营收增速/利润增速/ROE均值/负债率/流动比/动量/波动率/量比)
- **评分:** 五维百分制 (价值25 + 质量25 + 动量20 + 风险15 + 流动性15)
- **等级:** S(85-100) / A(70-84) / B(55-69) / C(40-54) / D(0-39)
- **状态:** FROZEN

### 5.3 Backtest Worker (Xavier-03, stdlib)

- **端点:** GET /health, GET /version, GET /strategies, POST /backtest
- **策略:** 7 个 (EMA_MACD, RSI, SMA_CROSS, TURTLE, GRID, BOLLINGER, VWAP)
- **高级指标:** Sharpe/Sortino/Calmar 比率, 盈亏比, 资金曲线 (50点)
- **滑点/手续费:** slippage_bps + commission_bps 参数
- **状态:** FROZEN

### 5.4 Monitor Worker (Xavier-04, stdlib)

- **端点:** GET /health, GET /metrics, GET /services, GET /cluster, POST /monitor
- **监控:** CPU/RAM/Disk/GPU/网络/进程数
- **状态:** FROZEN

---

## 六、V3.0 AI Gateway (进行中)

### 6.1 目标

在 Windows Master 上部署 Arc A770M 本地 LLM，提供:
- 投研报告自动生成 (输入: 因子数据 + 市场数据)
- 策略自然语言描述 (输入: 回测结果)
- 信号解读 (输入: 技术指标)
- 通用对话 (调试用)

### 6.2 推理框架

**llama-cpp-python + Intel Arc SYCL 后端** (GGUF 量化模型)

| 组件 | 选型 | 说明 |
|------|------|------|
| 推理框架 | llama-cpp-python | SYCL 后端支持 Intel Arc |
| 模型格式 | GGUF Q4_K_M | ~8.37GB |
| 首选模型 | Qwen2.5-14B-Instruct | 中文投研最佳 |

### 6.3 当前进度

| Phase | 名称 | 状态 | 说明 |
|-------|------|------|------|
| 0 | 环境准备 | DONE | Arc A770M 驱动 32.0.101.8826 + oneAPI 2026.0 + Python 3.13.12 |
| 1 | 模型下载 | DONE | Qwen2.5-14B GGUF (8.37GB) 已下载 |
| 1.5 | 编译安装 | BLOCKED | Qwen2.5-14B-Instruct SYCL 后端编译阻塞 |
| 2 | 核心实现 | TODO | server.py + inference.py + prompts.py |
| 3 | API 对接 | TODO | Master proxy + Dashboard AI 按钮 |
| 4 | 冒烟测试 | TODO | 6 个端点逐个验证 |
| 5 | 性能调优 | TODO | 延迟优化 + 缓存 |
| 6 | 冻结 | TODO | 文档更新 + CHANGELOG |

### 6.4 本地环境

| 项目 | 状态 | 详情 |
|------|------|------|
| GPU | DONE | Intel Arc A770M, 驱动 32.0.101.8826 |
| oneAPI | DONE | 2026.0, sycl-ls 可见 Arc A770M |
| Python | DONE | 3.13.12 (Miniconda), qwen-ai conda 环境 |
| venv | DONE | ai-gateway/.venv (fastapi/uvicorn/pydantic/pyyaml/huggingface-hub) |
| 模型 | DONE | qwen2.5-14b-instruct-q4_k_m.gguf (8.37GB) |
| Qwen2.5-14B-Instruct | BLOCKED | SYCL 后端编译为阻塞项 |

### 6.5 已创建文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `ai-gateway/prompts.py` | DONE | 3 个 prompt 模板 (投研/策略/信号) |
| `ai-gateway/config.yaml` | DONE | 端口 9100 / 模型路径 / n_ctx 4096 |
| `ai-gateway/requirements.txt` | DONE | 6 个依赖 |
| `ai-gateway/tests/test_server.py` | DONE | 6 个冒烟测试用例 |
| `ai-gateway/server.py` | DONE | FastAPI 入口 |
| `ai-gateway/inference.py` | DONE | LLM 推理引擎封装 |

### 6.6 API 端点设计

| 端点 | 说明 | 输入 | 输出 |
|------|------|------|------|
| `GET /health` | 健康检查 + GPU 状态 | 无 | GPU 信息/模型状态 |
| `GET /models` | 已加载模型列表 | 无 | 模型名称/状态 |
| `POST /api/v1/ai/generate` | 投研报告 | 因子+市场数据 | Markdown 报告 |
| `POST /api/v1/ai/describe` | 策略描述 | 回测结果 | 策略评估文本 |
| `POST /api/v1/ai/signal` | 信号解读 | 技术指标 | 信号分析 |
| `POST /api/v1/ai/chat` | 通用对话 | messages | 回复文本 |

---

## 七、已知问题

### 7.1 环境限制

1. **Python 3.6.9** -- Xavier 系统自带, 不可升级, 所有 Worker 必须兼容
2. **无 Docker Hub** -- Xavier 上无法拉取镜像, 必须本地构建后 SCP 传输
3. **无 pip/apt** -- Xavier 上无法安装包, 仅 stdlib 可用
4. **无 nvidia-smi** -- GPU 监控受限

### 7.2 Python 3.6 兼容要点

- 禁用 `subprocess.run(capture_output=True)` -> 用 `stdout=PIPE` + `.decode()`
- 禁用 `subprocess.run(text=True)` -> 用 `.decode()`
- 禁用 `match/case` (3.10+) -> 用 `if/elif`
- f-strings 可用 (3.6+)

### 7.3 架构限制

- 单线程 HTTPServer 会死锁自探 -> 已用 ThreadingMixIn 解决
- Xavier 间 HTTP 互访不通 -> Master->Worker 链路正常
- PowerShell 执行 Python 脚本文件时 stdout 为空 -> 用内联 `-c` 模式
- Master 后台探测线程串行, 单个 Worker 超时会阻塞后续探测

### 7.4 V3.0 阻塞项

- Qwen2.5-14B-Instruct SYCL 后端编译为 Phase 1.5 阻塞项
- 备选: OpenVINO 后端 / CPU fallback

---

## 八、稳定性测试报告 (2026-07-31 完成)

| # | 测试 | 结果 | 详情 |
|---|------|------|------|
| 1 | 连续 100 次 RSI 调度 | PASS | 100/100 COMPLETED, 平均 61.3ms/task |
| 2 | 4 Worker 并发提交 | PASS | Indicator/Factor/Backtest/Monitor 同时提交全部 COMPLETED |
| 3 | Worker 崩溃恢复 | PASS | kill->1s内检测OFFLINE->TM-1002->重启->1s内恢复ONLINE |
| 4 | 长时间运行 24h | PENDING | 脚本已就绪, 需手动启动 |
| 5 | 网络中断恢复 | NOT TESTED | 需 iptables 操作 |

---

## 九、读取顺序 (给新 AI)

1. **PROJECT_OVERVIEW.md** -- 本文件 (项目全貌)
2. **CONTEXT.md** -- 完整上下文 (网络/角色/API/部署/问题)
3. **V3_AI_GATEWAY_SPEC.md** -- V3.0 AI Gateway 详细设计
4. **TODO.md** -- 当前任务 (Phase 计划/测试清单)
5. **AGENTS.md** -- AI 协作规则
6. **按需读** -- DECISIONS.md / CHANGELOG.md
7. **看代码** -- `master/api/app/service/task_service.py` (核心调度)

---

## 十、下一步行动

### 短期 (V3.0)

1. **解决 Qwen2.5-14B-Instruct 编译阻塞** -- 尝试 OpenVINO 后端或 CPU fallback
2. **实现 server.py + inference.py** -- Phase 2 核心实现
3. **Master proxy 对接** -- Phase 3 API 集成
4. **冒烟测试** -- Phase 4 端点验证

### 中期 (V4.0)

- Research Agent: AI 自动扫描市场数据, 发现异常, 生成策略, 回测验证
- 前置: V3.0 Freeze + 30 天历史数据积累

### 长期 (V5.0)

- MT5 Bridge: 实盘交易链路, 风控, 仓位管理
- 前置: V4.0 Freeze + MT5 终端 + 3 个月模拟盘验证
