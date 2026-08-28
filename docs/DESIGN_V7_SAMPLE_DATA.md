# V7.0 本机样本 CSV — Phase 1 Design

> **状态：** ✅ FROZEN（2026-08-24）。  
> **日期：** 2026-08-24

## 1. 要解决什么

最终链的第一格是「数据」。现在指标研究的收盘价写死在 `research_service.PRESETS` 里，人看不见、换不了。

V7 只做一件事：指标研究从本机 `data/samples/*.csv` 读收盘价。不是行情，不是 MT5，不改 Worker。

```
人点「开始研究」（欧元美元 RSI）
  → Master 读 data/samples/eurusd.csv
  → 现有 POST /task（payload 仍是 {symbol, close}）
  → 后面研究 / 拟单 / 纸质单不变
```

## 2. 冻结范围

| 做 | 不做 |
| --- | --- |
| 内置 `eurusd.csv`（与旧硬编码同一串，RSI 仍约 76.1） | 拉实时行情、爬网、接券商 |
| `GET /api/v1/samples` 列出本机 csv | 上传控件、编辑器、数据库 |
| 指标研究可读 `sample_id`（默认 `eurusd`） | 改因子/回测/监控的内置库 |
| 人可把合规 csv 放进目录后出现在列表 | 改 Xavier Worker、新错误码 |
| 控制台写明「本机样本，不是行情」 | `order_send`、自动研究 |

因子 / 回测仍用 Worker 板上表。那是下一刀，不是本模块。

## 3. 文件约定

路径：`data/samples/{sample_id}.csv`（utf-8）。

`sample_id`：`^[a-z0-9][a-z0-9_-]{0,31}$`。禁止 `..`、斜杠、绝对路径。

表头必须有 `close`。可选 `symbol`（缺省用 `sample_id` 大写）。

- 最少 15 根（RSI 14）。  
- 最多 500 根。  
- 非法 id → `TM-1001`。  
- 文件不存在 / 读不开 / 列不够 → `TM-1003`。  
- `sample_id` 用在非 indicator 上 → `TM-1001`。

## 4. 接口

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/api/v1/samples` | 列出本机样本 |

`POST /api/v1/research/run` 增加可选 `sample_id`。空且 preset=indicator → `eurusd`。

研究记录增加可选 `sample_id`。旧记录没有该字段仍可读。

## 5. 验收

1. 仓库带 `data/samples/eurusd.csv`，`GET /samples` 能看到。  
2. 默认指标研究不再依赖 Python 里的 close 数组。  
3. 坏 id / 缺文件有稳定错误码。  
4. 控制台 `init()` 不自动研究。  
5. 仍不发 MT5。
