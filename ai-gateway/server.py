"""TradeMind AI Gateway V3.0 - FastAPI Server.

Provides LLM-backed 投研报告 / 策略描述 / 信号解读 / 通用对话 on port 9100.
Designed to import and serve /health even when the llama_cpp native extension
is not yet installed (Phase 1.5); inference endpoints return 503 in that case.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from inference import EngineBusy, InferenceEngine
from models import ChatRequest, DescribeRequest, GenerateRequest, SignalRequest
from prompts import (
    RESEARCH_REPORT_TEMPLATE,
    SIGNAL_INTERPRET_TEMPLATE,
    STRATEGY_DESCRIBE_TEMPLATE,
    SYSTEM_PROMPT_ZH,
    dict_to_text,
)

logger = logging.getLogger(__name__)

# --- Config ---

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


CONFIG = load_config()
MODEL_PATH = CONFIG.get("model_path", "models/qwen2.5-14b-instruct-q4_k_m.gguf")
MODEL_NAME = CONFIG.get("model_name", "Qwen2.5-14B-Instruct")
N_CTX = CONFIG.get("n_ctx", 4096)
N_GPU_LAYERS = CONFIG.get("n_gpu_layers", -1)
SERVICE_NAME = CONFIG.get("service_name", "trademind-ai-gateway")
VERSION = CONFIG.get("version", "3.0.0")
PORT = CONFIG.get("port", 9100)


# --- Global engine ---

_engine: InferenceEngine | None = None
_start_time: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _start_time
    _start_time = datetime.now(timezone.utc)
    _engine = InferenceEngine(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
    )
    try:
        _engine.load()
        if _engine.is_loaded:
            logger.info("AI Gateway model loaded: %s", MODEL_NAME)
        else:
            logger.warning("AI Gateway started DEGRADED: %s", _engine.load_error)
    except Exception as exc:  # defensive: never block startup
        logger.error("Unexpected engine init error: %s", exc)
    yield
    if _engine:
        _engine.unload()
    logger.info("AI Gateway shutdown")


app = FastAPI(title="TradeMind AI Gateway", version=VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helpers ---


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uptime_seconds() -> float:
    if _start_time is None:
        return 0.0
    return round((datetime.now(timezone.utc) - _start_time).total_seconds(), 3)


def _require_engine() -> InferenceEngine:
    if _engine is None or not _engine.is_loaded:
        detail = (_engine.load_error if _engine else "Engine not initialized")
        raise HTTPException(status_code=503, detail=f"Model not loaded: {detail}")
    return _engine


def _run_generate(engine: InferenceEngine, **kwargs: Any) -> Dict[str, Any]:
    try:
        return engine.generate(**kwargs)
    except EngineBusy:
        raise HTTPException(status_code=503, detail="AI Gateway busy")


def _build_prompt(report_type: str, context: Dict[str, Any]) -> str:
    """按报告类型把 context 拼成发给模型的 prompt。"""
    if report_type == "research_report":
        return RESEARCH_REPORT_TEMPLATE.format(
            stock=context.get("stock", "unknown"),
            stock_name=context.get("stock_name", "unknown"),
            sector=context.get("sector", "unknown"),
            factors_text=dict_to_text(context.get("factors", {})),
            score_text=dict_to_text(context.get("score", {})),
            indicators_text=dict_to_text(context.get("indicators", {})),
            market_comment=context.get("market_comment", "无"),
        )
    if report_type == "strategy_description":
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
            benchmark_text=dict_to_text(context.get("benchmark", {})),
        )
    if report_type == "signal_interpretation":
        return SIGNAL_INTERPRET_TEMPLATE.format(
            symbol=context.get("symbol", "unknown"),
            timeframe=context.get("timeframe", "H4"),
            indicators_text=dict_to_text(context.get("indicators", {})),
            price_text=dict_to_text(context.get("price", {})),
        )
    return str(context)


# --- Routes ---


@app.get("/health")
def health() -> Dict[str, Any]:
    gpu_info = {"name": "unknown", "vram_total_gb": 0, "vram_used_gb": 0, "vram_percent": 0}
    loaded = bool(_engine and _engine.is_loaded)
    return {
        "success": True,
        "data": {
            "status": "healthy" if loaded else "degraded",
            "service": SERVICE_NAME,
            "version": VERSION,
            "model_loaded": loaded,
            "model_name": MODEL_NAME,
            "model_quantization": "Q4_K_M",
            "gpu": gpu_info,
            "inference": _engine.stats if _engine else {},
            "uptime_seconds": _uptime_seconds(),
            "timestamp": _now_iso(),
        },
    }


@app.get("/models")
def models() -> Dict[str, Any]:
    loaded = bool(_engine and _engine.is_loaded)
    return {
        "success": True,
        "data": {
            "models": [
                {
                    "name": MODEL_NAME,
                    "path": MODEL_PATH,
                    "loaded": loaded,
                    "quantization": "Q4_K_M",
                }
            ]
        },
    }


@app.post("/api/v1/ai/generate")
def generate_report(req: GenerateRequest) -> Dict[str, Any]:
    engine = _require_engine()
    prompt = _build_prompt(req.type, req.context)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ZH},
        {"role": "user", "content": prompt},
    ]
    result = _run_generate(
        engine,
        messages=messages,
        max_tokens=req.params.get("max_tokens", 1024),
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
            "timestamp": _now_iso(),
        },
    }


@app.post("/api/v1/ai/describe")
def describe_strategy(req: DescribeRequest) -> Dict[str, Any]:
    engine = _require_engine()
    prompt = _build_prompt(req.type, req.context)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ZH},
        {"role": "user", "content": prompt},
    ]
    result = _run_generate(
        engine,
        messages=messages,
        max_tokens=req.params.get("max_tokens", 1024),
        temperature=req.params.get("temperature", 0.3),
    )
    return {
        "success": True,
        "data": {
            "report_type": req.type,
            "description": result["text"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"],
            "model": MODEL_NAME,
            "timestamp": _now_iso(),
        },
    }


@app.post("/api/v1/ai/signal")
def interpret_signal(req: SignalRequest) -> Dict[str, Any]:
    engine = _require_engine()
    prompt = _build_prompt(req.type, req.context)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ZH},
        {"role": "user", "content": prompt},
    ]
    result = _run_generate(
        engine,
        messages=messages,
        max_tokens=req.params.get("max_tokens", 512),
        temperature=req.params.get("temperature", 0.2),
    )
    return {
        "success": True,
        "data": {
            "report_type": req.type,
            "interpretation": result["text"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"],
            "model": MODEL_NAME,
            "timestamp": _now_iso(),
        },
    }


@app.post("/api/v1/ai/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    engine = _require_engine()
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    result = _run_generate(
        engine,
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
            "model": MODEL_NAME,
            "timestamp": _now_iso(),
        },
    }


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
