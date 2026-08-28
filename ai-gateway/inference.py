"""LLM Inference Engine for AI Gateway V3.0.

Wraps llama-cpp-python with the Intel Arc SYCL backend.

NOTE: `llama_cpp` is imported *lazily* inside `load()`/`generate()` rather than
at module import time. This is a deliberate deviation from the original SPEC so
that the module (and the whole FastAPI app) can be imported and white-box tested
even before Phase 1.5 installs the native extension. Without the extension the
engine reports `is_loaded == False` and the API degrades gracefully (503).
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_GEN_TOKENS = 1024
MAX_MESSAGES = 4
MAX_MESSAGE_CHARS = 4000


class EngineBusy(RuntimeError):
    """A second generate() arrived while the 14B model is already running."""


class InferenceEngine:
    """封装 llama-cpp-python 推理逻辑，支持模型缺失时优雅降级。"""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,  # -1 = offload all layers to GPU
        n_threads: int = 4,
        verbose: bool = False,
    ) -> None:
        self.model_path = Path(model_path)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose

        self._model: Any = None
        self._load_error: Optional[str] = None
        self._lock = threading.Lock()

        # 累计统计（修复 SPEC 中 stats.avg_latency_ms 的 TODO）
        self._total_requests = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    def load(self) -> None:
        """加载模型到 GPU；任何失败都记录错误并保留未加载状态。"""
        # 先检查原生扩展是否可用（Phase 1.5 的核心依赖），再检查模型文件。
        # 这样在库未安装时，错误信息明确指向 llama_cpp 而非模型路径。
        try:
            from llama_cpp import Llama  # noqa: F401  (lazy import)
        except Exception as exc:  # ImportError or any native load failure
            self._load_error = f"llama_cpp unavailable: {exc}"
            logger.error(self._load_error)
            return

        if not self.model_path.exists():
            self._load_error = f"Model not found: {self.model_path}"
            logger.error(self._load_error)
            return

        try:
            self._model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                n_batch=512,
                flash_attn=False,
                verbose=self.verbose,
            )
            self._load_error = None
            logger.info("AI Gateway model loaded: %s", self.model_path)
        except Exception as exc:
            self._load_error = f"Model load failed: {exc}"
            logger.error(self._load_error)
            self._model = None

    def unload(self) -> None:
        """释放模型。"""
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """生成文本。

        Returns:
            {
                "text": str,
                "tokens_used": int,
                "latency_ms": float,
                "finish_reason": str
            }
        """
        if not self.is_loaded:
            raise RuntimeError(self._load_error or "Model not loaded")

        messages = self.prepare_messages(messages)
        try:
            max_tokens = int(max_tokens)
        except (TypeError, ValueError):
            max_tokens = 256
        max_tokens = max(1, min(max_tokens, MAX_GEN_TOKENS))

        if not self._lock.acquire(blocking=False):
            raise EngineBusy("AI Gateway busy")

        try:
            # Each request is independent. Do not keep previous chats in the context window.
            if hasattr(self._model, "reset"):
                self._model.reset()

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
            self._total_latency_ms += latency_ms

            return {
                "text": text,
                "tokens_used": tokens_used,
                "latency_ms": round(latency_ms, 1),
                "finish_reason": choice.get("finish_reason", "unknown"),
            }
        finally:
            self._lock.release()

    def prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Keep the last few short messages so 32GB does not ingest a novel."""
        trimmed = list(messages or [])[-MAX_MESSAGES:]
        out: List[Dict[str, str]] = []
        for item in trimmed:
            content = str(item.get("content") or "")
            if len(content) > MAX_MESSAGE_CHARS:
                content = content[:MAX_MESSAGE_CHARS] + "\n...(truncated)"
            out.append({
                "role": str(item.get("role") or "user"),
                "content": content,
            })
        return out

    @property
    def stats(self) -> Dict[str, Any]:
        avg = (
            round(self._total_latency_ms / self._total_requests, 1)
            if self._total_requests
            else 0
        )
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": avg,
        }
