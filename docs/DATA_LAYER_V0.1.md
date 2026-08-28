# Data Layer V0.1

冻结日期：2026-08-25。独立于 V11.7。不接回测、不接 Xavier、不下单。

## Purpose

给下一阶段 OHLCV + UTC timestamp + 可追溯研究提供**唯一可信**市场历史数据源。

给定 `dataset_id`，必须能回答：来自哪个 MT5 终端、何时抓取、时间范围、多少根 K 线、字段是什么、质量如何、文件有没有被改过。任何人不能无痕覆盖。

本版本不是策略、不是参数搜索、不是 Final OOS。

## Architecture

```text
MT5 (already logged in)
        ↓
Read-only Data Adapter
        ↓
Validation (no auto-repair)
        ↓
Immutable Dataset + Manifest + SHA256
        ↓
DatasetRepository (local Python API)
        ↓
Future research / future backtest engine
```

V11.7 继续只用原来的 `{symbol, close[], cut, strategy, params}`。新数据**不**灌进 V11.7。

存储策略：`single_immutable_copy`。`data/market/raw/` 与 `validated/` 留空，避免同一份 bars 存五份。

旧实验仍在 `data/mine/longrun/`。两边禁止混放。

## MT5 Read-only Contract

允许：`initialize`、`shutdown`、`terminal_info`、`version`、`symbols_get`、`symbol_info`、`symbol_select`、`copy_rates_from_pos`、`copy_rates_from`、`copy_rates_range`、`last_error`。

周期常量必须走 `mt5.TIMEFRAME_M15 / H1 / H4 / D1`。

禁止：`order_send` 及一切交易执行 / 持仓查询 API。调用即 `RuntimeError("DATA_LAYER_READ_ONLY")`。

不自动登录、不写账号密码。使用当前已登录终端。

不把 MT5 装到 Xavier。采集只在 Windows Master。

优先 `copy_rates_range`（UTC 起止）。失败才回退 `copy_rates_from_pos`，并写入 `history_request`。

## Dataset Schema

CSV（当前 venv 无 pandas / pyarrow，未偷偷安装）。列：

| 字段 | 说明 |
|------|------|
| `timestamp_utc` | 存储只用 UTC |
| `timestamp_unix` | MT5 `time` |
| `open` `high` `low` `close` | 必须 finite 且 > 0 |
| `tick_volume` | 不得改名为来源不明的 `volume` |
| `real_volume` | 可全 0；不得用 tick 冒充 |
| `spread` | 缺失写 null，禁止偷填 0 |

## Manifest Schema

`dataset_id` 形如 `tm-market-GOLD-M15-20260825-000001`。

必填：`dataset_id`、`logical_symbol`、`mt5_symbol`、`timeframe`、`timeframe_minutes`、`source`、`source_type`、`broker`、`terminal`、`terminal_version`、`python_package_version`、`retrieved_at_utc`、`data_start_utc`、`data_end_utc`、`row_count`、`columns`、`timezone`、`volume_policy`、`history_request`、`sha256`、`validation_status`、`schema_version`、`tick_volume_present`、`real_volume_present`、`spread_present`。

另记：`parent_dataset_id`、`requested_*` / `actual_*`、`history_shortfall`、`role`、`FINAL_OOS_LOCKED`。

## Validation Rules

| 条件 | 结果 |
|------|------|
| 缺 open / high / low / close | FAIL |
| high < max(open, close) 或 low > min(open, close) | FAIL |
| NaN / inf / 零价 / 负价 | FAIL |
| 重复 timestamp | FAIL |
| 乱序 timestamp | FAIL |
| 周期内短间隔重叠 | FAIL |
| 周末 / 时段 gap | WARN（D1 不按 24h 判错） |
| `real_volume` 全 0 | WARN + `tick_volume_only`，不 FAIL |
| 实得 < 请求 | WARN + `history_shortfall` |
| SHA256 不一致 | `DATA_CORRUPTED`，不自动修 |

不自动修复任何 bar。

## Immutable Storage Rules

第一次成功写入后禁止覆盖。再次抓取必须新 `dataset_id`，并用 `parent_dataset_id` 指向上一份。

本次已验证：`tm-market-GOLD-M15-20260825-000001` 保留；第二次抓取写成 `...-000002`，parent 指向 000001。

## Final OOS Isolation

三个角色：`RESEARCH` / `VALIDATION` / `FINAL_OOS`。

V0.1：`data/market/final_oos/LOCK.json` 中 `FINAL_OOS_LOCKED = false`。`final_oos/` 不放数据。

禁止把「刚下载的最新数据」叫 Final OOS。锁定后禁止按该窗口改 RSI / 均线 / 门槛 / 成本。

## Symbol Mapping

配置写 `logical_symbol`。现场 `symbols_get` 解析 `mt5_symbol`。

本次 Ava Trade 实测：

| logical | mt5_symbol |
|---------|------------|
| GOLD | GOLD |
| EURUSD | EURUSD |
| USDJPY | USDJPY |
| OIL | CrudeOIL |

不要假设一定存在 `XAUUSD`。

## Timeframe Mapping

`M15 → TIMEFRAME_M15`，`H1 → TIMEFRAME_H1`，`H4 → TIMEFRAME_H4`，`D1 → TIMEFRAME_D1`。

## Error Handling

`initialize` 失败：明确错误，不无限重试。`copy_rates_*` 返回 None：记 `last_error`。数量不足：WARN。结构异常 / hash mismatch / 磁盘问题：FAIL。不静默继续。请求之间限速约 0.35s。

## Test Results

`python -m unittest discover -s tests/data_layer -v`

29 tests，2026-08-25 **PASS**。

覆盖：缺 open、high<close、重复/乱序 timestamp、NaN、real_volume 全 0 不 FAIL、hash 篡改、二次保存不覆盖、`order_send` 拒绝、源码无 `order_send(` 调用、2000 bars 创建。

## Real MT5 Read-only Test

终端：Ava Trade MT5 Terminal，build 6140，包版本 5.0.5735。路径 `C:\Program Files\Ava Trade MT5 Terminal`。

方法：`copy_rates_range`。无 `order_send`。无回测。

16/16 组合各 2000 根，另加 GOLD M15 第二次快照（000002）。全部 WARN，无 FAIL，无 `history_shortfall`。

WARN 原因：Ava 的 `real_volume` 全 0（合法，`tick_volume_only`）；M15/H1/H4 有周末/时段 gap。

权威索引：`data/market/V0.1_FETCH_INDEX.json`。

## Known Limitations

- 无 Parquet（环境无 pyarrow/pandas）
- 只有 tick_volume 可用作量；real_volume 全 0
- 历史长度受终端 Max. bars 限制；本批 2000 根够用，不是无限历史
- 未接 V11.7，也没有新回测引擎
- Final OOS 未锁定
- 不比较多 broker、不对齐跨品种时间轴

### V11.7_TECH_DEBT（只记录，不修）

`review_ledgers.json` 丢掉了 worker `trades[].pnl_pct`。见 `data/mine/longrun/NEXT_EXPERIMENT_REQUIREMENTS.md` Requirement 4。

## V0.2 Requirements

只记录，本次不实现：

- 更大历史范围
- Tick 数据
- 多 broker
- 数据对齐 / 跨品种时间轴
- 股票 corporate actions
- 数据供应商对比
- dataset lineage / 快照比较
- 自动缺口修复
- Parquet adapter（环境具备 pyarrow 后再做）
