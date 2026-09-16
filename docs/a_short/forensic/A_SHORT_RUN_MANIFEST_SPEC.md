# A_SHORT_RUN_MANIFEST_SPEC.md

> 每次实验的 Run Manifest 规范。目的：任何结果都能回答「哪一次代码 / 哪一次数据 / 哪一次模型产生的」。

---

## 1. RUN_ID
```
A_SHORT_<experiment>_<UTC_YYYYMMDDTHHMMSSZ>
例：A_SHORT_baseline_momentum_20260916T121500Z
```
- `<experiment>`：小写下划线（baseline_momentum / cost_tables / …）。
- 时间戳 = UTC ISO 基本格式（可排序、唯一）。

## 2. 目录
```
results/runs/<RUN_ID>/{RUN_MANIFEST,CONFIG,DATA_LINEAGE,SIGNALS,TRADES,LEDGER,METRICS,ERRORS}.json + REPORT.md
```
（实现落 `data/market/research_engine/cn_a_short/runs/<RUN_ID>/`；大件 gitignore。）
并发安全：沿用 `paper_ops` 的 `runs/CURRENT.json` 独占锁模式（可选）。

## 3. RUN_MANIFEST.json 必需字段
| 组 | 字段 | 来源 |
|----|------|------|
| 代码 | `git_commit`, `branch`, `dirty`(有无未提交改动) | `git rev-parse HEAD` / `symbolic-ref` / `status --porcelain` |
| 环境 | `python_version`, `os`, `platform`, `dependencies`(name→version，至少 numpy) | `platform`, `importlib.metadata` |
| 数据 | `upstream_dataset_id`, `upstream_hash`, `derived_dataset_id`, `derived_dataset_hash`, `pack_meta_hash` | 合同常量 + pack meta |
| 合同 | `contract_id`, `contract_hash`(sha256 合同 md) | `run_baseline._meta`（已有） |
| 模型 | `model_name`, `model_version` | 常量（当前 `20D_MOMENTUM_BASELINE` / `v1`） |
| Universe | `universe_definition`(boards/exclude_st/min_hist/min_eligible 等结构化) | `__init__` + baseline 默认 |
| 成本 | `cost_model_version` | `cn_a_short/cost.py` 常量指纹 |
| 执行 | `execution_simulator_version` | `top_k_period` 语义版本号（含 EXIT_CARRY_MAX） |
| 随机 | `seed` | `__init__.SEED`（已有） |
| 窗口 | `research/validation/oos_window` | 已有 |
| 时间 | `generated_at_utc` | 已有 |
| 状态 | `status`(RESEARCH_COMPLETE / DATA_BLOCKED / …) | 已有 |

> 现状：`run_baseline._meta` 已覆盖 contract/upstream/derived/commit/seed/windows/generated_at。**待补**：branch/dirty、python/os/deps、model_name/version、universe_definition(结构化)、cost_model_version、execution_simulator_version、pack_meta_hash。

## 4. 版本号约定（新增常量，不改逻辑）
- `MODEL_VERSION = "20D_MOMENTUM_BASELINE/v1"`
- `COST_MODEL_VERSION`：hash(COMMISSION,TRANSFER,SLIPPAGE,STAMP_NEW,MIN_FEE,LOT) → 短指纹
- `EXECUTION_SIMULATOR_VERSION`：hash(撮合语义关键常量：EXIT_CARRY_MAX + 撮合规则版本串)

## 5. 复现（Reproducibility）
- `REPRODUCTION` 段：精确复现命令（含 RUN_ID 不必相同，但 normalized manifest 应一致）。
- **规范化 manifest hash**：对 manifest 去掉 `generated_at_utc`（和可选 `git_commit` 若跨 commit 比较）后 sha256，作为"同输入→同结果"的判定键（测试用）。
- 判定：same code+data+config+seed ⇒ 规范化 manifest hash 一致、METRICS 关键数值确定性。若不一致 → 报告 `REPRODUCIBILITY=FAIL` 并解释。

## 6. CONFIG.json
本次入参：`window/equity/boards/horizons/top_ks/model/slippage_grid/…`（就是 CLI/函数参数的快照），与 manifest 分离以便对比"同代码不同配置"。

## 7. DATA_LINEAGE.json
`upstream_dataset_id/hash`、`derived_dataset_id/hash`、`pack_exists`、`pack_meta`（若有）、`panel_coverage` 摘要、`data_status`(READY/DATA_BLOCKED/DEGENERATE)。
