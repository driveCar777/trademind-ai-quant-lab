# PHASE3_FORENSIC_IMPLEMENTATION_REPORT.md

> Phase 3：A-Short Observability / Forensic 基础设施**最小实现**。只增加"解释为什么赚钱/亏钱"的能力；不改 alpha/baseline/合同/universe/成本/数据源。

---

## 1. 实现内容
新增只读观测层 `research_engine/cn_a_short/forensic/`（薄持久化 + 派生分析，挂在既有 baseline 输出之上）：
| 模块 | 作用 |
|------|------|
| `run_manifest.py` | RUN_ID + 统一运行记录；**确定性(语义)字段算 `manifest_hash`**，时间/commit/env 单独存、不污染 hash；记录 code/branch/py/OS/deps/contract/dataset/derived/seed/windows/model/exec/cost 版本 |
| `snapshots.py` | `DATA_SNAPSHOT`：股票数量/池组成(主板/创业/科创/北交所)/ST/停牌/涨跌停计数/价格·成交额·换手分布；**市值/波动=UNKNOWN（无数据，不编造）** |
| `signals.py` | 逐日 SIGNAL 快照：symbol/rank/score/eligibility/reject_reason；`features={momentum20}`（仅 baseline，未加新因子，`features` 为未来预留） |
| `lifecycle.py` | 交易生命周期状态机（SIGNAL→…→CLOSED；异常 ENTRY_BLOCKED/EXIT_BLOCKED/STUCK），**从 `top_k_period` 输出派生**，不改结果 |
| `attribution.py` | 收益归因（**APPROX**）：market_beta=EW 暴露；momentum=超额(APPROX)；size/selection=UNKNOWN（无市值/因子模型）；best/worst 10 |
| `errors.py` | 错误分类 DATA/MODEL/EXECUTION/COST/ENV + `classify_run` 推断 primary_conclusion（STYLE_EXPOSURE_ONLY/TRUE_NO_EDGE/COST_ERROR/DATA_BLOCKED…） |
| `report.py` | 自动 `REPORT.md`（11 节）+ 结尾 `WHY_RESULT_HAPPENED`（亏损必须归入 alpha/数据/执行/成本/环境之一） |
| `__init__.py` | `run_forensic(...)` 编排：写 `runs/<RUN_ID>/{RUN_MANIFEST,CONFIG,DATA_LINEAGE,DATA_SNAPSHOT,SIGNALS,TRADES,LEDGER,METRICS,ERRORS}.json + REPORT.md`；**永不抛异常** → 失败即 `FORENSIC_STATUS=DEGRADED` |

接入：`run_baseline.py` 加 `--forensic`（默认开）/`--no-forensic`；DATA_BLOCKED、退化、成功三条路径均调用；forensic 失败不影响 baseline（返回 DEGRADED）。`runs/` 已 gitignore（防 churn）。

## 2. 修改文件列表
```
新增 research_engine/cn_a_short/forensic/__init__.py
新增 research_engine/cn_a_short/forensic/run_manifest.py
新增 research_engine/cn_a_short/forensic/snapshots.py
新增 research_engine/cn_a_short/forensic/signals.py
新增 research_engine/cn_a_short/forensic/lifecycle.py
新增 research_engine/cn_a_short/forensic/attribution.py
新增 research_engine/cn_a_short/forensic/errors.py
新增 research_engine/cn_a_short/forensic/report.py
新增 research_engine/cn_a_short/tests/test_forensic.py
改   research_engine/cn_a_short/run_baseline.py   （只加接线：--forensic 开关 + 三路径调用；未改 baseline 计算）
改   .gitignore                                    （忽略 runs/ 运行产物）
新增 docs/a_short/forensic/PHASE3_FORENSIC_IMPLEMENTATION_REPORT.md（本文件）
```
**未改**：`baseline.py`、`cost.py`、`account.py`、`feasibility.py`、`__init__.py`（合同常量）、任何冻结 dataset / ML1/V33/V25/V26。

## 3. 测试结果
```
python -m pytest research_engine/cn_a_short/tests/ -q
=> 42 passed  (33 原有 + 9 forensic)  0 failed  0 skipped
```
`test_forensic.py` 覆盖（业务不变量）：
1. manifest hash 稳定（同语义输入→同 hash）
2. 时间/commit 字段不污染 hash（篡改时间后 hash 不变）
3. DATA_BLOCKED 路径产出完整 bundle + FORENSIC_STATUS=PASS + 结论 DATA_BLOCKED
4. 缺字段→UNKNOWN（无 pack / 无市值 / 无波动，均 UNKNOWN 不编造）
5. 生命周期完整（entered→CLOSED/STUCK；未入场→ENTRY_BLOCKED）
6. 未来泄漏检测（forward_label 严格前向；篡改 ≤T 历史，label 不变）
7. 负现金检测（cash_out>equity 被 LEDGER 标记；健康期通过）
8. 合成 pack 端到端（10 个产物齐全；结论 STYLE_EXPOSURE_ONLY）

实运行验证：`run_baseline` 默认写 `runs/<RUN_ID>/` 10 文件，`REPORT.md` 以 `WHY_RESULT_HAPPENED` 收尾；`--no-forensic` 关闭；`runs/` gitignored。

## 4. 是否影响 baseline？
**否。** `baseline.py` 未改；forensic 只读既有输出。`PHASE2A2_RESULTS.json` 内容不变（forensic 结果写到独立 `runs/`，`result["forensic"]` 仅加在返回 dict、在 artifact 写盘之后）。forensic 异常被吞（DEGRADED），绝不打断 baseline。

## 5. 是否改变 contract？
**否。** 合同 `A_SHORT_D1_V1` 常量、窗口、参数、universe、成本模型均未改。manifest 只**读取**这些值。

## 6. 是否改变 alpha？
**否。** 无新因子/新过滤/新 hold/新成本；唯一打分仍是 20D 动量。`signals.features` 只含 `momentum20`；attribution 明确 size/selection=UNKNOWN、momentum=APPROX，不伪造收益来源。

## 7. Known limitations
1. **市值/波动/行业=UNKNOWN**：A-Short pack 无股本/行业数据 → attribution 的 size/sector/selection 无法精确分离，只给 market_beta + APPROX momentum，其余 UNKNOWN（诚实，不编造）。
2. **成功路径需数据**：Cloud DATA_BLOCKED → 真实 SIGNALS/TRADES 快照未产出；成功路径由合成 pack + 单测覆盖，真实快照待数据物化。
3. **SIGNALS/lifecycle 采样**：`run_baseline` 成功路径只对代表性 (hold=1,k=10, 采样 ≤5 日) 建 SIGNALS/TRADES（观测采样，不改 evaluate 全量指标）；如需全量逐日快照，后续可扩（新任务）。
4. **attribution 为 APPROX**：momentum vs selection 无因子模型无法分离，已显式标注；不得当精确归因。
5. **overlap 占用未计**（Phase 2A.1 遗留）：错误分类可提示，但未实现完整重叠会计。
6. **manifest_hash 语义口径**：排除 time/commit/env，代表"逻辑输入"而非"哪台机/哪次提交"；env 单独记录用于排查环境差异。

---
**Phase 3 到此停止。** 不进入 Phase 4，不接 LLM/新闻/GUI/通知/交易，不优化收益。等待下一条指令。
