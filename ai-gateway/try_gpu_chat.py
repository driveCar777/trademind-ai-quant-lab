"""One-shot SYCL GPU chat. Must run after oneAPI setvars.bat."""

from __future__ import annotations

import time
from pathlib import Path

MODEL = Path(__file__).parent / "models" / "qwen2.5-14b-instruct-q4_k_m.gguf"


def main() -> int:
    from llama_cpp import Llama

    print("loading", MODEL, flush=True)
    t0 = time.time()
    llm = Llama(
        model_path=str(MODEL),
        n_ctx=2048,
        n_gpu_layers=-1,  # full offload to Arc A770M; verified 2026-08-22
        n_batch=512,
        n_threads=4,
        flash_attn=False,
        verbose=True,
    )
    print("load_seconds", round(time.time() - t0, 1), flush=True)
    t1 = time.time()
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": "用一句话介绍你自己。"}],
        max_tokens=32,
        temperature=0.2,
    )
    text = out["choices"][0]["message"]["content"]
    tokens = out.get("usage", {}).get("completion_tokens", 0)
    elapsed = time.time() - t1
    print("reply", text, flush=True)
    print("tokens", tokens, "seconds", round(elapsed, 1), flush=True)
    print("GPU_CHAT_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
