# V4.0 Research Agent — Phase 1 Design

> **状态：** ✅ FROZEN（2026-08-23）。下一模块才是 V4.1。  
> **日期：** 2026-08-23

## 1. V4 要解决什么

今天的闭环是人点计算、人再点问 AI。  
V4 要变成：**人点一次「研究一笔」→ Master 编排「算一笔 + 读结果 + 问通义千问」→ 留下一份研究记录。**

这仍是研究，不是下单。不是自动选股机器人。

```
人点击
  → 选一个在线预设计算（与控制台推荐相同）
  → 现有 POST /task
  → 现有 GET /task/{id}（带 result）
  → 现有 POST /api/v1/ai/signal|describe|generate（只送摘要数字）
  → 写入 data/research/{id}.json
  → 控制台展示报告
```

## 2. 第一版冻结范围（必须小）


| 做                                     | 不做                         |
| ------------------------------------- | -------------------------- |
| 一次研究 = **1 次** Worker 任务 + **1 次** AI | 连跑因子再回测、自动扫 50 只           |
| 计算只用现有四套预设（指标/因子/回测/监控）               | AI 自己发明 JSON、新指标、新策略代码     |
| 人选「研究一笔」或指定 preset                    | 打开页面自动跑、定时 Cron            |
| 同时只跑 **1** 份研究                        | 队列、线程池、RabbitMQ、数据库        |
| 文件存储 `data/research/`                 | SQLite / Dashboard 新框架     |
| 复用 TM-1001…1005                       | 新错误码                       |
| 只动 `master/api/` + 控制台 + SPEC         | 改冻结 Worker、改 Xavier Python |


V4.1 以后才谈：AI 选哪台、两步链路、异常扫描。V5 才谈 MT5。

## 3. 接口（SPEC §16 已生效）

统一包装 `{success, message, code, data}`。

```
POST /api/v1/research/run
GET  /api/v1/research/{research_id}
GET  /api/v1/research?limit=20
```

`POST /api/v1/research/run` 请求：


| 字段       | 必填  | 说明                                                              |
| -------- | --- | --------------------------------------------------------------- |
| `preset` | 否   | `indicator` / `factor` / `backtest` / `monitor`。空 = 与控制台相同的在线推荐 |


成功 `data`：


| 字段            | 说明                            |
| ------------- | ----------------------------- |
| `research_id` | `tm-research-YYYYMMDD-NNNNNN` |
| `task_id`     | 已有任务号                         |
| `preset`      | 实际用的预设                        |
| `summary`     | 与控制台 `summarizeResult` 同级的一句话 |
| `ai_text`     | 通义千问正文                        |
| `ai_skipped`  | 网关离线/忙碌时为 true，研究仍算成功（有数字）    |


错误（复用）：


| 情况                   | code    |
| -------------------- | ------- |
| 非法 preset            | TM-1001 |
| 对应 Worker 离线 / 网关连不上 | TM-1002 |
| 任务失败                 | TM-1003 |
| 超时                   | TM-1004 |
| 已有研究在跑               | TM-1005 |


同步接口，最长跟现有 `POST /task` + AI 超时走（网关 120s）。禁止在 Master 里再开线程池。

## 4. 编排规则

1. 解析 preset；空则按 指标→因子→回测→监控 找第一台 ONLINE。
2. 四台都离线 → TM-1002，不算研究。
3. `POST /task` 用与控制台相同的预设 JSON。
4. `GET /task/{id}` 取 `result`；没有正文则失败。
5. 只把**摘要结构**交给 AI（RSI latest / 因子 score / 回测收益回撤胜率）。禁止把整条 `equity_curve` 或原始 close 数组塞进 14B。
6. 监控预设：可以不算「解读信号」，`ai_text` 用摘要或 chat 一句；或 `ai_skipped=true`。
7. 通义千问 503 busy / offline：研究记录仍保存数字，`ai_skipped=true`，`ai_text` 写明原因。人可稍后点「问 AI」。
8. 全程一把研究锁。第二份 `run` → TM-1005。



## 5. 存储

```
data/research/tm-research-20260823-000001.json
```

元数据含：`research_id, task_id, preset, summary, ai_text, ai_skipped, created_at`。  
**不含** 再复制一份完整 Worker 结果（结果仍在 `data/results/`）。

## 6. 控制台

一个主按钮：「研究一笔」。  
点下去才 `POST /api/v1/research/run`。  
列出研究记录；点开看 `summary` + `ai_text`。  
**禁止**自动提问之外再自动开第二轮。

通义千问离线：按钮仍可算数，文案写「先出数字，解读稍后」。

## 7. 与现有铁律的对齐

- Worker 不知道 Master，不改 `/health` `/ready`。  
- 环境变量仍 `TRADEMIND_*`。  
- 不硬编码新 IP。  
- Master 仍不推理，只代理 9100。  
- Python 3.8 Master；Xavier 3.6 不动。



## 8. 冒烟标准（实现阶段才跑）

1. 01 在线时 `POST /research/run` preset=indicator → 有 `task_id` 与 `summary` 含 RSI。
2. 网关若在线则有 `ai_text`；若 busy/offline 则 `ai_skipped=true` 且 HTTP 仍成功。
3. 研究进行中再 `POST` → TM-1005。
4. 非法 preset → TM-1001。
5. 控制台源码有「研究一笔」，且 `init()` 不调用 `/research/run`。



## 9. 本模块五步（每步目标）

对照总表：`docs/STAGE_GOALS.md`。

| 步 | 状态 | 这一步的目标 |
|----|------|----------------|
| 1 Design | **本文 + SPEC §16 草案 + Decision 024** | 范围锁死，确认前不写实现 |
| 2 Implement | ✅ | 三条 research 路由 + 存档 + 「研究一笔」按钮 |
| 3 Smoke | ✅ PASS | 见 §8 五条，`tests/smoke/12_research.py` |
| 4 Stability | ✅ PASS | `tests/stability/01_research.py`：10 次不崩、不双开模型 |
| 5 Freeze | ✅ | 文档对齐。下一模块 V4.1 |




## 10. 确认清单（实现前请点头）

- [x] 一次研究只跑 1 次计算 + 最多 1 次 AI  
- [x] 只用现有预设，AI 不发明任务  
- [x] 必须人点「研究一笔」  
- [x] 不做 MT5、不做队列、不加库  
- [x] 网关忙碌时研究仍保存数字  

V4.0 已冻结。