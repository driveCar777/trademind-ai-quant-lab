# Alpha Asset Inventory V1

Program: `ALPHA_PROGRAM_V1`. Phase 0.  
Scanned 2026-08-26 from disk, not from memory of chat.

Read-only. No experiment. No hash change. No Final OOS payload read.

---

## Executive Summary

仓库里没有根目录 `registry/`。研究注册表散落在：

- `data/market/research_engine/factor_discovery/registry/`
- `research_engine/family.py` / `catalog.py`（后者是草稿，正式身份以 14:11 JSON 为准）

**可继续产生信息的资产：** 16 份不可变 OHLCV（研究宇宙）+ 已冻失败结论 + 未跑的 V0.9 合同 + D1 对齐包 + 统计/成本引擎。  
**不能产生信息的动作：** 再扫 RSI/MA/Donchian、改 XA、读 Final OOS、无边就做组合。

Level 1 Candidate：**0**。

---

## 1. 扫描范围（FACT）

| 路径 | 结果 |
| --- | --- |
| `docs/` | 68 个 md；研究权威在 `docs/research_engine/`（27 个） |
| `docs/research_engine/` | 合同 / 报告 / V1 地图 / V0.9 合同（未跑） |
| `data/market/immutable/` | 17 份（16 研究宇宙 + GOLD M15 `000002` 非宇宙） |
| `data/market/V0.1_FETCH_INDEX.json` | 索引存在；`FINAL_OOS_LOCKED=false` |
| `data/market/final_oos/` | 仅 `LOCK.json` + README；**无行情** |
| `data/market/research_engine/` | HYP-0001 / FD / V0.5 / V0.6 / V0.8 结果 |
| `research_engine/` | 77 个文件：协议、因子、状态、策略、利润、跨品种 |
| `tests/research_engine/` | 29 个测试文件；上次记录 80 PASS |
| `tests/data_layer/` `research_protocol/` `research_readiness/` | 基础设施测试在 |
| `registry/`（仓库根） | **不存在** |

未打开：`data/mine/longrun/`（V11.7 已收口，禁止当研究宇宙）。

---

## 2. 现在有哪些实验？

### 2.1 已执行并冻结

| id | 磁盘位置 | 结果 |
| --- | --- | --- |
| Data Layer V0.1 | `data/market/immutable/` + `docs/DATA_LAYER_V0.1.md` | 能力 DONE，不是 alpha |
| Qualification V0.1 | docs + profiles | 画像 DONE |
| Readiness V0.2 | docs + tests | 稳定性 DONE |
| Protocol V0.3 | `research_protocol/` | 窗口/泄漏哨兵 DONE |
| HYP-0001 | `data/market/research_engine/` 14:11 JSON | 家族 rollup **WEAK_SUPPORT**；不是书 |
| FD V0.1 | `factor_discovery/` | `NO_USEFUL_FACTORS_FOUND`；57；FDR 0 |
| V0.5 | `strategy_discovery/` | `NO_USEFUL_STRATEGIES_FOUND` |
| V0.6 | `profit_discovery/` | `WEAK_EDGE_ONLY`；CANDIDATE=0 |
| V0.8 | `cross_asset/` | `NO_CANDIDATE`；3/3 FALSIFIED；FDR 0/3 |

### 2.2 仅设计 / 合同未跑

| id | 磁盘 | 状态 |
| --- | --- | --- |
| V0.7 / V0.7.1 | `ALPHA_DISCOVERY_V0.7_PLAN.md` / `ALPHA_OPERATING_SYSTEM_V0.7.1.md` | DESIGN |
| Alpha Map V1 | `ALPHA_COVERAGE_MAP_V1.md` 等 | DESIGN |
| V0.9 | `REGIME_TRANSITION_V0.9_CONTRACT.md` | **LOCKED_NOT_RUN**；无 `research_engine/regime_transition/` runner |
| FD `FAM-FD-XASSET-0001` | 仍在 FD space JSON 标 DRAFT | V0.8 **激活并跑完**；**不要改该 FD 文件** |
| FD `FAM-FD-NEWS-0001` | DRAFT | 从未算；无新闻 |

### 2.3 非正式 / 禁止当权威

| 项 | 说明 |
| --- | --- |
| `research_engine/catalog.py` | `FAM-PERSISTENCE-0001` 草稿名；正式是 `FAM-MOMENTUM-0001` |
| V11.7 `data/mine/longrun/` | 已收口；不是 Data Layer 宇宙 |
| GOLD M15 `000002` | 二次快照；不进研究宇宙 |
| 根目录 `registry/` | 不存在 |

---

## 3. 哪些失败？

失败 = 锁定合同找过该边，无程序级 CANDIDATE（或明确 FALSIFIED）。

| 类 | 证据 | 禁止再做 |
| --- | --- | --- |
| Directional 短持有 | HYP-0001；FD 动量；V0.5；V0.6 MOM | RSI / 连续上涨调参 |
| Momentum 短持有 | 同上；OIL D1 仅 WEAK_EDGE ≈+0.23% CAGR | 改 N/hold 凑第二命中 |
| Mean Reversion | FD reversal；V0.5 fade；V0.6 MR-Z20 | z / 偏离均值再扫 |
| Breakout | FD DISTHIGH；V0.6 TF-BRK20 | Donchian N |
| Cross Asset 次日美元代理 | V0.8 XA-0001/0002/0003 | 第 4 条、改 lag/67%/方向 |
| 状态 **水平** 过滤 | V0.5 / V0.6 | 「处于 TREND_STRONG 则…」 |
| 空仓当利润 | V0.6 DEF | SKIP_HIVOL 当 alpha |
| 同品种假组合 | V0.6 TF+MR+MOM 等权 | 再等权三个失败袖套 |
| tick/spread 当方向 | FD VOLUME/SPREAD | 用 tick_volume 冒充订单流 |

HYP-0001 的 WEAK_SUPPORT **不是** Candidate，也不是失败到「连预测假设都不存在」。它失败的是 **当交易书 / 当 10%**。

---

## 4. 哪些 UNKNOWN？

未测，且现有数据够起步：

| 项 | 为何仍未知 |
| --- | --- |
| Regime **transition**（Δstate） | V0.5 有 `state_id`，从未用差分当信号；V0.9 合同已锁未跑 |
| D1 极窄日历（星期/周末） | `timestamp_utc` 在；从未预注册 |
| 跨品种残差 / 比价（新机制） | 对齐包在；与 V0.8 次日代理不同；本季不并行 |
| 低换手方向（新机制） | 未开；默认不是均线 |
| ML 预注册特征 | LLM 在；无合同 |
| Risk 4A 缩放 | 模块代码有雏形；无宿主边 |

---

## 5. 哪些 DATA BLOCKED？

| 项 | 缺什么 | 磁盘证据 |
| --- | --- | --- |
| Carry | 利率 / 掉期 | immutable 无此列 |
| 真 VRP | IV | 无 |
| Event | 日历 | `FAM-FD-NEWS-0001` DRAFT |
| 订单流 / 真流动性 | `real_volume` 全 0 | 17 份 manifest `tick_volume_only` |
| 日内季节主证 | 更长 M15/H1 | M15 ≈ 1 个月 |
| 另类数据 | 外部表 | 无 |
| Final OOS 研究 | 权限 | `final_oos_access()` raise；目录无 bars |
| 真跨品种组合书 | ≥2 存活袖套 | CANDIDATE=0 |

---

## 6. 哪些资产可以继续产生信息？

**高：**

1. 未跑的 V0.9 合同（新信息：Δstate 是否在成本后存在）  
2. 失败知识（避免重复浪费）  
3. GOLD/OIL D1 2000 根 + V0.5 状态代码（转换实验的输入）  
4. 四 Xavier + `statistics.py` + V0.6 成本/仓位（执行能力）  
5. 已有 D1 对齐包（给未来**新机制** RV，不给 XA 扩族）

**中：**

6. Data Layer V0.2 加长（打开时段；不阻塞 V0.9）  
7. 被动 D1 基准（路径，不是 alpha）

**低 / 负：**

8. 再挖 16 份上的 RSI/MACD/MA  
9. 读 Final OOS  
10. 无袖套做 Portfolio 引擎

---

## 7. 基础设施资产（不是 alpha）

| 组件 | 路径 | 状态 |
| --- | --- | --- |
| 合同 / 预注册 / hash | `preregistration.py` `experiment.py` | PASS |
| FDR / bootstrap / perm | `statistics.py` + tests | PASS |
| Final OOS 拒访 | `holdout.py` | PASS |
| 成本模型 | `profit/cost/model.py` | 单策略级 DONE |
| 仓位 | `profit/risk/sizing.py` | 单笔 0.5% + 1× DONE |
| 同品种等权组合 | `profit/portfolio/combine.py` | 假组合；非跨品种账本 |
| 跨品种 runner | `cross_asset/` | V0.8 DONE；V0.9 无独立包 |
| 状态 | `regime/state.py` `adx.py` | V0.5 水平 DONE；无 Δstate 模块 |

---

## Decision

盘点完成。下一信息增益最大的动作是 **机制库 V2（不是指标库）**，然后给未知项打分。不写 V0.9 代码。

---

## Next Automatic Action

Phase 1：`CANDIDATE_MECHANISM_LIBRARY_V2.md`。
