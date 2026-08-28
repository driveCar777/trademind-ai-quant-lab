#!/usr/bin/env python3
"""Write TRADERS_MASTER.md remaining sections."""
import os

PATH = r'd:\AGXXAIVER-4-WINDOWS-1-STOCK\TRADERS_MASTER.md'

part5 = """
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
| llama-cpp-python | FAIL | 待安装 |
| Qwen2.5-14B GGUF | FAIL | 待下载 |

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
"""

with open(PATH, 'a', encoding='utf-8') as f:
    f.write(part5)
print('Part5 OK,', len(part5), 'chars')
