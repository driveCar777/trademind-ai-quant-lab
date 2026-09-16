# EXPERIMENT_PROTOCOL.md

> Phase 6 — 实验协议。每次实验有唯一 `experiment_id`，绑定代码/数据/合同/参数/模型/结果/失败类，可追溯、可复现、可查重。**只设计。**
> 复用 Phase 3 forensic 已实现的 `runs/RUN_ID/` bundle（`RUN_MANIFEST.json` 已含大部分绑定字段）。

---

## 1. experiment_id
```
EXP_<NNNN>            人可读序号，如 EXP_0001（登记在 research_memory/experiments/）
run_id = A_SHORT_<experiment>_<UTC>   机器级运行号（forensic 已实现）
```
- 一个 `experiment_id` 可含多次 `run_id`（复现/重跑）；experiment 是**假设单元**，run 是**执行单元**。
- experiment_id 在 `research_memory/experiments/EXP_<NNNN>.json` 登记（含 hypothesis + 预注册）。

## 2. 必须绑定的字段
| 字段 | 含义 | 来源（现有 forensic） |
|------|------|------------------------|
| `experiment_id` | 假设单元号 | research_memory 登记 |
| `dataset_hash` | 上游数据集 hash（`dd39193c…`） | `RUN_MANIFEST.upstream_hash` ✅ |
| `derived_dataset_hash` | 派生集 hash（物化时盖章） | `RUN_MANIFEST.derived_dataset_hash` ✅ |
| `code_commit` | git HEAD | `RUN_MANIFEST.git_commit` ✅ |
| `contract_id` / `contract_hash` | 合同标识 + sha256(合同 md) | `RUN_MANIFEST` ✅ |
| `parameter_hash` | 参数指纹 = sha256(CONFIG.json 规范化) | 新增派生（对已有 `CONFIG.json` 取 hash） |
| `model_version` | 模型标识（`20D_MOMENTUM_BASELINE/v1`） | `RUN_MANIFEST.model_id/model_version` ✅ |
| `execution_version` / `cost_version` | 撮合/成本版本指纹 | `RUN_MANIFEST` ✅ |
| `manifest_hash` | 语义复现 hash（排除 time/commit/env） | `RUN_MANIFEST.manifest_hash` ✅ |
| `result` | 关键指标摘要 | `METRICS.json` ✅ |
| `failure_class` | 五类之一 或 PASS | `ERRORS.json.primary_conclusion` ✅ |

> `parameter_hash` 是 Phase 6 唯一新增派生（对现有 `CONFIG.json` 做规范化 sha256）；其余字段 forensic 层已产出，无需改代码即可组装。

## 3. 实验生命周期
```
REGISTER (research_memory: hypothesis + 预注册 + 预期比较数 m)
   ↓
RUN      (Local: run_baseline / 未来因子 runner → runs/RUN_ID bundle)
   ↓
CLASSIFY (forensic ERRORS.json → PASS / 五类失败)
   ↓
REPORT   (push experiment_reports/RUN_<date>_<id>/ 到 GitHub)
   ↓
DECIDE   (Cloud 分析 → 写 research_memory/decisions/ + failures/)
```

## 4. 预注册与多重性（防数据挖掘）
- REGISTER 阶段冻结：假设、特征集、窗口、Top-K/hold 比较组、预期比较数 `m`。
- 跑完不许搜参/换窗/换 sign（改动 = 新 experiment_id + 重计 m）。
- 报告含 FDR（BH q=0.05）over 所有预注册比较（沿用治理）。

## 5. 与 research_memory / FAILURE_ATLAS 的关系
- 每个 experiment 结束 → 追加一行到 `FAILURE_ATLAS`（含 experiment_id / hypothesis / result / failure_class / evidence / decision）。
- accepted/rejected 决策写入 `research_memory/`（见 `RESEARCH_MEMORY_DESIGN.md`）。
- **新实验 REGISTER 前必须查 FAILURE_ATLAS + research_memory/rejected**，命中即拒绝重跑（防重复）。

## 6. 复现命令（示例，不在本阶段运行）
```
# Local（有冻结 pack）:
python -c "from research_engine.cn_a_share_alpha.pack import pack_panel; pack_panel()"
python -m research_engine.cn_a_short.run_baseline --forensic
# 校验：同 manifest_hash + 同 seed + 同 windows → 关键 METRICS 确定性一致
```
