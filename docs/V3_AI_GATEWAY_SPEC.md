# V3.0 AI Gateway — 详细设计文档

> **版本:** V3.0.0 (Draft)
> **日期:** 2026-07-31
> **状态:** 设计先行 — 等待 Arc A770M 驱动就绪后编码
> **前置依赖:** V2.1 Backtest Worker 冻结

---

## 一、目标概述

在 Windows Master 上部署本地 LLM 推理服务 (AI Gateway)，利用 Intel Arc A770M (16GB VRAM) 运行开源大模型，为量化研究提供 AI 能力：

| 能力 | 说明 | 输出 |
|------|------|------|
| **投研报告生成** | 基于因子数据 + 市场数据，自动生成结构化投研报告 | Markdown 报告 |
| **策略自然语言描述** | 将回测结果转化为可读的策略评估 | 人类可读文本 |
| **信号解读** | 对技术指标异动给出 AI 分析 | 市场观点 |
| **策略建议** | 基于当前市场状态建议参数调整 | JSON 建议 |

---

## 二、硬件与软件环境

### 2.1 硬件

| 组件 | 规格 |
|------|------|
| GPU | Intel Arc A770M, 16GB VRAM |
| CPU | Windows Master 主机 CPU |
| 内存 | 建议 >= 32GB (模型加载需要) |
| 存储 | 建议 >= 50GB 可用 (模型文件) |

### 2.2 软件栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 推理框架 | **llama.cpp (llama-cpp-python)** | Intel Arc 通过 SYCL 后端支持, GGUF 量化模型 |
| API 框架 | **FastAPI** | 与现有 Master API 一致 |
| 模型格式 | **GGUF** | llama.cpp 原生格式, 支持 Q4_K_M/Q5_K_M 量化 |
| Python | **3.11+** (Master Windows) | 不受 Xavier 3.6 限制 |
| GPU 驱动 | Intel Arc 驱动 + oneAPI Runtime | SYCL 后端必需 |

### 2.3 推荐模型

| 模型 | 参数量 | 量化 | VRAM 占用 | 说明 |
|------|--------|------|-----------|------|
| **Qwen2.5-14B-Instruct** | 14B | Q4_K_M | ~9GB | 中文能力强, 适合投研 |
| Qwen2.5-7B-Instruct | 7B | Q5_K_M | ~6GB | 轻量备选, 响应更快 |
| DeepSeek-V2-Lite-Chat | 16B (MoE) | Q4_K_M | ~10GB | 推理能力好 |

**首选: Qwen2.5-14B-Instruct Q4_K_M** — 中文投研场景最佳平衡

---

## 三、架构设计

### 3.1 系统位置

```
┌─────────────────────────────────────────────────┐
│ Windows Master (localhost:9000)                  │
│                                                  │
│  ┌──────────────┐     ┌─────────────────────┐   │
│  │ Master API   │────>│ AI Gateway          │   │
│  │ (FastAPI)    │     │ (FastAPI, port 9100)│   │
│  │ port 9000    │     │                     │   │
│  └──────────────┘     │  llama.cpp backend  │   │
│                       │  (SYCL/Arc A770M)   │   │
│                       └─────────────────────┘   │
│                                │                  │
│                         ┌──────┴──────┐          │
│                         │ Arc A770M   │          │
│                         │ 16GB VRAM   │          │
│                         └─────────────┘          │
└─────────────────────────────────────────────────┘
```

### 3.2 部署方式: 独立进程

AI Gateway 作为**独立 FastAPI 进程**运行 (port 9100)，不嵌入 Master API (port 9000)。原因：

1. **隔离性** — 模型加载失败不影响 Master API 调度
2. **资源管理** — 独立进程可独立监控内存/GPU 使用
3. **灵活性** — 可独立重启, 不影响任务调度
4. **一致性** — 与 Worker 模式一致 (单进程 FastAPI)

### 3.3 目录结构

```
ai-gateway/
├── server.py                  # FastAPI 入口 (单文件, 类似 Worker 模式)
├── inference.py               # LLM 推理引擎封装
├── prompts.py                 # Prompt 模板 (投研/策略/信号)
├── models.py                  # Pydantic 数据模型
├── requirements.txt           # 依赖
├── config.yaml                # 配置文件
├── models/                    # GGUF 模型文件目录
│   └── qwen2.5-14b-instruct-q4_k_m.gguf
└── tests/
    ├── test_server.py         # 冒烟测试
    └── test_inference.py      # 推理测试
```

---

## 四、API 设计

### 4.1 端点总览

| 端点 | 方法 | 说明 | 输入 |
|------|------|------|------|
| `GET /health` | GET | 健康检查 + GPU 状态 | 无 |
| `GET /models` | GET | 已加载模型列表 | 无 |
| `POST /api/v1/ai/generate` | POST | 生成投研报告 | 因子+市场数据 |
| `POST /api/v1/ai/describe` | POST | 策略自然语言描述 | 回测结果 |
| `POST /api/v1/ai/signal` | POST | 信号解读 | 技术指标数据 |
| `POST /api/v1/ai/chat` | POST | 通用对话 (调试用) | messages |

### 4.2 统一响应格式

与 Master API 保持一致:

```json
{
  "success": true,
  "message": "",
  "code": "TM-0000",
  "data": { ... }
}
```

### 4.3 端点详细设计

#### 4.3.1 GET /health

```json
// Response 200
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "trademind-ai-gateway",
    "version": "3.0.0",
    "model_loaded": true,
    "model_name": "Qwen2.5-14B-Instruct",
    "model_quantization": "Q4_K_M",
    "gpu": {
      "name": "Intel Arc A770M",
      "vram_total_gb": 16.0,
      "vram_used_gb": 9.2,
      "vram_percent": 57.5
    },
    "inference": {
      "total_requests": 0,
      "avg_latency_ms": 0,
      "uptime_seconds": 0
    },
    "uptime_seconds": 0,
    "timestamp": "2026-07-31T12:00:00"
  }
}
```

#### 4.3.2 POST /api/v1/ai/generate — 投研报告生成

**请求:**

```json
{
  "type": "research_report",
  "context": {
    "stock": "600519",
    "stock_name": "贵州茅台",
    "sector": "白酒",
    "factors": {
      "roe": 30.12,
      "pe": 28.5,
      "pb": 10.2,
      "market_cap_bn": 22000,
      "momentum_60d": 5.3,
      "volatility_60d": 18.2
    },
    "score": {
      "total": 82,
      "grade": "A",
      "value": 18.5,
      "quality": 23.1,
      "momentum": 16.8,
      "risk": 12.0,
      "liquidity": 11.6
    },
    "indicators": {
      "rsi_14": 55.3,
      "macd_signal": "bullish",
      "ema_trend": "upward"
    },
    "market_comment": "白酒板块近期资金流入, 北向资金增持"
  },
  "params": {
    "max_tokens": 2048,
    "temperature": 0.3,
    "language": "zh"
  }
}
```

**响应:**

```json
{
  "success": true,
  "data": {
    "report_type": "research_report",
    "stock": "600519",
    "report": "# 贵州茅台 (600519) 投研报告\n\n## 基本面概览\n...\n## 估值分析\n...\n## 技术面\n...\n## 风险提示\n...\n## 投资建议\n...",
    "key_points": [
      "ROE 持续领先行业, 盈利质量优异",
      "PE 估值处于合理区间上沿",
      "短期 RSI 中性, MACD 金叉信号"
    ],
    "risk_level": "medium",
    "tokens_used": 1523,
    "latency_ms": 3200,
    "model": "Qwen2.5-14B-Instruct",
    "timestamp": "2026-07-31T12:00:00"
  }
}
```

#### 4.3.3 POST /api/v1/ai/describe — 策略描述

**请求:**

```json
{
  "type": "strategy_description",
  "context": {
    "strategy": "EMA_MACD",
    "symbol": "XAUUSD",
    "params": {"short": 12, "long": 26, "signal": 9},
    "result": {
      "profit": -12.31,
      "max_drawdown": 21.41,
      "win_rate": 20.0,
      "total_trades": 30,
      "sharpe_ratio": -0.839,
      "profit_factor": 0.53
    },
    "benchmark": {
      "buy_and_hold": 5.2,
      "risk_free_rate": 2.0
    }
  },
  "params": {
    "max_tokens": 1024,
    "temperature": 0.3
  }
}
```

**响应:**

```json
{
  "success": true,
  "data": {
    "report_type": "strategy_description",
    "description": "## EMA_MACD 策略评估 (XAUUSD)\n\n该策略在回测期间表现不佳...\n\n### 关键问题\n1. 胜率仅 20%, 远低于盈亏平衡线\n2. 最大回撤 21.4%, 风险偏高\n3. 夏普比率为负, 风险调整后收益为负\n\n### 改进建议\n- 增加趋势过滤器避免震荡市\n- 缩短持仓周期减少回撤\n- 考虑加入 ATR 动态止损",
    "score": 25,
    "grade": "D",
    "recommendation": "不建议实盘使用, 建议优化参数或更换策略",
    "tokens_used": 856,
    "latency_ms": 1800,
    "timestamp": "2026-07-31T12:00:00"
  }
}
```

#### 4.3.4 POST /api/v1/ai/signal — 信号解读

**请求:**

```json
{
  "type": "signal_interpretation",
  "context": {
    "symbol": "EURUSD",
    "indicators": {
      "rsi_14": 28.5,
      "macd_histogram": -0.0032,
      "ema_20": 1.0820,
      "ema_50": 1.0845,
      "sma_200": 1.0810,
      "atr_14": 0.0045
    },
    "price": {
      "current": 1.0815,
      "high_24h": 1.0890,
      "low_24h": 1.0780
    },
    "timeframe": "H4"
  },
  "params": {
    "max_tokens": 512,
    "temperature": 0.2
  }
}
```

**响应:**

```json
{
  "success": true,
  "data": {
    "report_type": "signal_interpretation",
    "signal": "bullish_divergence",
    "confidence": 0.72,
    "interpretation": "RSI 进入超卖区域 (28.5), 结合价格接近 200 日均线支撑, 存在潜在反弹信号。MACD 柱状图仍为负但收窄, 下跌动能减弱。建议关注 1.0800 支撑位。",
    "suggested_action": "观望为主, 等待 RSI 回升至 30 以上确认",
    "stop_loss_suggestion": 1.0765,
    "take_profit_suggestion": 1.0880,
    "tokens_used": 412,
    "latency_ms": 980,
    "timestamp": "2026-07-31T12:00:00"
  }
}
```

#### 4.3.5 POST /api/v1/ai/chat — 通用对话 (调试用)

```json
// Request
{
  "messages": [
    {"role": "system", "content": "你是一个专业的量化投资分析师..."},
    {"role": "user", "content": "RSI 超卖时应该如何操作？"}
  ],
  "params": {
    "max_tokens": 512,
    "temperature": 0.3
  }
}

// Response
{
  "success": true,
  "data": {
    "reply": "RSI (相对强弱指标) 进入超卖区域...",
    "tokens_used": 256,
    "latency_ms": 850,
    "timestamp": "2026-07-31T12:00:00"
  }
}
```

---

## 五、核心模块设计

### 5.1 inference.py — 推理引擎

```python
"""LLM Inference Engine for AI Gateway V3.0.

Uses llama-cpp-python with Intel Arc SYCL backend.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from llama_cpp import Llama


class InferenceEngine:
    """封装 llama-cpp-python 推理逻辑."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,  # -1 = offload all to GPU
        n_threads: int = 4,
        verbose: bool = False,
    ):
        self.model_path = Path(model_path)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose
        self._model: Optional[Llama] = None
        self._total_requests = 0
        self._total_tokens = 0

    def load(self) -> None:
        """加载模型到 GPU."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        self._model = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
            n_threads=self.n_threads,
            verbose=self.verbose,
            embedding=False,
        )

    def unload(self) -> None:
        """释放模型."""
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """生成文本.

        Returns:
            {
                "text": str,
                "tokens_used": int,
                "latency_ms": float,
                "finish_reason": str
            }
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        t0 = time.time()
        result = self._model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )
        latency_ms = (time.time() - t0) * 1000

        choice = result["choices"][0]
        text = choice["message"]["content"]
        tokens_used = result.get("usage", {}).get("completion_tokens", 0)

        self._total_requests += 1
        self._total_tokens += tokens_used

        return {
            "text": text,
            "tokens_used": tokens_used,
            "latency_ms": round(latency_ms, 1),
            "finish_reason": choice.get("finish_reason", "unknown"),
        }

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": 0,  # TODO: track
        }
```

### 5.2 prompts.py — Prompt 模板

```python
"""Prompt templates for AI Gateway."""

SYSTEM_PROMPT_ZH = """你是一个专业的量化投资分析师 AI 助手。
你的职责是基于提供的数据给出客观、专业的分析。
请使用中文回复, 结构化输出, 包含关键数据引用。
不要编造数据, 只基于给定的上下文进行分析。"""

RESEARCH_REPORT_TEMPLATE = """请基于以下数据生成投研报告:

## 股票信息
- 股票代码: {stock}
- 股票名称: {stock_name}
- 行业: {sector}

## 因子数据
{factors_text}

## 评分结果
{score_text}

## 技术指标
{indicators_text}

## 市场评论
{market_comment}

请生成包含以下章节的投研报告:
1. 基本面概览
2. 估值分析
3. 技术面分析
4. 风险提示
5. 投资建议 (包含关键要点列表)
"""

STRATEGY_DESCRIBE_TEMPLATE = """请评估以下回测结果并给出专业分析:

## 策略信息
- 策略: {strategy}
- 品种: {symbol}
- 参数: {params}

## 回测结果
- 总收益: {profit}%
- 最大回撤: {max_drawdown}%
- 胜率: {win_rate}%
- 总交易次数: {total_trades}
- 夏普比率: {sharpe_ratio}
- 盈亏比: {profit_factor}

## 基准对比
{benchmark_text}

请给出:
1. 策略表现总结 (1-2 句)
2. 关键问题分析
3. 改进建议
4. 综合评分 (0-100) 和等级 (S/A/B/C/D)
5. 实盘使用建议
"""

SIGNAL_INTERPRET_TEMPLATE = """请解读以下技术指标信号:

## 品种: {symbol} ({timeframe})

## 技术指标
{indicators_text}

## 价格信息
{price_text}

请给出:
1. 当前信号判断 (看多/看空/中性)
2. 信号置信度 (0-1)
3. 技术分析解读
4. 建议操作
5. 建议止损位和止盈位
"""
```

### 5.3 server.py — FastAPI 入口

```python
"""TradeMind AI Gateway V3.0 - FastAPI Server."""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from inference import InferenceEngine
from prompts import (
    RESEARCH_REPORT_TEMPLATE,
    SIGNAL_INTERPRET_TEMPLATE,
    STRATEGY_DESCRIBE_TEMPLATE,
    SYSTEM_PROMPT_ZH,
)

logger = logging.getLogger(__name__)

# --- Config ---

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

CONFIG = load_config()
MODEL_PATH = CONFIG.get("model_path", "models/qwen2.5-14b-instruct-q4_k_m.gguf")
MODEL_NAME = CONFIG.get("model_name", "Qwen2.5-14B-Instruct")
N_CTX = CONFIG.get("n_ctx", 4096)
N_GPU_LAYERS = CONFIG.get("n_gpu_layers", -1)
PORT = CONFIG.get("port", 9100)

# --- Global engine ---

_engine: Optional[InferenceEngine] = None
_start_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _start_time
    _start_time = datetime.utcnow()
    _engine = InferenceEngine(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
    )
    try:
        _engine.load()
        logger.info("AI Gateway model loaded: %s", MODEL_NAME)
    except Exception as e:
        logger.error("Failed to load model: %s", e)
    yield
    if _engine:
        _engine.unload()
    logger.info("AI Gateway shutdown")


app = FastAPI(
    title="TradeMind AI Gateway",
    version="3.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Schemas ---

class GenerateRequest(BaseModel):
    type: str = Field(..., description="research_report | strategy_description | signal_interpretation")
    context: dict
    params: dict = {}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    params: dict = {}


# --- Routes ---

@app.get("/health")
def health():
    gpu_info = {"name": "unknown", "vram_total_gb": 0, "vram_used_gb": 0, "vram_percent": 0}
    # TODO: query GPU via sycl or ipex
    return {
        "success": True,
        "data": {
            "status": "healthy" if (_engine and _engine.is_loaded) else "degraded",
            "service": "trademind-ai-gateway",
            "version": "3.0.0",
            "model_loaded": _engine.is_loaded if _engine else False,
            "model_name": MODEL_NAME,
            "gpu": gpu_info,
            "inference": _engine.stats if _engine else {},
            "uptime_seconds": round((datetime.utcnow() - _start_time).total_seconds(), 3),
            "timestamp": datetime.utcnow(),
        },
    }


@app.get("/models")
def models():
    return {
        "success": True,
        "data": {
            "models": [
                {
                    "name": MODEL_NAME,
                    "path": MODEL_PATH,
                    "loaded": _engine.is_loaded if _engine else False,
                    "quantization": "Q4_K_M",
                }
            ]
        },
    }


@app.post("/api/v1/ai/generate")
def generate_report(req: GenerateRequest):
    if not _engine or not _engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    prompt = _build_prompt(req.type, req.context)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ZH},
        {"role": "user", "content": prompt},
    ]
    result = _engine.generate(
        messages=messages,
        max_tokens=req.params.get("max_tokens", 2048),
        temperature=req.params.get("temperature", 0.3),
    )
    return {
        "success": True,
        "data": {
            "report_type": req.type,
            "report": result["text"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"],
            "model": MODEL_NAME,
            "timestamp": datetime.utcnow(),
        },
    }


@app.post("/api/v1/ai/chat")
def chat(req: ChatRequest):
    if not _engine or not _engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    result = _engine.generate(
        messages=messages,
        max_tokens=req.params.get("max_tokens", 1024),
        temperature=req.params.get("temperature", 0.3),
    )
    return {
        "success": True,
        "data": {
            "reply": result["text"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"],
            "timestamp": datetime.utcnow(),
        },
    }


def _build_prompt(report_type: str, context: dict) -> str:
    if report_type == "research_report":
        return RESEARCH_REPORT_TEMPLATE.format(
            stock=context.get("stock", "unknown"),
            stock_name=context.get("stock_name", "unknown"),
            sector=context.get("sector", "unknown"),
            factors_text=_dict_to_text(context.get("factors", {})),
            score_text=_dict_to_text(context.get("score", {})),
            indicators_text=_dict_to_text(context.get("indicators", {})),
            market_comment=context.get("market_comment", "无"),
        )
    elif report_type == "strategy_description":
        result = context.get("result", {})
        return STRATEGY_DESCRIBE_TEMPLATE.format(
            strategy=context.get("strategy", "unknown"),
            symbol=context.get("symbol", "unknown"),
            params=str(context.get("params", {})),
            profit=result.get("profit", 0),
            max_drawdown=result.get("max_drawdown", 0),
            win_rate=result.get("win_rate", 0),
            total_trades=result.get("total_trades", 0),
            sharpe_ratio=result.get("sharpe_ratio", 0),
            profit_factor=result.get("profit_factor", 0),
            benchmark_text=_dict_to_text(context.get("benchmark", {})),
        )
    elif report_type == "signal_interpretation":
        return SIGNAL_INTERPRET_TEMPLATE.format(
            symbol=context.get("symbol", "unknown"),
            timeframe=context.get("timeframe", "H4"),
            indicators_text=_dict_to_text(context.get("indicators", {})),
            price_text=_dict_to_text(context.get("price", {})),
        )
    else:
        return str(context)


def _dict_to_text(d: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in d.items())


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

### 5.4 config.yaml

```yaml
service_name: trademind-ai-gateway
version: "3.0.0"
host: "0.0.0.0"
port: 9100
log_level: INFO

model_path: "models/qwen2.5-14b-instruct-q4_k_m.gguf"
model_name: "Qwen2.5-14B-Instruct"
n_ctx: 4096
n_gpu_layers: -1

# Timeout for single inference request
request_timeout_seconds: 120
```

### 5.5 requirements.txt

```
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pyyaml>=6.0
llama-cpp-python>=0.3.0
```

**注意:** `llama-cpp-python` 需要从源码编译以支持 Intel Arc SYCL 后端, 或使用预编译的 wheel (如果可用)。

---

## 六、与 Master API 集成

### 6.1 Master 侧新增路由

在 `master/api/app/api/routes.py` 中新增 AI 相关路由:

Master 代理路由（完整清单见 `SPEC.md` 第十四节）。URL 来自配置 `ai_gateway.url`，禁止硬编码。

```
GET  /api/v1/ai/health     → Gateway GET  /health
GET  /api/v1/ai/models     → Gateway GET  /models
POST /api/v1/ai/generate   → Gateway POST /api/v1/ai/generate
POST /api/v1/ai/describe   → Gateway POST /api/v1/ai/describe
POST /api/v1/ai/signal     → Gateway POST /api/v1/ai/signal
POST /api/v1/ai/chat       → Gateway POST /api/v1/ai/chat
```

离线 → HTTP 503 / `TM-1002`；超时 → HTTP 504 / `TM-1004`。

### 6.2 调用链路

```
Dashboard / Client
    |
    v  POST /api/v1/ai/generate
Master API (port 9000)
    |  proxy转发
    v  POST /api/v1/ai/generate
AI Gateway (port 9100)
    |  llama.cpp inference
    v
Arc A770M GPU
    |
    v  生成文本
AI Gateway -> Master API -> Client
```

### 6.3 Dashboard 集成

在 `dashboard/index.html` 中新增:

1. **AI 报告按钮** — 选择任务结果后点击 "AI 分析" 按钮
2. **AI 报告展示** — 模态框显示 Markdown 渲染后的报告
3. **AI Gateway 状态** — Worker 面板新增 AI Gateway 卡片

---

## 七、安装与部署

### 7.1 前置条件安装

```powershell
# 1. 安装 Intel Arc 驱动
# 下载 Intel Arc GPU 驱动 + oneAPI Runtime
# https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

# 2. 安装 oneAPI Runtime (SYCL 后端)
# 下载 Intel oneAPI Runtime
# https://www.intel.com/content/www/us/en/developer/tools/oneapi/runtime-download.html

# 3. 创建 Python 环境
cd ai-gateway
python -m venv .venv
.\.venv\Scripts\activate

# 4. 安装 llama-cpp-python (需要 SYCL 支持)
# 方式A: 使用预编译 wheel (如果可用)
pip install llama-cpp-python

# 方式B: 从源码编译 (需要 SYCL 编译器)
# SET CMAKE_ARGS="-DGGML_SYCL=ON"
# pip install llama-cpp-python --no-cache-dir --force-reinstall

# 5. 安装其他依赖
pip install -r requirements.txt
```

### 7.2 下载模型

```powershell
# 下载 Qwen2.5-14B-Instruct Q4_K_M
mkdir models
# 从 HuggingFace 下载 GGUF 文件
# https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF
# 下载 qwen2.5-14b-instruct-q4_k_m.gguf (~8.5GB)
```

### 7.3 启动

```powershell
# 启动 AI Gateway
Set-Location "d:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway"
& ".\.venv\Scripts\python.exe" server.py

# 或使用 uvicorn
& ".\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 9100
```

### 7.4 验证

```powershell
# 健康检查
curl http://localhost:9100/health

# 模型列表
curl http://localhost:9100/models

# 通用对话测试
curl -X POST http://localhost:9100/api/v1/ai/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"你好"}]}'

# 投研报告测试
curl -X POST http://localhost:9100/api/v1/ai/generate -H "Content-Type: application/json" -d '{"type":"research_report","context":{"stock":"600519","stock_name":"贵州茅台"}}'
```

---

## 八、Phase 计划

| Phase | 名称 | 预估时间 | 说明 | 前置条件 |
|-------|------|----------|------|----------|
| 0 | 环境准备 | 1天 | Arc 驱动安装 + oneAPI + Python 环境 | 无 |
| 1 | 模型下载 | 0.5天 | 下载 Qwen2.5-14B GGUF + 验证加载 | Phase 0 |
| 2 | 核心实现 | 2天 | inference.py + prompts.py + server.py | Phase 1 |
| 3 | API 对接 | 0.5天 | Master 路由 + Dashboard 集成 | Phase 2 |
| 4 | 冒烟测试 | 0.5天 | 4 类端点逐个验证 | Phase 3 |
| 5 | 性能调优 | 1天 | 延迟优化 + 批处理 + 缓存 | Phase 4 |
| 6 | 冻结 | 0.5天 | 文档更新 + CHANGELOG | Phase 5 |

**总预估: 6 天** (不含环境准备的不确定性)

---

## 九、验证清单

### Phase 0: 环境

- [ ] Intel Arc 驱动安装成功
- [ ] oneAPI Runtime 安装成功
- [ ] `sycl-ls` 能看到 Arc A770M
- [ ] Python 3.11+ 环境创建成功
- [ ] llama-cpp-python 安装成功 (SYCL 后端)

### Phase 1: 模型

- [ ] GGUF 模型文件下载完成
- [ ] 模型文件完整性校验 (SHA256)
- [ ] Llama() 加载成功, 无报错
- [ ] GPU VRAM 占用正确 (~9-10GB)

### Phase 2: 核心

- [ ] `/health` 返回 GPU 信息
- [ ] `/models` 返回已加载模型
- [ ] `/api/v1/ai/chat` 基础对话正常
- [ ] `/api/v1/ai/generate` 投研报告生成正常
- [ ] `/api/v1/ai/describe` 策略描述正常
- [ ] `/api/v1/ai/signal` 信号解读正常

### Phase 3: 集成

- [ ] Master API 代理路由正常
- [ ] Dashboard AI 按钮可点击
- [ ] 报告在 Dashboard 中正确显示

### Phase 4: 性能

- [ ] 单次推理延迟 < 5s (14B Q4)
- [ ] 10 并发请求无崩溃
- [ ] 连续运行 1 小时无内存泄漏
- [ ] VRAM 占用稳定 (无持续增长)

---

## 十、风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| llama-cpp-python SYCL 编译失败 | 无法使用 Arc GPU | 备选: 使用 OpenVINO 后端; 或回退到 CPU 推理 |
| 模型加载 OOM | VRAM 不足 | 使用更小的量化 (Q3_K_M) 或更小的模型 (7B) |
| 推理延迟过高 | 用户体验差 | 使用 7B 模型; 增加缓存; 异步处理 |
| Arc 驱动不兼容 | GPU 无法使用 | 等待 Intel 修复; 临时 CPU fallback |
| 模型下载被墙 | 无法获取模型 | 使用镜像站; 或离线传输 |

---

## 十一、与 V4.0 Research Agent 的接口

V3.0 AI Gateway 为 V4.0 Research Agent 提供 AI 能力基础:

```
V4.0 Research Agent
    |
    | POST /api/v1/ai/signal (信号解读)
    | POST /api/v1/ai/generate (报告生成)
    | POST /api/v1/ai/chat (策略讨论)
    |
    v
V3.0 AI Gateway (port 9100)
    |
    v
Arc A770M LLM 推理
```

Research Agent 的工作流中每一步都可以调用 AI Gateway:

1. **异常发现** → AI 解读异常信号
2. **策略生成** → AI 建议策略参数
3. **回测评估** → AI 分析回测结果
4. **报告输出** → AI 生成最终报告
