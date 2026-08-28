# Data Qualification V0.1

冻结日期：2026-08-25。

DATA_QUALIFICATION_V0.1 = FROZEN  
V11.7 = 仍 FROZEN  
Data Layer V0.1 = 仍 FROZEN  
FINAL_OOS_LOCKED = false

## 目的

对 Data Layer V0.1 已冻结的 16 份真实市场数据做独立、确定性、可复验的资格审查与画像。

回答：数据是否干净、覆盖是否足够、价格行为如何、快照是否稳定、哪些 dataset 具备下一阶段研究资格。

不回答：哪个策略赚钱。

## 输入

只读 `data/market/immutable/{dataset_id}/` 的 `bars.csv` + `manifest.json` + `DATA_QUALITY.json`。

不读 `data/mine/longrun/`。不重新连 MT5。不改冻结文件。

## 计算方法

`research_profile/research_probe.py`：Python 3.6 标准库，一次性进程，无 HTTP 端口。

- SHA256 复验
- OHLC / return / log-return / 滚动波动 20/50 / True Range / ATR14（TR 的 14 期简单均值）
- K 线结构、gap、tick_volume、spread
- 异常只标记不修复
- 最大 10 个 |return| 标 EXTREME_MOVE
- trend_efficiency = abs(last-first) / sum(|delta|)
- Qualification 四档：QUALIFIED / QUALIFIED_WITH_WARNINGS / DATA_REVIEW_REQUIRED / DATA_INVALID

禁止 RSI / MACD / 回测 / Sharpe / P/L。

## 四节点分工

| Xavier | IP | 品种 |
|--------|-----|------|
| 01 | 192.168.1.200 | GOLD × 4 |
| 02 | 192.168.1.201 | EURUSD × 4 |
| 03 | 192.168.1.202 | USDJPY × 4 |
| 04 | 192.168.1.203 | OIL × 4 |

派发：`scripts/data_qualification_run.py`（SSH/SCP，复用 `TRADEMIND_XAVIER_*`）。远程 `/tmp/tm-data-qual-v01`，算完删除。

## 验证方法

GOLD M15 000001 在 Xavier-01 与 Xavier-04 各算一次。去掉时钟/节点字段后数值必须完全一致。

本次：**PASS**。

## Qualification 规则

- DATA_INVALID：hash / OHLC / 重复 / 乱序 / NaN / 零负价
- DATA_REVIEW_REQUIRED：周期重叠，或 |return|>=10% 的 bar >= 10 根
- QUALIFIED_WITH_WARNINGS：基础通过，但 real_volume 全 0、session gap、或列出了 EXTREME_MOVE
- QUALIFIED：以上警告都不存在

资格 = 研究就绪，≠ 值得交易。

## 快照差异规则

比较 timestamp + OHLC + tick_volume + real_volume + spread。

最后一根（或任一侧最后一根）变化 → LATEST_OR_FORMING_BAR。

更早的已关闭 bar 的 OHLC 变化 → HISTORICAL_MUTATION。

本次 GOLD M15 000001 vs 000002：1999 行相同，仅最后一根 close/tick_volume 不同。**无 HISTORICAL_MUTATION**。

## 确定性验证

同输入、同代码版本，跨节点 comparable() 字典相等。代码版本 = probe 文件 SHA256。

## 结果索引

- `data/market/profiles/DATASET_PROFILE_INDEX.json`
- `data/market/profiles/DATASET_QUALIFICATION_REPORT.md`
- `data/market/profiles/CROSS_NODE_VERIFY.md`
- `data/market/profiles/SNAPSHOT_DIFF_GOLD_M15.md`
- 每个 dataset 的 `dataset_profile.json` / `.md`

## 已知限制

- 无 pandas/numpy；ATR 非 Wilder
- Ava `real_volume` 全 0
- OIL D1 因 2020 极端日收益进 REVIEW，不是 schema 损坏
- 70/15/15 只是 CANDIDATE_WINDOW

## 下一阶段

只记录：未来回测引擎的 OHLCV 合同、时间戳、血缘、research/validation/holdout、Final OOS 锁定。本次不实现，也不锁 Final OOS。
