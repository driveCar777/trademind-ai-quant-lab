# Paper Hot Desk V1 — 高风险热点实验台

**日期：** 2026-09-10  
**端口：** `http://127.0.0.1:9001/paper`  
**主线冻结：** `http://127.0.0.1:9000/paper`（V2.1 / V26.8）一字不改。

## 为什么另开端口

用户要在上一版上加激进功能（不定 20 日、联网、打标签、短线/做T、热点龙头、国际局势与资金定仓）。这些与已冻结的 V26.8 / V33 / V34 冲突。另开进程，旧台继续跑。

## 不做

- 不改 `daily.py` / ML1 / `LEDGER_TOP20` / 主线 `JOURNAL.json` / `paper.html` / `paper_ops.py`
- 不 `order_send`
- 不把本仓库交给 Cloud Agent（`repos` 不传 = 无仓库 Agent）
- 不把本台结果当成 Candidate 或回测合同

## 做

- 独立成交日志 `live/paper_hot/JOURNAL.json`
- Cursor API：`GET /v1/models` 填下拉（Grok 额外列出 Extra High / Fast 变体）；`POST /v1/agents`（无仓库）出今日简报。官方模型名是 `grok-4.6`，Extra High Fast = `model.params`。失败必须写进 `BRIEF_RUN.error` 并显示在页面。
- 密钥只读 `D:\Cursor\APIKey.txt`（或环境变量）
- 普通账户 T+1 写在页面上

## 启动

`scripts\start_hot_desk.bat` → Master venv uvicorn `app.hot_main:app` `:9001`  
`start_all.bat` 仍只管 `:9000`。
