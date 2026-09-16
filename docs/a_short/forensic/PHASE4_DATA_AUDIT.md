# PHASE4_DATA_AUDIT.md

> Phase 4 Step 1 — Data Availability Audit（只读）。结论先行：**BLOCKED**。
> 环境 = Cursor Cloud VM（无本地 Windows / :9000 / AGX / D: 盘）。禁止：装 BaoStock / 重新下载 / 生成新 dataset / 改 hash。

---

## 目标数据
```
dataset_id : tm-ashare-EQUITY-D1-20260830-000002
hash       : dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80
```

## 可用性核查（本次实测）
| 检查 | 结果 |
|------|------|
| `pack_exists()` | **False** |
| `alpha_cache/v13_000002/`（打包 npy） | **不存在** |
| `raw/daily_panel_v12_1/`（冻结逐股票 raw） | **不存在** |
| `raw/daily_panel_v12_1/symbols/` | **不存在** |
| 任意 `raw.csv` | **0 个** |
| `reference/`（日历/basics/universe） | 存在（仅参考层，非价格面板） |
| Git LFS | **未启用**（`git lfs ls-files` 空） |
| Release artifact | **无**（仅 `freeze-20260907-paper-ops-v2.1` tag，非数据 release） |
| 面板字节曾入 git 历史？ | **NONE_IN_HISTORY**（`git rev-list --all` 仅命中 `*_MANIFEST_*.json` / quality JSON 等**元数据**，无逐股票 OHLCV 字节） |

## 合法恢复路径审计
| 候选 | 可用？ | 说明 |
|------|:---:|------|
| git tracked / LFS / release / actions artifact | ❌ | 全无 |
| 既有 cache / raw | ❌ | 缺失且 gitignored |
| BaoStock 重抓 | ❌（禁止且非法恢复） | 本阶段禁装/禁下载；重抓得到不同字节，hash ≠ `dd39193c…` → 破坏注册 lineage |
→ **无任何 Cloud 可达、且不破坏 lineage 的合法恢复路径。**

## 结论
```
DATA: BLOCKED
REASON: FROZEN_BYTES_UNAVAILABLE_IN_CLOUD (REGISTERED BUT BYTES UNAVAILABLE)
```
- 与 Phase 2A.3 / 2A.2 一致，本次重新实测确认，未变。
- `python -m research_engine.cn_a_short.run_baseline` → `DATA_BLOCKED`（forensic 层已将其归类 `DATA_ERROR / DATA_BLOCKED`）。

## 采取的动作（与未采取的）
- **未** materialize pack（Step 2 跳过）；**未** 跑 baseline（Step 3 跳过）；**未** 产出 empirical runs 结果（Step 4 跳过）。
- **未** 安装 BaoStock、**未** 重新下载、**未** 生成新 dataset、**未** 改 hash、**未** 找替代源。
- 仅只读审计 + 运行既有测试（`pytest` 42 passed）。

## STOP
数据不可用 → 按协议 **STOP**。第一份 empirical evidence 需先由 owner 解冻数据（见 `PHASE4_EMPIRICAL_DECISION.md` 与 `DATA_STORAGE_POLICY.md`）。
