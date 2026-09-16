# DATA_HANDOFF_STATUS.md

> 数据血缘交接状态。结论：**REGISTERED BUT BYTES UNAVAILABLE**（注册在案，字节不在 Cloud/git）。完整取证见 `A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md`。

---

## 注册数据
```
dataset_id : tm-ashare-EQUITY-D1-20260830-000002
hash       : dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80
n_files    : 5549     n_rows : 18,418,047     history : 1990-12-19 .. 2026-08-28
source     : BAOSTOCK (BAOSTOCK_FREE_NO_KEY)   frozen raw ≈ 124GB (owner 本地 D:)
```

## 可用性核查
| 检查 | 结果 |
|------|------|
| 数据实际存在（Cloud VM）？ | **否**（`pack_exists()=False`；`PANEL_RAW/symbols` 缺失；无 raw.csv/npy） |
| 在 git？ | **否**（`git rev-list --all` 无面板对象；`raw/`、`alpha_cache/` gitignored） |
| Git LFS？ | **否**（未启用，无 `.gitattributes`） |
| release artifact？ | **否**（仅 `freeze-20260907-paper-ops-v2.1` tag，非数据 release） |
| Cloud 可恢复？ | **否**（无 git/LFS/release/对象存储可达副本） |
| hash 出现在哪 | **仅注册/文档**：`A_SHARE_PANEL_MANIFEST_V12_2.json` + 各合同 `__init__` 常量 + docs |

→ **状态：REGISTERED BUT BYTES UNAVAILABLE**（`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`）。

## 禁止事项（硬）
- **禁止用 BaoStock 偷换数据**：重抓得到的字节 point-in-time 不同，`content_hash` 几乎必然 ≠ `dd39193c…` → 破坏注册 lineage；`compile_v12_2` 明文「不要 query live BaoStock」。
- 若确需重新获取，**必须走新合同**：
  ```
  new dataset id
  new hash
  new contract (A-Short upstream 修订)
  ```
  这是**新数据集**，不是恢复 V1。

## 解冻方案（owner 决策，本阶段不执行）
- A 本地盘保存（现状） / B 对象存储（保 id+hash） / C 压缩 pack snapshot / D 只传 sample。详见 `DATA_STORAGE_POLICY.md`。

## 交接结论
```
Data: EXTERNAL / BLOCKED
- 冻结字节不随 git 交接；本地若有 D: raw 可 pack_panel() 物化，否则同样 DATA_BLOCKED。
- 不采购、不换源、不改 hash（治理硬约束）。
```
