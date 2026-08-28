# TradeMind - 项目规划与下一步行动

> **事实以 `docs/TRADEMIND_CONTEXT.md` 为准。** 下文 2026-08-01 段落已过时，勿当现状。
> **最后更新:** 2026-08-24
> **当前版本:** V9.0 已冻结 — 人手确认后 MT5 模拟盘可进终端；实盘拒绝。
> **同花顺:** UNKNOWN，本环境没有可测官方接口。
> **项目总览:** TRADEMIND_CONTEXT.md (最高优先级) / PROJECT_VISION.md (愿景)

---


## 一、当前系统状态

### 组件清单

| 组件 | 版本 | 状态 | 节点 | 端口 | 部署方式 |
|------|------|------|------|------|----------|
| Master API | v1.2.0 | FROZEN | localhost:9000 | 9000 | FastAPI + Uvicorn |
| Indicator Worker | v1.0 | FROZEN | Xavier-01 (192.168.1.200) | 8080 | Docker (8080->8000) |
| Factor Worker | v2.0 | FROZEN | Xavier-02 (192.168.1.201) | 8080 | stdlib server.py |
| Backtest Worker | v2.1 | FROZEN | Xavier-03 (192.168.1.202) | 8080 | stdlib server.py |
| Monitor Worker | v1.0 | FROZEN | Xavier-04 (192.168.1.203) | 8080 | stdlib server.py |
| Dashboard | v1.3 | FROZEN | localhost:9000/dashboard | -- | 单文件 HTML |

### 系统架构

```
Windows Master (localhost:9000, FastAPI)
    |
    | REST (requests.post, sync)
Jetson Xavier Cluster (4 nodes, all port 8080)
    +-- Xavier-01 -- Indicator Worker (Docker, RSI/MACD/EMA/SMA)
    +-- Xavier-02 -- Factor Worker (stdlib, 50 A-shares, 15 factors, 5-dim score)
    +-- Xavier-03 -- Backtest Worker (stdlib, EMA_MACD/RSI/SMA_CROSS)
    +-- Xavier-04 -- Monitor Worker (stdlib, CPU/RAM/Disk/GPU monitor)
```

### 版本完成记录

| 版本 | 里程碑 | 冻结日期 |
|------|--------|----------|
| V1.0 | Worker Template (indicator-worker) | 2026-07-25 |
| V1.1 | Master API + 4 Worker 端到端 | 2026-07-25 |
| V1.2 | Master 增强 (重试/超时/探测/任务列表) | 2026-07-31 |
| V1.3 | Dashboard 前端 (单文件深色主题) | 2026-07-31 |
| V2.0 | Factor Worker 增强 (50只/15因子/五维评分) | 2026-07-31 |
| V2.1 | Backtest Worker 增强 (7策略/滑点/高级指标) | 2026-07-31 |

---

## 二、整体项目目标

### 愿景

构建一套**完全本地化**的 AI 量化研究与投研实验平台，整合 A 股数据、MT5 外汇、AI 模型与 Jetson 分布式计算集群。一人 + AI 长期协作维护。

### 最终目标 (V5.0)

```
Windows Master (调度 + AI + MT5 + Dashboard)
    | REST
Jetson Xavier Cluster (分布式计算)
    +-- Indicator: 外汇/股票技术指标实时计算
    +-- Factor: A股基本面因子评分
    +-- Backtest: 策略回测与优化
    +-- Monitor: 集群 GPU/系统监控
    +-- AI Gateway: 本地 LLM 推理 (Arc A770M)
    +-- Research Agent: AI驱动量化研究
        |
MT5 实盘交易 <-- 信号输出
```

### 六大核心能力

| # | 能力 | 说明 | 当前状态 |
|---|------|------|----------|
| 1 | A股研究 | 本地A股数据接入、因子分析 | DONE (V2.0) |
| 2 | MT5外汇 | MetaTrader 5 外汇/期货实盘与回测 | DONE (V1.0) -> V2.1增强 |
| 3 | AI推理 | Arc A770M 本地LLM，投研报告生成 | TODO (V3.0) |
| 4 | 分布式计算 | 4x Xavier NX 并行，REST调度 | DONE (4节点在线) |
| 5 | 实时监控 | GPU/系统状态，集群健康度 | DONE (V1.0) |
| 6 | Web Dashboard | 任务管理、结果可视化 | DONE (V1.3) |

---

## 三、版本路线图

| 版本 | 里程碑 | 状态 | 核心内容 |
|------|--------|------|----------|
| V1.0 | Worker Template | FROZEN | indicator-worker模板 + Docker部署 |
| V1.1 | Master API + 端到端 | FROZEN | REST调度 + 4 Worker通信 |
| V1.2 | Master 增强 | FROZEN | 自动重试/超时/健康探测/任务列表 |
| V1.3 | Dashboard | FROZEN | Web面板 (Worker状态/任务列表/一键提交) |
| V2.0 | Factor Worker 增强 | FROZEN | 50只/15因子/五维评分/行业对比/分位数 |
| V2.1 | Backtest Worker 增强 | FROZEN | 7策略/滑点/高级指标/资金曲线 |
| **V3.0** | **AI Gateway** | **NEXT** | **Arc A770M LLM推理/投研报告** |
| V4.0 | Research Agent | TODO | AI自动发现异常/生成策略/回测验证 |
| V5.0 | MT5 Bridge | TODO | 实盘交易/风控/仓位管理 |

---

## 四、下一步行动（详细）

### 推荐路线：稳定性测试 -> V2.1 -> V3.0

```
当前 -> 稳定性压力测试 -> V2.1 Backtest增强 -> V2.x Freeze -> V3.0 AI Gateway
         (1-2天)            (2-3天)             (1天)          (设计先行)
```

### 第 1 步：稳定性压力测试（建议先做）

**理由：** 4 个 Worker 刚上线，还没验证过连续运行/并发/崩溃恢复。如果 V2.1 部署后才发现基础不稳定，回滚成本高。

#### 1.1 连续 100 次 RSI 调度

- **目标：** 验证 Master -> Indicator Worker 链路稳定性
- **方法：** 循环提交 100 次 RSI 任务
- **预期：** 全部 COMPLETED，无 FAILED，平均延迟 < 200ms
- **检查：** 任务 ID 连续、结果文件完整、无内存泄漏

#### 1.2 4 Worker 并发提交

- **目标：** 验证 Master 处理并发请求能力
- **方法：** 同时 POST 4 个不同类型任务 (Indicator/Factor/Backtest/Monitor)
- **预期：** 4 个全部 COMPLETED
- **检查：** 无死锁、无超时、响应时间合理

#### 1.3 Worker 崩溃恢复

- **目标：** 验证 Master 检测 Worker 离线能力
- **方法：** SSH 到 Xavier-02, kill factor-worker 进程
- **预期：**
  1. Master 健康探测在 10s 内检测到 OFFLINE
  2. POST /task -> stock-factor-worker 返回 TM-1002 (Worker Offline)
  3. 重启 Worker 后自动恢复 ONLINE

#### 1.4 长时间运行 24h

- **目标：** 检测内存泄漏和服务稳定性
- **方法：** 每 5 分钟提交 1 次任务，持续 24 小时
- **预期：** 无崩溃、无 OOM、响应时间稳定
- **检查：** PID 存活、RSS 内存无增长趋势

#### 1.5 网络中断恢复

- **目标：** 验证网络恢复后 Worker 自动重连
- **方法：** iptables 临时阻断 -> 恢复
- **预期：** 阻断期间 Master 标记 OFFLINE，恢复后自动 ONLINE

---

### 第 2 步：V2.1 Backtest Worker 增强

**目标：** 在 V1.0 三个策略基础上新增 4 个策略，增加滑点/手续费模拟，增加夏普比率等高级指标。

#### 2.1 新增 4 个策略

| # | 策略 | 类型 | 入场条件 | 出场条件 | 止损 |
|---|------|------|----------|----------|------|
| 1 | TURTLE | 趋势跟踪 | 价格突破20日最高价 | 价格跌码10日最低价 | 2x ATR(14) |
| 2 | GRID | 震荡 | 价格每下跌grid_size%买入等额 | 价格每上涨grid_size%卖出等额 | 无 |
| 3 | BOLLINGER | 均值回归 | 价格跌码下轨 | 价格突破上轨 | 跌码下轨1.5x带宽 |
| 4 | VWAP | 量价 | 价格 < VWAP且量能确认 | 价格 > VWAP | 跌码VWAP 2% |

#### 2.2 滑点/手续费模型

```python
# 请求 params 可选
{
  "slippage_bps": 5,        # 滑点 (基点, 1bps = 0.01%)
  "commission_bps": 10,     # 手续费 (基点)
  "initial_capital": 10000  # 初始资金
}

# 每笔交易成本 = 交易金额 x (slippage_bps + commission_bps) / 10000
# 买入滑点: + (向上滑)
# 卖出滑点: - (向下滑)
# 手续费: 双向收取
```

#### 2.3 新增高级指标

| 指标 | 说明 | 计算公式 |
|------|------|----------|
| sharpe_ratio | 夏普比率 (年化, rf=2%) | (avg_return - rf_daily) / std_return x sqrt(252) |
| calmar_ratio | Calmar比率 | annualized_return / max_drawdown |
| sortino_ratio | Sortino比率 | 类似夏普但只计算下行波动 |
| profit_factor | 盈亏比 | sum(盄利交易) / abs(sum(亏损交易)) |
| avg_trade_duration | 平均持仓天数 | 所有交易持仓天数均值 |
| max_consecutive_wins | 最大连续盄利次数 | -- |
| max_consecutive_losses | 最大连续亏损次数 | -- |
| equity_curve | 资金曲线 | 均匀采样50个点 |

#### 2.4 Phase 计划

| Phase | 名称 | 预估时间 | 说明 |
|-------|------|----------|------|
| 1 | Design | 0.5h | 确认4策略算法参数 + 响应结构 |
| 2 | Implement | 2-3h | 4策略实现 + 滑点引擎 + 高级指标 |
| 3 | Smoke Test | 1h | 7策略逐个验证 + 边界测试 |
| 4 | Stability Test | 0.5h | 多品种多策略交叉测试 |
| 5 | Deploy + Freeze | 0.5h | SFTP上传Xavier-03 + 文档更新 |

#### 2.5 验证清单

- [ ] 7个策略全部通过冒烟测试
- [ ] 滑点/手续费正确扣减 (对比无滑点结果)
- [ ] 夏普/Calmar/Sortino计算正确
- [ ] equity_curve返回50个采样点
- [ ] Master端到端 POST /task COMPLETED
- [ ] Dashboard Backtest预设正常显示结果
- [ ] 50只股票 x 7策略 = 350次回测无崩溃

---

### 第 3 步：V2.x Freeze + 文档更新

| 任务 | 说明 |
|------|------|
| CHANGELOG.md | 添加 V2.1 变更记录 |
| CONTEXT.md | 更新 Backtest Worker 章节 (7策略/高级指标) |
| TODO.md | V2.1 标记完成, 下一步 V3.0 |
| DECISIONS.md | 如有新增决策则记录 |

---

### 第 4 步：V3.0 AI Gateway（设计先行）

> 详细设计文档: `V3_AI_GATEWAY_SPEC.md`

Arc A770M 驱动环境就绪后才能开始编码，架构设计已完成。

#### 推理框架

**llama-cpp-python + Intel Arc SYCL 后端** (GGUF 量化模型, 不用 PyTorch)

| 组件 | 选型 | 说明 |
|------|------|------|
| 推理框架 | llama-cpp-python | SYCL 后端支持 Intel Arc |
| 模型格式 | GGUF Q4_K_M | ~9GB VRAM |
| 首选模型 | Qwen2.5-14B-Instruct | 中文投研最佳 |

#### 架构

```
Dashboard / Master API (port 9000)
    ↓ REST proxy 转发
AI Gateway (port 9100, FastAPI, 独立进程)
    ↓ llama-cpp-python
Arc A770M (16GB VRAM, SYCL)
    ↓
投研报告 / 策略描述 / 信号解读 / 通用对话
```

#### 目录结构

```
ai-gateway/
├── server.py          # FastAPI 入口 (单文件)
├── inference.py       # LLM 推理引擎封装
├── prompts.py         # Prompt 模板
├── config.yaml        # 配置
├── models/            # GGUF 模型文件
├── requirements.txt   # 依赖
└── tests/             # 冒烟测试
```

#### API 端点

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 + GPU 状态 |
| `GET /models` | 已加载模型列表 |
| `POST /api/v1/ai/generate` | 投研报告 (输入: 因子+市场数据, 输出: Markdown) |
| `POST /api/v1/ai/describe` | 策略描述 (输入: 回测结果, 输出: 评估文本) |
| `POST /api/v1/ai/signal` | 信号解读 (输入: 技术指标, 输出: 信号分析) |
| `POST /api/v1/ai/chat` | 通用对话 (调试用) |

#### Phase 计划 (预估 6 天)

| Phase | 名称 | 预估 | 说明 | 状态 |
|-------|------|------|------|------|
| 0 | 环境准备 | 1天 | Arc 驱动 + oneAPI Runtime + Python 3.13 环境 + venv 创建 | ✅ DONE |
| 1 | 模型下载 | 0.5天 | Qwen2.5-14B-Instruct GGUF (8.37GB) 下载到 models/ | ✅ DONE |
| 1.5 | 推理库安装 | 0.5天 | llama-cpp-python SYCL 后端编译安装到 venv | ✅ DONE |
| 2 | 核心实现 | 2天 | inference.py + server.py (prompts.py/config 已完成) | ✅ DONE |
| 3 | API 对接 | 0.5天 | Master proxy 路由 + Dashboard AI 按钮 | ✅ DONE |
| 4 | 冒烟测试 | 0.5天 | 4 类端点逐个验证 | ✅ DONE (代理/入口; GPU 真推待补) |
| 5 | 性能调优 | 1天 | 延迟优化 + 缓存 + 异步 | 待定 |
| 6 | 冻结 | 0.5天 | 文档更新 + CHANGELOG | ✅ DONE 2026-08-22 |

> **Phase 0 环境检查结果 (2026-07-31):**
> - Intel Arc A770M 驱动 32.0.101.8826 ✅
> - oneAPI 2026.0 已安装, `sycl-ls` 可见 Arc A770M ✅
> - Python 3.13.12 (Miniconda) ✅
> - Conda 环境: qwen-ai, stock-review 等已有

> **Phase 1 实际状态 (2026-08-01):**
> - GGUF 模型已下载: `ai-gateway/models/qwen2.5-14b-instruct-q4_k_m.gguf` (8.37GB) ✅
> - venv 已创建, fastapi/uvicorn/pydantic/pyyaml/huggingface-hub 已装 ✅
> - llama-cpp-python **已安装** 0.3.34 SYCL wheel (2026-08-22) ✅
> - prompts.py / config.yaml / requirements.txt / tests/test_server.py 已完成 ✅
> - server.py / inference.py / models.py **已实现** ✅

#### 验证清单

- [ ] Arc A770M 驱动安装 + `sycl-ls` 可见
- [ ] llama-cpp-python SYCL 后端编译成功
- [ ] GGUF 模型加载成功, VRAM 占用 ~9-10GB
- [ ] `/health` 返回 GPU 信息
- [ ] `/api/v1/ai/chat` 基础对话正常
- [ ] `/api/v1/ai/generate` 投研报告生成正常
- [ ] `/api/v1/ai/describe` 策略描述正常
- [ ] `/api/v1/ai/signal` 信号解读正常
- [ ] 单次推理延迟 < 5s
- [ ] Master proxy 端到端正常
- [ ] Dashboard AI 按钮可点击

#### 前置条件

- [x] V2.1 Freeze
- [x] Arc A770M 驱动安装 (32.0.101.8826)
- [x] oneAPI Runtime 安装 (2026.0, sycl-ls 可见)
- [ ] Python 3.11+ 环境 + llama-cpp-python
- [ ] Qwen2.5-14B-Instruct GGUF 模型下载

#### 关键风险

| 风险 | 缓解 |
|------|------|
| SYCL 编译失败 | 备选: OpenVINO 后端; 或 CPU fallback |
| VRAM OOM | 更小量化 Q3_K_M 或换 7B 模型 |
| 延迟 >5s | 换 7B 模型 + prompt 缓存 |

---

## 五、中长期规划

### V4.0 Research Agent — AI 驱动量化研究

```
1. 定时扫描 (每小时)
   -> Indicator Worker: 技术指标异动检测
   -> Factor Worker: 因子评分突变检测

2. 异常发现
   -> RSI 超卖 + 因子评分 A级 = 买入信号候选

3. 策略生成
   -> AI Gateway: 基于异常生成策略参数

4. 回测验证
   -> Backtest Worker: 自动回测新策略

5. 输出报告
   -> Dashboard 展示 + 可选推送通知
```

**前置条件：** V3.0 Freeze + 至少30天历史数据积累

### V5.0 MT5 Bridge — 实盘交易链路

```
Research Agent 信号
    | REST POST /api/v1/bridge/signal
MT5 Bridge (Windows, port 9200)
    | MetaTrader 5 Python API
MT5 终端 -> 交易所执行
    |
持仓管理 / 止损止盈 / 资金管理
```

**核心功能：** 信号接收 / 风控检查 / 订单执行 / 持仓管理 / 资金曲线

**前置条件：** V4.0 Freeze + MT5终端安装 + 3个月模拟盘验证

---

## 六、关键约束与已知问题

### 技术约束

| 约束 | 说明 | 影响范围 |
|------|------|----------|
| Python 3.6.9 | Xavier系统自带, 不可升级 | 所有 stdlib Worker |
| 无 Docker Hub | Xavier上无法拉取镜像 | Docker 部署 |
| 无 pip/apt | Xavier上无法安装包 | 所有 Worker |
| 无 nvidia-smi | GPU监控受限 | Monitor Worker |

### Python 3.6 兼容要点

- 禁用 `subprocess.run(capture_output=True)` -> 用 `stdout=PIPE` + `.decode()`
- 禁用 `subprocess.run(text=True)` -> 用 `.decode()`
- 禁用 `match/case` (3.10+) -> 用 `if/elif`
- f-strings 可用 (3.6+)

### 架构限制

- 单线程 HTTPServer 会死锁自探 -> 已用 ThreadingMixIn 解决
- Xavier间 HTTP 互访不通 -> Master->Worker 链路正常
- PowerShell 执行 Python 脚本文件时 stdout 为空 -> 用内联 `-c` 模式

---

## 七、读取顺序（给新 AI）

1. **CONTEXT.md** — 完整上下文 (网络/角色/API/部署/问题)
2. **TODO.md** — 当前任务 (Phase计划/测试清单/验证清单)
3. **ROADMAP_NEXT.md** — 本文件 (整体目标/下一步/版本路线)
4. **AGENTS.md** — AI 协作规则
5. **按需读** — SPEC.md / DECISIONS.md / CHANGELOG.md
6. **看代码** — `master/api/app/service/task_service.py` (核心调度)
