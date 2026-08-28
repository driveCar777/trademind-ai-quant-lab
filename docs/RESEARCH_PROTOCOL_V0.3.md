# Research Protocol V0.3

冻结日期：2026-08-25。

RESEARCH_PROTOCOL_V0.3 = FROZEN  
RESEARCH_READINESS_V0.2 = 仍 FROZEN  
DATA_QUALIFICATION_V0.1 = 仍 FROZEN  
Data Layer V0.1 = 仍 FROZEN  
V11.7 = 仍 FROZEN  
FINAL_OOS_LOCKED = false

## Scope

在不可变行情层之上建立**研究协议**：Dataset / Experiment / Window / Execution / Lookback / Horizon / Purge-Embargo / Causal Feature / Leakage Sentinel。

不是回测。不是选参。不是 GOLD M15 RSI 再验证。窗口不由收益、RSI、波动或 Sharpe 决定。

输入只读：`data/market/immutable/`。  
结果只写：`data/market/research_protocol/`。

## What an experiment must answer

正式研究开始前，系统必须能回答：

1. `dataset_id` 与 `sha256`（`verify_hash()` 失败 → `EXPERIMENT_BLOCKED`）
2. dataset 是否 `immutable = true`
3. RESEARCH / VALIDATION / FINAL_OOS_CANDIDATE 的 UTC 时间窗
4. Final OOS 是否仍未锁（本阶段必须是 false）
5. 研究开始时哪些 bar 可见（`CausalView`：`0..t`，MT5 bar 时间为 OPEN UTC）
6. 信号字段与执行时序（默认 `NEXT_BAR_OPEN`：`close(t)` 之后才能执行 `open(t+1)`）
7. 是否允许当前 bar 的 close / high / low（执行禁止当前 bar）
8. 未来 index 访问是否被 Sentinel 挡住（`FUTURE_DATA_ACCESS`）
9. lookback / holding / purge / embargo
10. 实验合同是否 write-once；改任何输入必须新 `experiment_id`
11. 哪台 Xavier 算的，其他节点能否得到同一 hash

答不出其中一项：实验不得进入正式研究。

## Contracts

| 合同 | 模块 | 要点 |
|------|------|------|
| Dataset | `research_protocol/contracts.py` | id / sha256 / symbol / TF / timezone / rows / 区间 / schema / profile_hash / qualification / source / volume_policy / immutable |
| Experiment | 同上 + `experiments.py` | `tm-exp-YYYYMMDD-HHMMSS-NNN`；write-once；状态机 CREATED→VALIDATED→RUNNING→COMPLETED→FAILED→FROZEN |
| Window | `windows.py` | 70/15/15 **按 bar 数切分**，记录 **UTC 时间戳**。可配置，创建后冻结。Role=`CANDIDATE_WINDOW` |
| Lookback | `lookback.py` | 第一根可信号 = research_start + lookback。默认 120 |
| Horizon | `horizon.py` | signal / entry / exit；默认 holding=50，entry offset=1 |
| Execution | `execution.py` | `NEXT_BAR_OPEN` 与 `NEXT_BAR_CLOSE` 显式配置，不自动选 |
| Feature | `features.py` `REGISTRY` | sma/ema/rsi/atr/macd/bollinger/vwap；VWAP 只用 `tick_volume` |
| Leakage | `leakage.py` + `causal.py` | 未来 index 抛错；未来 close/volume/high/low/timestamp 攻击不得改变过去 feature |

`FINAL_OOS_LOCKED` 在本协议中保持 false。70/15/15 不是永久规则，也不是 V11.7 的 70/30。

## Bar time semantics

MT5 `time` = bar **OPEN** UTC。`close[t]` 只在 bar t 结束后可用。  
`signal on close(t)` 然后在 `open(t)` 成交 = look-ahead，协议禁止。

## Xavier allocation

one-shot：`research_protocol/node_runner.py`。不占 8002–8005。不改 Worker / Master。

| Node | Host | Home | Cross |
|------|------|------|-------|
| Xavier-01 | 192.168.1.200 | GOLD ×4 | OIL M15 + OIL D1 |
| Xavier-02 | 192.168.1.201 | EURUSD ×4 | USDJPY M15 + USDJPY D1 |
| Xavier-03 | 192.168.1.202 | USDJPY ×4 | EURUSD M15 + EURUSD D1 |
| Xavier-04 | 192.168.1.203 | OIL ×4 | GOLD M15 + GOLD D1 |

每节点：synthetic fixture + 每个真实 dataset 10 次 feature / window / leakage。  
现场 Python：01/04 = 3.6.9；02/03 = 3.6.8。stdlib only。

## Runtime

墙钟约 2.5 分钟（四台并行，2026-08-25T13:49:53Z → 13:52:08Z）。  
节点本机计算约 129–133s；含 SCP 约 131–135s。

24 条任务行（4×6）全部 DETERMINISTIC。  
16 份本地 `CANDIDATE_WINDOW` 与 Xavier `window_hash` 全同。

## Cross-node

| Pair | Dataset | Result |
|------|---------|--------|
| 01 ↔ 04 | GOLD M15 000001 | PASS |
| 01 ↔ 04 | OIL D1 000001 | PASS |
| 02 ↔ 03 | EURUSD M15 000001 | PASS |
| 02 ↔ 03 | USDJPY D1 000001 | PASS |

feature / window / leakage hash 全同。  
**COMPUTATION_MISMATCH = 无**  
**LEAKAGE_DETECTED = 无**  
**BOUNDARY_LEAKAGE = 无**  
**DETERMINISM_FAILURE = 无**

GOLD M15 feature_hash（01=04）：

`57dd2fbed870a8d0e1b84699c20d00d1d37bb685d8b53bf044169e2d8d1e406b`

## Candidate windows (not Final)

默认 lookback=120，holding=50，purge=50，embargo=1。  
切分与策略结果脱钩。GOLD M15 例：

| Role | UTC |
|------|-----|
| RESEARCH | 2026-07-24T19:00:00Z → 2026-08-17T00:45:00Z |
| VALIDATION | 2026-08-17T01:00:00Z → 2026-08-20T06:45:00Z |
| FINAL_OOS_CANDIDATE | 2026-08-20T07:00:00Z → 2026-08-25T12:45:00Z |

完整 16 份见 `data/market/research_protocol/windows/`。

## Features

实现且 golden + incremental 对齐：SMA20、EMA20、RSI14(Wilder)、ATR14(TR 简单均值)、MACD(12/26/9)、Bollinger(20,2 pop stdev)、VWAP20(`tick_volume_only`)。

缺 `tick_volume` 或 `volume_source=real_volume` → `FEATURE_UNAVAILABLE`，不合成。

## Known limitations

- 本阶段唯一 Experiment Contract 是协议自检 `PROTOCOL_SELF_TEST` / `strategy_id=NONE`，不是策略实验
- DatasetContract.qualification 继承 Readiness 探针字符串（GOLD M15 为 `READY_WITH_REVIEW`）；结构映射仍以 `docs/RESEARCH_READINESS_V0.2.md` 为准
- Xavier-02/03 为 Python 3.6.8，01/04 为 3.6.9；hash 仍一致
- 未锁 Final OOS，不得用这些窗口做样本外选参

## Next stage

最小任务：Hypothesis Registry——为**新**假设建第一份正式 Experiment Contract。  
禁止：重跑 V11.7、重验 GOLD M15 RSI 14/30/80、锁 Final OOS、按收益选窗。

索引：`data/market/research_protocol/RESEARCH_PROTOCOL_INDEX.json`  
完成报告：`data/market/research_protocol/RESEARCH_PROTOCOL_V0.3_COMPLETION.md`
