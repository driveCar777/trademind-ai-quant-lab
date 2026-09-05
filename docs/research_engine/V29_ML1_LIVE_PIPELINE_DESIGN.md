# V29 — ML1 前向管线（Paper 准备）设计

> Phase 1 Design。模块：`research_engine/ml1_live/`。目的：让 V26 规格的 ML1 每天能在**真实新数据**上产出名单、并把每一期的实际结果记在账上。
> 不发单。不碰冻结数据集。不改 ML1 任何参数。Paper 账户/行情源/开始日仍由用户决定；本模块先跑**影子账本**（用真实开盘价结算，无资金）。

## 1. 边界

| 允许 | 禁止 |
|---|---|
| 从 BaoStock / 东财增量拉 2026-08-29 之后的原始数据 | 改写 `tm-ashare-EQUITY-D1-20260830-000002` 及任何冻结 raw / normalized / alpha_cache |
| 用 V25 的 14 个特征函数、V26 的 REFIT_240 政策重新拟合 | 换特征、调参、换 hold / 分位 / 成本、看结果后挑变体 |
| 输出前 20% 名单 + 等权目标金额 + 影子账本 | `order_send`、任何券商接口 |

## 2. 数据流

```
frozen pack (…2026-08-28)  ─┐
live/bars/{symbol}.csv (2026-08-29…) ─┼─► live pack (内存 + live/pack/*.npy, meta 含 frozen_dataset_id + live_hash)
live/calendar.csv, live/basics.csv ─┘
margin raw (东财, 按日文件, END=今天)            ─► margin normalized_live (V23 compile, PIT lag 1)
holders raw_live (东财, 每股全史, 每周)           ─► holders normalized_live (V24 compile, 公告日截止=今天)
financial annual raw (BaoStock, 每月只补当年)   ─► V16 score_matrix（公告日）
index as-of monthly (BaoStock, 每月 15 日)       ─► V20 member_score
                                                  ─► V25 build_features → live/features/*.npy
                                                  ─► REFIT_240 模型缓存 live/models/REFIT_{date}.pkl
                                                  ─► live/signals/SIGNAL_{date}.json（名单）
                                                  ─► live/ledger/LEDGER.json（影子账本）
                                                  ─► live/STATUS.json
```

- **live pack** = 冻结面板逐位复制 + 新日期追加。符号顺序 = 冻结 5549 只 + 新上市（追加在后；新股 <40 个交易日本就不合格）。日历、basics 每次运行从 BaoStock 刷新到今天。
- **PIT 不变**：融资 lag 1；户数/年报公告日后可见；成分 as-of。特征只用到打分日收盘。
- 各层缓存的存在性检查以 live pack 的 T 为键：T 变了就重编译。

## 3. 打分政策（= V26）

- refit 日期序列：从 2012-01-04 起每 240 个交易日（与 V25.1 / V28 同一序列）。最近一次 2025-11-06，下一次 ≈ 2026-10-30。
- 打分日 t 用「≤ t 的最近一次 refit」的模型；训练行 = 研究起点起每 5 日、标签完全可知（≤ refit − 21）的所有截面；LightGBM 参数 = V25 合同；seed 固定。
- 模型按 refit 日期 pickle 缓存；同一 refit 日期只拟合一次。
- 名单：合格股票（上市、交易、非 ST、≥40 日历史、当日有量）按分数取前 20%，等权。`SIGNAL_{date}.json` 含：日期、n_eligible、n_selected、symbol 列表、每只目标权重、给定资金下的目标金额与手数（100 股整数）、14 个特征在当日的覆盖率、模型 refit 日期、live pack hash。

## 4. 影子账本（V26 规则）

- 期链接续 V28：V28 最后信号 2026-07-30，之后每 21 个交易日一个信号日（信号 t → t+1 开盘买 → t+21 开盘卖 → 同日再打分）。
- 每期记录：信号日、入场/出场日、名单、成交数（涨跌停/停牌按 V14.1 规则不成交留现金）、成本后收益、合格 EW 同期收益、LO−EW。
- 自动判定：12 期滚动 LO−EW < −8% → `PAUSE_REVIEW`；24 期连续 LO−EW ≤ 0 → `RETIRE`。只判定、写状态，不自己"恢复"。
- 账本在出场日数据到位后才结算；未到期显示 `OPEN`。

## 5. 运行

`python -m research_engine.ml1_live.daily [--capital 5000000] [--force-score]`
1. 刷日历/basics → 2. 增量 bars（每股一次 BaoStock 调用，只拉缺的日期）→ 3. margin 增量 → 4. 周/月任务按到期执行 → 5. 组 live pack → 6. 重编译到期的层 + 特征 → 7. 若今天是信号日或 `--force-score`：打分写名单 → 8. 结算已到期的账本期 → 9. `STATUS.json`。
- 幂等：重复运行同一天不重复拉、不重复拟合。
- BaoStock 同时只一个登录（复用 `BaoSession`）。

## 6. 冒烟测试（Phase 3 标准）

1. live pack 前 8714 行与冻结面板逐位相同（open/close/volume/tradestatus/isST/listed）。
2. 2026-08-29 → 最近交易日新增行数 = 日历天数；随机 20 只股票 close 与 BaoStock 单独查询一致。
3. 特征在 ≤ 2026-08-28 与 `v25_features_finaloos` 缓存逐位相同。
4. 用 REFIT 2025-11-06 模型对 2026-08-28 打分：名单与 V28 `SCORES_FINAL_OOS_GATE_REFIT240` 当日前 20% 完全一致（同一模型、同一输入 → 同一输出）。
5. `SIGNAL_{latest}.json` 生成；账本第一期（信号 2026-08-28）状态 OPEN，入场成交数与 xok 一致。

## 7. 稳定性（Phase 4）与冻结（Phase 5）

- 连续 5 个交易日日更无人工干预、无重复拉取、无拟合重复；第一期出场后账本结算成功。
- 冻结后：只允许改 bug 与数据源故障处理；任何影响名单的改动 = 违反 V26。
