# DIFF 2026-08-23 — 用这笔数字问 AI

不是 V4。不改 Master / Worker。不自动推理。

## 行为

- 算完出现下一步条：摘要 +「用这笔数字问 AI」（只滚动定位）。
- 通义千问离线时禁用提问。
- 真正发送仍要点「问 AI」。

## 冒烟

`tests/smoke/10_ai_next.py` → `SMOKE_10_PASS`
