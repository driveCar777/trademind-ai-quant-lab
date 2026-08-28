# DIFF 2026-08-23 — 网关单路推理

不是 V4 实现。不重载正在跑的模型进程。

- `inference.py`：锁、token/消息上限、`EngineBusy`
- `server.py`：busy → 503
- `start_sycl.bat`：`GGML_SYCL_F16=OFF`

`tests/smoke/11_gateway_guard.py` → PASS
