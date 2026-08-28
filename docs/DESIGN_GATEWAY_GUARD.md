# Phase 1 Design — 通义千问内存 / 并发防护

> **模块：** V3 运维补强（不是 V4）  
> **日期：** 2026-08-23  
> **状态：** Phase 3 Smoke 11 PASS（2026-08-23）。正在跑的网关需重启才加载锁。

## 1. 事实

本机 32GB。Qwen2.5-14B Q4 加载后约 9–10GB。SYCL `F16=ON` 曾 Abort。双开推理或超大 `max_tokens` 会把实验室挤垮。V4 还要叠一层编排，必须先单路。

## 2. 决定

| 项 | 做法 |
|----|------|
| 并发 | `generate()` 一把锁。第二路立刻失败，不等待排队 |
| 长度 | `max_tokens` 上限 1024；对话最多 4 条、每条最多 4000 字 |
| 启动 | `start_sycl.bat` 写死 `GGML_SYCL_F16=OFF`；禁止设 `ONEAPI_DEVICE_SELECTOR` |
| 上下文 | 每次 `reset()`（已有），不改 `n_ctx=4096`（已验证，本轮不重测加载） |

第二路：网关 HTTP 503，`detail` 含 `busy`。不新造 Master 错误码。Master 仍原样转发。

## 3. 不做

- 不重编 llama、不改 n_ctx、不重启用户正在跑的网关（代码下次启动生效）
- 不网页重启模型、不开始 V4 实现

## 4. 五阶段

1 Design 本文 + Decision 023  
2 Implement `inference.py` / `server.py` / `start_sycl.bat`  
3 Smoke `tests/smoke/11_gateway_guard.py`（读源码 + 截断单测，不真推理）  
4 / 5 不做
