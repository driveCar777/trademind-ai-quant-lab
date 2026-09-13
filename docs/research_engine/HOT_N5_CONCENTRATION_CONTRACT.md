# HOT_N5 集中度合同（热台对照账，预注册，只读一次）

**日期：** 2026-09-11（跑前写；用户授权的"激进杠杆 = 集中"）  
**归属：** `:9001` 热台「对照账」第四本。**不是 Candidate、不是 Level-1、不改 `:9000` / `daily.py` / ML1 / V26.8。**  
**代码：** `research_engine/hot_three_books/book_n5.py` → `live/paper_hot/B_N5_LEDGER.json`

## 1. 假设（事前）

V26.8 选 `n_target=10` 是研究期按夏普在 {10,20,40} 里挑的。集中到 5 只会放大单票权重：期望 TWR 更高、MaxDD 更深。这是**外壳参数**，不是 alpha。

## 2. 唯一改动

| 项 | 账本1（V26.8） | 本合同 |
|---|---|---|
| ML1 分数 | 冻结 `SCORES_ML1_LGBM.npy` | 同 |
| 外壳 `SHELL` | `assets.py`：¥20k、主板、≤¥100、等金额、100%、补仓、月定投 ¥2k | 同 |
| `n_target` | 10 | **5** |
| 引擎 | `top_n_book` + `daily_curve` | 同一函数、同一调用方式 |
| 窗口 | `VALIDATION` 2021-08-25 → 2024-02-29 | 同；**不读研究期、不读禁用窗、不读近期窗** |

单位 = `max(2000, 权益/5)`。其它任何东西都不动。

## 3. 指标（读一次，全部记录）

- `twr`（时间加权）与 `cagr`
- `daily_maxdd`：`daily_curve` 逐日盯市曲线的最大回撤（峰/谷/是否恢复）
- `equity_end`、`deposits`
- 逐期 `excess_vs_b1 = ret_n5 − ret_b1`（同一信号日对齐 `B1_LEDGER.json`）；`periods_beaten` = 正的期数 / 总期数
- `mean_excess_vs_b1`、`t_excess_vs_b1`

## 4. 标签规则（事前）

```
VIABLE_HISTORICAL  iff  twr > 0  AND  twr >= 0.390298 (账本1 冻结验证 TWR)
NOT_VIABLE         otherwise
```

标签 = `HOT_N5_CONCENTRATION_{VIABLE_HISTORICAL|NOT_VIABLE}`。无论哪个：**不是 Candidate**；不改主线 `n_target`；不进 `daily.py`。

## 5. 禁止

- 跑完不许试 N=3/4/6/7/8；不许调单位下限；不许按结果换主线。
- 不许读研究期为 N5 找解释；不许读禁用/近期窗。
- 不许把 N5 与 Layer A/B 混算；它只是对照账。

## 6. 结果（2026-09-11 23:00，已读一次，锁定）

**`HOT_N5_CONCENTRATION_NOT_VIABLE`**

| 指标 | N5 | 账本1（N10） |
|---|---|---|
| 验证 TWR | **−0.79%** | +39.03% |
| CAGR | −0.31% | ≈ +14% |
| 逐日盯市 MaxDD | **−28.1%**（峰 2022-12-13 → 谷 2024-02-06，未恢复） | −24%（V26.8 记录） |
| 期末权益 | ¥70,283（含定投 ¥54k） | ¥86.9k |
| 打过账本1 的期数 | **8 / 29** | — |
| 逐期超额 vs 账本1 | 均值 −1.19%/期，t **−2.03** | — |

结论：集中到 5 只把 V26.8 的验证收益几乎全部抹掉，回撤更深，且 29 期里 21 期落后。假设（"集中 = 更高 TWR"）**被证伪**。这不是 alpha 问题，是一个外壳参数在这段窗口上的单次读数；**不因此调主线、不试其它 N、不读别的窗**。热台「对照账」保留 `B_N5_LEDGER.json` 供审计。`B_N5_LEDGER.json` 存在且 `read_once=true` 时 `book_n5.build()` 拒绝再跑。
