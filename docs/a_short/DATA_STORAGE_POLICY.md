# DATA_STORAGE_POLICY.md

> GitHub 迁移/存储策略。目标：代码与小型审计产物入 git；大数据不入 git。**当前只定策略，不执行搬运。**

---

## GitHub 保存
### 允许
- code（`research_engine/`、`master/`、`ai-gateway/` 等源码）
- docs（`docs/`，含本审计报告）
- config template（`config/*.yaml` 模板，**不含**密钥）
- small json（manifest / catalog / 研究判决 / 小 artifact，KB~低 MB）
- audit report

### 禁止
- ~124GB OHLCV 原始行情库（`data/market/cn_a_share/raw/daily_panel_v12_1/`）
- 原始行情库 / 逐股票 raw.csv
- 大型 cache（`alpha_cache/`、feature `*.npy`、live `pack/*.npy`）
- `.env` / API key / token / 凭据

## 现状（已由 `.gitignore` 保证）
| 路径 | 状态 |
|------|------|
| `data/market/cn_a_share/raw/` | gitignored |
| `data/market/cn_a_share/alpha_cache/` | gitignored |
| `data/market/cn_a_share/live/*`（`pack/*.npy` 等） | gitignored |
| `.venv-*/` | gitignored |
| `data/market/research_engine/*/SCORES_*.npy` 等 | gitignored |
> git 里只有：manifests/catalog/参考表（日历/basics/universe）、小 json、审计文档。**冻结面板字节从未进 git（Phase 2A.3 已证）。**

## 时间戳 churn 提醒
`report_tables.py` / `run_baseline.py` 会重写 `data/market/research_engine/cn_a_short/PHASE2A*_*.json`（含 `generated_at_utc`）。这些是**可复现产物**——**不要**为时间戳差异反复 commit；只在内容有意义变化时提交。

---

## 大数据未来方案（列出，当前不执行）
| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **A 本地硬盘保存** | 冻结 raw/pack 留在 owner 本地 D:（现状） | 零成本、私密、保 lineage | 不可跨机、Cloud 不可用 |
| **B 对象存储** | 上传到 S3/OSS/R2 等，按 dataset_id 组织 | Cloud/本地皆可拉、保 id+hash | 需账号/带宽/访问控制 |
| **C 压缩研究 snapshot** | 打包冻结 pack（npy）为单一压缩件（release/对象存储） | 体积小于 raw、可校验 hash | 仍需外部托管 |
| **D 只上传必要 sample** | 少量股票/时段样本入 git 供 CI/冒烟 | 轻、可入 git | 非全量，不能出正式 empirical |

## 与解冻决策的关系
- 恢复注册的冻结数据集须**保 `dataset_id` + `hash` 不变**（B/C 可满足）。
- **不采购付费数据、不换 provider、不改 hash**（治理硬约束）。
- 具体选哪个方案 = **owner 决策**（见 `A_SHORT_CLOUD_FINAL_AUDIT.md` G0）。本阶段仅记录，不搬运。
