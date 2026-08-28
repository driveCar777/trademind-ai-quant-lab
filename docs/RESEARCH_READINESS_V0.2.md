# Research Readiness V0.2

冻结日期：2026-08-25。

RESEARCH_READINESS_V0.2 = FROZEN  
DATA_QUALIFICATION_V0.1 = 仍 FROZEN  
Data Layer V0.1 = 仍 FROZEN  
V11.7 = 仍 FROZEN  
FINAL_OOS_LOCKED = false

## Scope

对 16 个不可变 dataset 做分块、滚动、分布、自相关、极端集中度、快照稳定性和四节点 20 次重复指纹。

不是策略、不是回测、不是选参。

输入只读：`data/market/immutable/`。

## Dataset Matrix

GOLD / EURUSD / USDJPY / OIL × M15 / H1 / H4 / D1。每份 2000 bars。Ava Trade MT5，build 6140。

GOLD M15 000001 另在 Xavier-04 复算 20 次。

## Xavier Allocation

| Node | Host | 主任务 | 额外 |
|------|------|--------|------|
| Xavier-01 | 192.168.1.200 | GOLD ×4 | |
| Xavier-02 | 192.168.1.201 | EURUSD ×4 | |
| Xavier-03 | 192.168.1.202 | USDJPY ×4 | |
| Xavier-04 | 192.168.1.203 | OIL ×4 | GOLD M15 ×20 |

## Runtime

墙钟约 3 分钟（四台并行）。节点本机：01 141s、02 150s、03 143s、04 172s。

Full profile 次数：4×80 + 20 = **340**（超过要求的 320）。全部成功。

每份分析含 8 blocks + 19 rolling。计算量约 **2720** block profiles、**6460** rolling windows。

## Resource Usage

CPU 频率全程 **2265600 kHz**，min=max，未见降频。  
CPU-therm 约 33–36°C。`PMIC-Die` 读数 100°C 是 Jetson 占位传感器，不是 CPU 结温。  
内存 Available 约 28 GB。未改 nvpmodel。未见 thermal throttling。

## Repeat Determinism

每份 20 次：`profile_hash` / `block_hash` / `rolling_hash` / `quantile_hash` / `extreme_hash` 全同。  
**DETERMINISTIC_REPEAT = PASS**（17/17 任务行，含跨节点 GOLD M15）。

## Cross Node Determinism

GOLD M15 000001：Xavier-01 与 Xavier-04  
`profile_hash = 0b063463826df38f5605ce91d6c944cbc9cef0098b7fc4b32363493819aa678c`  
**PASS**

## Block Stability

8×250 连续块。`max/min >= 4` 记 STATISTICAL_CHANGE（不是 STRATEGY_REGIME）。

出现 block 比异常的：GOLD D1 / H4，USDJPY D1 / H1 / M15，OIL H4。

## Rolling Stability

200-bar 窗口、步长 100、每份 19 窗。结果写入 `data/market/research_readiness/rolling/`。

## Return Distribution

P1–P99 确定性分位（index = floor(p/100*(n-1))）。偏度已算。不是交易胜率。

## Autocorrelation

`sum((x_t-m)(x_{t+k}-m))/sum((x_t-m)^2)`，lag 1/5/10。只描述收益依赖。

## Volume Profile

仍是 tick_volume。real_volume 全 0。部分 D1/H4 出现 VOLUME_BLOCK_RATIO（tick 均值跨块变化大）。

## Spread Profile

只描述。部分 dataset 有 SPREAD_BLOCK_RATIO 未触发（阈值 4）。

## Extreme Move Concentration

Top 20 |return| 合法 OHLC → MARKET_EXTREME，不自动坏数据。

>50% 落在单块：

- GOLD D1 block 7 share 0.70
- USDJPY M15 block 1 share 0.90
- OIL D1 block 0 share 0.60
- OIL H4 block 5 share 0.60

## Session Gap Distribution

P50/P90/P95/P99 与 max gap 在各 analysis 的 `gap_distribution`。周末不是错误。D1 不按 24h 判错。

## Snapshot Stability

000001 vs 000002：1999 行相同，仅最后一根 2026-08-25T12:45:00Z。  
**SNAPSHOT_STABILITY = PASS**  
**HISTORICAL_MUTATION = false**

## Fault Injection

临时副本 8 类故障（删行/重复/乱序/改 close/改时间/high<low/改 tick/截断）四台均检出。  
**FAULT_INJECTION_PASS = true**。immutable 未写回。

## Qualification

探针把「Top20 皆为 MARKET_EXTREME」也标成 READY_WITH_REVIEW，干净数据会全部落在这一档。  
**结构映射**（报告用，不改冻结 JSON）：

| 档 | dataset |
|----|---------|
| READY_FOR_RESEARCH | GOLD M15, GOLD H1, EURUSD M15/H1/H4/D1, USDJPY H4, OIL M15, OIL H1 |
| READY_WITH_REVIEW | GOLD H4, GOLD D1, USDJPY M15, USDJPY H1, USDJPY D1, OIL H4, OIL D1 |
| HOLD_FOR_REVIEW | 无 |
| INVALID | 无 |

OIL D1：`OIL_D1_EXTREME_REVIEW = MARKET_EXTREME`。20 个极端日 OHLC/时间合法，集中在 block 0（2020）。不是 DATA_INVALID。

## Known Limitations

- 探针 qualification 对 Top20 过严；以本文件结构映射为准
- ATR14 为 TR 简单均值
- `PMIC-Die` 100°C 不可当作 CPU 温度
- 70/15/15 仍是 CANDIDATE_WINDOW

## Next Stage

已完成：`docs/RESEARCH_PROTOCOL_V0.3.md`（合同 + 泄漏哨兵，未锁 Final OOS）。  
不要锁 research/validation/holdout。FINAL_OOS 保持 UNLOCKED。

索引：`data/market/research_readiness/RESEARCH_READINESS_INDEX.json`
