# DIFF 2026-08-23 — 一键状态以 HTTP 为准

不是 V4。不新开 Master 路由。不跑会弹窗的完整一键。

## 行为

- `start_all.bat` 用 `lab_status.py --check-master/--check-gateway`，不再 `netstat findstr`。
- 端口通但 `/health` 失败：禁止再开第二个窗口。
- `start_lab.bat` 结束列出六项；只有 `LAB_STATUS_OK` 才说都在线。

## 冒烟

`tests/smoke/09_lab_status.py` → `SMOKE_09_PASS`
