# TradeMind — 测试计划

> 所有模块必须通过对应测试，才允许进入下一阶段或冻结。

---

## 测试层级

| 层级 | 目录 | 时机 |
|------|------|------|
| 冒烟测试 | `tests/smoke/` | 实现完成后立即执行 |
| 稳定性测试 | `tests/stability/` | 冒烟 PASS 后执行 |
| 单元测试 | 各模块 `tests/` | 实现过程中 |

---

## V1.1 Implement 测试进度

```
Smoke       ░░░░░░░░░░   0%  待 Phase 4
Stability   ░░░░░░░░░░   0%  待 Phase 7
Freeze      ░░░░░░░░░░   0%  待 Phase 8
```

---

## 模块测试状态

| 模块 | 冒烟测试 | 稳定性测试 | 冻结 |
|------|----------|------------|------|
| Worker Template (indicator-worker) | ✅ PASS | ✅ PASS | ✅ 已冻结 |
| Master API | ⬜ 待测 | ⬜ 待测 | ⬜ |
| Master ↔ Worker 端到端 | ⬜ 待测 | ⬜ 待测 | ⬜ |
| Dashboard | ⬜ 待测 | ⬜ 待测 | ⬜ |
| SDK | ⬜ 待测 | ⬜ 待测 | ⬜ |
| Factor Worker | ⬜ 待测 | ⬜ 待测 | ⬜ |
| Backtest Worker | ⬜ 待测 | ⬜ 待测 | ⬜ |

---

## Worker Template — 冒烟测试 ✅

**文件：** `workers/indicator-worker/tests/`（V1.0 已通过）

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 健康检查 | `GET /health` 返回 200 | ✅ |
| 2 | 就绪探针 | `GET /ready` 返回 200 | ✅ |
| 3 | RSI 计算 | `POST /api/v1/indicator/calculate` 返回 JSON | ✅ |
| 4 | 指标列表 | `GET /indicators` 包含 RSI | ✅ |

---

## Worker Template — 稳定性测试 ✅

**文件：** `workers/indicator-worker/tests/`

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 连续调用 | 100 次 RSI，全部成功 | ✅ |
| 2 | 大数据集 | 10000 根 K 线 SMA | ✅ |
| 3 | 并发 | 10 并发请求，全部成功 | ✅ |
| 4 | 24 小时 | 持续运行（后续） | ⬜ |

---

## V1.1 Smoke Test — 01 Worker ⬜

**文件：** `tests/smoke/01_worker.py`

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 健康检查 | `GET /health` 返回 200 | ⬜ |
| 2 | 就绪探针 | `GET /ready` 返回 200 | ⬜ |
| 3 | 版本信息 | `GET /version` 返回 JSON | ⬜ |
| 4 | RSI 计算 | `POST /api/v1/indicator/calculate` 返回 JSON | ⬜ |

**前置条件：** Worker 已启动（本地或 Xavier）

---

## V1.1 Smoke Test — 02 Master ⬜

**文件：** `tests/smoke/02_master.py`

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 健康检查 | `GET /health` 返回 200 | ⬜ |
| 2 | Worker 列表 | `GET /workers` 返回统一响应格式 | ⬜ |
| 3 | 提交任务 | `POST /task` 返回 `{task_id, status: COMPLETED\|FAILED, worker_id}` | ⬜ |
| 4 | 查询任务 | `GET /task/{id}` 返回任务元数据 | ⬜ |

**前置条件：** Master 已启动，workers.json 已配置

---

## V1.1 Smoke Test — 03 Master ↔ Worker ⬜

**文件：** `tests/smoke/03_master_worker.py`

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 端到端 | Master POST /task → Worker 计算 RSI → 返回 COMPLETED | ⬜ |
| 2 | 结果查询 | GET /task/{id} 返回 result 或 result_path | ⬜ |
| 3 | 任务持久化 | `storage/tasks/tm-task-*.json` 正确写入 | ⬜ |
| 4 | 结果持久化 | `storage/results/YYYY/MM/DD/tm-task-*.json` 正确写入 | ⬜ |
| 5 | Worker 状态 | GET /workers 显示 ONLINE + latency_ms | ⬜ |

**前置条件：** Master + Worker 均已启动并可通信

**失败则停止开发，修复后再测。**

---

## V1.1 稳定性测试 ⬜

**文件：** `tests/smoke/` 或 `tests/stability/`（Phase 7）

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 连续调用 | 100 次 POST /task（RSI），全部 COMPLETED | ⬜ |

---

## V1.1 Definition of Done（测试层）

| 层次 | 标准 | 状态 |
|------|------|------|
| Smoke 01 | Worker 四接口 + calculate PASS | ⬜ |
| Smoke 02 | Master 四接口 PASS | ⬜ |
| Smoke 03 | 端到端 Master → Worker → RSI PASS | ⬜ |
| Stability | 连续 100 次 RSI 全部 PASS | ⬜ |

---

## V3.0 Smoke Test — 04 AI Gateway 代理 ✅

**文件：** `tests/smoke/04_ai_gateway.py`  
**日期：** 2026-08-22

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | Gateway 离线 | Master 代理返回 503 / `TM-1002` | ✅ |
| 2 | Gateway 超时 | Master 代理返回 504 / `TM-1004` | ✅ |
| 3 | 代理成功 | 转发 JSON, `model_name=Qwen2.5-14B-Instruct` | ✅ |
| 4 | 路由注册 | `/api/v1/ai/{health,models,generate,describe,signal,chat}` | ✅ |
| 5 | Dashboard 入口 | 含 AI Gateway / Ask AI, 不含 GPT-5.6 | ✅ |
| 6 | Live Master :9000 | 本轮未运行, SKIP | ⬜ |

**未做 (当时):** 本节 2026-08-22 上午记录。下午 GPU 真推理已补:

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 7 | `try_gpu_chat.py` | SYCL0=A770M, 打印 `GPU_CHAT_OK` | ✅ |
| 8 | `POST /api/v1/ai/chat` (SYCL 网关) | HTTP 200, 模型 Qwen | ✅ |

---

## 运维冒烟 — 05 一键启动 ✅

**文件：** `tests/smoke/05_oneclick.py`  
**日期：** 2026-08-22

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | Master `:9000/health` | `status=healthy` | ✅ |
| 2 | Gateway `:9100/health` | `model_loaded` + Qwen2.5-14B-Instruct | ✅ |
| 3 | Master 代理 `/api/v1/ai/health` | HTTP 200 | ✅ |
| 4 | Xavier-02/03/04 拉起后 `/workers` | 四台 ONLINE（03 端口 8002） | ✅ |
| 5 | `POST /task` factor/monitor/backtest | 三笔 COMPLETED | ✅ |

对照：`docs/DIFF_2026-08-22_oneclick.md`。

---

## 运维冒烟 — 06 启动/重启接口 ✅

**文件：** `tests/smoke/06_ops.py`  
**日期：** 2026-08-22

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | `POST /api/v1/ops/worker/worker-99/start` | `TM-1001` | ✅ |
| 2 | `POST /api/v1/ops/worker/worker-02/start` | 已在线提示，不重复拉 | ✅ |

---

## 默认路径冒烟 — 07 详情结果 ✅

**文件：** `tests/smoke/07_default_path.py`  
**日期：** 2026-08-23（Master 重启后）

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | `GET /tasks` | 列表项 `result` 为 `null` | ✅ |
| 2 | `GET /task/{id}` | COMPLETED 且文件在则有 `result` | ✅ |
| 3 | `POST /task` RSI（01 在线） | `result.result.latest` 为数字 | ✅ `76.104` |

---

## Xavier-01 冒烟 — 08 四台同等启动 ✅

**文件：** `tests/smoke/08_xavier01.py`  
**日期：** 2026-08-23

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 脚本源码 | 无 `SKIP Xavier-01` | ✅ |
| 2 | `192.168.1.200:8080/health` | HTTP 200 | ✅ |
| 3 | `POST /api/v1/ops/worker/worker-01/start` | 已在线则不重复拉 | ✅ |

不停 01、不做重启破坏性测试。

---

## 一键状态冒烟 — 09 HTTP 判据 ✅

**文件：** `tests/smoke/09_lab_status.py`  
**日期：** 2026-08-23

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | `start_all.bat` | 无 `netstat findstr :9000` | ✅ |
| 2 | `--check-master` | 健康则 skip / 退出 0 | ✅ |
| 3 | `--check-gateway` | 已加载或加载中则 skip | ✅ |
| 4 | 默认报告 | 含 Master、worker-01、汇总标签 | ✅ |

不运行会弹窗的 `start_lab.bat`。

---

## 默认路径收口冒烟 — 10 下一步问 AI ✅

**文件：** `tests/smoke/10_ai_next.py`  
**日期：** 2026-08-23

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 页面 | 有「用这笔数字问 AI」 | ✅ |
| 2 | `fillAiFromTask` | 不 `fetch` / 不 `submitAI` | ✅ |
| 3 | `goAskAi` | 不 POST `/api/v1/ai/` | ✅ |
| 4 | 离线 | 有禁用提问的守卫 | ✅ |

不跑真实推理。

---

## 网关防护冒烟 — 11 单路 / 截断 ✅

**文件：** `tests/smoke/11_gateway_guard.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | `EngineBusy` + 非阻塞锁 | ✅ |
| 2 | token / 消息上限 | ✅ |
| 3 | 503 busy | ✅ |
| 4 | 不再默认 2048 tokens | ✅ |
| 5 | `start_sycl.bat` F16=OFF | ✅ |
| 6 | `prepare_messages` 截断 | ✅ |

不跑真实推理。

---

## V4 研究一笔冒烟 — 12 Research ✅

**文件：** `tests/smoke/12_research.py`  
**日期：** 2026-08-23

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 控制台 | 有「研究一笔」与研究记录；`init()` 不 POST `/research/run` | ✅ |
| 2 | 非法 preset | `TM-1001` | ✅ |
| 3 | 重叠研究 | `TM-1005` | ✅ |
| 4 | indicator | 有 `task_id`，摘要含 RSI | ✅ `tm-research-20260823-000001` |
| 5 | 列表/详情 | `GET /api/v1/research` 与按 id 读取 | ✅ |

本轮网关在线，`ai_skipped=false`。忙碌/离线形态见稳定性 01。

---

## V4 研究一笔稳定性 — 01 Research ✅

**文件：** `tests/stability/01_research.py`  
**日期：** 2026-08-23

| # | 测试项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 连续 10 次 | `preset=monitor` 均成功，id 不重复 | ✅ 000002–000011 |
| 2 | 调度中心 | 每次后 `/health` 仍 healthy | ✅ |
| 3 | 不双开 14B | `:9100` 监听 PID 始终同一份 | ✅ 10756 |
| 4 | Worker 离线 | 空 registry → TM-1002 路径 | ✅ |
| 5 | 网关 503 | `_call_ai` → `ai_skipped` | ✅ |

---

## V4.1 两步研究冒烟 — 13 Chain ✅

**文件：** `tests/smoke/13_research_chain.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台「因子后再回测」；`init()` 不自动跑 | ✅ |
| 2 | `chain` 3 步 → TM-1001 | ✅ |
| 3 | 进行中再 POST → TM-1005 | ✅ |
| 4 | factor+backtest `steps=2` | ✅ `tm-research-20260823-000012` |

---

## V4.1 两步研究稳定性 — 02 Chain ✅

**文件：** `tests/stability/02_research_chain.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 因子离线不提交回测 | ✅ |
| 2 | 3 步拒绝 | ✅ |
| 3 | 研究锁 | ✅ |

---

## V5 模拟单冒烟 — 14 Paper Order ✅

**文件：** `tests/smoke/14_paper_order.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台「确认挂模拟单」；`init()` 不提交 | ✅ |
| 2 | 服务无 broker send | ✅ |
| 3 | 无 confirm → TM-1001 | ✅ |
| 4 | 研究不存在 → TM-1003 | ✅ |
| 5 | indicator 落盘 paper ACCEPTED | ✅ `tm-order-20260823-000003` SELL |
| 6 | 重复提交 → TM-1005 | ✅ |

---

## V5 模拟单稳定性 — 03 Paper Order ✅

**文件：** `tests/stability/03_paper_order.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | confirm=false | ✅ |
| 2 | 研报缺失 | ✅ |
| 3 | 回测研究拒绝 | ✅ |
| 4 | 锁 | ✅ |

---

## V6 台账冒烟 — 15 Paper Desk ✅

**文件：** `tests/smoke/15_paper_desk.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | `showResearch` 先 preview | ✅ |
| 2 | `init()` 不 submit | ✅ |
| 3 | 无 broker send | ✅ |
| 4 | preview SELL 且不落盘 | ✅ |
| 5 | `GET /desk/today` | ✅ |

---

## V6 台账稳定性 — 04 Paper Desk ✅

**文件：** `tests/stability/04_paper_desk.py`  
**日期：** 2026-08-23

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 20 次 preview | ✅ |
| 2 | 不新增订单文件 | ✅ |
| 3 | desk 重复可读 | ✅ |

---

## V11 证伪回测冒烟 — 20 Walk-forward ✅

**文件：** `tests/smoke/20_walkforward.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台「黄金证伪回测」 | ✅ |
| 2 | 70/30 切分；证伪 / 风控 / 不足 / survived | ✅ |
| 3 | Worker 用传入 close，合成路径仍在 | ✅ |
| 4 | `source=mt5` + factor 仍拒绝 | ✅ |
| 5 | 白盒：`context.result.total_trades` 嵌套；旧扁平结构会变成 0 笔 | ✅ |
| 6 | 白盒：证伪解读写 28/12，不写「没有任何交易」 | ✅ |
| 7 | 白盒：网关 prompt 含 12/28；有 verdict 不走 LLM | ✅ |
| 8 | 白盒：CSV 回测同样把数字放进 `result` | ✅ |
| 9 | 白盒：RSI 回 `idx/price`；`stamp_trades` 对上时间 | ✅ |
| 10 | 控制台有成交明细表；MT5 留下 `time` | ✅ |

---

## V11 回测审计冒烟 — 21 Backtest audit ✅

**文件：** `tests/smoke/21_backtest_audit.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 独立 RSI 买卖点与 Worker 一致 | ✅ |
| 2 | 成交价还原盈亏 = Worker `pnl_pct` / `profit` | ✅ |
| 3 | 判定：survived / 证伪 / 不足 / 风控 | ✅ |
| 4 | 009995 四十笔配对盈亏与 28/12 一致 | ✅ |
| 5 | 本机 MT5 GOLD H1 2000 可复算；连续切分不在 cut 强平 | ✅ |
| 6 | 冻结五策略都回 is/oos；直播研究带 basket | ✅ |

---

## V11 证伪稳定性 — 08 Walk-forward ✅

**文件：** `tests/stability/08_walkforward.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 20 次切分相同 | ✅ |
| 2 | 20 次判定仍为证伪 | ✅ |

---

## V10 测通冒烟 — 19 Wire Test ✅

**文件：** `tests/smoke/19_wire_test.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台「测买 / 测卖」；`init()` 不提交 | ✅ |
| 2 | 中性 RSI preview = HOLD + wire_test | ✅ |
| 3 | 无 side 仍 rsi_neutral | ✅ |
| 4 | 非法 side → TM-1001；BUY 测通 ACCEPTED | ✅ |

未打真实模拟账户。

---

## V9 MT5 模拟盘冒烟 — 18 MT5 Demo ✅

**文件：** `tests/smoke/18_mt5_demo.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台 MT5 芯片 + `source=mt5`；`init()` 不自动跑 | ✅ |
| 2 | Xavier workers 不导入 MetaTrader5 | ✅ |
| 3 | 假终端 probe demo + 四品种 | ✅ |
| 4 | 拉 30 根 close；假 `order_send` 有 ticket | ✅ |
| 4b | Ava 名称：`GOLD` / `CrudeOIL` | ✅ |
| 5 | `TRADEMIND_MT5_SEND=0` 不发；live 拒绝 | ✅ |
| 6 | `source=mt5` 非指标 → TM-1001；`GET /mt5/quotes` | ✅ |

未打真实模拟账户。

---

## V9 MT5 模拟盘稳定性 — 07 MT5 Demo ✅

**文件：** `tests/stability/07_mt5_demo.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 20 次 fetch_closes 相同 | ✅ |
| 2 | live 10 次拒绝且不发 | ✅ |
| 3 | SEND=0 永不 `order_send` | ✅ |
| 4 | 非指标 `source=mt5` 保持拒绝 | ✅ |

---

## V8 因子/回测样本冒烟 — 17 Sample Presets ✅

**文件：** `tests/smoke/17_sample_presets.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台含 moutai/xauusd；`init()` 不自动研究 | ✅ |
| 2 | PRESETS 不再写死 600519 / EMA_MACD | ✅ |
| 3 | 默认 payload 与旧硬编码相同 | ✅ |
| 4 | 种类对不上 / 监控带样本 → TM-1001 | ✅ |
| 5 | `GET /samples` 三种 kind | ✅ |

---

## V8 因子/回测样本稳定性 — 06 Sample Presets ✅

**文件：** `tests/stability/06_sample_presets.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 连续 20 次加载相同 | ✅ |
| 2 | 列表 kind 仍在 | ✅ |
| 3 | 错配保持拒绝 | ✅ |

---

## V7 本机样本冒烟 — 16 Sample Data ✅

**文件：** `tests/smoke/16_sample_data.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 控制台写本机样本；`init()` 不自动研究 | ✅ |
| 2 | `eurusd.csv` 30 根；研究服务不再写死 close | ✅ |
| 3 | 路径穿越 / 非指标带 sample → TM-1001 | ✅ |
| 4 | 缺文件 → TM-1003 | ✅ |
| 5 | `GET /api/v1/samples` 含 eurusd | ✅ |

---

## V7 本机样本稳定性 — 05 Sample Data ✅

**文件：** `tests/stability/05_sample_data.py`  
**日期：** 2026-08-24

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 连续 20 次加载结果相同 | ✅ |
| 2 | 列表仍有 eurusd | ✅ |
| 3 | 坏 id / 缺文件保持拒绝 | ✅ |

---

## Research Readiness V0.2 — `tests/research_readiness/` ✅

**日期：** 2026-08-25  
**命令：** `master/api/.venv/Scripts/python.exe -m unittest discover -s tests/research_readiness -v`

13 tests PASS。现场：四台各 ≥80 full profiles；GOLD M15 两节点各 20；跨节点 hash PASS。

---

## Research Protocol V0.3 — `tests/research_protocol/` ✅

**日期：** 2026-08-25  
**命令：** `master/api/.venv/Scripts/python.exe -m unittest discover -s tests/research_protocol -v`

14 tests PASS（causal / execution / experiment write-once / golden features / incremental=pointwise / purity / sentinel / timestamp windows）。

现场：四台各 6 dataset × 10 次；synthetic 各 10 次；交叉 4 组 hash PASS。见 `docs/RESEARCH_PROTOCOL_V0.3.md`。

不是 V11.7 冒烟。不启动回测。FINAL_OOS 未锁。

---

## Data Qualification V0.1 — `tests/research_profile/` ✅

**日期：** 2026-08-25  
**命令：** `master/api/.venv/Scripts/python.exe -m unittest discover -s tests/research_profile -v`

17 tests PASS（schema / returns / ATR / gap / extreme / trend / qualification / snapshot / determinism）。

现场：四台 Xavier 各 4 个 dataset + GOLD M15 跨节点 PASS。

---

## Data Layer V0.1 — `tests/data_layer/` ✅

**日期：** 2026-08-25  
**命令：** `master/api/.venv/Scripts/python.exe -m unittest discover -s tests/data_layer -v`

| # | 测试项 | 状态 |
|---|--------|------|
| 1 | 缺 open → FAIL | ✅ |
| 2 | high < close → FAIL | ✅ |
| 3 | 重复 timestamp → FAIL | ✅ |
| 4 | 乱序 timestamp → FAIL | ✅ |
| 5 | NaN → FAIL | ✅ |
| 6 | real_volume 全 0 不 FAIL | ✅ |
| 7 | 文件篡改 → DATA_CORRUPTED | ✅ |
| 8 | 二次保存不覆盖 | ✅ |
| 9 | order_send 拒绝 + 源码无调用 | ✅ |
| 10 | 2000 bars 可创建 | ✅ |
| — | 现场 MT5 只读 16 组合 | ✅ 见 `data/market/V0.1_FETCH_INDEX.json` |

不是 V11.7 冒烟。不启动回测。

---

## Research Engine HYP-0001 — 2026-08-26

| 项 | 结果 |
|----|------|
| 单元 `tests/research_engine`（含 contract authority 1–10） | ✅ 34 PASS |
| Smoke：Xavier-01 / GOLD M15 / HYP-0001-A / tm-exp-20260825-141158-001 | ✅ PASS |
| Full：48 jobs / 32 experiment IDs / 四台 | ✅ PASS |
| Cross 01↔04 GOLD M15+H1，02↔03 EURUSD M15 + USDJPY M15 | ✅ 4/4 PASS |
| continuation_mean vs 0；无 PENDING experiment_id | ✅ |
| Final OOS 仍 DENIED | ✅ |
| 14:11 A/B hash 未变 | ✅ |

不是交易许可。WEAK_SUPPORT ≠ 年化 10%。

---

## Factor Discovery V0.1 — 2026-08-26

**命令：** `C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine -v`

| 项 | 结果 |
|----|------|
| 旧 research_engine 单元（含 contract authority 1–10） | ✅ 34 PASS（未改弱） |
| 新 `test_factor_*` | ✅ 22 PASS |
| 合计 | ✅ 56 PASS |
| Smoke：Xavier-01 / GOLD M15 / 全 57 candidates | ✅ PASS（wall 87s） |
| Full：17 jobs / 四台 / FDR m=876 | ✅ PASS |
| GOLD M15 content-hash 01↔04 | ✅ PASS |
| Final OOS 仍 DENIED | ✅ |
| 14:11 HYP-0001 未改 | ✅ |
| 结果 | `NO_USEFUL_FACTORS_FOUND`（PROMISING 0） |

不是交易许可。不是年化 10%。下一阶段不是 Strategy Mining。

---

## Research Engine V0.5 — 2026-08-26

**命令：** `C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine -v`

| 项 | 结果 |
|----|------|
| 合计 research_engine 单元 | ✅ 64 PASS |
| 其中 V0.5 regime/strategy | ✅ 8 PASS |
| 本地 16 dataset / 15 sketches / FDR m=203 | ✅ `NO_USEFUL_STRATEGIES_FOUND` |
| 四 Xavier 实跑 | 未在本轮执行（调度脚本已存在） |

---

## Alpha discovery pipeline — 2026-08-26

**命令：** `C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine -v`  
另：`python scripts\research_engine_alpha_pipeline.py`

| 项 | 结果 |
|----|------|
| 合计 research_engine 单元 | ✅ 85 PASS |
| 其中 pipeline | ✅ 5 PASS |
| 52 题 / live 29 / 簇 RT-Residual-Calendar | ✅ |
| V0.8 / V0.9 hash | ✅ 未改 |
| V0.9 Xavier | 未跑 |
| Final OOS | ✅ 未访问 |

---

## Alpha Map V1 + V0.9 contract — 2026-08-26

设计任务。无新代码，无新单元测试，无 Xavier job。  
旧 `tests/research_engine` 仍以 V0.8 的 80 PASS 为准。未重跑。

| 项 | 结果 |
|----|------|
| 新实验 / 新 ranking | 未创建（禁止） |
| 14:11 / FD / V0.5 / V0.6 / V0.8 | ✅ 未改 |
| 交付 | `ALPHA_COVERAGE_MAP_V1.md` + `REGIME_TRANSITION_V0.9_CONTRACT.md` |

---

## Cross Asset V0.8 execution — 2026-08-26

**命令：** `C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine -v`

| 项 | 结果 |
|----|------|
| 合计 research_engine 单元 | ✅ 80 PASS |
| 其中 V0.8 对齐/合同/OOS/worker | ✅ 6 PASS |
| 四 Xavier 实跑 | ✅ PASS（01=0001 / 02=0002 / 03=0003 / 04=0001 交叉；01=04 hash） |
| 程序级 CANDIDATE | 0 |
| 结果 | `NO_CANDIDATE`（3/3 FALSIFIED；FDR 0/3） |
| Final OOS / 14:11 | ✅ 未访问 / 未改 |
| 14:11 / FD V0.1 / V0.5 / V0.6 未改 | ✅ |

---

## Cross Asset V0.8 contract — 2026-08-26

合同定稿（执行见上一节）。四向 D1 join 1993 日。hash `787a37f9…9827`。

| 项 | 结果 |
|----|------|
| 数据审计 | `docs/research_engine/CROSS_ASSET_DATA_AUDIT.md`（1993 日 join） |
| 合同 | `docs/research_engine/CROSS_ASSET_ALPHA_V0.8_CONTRACT.md` |
| 旧合同 / 14:11 / 不可变 bars | ✅ 未改 |

---

## Alpha OS V0.7.1 — 2026-08-26

设计任务。无新代码，无新测试，无 Xavier job，无新 hypothesis JSON。

| 项 | 结果 |
|----|------|
| 新实验 / 新 ranking | 未创建（禁止） |
| 14:11 / FD / V0.5 / V0.6 | ✅ 未改 |
| 交付 | `docs/research_engine/ALPHA_OPERATING_SYSTEM_V0.7.1.md` |

---

## Alpha Discovery V0.7 — 2026-08-26

设计任务。无新代码，无新单元测试，无 Xavier job。  
旧 `tests/research_engine` 仍以 V0.6 的 74 PASS 为准。未重跑。

| 项 | 结果 |
|----|------|
| 新实验 / 新 ranking | 未创建（禁止） |
| 14:11 / FD / V0.5 / V0.6 | ✅ 未改 |
| 交付 | `docs/research_engine/ALPHA_DISCOVERY_V0.7_PLAN.md` |

---

## Profit Discovery V0.6 — 2026-08-26

**命令：** `C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine -v`

| 项 | 结果 |
|----|------|
| 合计 research_engine 单元 | ✅ 74 PASS |
| 四 Xavier 16 jobs | ✅ PASS（01 GOLD / 02 EURUSD / 03 USDJPY / 04 OIL） |
| 程序级 CANDIDATE | 0 |
| 结果 | `WEAK_EDGE_ONLY` |
| Final OOS / 14:11 | ✅ 未访问 / 未改 |
| Final OOS 仍 DENIED | ✅ |
| 14:11 / FD V0.1 未改 | ✅ |

---

## Alpha Discovery Program V1.0 + V0.9/V0.91 — 2026-08-27

**命令：** `C:\ProgramData\miniconda3\python.exe -m pytest tests/research_engine --import-mode=importlib`  
或：`C:\ProgramData\miniconda3\python.exe -m unittest discover -s tests/research_engine`

| 项 | 结果 |
|----|------|
| research_engine 单元 | ✅ **149 PASS** |
| 其中 T1–T13 / universe / classifier / OOS / hash / worker | ✅ |
| V0.9 四 Xavier | ✅ PASS（01=0001 / 02=0002 / 03=0003 / 04=0001；01=04 hash） |
| V0.9 程序级 CANDIDATE | 0（`NO_CANDIDATE`） |
| V0.91 本地 2000-iter | ✅ 跑完；`NO_CANDIDATE` |
| V0.8 / V0.9 / V0.91 hash | ✅ 未改 |
| Final OOS | ✅ 未访问 |
| 14:11 / FD / V0.6 | ✅ 未改 |

不是交易许可。不是年化 10%。

---

## Alpha Recovery Program V1.0 — 2026-08-27

**命令：** `C:\ProgramData\miniconda3\python.exe -m pytest tests/research_engine --import-mode=importlib`  
另：`python scripts\research_engine_alpha_recovery.py`（写报告；**不跑**新家族）

| 项 | 结果 |
|----|------|
| research_engine 单元 | ✅ **167 PASS** |
| 覆盖 / A-E / Opportunity V2 / 日历计数 / IT hash | ✅ |
| 只读 MT5 探针 | ✅ H1 5y 与 M15 2y 可达；GOLD/OIL D1 <10y |
| 新家族执行 | ❌ 未跑（合同 LOCKED_NOT_RUN） |
| V0.8 / V0.9 / V0.91 hash | ✅ 未改 |
| Final OOS | ✅ 未访问 |

不是交易许可。不是年化 10%。

---

## Data Expansion Mission V3.0 — 2026-08-28 WAIT_HUMAN

**命令：** `C:\ProgramData\miniconda3\python.exe -m pytest tests/research_engine --import-mode=importlib`

| 项 | 结果 |
|----|------|
| research_engine 单元 | ✅ **221 PASS**（V2 的 210 + SUPPLY 3 + factory 8） |
| SUPPLY_V1 合同锁 | `4f6548b39376eb773f772d739a06a8f0d436e52b02d5366b49aeacc61dbb16f1` |
| SUPPLY_V1 四 Xavier | ✅ 01=04；程序 NO_CANDIDATE |
| 指数 IV ≠ option surface | ✅ 测试门 |
| 无字节不得 READY | ✅ |
| Databento 无 key | CREDENTIAL_REQUIRED |
| 花费 | $0 |
| Final OOS | ✅ 未访问 |

不是交易许可。不是年化 10%。下一动作 = 人类买 Databento credits。

## Alpha Research Mission V2.0 — 2026-08-28 STOP B

**命令：** `C:\ProgramData\miniconda3\python.exe -m pytest tests/research_engine --import-mode=importlib`

| 项 | 结果 |
|----|------|
| research_engine 单元 | ✅ **210 PASS** |
| 新增 IV / POS / INV / RATES / CARRY 合同与泄漏门 | ✅ |
| IV / POS / INV / RATES / CARRY_V1A 四 Xavier | ✅ 01=04；程序 NO_CANDIDATE |
| CARRY_V1 | INVALID_ALIGNMENT；不是机制结论 |
| 冻结 20260825 / V0.8–0.91 / IT hashes | ✅ 未改 |
| Final OOS | ✅ 未访问 |
| 程序级 CANDIDATE / Level | 0 / Level 0 |

不是交易许可。不是年化 10%。不要调参救。下一美元 = 付费/人工新数据。

## Alpha Mission V1.1 — 2026-08-28 STOP B

**命令：** `C:\ProgramData\miniconda3\python.exe -m pytest tests/research_engine --import-mode=importlib`

| 项 | 结果 |
|----|------|
| research_engine 单元 | ✅ **192 PASS** |
| 其中新增 IT / TS / MS / RI / AMS 合同与泄漏门 | ✅ |
| IT 四 Xavier | ✅ 01=04；程序 WEAK_EDGE；FDR 0/3 |
| TS / MS 四 Xavier | ✅ cross_check True；3/3 FALSIFIED |
| RI / AMS | ✅ 本地 2000 权威；3/3 FALSIFIED |
| GOLD/OIL D1 最大历史 | 7.715y BROKER_LIMITATION；冻结 `20260825` 未覆盖 |
| V0.8 / V0.9 / V0.91 / IT hash | ✅ 未改 |
| Final OOS | ✅ 未访问 |
| 14:11 / FD / V0.6 | ✅ 未改 |
| 程序级 CANDIDATE / Level | 0 / Level 0 |

不是交易许可。不是年化 10%。不要调参救。

---

## 冒烟测试规则

1. 每次只验证**最核心**路径
2. 冒烟失败 → **停止开发**，修复后重测
3. 冒烟 PASS → 才能开始稳定性测试
4. 稳定性 PASS → 才能 Freeze
5. Freeze 后更新 CHANGELOG.md + TODO.md + PROJECT_STATUS.md
