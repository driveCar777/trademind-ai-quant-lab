# Research Protocol V0.3 Audit

2026-08-25T13:52:08Z。

## Anti-cheat

| 搜索 | research_protocol/ | data_layer 调用 |
|------|-------------------|-----------------|
| order_send( | 无 | 无 |
| order_check( | 无 | 无 |
| positions_get( | 无 | 无 |
| orders_get( | 无 | 无 |
| mine_longrun / mine_is_only / watchdog | 调度脚本无 | — |

`data_layer/constants.py` 仅把上述名字列为只读拒绝清单，不是调用。

V11.7 / `data/mine/longrun/` / `master/api/` / 现有 Xavier Worker：本阶段未改。

## Integrity

- immutable bars.csv sha256 与 manifest：0 mismatch
- 16 份 Windows `CANDIDATE_WINDOW` 与各 Xavier `window_hash`：0 mismatch
- `data/market/final_oos/LOCK.json`：`FINAL_OOS_LOCKED=false`

## Nodes

| Node | Host | Python | 计算秒 | 调度秒 | 任务 |
|------|------|--------|--------|--------|------|
| Xavier-01 | 192.168.1.200 | 3.6.9 | 132.6 | 134.8 | GOLD×4 + OIL M15/D1 |
| Xavier-02 | 192.168.1.201 | 3.6.8 | 131.5 | 133.6 | EURUSD×4 + USDJPY M15/D1 |
| Xavier-03 | 192.168.1.202 | 3.6.8 | 131.2 | 133.4 | USDJPY×4 + EURUSD M15/D1 |
| Xavier-04 | 192.168.1.203 | 3.6.9 | 128.9 | 131.1 | OIL×4 + GOLD M15/D1 |

每任务 10 次 feature + 10 次 window + 10 次 leakage。合成语料各 10 次。全部 PASS。

## Cross hashes

GOLD M15 feature `57dd2fbed870a8d0e1b84699c20d00d1d37bb685d8b53bf044169e2d8d1e406b`  
OIL D1 feature `a6903c6130a1de1f78f8ff56b10e4241c200dbf3575e4998397bd8ba0262bbd9`  
EURUSD M15 feature `53d80fa8d10c330ddd051c99c050b6f12f7a20cc77aae1f39d8b0b56106b0a87`  
USDJPY D1 feature `70bf447fe0dd9ec03b37037aafd69e0dbb7990e02decb9b82c3585914129f44c`

protocol_source_hash `02e8ce5056342e1a0156470eecb80f84fa4afaf6eafe2ba25f16a1f19d3337da`  
registry_hash `e931dcede36a5d165fa67604be9bc54d8ac6617ce5ec6cba3cf9c0c9e3a14126`

## Flags

COMPUTATION_MISMATCH = none  
LEAKAGE_DETECTED = none  
BOUNDARY_LEAKAGE = none  
DETERMINISM_FAILURE = none
