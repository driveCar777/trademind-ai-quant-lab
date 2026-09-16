# A_SHORT_PHASE2A2_DATA_FORENSIC.md

> Phase 2A.2 数据血缘取证。**先验证数据，再谈 alpha。** 结论先行：**frozen D1 价格面板在本 Cloud VM 无法物化 → `DATA_BLOCKED`**（原则性，不是懒）。
> 未编造任何价格/收益数字；未改冻结数据；未从 BaoStock 旁路重建（会得到不同、不可验证、与注册 `upstream_hash` 不符的数据集）。

---

## 0. 环境 / 合同一致性（Step 1）✅
| 项 | 值 | 校验 |
|----|----|------|
| branch | `cursor/a-short-architecture-forensic-3072` | ✅ |
| HEAD | `5d8ffd7f…`（运行时；见 artifact `code_commit`） | ✅ |
| git diff --check | clean | ✅ |
| contract_id | `A_SHORT_D1_V1` | ✅ 一致 |
| upstream_dataset_id | `tm-ashare-EQUITY-D1-20260830-000002` | ✅ 一致 |
| upstream_hash | `dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80` | ✅ 一致 |
| research window | `2014-01-01 .. 2021-12-31` | ✅ 一致 |
| validation | `2022-01-01 .. 2023-12-31` | ✅ 一致 |
| OOS | `2024-01-01 .. latest`（LOCKED） | ✅ 一致 |
| seed | `20260916` | ✅ |
| m（主比较） | `4 horizons × 5 Top-K = 20` | ✅ |

无任何不一致。

---

## 1. Frozen panel 物化尝试（Step 2）→ 失败
`pack_panel()` 的真实数据来源（读代码 `research_engine/cn_a_share_alpha/pack.py`）：
```
PANEL_RAW/symbols/<symbol>/raw.csv   # 逐股票冻结原始 OHLCV CSV（"Never call BaoStock"）
```
本 VM 检查：
| 检查 | 结果 |
|------|------|
| `pack_exists()` | **False** |
| `PANEL_RAW`（`data/market/cn_a_share/raw/daily_panel_v12_1`） | **不存在** |
| `PANEL_RAW/symbols` | **不存在** |
| 任意 `raw.csv` / `daily_panel*` | **0 个** |
| `live/bars` | **空** |
| `baostock` 模块 | **未安装** |

**关键陷阱（已修）**：`pack_panel()` 对缺失的 `raw.csv` 是**静默 `continue`**，会写出一份**全 NaN 的 pack**并"成功"返回。这会让 runner 在空数据上"跑出"n_signal=0 的假结果。已加守卫（见 §4）。

**为何不从 BaoStock 重建**（原则性）：
1. `AGENTS.md` 硬规则：**BaoStock 登录只从 :9000 发**；本环境是 Cloud，非 :9000。
2. `pack.py` 明确 **"Never call BaoStock"**——冻结 pack 只从冻结原始 CSV 构建。
3. 重新抓取会产生**不同的数据集**，其 hash ≠ 注册的 `dd39193c…` → **违反 lineage / 合同不可变性**，等于凭空造一个未审计数据集（本阶段禁止）。

→ **STATUS = DATA_BLOCKED**（`reason = FROZEN_PRICE_PACK_NOT_MATERIALIZED`）。artifact：`PHASE2A2_RESULTS.json`。

---

## 2. 数据血缘摘要（可算部分 / 不可算部分）
| 字段 | 值 |
|------|----|
| upstream_dataset_id | `tm-ashare-EQUITY-D1-20260830-000002` |
| upstream_hash | `dd39193c…ae80` |
| derived_dataset_id | `tm-ashort-D1BASE-V1` |
| derived_dataset_hash | **N/A（BLOCKED，无 pack 无法盖章）** |
| calendar_id | `tm-cn-a-CALENDAR-20260830-000001` ✅ 存在 |
| n_trading_days | **8,714**（`1990-12-19` .. `2026-08-28`） |
| trading days in research 2014-2021 | 1,950 |
| trading days in validation 2022-2023 | 484 |
| trading days in OOS 2024-.. | 644 |
| basic universe | 5,549 EQUITY（+596 INDEX / 1,651 ETF / 1,132 CONVERTIBLE） |
| universe_history | `A_SHARE_UNIVERSE_HISTORY_V12_2.csv` ✅ 存在（310 KB，PIT 上市/退市已知日） |
| **date_min/date_max（价格）** | **N/A（无面板）** |
| **row_count / n_symbols（价格）** | **N/A（无面板）** |
| **missing_open/close/volume/amount/turn_rate** | **N/A（无面板）** |
| **listed/tradestatus/isST coverage** | **N/A（无面板）** |

> 参考层（日历/基础/universe 历史）**齐全且 PIT**；缺的正是逐股票 **OHLCV 价格面板**——正是计算前向收益/成本/执行所必需。

---

## 3. PIT / 复权 / 前视 检查（对现有件的可查部分）
- **A. PIT universe**：`universe_history` 带 `listing_date_known / delisting_date_known`；引擎 `simple_eligible` 用 `listed`（PIT 累计 `listed_cum`）判定，**不使用幸存者宇宙、不用当前在市反推、不用后验退市改历史 eligibility**。（代码可查；实证需面板。）
- **B. Corporate action**：冻结面板口径由上游 `tm-ashare-EQUITY-D1` 定义（`open/high/low/close/preclose/volume/amount/turn` + `tradestatus/isST/listed`）。本阶段**不改冻结数据口径**；复权/preclose 处理沿用冻结源，实证核对需面板。
- **C. Future leakage**：引擎结构上 PIT-safe——signal 用 ≤ 收盘(T)，`forward_label` 用 open(t+1)→open(t+1+hold)，`listed_cum` 是**历史累计（PIT-safe）**，无跨样本 normalization、无未来日期进特征、OOS 窗独立且 LOCKED。（结构可证；数值证据需面板。）

---

## 4. 修复：runner 防退化守卫（in-scope 正确性修）
新增 `baseline.panel_coverage(pack)` + `run_baseline` 守卫：加载 pack 后测 `listed==1` 处的 finite-close 覆盖率；若退化（无任何股票有价 / `finite_close_rate_when_listed < 0.2`）→ **`DATA_BLOCKED: DEGENERATE_PANEL_NO_PRICES`**，不在空数据上"跑研究"。单测 `test_panel_coverage_detects_good_and_degenerate` 覆盖（好 pack 不退化；全 NaN pack 退化）。

---

## 5. 结论
```
DATA STATUS: BLOCKED
reason: FROZEN_PRICE_PACK_NOT_MATERIALIZED (raw OHLCV panel absent in Cloud VM; BaoStock rebuild prohibited & would break lineage)
derived_dataset_hash: N/A
```
复现命令（在 :9000 主机）：
```
python -c "from research_engine.cn_a_share_alpha.pack import pack_panel; pack_panel()"
python -c "from research_engine.cn_a_share_alpha.pack import pack_exists; print(pack_exists())"
python -m research_engine.cn_a_short.run_baseline
```
物化后本 runner 会自动：跑 20 主比较、写全部 PHASE2A2 artifacts、并对退化面板报 DATA_BLOCKED。
