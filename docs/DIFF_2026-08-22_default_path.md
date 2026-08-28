# DIFF 2026-08-22 — 默认计算路径

不是 V4。不改 Worker 计算代码。

## 行为

- 打开控制台：推荐当前在线节点的一笔预设计算。
- 用户点「现在就计算」才 `POST /task`。刷新不自动提交。
- 算完后把数字填进 AI 框。不自动调用通义千问。
- 离线类型灰掉，提交被拒绝。

## 接口

- `GET /task/{id}` 增加 `data.result`（文件可读时）。
- `GET /tasks` 不读结果文件，`result` 恒 `null`。

## 文件

- `SPEC.md` §8.4
- `docs/DECISIONS.md` Decision 019
- `master/api/app/model/schemas.py`
- `master/api/app/service/task_service.py`
- `dashboard/index.html`
- `tests/smoke/07_default_path.py`
