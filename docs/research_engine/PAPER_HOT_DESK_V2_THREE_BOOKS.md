# Paper Hot Desk V2 — 三本对照账

**日期：** 2026-09-10  
**端口：** `http://127.0.0.1:9001/paper`  
**主线冻结：** `http://127.0.0.1:9000/paper`（V2.1 / V26.8）一字不改。

## 票怎么来的（事实）

- `:9000` = 本地 ML1 + V26.8。没有 Cursor。
- V1 `:9001` = Grok 联网荐股，ML1 只参考。
- V2 = 三本对照。不是 Candidate。不改 `daily.py` / ML1。

## 三本

**账本1** 冻结 `SCORES_ML1_LGBM.npy` + V26.8 `top_n_book`。Grok 不参与。21 日调仓，逐日盯市。验证 TWR 必须对上冻结 READ（约 +39.03%）。

**账本2** 同一套 V26.8 候选 → 匿名 OHLC（`U01…`，首收盘=100，无代码/名称/日期/成交量）→ Grok 只回 `keep`。禁止搜网。第一次只跑验证窗。剩余路径识别 ≠ 零泄露。不能当 Candidate。

**账本3** 最新 ML1 SHORTLIST 为池；Grok 可联网、可知代码。下一交易日开盘登记。日志 `JOURNAL.json`。不回测这本。

## 产物

只写 `data/market/cn_a_share/live/paper_hot/`：`B1_LEDGER.json`、`B2_LEDGER.json`、`B2_ANON_LOG.json`、`B2_RUN.json`、`JOURNAL.json`。

发出去的账本2 payload 不得出现 `sh.` / `sz.` / 中文名 / `YYYY-MM-DD`。

## 接口（只 :9001）

- `GET /api/v1/hot/desk` → `profile=HOT_V2`，`books.{b1,b2,b3}`
- `POST /api/v1/hot/book1/run` 回放账本1
- `POST /api/v1/hot/book2/run` `{limit?, tail?}`；`POST /api/v1/hot/book2/stop`
- `POST /api/v1/hot/brief` 只服务账本3（联网 + 下一开盘）

## 2026-09-10 一枪

验证窗最后一期 `2024-01-26`：Grok `keep=["U02","U04","U05"]`（只回 Uxx）。payload 无代码/日期。不是结论。全窗 29 期另跑。
