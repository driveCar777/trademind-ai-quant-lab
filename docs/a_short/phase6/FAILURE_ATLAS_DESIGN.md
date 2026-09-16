# FAILURE_ATLAS_DESIGN.md

> Phase 6 — 失败知识库设计。目的：把每次失败沉淀为可查询证据，**未来任何 AI/人在提出新实验前先查，避免重复踩坑**。**只设计。**
> 沿用仓库既有约定 `POST_V21_AUTODRIVE/FAILURE_ATLAS.json`（ML1 系列已用）；A-Short 建自己的 atlas，不改旧的。

---

## 1. 位置与格式
```
research_memory/failures/FAILURE_ATLAS.json      # 追加式数组，每行一个已判失败
research_memory/failures/EXP_<NNNN>.md           # 单实验详述（可选，长证据）
```
- 追加式，**只加不改历史**（治理：不改写 evidence）。
- 小 json，入 GitHub（无 raw data）。

## 2. 每条 atlas 记录字段
| 字段 | 含义 |
|------|------|
| `experiment_id` | EXP_NNNN |
| `date_utc` | 判定日期 |
| `hypothesis` | 预注册假设（一句话） |
| `dataset_hash` / `code_commit` / `contract_id` / `parameter_hash` / `model_version` | 绑定（EXPERIMENT_PROTOCOL） |
| `result` | 关键指标（IC/excess/net/…） |
| `failure_class` | DATA / MODEL / EXECUTION / COST / SOFTWARE |
| `failure_code` | 细分（见 §3） |
| `evidence` | 证据（forensic 字段/文件引用，如 t_excess、carry_rate、DATA_SNAPSHOT 分位） |
| `decision` | REJECT / KEEP_LOW_PRIORITY / NEEDS_DATA / RETRY_WITH_NEW_CONTRACT |
| `do_not_retry` | 布尔 + 原因（防重复触发） |

## 3. 分类（五类 + 细分码）
- **DATA_ERROR**：`MISSING_BAR / TIME_LEAK / PIT_ERROR / DEGENERATE_PANEL / DATA_BLOCKED / INCOMPLETE_UNIVERSE`
- **MODEL_ERROR**：`NO_ALPHA / OVERFIT / STYLE_EXPOSURE_ONLY / UNSTABLE / SAME_CLUSTER(corr≥0.9)`
- **EXECUTION_ERROR**：`UNFILLABLE / LIMIT_LOCK / SUSPENSION / T1_VIOLATION / OVERLAP_UNDERCOUNT / STUCK_MISPRICED`
- **COST_ERROR**：`COST_EROSION / TURNOVER_TOO_HIGH / MIN_FEE_DOMINATED / SLIPPAGE_UNVERIFIED`
- **SOFTWARE_ERROR**：`BUG / ENV_MISMATCH / NON_DETERMINISTIC`（代码层映射 `ENV_ERROR + code_bug`）
> 与 Phase 3 `forensic/errors.py` 及 `A_SHORT_FAILURE_DIAGNOSIS.md` 对齐；SOFTWARE_ERROR = Phase 6 命名，映射现有 ENV_ERROR。

## 4. 查询流程（防重复）
```
提出新实验 → 计算候选 (hypothesis, feature, universe, hold, contract)
   → 查 FAILURE_ATLAS：是否已有 do_not_retry 命中？
        命中 → 拒绝重跑，引用 atlas 行；除非带“新证据/新数据/新合同”
        未命中 → 允许 REGISTER（EXP_NNNN）
```
- A-Short 的历史已知禁区（须预置进 atlas）：20D 动量 = CONTROL 非策略；ST/微盘 β 错觉；¥5 最低佣金主导小单；T+1 满换成本天花板；V33 涨停不可交易（不可复用）；新闻/政策无 PIT 语料不可回测。

## 5. 与治理的一致性
- 不改写历史 evidence；失败也是有效结果（NO_ALPHA/DATA_BLOCKED 照记）。
- 任何“看起来很好”的结果先进 atlas 的**审计队列**（leakage/幸存者/β/重复检验/regime），审计通过才升级，不直接当 candidate。
